from django.contrib import admin
from .models import Appointment, ProviderAvailability


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("provider", "day_of_week", "date", "start_time", "end_time", "is_available")
    list_filter = ("provider",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "provider", "date", "start_time", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("patient__username", "provider__username")
