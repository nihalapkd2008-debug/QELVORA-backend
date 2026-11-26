
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, serializers, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsAdmin,
    IsApprovedVendor,
    IsCustomerOrVendor,
)

from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
)
from .pagination import AdminProductPagination
from .serializers import (
    AdminProductSerializer,
    CartAddItemSerializer,
    CartQuantityUpdateSerializer,
    CartSerializer,
    CategorySerializer,
    CurrentUserSerializer,
    OrderSerializer,
    ProductSerializer,
    RegisterSerializer,
    VendorProductSerializer,
)

# DOCUMENTATION RESPONSE SERIALIZERS

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(
        help_text="Description of the error."
    )


class OrderCreateResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    order = OrderSerializer()


# COMMON PATH PARAMETERS

PRODUCT_ID_PARAMETER = OpenApiParameter(
    name="id",
    type=int,
    location=OpenApiParameter.PATH,
    description="Unique product ID.",
)

CART_ITEM_ID_PARAMETER = OpenApiParameter(
    name="item_id",
    type=int,
    location=OpenApiParameter.PATH,
    description="Unique cart item ID.",
)


# CATEGORY API

@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        summary="Retrieve Categories",
        description="""
        Retrieves all active product categories.

        Authentication is not required.
        Returns category information in JSON format.
        """,
        responses={200: CategorySerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        summary="Retrieve Category Details",
        description="Retrieves details of a specific category.",
        responses={
            200: CategorySerializer,
            404: OpenApiResponse(description="Category not found."),
        },
    ),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    authentication_classes = []


# CUSTOMER PRODUCT API

