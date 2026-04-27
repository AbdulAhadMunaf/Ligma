from rest_framework import serializers

from apps.ai_tasks.models import AIInferenceJob, AITaskProjection


class AIRerunSerializer(serializers.Serializer):
    after_sequence = serializers.IntegerField(required=False, min_value=0, default=0)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=200)


class AITaskFeedbackSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=False, max_length=255)
    status = serializers.CharField(required=False, max_length=32)
    priority = serializers.CharField(required=False, max_length=32)
    confidence = serializers.FloatField(required=False)
    metadata = serializers.DictField(required=False)


class AITaskProjectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITaskProjection
        fields = (
            "task_uid",
            "title",
            "task_type",
            "priority",
            "status",
            "depends_on_uids",
            "origin_node_ids",
            "confidence",
            "metadata",
            "created_at",
            "updated_at",
        )


class AIInferenceJobSerializer(serializers.ModelSerializer):
    room_id = serializers.IntegerField(source="room.id")
    trigger_event_id = serializers.IntegerField(source="trigger_event.id")

    class Meta:
        model = AIInferenceJob
        fields = (
            "id",
            "room_id",
            "trigger_event_id",
            "status",
            "debounce_key",
            "patch_count",
            "started_at",
            "finished_at",
            "error_message",
            "provider",
            "model_tier1",
            "model_tier2",
            "model_tier3",
            "created_at",
            "updated_at",
        )