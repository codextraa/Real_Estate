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
    slug = models.SlugField(unique=True, blank=True, null=True)

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
    description = models.TextField()
    beds = models.IntegerField()
    baths = models.IntegerField()
    price = models.FloatField()
    area_sqft = models.IntegerField()
    address = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    image_url = models.ImageField(
        upload_to="property_images/", blank=True, null=True, max_length=500
    )

    def save(self, *args, **kwargs):
        """Running Validators before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"
