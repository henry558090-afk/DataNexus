from django.conf import settings
from django.db import models


class DataFile(models.Model):
    """数据文件：文件夹里的一个 Excel。数据集每次运行新增一个（带日期命名）。"""

    class Status(models.TextChoices):
        RUNNING = "running", "生成中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    folder = models.ForeignKey(
        "catalog.Folder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files",
        verbose_name="所在文件夹",
    )
    name = models.CharField("文件名", max_length=255)
    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        verbose_name="来源数据集",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    row_count = models.IntegerField("行数", null=True, blank=True)
    file_path = models.CharField("文件路径", max_length=500, blank=True)
    file_size = models.BigIntegerField("大小(字节)", null=True, blank=True)
    error_msg = models.TextField("错误信息", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_files",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "数据文件"
        verbose_name_plural = "数据文件"

    def __str__(self) -> str:
        return self.name
