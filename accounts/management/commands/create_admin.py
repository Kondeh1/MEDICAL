"""
Create an administrator account for the Telemedical Consultation Platform.
Run: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

# Default credentials (change in production)
DEFAULT_USERNAME = "telemedicine_admin"
DEFAULT_PASSWORD = "Telemed@2025"


class Command(BaseCommand):
    help = "Creates an administrator user with full access"

    def add_arguments(self, parser):
        parser.add_argument("--username", default=DEFAULT_USERNAME, help="Admin username")
        parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Admin password")

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
            self.stdout.write(self.style.SUCCESS(f"Admin user created: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"Admin user updated: {username}"))

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("ADMIN CREDENTIALS")
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Username: {username}")
        self.stdout.write(f"  Password: {password}")
        self.stdout.write("=" * 50)
        self.stdout.write("")
        self.stdout.write("Admin can:")
        self.stdout.write("  - Approve provider accounts (Django admin + dashboard)")
        self.stdout.write("  - Manage users (Django admin /accounts/user/)")
        self.stdout.write("  - View system analytics (Admin dashboard in navbar)")
        self.stdout.write("  - View consultation statistics (Admin dashboard)")
        self.stdout.write("  - Access audit logs (Audit Logs in navbar)")
        self.stdout.write("")
