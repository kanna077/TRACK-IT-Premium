import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.conf import settings  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402

django_application = get_asgi_application()

if getattr(settings, "CHANNELS_AVAILABLE", False):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from apps.notifications.routing import websocket_urlpatterns

    application = ProtocolTypeRouter(
        {
            "http": django_application,
            "websocket": AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            ),
        }
    )
else:
    application = django_application
