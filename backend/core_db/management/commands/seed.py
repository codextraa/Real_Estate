import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core_db.factories import (
    UserFactory,
    AgentFactory,
    PropertyFactory,
    SuperuserFactory,
    StaffuserFactory,
    FIXED_PASSWORD,
)
from core_db.models import User, Agent, Property


class Command(BaseCommand):
    help = "Seeds the database with test data according to specific constraints."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("--- Starting Database Seeding ---"))

        self.stdout.write("Clearing old data...")
        Property.objects.all().delete()
        Agent.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.stdout.write(self.style.NOTICE("Clean up complete."))

        # --- GROUP CREATION ---

        self.stdout.write("\nCreating user groups...")
        superuser_group, _ = Group.objects.get_or_create(name="Superuser")
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        agent_group, _ = Group.objects.get_or_create(name="Agent")
        default_group, _ = Group.objects.get_or_create(name="Default")
        self.stdout.write(
            self.style.SUCCESS("✅ Groups created: Superuser, Admin, Agent, Default.")
        )

        # --- USER CREATION & ASSIGNMENT ---

        self.stdout.write(
            f"\nCreating fixed-credential users (Password: {FIXED_PASSWORD}):"
        )
        superuser = SuperuserFactory.create()
        superuser.groups.add(superuser_group)
        staffuser = StaffuserFactory.create()
        staffuser.groups.add(admin_group)
        self.stdout.write(self.style.SUCCESS(f"✅ Superuser: superuser@example.com"))
        self.stdout.write(self.style.SUCCESS(f"✅ Staffuser: staffuser@example.com"))

        # Create specific default user
        self.stdout.write("\nCreating specific default user...")
        defaultuser = UserFactory.create(email="defaultuser@example.com")
        defaultuser.groups.add(default_group)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Default user: defaultuser@example.com")
        )

        # Create specific agent user and agent
        self.stdout.write("\nCreating specific agent user and agent...")
        agent_user = UserFactory.create(email="agentuser@example.com", is_agent=True)
        agent1 = AgentFactory.create(user=agent_user)
        agent1.user.groups.add(agent_group)
        self.stdout.write(self.style.SUCCESS(f"✅ Agent user: agentuser@example.com"))

        # Create Basic Users (10)
        self.stdout.write("\nCreating 10 basic users...")
        basic_users = UserFactory.create_batch(10)
        for user in basic_users:
            user.groups.add(default_group)
        self.stdout.write(self.style.SUCCESS("✅ 10 basic users created."))

        # --- AGENT AND PROPERTY CREATION ---

        self.stdout.write("\nCreating 2 specific agents and their properties...")

        # Agent 1 (12 Properties)
        PropertyFactory.create_batch(12, agent=agent1)
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Agent 1 ({agent1.user.email}) created with 12 properties."
            )
        )

        # Agent 2 (6 Properties)
        agent2 = AgentFactory.create()
        agent2.user.groups.add(agent_group)
        PropertyFactory.create_batch(6, agent=agent2)
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Agent 2 ({agent2.user.email}) created with 6 properties."
            )
        )

        # Create 8 extra Agents
        self.stdout.write("\nCreating 8 extra agents...")
        extra_agents = AgentFactory.create_batch(8)
        for agent in extra_agents:
            agent.user.groups.add(agent_group)
        self.stdout.write(self.style.SUCCESS(f"✅ 8 extra agents created."))

        # Assign 12 properties randomly to the 8 extra agents
        self.stdout.write(
            "Assigning 12 properties to each of the 8 extra agents randomly..."
        )

        # Create 12 properties, each assigned to a random agent from the extra agents
        for i in range(12):
            random_agent = random.choice(extra_agents)
            PropertyFactory.create(agent=random_agent)
            self.stdout.write(
                f"  - Property {i+1} created and assigned to {random_agent.company_name}."
            )

        # Verification
        total_properties = Property.objects.count()
        expected_properties = (
            12 + 6 + 12
        )  # Agent 1 (12) + Agent 2 (6) + Random pool (12) = 30

        self.stdout.write(f"\nTotal Agents Created: {Agent.objects.count()}")
        self.stdout.write(
            f"Total Properties Created: {total_properties} (Expected: {expected_properties})"
        )
        self.stdout.write(
            self.style.SUCCESS("--- Database Seeding Finished Successfully! 🚀 ---")
        )
        self.stdout.write(f"Remember the fixed password is: {FIXED_PASSWORD}")
