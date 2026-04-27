import pytest

from apps.ai_tasks.contracts import IncomingEventContext
from apps.ai_tasks.services.inference_service import AITaskInferenceService
from apps.ai_tasks.services.patch_proposal_service import AIPatchProposalService
from apps.ai_tasks.services.pipeline_service import AIPipelineService


@pytest.mark.django_db
class TestAIPipelineService:
    def test_should_queue_event_only_for_semantic_changes(self):
        assert AIPipelineService.should_queue_event(
            event_type="app_state.update",
            payload={"operations": [{"op": "app_state.update"}]},
        ) is False
        assert AIPipelineService.should_queue_event(
            event_type="delta.batch",
            payload={"operations": [{"op": "text.patch", "node_id": "text-1"}]},
        ) is True

    def test_patch_clustering_is_stable_for_fixed_input(self):
        context = IncomingEventContext(
            room_uuid="123e4567-e89b-12d3-a456-426614174000",
            event_uuid="123e4567-e89b-12d3-a456-426614174001",
            event_sequence=4,
            event_type="delta.batch",
            payload={"operations": [{"op": "text.patch", "node_id": "node-b"}, {"op": "element.update", "node_id": "node-a"}]},
            metadata={},
            snapshot={
                "elements": [
                    {"id": "node-a", "type": "text", "x": 10, "y": 20, "text": "Fix this"},
                    {"id": "node-b", "type": "text", "x": 15, "y": 25, "text": "Need review"},
                ]
            },
        )

        proposals = AIPatchProposalService.build_patch_proposals(context)

        assert [proposal.patch_id for proposal in proposals] == ["patch-001"]
        assert proposals[0].node_ids == ["node-a", "node-b"]

    def test_global_inference_dedupes_tasks_by_uid(self):
        context = IncomingEventContext(
            room_uuid="123e4567-e89b-12d3-a456-426614174000",
            event_uuid="123e4567-e89b-12d3-a456-426614174001",
            event_sequence=4,
            event_type="delta.batch",
            payload={"operations": [{"op": "text.patch", "node_id": "node-a"}]},
            metadata={},
            snapshot={"elements": [{"id": "node-a", "type": "text", "x": 10, "y": 20, "text": "Fix login bug"}]},
        )
        proposals = AIPatchProposalService.build_patch_proposals(context)
        patch_output = AITaskInferenceService.build_patch_inference(
            room_uuid=str(context.room_uuid),
            event_sequence=context.event_sequence,
            patch=proposals[0],
            snapshot_elements=context.snapshot["elements"],
        )

        global_output = AITaskInferenceService.build_global_inference(
            room_uuid=str(context.room_uuid),
            patch_outputs=[patch_output, patch_output],
        )

        assert len(global_output.tasks) == 1
