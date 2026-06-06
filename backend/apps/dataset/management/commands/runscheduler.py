"""启动定时调度进程：python manage.py runscheduler

须仅在单个进程内运行（见技术方案 §10.1）。每 30 秒 reconcile 一次，
自动同步数据集的定时配置（cron / interval）。
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "启动定时调度（按数据集 cron/interval 自动运行）"

    def handle(self, *args, **options):
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        from core import scheduler as sched_core

        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_job(
            lambda: sched_core.reconcile(scheduler),
            IntervalTrigger(seconds=30),
            id="__reconcile__",
            max_instances=1,
            coalesce=True,
        )
        sched_core.reconcile(scheduler)  # 启动即同步一次
        self.stdout.write(
            self.style.SUCCESS("定时调度已启动（每 30s 同步一次配置）。Ctrl+C 退出。")
        )
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
