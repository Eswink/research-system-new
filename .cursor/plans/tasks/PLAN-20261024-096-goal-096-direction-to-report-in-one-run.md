---
id: PLAN-20261024-096
slug: goal-096-direction-to-report-in-one-run
title: GOAL-096 全五个 EC —— 六相科研链 + 报告站在本 run 自己的问题上
status: DONE
created_at: 2026-10-24
updated_at: 2026-10-25
parent_goal: GOAL-20261024-096
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261024-096-goal-096-direction-to-report-in-one-run.md
memory_entries:
  - MEM-20261024-230
---

# PLAN-20261024-096 — 六相科研链 + 报告站在本 run 自己的问题上

- **GOAL**: `GOAL-20261024-096`（序 64）
- **状态**: DONE
- **能力域**: 报告

## 一句话

新建 `examples/protocols/direction_to_report_v1.yaml`（question → retrieval → plan →
experiment → review → report），让一次 run 走完「方向 → 问题 → 检索 → 立题 → 实验 →
评审 → 报告」；同轮让报告第 1 节从**本 run 自己**的 `research_question` 制品读出正文
（此前 `objective=None` 写死 ⇒ 该节恒空），并补上收口验证器这件固定交付。

## 为什么本轮是必要的（建档实测）

| # | 缺口 | 实测读数 |
| --- | --- | --- |
| 1 | **链断成两截** | 23 份协议里**没有一份**同时含 `question` 与 `experiment` 相：`direction_to_question_v1` 止于 `retrieval_report`；`research_report_chain_v1` 从手写 `input-brief:real_research_v1` 起步 ⇒ **没有一次 run 走过完整链** |
| 2 | **报告第 1 节恒空** | `report_facts.report_inputs` 把 `objective=None` / `budget=None` 写死 ⇒ 第 1 节永远是「_（无：本 run 未声明目标）_」 |
| 3 | **收口验证器靠人记** | `tools/verify_goal{076,090,095}_closeout.py` **从未存在**，而分类判据只查「磁盘上存在的验证器是否被分类」⇒ 缺失文件**两头都不报**（不在 `_VERIFIERS` 不被看，也不在 `LEGACY_INLINE` 不被问） |

## 交付面（逐条对 EC）

### EC-01｜协议与结构

- `examples/protocols/direction_to_report_v1.yaml`：六相，依赖链
  `retrieval←question` / `plan←retrieval` / `experiment←plan` / `review←experiment` /
  `report←{plan,experiment,review}`。
- **C-1**：`experiment` 与 `report` 两相**不声明**跨相 `inputs` ——
  `protocol_compile/cross_phase_inputs._executor_consumes_declared_inputs` 对
  「合约声明了 `report` / `experiment`」返回 `False`。实验设计只走装配面
  `design_source="plan"`；报告只走 `report_facts`。
- **C-2**：两份既有协议**一字节未改**（`test_direction_to_question_protocol.py`
  与 `test_research_report_arc_offline.py` 的相集断言仍绿）。
- **C-3/C-4**：id `direction_to_report_v1_0_0` 合 schema 正则；只用既有能力名
  （`artifact.read` / `literature.search` / `literature.read` / `workspace.read` /
  `evidence.read`），词表与 policy 差集判据零改动。
- 判据：`tests/contracts/test_direction_to_report_protocol.py`（5 例）。

### EC-02｜跨相边两向可判

- (i) 改 `question` 产出 ⇒ `retrieval` 实际发给 provider 的 query 随之变：
  - 机制层：`tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py`
    （`queries == [query]`，两个变体各自等于自己的产出）；
  - 编排层：`tests/e2e/test_direction_to_report_arc_offline.py`
    （provider 传输层的 `offline.requests[0]`）。
- (ii) 改 `retrieval` 产出 ⇒ `plan` 的提示词材料随之变：同 e2e 的
  `test_changing_the_retrieval_output_changes_the_plan_prompt_material`
  （读 `spec.retrieval_prompt` —— 会话创建点拼进提示词的**同一份字节**）。
- (iii) 反证：摘掉 `question` ⇒ **编译期** `CROSS_PHASE_INPUT_INVALID`
  （`test_removing_the_question_phase_fails_at_compile_time`），不是运行期静默用默认值。

