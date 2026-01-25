from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


# Shadow models
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = "core_db_user"

    USERNAME_FIELD = "email"


class Agent(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    company_name = models.CharField(max_length=255)
    bio = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = "core_db_agent"


class Property(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=150)
    description = models.TextField()
    beds = models.IntegerField()
    baths = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    area_sqft = models.IntegerField()
    address = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = "core_db_property"


class AIReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="ai_reports"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_reports"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    extracted_area = models.CharField(max_length=100, blank=True)
    extracted_city = models.CharField(max_length=100, blank=True)
    comparable_data = models.JSONField(null=True, blank=True)
    avg_beds = models.IntegerField(null=True)
    avg_baths = models.IntegerField(null=True)
    avg_market_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    avg_price_per_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    investment_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Rating from 0.0 to 5.0 based on analysis",
    )

    ai_insight_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.property.title} ({self.status})"


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report = models.ForeignKey(
        AIReport, on_delete=models.SET_NULL, null=True, blank=True
    )
    user_message_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat with {self.user.username}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]
