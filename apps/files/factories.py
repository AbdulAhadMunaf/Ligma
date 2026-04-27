import factory
from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory

from apps.files.models import FileAttachment


class FileAttachmentFactory(DjangoModelFactory):
    class Meta:
        model = FileAttachment

    name = factory.Faker("file_name", extension="png")
    file = factory.LazyAttribute(
        lambda obj: ContentFile(b"fake image content", name=obj.name)
    )
    file_type = "image/png"
    tag = ""
