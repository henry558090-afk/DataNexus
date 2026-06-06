"""调度 trigger 构造单测（纯逻辑，无需 DB/真实调度器）。"""

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.scheduler import build_trigger


def test_cron_trigger():
    assert isinstance(build_trigger("0 8 * * *", None), CronTrigger)


def test_interval_trigger():
    assert isinstance(build_trigger("", 30), IntervalTrigger)


def test_cron_takes_priority():
    assert isinstance(build_trigger("0 8 * * *", 30), CronTrigger)


def test_none_when_unset():
    assert build_trigger("", None) is None
    assert build_trigger("", 0) is None


def test_invalid_cron_returns_none():
    assert build_trigger("not a cron", None) is None
