from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.ai_tasks.choices import AIInferenceStatusChoices, AITaskStatusChoices
from apps.ai_tasks.contracts import IncomingEventContext
from apps.ai_tasks.models import AIInferenceJob, AIPatchInference, AIPatchSnapshot, AITaskProjection, AITaskProjectionHistory
from apps.ai_tasks.services.inference_service import AITaskInferenceService
from apps.ai_tasks.services.patch_proposal_service import AIPatchProposalService
from apps.collaboration.models import CollaborationRoom, CollaborationRoomEvent
from apps.collaboration.services.centrifugo_service import CentrifugoService


class AIPipelineService:
    semantic_operations = {"element.create", "element.update", "element.delete", "text.patch", "node_acl.set"}

    @classmethod
    def should_queue_event(cls, *, event_type: str, payload: Dict) -> bool:
        from django.conf import settings

        if not getattr(settings, "AI_PIPELINE_ENABLED", True):
            return False

        operations = payload.get("operations") or []
        if operations:
            return any(operation.get("op") in cls.semantic_operations for operation in operations)
        if event_type in {"app_state.update", "files.update"}:
            return False
        if event_type in {"scene.changed", "delta.batch"}:
            return True
        return event_type in cls.semantic_operations

    @classmethod
    def execute_event(cls, *, event_uuid: str) -> Optional[AIInferenceJob]:
        event = CollaborationRoomEvent.objects.select_related("room", "room__snapshot").filter(event_uuid=event_uuid).first()
        if not event:
            return None

        room = event.room
        skipped_job = cls._get_recent_room_job(room=room)
        if skipped_job:
            return skipped_job

        if not cls.should_queue_event(event_type=event.event_type, payload=event.payload):
            job, _ = AIInferenceJob.objects.get_or_create(
                room=room,
                trigger_event=event,
                defaults={"status": AIInferenceStatusChoices.SKIPPED, "debounce_key": cls._build_debounce_key(room=room, event=event)},
            )
            return job

        job, _ = AIInferenceJob.objects.get_or_create(
            room=room,
            trigger_event=event,
            defaults={
                "status": AIInferenceStatusChoices.QUEUED,
                "debounce_key": cls._build_debounce_key(room=room, event=event),
                "provider": "openrouter",
                "model_tier1": "openrouter/auto",
                "model_tier2": "openrouter/auto",
                "model_tier3": "openrouter/auto",
            },
        )
        if job.status == AIInferenceStatusChoices.COMPLETED:
            return job

        cls._run_job(job=job)
        return job

    @classmethod
    def rerun_room_window(cls, *, room_uuid: str, after_sequence: int = 0, limit: int = 200) -> Dict:
        room = CollaborationRoom.objects.select_related("snapshot").get(room_uuid=room_uuid)
        events = CollaborationRoomEvent.objects.filter(room=room, sequence__gt=after_sequence).order_by("sequence")[:limit]
        processed_job_ids: List[int] = []
        for event in events:
            job = cls.execute_event(event_uuid=str(event.event_uuid))
            if job:
                processed_job_ids.append(job.id)
        return {"room_uuid": str(room.room_uuid), "after_sequence": after_sequence, "limit": limit, "processed_job_ids": processed_job_ids, "processed_count": len(processed_job_ids)}

    @classmethod
    def _run_job(cls, *, job: AIInferenceJob) -> AIInferenceJob:
        if job.status == AIInferenceStatusChoices.RUNNING:
            return job

        snapshot = job.room.snapshot
        context = IncomingEventContext(
            room_uuid=job.room.room_uuid,
            event_uuid=job.trigger_event.event_uuid,
            event_sequence=job.trigger_event.sequence,
            event_type=job.trigger_event.event_type,
            payload=job.trigger_event.payload or {},
            metadata=job.trigger_event.metadata or {},
            snapshot={"elements": snapshot.elements, "app_state": snapshot.app_state, "files": snapshot.files, "library_items": snapshot.library_items},
        )
        patch_proposals = AIPatchProposalService.build_patch_proposals(context)

        with transaction.atomic():
            job.status = AIInferenceStatusChoices.RUNNING
            job.started_at = timezone.now()
            job.patch_count = len(patch_proposals)
            job.save(update_fields=["status", "started_at", "patch_count", "updated_at"])

            patch_outputs = []
            snapshot_elements = snapshot.elements or []
            for proposal in patch_proposals:
                patch_snapshot = AIPatchSnapshot.objects.create(
                    job=job,
                    patch_id=proposal.patch_id,
                    centroid_x=proposal.centroid_x,
                    centroid_y=proposal.centroid_y,
                    bbox=proposal.bbox,
                    node_ids=proposal.node_ids,
                    patch_hash=proposal.patch_hash,
                )
                patch_output = AITaskInferenceService.build_patch_inference(room_uuid=str(job.room.room_uuid), event_sequence=job.trigger_event.sequence, patch=proposal, snapshot_elements=snapshot_elements)
                AIPatchInference.objects.create(
                    job=job,
                    patch_snapshot=patch_snapshot,
                    tier1_decision=patch_output.tier1_decision,
                    content_items=patch_output.content_items,
                    local_inference=patch_output.local_inference,
                    prompt_tokens=patch_output.prompt_tokens,
                    completion_tokens=patch_output.completion_tokens,
                    model_name=patch_output.model_name,
                    latency_ms=patch_output.latency_ms,
                )
                patch_outputs.append(patch_output)

            global_output = AITaskInferenceService.build_global_inference(room_uuid=str(job.room.room_uuid), patch_outputs=patch_outputs)
            cls._persist_projection(job=job, tasks=global_output.tasks)
            cls._broadcast_update(job=job)

            job.status = AIInferenceStatusChoices.COMPLETED
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "finished_at", "updated_at"])

        return job

    @classmethod
    def _persist_projection(cls, *, job: AIInferenceJob, tasks) -> None:
        existing_task_uids = set(AITaskProjection.objects.filter(room=job.room).values_list("task_uid", flat=True))
        incoming_task_uids = set()

        for task in tasks:
            incoming_task_uids.add(task.task_uid)
            projection, created = AITaskProjection.objects.get_or_create(
                room=job.room,
                task_uid=task.task_uid,
                defaults={
                    "title": task.title,
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "status": task.status,
                    "depends_on_uids": task.depends_on_uids,
                    "origin_node_ids": task.origin_node_ids,
                    "confidence": task.confidence,
                    "metadata": task.metadata,
                    "last_job": job,
                },
            )
            before_state = {}
            if not created:
                before_state = {"title": projection.title, "task_type": projection.task_type, "priority": projection.priority, "status": projection.status, "depends_on_uids": projection.depends_on_uids, "origin_node_ids": projection.origin_node_ids, "confidence": projection.confidence, "metadata": projection.metadata}
                projection.title = task.title
                projection.task_type = task.task_type
                projection.priority = task.priority
                projection.status = task.status
                projection.depends_on_uids = task.depends_on_uids
                projection.origin_node_ids = task.origin_node_ids
                projection.confidence = task.confidence
                projection.metadata = task.metadata
                projection.last_job = job
                projection.save()
            AITaskProjectionHistory.objects.create(
                room=job.room,
                job=job,
                task_uid=task.task_uid,
                change_type="upsert",
                before_state=before_state,
                after_state={"title": task.title, "task_type": task.task_type, "priority": task.priority, "status": task.status, "depends_on_uids": task.depends_on_uids, "origin_node_ids": task.origin_node_ids, "confidence": task.confidence, "metadata": task.metadata},
            )

        stale_task_uids = existing_task_uids - incoming_task_uids
        for task_uid in stale_task_uids:
            projection = AITaskProjection.objects.filter(room=job.room, task_uid=task_uid).first()
            if not projection:
                continue
            before_state = {"title": projection.title, "task_type": projection.task_type, "priority": projection.priority, "status": projection.status, "depends_on_uids": projection.depends_on_uids, "origin_node_ids": projection.origin_node_ids, "confidence": projection.confidence, "metadata": projection.metadata}
            projection.status = AITaskStatusChoices.ARCHIVED
            projection.last_job = job
            projection.save(update_fields=["status", "last_job", "updated_at"])
            AITaskProjectionHistory.objects.create(room=job.room, job=job, task_uid=task_uid, change_type="archive", before_state=before_state, after_state={"status": AITaskStatusChoices.ARCHIVED})

    @classmethod
    def _broadcast_update(cls, *, job: AIInferenceJob) -> None:
        payload = {"event": "TASK_UPDATE", "room_uuid": str(job.room.room_uuid), "job_id": job.id, "task_count": job.room.ai_task_projections.count(), "updated_at": job.updated_at.isoformat() if job.updated_at else None}
        CentrifugoService.publish_event(job.room, payload)

    @staticmethod
    def _build_debounce_key(*, room: CollaborationRoom, event: CollaborationRoomEvent) -> str:
        key_source = f"{room.room_uuid}|{event.event_type}|{event.sequence}"
        return hashlib.sha1(key_source.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_recent_room_job(*, room: CollaborationRoom) -> Optional[AIInferenceJob]:
        from django.conf import settings

        cooldown_ms = getattr(settings, "AI_ROOM_COOLDOWN_MS", 3000)
        if cooldown_ms <= 0:
            return None

        latest_job = room.ai_inference_jobs.order_by("-created_at").first()
        if not latest_job:
            return None

        age = timezone.now() - latest_job.created_at
        if age <= timedelta(milliseconds=cooldown_ms):
            return latest_job
        return None