"""文件夹可见性判定单测（递归 + 部门/个人授权，默认拒绝）。"""

from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.catalog.models import Department, Folder, FolderShare
from apps.execution.models import DataFile
from apps.permission.models import DepartmentMembership
from apps.permission.services import can_view_file, can_view_folder, visible_folders

User = get_user_model()


def mk(username: str, **flags):
    return User.objects.create_user(username, password="x", **flags)


@pytest.fixture
def world(db):
    fin = Department.objects.create(name="财务部")
    root = Folder.objects.create(name="财务报表")
    sub = Folder.objects.create(name="月报", parent=root)
    f = DataFile.objects.create(folder=sub, name="应收_20260607.xlsx", status="success")
    other = Folder.objects.create(name="销售")
    of = DataFile.objects.create(folder=other, name="销售.xlsx", status="success")
    return SimpleNamespace(fin=fin, root=root, sub=sub, f=f, other=other, of=of)


def test_superuser_sees_all(world):
    u = User.objects.create_superuser("root", "r@x.com", "x")
    assert can_view_file(u, world.f) and can_view_file(u, world.of)


def test_boss_sees_all(world):
    assert can_view_file(mk("boss", is_boss=True), world.f)


def test_default_deny(world):
    assert can_view_file(mk("m0"), world.f) is False


def test_share_to_department_recursive(world):
    u = mk("m1")
    DepartmentMembership.objects.create(user=u, department=world.fin)
    FolderShare.objects.create(folder=world.root, subject_department=world.fin)
    assert can_view_file(u, world.f) is True  # 子文件夹里的文件也可见（递归）
    assert can_view_folder(u, world.sub) is True
    assert can_view_file(u, world.of) is False  # 未授权的文件夹不可见


def test_share_to_person(world):
    u = mk("m2")
    FolderShare.objects.create(folder=world.sub, subject_user=u)
    assert can_view_file(u, world.f) is True


def test_visible_folders_includes_descendants(world):
    u = mk("m3")
    DepartmentMembership.objects.create(user=u, department=world.fin)
    FolderShare.objects.create(folder=world.root, subject_department=world.fin)
    ids = set(visible_folders(u).values_list("id", flat=True))
    assert world.root.id in ids and world.sub.id in ids
    assert world.other.id not in ids


def test_unauthenticated_denied(world):
    assert can_view_file(AnonymousUser(), world.f) is False
