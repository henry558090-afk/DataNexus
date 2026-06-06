"""目录(部门/分类) CRUD + 用户端门户(可见性过滤树/下载鉴权) 单测。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Category, Department
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from apps.execution.models import Execution
from apps.permission.models import DepartmentMembership, Grant

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="x", is_assistant_admin=True)


@pytest.fixture
def member(db):
    return User.objects.create_user("mem", password="x")


def cli(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def filed_dataset(db):
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.save()
    dep = Department.objects.create(name="财务部")
    cat = Category.objects.create(name="月报", department=dep)
    return Dataset.objects.create(name="应收", datasource=ds, category=cat, sql_text="SELECT 1")


# ---- 目录 CRUD ----


def test_department_crud_manager(manager):
    client = cli(manager)
    assert client.post("/api/departments/", {"name": "财务部"}, format="json").status_code == 201
    assert client.get("/api/departments/").status_code == 200


def test_category_filter_by_department(manager):
    client = cli(manager)
    dep = client.post("/api/departments/", {"name": "销售部"}, format="json").data
    client.post("/api/categories/", {"name": "月报", "department": dep["id"]}, format="json")
    resp = client.get(f"/api/categories/?department={dep['id']}")
    assert len(resp.data) == 1


def test_catalog_forbidden_for_member(member):
    assert cli(member).get("/api/departments/").status_code == 403


# ---- 用户端门户 ----


def test_portal_tree_admin_sees(manager, filed_dataset):
    resp = cli(manager).get("/api/portal/tree/")
    assert resp.status_code == 200
    assert resp.data[0]["name"] == "财务部"
    assert resp.data[0]["categories"][0]["datasets"][0]["name"] == "应收"


def test_portal_tree_member_empty_by_default(member, filed_dataset):
    assert cli(member).get("/api/portal/tree/").data == []


def test_portal_tree_member_with_grant(member, filed_dataset):
    DepartmentMembership.objects.create(
        user=member, department=filed_dataset.category.department, role="member"
    )
    Grant.objects.create(subject_user=member, dataset=filed_dataset)
    assert len(cli(member).get("/api/portal/tree/").data) == 1


def test_portal_download_visibility(member, manager, filed_dataset, tmp_path):
    f = tmp_path / "x.xlsx"
    f.write_bytes(b"PK\x03\x04test")
    ex = Execution.objects.create(
        dataset=filed_dataset, status="success", file_path=str(f), is_latest=True
    )
    assert cli(member).get(f"/api/portal/executions/{ex.id}/download/").status_code == 403
    assert cli(manager).get(f"/api/portal/executions/{ex.id}/download/").status_code == 200
