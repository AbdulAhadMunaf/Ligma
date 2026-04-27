from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

import apps.users.models as user_models


class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_filter = ("name",)


class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "name",
        "email",
    )
    search_fields = ("name", "email")
    list_filter = UserAdmin.list_filter + ()
    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            _("Personal info"),
            {
                "fields": ("name", "organization"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    # "username",
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    "name",
                    "organization",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )
    readonly_fields = (
        "date_joined",
        "last_login",
    )


# add UserModule, UserPermission admin classes


class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user")


class UserModuleAdmin(admin.ModelAdmin):
    list_display = ("user", "modules")


admin.site.register(user_models.User, CustomUserAdmin)
