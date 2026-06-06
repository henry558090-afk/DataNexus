from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.dataset import services
from apps.dataset.models import Dataset
from apps.dataset.serializers import DatasetSerializer
from apps.execution.models import Execution
from apps.execution.serializers import ExecutionSerializer


class DatasetViewSet(viewsets.ModelViewSet):
    """数据集管理（仅管理员）：CRUD + 预览 + 运行。"""

    # 预取"最新执行"，避免列表 get_latest 的 N+1 查询
    queryset = (
        Dataset.objects.select_related("datasource", "category")
        .prefetch_related(
            Prefetch(
                "executions",
                queryset=Execution.objects.filter(is_latest=True),
                to_attr="latest_execs",
            )
        )
        .all()
    )
    serializer_class = DatasetSerializer
    permission_classes = [IsManager]

    @action(detail=True, methods=["post"])
    def preview(self, request: Request, pk: str | None = None) -> Response:
        """预览前 50 行（不落文件）。需可连通的数据源。"""
        dataset = self.get_object()
        try:
            columns, rows = services.preview_dataset(dataset, limit=50)
        except Exception as exc:  # noqa: BLE001 - 返回失败原因而非 500
            return Response({"ok": False, "message": str(exc)})
        return Response({"ok": True, "columns": columns, "rows": rows})

    @action(detail=True, methods=["post"])
    def run(self, request: Request, pk: str | None = None) -> Response:
        """运行数据集 → 生成 Excel。返回本次执行记录。"""
        from apps.audit.services import log

        dataset = self.get_object()
        execution = services.run_dataset(dataset, user=request.user)
        log("run", request=request, target=dataset.name)
        return Response(ExecutionSerializer(execution).data)
