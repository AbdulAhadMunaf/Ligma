import os

from django.test.runner import DiscoverRunner

from core.settings import *  # noqa: F403

UNDER_TEST = True
MOCK_EXTERNAL_SERVICES = True
MESSAGING_SYSTEM = "noop"


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    """

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps

        self.unmanaged_models = [m for m in apps.get_models() if not m._meta.managed]
        for m in self.unmanaged_models:
            m._meta.managed = True
        super(UnManagedModelTestRunner, self).setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).teardown_test_environment(*args, **kwargs)
        # reset unmanaged models
        for m in self.unmanaged_models:
            m._meta.managed = False


# Since we can't create a test db on the read-only host, and we
# want our test dbs created with sqlite rather than the default
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),  # noqa: F405
    },
}

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable Celery for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "memory://"

# Skip the migrations by setting "MIGRATION_MODULES"
# to the DisableMigrations class defined above
MIGRATION_MODULES = DisableMigrations()

# Set Django's test runner to the custom class defined above
TEST_RUNNER = "unit_test_settings.UnManagedModelTestRunner"
