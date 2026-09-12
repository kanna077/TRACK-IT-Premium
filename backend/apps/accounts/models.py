from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Campus User / Student"
        FACULTY = "FACULTY", "Faculty / Authorized Staff"
        EXTERNAL_FINDER = "EXTERNAL_FINDER", "External Finder"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    college_id = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username


class EmailVerificationOTP(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_otp",
    )
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email verification for {self.user.email}"
