from __future__ import annotations

import math
from typing import Dict, Tuple


def poisson_tail_probability(lam: float, threshold: int) -> float:
    """计算泊松分布尾概率 P(X>=k)。"""
    if threshold <= 0:
        return 1.0
    if lam <= 0:
        return 0.0

    if lam >= 80:
        # 大 lambda 下使用正态近似，避免阶乘级累加带来的性能损耗。
        z_score = (threshold - 0.5 - lam) / math.sqrt(lam)
        return 0.5 * math.erfc(z_score / math.sqrt(2.0))

    term = math.exp(-lam)
    cumulative = term
    for index in range(1, threshold):
        term *= lam / index
        cumulative += term
    return min(max(1.0 - cumulative, 0.0), 1.0)


def recommend_threshold(lam: float, exceedance_target: float) -> Tuple[int, float]:
    """按目标超阈值概率反推最小阈值 k。"""
    threshold = max(1, int(math.floor(lam)))
    while poisson_tail_probability(lam, threshold) > exceedance_target:
        threshold += 1

    while threshold > 1 and poisson_tail_probability(lam, threshold - 1) <= exceedance_target:
        threshold -= 1

    return threshold, poisson_tail_probability(lam, threshold)


def calculate_poisson_metrics(
    daily_dialogs: int,
    avg_duration: float,
    daytime_ratio: float,
    active_seconds: float,
) -> Dict[str, float]:
    """计算泊松模型所需的核心指标。"""
    full_day_avg = daily_dialogs * avg_duration / 86400
    # 文档中的 λ，表示每秒平均请求数，也可理解为日间平均并发。
    lam = daily_dialogs * daytime_ratio * avg_duration / active_seconds

    return {
        "full_day_avg": full_day_avg,
        "lambda": lam,
    }
