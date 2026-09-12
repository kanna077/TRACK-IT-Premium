from django.contrib import admin

from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "title",
        "report_type",
        "category",
        "location",
        "status",
        "reporter",
        "event_date",
    )
    list_filter = ("report_type", "status", "category", "event_date")
    search_fields = (
        "title",
        "description",
        "brand",
        "location",
        "reporter__username",
        "reporter__email",
    )
    readonly_fields = ("created_at", "updated_at")
