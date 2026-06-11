"""数据集运行：连库跑 SQL → 生成 Excel → 在目标文件夹新增数据文件（带命名 + 保留清理）。"""

from __future__ import annotations

import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import OperationalError
from django.utils import timezone

from apps.dataset.models import Dataset
from apps.execution.models import DataFile
from core import db, excel


def _retry_locked(fn, *, attempts: int = 5, base_delay: float = 0.2):
    """对 SQLite "database is locked" 做指数退避重试（S2）。

    web + 调度双进程并发写元数据库时，偶发锁等待超时；重试可消化瞬时争用。
    非锁错误或重试用尽则原样抛出。其他数据库（MySQL）不会触发此分支。
    """
    for i in range(attempts):
        try:
            return fn()
        except OperationalError as exc:
            if "locked" not in str(exc).lower() or i == attempts - 1:
                raise
            time.sleep(base_delay * (2**i))


def _conn_params(datasource) -> db.ConnParams:
    return db.ConnParams(
        db_type=datasource.db_type,
        host=datasource.host,
        port=datasource.port,
        service_name=datasource.service_name,
        user=datasource.username,
        password=datasource.password,
    )


def resolve_params(dataset: Dataset, provided: dict | None = None) -> dict:
    """合并数据集参数定义的默认值与本次提供的值（v0.26）。

    只接受**已定义**的参数名（防注入额外绑定变量）；缺省用定义里的 default。
    dataset.params 形如 [{"name": "dt", "label": "日期", "default": "2026-01-01"}, ...]。
    """
    provided = provided or {}
    resolved: dict = {}
    for spec in dataset.params or []:
        name = spec.get("name")
        if not name:
            continue
        resolved[name] = provided.get(name, spec.get("default"))
    return resolved


def preview_dataset(
    dataset: Dataset, *, params: dict | None = None, limit: int = 50
) -> tuple[list[str], list[tuple]]:
    return db.preview_query(
        _conn_params(dataset.datasource),
        dataset.sql_text,
        binds=resolve_params(dataset, params),
        limit=limit,
        timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
    )


def _apply_retention(dataset: Dataset) -> None:
    """按数据集的 keep_count / keep_days 清理旧文件（含磁盘文件）。

    只对**成功**文件计数与按天清理，失败/运行中的文件不占用保留名额、
    也不会因为几次失败把成功的好文件挤掉（见 v0.22 M1）。
    """
    success = DataFile.objects.filter(
        dataset=dataset, status=DataFile.Status.SUCCESS
    ).order_by("-created_at")
    to_delete = []
    if dataset.keep_count and dataset.keep_count > 0:
        to_delete += list(success[dataset.keep_count :])
    if dataset.keep_days and dataset.keep_days > 0:
        cutoff = timezone.now() - timedelta(days=dataset.keep_days)
        to_delete += list(success.filter(created_at__lt=cutoff))
    for f in {x.id: x for x in to_delete}.values():
        if f.file_path:
            p = Path(f.file_path)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        f.delete()


def reap_stuck_running(timeout_seconds: int | None = None) -> int:
    """把卡死的"运行中"文件标记为失败（进程崩溃/重启会留下僵尸 RUNNING）。

    超过 ``timeout_seconds``（默认取 settings.STUCK_RUNNING_SECONDS）仍处于
    RUNNING 的文件视为已死。返回标记数量。由调度进程周期性调用，也可在启动时调用。
    """
    if timeout_seconds is None:
        timeout_seconds = getattr(settings, "STUCK_RUNNING_SECONDS", 1800)
    cutoff = timezone.now() - timedelta(seconds=timeout_seconds)
    stuck = DataFile.objects.filter(
        status=DataFile.Status.RUNNING, created_at__lt=cutoff
    )
    return stuck.update(
        status=DataFile.Status.FAILED,
        error_msg="运行超时或进程中断，已自动标记为失败（v0.22 清道夫）。",
    )


