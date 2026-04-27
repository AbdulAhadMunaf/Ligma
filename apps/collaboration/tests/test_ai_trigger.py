import pytest

from django.db import transaction

from apps.ai_tasks.tasks import process_room_event


@pytest.mark.django_db
class TestCollaborationAITaskTrigger:
    def test_semantic_event_triggers_ai_queue(self, bob_user_api_client, monkeypatch):
        calls = []

        def fake_delay(event_uuid):
            calls.append(event_uuid)

        def immediate_on_commit(callback):
            callback()

        monkeypatch.setattr(process_room_event, "delay", fake_delay)
        monkeypatch.setattr(transaction, "on_commit", immediate_on_commit)

        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Trigger room"},
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
                            "element": {"id": "node-1", "type": "text", "text": "Fix docs"},
                        }
                    ]
                }
            },
            format="json",
        )

        assert len(calls) == 1

    def test_non_semantic_event_does_not_trigger_ai_queue(self, bob_user_api_client, monkeypatch):
        calls = []

        def fake_delay(event_uuid):
            calls.append(event_uuid)

        monkeypatch.setattr(process_room_event, "delay", fake_delay)

        create_response = bob_user_api_client.post(
            "/api/collaboration/rooms/",
            {"name": "Trigger room 2"},
            format="json",
        )
        room_uuid = create_response.json()["data"]["room_uuid"]

        bob_user_api_client.post(
            f"/api/collaboration/rooms/{room_uuid}/events/",
            {"payload": {"operations": [{"op": "app_state.update", "app_state_delta": {"theme": "light"}}]}},
            format="json",
        )

        assert calls == []
