"""根 URL 路由。"""

from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from apps.accounts.permissions import IsManager
from apps.accounts.views import LoginView, UserViewSet
from apps.audit.views import AuditLogViewSet
from apps.catalog import portal
from apps.catalog.views import CategoryViewSet, DepartmentViewSet
from apps.dataset.views import DatasetViewSet
from apps.datasource.views import DataSourceViewSet
from apps.execution.views import ExecutionViewSet
from apps.permission.views import GrantViewSet, MembershipViewSet

router = DefaultRouter()
router.register("datasources", DataSourceViewSet, basename="datasource")
router.register("datasets", DatasetViewSet, basename="dataset")
router.register("executions", ExecutionViewSet, basename="execution")
router.register("departments", DepartmentViewSet, basename="department")
router.register("categories", CategoryViewSet, basename="category")
router.register("users", UserViewSet, basename="user")
router.register("memberships", MembershipViewSet, basename="membership")
router.register("grants", GrantViewSet, basename="grant")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")


def health(_request: HttpRequest) -> JsonResponse:
    """健康检查，便于确认服务可用。"""
    return JsonResponse({"status": "ok", "service": "data-nexus", "version": "v0.15"})


@api_view(["GET"])
@permission_classes([IsManager])
def stats(_request: Request) -> Response:
    """管理端首页统计。"""
    from django.utils import timezone

    from apps.dataset.models import Dataset
    from apps.datasource.models import DataSource
    from apps.execution.models import Execution

    today = timezone.localdate()
    return Response(
        {
            "datasources": DataSource.objects.count(),
            "datasets": Dataset.objects.count(),
            "executions": Execution.objects.count(),
            "today_runs": Execution.objects.filter(started_at__date=today).count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    """返回当前登录用户信息与角色，供前端登录态校验与角色分流。"""
    user = request.user
    return Response(
        {
            "username": user.username,
            "is_superuser": user.is_superuser,
            "is_assistant_admin": getattr(user, "is_assistant_admin", False),
            "is_boss": getattr(user, "is_boss", False),
            # 是否可进入管理端（超管或辅助管理员）
            "is_manager": getattr(user, "is_manager_role", user.is_superuser),
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/token/", LoginView.as_view(), name="auth-token"),  # 账号密码换 Token + 审计
    path("api/auth/me/", me, name="auth-me"),
    path("api/stats/", stats, name="stats"),
    path("api/", include(router.urls)),  # /api/datasources/ ...
    # 用户端数据门户（按可见性）
    path("api/portal/tree/", portal.portal_tree, name="portal-tree"),
    path("api/portal/datasets/<int:pk>/", portal.portal_dataset_detail, name="portal-dataset"),
    path(
        "api/portal/executions/<int:pk>/download/", portal.portal_download, name="portal-download"
    ),
]
