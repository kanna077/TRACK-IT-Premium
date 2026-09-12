from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


FAQS = [
    (
        {"lost", "missing", "misplaced"},
        (
            "Open Report Item, choose Lost, add a clear description, "
            "location, date and image. TRACK-IT will suggest matching "
            "found reports."
        ),
    ),
    (
        {"found", "finder", "discovered"},
        (
            "Open Report Item, choose Found, record where and when the "
            "item was found, and avoid publishing sensitive contents."
        ),
    ),
    (
        {"claim", "owner", "ownership"},
        (
            "Open Claims, select a found item and provide private "
            "ownership evidence such as hidden marks, serial details "
            "or contents. Authorized staff review every claim."
        ),
    ),
    (
        {"match", "ai", "similar"},
        (
            "AI Matches compares descriptions, category, color, brand, "
            "location and date. Match scores are suggestions only and "
            "never prove ownership."
        ),
    ),
    (
        {"qr", "otp", "handover", "return"},
        (
            "After a claim is approved, TRACK-IT generates a time-limited "
            "QR token and 6-digit OTP. Authorized staff must verify both "
            "to complete the handover."
        ),
    ),
    (
        {"email", "verify", "verification"},
        (
            "Registration sends a 6-digit OTP to the entered email. "
            "The OTP expires after 10 minutes; use Resend OTP when needed."
        ),
    ),
    (
        {"privacy", "contact", "identity"},
        (
            "Public item cards show only the reporter username. Private "
            "ownership evidence and contact details remain restricted "
            "to authorized workflows."
        ),
    ),
]


class ChatbotQueryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        message = str(request.data.get("message", "")).strip().lower()
        if not message:
            return Response(
                {
                    "answer": (
                        "Ask me about lost reports, found reports, claims, "
                        "AI matching, email OTP or secure handover."
                    )
                }
            )

        words = set(message.replace("?", " ").split())
        best_answer = None
        best_score = 0
        for keywords, answer in FAQS:
            score = len(words & keywords)
            if score > best_score:
                best_score = score
                best_answer = answer

        return Response(
            {
                "answer": best_answer
                or (
                    "I can help with reporting, search, AI-assisted matches, "
                    "ownership claims, notifications and QR/OTP handover. "
                    "For account-specific decisions, contact authorized staff."
                ),
                "informational_only": True,
            }
        )
