import factory
from factory.django import DjangoModelFactory

from apps.users import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User

    name = factory.Faker("name")
    email = factory.sequence(lambda n: "user+{}@backend.ai".format(n))
    password = factory.PostGenerationMethodCall("set_password", "secret_pwd")
    is_staff = False
    is_superuser = False
