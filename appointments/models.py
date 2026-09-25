"""
Appointment: patient requests a slot; provider accepts/rejects.
Availability is stored as ProviderAvailability (reusable slots).
"""
from django.conf import settings
from django.db import models


class ProviderAvailability(models.Model):
    """Recurring or one-off time slots when a provider is available."""

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availability_slots",
        limit_choices_to={"role": "PROVIDER"},
    )
    day_of_week = models.PositiveSmallIntegerField(
        help_text="0=Monday, 6=Sunday",
        null=True,
        blank=True,
    )
    date = models.DateField(null=True, blank=True, help_text="Specific date override (optional)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Provider availability"
        verbose_name_plural = "Provider availabilities"
        ordering = ["day_of_week", "start_time"]

    DAYS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    def get_day_display(self):
        return self.DAYS.get(self.day_of_week, str(self.day_of_week)) if self.day_of_week is not None else (str(self.date) if self.date else "")

    def __str__(self):
        day = self.DAYS.get(self.day_of_week, str(self.date)) if self.day_of_week is not None else str(self.date)
        return f"{self.provider.get_full_name()}: {day} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """A booked appointment between patient and provider."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    class SicknessType(models.TextChoices):
        GENERAL = "general", "General / Not Sure"
        CARDIOLOGY = "cardiology", "Heart & Cardiovascular"
        DERMATOLOGY = "dermatology", "Skin, Hair & Nails"
        ENDOCRINOLOGY = "endocrinology", "Diabetes & Hormonal"
        ENT = "ent", "Ear, Nose & Throat"
        GASTROENTEROLOGY = "gastroenterology", "Digestive & Stomach"
        GYNECOLOGY = "gynecology", "Women's Health & Gynecology"
        MENTAL_HEALTH = "mental_health", "Mental Health & Psychiatry"
        NEUROLOGY = "neurology", "Brain & Nervous System"
        ONCOLOGY = "oncology", "Cancer & Oncology"
        OPHTHALMOLOGY = "ophthalmology", "Eye & Vision"
        ORTHOPEDICS = "orthopedics", "Bones, Joints & Muscles"
        PEDIATRICS = "pediatrics", "Children's Health"
        PULMONOLOGY = "pulmonology", "Lungs & Respiratory"
        UROLOGY = "urology", "Urinary & Kidney"
        OTHER = "other", "Other"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments_as_patient",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments_as_provider",
    )
    sickness_type = models.CharField(
        max_length=50,
        choices=SicknessType.choices,
        default=SicknessType.GENERAL,
        help_text="Type of condition to match with the right specialist.",
    )
    sickness_other = models.CharField(
        max_length=255,
        blank=True,
        help_text="Describe the condition when 'Other' is selected.",
    )
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-start_time"]
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"{self.patient.get_full_name()} with {self.provider.get_full_name()} on {self.date} ({self.get_status_display()})"
