"""可见性判定单元测试（权限核心，覆盖各角色）。"""

from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.catalog.models import Category, Department
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from apps.permission.models import DepartmentMembership, Grant
from apps.permission.services import can_view_dataset

User = get_user_model()


def make_user(username: str, **flags) -> "User":
    return User.objects.create_user(username=username, password="x", **flags)


@pytest.fixture
def world(db):
    """两个部门、各一分类一数据集，共享一个数据源。"""
    ds = DataSource.objects.create(
        name="oracle1", host="h", port=1521, service_name="s", username="u", password_encrypted=""
    )
    fin = Department.objects.create(name="财务部")
    sales = Department.objects.create(name="销售部")
    fin_cat = Category.objects.create(name="月度报表", department=fin)
    sales_cat = Category.objects.create(name="业绩", department=sales)
    fin_ds = Dataset.objects.create(
        name="应收明细", category=fin_cat, datasource=ds, sql_text="SELECT 1"
    )
    sales_ds = Dataset.objects.create(
        name="销售汇总", category=sales_cat, datasource=ds, sql_text="SELECT 1"
    )
    return SimpleNamespace(fin=fin, sales=sales, fin_cat=fin_cat, fin_ds=fin_ds, sales_ds=sales_ds)


# ---- 全局可见角色 ----


def test_superuser_sees_all(world):
    u = User.objects.create_superuser("root", "r@x.com", "x")
    assert can_view_dataset(u, world.fin_ds)
    assert can_view_dataset(u, world.sales_ds)


def test_assistant_admin_sees_all(world):
    u = make_user("aa", is_assistant_admin=True)
    assert can_view_dataset(u, world.fin_ds)
    assert can_view_dataset(u, world.sales_ds)


def test_boss_sees_all(world):
    u = make_user("boss", is_boss=True)
    assert can_view_dataset(u, world.fin_ds)


# ---- 部门内角色 ----


def test_director_sees_dept_only(world):
    u = make_user("dir")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="director")
    assert can_view_dataset(u, world.fin_ds)
    assert not can_view_dataset(u, world.sales_ds)


def test_manager_sees_dept(world):
    u = make_user("mgr")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="manager")
    assert can_view_dataset(u, world.fin_ds)
    assert not can_view_dataset(u, world.sales_ds)


def test_member_default_denied(world):
    u = make_user("m")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="member")
    assert not can_view_dataset(u, world.fin_ds)


def test_member_see_all_in_dept(world):
    u = make_user("m2")
    DepartmentMembership.objects.create(
        user=u, department=world.fin, role="member", see_all_in_dept=True
    )
    assert can_view_dataset(u, world.fin_ds)
    assert not can_view_dataset(u, world.sales_ds)


# ---- 成员授权 ----


def test_member_individual_grant_dataset(world):
    u = make_user("m3")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="member")
    Grant.objects.create(subject_user=u, dataset=world.fin_ds)
    assert can_view_dataset(u, world.fin_ds)


def test_member_individual_grant_category(world):
    u = make_user("m4")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="member")
    Grant.objects.create(subject_user=u, category=world.fin_cat)
    assert can_view_dataset(u, world.fin_ds)


def test_member_role_group_grant(world):
    u = make_user("m5")
    DepartmentMembership.objects.create(user=u, department=world.fin, role="member")
    Grant.objects.create(
        subject_department=world.fin, subject_role="member", category=world.fin_cat
    )
    assert can_view_dataset(u, world.fin_ds)


def test_unauthenticated_denied(world):
    assert not can_view_dataset(AnonymousUser(), world.fin_ds)
