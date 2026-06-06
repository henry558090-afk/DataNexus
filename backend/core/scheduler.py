"""定时调度：根据数据集的 cron / interval 自动运行（进程内 APScheduler）。

须在**单个进程**内运行（见技术方案 §10.1）：用 `python manage.py runscheduler`。
reconcile 周期性把"数据集的定时配置"与"调度器里的任务"对齐——增删改都自动生效，无需重启。
"""

from __future__ import annotations


def build_trigger(cron: str, interval_minutes: int | None):
    """根据配置构造 APScheduler 触发器；都没配则返回 None（手动）。

    cron 优先；其次 interval_minutes。非法配置返回 None。
    """
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    if cron:
        try:
            return CronTrigger.from_crontab(cron)
        except ValueError:
            return None
    if interval_minutes and interval_minutes > 0:
        return IntervalTrigger(minutes=interval_minutes)
    return None


def _signature(cron: str, interval_minutes: int | None) -> str:
    return f"{cron}|{interval_minutes}"


def _run_job(dataset_id: int) -> None:
    """调度触发的任务：跑一次数据集。"""
    from apps.dataset.models import Dataset
    from apps.dataset.services import run_dataset

    ds = Dataset.objects.filter(id=dataset_id, is_active=True).first()
    if ds is not None:
        run_dataset(ds, user=None)


# 记录每个任务当前的配置签名，用于检测"定时改了"
_signatures: dict[str, str] = {}


def reconcile(scheduler) -> None:
    """把调度器任务与活跃数据集的定时配置对齐（增/删/改）。"""
    from apps.dataset.models import Dataset

    desired: dict[str, tuple] = {}
    for ds in Dataset.objects.filter(is_active=True):
        trigger = build_trigger(ds.cron, ds.interval_minutes)
        if trigger is not None:
            desired[str(ds.id)] = (trigger, _signature(ds.cron, ds.interval_minutes))

    existing = {j.id for j in scheduler.get_jobs() if j.id != "__reconcile__"}

    # 新增或配置变更
    for job_id, (trigger, sig) in desired.items():
        if job_id not in existing or _signatures.get(job_id) != sig:
            scheduler.add_job(
                _run_job,
                trigger,
                args=[int(job_id)],
                id=job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            _signatures[job_id] = sig

    # 删除已不该存在的
    for job_id in existing - desired.keys():
        scheduler.remove_job(job_id)
        _signatures.pop(job_id, None)
