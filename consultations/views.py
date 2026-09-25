"""
Consultation list, detail, and chat-based room (simulated with messaging).
"""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q, Max

from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.mixins import PatientRequiredMixin, ProviderRequiredMixin
from appointments.models import Appointment
from audit_logs.utils import log_action
from audit_logs.models import AuditLog

from .models import Consultation
from .forms import ConsultationNotesForm


class ConsultationListView(LoginRequiredMixin, ListView):
    """List consultations for current user (patient or provider)."""
    model = Consultation
    template_name = "consultations/list.html"
    context_object_name = "consultations"
    paginate_by = 15

    def get_queryset(self):
        qs = Consultation.objects.select_related("appointment", "appointment__patient", "appointment__provider")
        if self.request.user.is_patient:
            return qs.filter(appointment__patient=self.request.user)
        if self.request.user.is_provider:
            return qs.filter(appointment__provider=self.request.user)
        if self.request.user.is_administrator:
            return qs
        return qs.none()


class ConsultationDetailView(LoginRequiredMixin, DetailView):
    """View consultation summary (after ended)."""
    model = Consultation
    template_name = "consultations/detail.html"
    context_object_name = "consultation"

    def get_queryset(self):
        qs = super().get_queryset().select_related("appointment__patient", "appointment__provider")
        if self.request.user.is_administrator:
            return qs
        return qs.filter(appointment__patient=self.request.user) | qs.filter(appointment__provider=self.request.user)


def consultation_dashboard(request):
    """Consultation dashboard - centralized command center for managing virtual visits."""
    # Get consultations for the current user
    consultations_qs = Consultation.objects.select_related(
        "appointment", "appointment__patient", "appointment__provider"
    ).order_by("-started_at")
    
    if request.user.is_patient:
        consultations = consultations_qs.filter(appointment__patient=request.user)
    elif request.user.is_provider:
        consultations = consultations_qs.filter(appointment__provider=request.user)
    elif request.user.is_administrator:
        consultations = consultations_qs
    else:
        consultations = Consultation.objects.none()
    
    # Get upcoming appointments
    from appointments.models import Appointment
    from datetime import datetime
    today = timezone.now().date()
    upcoming_appointments = Appointment.objects.filter(
        Q(patient=request.user) | Q(provider=request.user),
        date__gte=today,
        status=Appointment.Status.CONFIRMED
    ).select_related("patient", "provider").order_by("date", "start_time")
    
    # Get recent consultations
    recent_consultations = consultations.filter(status=Consultation.Status.ENDED)[:5]
    
    # Get active consultations
    active_consultations = consultations.filter(status=Consultation.Status.ACTIVE)
    
    # Get patient records if provider
    patient_records = []
    if request.user.is_provider:
        from medical_records.models import MedicalRecord
        # Get unique patients by getting the latest record for each patient
        patient_ids = (
            MedicalRecord.objects
            .filter(patient__in=Appointment.objects.filter(provider=request.user).values('patient'))
            .values('patient')
            .annotate(latest_record=Max('id'))
            .values_list('latest_record', flat=True)
        )
        patient_records = (
            MedicalRecord.objects
            .filter(id__in=patient_ids)
            .select_related('patient')
            .order_by('-created_at')[:5]
        )
    
    # Get scheduled calls for provider
    scheduled_calls = []
    if request.user.is_provider:
        from messaging.models import ScheduledCall
        scheduled_calls = ScheduledCall.objects.filter(
            appointment__provider=request.user,
            scheduled_time__gte=timezone.now()
        ).select_related('appointment', 'appointment__patient').order_by('scheduled_time')[:5]
    
    context = {
        "consultations": consultations,
        "upcoming_appointments": upcoming_appointments,
        "recent_consultations": recent_consultations,
        "active_consultations": active_consultations,
        "patient_records": patient_records,
        "scheduled_calls": scheduled_calls,
    }
    
    return render(request, "consultations/dashboard.html", context)


