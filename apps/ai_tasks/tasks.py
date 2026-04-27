from celery import shared_task

from apps.ai_tasks.services.pipeline_service import AIPipelineService


@shared_task(bind=True, name="apps.ai_tasks.process_room_event")
def process_room_event(self, event_uuid: str):
    return AIPipelineService.execute_event(event_uuid=event_uuid)


@shared_task(bind=True, name="apps.ai_tasks.rerun_room_window")
def rerun_room_window(self, room_uuid: str, after_sequence: int = 0, limit: int = 200):
    return AIPipelineService.rerun_room_window(room_uuid=room_uuid, after_sequence=after_sequence, limit=limit)