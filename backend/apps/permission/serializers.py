from rest_framework import serializers

from apps.permission.models import DepartmentMembership


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = DepartmentMembership
        fields = ["id", "user", "username", "department", "department_name"]
