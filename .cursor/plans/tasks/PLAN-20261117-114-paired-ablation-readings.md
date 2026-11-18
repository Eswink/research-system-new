---
id: PLAN-20261117-114
slug: paired-ablation-readings
title: GOAL-114 子计划 —— 配对消融从「机制」变成「读数」
status: DONE
created_at: 2026-11-17
updated_at: 2026-11-18
parent_goal: GOAL-20261117-114
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261118-114-paired-ablation-readings.md
memory_entries:
  - .cursor/memory/entries/MEM-20261118-244-three-silent-faces-found-by-real-runs.md
---

# PLAN-20261117-114

## 背景与靶子

序 82。勘测实测：GOAL-109 交付的配对消融机制在**真实 run 上根本用不了** ——
`comparison_digest` 比较的 27 个字段里含 `accepted_policy_exceptions`，而其中每条都带
`accepted_at`（冻结那一刻的墙钟）⇒ 同一份装配的两次真实 run 的键**永不相等**。
GOAL-109 的夹具把它设成 `[]`，所以七条 EC 全绿而**零次真实使用**。

## 交付面（checkbox）

- [x] EC-01 `GOAL-113` 补 `## 残余与未覆盖范围` + 读取器能产出骨架；
      `retrieval_context.py` 的过期陈述改正；
      `tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py`（四条含两条反证）
- [x] EC-02 `comparison_digest` 的 `accepted_at` 窄归一化（`NORMALIZED_NESTED_KEYS` 一处声明；
      `EXCLUDED_FIELDS` 仍三元）+ 6 条反证
- [x] EC-03 `frozen_payload` 增 `comparison_digest`（完整 manifest 不落库 ⇒ 事后无从复算）
- [x] EC-04 `ablation_observations.observation_from`（四列 `int`，拒 `bool`，闭集外点名）
- [x] EC-05 `examples/protocols/ablation_plan_probe_v1.yaml`（单相消融台，合约原样复用）
- [x] EC-06 离线两臂（`assemble()` + 真 SQLite）配得起来 + 观测过门
- [x] EC-07 真实 k=3 × 2 臂六次 run（全 `SUCCEEDED`、六条可比键逐字相同、三列位移）
      + 证据 JSON
- [x] EC-08 阶梯「计划」行 `当前级` 追加描述性读数、`下一级` 逐字不动
- [x] EC-09 程序表序 82 + 两表各 3 行 + 归档 + GOAL-113 tip CI 回填
- [x] EC-10 收口资产 + `_VERIFIERS` + 工具射程登记

## 实施清单

1. **可比键**：`packages/application/run_orchestration/comparison_digest.py`
   —— `_strip_nested` 只剥 `accepted_policy_exceptions[*].accepted_at`；形态保持
   （仍是映射的列表，顺序不变）；畸形条目原样返回（留给 `digest_of` 去拒）。
2. **冻结快照**：`eventing.frozen_payload` 现算 `comparison_digest(manifest).digest`。
3. **观测映射**：`ablation_observations.py` —— 三态 → 四列，`int(...)` 而非 bool。
4. **消融台协议**：`examples/protocols/ablation_plan_probe_v1.yaml` —— 相 id 取
   `retrieval`（出厂检索面瞄准的那个），能力集与 `research_report_chain_v1` 的 plan 相相等。
5. **真跑**：`tests/e2e/test_paired_ablation_on_the_plan_live.py`（P/A 交替预先声明、
   每 run 一个全新库、失败也登记）。

## 真跑抓到的缺陷（各有判据）

1. `TOOL_HEALTH_UNPROVEN` 没有接受通道 ⇒ 拒冻且**不落事件**（读面表现为「秒失败无原因」）。
2. 相 id 与出厂面不匹配 ⇒ `planned_in_this_phase` 静默跳过 ⇒ 失败归因错位。
3. `assemble()` 不传 `agent_runtime` ⇒ 回落 Fake 执行体 ⇒ 交付物名恒缺。
4. **判据缺陷**：`citation_count` 缺分母恒 0（不可能判红）⇒ 已修并按同一批产物字节重算。

