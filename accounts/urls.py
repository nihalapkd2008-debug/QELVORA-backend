from django.urls import path
from .views import VendorApplicationView
from .views import AdminUserListView, AdminUserDetailView
urlpatterns = [
    path(
        "vendor/apply/",
        VendorApplicationView.as_view(),
        name="vendor-application",
    ),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
path(
    "admin/users/<int:pk>/",
    AdminUserDetailView.as_view(),
    name="admin-user-detail"
),
]