"""审计写入助手。任何数据访问动作都应调用 log()。"""

from __future__ import annotations

from apps.audit.models import AuditLog


def client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log(action: str, *, user=None, request=None, target: str = "") -> None:
    """记录一条审计。失败不影响主流程。"""
    ip = None
    if request is not None:
        ip = client_ip(request)
        if user is None:
            user = getattr(request, "user", None)
    real_user = user if (user is not None and getattr(user, "is_authenticated", False)) else None
    try:
        AuditLog.objects.create(
            user=real_user,
            username=getattr(real_user, "username", "") or "",
            action=action,
            target=target[:200],
            ip=ip,
        )
    except Exception:  # noqa: BLE001 - 审计失败不应阻断业务
        pass
