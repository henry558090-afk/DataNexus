from rest_framework import viewsets

from apps.accounts.permissions import IsManager
from apps.catalog.models import Category, Department
from apps.catalog.serializers import CategorySerializer, DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理（仅管理员）。"""

    queryset = Department.objects.prefetch_related("categories").all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsManager]


class CategoryViewSet(viewsets.ModelViewSet):
    """分类管理（仅管理员）。支持 ?department 过滤。"""

    queryset = Category.objects.select_related("department").all()
    serializer_class = CategorySerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        department_id = self.request.query_params.get("department")
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs
