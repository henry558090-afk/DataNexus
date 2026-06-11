from django.apps import AppConfig


def _set_sqlite_pragmas(sender, connection, **kwargs):
    """SQLite 开 WAL + 合理超时，缓解 web/调度双进程并发写（其他库忽略）。"""
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=20000;")  # 与 settings OPTIONS.timeout 一致


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "账号"

    def ready(self):
        from django.db.backends.signals import connection_created

        connection_created.connect(_set_sqlite_pragmas)
