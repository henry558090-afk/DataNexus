from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """审计日志：谁、何时、做了什么、来自哪个 IP。"""

    class Action(models.TextChoices):
        LOGIN = "login", "登录"
        RUN = "run", "运行数据集"
        DOWNLOAD = "download", "下载文件"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    username = models.CharField("账号", max_length=150, blank=True)  # 冗余，防用户删除后丢失
    action = models.CharField("动作", max_length=20, choices=Action.choices)
    target = models.CharField("对象", max_length=200, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"

    def __str__(self) -> str:
        return f"{self.username} {self.action} {self.target}"
