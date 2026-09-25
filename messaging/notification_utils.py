"""
Notification utility functions for creating and sending various types of notifications
"""
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification, Call, ScheduledCall

User = get_user_model()

def create_call_notification(recipient, caller, call_type, room_id, call_id, notification_type="CALL_INVITE"):
    """Create and send call notification"""
    title = f"{'Video' if call_type == 'VIDEO' else 'Audio'} Call from {caller.get_full_name() or caller.username}"
    message = f"You have an incoming {'video' if call_type == 'VIDEO' else 'audio'} call"
    
    if notification_type == "CALL_MISSED":
        title = f"Missed Call from {caller.get_full_name() or caller.username}"
        message = f"You missed a {'video' if call_type == 'VIDEO' else 'audio'} call"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        call_id=call_id
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def create_message_notification(recipient, sender, conversation, message_content):
    """Create and send message notification"""
    title = f"New message from {sender.get_full_name() or sender.username}"
    message = message_content[:100] + "..." if len(message_content) > 100 else message_content
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="MESSAGE",
        title=title,
        message=message,
        conversation=conversation,
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def create_prescription_notification(recipient, provider, prescription, notification_type="PRESCRIPTION"):
    """Create and send prescription notification"""
    if notification_type == "PRESCRIPTION":
        title = f"New Prescription from {provider.get_full_name() or provider.username}"
        message = f"You have received a new prescription with {prescription.items.count()} medication(s)"
    elif notification_type == "PRESCRIPTION_UPDATE":
        title = f"Prescription Updated by {provider.get_full_name() or provider.username}"
        message = f"Your prescription has been updated"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        prescription=prescription
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def create_scheduled_call_notification(recipient, scheduled_call):
    """Create and send scheduled call notification"""
    call_type = "Video" if scheduled_call.call_type == "VIDEO" else "Audio"
    title = f"Upcoming {call_type} Call"
    message = f"Your {call_type.lower()} call is scheduled for {scheduled_call.scheduled_time.strftime('%B %d, %Y at %I:%M %p')}"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="SCHEDULED_CALL",
        title=title,
        message=message,
        scheduled_call=scheduled_call
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def create_appointment_reminder(recipient, appointment):
    """Create and send appointment reminder notification"""
    title = "Appointment Reminder"
    message = f"Your appointment with {appointment.provider.get_full_name() or appointment.provider.username} is scheduled for {appointment.date.strftime('%B %d, %Y')} at {appointment.start_time.strftime('%I:%M %p')}"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="APPOINTMENT_REMINDER",
        title=title,
        message=message,
        appointment=appointment
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def create_scheduled_consultation_notification(recipient, consultation):
    """Create and send scheduled consultation notification"""
    title = "Scheduled Consultation"
    message = f"Your consultation is scheduled for {consultation.scheduled_time.strftime('%B %d, %Y at %I:%M %p')}"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="SCHEDULED_CONSULTATION",
        title=title,
        message=message,
        consultation=consultation
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification

def send_websocket_notification(user_id, notification):
    """Send notification via WebSocket to specific user"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'notification_type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.is_read
                }
            }
        )
    except Exception as e:
        # Log error but don't fail the notification creation
        print(f"Failed to send WebSocket notification: {e}")

def get_unread_notification_count(user):
    """Get count of unread notifications for a user"""
    return Notification.objects.filter(recipient=user, is_read=False).count()

def mark_all_notifications_read(user):
    """Mark all notifications as read for a user"""
    Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)


def create_appointment_approval_notification(recipient, provider, appointment):
    """Create and send appointment approval notification with scheduled time"""
    title = f"Appointment Approved with {provider.get_full_name() or provider.username}"
    message = f"Your appointment on {appointment.date.strftime('%B %d, %Y')} has been approved and scheduled for {appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}"
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="APPOINTMENT_APPROVED",
        title=title,
        message=message,
        appointment=appointment
    )
    
    # Send WebSocket notification
    send_websocket_notification(recipient.id, notification)
    return notification


def create_appointment_request_notification(recipient, patient, provider, appointment):
    """Create and send notification when a patient requests an appointment."""
    # appointment.start_time/end_time are typically set by the patient from provider availability.
    if appointment.start_time and appointment.end_time:
        time_part = f"{appointment.start_time.strftime('%I:%M %p')} - {appointment.end_time.strftime('%I:%M %p')}"
    else:
        time_part = "at a time to be scheduled"

    title = f"New appointment request from {patient.get_full_name() or patient.username}"
    message = (
        f"You have a new appointment request for {appointment.date.strftime('%B %d, %Y')} "
        f"({time_part})."
    )

    notification = Notification.objects.create(
        recipient=recipient,
        notification_type="APPOINTMENT_REQUEST",
        title=title,
        message=message,
        appointment=appointment,
    )

    send_websocket_notification(recipient.id, notification)
    return notification