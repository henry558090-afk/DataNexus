"""v0.26 参数化查询 + 图表数据。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Folder
from apps.dataset.models import Dataset
from apps.dataset.services import resolve_params, run_dataset
from apps.datasource.models import DataSource
from apps.execution.models import DataFile
from core import db, excel

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


def _dataset(datasource, **kw):
    folder = Folder.objects.create(name="月报")
    return Dataset.objects.create(
        name="d", datasource=datasource, sql_text="SELECT 1", target_folder=folder, **kw
    )


# ---------- 参数解析 ----------
def test_resolve_params_merges_defaults(datasource):
    ds = _dataset(datasource, params=[{"name": "dt", "default": "2026-01-01"}, {"name": "dept"}])
    out = resolve_params(ds, {"dept": "销售"})
    assert out == {"dt": "2026-01-01", "dept": "销售"}


def test_resolve_params_ignores_undefined(datasource):
    ds = _dataset(datasource, params=[{"name": "dt"}])
    out = resolve_params(ds, {"dt": "x", "evil": "DROP"})
    assert out == {"dt": "x"}  # 未定义的参数被丢弃


def test_run_passes_binds(manager, datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = _dataset(datasource, params=[{"name": "dt", "default": "2026-06-01"}])
    captured = {}

    def fake_stream(params, sql, binds=None, **kw):
        captured["binds"] = binds
        return ["x"], iter([(1,)])

    monkeypatch.setattr(db, "stream_query", fake_stream)
    cli(manager).post(
        f"/api/datasets/{ds.id}/run/", {"params": {"dt": "2026-06-30"}}, format="json"
    )
    assert captured["binds"] == {"dt": "2026-06-30"}


def test_scheduled_run_uses_param_default(datasource, monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    ds = _dataset(datasource, params=[{"name": "dt", "default": "2026-06-01"}])
    captured = {}

    def fake_stream(params, sql, binds=None, **kw):
        captured["binds"] = binds
        return ["x"], iter([(1,)])

    monkeypatch.setattr(db, "stream_query", fake_stream)
    run_dataset(ds)  # 无 params → 用默认
    assert captured["binds"] == {"dt": "2026-06-01"}


# ---------- 图表数据 ----------
def _file_with_data(dataset, tmp_path, cols, rows):
    path = tmp_path / "chart.xlsx"
    excel.export_to_xlsx(list(cols), [list(r) for r in rows], path)
    return DataFile.objects.create(
        dataset=dataset,
        folder=dataset.target_folder,
        name="chart.xlsx",
        status=DataFile.Status.SUCCESS,
        file_path=str(path),
    )


def test_chart_data_sum(manager, datasource, tmp_path):
    ds = _dataset(datasource)
    _file_with_data(ds, tmp_path, ("部门", "金额"), [("销售", 10), ("销售", 5), ("财务", 20)])
    r = cli(manager).get(f"/api/datasets/{ds.id}/chart-data/?x=部门&y=金额&agg=sum")
    assert r.status_code == 200
    data = dict(zip(r.data["labels"], r.data["values"], strict=False))
    assert data == {"销售": 15, "财务": 20}


def test_chart_data_count(manager, datasource, tmp_path):
    ds = _dataset(datasource)
    _file_with_data(ds, tmp_path, ("部门", "金额"), [("销售", 10), ("销售", 5), ("财务", 20)])
    r = cli(manager).get(f"/api/datasets/{ds.id}/chart-data/?x=部门&agg=count")
    data = dict(zip(r.data["labels"], r.data["values"], strict=False))
    assert data == {"销售": 2, "财务": 1}


def test_chart_data_avg(manager, datasource, tmp_path):
    ds = _dataset(datasource)
    _file_with_data(ds, tmp_path, ("部门", "金额"), [("销售", 10), ("销售", 20)])
    r = cli(manager).get(f"/api/datasets/{ds.id}/chart-data/?x=部门&y=金额&agg=avg")
    assert dict(zip(r.data["labels"], r.data["values"], strict=False)) == {"销售": 15.0}


def test_chart_data_no_file(manager, datasource):
    ds = _dataset(datasource)
    assert cli(manager).get(f"/api/datasets/{ds.id}/chart-data/?x=部门").status_code == 404
