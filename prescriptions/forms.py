from django import forms
from .models import Prescription, PrescriptionItem


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ("medication_name", "dosage", "frequency", "duration", "instructions")
        widgets = {
            "instructions": forms.Textarea(attrs={"rows": 2}),
        }


PrescriptionItemFormSet = forms.inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
)


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ("patient", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
