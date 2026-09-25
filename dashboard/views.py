"""
Home: landing when anonymous; role-based dashboard when authenticated.
Admin dashboard: analytics and provider approval.
"""
from django.contrib import messages
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from accounts.mixins import AdminRequiredMixin
from accounts.models import CustomUser, ProviderProfile
from appointments.models import Appointment
from consultations.models import Consultation
from prescriptions.models import Prescription
from audit_logs.models import AuditLog


class HomeView(TemplateView):
    """Landing or role-based dashboard."""
    template_name = "dashboard/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_administrator:
                return redirect("dashboard:admin_dashboard")
            if request.user.is_provider:
                return redirect("dashboard:provider_dashboard")
            return redirect("dashboard:patient_dashboard")
        return super().get(request, *args, **kwargs)


class AboutView(TemplateView):
    """About page with platform information."""
    template_name = "dashboard/about.html"


class PatientDashboardView(LoginRequiredMixin, TemplateView):
    """Patient dashboard: quick links and recent activity."""
    template_name = "dashboard/patient_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["recent_appointments"] = (
            Appointment.objects.filter(patient=user).order_by("-date", "-start_time")[:5]
        )
        context["recent_prescriptions"] = (
            user.prescriptions.select_related("provider").order_by("-created_at")[:5]
        )
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_patient:
            if request.user.is_provider:
                return redirect("dashboard:provider_dashboard")
            if request.user.is_administrator:
                return redirect("dashboard:admin_dashboard")
        return super().dispatch(request, *args, **kwargs)


class ProviderDashboardView(LoginRequiredMixin, TemplateView):
    """Provider dashboard: pending appointments, schedule link. Accessible to all providers regardless of approval status."""
    template_name = "dashboard/provider_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["pending_appointments"] = (
            Appointment.objects.filter(provider=user, status=Appointment.Status.PENDING)
            .select_related("patient")
            .order_by("date", "start_time")[:10]
        )
        context["today_appointments"] = (
            Appointment.objects.filter(provider=user, status=Appointment.Status.CONFIRMED)
            .select_related("patient")
        )  # filter by date in view or template
        
        # Add approval status to context for display
        if hasattr(user, 'provider_profile'):
            context["is_approved"] = user.provider_profile.is_approved
            context["approval_status"] = user.provider_profile.approval_status
        
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_provider and not request.user.is_administrator:
            return redirect("dashboard:patient_dashboard")
        return super().dispatch(request, *args, **kwargs)


def _admin_required(view_func):
    """Decorator to require administrator role."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_administrator:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Administrator access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@_admin_required
@require_POST
def approve_provider(request, pk):
    """Approve a pending provider application."""
    profile = get_object_or_404(ProviderProfile, pk=pk)
    if profile.approval_status != ProviderProfile.ApprovalStatus.PENDING:
        messages.warning(request, "This provider application has already been processed.")
    else:
        profile.approval_status = ProviderProfile.ApprovalStatus.APPROVED
        profile.approved_at = timezone.now()
        profile.approved_by = request.user
        profile.save()
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.PROVIDER_APPROVED,
            message=f"Provider {profile.user.username} approved.",
        )
        messages.success(request, f"Provider {profile.user.get_full_name() or profile.user.username} has been approved.")
    return redirect("dashboard:admin_dashboard")


@login_required
@_admin_required
@require_POST
def reject_provider(request, pk):
    """Reject a pending provider application."""
    profile = get_object_or_404(ProviderProfile, pk=pk)
    if profile.approval_status != ProviderProfile.ApprovalStatus.PENDING:
        messages.warning(request, "This provider application has already been processed.")
    else:
        profile.approval_status = ProviderProfile.ApprovalStatus.REJECTED
        profile.save()
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.PROVIDER_REJECTED,
            message=f"Provider {profile.user.username} rejected.",
        )
        messages.success(request, f"Provider {profile.user.get_full_name() or profile.user.username} has been rejected.")
    return redirect("dashboard:admin_dashboard")


@login_required
@_admin_required
def provider_application_detail(request, pk):
    """View full provider application details (info + documents) before approving."""
    profile = get_object_or_404(ProviderProfile, pk=pk)
    return render(request, "dashboard/provider_application_detail.html", {"profile": profile})


@login_required
@_admin_required
def provider_credentials_detail(request, pk):
    """View provider credentials (read-only) for medical director review."""
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.PROVIDER)
    profile = get_object_or_404(ProviderProfile, user=user)
    return render(request, "dashboard/provider_credentials_detail.html", {"provider_user": user, "profile": profile})


@login_required
@_admin_required
def manage_users(request):
    """List all users with filter by role; admins can activate, deactivate, delete."""
    from django.core.paginator import Paginator

    qs = CustomUser.objects.all().order_by("-date_joined")
    role_filter = request.GET.get("role")
    if role_filter and role_filter in dict(CustomUser.Role.choices):
        qs = qs.filter(role=role_filter)

    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            models.Q(username__icontains=search)
            | models.Q(email__icontains=search)
            | models.Q(first_name__icontains=search)
            | models.Q(last_name__icontains=search)
        )

    paginator = Paginator(qs, 20)
    try:
        page_num = int(request.GET.get("page", 1))
    except ValueError:
        page_num = 1
    page_obj = paginator.get_page(page_num)

    return render(
        request,
        "dashboard/manage_users.html",
        {
            "page_obj": page_obj,
            "role_filter": role_filter,
            "search": search,
            "role_choices": CustomUser.Role.choices,
        },
    )


@login_required
@_admin_required
@require_POST
def user_activate(request, pk):
    """Activate a user account."""
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.warning(request, "You cannot change your own status.")
        return redirect("dashboard:manage_users")
    if user.is_active:
        messages.info(request, f"{user.username} is already active.")
    else:
        user.is_active = True
        user.save()
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.USER_UPDATED,
            message=f"User {user.username} activated.",
        )
        messages.success(request, f"{user.username} has been activated.")
    return redirect("dashboard:manage_users")


@login_required
@_admin_required
@require_POST
def user_deactivate(request, pk):
    """Deactivate a user account."""
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.warning(request, "You cannot deactivate your own account.")
        return redirect("dashboard:manage_users")
    if not user.is_active:
        messages.info(request, f"{user.username} is already inactive.")
    else:
        user.is_active = False
        user.save()
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.USER_UPDATED,
            message=f"User {user.username} deactivated.",
        )
        messages.success(request, f"{user.username} has been deactivated.")
    return redirect("dashboard:manage_users")


@login_required
@_admin_required
@require_POST
def user_delete(request, pk):
    """Delete a user account."""
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.warning(request, "You cannot delete your own account.")
        return redirect("dashboard:manage_users")
    if user.is_administrator and CustomUser.objects.filter(role=CustomUser.Role.ADMIN, is_active=True).count() <= 1:
        messages.warning(request, "Cannot delete the last active administrator.")
        return redirect("dashboard:manage_users")
    username = user.username
    user.delete()
    AuditLog.objects.create(
        user=request.user,
        action=AuditLog.Action.OTHER,
        message=f"User {username} deleted.",
    )
    messages.success(request, f"User {username} has been deleted.")
    return redirect("dashboard:manage_users")


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard: analytics, approve provider applications, audit."""
    template_name = "dashboard/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_patients"] = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).count()
        context["total_providers"] = CustomUser.objects.filter(role=CustomUser.Role.PROVIDER).count()
        context["pending_providers"] = ProviderProfile.objects.filter(
            approval_status=ProviderProfile.ApprovalStatus.PENDING
        ).select_related("user")
        context["total_appointments"] = Appointment.objects.count()
        context["appointments_by_status"] = (
            Appointment.objects.values("status").annotate(count=Count("id")).order_by("-count")
        )
        context["total_consultations"] = Consultation.objects.count()
        context["total_prescriptions"] = Prescription.objects.count()
        return context


