from django.contrib import admin

from apps.collaboration.models import (
    CollaborationNodeAccess,
    CollaborationRoom,
    CollaborationRoomEvent,
    CollaborationRoomMember,
    CollaborationRoomSnapshot,
    CollaborationTextOperation,
)


@admin.register(CollaborationRoom)
class CollaborationRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_uuid", "name", "created_by", "last_event_sequence")
    search_fields = ("name", "room_uuid", "created_by__email")


@admin.register(CollaborationRoomMember)
class CollaborationRoomMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "role", "group")
    search_fields = ("room__name", "user__email", "group__name")


@admin.register(CollaborationRoomSnapshot)
class CollaborationRoomSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "scene_version", "updated_by")


@admin.register(CollaborationNodeAccess)
class CollaborationNodeAccessAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "node_id", "allowed_roles", "locked_by")
    search_fields = ("room__name", "node_id")


@admin.register(CollaborationRoomEvent)
class CollaborationRoomEventAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sequence", "event_type", "actor", "source")
    search_fields = ("room__name", "event_type", "actor__email", "client_event_id")


@admin.register(CollaborationTextOperation)
class CollaborationTextOperationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "node_id",
        "base_version",
        "applied_version",
        "position",
        "delete_count",
    )
    search_fields = ("room__name", "node_id", "actor__email")
