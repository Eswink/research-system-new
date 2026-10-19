---
id: RECHECK-20261019-089
slug: goal-089-direction-drives-question-drives-retrieval
title: GOAL-089 复检 —— 方向驱动问题、问题驱动检索、推进自动化、真跑读数
status: COMPLETED
result: PASS
created_at: 2026-10-19
updated_at: 2026-10-19
plan_id: PLAN-20261019-089
parent_goal: GOAL-20261019-089
owners:
  - root-agent
verify_paths:
  - tools/verify_goal089_closeout.py
  - tools/goal089_closeout_assertions.py
  - tests/e2e/test_direction_to_question_to_retrieval_live.py
memory_entries: []
---

# RECHECK-20261019-089 — GOAL-089

## 检查结果

### EC-01：方向 → 问题 → 检索

**判什么**：检索词是否**真的**来自上游模型写下的问题，而不是操作者预填的简报。

三条判据分工（互不替代）：

| 判据 | 判的面 | 读数 |
| --- | --- | --- |
| `tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py` | **机制**：跨相材料怎么进参数材料 | **9 passed** |
| `tests/contracts/test_direction_to_question_protocol.py` | **声明**：出厂协议真的按那个形态写出来 | **4 passed** |
| `tests/e2e/test_direction_to_question_to_retrieval.py` | **编排**：两格真的按声明串起来 | **2 passed** |

**双向判据（逐条实跑）**：

- **改上游产出 ⇒ 换检索词**：`test_a_different_question_changes_the_retrieval_query` 用同一装配、只换上游交付物里的 `query`，provider 收到的参数随之改变；
- **摘掉上游 ⇒ 编译期点名**：`test_removing_the_producer_is_named_at_compile_time` 与 `test_removing_the_question_phase_breaks_compilation_naming_the_producer` 都判 `CROSS_PHASE_INPUT_INVALID`（**不是**运行期静默用默认值）。

**编译期判定的一处修正（收窄而非放宽）**：`is_cross_phase_reference` 原先只认「左段是 phase id」或「右段是某 phase 的产物名」；`LOCAL_INPUT_PREFIXES = ("input-brief", "input-corpus")` 让**其余** `a:b` 一律按跨相处理 ⇒ 悬空引用（如 `question:research_question` 里的 `question` 被删）不再是「本地输入」。

### EC-02：方向进 canonical

**判什么**：方向是**自己的**字段，不是 `name` 的别名。

- `ProjectDefinition.direction`：可选、缺省 `None`、空白拒绝、去首尾空白、≤2000；
- `with_direction(...)` 与 `renamed(...)` **分开** —— `test_renamed_keeps_the_direction_and_with_direction_keeps_the_name` 判两者互不侵扰；
- sqlite：`_encode` 在 `None` 时**不写那个键**，`_decode` 把缺键读成 `None` ⇒ 旧行逐字可读（`test_a_legacy_row_without_the_key_reads_back_as_none`）；
- 读面：`GET /projects` 与 `GET /projects/{id}` 披露；写面：`POST` 可带、`PATCH` 三态可辨（不改 / 设 / 清）、`PUT /projects/{id}/direction` 只碰方向；
- 三处同步：OpenAPI 快照（`tools/gen_openapi.py` 重生成）、`apps/web/src/api/types.ts`、隐私读面登记。

读数：`tests/api/test_project_direction.py` **13 passed**；`tests/observability/test_privacy_read_face_canary.py` + `tests/contracts/test_openapi_snapshot.py` 合计 **31 passed**。

### EC-03：迭代自动起来

**判什么**：推进由周期作业**自动**发生，且**不建第二套**装配。

- `ScheduleJob.PROGRAM_ADVANCE`（词表 + 内置定义 + `JOB_PURPOSE`）；
- `services/api/program_advance.py::advance_for` 是**唯一**装配入口：端点与作业都调它（`test_the_job_calls_the_same_assembly_as_the_manual_endpoint` 判两者读到**同一个** `advance_program` 调用点）；
- `ProgramAdvanceScheduler` 是 `PeriodicDaemon` 子类，`job = ScheduleJob.PROGRAM_ADVANCE`；无 program store ⇒ `executor_attached=False`（不假装有执行体）。

读数：`tests/application/ops/test_program_advance_job.py` **5 passed**；`tests/api/test_ops_schedules_api.py`（含 `_BUILTIN_NAMES` 登记）**5 passed**。

**闸门语义一字未动**：`test_a_declared_gate_still_stops_the_program_with_a_readable_reason` 判「声明了闸门 ⇒ 停下且理由可读」；三种既有闸门（`WAIT_FOR_APPROVAL` / 判词条件式 / 多点）的判定代码零改动。

### EC-04：真跑读数

读数全表见 [`GOAL-20261019-089-live-run.txt`](../goals/evidence/GOAL-20261019-089-live-run.txt)。要点：

