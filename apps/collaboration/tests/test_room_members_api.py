import pytest


@pytest.mark.django_db
class TestCollaborationRoomMembersAPI:
    def test_owner_can_add_room_member(self, bob_user_api_client, admin_user):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Member room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "editor"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["data"]["role"] == "editor"
        assert response.json()["data"]["group_name"] == "collaboration_editor"

    def test_non_owner_cannot_add_room_member(
        self, bob_user_api_client, admin_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Restricted room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = admin_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "viewer"},
            format="json",
        )

        assert response.status_code == 403

    def test_room_members_list_is_visible_to_room_member(
        self, bob_user_api_client, admin_user
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "List room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]
        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/members/",
            {"user_id": admin_user.id, "role": "viewer"},
            format="json",
        )

        response = bob_user_api_client.get(f"/api/collaboration/rooms/{room_uuid}/members/")

        assert response.status_code == 200
        assert len(response.json()["data"]["members"]) == 2

    def test_owner_can_set_node_level_access(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "ACL room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/node-access/",
            {"node_id": "node-1", "allowed_roles": ["owner"], "metadata": {"locked": True}},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["data"]["node_id"] == "node-1"
        assert response.json()["data"]["allowed_roles"] == ["owner"]
