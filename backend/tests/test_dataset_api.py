"""数据集（SQL任务）+ 数据文件 API 单测：SQL校验、运行新增文件、命名、保留、下载、权限。"""

from pathlib import Path

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


def make_dataset(datasource, **kw) -> Dataset:
    folder = Folder.objects.create(name="月报")
    return Dataset.objects.create(
        name="应收明细",
        datasource=datasource,
        sql_text="SELECT 1 FROM dual",
        target_folder=folder,
        **kw,
    )


def test_create_rejects_non_select(manager, datasource):
    r = cli(manager).post(
        "/api/datasets/",
        {"name": "d", "datasource": datasource.id, "sql_text": "DELETE FROM t"},
        format="json",
    )
    assert r.status_code == 400


def test_create_ok_sets_owner(manager, datasource):
    r = cli(manager).post(
        "/api/datasets/",
        {"name": "d", "datasource": datasource.id, "sql_text": "SELECT 1 FROM dual"},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["owner"] == manager.id


def test_run_creates_named_file_in_folder(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource, file_prefix="应收明细", date_format="%Y%m%d")
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a", "b"], iter([(1, 2)])))
    r = cli(manager).post(f"/api/datasets/{ds.id}/run/")
    assert r.data["status"] == "success"
    assert r.data["row_count"] == 1
    f = DataFile.objects.get(id=r.data["id"])
    assert f.folder_id == ds.target_folder_id
    assert f.name.startswith("应收明细_") and f.name.endswith(".xlsx")
    assert Path(f.file_path).exists()


def test_run_failure_records_error(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)

    def boom(*a, **k):
        raise RuntimeError("ORA-00942")

    monkeypatch.setattr(db, "stream_query", boom)
    r = cli(manager).post(f"/api/datasets/{ds.id}/run/")
    assert r.data["status"] == "failed" and "ORA-00942" in r.data["error_msg"]


def test_retention_keep_count(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource, keep_count=2)
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    c = cli(manager)
    for _ in range(4):
        c.post(f"/api/datasets/{ds.id}/run/")
    assert DataFile.objects.filter(dataset=ds).count() == 2


def test_datafile_download(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = make_dataset(datasource)
    monkeypatch.setattr(db, "stream_query", lambda *a, **k: (["a"], iter([(1,)])))
    fid = cli(manager).post(f"/api/datasets/{ds.id}/run/").data["id"]
    r = cli(manager).get(f"/api/datafiles/{fid}/download/")
    assert r.status_code == 200 and "attachment" in r["Content-Disposition"]


def test_non_manager_forbidden(db, datasource):
    u = User.objects.create_user("u", password="x")
    assert cli(u).get("/api/datasets/").status_code == 403
