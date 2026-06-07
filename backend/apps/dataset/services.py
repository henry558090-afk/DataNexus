"""数据集运行：连库跑 SQL → 生成 Excel → 在目标文件夹新增数据文件（带命名 + 保留清理）。"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.dataset.models import Dataset
from apps.execution.models import DataFile
from core import db, excel


def _conn_params(datasource) -> db.ConnParams:
    return db.ConnParams(
        db_type=datasource.db_type,
        host=datasource.host,
        port=datasource.port,
        service_name=datasource.service_name,
        user=datasource.username,
        password=datasource.password,
    )


def preview_dataset(dataset: Dataset, *, limit: int = 50) -> tuple[list[str], list[tuple]]:
    return db.preview_query(
        _conn_params(dataset.datasource),
        dataset.sql_text,
        limit=limit,
        timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
    )


def _apply_retention(dataset: Dataset) -> None:
    """按数据集的 keep_count / keep_days 清理旧文件（含磁盘文件）。"""
    qs = DataFile.objects.filter(dataset=dataset).order_by("-created_at")
    to_delete = []
    if dataset.keep_count and dataset.keep_count > 0:
        to_delete += list(qs[dataset.keep_count :])
    if dataset.keep_days and dataset.keep_days > 0:
        cutoff = timezone.now() - timedelta(days=dataset.keep_days)
        to_delete += list(qs.filter(created_at__lt=cutoff))
    for f in {x.id: x for x in to_delete}.values():
        if f.file_path:
            p = Path(f.file_path)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        f.delete()


def run_dataset(dataset: Dataset, user=None) -> DataFile:
    """运行数据集，在目标文件夹新增一个数据文件。无论成败返回 DataFile。"""
    now = timezone.localtime()
    datafile = DataFile.objects.create(
        folder=dataset.target_folder,
        name=dataset.build_filename(now),
        dataset=dataset,
        status=DataFile.Status.RUNNING,
        created_by=user,
    )
    try:
        columns, rows = db.stream_query(
            _conn_params(dataset.datasource),
            dataset.sql_text,
            max_rows=settings.QUERY_MAX_ROWS,
            fetch_size=settings.QUERY_FETCH_SIZE,
            timeout_seconds=settings.QUERY_TIMEOUT_SECONDS,
        )
        stamp = now.strftime("%Y%m%d_%H%M%S")
        out_dir = Path(settings.MEDIA_ROOT) / "exports" / str(dataset.id)
        out_path = out_dir / f"{stamp}_{datafile.id}.xlsx"  # 磁盘名唯一
        row_count = excel.export_to_xlsx(columns, rows, out_path)

        datafile.status = DataFile.Status.SUCCESS
        datafile.row_count = row_count
        datafile.file_path = str(out_path)
        datafile.file_size = out_path.stat().st_size
        datafile.save()
        _apply_retention(dataset)
    except Exception as exc:  # noqa: BLE001 - 失败落库，不抛 500
        datafile.status = DataFile.Status.FAILED
        datafile.error_msg = str(exc)
        datafile.save()
    return datafile
