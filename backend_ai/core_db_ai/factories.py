import random
import factory
import numpy as np
from factory.fuzzy import FuzzyInteger, FuzzyDecimal, FuzzyChoice
from .models import User, AIReport, Property, ChatMessage, ChatSession


class AIReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIReport

    # Instead of SubFactory, we pick a random existing property and user
    # We use a lambda to ensure the query runs when the factory is called
    property = factory.LazyAttribute(lambda _: random.choice(Property.objects.all()))
    user = factory.LazyAttribute(lambda _: random.choice(User.objects.all()))

    status = FuzzyChoice(
        [
            AIReport.Status.PENDING,
            AIReport.Status.PROCESSING,
            AIReport.Status.COMPLETED,
            AIReport.Status.FAILED,
        ]
    )

    extracted_area = factory.Faker("street_name")
    extracted_city = factory.Faker("city")

    @factory.lazy_attribute
    def comparable_data(self):
        return [
            {
                "price": random.randint(200000, 900000),
                "area_sqft": random.randint(800, 3500),
                "beds": random.randint(1, 5),
                "baths": random.randint(1, 4),
            }
            for _ in range(100)
        ]

    avg_beds = FuzzyInteger(1, 10)
    avg_baths = FuzzyInteger(1, 10)
    avg_market_price = FuzzyDecimal(15000.00, 60000.00, 2)
    avg_price_per_sqft = FuzzyDecimal(50.00, 300.00, 2)
    investment_rating = FuzzyChoice(np.arange(0.0, 5.5, 0.5))

    ai_insight_summary = factory.Faker("paragraph", nb_sentences=3)


class ChatSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChatSession

    user = factory.LazyAttribute(lambda _: random.choice(User.objects.all()))
    report = factory.LazyAttribute(lambda _: random.choice(AIReport.objects.all()))
    user_message_count = 0


class ChatMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChatMessage

    session = factory.SubFactory(ChatSessionFactory)
    role = FuzzyChoice([ChatMessage.Role.USER, ChatMessage.Role.AI])
    content = factory.Faker("paragraph", nb_sentences=3)

    @factory.post_generation
    def update_session_counter(
        self, create, extracted, **kwargs
    ):  # pylint: disable=unused-argument
        if not create:
            return

        if self.role == ChatMessage.Role.USER:
            self.session.user_message_count += 1
            self.session.save()
