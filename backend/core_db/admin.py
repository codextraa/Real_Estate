"""Admin registration for blog api."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Agent, Property
from .forms import CustomUserCreationForm


class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""

    list_display = ("email", "username")
    list_filter = ("groups",)
    prepopulated_fields = {"slug": ("username",)}

    # Fields to be displayed on the user detail page
    fieldsets = (
        (None, {"fields": ("email", "username", "password", "slug")}),
        (
            "Personal_info",
            {"fields": ("first_name", "last_name")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_form = CustomUserCreationForm
    # Fields to be displayed in user creation form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "slug",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_agent",
                ),
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Agent)
admin.site.register(Property)
