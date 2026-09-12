from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import EmailVerificationOTP, User


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class AccountFlowTests(APITestCase):
    def test_registration_sends_otp_and_verifies_email(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "external1",
                "email": "external1@example.com",
                "password": "SecurePass!2026",
                "password_confirm": "SecurePass!2026",
                "role": "EXTERNAL_FINDER",
                "college_id": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(username="external1")
        self.assertFalse(user.is_email_verified)
        otp = EmailVerificationOTP.objects.get(user=user).code

        verify = self.client.post(
            "/api/v1/auth/verify-email/",
            {"email": user.email, "otp": otp},
            format="json",
        )
        self.assertEqual(verify.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_student_requires_college_domain(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "student1",
                "email": "student1@gmail.com",
                "password": "SecurePass!2026",
                "password_confirm": "SecurePass!2026",
                "role": "STUDENT",
                "college_id": "22CS001",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
