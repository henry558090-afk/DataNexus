"""数据源 API 单元测试：加密、密码不回显、权限、测试连接（mock）。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.datasource.models import DataSource
from core import db

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="x", is_assistant_admin=True)


@pytest.fixture
def normal(db):
    return User.objects.create_user("usr", password="x")


def auth_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_encrypts_password_and_hides_it(manager):
    client = auth_client(manager)
    resp = client.post(
        "/api/datasources/",
        {
            "name": "ora1",
            "host": "h",
            "port": 1521,
            "service_name": "orcl",
            "username": "scott",
            "password": "tiger",
        },
        format="json",
    )
    assert resp.status_code == 201
    assert "password" not in resp.data  # 永不回显
    ds = DataSource.objects.get(name="ora1")
    assert ds.password_encrypted and ds.password_encrypted != "tiger"  # 已加密
    assert ds.password == "tiger"  # 可解密
    assert ds.created_by == manager


def test_normal_user_forbidden(normal):
    client = auth_client(normal)
    assert client.get("/api/datasources/").status_code == 403
    assert client.post("/api/datasources/", {}, format="json").status_code == 403


def test_unauthenticated_denied():
    assert APIClient().get("/api/datasources/").status_code == 401


def test_update_blank_password_keeps_old(manager):
    ds = DataSource(name="ora2", host="h", port=1521, service_name="s", username="u")
    ds.password = "secret"
    ds.created_by = manager
    ds.save()
    client = auth_client(manager)
    resp = client.patch(f"/api/datasources/{ds.id}/", {"host": "h2", "password": ""}, format="json")
    assert resp.status_code == 200
    ds.refresh_from_db()
    assert ds.host == "h2"
    assert ds.password == "secret"  # 留空不改密码


def test_test_connection_action_ok(manager, monkeypatch):
    ds = DataSource(name="ora3", host="h", port=1521, service_name="s", username="u")
    ds.password = "p"
    ds.save()
    monkeypatch.setattr(db, "test_connection", lambda params, **k: None)
    resp = auth_client(manager).post(f"/api/datasources/{ds.id}/test/")
    assert resp.status_code == 200
    assert resp.data["ok"] is True


def test_test_connection_action_fail(manager, monkeypatch):
    ds = DataSource(name="ora4", host="h", port=1521, service_name="s", username="u")
    ds.password = "p"
    ds.save()

    def boom(params, **k):
        raise RuntimeError("ORA-12541 no listener")

    monkeypatch.setattr(db, "test_connection", boom)
    resp = auth_client(manager).post(f"/api/datasources/{ds.id}/test/")
    assert resp.data["ok"] is False
    assert "ORA-12541" in resp.data["message"]


def test_test_connection_params_endpoint(manager, monkeypatch):
    monkeypatch.setattr(db, "test_connection", lambda params, **k: None)
    resp = auth_client(manager).post(
        "/api/datasources/test-connection/",
        {
            "host": "h",
            "port": 1521,
            "service_name": "s",
            "username": "u",
            "password": "p",
        },
        format="json",
    )
    assert resp.data["ok"] is True


def test_create_mysql_datasource(manager):
    resp = auth_client(manager).post(
        "/api/datasources/",
        {
            "name": "mysql1",
            "db_type": "mysql",
            "host": "h",
            "port": 3306,
            "service_name": "appdb",
            "username": "ro",
            "password": "p",
        },
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["db_type"] == "mysql"


def test_stats_endpoint(manager):
    resp = auth_client(manager).get("/api/stats/")
    assert resp.status_code == 200
    assert "datasources" in resp.data and "today_runs" in resp.data
