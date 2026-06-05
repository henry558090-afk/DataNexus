"""Oracle 取数客户端（python-oracledb thin 模式，免装 Oracle 客户端）。

安全护栏（开发规范第 6 节，缺一不可）：
    1. 执行前用 sql_guard 校验只读单语句；
    2. 一切动态值走绑定变量（binds），严禁字符串拼接；
    3. fetchmany 流式读取 + 行数上限 + 查询超时，防 OOM 与拖垮源库。

所有取数都应走本模块，错一次就全局安全。
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

import oracledb

from core.sql_guard import validate_readonly_sql


class QueryRowLimitExceeded(RuntimeError):
    """结果行数超过上限。"""


@dataclass(frozen=True)
class OracleConnParams:
    """Oracle 连接参数。"""

    host: str
    port: int
    service_name: str
    user: str
    password: str


def _build_dsn(params: OracleConnParams) -> str:
    return oracledb.makedsn(params.host, params.port, service_name=params.service_name)


def test_connection(params: OracleConnParams, timeout_seconds: int = 10) -> None:
    """测试连接，失败抛异常；成功返回 None。"""
    conn = oracledb.connect(
        user=params.user,
        password=params.password,
        dsn=_build_dsn(params),
        tcp_connect_timeout=timeout_seconds,
    )
    try:
        conn.ping()
    finally:
        conn.close()


def run_query(
    params: OracleConnParams,
    sql: str,
    binds: Mapping[str, object] | None = None,
    *,
    max_rows: int = 100_000,
    fetch_size: int = 1_000,
    timeout_seconds: int = 60,
) -> tuple[list[str], list[tuple]]:
    """执行只读查询，返回 (列名, 数据行)。

    内部流式抓取并强制行数上限：超过 ``max_rows`` 抛 :class:`QueryRowLimitExceeded`。
    适合中小结果集；超大导出请用 :func:`stream_query` 直连 Excel 写入。
    """
    columns: list[str] = []
    rows: list[tuple] = []
    for col_names, batch in _execute_stream(
        params,
        sql,
        binds,
        max_rows=max_rows,
        fetch_size=fetch_size,
        timeout_seconds=timeout_seconds,
    ):
        if not columns:
            columns = col_names
        rows.extend(batch)
    return columns, rows


def stream_query(
    params: OracleConnParams,
    sql: str,
    binds: Mapping[str, object] | None = None,
    *,
    max_rows: int = 100_000,
    fetch_size: int = 1_000,
    timeout_seconds: int = 60,
) -> tuple[list[str], Iterator[tuple]]:
    """流式执行：返回 (列名, 行生成器)。

    行生成器须在连接关闭前消费完（如直接喂给 Excel 写入器）。
    """
    gen = _execute_stream(
        params,
        sql,
        binds,
        max_rows=max_rows,
        fetch_size=fetch_size,
        timeout_seconds=timeout_seconds,
    )
    # 先取第一批以拿到列名
    try:
        first_cols, first_batch = next(gen)
    except StopIteration:
        return [], iter(())

    def _rows() -> Iterator[tuple]:
        yield from first_batch
        for _cols, batch in gen:
            yield from batch

    return first_cols, _rows()


def preview_query(
    params: OracleConnParams,
    sql: str,
    binds: Mapping[str, object] | None = None,
    *,
    limit: int = 50,
    timeout_seconds: int = 30,
) -> tuple[list[str], list[tuple]]:
    """预览：只取前 ``limit`` 行（不报行数超限），连接用完即关。"""
    safe_sql = validate_readonly_sql(sql)
    conn = oracledb.connect(
        user=params.user,
        password=params.password,
        dsn=_build_dsn(params),
        tcp_connect_timeout=timeout_seconds,
    )
    try:
        conn.call_timeout = timeout_seconds * 1000
        cursor = conn.cursor()
        cursor.arraysize = limit
        cursor.execute(safe_sql, dict(binds or {}))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(limit)
        return columns, rows
    finally:
        conn.close()


def _execute_stream(
    params: OracleConnParams,
    sql: str,
    binds: Mapping[str, object] | None,
    *,
    max_rows: int,
    fetch_size: int,
    timeout_seconds: int,
) -> Iterator[tuple[list[str], list[tuple]]]:
    """连接 -> 校验 -> 执行 -> 分批 yield (列名, 一批行)，并强制行数上限。"""
    safe_sql = validate_readonly_sql(sql)
    bind_values = dict(binds or {})

    conn = oracledb.connect(
        user=params.user,
        password=params.password,
        dsn=_build_dsn(params),
        tcp_connect_timeout=timeout_seconds,
    )
    try:
        # 查询级超时（毫秒）
        conn.call_timeout = timeout_seconds * 1000
        cursor = conn.cursor()
        cursor.arraysize = fetch_size
        cursor.execute(safe_sql, bind_values)  # 绑定变量，防注入
        columns = [desc[0] for desc in cursor.description]

        fetched = 0
        while True:
            batch = cursor.fetchmany(fetch_size)
            if not batch:
                break
            fetched += len(batch)
            if fetched > max_rows:
                raise QueryRowLimitExceeded(
                    f"结果行数超过上限 {max_rows}，请缩小查询范围或调整上限。"
                )
            yield columns, batch
    finally:
        conn.close()
