from __future__ import annotations

from typing import Annotated

import typer

from cli_args import (
    format_decimal,
    format_percent,
    parse_percentiles,
    validate_inputs,
)
from calc import estimate_peak_qps
from params import DEFAULT_PERCENTILES, DEFAULT_WINDOW_SECONDS


app = typer.Typer(
    add_completion=False,
    help="基于 doc/并发量估算.md 的高分位请求强度测算工具。",
)


@app.command()
def main(
    daily_requests: Annotated[
        int | None,
        typer.Option("--d", "-d", help="模型日请求量 R_d。"),
    ] = None,
    active_ratio: Annotated[
        float | None,
        typer.Option("--day-ratio", "-r", help="活跃时段流量占比 R_act，支持 0.9 或 90 两种写法。"),
    ] = None,
    active_duration: Annotated[
        str | None,
        typer.Option("--day-time", "-a", help="活跃时段时长 H_act，使用 NUM+UNIT 格式，例如 10h、30m 或 10h30m。"),
    ] = None,
    window: Annotated[
        float | None,
        typer.Option("--window", "-w", help="统计窗口 Δt（秒），默认 10 秒。"),
    ] = None,
    percentile: Annotated[
        list[str] | None,
        typer.Option("--percentile", "-p", help="目标分位，可多次传入，例如 --percentile 0.99 --percentile 0.999。"),
    ] = None,
) -> None:
    """高分位请求强度测算工具。

    示例:
      python src/main.py --d 100000 --day-ratio 0.9 --day-time 10h
      python src/main.py --d 100000 --day-ratio 0.9 --day-time 10h --window 10 --percentile 0.99 --percentile 0.999
    """
    window_seconds = window if window is not None else DEFAULT_WINDOW_SECONDS

    try:
        values = validate_inputs(
            daily_requests=daily_requests,
            active_ratio=active_ratio,
            active_duration=active_duration,
        )
        percentiles = parse_percentiles(percentile or DEFAULT_PERCENTILES)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    if window_seconds <= 0:
        raise typer.BadParameter("统计窗口 Δt 必须大于 0。")

    # ── 输入参数 ──
    typer.echo("输入参数")
    typer.echo(f"  模型日请求量 R_d:       {format_decimal(float(values['daily_requests']))}")
    typer.echo(f"  活跃时段流量占比 R_act:  {format_percent(float(values['active_ratio']))}")
    if "active_duration_label" in values:
        typer.echo(
            f"  活跃时段时长 H_act:      {values['active_duration_label']} "
            f"({format_decimal(float(values['active_seconds']))} 秒)"
        )
    else:
        typer.echo(f"  活跃时段时长 H_act:      {format_decimal(float(values['active_seconds']))} 秒")
    typer.echo(f"  统计窗口 Δt:            {format_decimal(window_seconds)} 秒")
    typer.echo(f"  目标分位:               {', '.join(format_percent(p) for p in percentiles)}")

    # ── 高分位 QPS 测算 ──
    typer.echo("\n高分位 QPS 测算")
    for p in percentiles:
        result = estimate_peak_qps(
            daily_requests=int(float(values["daily_requests"])),
            active_ratio=float(values["active_ratio"]),
            active_seconds=float(values["active_seconds"]),
            window_seconds=window_seconds,
            percentile=p,
        )
        typer.echo(f"\n  ── {format_percent(p)} 分位 ──")
        typer.echo(f"  活跃时段平均到达率 QPS_avg:  {format_decimal(result['qps_avg'])}")
        typer.echo(f"  窗口平均请求数 μ:            {format_decimal(result['mu'])}")
        typer.echo(f"  高分位请求数 q_{{p,Δt}}:       {format_decimal(result['q_p'])}")
        typer.echo(f"  高分位等效 QPS:              {format_decimal(result['qps_peak'])}")


if __name__ == "__main__":
    app()
