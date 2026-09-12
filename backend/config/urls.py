from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone


def health(_request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "TRACK-IT API",
            "timestamp": timezone.now().isoformat(),
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/items/", include("apps.items.urls")),
    path("api/v1/claims/", include("apps.claims.urls")),
    path("api/v1/handover/", include("apps.qr_tracking.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/messages/", include("apps.messaging.urls")),
    path("api/v1/chatbot/", include("apps.chatbot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
