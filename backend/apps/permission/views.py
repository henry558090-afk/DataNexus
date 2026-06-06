from rest_framework import viewsets

from apps.accounts.permissions import IsManager
from apps.permission.models import DepartmentMembership, Grant
from apps.permission.serializers import GrantSerializer, MembershipSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    """部门成员关系（仅管理员）。支持 ?user 过滤。"""

    serializer_class = MembershipSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = DepartmentMembership.objects.select_related("user", "department").all()
        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs


class GrantViewSet(viewsets.ModelViewSet):
    """成员授权（仅管理员）。支持 ?user 过滤（按个人授权主体）。"""

    serializer_class = GrantSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = Grant.objects.all()
        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(subject_user_id=user_id)
        return qs
