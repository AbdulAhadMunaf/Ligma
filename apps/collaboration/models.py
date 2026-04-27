import uuid

from django.contrib.auth.models import Group
from django.db import models

from apps.collaboration.choices import RoomRoleChoices
from apps.users.models import User
from utils.db.models import BaseModel


class CollaborationRoom(BaseModel):
    room_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_collaboration_rooms",
    )
    is_active = models.BooleanField(default=True)
    last_event_sequence = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @property
    def channel_name(self):
        return f"collab:room:{self.room_uuid}"


class CollaborationRoomMember(BaseModel):
    room = models.ForeignKey(
        CollaborationRoom,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="collaboration_room_memberships",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="collaboration_room_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=RoomRoleChoices.choices,
        default=RoomRoleChoices.EDITOR,
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_collaboration_room_members",
    )
    permissions = models.JSONField(default=dict, blank=True)
    last_seen_event_sequence = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("room", "user")
        ordering = ["created_at"]

    @property
    def can_edit(self):
        return self.role in {RoomRoleChoices.OWNER, RoomRoleChoices.EDITOR}

    @property
    def can_manage_members(self):
        return self.role == RoomRoleChoices.OWNER


class CollaborationRoomSnapshot(BaseModel):
    room = models.OneToOneField(
        CollaborationRoom,
        on_delete=models.CASCADE,
        related_name="snapshot",
    )
    scene_version = models.PositiveBigIntegerField(default=0)
    elements = models.JSONField(default=list, blank=True)
    app_state = models.JSONField(default=dict, blank=True)
    files = models.JSONField(default=dict, blank=True)
    library_items = models.JSONField(default=list, blank=True)
    last_event = models.ForeignKey(
        "CollaborationRoomEvent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_snapshot_for_rooms",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_collaboration_room_snapshots",
    )


class CollaborationNodeAccess(BaseModel):
    room = models.ForeignKey(
        CollaborationRoom,
        on_delete=models.CASCADE,
        related_name="node_access_entries",
    )
    node_id = models.CharField(max_length=255)
    allowed_roles = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_collaboration_nodes",
    )

    class Meta:
        unique_together = ("room", "node_id")
        ordering = ["node_id"]


class CollaborationRoomEvent(BaseModel):
    event_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    room = models.ForeignKey(
        CollaborationRoom,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collaboration_room_events",
    )
    event_type = models.CharField(max_length=64)
    sequence = models.PositiveBigIntegerField()
    payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    client_event_id = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=64, default="api")
    client_timestamp = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["sequence"]
        unique_together = (
            "room",
            "sequence",
        )
        indexes = [
            models.Index(fields=["room", "sequence"]),
            models.Index(fields=["room", "event_type"]),
        ]


class CollaborationTextOperation(BaseModel):
    room = models.ForeignKey(
        CollaborationRoom,
        on_delete=models.CASCADE,
        related_name="text_operations",
    )
    node_id = models.CharField(max_length=255)
    event = models.ForeignKey(
        CollaborationRoomEvent,
        on_delete=models.CASCADE,
        related_name="text_operations",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collaboration_text_operations",
    )
    base_version = models.PositiveBigIntegerField(default=0)
    applied_version = models.PositiveBigIntegerField()
    position = models.PositiveBigIntegerField()
    delete_count = models.PositiveBigIntegerField(default=0)
    insert_text = models.TextField(blank=True)
    client_id = models.CharField(max_length=255, default="")
    client_sequence = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["applied_version"]
        unique_together = (
            "room",
            "node_id",
            "applied_version",
        ), (
            "room",
            "node_id",
            "client_id",
            "client_sequence",
        )
        indexes = [
            models.Index(fields=["room", "node_id", "applied_version"]),
        ]
