from django import forms
from .models import Appointment, ProviderAvailability


class BookAppointmentForm(forms.ModelForm):
    """Patient books an appointment: sickness type, provider, date, time, reason."""

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset is not None and "provider" in self.fields:
            self.fields["provider"].queryset = queryset
        if self.is_bound:
            for name in self.errors:
                if name not in self.fields:
                    continue
                field = self.fields[name]
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing} is-invalid".strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("sickness_type") == "other" and not cleaned.get("sickness_other", "").strip():
            self.add_error("sickness_other", "Please describe your condition when selecting 'Other'.")
        return cleaned

    class Meta:
        model = Appointment
        fields = ("sickness_type", "sickness_other", "provider", "date", "start_time", "end_time", "reason")
        widgets = {
            "sickness_type": forms.Select(attrs={"class": "form-select", "id": "id_sickness_type"}),
            "sickness_other": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_sickness_other",
                "placeholder": "e.g. Migraine, Back pain, Fever...",
                "maxlength": "255",
            }),
            "provider": forms.Select(attrs={"class": "form-select", "id": "id_provider"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control", "id": "id_date"}),
            "start_time": forms.TimeInput(attrs={"type": "hidden", "id": "id_start_time"}),
            "end_time": forms.TimeInput(attrs={"type": "hidden", "id": "id_end_time"}),
            "reason": forms.Textarea(attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Briefly describe your symptoms, concerns, or the reason for this visit.",
            }),
        }


class ProviderAvailabilityForm(forms.ModelForm):
    """Provider adds/edits availability slot."""

    DAY_CHOICES = [("", "— Select day —")] + [(i, d) for i, d in enumerate(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )]

    class Meta:
        model = ProviderAvailability
        fields = ("day_of_week", "date", "start_time", "end_time", "is_available")
        widgets = {
            "day_of_week": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["day_of_week"].widget.choices = self.DAY_CHOICES
        self.fields["day_of_week"].required = False
        self.fields["date"].required = False
        self.fields["start_time"].label = "Start time"
        self.fields["end_time"].label = "End time"
        self.fields["day_of_week"].label = "Day of week (recurring)"
        self.fields["date"].label = "Specific date (one-off)"
        self.fields["is_available"].label = "Active"

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("day_of_week") and cleaned.get("day_of_week") != 0 and not cleaned.get("date"):
            raise forms.ValidationError("Provide either a day of week (recurring) or a specific date.")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned


class AppointmentApprovalForm(forms.ModelForm):
    """Provider approves appointment and sets schedule."""
    
    class Meta:
        model = Appointment
        fields = ("start_time", "end_time")
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].required = True
        self.fields["end_time"].required = True
        self.fields["start_time"].label = "Appointment Start Time"
        self.fields["end_time"].label = "Appointment End Time"
