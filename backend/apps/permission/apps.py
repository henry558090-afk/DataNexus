from django.apps import AppConfig


class PermissionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.permission"
    label = "permission"
    verbose_name = "权限"
