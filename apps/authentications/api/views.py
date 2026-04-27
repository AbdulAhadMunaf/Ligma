import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentications.api.serializers import AuthenticationChangePasswordSerializer

from apps.authentications.api.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    SignUpSerializer,
    TokenRefreshSerializer,
    UserLoginSerializer,
)
from apps.users.models import User
from utils import utils
from utils.response.resp import APIResponse

logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        req_data = request.data
        login_serializer = LoginSerializer(data=req_data)

        if not login_serializer.is_valid():
            return Response(
                APIResponse.get_response(
                    message="Validation error",
                    error=login_serializer.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=req_data["email"])
        except User.DoesNotExist:
            return Response(
                APIResponse.get_response(
                    message="No user found with this email address.",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the user is active using custom logic (is_iam_active)
        if not user.is_iam_active:
            raise AuthenticationFailed

        # Update last login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        user_serializer = UserLoginSerializer(user)
        data = {
            "user": user_serializer.data,
            "token": login_serializer.validated_data,
        }
        return Response(
            APIResponse.get_response(
                data=data,
            )
        )


class RefreshTokenAPIView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(request_body=TokenRefreshSerializer)
    def post(self, request):
        req_data = request.data
        serializer = TokenRefreshSerializer(data=req_data)
        serializer.is_valid(raise_exception=True)
        data = {
            "token": serializer.validated_data,
        }
        return Response(
            APIResponse.get_response(
                data=data,
            )
        )


class ForgotPasswordAPI(APIView):
    permission_classes = (AllowAny,)
    """
    Handles sending a password reset email with a token.
    """

    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        user = User.objects.filter(email=email).first()

        # If a user exists, generate and send the reset token
        if user and user.is_iam_active:
            token = utils.generate_token(dict(user_id=user.id))
            reset_link = f"{settings.FRONTEND_URL}/reset-password/?token={token}"

            # Send email (this happens silently even if the email doesn't exist)
            email = EmailMessage(
                subject="Password Reset Request",
                body=f"Click the link below to reset your password:\n{reset_link}",
                to=[email],
            )

            try:
                email.send()
                logger.info("Email sent successfully!")
            except Exception as e:
                logger.error("Error while sending email:", e)

        # Always return the same response regardless of whether the user exists
        return Response(
            APIResponse.get_response(
                message="Email has been sent.", data={"token": token}
            )
        )


class ResetPasswordAPI(APIView):
    permission_classes = (AllowAny,)
    """
    Handles password reset using a token.
    """

    @swagger_auto_schema(request_body=PasswordResetSerializer)
    def post(self, request):
        # Validate new password
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        # Validate token and retrieve user ID
        data = utils.validate_token(token)
        if not data:
            # TODO: generic exception raise
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = data.get("user_id")
        user = get_object_or_404(User, id=user_id)

        if user and not user.is_iam_active:
            raise AuthenticationFailed

        # Set new password and clear password reset requirement
        user.set_password(serializer.validated_data["password"])
        user.pwd_reset_required = False
        user.save()

        return Response(
            APIResponse.get_response(
                message="Password has been reset successfully.",
            ),
            status=status.HTTP_200_OK,
        )


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=AuthenticationChangePasswordSerializer)
    def post(self, request):
        serializer = AuthenticationChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.pwd_reset_required = False
        user.save()
        return Response(
            APIResponse.get_response(message="Password changed successfully."),
            status=status.HTTP_200_OK,
        )


class SignUpAPIView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(request_body=SignUpSerializer)
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        user_serializer = UserLoginSerializer(user)
        data = {
            "user": user_serializer.data,
            "token": tokens,
        }
        return Response(
            APIResponse.get_response(message="User created successfully.", data=data),
            status=status.HTTP_201_CREATED,
        )
