"""对称加密：用于数据源密码等敏感字段的加解密。

使用 Fernet（AES-128-CBC + HMAC）。密钥从 Django settings.FERNET_KEY 读取，
该值来自 .env，绝不进仓库（开发规范第 6 节）。
"""

from __future__ import annotations

from cryptography.fernet import Fernet


def _get_fernet(key: str | bytes | None = None) -> Fernet:
    """构造 Fernet 实例；key 为空时从 Django settings 读取。"""
    if key is None:
        from django.conf import settings

        key = settings.FERNET_KEY
    if not key:
        raise RuntimeError("未配置 FERNET_KEY，无法加解密。请在 .env 中设置。")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(plaintext: str, key: str | bytes | None = None) -> str:
    """加密明文，返回可存库的字符串。"""
    return _get_fernet(key).encrypt(plaintext.encode()).decode()


def decrypt(token: str, key: str | bytes | None = None) -> str:
    """解密密文，返回明文。"""
    return _get_fernet(key).decrypt(token.encode()).decode()
