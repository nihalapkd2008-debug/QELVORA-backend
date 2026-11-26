from django.core.exceptions import ObjectDoesNotExist
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
        except ObjectDoesNotExist:
            return False

        return (
            profile.role == "vendor"
            and profile.vendor_status == "approved"
        )


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            return False

        return profile.role == "customer"
class IsCustomerOrVendor(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            return False

        return profile.role in ["customer", "vendor"]