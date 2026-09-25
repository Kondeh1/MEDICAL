"""
Inbox (list of conversations) and thread view (messages in a conversation).
Video and audio call functionality using WebRTC.
"""
import uuid
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from django.http import JsonResponse

from .models import Conversation, Message, Call, ScheduledCall, Notification
from .notification_utils import create_call_notification, create_message_notification, create_prescription_notification, create_scheduled_call_notification, create_appointment_reminder, create_scheduled_consultation_notification

# Import for WebSocket notifications
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class InboxView(LoginRequiredMixin, ListView):
    """List conversations for current user (patient or provider)."""
    model = Conversation
    template_name = "messaging/inbox.html"
    context_object_name = "conversations"
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        return (
            Conversation.objects.filter(
                Q(patient=self.request.user) | Q(provider=self.request.user)
            )
            .select_related("patient", "provider")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get missed calls for the current user (as receiver)
        context["missed_calls"] = Call.objects.filter(
            receiver=self.request.user,
            status=Call.Status.MISSED,
        ).select_related("caller", "conversation").order_by("-started_at")[:10]
        return context


def thread_view(request, pk):
    """View a conversation thread; send new message via POST."""
    conv = get_object_or_404(Conversation.objects.select_related("patient", "provider"), pk=pk)
    if request.user != conv.patient and request.user != conv.provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if request.method == "POST":
        # Handle AJAX requests for real-time messaging
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            action = request.POST.get("action", "send_message")
            
            if action == "send_message":
                text = (request.POST.get("content") or "").strip()
                if text:
                    message = Message.objects.create(conversation=conv, sender=request.user, content=text)
                    
                    # Send WebSocket notification to other participants
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'chat_{conv.id}',
                        {
                            'type': 'chat_message',
                            'message_id': message.id,
                            'content': message.content,
                            'sender_id': message.sender.id,
                            'sender_username': message.sender.get_full_name() or message.sender.username,
                            'sender_avatar': message.sender.profile_picture.url if message.sender.profile_picture else None,
                        }
                    )
                    
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
                else:
                    return JsonResponse({'status': 'error', 'message': 'Empty message'})
        else:
            # Handle regular POST requests (legacy)
            action = request.POST.get("action", "send_message")

            if action == "send_message":
                text = (request.POST.get("content") or "").strip()
                if text:
                    Message.objects.create(conversation=conv, sender=request.user, content=text)
                    return redirect("messaging:thread", pk=pk)

            elif action == "send_prescription" and request.user.is_provider:
                from prescriptions.models import Prescription, PrescriptionItem
                notes = request.POST.get("prescription_notes", "").strip()

                # Create prescription
                prescription = Prescription.objects.create(
                    patient=conv.patient,
                    provider=request.user,
                    notes=notes,
                )
                
                # Create prescription notification
                create_prescription_notification(conv.patient, request.user, prescription)

                # Add prescription items
                medications = request.POST.getlist("medication_name[]")
                dosages = request.POST.getlist("dosage[]")
                frequencies = request.POST.getlist("frequency[]")
                durations = request.POST.getlist("duration[]")
                instructions_list = request.POST.getlist("instructions[]")

                for i in range(len(medications)):
                    if medications[i].strip():
                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medication_name=medications[i].strip(),
                            dosage=dosages[i].strip() if i < len(dosages) else "",
                            frequency=frequencies[i].strip() if i < len(frequencies) else "",
                            duration=durations[i].strip() if i < len(durations) else "",
                            instructions=instructions_list[i].strip() if i < len(instructions_list) else "",
                        )

                # Create prescription message
                Message.objects.create(
                    conversation=conv,
                    sender=request.user,
                    content=f"Prescription issued: {prescription.items.count()} medication(s)",
                    message_type=Message.MessageType.PRESCRIPTION,
                    prescription=prescription,
                )
                return redirect("messaging:thread", pk=pk)

    messages_list = list(conv.messages.select_related("sender", "prescription").order_by("created_at"))
    
    return render(
        request,
        "messaging/thread.html",
        {"conversation": conv, "messages_list": messages_list},
    )


