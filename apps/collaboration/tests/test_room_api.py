import jwt
import pytest

from apps.collaboration.models import CollaborationRoomMember


@pytest.mark.django_db
class TestCollaborationRoomAPI:
    def test_create_room_creates_owner_membership(self, bob_user_api_client):
        response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Design room", "metadata": {"project": "alpha"}},
            format="json",
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Design room"
        assert CollaborationRoomMember.objects.filter(
            room_id=data["id"],
            user_id=data["created_by_id"],
            role="owner",
        ).exists()

    def test_get_scene_returns_excalidraw_initial_data(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Scene room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.get(f"/api/collaboration/rooms/{room_uuid}/scene/")

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["initial_data"]["elements"] == []
        assert payload["initial_data"]["appState"] == {}
        assert payload["initial_data"]["nodeAccess"] == {}
        assert payload["channel"].startswith("collab:room:")

    def test_realtime_token_endpoint_returns_centrifugo_tokens(
        self, bob_user_api_client, bob_user, settings
    ):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Realtime room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/realtime-token/"
        )

        assert response.status_code == 200
        data = response.json()["data"]
        decoded = jwt.decode(
            data["connection_token"],
            settings.CENTRIFUGO_HMAC_SECRET,
            algorithms=["HS256"],
        )
        assert decoded["sub"] == str(bob_user.id)
        assert data["role"] == "owner"
