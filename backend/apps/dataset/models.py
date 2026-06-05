from django.conf import settings
from django.db import models


class Dataset(models.Model):
    """数据集：一段 SQL + 归属分类 + 数据源，运行后产出 Excel 文件。

    取代旧设计的「查询任务」。定时规则为空表示仅手动运行。
    """

    name = models.CharField("名称", max_length=150)
    description = models.CharField("说明", max_length=500, blank=True)
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        related_name="datasets",
        verbose_name="归属分类",
    )
    datasource = models.ForeignKey(
        "datasource.DataSource",
        on_delete=models.PROTECT,
        related_name="datasets",
        verbose_name="数据源",
    )
    sql_text = models.TextField("SQL")
    params = models.JSONField("参数定义", default=list, blank=True)
    cron = models.CharField("Cron 定时", max_length=100, blank=True)
    interval_minutes = models.IntegerField("间隔(分钟)", null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datasets",
    )
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [("category", "name")]
        verbose_name = "数据集"
        verbose_name_plural = "数据集"

    def __str__(self) -> str:
        return self.name
