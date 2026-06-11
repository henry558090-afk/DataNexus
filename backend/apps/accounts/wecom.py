"""企业微信（WeCom）SSO 对接（v0.27）。

零额外依赖：HTTP 用标准库 urllib。CORP_ID/AGENT_ID/SECRET 由 .env 配置；
未配置则视为未启用。所有外部调用集中在 _api_get，便于测试 mock。
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from django.conf import settings

_QYAPI = "https://qyapi.weixin.qq.com/cgi-bin"


def is_enabled() -> bool:
    return bool(
        getattr(settings, "WECOM_ENABLED", False)
        and settings.WECOM_CORP_ID
        and settings.WECOM_SECRET
    )


def authorize_url(redirect_uri: str, state: str = "data-nexus") -> str:
    """构造企业微信扫码登录授权 URL（前端跳转到这里）。"""
    params = {
        "appid": settings.WECOM_CORP_ID,
        "agentid": settings.WECOM_AGENT_ID,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return "https://login.work.weixin.qq.com/wwlogin/sso/login?" + urllib.parse.urlencode(params)


def _api_get(path: str, params: dict) -> dict:
    url = f"{_QYAPI}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 - 固定企微域名
        return json.loads(resp.read().decode())


def _access_token() -> str:
    data = _api_get(
        "gettoken", {"corpid": settings.WECOM_CORP_ID, "corpsecret": settings.WECOM_SECRET}
    )
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"企微 gettoken 失败：{data}")
    return data["access_token"]


def exchange_code_for_userid(code: str) -> str:
    """用扫码回调的 code 换企业微信 userid。"""
    token = _access_token()
    data = _api_get("auth/getuserinfo", {"access_token": token, "code": code})
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"企微 getuserinfo 失败：{data}")
    userid = data.get("userid") or data.get("UserId")
    if not userid:
        raise RuntimeError(f"企微未返回 userid（可能是外部联系人）：{data}")
    return userid
