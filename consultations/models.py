"""
Consultation: one per appointment when provider starts the session.
Chat messages stored in messaging.Message linked to consultation or appointment.
"""
from django.conf import settings
from django.db import models


class Consultation(models.Model):
    """A consultation session linked to an appointment (chat-based simulation)."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ENDED = "ENDED", "Ended"

    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="consultation",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Provider notes after consultation")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"

    def __str__(self):
        return f"Consultation for appointment #{self.appointment_id} ({self.get_status_display()})"

    @property
    def patient(self):
        return self.appointment.patient

    @property
    def provider(self):
        return self.appointment.provider
