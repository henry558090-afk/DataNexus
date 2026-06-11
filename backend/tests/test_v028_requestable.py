"""审批闭环：只露「可申请」目录，用户自助申请。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Folder, FolderShare
from apps.permission.models import AccessRequest

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user("viewer", password="x")


def cli(u) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def test_requestable_lists_only_marked_and_invisible(user):
    Folder.objects.create(name="公开月报", requestable=True)
    Folder.objects.create(name="财务密", requestable=False)  # 敏感，不开放
    granted = Folder.objects.create(name="我已有", requestable=True)
    FolderShare.objects.create(folder=granted, subject_user=user)  # 已可见，不该再出现
    data = cli(user).get("/api/portal/requestable-folders/").data
    names = [f["name"] for f in data]
    assert names == ["公开月报"]  # 只有可申请且我看不到的
    assert data[0]["pending"] is False


def test_request_marks_pending(user):
    f = Folder.objects.create(name="公开月报", requestable=True)
    c = cli(user)
    r = c.post("/api/portal/access-requests/", {"folder": f.id, "reason": "对账"}, format="json")
    assert r.status_code == 201
    data = c.get("/api/portal/requestable-folders/").data
    assert data[0]["pending"] is True  # 列表里标记已申请


def test_cannot_request_non_requestable_folder(user):
    secret = Folder.objects.create(name="财务密", requestable=False)
    r = cli(user).post("/api/portal/access-requests/", {"folder": secret.id}, format="json")
    assert r.status_code == 403  # 不开放申请


def test_approve_creates_share_and_clears_from_requestable(user, db):
    mgr = User.objects.create_user("mgr", password="x", is_assistant_admin=True)
    f = Folder.objects.create(name="公开月报", requestable=True)
    r = cli(user).post("/api/portal/access-requests/", {"folder": f.id}, format="json")
    ar_id = r.data["id"]
    cli(mgr).post(f"/api/access-requests/{ar_id}/approve/")
    # 通过后用户已可见 → 不再出现在可申请列表
    data = cli(user).get("/api/portal/requestable-folders/").data
    assert data == []
    assert AccessRequest.objects.get(id=ar_id).status == "approved"
