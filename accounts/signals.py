"""
Create PatientProfile or ProviderProfile when a user is created with the corresponding role.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, PatientProfile, ProviderProfile


@receiver(post_save, sender=CustomUser)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    """Create role-specific profile when user is created (if not already present)."""
    if not created:
        return
    if instance.role == CustomUser.Role.PATIENT:
        PatientProfile.objects.get_or_create(user=instance)
    elif instance.role == CustomUser.Role.PROVIDER:
        ProviderProfile.objects.get_or_create(
            user=instance,
            defaults={
                "approval_status": ProviderProfile.ApprovalStatus.PENDING,
            },
        )
