from django.conf import settings
from django.db import models


class DepartmentMembership(models.Model):
    """用户—部门归属（一人可属于多个部门）。不再细分部门内角色。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    department = models.ForeignKey(
        "catalog.Department",
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    class Meta:
        unique_together = [("user", "department")]
        verbose_name = "部门成员"
        verbose_name_plural = "部门成员"

    def __str__(self) -> str:
        return f"{self.user_id}@{self.department_id}"
