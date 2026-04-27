from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from utils.db.models import BaseModel


# Create your models here.
class FileAttachment(BaseModel):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    content_object = GenericForeignKey("content_type", "object_id")

    name = models.CharField(max_length=255)  # Always stores the original file name
    file = models.FileField(upload_to="attachments/")
    file_type = models.CharField(max_length=100, blank=True)  # Store MIME type
    tag = models.CharField(max_length=100, blank=True)

    def delete(self, *args, **kwargs):
        """Ensure file is deleted from S3 before deleting model instance"""
        self.file.delete(save=False)
        super().delete(*args, **kwargs)

    @classmethod
    def cleanup_pending_files(cls, older_than_hours=24):
        """Delete files that are not attached to any object (object_id is NULL) and older than a threshold"""
        from datetime import timedelta

        from django.utils.timezone import now

        threshold_time = now() - timedelta(hours=older_than_hours)
        pending_files = cls.objects.filter(
            object_id__isnull=True,
            created_at__lt=threshold_time,
        )

        for file_attachment in pending_files:
            file_attachment.delete()  # This ensures the file itself is deleted

        return pending_files.count()  # Return number of files deleted

    @classmethod
    def associate_files_with_content(cls, content_model, content_id, file_ids):
        """Associates the given file IDs with a specific content object."""
        try:
            # Get the ContentType for the provided model dynamically
            content_type = ContentType.objects.get_for_model(content_model)

            # Get the content instance by its ID
            content_instance = content_model.objects.get(id=content_id)

            # Get the files by their IDs and only those who are not assigned
            files = cls.objects.filter(id__in=file_ids, object_id__isnull=True)

            # Associate each file with the content
            for file in files:
                file.content_type = content_type
                file.object_id = content_instance.id
                file.save()

            return files
        except ContentType.DoesNotExist:
            raise ValueError(
                f"Content type for model {content_model.__name__} does not exist."
            )
        except content_model.DoesNotExist:
            raise ValueError(
                f"Content with ID {content_id} not found for model {content_model.__name__}."
            )
        except cls.DoesNotExist:
            raise ValueError("One or more files not found.")
