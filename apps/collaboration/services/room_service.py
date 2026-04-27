from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.collaboration.choices import RoomEventTypeChoices, RoomRoleChoices
from apps.collaboration.models import (
    CollaborationNodeAccess,
    CollaborationRoom,
    CollaborationRoomEvent,
    CollaborationRoomMember,
    CollaborationRoomSnapshot,
    CollaborationTextOperation,
)
from apps.collaboration.services.centrifugo_service import CentrifugoService
from apps.users.models import User


class CollaborationRoomService:
    role_group_map = {
        RoomRoleChoices.OWNER: "collaboration_owner",
        RoomRoleChoices.EDITOR: "collaboration_editor",
        RoomRoleChoices.VIEWER: "collaboration_viewer",
    }

    @classmethod
    def _get_role_group(cls, role):
        group_name = cls.role_group_map[role]
        group, _ = Group.objects.get_or_create(name=group_name)
        return group

    @classmethod
    @transaction.atomic
    def create_room(cls, *, creator, name, metadata=None):
        room = CollaborationRoom.objects.create(
            name=name,
            metadata=metadata or {},
            created_by=creator,
        )
        cls.upsert_member(
            room=room,
            actor=creator,
            member_user=creator,
            role=RoomRoleChoices.OWNER,
            skip_permission_check=True,
        )
        CollaborationRoomSnapshot.objects.create(room=room, updated_by=creator)
        return room

    @classmethod
    def get_room_or_404(cls, room_uuid):
        return get_object_or_404(
            CollaborationRoom.objects.select_related("created_by", "snapshot"),
            room_uuid=room_uuid,
            is_active=True,
        )

    @classmethod
    def get_membership(cls, *, room, user):
        membership = (
            CollaborationRoomMember.objects.select_related("group", "user")
            .filter(room=room, user=user)
            .first()
        )
        if not membership:
            raise PermissionDenied("You are not a member of this room.")
        return membership

    @classmethod
    def assert_can_view(cls, *, room, user):
        return cls.get_membership(room=room, user=user)

    @classmethod
    def assert_can_edit(cls, *, room, user):
        membership = cls.get_membership(room=room, user=user)
        if not membership.can_edit:
            raise PermissionDenied("You do not have permission to edit this room.")
        return membership

    @classmethod
    def assert_can_manage_members(cls, *, room, user):
        membership = cls.get_membership(room=room, user=user)
        if not membership.can_manage_members:
            raise PermissionDenied("You do not have permission to manage room members.")
        return membership

    @classmethod
    @transaction.atomic
    def upsert_member(
        cls,
        *,
        room,
        actor,
        member_user,
        role,
        skip_permission_check=False,
    ):
        if not skip_permission_check:
            cls.assert_can_manage_members(room=room, user=actor)

        group = cls._get_role_group(role)
        membership, _ = CollaborationRoomMember.objects.update_or_create(
            room=room,
            user=member_user,
            defaults={
                "group": group,
                "role": role,
                "permissions": cls.build_permissions(role),
                "invited_by": actor,
            },
        )
        return membership

    @classmethod
    def build_permissions(cls, role):
        return {
            "can_view": True,
            "can_edit": role in {RoomRoleChoices.OWNER, RoomRoleChoices.EDITOR},
            "can_manage_members": role == RoomRoleChoices.OWNER,
        }

    @classmethod
    def build_initial_data(cls, room):
        snapshot = room.snapshot
        return {
            "elements": snapshot.elements,
            "appState": snapshot.app_state,
            "files": snapshot.files,
            "libraryItems": snapshot.library_items,
            "nodeAccess": cls.get_node_access_map(room),
            "scene_version": snapshot.scene_version,
            "last_event_sequence": room.last_event_sequence,
        }

    @classmethod
    def get_node_access_map(cls, room):
        return {
            node_access.node_id: {
                "allowed_roles": node_access.allowed_roles,
                "metadata": node_access.metadata,
                "locked_by_id": node_access.locked_by_id,
            }
            for node_access in room.node_access_entries.all()
        }

    @classmethod
    def _validate_operations_shape(cls, operations):
        if not isinstance(operations, list) or not operations:
            raise ValidationError({"payload": "Operations must be a non-empty list."})
        for operation in operations:
            if not isinstance(operation, dict):
                raise ValidationError({"payload": "Each operation must be an object."})
            if "op" not in operation:
                raise ValidationError({"payload": "Each operation must include op."})

    @classmethod
    def normalize_event_payload(cls, payload):
        if not isinstance(payload, dict):
            raise ValidationError({"payload": "Payload must be an object."})

        if "payload" in payload and isinstance(payload["payload"], dict):
            normalized_payload = payload["payload"]
            event_type = payload.get("event_type") or payload.get("type")
            client_event_id = payload.get("client_event_id", "")
            metadata = payload.get("metadata") or {}
            client_timestamp = payload.get("client_timestamp")
        else:
            normalized_payload = payload
            event_type = payload.get("event_type") or payload.get("type")
            client_event_id = payload.get("client_event_id", "")
            metadata = payload.get("metadata") or {}
            client_timestamp = payload.get("client_timestamp")

        if normalized_payload.get("operations"):
            cls._validate_operations_shape(normalized_payload["operations"])
            cls._inject_text_patch_client_metadata(
                operations=normalized_payload["operations"],
                metadata=metadata,
            )
            if not event_type:
                event_type = "delta.batch"
        else:
            if not event_type:
                event_type = RoomEventTypeChoices.SCENE_CHANGED
            if event_type == RoomEventTypeChoices.SCENE_CHANGED:
                if "elements" not in normalized_payload or "appState" not in normalized_payload:
                    raise ValidationError(
                        {"payload": "Scene events must include elements and appState."}
                    )

        return {
            "event_type": event_type,
            "payload": normalized_payload,
            "metadata": metadata,
            "client_event_id": client_event_id,
            "client_timestamp": client_timestamp,
        }

    @classmethod
    def _inject_text_patch_client_metadata(cls, *, operations, metadata):
        default_client_id = metadata.get("client_id") or metadata.get("client")
        default_client_sequence_start = metadata.get("client_sequence_start")
        default_client_sequence = metadata.get("client_sequence")
        text_patch_index = 0

        for operation in operations:
            if operation.get("op") != "text.patch":
                continue

            text_delta = operation.get("text_delta")
            if not isinstance(text_delta, dict):
                continue

            if not text_delta.get("client_id") and default_client_id:
                text_delta["client_id"] = str(default_client_id)

            if text_delta.get("client_sequence") is None:
                if default_client_sequence_start is not None:
                    text_delta["client_sequence"] = int(default_client_sequence_start) + text_patch_index
                elif default_client_sequence is not None:
                    text_delta["client_sequence"] = int(default_client_sequence) + text_patch_index

            text_patch_index += 1

    @classmethod
    def assert_can_access_node(cls, *, room, membership, node_id):
        node_access = CollaborationNodeAccess.objects.filter(room=room, node_id=node_id).first()
        if not node_access:
            return None
        if membership.role not in node_access.allowed_roles:
            raise PermissionDenied("You do not have permission to mutate this node.")
        return node_access

    @classmethod
    def validate_operations(cls, *, room, membership, operations):
        for operation in operations:
            op_name = operation["op"]
            node_id = operation.get("node_id") or operation.get("element", {}).get("id")
            if op_name in {"element.create", "element.update", "element.delete", "text.patch"}:
                if not node_id:
                    raise ValidationError({"payload": f"{op_name} requires node_id."})
                cls.assert_can_access_node(room=room, membership=membership, node_id=node_id)
                if op_name == "text.patch":
                    text_delta = operation.get("text_delta")
                    if not isinstance(text_delta, dict):
                        raise ValidationError({"payload": "text.patch requires text_delta."})
                    client_id = text_delta.get("client_id")
                    client_sequence = text_delta.get("client_sequence")
                    if not client_id:
                        raise ValidationError({"payload": "text.patch requires text_delta.client_id."})
                    if client_sequence is None:
                        raise ValidationError(
                            {"payload": "text.patch requires text_delta.client_sequence."}
                        )
                    try:
                        parsed_sequence = int(client_sequence)
                    except (TypeError, ValueError):
                        raise ValidationError(
                            {"payload": "text.patch client_sequence must be an integer."}
                        )
                    if parsed_sequence < 0:
                        raise ValidationError(
                            {"payload": "text.patch client_sequence must be positive."}
                        )
            elif op_name == "node_acl.set":
                if membership.role != RoomRoleChoices.OWNER:
                    raise PermissionDenied("Only owners can update node access.")
                if not node_id:
                    raise ValidationError({"payload": "node_acl.set requires node_id."})
                if not operation.get("allowed_roles"):
                    raise ValidationError({"payload": "node_acl.set requires allowed_roles."})
            elif op_name in {"app_state.update", "files.update"}:
                continue
            else:
                raise ValidationError({"payload": f"Unsupported operation {op_name}."})

    @classmethod
    def _upsert_element(cls, elements_by_id, element):
        element_id = element.get("id")
        if not element_id:
            raise ValidationError({"payload": "Element operation requires element.id."})
        elements_by_id[element_id] = {**elements_by_id.get(element_id, {}), **element}

    @classmethod
    def _transform_position_with_prior_ops(
        cls,
        *,
        position,
        prior_operations,
        current_client_id,
        current_client_sequence,
    ):
        transformed_position = position
        for prior_operation in prior_operations:
            prior_position = int(prior_operation.position)
            net_delta = int(len(prior_operation.insert_text) - prior_operation.delete_count)

            if prior_position < transformed_position:
                transformed_position += net_delta
            elif prior_position == transformed_position and net_delta > 0:
                current_key = (str(current_client_id), int(current_client_sequence))
                prior_key = (
                    str(prior_operation.client_id),
                    int(prior_operation.client_sequence),
                )
                if current_key > prior_key:
                    transformed_position += net_delta

        return max(0, transformed_position)

    @classmethod
    def _apply_text_patch(cls, *, room, actor, event, elements_by_id, operation):
        node_id = operation["node_id"]
        element = elements_by_id.get(node_id)
        if not element:
            raise ValidationError({"payload": "Cannot patch text for a missing node."})
        if element.get("type") != "text":
            raise ValidationError({"payload": "text.patch can only target text nodes."})
        text_delta = operation.get("text_delta")
        if not isinstance(text_delta, dict):
            raise ValidationError({"payload": "text.patch requires text_delta."})
        base_text = element.get("text", "")
        current_version = int(element.get("text_version", 0))
        base_version = int(text_delta.get("base_version", current_version))
        position = int(text_delta.get("position", len(base_text)))
        delete_count = int(text_delta.get("delete_count", 0))
        insert_text = text_delta.get("insert_text", "")
        client_id = str(text_delta.get("client_id", ""))
        client_sequence = int(text_delta.get("client_sequence", 0))

        duplicate_operation = CollaborationTextOperation.objects.filter(
            room=room,
            node_id=node_id,
            client_id=client_id,
            client_sequence=client_sequence,
        ).first()
        if duplicate_operation:
            return

        if position < 0 or position > len(base_text):
            raise ValidationError({"payload": "text.patch position is out of bounds."})
        if base_version < 0 or base_version > current_version:
            raise ValidationError({"payload": "text.patch base_version is invalid."})
        if delete_count < 0:
            raise ValidationError({"payload": "text.patch delete_count must be positive."})

        prior_operations = CollaborationTextOperation.objects.filter(
            room=room,
            node_id=node_id,
            applied_version__gt=base_version,
        ).order_by("applied_version")
        transformed_position = cls._transform_position_with_prior_ops(
            position=position,
            prior_operations=prior_operations,
            current_client_id=client_id,
            current_client_sequence=client_sequence,
        )

        if transformed_position > len(base_text):
            transformed_position = len(base_text)

        updated_text = (
            base_text[:transformed_position]
            + insert_text
            + base_text[transformed_position + delete_count :]
        )
        element["text"] = updated_text
        next_version = current_version + 1
        element["text_version"] = next_version
        element["versionNonce"] = int(element.get("versionNonce", 0)) + 1
        elements_by_id[node_id] = element
        CollaborationTextOperation.objects.create(
            room=room,
            node_id=node_id,
            event=event,
            actor=actor,
            base_version=base_version,
            applied_version=next_version,
            position=transformed_position,
            delete_count=delete_count,
            insert_text=insert_text,
            client_id=client_id,
            client_sequence=client_sequence,
        )

    @classmethod
    def apply_operations(cls, *, room, actor, event, snapshot, operations):
        elements_by_id = {
            element["id"]: dict(element)
            for element in snapshot.elements
            if isinstance(element, dict) and element.get("id")
        }

        for operation in operations:
            op_name = operation["op"]
            if op_name in {"element.create", "element.update"}:
                cls._upsert_element(elements_by_id, operation.get("element") or {})
            elif op_name == "element.delete":
                node_id = operation["node_id"]
                if node_id in elements_by_id:
                    elements_by_id[node_id]["isDeleted"] = True
            elif op_name == "text.patch":
                cls._apply_text_patch(
                    room=room,
                    actor=actor,
                    event=event,
                    elements_by_id=elements_by_id,
                    operation=operation,
                )
            elif op_name == "node_acl.set":
                CollaborationNodeAccess.objects.update_or_create(
                    room=room,
                    node_id=operation["node_id"],
                    defaults={
                        "allowed_roles": operation["allowed_roles"],
                        "metadata": operation.get("metadata") or {},
                        "locked_by": actor,
                    },
                )
            elif op_name == "app_state.update":
                snapshot.app_state = {
                    **snapshot.app_state,
                    **(operation.get("app_state_delta") or {}),
                }
            elif op_name == "files.update":
                snapshot.files = {
                    **snapshot.files,
                    **(operation.get("files_delta") or {}),
                }

        snapshot.elements = list(elements_by_id.values())
        return snapshot

    @classmethod
    @transaction.atomic
    def append_event(
        cls,
        *,
        room,
        actor,
        payload,
        source,
    ):
        normalized_event = cls.normalize_event_payload(payload)
        room = CollaborationRoom.objects.select_for_update().get(pk=room.pk)
        snapshot = CollaborationRoomSnapshot.objects.select_for_update().get(room=room)
        membership = cls.get_membership(room=room, user=actor) if actor else None

        operations = normalized_event["payload"].get("operations") or []
        if operations:
            if not membership:
                raise PermissionDenied("Authenticated membership is required.")
            cls.validate_operations(room=room, membership=membership, operations=operations)

        event = CollaborationRoomEvent.objects.create(
            room=room,
            actor=actor,
            event_type=normalized_event["event_type"],
            sequence=room.last_event_sequence + 1,
            payload=normalized_event["payload"],
            metadata=normalized_event["metadata"],
            client_event_id=normalized_event["client_event_id"],
            client_timestamp=normalized_event["client_timestamp"],
            source=source,
        )

        room.last_event_sequence = event.sequence
        room.save(update_fields=["last_event_sequence", "updated_at"])

        if operations:
            snapshot = cls.apply_operations(
                room=room,
                actor=actor,
                event=event,
                snapshot=snapshot,
                operations=operations,
            )
            snapshot.scene_version = event.sequence
            snapshot.last_event = event
            snapshot.updated_by = actor
            snapshot.save()
        elif event.event_type == RoomEventTypeChoices.SCENE_CHANGED:
            scene_payload = normalized_event["payload"]
            snapshot.elements = scene_payload.get("elements", [])
            snapshot.app_state = scene_payload.get("appState", {})
            snapshot.files = scene_payload.get("files", {})
            snapshot.library_items = scene_payload.get("libraryItems", [])
            snapshot.scene_version = event.sequence
            snapshot.last_event = event
            snapshot.updated_by = actor
            snapshot.save()

        if cls._should_queue_ai_pipeline(event_type=event.event_type, payload=normalized_event["payload"]):
            from apps.ai_tasks.tasks import process_room_event

            transaction.on_commit(
                lambda event_uuid=str(event.event_uuid): process_room_event.delay(event_uuid)
            )

        return event

    @classmethod
    def list_events(cls, *, room, after_sequence=0, limit=200):
        return CollaborationRoomEvent.objects.filter(
            room=room,
            sequence__gt=after_sequence,
        ).select_related("actor")[:limit]

    @classmethod
    def replay_events(cls, *, room, after_sequence=0, limit=200):
        events = list(
            CollaborationRoomEvent.objects.filter(
                room=room,
                sequence__gt=after_sequence,
            )
            .select_related("actor")
            .order_by("sequence")[:limit]
        )
        return {
            "events": events,
            "from_sequence": after_sequence,
            "to_sequence": room.last_event_sequence,
            "has_more": room.events.filter(sequence__gt=(events[-1].sequence if events else after_sequence)).exists(),
        }

    @classmethod
    def issue_realtime_tokens(cls, *, room, user):
        membership = cls.assert_can_view(room=room, user=user)
        return {
            "channel": room.channel_name,
            "role": membership.role,
            "connection_token": CentrifugoService.build_connection_token(
                user, room, membership
            ),
            "subscription_token": CentrifugoService.build_subscription_token(
                user, room, membership
            ),
        }

    @classmethod
    def list_rooms_for_user(cls, user):
        room_ids = user.collaboration_room_memberships.values_list("room_id", flat=True)
        return (
            CollaborationRoom.objects.filter(id__in=room_ids, is_active=True)
            .select_related("created_by")
            .prefetch_related("members__user", "members__group", "node_access_entries")
        )

    @classmethod
    def get_actor_from_proxy_user(cls, proxy_user_id):
        if not proxy_user_id:
            return None
        return User.objects.filter(id=proxy_user_id).first()

    @classmethod
    def parse_room_uuid_from_channel(cls, channel_name):
        parts = channel_name.split(":")
        if len(parts) != 3 or parts[0] != "collab" or parts[1] != "room":
            raise ValidationError({"channel": "Unsupported collaboration channel."})
        return parts[2]

    @classmethod
    def _should_queue_ai_pipeline(cls, *, event_type, payload):
        from apps.ai_tasks.services.pipeline_service import AIPipelineService

        return AIPipelineService.should_queue_event(event_type=event_type, payload=payload)
