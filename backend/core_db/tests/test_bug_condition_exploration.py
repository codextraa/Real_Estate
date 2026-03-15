"""
Bug Condition Exploration Test for Cross-Service Integrity Bugfix

This test explores the bug condition where deleting Users, Agents, or Properties
with AI backend references (AIReport, ChatSession, ChatMessage) causes
ForeignKeyViolation errors.

CRITICAL: This test is EXPECTED TO FAIL on unfixed code.
Failure confirms the bug exists and validates the root cause analysis.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""

from core_db.factories import AgentFactory, PropertyFactory, UserFactory
from core_db.models import Agent, AIReport, ChatMessage, ChatSession, Property
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

USER_DETAIL_URL = lambda pk: reverse("user-detail", kwargs={"pk": pk})
AGENT_DETAIL_URL = lambda pk: reverse("agent-detail", kwargs={"pk": pk})
PROPERTY_DETAIL_URL = lambda pk: reverse("property-detail", kwargs={"pk": pk})


class BugConditionExplorationTest(TestCase):
    """
    Property 1: Bug Condition - AI Backend Records Cleanup

    This test verifies that deletion requests for entities with AI backend references
    (AIReport, ChatSession, ChatMessage) complete successfully without ForeignKeyViolation errors.

    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS with ForeignKeyViolation errors
    This failure confirms the bug exists.

    EXPECTED OUTCOME ON FIXED CODE: Test PASSES - all deletions complete successfully
    """

    def setUp(self):
        """Set up test client and authentication"""
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_authenticate(user=self.superuser)

    def test_user_with_aireport_deletion(self):
        """
        Test Case 1: User with AIReport records deletion

        WHEN a User with associated AIReport records is deleted through UserViewSet
        THEN the system should delete all AIReport records (and cascading ChatSession/ChatMessage)
        AND complete the User deletion successfully with status 200

        EXPECTED ON UNFIXED CODE: ForeignKeyViolation on ai_report.user_id
        """
        # Create user with AIReport
        user = UserFactory()
        agent = AgentFactory()
        property_obj = PropertyFactory(agent=agent)

        # Create AIReport referencing the user
        ai_report = AIReport.objects.create(
            user=user, property=property_obj, status=AIReport.Status.COMPLETED
        )

        # Verify setup
        self.assertTrue(AIReport.objects.filter(user=user).exists())

        # Attempt deletion
        url = USER_DETAIL_URL(user.id)
        response = self.client.delete(url)

        # Assertions for FIXED code behavior
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expected 200 OK, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else response.content}",
        )

        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=user.id).exists())

        # Verify AI backend references are cleaned up
        self.assertFalse(
            AIReport.objects.filter(user_id=user.id).exists(),
            "AIReport records should be deleted",
        )

    def test_user_with_chatsession_deletion(self):
        """
        Test Case 2: User with ChatSession records deletion

        WHEN a User with associated ChatSession records is deleted through UserViewSet
        THEN the system should delete all ChatSession records (and cascading ChatMessage)
        AND complete the User deletion successfully with status 200

        EXPECTED ON UNFIXED CODE: ForeignKeyViolation on chat_session.user_id
        """
        # Create user with ChatSession
        user = UserFactory()
        agent = AgentFactory()
        property_obj = PropertyFactory(agent=agent)
        ai_report = AIReport.objects.create(
            user=user, property=property_obj, status=AIReport.Status.COMPLETED
        )

        # Create ChatSession referencing the user
        chat_session = ChatSession.objects.create(
            user=user, report=ai_report, user_message_count=1
        )
        chat_message = ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.Role.USER,
            status=ChatMessage.Status.COMPLETED,
        )

        # Verify setup
        self.assertTrue(ChatSession.objects.filter(user=user).exists())
        self.assertTrue(ChatMessage.objects.filter(session=chat_session).exists())

        # Attempt deletion
        url = USER_DETAIL_URL(user.id)
        response = self.client.delete(url)

        # Assertions for FIXED code behavior
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expected 200 OK, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else response.content}",
        )

        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=user.id).exists())

        # Verify AI backend references are cleaned up
        self.assertFalse(
            ChatSession.objects.filter(user_id=user.id).exists(),
            "ChatSession records should be deleted",
        )
        self.assertFalse(
            ChatMessage.objects.filter(session_id=chat_session.id).exists(),
            "ChatMessage records should be deleted",
        )

    def test_agent_with_property_aireports_deletion(self):
        """
        Test Case 3: Agent with Properties that have AIReport records deletion

        WHEN an Agent with Properties that have AIReport records is deleted through AgentViewSet
        THEN the system should delete all AIReport records for all Properties owned by the Agent
        AND complete the Agent deletion successfully with status 200

        EXPECTED ON UNFIXED CODE: ForeignKeyViolation on ai_report.property_id
        """
        # Create agent with properties that have AIReports
        agent = AgentFactory()
        property1 = PropertyFactory(agent=agent)
        property2 = PropertyFactory(agent=agent)

        user = UserFactory()
        ai_report1 = AIReport.objects.create(
            property=property1, user=user, status=AIReport.Status.COMPLETED
        )
        ai_report2 = AIReport.objects.create(
            property=property2, user=user, status=AIReport.Status.COMPLETED
        )

        # Verify setup
        self.assertEqual(Property.objects.filter(agent=agent).count(), 2)
        self.assertTrue(AIReport.objects.filter(property=property1).exists())
        self.assertTrue(AIReport.objects.filter(property=property2).exists())

        # Attempt deletion
        url = AGENT_DETAIL_URL(agent.user.id)
        response = self.client.delete(url)

        # Assertions for FIXED code behavior
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expected 200 OK, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else response.content}",
        )

        # Verify agent and user are deleted
        self.assertFalse(Agent.objects.filter(id=agent.id).exists())
        self.assertFalse(User.objects.filter(id=agent.user.id).exists())

        # Verify AI backend references are cleaned up
        self.assertFalse(
            AIReport.objects.filter(property_id=property1.id).exists(),
            "AIReport records for property1 should be deleted",
        )
        self.assertFalse(
            AIReport.objects.filter(property_id=property2.id).exists(),
            "AIReport records for property2 should be deleted",
        )

    def test_property_with_aireport_chain_deletion(self):
        """
        Test Case 4: Property with AIReport, ChatSession, and ChatMessage chain deletion

        WHEN a Property with AIReport, ChatSession, and ChatMessage records is deleted
        THEN the system should delete all records in dependency order:
        ChatMessage → ChatSession → AIReport → Property
        AND complete the Property deletion successfully with status 200

        EXPECTED ON UNFIXED CODE: ForeignKeyViolation on ai_report.property_id
        """
        # Create property with full AI backend chain
        agent = AgentFactory()
        property_obj = PropertyFactory(agent=agent)
        user = UserFactory()

        # Create AIReport
        ai_report = AIReport.objects.create(
            property=property_obj, user=user, status=AIReport.Status.COMPLETED
        )

        # Create ChatSession linked to AIReport
        chat_session = ChatSession.objects.create(
            user=user, report=ai_report, user_message_count=2
        )

        # Create ChatMessages linked to ChatSession
        chat_message1 = ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.Role.USER,
            status=ChatMessage.Status.COMPLETED,
        )
        chat_message2 = ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.Role.AI,
            status=ChatMessage.Status.COMPLETED,
        )

        # Verify setup
        self.assertTrue(AIReport.objects.filter(property=property_obj).exists())
        self.assertTrue(ChatSession.objects.filter(report=ai_report).exists())
        self.assertEqual(ChatMessage.objects.filter(session=chat_session).count(), 2)

        # Authenticate as the agent who owns the property
        self.client.force_authenticate(user=agent.user)

        # Attempt deletion
        url = PROPERTY_DETAIL_URL(property_obj.id)
        response = self.client.delete(url)

        # Assertions for FIXED code behavior
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expected 200 OK, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else response.content}",
        )

        # Verify property is deleted
        self.assertFalse(Property.objects.filter(id=property_obj.id).exists())

        # Verify AI backend references are cleaned up in correct order
        self.assertFalse(
            ChatMessage.objects.filter(session_id=chat_session.id).exists(),
            "ChatMessage records should be deleted",
        )
        self.assertFalse(
            ChatSession.objects.filter(id=chat_session.id).exists(),
            "ChatSession records should be deleted",
        )
        self.assertFalse(
            AIReport.objects.filter(id=ai_report.id).exists(),
            "AIReport records should be deleted",
        )
