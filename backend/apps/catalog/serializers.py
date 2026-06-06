from rest_framework import serializers

from apps.catalog.models import Category, Department


class CategorySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "department", "department_name", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "order", "created_at", "categories"]
        read_only_fields = ["id", "created_at"]
