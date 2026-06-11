"""SQL 安全校验：只允许单条只读 SELECT 查询。

这是安全的**第二道防线**（第一道是 Oracle 只读账号）。开发规范第 6 节要求 day 1 落地。

策略：
    去注释 -> 去字符串字面量 -> 校验单语句 -> 必须 SELECT/WITH 开头 -> 禁止写操作关键字。

说明：
    - 关键字采用全词匹配（``\\b``）。Python 正则中 ``_`` 属于单词字符，
      因此 ``update_time`` 这类标识符不会误判为 ``update``。
    - 为减少误杀，校验前会先剥离字符串字面量（如 ``WHERE name = 'delete'`` 不触发）。
    - 宁可误拒合法 SQL，也不放过危险 SQL —— 安全优先于便利。
"""

from __future__ import annotations

import re

# 禁止的关键字（写操作 / DDL / 事务 / PLSQL）
_FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "merge",
    "drop",
    "create",
    "alter",
    "truncate",
    "rename",
    "grant",
    "revoke",
    "begin",
    "declare",
    "call",
    "exec",
    "execute",
    "commit",
    "rollback",
    "savepoint",
    "into",  # SELECT ... INTO 属 PL/SQL 写语义
)


class SqlNotAllowed(ValueError):
    """SQL 未通过只读安全校验。"""


def _strip_comments(sql: str) -> str:
    """去除块注释 ``/* */``、行注释 ``--`` 与 MySQL 的 ``#`` 行注释。"""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"#[^\n]*", " ", sql)  # MySQL 井号行注释
    return sql


def _strip_string_literals(sql: str) -> str:
    """把字符串字面量替换为空串，避免字面量里的词触发关键字校验。

    覆盖：单引号串（含 ``''`` 转义与 ``\\'`` 反斜杠转义）、双引号串（MySQL 字符串 /
    带引号标识符）。只用于关键字/结构探测，真正执行用的是原始 SQL，所以这里
    多剥离一些只会更安全（更倾向误拒，符合本模块"安全优先"策略）。
    """
    sql = re.sub(r"'(?:[^'\\]|''|\\.)*'", "''", sql)
    sql = re.sub(r'"(?:[^"\\]|""|\\.)*"', '""', sql)
    return sql


def validate_readonly_sql(sql: str) -> str:
    """校验并返回规整后的只读 SQL；不合法则抛 :class:`SqlNotAllowed`。

    返回值为去掉注释、去掉结尾分号后的 SQL 主体，可直接交给数据库执行。
    """
    if not sql or not sql.strip():
        raise SqlNotAllowed("SQL 不能为空")

    cleaned = _strip_comments(sql)
    body = cleaned.strip().rstrip(";").strip()
    if not body:
        raise SqlNotAllowed("SQL 不能为空")

    # 用“去字符串”后的文本做结构与关键字判断
    probe = _strip_string_literals(body)

    # 单语句：去掉唯一结尾分号后不应再出现分号
    if ";" in probe:
        raise SqlNotAllowed("只允许执行单条 SQL 语句")

    lowered = probe.lower()

    # 必须以 SELECT 或 WITH(CTE) 开头
    if not re.match(r"^\s*(select|with)\b", lowered):
        raise SqlNotAllowed("只允许 SELECT 查询")

    # 禁止写操作关键字
    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise SqlNotAllowed(f"禁止使用关键字：{keyword.upper()}")

    # 禁止 FOR UPDATE 加锁
    if re.search(r"\bfor\s+update\b", lowered):
        raise SqlNotAllowed("禁止 FOR UPDATE 加锁查询")

    # 禁止调用 Oracle 系统包 / 模式
    if re.search(r"\b(dbms_|utl_|sys\.)", lowered):
        raise SqlNotAllowed("禁止调用 Oracle 系统包")

    return body
