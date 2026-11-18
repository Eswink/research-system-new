---
id: RECHECK-20261118-114
slug: paired-ablation-readings
title: GOAL-114 复检 —— 配对消融从「机制」变成「读数」
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-18
updated_at: 2026-11-18
plan_id: PLAN-20261117-114
parent_goal: GOAL-20261117-114
owners:
  - root-agent
verify_paths:
  - packages/application/run_orchestration/comparison_digest.py
  - packages/application/run_orchestration/eventing.py
  - packages/application/run_orchestration/ablation_observations.py
  - examples/protocols/ablation_plan_probe_v1.yaml
  - tests/e2e/test_paired_ablation_offline_arms.py
  - tests/e2e/test_paired_ablation_on_the_plan_live.py
  - .cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json
  - tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py
---

# RECHECK-20261118-114

## 复检范围

GOAL-20261117-114 的十条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

- **只测「计划」一格**：检索 / 复检 / 迭代三格的能力阶梯 `下一级` **逐字未动**。
- **bar 未升**：阶梯「计划」行的 `下一级` 与 GOAL-109 收口时**逐字相同**；本轮只在
  `当前级` 追加**描述性**读数（用户 2026-11-17 拍板）。
- **n=3 是标定下界**，不是统计功效；全仓无采样控制（无 `temperature` / 无 `seed`）。

## 检查结果

### EC-01 上一轮的残余真的可读

- `GOAL-20261114-113` 补了 `## 残余与未覆盖范围`（`W-1` + `U-1`/`U-2`/`U-3`）；
- `tools/next_round_charter.py --root . --goal <GOAL-113> --next-goal-id GOAL-20261117-114`
  **确实产出非空骨架**（「二、」节逐条原文 + 「三、」阶梯 + 「四、」CI 读数 + 骨架）；
- 新判据 `tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py` 四条全绿：
  可读 / 条目不丢 / **节缺席 ⇒ `RESIDUAL_SECTION_MISSING`** / **断号 ⇒ `RESIDUAL_GAP`**。
- `retrieval_context.py` 的过期陈述（「全仓零构造点」）已改为如实描述并点名构造点位置。

### EC-02 可比键在真实路径可用

- `NORMALIZED_NESTED_KEYS == (("accepted_policy_exceptions", "accepted_at"),)` —— **显式声明一处**；
- `EXCLUDED_FIELDS` 仍 `{"run_id","frozen_at","project_id"}`（`goal109` 的 27 条断言零 FAIL，
  证明剔除面**没有被改宽**）；
- 6 条反证逐条判红：空/非空表、capability、provider、constraints、decision、**顺序**。

### EC-03 冻结快照携带可比键

- `frozen_payload` 带 `comparison_digest`；三个 digest **不是别名**：
  身份字段不同的两份 manifest ⇒ `digest` 与 `semantic_digest` 都不等、**只有可比键相等**；
  语义漂移 ⇒ 可比键也变。

### EC-04 读数 → 观测

- 四列 `type(...) is int`（`bool` 被消融门显式拒绝）；
- 三态逐格钉死（`block_present`/`arms_absent` = 1/0/0；`block_absent` = 0/0/0）；
- 闭集外 `source_state` ⇒ `AblationObservationError` 点名；
- 闭环：观测直接喂 `tools/ablation_report.build_report` ⇒ 门接受、四列渲染。

### EC-05 消融台协议

- 单相、相 id = `retrieval`（**等于** `retrieval_wiring.RETRIEVAL_PHASE`）、合约逐字
  `research_report_plan`、能力集与 `research_report_chain_v1` 的 plan 相**集合相等**；
- 不声明会话工具绑定（`run_chain` ⇒ 会话工具面为空）；
- 两条协议都能 `compile_protocol` 给出 `plan`。

### EC-06 离线两臂（真实装配）

- `assemble()` 上两臂都 `SUCCEEDED`；**两 run 的 `comparison_digest` 相等**；
- 各得四列 `int` 观测；一对观测复制成 k=3 后过门。

### EC-07 真实 k=3 × 2 臂

- **六次 run 全部 `SUCCEEDED`**（墙钟 196.4–306.7 秒，合计 26 分 29 秒）；
- **六条 `comparison_digest` 逐字相同**（`sha256:57a7b1a3…`）—— 这是 EC-02 在真控制面上的证据；
- 语料门：`sufficient=true, pairs=3`；
- 四列位移（n=3 两臂均值）：

  | 列 | present | absent | 位移 |
  | --- | --- | --- | --- |
  | `design_block` | 1.0 | 1.0 | 0.0（不动） |
  | `arm_count` | 2.0 | 2.3333 | −0.3333 |
  | `parameter_count` | 6.0 | 7.0 | −1.0 |
  | `citation_count` | 1.0 | 0.0 | +1.0 |

- **两臂的记忆面确实只差那一行**（逐库核对：present 三库各有 `mem-ablation-live-prior`，
  absent 三库全空）。

### EC-08 阶梯

