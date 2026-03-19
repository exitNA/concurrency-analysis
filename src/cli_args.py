from __future__ import annotations

import re

import typer


def format_decimal(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def format_percent(ratio: float) -> str:
    return f"{ratio * 100:.1f}%"


def parse_ratio(value: float | str, label: str) -> float:
    """把比例参数统一转换为 0~1 之间的小数。"""
    numeric = float(value)
    if numeric <= 0:
        raise ValueError(f"{label} 必须大于 0")
    if numeric <= 1:
        return numeric
    if numeric <= 100:
        return numeric / 100
    raise ValueError(f"{label} 必须是 0~1 或 0~100 之间的数值")


def parse_percentiles(values: list[str] | tuple[float, ...]) -> tuple[float, ...]:
    """解析目标分位列表，例如 0.99 或 99。"""
    parsed = []
    for value in values:
        ratio = parse_ratio(value, "目标分位")
        if ratio >= 1:
            raise ValueError("目标分位必须小于 100%")
        parsed.append(ratio)
    return tuple(sorted(set(parsed)))


def parse_duration_to_seconds(value: str | None) -> float | None:
    """解析时长字符串，格式为 NUM+UNIT，例如 3h20m43s。"""
    if value is None:
        return None

    normalized = value.strip().lower().replace(" ", "")
    if not normalized:
        return None

    matches = list(re.finditer(r"(\d+)([hms])", normalized))
    if not matches:
        raise typer.BadParameter(
            "活跃时段时长必须使用 NUM+UNIT 格式，例如 3h、19m、4s 或 3h20m43s。"
        )

    consumed = "".join(match.group(0) for match in matches)
    if consumed != normalized:
        raise typer.BadParameter(
            "活跃时段时长必须使用 NUM+UNIT 格式，例如 3h、19m、4s 或 3h20m43s。"
        )

    unit_seconds = {"h": 3600, "m": 60, "s": 1}
    total_seconds = 0
    for match in matches:
        amount = int(match.group(1))
        unit = match.group(2)
        total_seconds += amount * unit_seconds[unit]

    if total_seconds <= 0:
        raise typer.BadParameter("活跃时段时长必须大于 0 秒。")

    return float(total_seconds)


def validate_inputs(
    daily_requests: int | None,
    active_ratio: float | None,
    active_duration: str | None,
) -> dict[str, float | str]:
    """校验命令行参数，并整理成统一的 CLI 输入。"""
    if daily_requests is None or daily_requests <= 0:
        raise typer.BadParameter("请提供大于 0 的 --d（日请求量）。")

    values: dict[str, float | str] = {}
    if active_duration is not None and active_duration.strip():
        values["active_duration_label"] = active_duration.strip()

    overrides = {
        "active_ratio": parse_ratio(active_ratio, "活跃时段流量占比") if active_ratio is not None else None,
        "active_seconds": parse_duration_to_seconds(active_duration),
    }
    for key, value in overrides.items():
        if value is not None:
            values[key] = value

    required_fields = (
        ("active_ratio", "--active-ratio"),
        ("active_seconds", "--active-duration"),
    )
    missing_fields = [label for field, label in required_fields if field not in values]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise ValueError(f"缺少必要参数: {joined}。")

    if float(values["active_seconds"]) <= 0:
        raise typer.BadParameter("活跃时段时长必须大于 0。")

    values["daily_requests"] = float(daily_requests)
    return values
