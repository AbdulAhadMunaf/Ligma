from rest_framework import serializers

from apps.files.models import FileAttachment


class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAttachment
        fields = ("id", "name", "file_type", "file", "created_at", "tag")


class FileDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class FileTagSerializer(serializers.Serializer):
    tag = serializers.CharField(
        required=True, help_text="Tag name to assign to the file"
    )
