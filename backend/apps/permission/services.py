"""权限可见性判定——**唯一权限出口**。

开发规范第 3 节 + 技术方案 §3.3：任何"列目录 / 看数据集 / 下载文件"都必须走本模块，
错一次就全局漏权。判定遵循"默认拒绝"。
"""

from __future__ import annotations

from django.db.models import Q

from apps.permission.models import DepartmentMembership, Grant


def can_view_dataset(user, dataset) -> bool:
    """判断 user 是否可见某 dataset（含其文件、预览）。

    顺序（命中即返回 True）：
        1. 超级管理员 / 辅助管理员 / 老板 → 全部可见；
        2. 在该数据集所属部门为 总监 或 主管 → 部门全部可见；
        3. 为成员且勾选"看本部门全部" → 可见；
        4. 命中个人授权 或 角色组授权（到分类或数据集）→ 可见；
        5. 否则不可见。
    """
    if not getattr(user, "is_authenticated", False):
        return False

    # 1. 全局可见角色
    if (
        user.is_superuser
        or getattr(user, "is_assistant_admin", False)
        or getattr(user, "is_boss", False)
    ):
        return True

    department_id = dataset.category.department_id
    membership = DepartmentMembership.objects.filter(user=user, department_id=department_id).first()

    # 2 & 3. 部门内角色
    if membership:
        if membership.role in (
            DepartmentMembership.Role.DIRECTOR,
            DepartmentMembership.Role.MANAGER,
        ):
            return True
        if membership.role == DepartmentMembership.Role.MEMBER and membership.see_all_in_dept:
            return True

    target_q = Q(dataset=dataset) | Q(category_id=dataset.category_id)

    # 4a. 个人授权
    if Grant.objects.filter(target_q, subject_user=user).exists():
        return True

    # 4b. 角色组授权（该部门下用户当前角色）
    if (
        membership
        and Grant.objects.filter(
            target_q,
            subject_department_id=department_id,
            subject_role=membership.role,
        ).exists()
    ):
        return True

    return False
