from django.urls import path
from . import views

app_name = "medical_records"

urlpatterns = [
    path("", views.MedicalRecordListView.as_view(), name="list"),
    path("create/", views.create_medical_record, name="create"),
    path("<int:pk>/", views.MedicalRecordDetailView.as_view(), name="detail"),
]
