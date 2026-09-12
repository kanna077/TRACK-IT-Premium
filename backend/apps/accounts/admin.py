from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailVerificationOTP, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "is_email_verified",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "role",
        "is_email_verified",
        "is_staff",
        "is_active",
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            "TRACK-IT Information",
            {
                "fields": (
                    "role",
                    "college_id",
                    "department",
                    "phone",
                    "is_email_verified",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "TRACK-IT Information",
            {
                "fields": (
                    "email",
                    "role",
                    "college_id",
                    "department",
                    "phone",
                    "is_email_verified",
                )
            },
        ),
    )


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "attempts", "updated_at")
    readonly_fields = ("code", "expires_at", "attempts", "updated_at")
    search_fields = ("user__email", "user__username")
