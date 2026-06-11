from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.catalog.models import FolderShare
from apps.permission.models import AccessRequest, DepartmentMembership
from apps.permission.serializers import AccessRequestSerializer, MembershipSerializer


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


class AccessRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """访问申请审批（仅管理员，v0.25）：列表 + 通过/拒绝。?status 过滤。"""

    serializer_class = AccessRequestSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = AccessRequest.objects.select_related("user", "folder", "reviewed_by").all()
        status_q = self.request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk: str | None = None) -> Response:
        ar = self.get_object()
        if ar.status == AccessRequest.Status.PENDING:
            # 通过即给该用户授权该文件夹（递归覆盖子文件夹/文件）
            FolderShare.objects.get_or_create(folder=ar.folder, subject_user=ar.user)
            ar.status = AccessRequest.Status.APPROVED
            ar.reviewed_by = request.user
            ar.reviewed_at = timezone.now()
            ar.save()
        return Response(AccessRequestSerializer(ar).data)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk: str | None = None) -> Response:
        ar = self.get_object()
        if ar.status == AccessRequest.Status.PENDING:
            ar.status = AccessRequest.Status.REJECTED
            ar.reviewed_by = request.user
            ar.reviewed_at = timezone.now()
            ar.save()
        return Response(AccessRequestSerializer(ar).data)
