from rest_framework import serializers

from apps.permission.models import AccessRequest, DepartmentMembership


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = DepartmentMembership
        fields = ["id", "user", "username", "department", "department_name"]


class AccessRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    folder_name = serializers.CharField(source="folder.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "user",
            "username",
            "folder",
            "folder_name",
            "reason",
            "status",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = ["id", "user", "status", "reviewed_by", "reviewed_at", "created_at"]
