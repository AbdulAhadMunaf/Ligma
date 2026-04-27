import pytest
from datetime import date
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse

from apps.candidate import factories as candidate_factories
from apps.candidate import models as candidate_models
from apps.company import factories as company_factories
from apps.users import factories as user_factories
from apps.users.choices import UserGroupChoices


@pytest.mark.django_db
class TestUserMeAPI:
    def _add_group(self, user, group_name):
        """Helper to add group to user"""
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        return user

    def test_get_user_me_as_candidate(self, api_client):
        """Test getting user info as candidate"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.CANDIDATE.value)
        candidate = candidate_models.Candidate.objects.create(
            user=user,
            full_name="Test Candidate",
            nationality=candidate_factories.NationalityFactory(),
            gender=candidate_models.Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            years_of_professional_experience=candidate_factories.YearsOfProfessionalExperienceFactory(),
            current_location=candidate_factories.CountryFactory(),
        )
        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert UserGroupChoices.CANDIDATE.value in data["groups"]
        assert data["candidate_id"] == candidate.id

    def test_get_user_me_as_company_admin(self, api_client):
        """Test getting user info as company admin"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.COMPANY_ADMIN.value)
        company_member = company_factories.CompanyMemberFactory(user=user)
        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert UserGroupChoices.COMPANY_ADMIN.value in data["groups"]
        assert data["company_member_id"] == company_member.id

    def test_get_user_me_as_company_recruiter(self, api_client):
        """Test getting user info as company recruiter"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.COMPANY_RECRUITER.value)
        company_member = company_factories.CompanyMemberFactory(user=user)
        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert UserGroupChoices.COMPANY_RECRUITER.value in data["groups"]
        assert data["company_member_id"] == company_member.id

    def test_get_user_me_as_company_hiring_manager(self, api_client):
        """Test getting user info as company hiring manager"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.COMPANY_HIRING_MANAGER.value)
        company_member = company_factories.CompanyMemberFactory(user=user)
        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert UserGroupChoices.COMPANY_HIRING_MANAGER.value in data["groups"]
        assert data["company_member_id"] == company_member.id

    def test_get_user_me_with_multiple_company_groups(self, api_client):
        """User with multiple company groups (admin and recruiter)"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.COMPANY_ADMIN.value)
        self._add_group(user, UserGroupChoices.COMPANY_RECRUITER.value)
        company_member = company_factories.CompanyMemberFactory(user=user)

        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # `groups` should contain all user groups
        assert UserGroupChoices.COMPANY_ADMIN.value in data["groups"]
        assert UserGroupChoices.COMPANY_RECRUITER.value in data["groups"]
        assert len(data["groups"]) == 2

        # Should have company_member_id since first group is a company group
        assert data["company_member_id"] == company_member.id
        assert "candidate_id" not in data

    def test_get_user_me_with_all_three_company_groups(self, api_client):
        """User with all three company groups"""
        user = user_factories.UserFactory(is_active=True)
        self._add_group(user, UserGroupChoices.COMPANY_ADMIN.value)
        self._add_group(user, UserGroupChoices.COMPANY_RECRUITER.value)
        self._add_group(user, UserGroupChoices.COMPANY_HIRING_MANAGER.value)
        company_member = company_factories.CompanyMemberFactory(user=user)

        api_client.force_authenticate(user=user)

        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # `groups` should contain all three company groups
        assert UserGroupChoices.COMPANY_ADMIN.value in data["groups"]
        assert UserGroupChoices.COMPANY_RECRUITER.value in data["groups"]
        assert UserGroupChoices.COMPANY_HIRING_MANAGER.value in data["groups"]
        assert len(data["groups"]) == 3

        # Should have company_member_id
        assert data["company_member_id"] == company_member.id
        assert "candidate_id" not in data

    def test_get_user_me_unauthenticated(self, api_client):
        """Test getting user info without authentication"""
        url = reverse("user-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
