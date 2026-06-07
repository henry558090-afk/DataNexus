from rest_framework import viewsets

from apps.accounts.permissions import IsManager
from apps.catalog.models import Department, Folder, FolderShare
from apps.catalog.serializers import (
    DepartmentSerializer,
    FolderSerializer,
    FolderShareSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理（仅管理员）。"""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsManager]


class FolderViewSet(viewsets.ModelViewSet):
    """文件夹管理（仅管理员）：建/列/重命名/移动(改 parent)/删。支持 ?parent 过滤。"""

    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        if "parent" in self.request.query_params:
            parent = self.request.query_params.get("parent")
            qs = (
                qs.filter(parent__isnull=True)
                if parent in ("", "null")
                else qs.filter(parent_id=parent)
            )
        return qs


class FolderShareViewSet(viewsets.ModelViewSet):
    """文件夹授权（仅管理员）：folder → 部门 或 个人。支持 ?folder 过滤。"""

    queryset = FolderShare.objects.select_related("subject_department", "subject_user").all()
    serializer_class = FolderShareSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        folder_id = self.request.query_params.get("folder")
        if folder_id:
            qs = qs.filter(folder_id=folder_id)
        return qs
