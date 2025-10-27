import factory
from factory.fuzzy import FuzzyInteger, FuzzyDecimal
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from .models import User, Agent, Property
from . import signals

# --- Global Constants ---
FIXED_PASSWORD = "Django@123"
PASSWORD_HASH = make_password(FIXED_PASSWORD)
AGENT_IMAGE_PATH = "profile_images/default_profile.jpg"
PROPERTY_IMAGE_PATH = "property_images/default_image.jpg"


# --- User Factory ---
@factory.django.mute_signals(signals.pre_save, signals.post_save)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Faker("email")
    username = factory.LazyAttribute(lambda obj: obj.email)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_agent = False
    password = PASSWORD_HASH
    slug = factory.LazyAttribute(lambda obj: slugify(f"{obj.email}"))


# --- Superuser Factory ---
@factory.django.mute_signals(signals.pre_save, signals.post_save)
class SuperuserFactory(UserFactory):
    email = "superuser@example.com"
    is_staff = True
    is_superuser = True


# --- Staff User Factory ---
@factory.django.mute_signals(signals.pre_save, signals.post_save)
class StaffuserFactory(UserFactory):
    email = "staffuser@example.com"
    is_staff = True


# --- Agent Factory ---
@factory.django.mute_signals(signals.pre_save, signals.post_save)
class AgentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Agent

    user = factory.SubFactory(UserFactory, is_agent=True)
    company_name = factory.Faker("company")
    bio = factory.Faker("paragraph", nb_sentences=2)
    image_url = AGENT_IMAGE_PATH


# --- Property Factory ---
@factory.django.mute_signals(signals.pre_save, signals.post_save)
class PropertyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Property

    agent = factory.SubFactory(AgentFactory)
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    beds = FuzzyInteger(1, 10)
    baths = FuzzyInteger(1, 10)
    price = FuzzyDecimal(10000.00, 50000.00, 2)
    area_sqft = FuzzyInteger(500, 5000)
    address = factory.Faker("address")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    image_url = PROPERTY_IMAGE_PATH
