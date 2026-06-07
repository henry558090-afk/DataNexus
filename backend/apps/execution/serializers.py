from rest_framework import serializers

from apps.execution.models import DataFile


class DataFileSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)
    folder_name = serializers.CharField(source="folder.name", read_only=True)

    class Meta:
        model = DataFile
        fields = [
            "id",
            "folder",
            "folder_name",
            "name",
            "dataset",
            "dataset_name",
            "status",
            "row_count",
            "file_size",
            "error_msg",
            "created_at",
        ]
