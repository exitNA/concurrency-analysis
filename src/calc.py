from __future__ import annotations

import math
from typing import Dict


def poisson_quantile(mu: float, p: float) -> int:
    """求满足 P(X ≤ q) ≥ p 的最小整数 q（泊松分布分位数）。

    参数:
        mu: 泊松分布参数（窗口平均请求数）。
        p:  目标分位，例如 0.99 表示 P99。

    返回:
        满足条件的最小整数 q。
    """
    if mu <= 0:
        return 0
    if p <= 0:
        return 0
    if p >= 1:
        raise ValueError("目标分位 p 必须严格小于 1")

    if mu >= 80:
        # 大 mu 下使用正态近似求初始值，再微调。
        z = _normal_ppf(p)
        q = max(0, int(math.ceil(mu + z * math.sqrt(mu) - 0.5)))
    else:
        q = max(0, int(math.floor(mu)))

    # 向上搜索：确保 CDF(q) >= p
    while _poisson_cdf(mu, q) < p:
        q += 1

    # 向下搜索：确保 q 是满足条件的最小值
    while q > 0 and _poisson_cdf(mu, q - 1) >= p:
        q -= 1

    return q


def _poisson_cdf(mu: float, k: int) -> float:
    """计算泊松分布 CDF: P(X ≤ k)。"""
    if k < 0:
        return 0.0
    if mu <= 0:
        return 1.0

    if mu >= 80:
        z_score = (k + 0.5 - mu) / math.sqrt(mu)
        return 0.5 * (1 + math.erf(z_score / math.sqrt(2.0)))

    term = math.exp(-mu)
    cumulative = term
    for i in range(1, k + 1):
        term *= mu / i
        cumulative += term
    return min(cumulative, 1.0)


def _normal_ppf(p: float) -> float:
    """标准正态分布分位数的近似（Abramowitz & Stegun 26.2.23）。"""
    if p <= 0 or p >= 1:
        raise ValueError("p 必须在 (0, 1) 之间")
    if p == 0.5:
        return 0.0

    if p < 0.5:
        return -_normal_ppf(1 - p)

    # Rational approximation for upper half
    t = math.sqrt(-2 * math.log(1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)


def estimate_peak_qps(
    daily_requests: int,
    active_ratio: float,
    active_seconds: float,
    window_seconds: float,
    percentile: float,
) -> Dict[str, float]:
    """基于文档方法计算高分位等效 QPS。

    计算链路:
        R_d × R_act / H_act → QPS_avg
        QPS_avg × Δt → μ
        Poisson(μ) → q_{p,Δt}
        q_{p,Δt} / Δt → QPS_{p,Δt}

    参数:
        daily_requests:  日请求量 R_d
        active_ratio:    活跃时段流量占比 R_act
        active_seconds:  活跃时段时长 H_act（秒）
        window_seconds:  统计窗口 Δt（秒）
        percentile:      目标分位 p

    返回:
        包含 qps_avg, mu, q_p, qps_peak 的字典。
    """
    # 第二步：活跃时段平均到达率
    qps_avg = daily_requests * active_ratio / active_seconds

    # 第三步：窗口平均请求数
    mu = qps_avg * window_seconds

    # 第五步：高分位请求数
    q_p = poisson_quantile(mu, percentile)

    # 第六步：高分位等效 QPS
    qps_peak = q_p / window_seconds

    return {
        "qps_avg": qps_avg,
        "mu": mu,
        "q_p": float(q_p),
        "qps_peak": qps_peak,
    }
