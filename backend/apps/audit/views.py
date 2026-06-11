from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from core.pagination import DefaultPagination


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """审计日志（仅管理员，分页）。支持 ?action / ?user 过滤。"""

    serializer_class = AuditLogSerializer
    permission_classes = [IsManager]
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = AuditLog.objects.all()
        action = self.request.query_params.get("action")
        user_id = self.request.query_params.get("user")
        if action:
            qs = qs.filter(action=action)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    @action(detail=False, methods=["get"])
    def stats(self, request: Request) -> Response:
        """审计可视化（v0.27）：近 N 天按动作分类、每日趋势、活跃用户 Top。"""
        try:
            days = max(1, min(90, int(request.query_params.get("days", 30))))
        except (TypeError, ValueError):
            days = 30
        since = timezone.now() - timedelta(days=days)
        qs = AuditLog.objects.filter(created_at__gte=since)
        by_action = list(qs.values("action").annotate(count=Count("id")).order_by("-count"))
        by_day = list(
            qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        top_users = list(
            qs.exclude(username="")
            .values("username")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(
            {
                "days": days,
                "total": qs.count(),
                "by_action": by_action,
                "by_day": [{"day": str(d["day"]), "count": d["count"]} for d in by_day],
                "top_users": top_users,
            }
        )
