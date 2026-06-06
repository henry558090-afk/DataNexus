from django.apps import AppConfig


class DataSourceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.datasource"
    label = "datasource"
    verbose_name = "数据源"