@login_required
def initiate_call(request, pk, call_type):
    """Initiate a video or audio call in a conversation."""
    conv = get_object_or_404(Conversation.objects.select_related("patient", "provider"), pk=pk)
    if request.user != conv.patient and request.user != conv.provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Determine receiver (the other person)
    receiver = conv.provider if request.user == conv.patient else conv.patient

    # Validate call type
    if call_type not in [Call.CallType.VIDEO, Call.CallType.AUDIO]:
        call_type = Call.CallType.VIDEO

    # Create call record
    room_id = str(uuid.uuid4())
    call = Call.objects.create(
        conversation=conv,
        caller=request.user,
        receiver=receiver,
        call_type=call_type,
        status=Call.Status.PENDING,
        room_id=room_id,
    )
    
    # Send WebSocket notification to receiver
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{receiver.id}',
        {
            'type': 'call_notification',
            'call_id': call.id,
            'caller_id': request.user.id,
            'caller_name': request.user.get_full_name() or request.user.username,
            'call_type': call_type,
            'room_id': room_id,
            'timestamp': timezone.now().isoformat(),
        }
    )

    return redirect("messaging:call_room", room_id=room_id)


@login_required
def call_room(request, room_id):
    """Join a call room (WebRTC video/audio interface)."""
    call = get_object_or_404(Call.objects.select_related("caller", "receiver", "conversation"), room_id=room_id)

    # Only caller or receiver can join
    if request.user != call.caller and request.user != call.receiver:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Update status when receiver joins
    if request.user == call.receiver and call.status == Call.Status.PENDING:
        call.status = Call.Status.CONNECTED
        call.connected_at = timezone.now()
        call.save()

    is_caller = request.user == call.caller
    other_user = call.receiver if is_caller else call.caller

    return render(
        request,
        "messaging/call_room.html",
        {
            "call": call,
            "is_caller": is_caller,
            "other_user": other_user,
            "room_id": room_id,
        },
    )


@login_required
def end_call(request, room_id):
    """End an active call."""
    call = get_object_or_404(Call, room_id=room_id)

    if request.user != call.caller and request.user != call.receiver:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if call.status in [Call.Status.PENDING, Call.Status.CONNECTED]:
        call.status = Call.Status.ENDED
        call.ended_at = timezone.now()
        call.save()

    return redirect("messaging:thread", pk=call.conversation.pk)


@login_required
def mark_call_missed(request, call_id):
    """Mark a call as missed (called when receiver doesn't answer)."""
    call = get_object_or_404(Call, pk=call_id)

    if request.user != call.caller and request.user != call.receiver:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if call.status == Call.Status.PENDING:
        call.status = Call.Status.MISSED
        call.ended_at = timezone.now()
        call.save()

    return redirect("messaging:inbox")


