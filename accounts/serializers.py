
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import VendorApplication

User = get_user_model()


# VENDOR APPLICATION SERIALIZER
class VendorApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorApplication
        fields = [
            "id",
            "business_name",
            "description",
            "contact_email",
            "contact_phone",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]


# ADMIN USER SERIALIZER
class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    vendor_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "role",
            "vendor_status",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "role",
            "vendor_status",
        ]

    def get_role(self, obj) -> str | None:
        profile = getattr(obj, "profile", None)
        return profile.role if profile else None

    def get_vendor_status(self, obj) -> str | None:
        profile = getattr(obj, "profile", None)
        return profile.vendor_status if profile else None
