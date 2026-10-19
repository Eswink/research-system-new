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

### 既有判据改动逐条申报（`numstat` + 谓词比对）

基线 `3f763fd5`（本轮起点）→ `2dc324d8`。**判定口径**：删除行必须逐条给出
「原谓词 → 新谓词 + 为什么不是放宽」；新增行一律是**收紧或显式登记**。

| 文件 | `numstat`（+/-） | 删除的谓词 / 行 | 现在的谓词 | 性质 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_program_nudge_bound_reachability.py` | +15 / -3 | `source = ...routers/programs.py` + `assert "nudges=deps.nudges" in source` | 同一句 `assert "nudges=deps.nudges" in source`，但 `source` 读 `services/api/program_advance.py`；**外加** `assert "advance_for(deps, program_id)" in router` | **落点迁移 + 收紧**（判据从 1 条变 2 条；删掉新落点那行仍红） |
| `tests/api/test_ops_schedules_api.py` | +2 / -0 | —（纯新增） | `_BUILTIN_NAMES` 增 `"program_advance"` | 纯收紧（少登记一个 ⇒ 词表判据红） |
| `tests/api/test_write_face_cannot_be_bypassed.py` | +4 / -1 | `_MEASURED_MUTATING_COUNT = 63` | `= 64` | **纯同步**：方法是保护面定义、断言强度未动；新端点自动落入枚举面并被全覆盖用例覆盖（该文件自己的注释逐字要求「新增写面时改这一行」） |
| `tests/api/test_write_face_query_params_are_refused.py` | +19 / -6 | 两处 `sorted(...) == ["created_at","id","name","status","updated_at"]` | 两处列表多一个 `"direction"`（位置保持字母序） | **纯同步**：键集必须与 DTO 一致；键集**收窄**（多一个名字 ⇒ 任何多余键仍判红） |
| `tests/architecture/python/test_live_switch_is_single_source.py` | +4 / -0 | —（纯新增） | `LITERAL_MENTIONS` 与 `LIVE_MODULES` 各加一条（同一文件） | 纯收紧（两处都是「新加一个就露头」的显式清单） |
| `tests/observability/test_privacy_exit_census.py` | +2 / -0 | —（纯新增） | 两个新模块登记为**受判**出口（`program_advance.py` 的 `failure_payload`、`program_advance_scheduler.py` 的 `otlp_span`） | 纯收紧（**不是豁免**：`ExitSurface` 的 `JUDGED` 面，要有观测方式） |
| `tests/observability/read_face_route_registry.py` | +8 / -1 | `ReadRouteRule("/projects", ZERO_HIT, _META)` | `"/projects"` 移入 `DECLARED_CONTENT`（`+` 行，含「一等边界」注记） | **受判面迁移（如实申报）**：`/projects` 现在披露 `direction` ⇒ 从「零命中」改为「有内容披露」；`MAX_DECLARED = 15` **恰好到界未超**（实测 `len(DECLARED_CONTENT) == 15`）；`MIN_EXERCISED = 40` 未动 |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | +2 / -0 | —（纯新增） | `_VERIFIERS` 加 `tools/verify_goal089_closeout.py` | 纯收紧（新验证器必须跑自己的断言集） |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | +13 / -14 | 三个门包装各自内联 `paths=...` / `_run([...])` / `return [...]`（三个函数 × 4–5 行） | 三个包装共用 `_gate(root, relatives, argv, label)`，各自一行转发；四条 `test_` 用例**一行未删** | **等价重构**（文件原本正好 450 行，加两条登记会越界）；按压判据 `test_every_gate_actually_detects_a_broken_script` 未动 ⇒ 三道门仍各自可证伪 |
| `tools/goal044_closeout_assertions.py` | +7 / -1 | `"approvals=deps.approvals" in _text(root, ROUTER)` | 同一句改为 `in _text(root, ADVANCE)` **且** `"advance_for(deps, program_id)" in _text(root, ROUTER)` | 历史资产**落点迁移 + 收紧**（判词名与意图不变，条件变严） |
| `tools/goal059_closeout_assertions.py` | +7 / -2 | `"nudges=deps.nudges" in router`（+ 原判词串） | 同一句改为 `in _text(root, ADVANCE)` **且** 端点断言；判词串**逐字保留** | 同上（判词串未改，只换受判文件并加一条） |
| `tests/e2e/live_control_plane_support.py` | +18 / -3 | `def product_control_plane_deps(db_path: str)` + 一行 docstring + `assemble(ApiSettings(db_path=db_path))` | 签名多两个**关键字-only** 参数（`agent_runtime=""`、`allow_host_shell=False`），缺省值保持既有行为；`ApiSettings` 多传两个字段 | **向后兼容的接线面**（缺省逐字等价；既有调用点一行未改） |

**结论**：无一处删除断言、无一处放宽阈值 / 词表 / 扫描面。唯一「受判面迁移」的
`read_face_route_registry.py` 逐条写明方向（`ZERO_HIT` → `DECLARED_CONTENT`）与上界读数。

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

### 收口补齐（2026-10-20）

- **`2dc324d8` 的 CI 已到终态**：M0 run `39324938465` **success**（attempt 1），
  `console-frontend` / `collector-quality` / `quality-windows-latest` / `eval-gate` /
  `quality-ubuntu-latest` / `observability-overhead-ubuntu-latest` /
  `observability-overhead-windows-latest` / `container-quality` **8/8 success**；
  `Push on main` run `39324938696` success；
- **既有判据改动逐条申报**：见上一节（11 个文件，`numstat` + 谓词比对）；
- **本记录之后的最后一轮全量 m0**（独占、静止工作树、`.venv`）：终态行
  `PASS: profile=m0; 23 deterministic checks`；`PASS [` **24 行**（含
  `release-assets-immutable`）；`FAILED` **0 行**。

### 推送纪律的偏差（如实登记，不改写历史）

**本轮实际推送 4 次**：`3f763fd5..dc5646fe`、`dc5646fe..43ca33dc`、
`43ca33dc..0645bd08`、`0645bd08..2dc324d8`。硬纪律写的是「批量推送（一个 cycle 一次）」，
实际做法偏离了它，偏差是**收口期的台账自指**造成的：

1. 第一次（含 6 个提交）符合纪律；
2. 第二次是因为「两树复检要以含本轮改动的提交为基准」⇒ 必须先落地；
3. 第三 / 四次是**台账写入自身**：每记一个提交的 CI 结论，就产生一个新的记录提交，
   而那个提交又会触发一次 CI —— 这是一个**自指环**（记录 CI 的动作触发 CI）。

**处置（不是掩饰）**：

- 台账逐提交登记全部 4 批，零 run 与 `cancelled` 都如实写明 `covered_by`；
- 自指环在**第五次**（本文件所在的收口补齐提交）处**停止**：该提交只改记录，
  它自己那次 run 的结论**不写回台账**，而是把边界写在这里 —— 继续追会让「最后一个提交」
  永远不存在；
- 这不是放宽判据：台账仍要求「每个提交要么有 run 结论、要么有 `covered_by`、
  要么有明写边界」，本段的边界声明就是第三种形态的显式登记。

**下一轮的约束**（写进记忆）：收口期把「台账写入」与「推送」合并成**一次** ——
先在本地把所有结论写全（包括「本轮共 N 次推送」的说明），再一次性推送并轮询。

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
