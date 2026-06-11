"""v0.22 生产硬伤修复的回归测试。

覆盖：保留只算成功(M1)、僵尸清道夫(M2)、Excel公式注入(M4)、SQL校验补盲(M5)、
登录限流(SEC1)、Token过期+登出失效(SEC2)、文件夹祖先链(M3)。
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.catalog.models import Folder, FolderShare
from apps.dataset.models import Dataset
from apps.dataset.services import _apply_retention, reap_stuck_running
from apps.datasource.models import DataSource
from apps.execution.models import DataFile
from apps.permission.services import can_view_folder
from core import excel
from core.sql_guard import SqlNotAllowed, validate_readonly_sql

User = get_user_model()


@pytest.fixture
def datasource(db):
    ds = DataSource(name="o", host="h", port=1521, service_name="s", username="u")
    ds.password = "p"
    ds.save()
    return ds


def _login(client, username, password="pw123456"):
    r = client.post(
        "/api/auth/token/", {"username": username, "password": password}, format="json"
    )
    return r.data["token"]


def _make_file(dataset, status, *, age_seconds=0):
    f = DataFile.objects.create(
        dataset=dataset, folder=dataset.target_folder, name="f", status=status
    )
    if age_seconds:
        DataFile.objects.filter(id=f.id).update(
            created_at=timezone.now() - timedelta(seconds=age_seconds)
        )
    return f


# ---------- M1 保留只算成功文件 ----------
def test_retention_counts_only_success(datasource):
    folder = Folder.objects.create(name="月报")
    ds = Dataset.objects.create(
        name="d", datasource=datasource, sql_text="SELECT 1", target_folder=folder, keep_count=2
    )
    # 3 个成功 + 2 个失败：失败不应占用名额、也不应把成功挤掉
    for i in range(3):
        _make_file(ds, DataFile.Status.SUCCESS, age_seconds=100 - i)
    _make_file(ds, DataFile.Status.FAILED)
    _make_file(ds, DataFile.Status.FAILED)
    _apply_retention(ds)
    assert DataFile.objects.filter(dataset=ds, status=DataFile.Status.SUCCESS).count() == 2
    # 失败文件不被保留逻辑删除
    assert DataFile.objects.filter(dataset=ds, status=DataFile.Status.FAILED).count() == 2


# ---------- M2 僵尸"运行中"清道夫 ----------
def test_reaper_marks_stuck_running_failed(datasource):
    folder = Folder.objects.create(name="x")
    ds = Dataset.objects.create(
        name="d", datasource=datasource, sql_text="SELECT 1", target_folder=folder
    )
    fresh = _make_file(ds, DataFile.Status.RUNNING)  # 刚开始的，不该被清
    stale = _make_file(ds, DataFile.Status.RUNNING, age_seconds=4000)  # 卡死的
    n = reap_stuck_running(timeout_seconds=1800)
    assert n == 1
    fresh.refresh_from_db()
    stale.refresh_from_db()
    assert fresh.status == DataFile.Status.RUNNING
    assert stale.status == DataFile.Status.FAILED


# ---------- M4 Excel 公式注入 ----------
@pytest.mark.parametrize(
    "raw,expected",
    [("=1+1", "'=1+1"), ("+x", "'+x"), ("-2", "'-2"), ("@cmd", "'@cmd"), ("正常", "正常")],
)
def test_excel_sanitize(raw, expected):
    assert excel._sanitize(raw) == expected


def test_excel_sanitize_non_string_passthrough():
    assert excel._sanitize(5) == 5
    assert excel._sanitize(None) is None


def test_export_escapes_formula(tmp_path):
    p = tmp_path / "o.xlsx"
    excel.export_to_xlsx(["c"], [["=SUM(A1:A9)"]], p)
    wb = load_workbook(p)
    assert wb.active["A2"].value == "'=SUM(A1:A9)"


# ---------- M5 SQL 校验补盲 ----------
def test_sql_guard_strips_hash_comment(datasource):
    # MySQL # 行注释里的 delete 不应触发拦截
    assert validate_readonly_sql("SELECT 1 FROM dual # delete everything").startswith("SELECT")


def test_sql_guard_strips_double_quoted_identifier():
    # 双引号标识符里的 drop 不该误杀
    assert validate_readonly_sql('SELECT 1 AS "drop" FROM t').startswith("SELECT")


def test_sql_guard_still_blocks_real_write():
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql("DELETE FROM t")
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql("SELECT 1; DROP TABLE t")


# ---------- SEC1 登录限流 ----------
def test_login_throttled(db, settings):
    User.objects.create_user("bob", password="pw123456")
    c = APIClient()
    payload = {"username": "bob", "password": "pw123456"}
    codes = [
        c.post("/api/auth/token/", payload, format="json").status_code for _ in range(15)
    ]
    assert 429 in codes  # 默认 10/min，第 11 次起被限流


# ---------- SEC2 Token 过期 + 登出失效 ----------
def test_expired_token_rejected(db, settings):
    settings.TOKEN_TTL_SECONDS = 3600
    user = User.objects.create_user("amy", password="pw123456")
    token = Token.objects.create(user=user)
    Token.objects.filter(key=token.key).update(created=timezone.now() - timedelta(hours=2))
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    assert c.get("/api/auth/me/").status_code == 401


def test_logout_invalidates_token(db):
    User.objects.create_user("cara", password="pw123456")
    c = APIClient()
    token = _login(c, "cara")
    c.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    assert c.get("/api/auth/me/").status_code == 200
    assert c.post("/api/auth/logout/").status_code == 204
    assert c.get("/api/auth/me/").status_code == 401  # 同一 token 已失效


def test_login_rotates_token(db):
    User.objects.create_user("dan", password="pw123456")
    c = APIClient()
    t1 = _login(c, "dan")
    t2 = _login(c, "dan")
    assert t1 != t2  # 轮换：新登录换新 token
    # 旧 token 失效
    c.credentials(HTTP_AUTHORIZATION=f"Token {t1}")
    assert c.get("/api/auth/me/").status_code == 401


# ---------- M3 文件夹祖先链 ----------
def test_ancestor_ids_walks_full_chain(db):
    root = Folder.objects.create(name="root")
    child = Folder.objects.create(name="child", parent=root)
    grand = Folder.objects.create(name="grand", parent=child)
    assert grand.ancestor_ids() == [grand.id, child.id, root.id]


def test_share_on_ancestor_grants_descendant(db):
    root = Folder.objects.create(name="root")
    child = Folder.objects.create(name="child", parent=root)
    grand = Folder.objects.create(name="grand", parent=child)
    user = User.objects.create_user("eve", password="x")
    FolderShare.objects.create(folder=root, subject_user=user)
    assert can_view_folder(user, grand) is True
