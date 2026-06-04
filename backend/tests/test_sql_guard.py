"""sql_guard 只读校验单元测试（安全核心，必须覆盖）。"""

import pytest

from core.sql_guard import SqlNotAllowed, validate_readonly_sql

# ---- 合法：应通过 ----


def test_simple_select_ok():
    assert validate_readonly_sql("SELECT * FROM orders").lower().startswith("select")


def test_with_cte_ok():
    sql = "WITH t AS (SELECT id FROM orders) SELECT * FROM t"
    assert validate_readonly_sql(sql)


def test_trailing_semicolon_stripped():
    assert validate_readonly_sql("SELECT 1 FROM dual;") == "SELECT 1 FROM dual"


def test_identifier_containing_keyword_ok():
    # update_time 含 'update' 子串，但全词匹配不应误判
    assert validate_readonly_sql("SELECT update_time, created_at FROM orders")


def test_string_literal_containing_keyword_ok():
    # 字面量里的 'delete' 不应触发关键字校验
    assert validate_readonly_sql("SELECT id FROM orders WHERE status = 'deleted'")


def test_bind_variable_ok():
    assert validate_readonly_sql("SELECT * FROM orders WHERE dept = :dept")


# ---- 非法：应拒绝 ----


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE orders SET amount = 0",
        "DELETE FROM orders",
        "INSERT INTO orders VALUES (1)",
        "DROP TABLE orders",
        "TRUNCATE TABLE orders",
        "ALTER TABLE orders ADD c INT",
        "CREATE TABLE t (id INT)",
        "GRANT SELECT ON orders TO x",
        "BEGIN NULL; END;",
        "SELECT * FROM orders FOR UPDATE",
        "SELECT id INTO v FROM orders",
        "SELECT dbms_lock.sleep(10) FROM dual",
    ],
)
def test_write_or_dangerous_rejected(sql):
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql(sql)


def test_multiple_statements_rejected():
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql("SELECT 1 FROM dual; DROP TABLE orders")


def test_comment_hidden_injection_rejected():
    # 注释被剥离后暴露出 DROP，应拒绝
    sql = "SELECT 1 FROM dual /* harmless */ ; DROP TABLE orders"
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql(sql)


def test_empty_rejected():
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql("   ")


def test_non_select_rejected():
    with pytest.raises(SqlNotAllowed):
        validate_readonly_sql("EXPLAIN PLAN FOR SELECT 1 FROM dual")
