"""文件夹 CRUD（含防环）+ 授权 + 用户端门户（树/文件/搜索/下载鉴权）单测。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Department, Folder, FolderShare
from apps.execution.models import DataFile
from apps.permission.models import DepartmentMembership

User = get_user_model()


@pytest.fixture
def manager(db):
    return User.objects.create_user("mgr", password="x", is_assistant_admin=True)


@pytest.fixture
def member(db):
    return User.objects.create_user("mem", password="x")


def cli(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ---- 文件夹管理 ----


def test_folder_crud_and_move(manager):
    c = cli(manager)
    a = c.post("/api/folders/", {"name": "财务"}, format="json").data
    b = c.post("/api/folders/", {"name": "月报", "parent": a["id"]}, format="json").data
    assert b["parent"] == a["id"]
    # 重命名
    assert (
        c.patch(f"/api/folders/{b['id']}/", {"name": "月度报表"}, format="json").status_code == 200
    )
    # 移动到根
    assert c.patch(f"/api/folders/{b['id']}/", {"parent": None}, format="json").status_code == 200


def test_folder_move_cycle_rejected(manager):
    c = cli(manager)
    a = c.post("/api/folders/", {"name": "A"}, format="json").data
    b = c.post("/api/folders/", {"name": "B", "parent": a["id"]}, format="json").data
    # 把 A 移到 B 下（B 是 A 的子）→ 应拒绝
    assert (
        c.patch(f"/api/folders/{a['id']}/", {"parent": b["id"]}, format="json").status_code == 400
    )


def test_folder_forbidden_for_member(member):
    assert cli(member).get("/api/folders/").status_code == 403


def test_folder_share_requires_one_subject(manager):
    c = cli(manager)
    fid = c.post("/api/folders/", {"name": "F"}, format="json").data["id"]
    # 既不给部门也不给个人 → 400
    assert c.post("/api/folder-shares/", {"folder": fid}, format="json").status_code == 400


# ---- 门户 ----


@pytest.fixture
def tree(db):
    root = Folder.objects.create(name="财务报表")
    sub = Folder.objects.create(name="月报", parent=root)
    f = DataFile.objects.create(folder=sub, name="应收_20260607.xlsx", status="success")
    return root, sub, f


def test_portal_tree_member_empty_then_shared(manager, member, tree):
    root, sub, f = tree
    assert cli(member).get("/api/portal/tree/").data == []  # 默认拒绝
    dep = Department.objects.create(name="财务部")
    DepartmentMembership.objects.create(user=member, department=dep)
    FolderShare.objects.create(folder=root, subject_department=dep)
    data = cli(member).get("/api/portal/tree/").data
    assert data[0]["name"] == "财务报表"
    assert data[0]["children"][0]["name"] == "月报"  # 递归含子文件夹


def test_portal_folder_files_and_download(manager, member, tree):
    root, sub, f = tree
    FolderShare.objects.create(folder=root, subject_user=member)
    files = cli(member).get(f"/api/portal/folders/{sub.id}/files/").data
    assert files[0]["name"] == "应收_20260607.xlsx"
    # 无权限用户下载 → 403；有权限 → 走可见性（文件无真实文件 → 404 但已过鉴权）
    assert (
        cli(User.objects.create_user("x", password="x"))
        .get(f"/api/portal/files/{f.id}/download/")
        .status_code
        == 403
    )


def test_portal_search(manager, member, tree):
    root, sub, f = tree
    FolderShare.objects.create(folder=root, subject_user=member)
    assert len(cli(member).get("/api/portal/search/?q=应收").data) == 1
    assert cli(member).get("/api/portal/search/?q=不存在").data == []
