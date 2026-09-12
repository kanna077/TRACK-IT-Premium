from rest_framework.test import APITestCase


class ChatbotTests(APITestCase):
    def test_claim_question_returns_informational_answer(self):
        response = self.client.post(
            "/api/v1/chatbot/query/",
            {"message": "How do I submit an ownership claim?"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["informational_only"])
        self.assertIn("ownership", response.data["answer"].lower())
