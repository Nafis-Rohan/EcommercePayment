from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a default admin (superuser) account for local development."

    def handle(self, *args, **options):
        email = "admin@example.com"
        username = "admin"
        password = "admin12345"

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Admin user '{email}' already exists, skipping."))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created admin user: {email} / {password}"))
