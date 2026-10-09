---
id: PLAN-20261009-365
slug: goal-042-ec01-03-memory-consumption-on-the-run-path
title: GOAL-20261009-042 cycle 1（EC-01/EC-02/EC-03）：记忆的时效**被消费** —— 读能力承接 + 三态处置可判定
status: IN_PROGRESS
created_at: 2026-10-09
updated_at: 2026-10-09
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-366-goal-042-ec03-04-memory-consumption-on-the-run-path.md
memory_entries: []
parent_goal: GOAL-20261009-042
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261009-042 的 **EC-01 / EC-02 / EC-03**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：判定**不读挂钟**（时点由调用方给）；
    三态**互不混用**；**跳过必须点名**（禁静默丢弃）；未声明时效 ⇒ **不猜**（逐字保持既有
    行为）；只增**一条只读**能力（承 GOAL-036/037 的五件套手法）；**改既有判据必须走自证清单**
    （`MEM-20261009-210`）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字
    （**明确否认**）。
objective: >-
    ① **勘察定稿**（已有三条读数，本 PLAN 再补「落点选择」的复核）；② **承接与判定**：
    新增**一条只读**能力（建议 `memory.read`，与既有 `*.read` 命名面同族）**五件套齐**
    —— 目录声明（`examples/config/capabilities.yaml` + `tool_providers.yaml` + `skills.yaml`）
    + provider 实现在**新模块**（`adapters/canonical/memory_read.py`；`read_provider.py` 已
    **433/450 行**，不再加实现体）+ 工具/能力映射（`_TOOL_CAPABILITIES`）+ **两组合根接线**
    （`register_session_tools`）+ **一条只读 allow**（`examples/config/policy.yaml`）；
    读面按**调用方给的时点**逐条给 `validity` 与**处置**；③ **真的影响行为**：研究循环
    **至少一条**路径按该读面改变行为（到期/待复核的记忆**被跳过或被标注**，两者互不混用且
    逐条点名；未声明时效 ⇒ 逐字保持既有行为）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（落点复核）**：`read_provider.py` 行数（**433**，上限 450）⇒ 新实现**必须**
      独立成模块；`_TOOL_CAPABILITIES` 映射位置与两组合根接线点逐条落位；
      `validity_at` 的签名（纯函数 / 不读挂钟）与 `MemoryRecord` 的时效字段逐字确认。
    verify: >-
      `wc -l adapters/canonical/read_provider.py`；`rg -n "_TOOL_CAPABILITIES" adapters/canonical/`；
      `rg -n "register_session_tools" services/`。
    status: PENDING
  - id: AC-2
    criterion: >-
      **承接五件套齐**（声明 + 实现 + 映射 + 两组合根 + 一条只读 allow）；缺任一件 ⇒
      preflight **点名**（不静默降级）。读面载荷：逐条记忆给 `memory_id` / `tier` / `scope` /
      `content`（或 digest）/ `validity`（三态之一或 `None`）/ **处置**（照用 / 标注 / 跳过）
      + **理由**；**不读挂钟**（`now` 由调用方给 ⇒ 同记录同时点判定相同）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters tests/api -q`
      ⇒ 全绿 + 新用例（三态逐条 + 可复现性）。
    status: PENDING
  - id: AC-3
    criterion: >-
      **真的影响行为**：研究循环的**一条**具名路径按该读面改变行为；三态与处置**互不混用**：
      `EXPIRED` ⇒ 跳过（**点名**该 id 与状态）/ `REVIEW_DUE` ⇒ 标注（**点名**）/ `None` ⇒
      照用（**不**增加任何标记）；**未声明时效 ⇒ 逐字保持**既有行为。
    verify: >-
      该路径的判据用例（三态 × 声明面）逐条；缺省面对拍既有行为。
    status: PENDING
---

# PLAN-20261009-365 — GOAL-20261009-042 cycle 1

> **主线归属**：`GOAL-20261009-042`（MAINLINE 程序表**序 10**）的 EC-01/EC-02/EC-03。
> **状态：IN_PROGRESS** —— 建档与勘察已在 GOAL 的 cycle 0 完成（三条实测读数），
> 本 PLAN 承载**实现面**；下一次触发从「实施清单」的未勾选项继续。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（落点复核：新模块 / 映射 / 两组合根） | PENDING |
| AC-2 | 承接五件套齐 + 读面三态与处置可判定（不读挂钟） | PENDING |
| AC-3 | 真的影响行为（跳过 vs 标注互不混用 + 未声明逐字不变） | PENDING |

## 实施清单

- [ ] WP-1 勘察复核：`read_provider.py` 行数 / `_TOOL_CAPABILITIES` / 两组合根接线点
- [ ] WP-2 目录声明：`examples/config/capabilities.yaml` +1 条只读能力；
      `examples/config/tool_providers.yaml` 的 `m12_artifact`（或同族 provider）挂上它；
      `examples/config/skills.yaml` 的**一个** role 挂上它（按研究循环真的用到的口径）
- [ ] WP-3 实现：新模块 `adapters/canonical/memory_read.py`（读 `MemoryStore.query()` +
      `validity_at(record, now)`；`now` 由**调用方**给）+ `read_provider.py` 只加**转发**
- [ ] WP-4 映射 + 两组合根：`_TOOL_CAPABILITIES` +1；`register_session_tools`（两组合根）
- [ ] WP-5 策略：`examples/config/policy.yaml` **只增一条**只读 allow
- [ ] WP-6 行为影响：研究循环的具名路径（`phase_capabilities.py` 的调用声明）按读面分派
      （到期 ⇒ 跳过并点名 / 待复核 ⇒ 标注并点名 / 未声明 ⇒ 照用）
- [ ] WP-7 判据：驱动 / e2e（两时点可区分 + 三条反证：未声明不跳、不静默丢弃、未放行点名）
- [ ] WP-8 两向反证 + 记录 + 门 + CI + 台账

## 证据

**周期 0 已取的三条读数**（见 `GOAL-20261009-042` 的「事实层结论」节）：

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | `memory.read` 不在能力目录 | `rg -n "memory.read" examples/config/capabilities.yaml` ⇒ 零命中 |
| 2 | 研究循环零引用 memory | `rg -n "memory" packages/application/run_orchestration/phase_capabilities.py` ⇒ 零命中 |
| 3 | `validity_at` 只到 REST 读面 | `rg -ln "validity_at" packages services adapters --glob '*.py'` ⇒ 2 处（定义 + 读面） |

## 影响报告

- **Domain / API / schema 变化**：**待 cycle 1 定**（预期：能力目录 +1 只读；**无**迁移 ——
  判定输入全部在既有 canonical 字段上）。
- **安全 / 凭据变化**：**只增一条只读 allow**（不放行任何写 / 执行 / 审批面）。
- **兼容性 / 迁移风险**：预期**低**（新增能力 + 新增读面；未声明时效的既有行为逐字保持）。
- **上游版本影响**：无。
- **下一项任务**：cycle 1 实现面（本 PLAN 的实施清单）。

## 无可复用事实

**待定** —— 本 PLAN 收口时按实际发现回填。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | IN_PROGRESS | 建档（derive）：本 PLAN 承载实现面；AC-1…AC-3 全 PENDING；实施清单 WP-1…WP-8 待执行。周期 0 的三条实测读数已在 GOAL-042 的「事实层结论」节逐条留档。 |