- 「计划」行 `下一级` **逐字未动**（三条锚点全在）；`当前级` 追加描述性读数；
- `tests/tooling/test_goal109_ladder_pilot_scope.py` 四条仍绿 + `goal109` 27 条断言零 FAIL；
- 其余六行不含本轮读数锚（未越级推广）。

### EC-09 记账

- 程序表序 82 行在场（六格，依赖 `序 77、81`）；
- 两表各 3 行；各移出最旧 1 行到 `archive/MAINLINE-2026-11-18-{progress-111,revisions-79}-only.md`；
- 归档后 **14 个历史验证器零 FAIL**（`verify_goal100…113`）；
- GOAL-113 的 tip CI 读数已回填（`65a2de65`：M0 8/8、Push 3/3 全 `success`）。

### EC-10 收口资产

- `tools/verify_goal114_closeout.py` + `tools/goal114_closeout_assertions.py`；
- 登记进 `_VERIFIERS`（`test_closeout_verifiers_run_their_own_assertions.py:176`）；
- 自指判据绿（加载的是自己那份断言集）。

## 真跑抓到的三个实现缺陷（只有真跑才暴露）

1. **`TOOL_HEALTH_UNPROVEN` 没有接受通道** ⇒ `freeze_manifest` 拒冻，而拒冻抛出后控制面
   **不落任何事件** ⇒ 读面表现为「六次 run 在 0.4–0.7 秒内秒失败而读不到原因」。
   处置：走既有 live 判据同一条显式运维上下文路径。
2. **相 id 必须与出厂检索面瞄准的那个一致**：取名成 `plan` ⇒ `planned_in_this_phase`
   静默跳过 ⇒ 失败归因落在合约的 `minimum_retrieved_sources` 上（错位）。
3. **`assemble(ApiSettings(...))` 不传 `agent_runtime` ⇒ 回落 Fake 执行体**：Fake 只发
   `analysis_report` ⇒ 探针的 `research_plan` 恒缺 ⇒ 验收门判拒。

## 判据缺陷（真跑抓到，已修并重算）

**`citation_count` 首轮两臂全 0** —— 不是模型没引用（`present` 臂的计划正文逐字写着
`mem-ablation-live-prior`），而是读数调用没给 `known_memory_ids` 分母 ⇒ 该列**结构上
恒为 0**，即一条**不可能判红**的判据。修法：分母按**臂的持久事实**给
（`present` ⇒ 那条 id；`absent` ⇒ 空集），并用**同一批已落库的产物字节**重算
（六次 run 都已 SUCCEEDED，模型输出不受判据缺陷影响；重跑只会换六份新随机输出、
丢掉那次真跑的读数）。新增两条判据：`test_the_run_arm_supplies_a_citation_denominator`、
`test_the_evidence_records_the_recompute`。

## 残余 / 未覆盖 / 声称边界

- **`W-1` 采集器仍是「判据侧驱动」**：`tests/e2e/paired_ablation_live_support.py` 把六次 run
  汇总成观测，**产品面没有一个「从 run 库自动汇总 k×2」的命令**（GOAL-109 `W-2` 的
  那一半仍未交付）。本轮把它推到了「可用」，不是「可运维」。
- **`W-2` `plan_fallback` 仍是未被接线的死缝**：`packages/application/model_relay/fallback.py`
  有实现、`ModelProfile.fallback` 被 preflight 的独立性判据读，但**运行期没有任何时候真的
  按 fallback 切模型**（`adapters/relay/gateway.py` 只有 circuit breaker + retry）。
  它牵涉评审独立性判据的穷举结论 ⇒ 接线要重算那些结论，属另一件事。**本轮只登记不修**。
- **`U-1` 只测「计划」一格**：检索 / 复检 / 迭代三格的 `下一级` 仍无真实读数（机制同构，
  但一格的证据不足以推广）。
- **`U-2` n=3 不是统计功效**：无显著性检验、无方差刻画、无采样控制 ⇒ 只能读「分布位移」，
  不能读「位移的因果方向」。
- **`R-1` 不宣称「模型采纳了前序知识」**：判的是四列**读数**的分布位移，正文里那句
  `mem-ablation-live-prior` 是 **`citation_count` 的证据**，不是「采纳」的证据
  （「采纳」仍被 GOAL-082 EC-04 的未决取舍挡着）。
- **`R-2` 不宣称消融台是生产协议**：产品面今天不认 `ablation_plan_probe_v1.yaml`
  （检索调用表由装配方给出 —— 产品那份的检索词路径是 `research_question.query`，
  单相简报驱动的探针没有那个字段）。

## 结论

`result: PASS_WITH_WARNINGS`。十条 EC 全 PASS；两条 `W` 与四条 `U/R` 如实登记为
**未覆盖**，其中 `W-1`（采集器产品化）与 `U-1`（其余三格）是下一轮最直接的续点。
本轮的核心事实是三条：**真实路径上六次 run 的可比键逐字相同**（GOAL-109 交付的机制
第一次真的可用）、**`citation_count` 位移 +1.0**（修掉分母缺陷后）、
**bar 未升**（n=3 的描述性读数不构成「分布位移」这一世界断言的达成）。
