from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router1 = DefaultRouter()
router2 = DefaultRouter()
router1.register(r"users", views.UserViewSet)
router2.register(r"agents", views.AgentViewSet)

urlpatterns = [
    path("", include(router1.urls)),
    path("", include(router2.urls)),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh-token/", views.RefreshTokenView.as_view(), name="refresh-token"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
