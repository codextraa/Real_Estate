import sys
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)

# Determine if we are running tests
IS_TESTING = "test" in sys.argv
ON_DELETE = models.CASCADE if IS_TESTING else models.DO_NOTHING


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


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
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()


class Agent(models.Model):
    user = models.ForeignKey(User, on_delete=ON_DELETE)
    company_name = models.CharField(max_length=255)
    bio = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = "core_db_agent"


class Property(models.Model):
    agent = models.ForeignKey(Agent, on_delete=ON_DELETE)
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

    extracted_area = models.CharField(max_length=100, blank=True, null=True)
    extracted_city = models.CharField(max_length=100, blank=True, null=True)
    comparable_data = models.JSONField(blank=True, null=True)
    avg_beds = models.IntegerField(blank=True, null=True)
    avg_baths = models.IntegerField(blank=True, null=True)
    avg_market_price = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    avg_price_per_sqft = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    investment_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Rating from 0.0 to 5.0 based on analysis",
    )

    ai_insight_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Analysis for {self.property.title} ({self.status})"


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    report = models.ForeignKey(
        AIReport, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    user_message_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat with {self.user.username}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["timestamp"]
