from rest_framework import serializers

from .models import ClaimMessage


class ClaimMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(
        source="sender.username",
        read_only=True,
    )

    class Meta:
        model = ClaimMessage
        fields = (
            "id",
            "claim",
            "sender",
            "sender_name",
            "message",
            "created_at",
        )
        read_only_fields = (
            "id",
            "sender",
            "sender_name",
            "created_at",
        )

    def validate_message(self, value):
        message = value.strip()
        if not message:
            raise serializers.ValidationError(
                "Message cannot be empty."
            )
        return message
