from django.urls import path

from .views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    RegisterView,
    ResendEmailOTPView,
    VerifyEmailOTPView,
)


urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailOTPView.as_view()),
    path("resend-otp/", ResendEmailOTPView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", CurrentUserView.as_view()),
]
