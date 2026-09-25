"""
WebSocket routing configuration for real-time messaging and WebRTC signaling.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat messaging
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    # Call room WebRTC signaling (room_name can be UUID or alphanumeric)
    re_path(r'ws/call/(?P<room_name>[\w-]+)/$', consumers.CallConsumer.as_asgi()),
    # General notifications endpoint
    re_path(r'ws/call/notifications/$', consumers.CallConsumer.as_asgi()),
    # Old consultation consumer removed
    re_path(r'ws/consultation_call/(?P<consultation_id>\d+)/$', consumers.ConsultationCallConsumer.as_asgi()),
]
