from rest_framework import serializers

from apps.dataset.models import Dataset
from core.sql_guard import SqlNotAllowed, validate_readonly_sql


class DatasetSerializer(serializers.ModelSerializer):
    datasource_name = serializers.CharField(source="datasource.name", read_only=True)
    folder_name = serializers.CharField(source="target_folder.name", read_only=True)
    last_run = serializers.SerializerMethodField()

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "datasource",
            "datasource_name",
            "sql_text",
            "params",
            "target_folder",
            "folder_name",
            "file_prefix",
            "date_format",
            "cron",
            "interval_minutes",
            "keep_count",
            "keep_days",
            "owner",
            "is_active",
            "created_at",
            "updated_at",
            "last_run",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate_sql_text(self, value: str) -> str:
        try:
            validate_readonly_sql(value)
        except SqlNotAllowed as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def get_last_run(self, obj: Dataset) -> dict | None:
        f = obj.files.order_by("-created_at").first()
        if f is None:
            return None
        return {
            "id": f.id,
            "status": f.status,
            "row_count": f.row_count,
            "created_at": f.created_at,
        }

    def create(self, validated_data: dict) -> Dataset:
        request = self.context.get("request")
        if request is not None:
            validated_data["owner"] = request.user
        return super().create(validated_data)
