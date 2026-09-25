"""
Conversation between one patient and one provider. Optional link to appointment for in-consultation chat.
"""
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """One thread between a patient and a provider; optionally tied to an appointment."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_patient",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_provider",
    )
    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messaging_conversation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"{self.patient.get_full_name()} – {self.provider.get_full_name()}"


class Message(models.Model):
    """A single message in a conversation."""

    class MessageType(models.TextChoices):
        TEXT = "TEXT", "Text Message"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    prescription = models.ForeignKey(
        "prescriptions.Prescription",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class Call(models.Model):
    """Video or audio call between patient and provider in a conversation."""

    class CallType(models.TextChoices):
        VIDEO = "VIDEO", "Video Call"
        AUDIO = "AUDIO", "Audio Call"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONNECTED = "CONNECTED", "Connected"
        ENDED = "ENDED", "Ended"
        MISSED = "MISSED", "Missed"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="calls",
    )
    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calls_made",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calls_received",
    )
    call_type = models.CharField(
        max_length=10,
        choices=CallType.choices,
        default=CallType.VIDEO,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    room_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique room identifier for the call session.",
    )

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Call"
        verbose_name_plural = "Calls"

    def __str__(self):
        return f"{self.call_type} call: {self.caller.username} -> {self.receiver.username} ({self.status})"


class Notification(models.Model):
    """Notification system for incoming calls and other alerts."""
    
    class NotificationType(models.TextChoices):
        CALL_INVITE = "CALL_INVITE", "Call Invite"
        CALL_MISSED = "CALL_MISSED", "Call Missed"
        MESSAGE = "MESSAGE", "Message"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"
        SCHEDULED_CALL = "SCHEDULED_CALL", "Scheduled Call"
        APPOINTMENT_REQUEST = "APPOINTMENT_REQUEST", "Appointment Request"
        APPOINTMENT_APPROVED = "APPOINTMENT_APPROVED", "Appointment Approved"
        APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER", "Appointment Reminder"
        PRESCRIPTION_UPDATE = "PRESCRIPTION_UPDATE", "Prescription Update"
        SCHEDULED_CONSULTATION = "SCHEDULED_CONSULTATION", "Scheduled Consultation"
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    call = models.ForeignKey(
        'Call',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    scheduled_call = models.ForeignKey(
        'ScheduledCall',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    consultation = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Conversation thread this notification belongs to (for MESSAGE notifications).",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.notification_type}: {self.title} for {self.recipient.username}"


class ScheduledCall(models.Model):
    """Scheduled video/audio call linked to an appointment."""

    class CallType(models.TextChoices):
        VIDEO = "VIDEO", "Video Call"
        AUDIO = "AUDIO", "Audio Call"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        NOTIFIED = "NOTIFIED", "Notified"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="scheduled_calls",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="scheduled_calls",
    )
    call_type = models.CharField(
        max_length=10,
        choices=CallType.choices,
        default=CallType.VIDEO,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    scheduled_time = models.DateTimeField()
    notified_at = models.DateTimeField(null=True, blank=True)
    room_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique room identifier for the scheduled call.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_time"]
        verbose_name = "Scheduled Call"
        verbose_name_plural = "Scheduled Calls"

    def __str__(self):
        return f"{self.call_type} call scheduled for {self.appointment} at {self.scheduled_time}"
