from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户管理。密码 write_only；超管标志只读（不能通过此接口提权为超管）。"""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "is_superuser",
            "is_assistant_admin",
            "is_boss",
            "is_active",
            "password",
        ]
        read_only_fields = ["id", "is_superuser"]

    def create(self, validated_data: dict):
        raw_password = validated_data.pop("password", "") or None
        user = User(**validated_data)
        if raw_password:
            user.set_password(raw_password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data: dict):
        raw_password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if raw_password:
            instance.set_password(raw_password)
        instance.save()
        return instance
