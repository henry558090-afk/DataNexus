from django.conf import settings
from django.db import models

from core import crypto


class DataSource(models.Model):
    """Oracle 数据源连接。密码加密存储，绝不明文落库。"""

    name = models.CharField("名称", max_length=100, unique=True)
    host = models.CharField("主机", max_length=200)
    port = models.IntegerField("端口", default=1521)
    service_name = models.CharField("服务名", max_length=100)
    username = models.CharField("账号", max_length=100)
    password_encrypted = models.TextField("密码(加密)", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datasources",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "数据源"
        verbose_name_plural = "数据源"

    def __str__(self) -> str:
        return self.name

    @property
    def password(self) -> str:
        """读取明文密码（解密）。"""
        return crypto.decrypt(self.password_encrypted) if self.password_encrypted else ""

    @password.setter
    def password(self, raw: str) -> None:
        """写入明文密码时自动加密。"""
        self.password_encrypted = crypto.encrypt(raw) if raw else ""
