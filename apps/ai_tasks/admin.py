from django.contrib import admin

from apps.ai_tasks.models import AIInferenceJob, AIPatchInference, AIPatchSnapshot, AITaskProjection, AITaskProjectionHistory


@admin.register(AIInferenceJob)
class AIInferenceJobAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "trigger_event", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("room__room_uuid", "trigger_event__event_uuid", "debounce_key")


@admin.register(AIPatchSnapshot)
class AIPatchSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "patch_id", "patch_hash", "created_at")
    search_fields = ("patch_id", "patch_hash")


@admin.register(AIPatchInference)
class AIPatchInferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "patch_snapshot", "tier1_decision", "model_name")
    list_filter = ("tier1_decision",)


@admin.register(AITaskProjection)
class AITaskProjectionAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "task_uid", "task_type", "priority", "status")
    list_filter = ("task_type", "priority", "status")
    search_fields = ("task_uid", "title", "room__room_uuid")


@admin.register(AITaskProjectionHistory)
class AITaskProjectionHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "job", "task_uid", "change_type", "created_at")
    list_filter = ("change_type", "created_at")