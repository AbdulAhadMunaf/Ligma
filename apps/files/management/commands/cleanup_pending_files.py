from django.core.management.base import BaseCommand

from apps.files.models import FileAttachment


class Command(BaseCommand):
    help = "Cleanup pending files that were uploaded but never attached to any object"

    def add_arguments(self, parser):
        parser.add_argument(
            "--older_than_hours",
            type=int,
            default=24,
            help="Delete files that are older than this many hours (default: 24 hours)",
        )

    def handle(self, *args, **kwargs):
        older_than_hours = kwargs["older_than_hours"]
        deleted_files_count = FileAttachment.cleanup_pending_files(older_than_hours)

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_files_count} pending files.")
        )
