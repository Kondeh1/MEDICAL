"""
Authentication and profile views: login, register (patient/provider), profile edit.
"""
from django.contrib import messages
from django.contrib.auth import login, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView, TemplateView

from .forms import (
    PatientRegistrationForm,
    PatientProfileForm,
    ProviderRegistrationForm,
    ProviderProfileForm,
    UserProfileForm,
)
from .models import PatientProfile, ProviderProfile

User = get_user_model()


class CustomLoginView(LoginView):
    """Login with Django auth; redirect by role after success. Admins go to app dashboard, not Django admin."""
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard:home")

    def get_redirect_url(self):
        """Administrators always go to app admin dashboard, never Django admin or next param."""
        if self.request.user.is_authenticated and getattr(
            self.request.user, "is_administrator", False
        ):
            # Medical director has a specific dashboard
            if self.request.user.username == "medical_director":
                return str(reverse_lazy("dashboard:medical_director_dashboard"))
            return str(reverse_lazy("dashboard:admin_dashboard"))
        return super().get_redirect_url()

    def form_valid(self, form):
        """Login user; administrators (including medical_director) go to app admin dashboard."""
        login(self.request, form.get_user())
        redirect_to = self.get_redirect_url() or self.get_success_url()
        return redirect(redirect_to)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = settings
        return context


class CustomLogoutView(LogoutView):
    """Logout and redirect to login."""
    next_page = reverse_lazy("accounts:login")


class RegisterPatientView(FormView):
    """Patient registration: create User (PATIENT) + PatientProfile."""
    template_name = "accounts/register_patient.html"
    form_class = PatientRegistrationForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.PATIENT
        user.save()
        PatientProfile.objects.get_or_create(user=user)
        
        # Login with explicit backend
        from django.contrib.auth import get_backends
        backend = get_backends()[0]  # Use the first backend (ModelBackend)
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(self.request, user)
        
        messages.success(self.request, "Account created. Please complete your profile.")
        return redirect(self.success_url)


class RegisterProviderView(FormView):
    """Provider registration: create User (PROVIDER) + ProviderProfile (PENDING)."""
    template_name = "accounts/register_provider.html"
    form_class = ProviderRegistrationForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.PROVIDER
        user.save()
        profile, _ = ProviderProfile.objects.update_or_create(
            user=user,
            defaults={
                "credentials": form.cleaned_data["credentials"],
                "specialization": form.cleaned_data["specialization"],
                "license_number": form.cleaned_data.get("license_number", ""),
                "bio": form.cleaned_data.get("bio", ""),
                "approval_status": ProviderProfile.ApprovalStatus.PENDING,
            },
        )
        # Save uploaded documents
        profile.professional_licence = form.cleaned_data.get("professional_licence")
        profile.academic_certificates = form.cleaned_data.get("academic_certificates")
        profile.identification_documents = form.cleaned_data.get("identification_documents")
        profile.save()
        
        # Login with explicit backend
        from django.contrib.auth import get_backends
        backend = get_backends()[0]  # Use the first backend (ModelBackend)
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(self.request, user)
        
        messages.success(
            self.request,
            "Provider account created. Your account is pending admin approval.",
        )
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """Log form errors for debugging."""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Provider registration form errors: {form.errors}")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ProviderPendingApprovalView(TemplateView):
    """Shown when provider is not yet approved."""
    template_name = "accounts/provider_pending_approval.html"


def provider_pending_approval(request):
    """Simple view for redirect target."""
    return render(request, "accounts/provider_pending_approval.html")


class ProfileView(TemplateView):
    """Show current user profile (role-specific). Redirects medical director to enhanced profile."""
    template_name = "accounts/profile.html"

    def get(self, request, *args, **kwargs):
        # Redirect medical director (admin with specific username) to enhanced profile
        if request.user.is_administrator and request.user.username == "medical_director":
            return redirect("accounts:medical_director_profile")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context


class ProfileEditView(UpdateView):
    """Edit user + role-specific profile."""
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_class(self):
        return UserProfileForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only inject a fresh sub-form if one isn't already in context (POST re-render passes bound forms)
        if self.request.user.is_patient and hasattr(self.request.user, "patient_profile"):
            if "patient_form" not in context:
                context["patient_form"] = PatientProfileForm(instance=self.request.user.patient_profile)
        elif self.request.user.is_provider and hasattr(self.request.user, "provider_profile"):
            if "provider_form" not in context:
                context["provider_form"] = ProviderProfileForm(instance=self.request.user.provider_profile)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        # Build role-specific sub-form with submitted data
        if request.user.is_patient and hasattr(request.user, "patient_profile"):
            sub_form = PatientProfileForm(request.POST, instance=request.user.patient_profile)
        elif request.user.is_provider and hasattr(request.user, "provider_profile"):
            sub_form = ProviderProfileForm(request.POST, request.FILES, instance=request.user.provider_profile)
        else:
            sub_form = None

        sub_valid = sub_form.is_valid() if sub_form else True

        if form.is_valid() and sub_valid:
            form.save()
            if sub_form:
                sub_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect(self.success_url)

        # Re-render: pass bound sub-form so errors show
        extra = {}
        if request.user.is_patient:
            extra["patient_form"] = sub_form
        elif request.user.is_provider:
            extra["provider_form"] = sub_form
        context = self.get_context_data(form=form, **extra)
        return render(request, self.template_name, context)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['files'] = self.request.FILES
        return kwargs


class MedicalDirectorProfileView(TemplateView):
    """Show medical director profile with enhanced design."""
    template_name = "accounts/medical_director_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context


def change_password(request):
    """Change password for current user."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Password updated.")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})