def consultation_room(request, pk):
    """
    Consultation room with chat and video/audio call functionality.
    Only for confirmed appointment; provider can start;
    both can send messages (stored in messaging app) and provider can end with notes.
    """
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "provider"),
        pk=pk,
    )
    # Must be participant
    if request.user != appointment.patient and request.user != appointment.provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if appointment.status != Appointment.Status.CONFIRMED:
        messages.warning(request, "This appointment is not confirmed.")
        return redirect("appointments:detail", pk=pk)

    consultation, created = Consultation.objects.get_or_create(
        appointment=appointment,
        defaults={"status": Consultation.Status.ACTIVE},
    )
    if created and request.user.is_provider:
        log_action(request, AuditLog.Action.CONSULTATION_STARTED, message=f"Consultation started for appointment #{pk}")

    # Import messaging models for in-consultation chat (same conversation as messaging)
    from messaging.models import Conversation, Message
    from messaging.notification_utils import create_message_notification
    conv, _ = Conversation.objects.get_or_create(
        appointment=appointment,
        defaults={"patient": appointment.patient, "provider": appointment.provider},
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "send_message":
            text = (request.POST.get("text") or "").strip()
            if text:
                message = Message.objects.create(conversation=conv, sender=request.user, content=text)
                
                # Send notification via WebSocket if available
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"chat_{conv.id}",
                        {
                            "type": "chat_message",
                            "message": {
                                "id": message.id,
                                "content": message.content,
                                "sender": message.sender.username,
                                "sender_name": message.sender.get_full_name() or message.sender.username,
                                "sender_profile_picture": message.sender.profile_picture.url if message.sender.profile_picture else None,
                                "created_at": message.created_at.strftime('%H:%M'),
                                "message_type": message.message_type,
                                "prescription_id": message.prescription.id if message.prescription else None,
                            }
                        }
                    )
                except ImportError:
                    # Fallback if channels is not available
                    pass
                
                # Create notification for the other participant
                other_user = conv.provider if request.user == conv.patient else conv.patient
                create_message_notification(other_user, request.user, conv, text)
                
                # Return JSON response for AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': True,
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender': message.sender.username,
                            'sender_name': message.sender.get_full_name() or message.sender.username,
                            'sender_profile_picture': message.sender.profile_picture.url if message.sender.profile_picture else None,
                            'created_at': message.created_at.strftime('%H:%M'),
                            'message_type': message.message_type,
                            'prescription_id': message.prescription.id if message.prescription else None,
                        }
                    })
                
                return redirect("consultations:room", pk=pk)
        elif action == "send_prescription" and request.user.is_provider:
            # Handle prescription sending
            medication = request.POST.get('medication')
            dosage = request.POST.get('dosage')
            frequency = request.POST.get('frequency')
            duration = request.POST.get('duration')
            notes = request.POST.get('notes', '')
            
            if medication and dosage and frequency and duration:
                try:
                    # Create prescription
                    from prescriptions.models import Prescription, PrescriptionItem
                    
                    # Create the prescription
                    prescription = Prescription.objects.create(
                        patient=appointment.patient,
                        provider=appointment.provider,
                        consultation=consultation,
                        notes=notes
                    )
                    
                    # Create prescription item with medication details
                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medication_name=medication,
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        instructions=notes
                    )
                    
                    # Create message with prescription
                    message = Message.objects.create(
                        conversation=conv,
                        sender=request.user,
                        content=f"Prescription for {medication}: {dosage}, {frequency}, {duration}",
                        message_type='PRESCRIPTION',
                        prescription=prescription
                    )
                    
                    # Send notification via WebSocket if available
                    try:
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"chat_{conv.id}",
                            {
                                "type": "chat_message",
                                "message": {
                                    "id": message.id,
                                    "content": message.content,
                                    "sender": message.sender.username,
                                    "sender_name": message.sender.get_full_name() or message.sender.username,
                                    "sender_profile_picture": message.sender.profile_picture.url if message.sender.profile_picture else None,
                                    "created_at": message.created_at.strftime('%H:%M'),
                                    "message_type": message.message_type,
                                    "prescription_id": message.prescription.id if message.prescription else None,
                                }
                            }
                        )
                    except ImportError:
                        # Fallback if channels is not available
                        pass
                    
                    # Return JSON response for AJAX
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        from django.http import JsonResponse
                        return JsonResponse({'success': True})
                    
                    return redirect("consultations:room", pk=pk)
                    
                except Exception as e:
                    # Log the error and return error response
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error creating prescription: {str(e)}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        from django.http import JsonResponse
                        return JsonResponse({'success': False, 'error': str(e)}, status=400)
                    
                    messages.error(request, f"Error creating prescription: {str(e)}")
                    return redirect("consultations:room", pk=pk)
            else:
                # Missing required fields
                error_msg = "All fields (medication, dosage, frequency, duration) are required."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                
                messages.error(request, error_msg)
                return redirect("consultations:room", pk=pk)
        elif action == "end_consultation" and request.user.is_provider:
            form = ConsultationNotesForm(request.POST, instance=consultation)
            if form.is_valid():
                form.save()
                consultation.status = Consultation.Status.ENDED
                consultation.ended_at = timezone.now()
                consultation.save()
                appointment.status = Appointment.Status.COMPLETED
                appointment.save()
                log_action(request, AuditLog.Action.CONSULTATION_ENDED, message=f"Consultation ended for appointment #{pk}")
                messages.success(request, "Consultation ended.")
                return redirect("consultations:list")

    messages_list = list(conv.messages.select_related("sender").order_by("created_at"))
    return render(
        request,
        "consultations/room.html",
        {
            "appointment": appointment,
            "consultation": consultation,
            "conversation": conv,
            "messages_list": messages_list,
            "notes_form": ConsultationNotesForm(instance=consultation) if request.user.is_provider and consultation.status == Consultation.Status.ACTIVE else None,
        },
    )
