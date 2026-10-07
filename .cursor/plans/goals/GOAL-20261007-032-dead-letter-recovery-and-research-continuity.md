---
id: GOAL-20261007-032
slug: dead-letter-recovery-and-research-continuity
title: 死信人工恢复 + outbox 取证追认 + 研究连续性 —— 把「已实现但未取证」推进到「有判据的结论」
status: ACTIVE
created_at: 2026-10-07
updated_at: 2026-10-07
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-07 用户会话指令（goal 模式）：**建档 GOAL-032（死信恢复 + outbox 取证追认 +
    研究连续性）并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点：
    (0) **授权承继（GOAL-031 的治理前提继续有效）**：用户 2026-10-06 **明确下放全部权限给
    驱动，用户只保留总目标** ⇒ 此前以「需用户拍板」登记的项**全部由驱动决定**（见「决策登记」
    节）。**区分写死**：「权限下放」= **可以决定**（含新增 allow / **有界改产品语义**），
    **不等于**可以放宽**判据、门禁、阈值或断言** —— 本轮不许有例外（本轮无 allow 面变更、
    无 pin 夹具追加授权）。
    (1) **五项授权开工**：(i) **`R26-1` 死信人工恢复路径**（§7 明文「dead-letter / manual
    recovery」；本轮主干）—— 先勘察 `ADR-0030` 的候选方案，选一或新增 ADR；实现人工显式恢复；
    幂等 + 去重；不可恢复输入**点名拒绝**；两向反证；实跑留档；(ii) **`R26-5` 取证追认**
    （**不是新实现** —— 实现已在树且生产启用；本轮把它从「未取证」推进到「有判据的结论」或
    如实登记确切边界）；(iii) **研究连续性**（勘察 `services/api/run_resume.py::rebuild_and_resume`
    的真实覆盖度，逐条实测）；(iv) 三项带来的**同步集**（声明面 / 文档 / 判据射程 / 镜像表）；
    (v) 修实现过程中发现的**真缺陷**。
    (2) **明确不做**（驱动已决定，非待拍板）：默认 runtime 改真（AGENTS.md §11）/ 读面认证 /
    多租户 · RBAC · BOLA·BFLA（M18 deferred）/ D 组审批通道（审批通道未接通，触达即 BLOCKED）/
    `G24-5` 运行时拦截器 / 部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`
    （条件不满足，逐条保持）/ 把 destructive 能力从 `require_approval` 改 allow /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**（含 skip /
    xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；**宣称项目安全**（`R-M1` 未收口）；
    **宣称投递语义为「恰好一次」**（**明确否认**；口径只能是 at-least-once + idempotency +
    deduplication）；**静默改 `terminal()` 语义而不留 ADR**。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）；
    默认姿态不变（默认 runtime 保持 **Fake**、默认 CI **离线**）。观测隐私按 AGENTS.md §10。
    (5) **边界（承继）**：GOAL-001…031 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…031 的未覆盖范围**原样保留**；
    GOAL-026 的 `R26-*` 登记中 **`R26-5` 已被本轮勘察实测推翻**（见「事实层结论」第 1 条）
    ⇒ 只**追加**事实更正，**不改历史 GOAL 正文**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 AGENTS.md §7 的「dead-letter / manual recovery」从**只有半边成立**（可枚举、可处置的
    终态成立；**人工恢复动作无产品路径**，GOAL-026 登记 `R26-1`）推进到**两半都成立且有判据**：
    ① **死信人工恢复路径** —— `DEAD_LETTER` 可被**人工显式恢复**（重新入队 / 重新派发），
    幂等（重复恢复零第二次副作用）、对不可恢复输入**点名拒绝**、两向反证、实跑留档；
    改终态语义必须**按既有 ADR 或新增 ADR**，**不得静默修改**（EC-01）→ ② **`R26-5` 取证
    追认** —— 把「已实现但从未取证」变成**有判据的结论**：relay 一轮真的投递并 mark（有读数）、
    崩溃语义（publish 后 mark 前崩溃 ⇒ 重新投递，at-least-once 实证）、消费端按 `event_id`
    去重有效、未启用组合根**如实登记**；两向反证（改坏 mark / 摘掉去重 ⇒ 判红）；并把
    GOAL-026 的过期登记**只追加**一条事实更正（EC-02）→ ③ **研究连续性** —— `rebuild_and_resume`
    的覆盖度**逐条实测**（进程重启？租约过期？死信？），只收「能被既有机制覆盖但缺判据」的部分，
    需要新机制的**如实登记为下一轮输入**；被中断的 run 恢复后继续到终态、不重复已完成的副作用、
    反证判红（EC-03）→ ④ **自举收口** —— 验证器进树 + 两树复检 + 判词归档进树 + as-is m0
    23/23（在全部记录写入之后）+ 治理绿 + CI 台账逐提交（EC-04）。
    **硬约束**：先复核再依赖（本 GOAL 的起点事实全部待复核）；受判面**不得**是交集 / 过滤；
    真被使用才算数（断言调用证据 + 下游消费证据）；点名失败而非静默；留档**二进制写盘**、
    判词归档**进树**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义
    为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **死信人工恢复路径（`R26-1`，主干）**。
      (a) **先勘察后实现**：读 `ADR-0030` 给出的候选方案（A–E），**选一个并写明理由**并逐条
      对照代价；若 ADR 的方案都不合适 ⇒ 按本仓惯例**新增 ADR**（`docs/adr/ADR-00NN-*`，
      `Status: Proposed` 或 `Accepted` 按本轮决定登记），**不得静默偏离既有 ADR**；
      (b) **实现**：让 `DEAD_LETTER` 可被**人工显式恢复**（重新入队 / 重新派发），且**不破坏
      终态语义** —— `terminal()` 的既有判定要么保持、要么明确修订并**逐条说明影响**（`terminal()`
      的全部消费点：`acquire_lease` 守卫、`cancel_run`、PG `_validate_completion_lease`、
      `cancel_run.py` 两 adapter、`workflow_ops` 的 `_COMPLETION_ALREADY_APPLIED`、
      `test_state_machines.py::test_terminal_states_are_final`、`test_task_state_drivers.py`）；
      (c) **幂等与去重**：重复恢复同一死信任务**不产生第二次副作用**（承 §7；以副作用计数为
      判据，计数取样必须在**第二次恢复之前**——承 GOAL-026 EC-03 的假绿教训）；
      (d) **点名失败**：对不可恢复的任务（状态不符 / 已恢复 / 不存在）**点名拒绝**
      （结构化错误 + 消息含任务 id 与原因），**不得静默**；
      (e) **反证两向**：① 恢复后任务真的能再次执行（有执行证据：第二次 attempt 交付 +
      `fence` 前进 + 事件链可读）；② 不可恢复的输入各自被**点名拒绝**（三种输入逐条判词）；
      (f) **实跑**：造一条真死信（用既有失败注入路径：`max_attempts` 打满 + 可重试类别）
      → 人工恢复 → 跑到终态，全程留档（含恢复前后的状态转移逐条）。
      **同轮同步集（建档实测标定，逐条登记）**：本 EC 会打红**已知判据**（实测枚举，见
      「事实层结论」第 2 条）——同步方式**只允许**：① `docs/reliability/RUN_STATE_MACHINE.md`
      的 `ResearchTask` 迁移表 + Terminal 行（**输入登记面**）；② `tests/adapters/sqlite/
      test_workflow_dead_letter_surface.py::test_dead_letter_has_no_outgoing_transition`
      （它钉的正是「无出边」= 本轮要改的机械事实 ⇒ 按新事实**重新定基**：改为钉「**只有**
      人工恢复一条出边，且它不在自动路径上」，断言形态与受判面**不得收窄**）；
      ③ `tests/domain/test_state_machines.py::test_terminal_states_are_final` 的
      `DEAD_LETTER` 行（`ENQUEUE` 事件——若恢复事件取别的事件名则该行**逐字不动**，取
      `ENQUEUE` 则按新事实定基并自证强度未降）；④ `tests/domain/test_task_state_drivers.py`
      的 `_DRIVEN_BY` 登记（`DEAD_LETTER` 的驱动方新增人工入口）。**上述以外的任何既有判据
      改动 ⇒ BLOCKED**；每条同步都要在记录内给出 before/after 逐字节对照与「强度未降」自证。
      **判据**：恢复路径 + 幂等 + 点名拒绝 + 两向反证 + 实跑留档 + （如新增）ADR + 同步集自证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite tests/domain
      tests/application tests/e2e -q` ⇒ 全绿；新增判据文件（恢复路径 / 幂等 / 点名拒绝 /
      两向反证）全绿；配套留档：ADR（既有或新增）的选择理由、`terminal()` 影响逐条清单、
      恢复前后状态转移序列、副作用计数读数、三种不可恢复输入的判词逐字、两向反证判红原文、
      同步集四条 before/after 对照与「强度未降」自证。
    status: PENDING
  - id: EC-02
    criterion: >-
      **`R26-5` 取证追认（不是新实现）**。
      (a) **实现面核实**：`adapters/postgres/outbox_relay.py::PgOutboxRelay.run_once` 的真实
      行为（drain 语义 = 先取 pending 再逐条 publish+mark；mark 语义 = 按 event_id 标记已发布；
      失败时的行为 = sink 抛错 ⇒ 本轮中断，已 mark 的不重投 / 未 mark 的下轮重投）；
      `services/api/scheduler.py::OutboxRelayScheduler`（`PeriodicDaemon`，`job =
      ScheduleJob.OUTBOX_RELAY`，`interval_seconds=5.0` 默认）；
      (b) **启用面实测**：`services/api/pg_composition.py` 设 `deps.outbox_relay_enabled = True`
      （实测真值路径）⇒ **生产 PG 组合根默认启用**；SQLite 组合根（`services/api/composition.py`
      的 `outbox_relay_enabled: bool = False`）**未启用**且 `OutboxRelayScheduler` 的构造点
      唯一；**未启用的组合根如实登记**（`/ops/schedules` 读面 `executor_attached=False`）；
      (c) **判据（新）**：① relay 一轮真的把 pending 投递并 mark（有读数：pending 前后计数 +
      sink 收到的 event_id 集合 + `mark_outbox_published` 调用证据）；② **崩溃语义**：
      publish 后 mark 前崩溃 ⇒ 重新投递（at-least-once 实证：注入「mark 抛错」或「publish 后
      中断」，下一轮 pending 仍含该 event_id）；③ **消费端按 `event_id` 去重**有效（重复投递
      不产生第二条事实：`INSERT OR IGNORE` 语义 + 重复 publish 的 `rowcount==0` 读数）；
      ④ 未启用组合根的行为**点名**或**如实登记**（不得当成已覆盖）；
      (d) **反证**：把 mark 逻辑改坏 ⇒ 判红（重复投递被检出）；把去重摘掉 ⇒ 判红；
      (e) **修正记录面**：GOAL-026 的 `R26-5` 登记**已被实测推翻** ⇒ 在本轮记录里**只追加**
      一条事实更正（不改历史 GOAL 正文），写明「实现已存在（`ed2fa0e` 起）、登记过期」。
      **判据**：实现面核实 + 启用面实测 + 四条判据 + 两向反证 + 记录更正（只追加）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/postgres/test_outbox_pg.py
      tests/api/test_ops_schedules_api.py tests/architecture -q` ⇒ 全绿；新增判据文件
      （relay 一轮 / 崩溃语义 / 去重 / 未启用登记）全绿（PG 不可达时如实 skip + 登记，
      **不得**把 skip 记成 PASS）；配套留档：启用面真值路径逐文件读数、pending/mark 计数对照、
      两向反证判红原文、记录更正条目。
    status: PENDING
  - id: EC-03
    criterion: >-
      **研究连续性（`run_resume` 覆盖度）**。
      (a) **勘察前置**：`services/api/run_resume.py::rebuild_and_resume` 处理哪些情形、不处理
      哪些（**逐条列出**：有冻结正文的自包含重建 / 无冻结正文的来源依赖重建 / 早退拒绝两类 /
      preflight 失败拒绝 / 语义漂移拒绝）；
      (b) **缺口判定（每条给出实测结论，不得推定）**：① 死亡任务（`DEAD_LETTER`）能否被它
      捞回？② 进程重启后未完成任务呢？③ 租约过期后呢？（提示词点名的三条各给实测读数）
      (c) **本轮范围**：只收**能被既有机制覆盖但缺判据**的部分（预期：重启后 `PAUSED` run 的
      重建续跑已有实现与既有判据、`EXPIRE_LEASE` → `QUEUED` 已有判据；`DEAD_LETTER` 的捞回
      属 EC-01）⇒ **需要新机制的部分如实登记为下一轮输入**（不得为本轮凑数硬做）；
      (d) **判据**：① 被中断的 run 恢复后**继续到终态**（有实跑留档：`PAUSED` → 重建 →
      `SUCCEEDED`，事件链可读）；② 恢复**不重复已完成的副作用**（承 §7 幂等：已 `SUCCEEDED`
      的任务在重建续跑里**零新交付**，以 deliveries 计数为判据）；③ **反证**：把恢复逻辑
      改坏 ⇒ 判红（点名缺口）。
      **判据**：覆盖度逐条 + 实测结论 + 实跑留档 + 反证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_restart_rebuild_resume.py
      tests/e2e/test_retry_park_and_resume.py tests/e2e/test_workflow_restart_recovery.py
      tests/application/run_orchestration -q` ⇒ 全绿；新增判据文件（覆盖度矩阵 / 实跑 /
      两向反证）全绿；配套留档：覆盖度逐条实测读数（含「不处理」清单）、实跑状态转移、
      deliveries 计数前后对照、反证判红原文。
    status: PENDING
  - id: EC-04
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools` +
      `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py`，`--script-mode shared` +
      `--base-ref`）+ **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**、
      `CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py` 绿；
      ⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；基础设施红按
      GOAL-031 的三条取证口径处理；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）；
      ⑥ 承继残余逐条在位（含 `R26-*` 的终态：本轮 `R26-1` 收口、`R26-5` 更正，其余逐条保持 +
      理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal032_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <建档基线>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；`uv run --frozen --no-sync python -B
      .cursor/skills/governance-check/scripts/validate.py` ⇒ 绿；配套留档：
      两路判词 sha256 相同的归档、m0 日志、CI 台账逐提交行。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **为了凑数而声明没有实现的能力**；**把受判面写成交集 / 过滤 / 空集恒真**
      （承 `MEM-20260928-160`：`declared ∩ implemented` 使「声明了但没实现」在构造上不可能
      被报出）；**只断言「注册了 / 返回成功」而不取调用与下游消费证据**
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据
      （`test_reproducibility_wording.py` / `test_delivery_semantics_wording.py` /
      `test_record_face_is_covered_by_the_gate.py`）、两树入口判据、规模门禁、
      `tests/application/preflight/**`、`tests/application/test_m2_audit.py`、
      `tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**` 既有文件）
      —— **新增**判据与新增文件不受此限
    - >-
      **本 GOAL 特有的同轮同步例外（逐条点名，EC-01 的必然结果，建档实测标定）**：仅限
      ① `docs/reliability/RUN_STATE_MACHINE.md` 的 ResearchTask 迁移表 + Terminal 行
      （**输入登记面**，判据本体不动）；② `tests/adapters/sqlite/test_workflow_dead_letter_surface.py`
      的 `test_dead_letter_has_no_outgoing_transition`（**按新事实重新定基**：钉「只有人工恢复
      一条出边」而非「无出边」，受判面**扩大**不缩小，并在记录内逐条自证）；③
      `tests/domain/test_state_machines.py` 的 `terminal → DEAD_LETTER + ENQUEUE` 参数行
      （仅当恢复事件取 `ENQUEUE` 名时按新事实定基；取别的事件名 ⇒ 该行**逐字不动**）；④
      `tests/domain/test_task_state_drivers.py` 的 `_DRIVEN_BY` 登记（`DEAD_LETTER` 增列
      人工恢复入口，**只增不改**其余行）。**上述以外的任何既有判据改动 ⇒ BLOCKED**；
      每条同步都要在记录内给出 before/after 逐字节对照与「强度未降」自证。
    - >-
      **放宽任何既有判据的断言**（含把受判面收窄成交集、删断言、改期望值使其通过）；
      **把 `terminal()` 语义静默改掉而不留 ADR**（改它 = 改产品语义 ⇒ 必须按 ADR-0030
      既有方案或**新增 ADR**，且记录内逐条说明影响面）
    - >-
      改 `default_effect: DENY` / 放宽 §9 默认 deny / **新增任何 allow 或 pin 夹具改动**；
      或改 `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` 与
      `policy.yaml` 的镜像并集**使两者不等**（两张表由既有测试锁死并集相等）
    - >-
      **把非只读能力加入放行**；**把 destructive 能力从 `require_approval` 改 allow**；
      **允许未放行能力静默跳过**（缺实现 / 未放行 / 缺 pin / 映射缺失必须**点名**）
    - >-
      **未经 pin 的 provider**；**把真实凭据写进任何地方**；**放开默认网络**（默认门必须仍
      离线）；**触达 D 组**（`external.publish` / `package.install` / `git.commit` /
      `workspace.delete`）；**宣称项目安全**（`R-M1`）；**宣称投递语义为「恰好一次」**
escalation_triggers:
  - 需要修改 `default_effect: DENY` / 放宽 §9 默认 deny
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖 / 上游版本 pin 变更
  - 真实凭据进树 / 未 pin 接上游 / 触达 D 组（审批通道未接通）
  - 把非只读能力加入放行
  - 需要改（同步集以外的）任何既有判据的断言
  - 需要把 `terminal()` 语义改掉而无 ADR 依据（静默改语义）
  - 宣称项目安全 / 宣称投递语义为「恰好一次」
  - 同一失败签名超过 fix_policy 上限
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261007-032 — 死信人工恢复 + outbox 取证追认 + 研究连续性

本文件是 GOAL 层编排记录（`GOAL-*` 之上对齐 `PLAN-*` / `RECHECK-*` / `MEM-*` 体系；
单一流程权威见 `.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账；
工程事实、验收与复检仍由 PLAN/RECHECK 承载。

## 目标与退出标准

四条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 死信人工恢复路径（主干） | ADR 依据 + 恢复路径 + 幂等 + 点名拒绝 + 两向反证 + 实跑留档 + 同步集自证 | PENDING |
| EC-02 | `R26-5` 取证追认 | 实现面核实 + 启用面实测 + 四条判据 + 两向反证 + 记录更正（只追加） | PENDING |
| EC-03 | 研究连续性 | 覆盖度逐条实测 + 实跑留档 + 幂等 + 反证判红 | PENDING |
| EC-04 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**宣称项目安全**
（`R-M1`）；不得宣称投递语义为「恰好一次」（口径只能是 at-least-once + idempotency +
deduplication）；不得**静默改 `terminal()` 语义**（必须留 ADR）。观测隐私按 AGENTS.md §10；
默认 runtime 保持 Fake、默认 CI 离线（§11）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**（提示词已声明起点事实全部待复核）。主树零改动（只读勘察）。

### 1. ⚠️ 决定性出入：`R26-5` 的实现**早已存在**，GOAL-026 登记被推翻

复核命令与读数：

```bash
rg -n "outbox_relay_enabled|OutboxRelayScheduler|PgOutboxRelay" services/ adapters/
# services/api/app.py:121 _start_outbox_scheduler（要求 deps.outbox_relay_enabled）
# services/api/scheduler.py:137 class OutboxRelayScheduler(PeriodicDaemon)（interval 默认 5.0）
# services/api/pg_composition.py:318 deps.outbox_relay_enabled = True   ← 生产 PG 组合根默认启用
# services/api/composition.py:171 outbox_relay_enabled: bool = False    ← SQLite 组合根未启用
# adapters/postgres/outbox_relay.py:23 class PgOutboxRelay（run_once：pending → publish → mark 逐条）
git log -S "PgOutboxRelay" --oneline | head
#   0a5805a chore(m14): promote audit probes to tools/probes and ignore local scratch
#   ed2fa0e feat(m14): durable workflow postgres adapter with temporal defer + debt closure
rg -n "consumer_offsets" . -g '!*.pyc' --glob '!node_modules'
#   只命中 docs/storage/DATABASE_SCHEMA.md:139（文档独有，与 GOAL-026 的登记一致）
```

逐条读数：

| 事实 | 实测 | 提示词起点表述 | 判定 |
| --- | --- | --- | --- |
| `PgOutboxRelay.run_once` 存在且 drain→publish→mark 逐条 | ✅ `adapters/postgres/outbox_relay.py:23`（78 行） | 同 | **一致** |
| `OutboxRelayScheduler` 存在 | ✅ `services/api/scheduler.py:137`（`job = ScheduleJob.OUTBOX_RELAY`，`interval_seconds=5.0`，`thread_name="outbox-relay"`） | 同 | **一致** |
| `_start_outbox_scheduler` 门控于 `deps.outbox_relay_enabled` | ✅ `services/api/app.py:121-137`；`_lifespan` 里在 `deps.runs is not None` 时启动 | 同 | **一致** |
| 生产 PG 组合根默认启用 | ✅ `services/api/pg_composition.py:318` `deps.outbox_relay_enabled = True` | 同 | **一致** |
| SQLite 组合根未启用 | ✅ `services/api/composition.py:171` `outbox_relay_enabled: bool = False`（构造点唯一：`services/api/app.py` 只读它） | 同 | **一致** |
| **`R26-5` 登记「实现 = 新建消费者」** | ❌ **登记过期**：relay 自 `ed2fa0e`（M14）起在树，生产 PG 根默认启用 | 提示词：**这是与 GOAL-026 登记的最大出入，必须复核** | **提示词正确，GOAL-026 登记被推翻** |
| `consumer_offsets` 文档独有 | ✅ 全仓只命中 `docs/storage/DATABASE_SCHEMA.md:139` | 同（登记口径本身没错，错在它把 relay 也算作「不存在」） | **部分一致** |

**结论**：`R26-5` 的**实现面与启用面均已在树且生产启用**；GOAL-026 把它登记为
「应用级事件消费者不存在 ⇒ 新建消费者」**与实测不符** ⇒ 本轮只**追加**一条事实更正
（EC-02(e)），**不改历史 GOAL 正文**。**取证面**（relay 一轮真的投递并 mark、崩溃语义、
消费端去重、未启用组合根登记）**确实从未有过专门判据** —— 这正是 EC-02 的内容。
另有残余：**应用级「按偏移量物化业务事实」的消费者仍不存在**（`consumer_offsets` 只在文档）
⇒ 如实登记，不在本轮实现（属新能力 + 触碰 Canonical State 写入面）。

### 2. `R26-1` 的缺口**精确形态**与 `terminal()` 消费点（EC-01 的射程）

复核命令与读数：

```bash
rg -n "DEAD_LETTER" packages/domain/task_state.py
#   24,40 状态/事件常量；60 (RETRY_SCHEDULED, DEAD_LETTER) → DEAD_LETTER；81 terminal() 含 DEAD_LETTER
rg -n "terminal\(\)" packages/ adapters/ services/ --type py
#   packages/domain/task_state.py:77（定义）；adapters/sqlite/workflow_ops.py:156（acquire 守卫）
#   adapters/postgres/cancel_run.py:21,45；adapters/sqlite/cancel_run.py:30,58
#   adapters/postgres/workflow_acquire.py:32；adapters/postgres/workflow_ops.py:206
#   （`ResearchTaskState.terminal()` 的**全部**消费点 = 上面 5 个 adapter 文件 + 2 条既有判据）
```

缺口的**精确形态**（机械事实，非散文）：

- `DEAD_LETTER` **无出边**：`_TRANSITIONS` 里没有任何 `(DEAD_LETTER, *)` 键；
  `terminal()` 含它 ⇒ 今天**没有任何产品路径**能把死信任务重新派发；
- **谁能改它**：改 `packages/domain/task_state.py` 的 `_TRANSITIONS` / `terminal()` 即可，
  但改动会**同时移动 5 个 adapter 的守卫语义**（`acquire_lease` 拒绝、`cancel_run` 跳过、
  PG 完成校验、`_COMPLETION_ALREADY_APPLIED` 幂等集）；
- **既有判据把它钉成机械事实**：`tests/adapters/sqlite/test_workflow_dead_letter_surface.py`
  的 `test_dead_letter_has_no_outgoing_transition` 逐一遍历 `Transition` 枚举并断言**每一个**
  都非法 ⇒ **本 EC 必然打红它**（这是设计意图：判据的作用就是「改事实必须显式」）；
- **ADR-0030 的候选方案**（`docs/adr/ADR-0030-validation-failure-consumption.md`，
  `Status: Proposed`）：A（`SUCCEEDED --VALIDATION_REJECTED--> DEAD_LETTER`）/ B（新增独立
  终态 `VALIDATION_REJECTED`）/ C（维持 run 级处置 + 读面点名）/ D（把验收门挪到 durable
  `SUCCEEDED` **之前** ⇒ 拒收落在非终态，**只加一条从非终态出发的迁移**）/ E（不做）。

**关键区分（本轮必须写清）**：ADR-0030 讨论的是「**验收门拒收**该怎么落 canonical」，
而 `R26-1` 要的是「**已经是死信**的任务如何**人工恢复**」——**两者不是同一个决策**：
前者问「要不要新增进入 `DEAD_LETTER` 的路径」，后者问「`DEAD_LETTER` 要不要有一条**出边**」。
ADR-0030 的选项 D 的**机制观察**（「新迁移只要**不从终态出发**就不破坏终态语义」）**在结构上
最贴近**本 EC；但 D 本身是「移动验收门的次序」，**不是**恢复路径 ⇒ 本 EC 的候选做法：

- **候选 I（首选）**：**新增一条从 `DEAD_LETTER` 出发的显式恢复迁移**（事件名待定，
  如 `REQUEUE`），并**明确修订 `terminal()` 的语义**（`DEAD_LETTER` 移出自动终态集，
  或引入「终态但可人工恢复」的分类）；代价 = 5 个 adapter 守卫逐条审查 + 事件链要有新规则；
- **候选 II**：**新增 ADR 记录「死信不是终态，是等人值守的状态」**，把候选 I 的语义修订
  写成决策（`Status: Accepted` of a new ADR，或按本仓惯例 `Proposed` 并说明为何够用）；
- **候选 III**：**不改状态机**，在 adapter 层加 `requeue` 写面（把 `DEAD_LETTER` 行直接改回
  `QUEUED`，绕开状态机）—— **明确否决**：绕过状态机 = 静默改语义，违反本 GOAL 的禁令。

**本轮决定（驱动决定，登记在「决策登记」）**：**候选 I + 候选 II 组合** —— 在
`packages/domain/task_state.py` 加一条**显式人工恢复迁移**，并**新增 ADR** 记录这次语义修订
（理由：`DEAD_LETTER ∈ terminal()` 是既有设计决定，按本 GOAL 的禁令「改它必须留 ADR」）。
`terminal()` 的修订方案与影响面在 EC-01 的实跑里逐条取证。

### 3. `run_resume` 的**真实覆盖度**（EC-03 的前置读数）

复核命令与读数：

```bash
rg -n "def rebuild_and_resume" -A 40 services/api/run_resume.py   # 152 行全读
rg -n "def resume_rebuilt" -A 20 packages/application/run_orchestration/service.py
rg -n "def _remaining_specs" -A 25 packages/application/run_orchestration/service.py
rg -n "def _dispatch_due" -A 20 services/api/scheduler.py
```

逐条读数（**覆盖**与**不覆盖**）：

| 情形 | 覆盖？ | 证据 |
| --- | --- | --- |
| **run 级**（不是 task 级）：`PAUSED` run 按 durable 来源重建上下文再续跑 | ✅ | `run_resume.py::rebuild_and_resume` → `_resume_from_source` → `service.resume_rebuilt` |
| 有冻结正文 ⇒ 自包含重建（不碰外部来源） | ✅ | `rebuild_readiness` 的 `REBUILD_SELF_CONTAINED`；`run_resume` 的 `protocol_body` 分支 |
| 无冻结正文 ⇒ 来源依赖重建（路径/草稿仍在才行） | ✅ | `REBUILD_SOURCE_DEPENDENT`；拒绝时**同时点名**缺正文与解析失败 |
| 旧 run（无来源登记）⇒ 早退拒绝 | ✅ | `readiness.early_refusal()`；`test_rebuild_readiness.py` |
| preflight 不过 / 语义漂移 ⇒ 拒绝 | ✅ | `resume_rebuilt` 内 `assert_semantics_frozen`；`test_restart_rebuild_resume.py` 有两条 |
| **进程重启后未完成任务**（重排到期） | ✅ | `RetryDispatchScheduler`（15s）扫 `PAUSED` + `due_retry_task_ids` ⇒ `continue_from_rebuild`；`test_restart_rebuild_resume.py::test_a_restarted_process_finishes_a_parked_run_from_its_recorded_source` |
| **租约过期** | ✅（**任务级**，不属 `run_resume`） | `recover_expired_leases()`：`EXPIRE_LEASE` → `QUEUED`；`LeaseRecoveryScheduler`（30s）；`test_workflow_restart_recovery.py` 3 例 |
| **死信任务能否被它捞回？** | ❌ **不能** | `_remaining_specs` 只跳过 `SUCCEEDED`；死信任务**不在** `CLAIMABLE_STATUSES` 里 ⇒ 重建后 `acquire_lease` 被 `terminal()` 守卫**点名拒绝**（实跑读数见 EC-01，本轮一并取证）；这正是 `R26-1` 的用户可见后果 |
| 已成功任务不重跑 | ✅ | `_remaining_specs` 按 `idempotency_key` 对齐 canonical；`test_already_finished_work_is_not_delivered_again_after_a_rebuild` |

**结论**：`run_resume` 是**run 级**入口，覆盖「重启后停车 run 的重建续跑」与「重排到期的自动
派发」；**不覆盖死信任务**（那是 EC-01）。EC-03 的本轮范围 = 把上表的**覆盖/不覆盖逐条变成
判据**（含实跑与反证），并把「死信捞回」的读数作为 EC-01 的输入（不重复实现）。

### 4. 三项的**同步集**（改它们会打红哪些既有判据 / 快照 / 声明面）

| 项 | 会打红的既有面（实测标定） | 同步方式 |
| --- | --- | --- |
| EC-01（加恢复迁移 + 修订 `terminal()`） | ① `test_workflow_dead_letter_surface.py::test_dead_letter_has_no_outgoing_transition`（**必然红**：它钉「无出边」）；② `tests/domain/test_state_machines.py` 的 `termal → DEAD_LETTER + ENQUEUE` 参数行（**仅当**恢复事件取 `ENQUEUE`）；③ `test_workflow_cancel_semantics.py::test_cancel_is_terminal_in_the_state_machine`（断言 `DEAD_LETTER in terminal()` —— **若修订 `terminal()` 则必红**）；④ `test_task_state_drivers.py::_DRIVEN_BY`（登记面）；⑤ `docs/reliability/RUN_STATE_MACHINE.md` 的迁移表 + Terminal 行（**输入登记面**） | 仅限 fix_policy 点名的四条：**按新事实重新定基**（受判面扩大不收窄）+ before/after 逐字节对照 + 强度未降自证 |
| EC-02（新增 relay 判据） | 无既有判据被打红（纯新增）；**未启用组合根**的读数已由 `tests/api/test_ops_schedules_api.py:120` 钉住（`executor_attached is False`）⇒ 新判据引用它、不改它 | 纯新增 |
| EC-03（新增覆盖度判据） | 无既有判据被打红（纯新增） | 纯新增 |
| 新 ADR（EC-01 语义修订） | `docs/INDEX.md` 需登记（索引面）；`tests/tooling/test_pending_validation_failure_registration.py` 钉的是 **ADR-0030 必须仍是 `Proposed`** ⇒ **该 ADR 一字不动**（本轮的语义修订写**新 ADR**，不碰 ADR-0030）；`test_landed_decisions_are_citable.py` 钉 ADR-0031/0032 ⇒ 不碰 | 纯新增 + 索引一行 |

### 5. 记录面与门（本轮受判面）

- `.cursor/plans` 在 `test_reproducibility_wording.py` 的扫描面内 ⇒ 本记录**不得**出现
  肯定式「完全可复现 / fully reproducible」（引用或否定式放行）；
- `.cursor/plans/goals/**` 是 `test_delivery_semantics_wording.py` 的**规则文本面**：
  **凡引用 exactly-once 的 GOAL 文件必须同时含禁令词**（禁止 / 不得 / 否认 / 不做 /
  BLOCKED / 口径）—— 本文件**已含**这六个词；
- 健康顺序（GOAL-019 的教训）：**先写记录 → 记录面判据 → 全量门**；m0 必须**独占**且在
  记录写入**之后**跑；m0 计数口径 = 终局行 `PASS: profile=m0; 23 deterministic checks`
  （`PASS [` 行数 24 含计数外的一条，承 `MEM: m0 profile roots & count`）；
- **一个 cycle 一次推送**（避免 `cancel-in-progress` 取消在飞 M0，承 GOAL-030 的流程自省）。

### 6. 建档基线的 `sha256`（EC-01 同步集的 before/after 比对基准）

读数（`sha256sum`，建档当日）：

| 文件 | 基线 `sha256` | 用途 |
| --- | --- | --- |
| `packages/domain/task_state.py` | `9114418ad43eddef289a1d579b891f0d1983fd538fbd50ff27fd5985c6ce885e` | 恢复迁移的前后对照 |
| `adapters/sqlite/workflow_ops.py` | `4a9c2b3e6ef8f2e9080d5663f5c4c05640625d5f9123c6bb441e649f7da217e6` | `terminal()` 消费点对照 |
| `adapters/postgres/workflow_ops.py` | `b751d566e346674e87a2b022e9995d8c8263356c778aa57d8090f085d44d0b31` | 同上 |
| `packages/application/ports/workflow_engine.py` | `1549a5960e2523b35c14ae460ba38cfe2b5d77bc245633c8030785d3bcbd1473` | 新 Port 方法的对照 |
| `tests/adapters/sqlite/test_workflow_dead_letter_surface.py` | `2d335f5e7cc24520401b81013d6a2b607658b788c662531d7710704706cb1c26` | **重新定基**的 before 字节 |
| `examples/config/policy.yaml` | `e7205cee8f819c672315a4d6f02aed2ddff176de6ebcad0e51397f206eea10c0` | 本轮**零改动**的对照 |
| `adapters/postgres/outbox_relay.py` | `227f1b9be422aa9f86ca5c429e2e8b5ab1184d49075743aadaa2187257007346` | EC-02 实现面基线（只读） |
| `services/api/scheduler.py` | `e870b1ee17b1732434e406d17a98ed4735e745e934de95a35312ff4766d7f03a` | 同上 |

`policy.yaml` 的读数（GOAL-031 后的终值，**本轮不动**）：`allow` **18** 条 +
`allow_with_constraints` **3** 条 + `require_approval` **5** 条（3 capability + 2 action）+
`deny` **3** 条；`default_effect: DENY`。**注**：提示词的起点表述记作「5 require_approval +
3 deny」，实测 `deny` 段是 3 条（`network.public` + 两个 action）⇒ 与起点表述**一致**；
`require_approval` 段的条目数按 capability 计为 3、含两条 action 规则为 5 ⇒ 两种数法都可读，
以条数为准。

## 决策登记（逐条状态）

> 触发依据：用户 2026-10-06「所有权限下放给驱动，用户只保留总目标」⇒ 此前登记为「需用户
> 拍板」的项**全部由驱动决定**。**全局禁令四条**（不列入计数，贯穿全 GOAL）：
> ① 不得**放宽任何既有判据的断言**（含 skip / xfail / 降强度 / 受判面收窄）；② 不得
> **宣称项目安全**（`R-M1`）；③ 不得宣称投递语义为「恰好一次」（**明确否认**）；
> ④ 不得**静默改 `terminal()` 语义**（必须留 ADR）。

| # | 项 | 状态 | 理由 / 边界 |
| --- | --- | --- | --- |
| ① | `R26-1` 死信人工恢复路径 | **授权开工** | §7 明文要求；ADR-0030 的 D 方案机制观察最贴近；实现取候选 I + 新增 ADR |
| ② | `R26-5` 取证追认 | **授权开工** | 实现已在树（`ed2fa0e` 起）且生产启用；本轮补判据 + 记录更正 |
| ③ | 研究连续性（`run_resume` 覆盖度） | **授权开工** | 勘察已给出逐条覆盖矩阵；本轮把「覆盖/不覆盖」变成判据 |
| ④ | 同步集（声明面 / 文档 / 射程 / 镜像表） | **授权开工** | 仅限 fix_policy 点名的四条；其余 ⇒ BLOCKED |
| ⑤ | 修实现过程中发现的真缺陷 | **授权开工** | 「只收紧」优先；放宽面 ⇒ BLOCKED |
| ⑥ | 默认 runtime 改真 | **决定不做** | AGENTS.md §11（真实 LLM 不得成为默认 CI 依赖） |
| ⑦ | 读面认证 | **决定不做** | 另一条谱系（GOAL-019/020/021 已收口写面）；单列范围外 |
| ⑧ | 多租户 · RBAC · BOLA·BFLA | **决定不做** | M18 deferred（既有登记）；无隔离模型时做授权只会造出「看起来安全」的假象 |
| ⑨ | D 组审批通道 | **决定不做** | 审批通道未接通 ⇒ 触达即 BLOCKED；本轮不碰 D 组 |
| ⑩ | `G24-5` 运行时拦截器 | **决定不做** | 条款改为运行时产品行为超出本轮射程；原样登记 |
| ⑪ | 部署面验证 | **决定不做** | 标签保持「未验证」（无部署面可验；不推定） |
| ⑫ | `R26-2` 工具面断路器接通 | **决定不做** | 条件不满足：需产品级阈值来源与状态持久化决策 |
| ⑬ | `R26-3` 在飞取消信号 | **决定不做** | 条件不满足：需 worker 协议与 fencing 语义变更 |
| ⑭ | `R26-4` 非幂等补偿 | **决定不做** | 条件不满足：需「哪些动作非幂等」的产品级声明面 |
| ⑮ | `R26-6` HTTP 幂等 store 跨副本 | **决定不做** | 条件不满足：改 `IdempotencyMiddleware` 语义（既有禁改面） |
| ⑯ | 把 destructive 能力从 `require_approval` 改 allow | **决定不做** | AGENTS.md §9 默认 deny 的护栏；审批通道未接通 ⇒ 维持阻断 |
| ⑰ | `DEAD_LETTER` 的 `terminal()` 语义修订 | **授权决定（留 ADR）** | 属「有界改产品语义」的授权面；**必须**新增 ADR 记录，**不得**静默改；影响面 5 个 adapter + 既有判据逐条说明 |
| ⑱ | 恢复迁移的**事件名** | **授权决定** | 若取 `REQUEUE`（新事件）⇒ 既有 `test_terminal_states_are_final` 的 `ENQUEUE` 参数行**逐字不动**（更小的同步面）；若取 `ENQUEUE` ⇒ 需按同步集③重新定基。**优先后者**（新事件名，同步面最小） |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按「迭代日志」最后一行 + 工作树/远端实况
判定续点（与 `goals/README.md` 同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件（迭代日志 / 状态历史 / EC 状态），保证任意时刻崩溃后重入可续；
**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**（进入 cycle 时在迭代日志声明 owner 行）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；写子 PLAN
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261007-032` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 记录面判据 → 全量门**；m0 按组、**独占**、仓库 `.venv`、
  `uv run --frozen --no-sync python -B`、**不接管道**（避免缓冲吞输出）；受影响的定向套件
  （`tests/domain` / `tests/adapters` / `tests/application` / `tests/e2e` / `tests/postgres`）；
  web 门按改动面（本 GOAL 预期零 web 改动）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run（脚本口径见「CI 台账」节）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤；
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **先复核再依赖**：起点事实全部待复核（其中 `R26-5` 的登记已被建档实测推翻）；
  出入以实测为准并写进「事实层结论」；
- **改终态语义要留 ADR**：`DEAD_LETTER` 属 `terminal()` 是既有的设计决定；改它 =
  改语义 ⇒ 按 ADR-0030 既有方案或**新增 ADR**，**不得**静默改；
- **只追加的事实更正**：GOAL-026 的正文是历史记录（不可变）⇒ 更正写在本轮，**不改历史 GOAL**；
- **受判面不得是交集**（承 GOAL-029 掩蔽教训）：新判据的受判面必须是**声明集**本身；
- **真被使用才算数**：断言调用证据 + 下游消费证据，不得只断言「注册了」/「返回成功」；
- **点名失败而非静默**：不可恢复输入 / 未启用组合根 / 缺判据一律点名；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次，避免取消在飞 run）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；本地假绿（Linux 侧复验链接类判据）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP DNS 出网判据、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 组合跑顺序） | 按既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | validator / Mimosa / 记录面判据命中新增项 | 按各处置文档修或登记；**不得绕过**；不得宣称安全 |
| 资源阈值型偶发 | 例如 CI 上 RSS < 128MiB 类阈值判据偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |

## 终止与收口

- **ACHIEVED 前置**：四条 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure`（验证器进树 + 两树 + 归档 + m0 +
  治理 + 台账）并声明 `verify_paths` ≥ 2 路、**用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers`（含「需改同步集以外的既有判据断言」）或
  `budget.max_cycles` 触顶（20）；停下留人工决策，逐条写明触发项。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停止并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；`W31-1`…`W31-4`；`W27-*` / `W10-12`；历史 `tools/`
目录仍有 73 条旧 lint 与无机器门的旧脚本（`tools/` 不过四道门，只有**被点名脚本**有界受判）；
GOAL-019…031 的未覆盖范围原样保留。

### `R26-*` 终态表（本轮更新）

| 项 | 本轮终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **收口**（EC-01） | §7 明文；本轮实现 + 判据 + 实跑 |
| `R26-5` 应用级消费者 | **更正**（EC-02(e)） | 实测：relay 实现早已在树且生产启用 ⇒ 登记过期；**残余** = 按偏移量物化业务事实的消费者仍不存在（如实登记，不在本轮实现） |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足（决策登记 ⑫–⑮） |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构，不重开 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**恢复迁移的语义边界**：`terminal()` 若修订为「终态但可人工恢复」，
  需逐条审查 5 个 adapter 守卫点；本轮**只覆盖** `DEAD_LETTER` 的人工恢复这一条路径，
  **不**覆盖「自动恢复」（重排由 dispatcher 管，属既有面）。
- （建档时登记）**`run_resume` 是 run 级**：task 级的死信恢复（EC-01）与 run 级的重建续跑
  （EC-03）是两条不同入口；两者的**协同**（死信恢复后 run 是否需要 resume）在本轮**只登记
  读数**，不实现自动协同（属新机制）。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**（读面认证是另一条谱系，本轮单列范围外）；**多租户未做** / **RBAC 未做** /
**BOLA·BFLA 未做**（M18 deferred）；**部署面未验证**（标签保持「未验证」）；
**D 组审批通道未接通**（`external.publish` / `package.install` / `git.commit` /
`workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**
（`consumer_offsets` 只在文档）；**不得**据此宣称项目安全；**不得**宣称投递语义为
「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的
> 「回顾性台账」提交自身不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以
> 「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| commit | 结论 | run / 说明 |
| --- | --- | --- |
| （待首个提交） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 待推送 | 只读勘察（三项起点事实逐条实测 + 同步集标定 + 基线 `sha256`；主树零改动）+ 治理 `validate.py` | 随建档提交登记 | — | 四 EC 未开启 | cycle 1 = EC-01（死信人工恢复：ADR 依据已定候选 I + 新 ADR；同步集四条已标定） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-07 | ACTIVE | **建档（cycle 0）**：读 `goals/README.md` 的 GOAL 格式契约 + 只读勘察（主树零改动）。**三项起点事实逐条复核**：**① `R26-5` 的实现与启用均已在树**（`PgOutboxRelay` 自 `ed2fa0e` 起、`OutboxRelayScheduler` 5s、`pg_composition.py:318` 生产启用、SQLite 根未启用）⇒ **GOAL-026 的登记被推翻**，本轮只**追加**事实更正；**② `R26-1` 是真缺口**（`DEAD_LETTER` 在 `terminal()` 且无出边；`terminal()` 的全部消费点 = 5 个 adapter + 2 条既有判据，逐条点名）；**③ `run_resume` 覆盖矩阵**（run 级重建续跑 ✅ / 重启后重排续跑 ✅ / 租约过期 ✅（任务级）/ **死信捞回 ❌**）。**同步集实测标定**（EC-01 会打红 `test_dead_letter_has_no_outgoing_transition` 与 `test_cancel_is_terminal_in_the_state_machine` 等，逐条列入 fix_policy 点名例外）；**决策登记 18 项**（5 授权开工 / 11 决定不做 / 2 授权决定含「改终态语义留 ADR」）。四 EC 全 `PENDING`。**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
