from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def _broadcast(notification):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)(
                f"user_{notification.user_id}",
                {
                    "type": "notification.message",
                    "notification": {
                        "id": notification.id,
                        "notification_type": (
                            notification.notification_type
                        ),
                        "title": notification.title,
                        "message": notification.message,
                        "link": notification.link,
                        "is_read": notification.is_read,
                        "created_at": (
                            notification.created_at.isoformat()
                        ),
                    },
                },
            )
    except Exception:
        pass


def notify_user(
    user,
    title,
    message,
    notification_type="SYSTEM",
    link="",
):
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    _broadcast(notification)
    return notification


def notify_reviewers(title, message, notification_type="SYSTEM", link=""):
    reviewers = User.objects.filter(
        is_active=True,
    ).filter(
        is_staff=True,
    ) | User.objects.filter(
        is_active=True,
        role__in=["ADMIN", "FACULTY"],
    )
    for user in reviewers.distinct():
        notify_user(
            user,
            title,
            message,
            notification_type,
            link,
        )
