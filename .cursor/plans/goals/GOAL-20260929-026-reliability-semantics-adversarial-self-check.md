---
id: GOAL-20260929-026
slug: reliability-semantics-adversarial-self-check
title: 可靠性语义对抗性自检（AGENTS.md §7 九项义务逐条取证 + 做不到的部分明确否认）
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-29 用户会话指令（goal 模式）：**建档 GOAL-026（可靠性语义对抗性自检：九项 §7 义务的逐条取证）
    并授权本驱动自动化循环推进、无需我确认**。authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为「把 AGENTS.md §7 的**九项义务**
    （**idempotency key** / **Task lease + heartbeat** / **retry classification** / **exponential backoff** /
    **circuit breaker** / **dead-letter · manual recovery** / **cancellation semantics** /
    **compensation for non-idempotent actions** / **transactional outbox**）各自从「**代码里有**」
    推进到「**有判据证明它真的成立**」，并**明确否认**任何做不到的部分」—— 即**只做证明与判据**
    （**不加新能力**、**不放宽任何判据**、**不改安全策略**、**不改任何既有判据**）。
    (1) **授权范围（严格限于）**：(i) **新增判据**（一律落 `tests/**`；落在既有 `python/tests`
    收集面内 ⇒ m0 条数**仍 23**）；(ii) **新增探针 / 夹具**（进树；若新增脚本落 `tools/`，
    **必须**显式加入 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` —— **纯收紧**）；
    (iii) 修**被新判据证明为真缺陷**的问题（**只允许收紧**：补幂等键 / 补去重 / 修 retry 分类 /
    补 heartbeat / 修 outbox 写入原子性等；**不得**借此改认证面、策略面、门禁阈值或安全语义）；
    (iv) 文档同源更新（`docs/` 下可靠性相关页 + `docs/INDEX.md` 登记）。
    (2) **明确不做（命中即 BLOCKED）**：任何「**假装 exactly-once**」的实现或措辞（AGENTS.md §7 明文禁止）；
    **修改**任何既有判据 / 门禁 / 阈值 / 放行面（**新增**可以）；改 `PRODUCT_ROOTS` / m0 任一 check /
    作业结构 / m0 条数（终态行必须仍是 `23`）；**新增依赖**（标准库 + 现有栈；**不得**引入真实 broker /
    Redis / Celery 等）；**真实出网**、真实 runtime、真实 tool provider、真实凭据（本 GOAL **全离线**，
    用 Fake runtime / Fake gateway / SQLite 或既有测试 DSN）；读面认证、多租户 / RBAC / BOLA·BFLA、
    `G24-4` / `G24-5`（**需用户单独拍板**，本轮只登记）；把真实 prompt / token / 凭据写进任何地方；
    动 `undici`；改 `ADR-0031` 的 `Status`；**宣称项目安全**（`R-M1` 仍在）；**宣称 exactly-once**。
    (3) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、**不 force**、
    **不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）+ **默认姿态不变**
    （默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）+ **默认门一律离线**
    （`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (4) **边界（承继）**：GOAL-001…025 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的**全部 13 项 `D-NN`** 已结清、**本 GOAL 不重开**；GOAL-019…025 的**未覆盖范围原样保留**。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >-
    对 AGENTS.md §7 的**九项义务**逐条做**对抗性自检**：每一项要么被**新判据**证明成立
    （**受判面非空** + **两向反证** + **按压先红后绿** + **逐字节复原**），要么**收窄为机械事实**
    （把散文式旧判词换成结构化断言），要么**逐条登记为 PENDING + 理由**（本机不可判定 /
    需用户拍板）—— **不得**用离线夹具假装取过证，**不得**把「代码里有」写成「已证明」。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**不修改任何既有判据**（只**新增**）；
    零新依赖；零策略面 allow；**全离线**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1` 仍在）；
    **不得**宣称 exactly-once（口径固定为 **at-least-once + idempotency + deduplication**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **幂等与去重（idempotency key + deduplication）**：① 写面 `Idempotency-Key` 的**重放**返回
      **同一结果**（状态码 + 正文 + `ETag` 三件套逐字符相等），且该取证必须打在**生产存储**
      （`SqliteIdempotencyStore`）上——既有 HTTP 判据注入的是 `InMemoryIdempotencyStore`；
      ② **同键不同载荷 ⇒ conflict**（422 `Idempotency-Key Reused`，**不得**静默复用）；
      ③ **无键 ⇒ 拒**（422 `Idempotency-Key Required`）；④ **域级去重**：同一 `idempotency_key`
      在 canonical 层**不产生第二条业务事实**（按存储行计数断言，不靠文本）；
      ⑤ **跨会话重放**（同一 store 文件、新 store 实例 + 新应用 + 新客户端）三件套结论一致。
      **两向反证**：把去重键换成随机值 ⇒ 判红（重复写入被观察为第二条事实）；
      **不同键 ⇒ 不判红**（第二条事实**应当**出现，证明断言非空转）；复原 ⇒ 绿。
      **另一条路径（重放来源）**：篡改**持久化行**（状态码 + 正文 + `ETag`）后重放 ⇒
      若重放**原样跟随**被篡改的值，则「同一结果」的来源是**读持久化行**而**不是**路由被重新执行的幂等假象。
      **注意**：`IdempotencyMiddleware` 与 `Idempotency-Key` 的**语义不得改动**（承 GOAL-019 判词），
      本 EC **只加判据**。**登记面**：store 是**节点本地**（PG 模式亦为 SQLite）/ check-then-act
      无 in-flight 标记（并发同键）⇒ 逐条登记为残余，**不得**宣称跨副本保证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api/test_idempotency_sqlite_semantics.py
      tests/e2e/test_idempotency_canonical_dedup.py -q` ⇒ 全绿（**实测 6 passed**）；配套留档：
      重放三件套实测值、计数证据（canonical 行数 1 / 异键 2）、按压先红后绿 + raw `sha256` 逐字节复原、
      第二条路径（篡改持久化行 ⇒ 重放原样跟随 ⇒ 来源是 store 行）。
    status: PASS
  - id: EC-02
    criterion: >-
      **租约 / 心跳 / 重试分类 / 退避（lease + heartbeat + retry classification + backoff）**：
      ① **lease 到期**：持有者失效（时钟推进过 `expires_at`）后任务可被**另一次 claim** 取得
      （fence 前进，**不得**永久卡死）；② **心跳**：心跳续租使 lease **不失效**（过原 TTL 后
      `recover_expired_leases()==0` 且任务仍 `LEASED`），**停止心跳后按预期到期**
      （过新 `expires_at` 后回收 1 条 → `QUEUED` → 二次 claim）；③ **重试分类**：可重试类与
      不可重试类**分别命中不同的结构化值**（`FailureAction` / 任务状态 / `FailureCategory`），
      **不靠错误文本子串**；④ **退避**：连续失败的重试间隔**单调不减**且**有上界**
      （`TaskContract.retry_delay` 的指数式 + `max_backoff_seconds` 帽），**经引擎路径**
      （真实写入的 `retry_at`）断言而非纯函数采样；⑤ **重试次数上限**：耗尽后进入终止态
      （接 EC-03 的死信面）；⑥ **worker 面续租**：续租线程**真的发生**（`renews > 0`，
      既有判据只记录该计数、从不断言其非零）。
      **两向反证**：把退避改成常量 ⇒ 判红；把不可重试类改成可重试 ⇒ 判红；复原 ⇒ 绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_workflow_lease_lifecycle.py
      tests/adapters/sqlite/test_workflow_retry_trajectory.py tests/worker/test_worker_renew_loop.py -q`
      ⇒ 全绿；配套留档：时钟注入下的 `expires_at` / `retry_at` 实测序列表、回收计数、
      按压先红后绿 + raw `sha256` 逐字节复原。
    status: PENDING
  - id: EC-03
    criterion: >-
      **断路器 / 死信 / 取消（circuit breaker + dead-letter + cancellation）**：
      ① **断路器**：模型端点面（`OpenAIChatGateway`，**产品装配路径**）三态各有**结构化断言** ——
      连续失败达阈值 ⇒ **OPEN**（后续调用**快速失败且不触达下游**，以 `transport.calls` 计数为证）；
      冷却后 **HALF_OPEN** 探针；成功 ⇒ **CLOSED**；并**判定** `gateway.py:108-111` 的
      **半开探针预算被吞**（注释称拒绝、实际放行）是否为**真缺陷** —— 若为新判据证明的真缺陷 ⇒
      按授权**只收紧**（最小改动让快速失败成立）并两向按压；若判定为不可在本轮安全收紧 ⇒
      **登记为残余 + 证据**，**不得**顺手改语义；
      ② **dead-letter**：超过重试上限的任务进入**可枚举的终止态**（按 run 枚举，逐行断言
      `status=DEAD_LETTER` 且 `attempt >= max_attempts`）且有**结构化**证据表明完成重放是
      幂等 no-op；**人工恢复路径**当前**不存在**（`DEAD_LETTER` 无出边、`ADR-0030` 明文
      「没有任何路径」且把恢复选项留作**未决**）⇒ 以**结构化断言**把这一边界钉成机械事实
      （断言状态机无出边）+ 登记为**需用户拍板**的残余，**不得**实现恢复路径（= 新能力 + 改 Accepted ADR）；
      ③ **取消语义**：任务/运行层取消**幂等**（第二次取消结论一致、按结构化返回值断言）；
      取消后**不再产生新副作用**（取消后陈旧完成 / 二次操作**不产生新事件**，按 outbox 行计数断言）；
      已发生的副作用**无补偿**（接 EC-04，登记）。
      **两向反证**：断路器阈值调成不可能达到 ⇒ 判红；取消后仍产生副作用 ⇒ 判红；复原 ⇒ 绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/relay/test_gateway_half_open_budget.py
      tests/adapters/sqlite/test_workflow_dead_letter_surface.py
      tests/adapters/sqlite/test_workflow_cancel_semantics.py
      tests/application/test_tool_plane_breaker_boundary.py -q` ⇒ 全绿；配套留档：三态转移实测序列
      （含下游调用计数）、死信枚举行、取消后事件计数、工具面断路器边界的结构化断言与
      非空 PENDING 理由、按压先红后绿 + raw `sha256` 逐字节复原。
    status: PENDING
  - id: EC-04
    criterion: >-
      **补偿与事务性发件箱（compensation + transactional outbox）**：
      ① **outbox 原子性（失败注入）**：在**同一提交块内**制造异常（业务写之后、提交之前）
      ⇒ **业务事实与域事件同时不可见**（all-or-nothing）；成功路径 ⇒ **两者同时可见**；
      既有判据（`test_events_are_written_transactionally` / `test_outbox_atomic_with_task_transition`）
      **都是全绿路径**，本 EC 补的是**失败注入**这一向；**反向**：把事件写进**另一个事务** ⇒ 判红；
      ② **至少一次投递 + 去重面**：同一事件重复投递 ⇒ 存储 / 出口边界**只留一条**（按主键 + 行数断言）；
      并把仓内**所有**接收事件的边界**逐条枚举**（`INSERT OR IGNORE` 写点、读面游标、运行时事件去重），
      **断言清单下界**（承 MEM-160），每条给出「去重键 = `event_id`」的结构化证据；
      如实登记**仓内不存在「按事件物化业务事实」的应用消费者**（PENDING + 理由）；
      ③ **补偿判定**：把仓内**唯一可调用**的补偿（恢复失败的 canonical 状态回滚）做成**可复核**判据
      （点名补偿了什么、依据哪条事实、事件字段），并把**非幂等副作用的补偿缺失**登记为结构化边界
      （`COMPENSATING` 会话态无产品驱动、`compensation_actions` 只在文档里）—— **不实现新补偿**；
      ④ **明确否认 exactly-once 的机械判据**：在**有界且显式声明**的面上逐条分类 `exactly[ _-]once`
      的全部出现（**禁止 / 否认 / 登记豁免（理由非空）/ 肯定式声明**），**受判面非空**（下界断言）、
      **肯定式投递语义声明 ⇒ 判红**；并断言口径串（`at-least-once` + `idempotency` + `outbox`）在
      可靠性文档里在位。
      **两向反证**：把事件写进另一个事务 ⇒ 判红（原子性被破坏）；关掉消费者去重 ⇒ 判红；复原 ⇒ 绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_outbox_atomicity.py
      tests/application/run_orchestration/test_compensation_boundary.py
      tests/architecture/python/test_delivery_semantics_wording.py -q` ⇒ 全绿；
      配套留档：失败注入前后两张表的实测行数、去重边界枚举清单（含下界）、
      `exactly-once` 逐条分类表、按压先红后绿 + raw `sha256` 逐字节复原。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用 022 / 023 / 024 / 025 的机器）**：① 本轮收口验证器**进树**
      （`tools/verify_goal026_closeout.py`，复用 `tools/closeout_recheck_assertions.py` 的公共判词，
      只写本轮特有断言）并**显式加入** `IN_SCOPE`（**纯收紧**；注意 **450 行硬上限**，
      超限先搬公共部分）；② `tools/two_tree_recheck.py` 跑**当前树 + 干净 checkout**
      ⇒ 两树同结论（逐行相同 + `sha256` 相同；**留档一律二进制写盘**）；
      ③ **as-is 本机 m0 到 23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`），
      **运行发生在记录写入之后**（承 MEM-145）；④ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
      ⑤ **CI 台账到终态**（八 job + CodeQL + `run_attempt`），且**台账审计脚本自带下界判定**：
      新建 `tools/audit_goal026_ledger.py` 并进 `IN_SCOPE`，其判定为
      **`jobs` 为空 / 低于下界 ⇒ 该行判「未取证」**（**不得**记 OK）——
      这是 GOAL-025 的实测教训（`scratch/audit_goal025_ledger.sh:39-41` 对空 `jobs`
      **无条件**打 `-> OK`，其口径只写进了记忆、脚本未修），本轮由验证器**断言该下界逻辑存在**；
      ⑥ 承继残余逐条在位（**12 条承继** + `G24-1`…`G24-6`，其中 `G24-4` / `G24-5` 注明
      「需用户拍板」）+ 本轮新增残余（**九项义务里凡本机不可判定的，逐条登记为 PENDING + 理由**）；
      ⑦ **未覆盖范围逐条明写**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` 未收口）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal026_closeout.py
      --script-mode shared --root .` ⇒ 两树判词逐行相同 + `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；
      两路留档二进制一致（`cmp`）；m0 终态行实测；CI 台账逐 run 逐 job 实查（`run_attempt` 由 REST API）；
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_tooling_scripts_meet_product_gates.py -q`
      ⇒ `IN_SCOPE` 含本轮两个脚本且必备清单为**下界单调**。
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
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/e2e/test_idempotency.py`、
      `test_retry_park_and_resume.py`、`test_workflow_restart_recovery.py`、
      `tests/adapters/sqlite/test_workflow_engine.py`、`test_workflow_retry_policy.py`、
      `test_workflow_retry_backoff.py`、`test_workflow_cancel_run.py`、
      `tests/domain/test_circuit_breaker.py`、`tests/domain/test_retry_backoff.py`、
      `tests/adapters/relay/test_gateway_circuit.py`、`tests/application/test_tool_plane.py`、
      `tests/api/test_idempotency_ifmatch.py`、`tests/api/test_api_restart_recovery.py`、
      `tests/contracts/test_m13_r1_store_contracts.py`、
      `tests/tooling/test_console_stub_idempotency_parity.py`、`tests/postgres/**`、
      `tests/distributed/**`、`tests/tooling/test_tooling_scripts_meet_product_gates.py`、
      `tests/egress_guard.py`、三道记录面判据、多路证据判据、射程边界判据）—— **新增**判据不受此限
    - >-
      改 `IdempotencyMiddleware` / `Idempotency-Key` 的**语义**（方法分类 / replay / conflict /
      record 行为；承 GOAL-019 判词）—— 本 GOAL 对该面**只加判据**
    - >-
      引入**真实** broker / 外部队列 / 消息中间件（Redis / Celery / RabbitMQ / Kafka 等），
      或**新增任何依赖**（含为判据引入第三方库；一律标准库 + 现有栈）
    - >-
      在记录 / 判词 / 文档 / 代码注释里写下 **exactly-once 的肯定式声明**（口径只能是
      **at-least-once + idempotency + deduplication**；AGENTS.md §7 明文禁止「假装实现 exactly once」）
    - >-
      用 **skip / xfail** 处理取不到的路径，或以「受判集合为空」的空真充当通过
      （承 MEM-156：受判面非空是交付前提）
    - >-
      用**真实出网**换取更强取证（真实中转站 / 真实 runtime / 真实 tool provider 一律**不得**
      成为本 GOAL 的取证手段；不可在本机验证者**登记 + 给可复核检查项**）
    - >-
      把**真实** prompt / token / 凭据 / 用户内容写进夹具、记录、日志、遥测或以任何形式留档
      （凭据只登记变量名、绝不留值；测试与夹具一律**合成值**）
    - >-
      改 `PRODUCT_ROOTS` / m0 任一 check / 作业结构 / m0 条数（终态行必须仍是 `23`）——
      **立即 BLOCKED**
    - >-
      **新增能力**：实现死信人工恢复路径、接通工具面断路器、把取消信号接进在飞远端作业、
      新建应用级事件消费者—— 这些属于**产品行为变更 / 新能力**，本轮**只允许登记**；
      若新判据证明其为缺陷，仍需**用户拍板**后另立 GOAL
    - >-
      给读面（GET / HEAD）加认证，或改读面放行语义（GOAL-019 判词 (i) 不变：保护范围**只有写面**）
    - >-
      引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容；
      或做 **BOLA / BFLA 的专项实现**
    - >-
      把**新判据**写成「被文档引用 / 字面量喂饱」的形态（承 MEM-141：判据必须绑定
      **结构化字段 / 状态机 / 存储行 / 行为**），或让新判据**跳过按压**
    - >-
      动 `G24-4` 的 DTO 契约或 `G24-5` 的运行时拦截器（两者**需用户单独拍板**）
    - >-
      改认证的 401 响应形态、动 `undici`、改 `ADR-0031` 的 `Status`、
      把真实 runtime 设为**默认**（默认必须仍是 Fake）
    - >-
      宣称「项目安全」「授权面已覆盖」或任何形式的安全结论（`R-M1` 未收口）；
      宣称 exactly-once 或任何超出实跑证据的可靠性结论
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    **宣称 exactly-once**（记录 / 判词 / 文档 / 注释里的肯定式声明），或**假装实现 exactly-once**
    —— **立即 BLOCKED**（AGENTS.md §7 明文禁止）
  - >-
    **新增能力**（死信人工恢复 / 工具面断路器接通 / 在飞取消信号接通 / 新建应用级事件消费者）
    —— **立即 BLOCKED**，需用户拍板
  - >-
    **给读面加认证** —— **立即 BLOCKED**（GOAL-019 判词 (i)：保护范围**只有写面**）
  - >-
    **引入多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容，
    或做 **BOLA / BFLA 的专项实现** —— **立即 BLOCKED**
  - >-
    **新增依赖** / 引入真实 broker 或外部队列 —— **立即 BLOCKED**（判据只能用标准库 + 现有栈）
  - >-
    **把 token / 真实凭据 / 真实用户内容写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 /
    夹具 / 示例 / 判据源码）—— **立即 BLOCKED**
  - >-
    **改 `IdempotencyMiddleware` / `Idempotency-Key` 语义**，或改认证的 401 响应形态
    —— **立即 BLOCKED**
  - >-
    **放宽 / 削弱任一既有判据 / 门禁 / 阈值 / 放行面**，或**修改**任何既有判据
    （**新增**判据不受此限）—— **立即 BLOCKED**
  - >-
    **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**（`23` 这一终态条数；把 `tools` 纳入
    `PRODUCT_ROOTS` 属另行授权）—— **立即 BLOCKED**
  - >-
    **放宽 §9 默认 deny**，或新增任何策略面 allow / 类别级规则 —— **立即 BLOCKED**
  - >-
    **Canonical State 边界**（改「PostgreSQL Domain Entity 是业务真相」的口径，
    或把「域表里出现 `DEAD_LETTER` / 重复行」当成泄漏并据此改域模型）—— **立即 BLOCKED**
  - >-
    **动 `G24-4` 的 DTO 契约或 `G24-5` 的运行时拦截器**（两者**需用户单独拍板**）
    —— **立即 BLOCKED**
  - >-
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**（Mimosa 钩子
    `scanner_enobufs` 未得完整结论）
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20260929-245-goal-026-ec01-idempotency-and-dedup.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-246-goal-026-ec01-idempotency-and-dedup.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-167-replay-criteria-need-production-store-and-row-tamper-proof.md
---

## 目标与退出标准

**一句话**：AGENTS.md §7 列了**九项义务**；此前只有 §7 的**散文**与若干**局部判据**。
本 GOAL 去把每一项从「**代码里有**」推进到「**有判据证明它真的成立**」，
并把**做不到的部分明确否认**（收窄为机械事实，或登记为 PENDING + 理由）。

**本 GOAL 不加新能力、不改安全策略、不放宽任何判据、不修改任何既有判据。**
若新判据**证明**某处是真缺陷 ⇒ **只允许按授权收紧**（补幂等键 / 补去重 / 修 retry 分类 /
补 heartbeat / 修 outbox 写入原子性等；**不得**改认证面、策略面、门禁阈值或安全语义）；
若某条**本机无法判定**或**需要产品行为变更** ⇒ **登记为 PENDING / 残余**，**不得**记 PASS。

| 义务（AGENTS.md §7） | 归属 EC | 计划判定口径 |
| --- | --- | --- |
| **idempotency key** | EC-01 | 写面重放/冲突/拒 + 域级去重 + 跨会话 |
| **Task lease + heartbeat** | EC-02 | 到期回收 / 续租挡住回收 / 停跳按预期到期 |
| **retry classification** | EC-02 | 结构化字段（枚举 / 状态），两分类分别命中 |
| **exponential backoff** | EC-02 | 引擎路径的 `retry_at` 单调不减 + 有上界 + 耗尽终止 |
| **circuit breaker** | EC-03 | 产品装配面的三态 + 快速失败；工具面空壳登记 |
| **dead-letter · manual recovery** | EC-03 | 终止态 + 可枚举 + 重放幂等；**恢复路径不存在 ⇒ 收窄 + 需拍板** |
| **cancellation semantics** | EC-03 | 取消幂等 + 取消后无新副作用；在飞信号空壳登记 |
| **compensation** | EC-04 | 唯一可调用补偿判据化；**副作用补偿缺失 ⇒ 收窄 + 登记** |
| **transactional outbox** | EC-04 | **失败注入**的原子性两向 + 投递去重边界枚举 + 否认 exactly-once |

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **幂等与去重**（生产 store 上的三件套 + 域级计数 + 跨会话） | 两个新判据文件 + 按压/复原留档 | **PASS**（cycle 1） |
| EC-02 | **租约 / 心跳 / 重试分类 / 退避**（时钟注入两向 + 引擎路径轨迹） | 三个新判据文件 + 轨迹留档 | **PENDING** |
| EC-03 | **断路器 / 死信 / 取消**（三态 + 终止面 + 取消后无新副作用） | 四个新判据文件 + 边界登记 | **PENDING** |
| EC-04 | **补偿 / 发件箱**（失败注入原子性 + 去重边界 + 话术机械判据） | 三个新判据文件 + 分类表 | **PENDING** |
| EC-05 | **自举收口**（进树验证器 + 审计脚本下界 + 两树 + m0 + 台账 + 残余） | `tools/verify_goal026_closeout.py` + `tools/audit_goal026_ledger.py` | **PENDING** |

**依赖关系**：EC-01…EC-04 **互不依赖**（各自独立可验收、独立 RECHECK）；
EC-05 **依赖** EC-01…EC-04（收口验证器要断言前四者的终态与登记面）。
EC-05 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

### 建档当日已核实的**事实层结论**（全部实测，非推测；决定 EC 切分与哪些项必须登记为 PENDING）

> 方法：只读勘察九项义务的**代码面**（产品装配路径 vs 仅测试调用）、**既有判据面**
> （到底断言了什么 / 没断言什么）、**可注入缝**（时钟 / 阈值 / 传输层 / 存储）。
> 「代码里有」一律不算数——下面每条都标注**它是否被产品路径调用**。

1. **幂等（写面）已实测成立，缺的是「生产 store 上的取证」**：`services/api/middleware.py:59-101`
   的 `IdempotencyMiddleware` 按摘要（`sha256(method + "\0" + path + "\0" + raw body)`，
   `services/api/idempotency.py:48-56`，**不含 query string**）判重放 / 冲突；
   生产装配 `services/api/composition.py:399` 用 `SqliteIdempotencyStore`
   （`adapters/sqlite/idempotency_store.py:28-81`，表 `idempotency_responses` 以 `idem_key` 为主键）。
   **缺口**：既有 HTTP 判据注入的是 `InMemoryIdempotencyStore`
   （`tests/api/base_fixtures.py:129`、`tests/api/run_fixtures.py:168`）⇒ **生产 store 的 HTTP 语义无判据**；
   跨会话重放判据只断言 id 与列表长度、**不断言状态码 / 正文 / `ETag`**
   （`tests/api/test_api_restart_recovery.py:152-169`）。**⇒ EC-01 的判据落点明确。**
2. **幂等的存储边界（实测，必须如实登记）**：HTTP 幂等 store 在 **PG 模式下仍是 SQLite**
   （`services/api/pg_composition.py:307-315`）⇒ **节点本地、不跨副本**；
   且 `get → call_next → put` 是 **check-then-act**（无 per-key in-flight 标记）⇒ 并发同键未证伪。
   两条**都登记为残余**，**不得**宣称跨副本保证（授权范围不允许改语义）。
3. **域级去重已实测成立**：`tasks.idempotency_key` 偏 UNIQUE 索引（`adapters/sqlite/db.py:53,68-69`；
   PG `adapters/postgres/migrations/001_initial.sql:8,18-19`）+ `idempotency_records(operation_key PK)`
   （`db.py:124-129`）；重复提交是**静默 no-op（`deduped`）**（`adapters/sqlite/workflow_engine.py:287-296`；
   PG `ON CONFLICT DO NOTHING`，`adapters/postgres/workflow_submit.py:69-80`）。
   **缺口**：无「重放后 canonical 恰好一行」的**计数**判据，也无「异键 ⇒ 应当两行」的**两向控制**。
4. **租约已实测成立且** claim 与回收是**两条路径**：`leases(task_id PK, lease_id, agent_id,
   expires_at, heartbeat_at, worker_id, fence)`（`adapters/sqlite/db.py:72-80`）；
   claim **只取** `CLAIMABLE_STATUSES = {QUEUED, RETRY_SCHEDULED}`（`adapters/sqlite/workflow_claim.py:27-30,53-73`）
   ⇒ **claim 自己不回收过期租约**；回收走 `_recover_impl`（`adapters/sqlite/workflow_ops.py:362-400`：
   选 `expires_at < now OR worker state='LOST'`，删租约、置 `QUEUED`、发 `task.retry_scheduled(reason=lease_expired)`、
   指标 `WORKFLOW_LEASE_EXPIRED`），周期驱动 `services/api/lease_recovery.py:18-65`（默认 30 s）。
   **⇒ 「持有者失效后能被另一次 claim 取得」= 到期 + 回收 + 再 claim 三步，判据必须三步都观察。**
5. **心跳已实测成立，但「挡住回收 / 停跳后到期」的两向组合无人证**：
   `heartbeat` 匹配 `lease_id`、**轮换 lease_id**、`expires_at = now + ttl`
   （`adapters/sqlite/workflow_ops.py:233-264`）；既有判据只证「续租使 `expires_at` 变大 + 轮换 id」
   （`tests/adapters/sqlite/test_workflow_engine.py:76-88`）。worker 面 `renew_lease`
   （`workflow_ops.py:266-282`）由 `services/worker/loop.py:399-416` 的 `_renew_loop` 守护线程调用，
   而 `tests/worker/test_worker_loop.py` **记录 `client.renews` 却从不断言其非零**。
   **⇒ EC-02 的 ①②⑥ 三个判据点均可离线确定性取证（`now=` 可注入，见第 12 条）。**
6. **重试分类是结构化的（已实测），本 GOAL 只需扩面，**不得**改成文本匹配**：
   `FailureCategory`（22 值）/ `FailureAction{RETRY, DEAD_LETTER, FAIL}`（`packages/domain/enums.py:48-85`）；
   决策 `TaskContract.decide_failure`（`packages/domain/tasks.py:172-193`）与 `disposition`（`:154-170`）；
   异常侧 `PortError.retryable`（`packages/application/ports/errors.py:21-80`）。
   既有判据**已按结构化值**断言（`tests/adapters/sqlite/test_workflow_retry_policy.py:105-156`）⇒
   本轮**不得**重复造轮子，只补「分类 → 退避轨迹 → 终止态」的**联合**面。
   **实测的边界（登记）**：`PortError.retryable` **不是**重试决策的输入
   （决策看 `isinstance(TransientPortError)` + 类别表，`task_executor.py:116-123`）。
7. **退避公式已实测：指数 + 上界**，但**无整合轨迹判据**：
   `seconds = backoff_seconds * 2**(attempt-1)`、`min(..., max_backoff_seconds)`
   （`packages/domain/tasks.py:195-213`）；写盘 `retry_at`（`adapters/sqlite/workflow_ops.py:340-360`）；
   入队处统一校验（`workflow_claim.py:63`）+ 直取守卫 `RetryNotDueError`（`workflow_ops.py:66-75,171-175`）。
   既有判据只在**纯函数层采样三点 + 帽**（`tests/domain/test_retry_backoff.py:29-56`），
   引擎层只断言**第一次**延迟（`tests/adapters/sqlite/test_workflow_retry_backoff.py:116-132`）。
   **⇒ EC-02 ④ 的价值在「经引擎路径的多轮单调性 + 上界」。**
8. **断路器（模型端点面）是真的且产品已装配**：`OpenAIChatGateway` 每端点一断路器
   （`adapters/relay/gateway.py:84-87`），`_consult_circuit` 快速失败抛 `CircuitOpenRelayError`（`:97-118`），
   由 `complete` / `list_models` 调用（`:142,194`）；装配在 `services/api/composition.py:395` /
   `pg_composition.py:273`。既有判据**已含**端到端三态序列
   （`tests/adapters/relay/test_gateway_circuit.py:79-109`，含「快速失败且 `transport.calls` 不变」）。
   **⇒ EC-03 ① 不重做三态，而是判定下面这条实测到的边界。**
9. **断路器（工具面）是空壳，且半开探针预算被吞（候选真缺陷）**：
   `packages/application/tool_plane/health.py` **只被** `__init__` 再导出与测试调用
   （`tests/application/test_tool_plane.py:168-195`），`monitor_config()` **无参**且恒返回默认配置
   （`health.py:40-41`），只 import `initial_state/apply_success/apply_failure`
   ⇒ **`apply_tick` 从不被调用 ⇒ 一旦 OPEN 永不半开**；
   生产健康面走实时探针（`services/api/preflight_support.py:102-108`），**不读断路器状态**。
   另：`adapters/relay/gateway.py:108-111` 在**半开探针预算耗尽**时吞掉
   `CircuitBreakerTransitionError` 并**放行请求**（与紧邻注释「本次 consult 拒绝」相反），
   而既有判据只覆纯函数层的预算（`tests/domain/test_circuit_breaker.py:105-110`）。
   **⇒ EC-03 ① 的判据要给出「真缺陷 / 非缺陷」的**判定**与证据；工具面空壳只登记。**
10. **死信：终止态成立、可枚举只到 run 级、恢复路径不存在**：
    `ResearchTaskState.State.DEAD_LETTER` 为**无出边**终止态（`packages/domain/task_state.py:24,40,60,77-83`）；
    由 `FailureAction.DEAD_LETTER` 触发（`packages/domain/tasks.py:191-193` 规则 4）；
    写入 `adapters/sqlite/workflow_ops.py:298-361`；**枚举面只有** `list_tasks(run_id)`
    （`adapters/sqlite/workflow_engine.py:254`）经 `GET /runs/{run_id}/tasks`（`services/api/routers/runs.py:168-185`）
    ⇒ **无跨 run 的 DLQ 面，`services/` 与 `tools/` 下零 `DEAD_LETTER`**；
    **无任何恢复路径**，`docs/adr/ADR-0030-validation-failure-consumption.md:29-30,51-100`
    明文承认「没有任何路径」且把恢复选项留作**未决** ⇒ **实现恢复 = 改 Accepted ADR + 新能力
    ⇒ 本轮只收窄 + 登记「需用户拍板」。**
11. **取消：任务/运行层幂等已成立，控制面→在飞信号是空壳**：
    第二次 `cancel` 返回 `deduped`（`tests/adapters/sqlite/test_workflow_engine.py:139-147`）；
    `cancel_run` 第二次 0 条（`tests/adapters/sqlite/test_workflow_cancel_run.py:72-78`）；
    完成重放有 `_COMPLETION_ALREADY_APPLIED` 守卫（`adapters/sqlite/workflow_ops.py:51-62,308-313`）。
    **边界 A**：HTTP 第二次 `POST /runs/{id}/cancel` 返回 **409**（`CANCELLED` 无出边），
    与 router docstring 的「幂等」措辞**不一致**（`services/api/routers/runs.py:148-165`）
    ⇒ 判据要按**结构化事实**钉住「状态幂等、HTTP 码不同」，**不得**改行为。
    **边界 B（空壳）**：`execution_jobs.cancel_requested` 的唯一写点是
    `PostgresExecutionJobQueue.request_cancel`（`adapters/postgres/execution_job_queue.py:292-297`），
    唯一调用方是 `RemoteExecutionBackend`（`adapters/execution/remote_backend.py:151,154`），
    而**生产 worker 不构造它**（`services/worker/__main__.py:140-146`）⇒ **控制面取消不通知在飞远端作业**；
    `AgentRuntime.cancel`（`packages/application/ports/agent_runtime.py:139-143`）**无产品调用方**
    ⇒ **只登记**（接通 = 新能力）。
12. **可注入缝（实测，决定判据可离线确定性）**：SQLite 引擎构造子
    `SqliteWorkflowEngine(db_path=":memory:", *, connection=None, lease_ttl_seconds=300,
    now: Callable[[], datetime] | None = None, telemetry=None)`（`adapters/sqlite/workflow_engine.py:58-73`）
    是全链时钟缝（写 / 比较 / 判据都走 `self._now`）；继电器面 `OpenAIChatGateway(now=...)`
    + `httpx.BaseTransport` 注入（`adapters/relay/gateway.py:74-80`）；**无 freezegun**。
    PG 侧 `server_now` 让**假时钟无法推进** ⇒ PG 的到期类判据只能改行 / 真跑
    （`tests/postgres/test_workflow_retry_backoff_pg.py:120-131`）⇒ **本 GOAL 的确定性判据一律落 SQLite**，
    PG 只作**既有资产引用 + 登记**。
13. **发件箱：同事务写入已成立（代码事实），但失败注入判据缺失**：
    SQLite `outbox_events(event_id PK, envelope_json, created_at, published_at)`
    （`adapters/sqlite/db.py:131-136`）+ PG（`001_initial.sql:37-44`）；
    业务写与事件写**同块**：SQLite `with self._conn:`（`adapters/sqlite/workflow_ops.py:325-337`，
    块内注释已说明理由）、PG `with conn.transaction():`（`adapters/postgres/workflow_ops.py:135,172-179`）；
    事件写入器**不自提交**（`adapters/sqlite/outbox.py:24-49`、`adapters/postgres/outbox.py:20-24`）。
    **缺口（实测）**：`test_events_are_written_transactionally`
    （`tests/adapters/sqlite/test_workflow_engine.py:204-217`）与 `test_outbox_atomic_with_task_transition`
    （`tests/postgres/test_outbox_pg.py:50-64`）**都是全绿路径** ⇒ 「业务事实可见 ⇔ 事件可见」**未被证伪过**
    （承 MEM-156：受判面非空，但**命题**从未被压）。
14. **投递 / 消费：去重在存储与读面边界，仓内无应用级消费者**：
    投递语义是 at-least-once（`docs/adr/ADR-0016-at-least-once-idempotency-outbox.md`）；
    去重发生在 `outbox_events.event_id` 主键 + `INSERT OR IGNORE`
    （`adapters/sqlite/outbox.py:46-48`、`adapters/sqlite/event_publisher.py:50-57`、PG `ON CONFLICT DO NOTHING`）
    与读面游标（`services/api/routers/run_events.py:62-67`）；
    **无 `processed_events` / `inbox` / `consumer_offsets` 表或守卫**
    （`docs/storage/DATABASE_SCHEMA.md:138` 列的 `consumer_offsets` 是**文档独有**）。
    SQLite 侧**无 relay 派发器**（`pending()/mark_published()` 仅测试调用 ⇒ `published_at` 在生产中永不推进），
    PG relay 只在 `outbox_relay_enabled` 下启用（`services/api/pg_composition.py:303`）。
    **⇒ EC-04 ② 的正确形态 = 「域内交付边界逐条枚举 + 下界断言 + 每条给出 event_id 去重证据」
    + 如实登记「无应用消费者」**，**不得**新建消费者（= 新能力）。
15. **补偿：唯一可调用的是恢复失败的状态回滚**（`packages/application/run_orchestration/run_terminals.py:85-107`，
    调用点 `services/api/routers/approvals.py:189,268`、`services/api/scheduler.py:396,404-423`）；
    会话态 `COMPENSATING`（`packages/domain/session_state.py:83-119`）**无产品驱动**；
    `compensation_actions` 表 / `CompensationAction` 类**只存在于文档**
    （`docs/storage/DATABASE_SCHEMA.md:131-138`、`docs/architecture/DOMAIN_MODEL.md:325-326`），
    **无 DDL、无类型、无测试** ⇒ 非幂等副作用的补偿**未实现** ⇒ **收窄 + 登记**（实现 = 新能力）。
16. **exactly-once 措辞：一律是否认 / 禁止，无机械判据**：全仓（含 `.cursor/`）`exactly[ _-]once`
    命中 **19 条** —— 1 条**禁止**（`AGENTS.md:175`）、10 条**否认 / 免责**
    （`ADR-0016:5`、`OPERATIONS_RUNBOOK.md:102`、`CONSOLE_PAGE_MAP.md:95-96`、`experiment_state.py:111`、
    `ports/experiment_store.py:21`、`services/api/experiment_queue.py:11`、两条 `.cursor` 记录、
    `MEM-20260915-029`、`PLAN-20260915-052`）、**2 条只关于内部继电机制的肯定式**
    （`tools/probes/probe_outbox.py:8`、`probe_scheduled_recovery.py:171`，**均非投递语义**）、6 条中性
    ⇒ 产品 / user-facing 面对**投递语义零肯定式**，但**没有任何判据钉住它** ⇒ EC-04 ④ 给机械判据
    （**有界面 + 逐条分类 + 下界 + 肯定式投递声明判红**）。
17. **规模余量（实测，决定判据落点）**：`adapters/sqlite/workflow_ops.py` **430 行**（硬上限 450
    ⇒ **只剩 20 行余量**，任何产品侧收紧必须极小或改判据落点）、`packages/domain/tasks.py` **284 行**、
    `adapters/relay/gateway.py` **261 行**、`tests/adapters/sqlite/test_workflow_engine.py` **269 行**
    ⇒ **新判据一律落新文件**；若需动 `workflow_ops.py`，先量余量并优先把断言放判据侧。
18. **`IN_SCOPE` 现为 5 条**（`tests/tooling/test_tooling_scripts_meet_product_gates.py:49-55`）
    ⇒ 本轮把 `tools/verify_goal026_closeout.py` 与 `tools/audit_goal026_ledger.py` **显式加入**
    为**纯收紧**（必备清单 ⊆ 推导射程 单调）。
19. **台账审计脚本的软通过（实测复核，本轮必须处置）**：
    `scratch/audit_goal025_ledger.sh:39` 打印 `jobs=%d ok=%d bad=%s`，第 41 行**无条件**
    `verdict="OK"` ⇒ **`jobs=0 ok=0 bad=[] -> OK`（空集合被记 OK）**；
    GOAL-025 的「空集合 = 未取证」口径**只写进了记忆、脚本未修**。
    ⇒ 本 GOAL 的审计脚本**自带下界判定**（`jobs` 为空 / 低于下界 ⇒ **未取证**），
    并由 EC-05 的验证器**断言该下界逻辑存在**。
20. **工作树现状（实测，供驱动遵守）**：`git status --short` 有 **4 个与本 GOAL 无关**的路径
    显示 modified（`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
    `services/api/dto/models.py`、`services/api/middleware.py`），而 `git diff --stat` 为**空**
    ⇒ 只是**行尾态**差异。**一律只用显式路径提交，绝不 `git add -A`，绝不碰这 4 个文件。**
21. **基线 m0（实测口径）**：GOAL-025 收口时终态行 `PASS: profile=m0; 23 deterministic checks`
    （`PASS [` = 24、`4755 passed / 21 skipped`）⇒ 本 GOAL 的终态行**必须仍是 23**，
    用例数只允许**增加**。
22. **记录面判据**：`tests/architecture/python/test_reproducibility_wording.py` 的
    `OVERCLAIM_PHRASES` + 扫描面含 `.cursor/plans` ⇒ 本文件与其后续记录**不得**出现那四条越级措辞
    （本文件已按该门自查）；`tests/architecture/python/test_record_face_is_covered_by_the_gate.py`
    要求记录面受门覆盖 ⇒ 顺序一律「**写记录 → 记录面判据 → 全量门**」。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 默认门一律离线**（不需要 `.env` 凭据；**不做真实出网调用**；PG 只作既有资产引用与登记）。

## 循环入口协议

驱动方（会话 / 定时自动化 / 客户端 goal 模式）进入时，按**迭代日志最后一行** +
**工作树 / 远端实况**判定续点；**禁止凭记忆假设上一轮状态**：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①（先 derive 子 PLAN）。
2. 有子 PLAN 但仍在 `IN_PROGRESS` → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待 / 判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后**立即回写本文件**（状态历史 / 迭代日志），保证任意时刻崩溃后重入可续。
同时只允许一个驱动持有 ACTIVE cycle 的推进权；**另一驱动持有未收口 ACTIVE cycle 时等待**。

**每轮只读入口必需的最小集**（`per_cycle_minutes=120` 是硬预算）：本文件 + 当前子 PLAN +
其引用的判据 / 证据；不整目录通读。

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-026-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-026**」（**不是**把任何既有 GOAL 置回 ACTIVE）。
理由：§7 九项义务的**逐条对抗性取证**（尤其「发件箱失败注入原子性」「退避轨迹整合」
「死信恢复路径缺失的判定化」「工具面断路器空壳的判定化」）在 GOAL-001…025 里**从未**作为交付面出现过。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260929-026` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件**——新判据与新夹具同样受门）；
  快照类门禁（OpenAPI / 设计基线：**若漂移按既有流程重生成 + 目检，不调容差**）；
  **默认门一律离线**（`tests/egress_guard.py` 不得放宽）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（**仅限 main**）
  → 用 `scratch/poll_ci_all.sh <sha>` 走 GitHub REST API 轮询到终态
  （M0 **八 job** + CodeQL + `run_attempt`）；**禁止猜测绿**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；
  未达终态 → 回到 ①（cycle+1）；触顶预算 → BLOCKED。

**本 GOAL 特有的执行纪律**：

- **先勘察再设计**：可靠性语义的判据极易写成「按错误文本猜分类」⇒ **必须绑定结构化字段 /
  状态机 / 存储行 / 传输层计数**，**不得**匹配散文（承 MEM-141）。
- **正控制与受判面非空（承 MEM-156）**：每条义务的判据**必须**在本次运行里**真的观测到**目标现象
  （真的经历过一次租约到期、真的投递过两次同一事件、真的注入过一次事务内失败），
  否则判红；**不得**出现「受判集合为空」的空真。
- **反证两向（承 MEM-159）**：既证「**该红时会红**」（随机去重键 / 常量退避 / 异事务写事件
  ⇒ 判红），也证「**不该红时不红**」（异键 ⇒ 第二条事实**应当**出现；正常完成 ⇒ 不判重放冲突）。
- **射程显式分类（承 MEM-158）**：九项义务**每一项**要么在射程内、要么登记 PENDING + 理由；
  运行期观测到的未分类项 ⇒ 判红。
- **不得靠并集掩蔽（承 MEM-160）**：必备清单（九项义务 / 去重边界 / `exactly-once` 分类面）
  **必须**有专门断言清单**下界**的判据（本轮：`IN_SCOPE`、去重边界、话术分类面三处都要下界）。
- **按压 → 逐字节复原必须 raw `sha256` + 二进制读写**（承 MEM-152）：任何留档（判词 / 日志 / 证据）
  **都不得**用文本模式写盘；按压 / 复原**一律用 Edit 工具**（不用 Bash 写源码）。
- **判据自身恒真（承 MEM-141）**：新判据**不得**被文档引用 / 字面量喂饱——必须绑**运行时行为**
  （真实 claim / recover / complete / 注入失败），且**必须被按压过**（先红后绿 + 逐字节复原）。
- **台账审计下界（承 GOAL-025 的实测教训）**：轮询 / 审计脚本对**空集合 / 空字段**一律判
  「**未取证**」，**不得**记 OK；解析打嗝**必须**单独取原始 JSON 复核后再定论。
- **改工具先数夹具**：若动 `tools/two_tree_recheck.py` 或其契约，先确认
  `tests/tooling/test_two_tree_recheck_entry.py` 与
  `tests/tooling/test_closeout_assertions_are_in_tree.py` 的断言**一字不改且全绿**。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧复验**
  （由 CI 承担；本地按同一形态自查）。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」；
  本地门跑在「当时记录已写完」的状态，**记录面的最终覆盖由 CI 承担**；
  **不得**预先声明尚未跑出的结论（承 GOAL-023 的「见补记」做法）。
- **批量推送（承 MEM：`cancel-in-progress`）**：一个 cycle 攒成**一次**推送，
  避免取消在飞的 M0 run；被取消的 run **如实记 `cancelled`**。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品**或**测试各半）；**修产品优先，禁改断言迁就**；若红的是**本轮新增判据**且根因是判据自身写错 ⇒ 改判据（并**按压**复验） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、RSS 阈值型、`evolution_state.json` 的 WinError 5、draft-id 排序） | 按既有配方重跑；**flake 判定必须靠同一代码的复跑对照**；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 **全部 PASS** 且有**实跑证据**（每条含**先红后绿**或
  **边界成立**的证据）+ 独立 RECHECK `PASS` / `PASS_WITH_WARNINGS` + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + **未覆盖范围逐条明写**。
  **未实跑不得记 PASS**；本机无法判定记 PENDING 并停止推进。
  本 GOAL 的收口判词**必须**写明：**① 九项义务逐条的判定结果**（成立 / 收窄 / PENDING + 理由）、
  **② 每条义务的正控制与反证证据**、**③ 两树实跑证据（逐行 + `sha256`）**、
  **④ 按压与逐字节复原记录（raw `sha256`）**、**⑤ 审计脚本「空集合 ⇒ 未取证」下界断言的落地**、
  **⑥ as-is 本机 m0 的终态行与「门在记录之后」的时刻证据**、
  **⑦ 未覆盖范围（五条）与新增残余登记（含需用户拍板项）**。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**宣称 exactly-once**、**新增能力**、
  **给读面加认证**、**引入多租户 / RBAC**、**新增依赖 / 真实 broker**、
  **把真实内容 / token 写进任何地方**、**改 `Idempotency-Key` 语义**、
  **放宽或修改任何既有判据 / 门禁 / 阈值**、**Canonical State 边界**、
  **真实 runtime 设为默认**）、同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、
  或连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，
  **留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**与**需拍板项**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**、**部分实施 1 项**（`D-03`：`undici` 已调研未升）、
**已拍板为维持现状 3 项**、**未授权待拍板 0 项**。⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019…025 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子 `scanner_enobufs` 未得完整结论 | **原样保留**（**不得**据此宣称项目安全） |
| `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` | `undici` 归上游 / 非 ASCII 路径豁免 / 主观面先操作化 / 规模不足的诚实边界 | **原样保留** |
| `W-4` / `W-5` / `W-6` | 本机 m0 同进程跑阈值判据 / 新作业多一次冷装 / `live_run_support.py` 零余量 | **原样保留** |
| `W-10` / `W-11` / `W-12` | 单 token ⇒ 单主体 / BOLA·BFLA 未做 / 部署面未验证 | **原样保留**（本 GOAL 不碰认证面） |
| 历史遗留 **37** 个 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**脚本加入必备清单） |
| 四条历史收口复检**不可回填** | GOAL-023 新增② | **原样保留** |
| 可复跑性 ≠ 跨平台复验 | GOAL-023 新增③ | **原样保留**（本机只在 Windows 实跑；跨平台由 CI 承担） |
| `G24-1` | 四个金丝雀源在默认离线链上没有注入面（真实 runtime / 工具面部分） | **原样保留**（GOAL-025 已收窄离线可判定部分） |
| `G24-2` / `G24-3` / `G24-6` | 响应头面 / 白名单派生 / 正控制 | **已由 GOAL-025 收口或收窄 ⇒ 原样保留，不重开** |
| `G24-4` | `LineageNodeDto.label` 字段名与内容语义不一致 | **原样保留 + 注明「需用户拍板」** |
| `G24-5` | 文档条款是文档 + 判据形态，不是运行时拦截器 | **原样保留 + 注明「需用户拍板」** |

**本轮新增、需用户拍板（本 GOAL 只登记，不实现）**：

| 编号 | 内容 | 为什么需要拍板 |
| --- | --- | --- |
| `R26-1` | **死信人工恢复路径不存在**（`DEAD_LETTER` 无出边；`ADR-0030` 明文承认并把恢复选项留作**未决**） | 实现 = 改 **Accepted ADR** + 新能力（状态机加出边 / 新增恢复入口） |
| `R26-2` | **工具面断路器未接通**（`tool_plane/health.py` 无产品调用方、`apply_tick` 从不被调用 ⇒ 一旦 OPEN 永不半开） | 接通 = 改产品行为 + 决定阈值来源与状态持久化 |
| `R26-3` | **在飞取消信号未接通**（控制面取消不通知在飞远端作业；`AgentRuntime.cancel` 无产品调用方） | 接通 = 新能力 + 影响 worker 协议与 fencing 语义 |
| `R26-4` | **非幂等副作用的补偿未实现**（只有恢复失败的 canonical 状态回滚；`compensation_actions` 只在文档里） | 实现 = 新能力 + 需要「哪些动作非幂等」的产品级声明面 |
| `R26-5` | **应用级事件消费者不存在**（仓内无「按事件物化业务事实」的消费者；`consumer_offsets` 是文档独有） | 新建消费者 = 新能力 + 触碰 Canonical State 写入面 |
| `R26-6` | **HTTP 幂等 store 是节点本地**（PG 模式亦为 SQLite）且 `get→call_next→put` 是 check-then-act | 跨副本保证 / in-flight 标记 = 改 `IdempotencyMiddleware` 语义（**本 GOAL 明令禁止**） |

**本 GOAL 特有边界（= 用户判词的「明确不做」，命中即 BLOCKED）**：

1. **假装 / 宣称 exactly-once**——**不做**（口径只能是 at-least-once + idempotency + deduplication）；
2. **新增能力**（死信恢复 / 工具面断路器 / 在飞取消 / 应用级消费者）——**不做**，只登记；
3. **修改任何既有判据 / 门禁 / 阈值 / 放行面**——**不做**；**新增**判据**可以**；
4. **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**——**不做**（终态行仍是 `23`）；
5. **新增依赖** / 真实 broker / 外部队列——**不做**；
6. **真实出网** / 真实 runtime / 真实 tool provider / 真实凭据——**不做**（全离线）；
7. **把真实 prompt / token / 凭据写进任何地方**——**不做**；测试与夹具一律**合成值**；
8. **改 `IdempotencyMiddleware` / `Idempotency-Key` 语义**——**不做**（该面只加判据）；
9. **读面认证 / 多租户 / RBAC / BOLA·BFLA / 逐调用方身份**——**不做**；
10. **`G24-4` 的 DTO 契约 / `G24-5` 的运行时拦截器**——**只登记**（需用户拍板）；
11. **动 `undici` / 改 `ADR-0031` 的 `Status`**——**不做**；
12. **默认 runtime 设为真实**——**不做**（默认必须仍是 Fake；默认 CI 必须离线）；
13. **用 skip / xfail 处理取不到的路径**——**不做**（要么取证，要么登记为 PENDING + 理由）；
14. **用「受判集合为空」的空真充当通过**——**不做**（承 MEM-156）；
15. **把新判据写成「被文档引用 / 字面量喂饱」的形态**——**不做**（承 MEM-141）；
16. **宣称项目安全**（`R-M1` 仍在）——**不做**。

**本 GOAL 交付的是「九项义务的判定结果 + 可复跑判据」，不是「可靠性已完备」**：

- EC-01 只证明**单节点**上的幂等与去重，**不**证明跨副本 / 并发同键（`R26-6`）；
- EC-02 的判据全部落在 **SQLite + 注入时钟**上（PG / 分布式由既有资产与 CI 承担，本轮只引用 + 登记）；
- EC-03 的断路器判定**只覆盖模型端点面**（工具面是空壳 ⇒ 只登记）；死信的**恢复路径不存在**（`R26-1`）；
- EC-04 的原子性判据落 **SQLite**（PG 侧登记）；补偿**只覆盖恢复失败回滚**（`R26-4`）；
- **未覆盖范围（逐条明写；本 GOAL 不消解任何一条）**：

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 配置了外部队列的部署面只在登记面；
5. **R-M1 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称项目安全。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 本行所在的**建档 + 记录提交**（同一提交：新增本文件 + 回填门结果；建档轮的「记录」就是本文件自身，故不拆两笔） | 治理 `validate.py` = `Cursor 治理验证通过`（8 行结论，含 GOAL 结构合规与 push 授权登记）；**记录面判据**（`test_reproducibility_wording.py` + `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）= **24 passed in 10.83s**（`egress guard: judged 0 connection attempt(s); blocked 0`）；**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`FAIL [` = 0、`4755 passed / 21 skipped`、`EXIT=0`；日志 `scratch/goal026-c0-m0.log`，python/tests 段 `in 696.28s`，**日志文件时刻 `12:54:49` 晚于**本文件最后一次写入 `12:38:25`（`ls -l` 实测）⇒ 门跑在「本文件已写完」的状态）；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令（canonical 等价：`.venv` 经 `uv run --frozen --no-sync python -B`、DSN 固化、`--keep-going`、不接管道）；**独占运行**（跑前零 python 进程、`research-system-postgres-1` healthy）；**进程卫生**：跑完 python 进程 **0**。**本行数字写于门之后** ⇒ 记录面最终覆盖由 CI 承担 | 见下方 CI 台账（建档提交的 run 在台账行回填） | 建档轮**零产品代码改动**（只新增本文件） | EC-01…EC-05 全 PENDING。起点已定位：见「事实层结论」22 条（其中 **5 条**决定 EC 形状：第 1 / 9 / 10 / 13 / 19 条 —— 生产 store 的 HTTP 语义无判据 / 工具面断路器空壳 + 半开预算被吞 / 死信恢复路径不存在 / 发件箱无失败注入判据 / 台账脚本对空集合打 OK） | cycle 1 = **EC-01**（幂等与去重：生产 store 上的三件套 + 域级计数 + 跨会话） |
| 1 | PLAN-20260929-245（EC-01） | 本行所在的**实施 + 记录提交**（2 个新增判据文件 + PLAN / RECHECK / MEM / ALL_PLAN / GOAL 回写；批量一次推送） | **EC-01 全部验收成立且有实跑证据**。交付 = `tests/api/test_idempotency_sqlite_semantics.py`（**4 例**：重放三件套 / 同键异载荷 422 / 无键 422 / 跨会话）+ `tests/e2e/test_idempotency_canonical_dedup.py`（**2 例**：同键恰 1 行 / 异键 2 行两向控制）+ `RECHECK-20260929-246`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-20260929-167`。**实跑**：新判据 **6 passed**；受影响套件（既有 4 文件 + 新 2 文件）**35 passed**（`egress guard: blocked 0`）。**判据打在生产实现上**：`deps.idempotency` 由 `InMemoryIdempotencyStore` 换成 **`SqliteIdempotencyStore`（文件库）**；`_assert_etag_is_real` 守住「受判面非空」（否则两次 `None` 相等会退化成空真）。**按压先红后绿 + 逐字节复原**：**P1** 去重键 → 随机值 ⇒ `assert 2 == 1`（`1 failed, 1 passed`）；**P2** 重放键 → 异键 ⇒ `At index 1 diff: {'id': '0afe552e-…'} != {'id': '68c79bf0-…'}`（`1 failed, 3 passed`）；复原后 raw `sha256` 回到 `fd0e1128…4f89` / `34c7bef2…147a`（两者 `MATCHES_BASELINE True`）⇒ **6 passed**；留档 `scratch/goal026-ec01-press-matrix.log`（二进制写盘 / `CR` 计数 0）。**第二条路径（重放来源）**：篡改持久化行（`299` + 篡改正文 + 篡改 `ETag`）⇒ 重放**原样跟随**且 canonical 端点仍为 1 ⇒ 重放来源是**持久化行**，**不是**路由被重新执行的假象。**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模门参数化 **8 passed**。**既有判据逐字节未改**（`git status --porcelain -- tests/` 只有两个 `??`）。**零产品代码改动**；m0 与 CI 台账见下方（记录写入之后才跑） | 见下方 CI 台账 | **零真缺陷** | **EC-01 = PASS**（`R26-6` 原样保留：节点本地 store / check-then-act 未取证）。**如实登记六条警告**（`RECHECK-246`）：`W-1` 单节点射程（PG 模式 store 仍是 SQLite ⇒ 跨副本未取证）；`W-2` 并发同键未取证（`get → call_next → put` 无 in-flight 标记，改语义属禁止面）；`W-3` 两次按压是**判据源码级**、未在产品侧按压；`W-4` 跨会话是**同进程顺序会话 + 文件库**、非跨进程；`W-5` `ETag` 相等依赖路由发 `ETag`（仅重放 / 跨会话两例守住非空）；`W-6` 计数只证行数、不证是哪条分支去重；`R-M1` 未收口 | cycle 2 = **EC-02**（租约 / 心跳 / 重试分类 / 退避：时钟注入两向 + 引擎路径轨迹） |

### 建档轮本地验证

**顺序承 MEM-145（记录先写、门后跑）**，全部**实跑**：

- **记录写入时刻**：本文件 mtime **`12:38:25`**（`ls -l --time-style=+%H:%M:%S` 实测）。
- **治理 `validate.py`** = `Cursor 治理验证通过`（8 行结论，含「GOAL 循环记录（plans/goals/）
  结构合规；push 授权显式登记」与「未发现明显凭据材料」）。
- **记录面判据**（`tests/architecture/python/test_reproducibility_wording.py` +
  `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）
  = **24 passed in 10.83s**（与 GOAL-025 基线同值）；同时 `egress guard: judged 0 connection
  attempt(s); blocked 0`。
- **as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、
  `FAIL [` = **0**、`4755 passed / 21 skipped / 94 warnings`（python/tests 段 `in 696.28s`）、
  `EXIT=0`；日志 `scratch/goal026-c0-m0.log`）。**日志文件时刻 `12:54:49` 晚于**本文件最后一次
  写入 `12:38:25`（`ls -l` 实测）⇒ 门跑在「本文件已写完」的状态。
- **口径**：本机**无 `make`** ⇒ 直跑 Makefile 的同一命令
  `run_all_checks.py --profile m0 --keep-going`（同解释器：仓库 `.venv` 经
  `uv run --frozen --no-sync python -B`；同 DSN 固化
  `RESEARCHOS_POSTGRES_DSN=<测试 DSN>` + `DATABASE_URL=` + `POSTGRES_DSN=` + `LLM_MAIN_KEY=`；
  同 `--keep-going`；**不接管道**以免缓冲）。
- **独占运行**：跑前 `tasklist` **零 python 进程**、`research-system-postgres-1` healthy；
  **进程卫生**：跑完 `tasklist` python 进程 **0**（零泄漏）。
- **记录面最终覆盖由 CI 承担**：本小节的数字写于门**之后** ⇒ 依 GOAL-021 的澄清，
  **不**声称本地门覆盖了本小节的最终文本。

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-026 落地） | `3e54564` | M0 [**36524348598**](https://github.com/Eswink/research-system-new/actions/runs/36524348598) / CodeQL [**36524349477**](https://github.com/Eswink/research-system-new/actions/runs/36524349477) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `console-frontend` / `eval-gate` / `observability-overhead-windows-latest` / `collector-quality` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `quality-ubuntu-latest` / `container-quality` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (python)` / `Analyze (actions)` **3/3 `success`**。轮询日志 `scratch/goal026-c0-ci-poll.log`（`ALL_TERMINAL sha=3e545648a23b0d95ff797064645a3c9b15032fdf`，**37 轮**）。**台账审计口径**：第 28–32 轮出现 5 次「unparseable API response」⇒ 按口径**单独取原始 JSON 复核**（`/actions/runs/<id>/jobs` 落盘 `scratch/goal026-c0-run-36524348598-jobs.json` / `…-36524349477-jobs.json`）：`jobs=8 ok=8 bad=[]` 与 `jobs=3 ok=3 bad=[]`，逐 run 的 `status=completed` / `conclusion=success` / `run_attempt=1` 亦由 REST API 实查 ⇒ **未把解析打嗝写成不一致，也未把不一致读成打嗝**。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ **零依赖改动** |
| 本条台账的**记录提交** | 本行所在的记录提交 | **依「固定口径」：写台账的那一步自身的 run 只在回合汇报记账**（不重复回写文件 —— 否则每写一行就产生一个待记账的新提交，台账永远追不上自己） | 见回合汇报 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | ACTIVE | **建档 cycle 0 完成，进入循环**：EC-01…EC-05 全 PENDING，下一 cycle 做 **EC-01**（幂等与去重）。**本地验证（顺序承 MEM-145）**：记录（本文件）先写完（`12:38:25`）→ 治理 `Cursor 治理验证通过` → 记录面判据 **24 passed**（egress `judged 0 / blocked 0`）→ **as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`FAIL [` = 0、`4755 passed / 21 skipped`、`EXIT=0`；日志 `scratch/goal026-c0-m0.log`，**日志时刻 `12:54:49` 晚于**本文件写入 `12:38:25`）；独占运行 + 进程卫生零泄漏；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令（canonical 等价）。**本行数字写于门之后** ⇒ 记录面最终覆盖由 CI 承担。**建档提交**的 CI 到终态后在下方台账回填。 |
| 2026-09-29 | ACTIVE | **cycle 1（PLAN-20260929-245）：EC-01 = PASS**（§7 义务「idempotency key + deduplication」的对抗性自检）。交付 = `tests/api/test_idempotency_sqlite_semantics.py`（4 例）+ `tests/e2e/test_idempotency_canonical_dedup.py`（2 例）+ `RECHECK-246`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-167`。**判据打在生产实现**（`SqliteIdempotencyStore` 文件库，替换测试用的内存实现）；**按压 P1/P2 先红后绿 + raw `sha256` 逐字节复原**；**第二条路径**证明重放来源是持久化行（篡改行 ⇒ 重放原样跟随）。新判据 6 passed / 受影响套件 35 passed / 四道门绿 / 既有判据逐字节未改。**零产品代码改动**。 |
| 2026-09-29 | ACTIVE | **cycle 1 本地 m0（as-is，记录写入之后）**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = **24**、`FAIL [` = 0、**4763 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal026-c1-m0.log`，python/tests 段 `in 568.41s`）。**时刻证据**：**日志文件时刻 `13:24:04` 晚于全部记录文件**（GOAL `13:10:50`、PLAN `13:09:58`、RECHECK `13:09:29`、MEM `13:11:59`、INDEX `13:11:51`、ALL_PLAN `13:10:05`，`ls -l` 实测）⇒ 门跑在「记录已写完」的状态。**用例数 +8 = 本轮新判据 6 例 + 规模门按文件参数化 2 例**（`test_python_source_limits.py` 对 `PRODUCT_ROOTS` 下**每个** `.py` 参数化 ⇒ 新增两个文件各 +1）。**独占运行**（跑前 `tasklist` 零 python 进程、`research-system-postgres-1` healthy）；**进程卫生**：跑完 python 进程 **0**。解释器 / 口径与 canonical 一致（仓库 `.venv` 经 `uv run --frozen --no-sync python -B`、`--profile m0 --keep-going`、DSN 固化 + `LLM_MAIN_KEY=""`；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令）。**本行数字写于门之后** ⇒ 依 GOAL-021 的澄清，**不**声称本地门覆盖了本行的最终文本；**记录面最终覆盖由 CI 承担**。 |
| 2026-09-29 | ACTIVE | **建档**：用户会话指令（goal 模式）授权对 AGENTS.md §7 的**九项义务**（idempotency key / Task lease + heartbeat / retry classification / exponential backoff / circuit breaker / dead-letter · manual recovery / cancellation semantics / compensation for non-idempotent actions / transactional outbox）做**对抗性自检** —— 从「代码里有」推进到「有判据证明成立」或「逐条登记为 PENDING + 理由」，并授权本驱动自动化循环推进、无需逐轮确认。**明确不做**：假装 / 宣称 exactly-once、新增能力（死信恢复 / 工具面断路器 / 在飞取消 / 应用级消费者）、修改任何既有判据 / 门禁 / 阈值 / 放行面、改 `IdempotencyMiddleware` / `Idempotency-Key` 语义、改 `PRODUCT_ROOTS` / m0 条数 / 作业结构、新增依赖（含真实 broker / 外部队列）、真实出网 / 真实 runtime / 真实凭据、读面认证 / 多租户 / RBAC / BOLA·BFLA、`G24-4` / `G24-5`、动 `undici`、改 `ADR-0031` 的 `Status`、宣称项目安全。五 EC 设计（幂等与去重 / 租约心跳重试退避 / 断路器死信取消 / 补偿与发件箱 / 自举收口），budget = 20 / 120 / 2。**建档当日实测 22 条事实层结论**（见「目标与退出标准」），其中五条决定 EC 形状：**① 幂等的 HTTP 判据至今只打在 `InMemoryIdempotencyStore` 上**（生产 store 无判据）；**② 工具面断路器是空壳且 `gateway.py:108-111` 的半开探针预算被吞（候选真缺陷）**；**③ 死信的恢复路径不存在且 `ADR-0030` 明文承认（⇒ 只收窄 + 需拍板）**；**④ 发件箱的原子性判据缺失（既有两条同名判据都是全绿路径，无失败注入）**；**⑤ `scratch/audit_goal025_ledger.sh` 对空 `jobs` 无条件打 OK（本轮必须给下界判定）**。**建档时零产品代码改动**（只增本文件）；工作树另有 4 个**与本 GOAL 无关**的并发改动（仅行尾态差异，`git diff --stat` 为空），本 GOAL 一律只用**显式路径**提交。 |
