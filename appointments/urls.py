from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.AppointmentListView.as_view(), name="list"),
    path("book/", views.BookAppointmentView.as_view(), name="book"),
    path("providers-by-sickness/", views.providers_by_sickness, name="providers_by_sickness"),
    path("schedule/", views.ProviderScheduleView.as_view(), name="provider_schedule"),
    path("schedule/add/", views.add_availability, name="add_availability"),
    path("schedule/<int:pk>/delete/", views.delete_availability, name="delete_availability"),
    path("provider/<int:provider_id>/slots/", views.provider_availability_slots, name="provider_slots"),
    path("<int:pk>/", views.AppointmentDetailView.as_view(), name="detail"),
    path("<int:pk>/respond/", views.accept_reject_appointment, name="accept_reject"),
]
