from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        SYSTEM = "SYSTEM", "System"
        ITEM = "ITEM", "Item"
        MATCH = "MATCH", "AI Match"
        CLAIM = "CLAIM", "Claim"
        HANDOVER = "HANDOVER", "Handover"
        MESSAGE = "MESSAGE", "Message"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
    )
    title = models.CharField(max_length=140)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "is_read", "created_at"],
                name="notificatio_user_id_5fd425_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user}: {self.title}"
