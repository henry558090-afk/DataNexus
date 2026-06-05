from django.conf import settings
from django.db import models


class DepartmentMembership(models.Model):
    """用户在某部门内的身份（数据可见角色）。

    一个用户可属于多个部门；总监 = 在多个部门挂此关系。
    """

    class Role(models.TextChoices):
        DIRECTOR = "director", "总监"
        MANAGER = "manager", "部门主管"
        MEMBER = "member", "成员"

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
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    see_all_in_dept = models.BooleanField("成员可见本部门全部", default=False)

    class Meta:
        unique_together = [("user", "department")]
        verbose_name = "部门成员"
        verbose_name_plural = "部门成员"

    def __str__(self) -> str:
        return f"{self.user_id}@{self.department_id}:{self.role}"


class Grant(models.Model):
    """成员级授权：主体（个人 或 部门角色组）→ 目标（分类 或 数据集）。

    - 个人授权：填 ``subject_user``。
    - 角色组授权：填 ``subject_department`` + ``subject_role``（如给"财务部-成员"）。
    - 目标二选一：``category`` 或 ``dataset``。
    """

    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grants",
    )
    subject_department = models.ForeignKey(
        "catalog.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="role_grants",
    )
    subject_role = models.CharField(max_length=20, blank=True)

    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grants",
    )
    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grants",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "授权"
        verbose_name_plural = "授权"

    def __str__(self) -> str:
        subject = self.subject_user_id or f"{self.subject_department_id}:{self.subject_role}"
        target = self.dataset_id and f"dataset#{self.dataset_id}" or f"category#{self.category_id}"
        return f"{subject} -> {target}"
