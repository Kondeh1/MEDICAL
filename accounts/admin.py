from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import CustomUser, PatientProfile, ProviderProfile
from audit_logs.models import AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role", {"fields": ("role", "phone")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role", "phone")}),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "date_of_birth", "created_at")
    search_fields = ("user__username", "user__email")


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "credentials", "approval_status", "created_at")
    list_filter = ("approval_status",)
    search_fields = ("user__username", "specialization", "credentials")
    readonly_fields = ("professional_licence", "academic_certificates", "identification_documents")

    def save_model(self, request, obj, form, change):
        if change and "approval_status" in form.changed_data:
            if obj.approval_status == ProviderProfile.ApprovalStatus.APPROVED:
                obj.approved_at = timezone.now()
                obj.approved_by = request.user
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.PROVIDER_APPROVED,
                    message=f"Provider {obj.user.username} approved.",
                )
            elif obj.approval_status == ProviderProfile.ApprovalStatus.REJECTED:
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.PROVIDER_REJECTED,
                    message=f"Provider {obj.user.username} rejected.",
                )
        super().save_model(request, obj, form, change)
