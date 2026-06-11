from django.conf import settings
from django.db import models


class Dataset(models.Model):
    """SQL 任务：定时/手动跑 → 在目标文件夹里【新增】一个带日期命名的数据文件。"""

    name = models.CharField("名称", max_length=150)
    description = models.CharField("说明", max_length=500, blank=True)
    datasource = models.ForeignKey(
        "datasource.DataSource",
        on_delete=models.PROTECT,
        related_name="datasets",
        verbose_name="数据源",
    )
    sql_text = models.TextField("SQL")
    params = models.JSONField("参数定义", default=list, blank=True)

    # 输出
    target_folder = models.ForeignKey(
        "catalog.Folder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datasets",
        verbose_name="目标文件夹",
    )
    file_prefix = models.CharField("文件名前缀", max_length=150, blank=True)  # 空=用任务名
    date_format = models.CharField("日期格式", max_length=30, default="%Y%m%d")

    # 定时
    cron = models.CharField("Cron 定时", max_length=100, blank=True)
    interval_minutes = models.IntegerField("间隔(分钟)", null=True, blank=True)

    # 历史保留（0/空=全部保留）
    keep_count = models.IntegerField("保留份数", null=True, blank=True)
    keep_days = models.IntegerField("保留天数", null=True, blank=True)

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
        verbose_name = "数据集"
        verbose_name_plural = "数据集"

    def __str__(self) -> str:
        return self.name

    def build_filename(self, when) -> str:
        """按命名规范生成文件名：前缀_日期.xlsx。"""
        prefix = self.file_prefix or self.name
        try:
            stamp = when.strftime(self.date_format or "%Y%m%d")
        except (ValueError, TypeError):
            stamp = when.strftime("%Y%m%d")
        return f"{prefix}_{stamp}.xlsx"


class Subscription(models.Model):
    """数据集运行成功后的推送订阅（v0.25）：邮件 或 Webhook（钉钉/企业微信机器人）。"""

    class Channel(models.TextChoices):
        EMAIL = "email", "邮件"
        WEBHOOK = "webhook", "Webhook(钉钉/企微)"

    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="数据集"
    )
    channel = models.CharField("渠道", max_length=20, choices=Channel.choices)
    target = models.CharField("目标", max_length=500)  # 邮箱地址 或 webhook URL
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "推送订阅"
        verbose_name_plural = "推送订阅"

    def __str__(self) -> str:
        return f"{self.dataset_id}:{self.channel}:{self.target}"
