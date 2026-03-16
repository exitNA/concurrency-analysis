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


def parse_stability_targets(values: list[str] | tuple[float, ...]) -> tuple[float, ...]:
    """解析稳定性目标，例如 0.999 或 99.9。"""
    parsed = []
    for value in values:
        ratio = parse_ratio(value, "稳定性目标")
        if ratio >= 1:
            raise ValueError("稳定性目标必须小于 100%")
        parsed.append(ratio)
    return tuple(sorted(set(parsed)))


def parse_threshold_range(value: str | None) -> list[int]:
    """解析并发阈值，支持单个值 k 或范围 n~m。"""
    if value is None or not value.strip():
        return []

    normalized = value.strip().replace(" ", "")
    if "~" not in normalized:
        try:
            threshold = int(normalized)
        except ValueError as error:
            raise typer.BadParameter("并发阈值必须是整数，或使用 n~m 格式，例如 --k 10 或 --k 10~14。") from error
        if threshold <= 0:
            raise typer.BadParameter("并发阈值必须大于 0。")
        return [threshold]

    start_text, end_text = normalized.split("~", 1)
    if not start_text or not end_text:
        raise typer.BadParameter("并发阈值范围必须使用完整的 n~m 格式，例如 --k 10~14。")

    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError as error:
        raise typer.BadParameter("并发阈值范围中的 n 和 m 必须是整数。") from error

    if start <= 0 or end <= 0:
        raise typer.BadParameter("并发阈值范围中的 n 和 m 必须大于 0。")
    if start > end:
        raise typer.BadParameter("并发阈值范围必须满足 n<=m，例如 --k 10~14。")

    return list(range(start, end + 1))


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
            "日间活跃时长必须使用 NUM+UNIT 格式，例如 3h、19m、4s 或 3h20m43s。"
        )

    consumed = "".join(match.group(0) for match in matches)
    if consumed != normalized:
        raise typer.BadParameter(
            "日间活跃时长必须使用 NUM+UNIT 格式，例如 3h、19m、4s 或 3h20m43s。"
        )

    unit_seconds = {"h": 3600, "m": 60, "s": 1}
    total_seconds = 0
    for match in matches:
        amount = int(match.group(1))
        unit = match.group(2)
        total_seconds += amount * unit_seconds[unit]

    if total_seconds <= 0:
        raise typer.BadParameter("日间活跃时长必须大于 0 秒。")

    return float(total_seconds)


def validate_inputs(
    daily_dialogs: int | None,
    avg_duration: float | None,
    daytime_ratio: float | None,
    active_duration: str | None,
) -> dict[str, float | str]:
    """校验命令行参数，并整理成统一的 CLI 输入。"""
    if daily_dialogs is None or daily_dialogs <= 0:
        raise typer.BadParameter("请提供大于 0 的 --d。")

    values: dict[str, float | str] = {}
    if active_duration is not None and active_duration.strip():
        values["active_duration_label"] = active_duration.strip()

    overrides = {
        "avg_duration": avg_duration,
        "daytime_ratio": parse_ratio(daytime_ratio, "日间流量占比") if daytime_ratio is not None else None,
        "active_seconds": parse_duration_to_seconds(active_duration),
    }
    for key, value in overrides.items():
        if value is not None:
            values[key] = value

    required_fields = ("avg_duration", "daytime_ratio", "active_seconds")
    missing_fields = [field for field in required_fields if field not in values]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise ValueError(f"缺少必要参数: {joined}。请直接通过 CLI 传入。")

    if float(values["active_seconds"]) <= 0:
        raise typer.BadParameter("日间活跃时长必须大于 0。")
    if float(values["avg_duration"]) <= 0:
        raise typer.BadParameter("单轮对话平均耗时必须大于 0。")

    values["daily_dialogs"] = float(daily_dialogs)
    return values
