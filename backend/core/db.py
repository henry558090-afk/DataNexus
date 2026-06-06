"""统一数据库取数客户端：支持 Oracle 与 MySQL（只读）。

安全护栏不变（开发规范第 6 节）：sql_guard 只读校验 + 流式 fetch + 行数上限 + 超时。
两种库均遵循 DB-API 2.0，执行/取数逻辑通用，仅连接方式不同；MySQL 流式用 SSCursor。
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from core.sql_guard import validate_readonly_sql

ORACLE = "oracle"
MYSQL = "mysql"


class QueryRowLimitExceeded(RuntimeError):
    """结果行数超过上限。"""


@dataclass(frozen=True)
class ConnParams:
    """数据库连接参数。service_name 对 Oracle 为服务名，对 MySQL 为库名。"""

    db_type: str
    host: str
    port: int
    service_name: str
    user: str
    password: str


def _connect(params: ConnParams, timeout_seconds: int):
    if params.db_type == MYSQL:
        import pymysql

        return pymysql.connect(
            host=params.host,
            port=params.port,
            user=params.user,
            password=params.password,
            database=params.service_name or None,
            connect_timeout=timeout_seconds,
            read_timeout=timeout_seconds,
        )
    import oracledb

    dsn = oracledb.makedsn(params.host, params.port, service_name=params.service_name)
    conn = oracledb.connect(
        user=params.user,
        password=params.password,
        dsn=dsn,
        tcp_connect_timeout=timeout_seconds,
    )
    conn.call_timeout = timeout_seconds * 1000  # 查询级超时（毫秒）
    return conn


def test_connection(params: ConnParams, timeout_seconds: int = 10) -> None:
    """测试连接，失败抛异常。"""
    conn = _connect(params, timeout_seconds)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM dual" if params.db_type == ORACLE else "SELECT 1")
        cursor.fetchone()
    finally:
        conn.close()


def preview_query(
    params: ConnParams,
    sql: str,
    binds: Mapping[str, object] | None = None,
    *,
    limit: int = 50,
    timeout_seconds: int = 30,
) -> tuple[list[str], list[tuple]]:
    """预览：只取前 ``limit`` 行，连接用完即关。"""
    safe_sql = validate_readonly_sql(sql)
    conn = _connect(params, timeout_seconds)
    try:
        cursor = conn.cursor()
        cursor.execute(safe_sql, dict(binds or {}))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(limit)
        return columns, list(rows)
    finally:
        conn.close()


def stream_query(
    params: ConnParams,
    sql: str,
    binds: Mapping[str, object] | None = None,
    *,
    max_rows: int = 100_000,
    fetch_size: int = 1_000,
    timeout_seconds: int = 60,
) -> tuple[list[str], Iterator[tuple]]:
    """流式执行：返回 (列名, 行生成器)。生成器须在连接关闭前消费完。"""
    gen = _execute_stream(
        params,
        sql,
        binds,
        max_rows=max_rows,
        fetch_size=fetch_size,
        timeout_seconds=timeout_seconds,
    )
    try:
        first_cols, first_batch = next(gen)
    except StopIteration:
        return [], iter(())

    def _rows() -> Iterator[tuple]:
        yield from first_batch
        for _cols, batch in gen:
            yield from batch

    return first_cols, _rows()


def _execute_stream(
    params: ConnParams,
    sql: str,
    binds: Mapping[str, object] | None,
    *,
    max_rows: int,
    fetch_size: int,
    timeout_seconds: int,
) -> Iterator[tuple[list[str], list[tuple]]]:
    """连接 -> 校验 -> 执行 -> 分批 yield (列名, 一批行)，强制行数上限。"""
    safe_sql = validate_readonly_sql(sql)
    bind_values = dict(binds or {})
    conn = _connect(params, timeout_seconds)
    try:
        if params.db_type == MYSQL:
            import pymysql.cursors

            cursor = conn.cursor(pymysql.cursors.SSCursor)  # 服务端游标，真正流式
        else:
            cursor = conn.cursor()
            cursor.arraysize = fetch_size

        cursor.execute(safe_sql, bind_values)  # 绑定变量，防注入
        columns = [desc[0] for desc in cursor.description]

        fetched = 0
        first = True
        while True:
            batch = cursor.fetchmany(fetch_size)
            if not batch:
                if first:
                    yield columns, []  # 0 行也交付列名，保证 Excel 表头
                break
            first = False
            fetched += len(batch)
            if fetched > max_rows:
                raise QueryRowLimitExceeded(
                    f"结果行数超过上限 {max_rows}，请缩小查询范围或调整上限。"
                )
            yield columns, batch
    finally:
        conn.close()
