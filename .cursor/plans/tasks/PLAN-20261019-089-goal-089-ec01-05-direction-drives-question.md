---
id: PLAN-20261019-089
slug: goal-089-ec01-05-direction-drives-question
title: GOAL-089 EC-01…05 —— 方向驱动问题、问题驱动检索、推进自动化、真跑与自举收口
status: DONE
created_at: 2026-10-19
updated_at: 2026-10-19
parent_goal: GOAL-20261019-089
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261019-089-goal-089-direction-drives-question-drives-retrieval.md
memory_entries: []
---

# PLAN-20261019-089 — GOAL-089 全五个 EC

## 验收条件

- [x] **EC-01**：检索词**逐字**来自上游模型写下的 `research_question.query`；改上游产出 ⇒ 换检索词；摘上游 ⇒ **编译期**点名。
- [x] **EC-02**：方向是 `ProjectDefinition.direction`（可选、≤2000、空白拒绝），两端点读写，三处读面同轮同步；`renamed()` 语义未变。
- [x] **EC-03**：`ScheduleJob.PROGRAM_ADVANCE` 由周期作业调用**与手动端点同一条**装配链；无 store ⇒ `executor_attached=False`。
- [x] **EC-04**：真实 run `SUCCEEDED`，读数逐条落盘（run id / 问题 / 检索词 / 真实标识 / digest）。
- [x] **EC-05**：验证器 + 断言集进树并登记；本树 **89 条判词**全绿。

## 一、五个 EC 的落点（逐条对应 GOAL 的退出标准）

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `phase_input_material.py`（跨相材料 → 参数材料，含信封解包与歧义点名）+ `phase_capabilities.py`（接线）+ `protocol_compile/cross_phase_inputs.py`（悬空引用是编译期错误）+ `direction_to_question_v1.yaml` + 合约两条 | `test_run_chain_reads_cross_phase_material.py`（9）、`test_direction_to_question_protocol.py`（4）、`test_direction_to_question_to_retrieval.py`（2） |
| EC-02 | `ProjectDefinition.direction`（可选，≤2000，空白拒绝，`with_direction` 与 `renamed` 分开）+ sqlite 往返 + DTO 三处 + `PUT /projects/{id}/direction` + OpenAPI 快照 + `types.ts` + 隐私清单 + 提示词那一段 | `test_project_direction.py`（13） |
| EC-03 | `ScheduleJob.PROGRAM_ADVANCE`（词表 + 内置 + purpose）+ `program_advance.py`（**一条**装配链）+ `program_advance_scheduler.py`（周期作业）+ lifespan | `test_program_advance_job.py`（5）、`test_ops_schedules_api.py` |
| EC-04 | 新中转站 + 真实 runtime，一句话方向跑完整链 | `test_direction_to_question_to_retrieval_live.py`（1）；读数 `.cursor/plans/goals/evidence/GOAL-20261019-089-live-run.txt` |
| EC-05 | `tools/goal089_closeout_assertions.py` + `tools/verify_goal089_closeout.py` + 两处注册表 | 本树 **89 条判词**（8 条记录面待写 → 收口时全绿） |

## 二、执行顺序（本轮实际走的）

1. **建档**：GOAL + MAINLINE 程序表第 57 行。
2. **断点勘察**：读到第四处断点 —— `_input_material` 只扫**本地**声明输入，上游 phase 的产出根本不进参数材料（GOAL 里记为建档实测的第 4 条）。
3. **EC-01 机制**：先做材料合并（含信封解包），再做编译期悬空判定，最后写协议与合约。
4. **EC-02 canonical**：域字段 → 存储 → DTO → 路由 → 快照/类型/隐私清单 → 提示词 → 两个组合根接线。
5. **EC-03 自动化**：先抽 `advance_for` 让端点与作业共用，再加词表/内置/作业/生命周期。
6. **EC-04 真跑**：三次失败后（详见 RECHECK 的「三次真缺陷」），得到一次 `SUCCEEDED` 与干净读数。
7. **EC-05 自举收口**：断言集与验证器进树 + 两处注册表登记 + 两树复检。

## 实施清单

1. **WP-A（跨相材料）**：`phase_input_material.py` 合并声明输入与上游产物，信封解包 + 歧义点名；`phase_capabilities.py` 接线。
2. **WP-B（编译期）**：`LOCAL_INPUT_PREFIXES` ⇒ 悬空引用按跨相处理（编译期点名）。
3. **WP-C（协议与合约）**：`direction_to_question_v1.yaml` 两格 + 两条合约。
4. **WP-D（方向进 canonical）**：域字段 + sqlite + DTO + 路由 + 快照/类型/隐私清单 + 提示词。
5. **WP-E（推进自动化）**：`program_advance.py`（唯一装配）+ 词表/内置 + 周期作业 + lifespan。
6. **WP-F（判据与收口）**：六份新判据 + 断言集 + 验证器 + 两处注册表。

