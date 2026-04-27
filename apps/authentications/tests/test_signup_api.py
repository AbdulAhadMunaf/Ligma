import pytest
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse

from apps.users.choices import UserGroupChoices
from apps.users.factories import UserFactory


@pytest.mark.django_db
class TestSignupAPI:
    def setup_method(self):
        """Setup test data"""
        # Ensure groups exist
        Group.objects.get_or_create(name=UserGroupChoices.SUPER_ADMIN.value)

    def test_signup_success(self, api_client):
        """Test successful user signup"""
        url = reverse("signup_api")
        data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
        }

        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "User created successfully."
        assert response.json()["data"]["user"]["email"] == "test@example.com"
        assert response.json()["data"]["user"]["name"] == "test@example.com"
        assert "token" in response.json()["data"]
        assert "access" in response.json()["data"]["token"]
        assert "refresh" in response.json()["data"]["token"]

    def test_signup_duplicate_email(self, api_client):
        """Test signup with existing email"""
        # Create existing user
        UserFactory(email="existing@example.com")

        url = reverse("signup_api")
        data = {
            "email": "existing@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
        }

        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_missing_fields(self, api_client):
        """Test signup with missing required fields"""
        url = reverse("signup_api")
        data = {
            # Missing email, password, confirm_password
        }

        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_invalid_email_format(self, api_client):
        """Test signup with invalid email format"""
        url = reverse("signup_api")
        data = {
            "email": "invalid-email",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
        }

        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
