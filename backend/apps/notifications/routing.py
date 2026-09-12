from django.urls import path

from .consumers import NotificationConsumer
from .token_auth import TokenAuthMiddleware

websocket_urlpatterns = [
    path(
        "ws/notifications/",
        TokenAuthMiddleware(NotificationConsumer.as_asgi()),
    ),
]
