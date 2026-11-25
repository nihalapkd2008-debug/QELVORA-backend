from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsApprovedVendor(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            profile = user.profile
            return (
                profile.role == "vendor"
                and profile.vendor_status == "approved"
            )
        except Exception:
            return False


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            return user.profile.role == "customer"
        except Exception:
            return False