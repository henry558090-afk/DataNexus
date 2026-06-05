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
    return JsonResponse({"status": "ok", "service": "data-nexus", "version": "v0.04"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    """返回当前登录用户信息，供前端校验登录态。"""
    user = request.user
    return Response({"username": user.username, "is_staff": user.is_staff})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/token/", obtain_auth_token, name="auth-token"),  # 账号密码换 Token
    path("api/auth/me/", me, name="auth-me"),
]