@extend_schema_view(
    list=extend_schema(
        tags=["Products"],
        summary="Retrieve Products",
        description="""
        Retrieves the available products in the QELVORA store.

        Supported ordering:
        - price
        - -price
        - name
        - created_at
        - -created_at

        Authentication is not required.
        """,
        responses={200: ProductSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Products"],
        summary="Retrieve Product Details",
        description="Retrieves details of an individual product.",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
    ),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    filter_backends = [OrderingFilter]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["-created_at"]


# VENDOR PRODUCT CRUD API

@extend_schema_view(
    list=extend_schema(
        tags=["Vendor Products"],
        summary="Retrieve Vendor Products",
        description="""
        Retrieves products belonging to the authenticated
        approved vendor only.

        Requires an approved vendor account.
        """,
        responses={
            200: VendorProductSerializer(many=True),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(
                description="Approved vendor permission required."
            ),
        },
    ),
    retrieve=extend_schema(
        tags=["Vendor Products"],
        summary="Retrieve Vendor Product",
        description="Retrieves a product owned by the authenticated vendor.",
        parameters=[PRODUCT_ID_PARAMETER],
        responses={
            200: VendorProductSerializer,
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    create=extend_schema(
        tags=["Vendor Products"],
        summary="Add Vendor Product",
        description="""
        Creates a new product for the authenticated vendor.

        The vendor is automatically assigned from the authenticated user.
        Vendor ownership cannot be selected through this request.
        """,
        request=VendorProductSerializer,
        responses={
            201: VendorProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            403: OpenApiResponse(
                description="Approved vendor permission required."
            ),
        },
    ),
    update=extend_schema(
        tags=["Vendor Products"],
        summary="Update Vendor Product",
        description="Replaces the details of a vendor-owned product.",
        parameters=[PRODUCT_ID_PARAMETER],
        request=VendorProductSerializer,
        responses={
            200: VendorProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    partial_update=extend_schema(
        tags=["Vendor Products"],
        summary="Partially Update Vendor Product",
        description="""
        Updates selected fields of a vendor-owned product.
        Can be used to update product price or stock.
        """,
        parameters=[PRODUCT_ID_PARAMETER],
        request=VendorProductSerializer,
        responses={
            200: VendorProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    destroy=extend_schema(
        tags=["Vendor Products"],
        summary="Delete Vendor Product",
        description="Soft-deletes a product owned by the authenticated vendor.",
        parameters=[PRODUCT_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description="Product deleted successfully."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
)
class VendorProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = VendorProductSerializer
    permission_classes = [IsApprovedVendor]

    def get_queryset(self):
        return Product.objects.select_related(
            "category"
        ).filter(vendor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)


# ADMIN PRODUCT MANAGEMENT

@extend_schema_view(
    list=extend_schema(
        tags=["Admin Products"],
        summary="Retrieve All Products",
        description="Allows administrators to retrieve active products.",
        responses={200: AdminProductSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Admin Products"],
        summary="Retrieve Product",
        description="Retrieves details of an individual product.",
        parameters=[PRODUCT_ID_PARAMETER],
        responses={
            200: AdminProductSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    create=extend_schema(
        tags=["Admin Products"],
        summary="Create Product",
        description=(
            "Allows administrators to create products "
            "and optionally assign a vendor."
        ),
        request=AdminProductSerializer,
        responses={
            201: AdminProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            403: OpenApiResponse(
                description="Administrator permission required."
            ),
        },
    ),
    update=extend_schema(
        tags=["Admin Products"],
        summary="Update Product",
        description="Allows administrators to update product details.",
        parameters=[PRODUCT_ID_PARAMETER],
        request=AdminProductSerializer,
        responses={
            200: AdminProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    partial_update=extend_schema(
        tags=["Admin Products"],
        summary="Partially Update Product",
        description="Allows administrators to update selected product fields.",
        parameters=[PRODUCT_ID_PARAMETER],
        request=AdminProductSerializer,
        responses={
            200: AdminProductSerializer,
            400: OpenApiResponse(description="Invalid product details."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    destroy=extend_schema(
        tags=["Admin Products"],
        summary="Delete Product",
        description="Soft-deletes an active product.",
        parameters=[PRODUCT_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description="Product deleted successfully."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
)
class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        "category",
        "vendor",
    ).all().order_by("-id")

    serializer_class = AdminProductSerializer
    permission_classes = [IsAdmin]
    pagination_class = AdminProductPagination


# USER REGISTRATION

@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Register Customer",
        description="""
        Registers a new customer account.

        Username, email and password are required.
        Password validation follows Django password validators.

        No authentication is required.
        """,
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiResponse(
                description="Registration validation failed."
            ),
        },
    ),
)
class RegisterView(generics.CreateAPIView):
    queryset = RegisterSerializer.Meta.model.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# CURRENT USER

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Retrieve Current User",
        description="""
        Retrieves the profile information of the currently
        authenticated user.

        Requires a valid access token.

        Returns username, email, role, staff status
        and vendor approval status.
        """,
        responses={
            200: CurrentUserSerializer,
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                )
            ),
        },
    )
    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


# CART API

class CartView(APIView):
    permission_classes = [IsCustomerOrVendor]

    @extend_schema(
        tags=["Cart"],
        summary="Retrieve Shopping Cart",
        description="""
        Retrieves the shopping cart of the authenticated customer or vendor.

        Creates an empty cart if one does not already exist.
        Requires authentication.
        """,
        responses={
            200: CartSerializer,
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        tags=["Cart"],
        summary="Add Product to Cart",
        description="""
        Adds a product to the authenticated customer's or vendor's cart.

        If the product already exists in the cart,
        its quantity is increased.

        Requested quantity cannot exceed available stock.
        """,
        request=CartAddItemSerializer,
        responses={
            200: CartSerializer,
            400: ErrorResponseSerializer,
            404: OpenApiResponse(description="Product not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def post(self, request):
        serializer = CartAddItemSerializer(data=request.data)

        if not serializer.is_valid():
            error = next(iter(serializer.errors.values()))[0]

            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        product = get_object_or_404(Product, id=product_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not item_created:
            cart_item.quantity += quantity

        if cart_item.quantity > product.stock:
            return Response(
                {"error": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.save()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# CART ITEM UPDATE / DELETE

class CartItemDetailView(APIView):
    permission_classes = [IsCustomerOrVendor]

    @extend_schema(
        tags=["Cart"],
        summary="Update Cart Item Quantity",
        description="""
        Updates the quantity of a cart item belonging
        to the authenticated customer or vendor.

        Quantity must be at least 1 and cannot exceed
        the available product stock.
        """,
        parameters=[CART_ITEM_ID_PARAMETER],
        request=CartQuantityUpdateSerializer,
        responses={
            200: CartSerializer,
            400: ErrorResponseSerializer,
            404: OpenApiResponse(description="Cart item not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def patch(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
        )

        serializer = CartQuantityUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            error = next(iter(serializer.errors.values()))[0]

            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quantity = serializer.validated_data["quantity"]

        if quantity > cart_item.product.stock:
            return Response(
                {"error": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save()

        response_serializer = CartSerializer(cart_item.cart)

        return Response(response_serializer.data)

    @extend_schema(
        tags=["Cart"],
        summary="Remove Cart Item",
        description="""
        Removes a cart item belonging to the authenticated customer or vendor.

        Returns the updated shopping cart.
        """,
        parameters=[CART_ITEM_ID_PARAMETER],
        request=None,
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart item not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def delete(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
        )

        cart = cart_item.cart
        cart_item.delete()

        serializer = CartSerializer(cart)
        return Response(serializer.data)


# CREATE ORDER

class OrderCreateView(APIView):
    permission_classes = [IsCustomerOrVendor]

    @extend_schema(
        tags=["Orders"],
        summary="Place Customer Order",
        description="""
        Creates an order using the authenticated customer's or vendor's cart.

        Before creating the order, the API:
        - Checks whether the cart contains products.
        - Checks available product stock.
        - Calculates the total order price.
        - Creates the order and order items.
        - Reduces product stock.
        - Clears the customer's cart.

        The operation is performed within a database transaction.

        No request body is required.
        """,
        request=None,
        responses={
            201: OrderCreateResponseSerializer,
            400: ErrorResponseSerializer,
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Cart not found."),
        },
    )
    @transaction.atomic
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)

        cart_items = list(
            cart.items.select_related("product").all()
        )

        if not cart_items:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_price = 0

        for item in cart_items:
            product = Product.objects.select_for_update().get(
                id=item.product_id
            )

            if item.quantity > product.stock:
                return Response(
                    {
                        "error": f"Insufficient stock for {product.name}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total_price += product.price * item.quantity

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
        )

        for item in cart_items:
            product = Product.objects.select_for_update().get(
                id=item.product_id
            )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price,
            )

            product.stock -= item.quantity
            product.save(update_fields=["stock"])

        cart.items.all().delete()

        serializer = OrderSerializer(order)

        return Response(
            {
                "message": "Order placed successfully.",
                "order": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


# ORDER HISTORY

@extend_schema_view(
    get=extend_schema(
        tags=["Orders"],
        summary="Retrieve Customer Order History",
        description="""
        Retrieves the order history of the authenticated customer or vendor.

        Orders are returned in descending order of creation date.
        Each order includes its items and product details.

        A user can only retrieve their own orders.
        """,
        responses={
            200: OrderSerializer(many=True),
            401: OpenApiResponse(description="Authentication required."),
        },
    ),
)
class OrderHistoryView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsCustomerOrVendor]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items__product__category")
            .order_by("-created_at")
        )
