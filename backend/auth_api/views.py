"""Views for Auth API."""  # pylint: disable=C0302

from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
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


def check_user_id(user_id):
    """Check if user id is valid."""
    try:
        user_id = int(user_id)
    except Exception as e:  # pylint: disable=W0718
        print(e)
        return Response(
            {"error": "Invalid Session"}, status=status.HTTP_400_BAD_REQUEST
        )

    user = get_user_model().objects.filter(id=user_id).first()

    if not user:
        return Response(
            {"error": "Invalid Session"}, status=status.HTTP_400_BAD_REQUEST
        )

    return check_user_validity(user.email)


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


class RefreshTokenView(TokenRefreshView):
    """Refresh Token View generates JWT access token using the refresh token."""

    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):
        """Post a request to RefreshTokenView. Verifies OTP and generates JWT tokens."""
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "Tokens are required"}, status=status.HTTP_400_BAD_REQUEST
                )

            response = super().post(request, *args, **kwargs)
            response.data["access_token_expiry"] = (
                now() + timedelta(minutes=5)
            ).isoformat()

            # Extract the access token and refresh token
            refresh_token = response.data.get("refresh")
            access_token = response.data.get("access")

            if not refresh_token or not access_token:
                return Response(
                    {"error": "Invalid tokens"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Decode the access token to extract user details
            decoded_token = RefreshToken(refresh_token)
            user_id = decoded_token.get("user_id", None)
            if not user_id:
                raise InvalidToken("Invalid refresh token")

            # Check user validity
            user = check_user_id(user_id)

            if isinstance(user, Response):
                return user

            user_role = get_user_role(user)

            response.data["user_role"] = user_role
            response.data["user_id"] = user.id
            response.data["access_token"] = response.data["access"]
            response.data["refresh_token"] = response.data["refresh"]
            response.data.pop("access")
            response.data.pop("refresh")

            return response

        except TokenError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:  # pylint: disable=W0718
            # return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
            print(e)
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
