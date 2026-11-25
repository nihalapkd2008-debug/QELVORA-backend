
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile


User = get_user_model()


class AdminUserPermissionTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="test_admin",
            password="TestPassword123!",
            is_staff=True,
        )

        self.customer = User.objects.create_user(
            username="test_customer",
            password="TestPassword123!",
        )

        self.vendor = User.objects.create_user(
            username="test_vendor",
            password="TestPassword123!",
        )

        vendor_profile = self.vendor.profile
        vendor_profile.role = UserProfile.Role.VENDOR
        vendor_profile.vendor_status = UserProfile.VendorStatus.APPROVED
        vendor_profile.save()

        self.admin_url = "/api/accounts/admin/users/"

    def test_admin_can_view_users(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_cannot_view_admin_users(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_cannot_view_admin_users(self):
        self.client.force_authenticate(user=self.vendor)

        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_view_admin_users(self):
        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VendorApplicationTests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="vendor_applicant",
            password="TestPassword123!",
        )

        self.application_url = "/api/accounts/vendor/apply/"

    def test_customer_can_submit_vendor_application(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.application_url,
            {
                "business_name": "Test Fashion Store",
                "description": "Fashion and clothing products",
                "contact_email": "testvendor@example.com",
                "contact_phone": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.customer.profile.refresh_from_db()

        self.assertEqual(
            self.customer.profile.role,
            UserProfile.Role.VENDOR,
        )

        self.assertEqual(
            self.customer.profile.vendor_status,
            UserProfile.VendorStatus.PENDING,
        )
