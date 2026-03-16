from __future__ import annotations

from typing import Annotated

import typer

from cli_args import (
    format_decimal,
    format_percent,
    parse_stability_targets,
    parse_threshold_range,
    validate_inputs,
)
from calc import calculate_poisson_metrics, poisson_tail_probability, recommend_threshold
from params import DEFAULT_STABILITY_TARGETS


app = typer.Typer(
    add_completion=False,
    help="根据 doc/并发量估算.md 使用泊松分布统计模型估算 AI 对话类应用并发阈值。",
)


@app.command()
def main(
    daily_dialogs: Annotated[
        int | None,
        typer.Option("--d", "-d", help="日对话次数 D。"),
    ] = None,
    avg_duration: Annotated[
        float | None,
        typer.Option("--t", "-t", help="单轮对话平均耗时 T（秒）。"),
    ] = None,
    daytime_ratio: Annotated[
        float | None,
        typer.Option("--day-ratio", "-r", help="日间流量占比，支持 0.9 或 90 两种写法。"),
    ] = None,
    active_duration: Annotated[
        str | None,
        typer.Option("--day-time", "-a", help="日间活跃时长，使用 NUM+UNIT 格式，例如 3h、19m、4s 或 3h20m43s。"),
    ] = None,
    threshold: Annotated[
        str | None,
        typer.Option("--k", "-k", help="并发阈值，可传单个值 k 或范围 n~m，例如 10 或 10~14。"),
    ] = None,
    stability_target: Annotated[
        list[str] | None,
        typer.Option("--stability", "-s", help="稳定性目标列表。多次传入该参数可分析多个目标，例如 --stability 99.5。"),
    ] = None,
) -> None:
    """泊松分布并发量估算工具。

    示例:
      python src/main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h --k 10
      python src/main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h --k 10~14
    """
    thresholds = parse_threshold_range(threshold)
    try:
        values = validate_inputs(
            daily_dialogs=daily_dialogs,
            avg_duration=avg_duration,
            daytime_ratio=daytime_ratio,
            active_duration=active_duration,
        )
        stability_targets = parse_stability_targets(stability_target or DEFAULT_STABILITY_TARGETS)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    metrics = calculate_poisson_metrics(
        daily_dialogs=int(float(values["daily_dialogs"])),
        avg_duration=float(values["avg_duration"]),
        daytime_ratio=float(values["daytime_ratio"]),
        active_seconds=float(values["active_seconds"]),
    )

    typer.echo("输入参数")
    typer.echo(f"- 日总对话次数 D: {format_decimal(float(values['daily_dialogs']))}")
    typer.echo(f"- 单轮耗时 T: {format_decimal(float(values['avg_duration']))} 秒")
    typer.echo(f"- 日间流量占比: {format_percent(float(values['daytime_ratio']))}")
    if "active_duration_label" in values:
        typer.echo(
            f"- 日间活跃时长: {values['active_duration_label']} "
            f"({format_decimal(float(values['active_seconds']))} 秒)"
        )
    else:
        typer.echo(f"- 日间活跃时长: {format_decimal(float(values['active_seconds']))} 秒")

    typer.echo("\n泊松模型结果")
    typer.echo(f"- λ（每秒平均请求数 / 日间平均并发）: {format_decimal(metrics['lambda'])}")

    if thresholds:
        typer.echo("\n指定阈值分析")
        for current_threshold in thresholds:
            tail_probability = poisson_tail_probability(metrics["lambda"], current_threshold)
            stability = 1 - tail_probability
            typer.echo(
                f"- k={current_threshold}: 超阈值概率 P(X>=k)≈{format_percent(tail_probability)}, "
                f"稳定性≈{format_percent(stability)}"
            )

    typer.echo("\n泊松阈值建议")
    for stability in stability_targets:
        recommended_threshold, tail_probability = recommend_threshold(metrics["lambda"], 1 - stability)
        typer.echo(
            f"- {format_percent(stability)} 稳定性: 建议阈值 k={recommended_threshold}, "
            f"超阈值概率≈{format_percent(tail_probability)}"
        )


if __name__ == "__main__":
    app()
