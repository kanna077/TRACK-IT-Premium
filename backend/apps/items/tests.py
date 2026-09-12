from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .matching import rank_candidates
from .models import Item

User = get_user_model()


class ItemMatchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student",
            email="student@gcet.edu.in",
            password="SecurePass!2026",
            college_id="22CS001",
            is_email_verified=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.user).key}"
        )

    def create_item(self, report_type, title):
        return Item.objects.create(
            reporter=self.user,
            report_type=report_type,
            title=title,
            category="Wallet",
            color="Black",
            brand="WildHorn",
            description="Leather wallet with a small scratch.",
            location="Block 5 Auditorium",
            event_date=date(2026, 7, 29),
        )

    def test_empty_candidates_return_empty_results(self):
        lost = self.create_item("LOST", "Black leather wallet")
        response = self.client.get(
            f"/api/v1/items/{lost.id}/matches/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_similar_found_item_ranks_first(self):
        lost = self.create_item("LOST", "Black leather wallet")
        found = self.create_item("FOUND", "Found black wallet")
        results = rank_candidates(lost, [found])
        self.assertEqual(results[0].item, found)
        self.assertGreater(results[0].score, 50)

    def test_anonymous_user_cannot_create_report(self):
        self.client.credentials()
        response = self.client.post(
            "/api/v1/items/",
            {
                "report_type": "LOST",
                "title": "Phone",
                "category": "Electronics",
                "description": "Black phone lost near the library.",
                "location": "Library",
                "event_date": "2026-07-29",
            },
            format="json",
        )
        self.assertIn(response.status_code, {401, 403})