## 三、过程中修掉的**真缺陷**（不是判据放宽）

1. **参数取证面选错**：`tool-args:` 制品不挂 claim relation ⇒ 不在 `/runs/{id}/artifacts`；而运行链步在 `engine.submit` **之前**执行 ⇒ 检索失败时连任务行都没有。判据改为**制品面枚举**。
2. **问题契约对 query 形态的约束不足**：8–9 词的 query 在 PubMed 上 AND 连接后返回 `count: 0` ⇒ 读取步无 id ⇒ run `FAILED`。契约正文补「三到六个高信号词」的规则（改的是提示词，不是判据）。
3. **信封解包只认第一个围栏块**：真实回复是「说明 + 若干块」，示例块常在答案块之前。改为扫描全部围栏块 + 裸 JSON 段，**多份带期望键则点名**（不取最后一条）。
4. **`_json_in_text` 的期望键过严导致直形态失效**：改为「带期望键者优先；只有一个无键对象 ⇒ 用它；多个无键对象 ⇒ 点名」。

## 工程记忆

**无可复用事实**（本轮读数是判据文件与 GOAL 的读数小节）：唯一值得记的是
「跨相材料进 run-chain 参数材料」这条缝的**取法纪律** —— 参数制品不挂 claim
relation，取证只能靠制品面枚举；以及「为清空会话工具面而声明 run_chain」会顺带
改变产物性质（登记为 `W-6`）。

## 影响报告

- **Domain**：`ProjectDefinition` 新增**可选** `direction`（缺省 `None` ⇒ 既有行逐字不变）；新增 `MAX_PROJECT_DIRECTION_LENGTH` 与 `with_direction`。**无破坏性迁移**（sqlite 缺键读 `None`）。
- **Domain（调度词表）**：`ScheduleJob` 新增 `PROGRAM_ADVANCE`（受控词表 + 内置定义 + purpose）。
- **API**：`POST /projects` 可带 direction、`PATCH` 三态、新增 `PUT /projects/{id}/direction`；OpenAPI 快照重生成。
- **Application**：跨相输入进 run-chain 参数材料（只增面，未声明 ⇒ 逐字节不变）；提示词多一个 optional 段（无方向 ⇒ 不出现）。
- **安全/凭据**：**无**新放行、**无**新 deny 例外、**无**凭据面改动；`sk-` 零命中
  （`tools/credential_audit.py` 四面 `offenders=0`）。
- **兼容性**：旧行无 `direction` ⇒ `None`（读面不披露、提示词无该段）。
- **上游版本影响**：无新增依赖、无 pin 变更。
- **下一项任务**：`W-6` 的修法需拍板（改 `TrustLabel` 推导语义）。

## 四、如实登记的残余

`W-6`：`producer_trust_label` 只看「声明了 `run_chain` + 能力面落在带 `network_domains` 的 provider 上」，而 `question` 格**必须**声明 `run_chain` 才能把文献 provider 排除出它的会话工具面（否则 SDK 点名 `ToolDefinition 'europe_pmc' is not registered`）⇒ 模型写的 `research_question` 被标成 `RETRIEVED`。补偿判据是 e2e/live 两份判据都从 **provider 收到的参数**逐字取证，不依赖该标签。修它需要改 `TrustLabel` 的推导语义（GOAL 的 escalation trigger），须先拍板。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 机制 / 声明 / 编排 | 9 + 4 + 2 = **15 passed** | `pytest tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py tests/contracts/test_direction_to_question_protocol.py tests/e2e/test_direction_to_question_to_retrieval.py -q` |
| EC-02 方向面 | **13 passed**（含 OpenAPI/隐私 31） | `pytest tests/api/test_project_direction.py -q` |
| EC-03 推进面 | **10 passed** | `pytest tests/application/ops/test_program_advance_job.py tests/api/test_ops_schedules_api.py -q` |
| EC-04 真跑 | **1 passed**（live 开关下） | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 pytest tests/e2e/test_direction_to_question_to_retrieval_live.py -q` |
| 收口验证器 | **89 条判词全绿** | `python -B tools/verify_goal089_closeout.py --root .` |
| 静态门 | ruff / format / mypy 全绿 | `ruff check/format --check`、`mypy` |

## 五、验证读数

- `tests/application tests/contracts tests/api`：**1471 passed / 76 skipped**；
- `ruff check`（产品根）：0 错；`ruff format --check`：产品文件全通过；
- `mypy`：`Success: no issues found in 1288 source files`；
- 真跑：`1 passed`（`egress guard: judged 6 connection attempt(s); blocked 0`）；
- 收口验证器本树：**89 条判词**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-19 | **IN_PROGRESS** | 承 GOAL-089 建档：五个 EC 同时推进。 |
| 2026-10-19 | **DONE** | 五 EC 全达成；真跑 `SUCCEEDED`；收口验证器 89 条全绿。 |