class MedicalDirectorDashboardView(AdminRequiredMixin, TemplateView):
    """Medical Director dashboard: analytics, approve provider applications, audit."""
    template_name = "dashboard/medical_director_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_patients"] = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).count()
        context["total_providers"] = CustomUser.objects.filter(role=CustomUser.Role.PROVIDER).count()
        context["pending_providers"] = ProviderProfile.objects.filter(
            approval_status=ProviderProfile.ApprovalStatus.PENDING
        ).select_related("user")
        context["total_appointments"] = Appointment.objects.count()
        context["appointments_by_status"] = (
            Appointment.objects.values("status").annotate(count=Count("id")).order_by("-count")
        )
        context["total_consultations"] = Consultation.objects.count()
        context["total_prescriptions"] = Prescription.objects.count()
        return context

    def dispatch(self, request, *args, **kwargs):
        # Ensure only medical directors can access this dashboard (in addition to admin requirement)
        if request.user.username != "medical_director":
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Medical Director access required.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def providers_list(request):
    """List all healthcare providers with filtering and search."""
    if not request.user.is_administrator:
        messages.warning(request, "Admin access required.")
        return redirect("dashboard:home")
    
    providers = ProviderProfile.objects.select_related("user").all()
    status_filter = request.GET.get("status")
    search = request.GET.get("search", "")
    
    if status_filter:
        providers = providers.filter(approval_status__iexact=status_filter.upper())
    
    if search:
        providers = providers.filter(
            models.Q(user__username__icontains=search) |
            models.Q(user__email__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search) |
            models.Q(specialization__icontains=search)
        )
    
    total_providers = ProviderProfile.objects.count()
    pending_count = ProviderProfile.objects.filter(
        approval_status=ProviderProfile.ApprovalStatus.PENDING
    ).count()
    
    context = {
        "providers": providers,
        "total_providers": total_providers,
        "pending_count": pending_count,
        "status_filter": status_filter,
        "search": search,
    }
    return render(request, "dashboard/providers.html", context)


def doctors_list(request):
    """Public list of approved healthcare providers for patients to browse."""
    # Get only approved providers
    providers = ProviderProfile.objects.filter(
        approval_status=ProviderProfile.ApprovalStatus.APPROVED
    ).select_related("user").order_by("user__first_name", "user__last_name")
    
    # Filter by specialization if provided
    specialization = request.GET.get("specialization", "")
    if specialization:
        providers = providers.filter(specialization__icontains=specialization)
    
    # Get unique specializations for filter dropdown
    specializations = ProviderProfile.objects.filter(
        approval_status=ProviderProfile.ApprovalStatus.APPROVED
    ).values_list("specialization", flat=True).distinct().order_by("specialization")
    
    context = {
        "providers": providers,
        "specializations": specializations,
        "selected_specialization": specialization,
    }
    return render(request, "dashboard/doctors.html", context)
