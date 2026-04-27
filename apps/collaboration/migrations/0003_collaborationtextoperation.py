from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("collaboration", "0002_collaborationnodeaccess"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CollaborationTextOperation",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("node_id", models.CharField(max_length=255)),
                ("base_version", models.PositiveBigIntegerField(default=0)),
                ("applied_version", models.PositiveBigIntegerField()),
                ("position", models.PositiveBigIntegerField()),
                ("delete_count", models.PositiveBigIntegerField(default=0)),
                ("insert_text", models.TextField(blank=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="collaboration_text_operations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="text_operations",
                        to="collaboration.collaborationroomevent",
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="text_operations",
                        to="collaboration.collaborationroom",
                    ),
                ),
            ],
            options={"ordering": ["applied_version"]},
        ),
        migrations.AddIndex(
            model_name="collaborationtextoperation",
            index=models.Index(
                fields=["room", "node_id", "applied_version"],
                name="collaborati_room_id_4b8ecf_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="collaborationtextoperation",
            unique_together={("room", "node_id", "applied_version")},
        ),
    ]
