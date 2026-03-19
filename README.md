# 高分位请求强度测算工具

基于 [doc/流量测算.md](doc/流量测算.md) 中的泊松分布分位数方法，从模型日请求量估算高分位等效 QPS。

## 核心计算链路

$$
日请求量\ R_d \rightarrow 活跃时段平均到达率\ QPS_{avg} \rightarrow 窗口请求数泊松分布 \rightarrow 高分位请求数\ q_{p,\Delta t} \rightarrow 高分位等效\ QPS
$$

## 代码结构

- `src/main.py`: Typer CLI 入口与结果输出
- `src/cli_args.py`: CLI 参数解析、校验、格式化
- `src/calc.py`: 泊松分位数核心计算逻辑
- `src/params.py`: 默认常量
- `doc/流量测算.md`: 计算方法文档

## 安装

```bash
uv sync
```

或：

```bash
pip install typer
```

## 使用方式

查看帮助：

```bash
python src/main.py --help
```

基础示例（使用默认窗口 10s、默认分位 P99 + P99.9）：

```bash
python src/main.py --d 100000 --active-ratio 0.9 --active-duration 10h
```

指定统计窗口和分位：

```bash
python src/main.py --d 100000 --active-ratio 0.9 --active-duration 10h --window 60 --percentile 0.99 --percentile 0.999
```

## CLI 参数

| 参数 | 缩写 | 说明 | 默认值 |
|---|---|---|---|
| `--d` | `-d` | 模型日请求量 $R_d$ | 必填 |
| `--active-ratio` | `-r` | 活跃时段流量占比 $R_{act}$，支持 `0.9` 或 `90` | 必填 |
| `--active-duration` | `-a` | 活跃时段时长 $H_{act}$，支持 `10h`、`30m`、`10h30m` | 必填 |
| `--window` | `-w` | 统计窗口 $\Delta t$（秒） | `10` |
| `--percentile` | `-p` | 目标分位，可多次传入 | `0.99, 0.999` |

## 输出说明

对每个目标分位，输出：

| 指标 | 含义 |
|---|---|
| `QPS_avg` | 活跃时段平均到达率 $\lambda$ |
| `μ` | 统计窗口内平均请求数 |
| `q_{p,Δt}` | 高分位请求数 |
| `QPS_{p,\Delta t}` | 高分位等效 QPS，即 $q_{p,\Delta t} / \Delta t$ |

## 示例输出

```
输入参数
  模型日请求量 R_d:       100,000
  活跃时段流量占比 R_act:  90.0%
  活跃时段时长 H_act:      10h (36,000 秒)
  统计窗口 Δt:            10 秒
  目标分位:               99.0%, 99.9%

高分位 QPS 测算

  ── 99.0% 分位 ──
  活跃时段平均到达率 QPS_avg:  2.50
  窗口平均请求数 μ:            25
  高分位请求数 q_{p,Δt}:       37
  高分位等效 QPS_{p,Δt}:      3.70

  ── 99.9% 分位 ──
  活跃时段平均到达率 QPS_avg:  2.50
  窗口平均请求数 μ:            25
  高分位请求数 q_{p,Δt}:       42
  高分位等效 QPS_{p,Δt}:      4.20
```
