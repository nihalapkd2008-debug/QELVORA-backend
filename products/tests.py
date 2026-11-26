
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from products.models import Category, Product

User = get_user_model()


class ProductPermissionTests(APITestCase):

    def setUp(self):
        # Create Admin
        self.admin = User.objects.create_user(
            username="product_test_admin",
            password="TestPassword123!",
            is_staff=True,
        )

        # Create Customer
        self.customer = User.objects.create_user(
            username="product_test_customer",
            password="TestPassword123!",
        )

        # Create Approved Vendor
        self.vendor = User.objects.create_user(
            username="product_test_vendor",
            password="TestPassword123!",
        )

        vendor_profile = self.vendor.profile
        vendor_profile.role = UserProfile.Role.VENDOR
        vendor_profile.vendor_status = UserProfile.VendorStatus.APPROVED
        vendor_profile.save()

        # Create another Vendor
        self.other_vendor = User.objects.create_user(
            username="another_test_vendor",
            password="TestPassword123!",
        )

        other_profile = self.other_vendor.profile
        other_profile.role = UserProfile.Role.VENDOR
        other_profile.vendor_status = UserProfile.VendorStatus.APPROVED
        other_profile.save()

        # Create Category
        self.category = Category.objects.create(
            name="Test Clothing",
            description="Test product category",
        )

        # Create products
        self.vendor_product = Product.objects.create(
            category=self.category,
            vendor=self.vendor,
            name="Vendor Test Shirt",
            description="Test vendor product",
            price="1200.00",
            stock=10,
            image="https://example.com/shirt.jpg",
        )

        self.other_vendor_product = Product.objects.create(
            category=self.category,
            vendor=self.other_vendor,
            name="Another Vendor Shirt",
            description="Another vendor product",
            price="1500.00",
            stock=5,
            image="https://example.com/another-shirt.jpg",
        )

        self.admin_product = Product.objects.create(
            category=self.category,
            vendor=None,
            name="Admin Test Shirt",
            description="Admin-created product",
            price="1000.00",
            stock=20,
            image="https://example.com/admin-shirt.jpg",
        )

        self.admin_products_url = "/api/admin/products/"
        self.vendor_products_url = "/api/vendor/products/"

    def get_response_items(self, response):
        data = response.data

        if isinstance(data, dict):
            return data.get("results", [])

        return data

    # Admin Product API tests

    def test_admin_can_view_all_products(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.admin_products_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = self.get_response_items(response)

        self.assertEqual(len(products), 3)

    def test_customer_cannot_access_admin_products(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.admin_products_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_vendor_cannot_access_admin_products(self):
        self.client.force_authenticate(user=self.vendor)

        response = self.client.get(self.admin_products_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # Vendor Product API tests

    def test_approved_vendor_can_view_own_products(self):
        self.client.force_authenticate(user=self.vendor)

        response = self.client.get(self.vendor_products_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = self.get_response_items(response)
        product_ids = [product["id"] for product in products]

        self.assertIn(self.vendor_product.id, product_ids)
        self.assertNotIn(self.other_vendor_product.id, product_ids)

    def test_customer_cannot_access_vendor_products(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.vendor_products_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_cannot_access_vendor_products(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.vendor_products_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_pending_vendor_cannot_access_vendor_products(self):
        pending_vendor = User.objects.create_user(
            username="pending_test_vendor",
            password="TestPassword123!",
        )

        profile = pending_vendor.profile
        profile.role = UserProfile.Role.VENDOR
        profile.vendor_status = UserProfile.VendorStatus.PENDING
        profile.save()

        self.client.force_authenticate(user=pending_vendor)

        response = self.client.get(self.vendor_products_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
