from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin

from .serializers import AdminUserSerializer, VendorApplicationSerializer

User = get_user_model()

class VendorApplicationView(generics.CreateAPIView):
    serializer_class = VendorApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        profile = self.request.user.profile
        profile.role = "vendor"
        profile.vendor_status = "pending"
        profile.save(update_fields=["role", "vendor_status"])


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "patch", "head", "options"]


