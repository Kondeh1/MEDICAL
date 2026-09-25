"""
Management command to create scheduled calls for confirmed appointments.
Run this command periodically (e.g., every hour) to schedule calls for upcoming appointments.
"""
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import Appointment
from messaging.models import Conversation, ScheduledCall


class Command(BaseCommand):
    help = "Create scheduled calls for confirmed appointments"

    def handle(self, *args, **options):
        # Get confirmed appointments that are coming up in the next 24 hours
        now = timezone.now()
        tomorrow = now + timedelta(hours=24)
        
        appointments = Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            date__gte=now.date(),
            date__lte=tomorrow.date(),
        ).select_related('patient', 'provider')
        
        created_count = 0
        
        for appointment in appointments:
            # Check if a scheduled call already exists for this appointment
            existing_call = ScheduledCall.objects.filter(
                appointment=appointment,
                status__in=[
                    ScheduledCall.Status.SCHEDULED,
                    ScheduledCall.Status.NOTIFIED
                ]
            ).first()
            
            if existing_call:
                continue
            
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                patient=appointment.patient,
                provider=appointment.provider,
                defaults={'appointment': appointment}
            )
            
            # Create scheduled time (combine date and start_time)
            scheduled_time = timezone.make_aware(
                datetime.combine(appointment.date, appointment.start_time)
            )
            
            # Create scheduled call (default to VIDEO call)
            scheduled_call = ScheduledCall.objects.create(
                appointment=appointment,
                conversation=conversation,
                call_type=ScheduledCall.CallType.VIDEO,
                scheduled_time=scheduled_time,
                room_id=str(uuid.uuid4()),
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created scheduled call for appointment {appointment.id} at {scheduled_time}"
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nTotal scheduled calls created: {created_count}")
        )
