from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, RegexValidator
from backend.validators import validate_password_complexity


class UserManager(BaseUserManager):
    """Custom User Manager"""

    def create_user(self, email, password=None, **extra_fields):
        """Custom User Creation"""
        if not email:
            raise ValueError("You must have an email address")

        try:
            validate_email(email)
        except ValidationError as exc:
            raise ValidationError("Invalid Email Format") from exc

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        """Super User Creation"""
        if not password:
            raise ValueError("SuperUser must have a password")

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Class"""

    class Meta:
        ordering = ["email"]

    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\S+$",  # No whitespace allowed
                message="Username cannot contain spaces",
                code="invalid_username",
            )
        ],
    )
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=255)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def set_password(self, raw_password):
        """Validates raw password before hashing"""
        if not raw_password:
            raise ValidationError({"password": "Password is required"})
        errors = validate_password_complexity(raw_password)
        if len(errors["password"]) > 0:
            raise ValidationError(errors)
        super().set_password(raw_password)

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return Email"""
        return f"{self.email}"


class Agent(models.Model):
    "Custom Agent Class"

    class Meta:
        ordering = ["user__email"]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    bio = models.CharField(max_length=150, blank=True, null=True)
    image_url = models.ImageField(
        upload_to="profile_images/", blank=True, null=True, max_length=500
    )

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name}"


class Property(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=150, blank=True, null=True)
    beds = models.IntegerField()
    baths = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    area_sqft = models.IntegerField()
    address = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=150)
    image_url = models.ImageField(
        upload_to="property_images/", blank=True, null=True, max_length=500
    )

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"


# Shadow Models for AI Backend Tables
# These models mirror the AI backend's models to allow the main backend
# to query and delete AI backend records for cross-service integrity


class AIReport(models.Model):
    """Shadow model for AI backend's AIReport table"""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ai_reports", db_column="user_id"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="ai_reports",
        db_column="property_id",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        managed = False
        db_table = "core_db_ai_aireport"


class ChatSession(models.Model):
    """Shadow model for AI backend's ChatSession table"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        db_column="user_id",
    )
    report = models.ForeignKey(
        AIReport,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        db_column="report_id",
    )
    user_message_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "core_db_ai_chatsession"


class ChatMessage(models.Model):
    """Shadow model for AI backend's ChatMessage table"""

    class Role(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        db_column="session_id",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        managed = False
        db_table = "core_db_ai_chatmessage"