### EC-03｜报告第 1 节来自本 run 自己的问题

- 新模块 `packages/application/run_orchestration/report_question.py`
  （`report_task.py` 433/450、`report_facts.py` 260 ⇒ 不压缩既有注释换行数）。
- `report_facts.report_inputs` 改为 `objective=question_objective(artifacts, evidence)`：
  从**本 run 证据投影**里找 `:research_question` 制品（零/多条都点名），
  信封形态取模型声明块的**原文切片**、直形态取制品原文。
- 两处渲染器口径同步：`research_report._header_lines` / `_question_section` 与
  `report_narrative` 的抬头，从「目标（来自协议/合约声明）」改成
  「研究问题（本 run 自提；逐字引用）」—— 旧文案在接通后会变成假话。
- 判据：`tests/application/run_orchestration/test_report_question_objective.py`（6 例：
  两种形态逐字、改制品 ⇒ 改报告、无制品 ⇒ 点名「本 run 没有 research_question 制品」、
  解不出 ⇒ 抛错、两制品 ⇒ 歧义）。

### EC-04｜真跑六相

判据 `tests/e2e/test_direction_to_report_live.py`（真中转站 + 真 runtime +
`design_source="plan"`），读数落 `.cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt`。
**首次实跑失败**：`litellm.RateLimitError: Channel rate limit reached for model`
（中转站瞬时基础设施类，非产品缺陷）；按 fix_policy 重试并如实记录终态。

### EC-05｜收口资产

- `tools/verify_goal096_closeout.py` + `tools/goal096_closeout_assertions.py`
  （外部断言集形态，自指判据钉住「加载的是自己那份」）。
- 登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的
  `_VERIFIERS` 与 `test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`。
- **跨 GOAL** 的 tooling 判据：`tests/tooling/test_terminal_goals_have_closeout_verifiers.py`
  —— 受判面内每个终态 GOAL 必须有验证器且**被分类**；空真守卫点名判红；
  祖父条款 `_CUTOFF_SEQ = 64`（090/095/076 的缺口不追认成历史义务，只登记）。
- **不**回填 090/095/076。

## 两向按压（判据自身可信）

1. `test_terminal_goals_have_closeout_verifiers.py` 的**空真守卫**：在宪章程序表还没有
   序 64 时，受判面为空 ⇒ 实测判红并点名「受判面为空（下界序 64）⇒ 本条失去判据对象」
   （**不是**恒过）。
2. 从 `_VERIFIERS` 撤掉 096 那一行 ⇒ 「未分类」分支点名（见 RECHECK 的按压节）。
3. 按压后按 raw `sha256` 逐字节复原（`git diff` 不作逐字节证据）。

## 规模与门

单文件 ≤450 行 / 单函数 ≤50 行 / 行长 ≤100（`ruff check` 与 `ruff format` 两道门）。
`report_question.py` 的 `_braced_segments` 主循环分支吃满复杂度配额 ⇒ 字符串态推进
抽成 `_advance_string_state`（与 `phase_input_material` 同一手法）。

## 验收条件

- [x] **EC-01**：`examples/protocols/direction_to_report_v1.yaml` 六相齐备、依赖链正确、`experiment`/`report` 两相**不声明**跨相 `inputs`（C-1）、编译零 ERROR；两份既有协议一字未改。判据 `tests/contracts/test_direction_to_report_protocol.py` **5 passed**。
- [x] **EC-02**：两向可判 —— 改 `question` 产出 ⇒ provider 收到的 query 变（机制层 `queries == [query]` + 编排层 `offline.requests[0]`）；改 `retrieval` 产出 ⇒ `plan` 的 `retrieval_prompt` 变；摘 `question` ⇒ **编译期** `CROSS_PHASE_INPUT_INVALID`。
- [x] **EC-03**：`report_question.py`（新模块）从本 run 的 `research_question` 制品读正文填 `objective`；两处渲染器口径同步；无制品 ⇒ 点名缺席、解不出 ⇒ 抛错、两制品 ⇒ 歧义。判据 **6 passed**。
- [x] **EC-04**：真跑**第三次通过** —— `state: SUCCEEDED`、六相全落库、检索词逐字等于模型自提的 query、真实 **PMID 42787049**、三臂实验、报告第 1 节逐字引用本 run 的问题块。读数落 `.cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt`。
- [x] **EC-05**：`tools/verify_goal096_closeout.py` + `tools/goal096_closeout_assertions.py` 在树并登记 `_VERIFIERS` / `IN_SCOPE`；新增**跨 GOAL** 判据（受判面内每个终态 GOAL 必须有验证器且被分类，含空真守卫）；090/095/076 **不**回填（只登记残余）。

