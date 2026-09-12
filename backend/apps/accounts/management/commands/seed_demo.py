from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.items.models import Item

User = get_user_model()


class Command(BaseCommand):
    help = "Create submission-ready TRACK-IT demo accounts and item reports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo accounts and their data first.",
        )

    def handle(self, *args, **options):
        usernames = ["admin1", "student1", "finder1"]
        if options["reset"]:
            User.objects.filter(username__in=usernames).delete()

        admin, _ = User.objects.get_or_create(
            username="admin1",
            defaults={
                "email": "admin@trackit.local",
                "role": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "is_email_verified": True,
            },
        )
        admin.role = "ADMIN"
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_email_verified = True
        admin.set_password("TrackIt@2026")
        admin.save()

        student, _ = User.objects.get_or_create(
            username="student1",
            defaults={
                "email": "student1@gcet.edu.in",
                "role": "STUDENT",
                "college_id": "22CS001",
                "is_email_verified": True,
            },
        )
        student.is_email_verified = True
        student.set_password("TrackIt@2026")
        student.save()

        finder, _ = User.objects.get_or_create(
            username="finder1",
            defaults={
                "email": "finder1@example.com",
                "role": "EXTERNAL_FINDER",
                "is_email_verified": True,
            },
        )
        finder.is_email_verified = True
        finder.set_password("TrackIt@2026")
        finder.save()

        if not Item.objects.filter(
            reporter=student,
            title="Black leather wallet",
            report_type="LOST",
        ).exists():
            Item.objects.create(
                reporter=student,
                report_type="LOST",
                title="Black leather wallet",
                category="Wallet",
                color="Black",
                brand="WildHorn",
                description=(
                    "Black leather wallet containing a college ID "
                    "card and two bank cards."
                ),
                location="Block 5 Auditorium",
                event_date=date.today(),
            )

        if not Item.objects.filter(
            reporter=finder,
            title="Found black leather wallet",
            report_type="FOUND",
        ).exists():
            Item.objects.create(
                reporter=finder,
                report_type="FOUND",
                title="Found black leather wallet",
                category="Wallet",
                color="Black",
                brand="WildHorn",
                description=(
                    "Black leather wallet found beside the seats "
                    "in Block 5 Auditorium."
                ),
                location="Block 5 Auditorium",
                event_date=date.today(),
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready.\n"
                "admin1 / TrackIt@2026\n"
                "student1 / TrackIt@2026\n"
                "finder1 / TrackIt@2026\n"
                "Change these passwords before public deployment."
            )
        )
