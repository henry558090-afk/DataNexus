"""数据集运行：连 Oracle 跑 SQL → 生成 Excel → 写执行记录。"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.dataset.models import Dataset
from apps.execution.models import Execution
from core import excel, oracle_client


def preview_dataset(dataset: Dataset, *, limit: int = 50) -> tuple[list[str], list[tuple]]:
    """预览数据集 SQL 的前 N 行（不落文件）。"""
    ds = dataset.datasource
    params = oracle_client.OracleConnParams(
        host=ds.host,
        port=ds.port,
        service_name=ds.service_name,
        user=ds.username,
        password=ds.password,
    )
    return oracle_client.preview_query(
        params,
        dataset.sql_text,
        limit=limit,
        timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
    )


def run_dataset(dataset: Dataset, user=None) -> Execution:
    """运行数据集，生成 Excel 并记录。无论成败都返回 Execution（失败含 error_msg）。"""
    execution = Execution.objects.create(
        dataset=dataset,
        status=Execution.Status.RUNNING,
        triggered_by=user,
    )
    try:
        ds = dataset.datasource
        params = oracle_client.OracleConnParams(
            host=ds.host,
            port=ds.port,
            service_name=ds.service_name,
            user=ds.username,
            password=ds.password,
        )
        columns, rows = oracle_client.stream_query(
            params,
            dataset.sql_text,
            max_rows=settings.QUERY_MAX_ROWS,
            fetch_size=settings.QUERY_FETCH_SIZE,
            timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
        )

        ts = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(settings.MEDIA_ROOT) / "exports" / str(dataset.id)
        out_path = out_dir / f"{dataset.name}_{ts}.xlsx"
        row_count = excel.export_to_xlsx(columns, rows, out_path)

        # 切换最新版本标记
        Execution.objects.filter(dataset=dataset, is_latest=True).update(is_latest=False)
        execution.status = Execution.Status.SUCCESS
        execution.row_count = row_count
        execution.file_path = str(out_path)
        execution.file_size = out_path.stat().st_size
        execution.is_latest = True
        execution.ended_at = timezone.now()
        execution.save()
    except Exception as exc:  # noqa: BLE001 - 失败信息落库，不抛 500
        execution.status = Execution.Status.FAILED
        execution.error_msg = str(exc)
        execution.ended_at = timezone.now()
        execution.save()
    return execution
