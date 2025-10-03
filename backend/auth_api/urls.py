from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh-token/", views.RefreshTokenView.as_view(), name="refresh-token"),
]
