# Signals to automatically create scheduled calls when appointments are confirmed
from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import Conversation, ScheduledCall, Message
from django.utils import timezone
import uuid


@receiver(post_save, sender=Appointment)
def create_conversation_for_confirmed_appointment(sender, instance, created, **kwargs):
    # Create conversation when appointment is confirmed
    if (created or kwargs.get('update_fields') is None or 'status' in kwargs.get('update_fields', set())) and instance.status == 'CONFIRMED':
        Conversation.objects.get_or_create(
            appointment=instance,
            defaults={'patient': instance.patient, 'provider': instance.provider}
        )


@receiver(post_save, sender=Appointment)
def create_scheduled_call_for_confirmed_appointment(sender, instance, created, **kwargs):
    # Create scheduled call when appointment is confirmed
    if (created or kwargs.get('update_fields') is None or 'status' in kwargs.get('update_fields', set())) and instance.status == 'CONFIRMED':
        # Check if a scheduled call already exists
        if not ScheduledCall.objects.filter(appointment=instance).exists():
            # Only create scheduled call if both date and start_time are available
            if instance.date and instance.start_time:
                # Calculate the scheduled time based on appointment date and time
                scheduled_datetime = timezone.make_aware(
                    timezone.datetime.combine(instance.date, instance.start_time)
                )
            
            # Create a conversation for this appointment if it doesn't exist
            conversation, _ = Conversation.objects.get_or_create(
                appointment=instance,
                defaults={'patient': instance.patient, 'provider': instance.provider}
            )
            
            # Create the scheduled call
            ScheduledCall.objects.create(
                appointment=instance,
                conversation=conversation,
                scheduled_time=scheduled_datetime,
                call_type=ScheduledCall.CallType.VIDEO,  # Default to video call
                room_id=str(uuid.uuid4())
            )