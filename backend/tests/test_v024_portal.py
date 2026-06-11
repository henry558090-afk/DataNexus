"""v0.24 用户门户：在线预览 / 选列下载 / 搜索增强 / 收藏 / 最近下载 / 更新通知。"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Favorite, Folder, FolderShare
from apps.execution.models import DataFile
from core import excel

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user("viewer", password="x")


@pytest.fixture
def folder(db):
    return Folder.objects.create(name="月报")


def cli(u) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _grant(user, folder):
    FolderShare.objects.create(folder=folder, subject_user=user)


def _file_with_xlsx(folder, tmp_path, name="f.xlsx", cols=("姓名", "金额"), rows=((1, 2),)):
    path = tmp_path / name
    excel.export_to_xlsx(list(cols), [list(r) for r in rows], path)
    return DataFile.objects.create(
        folder=folder, name=name, status=DataFile.Status.SUCCESS, file_path=str(path)
    )


def test_preview_requires_visibility(user, folder, tmp_path):
    f = _file_with_xlsx(folder, tmp_path)
    # 未授权 → 403
    assert cli(user).get(f"/api/portal/files/{f.id}/preview/").status_code == 403
    _grant(user, folder)
    r = cli(user).get(f"/api/portal/files/{f.id}/preview/")
    assert r.status_code == 200
    assert r.data["columns"] == ["姓名", "金额"]
    assert len(r.data["rows"]) == 1


def test_column_select_download(user, folder, tmp_path):
    f = _file_with_xlsx(folder, tmp_path, cols=("a", "b", "c"), rows=((1, 2, 3),))
    _grant(user, folder)
    r = cli(user).get(f"/api/portal/files/{f.id}/download/?columns=a,c")
    assert r.status_code == 200 and "attachment" in r["Content-Disposition"]


def test_search_date_range(user, folder, tmp_path):
    _grant(user, folder)
    old = _file_with_xlsx(folder, tmp_path, name="old.xlsx")
    DataFile.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(days=10))
    _file_with_xlsx(folder, tmp_path, name="new.xlsx")
    today = timezone.localdate().isoformat()
    r = cli(user).get(f"/api/portal/search/?from={today}")
    names = [x["name"] for x in r.data]
    assert "new.xlsx" in names and "old.xlsx" not in names


def test_favorite_toggle(user, folder):
    _grant(user, folder)
    c = cli(user)
    r1 = c.post(f"/api/portal/folders/{folder.id}/favorite/")
    assert r1.data["favorited"] is True
    assert Favorite.objects.filter(user=user, folder=folder).exists()
    r2 = c.post(f"/api/portal/folders/{folder.id}/favorite/")
    assert r2.data["favorited"] is False
    favs = c.get("/api/portal/favorites/").data
    assert favs == []


def test_favorite_requires_visibility(user, folder):
    assert cli(user).post(f"/api/portal/folders/{folder.id}/favorite/").status_code == 403


def test_recent_downloads(user, folder, tmp_path):
    _grant(user, folder)
    f = _file_with_xlsx(folder, tmp_path)
    c = cli(user)
    c.get(f"/api/portal/files/{f.id}/download/")  # 产生一条下载审计
    r = c.get("/api/portal/recent-downloads/")
    assert len(r.data) == 1 and r.data[0]["target"] == f.name


def test_updates_since(user, folder, tmp_path):
    _grant(user, folder)
    old = _file_with_xlsx(folder, tmp_path, name="old.xlsx")
    DataFile.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(hours=2))
    since = (timezone.now() - timedelta(hours=1)).isoformat()
    _file_with_xlsx(folder, tmp_path, name="new.xlsx")
    r = cli(user).get("/api/portal/updates/", {"since": since})  # data 字典正确编码 +
    assert r.data["count"] == 1
    assert r.data["files"][0]["name"] == "new.xlsx"
