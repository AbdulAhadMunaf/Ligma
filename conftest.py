import tempfile
from pathlib import Path

import pytest
from django.test.utils import override_settings
from rest_framework.test import APIClient

from apps.users import factories as user_factories


@pytest.fixture(scope="session")
def celery_config():
    with override_settings(
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
        CELERY_RESULT_BACKEND="cache+memory://",
    ):
        yield


@pytest.fixture(autouse=True)
def temp_file_storage_setting(settings):
    settings.MEDIA_ROOT = Path(tempfile.gettempdir())


@pytest.fixture(autouse=True)
def enable_db_access(db):
    """This method (fixture) will enable db access globally for all tests"""
    pass


@pytest.fixture
def admin_user():
    user = user_factories.UserFactory.create(
        name="admin",
        email="admin@backend.ai",
        password="secret_pwd",
        is_superuser=True,
        is_staff=True,
    )

    return user


@pytest.fixture
def bob_user():
    return user_factories.UserFactory.create(
        name="bob",
        email="bob@backend.ai",
        password="secret_pwd",
        is_superuser=False,
        is_staff=False,
    )


@pytest.fixture
def user():
    return user_factories.UserFactory.create(
        name="bob",
        password="secret_pwd",
    )


@pytest.fixture
def secret_pwd():
    return "secret_pwd"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user_api_client(admin_user):
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def bob_user_api_client(bob_user):
    api_client = APIClient()
    api_client.force_authenticate(user=bob_user)
    yield api_client
    api_client.force_authenticate(user=None)
