from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """仅管理员（超级管理员或辅助管理员）可访问管理端接口。"""

    message = "需要管理员权限"

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "is_manager_role", user.is_superuser)
        )
