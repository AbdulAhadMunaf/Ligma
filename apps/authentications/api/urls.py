from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from apps.authentications.api.views import (
    ForgotPasswordAPI,
    LoginAPIView,
    RefreshTokenAPIView,
    ResetPasswordAPI,
    SignUpAPIView,
    ChangePasswordAPI,
)

urlpatterns = [
    path("token/", LoginAPIView.as_view(), name="login_api"),
    path("token/refresh/", RefreshTokenAPIView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("forgot-password/", ForgotPasswordAPI.as_view()),
    path("reset-password/", ResetPasswordAPI.as_view()),
    path("signup/", SignUpAPIView.as_view(), name="signup_api"),
    path("change-password/", ChangePasswordAPI.as_view(), name="change_password"),
]