| 项 | 读数 |
| --- | --- |
| run id | `07f339e2-2845-4df0-bb3b-4d9fa3146a04` |
| 终态 | `SUCCEEDED` |
| 一句话方向 | `retrieval augmentation for scientific hypothesis generation` |
| 模型自提的检索词 | `retrieval-augmented generation scientific hypothesis discovery` |
| 命中的真实标识 | `41408154` / `41743026` / `42160738` |
| 检索报告 digest | `sha256:c736c6a2a323531901a423c22037d477880571a19ba4578edf50084f43349493` |

**三次失败到成功的路径**（每次都是**真缺陷**，逐条登记在 GOAL 的「真跑读数」小节）：

1. 判据从 `/runs/{id}/artifacts` 找 `tool-args:` 制品 —— 那条读面按 claim relation 投影，参数制品**不挂**它；
2. 改为按 `task_identities` 找 —— 运行链步在 `engine.submit` **之前**执行，检索失败时**没有任务行**；
3. 最终改为**制品面枚举**（`list_refs` 的 `classification` + id 后缀）⇒ 取证不再依赖 run 是否成功。

另有**两处产品侧修正**（不是判据放宽）：

- 问题契约补「三到六个高信号词」的 query 形态规则（8–9 词的 query 在 PubMed 上 AND 连接后返回 `count: 0`，读取步因此无 id，run `FAILED`）；
- `_json_in_text` 扫**全部**围栏块与裸 JSON 段（真实回复是「说明 + 若干块」，示例块常在答案前），且**多份带期望键就点名**。

### EC-05：自举收口

- `tools/goal089_closeout_assertions.py`（本轮特有断言：材料面 8 + 悬空 2 + 声明 4 + 方向 9 + 推进 8 + 用例 11 + 例数下界 6 + 既有判据 3）；
- `tools/verify_goal089_closeout.py`（标准断言集 + 本轮特有 + 记录面；`self-loads-its-own-assertions` 按本文件名推导）；
- 两处注册表显式登记（`IN_SCOPE` 与 `_VERIFIERS`）；`test_tooling_scripts_meet_product_gates.py` 原本**正好 450 行**，同轮把三个门包装压成共用一个 `_gate`（**判据语义一字未改**），腾出空间后仍 ≤ 450。

**判词读数**：

- 本树：`exit=0`，**89 条判词**，`sha256=67894073183c053543473bfef0a23ef7a1c2bd2d2ec0db6e16f11e2a5bf355ab`；
- 干净 checkout（`../rs-goal089-clean` @ `493020b8`）：同一份 **89 条**，**同一个 `sha256`**；
- `COMPARE identical=True` ⇒ **TWO-TREE PASS**；
- 判词归档进树：`evidence/GOAL-20261019-089-verdict-current.txt` 与 `-verdict-clean.txt`
  （各 3693 字节、89 行、**CR=0** —— 二进制写盘）。

**两处反向按压（证明判据不是恒真）**：

- 把 `PROGRAM_ADVANCE = "program_advance"` 改成 `"program_advance_X"` ⇒ `schedule-vocabulary-has-the-job` 立刻 **FAIL**；还原后该文件 `sha256` 逐字节相同（`0c7a7b4af19b38c32d143c2cd88607cf59fbb76562ccba04d6d9235f04f7f378`）。

### 如实登记的残余

**`W-6`（本轮实测发现，未修）**：`producer_trust_label` 只看「声明了 `run_chain` + 能力面落在带 `network_domains` 的 provider 上」，而 `question` 格**必须**声明 `run_chain` 才能把文献 provider 排除出它的会话工具面（否则 SDK 点名 `ToolDefinition 'europe_pmc' is not registered`，本轮实测）⇒ 模型写的 `research_question` 被标成 `RETRIEVED`，而检索格的 `EVIDENCE_COVERAGE` 性质维可被这条跨相边**单独满足**。

**补偿判据在位**：两份 e2e/live 判据都从 **provider 收到的请求参数**逐字取证「检索词 == 模型写下的 query」，并都要求检索命中真实标识 ⇒「检索真的发生了」仍可机械判定。

**为什么不修**：改它等于改 `TrustLabel` 的推导语义（GOAL 的 `escalation_triggers` 明写），而既有判据 `test_cross_phase_inputs.py::test_b_*` 正把这个推导**连同按压**钉住 —— 那是 `GOAL-20261016-081 EC-04` 的受判面。须先由用户拍板。

### 未覆盖范围（逐条明写，本 GOAL **不声称**已解决）

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` **未写进** `.env`（逐命令传）；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**），只有 at-least-once + 幂等 + 去重。

## 结论

GOAL-089 的五个 EC 全部达成：方向进 canonical、上游模型产出成为下游检索词的**唯一**来源（双向判据可证伪）、推进由周期作业**自动**调用同一条装配链、真实 run 在新中转站 + 真实 runtime 上跑通并留下可核读数。`W-6` 如实登记为残余，补偿判据在位。
