# 并发量估算工具

基于 [doc/并发量估算.md](/mnt/c/work/concurrency-analysis/doc/并发量估算.md) 中的泊松分布统计模型，估算对话类 AI 应用的并发风险、阈值超标概率和建议限流阈值。

## 功能

- 根据日对话次数 `D`、单轮耗时 `T`、日间流量占比、日间活跃时长计算 `λ`
- 计算指定并发阈值 `k` 的超阈值概率 `P(X>=k)`
- 根据稳定性目标反推建议阈值
- 支持时长格式 `3h`、`19m`、`4s`、`3h20m43s`
- 支持单个阈值 `k=10`，也支持范围 `k=10~14`

## 代码结构

- [main.py](/mnt/c/work/concurrency-analysis/main.py): Typer CLI 入口与结果输出
- [cli_args.py](/mnt/c/work/concurrency-analysis/cli_args.py): CLI 参数解析、校验、格式化
- [calc.py](/mnt/c/work/concurrency-analysis/calc.py): 泊松分布核心计算逻辑
- [params.py](/mnt/c/work/concurrency-analysis/params.py): 默认常量
- [doc/并发量估算.md](/mnt/c/work/concurrency-analysis/doc/并发量估算.md): 计算依据文档

## 安装

项目依赖写在 [pyproject.toml](/mnt/c/work/concurrency-analysis/pyproject.toml)。

如果使用 `uv`：

```bash
uv sync
```

如果直接使用本地 Python 环境，至少需要安装：

```bash
pip install typer
```

## 使用方式

查看帮助：

```bash
python main.py --help
```

基础示例：

```bash
python main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h
```

分析单个阈值：

```bash
python main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h --k 10
```

分析阈值范围：

```bash
python main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h --k 10~14
```

指定稳定性目标：

```bash
python main.py --d 100000 --t 2 --day-ratio 90 --day-time 10h --stability 95 --stability 99.5 --stability 99.9
```

## CLI 参数

- `--d`, `-d`: 日对话次数 `D`
- `--t`, `-t`: 单轮对话平均耗时 `T`，单位秒
- `--day-ratio`, `-r`: 日间流量占比，支持 `0.9` 或 `90`
- `--day-time`, `-a`: 日间活跃时长，支持 `3h`、`19m`、`4s`、`3h20m43s`
- `--k`, `-k`: 并发阈值，支持单个值 `10` 或范围 `10~14`
- `--stability`, `-s`: 稳定性目标，可重复传入多个值

## 输出说明

工具会输出三类结果：

- 输入参数回显
- 泊松模型核心结果：全天平均并发与 `λ`
- 指定阈值分析：`P(X>=k)` 与对应稳定性
- 泊松阈值建议：按稳定性目标反推建议阈值

示例输出中的：

- `λ`: 每秒平均请求数，也可理解为日间平均并发
- `P(X>=k)`: 某一秒并发量大于等于阈值 `k` 的概率

## 校验

可以用下面的方式检查脚本是否可正常导入：

```bash
python -m py_compile main.py calc.py cli_args.py params.py
```
