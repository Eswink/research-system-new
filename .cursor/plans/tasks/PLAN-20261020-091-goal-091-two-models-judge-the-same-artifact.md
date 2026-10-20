---
id: PLAN-20261020-091
slug: goal-091-two-models-judge-the-same-artifact
title: GOAL-091 EC-01…06 —— 两个不同模型对同一产物各判一次，判词可归因且分歧可读
status: DONE
created_at: 2026-10-20
updated_at: 2026-10-20
parent_goal: GOAL-20261020-091
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md
memory_entries:
  - MEM-20261020-225
---

# PLAN-20261020-091 — GOAL-091 全六个 EC

## 验收条件

- [x] **EC-01**：`REVIEW_SCORE` 在**真实交付物形态**（信封）下取得到分数；取不到仍 `review score unknown`（fail-closed 逐字不变）。
- [x] **EC-02**：被评对象进评审者提示词的第四段（并列、有界、截断可见、同源）；未声明 ⇒ 提示词逐字不变；非 `REVIEWER` 不挂。
- [x] **EC-03**：成对判据 —— 不同目标 + 同一被评对象、构造分歧 `dissent` 非空、同模型判红、单评审 `panels == []`（全部走 `deps.runs.start_run`）。
- [x] **EC-04**：真跑一次，两位评审模型各落一条可归因判词；判词全文逐字归档。
- [x] **EC-05**：记录 → 记录面判据 → **最后**跑 m0 写见证 → 提交推送 → CI 到终态；阶梯「复检」行同轮升级。
- [x] **EC-06**：`tools/run_m0_with_witness.py --verify-only`（纯读、三态退出码、不写见证）。

## 一、六个 EC 的落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `packages/application/run_orchestration/evaluation_gate.py`（`declared_review_score` + `_unwrap_deliverable`，复用 `declared_object`） | `test_review_score_reads_the_envelope.py`（4） |
| EC-02 | 新 `run_orchestration/review_material.py`（装配器 + `is_reviewer` + `with_review_material`）、`retrieval_prompt.py`（第四段渲染 + `compose_prompt` 参数）、`session_prompts.py`（取值面）、`task_executor.py`（spec 槽 + 接线）、`ports/agent_runtime.py`（`AgentSessionSpec` 字段）、`adapters/openhands/session_builder.py`（拼进 headline）、`dependencies.py` / `phase_runner.py` / `runner_wiring.py`（装配链）、`services/api/review_material_support.py`（组合根闭包）、两个组合根各一行 | `test_review_material_in_prompt.py`（12） |
| EC-03 | 新协议 `examples/protocols/dual_model_review_v1.yaml` + 两份契约（`dual_model_review_plan` / `dual_model_review_deliverable`） | `tests/e2e/test_two_models_judge_the_same_artifact.py`（4） |
| EC-04 | `tests/e2e/test_two_models_judge_the_same_artifact_live.py` + `scratch/goal091-ec04-*.json` | live 判据（1 passed / 门关则如实 skip） |
| EC-05 | 记录 + 正式见证 + CI 台账 | 见证 `terminal_line` + 指纹相等 |
| EC-06 | `tools/run_m0_with_witness.py`（`--verify-only` + `_rows` + `_label`） | `test_m0_witness_matches_the_tree.py`（新增 1 条） |

## 二、执行顺序（本轮实际走的）

1. **建档实测三处缺口**（不是读文档推断）：
   - 信封形态下 `declared_review_score` 恒 `None`（直形态取到 `0.5`、信封取到 `None`）；
   - `compose_prompt` 没有第四个槽位，被评对象只进证据链；
   - GOAL-085/086/087 已把聚合面补齐，但零真分歧。
