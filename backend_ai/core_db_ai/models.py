from django.db import models
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
