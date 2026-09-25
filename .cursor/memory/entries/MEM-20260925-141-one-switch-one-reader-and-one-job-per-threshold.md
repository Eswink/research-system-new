---
id: MEM-20260925-141
title: "一个开关一个读取点：live 开门条件收紧的形态，与「阈值判据独占进程」的取舍"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-182-live-switch-and-observability-job-isolation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-183-live-switch-and-observability-job-isolation.md
supersedes: []
tags: [live-run, gate, explicit-switch, ci-jobs, observability, goal-017, d-11, d-13]
---

## 做了什么

两件事，各自都能被**独立按压**：

1. **live 开门条件收紧（D-11）**：`packages/application/model_relay/live_run_gate.py` 新增产品常量
   `LIVE_RUN_SWITCH = "RESEARCHOS_LIVE_E2E"`，`evaluate_live_run_gate(...)` 增**必填**参数
   `live_switch: bool` ⇒ 门从两条条件（runtime / 凭据）变**三条**（开关 / runtime / 凭据），
   凭据由**充分**降为**必要**。环境**只在** `tests/e2e/live_switch_support.py::live_e2e_switch_enabled`
   读一次（值**恰为** `"1"` 才算开；该模块是**单一职责**小模块，理由见下）；12 个 live 模块全部经
   这道逻辑（8 处经门、4 处经谓词）；`docs/integration/LIVE_MODEL_RUNBOOK.md` §4/§7/§8 逐字同源。
2. **整进程资源阈值判据独占进程（D-13）**：`.github/workflows/m0-quality.yml` 新增作业
   `observability-overhead`（矩阵 ubuntu + windows）单独跑
   `tests/observability/test_telemetry_overhead.py`；`quality-*` 的「Run all M0 gates」步骤加
   `PYTEST_ADDOPTS: --ignore=tests/observability/test_telemetry_overhead.py`。**判据、阈值、测量语义一字未动**。

## 为什么这样做

- **凭据在场不是「我想跑真实调用」的意思表示**：环境里恰好有凭据（CI secret、开发机 `.env`、
  导入栈的 dotenv）会让默认门**真的出网**，于是「默认门离线」这句话取决于环境而不可判。
  收紧成「开关 **且** 凭据」之后，默认门的行为**与被试环境无关**。
- **同源要能被按压才知道**：第一版判据用**文本**找读取点（`os.environ` 与开关名同现），
  按压 `_os.environ.get('RESEARCHOS_LIVE_E2E')` + 别名时**看着绿**——docstring 里的操作者口令
  被算成读取点、真正的第二读取点却漏过。改成 **AST**（「按开关名取映射项」的表达式）后才真的受判。
  ⇒ **判据要用语法结构判，不要用文本巧合判**。
- **阈值判据的噪声来自同进程的邻居，不来自它自己**：两次实测（GOAL-015 的 run `36071654181` 与
  GOAL-017 cycle 1 的 run `36163737079`，都是 `quality-windows-latest`）整进程 RSS 增量
  174.0 / 175.3 MiB > 阈值 128 MiB，同代码复跑（`run_attempt=2`）又绿 ⇒ 属 `(ii)` 类。
  阈值与测量语义**不能动**（那是放宽），**能动的只有进程边界**：把判据拆到自己的进程里。
- **贴线文件不要「顺手加东西」，拆模块而不是调阈值**：把开关两函数放进
  `tests/e2e/live_run_support.py`（448 行）后它变成 **477 行 > 450 硬上限**，m0 当场判红
  （`test_python_source_size_limits[...live_run_support.py]`）。处置是**拆出单一职责小模块**
  （`tests/e2e/live_switch_support.py`，43 行）并改 12 处 import，**不是**抬 450 这个数。
  ⇒ 规模门禁的价值正在于此：它把「哪个文件该装什么」变成**机械判据**。

## 怎么做与复现

```bash
# D-11 判据（14 条）+ 6 处按压（逐次改一处、跑判据、按 sha256 逐字节还原）
.venv/Scripts/python.exe -m pytest tests/architecture/python/test_live_switch_is_single_source.py -q
.venv/Scripts/python.exe scratch/goal017-d11-press.py     # 期望 pressed=6 failures=[]
# 三态（①②离线、③是本 GOAL 唯一一次真实出网）
RESEARCHOS_AGENT_RUNTIME=openhands pytest tests/e2e/test_ec04_live_first_run.py -q -rs          # ① skip 点名开关
LLM_MAIN_KEY= RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands pytest … -q -rs          # ② skip 点名凭据
RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands pytest … -q -rs                        # ③ 门开、run 到终态

# D-13：机制取证（3 → 0）+ 隔离进程实跑 + 阈值零改动
PYTEST_ADDOPTS=--ignore=tests/observability/test_telemetry_overhead.py pytest tests/observability --collect-only -q
pytest tests/observability/test_telemetry_overhead.py -q     # 独立进程：3 passed（远低于阈值）
git diff -- tests/observability/test_telemetry_overhead.py   # 必须为空
```

## 适用边界

- **开关的语义是「恰为 `1`」**，不做真值解析（`true`/`yes`/`on`/` 1`/`1 ` 一律算关）；
  与 `RESEARCHOS_REQUIRE_DOCKER` / `RESEARCHOS_REQUIRE_GPU` 同形态。
- **开关名是操作者契约**：要改必须先改产品常量，再同步 runbook 与各 live 模块 docstring 里的口令
  （判据会按**导入的常量**比对 §4，改任一侧即红）。
- **`packages/application/**` 保持 env-free**：开关的**名称**是产品常量、**值**由调用方作**必填**参数传入
  ⇒ 漏传是 `TypeError`，不存在「忘了传就默认开门」。
- **D-13 只改 CI 结构**：本机 m0 仍在同一进程里跑该阈值判据（负载高时仍可能偶发红，仍按 `(ii)` 类复跑）。
  新作业与既有作业同形态（无 `continue-on-error` / `if:`）⇒「本作业红 ⇒ 整体 CI 红」不变。
- **单读取点的实物搬了家，判据的显式清单必须同步**：`SWITCH_PREDICATE_MODULE` /
  `CONSTANT_MENTIONS` 这类清单是**自检**的（改错就红），搬迁时正靠它确认新模块已就位。
- **放行面没变**：`tests/egress_guard.py` 仍只认 `requires_live_llm` 一个 marker；开关只决定
  「进不进 run」，**不**参与出网放行。

## 来源

- 计划：`PLAN-20260925-182`（GOAL-017 EC-02 / EC-03，授权原文见其 frontmatter `authorization.ref`）。
- 复检：`RECHECK-20260925-183`（`PASS_WITH_WARNINGS`：8 条 AC + W-1…W-5）。
- 实跑日志：`scratch/goal017-c2-state3-live.log`（三态③）、`scratch/goal017-d11-press.py`（按压）。
- 相关记忆：[[evidence-read-face-claim-relation]]、[[live-e2e-policy-and-fixtures]]、
  [[local-gate-protocol-and-flake-classes]]、[[goal-closeout-procedure]]、[[m0-ci-concurrency-batch-push]]。