@login_required
def decline_call(request, call_id):
    """Decline an incoming call via AJAX."""
    if request.method == 'POST':
        call = get_object_or_404(Call, pk=call_id)
        
        if request.user != call.receiver:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        if call.status == Call.Status.PENDING:
            call.status = Call.Status.MISSED
            call.ended_at = timezone.now()
            call.save()
            
            # Send WebSocket notifications to end the call completely
            try:
                channel_layer = get_channel_layer()
                
                print(f"Call details: ID={call_id}, Room={call.room_id}, Caller={call.caller.username}, Decliner={request.user.username}")
                
                # Send decline notification to caller's personal group
                caller_group_name = f'user_{call.caller.id}'
                print(f"Sending decline notification to caller group: {caller_group_name}")
                async_to_sync(channel_layer.group_send)(
                    caller_group_name,
                    {
                        'type': 'call_status_update',
                        'call_id': call_id,
                        'status': 'DECLINED',
                        'message': f'{request.user.get_full_name() or request.user.username} declined your call'
                    }
                )
                
                # Send call_ended message to caller's personal group
                print(f"Sending call_ended to caller group: {caller_group_name}")
                async_to_sync(channel_layer.group_send)(
                    caller_group_name,
                    {
                        'type': 'call_ended',
                        'sender_id': str(request.user.id),
                        'sender_name': request.user.get_full_name() or request.user.username,
                        'message': f'Call declined by {request.user.get_full_name() or request.user.username}'
                    }
                )
                
                # Also send call_ended to the call room group (for users who joined)
                room_group_name = f'call_{call.room_id}'
                print(f"Sending call_ended to room group: {room_group_name}")
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'call_ended',
                        'sender_id': str(request.user.id),
                        'sender_name': request.user.get_full_name() or request.user.username,
                        'message': f'Call declined by {request.user.get_full_name() or request.user.username}'
                    }
                )
                
                print("Successfully sent all WebSocket messages for call termination")
            except Exception as e:
                print(f"Error sending decline notification: {e}")
                import traceback
                traceback.print_exc()
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'error', 'message': 'Call cannot be declined'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@login_required
def update_call_status(request, call_id):
    """Update or get call status via AJAX (for WebRTC connection status)."""
    import json
    from django.http import JsonResponse
    
    call = get_object_or_404(Call, pk=call_id)
    
    if request.user != call.caller and request.user != call.receiver:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status == 'CONNECTED' and call.status == Call.Status.PENDING:
                call.status = Call.Status.CONNECTED
                call.connected_at = timezone.now()
                call.save()
                return JsonResponse({'status': 'success', 'call_status': call.status})
            elif new_status == 'IN_CALL' and call.status == Call.Status.PENDING:
                # User has joined the call page
                return JsonResponse({'status': 'success', 'call_status': 'PENDING', 'user_in_call': True})
            
            return JsonResponse({'status': 'success', 'call_status': call.status})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    elif request.method == 'GET':
        # Return current call status
        return JsonResponse({
            'status': 'success',
            'call_status': call.status,
            'caller_in_call': call.caller == request.user or call.status != Call.Status.PENDING,
            'receiver_in_call': call.receiver == request.user or call.status != Call.Status.PENDING
        })
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@login_required
def download_prescription(request, prescription_id, format):
    """Download prescription as PDF or DOCX."""
    from prescriptions.models import Prescription
    from django.http import HttpResponse
    from datetime import datetime

    prescription = get_object_or_404(Prescription, pk=prescription_id)

    # Only patient or provider can download
    if request.user != prescription.patient and request.user != prescription.provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if format == "pdf":
        # Generate PDF response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="prescription_{prescription_id}.pdf"'

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            doc = SimpleDocTemplate(response, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#0d6efd"),
                spaceAfter=30,
                alignment=1,  # Center
            )
            elements.append(Paragraph("MEDICAL PRESCRIPTION", title_style))
            elements.append(Spacer(1, 0.2 * inch))

            # Provider and Patient Info
            info_data = [
                ["Provider:", prescription.provider.get_full_name() or prescription.provider.username],
                ["Patient:", prescription.patient.get_full_name() or prescription.patient.username],
                ["Date:", prescription.created_at.strftime("%B %d, %Y")],
            ]
            if prescription.notes:
                info_data.append(["Notes:", prescription.notes])

            info_table = Table(info_data, colWidths=[1.5 * inch, 4 * inch])
            info_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Medications
            elements.append(Paragraph("Prescribed Medications:", styles["Heading2"]))
            elements.append(Spacer(1, 0.1 * inch))

            med_data = [["Medication", "Dosage", "Frequency", "Duration", "Instructions"]]
            for item in prescription.items.all():
                med_data.append([
                    item.medication_name,
                    item.dosage,
                    item.frequency,
                    item.duration,
                    item.instructions[:50] + "..." if len(item.instructions) > 50 else item.instructions,
                ])

            med_table = Table(med_data, colWidths=[1.5 * inch, 1 * inch, 1.2 * inch, 1 * inch, 1.8 * inch])
            med_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(med_table)

            # Footer
            elements.append(Spacer(1, 0.5 * inch))
            footer_style = ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                alignment=1,
            )
            elements.append(Paragraph("This prescription was generated electronically.", footer_style))

            doc.build(elements)
            return response

        except ImportError:
            # Fallback if reportlab is not installed
            response = HttpResponse("PDF generation requires reportlab. Please install: pip install reportlab", content_type="text/plain")
            return response

    elif format == "docx":
        # Generate DOCX response
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="prescription_{prescription_id}.docx"'

        try:
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # Title
            title = doc.add_heading("MEDICAL PRESCRIPTION", 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Info
            doc.add_paragraph(f"Provider: {prescription.provider.get_full_name() or prescription.provider.username}")
            doc.add_paragraph(f"Patient: {prescription.patient.get_full_name() or prescription.patient.username}")
            doc.add_paragraph(f"Date: {prescription.created_at.strftime('%B %d, %Y')}")
            if prescription.notes:
                doc.add_paragraph(f"Notes: {prescription.notes}")

            doc.add_paragraph()

            # Medications table
            doc.add_heading("Prescribed Medications:", level=2)
            table = doc.add_table(rows=1, cols=5)
            table.style = "Light Grid Accent 1"

            # Header
            hdr_cells = table.rows[0].cells
            headers = ["Medication", "Dosage", "Frequency", "Duration", "Instructions"]
            for i, header in enumerate(headers):
                hdr_cells[i].text = header

            # Data rows
            for item in prescription.items.all():
                row_cells = table.add_row().cells
                row_cells[0].text = item.medication_name
                row_cells[1].text = item.dosage
                row_cells[2].text = item.frequency
                row_cells[3].text = item.duration
                row_cells[4].text = item.instructions

            # Footer
            doc.add_paragraph()
            footer = doc.add_paragraph("This prescription was generated electronically.")
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer.runs[0].font.size = Pt(8)
            footer.runs[0].font.color.rgb = RGBColor(128, 128, 128)

            doc.save(response)
            return response

        except ImportError:
            # Fallback if python-docx is not installed
            response = HttpResponse("DOCX generation requires python-docx. Please install: pip install python-docx", content_type="text/plain")
            return response

    else:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Invalid format. Use 'pdf' or 'docx'.")


@login_required
def get_scheduled_calls(request):
    """API endpoint to get upcoming scheduled calls for the current user."""
    from django.http import JsonResponse
    from datetime import timedelta
    
    now = timezone.now()
    # Get calls scheduled within the next 5 minutes or that should have started
    window_start = now - timedelta(minutes=2)
    window_end = now + timedelta(minutes=5)
    
    scheduled_calls = ScheduledCall.objects.filter(
        scheduled_time__gte=window_start,
        scheduled_time__lte=window_end,
        status=ScheduledCall.Status.SCHEDULED,
    ).filter(
        models.Q(appointment__patient=request.user) | 
        models.Q(appointment__provider=request.user)
    ).select_related('appointment', 'conversation')
    
    calls_data = []
    for call in scheduled_calls:
        other_user = call.appointment.provider if request.user == call.appointment.patient else call.appointment.patient
        calls_data.append({
            'id': call.id,
            'call_type': call.call_type,
            'scheduled_time': call.scheduled_time.isoformat(),
            'room_id': call.room_id,
            'conversation_id': call.conversation.id,
            'other_user_name': other_user.get_full_name() or other_user.username,
            'appointment_id': call.appointment.id,
        })
    
    return JsonResponse({'calls': calls_data})


@login_required
def start_scheduled_call(request, call_id):
    """Mark a scheduled call as notified and create the actual call."""
    from django.http import JsonResponse
    
    scheduled_call = get_object_or_404(
        ScheduledCall,
        id=call_id,
        status=ScheduledCall.Status.SCHEDULED
    )
    
    # Verify user is part of this appointment
    if request.user != scheduled_call.appointment.patient and request.user != scheduled_call.appointment.provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    # Update scheduled call status
    scheduled_call.status = ScheduledCall.Status.NOTIFIED
    scheduled_call.notified_at = timezone.now()
    scheduled_call.save()
    
    # Create the actual call
    other_user = scheduled_call.appointment.provider if request.user == scheduled_call.appointment.patient else scheduled_call.appointment.patient
    
    call = Call.objects.create(
        conversation=scheduled_call.conversation,
        caller=request.user,
        receiver=other_user,
        call_type=scheduled_call.call_type,
        room_id=scheduled_call.room_id,
    )
    
    return JsonResponse({
        'success': True,
        'call_id': call.id,
        'room_id': call.room_id,
        'redirect_url': f"/messages/call/{call.room_id}/"
    })


@login_required
def get_user_status(request, user_id):
    """API endpoint to get a user's online status."""
    from django.http import JsonResponse
    from accounts.models import CustomUser
    
    try:
        user = CustomUser.objects.get(id=user_id)
        status = user.get_online_status()
        
        return JsonResponse({
            'is_online': user.is_online,
            'status_text': status['text'],
            'last_seen': user.last_seen.isoformat() if user.last_seen else None,
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
def get_notifications(request):
    """Return user's notifications as JSON."""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:10]  # Last 10 unread notifications
    
    notification_data = []
    for notification in notifications:
        data = {
            'id': notification.id,
            'notification_type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
        }
        
        # Add call-specific data if it's a call notification
        if notification.call:
            data['call_id'] = notification.call.id
            data['call_room_id'] = notification.call.room_id

        if notification.scheduled_call:
            data['scheduled_call_id'] = notification.scheduled_call.id

        if notification.appointment:
            data['appointment_id'] = notification.appointment.id

        if notification.consultation:
            data['consultation_id'] = notification.consultation.id

        # Add conversation id for message notifications.
        # Older MESSAGE notifications may not have the conversation FK populated yet,
        # so we attempt a best-effort lookup by matching the notification text
        # to a recent message in one of the user's conversations.
        if notification.notification_type == Notification.NotificationType.MESSAGE:
            if notification.conversation_id:
                data['conversation_id'] = notification.conversation.id
            else:
                try:
                    # notification.message is a truncated prefix; use it to search.
                    prefix = (notification.message or '').replace('...', '')
                    if prefix.strip():
                        window_start = timezone.now() - timedelta(days=7)
                        window_end = notification.created_at + timedelta(minutes=2)

                        # Find the most likely message that produced this notification.
                        msg = (
                            Message.objects.filter(
                                conversation__patient=request.user,
                                content__startswith=prefix,
                                created_at__gte=window_start,
                                created_at__lte=window_end,
                            )
                            .order_by('-created_at')
                            .first()
                        ) or (
                            Message.objects.filter(
                                conversation__provider=request.user,
                                content__startswith=prefix,
                                created_at__gte=window_start,
                                created_at__lte=window_end,
                            )
                            .order_by('-created_at')
                            .first()
                        )

                        if msg and msg.conversation_id:
                            data['conversation_id'] = msg.conversation_id
                except Exception:
                    # Fall back to inbox if we can't infer it.
                    pass
        
        notification_data.append(data)
    
    return JsonResponse({'notifications': notification_data})



@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)



@login_required
def clear_notifications(request):
    """Clear all user notifications."""
    Notification.objects.filter(recipient=request.user).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def trigger_scheduled_calls_check(request):
    """Manually trigger the scheduled calls check for development purposes."""
    from django.core.management import call_command
    import io
    from django.http import JsonResponse
    
    # Only allow providers and administrators to trigger this
    if not (request.user.is_provider or request.user.is_administrator):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Capture output
        out = io.StringIO()
        call_command('check_scheduled_calls', stdout=out)
        output = out.getvalue()
        
        return JsonResponse({'success': True, 'output': output})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)