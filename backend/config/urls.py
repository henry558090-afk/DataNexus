"""根 URL 路由。"""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.urls import include, path, re_path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from apps.accounts.permissions import IsManager
from apps.accounts.views import LoginView, LogoutView, UserViewSet
from apps.audit.views import AuditLogViewSet
from apps.catalog import portal
from apps.catalog.views import DepartmentViewSet, FolderShareViewSet, FolderViewSet
from apps.dataset.views import DatasetViewSet, SubscriptionViewSet
from apps.datasource.views import DataSourceViewSet
from apps.execution.views import DataFileViewSet
from apps.permission.views import AccessRequestViewSet, MembershipViewSet

router = DefaultRouter()
router.register("datasources", DataSourceViewSet, basename="datasource")
router.register("datasets", DatasetViewSet, basename="dataset")
router.register("datafiles", DataFileViewSet, basename="datafile")
router.register("departments", DepartmentViewSet, basename="department")
router.register("folders", FolderViewSet, basename="folder")
router.register("folder-shares", FolderShareViewSet, basename="folder-share")
router.register("users", UserViewSet, basename="user")
router.register("memberships", MembershipViewSet, basename="membership")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("access-requests", AccessRequestViewSet, basename="access-request")


def health(_request: HttpRequest) -> JsonResponse:
    """健康检查，便于确认服务可用。"""
    return JsonResponse({"status": "ok", "service": "data-nexus", "version": "v0.22"})


def spa(_request: HttpRequest):
    """前端单页应用入口：非 api/admin/static 的路径都返回 index.html（支持前端路由刷新）。"""
    index = settings.FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(open(index, "rb"))
    return HttpResponse("前端未构建（请在 frontend 执行 npm run build）", status=404)


@api_view(["GET"])
@permission_classes([IsManager])
def stats(_request: Request) -> Response:
    """管理端首页统计。"""
    from django.utils import timezone

    from apps.dataset.models import Dataset
    from apps.datasource.models import DataSource
    from apps.execution.models import DataFile

    today = timezone.localdate()
    return Response(
        {
            "datasources": DataSource.objects.count(),
            "datasets": Dataset.objects.count(),
            "files": DataFile.objects.count(),
            "today_runs": DataFile.objects.filter(created_at__date=today).count(),
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
    path("django-admin/", admin.site.urls),  # 挪开，给前端 /admin/* 让路
    path("api/health/", health, name="health"),
    path("api/auth/token/", LoginView.as_view(), name="auth-token"),  # 账号密码换 Token + 审计
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),  # 登出删 Token
    path("api/auth/me/", me, name="auth-me"),
    path("api/stats/", stats, name="stats"),
    path("api/", include(router.urls)),  # /api/datasources/ ...
    # 用户端数据门户（按可见性）
    path("api/portal/tree/", portal.portal_tree, name="portal-tree"),
    path(
        "api/portal/folders/<int:pk>/files/", portal.portal_folder_files, name="portal-folder-files"
    ),
    path("api/portal/search/", portal.portal_search, name="portal-search"),
    path("api/portal/files/<int:pk>/download/", portal.portal_download, name="portal-download"),
    path("api/portal/files/<int:pk>/preview/", portal.portal_file_preview, name="portal-preview"),
    path("api/portal/favorites/", portal.portal_favorites, name="portal-favorites"),
    path(
        "api/portal/folders/<int:pk>/favorite/",
        portal.portal_toggle_favorite,
        name="portal-toggle-favorite",
    ),
    path(
        "api/portal/recent-downloads/",
        portal.portal_recent_downloads,
        name="portal-recent-downloads",
    ),
    path("api/portal/updates/", portal.portal_updates, name="portal-updates"),
    path(
        "api/portal/access-requests/", portal.portal_access_requests, name="portal-access-requests"
    ),
    # 前端单页：放最后，排除 api/django-admin/static/media（/admin/* 留给前端）
    re_path(r"^(?!api/|django-admin/|static/|media/).*$", spa, name="spa"),
]
