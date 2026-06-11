from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.dataset import services
from apps.dataset.models import Dataset
from apps.dataset.serializers import DatasetSerializer
from apps.execution.models import DataFile
from apps.execution.serializers import DataFileSerializer


class DatasetViewSet(viewsets.ModelViewSet):
    """数据集（SQL 任务，仅管理员）：CRUD + 预览 + 运行（在目标文件夹新增文件）。"""

    queryset = Dataset.objects.select_related("datasource", "target_folder").all()
    serializer_class = DatasetSerializer
    permission_classes = [IsManager]

    @action(detail=True, methods=["post"])
    def preview(self, request: Request, pk: str | None = None) -> Response:
        dataset = self.get_object()
        try:
            columns, rows = services.preview_dataset(dataset, limit=50)
        except Exception as exc:  # noqa: BLE001
            return Response({"ok": False, "message": str(exc)})
        return Response({"ok": True, "columns": columns, "rows": rows})

    @action(detail=True, methods=["post"])
    def run(self, request: Request, pk: str | None = None) -> Response:
        """触发运行：异步执行（S1），立即返回"运行中"的 DataFile，前端按 status 轮询。"""
        from apps.audit.services import log

        dataset = self.get_object()
        datafile = services.start_dataset_run(dataset, user=request.user)
        log("run", request=request, target=dataset.name)
        return Response(DataFileSerializer(datafile).data)

    @action(detail=False, methods=["post"], url_path="batch-run")
    def batch_run(self, request: Request) -> Response:
        """批量运行（v0.23）：body {ids:[..]} → 逐个异步触发，返回各自"运行中"的文件。"""
        from apps.audit.services import log

        ids = request.data.get("ids") or []
        datasets = self.get_queryset().filter(id__in=ids)
        results = []
        for ds in datasets:
            datafile = services.start_dataset_run(ds, user=request.user)
            log("run", request=request, target=ds.name)
            results.append({"dataset": ds.id, "file": DataFileSerializer(datafile).data})
        return Response({"count": len(results), "results": results})

    @action(detail=False, methods=["post"], url_path="batch-retention")
    def batch_retention(self, request: Request) -> Response:
        """批量改保留策略（v0.23）：body {ids:[..], keep_count?, keep_days?}。"""
        ids = request.data.get("ids") or []
        fields = {}
        if "keep_count" in request.data:
            fields["keep_count"] = request.data.get("keep_count")
        if "keep_days" in request.data:
            fields["keep_days"] = request.data.get("keep_days")
        if not fields:
            return Response({"detail": "未提供 keep_count / keep_days"}, status=400)
        updated = self.get_queryset().filter(id__in=ids).update(**fields)
        return Response({"updated": updated})

    @action(detail=False, methods=["get"], url_path="run-health")
    def run_health(self, request: Request) -> Response:
        """运行健康看板（v0.23）：近 N 天总数/成功率/平均耗时/最近失败/最慢数据集。"""
        try:
            days = max(1, min(90, int(request.query_params.get("days", 7))))
        except (TypeError, ValueError):
            days = 7
        since = timezone.now() - timedelta(days=days)
        qs = DataFile.objects.filter(created_at__gte=since)
        agg = qs.aggregate(
            total=Count("id"),
            success=Count("id", filter=Q(status=DataFile.Status.SUCCESS)),
            failed=Count("id", filter=Q(status=DataFile.Status.FAILED)),
            running=Count("id", filter=Q(status=DataFile.Status.RUNNING)),
            avg_ms=Avg("duration_ms", filter=Q(status=DataFile.Status.SUCCESS)),
        )
        total = agg["total"] or 0
        success = agg["success"] or 0
        recent_failures = [
            {
                "id": f.id,
                "dataset": f.dataset.name if f.dataset else None,
                "name": f.name,
                "error_msg": f.error_msg,
                "created_at": f.created_at,
            }
            for f in qs.filter(status=DataFile.Status.FAILED).select_related("dataset").order_by(
                "-created_at"
            )[:10]
        ]
        slowest = list(
            qs.filter(status=DataFile.Status.SUCCESS, dataset__isnull=False)
            .values("dataset", "dataset__name")
            .annotate(avg_ms=Avg("duration_ms"), runs=Count("id"))
            .order_by("-avg_ms")[:5]
        )
        return Response(
            {
                "days": days,
                "total": total,
                "success": success,
                "failed": agg["failed"] or 0,
                "running": agg["running"] or 0,
                "success_rate": round(success / total, 4) if total else None,
                "avg_duration_ms": int(agg["avg_ms"]) if agg["avg_ms"] else None,
                "recent_failures": recent_failures,
                "slowest_datasets": slowest,
            }
        )