## 验证

- 定向：`tests/application/run_orchestration/test_{comparison_digest,ablation_observations,
  frozen_payload_semantic_digest}.py`、`tests/contracts/test_ablation_plan_probe_protocol.py`、
  `tests/e2e/test_paired_ablation_offline_arms.py`、`tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py`
- live：`tests/e2e/test_paired_ablation_on_the_plan_live.py`（六次真实 run）
- 记录面：`tools/verify_goal114_closeout.py`（80 判词 0 FAIL）
- 全量 m0 + 两树复检 + CI 八 job

## 结果

见 `RECHECK-20261118-114`（`PASS_WITH_WARNINGS`）。四列读数：

| 列 | present | absent | 位移 |
| --- | --- | --- | --- |
| `design_block` | 1.0 | 1.0 | 0.0 |
| `arm_count` | 2.0 | 2.3333 | −0.3333 |
| `parameter_count` | 6.0 | 7.0 | −1.0 |
| `citation_count` | 1.0 | 0.0 | +1.0 |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | EC-02 | test | `tests/application/run_orchestration/test_comparison_digest.py` | 24 passed |
| EV-02 | EC-03 | test | `tests/application/run_orchestration/test_frozen_payload_semantic_digest.py` | 含三条新判据 |
| EV-03 | EC-04 | test | `tests/application/run_orchestration/test_ablation_observations.py` | 9 passed |
| EV-04 | EC-05 | test | `tests/contracts/test_ablation_plan_probe_protocol.py` | 6 passed |
| EV-05 | EC-06 | test | `tests/e2e/test_paired_ablation_offline_arms.py` | 5 passed |
| EV-06 | EC-07 | live | `tests/e2e/test_paired_ablation_on_the_plan_live.py` | 六次 run 全 SUCCEEDED（26m29s） |
| EV-07 | EC-07 | evidence | `.cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json` | 六条可比键逐字相同、三列位移 |
| EV-08 | EC-01 | test | `tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py` | 4 passed |
| EV-09 | EC-10 | verifier | `tools/verify_goal114_closeout.py` | 80 判词 0 FAIL |

## 验收条件

- 十条 EC 全部 PASS；
- 六次真实 run 的 `comparison_digest` 逐字相同且语料门 `sufficient=true`；
- 阶梯「计划」行 `下一级` 逐字未动（bar 不升）；
- 全量 m0 witness 绿 + 两树复检 sha256 相同 + CI 八 job 全绿。

## 状态历史

- 2026-11-17：建档（charter 由 `next_round_charter.py` 从 GOAL-113 读出）。
- 2026-11-18：EC-01…06 落地；真跑抓到三个实现缺陷 + 一个判据缺陷并修复；
  EC-07 六次真实 run 全部 SUCCEEDED；EC-08/09/10 落地；复检 `PASS_WITH_WARNINGS`。

## 影响报告

- **Domain/API/schema**：`comparison_digest` 增一个**嵌套归一化面**
  （`NORMALIZED_NESTED_KEYS`，只剥 `accepted_at`）；`manifest.frozen` 事件 payload 增
  `comparison_digest` 键；新件 `ablation_observations.observation_from`；新增出厂协议
  `ablation_plan_probe_v1.yaml`。**`EXCLUDED_FIELDS` 逐字不变**，既有 run 的 digest 计算
  除例外表外逐字节不变。
- **安全/凭据**：无新凭据面；live 判据的凭据仍只从环境读、只注册进本次装配的解析器
  （离线判据用常量占位串，明确标注「不是可用凭据」）。
- **兼容性/迁移**：详见 RECHECK「残余 / 未覆盖 / 声称边界」一节。
- **上游版本影响**：无（未改依赖 pin）。
