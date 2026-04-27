import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from apps.users.factories import UserFactory


@pytest.mark.django_db
class TestChangePasswordAPI:
    """Tests for ChangePasswordAPI"""

    def test_change_password_success(self, api_client):
        """Test successful password change"""
        user = UserFactory(is_active=True)
        user.set_password("oldpassword123")
        user.save()

        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password changed successfully."

        # Verify password was actually changed
        user.refresh_from_db()
        assert user.check_password("newpassword123")
        assert not user.check_password("oldpassword123")

    def test_change_password_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot change password"""
        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_passwords_dont_match(self, api_client):
        """Test that passwords must match"""
        user = UserFactory(is_active=True)
        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            "confirm_password": "differentpassword123",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "confirm_password" in str(response.json())

    def test_change_password_missing_fields(self, api_client):
        """Test that missing required fields return validation error"""
        user = UserFactory(is_active=True)
        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            # Missing confirm_password
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_empty_fields(self, api_client):
        """Test that empty password fields return validation error"""
        user = UserFactory(is_active=True)
        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "",
            "confirm_password": "",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_user_can_login_with_new_password(self, api_client):
        """Test that user can login with new password after change"""
        user = UserFactory(is_active=True)
        old_password = "oldpassword123"
        user.set_password(old_password)
        user.save()

        # Change password
        api_client.force_authenticate(user=user)
        url = reverse("change_password")
        new_password = "newpassword123"
        data = {
            "new_password": new_password,
            "confirm_password": new_password,
        }
        response = api_client.post(url, data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Verify old password no longer works
        user.refresh_from_db()
        assert not user.check_password(old_password)
        assert user.check_password(new_password)

    def test_change_password_multiple_times(self, api_client):
        """Test that user can change password multiple times"""
        user = UserFactory(is_active=True)
        password1 = "password1"
        user.set_password(password1)
        user.save()

        api_client.force_authenticate(user=user)
        url = reverse("change_password")

        # First password change
        password2 = "password2"
        data = {
            "new_password": password2,
            "confirm_password": password2,
        }
        response = api_client.post(url, data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password(password2)
        assert not user.check_password(password1)

        # Second password change
        password3 = "password3"
        data = {
            "new_password": password3,
            "confirm_password": password3,
        }
        response = api_client.post(url, data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password(password3)
        assert not user.check_password(password2)
        assert not user.check_password(password1)

    def test_change_password_clears_pwd_reset_required(self, api_client):
        """Test that changing password sets pwd_reset_required to False"""
        user = UserFactory(is_active=True, pwd_reset_required=True)
        user.set_password("oldpassword123")
        user.save()

        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify pwd_reset_required is set to False
        user.refresh_from_db()
        assert user.pwd_reset_required is False

    def test_change_password_maintains_pwd_reset_required_false(self, api_client):
        """Test that changing password maintains pwd_reset_required=False if already False"""
        user = UserFactory(is_active=True, pwd_reset_required=False)
        user.set_password("oldpassword123")
        user.save()

        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        response = api_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify pwd_reset_required remains False
        user.refresh_from_db()
        assert user.pwd_reset_required is False
