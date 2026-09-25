from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("doctors/", views.doctors_list, name="doctors"),
    path("patient/", views.PatientDashboardView.as_view(), name="patient_dashboard"),
    path("provider/", views.ProviderDashboardView.as_view(), name="provider_dashboard"),
    # App admin dashboard at /app-admin/ (Django admin stays at /admin/)
    path("app-admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("app-admin/users/", views.manage_users, name="manage_users"),
    path("app-admin/users/<int:pk>/activate/", views.user_activate, name="user_activate"),
    path("app-admin/users/<int:pk>/deactivate/", views.user_deactivate, name="user_deactivate"),
    path("app-admin/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("app-admin/provider/<int:pk>/", views.provider_application_detail, name="provider_application_detail"),
    path("app-admin/provider/<int:pk>/credentials/", views.provider_credentials_detail, name="provider_credentials_detail"),
    path("app-admin/approve-provider/<int:pk>/", views.approve_provider, name="approve_provider"),
    path("app-admin/reject-provider/<int:pk>/", views.reject_provider, name="reject_provider"),
    path("app-admin/providers/", views.providers_list, name="providers"),
    path("app-admin/medical-director/", views.MedicalDirectorDashboardView.as_view(), name="medical_director_dashboard"),
]
