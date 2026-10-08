---
id: RECHECK-20261008-342
slug: goal-037-ec03-cross-run-knowledge-read-in
title: 独立复检：GOAL-037 cycle 3（EC-03）跨 run 知识累积（承接 + 实跑 + 两向反证）
plan_id: PLAN-20261008-341
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-342 — GOAL-037 cycle 3（EC-03）独立复检

复检对象：`PLAN-20261008-341`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 承接链五件事（AC-1）

| 读法 | 读数 |
| --- | --- |
| 实现 | `adapters/canonical/research_state_read.py` 在树；缺 `RunStore` / 无程序归属 ⇒ `InvalidInputError` **点名** |
| 声明 | `examples/config/tool_providers.yaml` 的 `m12_artifact.capabilities` 含 `research_state.read` |
| 绑定 | `DEFAULT_SESSION_TOOL_BINDINGS` 含 `("research_state.read", "m12_artifact", "research_state_read")` |
| 接线 | `composition.py` 走 `sqlite_session_tools(faces, ports)`（`ports.program_store`）；`pg_composition.py` 的 `session_tool_face(..., c["program_store"])` |
| 放行 | `policy.yaml` 新增一条 `allow`（scope `project`）；`_CAPABILITY_SCOPE` 镜像同轮 |
| 判据 | `tests/adapters/canonical` + `tests/architecture` **322 passed** |

### 2. 后一轮真的读到前一轮结论（AC-2）

`tests/e2e/test_cross_run_knowledge_on_the_run_path.py` **6 passed**（本文件独立重跑）：

| 断言 | 读数 |
| --- | --- |
| 主路 | 第 2 轮 `prior_runs == [第 1 轮]`、`program_index == 1`、`state == SUCCEEDED`、`verdicts` 含 `PASS`（与 `review.read` 同一取值口径）、`reviewed_by == gate:reviewer_a`、`manifest_digest` 在场 |
| 第 1 轮构造性空集 | `prior_run_count == 0` + `prior_runs == []`（如实给，不是「读不到」） |
| 可复核 | 两轮结果制品 id **不同**；digest 在场 |
| 反证① | 撤 provider ⇒ `run.failed` 消息点名 provider / 工具 / 能力 |
| 反证② | 删 allow ⇒ preflight `FAIL` + finding 点名 `POLICY_DENIED` + 该能力 |

### 3. 登记面与读数（AC-3）

| 读法 | 读数 |
| --- | --- |
| 覆盖判据 | `research_state.read` 在 `_IN_SCOPE`、不在 `_OUT_OF_SCOPE_REASONS`（搬迁）；词表仍 46 条 |
| 出厂夹具 | `_PROVIDER.capabilities` +1；`test_canonical_read_carried_later` 的绑定覆盖判据绿 |
| 差集文档 | 该行离开差集表、进交集清单（17→18）；「该登记」计数 7→6 |
| 登记计数 | `EXPECTED_REGISTERED` 8→6；`_RELEASED` +1 / `_UNRELEASED_READS` −1 / scope 期望表 +1 |
| 判据 | `tests/application/preflight` **44 passed**；`tests/architecture` 全绿 |

### 3b. m0 首跑真红并修（如实登记）

`python/format-check` 判红（两个文件未过 `ruff format`：删登记条留下的空行 +
`research_state_read.py` 的嵌套字典）。处置 = **格式化**（不调阈值、不改判据），
随后重跑全量 m0 取终局读数。

### 4. 门链与记录面（AC-4）

`ruff` / `format` / `mypy`（1160 files）全绿；广面（e2e + application + architecture +
adapters + contracts + loaders + observability + tooling + api）**4583 passed, 95 skipped**
（唯一一次红为**已知类 flake**：OTLP teardown race —— 单跑该文件 4 passed 取证；
另有一次 `cross_run_support.py` 函数 **54 行**超 50 上限 ⇒ **拆 `_trim_the_grant`** 修复）。

as-is m0（在全部记录写入之后）：**`PASS: profile=m0; 23 deterministic checks`**
（`PASS [` 24 / `FAILED [` 0 / **5417 passed, 20 skipped**；首跑真红于 `python/format-check`
⇒ 格式化后重跑取值，日志 `scratch/m0-goal037-cycle3-rerun.log`）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立。

### Warnings

- **W-1（起 run 的写序在程序面改变）**：`POST /programs/{id}/advance` 起 run 时**先落
  run 行**（含程序归属）再执行 —— 因为读链工具在执行期要靠那一行反查程序归属（实测：
  不先落行 ⇒ `KeyError: run not found`）。HTTP 面（`POST /projects/{id}/runs`）写序
  **未变**；两条路径的差别已写进 `programs.py` 的注释。
- **W-2（判词取值口径）**：读面给出的是 `ReviewFinding.verdict` 的**值**（`PASS`），
  不是「逐字判词行」（那是 `findings` 数组，由 `review.read` 承载）。两条读面口径不同是
  **有意**的：本能力回答「上一轮的结论是什么」，不回答「上一轮的判据逐条怎么说」。
- **W-3（已知类 flake 复现一次 + 一次规模真红并修）**：`observability/test_lifecycle_bounds.py`
  在广面合跑时红一次（teardown race 签名），单跑通过；`cross_run_support.py` 函数超限 ⇒
  拆函数（不调阈值）。
- **W-4（承继残余原样保持）**：GOAL-036 的 `M-1`…`M-5`、`R26-*` 终态、未覆盖范围逐条保持；
  **不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
