from django.db import models

from apps.ai_tasks.choices import (
    AIInferenceStatusChoices,
    AITaskPriorityChoices,
    AITaskStatusChoices,
    AITaskTypeChoices,
)
from apps.collaboration.models import CollaborationRoom, CollaborationRoomEvent
from utils.db.models import BaseModel


class AIInferenceJob(BaseModel):
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name="ai_inference_jobs")
    trigger_event = models.ForeignKey(CollaborationRoomEvent, on_delete=models.CASCADE, related_name="ai_inference_jobs")
    status = models.CharField(max_length=32, choices=AIInferenceStatusChoices.choices, default=AIInferenceStatusChoices.QUEUED)
    debounce_key = models.CharField(max_length=255, db_index=True)
    patch_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    provider = models.CharField(max_length=64, blank=True, default="")
    model_tier1 = models.CharField(max_length=128, blank=True, default="")
    model_tier2 = models.CharField(max_length=128, blank=True, default="")
    model_tier3 = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        unique_together = ("room", "trigger_event")
        indexes = [
            models.Index(fields=["room", "status", "created_at"]),
            models.Index(fields=["room", "debounce_key"]),
            models.Index(fields=["room", "created_at"]),
        ]


class AIPatchSnapshot(BaseModel):
    job = models.ForeignKey(AIInferenceJob, on_delete=models.CASCADE, related_name="patch_snapshots")
    patch_id = models.CharField(max_length=64)
    centroid_x = models.IntegerField(default=0)
    centroid_y = models.IntegerField(default=0)
    bbox = models.JSONField(default=dict, blank=True)
    node_ids = models.JSONField(default=list, blank=True)
    patch_hash = models.CharField(max_length=128)

    class Meta:
        unique_together = ("job", "patch_id")
        indexes = [models.Index(fields=["job", "patch_hash"]), models.Index(fields=["job", "created_at"])]


class AIPatchInference(BaseModel):
    job = models.ForeignKey(AIInferenceJob, on_delete=models.CASCADE, related_name="patch_inferences")
    patch_snapshot = models.ForeignKey(AIPatchSnapshot, on_delete=models.CASCADE, related_name="inferences")
    tier1_decision = models.BooleanField(default=False)
    content_items = models.JSONField(default=list, blank=True)
    local_inference = models.JSONField(default=dict, blank=True)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    model_name = models.CharField(max_length=128, blank=True, default="")
    latency_ms = models.PositiveIntegerField(default=0)


class AITaskProjection(BaseModel):
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name="ai_task_projections")
    task_uid = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    task_type = models.CharField(max_length=32, choices=AITaskTypeChoices.choices, default=AITaskTypeChoices.ACTION)
    priority = models.CharField(max_length=32, choices=AITaskPriorityChoices.choices, default=AITaskPriorityChoices.MEDIUM)
    status = models.CharField(max_length=32, choices=AITaskStatusChoices.choices, default=AITaskStatusChoices.OPEN)
    depends_on_uids = models.JSONField(default=list, blank=True)
    origin_node_ids = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    last_job = models.ForeignKey(AIInferenceJob, on_delete=models.SET_NULL, null=True, blank=True, related_name="projection_updates")

    class Meta:
        unique_together = ("room", "task_uid")
        indexes = [models.Index(fields=["room", "status"]), models.Index(fields=["room", "updated_at"])]


class AITaskProjectionHistory(BaseModel):
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name="ai_task_projection_history")
    job = models.ForeignKey(AIInferenceJob, on_delete=models.CASCADE, related_name="projection_history_entries")
    task_uid = models.CharField(max_length=255)
    change_type = models.CharField(max_length=64)
    before_state = models.JSONField(default=dict, blank=True)
    after_state = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["room", "created_at"]), models.Index(fields=["job", "created_at"])]