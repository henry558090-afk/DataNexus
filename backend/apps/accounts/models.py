from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """平台用户。

    管理角色（管系统）：
        - 超级管理员：Django 内置 ``is_superuser``；
        - 辅助管理员：``is_assistant_admin``（能力同超管，但不能管理超管）。
    数据可见最高级：``is_boss``（老板，可见全部数据）。

    部门内角色（总监/主管/成员）见 apps.permission.DepartmentMembership。
    """

    is_assistant_admin = models.BooleanField("辅助管理员", default=False)
    is_boss = models.BooleanField("老板（可见全部数据）", default=False)

    @property
    def is_manager_role(self) -> bool:
        """是否可进管理端：超级管理员或辅助管理员。"""
        return bool(self.is_superuser or self.is_assistant_admin)
