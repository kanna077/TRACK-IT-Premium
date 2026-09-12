from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "display_name",
            "email",
            "first_name",
            "last_name",
            "role",
            "college_id",
            "department",
            "phone",
            "is_email_verified",
            "is_staff",
            "is_superuser",
        )
        read_only_fields = (
            "id",
            "display_name",
            "is_email_verified",
            "is_staff",
            "is_superuser",
        )

    def get_display_name(self, obj):
        return obj.get_full_name().strip() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "college_id",
            "department",
            "phone",
        )

    def validate_username(self, value):
        username = value.strip()
        if len(username) < 3:
            raise serializers.ValidationError(
                "Username must contain at least 3 characters."
            )
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        role = attrs.get("role", User.Role.STUDENT)
        public_roles = {
            User.Role.STUDENT,
            User.Role.EXTERNAL_FINDER,
        }
        if role not in public_roles:
            raise serializers.ValidationError(
                {
                    "role": (
                        "Faculty and administrator accounts must be "
                        "created by an administrator."
                    )
                }
            )

        if (
            role == User.Role.STUDENT
            and not attrs["email"].endswith("@gcet.edu.in")
        ):
            raise serializers.ValidationError(
                {
                    "email": (
                        "Campus users must register using an "
                        "@gcet.edu.in email address."
                    )
                }
            )

        college_id = attrs.get("college_id")
        if role == User.Role.STUDENT and not college_id:
            raise serializers.ValidationError(
                {"college_id": "College ID is required for students."}
            )
        if role == User.Role.EXTERNAL_FINDER:
            attrs["college_id"] = None

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            is_email_verified=False,
            **validated_data,
        )
