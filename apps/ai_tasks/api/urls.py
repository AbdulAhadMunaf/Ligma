from django.urls import path

from apps.ai_tasks.api.views import task_api

urlpatterns = [
    path("rooms/<uuid:room_uuid>/tasks/", task_api.AITaskRoomTaskListAPI.as_view()),
    path("rooms/<uuid:room_uuid>/jobs/<int:job_id>/", task_api.AIInferenceJobDetailAPI.as_view()),
    path("rooms/<uuid:room_uuid>/jobs/<int:job_id>/trace/", task_api.AIInferenceJobTraceAPI.as_view()),
    path("rooms/<uuid:room_uuid>/rerun/", task_api.AITaskRoomRerunAPI.as_view()),
    path("rooms/<uuid:room_uuid>/tasks/<str:task_uid>/feedback/", task_api.AITaskFeedbackAPI.as_view()),
]