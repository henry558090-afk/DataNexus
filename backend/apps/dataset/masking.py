"""列级脱敏（v0.27）：对指定列的值做遮蔽。管理员/属主看原值，普通用户看脱敏值。"""

from __future__ import annotations


def _mask_value(value, strategy: str) -> str:
    if value is None:
        return ""
    s = str(value)
    if strategy == "full" or len(s) <= 2:
        return "*" * max(len(s), 4)
    if strategy == "partial":
        return s[0] + "*" * (len(s) - 2) + s[-1]
    return "*" * len(s)


def mask_rows(columns: list[str], rows, rules: dict[str, str]):
    """对 rows 中、列名命中 rules 的单元格脱敏。

    :param rules: {列名: 策略}。返回脱敏后的新行列表。
    """
    if not rules:
        return list(rows)
    idx_strategy = {
        i: rules[col] for i, col in enumerate(columns) if col in rules
    }
    if not idx_strategy:
        return list(rows)
    out = []
    for row in rows:
        new = list(row)
        for i, strategy in idx_strategy.items():
            if i < len(new):
                new[i] = _mask_value(new[i], strategy)
        out.append(new)
    return out


def rules_for(dataset) -> dict[str, str]:
    """取数据集的脱敏规则 {列名: 策略}。"""
    from apps.dataset.models import MaskingRule

    return {
        r.column: r.strategy
        for r in MaskingRule.objects.filter(dataset=dataset)
    }
