---
id: RECHECK-20261008-340
slug: goal-037-ec02-program-advance-entry
title: 独立复检：GOAL-037 cycle 2（EC-02）程序推进驱动 + 产品入口 + 双 run 实跑
plan_id: PLAN-20261008-339
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-340 — GOAL-037 cycle 2（EC-02）独立复检

复检对象：`PLAN-20261008-339`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 驱动与六条判定（AC-1）

| 读法 | 读数 |
| --- | --- |
| 驱动判据 | `tests/application/run_orchestration/test_program_runner.py` **7 passed**（`START` / `WAIT` / `STOP_RULE` / `CONTINUE` / `STOP_GUARDRAIL` / `DEDUP` / 无启动面点名） |
| 判定输入全取落库事实 | 读源码：`advance_program` 只读 `runs.for_program` / `run.is_terminal` / `findings.for_run` / `programs.decisions_of` —— 无第二套状态 |
| 幂等崩溃窗口 | 用例实测：认领未落库 ⇒ `DEDUP`、`h.started == []`、run 数不变 |
| 规模门 | 拆函数后各 ≤ 50 行（本文件独立复核 `function_spans`） |

### 2. 产品入口与读面（AC-2）

| 读法 | 读数 |
| --- | --- |
| 路由在树 | `services/api/routers/programs.py`（三路由 + 列表路由）+ `services/api/dto/programs.py` |
| OpenAPI 快照 | 由生成器重生成（与 `types.ts` 的新类型一致）；`tests/contracts` **8 passed** |
| 读面可回答「为何继续 / 为何停」 | 读面用例断言 `decision.kind` / `reason` / **`cited_facts` 逐字**（`verdict PASS` / `verdict REJECT`） |
| 缺启动面点名 | 反证臂：`deps.runs = None` ⇒ 决策 `WAIT` + 理由含「未提供启动面」（**不是** 503 崩、不是静默 200） |

### 3. 双 run 实跑（AC-3）

| 读法 | 读数 |
| --- | --- |
| 新增判据文件 | `tests/e2e/test_program_advance_on_the_run_path.py` **6 passed** |
| 关联落 canonical | 第 1 轮 run 经 `GET /runs/{id}` 读出 `program_id` / `program_index == 1` |
| 结论驱动 | `CONTINUE` 的 `cited_facts == ["verdict PASS"]`；`STOP_RULE` 的 `cited_facts` 含 `verdict REJECT` |
| 护栏可区分 | `STOP_GUARDRAIL` 种类不同 + 理由点名 `max_runs=1` |

### 4. 门链与记录面（AC-4）

`ruff check` / `format` / `mypy`（1157 files）全绿；前端 `typecheck` + `lint` 绿；
广面（contracts + api + observability + tooling + architecture + e2e）**3209 passed, 91 skipped**
（唯一一次红为**已知类 flake**：OTLP teardown race —— 单跑该文件 4 passed、单跑该用例
1 passed 取证）；as-is m0 与治理读数见 GOAL 迭代日志 cycle 2 行。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立。

### Warnings

- **W-1（登记面同步如实登记）**：本轮为挂新读写路由，触及四处**登记面**（写面告警线
  61→63 / 读面登记 +2 条 / 出口普查 +2 处 / `create_app` 拆函数）。**断言强度与谓词
  一格未动**；`MEM-20261008-208` 记下判别法（点名计数/清单/规模 ⇒ 同步面；点名谓词 ⇒ 不是）。
- **W-2（跨 run 知识的**读入**不在本轮）**：本轮证的是「续跑由落库结论**驱动**」；
  第 2 轮是否**读到**第 1 轮的结论（能力面读入 + 下游消费）是 EC-03 的事。
- **W-3（已知类 flake 复现一次）**：`tests/observability/test_lifecycle_bounds.py` 在
  广面合跑时红一次（`/v1/metrics` 连接被拒 = teardown race 签名），单跑两次均通过；
  按既有配方处置，**未**改判据或产品代码。
- **W-4（承继残余原样保持）**：GOAL-036 的 `M-1`…`M-5`、`R26-*` 终态、未覆盖范围逐条保持；
  **不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
