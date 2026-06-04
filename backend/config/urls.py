"""根 URL 路由。"""

from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import path


def health(_request: HttpRequest) -> JsonResponse:
    """健康检查，便于确认服务可用。"""
    return JsonResponse({"status": "ok", "service": "data-nexus", "version": "v0.02"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
]
