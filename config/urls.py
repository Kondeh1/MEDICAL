"""
Root URL configuration for Telemedical Consultation Platform.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("appointments/", include("appointments.urls")),
    path("consultations/", include("consultations.urls")),
    path("prescriptions/", include("prescriptions.urls")),
    path("medical-records/", include("medical_records.urls")),
    path("messages/", include("messaging.urls")),
    path("audit-logs/", include("audit_logs.urls")),
]

# Add allauth URLs if available
try:
    import allauth.urls  # noqa: F401
    urlpatterns.append(path("auth/", include("allauth.urls")))
except ImportError:
    pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
