from django.conf import settings
from django.db import models


class Item(models.Model):
    class ReportType(models.TextChoices):
        LOST = "LOST", "Lost"
        FOUND = "FOUND", "Found"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CLAIMED = "CLAIMED", "Claim in Progress"
        RETURNED = "RETURNED", "Returned"
        CLOSED = "CLOSED", "Closed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_items",
    )
    report_type = models.CharField(
        max_length=10,
        choices=ReportType.choices,
    )
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=80)
    color = models.CharField(max_length=50, blank=True)
    brand = models.CharField(max_length=80, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=150)
    event_date = models.DateField()
    image = models.ImageField(
        upload_to="items/%Y/%m/",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["report_type", "status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["event_date"]),
        ]

    @property
    def reference_code(self):
        return f"TRK-{self.created_at:%y%m}-{self.pk:05d}"

    def __str__(self):
        return f"{self.report_type}: {self.title}"
