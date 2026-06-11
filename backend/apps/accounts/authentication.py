"""带有效期的 Token 认证（SEC2）。

默认 DRF Token 永不过期，一旦泄漏即永久有效。这里在标准 Token 认证之上加一道
绝对有效期校验：token 自创建（每次登录会轮换刷新）起超过 settings.TOKEN_TTL_SECONDS
即失效，并顺手删除，避免僵尸 token 越积越多。
"""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    """在标准 Token 认证基础上增加绝对有效期。"""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        ttl = getattr(settings, "TOKEN_TTL_SECONDS", 0)
        if ttl and token.created < timezone.now() - timezone.timedelta(seconds=ttl):
            token.delete()
            raise AuthenticationFailed("登录已过期，请重新登录。")
        return user, token
