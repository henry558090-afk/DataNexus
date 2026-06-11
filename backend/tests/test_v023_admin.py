"""v0.23 管理员效率：批量运行 / 批量改保留 / 运行健康看板。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Folder
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from apps.execution.models import DataFile
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


def cli(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _dataset(datasource, name="d", **kw):
    folder = Folder.objects.create(name=f"f-{name}")
    return Dataset.objects.create(
        name=name, datasource=datasource, sql_text="SELECT 1", target_folder=folder, **kw
    )


def test_batch_run(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    d1, d2 = _dataset(datasource, "a"), _dataset(datasource, "b")
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["x"], iter([(1,)])))
    r = cli(manager).post("/api/datasets/batch-run/", {"ids": [d1.id, d2.id]}, format="json")
    assert r.status_code == 200
    assert r.data["count"] == 2
    assert DataFile.objects.filter(status=DataFile.Status.SUCCESS).count() == 2


def test_batch_retention(manager, datasource):
    d1, d2 = _dataset(datasource, "a"), _dataset(datasource, "b")
    r = cli(manager).post(
        "/api/datasets/batch-retention/",
        {"ids": [d1.id, d2.id], "keep_count": 5, "keep_days": 30},
        format="json",
    )
    assert r.status_code == 200 and r.data["updated"] == 2
    d1.refresh_from_db()
    assert d1.keep_count == 5 and d1.keep_days == 30


def test_batch_retention_requires_field(manager, datasource):
    d1 = _dataset(datasource, "a")
    r = cli(manager).post("/api/datasets/batch-retention/", {"ids": [d1.id]}, format="json")
    assert r.status_code == 400


def test_run_health(manager, datasource):
    ds = _dataset(datasource, "a")
    folder = ds.target_folder
    DataFile.objects.create(
        dataset=ds, folder=folder, name="ok", status=DataFile.Status.SUCCESS, duration_ms=200
    )
    DataFile.objects.create(
        dataset=ds, folder=folder, name="ok2", status=DataFile.Status.SUCCESS, duration_ms=400
    )
    DataFile.objects.create(
        dataset=ds, folder=folder, name="bad", status=DataFile.Status.FAILED, error_msg="ORA-1"
    )
    r = cli(manager).get("/api/datasets/run-health/?days=7")
    assert r.status_code == 200
    assert r.data["total"] == 3 and r.data["success"] == 2 and r.data["failed"] == 1
    assert r.data["success_rate"] == round(2 / 3, 4)
    assert r.data["avg_duration_ms"] == 300
    assert len(r.data["recent_failures"]) == 1
    assert r.data["slowest_datasets"][0]["dataset__name"] == "a"


def test_batch_endpoints_forbidden_for_non_manager(db, datasource):
    u = User.objects.create_user("u", password="x")
    assert cli(u).post("/api/datasets/batch-run/", {"ids": []}, format="json").status_code == 403
    assert cli(u).get("/api/datasets/run-health/").status_code == 403
