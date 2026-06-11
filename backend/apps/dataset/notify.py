"""数据集运行成功后的推送（v0.25）：邮件 + Webhook（钉钉/企业微信机器人）。

零额外依赖：邮件走 Django send_mail；Webhook 用标准库 urllib POST JSON。
推送失败只记日志，绝不影响主运行流程。
"""

from __future__ import annotations

import json
import logging
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

from apps.dataset.models import Subscription

logger = logging.getLogger(__name__)


def _send_email(target: str, subject: str, body: str) -> None:
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [target], fail_silently=False)


def _send_webhook(target: str, subject: str, body: str) -> None:
    """POST 钉钉/企业微信机器人通用 text 消息格式。"""
    payload = json.dumps({"msgtype": "text", "text": {"content": f"{subject}\n{body}"}}).encode()
    req = urllib.request.Request(
        target, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    timeout = getattr(settings, "WEBHOOK_TIMEOUT_SECONDS", 10)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - 目标由管理员配置
        resp.read()


def notify_subscribers(dataset, datafile) -> int:
    """给数据集的活跃订阅推送"运行完成"。返回成功推送的条数。"""
    subs = list(Subscription.objects.filter(dataset=dataset, is_active=True))
    if not subs:
        return 0
    subject = f"[data-nexus] {dataset.name} 运行完成"
    base = getattr(settings, "PLATFORM_BASE_URL", "") or ""
    link = f"\n下载：{base}/api/portal/files/{datafile.id}/download/" if base else ""
    body = f"文件：{datafile.name}\n行数：{datafile.row_count}\n时间：{datafile.created_at}{link}"
    sent = 0
    for sub in subs:
        try:
            if sub.channel == Subscription.Channel.EMAIL:
                _send_email(sub.target, subject, body)
            else:
                _send_webhook(sub.target, subject, body)
            sent += 1
        except Exception:  # noqa: BLE001 - 推送失败不影响主流程
            logger.exception("推送失败 dataset=%s sub=%s", dataset.id, sub.id)
    return sent
