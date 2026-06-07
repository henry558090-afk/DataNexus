from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.dataset import services
from apps.dataset.models import Dataset
from apps.dataset.serializers import DatasetSerializer
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
        from apps.audit.services import log

        dataset = self.get_object()
        datafile = services.run_dataset(dataset, user=request.user)
        log("run", request=request, target=dataset.name)
        return Response(DataFileSerializer(datafile).data)
