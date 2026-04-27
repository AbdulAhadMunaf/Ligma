import pytest

from apps.collaboration.models import CollaborationRoomEvent, CollaborationTextOperation


@pytest.mark.django_db
class TestCollaborationRoomEventsAPI:
    def test_event_create_persists_snapshot_and_event(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Event room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "elements": [{"id": "rect-1", "type": "rectangle"}],
                    "appState": {"viewBackgroundColor": "#ffffff"},
                    "files": {},
                }
            },
            format="json",
        )

        assert response.status_code == 201
        event = response.json()["data"]["event"]
        assert event["sequence"] == 1

        scene_response = bob_user_api_client.get(
            f"/api/collaboration/rooms/{room_uuid}/scene/"
        )
        assert scene_response.json()["data"]["initial_data"]["elements"][0]["id"] == "rect-1"

    def test_viewer_cannot_create_room_event(
        self, bob_user_api_client, admin_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Viewer room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "viewer"},
            format="json",
        )

        response = admin_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "elements": [{"id": "rect-1"}],
                    "appState": {},
                    "files": {},
                }
            },
            format="json",
        )

        assert response.status_code == 403

    def test_editor_cannot_update_node_locked_to_owner(
        self, bob_user_api_client, admin_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Locked node room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "editor"},
            format="json",
        )

        create_element_response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "element.create",
                            "element": {"id": "node-1", "type": "rectangle", "x": 0, "y": 0},
                        },
                        {
                            "op": "node_acl.set",
                            "node_id": "node-1",
                            "allowed_roles": ["owner"],
                        },
                    ]
                }
            },
            format="json",
        )

        assert create_element_response.status_code == 201

        response = admin_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "element.update",
                            "node_id": "node-1",
                            "element": {"id": "node-1", "x": 100},
                        }
                    ]
                }
            },
            format="json",
        )

        assert response.status_code == 403

    def test_replay_returns_only_missed_events(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Replay room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {"payload": {"operations": [{"op": "app_state.update", "app_state_delta": {"theme": "light"}}]}},
            format="json",
        )
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {"payload": {"operations": [{"op": "files.update", "files_delta": {"f1": {"id": "f1"}}}]}},
            format="json",
        )

        response = bob_user_api_client.get(
            f"/api/collaboration/rooms/{room_uuid}/replay/?after_sequence=1"
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["events"]) == 1
        assert data["events"][0]["sequence"] == 2
        assert data["from_sequence"] == 1
        assert data["to_sequence"] == 2

    def test_text_patch_rebases_on_base_version_conflict(
        self, bob_user_api_client, admin_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Text merge room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "editor"},
            format="json",
        )

        seed_response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "element.create",
                            "element": {
                                "id": "text-1",
                                "type": "text",
                                "text": "AB",
                                "text_version": 0,
                            },
                        }
                    ]
                }
            },
            format="json",
        )
        assert seed_response.status_code == 201

        first_patch = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "text.patch",
                            "node_id": "text-1",
                            "text_delta": {
                                "position": 1,
                                "delete_count": 0,
                                "insert_text": "X",
                                "base_version": 0,
                                "client_id": "a-client",
                                "client_sequence": 1,
                            },
                        }
                    ]
                }
            },
            format="json",
        )
        assert first_patch.status_code == 201

        second_patch = admin_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "text.patch",
                            "node_id": "text-1",
                            "text_delta": {
                                "position": 1,
                                "delete_count": 0,
                                "insert_text": "Y",
                                "base_version": 0,
                                "client_id": "z-client",
                                "client_sequence": 1,
                            },
                        }
                    ]
                }
            },
            format="json",
        )
        assert second_patch.status_code == 201

        scene_response = bob_user_api_client.get(
            f"/api/collaboration/rooms/{room_uuid}/scene/"
        )
        elements = scene_response.json()["data"]["initial_data"]["elements"]
        text_element = [element for element in elements if element["id"] == "text-1"][0]
        assert text_element["text"] == "AXYB"
        assert text_element["text_version"] == 2

    def test_text_patch_uses_client_order_tie_break_not_arrival_order(
        self, bob_user_api_client, admin_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Tie break room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "editor"},
            format="json",
        )

        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "element.create",
                            "element": {
                                "id": "text-2",
                                "type": "text",
                                "text": "AB",
                                "text_version": 0,
                            },
                        }
                    ]
                }
            },
            format="json",
        )

        first_arrival = admin_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "text.patch",
                            "node_id": "text-2",
                            "text_delta": {
                                "position": 1,
                                "delete_count": 0,
                                "insert_text": "Z",
                                "base_version": 0,
                                "client_id": "z-client",
                                "client_sequence": 1,
                            },
                        }
                    ]
                }
            },
            format="json",
        )
        assert first_arrival.status_code == 201

        second_arrival = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "text.patch",
                            "node_id": "text-2",
                            "text_delta": {
                                "position": 1,
                                "delete_count": 0,
                                "insert_text": "A",
                                "base_version": 0,
                                "client_id": "a-client",
                                "client_sequence": 1,
                            },
                        }
                    ]
                }
            },
            format="json",
        )
        assert second_arrival.status_code == 201

        scene_response = bob_user_api_client.get(
            f"/api/collaboration/rooms/{room_uuid}/scene/"
        )
        elements = scene_response.json()["data"]["initial_data"]["elements"]
        text_element = [element for element in elements if element["id"] == "text-2"][0]
        assert text_element["text"] == "AAZB"
        assert text_element["text_version"] == 2

    def test_centrifugo_publish_proxy_stores_event(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Proxy room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        room_channel = f"collab:room:{room_uuid}"
        owner_id = create_response.json()["data"]["created_by_id"]

        response = bob_user_api_client.post(
            "/api/collaboration/centrifugo/publish/",
            {
                "channel": room_channel,
                "user": str(owner_id),
                "data": {
                    "elements": [{"id": "arrow-1", "type": "arrow"}],
                    "appState": {"theme": "light"},
                    "files": {},
                },
            },
            format="json",
        )

        assert response.status_code == 200
        assert CollaborationRoomEvent.objects.filter(
            room__room_uuid=room_uuid,
            source="centrifugo_publish_proxy",
        ).count() == 1

    def test_text_patch_accepts_client_metadata_fallback_from_payload_metadata(
        self, bob_user_api_client
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Bridge metadata room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "operations": [
                        {
                            "op": "element.create",
                            "element": {
                                "id": "text-meta-1",
                                "type": "text",
                                "text": "AB",
                                "text_version": 0,
                            },
                        }
                    ]
                }
            },
            format="json",
        )

        response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {
                "payload": {
                    "metadata": {
                        "client_id": "bridge-client",
                        "client_sequence_start": 100,
                    },
                    "operations": [
                        {
                            "op": "text.patch",
                            "node_id": "text-meta-1",
                            "text_delta": {
                                "position": 1,
                                "delete_count": 0,
                                "insert_text": "M",
                                "base_version": 0,
                            },
                        }
                    ],
                }
            },
            format="json",
        )

        assert response.status_code == 201
        applied_operation = CollaborationTextOperation.objects.filter(
            room__room_uuid=room_uuid,
            node_id="text-meta-1",
        ).latest("applied_version")
        assert applied_operation.client_id == "bridge-client"
        assert applied_operation.client_sequence == 100
