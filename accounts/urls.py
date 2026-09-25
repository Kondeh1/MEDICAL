from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterPatientView.as_view(), name="register"),
    path("register/patient/", views.RegisterPatientView.as_view(), name="register_patient"),
    path("register/provider/", views.RegisterProviderView.as_view(), name="register_provider"),
    path("pending-approval/", views.provider_pending_approval, name="provider_pending_approval"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/medical-director/", views.MedicalDirectorProfileView.as_view(), name="medical_director_profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("password-change/", views.change_password, name="password_change"),
    # Password reset URLs
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url="/accounts/password-reset/done/"
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"
    ), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url="/accounts/password-reset-complete/"
    ), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"
    ), name="password_reset_complete"),
]