2. **EC-01**：先加解包（复用 `declared_object`），再补判据与 fail-closed 四态。
3. **EC-02**：装配器 → 渲染器 → 第四个槽位 → 适配器 → 两个组合根，逐层各跑一次回归。
4. **EC-03**：写协议与契约（先确认能编译、两位评审者解析到两个不同目标）→ e2e 四条读数。
5. **EC-04**：真跑。**第一次真跑两位都判负（0.0）且都报告「被评对象段不存在」** —— 顺着读数剥出三处缺陷（见 RECHECK 的「真跑读数」）：
   - 合约措辞 `before this task text` 与实际拼法（追加在后）不符（改措辞）；
   - **既有缺陷**：`SessionBuilder` 提交的是**已渲染的 `str`**，而 `compose_prompt` 按视图对象再渲染 ⇒ 检索段 / 前序段 / 被评对象段**全部被静默丢弃**（真实 run 实测：提示词里 `UNDER REVIEW` 段整个不见）。修法 = `_section_of`：字符串原样用、视图才渲染。
   - 中转站对 `glm-5.3` 的一次瞬时失败（`retry budget exhausted`）⇒ 重跑取证。
6. **EC-06**：`--verify-only` + 三态退出码 + 「不写见证」判据。
7. **收口**：记录 → 记录面判据 → m0（含见证）→ 提交 → CI。

## 三、按压与反证（逐条）

| 项 | 按压 / 反证 | 读数 |
| --- | --- | --- |
| EC-01 fail-closed | 正文无 JSON / 分数非数 / 分数是布尔 / 路径缺失 / 只有 `content` 无 `declared_artifact` | 全部 `None`（4 条判据覆盖） |
| EC-02 零回归 | 未声明跨相输入 / 非 `REVIEWER` / 未接装配器 | `compose_prompt(...) == purpose`；spec **同一对象** |
| EC-03 独立性 | `reviewer_b` 指回 `critic_independent` | `targets == ["main/glm-5.3"]`、`independent is False` |
| EC-03 单评审 | `min_instances: 1` | `panels == []`、`panel_count == 0` |
| EC-06 第三态 | 见证搬到临时目录 | `verify_only() == 2` 且**不创建**见证 |

## 实施清单

1. **WP-A（EC-01 判定面）**：`evaluation_gate._unwrap_deliverable` + `declared_review_score`
   在路径每段解信封（复用 `declared_object`）；`phase_input_material` 的 fail-closed 分支
   修掉格式说明符缺陷。
2. **WP-B（EC-02 装配器）**：新 `review_material.py`（`build_review_material` / `is_reviewer`
   / `with_review_material` / `DEFAULT_MAX_CHARS`）。
3. **WP-C（EC-02 提示词）**：`retrieval_prompt` 第四段 + `_section_of` 缝合线修复；
   `session_prompts.review_material_prompt`；`SessionSpecContext.review_material`；
   `AgentSessionSpec.review_material_prompt`；`session_builder` 拼进 headline。
4. **WP-D（EC-02 装配链）**：`dependencies` / `phase_runner` / `runner_wiring` /
   `services/api/review_material_support.py` / 两个组合根各一行。
5. **WP-E（EC-03 协议与契约）**：`dual_model_review_v1.yaml` + `dual_model_review_plan` /
   `dual_model_review_deliverable`（后者带 `review_panel: COMPLETE_THEN_JUDGE`）。
6. **WP-F（EC-03 判据）**：`test_two_models_judge_the_same_artifact.py`（4）。
7. **WP-G（EC-04 真跑）**：`test_two_models_judge_the_same_artifact_live.py` + 判词全文归档。
8. **WP-H（EC-06 见证）**：`--verify-only` + `_rows` / `_label` + 三态判据。
9. **WP-I（EC-05 收口）**：记录 → 记录面判据 → m0（含见证）→ 提交推送 → CI 到终态。

## 工程记忆

- [MEM-20261020-225](../../memory/entries/MEM-20261020-225-prompt-segments-were-dropped-at-the-handoff-layer.md)
  —— 提示词四段在真实会话里全被静默丢弃：判据测的是渲染器，缺陷在「谁把什么交给谁」。

