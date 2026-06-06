from rest_framework import serializers

from apps.datasource.models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    """数据源序列化。密码 write_only，永不回显明文。"""

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
    )
    # 是否已设置密码（供前端展示，不泄露明文）
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = [
            "id",
            "name",
            "db_type",
            "host",
            "port",
            "service_name",
            "username",
            "password",
            "has_password",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def get_has_password(self, obj: DataSource) -> bool:
        return bool(obj.password_encrypted)

    def create(self, validated_data: dict) -> DataSource:
        raw_password = validated_data.pop("password", "")
        instance = DataSource(**validated_data)
        instance.password = raw_password  # 触发加密
        request = self.context.get("request")
        if request is not None:
            instance.created_by = request.user
        instance.save()
        return instance

    def update(self, instance: DataSource, validated_data: dict) -> DataSource:
        # 密码留空表示不修改，避免误清空
        raw_password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if raw_password:
            instance.password = raw_password
        instance.save()
        return instance
