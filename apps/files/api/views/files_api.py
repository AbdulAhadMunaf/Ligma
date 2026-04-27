import mimetypes

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.files.api.serializers import (
    FileDeleteSerializer,
    FileListSerializer,
    FileTagSerializer,
)
from apps.files.models import FileAttachment
from utils import swagger_fields
from utils.response.resp import APIResponse


class FileListDeleteAPI(APIView):
    @swagger_auto_schema(
        tags=["files"],
        manual_parameters=[swagger_fields.object_id],
    )
    def get(self, request):
        object_id = request.query_params.get("object_id")

        if not object_id:
            return Response(
                APIResponse.get_response(code=400, message="object_id is required.")
            )
        files = FileAttachment.objects.filter(object_id=object_id)
        serializer = FileListSerializer(files, many=True)
        return Response(
            APIResponse.get_response(
                data=serializer.data,
            )
        )

    @swagger_auto_schema(tags=["files"], request_body=FileDeleteSerializer)
    @transaction.atomic
    def delete(self, request):
        serializer = FileDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        FileAttachment.objects.filter(id__in=serializer.validated_data["ids"]).delete()
        return Response(
            APIResponse.get_response(
                message="files deleted successfully",
            )
        )


class FileGetAPI(APIView):
    @swagger_auto_schema(
        tags=["files"],
        manual_parameters=[swagger_fields.file_id],
        operation_description="To get the file DIRECTLY by file id",
    )
    def get(self, request):
        file_id = request.query_params.get("file_id")

        if not file_id:
            return Response(
                APIResponse.get_response(code=400, message="object_id is required.")
            )
        file_ = FileAttachment.objects.filter(id=file_id).first()
        serializer = FileListSerializer(file_)
        return Response(
            APIResponse.get_response(
                data=serializer.data,
            )
        )


class FileTagAPI(APIView):
    @swagger_auto_schema(
        tags=["files"],
        operation_description="""
            Get the tag for a specific file.
        """,
    )
    def get(self, request, *args, **kwargs):
        file_id = kwargs.get("file_id")

        try:
            file = FileAttachment.objects.get(id=file_id)
            return Response(
                APIResponse.get_response(
                    message="Tag retrieved successfully",
                    data={"file_id": file.id, "tag": file.tag},
                )
            )
        except FileAttachment.DoesNotExist:
            return Response(
                APIResponse.get_response(code=404, message="File not found.")
            )

    @swagger_auto_schema(
        tags=["files"],
        operation_description="""
            Assign Tag to a file.
            Just give in data {"tag":"tag_name"}
        """,
        request_body=FileTagSerializer,
    )
    def post(self, request, *args, **kwargs):
        file_id = kwargs.get("file_id")
        tag_name = request.data.get("tag", None)

        if not tag_name:
            return Response(
                APIResponse.get_response(code=400, message="tag name is required.")
            )

        try:
            file = FileAttachment.objects.get(id=file_id)
            file.tag = tag_name
            file.save()
            return Response(
                APIResponse.get_response(
                    message="Tag assigned successfully",
                    data={"file_id": file.id, "tag": file.tag},
                )
            )
        except FileAttachment.DoesNotExist:
            return Response(
                APIResponse.get_response(code=404, message="File not found.")
            )


class FileUploadAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        tags=["files"],
        operation_description="""
        Upload any file, in return you will get a file_id which you can
        send over in attachments list in any api which have attachments.
        """,
        manual_parameters=[swagger_fields.file],
    )
    def post(self, request, *args, **kwargs):
        file = request.FILES["file"]
        file_type, _ = mimetypes.guess_type(file.name) or "unknown"

        attachment = FileAttachment.objects.create(
            name=file.name,
            file=file,
            file_type=file_type,
        )
        data = {"file_id": attachment.id}
        return Response(
            APIResponse.get_response(
                data=data,
            )
        )
