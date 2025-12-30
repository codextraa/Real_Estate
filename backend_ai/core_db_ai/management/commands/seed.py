from django.core.management.base import BaseCommand
from django.db import transaction
from core_db_ai.models import Property, AIReport
from core_db_ai.factories import AIReportFactory


class Command(BaseCommand):
    help = (
        "Deletes existing AIReports and generates new ones for all existing Properties"
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Deleting existing AI Reports..."))
        deleted_count, _ = AIReport.objects.all().delete()
        self.stdout.write(f"Removed {deleted_count} old reports.")

        all_properties = Property.objects.all()
        total_props = all_properties.count()

        if total_props == 0:
            self.stdout.write(
                self.style.ERROR(
                    "No properties found in the database. Please seed core_db first."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(f"Found {total_props} properties. Starting generation...")
        )

        count = 0
        try:
            with transaction.atomic():
                for prop in all_properties:
                    AIReportFactory(property=prop)
                    count += 1

                    if count % 10 == 0:
                        self.stdout.write(
                            f"Progress: {count}/{total_props} processed..."
                        )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"An error occurred during seeding: {e}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {count} AI reports linked to existing properties."
            )
        )
