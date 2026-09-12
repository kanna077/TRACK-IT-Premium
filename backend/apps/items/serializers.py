from pathlib import Path

from rest_framework import serializers

from .models import Item


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 6 * 1024 * 1024


class ItemSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(
        source="reporter.username",
        read_only=True,
    )
    reference_code = serializers.CharField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = (
            "id",
            "reference_code",
            "reporter",
            "reporter_name",
            "report_type",
            "title",
            "category",
            "color",
            "brand",
            "description",
            "location",
            "event_date",
            "image",
            "image_url",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reference_code",
            "reporter",
            "reporter_name",
            "image_url",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_image(self, image):
        if image is None:
            return image
        if image.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                "Image size must not exceed 6 MB."
            )
        extension = Path(image.name).suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise serializers.ValidationError(
                "Upload a JPG, PNG or WEBP image."
            )
        return image

    def validate(self, attrs):
        title = attrs.get("title", "").strip()
        description = attrs.get("description", "").strip()
        if len(title) < 3:
            raise serializers.ValidationError(
                {"title": "Title must contain at least 3 characters."}
            )
        if len(description) < 10:
            raise serializers.ValidationError(
                {
                    "description": (
                        "Description must contain at least 10 characters."
                    )
                }
            )
        return attrs

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.image.url)
            if request
            else obj.image.url
        )
