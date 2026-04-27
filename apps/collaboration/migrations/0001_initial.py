from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CollaborationRoom",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("room_uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("last_event_sequence", models.PositiveBigIntegerField(default=0)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_collaboration_rooms",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CollaborationRoomEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("event_type", models.CharField(max_length=64)),
                ("sequence", models.PositiveBigIntegerField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("client_event_id", models.CharField(blank=True, max_length=255)),
                ("source", models.CharField(default="api", max_length=64)),
                ("client_timestamp", models.BigIntegerField(blank=True, null=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="collaboration_room_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="collaboration.collaborationroom",
                    ),
                ),
            ],
            options={"ordering": ["sequence"]},
        ),
        migrations.CreateModel(
            name="CollaborationRoomSnapshot",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("scene_version", models.PositiveBigIntegerField(default=0)),
                ("elements", models.JSONField(blank=True, default=list)),
                ("app_state", models.JSONField(blank=True, default=dict)),
                ("files", models.JSONField(blank=True, default=dict)),
                ("library_items", models.JSONField(blank=True, default=list)),
                (
                    "last_event",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="current_snapshot_for_rooms",
                        to="collaboration.collaborationroomevent",
                    ),
                ),
                (
                    "room",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snapshot",
                        to="collaboration.collaborationroom",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_collaboration_room_snapshots",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CollaborationRoomMember",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("owner", "owner"), ("editor", "editor"), ("viewer", "viewer")], default="editor", max_length=32)),
                ("permissions", models.JSONField(blank=True, default=dict)),
                ("last_seen_event_sequence", models.PositiveBigIntegerField(default=0)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="collaboration_room_memberships",
                        to="auth.group",
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invited_collaboration_room_members",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="collaboration.collaborationroom",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="collaboration_room_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="collaborationroomevent",
            index=models.Index(fields=["room", "sequence"], name="collaborati_room_id_ae188f_idx"),
        ),
        migrations.AddIndex(
            model_name="collaborationroomevent",
            index=models.Index(fields=["room", "event_type"], name="collaborati_room_id_9f071f_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="collaborationroomevent",
            unique_together={("room", "sequence")},
        ),
        migrations.AlterUniqueTogether(
            name="collaborationroommember",
            unique_together={("room", "user")},
        ),
    ]
