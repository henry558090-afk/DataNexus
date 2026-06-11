"""用户端数据门户（文件夹模型）：可见文件夹树、文件夹内文件、搜索、下载。

可见性统一走 apps.permission.services（默认拒绝）。
"""

import tempfile
from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Favorite, Folder
from apps.execution.models import DataFile
from apps.permission.services import can_view_file, can_view_folder, visible_folders
from core import excel


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
    """在可见文件夹内搜索：按文件名 + 可选时间范围（v0.24 增强）。"""
    keyword = (request.query_params.get("q") or "").strip()
    date_from = request.query_params.get("from")
    date_to = request.query_params.get("to")
    if not keyword and not date_from and not date_to:
        return Response([])
    folder_ids = list(visible_folders(request.user).values_list("id", flat=True))
    files = DataFile.objects.filter(
        folder_id__in=folder_ids, status=DataFile.Status.SUCCESS
    )
    if keyword:
        files = files.filter(name__icontains=keyword)
    if date_from:
        files = files.filter(created_at__date__gte=date_from)
    if date_to:
        files = files.filter(created_at__date__lte=date_to)
    files = files.order_by("-created_at")[:200]
    return Response([_file_brief(f) for f in files])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_file_preview(request: Request, pk: int) -> Response:
    """在线预览文件内容前 N 行（需可见，v0.24）。"""
    datafile = get_object_or_404(DataFile, pk=pk)
    if not can_view_file(request.user, datafile):
        return Response({"detail": "无权限"}, status=403)
    if not datafile.file_path or not Path(datafile.file_path).exists():
        return Response({"detail": "文件不存在"}, status=404)
    try:
        limit = max(1, min(200, int(request.query_params.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    columns, rows = excel.read_xlsx(datafile.file_path, limit=limit)
    return Response({"columns": columns, "rows": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_favorites(request: Request) -> Response:
    """当前用户收藏的（仍可见的）文件夹列表（v0.24）。"""
    visible_ids = set(visible_folders(request.user).values_list("id", flat=True))
    favs = Favorite.objects.filter(user=request.user).select_related("folder")
    return Response(
        [
            {"folder_id": f.folder_id, "name": f.folder.name}
            for f in favs
            if f.folder_id in visible_ids
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portal_toggle_favorite(request: Request, pk: int) -> Response:
    """收藏/取消收藏某文件夹（需可见，v0.24）。返回 {favorited: bool}。"""
    folder = get_object_or_404(Folder, pk=pk)
    if not can_view_folder(request.user, folder):
        return Response({"detail": "无权限"}, status=403)
    fav = Favorite.objects.filter(user=request.user, folder=folder).first()
    if fav:
        fav.delete()
        return Response({"favorited": False})
    Favorite.objects.create(user=request.user, folder=folder)
    return Response({"favorited": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_recent_downloads(request: Request) -> Response:
    """当前用户最近下载记录（来自审计日志，v0.24）。"""
    from apps.audit.models import AuditLog

    logs = AuditLog.objects.filter(
        user=request.user, action=AuditLog.Action.DOWNLOAD
    ).order_by("-created_at")[:10]
    return Response([{"target": log.target, "created_at": log.created_at} for log in logs])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portal_updates(request: Request) -> Response:
    """可见范围内、since 之后新增的成功文件（站内更新通知，v0.24）。

    前端把上次查看时间作为 since 传入；返回新文件列表与计数。
    """
    since_raw = request.query_params.get("since")
    folder_ids = list(visible_folders(request.user).values_list("id", flat=True))
    qs = DataFile.objects.filter(folder_id__in=folder_ids, status=DataFile.Status.SUCCESS)
    since = parse_datetime(since_raw) if since_raw else None
    if since is not None:
        qs = qs.filter(created_at__gt=since)
    files = qs.order_by("-created_at")[:50]
    return Response({"count": qs.count(), "files": [_file_brief(f) for f in files]})


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

    # 选列下载（v0.24）：?columns=a,b → 现生成只含这些列的文件
    cols_param = (request.query_params.get("columns") or "").strip()
    if cols_param:
        wanted = [c for c in cols_param.split(",") if c]
        columns, rows = excel.read_xlsx(datafile.file_path, columns=wanted)
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        excel.export_to_xlsx(columns, rows, tmp.name)
        resp = FileResponse(open(tmp.name, "rb"), as_attachment=True, filename=datafile.name)
        return resp
    return FileResponse(open(datafile.file_path, "rb"), as_attachment=True, filename=datafile.name)
