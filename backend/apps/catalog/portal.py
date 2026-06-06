"""用户端数据门户：按当前用户可见性返回目录树、数据集详情、下载。

所有可见性都走唯一出口 apps.permission.services.can_view_dataset（默认拒绝）。
"""

from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Department
from apps.dataset.models import Dataset
from apps.execution.models import Execution
from apps.execution.serializers import ExecutionSerializer
from apps.permission.services import can_view_dataset


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_tree(request: Request) -> Response:
    """返回当前用户可见的「部门 → 分类 → 数据集」树（空分支会被裁掉）。"""
    user = request.user
    departments = Department.objects.prefetch_related("categories__datasets").all()
    tree = []
    for dept in departments:
        categories = []
        for cat in dept.categories.all():
            datasets = [
                {"id": d.id, "name": d.name, "description": d.description}
                for d in cat.datasets.all()
                if d.is_active and can_view_dataset(user, d)
            ]
            if datasets:
                categories.append({"id": cat.id, "name": cat.name, "datasets": datasets})
        if categories:
            tree.append({"id": dept.id, "name": dept.name, "categories": categories})
    return Response(tree)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_dataset_detail(request: Request, pk: int) -> Response:
    """数据集详情（最新 + 历史成功版本）。"""
    dataset = get_object_or_404(Dataset, pk=pk)
    if not can_view_dataset(request.user, dataset):
        return Response({"detail": "无权限查看该数据集"}, status=403)
    execs = dataset.executions.filter(status=Execution.Status.SUCCESS).order_by("-started_at")[:20]
    return Response(
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "executions": ExecutionSerializer(execs, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_download(request: Request, pk: int):
    """下载某次执行的 Excel（带可见性校验）。"""
    execution = get_object_or_404(Execution, pk=pk)
    if not can_view_dataset(request.user, execution.dataset):
        return Response({"detail": "无权限下载"}, status=403)
    if not execution.file_path or not Path(execution.file_path).exists():
        return Response({"detail": "文件不存在"}, status=404)
    return FileResponse(
        open(execution.file_path, "rb"),
        as_attachment=True,
        filename=Path(execution.file_path).name,
    )
