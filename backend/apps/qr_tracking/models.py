import secrets
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.claims.models import Claim


def default_expiry():
    return timezone.now() + timedelta(minutes=30)


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


class HandoverToken(models.Model):
    claim = models.OneToOneField(
        Claim,
        on_delete=models.CASCADE,
        related_name="handover_token_record",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    otp = models.CharField(max_length=6, default=generate_otp)
    expires_at = models.DateTimeField(default=default_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return str(self.token)
