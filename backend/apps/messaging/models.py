from django.conf import settings
from django.db import models

from apps.claims.models import Claim


class ClaimMessage(models.Model):
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="claim_messages",
    )
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["claim", "created_at"],
                name="messaging_c_claim_i_536a6e_idx",
            )
        ]

    def __str__(self):
        return f"Message {self.pk} on claim {self.claim_id}"
