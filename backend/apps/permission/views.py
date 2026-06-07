from rest_framework import viewsets

from apps.accounts.permissions import IsManager
from apps.permission.models import DepartmentMembership
from apps.permission.serializers import MembershipSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    """部门成员关系（仅管理员）。支持 ?user / ?department 过滤。"""

    serializer_class = MembershipSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = DepartmentMembership.objects.select_related("user", "department").all()
        user_id = self.request.query_params.get("user")
        dept_id = self.request.query_params.get("department")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        return qs
