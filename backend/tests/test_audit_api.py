"""审计日志单测：登录/运行/下载留痕 + 列表分页过滤 + 权限。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.catalog.models import Folder
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from core import db

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="pw12345", is_assistant_admin=True)


def cli(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _dataset() -> Dataset:
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.save()
    folder = Folder.objects.create(name="月报")
    return Dataset.objects.create(
        name="应收", datasource=ds, sql_text="SELECT 1", target_folder=folder
    )


def test_login_is_audited(db):
    User.objects.create_user("alice", password="pw12345")
    r = APIClient().post(
        "/api/auth/token/", {"username": "alice", "password": "pw12345"}, format="json"
    )
    assert r.status_code == 200 and "token" in r.data
    assert AuditLog.objects.filter(action="login", username="alice").exists()


def test_run_is_audited(manager, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = _dataset()
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    cli(manager).post(f"/api/datasets/{ds.id}/run/")
    assert AuditLog.objects.filter(action="run", target="应收").exists()


def test_download_is_audited(manager, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = _dataset()
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    fid = cli(manager).post(f"/api/datasets/{ds.id}/run/").data["id"]
    cli(manager).get(f"/api/datafiles/{fid}/download/")
    assert AuditLog.objects.filter(action="download").exists()


def test_audit_list_paginated_and_filtered(manager):
    AuditLog.objects.create(action="login", username="a")
    AuditLog.objects.create(action="download", username="b")
    r = cli(manager).get("/api/audit-logs/")
    assert r.status_code == 200 and "results" in r.data
    filtered = cli(manager).get("/api/audit-logs/?action=login")
    assert all(x["action"] == "login" for x in filtered.data["results"])


def test_audit_forbidden_for_member(db):
    u = User.objects.create_user("u", password="x")
    assert cli(u).get("/api/audit-logs/").status_code == 403
