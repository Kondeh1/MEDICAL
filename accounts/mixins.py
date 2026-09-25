"""
Role-based access control mixins for class-based views.
Use with LoginRequiredMixin; apply role mixin after it.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class PatientRequiredMixin(LoginRequiredMixin):
    """Restrict view to users with role PATIENT."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_patient:
            raise PermissionDenied("This area is for patients only.")
        return super().dispatch(request, *args, **kwargs)


class ProviderRequiredMixin(LoginRequiredMixin):
    """Restrict view to users with role PROVIDER. Optionally require approved profile."""

    require_approved = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_provider:
            raise PermissionDenied("This area is for healthcare providers only.")
        if self.require_approved and hasattr(request.user, "provider_profile"):
            if not request.user.provider_profile.is_approved:
                return redirect("accounts:provider_pending_approval")
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Restrict view to users with role ADMIN."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_administrator:
            raise PermissionDenied("This area is for administrators only.")
        return super().dispatch(request, *args, **kwargs)


class ProviderOrAdminRequiredMixin(LoginRequiredMixin):
    """Allow both PROVIDER (approved) and ADMIN."""

    require_approved = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_administrator:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_provider:
            raise PermissionDenied("Access denied.")
        if self.require_approved and hasattr(request.user, "provider_profile"):
            if not request.user.provider_profile.is_approved:
                return redirect("accounts:provider_pending_approval")
        return super().dispatch(request, *args, **kwargs)
