from rest_framework import serializers

from apps.permission.models import DepartmentMembership, Grant


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = DepartmentMembership
        fields = [
            "id",
            "user",
            "username",
            "department",
            "department_name",
            "role",
            "see_all_in_dept",
        ]


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = [
            "id",
            "subject_user",
            "subject_department",
            "subject_role",
            "category",
            "dataset",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
