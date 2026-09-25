"""
Management command to check for scheduled calls that should start now and initiate them.
"""
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from messaging.models import ScheduledCall, Call, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check for scheduled calls that should start now and initiate them'

    def handle(self, *args, **options):
        now = timezone.now()
        # Check for calls scheduled within the last minute (in case of delayed execution)
        # and up to 1 minute in the future (to account for any timing differences)
        time_window_start = now - timedelta(minutes=1)
        time_window_end = now + timedelta(minutes=1)
        
        scheduled_calls = ScheduledCall.objects.filter(
            scheduled_time__gte=time_window_start,
            scheduled_time__lte=time_window_end,
            status=ScheduledCall.Status.SCHEDULED
        )

        for scheduled_call in scheduled_calls:
            # Create the actual call
            call = Call.objects.create(
                conversation=scheduled_call.conversation,
                caller=scheduled_call.appointment.provider,  # Provider initiates the call
                receiver=scheduled_call.appointment.patient,  # Patient receives the call
                call_type=scheduled_call.call_type,
                room_id=scheduled_call.room_id,
            )
            
            # Update the scheduled call status
            scheduled_call.status = ScheduledCall.Status.NOTIFIED
            scheduled_call.notified_at = now
            scheduled_call.save()
            
            # Create notification for the patient
            Notification.objects.create(
                recipient=scheduled_call.appointment.patient,
                notification_type=Notification.NotificationType.CALL_INVITE,
                title=f'Scheduled {scheduled_call.call_type} Call',
                message=f'Your appointment with {scheduled_call.appointment.provider.get_full_name() or scheduled_call.appointment.provider.username} is starting now.',
                call=call,
            )
            
            # Also create notification for the provider
            Notification.objects.create(
                recipient=scheduled_call.appointment.provider,
                notification_type=Notification.NotificationType.CALL_INVITE,
                title=f'Scheduled {scheduled_call.call_type} Call',
                message=f'Your appointment with {scheduled_call.appointment.patient.get_full_name() or scheduled_call.appointment.patient.username} is starting now.',
                call=call,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Started scheduled call for appointment {scheduled_call.appointment.id}')
            )

        if not scheduled_calls.exists():
            self.stdout.write('No scheduled calls to initiate.')