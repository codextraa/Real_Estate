"""Views for Auth API."""  # pylint: disable=C0302

from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from backend.renderers import ViewRenderer


def check_user_validity(email):
    """Check if user is valid using email."""
    user = get_user_model().objects.filter(email=email).first()

    # Check if user exists
    if not user:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user is active
    if not user.is_active:
        return Response(
            {"error": "Account is deactivated. Contact your admin"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return user


def get_user_role(user):
    """Get user role."""
    user_groups = user.groups.all()

    if user_groups.filter(name="Default").exists():
        user_role = "Default"
    elif user_groups.filter(name="Agent").exists():
        user_role = "Agent"
    elif user_groups.filter(name="Admin").exists():
        user_role = "Admin"
    elif user_groups.filter(name="Superuser").exists():
        user_role = "Superuser"
    else:
        user_role = "UnAuthorized"

    return user_role


class LoginView(TokenObtainPairView):
    """Login View."""

    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Post a request to login. Returns an OTP to the registered email."""
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if not email or not password:
                return Response(
                    {"error": "Email and password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = check_user_validity(email)

            if isinstance(user, Response):
                return user

            # Check if password is correct
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
                )

            response = super().post(request, *args, **kwargs)

            response.data["access_token_expiry"] = (
                now() + timedelta(hours=1)
            ).isoformat()

            user_role = get_user_role(user)

            response.data["user_role"] = user_role
            response.data["user_id"] = user.id
            response.data["access_token"] = response.data["access"]
            response.data["refresh_token"] = response.data["refresh"]
            response.data.pop("access")
            response.data.pop("refresh")

            return response
        except Exception as e:  # pylint: disable=W0718
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