## 实施清单

1. 读 GOAL-095 残余 → 建 GOAL-20261024-096（读取器 REFUSED `RESIDUAL_SECTION_MISSING`，改以 RECHECK 第七节为准逐条处置）。
2. 新建六相协议；编译验证（零 ERROR）；两处 run_chain 相补 `workspace.read`（冻结集比两相版多一件）。
3. 写 EC-01 判据（协议文档面 + 编译面 + C-1 + 兄弟协议未改）。
4. 写 EC-02 机制判据（两向 + 编译期反证）。
5. 新建 `report_question.py`；接线 `report_facts`；改两处渲染器口径；写 EC-03 判据（两种形态 / 反证 / 缺席 / fail-closed）。
6. 写离线 e2e（真容器 + 契约感知 mock 中转站 + `design_source="plan"` + 被评对象装配）：**6 passed**。
7. 写 live 判据并真跑：前两次 `RateLimitError`，第三次 `SUCCEEDED`；读数落盘。
8. 新建 096 验证器 + 断言集；登记 `_VERIFIERS` / `IN_SCOPE`；新增跨 GOAL 收口判据。
9. 宪章记账（程序表序 64 + 阶梯「报告」行升级 + 进展/修订各一行）；ALL_PLAN 顶部追加；PLAN / RECHECK。
10. 记录面判据 → m0 见证 → 提交推送 → CI 台账。

## 证据

| 面 | 读数 |
| --- | --- |
| 协议判据 | `tests/contracts/test_direction_to_report_protocol.py` **5 passed** |
| 跨相机制 | `tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py` **3 passed** |
| 报告问题读取面 | `tests/application/run_orchestration/test_report_question_objective.py` **6 passed** |
| 离线 e2e（真容器） | `tests/e2e/test_direction_to_report_arc_offline.py` **6 passed** |
| live 真跑 | `tests/e2e/test_direction_to_report_live.py` **1 passed**（run `94f605b9-15f6-49f9-a6e1-75eca388fbb1`，`SUCCEEDED`） |
| 真实标识 | **PMID 42787049**（检索读取步 `source_ref` 末段） |
| 实验 | 三臂，`n_items: 120` / `seed: 17`；处理臂 `comparison_reduction_ratio: 357.0` vs 对照 `0.0` |
| 报告 | `research_report.md` digest `sha256:518bc5f6…`；第 1 节逐字引用本 run 的问题块 |
| 登记面 | `test_run_chain_capability_exposure` **6 passed**；`test_session_tool_bindings_exposure` **9 passed**；`test_declared_input_sources` **3 passed**；`test_capability_coverage_is_implemented` **8 passed**；policy 差集 **12 passed** |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-24 | IN_PROGRESS | 建档：六相协议 + 报告第 1 节 + 收口资产三件。 |
| 2026-10-25 | DONE | 五 EC 全达成；EC-04 真跑第三次通过；记录面收口。 |

## 影响报告

- **Domain / schema**：无变化（未改任何域实体、TrustLabel 取值或 `schemas/protocol.schema.json`）。
- **API**：无路由变化；报告正文第 1 节的内容来源变化（读本 run 的问题制品）。
- **安全/凭据**：无放松（`workspace_allow_host_shell=True` 与既有 live 判据同一条做法，只影响该次受判 run 的装配；§9 默认 deny 十项未动）。
- **兼容性/迁移**：`ReportInputs.objective` 的**来源**变了、**类型与渲染结构不变**；无该制品的 run 逐字回到「无 + 原因」文案（措辞更新为点名 `research_question` 缺席）。既有报告链协议无 `research_question` 相 ⇒ 第 1 节仍为空+点名称缺，**不是**回归。
- **上游版本影响**：无新依赖、无 pin 变更。
- **下一项任务**：序 65（创新点相，C 口径：检索可证的新颖性 + 独立评审者结构化判词；修 `novelty_reviewer` 死配置）。
