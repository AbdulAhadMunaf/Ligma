from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.choices import UserPermissionChoices
from apps.users.manager import UserManager
from utils.db.models import BaseModel


class User(AbstractUser, BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(_("email address"), unique=True)
    pwd_reset_required = models.BooleanField(default=False)
    first_name = None
    last_name = None
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        ordering = [
            "name",
            "email",
        ]
        permissions = [(key, value) for key, value in UserPermissionChoices.choices]

    @property
    def group_id(self):
        group_obj = self.groups.first()
        if group_obj:
            return group_obj.id
        return None

    @property
    def group(self):
        group_obj = self.groups.first()
        if group_obj:
            return group_obj.name

    @property
    def permissions(self):
        group_obj = self.groups.first()
        if group_obj:
            permissions = Permission.objects.filter(group__user=self).values_list(
                "codename", flat=True
            )
            return permissions
        return []

    @property
    def is_iam_active(self):
        """
        Determines whether the user is active based on their role.
        - Superadmin: Only the user's `is_active` is checked.
        """
        return self.is_active

    def save(self, *args, **kwargs):
        """Override save to ensure email is always stored in lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
