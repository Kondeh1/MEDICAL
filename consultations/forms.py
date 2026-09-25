from django import forms
from .models import Consultation


class ConsultationNotesForm(forms.ModelForm):
    """Provider adds notes when ending consultation."""

    class Meta:
        model = Consultation
        fields = ("notes",)
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}
