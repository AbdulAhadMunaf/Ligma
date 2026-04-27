import pytest


@pytest.mark.django_db
class TestAITasksAPI:
    def test_list_tasks_returns_empty_collection(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "AI tasks room"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        response = bob_user_api_client.get(f"/api/ai-tasks/rooms/{room_uuid}/tasks/")

        assert response.status_code == 200
        assert response.json()["data"]["tasks"] == []

    def test_rerun_endpoint_processes_semantic_events(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "AI rerun room"},
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
                            "element": {"id": "node-1", "type": "text", "x": 10, "y": 10, "text": "Fix login flow"},
                        }
                    ]
                }
            },
            format="json",
        )

        response = bob_user_api_client.post(
            f"/api/ai-tasks/rooms/{room_uuid}/rerun/",
            {"after_sequence": 0, "limit": 10},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["data"]["processed_count"] >= 1

    def test_feedback_updates_projection_state(self, bob_user_api_client):
        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "AI feedback room"},
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
                            "element": {"id": "node-1", "type": "text", "x": 5, "y": 5, "text": "Need docs update"},
                        }
                    ]
                }
            },
            format="json",
        )
        bob_user_api_client.post(
            f"/api/ai-tasks/rooms/{room_uuid}/rerun/",
            {"after_sequence": 0, "limit": 10},
            format="json",
        )
        task_uid = bob_user_api_client.get(f"/api/ai-tasks/rooms/{room_uuid}/tasks/").json()["data"]["tasks"][0]["task_uid"]

        response = bob_user_api_client.post(
            f"/api/ai-tasks/rooms/{room_uuid}/tasks/{task_uid}/feedback/",
            {"status": "done", "priority": "high"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["data"]["task"]["status"] == "done"
        assert response.json()["data"]["task"]["priority"] == "high"
