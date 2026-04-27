from django.urls import path

from apps.settings.api.views.users_api import UserChangePasswordAPI, UserMeAPI

urlpatterns = [
    path(
        "users/change-password/",
        UserChangePasswordAPI.as_view(),
        name="user-change-password",
    ),
    path(
        "users/me/",
        UserMeAPI.as_view(),
        name="user-me",
    ),
]
