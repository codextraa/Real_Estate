import random
from django.core.management.base import BaseCommand
from django.db import transaction
from core_db_ai.models import Property, AIReport, User, ChatSession, ChatMessage
from core_db_ai.factories import AIReportFactory, ChatSessionFactory, ChatMessageFactory


class Command(BaseCommand):
    help = "Seeds AI Reports and Chat Sessions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Cleaning up old AI Reports..."))
        AIReport.objects.all().delete()

        all_properties = Property.objects.all()
        all_users = User.objects.filter(is_staff=False)

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

        self.stdout.write(self.style.WARNING("Cleaning up old Chat data..."))
        ChatSession.objects.all().delete()

        self.stdout.write(self.style.NOTICE("Seeding Chat Sessions..."))

        try:
            with transaction.atomic():
                # Create 20 random chat sessions
                for _ in range(20):
                    session = ChatSessionFactory()

                    # Create a random string of messages (1 to 10)
                    num_messages = random.randint(1, 10)
                    for _ in range(num_messages):
                        # Ensure the user doesn't exceed 10 'user' roles
                        # (handled by our loop and model logic)
                        ChatMessageFactory(session=session)

            self.stdout.write(
                self.style.SUCCESS(f"✅ Created 20 Chat Sessions with random messages.")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Chat seeding failed: {e}"))
