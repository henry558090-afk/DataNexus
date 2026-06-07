"""用户管理 + 部门成员 API 单测（无角色细分；端到端授权走文件夹分享）。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Department, Folder, FolderShare
from apps.execution.models import DataFile
from apps.permission.services import can_view_file

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
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def test_create_user_with_password(assistant):
    r = cli(assistant).post(
        "/api/users/",
        {"username": "newbie", "password": "pw123456", "is_boss": True},
        format="json",
    )
    assert r.status_code == 201
    u = User.objects.get(username="newbie")
    assert u.check_password("pw123456") and u.is_boss


def test_cannot_set_superuser_via_api(assistant):
    r = cli(assistant).post(
        "/api/users/", {"username": "x", "is_superuser": True, "password": "p"}, format="json"
    )
    assert r.status_code == 201
    assert User.objects.get(username="x").is_superuser is False


def test_assistant_cannot_see_superuser(assistant, superadmin):
    names = [u["username"] for u in cli(assistant).get("/api/users/").data]
    assert "root" not in names


def test_member_forbidden(member):
    assert cli(member).get("/api/users/").status_code == 403


def test_membership_and_folder_share_grants_visibility(assistant, member):
    dep = Department.objects.create(name="财务部")
    folder = Folder.objects.create(name="财务报表")
    f = DataFile.objects.create(folder=folder, name="应收.xlsx", status="success")
    c = cli(assistant)
    c.post("/api/memberships/", {"user": member.id, "department": dep.id}, format="json")
    assert can_view_file(member, f) is False  # 还没分享文件夹
    FolderShare.objects.create(folder=folder, subject_department=dep)
    assert can_view_file(member, f) is True  # 分享后可见
