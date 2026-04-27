from utils.choices.choices import BaseChoices


class RoomEventTypeChoices(BaseChoices):
    SCENE_CHANGED = "scene.changed", "scene.changed"
    POINTER_UPDATED = "pointer.updated", "pointer.updated"
    PRESENCE_SYNCED = "presence.synced", "presence.synced"
    ROOM_JOINED = "room.joined", "room.joined"
    ROOM_LEFT = "room.left", "room.left"


class RoomRoleChoices(BaseChoices):
    OWNER = "owner", "owner"
    EDITOR = "editor", "editor"
    VIEWER = "viewer", "viewer"

