"""可见性判定——唯一权限出口（文件夹模型）。

规则（默认拒绝）：超管/辅助管理员/老板 → 全部；否则看"用户所在部门或本人"是否被授权了
该文件夹或其任一祖先文件夹（授权递归覆盖子文件夹/文件）。
"""

from __future__ import annotations

from django.db.models import Q

from apps.catalog.models import Folder, FolderShare
from apps.permission.models import DepartmentMembership


def _is_global(user) -> bool:
    return bool(
        user.is_superuser
        or getattr(user, "is_assistant_admin", False)
        or getattr(user, "is_boss", False)
    )


def _dept_ids(user) -> list[int]:
    return list(
        DepartmentMembership.objects.filter(user=user).values_list("department_id", flat=True)
    )


def can_view_folder(user, folder: Folder) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if _is_global(user):
        return True
    shares = FolderShare.objects.filter(folder_id__in=folder.ancestor_ids())
    if shares.filter(subject_user=user).exists():
        return True
    dept_ids = _dept_ids(user)
    return bool(dept_ids and shares.filter(subject_department_id__in=dept_ids).exists())


def can_view_file(user, datafile) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if _is_global(user):
        return True
    if datafile.folder_id is None:
        return False
    return can_view_folder(user, datafile.folder)


def visible_folders(user):
    """返回用户可见的文件夹集合（被授权的文件夹 + 其所有子孙）。"""
    if _is_global(user):
        return Folder.objects.all()

    dept_ids = _dept_ids(user)
    shared_ids = set(
        FolderShare.objects.filter(
            Q(subject_user=user) | Q(subject_department_id__in=dept_ids)
        ).values_list("folder_id", flat=True)
    )
    result = set(shared_ids)
    frontier = set(shared_ids)
    while frontier:
        children = set(Folder.objects.filter(parent_id__in=frontier).values_list("id", flat=True))
        new = children - result
        result |= new
        frontier = new
    return Folder.objects.filter(id__in=result)
