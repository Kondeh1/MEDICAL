"""
Forms for registration, login, and profile editing.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from .models import PatientProfile, ProviderProfile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Base registration: email as optional, role set in view."""

    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


class PatientRegistrationForm(UserCreationForm):
    """Patient sign-up: username, email, name, password."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


class PatientProfileForm(forms.ModelForm):
    """Edit patient profile (medical history, DOB, etc.)."""

    class Meta:
        model = PatientProfile
        fields = (
            "date_of_birth",
            "address",
            "emergency_contact",
            "medical_history_summary",
            "blood_type",
            "allergies",
        )
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "medical_history_summary": forms.Textarea(attrs={"rows": 4}),
            "allergies": forms.Textarea(attrs={"rows": 2}),
        }


class ProviderRegistrationForm(UserCreationForm):
    """Provider sign-up: user fields plus credentials/specialization and document uploads."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    credentials = forms.CharField(max_length=255, required=True)
    specialization = forms.CharField(max_length=255, required=True)
    license_number = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

    # Required document uploads
    professional_licence = forms.FileField(
        required=True,
        help_text="Proof of registration with Medical or Pharmacy Council (PDF or image).",
        widget=forms.FileInput(attrs={"accept": "application/pdf,image/*"}),
    )
    academic_certificates = forms.FileField(
        required=True,
        help_text="Academic qualifications and certificates (PDF or image).",
        widget=forms.FileInput(attrs={"accept": "application/pdf,image/*"}),
    )
    identification_documents = forms.FileField(
        required=True,
        help_text="ID card, passport, or government-issued identification (PDF or image).",
        widget=forms.FileInput(attrs={"accept": "application/pdf,image/*"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )


class ProviderProfileForm(forms.ModelForm):
    """Edit provider profile (credentials, specialization, bio)."""

    class Meta:
        model = ProviderProfile
        fields = ("credentials", "specialization", "license_number", "bio")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class UserProfileForm(forms.ModelForm):
    """Edit user fields: first_name, last_name, email, phone, profile_picture."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "profile_picture")
        widgets = {
            "profile_picture": forms.FileInput(attrs={"accept": "image/*"}),
        }