## 影响报告

- **Domain**：`AcceptanceCriterion` / `Evidence` / `ReviewFinding` **一行未动**；
  `aggregate_panel` / `PanelVerdict` / `review_panel_judging` **一行未动**。
- **Application**：`EvaluationInputs` 无新槽（只改取值面）；`SessionSpecContext` 多一个
  可选槽 `review_material`（缺省 `None` ⇒ 既有行为逐字不变）；新增
  `compose_prompt(review_material=…)` 关键字参数（缺省 `None` ⇒ 逐字不变）。
- **Ports**：`AgentSessionSpec` 多一个可选字段 `review_material_prompt`（缺省 `None`）。
- **API / OpenAPI**：**无路由变化**（本轮不碰 HTTP 面）；`GET /runs/{id}/reviews` 的形态
  未动（`panels` 仍只在 canonical 读面 `review.read` 上）。
- **契约数据（新增，不改既有）**：`dual_model_review_plan` / `dual_model_review_deliverable`
  两份**新**合约；既有合约**一条未改**（只有自己新增那份的措辞在真跑后修正过）。
- **协议数据（新增）**：`dual_model_review_v1.yaml`。
- **安全/凭据**：**无**新放行、**无** deny 例外、**无**凭据面改动；
  `sk-` 零命中（`tools/credential_audit.py` 四面 `offenders=0`）。
- **兼容性**：未声明跨相输入的评审 phase ⇒ 提示词逐字不变；非 `REVIEWER` role ⇒ 不挂；
  直形态交付物的 `REVIEW_SCORE` 逐字不变。
- **上游版本影响**：无新增依赖、无 pin 变更。
- **下一项任务**：阶梯「复检」的 `下一级` 已改为「评审的判词驱动下一轮修订」。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 信封解析 | **4 passed** | `pytest tests/application/run_orchestration/test_review_score_reads_the_envelope.py -q` |
| EC-02 提示词四段 | **12 passed** | `pytest tests/application/run_orchestration/test_review_material_in_prompt.py -q` |
| EC-03 成对判据 | **4 passed** | `pytest tests/e2e/test_two_models_judge_the_same_artifact.py -q` |
| EC-04 真跑 | **1 passed**（门开；门关如实 skip） | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 pytest tests/e2e/test_two_models_judge_the_same_artifact_live.py -q -rs` |
| EC-06 见证三态 | **1 passed**（+ 既有 7） | `pytest tests/tooling/test_m0_witness_matches_the_tree.py -q` |
| 宪章三判据 | **20 passed** | `pytest tests/tooling/test_mainline_*.py -q` |
| 记录面判据 | **28 passed** | `pytest tests/architecture/python/test_reproducibility_wording.py … -q` |
| 凭据审计 | **offenders=0**（四面） | `python -B tools/credential_audit.py` |
| 全量 m0 | 见见证 `terminal_line` | `tools/run_m0_with_witness.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-20 | **IN_PROGRESS** | 承 GOAL-091 建档：判定面（信封）+ 提示词第四段 + 成对判据 + 真跑并行推进。 |
| 2026-10-20 | **DONE** | 六 EC 全达成；真跑取得分歧读数（0.45 判负 / 0.82 判过，`dissent` 非空）；顺带修掉「提示词段在真实会话被静默丢弃」的既有缺陷。 |

## 四、如实边界

- EC-03 用**受控执行体**证明「分歧可表达、可归因、可读、且两位读的是同一件东西」；真实中转站上的分歧由 EC-04 取证。
- EC-04 **不**声称评审判得对；它只判「两位各自跑完、各自落了一条可归因判词」。
- 本轮真跑**确实判出了分歧**（`glm-5.3` REJECT 0.45 / `kimi-k2.6` PASS 0.82），因此**没有**触发「同质化」这条停止条件。
