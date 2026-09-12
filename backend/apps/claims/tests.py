from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.items.models import Item
from apps.qr_tracking.models import HandoverToken

from .models import Claim

User = get_user_model()


class ClaimHandoverTests(APITestCase):
    def setUp(self):
        self.finder = User.objects.create_user(
            username="finder",
            email="finder@example.com",
            password="SecurePass!2026",
            role="EXTERNAL_FINDER",
            is_email_verified=True,
        )
        self.claimant = User.objects.create_user(
            username="claimant",
            email="claimant@gcet.edu.in",
            password="SecurePass!2026",
            college_id="22CS002",
            is_email_verified=True,
        )
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="SecurePass!2026",
            role="ADMIN",
            is_email_verified=True,
        )
        self.item = Item.objects.create(
            reporter=self.finder,
            report_type="FOUND",
            title="Black wallet",
            category="Wallet",
            color="Black",
            description="Black wallet found near the auditorium seats.",
            location="Auditorium",
            event_date=date(2026, 7, 29),
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_claim_approval_and_single_use_handover(self):
        self.authenticate(self.claimant)
        response = self.client.post(
            "/api/v1/claims/",
            {
                "item": self.item.id,
                "ownership_details": (
                    "The wallet contains my college card and has "
                    "a scratch on the lower-left corner."
                ),
                "proof_text": "The college card contains my name.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        claim = Claim.objects.get()

        self.authenticate(self.admin)
        approved = self.client.post(
            f"/api/v1/claims/{claim.id}/approve/",
            {"review_note": "Evidence verified."},
            format="json",
        )
        self.assertEqual(approved.status_code, 200)

        handover = HandoverToken.objects.get(claim=claim)
        completed = self.client.post(
            f"/api/v1/handover/{handover.token}/complete/",
            {"otp": handover.otp},
            format="json",
        )
        self.assertEqual(completed.status_code, 200)

        repeated = self.client.post(
            f"/api/v1/handover/{handover.token}/complete/",
            {"otp": handover.otp},
            format="json",
        )
        self.assertEqual(repeated.status_code, 409)

    def test_reporter_cannot_claim_own_item(self):
        self.authenticate(self.finder)
        response = self.client.post(
            "/api/v1/claims/",
            {
                "item": self.item.id,
                "ownership_details": (
                    "Attempting to claim an item reported by same account."
                ),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
