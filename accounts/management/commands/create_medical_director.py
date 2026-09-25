"""
Create a medical director account for the Telemedical Consultation Platform.
Medical directors are redirected to the admin dashboard on login.
Run: python manage.py create_medical_director
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

# Default credentials (change in production)
DEFAULT_USERNAME = "medical_director"
DEFAULT_PASSWORD = "MedicalDir@2025"


class Command(BaseCommand):
    help = "Creates a medical director user (admin role) with access to admin dashboard"

    def add_arguments(self, parser):
        parser.add_argument("--username", default=DEFAULT_USERNAME, help="Medical director username")
        parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Medical director password")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Medical director user created: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"Medical director user updated: {username}"))

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("MEDICAL DIRECTOR CREDENTIALS")
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Username: {username}")
        self.stdout.write(f"  Password: {password}")
        self.stdout.write("=" * 50)
        self.stdout.write("")
        self.stdout.write("On login, medical director is redirected to the admin dashboard.")
        self.stdout.write("")
