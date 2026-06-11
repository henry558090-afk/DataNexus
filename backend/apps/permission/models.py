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


class AccessRequest(models.Model):
    """用户对某文件夹的访问申请（v0.25）：管理员审批，通过即建 FolderShare 授权给该用户。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待审批"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_requests"
    )
    folder = models.ForeignKey(
        "catalog.Folder", on_delete=models.CASCADE, related_name="access_requests"
    )
    reason = models.CharField("申请理由", max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "访问申请"
        verbose_name_plural = "访问申请"

    def __str__(self) -> str:
        return f"{self.user_id}→folder#{self.folder_id}:{self.status}"
