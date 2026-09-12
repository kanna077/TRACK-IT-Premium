import secrets
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailVerificationOTP, User
from .serializers import RegisterSerializer, UserSerializer


OTP_VALID_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def send_verification_otp(user):
    code = f"{secrets.randbelow(1_000_000):06d}"

    EmailVerificationOTP.objects.update_or_create(
        user=user,
        defaults={
            "code": code,
            "expires_at": (
                timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)
            ),
            "attempts": 0,
        },
    )

    send_mail(
        subject="TRACK-IT email verification OTP",
        message=(
            f"Hello {user.username},\n\n"
            f"Your TRACK-IT verification OTP is: {code}\n\n"
            f"This OTP expires in {OTP_VALID_MINUTES} minutes. "
            "Do not share it with anyone."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_verification_otp(user)
        except (SMTPException, OSError):
            user.delete()
            return Response(
                {
                    "detail": (
                        "Registration email could not be sent. "
                        "Check the TRACK-IT email configuration."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message": (
                    "Registration successful. A 6-digit OTP was sent "
                    "to your registered email address."
                ),
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        otp = str(request.data.get("otp", "")).strip()

        if not email or not otp:
            return Response(
                {"detail": "Email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No registration was found for this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_email_verified:
            return Response(
                {"message": "Email is already verified. You may log in."}
            )

        try:
            record = EmailVerificationOTP.objects.get(user=user)
        except EmailVerificationOTP.DoesNotExist:
            return Response(
                {"detail": "No active OTP exists. Request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() >= record.expires_at:
            record.delete()
            return Response(
                {"detail": "OTP expired. Request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record.attempts >= MAX_OTP_ATTEMPTS:
            return Response(
                {
                    "detail": (
                        "Too many incorrect attempts. Request a new OTP."
                    )
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not secrets.compare_digest(record.code, otp):
            record.attempts += 1
            record.save(update_fields=["attempts", "updated_at"])
            return Response(
                {"detail": "Incorrect OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            record.delete()

        return Response(
            {"message": "Email verified successfully. You can now log in."}
        )


class ResendEmailOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No registration was found for this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_email_verified:
            return Response(
                {"message": "Email is already verified. You may log in."}
            )

        try:
            send_verification_otp(user)
        except (SMTPException, OSError):
            return Response(
                {"detail": "OTP email could not be sent."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"message": "A new OTP was sent to your registered email."}
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        identifier = str(request.data.get("identifier", "")).strip()
        password = request.data.get("password", "")

        if not identifier or not password:
            return Response(
                {"detail": "Username/email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = identifier
        if "@" in identifier:
            try:
                username = User.objects.get(
                    email__iexact=identifier
                ).username
            except User.DoesNotExist:
                pass

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Invalid username/email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_email_verified and not user.is_superuser:
            return Response(
                {
                    "detail": (
                        "Email is not verified. Enter the OTP sent "
                        "during registration."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"message": "Logged out successfully."})
