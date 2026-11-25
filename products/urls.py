
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CategoryViewSet,
    ProductViewSet,
    RegisterView,
    CurrentUserView,
    CartView,
    CartItemDetailView,
    OrderCreateView,
    OrderHistoryView,
    VendorProductViewSet,
    AdminProductViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register(
    "vendor/products",
    VendorProductViewSet,
    basename="vendor-products"
)
router.register(
    "admin/products",
    AdminProductViewSet,
    basename="admin-products"
)


urlpatterns = [
    # Authentication
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="current_user"),

    # Cart
    path("cart/", CartView.as_view(), name="cart"),
    path(
        "cart/items/<int:item_id>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail"
    ),

    # Day 5 - Orders
    path("orders/", OrderCreateView.as_view(), name="order-create"),
    path("orders/history/", OrderHistoryView.as_view(), name="order-history"),
]

urlpatterns += router.urls
