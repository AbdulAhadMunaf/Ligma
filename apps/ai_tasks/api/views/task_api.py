from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_tasks.models import AIInferenceJob, AITaskProjection, AITaskProjectionHistory
from apps.ai_tasks.serializers import AIInferenceJobSerializer, AIRerunSerializer, AITaskFeedbackSerializer, AITaskProjectionSerializer
from apps.ai_tasks.services.pipeline_service import AIPipelineService
from apps.collaboration.services.room_service import CollaborationRoomService
from utils.response.resp import APIResponse


class AITaskRoomTaskListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ai-tasks"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        tasks = AITaskProjection.objects.filter(room=room).order_by("-updated_at", "task_uid")
        return Response(APIResponse.get_response(data={"tasks": AITaskProjectionSerializer(tasks, many=True).data}))


class AIInferenceJobDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ai-tasks"])
    def get(self, request, room_uuid, job_id):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        job = get_object_or_404(AIInferenceJob.objects.select_related("room", "trigger_event"), id=job_id, room=room)
        return Response(APIResponse.get_response(data={"job": AIInferenceJobSerializer(job).data}))


class AIInferenceJobTraceAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ai-tasks"])
    def get(self, request, room_uuid, job_id):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        job = get_object_or_404(AIInferenceJob.objects.select_related("room", "trigger_event"), id=job_id, room=room)
        patch_snapshots = job.patch_snapshots.all().order_by("created_at")
        patch_inferences = job.patch_inferences.select_related("patch_snapshot").all().order_by("created_at")
        return Response(APIResponse.get_response(data={"job": AIInferenceJobSerializer(job).data, "patch_snapshots": [{"patch_id": patch_snapshot.patch_id, "node_ids": patch_snapshot.node_ids, "bbox": patch_snapshot.bbox, "patch_hash": patch_snapshot.patch_hash, "centroid_x": patch_snapshot.centroid_x, "centroid_y": patch_snapshot.centroid_y} for patch_snapshot in patch_snapshots], "patch_inferences": [{"patch_id": patch_inference.patch_snapshot.patch_id, "tier1_decision": patch_inference.tier1_decision, "content_items": patch_inference.content_items, "local_inference": patch_inference.local_inference, "prompt_tokens": patch_inference.prompt_tokens, "completion_tokens": patch_inference.completion_tokens, "model_name": patch_inference.model_name, "latency_ms": patch_inference.latency_ms} for patch_inference in patch_inferences]}))


class AITaskRoomRerunAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ai-tasks"], request_body=AIRerunSerializer)
    def post(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        serializer = AIRerunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rerun_result = AIPipelineService.rerun_room_window(room_uuid=str(room.room_uuid), after_sequence=serializer.validated_data.get("after_sequence", 0), limit=serializer.validated_data.get("limit", 200))
        return Response(APIResponse.get_response(message="AI rerun completed.", data=rerun_result))


class AITaskFeedbackAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["ai-tasks"], request_body=AITaskFeedbackSerializer)
    def post(self, request, room_uuid, task_uid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        serializer = AITaskFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        projection = get_object_or_404(AITaskProjection, room=room, task_uid=task_uid)
        before_state = {"title": projection.title, "task_type": projection.task_type, "priority": projection.priority, "status": projection.status, "confidence": projection.confidence, "metadata": projection.metadata}
        for field_name, value in serializer.validated_data.items():
            setattr(projection, field_name, value)
        projection.save()
        AITaskProjectionHistory.objects.create(room=room, job=projection.last_job, task_uid=projection.task_uid, change_type="feedback", before_state=before_state, after_state={"title": projection.title, "task_type": projection.task_type, "priority": projection.priority, "status": projection.status, "confidence": projection.confidence, "metadata": projection.metadata})
        return Response(APIResponse.get_response(message="Task feedback saved successfully.", data={"task": AITaskProjectionSerializer(projection).data}), status=status.HTTP_200_OK)