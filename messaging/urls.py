from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("<int:pk>/", views.thread_view, name="thread"),
    path("<int:pk>/call/initiate/<str:call_type>/", views.initiate_call, name="initiate_call"),
    path("call/<str:room_id>/", views.call_room, name="call_room"),
    path("call/<str:room_id>/end/", views.end_call, name="end_call"),
    path("call/<int:call_id>/missed/", views.mark_call_missed, name="mark_call_missed"),
    path("call/<int:call_id>/decline/", views.decline_call, name="decline_call"),
    path("call/<int:call_id>/status/", views.update_call_status, name="update_call_status"),
    path("prescription/<int:prescription_id>/download/<str:format>/", views.download_prescription, name="download_prescription"),
    path("api/scheduled-calls/", views.get_scheduled_calls, name="get_scheduled_calls"),
    path("api/scheduled-call/<int:call_id>/start/", views.start_scheduled_call, name="start_scheduled_call"),
    path("api/user-status/<int:user_id>/", views.get_user_status, name="get_user_status"),
    path("notifications/", views.get_notifications, name="get_notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/clear/", views.clear_notifications, name="clear_notifications"),
    path("scheduled-calls/check/", views.trigger_scheduled_calls_check, name="trigger_scheduled_calls_check"),
]
