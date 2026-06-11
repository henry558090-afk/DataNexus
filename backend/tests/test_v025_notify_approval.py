"""v0.25 订阅推送（邮件/Webhook）+ 权限申请-审批流。"""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework.test import APIClient

from apps.catalog.models import Folder, FolderShare
from apps.dataset import notify
from apps.dataset.models import Dataset, Subscription
from apps.dataset.services import run_dataset
from apps.datasource.models import DataSource
from apps.permission.models import AccessRequest
from apps.permission.services import can_view_folder
from core import db

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="x", is_assistant_admin=True)


@pytest.fixture
def datasource(db):
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.password = "p"
    ds.save()
    return ds


def cli(u) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _dataset(datasource):
    folder = Folder.objects.create(name="月报")
    return Dataset.objects.create(
        name="应收", datasource=datasource, sql_text="SELECT 1", target_folder=folder
    )


# ---------- 推送 ----------
def test_email_notification_on_success(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    ds = _dataset(datasource)
    Subscription.objects.create(
        dataset=ds, channel=Subscription.Channel.EMAIL, target="boss@corp.com"
    )
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["x"], iter([(1,)])))
    run_dataset(ds)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["boss@corp.com"]
    assert "应收" in mail.outbox[0].subject


def test_webhook_notification(monkeypatch, datasource):
    ds = _dataset(datasource)
    Subscription.objects.create(
        dataset=ds, channel=Subscription.Channel.WEBHOOK, target="https://oapi.example/robot"
    )
    sent = {}

    def fake_webhook(target, subject, body):
        sent["target"] = target
        sent["body"] = body

    monkeypatch.setattr(notify, "_send_webhook", fake_webhook)
    f = type("F", (), {"id": 1, "name": "应收_20260611.xlsx", "row_count": 9, "created_at": "t"})()
    n = notify.notify_subscribers(ds, f)
    assert n == 1 and sent["target"] == "https://oapi.example/robot"


def test_notification_failure_does_not_break_run(
    manager, datasource, monkeypatch, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = _dataset(datasource)
    Subscription.objects.create(
        dataset=ds, channel=Subscription.Channel.WEBHOOK, target="https://bad"
    )

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(notify, "_send_webhook", boom)
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["x"], iter([(1,)])))
    f = run_dataset(ds)  # 推送失败但运行仍成功
    assert f.status == "success"


def test_subscription_crud_manager_only(manager, datasource, db):
    ds = _dataset(datasource)
    r = cli(manager).post(
        "/api/subscriptions/",
        {"dataset": ds.id, "channel": "email", "target": "a@b.com"},
        format="json",
    )
    assert r.status_code == 201
    user = User.objects.create_user("u", password="x")
    assert cli(user).get("/api/subscriptions/").status_code == 403


# ---------- 审批流 ----------
def test_access_request_flow(manager, datasource, db):
    user = User.objects.create_user("alice", password="x")
    folder = Folder.objects.create(name="财务密")
    # 用户申请（当前不可见）
    r = cli(user).post(
        "/api/portal/access-requests/", {"folder": folder.id, "reason": "对账需要"}, format="json"
    )
    assert r.status_code == 201
    ar_id = r.data["id"]
    assert not can_view_folder(user, folder)
    # 管理员通过 → 自动授权
    r2 = cli(manager).post(f"/api/access-requests/{ar_id}/approve/")
    assert r2.data["status"] == "approved"
    assert FolderShare.objects.filter(folder=folder, subject_user=user).exists()
    assert can_view_folder(user, folder)


def test_access_request_reject(manager, db):
    user = User.objects.create_user("bob", password="x")
    folder = Folder.objects.create(name="X")
    ar = AccessRequest.objects.create(user=user, folder=folder)
    r = cli(manager).post(f"/api/access-requests/{ar.id}/reject/")
    assert r.data["status"] == "rejected"
    assert not can_view_folder(user, folder)


def test_access_request_duplicate_returns_existing(db):
    user = User.objects.create_user("carl", password="x")
    folder = Folder.objects.create(name="Y")
    c = cli(user)
    r1 = c.post("/api/portal/access-requests/", {"folder": folder.id}, format="json")
    r2 = c.post("/api/portal/access-requests/", {"folder": folder.id}, format="json")
    assert r1.status_code == 201 and r2.status_code == 200
    assert AccessRequest.objects.filter(user=user, folder=folder).count() == 1
