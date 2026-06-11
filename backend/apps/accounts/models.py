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


class WecomLoginCode(models.Model):
    """企业微信 SSO 一次性换取码（B5 修复）。

    回调不再把 Token 直接放跳转 URL（会进日志/历史），而是下发一个一次性短码，
    前端用它 POST 换 Token，换完即删。DB 存储以兼容多 worker。
    """

    code = models.CharField(max_length=64, unique=True, db_index=True)
    token_key = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "企微登录换取码"
        verbose_name_plural = verbose_name
