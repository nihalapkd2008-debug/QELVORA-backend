
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from accounts.models import UserProfile
from .models import (
    Category,
    Product,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


User = get_user_model()


# CURRENT USER SERIALIZER
class CurrentUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    vendor_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "role",
            "vendor_status",
        ]
        read_only_fields = fields

    def get_role(self, obj) -> str | None:
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return None

    def get_vendor_status(self, obj) -> str | None:
        try:
            return obj.profile.vendor_status
        except UserProfile.DoesNotExist:
            return None


# CATEGORY SERIALIZER
class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


# PRODUCT SERIALIZER
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


# REGISTRATION SERIALIZER
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# CART ITEM SERIALIZER
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
        ]


# CART SERIALIZER
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "created_at",
        ]


# CART ADD REQUEST SERIALIZER
class CartAddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(
        error_messages={
            "required": "product_id is required.",
            "invalid": "Product ID must be a valid number.",
        }
    )

    quantity = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        error_messages={
            "invalid": "Quantity must be a valid number.",
            "min_value": "Quantity must be at least 1.",
        },
    )


# CART UPDATE REQUEST SERIALIZER
class CartQuantityUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "A valid quantity is required.",
            "invalid": "A valid quantity is required.",
            "min_value": "Quantity must be at least 1.",
        },
    )


# ORDER ITEM SERIALIZER
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price",
        ]


# ORDER SERIALIZER
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = CurrentUserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "items",
            "total_price",
            "status",
            "created_at",
        ]


# VENDOR PRODUCT SERIALIZER
class VendorProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


# ADMIN PRODUCT SERIALIZER
class AdminProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )

    vendor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "vendor",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
