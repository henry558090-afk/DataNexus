from pathlib import Path

from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.execution.models import Execution
from apps.execution.serializers import ExecutionSerializer


class ExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """执行记录（仅管理员）：列表/详情 + 下载文件。

    支持 ?dataset=<id> 过滤。用户端下载（含可见性判定）在 v0.10+ 实现。
    """

    queryset = Execution.objects.select_related("dataset").all()
    serializer_class = ExecutionSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        dataset_id = self.request.query_params.get("dataset")
        if dataset_id:
            qs = qs.filter(dataset_id=dataset_id)
        return qs

    @action(detail=True, methods=["get"])
    def download(self, request: Request, pk: str | None = None):
        """下载该执行生成的 Excel。FileResponse 自动处理中文文件名(RFC5987)与流式。"""
        execution = self.get_object()
        if not execution.file_path or not Path(execution.file_path).exists():
            return Response({"detail": "文件不存在"}, status=404)
        return FileResponse(
            open(execution.file_path, "rb"),
            as_attachment=True,
            filename=Path(execution.file_path).name,
        )
