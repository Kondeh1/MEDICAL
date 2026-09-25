"""
Audit log for security and compliance: who did what, when.
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable log entry for important actions."""

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        USER_CREATED = "USER_CREATED", "User created"
        USER_UPDATED = "USER_UPDATED", "User updated"
        PROVIDER_APPROVED = "PROVIDER_APPROVED", "Provider approved"
        PROVIDER_REJECTED = "PROVIDER_REJECTED", "Provider rejected"
        APPOINTMENT_CREATED = "APPOINTMENT_CREATED", "Appointment created"
        APPOINTMENT_UPDATED = "APPOINTMENT_UPDATED", "Appointment updated"
        CONSULTATION_STARTED = "CONSULTATION_STARTED", "Consultation started"
        CONSULTATION_ENDED = "CONSULTATION_ENDED", "Consultation ended"
        PRESCRIPTION_CREATED = "PRESCRIPTION_CREATED", "Prescription created"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=50, choices=Action.choices, default=Action.OTHER)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.created_at}"
