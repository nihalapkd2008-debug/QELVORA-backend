
from django.urls import path

from .views import (
    AdminUserDetailView,
    AdminUserListView,
    AdminVendorApplicationDetailView,
    AdminVendorApplicationListView,
    GoogleLoginView,
    VendorApplicationView,
    CurrentUserView
)

urlpatterns = [

path(
    "google-login/",
    GoogleLoginView.as_view(),
    name="google-login",
),
    path(
        "vendor/apply/",
        VendorApplicationView.as_view(),
        name="vendor-application",
    ),
    path(
        "admin/users/",
        AdminUserListView.as_view(),
        name="admin-users",
    ),
    path(
        "admin/users/<int:pk>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail",
    ),
    path(
    "admin/vendor-applications/",
    AdminVendorApplicationListView.as_view(),
    name="admin-vendor-applications",
),
path(
    "admin/vendor-applications/<int:pk>/",
    AdminVendorApplicationDetailView.as_view(),
    name="admin-vendor-application-detail",
),

path(
    "me/",
    CurrentUserView.as_view(),
    name="current-user",
),

]
