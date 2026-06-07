from pathlib import Path

from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.audit.services import log
from apps.execution.models import DataFile
from apps.execution.serializers import DataFileSerializer
from core.pagination import DefaultPagination


class DataFileViewSet(viewsets.ReadOnlyModelViewSet):
    """数据文件（仅管理员）：列表/详情 + 下载。分页。支持 ?dataset / ?folder 过滤。"""

    queryset = DataFile.objects.select_related("dataset", "folder").all()
    serializer_class = DataFileSerializer
    permission_classes = [IsManager]
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = super().get_queryset()
        dataset_id = self.request.query_params.get("dataset")
        folder_id = self.request.query_params.get("folder")
        if dataset_id:
            qs = qs.filter(dataset_id=dataset_id)
        if folder_id:
            qs = qs.filter(folder_id=folder_id)
        return qs

    @action(detail=True, methods=["get"])
    def download(self, request: Request, pk: str | None = None):
        datafile = self.get_object()
        if not datafile.file_path or not Path(datafile.file_path).exists():
            return Response({"detail": "文件不存在"}, status=404)
        log("download", request=request, target=datafile.name)
        return FileResponse(
            open(datafile.file_path, "rb"), as_attachment=True, filename=datafile.name
        )
