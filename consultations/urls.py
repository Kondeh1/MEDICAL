from django.urls import path
from . import views

app_name = "consultations"

urlpatterns = [
    path("", views.ConsultationListView.as_view(), name="list"),
    path("dashboard/", views.consultation_dashboard, name="dashboard"),
    path("<int:pk>/", views.ConsultationDetailView.as_view(), name="detail"),
    path("room/<int:pk>/", views.consultation_room, name="room"),
]
