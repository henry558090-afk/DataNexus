"""用户管理 + 角色/部门成员/授权 API 单测。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Category, Department
from apps.dataset.models import Dataset
from apps.datasource.models import DataSource
from apps.permission.services import can_view_dataset

User = get_user_model()


@pytest.fixture
def superadmin(db):
    return User.objects.create_superuser("root", "r@x.com", "x")


@pytest.fixture
def assistant(db):
    return User.objects.create_user("asst", password="x", is_assistant_admin=True)


@pytest.fixture
def member(db):
    return User.objects.create_user("mem", password="x")


def cli(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_user_with_password(assistant):
    resp = cli(assistant).post(
        "/api/users/",
        {"username": "newbie", "password": "pw123456", "is_boss": True},
        format="json",
    )
    assert resp.status_code == 201
    user = User.objects.get(username="newbie")
    assert user.check_password("pw123456")
    assert user.is_boss


def test_cannot_set_superuser_via_api(assistant):
    resp = cli(assistant).post(
        "/api/users/",
        {"username": "x", "is_superuser": True, "password": "p"},
        format="json",
    )
    assert resp.status_code == 201
    assert User.objects.get(username="x").is_superuser is False


def test_assistant_cannot_see_superuser(assistant, superadmin):
    usernames = [u["username"] for u in cli(assistant).get("/api/users/").data]
    assert "root" not in usernames  # 辅助管理员看不到超管


def test_superuser_sees_all(superadmin, assistant):
    usernames = [u["username"] for u in cli(superadmin).get("/api/users/").data]
    assert "asst" in usernames
    assert "root" in usernames


def test_member_forbidden(member):
    assert cli(member).get("/api/users/").status_code == 403


def test_membership_and_grant_grants_visibility(assistant, member):
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.save()
    dep = Department.objects.create(name="财务部")
    cat = Category.objects.create(name="月报", department=dep)
    dataset = Dataset.objects.create(name="应收", datasource=ds, category=cat, sql_text="SELECT 1")

    client = cli(assistant)
    client.post(
        "/api/memberships/",
        {"user": member.id, "department": dep.id, "role": "member"},
        format="json",
    )
    assert can_view_dataset(member, dataset) is False  # 仅成员、未授权 → 不可见

    client.post("/api/grants/", {"subject_user": member.id, "category": cat.id}, format="json")
    assert can_view_dataset(member, dataset) is True  # 授权分类后可见
