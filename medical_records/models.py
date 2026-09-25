"""
Medical record entry: notes, diagnoses, etc. linked to a patient.
Provider or admin can create; patient can view own.
"""
from django.conf import settings
from django.db import models


class MedicalRecord(models.Model):
    """A medical record entry for a patient (created by provider)."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_records",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_records_created",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_records",
    )
    title = models.CharField(max_length=255)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Medical record"
        verbose_name_plural = "Medical records"

    def __str__(self):
        return f"{self.title} – {self.patient.get_full_name()}"
