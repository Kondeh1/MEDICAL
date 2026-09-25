from django.urls import path
from . import views

app_name = "prescriptions"

urlpatterns = [
    path("", views.PrescriptionListView.as_view(), name="list"),
    path("create/", views.create_prescription, name="create"),
    path("<int:pk>/", views.PrescriptionDetailView.as_view(), name="detail"),
    path("<int:prescription_id>/download/<str:format>/", views.download_prescription, name="download"),
]
