"""用户端数据门户（文件夹模型）：可见文件夹树、文件夹内文件、搜索、下载。

可见性统一走 apps.permission.services（默认拒绝）。
"""

from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Folder
from apps.execution.models import DataFile
from apps.permission.services import can_view_file, can_view_folder, visible_folders


def _file_brief(f: DataFile) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "row_count": f.row_count,
        "file_size": f.file_size,
        "created_at": f.created_at,
        "folder_id": f.folder_id,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_tree(request: Request) -> Response:
    """返回当前用户可见的文件夹树（被授权文件夹及其子孙；可见集外的父视为根）。"""
    folders = list(visible_folders(request.user).values("id", "name", "parent_id"))
    visible_ids = {f["id"] for f in folders}
    by_parent: dict = {}
    for f in folders:
        pid = f["parent_id"] if f["parent_id"] in visible_ids else None
        by_parent.setdefault(pid, []).append(f)

    def build(pid):
        return [
            {"id": f["id"], "name": f["name"], "children": build(f["id"])}
            for f in sorted(by_parent.get(pid, []), key=lambda x: x["name"])
        ]

    return Response(build(None))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_folder_files(request: Request, pk: int) -> Response:
    """某文件夹内的成功文件（需可见）。"""
    folder = get_object_or_404(Folder, pk=pk)
    if not can_view_folder(request.user, folder):
        return Response({"detail": "无权限"}, status=403)
    files = DataFile.objects.filter(folder=folder, status=DataFile.Status.SUCCESS).order_by(
        "-created_at"
    )
    return Response([_file_brief(f) for f in files])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_search(request: Request) -> Response:
    """在可见文件夹内按文件名搜索。"""
    keyword = (request.query_params.get("q") or "").strip()
    if not keyword:
        return Response([])
    folder_ids = list(visible_folders(request.user).values_list("id", flat=True))
    files = DataFile.objects.filter(
        folder_id__in=folder_ids,
        status=DataFile.Status.SUCCESS,
        name__icontains=keyword,
    ).order_by("-created_at")[:200]
    return Response([_file_brief(f) for f in files])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_download(request: Request, pk: int):
    """下载某文件（需可见）。"""
    from apps.audit.services import log

    datafile = get_object_or_404(DataFile, pk=pk)
    if not can_view_file(request.user, datafile):
        return Response({"detail": "无权限"}, status=403)
    if not datafile.file_path or not Path(datafile.file_path).exists():
        return Response({"detail": "文件不存在"}, status=404)
    log("download", request=request, target=datafile.name)
    return FileResponse(open(datafile.file_path, "rb"), as_attachment=True, filename=datafile.name)
