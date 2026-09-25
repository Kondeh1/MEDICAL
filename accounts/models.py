"""
Custom User model with role-based access: Patient, Healthcare Provider, Administrator.
Profiles store role-specific data.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


def user_profile_picture_path(instance, filename):
    """Upload path for user profile pictures: profile_pics/{user_id}/{filename}"""
    from django.utils.text import get_valid_filename
    safe_name = get_valid_filename(filename) or "profile.jpg"
    return f"profile_pics/{instance.id}/{safe_name}"


class CustomUser(AbstractUser):
    """User with role. Passwords hashed by Django (PBKDF2)."""

    class Role(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        PROVIDER = "PROVIDER", "Healthcare Provider"
        ADMIN = "ADMIN", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    # Optional: phone for contact
    phone = models.CharField(max_length=20, blank=True)
    # Profile picture
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        blank=True,
        null=True,
        help_text="Profile picture (optional).",
    )
    # Online status tracking
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def get_role_display_name(self):
        return dict(self.Role.choices).get(self.role, self.role)

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN
    
    def update_last_seen(self):
        """Update last seen timestamp and online status."""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.is_online = True
        self.save(update_fields=['last_seen', 'is_online'])
    
    def set_offline(self):
        """Set user as offline."""
        self.is_online = False
        self.save(update_fields=['is_online'])
    
    def get_online_status(self):
        """Get online status with last seen info."""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.is_online:
            return {'status': 'online', 'text': 'Online'}
        
        if self.last_seen:
            time_diff = timezone.now() - self.last_seen
            if time_diff < timedelta(minutes=1):
                return {'status': 'offline', 'text': 'Just now'}
            elif time_diff < timedelta(hours=1):
                minutes = int(time_diff.seconds / 60)
                return {'status': 'offline', 'text': f'Last seen {minutes}m ago'}
            elif time_diff < timedelta(days=1):
                hours = int(time_diff.seconds / 3600)
                return {'status': 'offline', 'text': f'Last seen {hours}h ago'}
            else:
                return {'status': 'offline', 'text': f'Last seen {self.last_seen.strftime("%b %d")}'}
        
        return {'status': 'offline', 'text': 'Offline'}


class PatientProfile(models.Model):
    """Extended profile for patients: medical history summary, DOB, etc."""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    medical_history_summary = models.TextField(
        blank=True,
        help_text="Summary of medical history for providers.",
    )
    blood_type = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"

    def __str__(self):
        return f"Patient profile: {self.user.get_full_name() or self.user.username}"


def _provider_doc_path(instance, filename, prefix):
    """Upload path for provider documents: provider_docs/{user_id}/{prefix}_{filename}"""
    from django.utils.text import get_valid_filename
    safe_name = get_valid_filename(filename) or "document"
    return f"provider_docs/{instance.user_id}/{prefix}_{safe_name}"


def provider_document_path(instance, filename):
    return _provider_doc_path(instance, filename, "licence")


def provider_academic_path(instance, filename):
    return _provider_doc_path(instance, filename, "academic")


def provider_id_path(instance, filename):
    return _provider_doc_path(instance, filename, "id")


class ProviderProfile(models.Model):
    """Extended profile for healthcare providers: credentials, specialization, approval status."""

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    credentials = models.CharField(
        max_length=255,
        help_text="Professional credentials (e.g. MD, MBBS).",
    )
    specialization = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    # Document uploads for credential verification
    professional_licence = models.FileField(
        upload_to=provider_document_path,
        blank=True,
        null=True,
        help_text="Proof of registration with Medical or Pharmacy Council.",
    )
    academic_certificates = models.FileField(
        upload_to=provider_academic_path,
        blank=True,
        null=True,
        help_text="Academic qualifications and certificates.",
    )
    identification_documents = models.FileField(
        upload_to=provider_id_path,
        blank=True,
        null=True,
        help_text="ID card, passport, or other government-issued identification.",
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_providers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Provider Profile"
        verbose_name_plural = "Provider Profiles"

    def __str__(self):
        return f"Provider: {self.user.get_full_name() or self.user.username} ({self.specialization})"

    @property
    def is_approved(self):
        return self.approval_status == self.ApprovalStatus.APPROVED
