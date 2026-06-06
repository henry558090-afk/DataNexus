from rest_framework import viewsets

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