def _create_running_file(dataset: Dataset, user=None) -> DataFile:
    """先建一条"运行中"记录，拿到 id（磁盘文件名要用）。"""
    now = timezone.localtime()
    return _retry_locked(
        lambda: DataFile.objects.create(
            folder=dataset.target_folder,
            name=dataset.build_filename(now),
            dataset=dataset,
            status=DataFile.Status.RUNNING,
            created_by=user,
        )
    )


def _execute_run(dataset: Dataset, datafile: DataFile, params: dict | None = None) -> None:
    """执行体：连库跑数 → 写 Excel → 回填结果 → 保留清理。无论成败落库，不抛。"""
    started = time.monotonic()
    try:
        columns, rows = db.stream_query(
            _conn_params(dataset.datasource),
            dataset.sql_text,
            binds=resolve_params(dataset, params),
            max_rows=settings.QUERY_MAX_ROWS,
            fetch_size=settings.QUERY_FETCH_SIZE,
            timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
        )
        stamp = datafile.created_at.astimezone(timezone.get_current_timezone()).strftime(
            "%Y%m%d_%H%M%S"
        )
        out_dir = Path(settings.MEDIA_ROOT) / "exports" / str(dataset.id)
        out_path = out_dir / f"{stamp}_{datafile.id}.xlsx"  # 磁盘名唯一
        row_count = excel.export_to_xlsx(columns, rows, out_path)

        datafile.status = DataFile.Status.SUCCESS
        datafile.row_count = row_count
        datafile.file_path = str(out_path)
        datafile.file_size = out_path.stat().st_size
        datafile.duration_ms = int((time.monotonic() - started) * 1000)
        _retry_locked(datafile.save)
        _apply_retention(dataset)
    except Exception as exc:  # noqa: BLE001 - 失败落库，不抛 500
        datafile.status = DataFile.Status.FAILED
        datafile.error_msg = str(exc)
        datafile.duration_ms = int((time.monotonic() - started) * 1000)
        _retry_locked(datafile.save)

    # 推送（v0.25）：仅成功时，放在 try 外，自身吞异常，绝不影响主运行结果
    if datafile.status == DataFile.Status.SUCCESS:
        from apps.dataset.notify import notify_subscribers

        try:
            notify_subscribers(dataset, datafile)
        except Exception:  # noqa: BLE001
            pass


def run_dataset(dataset: Dataset, user=None, params: dict | None = None) -> DataFile:
    """同步运行数据集（调度进程用）：建记录 → 执行 → 返回最终 DataFile。"""
    datafile = _create_running_file(dataset, user)
    _execute_run(dataset, datafile, params)
    return datafile


_run_pool = None


def _run_executor():
    """有界线程池（B2 修复）：限制并发运行数，避免批量运行打满线程/业务库连接。

    超出并发上限的运行会排队，而不是无限起线程。容量由 DATASET_RUN_CONCURRENCY 控制。
    """
    global _run_pool
    if _run_pool is None:
        from concurrent.futures import ThreadPoolExecutor

        workers = getattr(settings, "DATASET_RUN_CONCURRENCY", 4)
        _run_pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dsrun")
    return _run_pool


def start_dataset_run(dataset: Dataset, user=None, params: dict | None = None) -> DataFile:
    """异步运行（Web 接口用，S1）：立刻返回"运行中"记录，后台线程池执行实际跑数。

    避免长查询/写 Excel 阻塞 gunicorn worker。前端按 DataFile.status 轮询结果。
    用**有界线程池**（B2）防止批量运行起爆线程；线程内独立持有 DB 连接，结束时关闭。
    """
    from django.db import connections

    datafile = _create_running_file(dataset, user)

    # 测试或显式配置下内联执行，便于断言、避免线程跨事务可见性问题
    if getattr(settings, "DATASET_RUN_INLINE", False):
        _execute_run(dataset, datafile, params)
        datafile.refresh_from_db()
        return datafile

    def _worker():
        try:
            _execute_run(dataset, datafile, params)
        finally:
            connections.close_all()  # 关闭本线程的 DB 连接

    _run_executor().submit(_worker)
    return datafile
