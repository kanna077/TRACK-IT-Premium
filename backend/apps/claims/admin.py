from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "claimant",
        "status",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "item__title",
        "claimant__username",
        "ownership_details",
    )
