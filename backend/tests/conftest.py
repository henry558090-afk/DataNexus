"""测试全局夹具。"""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _run_dataset_inline(settings):
    """测试内联执行数据集运行（同步），避免后台线程跨事务不可见 + 便于断言（S1）。"""
    settings.DATASET_RUN_INLINE = True


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个测试前清缓存，避免登录限流计数（SEC1）在测试间累积导致 429。"""
    cache.clear()
    yield
    cache.clear()
