from rest_framework import serializers

from apps.catalog.models import Department, Folder, FolderShare


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["id", "name", "parent", "order", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_parent(self, value):
        # 移动时禁止把文件夹挂到自己或自己的子孙下（防成环）
        if value is None or self.instance is None:
            return value
        node = value
        while node is not None:
            if node.id == self.instance.id:
                raise serializers.ValidationError("不能移动到自身或其子文件夹下")
            node = node.parent
        return value


class FolderShareSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="subject_department.name", read_only=True)
    username = serializers.CharField(source="subject_user.username", read_only=True)

    class Meta:
        model = FolderShare
        fields = [
            "id",
            "folder",
            "subject_department",
            "department_name",
            "subject_user",
            "username",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        dept = attrs.get("subject_department")
        user = attrs.get("subject_user")
        if bool(dept) == bool(user):
            raise serializers.ValidationError("授权对象须二选一：部门 或 个人")
        return attrs
