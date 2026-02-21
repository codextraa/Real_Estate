from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from core_db_ai.models import User, Agent, Property, AIReport, ChatSession, ChatMessage


class ChatSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="John",
            last_name="Doe",
            slug="john-doe",
        )

        self.agent = Agent.objects.create(
            user=self.user, company_name="Dream Realty", bio="Expert in urban lofts"
        )

        self.property = Property.objects.create(
            agent=self.agent,
            title="Modern Condo",
            description="A beautiful condo in the city center",
            beds=2,
            baths=2,
            price=500000.00,
            area_sqft=1200,
            address="123 Main St",
            slug="modern-condo",
        )

        self.report = AIReport.objects.create(property=self.property, user=self.user)

    def test_chat_session_creation_success(self):
        """Test successful creation of ChatSession."""
        session = ChatSession.objects.create(user=self.user, report=self.report)
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(session.user_message_count, 0)

    def test_chatsession_report_cascade(self):
        """Test that deleting a report deletes its chat sessions."""
        ChatSession.objects.create(user=self.user, report=self.report)
        self.assertEqual(ChatSession.objects.count(), 1)
        self.report.delete()
        self.assertEqual(ChatSession.objects.count(), 0)


class ChatMessageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="John",
            last_name="Doe",
            slug="john-doe",
        )

        self.agent = Agent.objects.create(
            user=self.user, company_name="Dream Realty", bio="Expert in urban lofts"
        )

        self.property = Property.objects.create(
            agent=self.agent,
            title="Modern Condo",
            description="A beautiful condo in the city center",
            beds=2,
            baths=2,
            price=500000.00,
            area_sqft=1200,
            address="123 Main St",
            slug="modern-condo",
        )

        self.report = AIReport.objects.create(property=self.property, user=self.user)

        self.session = ChatSession.objects.create(user=self.user, report=self.report)

    def test_chat_message_creation_success(self):
        """Test successful creation of ChatMessage."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role=ChatMessage.Role.USER,
            content="Hello AI",
            timestamp=timezone.now(),
        )
        self.assertEqual(ChatMessage.objects.count(), 1)
        self.assertEqual(msg.status, ChatMessage.Status.PENDING)

    def test_chatmessage_session_cascade(self):
        """Test that deleting a session deletes all its messages."""
        ChatMessage.objects.create(session=self.session, role="user", content="1")
        ChatMessage.objects.create(session=self.session, role="ai", content="2")

        self.assertEqual(ChatMessage.objects.count(), 2)
        self.session.delete()
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_invalid_role_and_status(self):
        """Test validation for incorrect choices."""
        msg_role = ChatMessage(session=self.session, role="HACKER", content="X")
        with self.assertRaises(ValidationError):
            msg_role.save()

        msg_status = ChatMessage(session=self.session, role="user", status="REJECTED")
        with self.assertRaises(ValidationError):
            msg_status.save()

    def test_message_ordering(self):
        """Test that messages are returned in chronological order based on timestamp."""
        now = timezone.now()

        msg2 = ChatMessage.objects.create(
            session=self.session,
            role="ai",
            content="Second",
            timestamp=now + timedelta(seconds=10),
        )
        msg1 = ChatMessage.objects.create(
            session=self.session, role="user", content="First", timestamp=now
        )
        msg3 = ChatMessage.objects.create(
            session=self.session,
            role="user",
            content="Third",
            timestamp=now + timedelta(seconds=20),
        )

        messages = ChatMessage.objects.filter(session=self.session)
        self.assertEqual(list(messages), [msg1, msg2, msg3])
