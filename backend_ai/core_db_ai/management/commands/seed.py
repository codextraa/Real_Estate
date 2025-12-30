from django.core.management.base import BaseCommand
from django.db import transaction
from core_db_ai.models import Property, AIReport, User
from core_db_ai.factories import AIReportFactory


class Command(BaseCommand):
    help = "Seeds AI Reports by linking properties to random users"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Cleaning up old AI Reports..."))
        AIReport.objects.all().delete()

        all_properties = Property.objects.all()
        all_users = User.objects.all()

        if not all_properties.exists() or not all_users.exists():
            self.stdout.write(
                self.style.ERROR(
                    "❌ Error: You need both Properties and Users in the DB to seed reports."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Seeding reports for {all_properties.count()} properties..."
            )
        )

        count = 0
        try:
            with transaction.atomic():
                for prop in all_properties:
                    AIReportFactory(property=prop)
                    count += 1

                    if count % 10 == 0:
                        self.stdout.write(
                            f"Processed {count}/{all_properties.count()}..."
                        )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Seeding failed: {e}"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {count} AI reports successfully.")
        )
