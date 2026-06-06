"""审计日志单测：登录/运行/下载留痕 + 列表分页过滤 + 权限。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from core import db

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="pw12345", is_assistant_admin=True)


def cli(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _dataset() -> Dataset:
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.save()
    return Dataset.objects.create(name="应收", datasource=ds, sql_text="SELECT 1")


def test_login_is_audited(db):
    User.objects.create_user("alice", password="pw12345")
    resp = APIClient().post(
        "/api/auth/token/", {"username": "alice", "password": "pw12345"}, format="json"
    )
    assert resp.status_code == 200
    assert "token" in resp.data
    assert AuditLog.objects.filter(action="login", username="alice").exists()


def test_run_is_audited(manager, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    dataset = _dataset()
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    cli(manager).post(f"/api/datasets/{dataset.id}/run/")
    assert AuditLog.objects.filter(action="run", target="应收").exists()


def test_download_is_audited(manager, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    dataset = _dataset()
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    eid = cli(manager).post(f"/api/datasets/{dataset.id}/run/").data["id"]
    cli(manager).get(f"/api/executions/{eid}/download/")
    assert AuditLog.objects.filter(action="download", target="应收").exists()


def test_audit_list_paginated_and_filtered(manager):
    AuditLog.objects.create(action="login", username="a")
    AuditLog.objects.create(action="download", username="b")
    resp = cli(manager).get("/api/audit-logs/")
    assert resp.status_code == 200
    assert "results" in resp.data and "count" in resp.data
    filtered = cli(manager).get("/api/audit-logs/?action=login")
    assert all(x["action"] == "login" for x in filtered.data["results"])


def test_audit_forbidden_for_member(db):
    user = User.objects.create_user("u", password="x")
    assert cli(user).get("/api/audit-logs/").status_code == 403
