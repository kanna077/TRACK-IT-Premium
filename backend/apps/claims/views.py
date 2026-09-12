from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.items.models import Item
from apps.notifications.services import notify_user
from apps.qr_tracking.models import HandoverToken

from .models import Claim
from .serializers import ClaimSerializer


def can_review(user):
    return user.is_staff or getattr(user, "role", "") in {
        "FACULTY",
        "ADMIN",
    }


class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = Claim.objects.select_related(
            "item",
            "item__reporter",
            "claimant",
            "reviewed_by",
        ).prefetch_related("messages")

        if can_review(self.request.user):
            return queryset
        return queryset.filter(claimant=self.request.user)

    def perform_create(self, serializer):
        claim = serializer.save(claimant=self.request.user)
        reviewers = type(self.request.user).objects.filter(
            is_active=True,
        ).filter(is_staff=True)
        for reviewer in reviewers:
            notify_user(
                reviewer,
                title=f"Ownership claim #{claim.id} submitted",
                message=(
                    f"{claim.claimant.username} submitted a claim "
                    f"for '{claim.item.title}'."
                ),
                notification_type="CLAIM",
                link=f"/claims/{claim.id}",
            )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if not can_review(request.user):
            return Response(
                {
                    "detail": (
                        "Only faculty or administrators can approve claims."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            claim = (
                Claim.objects.select_for_update()
                .select_related("item", "claimant")
                .get(pk=pk)
            )
            if claim.status != Claim.Status.SUBMITTED:
                return Response(
                    {"detail": "Only submitted claims can be approved."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                Claim.objects.filter(
                    item=claim.item,
                    status=Claim.Status.APPROVED,
                )
                .exclude(pk=claim.pk)
                .exists()
            ):
                return Response(
                    {"detail": "Another claim is already approved."},
                    status=status.HTTP_409_CONFLICT,
                )

            now = timezone.now()
            claim.status = Claim.Status.APPROVED
            claim.review_note = request.data.get("review_note", "").strip()
            claim.reviewed_by = request.user
            claim.reviewed_at = now
            claim.save()

            Claim.objects.filter(
                item=claim.item,
                status=Claim.Status.SUBMITTED,
            ).exclude(pk=claim.pk).update(
                status=Claim.Status.REJECTED,
                review_note="Another ownership claim was approved.",
                reviewed_by=request.user,
                reviewed_at=now,
            )

            claim.item.status = Item.Status.CLAIMED
            claim.item.save(update_fields=["status", "updated_at"])
            HandoverToken.objects.get_or_create(claim=claim)

        claim = self.get_queryset().get(pk=claim.pk)
        notify_user(
            claim.claimant,
            title="Ownership claim approved",
            message=(
                f"Your claim for '{claim.item.title}' was approved. "
                "Use the secure QR token and OTP for handover."
            ),
            notification_type="HANDOVER",
            link=f"/claims/{claim.id}",
        )
        return Response(
            ClaimSerializer(
                claim,
                context={"request": request},
            ).data
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if not can_review(request.user):
            return Response(
                {
                    "detail": (
                        "Only faculty or administrators can reject claims."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        claim = self.get_object()
        if claim.status != Claim.Status.SUBMITTED:
            return Response(
                {"detail": "Only submitted claims can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        claim.status = Claim.Status.REJECTED
        claim.review_note = request.data.get("review_note", "").strip()
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.save()

        notify_user(
            claim.claimant,
            title="Ownership claim reviewed",
            message=(
                f"Your claim for '{claim.item.title}' was not approved. "
                f"{claim.review_note or 'Contact authorized staff for details.'}"
            ),
            notification_type="CLAIM",
            link=f"/claims/{claim.id}",
        )
        return Response(
            ClaimSerializer(
                claim,
                context={"request": request},
            ).data
        )
