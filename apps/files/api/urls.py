from django.urls import path

from .views import files_api

urlpatterns = [
    path("files/upload/", files_api.FileUploadAPI.as_view(), name="file-upload"),
    path(
        "files/",
        files_api.FileListDeleteAPI.as_view(),
        name="file-list",
    ),
    path(
        "files/<int:file_id>/tag/",
        files_api.FileTagAPI.as_view(),
        name="file-tag",
    ),
    path("files/get/", files_api.FileGetAPI.as_view(), name="file-get"),
]
