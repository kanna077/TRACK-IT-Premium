from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.items.models import Item

from .models import Claim


class ClaimSerializer(serializers.ModelSerializer):
    claimant_name = serializers.CharField(
        source="claimant.username",
        read_only=True,
    )
    item_title = serializers.CharField(
        source="item.title",
        read_only=True,
    )
    item_reference = serializers.CharField(
        source="item.reference_code",
        read_only=True,
    )
    handover_token = serializers.SerializerMethodField()
    handover_otp = serializers.SerializerMethodField()
    handover_expires_at = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(
        source="messages.count",
        read_only=True,
    )

    class Meta:
        model = Claim
        fields = (
            "id",
            "item",
            "item_title",
            "item_reference",
            "claimant",
            "claimant_name",
            "ownership_details",
            "proof_text",
            "status",
            "review_note",
            "reviewed_by",
            "created_at",
            "reviewed_at",
            "handover_token",
            "handover_otp",
            "handover_expires_at",
            "message_count",
        )
        read_only_fields = (
            "id",
            "item_title",
            "item_reference",
            "claimant",
            "claimant_name",
            "status",
            "review_note",
            "reviewed_by",
            "created_at",
            "reviewed_at",
            "handover_token",
            "handover_otp",
            "handover_expires_at",
            "message_count",
        )

    def validate_item(self, item):
        request = self.context.get("request")
        if item.report_type != Item.ReportType.FOUND:
            raise serializers.ValidationError(
                "Claims can be submitted only for found-item reports."
            )
        if item.status != Item.Status.ACTIVE:
            raise serializers.ValidationError(
                "This item is not available for a new claim."
            )
        if request and item.reporter_id == request.user.id:
            raise serializers.ValidationError(
                "You cannot claim an item reported by your own account."
            )
        if (
            request
            and Claim.objects.filter(
                item=item,
                claimant=request.user,
                status__in=[
                    Claim.Status.SUBMITTED,
                    Claim.Status.APPROVED,
                ],
            ).exists()
        ):
            raise serializers.ValidationError(
                "You already have an active claim for this item."
            )
        return item

    def validate_ownership_details(self, value):
        details = value.strip()
        if len(details) < 20:
            raise serializers.ValidationError(
                "Provide at least 20 characters of ownership evidence."
            )
        return details

    def _handover(self, obj):
        try:
            return obj.handover_token_record
        except ObjectDoesNotExist:
            return None

    def get_handover_token(self, obj):
        token = self._handover(obj)
        return str(token.token) if token else None

    def get_handover_otp(self, obj):
        token = self._handover(obj)
        return token.otp if token else None

    def get_handover_expires_at(self, obj):
        token = self._handover(obj)
        return token.expires_at if token else None
