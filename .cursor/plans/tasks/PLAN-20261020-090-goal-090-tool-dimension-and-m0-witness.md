---
id: PLAN-20261020-090
slug: goal-090-tool-dimension-and-m0-witness
title: GOAL-090 EC-01…05 —— 覆盖门工具维（堵 W-6）+ m0 见证把顺序纪律变成机器事实
status: DONE
created_at: 2026-10-20
updated_at: 2026-10-20
parent_goal: GOAL-20261020-090
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261020-090-goal-090-tool-dimension-and-m0-witness.md
memory_entries:
  - MEM-20261020-224
---

# PLAN-20261020-090 — GOAL-090 全五个 EC

## 验收条件

- [x] **EC-01**：`minimum_tool_evidences` 三维正交；未声明 ⇒ 判词逐字不变；声明而未给计数 ⇒ fail-closed 点名；负值构造期拒绝。
- [x] **EC-02**：两向按压在**真文件**上判红（合约摘维 / 计数恒零），raw `sha256` 逐字节复原并复绿。
- [x] **EC-03**：出厂 `research_question_retrieval` 升 `1.1.0` 并声明 `minimum_tool_evidences: 1`；判据读**产品数据文件**。
- [x] **EC-04**：见证三态语义成立；自我指涉边界经实测修掉；按压改一个受判字节 ⇒ 判红并点名两版 `sha256`。
- [x] **EC-05**：记录写完 → 记录面判据 → **最后**跑 m0 写正式见证 → 提交推送 → CI 到终态。

## 一、五个 EC 的落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `packages/domain/tasks.py`（可选字段 + 负值拒绝）、`packages/domain/acceptance.py`（三维求值）、`adapters/contracts/tasks_loaders.py`（解析）、`schemas/task-contract.schema.json`（登记）、`evaluation_gate.py`（`EvaluationInputs` 槽 + 透传）、`result_handler.py`（`count_tool_evidences`）、`task_phase_helpers.py`（接线） | `test_evidence_coverage_tool_dimension.py`（10） |
| EC-02 | 按压脚本（二进制读写 + `sha256` 留档） | 同上，两向各判红 |
| EC-03 | `examples/contracts/task_contracts.yaml` 的 `research_question_retrieval` 1.0.0 → 1.1.0 | `test_the_shipped_retrieval_contract_declares_the_dimension` |
| EC-04 | `tools/run_m0_with_witness.py`（指纹 + 见证 + `SELF_REFERENTIAL`）、`tests/tooling/test_m0_witness_matches_the_tree.py`（5） | 同左 |
| EC-05 | 记录 + 正式见证 + CI 台账 | 见证 `terminal_line` + 指纹相等 |

## 二、执行顺序（本轮实际走的）

1. **勘察判定面**：`retrieved_source_count` 从哪来、跨相证据怎么登记、`count_retrieved_sources` 的计数口径 —— 确认 `W-6` 的链条完整（不是理论推断）。
2. **EC-01 域与求值**：先加字段与三维求值，再加载器/schema，最后门接线（一次成型，改动点少）。
3. **EC-03 合约**：升版并声明。**为什么先做合约**：没有受判对象，EC-01 的判据是空真。
4. **EC-01 判据 10 条**：含「W-6 形态能过前两维」这条**先钉住缺口存在**的判据，和「`tool_refs` 是可判别依据」这条**钉住判据赖以成立的结构事实**的判据。
5. **EC-02 两向按压**：合约摘维、计数恒零。两次都先 `read_bytes` 备份，复原后验 `sha256` 一致。
6. **EC-04 见证**：先写工具，再写判据，然后**按压**（改 `schemas/` 一个字节）。按压立刻抓出**自我指涉缺陷**（见下）。
7. **EC-05 收口**：记录写完 → 记录面判据 → **最后**跑 m0。

## 实施清单

1. **WP-A（域与求值）**：`AcceptanceCriterion.minimum_tool_evidences`（可选 + 负值拒绝）
   → `CriterionInputs.tool_evidence_count` → `_evaluate_evidence_coverage` 三维正交。
2. **WP-B（加载与登记）**：`tasks_loaders` 解析 + `task-contract.schema.json` 登记。
3. **WP-C（门接线）**：`EvaluationInputs` 槽 + 透传；`count_tool_evidences` + `task_phase_helpers` 接线。
4. **WP-D（合约）**：`research_question_retrieval` 1.0.0 → 1.1.0 并声明新维。
5. **WP-E（判据）**：`test_evidence_coverage_tool_dimension.py`（10）。
6. **WP-F（m0 见证）**：`tools/run_m0_with_witness.py`（指纹 + 见证 + 自我指涉白名单）
   + `tests/tooling/test_m0_witness_matches_the_tree.py`（5）。
7. **WP-G（收口）**：记录 → 记录面判据 → 最后跑 m0 写正式见证 → 提交推送 → CI。

