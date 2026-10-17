---
id: PLAN-20261016-503
slug: goal-081-ec04-cross-phase-inputs-close-the-coverage-gap
title: GOAL-081 cycle 4 — 跨相输入：让上游检索进入立题格的覆盖（EC-04）
status: DONE
created_at: 2026-10-17
updated_at: 2026-10-17
parent_goal: GOAL-20261016-081
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-504-goal-081-ec04-cross-phase-inputs.md
memory_entries: []
---

# PLAN-20261016-503 — GOAL-081 cycle 4

## 验收条件

- [x] **(a) 形态**：`inputs` 支持 `{phase_id}:{artifact_name}`；**解析不了的引用在编译期点名**
      （六类：自引用 / 未知 phase / 非上游 / 产出方未声明该产物 / 产物歧义 / 读取方执行体不消费）
- [x] **(b) 性质来源**：跨相输入的 `trust_label` **由产出方决定**（编译期算，随 `CompiledPhase`
      携带）；**按压**：摘掉产出方的 run-chain 声明 ⇒ 性质必须变 `GENERATED`
- [x] **(c) 反编造门不削弱**：`_input_evidence` 的内容校验与「组合根供给」**并列**接受
      「有性质的 phase 产出」；**按压**：摘掉跨相证据 ⇒ 覆盖的性质维判拒（`0 < 1 retrieved`）
- [x] 接线 `grounded_report_chain_v1.yaml` 的 `plan` 相 `inputs`
- [x] **离线复现**：`plan` 的 `EVIDENCE_COVERAGE` 由 `0 < 1` 变成**成立**（run `SUCCEEDED`）
- [x] **live 实跑**：真实 run `SUCCEEDED`，`plan` 的提示词带三个真标识，且**计划正文引用了全部三条**
- [x] 读数归档进树（`CR=0`）+ 生态门（规模门 / ruff / mypy）
- [x] 记录面（PLAN + RECHECK + GOAL 回写 / `ALL_PLAN` / `MAINLINE` 阶梯）

## 目标（本 cycle 的可独立验收主题）

**EC-04 的阻塞点 (c)**：`inputs` 不能引用上游 phase 的产物 ⇒ 修复它，让「立题站在检索之上」
成为**机械可判**的事实（覆盖两维都由真实来源满足）。

## ★ 与前几个 cycle 的关系

- cycle 3 定位了**两条**根因（运行链证据无 claim relation / 覆盖门只数本任务），并**实测**了
  第三条：`inputs` 里的 id 被**逐字**当制品 id 解析。cycle 3 的 RECHECK 把它记为 `W-1`（未达成）。
- 本 cycle 采用 GOAL 取舍表里的**解法 A**（上游产物作下游声明输入），并**明确不做**解法 B
  （覆盖门按 run 作用域计数 —— 那会放宽「来源必须是自己看到的」这条既有判据）。

## 实施清单

1. **WP-A**（编译期）：`protocol_compile/cross_phase_inputs.py` —— 形态判定、六类校验、
   性质推导（`producer_trust_label`）；`CompiledPhase.cross_phase_inputs` 携带
   `(产出方, 产物名, TrustLabel)`。
2. **WP-B**（运行期）：`run_orchestration/cross_phase_inputs.py` —— 按 canonical 的
   idempotency key 解析真实 task id、内容校验（`meta` + `verify`）、登记 `SourceRecord`
   + `Evidence`（origin 为**有向边** `cross-phase:{读取方任务}:{产出方产物}`，不与产出方
   自己的记录相撞）。
3. **WP-C**（接线）：`RegistrationDeps.cross_phase_evidence` →
   `register_session_result` → `ResultRegistration.evidence`（与 `retrieved_evidence` 并列）。
4. **WP-D**（判据）：`tests/application/run_orchestration/test_cross_phase_inputs.py`（11 条，
   含两条按压）+ `tests/e2e/test_cross_phase_inputs_reach_the_plan_phase.py`（主判据 + 按压臂）。
5. **WP-E**（实跑）：离线复现 + live 实跑 + 读数归档。
6. **WP-F**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN` / `MAINLINE`；m0。

## 影响报告

- **产品代码**：新增三个模块（编译期解析 / 运行期解析登记 / 会话携带）；
  `result_handler` / `task_phase_helpers` / `task_executor` / `session_resolution` /
  `compiler` / `domain/protocols.py` 各自加一条**缺省空**的通道 ⇒ 未声明跨相输入的协议
  **逐字**不变（既有 e2e 20 条、application 1399 条零回归）。
- **读面 / DTO / 路由 / 快照**：零改动（跨相来源经既有 `GET /runs/{id}/evidence` 可读）。
- **判据面**：**只增**（两个新文件）；既有判据一条不动、无放宽。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮的新知识已全部写进本文件与 RECHECK-504 的可复核观察面；不另立工程记忆条目 —— 跨相输入的口径由判据文件本身钉住，读判据比读记忆更可靠）。

## 残余与未覆盖

- 只判「引用了标识」，**内容一致性**（说法与摘要是否相符）仍无人判（GOAL `W-2`）；
- 「看到全文」不在射程（GOAL `W-3`）；
- 跨相输入**只支持一层上游产物**（不做传递闭包式的多跳派生 —— 那需要另一轮设计）；
- **报告汇编器**与**沙箱实验**两个执行体不消费声明输入 ⇒ 编译期**点名拒绝**给它们声明
  跨相输入（不静默接受一条「没人读」的来源）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 编译期解析 | **8 passed**（六类非法 + 两类形态） | `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_cross_phase_inputs.py -q` |
| 性质来源 + 按压 | **3 passed**（产出方决定 / 无网络域 ⇒ GENERATED / 摘掉跨相证据 ⇒ 性质维归零） | 同上 |
| e2e 主判据 | **1 passed**：`plan` 的覆盖判词逐字 `n >= m sources; k >= j retrieved` | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_cross_phase_inputs_reach_the_plan_phase.py -q` |
| e2e 按压臂 | **1 passed**：摘掉跨相声明 ⇒ `plan` 判拒且判词点名性质维 | 同上 |
| 离线复现 | run **`SUCCEEDED`**（此前稳定 `FAILED` 于 `EVIDENCE_COVERAGE: 0 < 1 retrieved sources`）；`plan` 提示词 710 字符带三个真标识 | `uv run --frozen --no-sync python -B scratch/_ec04_probe3.py` |
| **live 实跑** | run **`SUCCEEDED`**；`research_report_plan` 的提示词带段；**计划正文引用全部 3 条标识** | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 uv run --frozen --no-sync python -B -m pytest tests/e2e/test_the_model_cites_the_retrieved_identifiers_live.py -q` |
| 读数归档 | `evidence/GOAL-20261016-081-ec04-live-citations.txt`（`CR=0`） | — |
| 受影响套件 | **1399 passed, 1 skipped**（application + integration + architecture） | — |
| 规模门 | **1267 passed** | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q` |
| as-is m0（全部记录写入之后） | **`PASS: profile=m0; 23 deterministic checks`**（24 行 `PASS [`，含计数之外的 `release-assets-immutable`） | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-17 | IN_PROGRESS | cycle 4 建档（跨相输入）。 |
| 2026-10-17 | DONE | 三处阻塞点第三条闭合：`inputs` 支持跨相引用（编译期点名 + 性质由产出方决定 + 门并列接受）；离线与 live 两路都跑到 `SUCCEEDED`，模型引用全部三条标识。 |
