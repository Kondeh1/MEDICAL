"""
E-prescription: created by provider for a patient (linked to consultation or appointment).
PrescriptionItem for line items (medication, dosage, instructions).
"""
from django.conf import settings
from django.db import models


class Prescription(models.Model):
    """A prescription issued by a provider to a patient."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions_issued",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"

    def __str__(self):
        return f"Prescription #{self.pk} for {self.patient.get_full_name()} by {self.provider.get_full_name()}"


class PrescriptionItem(models.Model):
    """One medication line on a prescription."""

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items",
    )
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=255, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)

    class Meta:
        verbose_name = "Prescription item"
        verbose_name_plural = "Prescription items"

    def __str__(self):
        return f"{self.medication_name} – {self.dosage}"