## 三、本轮遇到并修掉的两处缺陷

1. **见证自我指涉**（判据抓到）：初版把 `.cursor/` 整体算进受判面，而见证落在
   `.cursor/plans/goals/evidence/` ⇒ 写见证改变它所描述的树 ⇒ 立刻自我失效。
   修法 = `SELF_REFERENTIAL` 白名单。**这条正是「受判面要问一个只能由真实发生来回答的
   问题」的副产品**：描述者不能同时被描述。
2. **`--skip-run` 的见证没有终态行**（判据抓到）：`test_the_witness_records_a_terminal_line`
   判红并点名「runner 没有跑到终态 ⇒ 不能作为覆盖证据」。**保留该行为** —— 它正是
   「跑过 ≠ 跑完了」的机械表达；正式见证必须来自一次真实全量运行。

## 四、真实执行顺序（与 m0 顺序纪律一致）

```text
① 写全部记录（GOAL / PLAN / RECHECK / 阶梯 / 程序表 / 进展记录）
② 记录面判据（tests/architecture/python + tests/tooling）
③ 最后：tools/run_m0_with_witness.py 跑全量 m0 并写正式见证
④ 之后不再改任何受判文件
⑤ 提交 + 推送 + CI 到终态
```

**为什么②必须在③之前、③之后不能再改树**：m0 的见证绑定「跑门那一刻的树」。
第①步每多一次记录提交，前一次见证就失效一次 —— GOAL-089 为此多跑了三次全量 m0
（约 48 分钟独占）。本轮把顺序**当成受判对象**来走，而不是当成提醒。

## 工程记忆

已落库：`.cursor/memory/entries/MEM-20261020-224-a-witness-must-not-describe-itself.md`。

**一条可复用事实**（「散文咬不住顺序纪律，要给它装证据面」）：当一条纪律的失效形态是
「上一次的证据因为**后续动作**而失效」时，靠写规范条文没用 —— 失效发生在**条文之外**
（GOAL-089 为此多跑三次全量 m0）。正确形态是让动作本身**留下可重算的见证**，并让判据
重算当前状态与见证比对：`tools/run_m0_with_witness.py` 记 HEAD + 受判面脏文件 + `sha256`，
判据重算。**必须同时处理自我指涉**：见证文件不能落在它自己描述的受判面里，否则写见证
这个动作立刻让它失效（本轮实测）。三态语义（没跑过 / 指纹不等 / 覆盖成立）也必须
**分得开** —— 把「没跑过」读成「覆盖当前树」是这一类判据最容易犯的错。

## 影响报告

- **Domain**：`AcceptanceCriterion` 新增**可选** `minimum_tool_evidences`（缺省 `None`
  ⇒ 既有合约逐字不变）；`CriterionInputs` 新增 `tool_evidence_count`。**无破坏性迁移**
  （contract 数据是可选的 YAML 字段，旧文件不写即不启用）。
- **Domain（求值器）**：`_evaluate_evidence_coverage` 由两维扩到三维；**未声明第三维时
  判词逐字不变**（有判据钉住）。
- **API / OpenAPI**：无路由变化（本 GOAL 不碰 HTTP 面）。
- **Application**：验收门多一个输入槽；`count_tool_evidences` 是纯函数。
- **契约数据**：`research_question_retrieval` 1.0.0 → 1.1.0（判据**变严**）。
- **安全/凭据**：**无**新放行、**无** deny 例外、**无**凭据面改动；
  `sk-` 零命中（`tools/credential_audit.py` 四面 `offenders=0`）。
- **兼容性**：未声明 `minimum_tool_evidences` 的合约行为逐字不变；本仓仅检索格声明。
- **上游版本影响**：无新增依赖、无 pin 变更。
- **下一项任务**：`A`（改 `TrustLabel` 语义 = 通用修复）需用户拍板；`报告由模型撰写`
  与 `评审真的用不同模型判出负` 仍在阶梯 `下一级` 栏。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01/EC-02/EC-03 工具维 | **10 passed** | `pytest tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py -q` |
| EC-04 m0 见证 | **5 passed** | `pytest tests/tooling/test_m0_witness_matches_the_tree.py -q` |
| 零回归 | **1270 passed / 72 skipped** | `pytest tests/application/run_orchestration tests/domain tests/contracts -q` |
| 宪章三判据 | **20 passed** | `pytest tests/tooling/test_mainline_* -q` |
| 凭据审计 | **offenders=0**（四面） | `python -B tools/credential_audit.py` |
| 全量 m0 | 见见证 `terminal_line` | `tools/run_m0_with_witness.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-20 | **IN_PROGRESS** | 承 GOAL-090 建档：工具维 + m0 见证并行推进。 |
| 2026-10-20 | **DONE** | 五 EC 全达成；两向按压判红并逐字节复原；见证三态成立；零回归 1270 passed。 |
