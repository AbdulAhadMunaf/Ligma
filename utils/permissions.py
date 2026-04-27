from functools import wraps

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.permissions import BasePermission

from utils.exceptions.errors import CoreAuthorizedError


def access_required(
    groups: list = None, permissions: list = None, superuser_allowed=True
):
    """
    Custom decorator to check user group membership and permissions.

    :param groups: The required group(s) of the user. Can be a single group (str) or a list of groups.
    :param permissions: The required permission(s). Can be a single permission (str), a list of permissions, or None (optional).
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(self, request, *args, **kwargs):
            # Bypass all checks if the user is a superuser and superuser access is allowed
            if superuser_allowed and request.user.is_superuser:
                return view(self, request, *args, **kwargs)

            # Ensure groups are a list for consistency
            required_groups = groups if isinstance(groups, list) else [groups]

            # is staff user allowed.
            # if request.uuser is staffuser or admin user then allow

            # Check if the user belongs to any of the required groups
            if (
                groups
                and not request.user.groups.filter(name__in=required_groups).exists()
            ):
                raise PermissionDenied

            # Check permissions if provided
            if permissions:
                # Ensure permissions are a list for consistency
                required_permissions = (
                    permissions if isinstance(permissions, list) else [permissions]
                )
                permission_codenames = [f"{perm}" for perm in required_permissions]
                if not any(
                    request.user.has_perm(codename) for codename in permission_codenames
                ):
                    raise PermissionDenied

            # Proceed to the view if all checks pass
            return view(self, request, *args, **kwargs)

        return _wrapped_view

    return decorator


class IsSuperUser(BasePermission):
    """
    Allows access only to super users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsIamActive(BasePermission):
    """
    Allows access only to active users (IAM active check).
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_iam_active
        )


class EnforcePasswordReset(BasePermission):
    """
    Enforces password reset requirement.
    Blocks all protected APIs if pwd_reset_required = True,
    except for allowed paths (reset-password, /users/me, token refresh/verify).
    """

    # Allowed paths when password reset is required
    ALLOWED_PATHS = {
        "/auth/reset-password/",
        "/api/settings/users/me/",
        "/auth/token/refresh/",
        "/auth/token/verify/",
    }

    def has_permission(self, request, view):
        user = request.user

        # Allow unauthenticated requests (handled by other permissions)
        if not user or not user.is_authenticated:
            return True

        # If password reset is required, only allow specific paths
        if user.pwd_reset_required:
            # Normalize path (remove trailing slash for comparison)
            normalized_path = request.path.rstrip("/")
            allowed_paths_normalized = {path.rstrip("/") for path in self.ALLOWED_PATHS}

            if normalized_path not in allowed_paths_normalized:
                # Raise custom exception with proper error code
                raise DRFPermissionDenied(
                    detail={
                        "code": CoreAuthorizedError.PWD_RESET_REQUIRED.code,
                        "message": CoreAuthorizedError.PWD_RESET_REQUIRED.message,
                    }
                )

        return True


class IsAuthenticatedAndActive(BasePermission):
    """
    Combined permission that checks both password reset requirement and IAM active status.

    Use this when you need to set explicit permission_classes on a view.
    This ensures password reset enforcement is always checked along with IAM active status.

    Example:
        class MyAPI(APIView):
            permission_classes = [IsAuthenticatedAndActive]
    """

    def has_permission(self, request, view):
        user = request.user

        # Allow unauthenticated requests (handled by other permissions)
        if not user or not user.is_authenticated:
            return True

        # First check password reset requirement
        if user.pwd_reset_required:
            # Normalize path (remove trailing slash for comparison)
            normalized_path = request.path.rstrip("/")
            allowed_paths_normalized = {
                path.rstrip("/") for path in EnforcePasswordReset.ALLOWED_PATHS
            }

            if normalized_path not in allowed_paths_normalized:
                # Raise custom exception with proper error code
                raise DRFPermissionDenied(
                    detail={
                        "code": CoreAuthorizedError.PWD_RESET_REQUIRED.code,
                        "message": CoreAuthorizedError.PWD_RESET_REQUIRED.message,
                    }
                )

        # Then check IAM active status
        if not user.is_iam_active:
            return False

        return True
