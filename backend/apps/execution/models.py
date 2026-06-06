from django.conf import settings
from django.db import models


class Execution(models.Model):
    """数据集的一次执行 = 一个数据文件版本。"""

    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name="数据集",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    row_count = models.IntegerField("行数", null=True, blank=True)
    file_path = models.CharField("文件路径", max_length=500, blank=True)
    file_size = models.BigIntegerField("文件大小(字节)", null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error_msg = models.TextField("错误信息", blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
    )
    is_latest = models.BooleanField("最新版本", default=False)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "执行记录"
        verbose_name_plural = "执行记录"

    def __str__(self) -> str:
        return f"{self.dataset_id} @ {self.started_at:%Y-%m-%d %H:%M}"
