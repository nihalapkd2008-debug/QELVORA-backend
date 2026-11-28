
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import IsAdmin

from .models import UserProfile, VendorApplication
from .serializers import (
    AdminUserSerializer,
    GoogleLoginSerializer,
    VendorApplicationReviewSerializer,
    VendorApplicationSerializer,
)

User = get_user_model()

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "role": profile.role if profile else "customer",
            "vendor_status": (
                profile.vendor_status if profile else "not_applicable"
            ),
        })

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            google_data = id_token.verify_oauth2_token(
                serializer.validated_data["credential"],
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response(
                {"detail": "Invalid Google token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not google_data.get("email_verified"):
            return Response(
                {"detail": "Google email is not verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        google_sub = google_data.get("sub")
        email = google_data.get("email", "").strip().lower()
        name = google_data.get("name", "").strip()

        if not google_sub or not email:
            return Response(
                {"detail": "Required Google account information is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            profile = (
                UserProfile.objects.select_for_update()
                .filter(google_sub=google_sub)
                .select_related("user")
                .first()
            )

            if profile:
                user = profile.user
                if not user.is_active:
                    return Response(
                        {"detail": "This account is inactive."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                if User.objects.filter(email__iexact=email).exists():
                    return Response(
                        {
                            "detail": (
                                "An account with this email already exists. "
                                "Please sign in using your existing login method."
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                username = f"google_{uuid.uuid4().hex[:12]}"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    first_name=name[:150],
                )

                profile = user.profile
                profile.google_sub = google_sub
                profile.save(update_fields=["google_sub"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

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

class AdminVendorApplicationListView(generics.ListAPIView):
    queryset = VendorApplication.objects.select_related(
        "user"
    ).order_by("-created_at")

    serializer_class = VendorApplicationSerializer
    permission_classes = [IsAdmin]


class AdminVendorApplicationDetailView(generics.RetrieveUpdateAPIView):
    queryset = VendorApplication.objects.select_related("user")

    serializer_class = VendorApplicationReviewSerializer
    permission_classes = [IsAdmin]

    http_method_names = ["get", "patch", "head", "options"]
