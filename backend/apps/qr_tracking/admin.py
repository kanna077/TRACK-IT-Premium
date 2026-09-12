from django.contrib import admin

from .models import HandoverToken


@admin.register(HandoverToken)
class HandoverTokenAdmin(admin.ModelAdmin):
    list_display = (
        "token",
        "claim",
        "expires_at",
        "used_at",
        "created_at",
    )
    readonly_fields = ("token", "otp", "created_at", "used_at")
