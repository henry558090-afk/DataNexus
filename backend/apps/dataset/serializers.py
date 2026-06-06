from rest_framework import serializers

from apps.dataset.models import Dataset
from core.sql_guard import SqlNotAllowed, validate_readonly_sql


class DatasetSerializer(serializers.ModelSerializer):
    datasource_name = serializers.CharField(source="datasource.name", read_only=True)
    latest = serializers.SerializerMethodField()

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "category",
            "datasource",
            "datasource_name",
            "sql_text",
            "params",
            "cron",
            "interval_minutes",
            "owner",
            "is_active",
            "created_at",
            "updated_at",
            "latest",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate_sql_text(self, value: str) -> str:
        """保存时即校验只读 SQL，给管理员早反馈。"""
        try:
            validate_readonly_sql(value)
        except SqlNotAllowed as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def get_latest(self, obj: Dataset) -> dict | None:
        # 列表场景走预取的 latest_execs（避免 N+1）；详情/创建回退到查询
        prefetched = getattr(obj, "latest_execs", None)
        if prefetched is not None:
            ex = prefetched[0] if prefetched else None
        else:
            ex = obj.executions.filter(is_latest=True).first()
        if ex is None:
            return None
        return {
            "id": ex.id,
            "status": ex.status,
            "row_count": ex.row_count,
            "file_size": ex.file_size,
            "started_at": ex.started_at,
        }

    def create(self, validated_data: dict) -> Dataset:
        request = self.context.get("request")
        if request is not None:
            validated_data["owner"] = request.user
        return super().create(validated_data)
