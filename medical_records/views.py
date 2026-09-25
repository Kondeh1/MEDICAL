"""
List medical records (patient sees own; provider sees created). Create (provider).
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView

from .models import MedicalRecord
from .forms import MedicalRecordForm

User = get_user_model()


class MedicalRecordListView(LoginRequiredMixin, ListView):
    """Patient sees own records; provider sees those they created; admin sees all."""
    model = MedicalRecord
    template_name = "medical_records/list.html"
    context_object_name = "records"
    paginate_by = 15

    def get_queryset(self):
        qs = MedicalRecord.objects.select_related("patient", "provider")
        if self.request.user.is_patient:
            return qs.filter(patient=self.request.user)
        if self.request.user.is_provider:
            return qs.filter(provider=self.request.user)
        if self.request.user.is_administrator:
            return qs
        return qs.none()


class MedicalRecordDetailView(LoginRequiredMixin, DetailView):
    model = MedicalRecord
    template_name = "medical_records/detail.html"
    context_object_name = "record"

    def get_queryset(self):
        qs = super().get_queryset().select_related("patient", "provider")
        if self.request.user.is_administrator:
            return qs
        return qs.filter(patient=self.request.user) | qs.filter(provider=self.request.user)


def create_medical_record(request):
    if not request.user.is_authenticated or not request.user.is_provider:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if hasattr(request.user, "provider_profile") and not request.user.provider_profile.is_approved:
        return redirect("accounts:provider_pending_approval")

    patient_queryset = User.objects.filter(role=User.Role.PATIENT).order_by("username")
    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        form.fields["patient"].queryset = patient_queryset
        if form.is_valid():
            record = form.save(commit=False)
            record.provider = request.user
            record.save()
            from django.contrib import messages
            messages.success(request, "Medical record added.")
            return redirect("medical_records:list")
    else:
        form = MedicalRecordForm()
        form.fields["patient"].queryset = patient_queryset
    return render(request, "medical_records/create.html", {"form": form})
