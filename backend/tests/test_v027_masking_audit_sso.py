"""v0.27 列级脱敏 + 审计可视化 + 企业微信 SSO。"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts import views as account_views
from apps.audit.models import AuditLog
from apps.catalog.models import Folder, FolderShare
from apps.dataset.masking import mask_rows
from apps.dataset.models import Dataset, MaskingRule
from apps.datasource.models import DataSource
from apps.execution.models import DataFile
from core import excel

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


# ---------- 脱敏工具 ----------
def test_mask_rows_partial_and_full():
    cols = ["name", "phone"]
    rows = [["张三", "13800001111"]]
    out = mask_rows(cols, rows, {"phone": "partial"})
    assert out[0][0] == "张三"  # 未配置的列不动
    assert out[0][1].startswith("1") and out[0][1].endswith("1") and "*" in out[0][1]
    out2 = mask_rows(cols, rows, {"phone": "full"})
    assert set(out2[0][1]) == {"*"}


# ---------- 门户脱敏（普通用户脱敏，管理员看原值）----------
def _shared_file_with_masking(datasource, user, tmp_path):
    folder = Folder.objects.create(name="客户")
    FolderShare.objects.create(folder=folder, subject_user=user)
    ds = Dataset.objects.create(
        name="客户表", datasource=datasource, sql_text="SELECT 1", target_folder=folder
    )
    MaskingRule.objects.create(dataset=ds, column="手机", strategy="full")
    path = tmp_path / "c.xlsx"
    excel.export_to_xlsx(["姓名", "手机"], [["李四", "13900002222"]], path)
    f = DataFile.objects.create(
        dataset=ds,
        folder=folder,
        name="c.xlsx",
        status=DataFile.Status.SUCCESS,
        file_path=str(path),
    )
    return ds, f


def test_portal_preview_masks_for_regular_user(datasource, tmp_path, db):
    user = User.objects.create_user("viewer", password="x")
    _, f = _shared_file_with_masking(datasource, user, tmp_path)
    r = cli(user).get(f"/api/portal/files/{f.id}/preview/")
    assert r.data["columns"] == ["姓名", "手机"]
    assert r.data["rows"][0][0] == "李四"
    assert set(r.data["rows"][0][1]) == {"*"}  # 手机被遮蔽


def test_portal_preview_raw_for_manager(datasource, tmp_path, manager):
    # 管理员把文件夹也授权给自己以便走门户；管理员看原值
    _, f = _shared_file_with_masking(datasource, manager, tmp_path)
    r = cli(manager).get(f"/api/portal/files/{f.id}/preview/")
    assert r.data["rows"][0][1] == "13900002222"  # 未脱敏


def test_masking_rule_crud_manager_only(datasource, manager, db):
    folder = Folder.objects.create(name="f")
    ds = Dataset.objects.create(
        name="d", datasource=datasource, sql_text="SELECT 1", target_folder=folder
    )
    r = cli(manager).post(
        "/api/masking-rules/",
        {"dataset": ds.id, "column": "手机", "strategy": "full"},
        format="json",
    )
    assert r.status_code == 201
    u = User.objects.create_user("u", password="x")
    assert cli(u).get("/api/masking-rules/").status_code == 403


# ---------- 审计可视化 ----------
def test_audit_stats(manager, db):
    AuditLog.objects.create(username="a", action="login")
    AuditLog.objects.create(username="a", action="download")
    AuditLog.objects.create(username="b", action="download")
    r = cli(manager).get("/api/audit-logs/stats/?days=30")
    assert r.status_code == 200
    assert r.data["total"] == 3
    actions = {x["action"]: x["count"] for x in r.data["by_action"]}
    assert actions["download"] == 2
    top = {x["username"]: x["count"] for x in r.data["top_users"]}
    assert top["a"] == 2


# ---------- 企业微信 SSO ----------
def test_wecom_disabled_returns_400(db, settings):
    settings.WECOM_ENABLED = False
    assert APIClient().get("/api/auth/wecom/login/").status_code == 400


def test_wecom_callback_maps_user_and_issues_token(db, settings, monkeypatch):
    settings.WECOM_ENABLED = True
    settings.WECOM_CORP_ID = "corp"
    settings.WECOM_SECRET = "secret"
    settings.WECOM_AUTO_PROVISION = True
    settings.WECOM_REDIRECT_FRONTEND = "/"
    monkeypatch.setattr(account_views, "User", User)
    from apps.accounts import wecom

    monkeypatch.setattr(wecom, "exchange_code_for_userid", lambda code: "zhangsan")
    r = APIClient().get("/api/auth/wecom/callback/?code=abc")
    assert r.status_code == 302
    # B5：回调用一次性短码跳转，token 不进 URL
    assert "wecom_code=" in r["Location"] and "token=" not in r["Location"]
    assert User.objects.filter(username="zhangsan").exists()
