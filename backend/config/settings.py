"""Django 配置。

敏感配置一律从 .env 读取（见 .env.example），不硬编码、不进仓库。
路径用 pathlib，保证 Windows 开发 / Linux 部署一致。
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- 读取 .env ----
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    QUERY_MAX_ROWS=(int, 100000),
    QUERY_TIMEOUT_SECONDS=(int, 60),
    QUERY_FETCH_SIZE=(int, 1000),
    EXECUTION_KEEP=(int, 20),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-secret-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---- 应用 ----
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    # 业务应用
    "apps.accounts",
    "apps.catalog",
    "apps.datasource",
    "apps.dataset",
    "apps.execution",
    "apps.permission",
    "apps.audit",
]

# 自定义用户模型（含管理角色 / 老板标志）
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 生产直接发前端静态资源，免 Nginx
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---- 平台元数据库：默认 SQLite（开 WAL）；可用 DATABASE_URL 切到 MySQL，复用现有库 ----
# 例：DATABASE_URL=mysql://user:pass@host:3306/datanexus
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL", default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"
    )
}
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    # 增大锁等待，配合 WAL（PRAGMA 在 accounts.apps.ready 里设），缓解 web+调度双进程并发写
    DATABASES["default"].setdefault("OPTIONS", {})["timeout"] = 20

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---- 国际化 ----
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ---- 静态 / 媒体 ----
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- DRF：内置账号 + Token 认证 ----
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # 带绝对有效期的 Token 认证（SEC2），登录会轮换刷新有效期
        "apps.accounts.authentication.ExpiringTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # 限流：仅给登录接口配作用域速率，防暴力撞库（SEC1）。
    # 用默认本地内存缓存，多 worker 下为每进程独立；如需全局严格限流，
    # 配共享缓存（如数据库缓存 / Redis）即可，无需改代码。
    "DEFAULT_THROTTLE_RATES": {
        "login": env("LOGIN_THROTTLE_RATE", default="10/min"),
    },
}

# ---- CORS ----
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# ---- 业务安全护栏（取数）----
FERNET_KEY = env("FERNET_KEY", default="")
QUERY_MAX_ROWS = env("QUERY_MAX_ROWS")
QUERY_TIMEOUT_SECONDS = env("QUERY_TIMEOUT_SECONDS")
QUERY_FETCH_SIZE = env("QUERY_FETCH_SIZE")
# 每个数据集保留最近 N 次执行/文件，超出自动清理
EXECUTION_KEEP = env("EXECUTION_KEEP")
# 运行中文件超过该秒数仍未结束 → 视为进程崩溃留下的僵尸，清道夫标记为失败
STUCK_RUNNING_SECONDS = env.int("STUCK_RUNNING_SECONDS", default=1800)
# 登录 Token 绝对有效期（秒），默认 7 天；过期需重新登录（SEC2）。0=永不过期
TOKEN_TTL_SECONDS = env.int("TOKEN_TTL_SECONDS", default=7 * 24 * 3600)
# 数据集运行是否内联执行（同步）。默认 False=后台线程异步（S1）；测试置 True 便于断言
DATASET_RUN_INLINE = env.bool("DATASET_RUN_INLINE", default=False)

# ---- 订阅推送（v0.25）：邮件 + Webhook（钉钉/企业微信机器人）----
# 邮件：默认开发用 console 后端打印；生产填 SMTP。
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="data-nexus@localhost")
# 平台对外访问地址，用于推送消息里拼下载链接（如 https://data.corp.com）
PLATFORM_BASE_URL = env("PLATFORM_BASE_URL", default="")
# Webhook 推送超时秒
WEBHOOK_TIMEOUT_SECONDS = env.int("WEBHOOK_TIMEOUT_SECONDS", default=10)

# ---- 安全加固 ----
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    # 仅生产启用，避免开发期 https 相关设置影响本地调试
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# 域名 + HTTPS（走反向代理）时必须配，否则后台登录等会报 CSRF 403。
# 例：CSRF_TRUSTED_ORIGINS=https://data.corp.com
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# ---- 前端发布：生产把 frontend/dist 交给 WhiteNoise，在根路径直接发页面（免 Nginx）----
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    WHITENOISE_ROOT = str(FRONTEND_DIST)
WHITENOISE_INDEX_FILE = True

# ---- 日志：开发输出控制台；生产滚动写文件，便于排查 ----
LOG_DIR = BASE_DIR / "logs"
if not DEBUG:
    LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"std": {"format": "{asctime} {levelname} {name} {message}", "style": "{"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "std"},
        **(
            {}
            if DEBUG
            else {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(LOG_DIR / "app.log"),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "formatter": "std",
                    "encoding": "utf-8",
                }
            }
        ),
    },
    "root": {"handlers": ["console"] if DEBUG else ["console", "file"], "level": "INFO"},
}
