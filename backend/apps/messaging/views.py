from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.claims.models import Claim
from apps.notifications.services import notify_user

from .models import ClaimMessage
from .serializers import ClaimMessageSerializer


def can_access_claim(user, claim):
    return (
        user.is_staff
        or getattr(user, "role", "") in {"ADMIN", "FACULTY"}
        or claim.claimant_id == user.id
        or claim.item.reporter_id == user.id
    )


class ClaimMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimMessageSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = ClaimMessage.objects.select_related(
            "claim__item",
            "claim__claimant",
            "sender",
        )
        user = self.request.user
        if user.is_staff or getattr(user, "role", "") in {
            "ADMIN",
            "FACULTY",
        }:
            allowed = queryset
        else:
            allowed = queryset.filter(
                claim__claimant=user
            ) | queryset.filter(
                claim__item__reporter=user
            )

        claim_id = self.request.query_params.get("claim")
        if claim_id:
            allowed = allowed.filter(claim_id=claim_id)
        return allowed.distinct()

    def perform_create(self, serializer):
        claim = serializer.validated_data["claim"]
        if not can_access_claim(self.request.user, claim):
            raise PermissionDenied(
                "You are not a participant in this claim."
            )

        message = serializer.save(sender=self.request.user)
        recipients = {
            claim.claimant,
            claim.item.reporter,
        }
        if claim.reviewed_by:
            recipients.add(claim.reviewed_by)

        for recipient in recipients:
            if recipient.id != self.request.user.id:
                notify_user(
                    recipient,
                    title=f"New message for claim #{claim.id}",
                    message=(
                        f"{self.request.user.username}: "
                        f"{message.message[:120]}"
                    ),
                    notification_type="MESSAGE",
                    link=f"/claims/{claim.id}",
                )
