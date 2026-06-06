from rest_framework import serializers

from apps.execution.models import Execution


class ExecutionSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = Execution
        fields = [
            "id",
            "dataset",
            "dataset_name",
            "status",
            "row_count",
            "file_size",
            "started_at",
            "ended_at",
            "error_msg",
            "is_latest",
        ]
