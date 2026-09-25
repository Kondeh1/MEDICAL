"""
Appointment list, book, detail; provider schedule and accept/reject.
"""
import json
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView

from accounts.mixins import PatientRequiredMixin, ProviderRequiredMixin
from audit_logs.utils import log_action
from audit_logs.models import AuditLog

from .models import Appointment, ProviderAvailability
from .forms import BookAppointmentForm, ProviderAvailabilityForm, AppointmentApprovalForm

User = get_user_model()


class AppointmentListView(LoginRequiredMixin, ListView):
    """List appointments for current user (patient sees own; provider sees own)."""
    model = Appointment
    template_name = "appointments/list.html"
    context_object_name = "appointments"
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related("patient", "provider")
        if self.request.user.is_patient:
            return qs.filter(patient=self.request.user)
        if self.request.user.is_provider:
            return qs.filter(provider=self.request.user)
        if self.request.user.is_administrator:
            return qs
        return qs.none()


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Show single appointment (participant or admin)."""
    model = Appointment
    template_name = "appointments/detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        qs = super().get_queryset().select_related("patient", "provider")
        if self.request.user.is_administrator:
            return qs
        return qs.filter(patient=self.request.user) | qs.filter(provider=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.object
        
        # Add formatted time information
        if appointment.status == Appointment.Status.CONFIRMED and appointment.start_time and appointment.end_time:
            context["scheduled_time"] = f"{appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}"
        elif appointment.status == Appointment.Status.PENDING:
            context["status_message"] = "Awaiting doctor's schedule confirmation"
        
        return context


class BookAppointmentView(PatientRequiredMixin, CreateView):
    """Patient books a new appointment."""
    model = Appointment
    form_class = BookAppointmentForm
    template_name = "appointments/book.html"
    success_url = reverse_lazy("appointments:list")

    def form_valid(self, form):
        form.instance.patient = self.request.user
        form.instance.status = Appointment.Status.PENDING
        response = super().form_valid(form)
        log_action(
            self.request,
            AuditLog.Action.APPOINTMENT_CREATED,
            message=f"Appointment #{self.object.pk} booked with {self.object.provider.get_full_name()}",
        )
        messages.success(self.request, "Appointment request sent. The provider will confirm or reject.")

        # Notify provider about the pending appointment request.
        try:
            from messaging.notification_utils import create_appointment_request_notification

            create_appointment_request_notification(
                recipient=self.object.provider,
                patient=self.object.patient,
                provider=self.object.provider,
                appointment=self.object,
            )
        except Exception:
            # Notification failure should not break booking.
            pass

        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        from accounts.models import ProviderProfile
        approved_ids = ProviderProfile.objects.filter(approval_status="APPROVED").values_list("user_id", flat=True)
        kwargs["queryset"] = User.objects.filter(id__in=approved_ids)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import ProviderProfile
        from .models import Appointment as Appt

        profiles = ProviderProfile.objects.filter(
            approval_status="APPROVED"
        ).select_related("user").values("user_id", "user__first_name", "user__last_name", "specialization")

        # Keywords that map each sickness choice to specialization terms
        SICKNESS_KEYWORDS = {
            "cardiology":       ["cardio", "heart", "cardiovascular"],
            "dermatology":      ["dermat", "skin", "hair", "nail"],
            "endocrinology":    ["endocrin", "diabetes", "hormonal", "thyroid"],
            "ent":              ["ent", "ear", "nose", "throat", "otolaryngol"],
            "gastroenterology": ["gastro", "digestive", "stomach", "bowel", "intestin"],
            "gynecology":       ["gynecol", "obstetric", "women", "reproductive"],
            "mental_health":    ["psychiatr", "psycholog", "mental", "behav"],
            "neurology":        ["neurol", "brain", "nervous", "spine"],
            "oncology":         ["oncol", "cancer", "tumor", "tumour"],
            "ophthalmology":    ["ophthal", "eye", "vision", "ocular"],
            "orthopedics":      ["orthop", "bone", "joint", "muscle", "fracture", "spine"],
            "pediatrics":       ["pediatr", "paediatr", "child", "infant"],
            "pulmonology":      ["pulmon", "lung", "respirat", "chest", "bronch"],
            "urology":          ["urol", "kidney", "urinary", "bladder", "renal"],
        }

        provider_map = {}
        all_providers = []

        for p in profiles:
            uid = p["user_id"]
            name = f"{p['user__first_name']} {p['user__last_name']}".strip() or f"Provider #{uid}"
            spec = (p["specialization"] or "").lower()
            entry = {"id": uid, "name": name, "specialization": p["specialization"] or ""}
            all_providers.append(entry)

            for choice_val, keywords in SICKNESS_KEYWORDS.items():
                if any(kw in spec for kw in keywords):
                    provider_map.setdefault(choice_val, []).append(entry)

        context["provider_map_json"] = json.dumps(provider_map)
        context["all_providers_json"] = json.dumps(all_providers)
        return context


def providers_by_sickness(request):
    """AJAX: return approved providers filtered by sickness_type keyword match against specialization."""
    from accounts.models import ProviderProfile
    from .models import Appointment as Appt

    sickness = request.GET.get("sickness_type", "").strip().lower()
    profiles_qs = ProviderProfile.objects.filter(
        approval_status="APPROVED"
    ).select_related("user")

    if sickness and sickness not in ("general", "other"):
        keyword = sickness.replace("_", " ")
        profiles_qs = profiles_qs.filter(
            models.Q(specialization__icontains=keyword) |
            models.Q(specialization__icontains=sickness)
        )

    providers = [
        {
            "id": p.user_id,
            "name": p.user.get_full_name() or f"Provider #{p.user_id}",
            "specialization": p.specialization,
        }
        for p in profiles_qs
    ]
    return JsonResponse({"providers": providers})


def provider_availability_slots(request, provider_id):
    """AJAX: return active availability slots for a given provider."""
    from django.utils import timezone
    import datetime

    slots = ProviderAvailability.objects.filter(
        provider_id=provider_id,
        is_available=True,
    ).order_by("day_of_week", "date", "start_time")

    today = timezone.localdate()
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    data = []
    for s in slots:
        if s.date and s.date < today:
            continue  # skip past one-off dates
        if s.date:
            label = s.date.strftime("%a %d %b %Y")
        else:
            label = DAYS[s.day_of_week] if s.day_of_week is not None else "—"
        data.append({
            "id": s.pk,
            "label": label,
            "start": s.start_time.strftime("%I:%M %p"),
            "end": s.end_time.strftime("%I:%M %p"),
            "date": s.date.isoformat() if s.date else None,
            "day_of_week": s.day_of_week,
        })

    return JsonResponse({"slots": data})


class ProviderScheduleView(ProviderRequiredMixin, ListView):
    """Provider views and can add availability (handled in template + separate view)."""
    model = ProviderAvailability
    template_name = "appointments/provider_schedule.html"
    context_object_name = "slots"

    def get_queryset(self):
        return ProviderAvailability.objects.filter(provider=self.request.user).order_by("day_of_week", "start_time")


def add_availability(request):
    """Provider adds an availability slot."""
    if not request.user.is_authenticated or not request.user.is_provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == "POST":
        form = ProviderAvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.provider = request.user
            slot.save()
            messages.success(request, "Availability slot added.")
            return redirect("appointments:provider_schedule")
    else:
        form = ProviderAvailabilityForm()
    return render(request, "appointments/add_availability.html", {"form": form})


def delete_availability(request, pk):
    """Provider deletes one of their availability slots."""
    if not request.user.is_authenticated or not request.user.is_provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    slot = get_object_or_404(ProviderAvailability, pk=pk, provider=request.user)
    if request.method == "POST":
        slot.delete()
        messages.success(request, "Availability slot removed.")
    return redirect("appointments:provider_schedule")


def accept_reject_appointment(request, pk):
    """Provider accepts or rejects an appointment with scheduling."""
    appointment = get_object_or_404(Appointment, pk=pk, provider=request.user)
    
    if request.method == "POST":
        action = request.POST.get("action")
        from messaging.notification_utils import (
            create_appointment_approval_notification,
            create_appointment_request_notification,
        )
        
        # Provider sets or updates the exact time for the appointment.
        form = AppointmentApprovalForm(request.POST, instance=appointment)
        form_is_valid = form.is_valid()
        
        def is_slot_available(start_time, end_time):
            """Check if provider has an availability slot matching exactly."""
            if not (start_time and end_time and appointment.date):
                return False
            day_idx = appointment.date.weekday()  # Monday=0
            qs = ProviderAvailability.objects.filter(
                provider=request.user,
                is_available=True,
                start_time=start_time,
                end_time=end_time,
            ).filter(
                models.Q(date=appointment.date) | models.Q(date__isnull=True, day_of_week=day_idx)
            )
            return qs.exists()

        if action in ("accept", "reschedule") and form_is_valid:
            # Show scheduling form
            proposed = form.save(commit=False)
            proposed.status = Appointment.Status.CONFIRMED

            if not is_slot_available(proposed.start_time, proposed.end_time):
                messages.error(request, "Selected time is not within your availability slots.")
            else:
                appointment = proposed
                appointment.status = Appointment.Status.CONFIRMED
                appointment.save()

                # Create approval notification for the patient.
                create_appointment_approval_notification(
                    appointment.patient,
                    appointment.provider,
                    appointment,
                )

                log_action(
                    request,
                    AuditLog.Action.APPOINTMENT_UPDATED,
                    message=f"Appointment #{pk} confirmed{' (rescheduled)' if action == 'reschedule' else ''}.",
                )
                messages.success(request, "Appointment confirmed successfully. Patient has been notified.")
                return redirect("appointments:list")

        elif action == "refer":
            if not form_is_valid:
                messages.error(request, "Please fix the scheduling form errors before referring.")
            else:
                referred_provider_id = request.POST.get("referred_provider")
                if not referred_provider_id:
                    messages.error(request, "Please select a provider to refer the patient to.")
                else:
                    referred_provider = get_object_or_404(User, id=referred_provider_id, is_active=True)
                    # Ensure referred provider is a provider profile approved.
                    from accounts.models import ProviderProfile
                    referred_profile = get_object_or_404(ProviderProfile, user_id=referred_provider.id, approval_status="APPROVED")

                    # Validate referred provider matches the same speciality rules.
                    SICKNESS_KEYWORDS = {
                        "cardiology":       ["cardio", "heart", "cardiovascular"],
                        "dermatology":      ["dermat", "skin", "hair", "nail"],
                        "endocrinology":    ["endocrin", "diabetes", "hormonal", "thyroid"],
                        "ent":              ["ent", "ear", "nose", "throat", "otolaryngol"],
                        "gastroenterology": ["gastro", "digestive", "stomach", "bowel", "intestin"],
                        "gynecology":       ["gynecol", "obstetric", "women", "reproductive"],
                        "mental_health":    ["psychiatr", "psycholog", "mental", "behav"],
                        "neurology":        ["neurol", "brain", "nervous", "spine"],
                        "oncology":         ["oncol", "cancer", "tumor", "tumour"],
                        "ophthalmology":    ["ophthal", "eye", "vision", "ocular"],
                        "orthopedics":      ["orthop", "bone", "joint", "muscle", "fracture", "spine"],
                        "pediatrics":       ["pediatr", "paediatr", "child", "infant"],
                        "pulmonology":      ["pulmon", "lung", "respirat", "chest", "bronch"],
                        "urology":          ["urol", "kidney", "urinary", "bladder", "renal"],
                    }

                    spec = (referred_profile.specialization or "").lower()
                    sickness_type = appointment.sickness_type
                    allowed = False
                    if sickness_type in SICKNESS_KEYWORDS:
                        allowed = any(kw in spec for kw in SICKNESS_KEYWORDS[sickness_type])
                    elif sickness_type == Appointment.SicknessType.OTHER and appointment.sickness_other:
                        allowed = appointment.sickness_other.lower() in spec
                    else:
                        # For "general" we allow any approved provider.
                        allowed = sickness_type == Appointment.SicknessType.GENERAL

                    if not allowed:
                        messages.error(request, "Selected provider does not match the requested speciality.")
                        return render(request, "appointments/accept_reject.html", {"appointment": appointment, "form": form, "referral_providers": []})

                    # Create a new pending appointment for the referred provider.
                    referred_appt = Appointment.objects.create(
                        patient=appointment.patient,
                        provider=referred_provider,
                        sickness_type=appointment.sickness_type,
                        sickness_other=appointment.sickness_other,
                        date=appointment.date,
                        start_time=form.cleaned_data["start_time"],
                        end_time=form.cleaned_data["end_time"],
                        reason=appointment.reason,
                        status=Appointment.Status.PENDING,
                    )

                    # Mark original appointment rejected.
                    appointment.status = Appointment.Status.REJECTED
                    appointment.save()

                    # Notify the referred provider.
                    create_appointment_request_notification(
                        recipient=referred_appt.provider,
                        patient=referred_appt.patient,
                        provider=referred_appt.provider,
                        appointment=referred_appt,
                    )

                    log_action(
                        request,
                        AuditLog.Action.APPOINTMENT_UPDATED,
                        message=f"Appointment #{pk} referred to provider {referred_provider.username}.",
                    )
                    messages.success(request, "Patient referred successfully. The new provider has been notified.")
                    return redirect("appointments:list")

        # If action requires form validity but it's invalid, fall through to render with errors.
    
    # For GET request or when accepting, show the scheduling form
    form = AppointmentApprovalForm(instance=appointment)

    # Build referral provider list (same specialization) for "decline & refer".
    from accounts.models import ProviderProfile

    SICKNESS_KEYWORDS = {
        "cardiology":       ["cardio", "heart", "cardiovascular"],
        "dermatology":      ["dermat", "skin", "hair", "nail"],
        "endocrinology":    ["endocrin", "diabetes", "hormonal", "thyroid"],
        "ent":              ["ent", "ear", "nose", "throat", "otolaryngol"],
        "gastroenterology": ["gastro", "digestive", "stomach", "bowel", "intestin"],
        "gynecology":       ["gynecol", "obstetric", "women", "reproductive"],
        "mental_health":    ["psychiatr", "psycholog", "mental", "behav"],
        "neurology":        ["neurol", "brain", "nervous", "spine"],
        "oncology":         ["oncol", "cancer", "tumor", "tumour"],
        "ophthalmology":    ["ophthal", "eye", "vision", "ocular"],
        "orthopedics":      ["orthop", "bone", "joint", "muscle", "fracture", "spine"],
        "pediatrics":       ["pediatr", "paediatr", "child", "infant"],
        "pulmonology":      ["pulmon", "lung", "respirat", "chest", "bronch"],
        "urology":          ["urol", "kidney", "urinary", "bladder", "renal"],
    }

    profiles_qs = ProviderProfile.objects.filter(approval_status="APPROVED").select_related("user")
    sickness_type = appointment.sickness_type
    if sickness_type in SICKNESS_KEYWORDS:
        keywords = SICKNESS_KEYWORDS[sickness_type]
        q = models.Q()
        for kw in keywords:
            q |= models.Q(specialization__icontains=kw)
        profiles_qs = profiles_qs.filter(q)
    elif sickness_type == Appointment.SicknessType.OTHER and appointment.sickness_other:
        query = appointment.sickness_other.lower()
        profiles_qs = profiles_qs.filter(specialization__icontains=query)

    # Exclude current provider from referral list.
    profiles_qs = profiles_qs.exclude(user_id=request.user.id)

    referral_providers = [
        {
            "id": p.user_id,
            "name": p.user.get_full_name() or f"Provider #{p.user_id}",
            "specialization": p.specialization,
        }
        for p in profiles_qs
    ]

    return render(
        request,
        "appointments/accept_reject.html",
        {"appointment": appointment, "form": form, "referral_providers": referral_providers},
    )
