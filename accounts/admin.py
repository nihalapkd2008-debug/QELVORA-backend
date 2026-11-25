from django.contrib import admin
from .models import UserProfile, VendorApplication


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "vendor_status")
    list_filter = ("role", "vendor_status")
    search_fields = ("user__username", "user__email")


@admin.register(VendorApplication)
class VendorApplicationAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("business_name", "user__username")

    actions = ["approve_vendors", "reject_vendors"]

    @admin.action(description="Approve selected vendors")
    def approve_vendors(self, request, queryset):
        for application in queryset:
            application.status = "approved"
            application.save(update_fields=["status"])

            profile = application.user.profile
            profile.role = "vendor"
            profile.vendor_status = "approved"
            profile.save(update_fields=["role", "vendor_status"])

    @admin.action(description="Reject selected vendors")
    def reject_vendors(self, request, queryset):
        for application in queryset:
            application.status = "rejected"
            application.save(update_fields=["status"])

            profile = application.user.profile
            profile.vendor_status = "rejected"
            profile.save(update_fields=["vendor_status"])