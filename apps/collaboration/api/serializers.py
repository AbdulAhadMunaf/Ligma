from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.collaboration.choices import RoomRoleChoices
from apps.collaboration.models import (
    CollaborationNodeAccess,
    CollaborationRoom,
    CollaborationRoomEvent,
    CollaborationRoomMember,
)

User = get_user_model()


class CollaborationRoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    metadata = serializers.JSONField(required=False)


class CollaborationRoomMemberUpsertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=RoomRoleChoices.choices)


class CollaborationRoomEventCreateSerializer(serializers.Serializer):
    payload = serializers.JSONField()
    publish_to_centrifugo = serializers.BooleanField(required=False, default=False)


class CollaborationNodeAccessUpsertSerializer(serializers.Serializer):
    node_id = serializers.CharField(max_length=255)
    allowed_roles = serializers.ListField(
        child=serializers.ChoiceField(choices=RoomRoleChoices.choices),
        allow_empty=False,
    )
    metadata = serializers.JSONField(required=False)


class CollaborationProxyPublishSerializer(serializers.Serializer):
    channel = serializers.CharField()
    data = serializers.JSONField()
    user = serializers.CharField(required=False, allow_blank=True)
    client = serializers.CharField(required=False, allow_blank=True)


class CollaborationRoomMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = CollaborationRoomMember
        fields = (
            "id",
            "user_id",
            "email",
            "name",
            "role",
            "group_name",
            "permissions",
            "last_seen_event_sequence",
        )


class CollaborationNodeAccessSerializer(serializers.ModelSerializer):
    locked_by_id = serializers.IntegerField(source="locked_by.id", read_only=True)

    class Meta:
        model = CollaborationNodeAccess
        fields = ("id", "node_id", "allowed_roles", "metadata", "locked_by_id")


class CollaborationRoomSerializer(serializers.ModelSerializer):
    created_by_id = serializers.IntegerField(source="created_by.id", read_only=True)
    members = CollaborationRoomMemberSerializer(many=True, read_only=True)

    class Meta:
        model = CollaborationRoom
        fields = (
            "id",
            "room_uuid",
            "name",
            "metadata",
            "created_by_id",
            "is_active",
            "last_event_sequence",
            "members",
        )


class CollaborationRoomEventSerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(source="actor.id", read_only=True)
    node_ids = serializers.SerializerMethodField()

    class Meta:
        model = CollaborationRoomEvent
        fields = (
            "id",
            "event_uuid",
            "sequence",
            "event_type",
            "payload",
            "metadata",
            "client_event_id",
            "client_timestamp",
            "source",
            "actor_id",
            "node_ids",
            "created_at",
        )

    def get_node_ids(self, instance):
        payload = instance.payload or {}
        operations = payload.get("operations") or []
        if operations:
            node_ids = []
            for operation in operations:
                node_id = operation.get("node_id") or operation.get("element", {}).get("id")
                if node_id:
                    node_ids.append(node_id)
            return node_ids
        return [element.get("id") for element in payload.get("elements", []) if element.get("id")]
