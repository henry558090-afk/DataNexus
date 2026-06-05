"""根 URL 路由。"""

from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response


def health(_request: HttpRequest) -> JsonResponse:
    """健康检查，便于确认服务可用。"""
    return JsonResponse({"status": "ok", "service": "data-nexus", "version": "v0.07"})


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
    path("api/auth/token/", obtain_auth_token, name="auth-token"),  # 账号密码换 Token
    path("api/auth/me/", me, name="auth-me"),
]
