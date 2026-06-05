from django.db import models


class Department(models.Model):
    """部门（目录第一级）。"""

    name = models.CharField("部门名", max_length=100, unique=True)
    order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "部门"
        verbose_name_plural = "部门"

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    """分类（目录第二级，挂在部门下）。"""

    name = models.CharField("分类名", max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="部门",
    )
    order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("department", "name")]
        verbose_name = "分类"
        verbose_name_plural = "分类"

    def __str__(self) -> str:
        return f"{self.department.name} / {self.name}"
