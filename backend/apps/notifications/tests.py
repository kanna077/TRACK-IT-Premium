from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Notification

User = get_user_model()


class NotificationTests(APITestCase):
    def test_user_sees_only_own_notifications(self):
        user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="SecurePass!2026",
            is_email_verified=True,
        )
        other = User.objects.create_user(
            username="u2",
            email="u2@example.com",
            password="SecurePass!2026",
            is_email_verified=True,
        )
        Notification.objects.create(
            user=user,
            title="Mine",
            message="Visible",
        )
        Notification.objects.create(
            user=other,
            title="Other",
            message="Hidden",
        )
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, 200)
        rows = response.data.get("results", response.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Mine")
