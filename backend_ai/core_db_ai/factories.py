import factory
import random
from factory.fuzzy import FuzzyInteger, FuzzyDecimal, FuzzyChoice
from .models import AIReport, Property

class AIReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIReport

    # Instead of SubFactory, we pick a random existing property
    # We use a lambda to ensure the query runs when the factory is called
    property = factory.LazyAttribute(lambda _: random.choice(Property.objects.all()))

    status = FuzzyChoice([
        AIReport.Status.PENDING,
        AIReport.Status.PROCESSING,
        AIReport.Status.COMPLETED,
        AIReport.Status.FAILED
    ])

    extracted_area = factory.Faker("street_name")
    extracted_city = factory.Faker("city")

    @factory.lazy_attribute
    def comparable_data(self):
        return {
            "neighbors": [
                {"price": 45000, "sqft": 1200},
                {"price": 48000, "sqft": 1350}
            ],
            "market_status": "stable"
        }

    avg_market_price = FuzzyDecimal(15000.00, 60000.00, 2)
    avg_price_per_sqft = FuzzyDecimal(50.00, 300.00, 2)
    investment_rating = FuzzyInteger(0, 4) # Standardized to 0-4 per your model help_text

    ai_insight_summary = factory.Faker("paragraph", nb_sentences=3)