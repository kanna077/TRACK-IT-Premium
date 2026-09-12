from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.claims.models import Claim
from apps.items.models import Item
from apps.notifications.services import notify_user

from .models import HandoverToken


def can_complete(user):
    return user.is_staff or getattr(user, "role", "") in {
        "FACULTY",
        "ADMIN",
    }


class CompleteHandoverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        if not can_complete(request.user):
            return Response(
                {
                    "detail": (
                        "Only authorized staff can complete a handover."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        submitted_otp = str(request.data.get("otp", "")).strip()
        if len(submitted_otp) != 6 or not submitted_otp.isdigit():
            return Response(
                {"detail": "Enter a valid 6-digit OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                handover = (
                    HandoverToken.objects.select_for_update()
                    .select_related("claim__item", "claim__claimant")
                    .get(token=token)
                )
            except HandoverToken.DoesNotExist:
                return Response(
                    {"detail": "Invalid handover token."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if handover.is_used:
                return Response(
                    {"detail": "This handover token was already used."},
                    status=status.HTTP_409_CONFLICT,
                )
            if handover.is_expired:
                return Response(
                    {"detail": "This handover token has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if submitted_otp != handover.otp:
                return Response(
                    {"detail": "Invalid OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            claim = handover.claim
            if claim.status != Claim.Status.APPROVED:
                return Response(
                    {"detail": "The claim is not approved."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            handover.used_at = timezone.now()
            handover.save(update_fields=["used_at"])
            claim.status = Claim.Status.RETURNED
            claim.save(update_fields=["status"])

            item = claim.item
            item.status = Item.Status.RETURNED
            item.save(update_fields=["status", "updated_at"])

        notify_user(
            claim.claimant,
            title="Item returned successfully",
            message=(
                f"The handover for '{item.title}' was completed "
                f"by {request.user.username}."
            ),
            notification_type="HANDOVER",
            link=f"/claims/{claim.id}",
        )
        return Response(
            {
                "message": "Item handover completed successfully.",
                "receipt": {
                    "claim_id": claim.id,
                    "item_reference": item.reference_code,
                    "item": item.title,
                    "claimant": claim.claimant.username,
                    "completed_by": request.user.username,
                    "completed_at": handover.used_at,
                },
            }
        )
