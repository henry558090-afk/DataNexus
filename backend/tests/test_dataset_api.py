"""数据集 + 执行 API 单测：SQL 校验、运行生成 Excel(mock)、最新版本、失败记录、下载、权限。"""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from apps.execution.models import Execution
from core import oracle_client

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


def client_for(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_dataset(datasource) -> Dataset:
    return Dataset.objects.create(
        name="明细表", datasource=datasource, sql_text="SELECT 1 FROM dual"
    )


def test_create_rejects_non_select(manager, datasource):
    resp = client_for(manager).post(
        "/api/datasets/",
        {"name": "d1", "datasource": datasource.id, "sql_text": "DELETE FROM t"},
        format="json",
    )
    assert resp.status_code == 400


def test_create_ok_sets_owner(manager, datasource):
    resp = client_for(manager).post(
        "/api/datasets/",
        {"name": "d1", "datasource": datasource.id, "sql_text": "SELECT 1 FROM dual"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["owner"] == manager.id


def test_preview(manager, datasource, monkeypatch):
    ds = make_dataset(datasource)
    monkeypatch.setattr(oracle_client, "preview_query", lambda *a, **k: (["a", "b"], [(1, 2)]))
    resp = client_for(manager).post(f"/api/datasets/{ds.id}/preview/")
    assert resp.data["ok"] is True
    assert resp.data["columns"] == ["a", "b"]


def test_run_generates_excel(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)

    def fake_stream(params, sql, **kwargs):
        return ["a", "b"], iter([(1, 2), (3, 4)])

    monkeypatch.setattr(oracle_client, "stream_query", fake_stream)
    resp = client_for(manager).post(f"/api/datasets/{ds.id}/run/")
    assert resp.status_code == 200
    assert resp.data["status"] == "success"
    assert resp.data["row_count"] == 2
    ex = Execution.objects.get(id=resp.data["id"])
    assert ex.is_latest
    assert Path(ex.file_path).exists()


def test_run_marks_only_latest(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)
    monkeypatch.setattr(oracle_client, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    client = client_for(manager)
    e1 = client.post(f"/api/datasets/{ds.id}/run/").data["id"]
    e2 = client.post(f"/api/datasets/{ds.id}/run/").data["id"]
    assert Execution.objects.get(id=e1).is_latest is False
    assert Execution.objects.get(id=e2).is_latest is True


def test_run_failure_records_error(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)

    def boom(*a, **k):
        raise RuntimeError("ORA-00942 table not found")

    monkeypatch.setattr(oracle_client, "stream_query", boom)
    resp = client_for(manager).post(f"/api/datasets/{ds.id}/run/")
    assert resp.data["status"] == "failed"
    assert "ORA-00942" in resp.data["error_msg"]


def test_download(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)
    monkeypatch.setattr(oracle_client, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    client = client_for(manager)
    eid = client.post(f"/api/datasets/{ds.id}/run/").data["id"]
    resp = client.get(f"/api/executions/{eid}/download/")
    assert resp.status_code == 200
    assert "attachment" in resp["Content-Disposition"]


def test_non_manager_forbidden(db, datasource):
    user = User.objects.create_user("u", password="x")
    assert client_for(user).get("/api/datasets/").status_code == 403
