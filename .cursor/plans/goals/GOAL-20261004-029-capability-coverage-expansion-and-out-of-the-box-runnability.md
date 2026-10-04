---
id: GOAL-20261004-029
slug: capability-coverage-expansion-and-out-of-the-box-runnability
title: 能力承接面扩容（A 组零依赖能力 + 出厂可跑性）—— 收 GOAL-028 的 `W-1`
status: ACHIEVED
created_at: 2026-10-04
updated_at: 2026-10-05
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-04 用户会话指令（goal 模式）：**建档 GOAL-029（能力承接面扩容：A 组零依赖能力 +
    出厂可跑性）并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **方向承 GOAL-028 的 `W-1`**：GOAL-027 接上了真能力，GOAL-028 建成了 provider→SDK
    **声明式映射**并让多 role 子迭代在**默认装配**上跑通，但它自己登记了最要紧的限制 ——
    `W-1`：**映射机制成立 ≠ 出厂即可跑**（工具实现须装配方接线）。本轮收这条：把 canonical
    里已有的读面接成会话工具，让「能力承接面」从 **12/46** 真正扩起来，并**把「出厂即可跑」
    变成可复核的事实**。
    (1) **用户方向** = 真实科研能力（承 GOAL-027 / 028）；本轮**承 GOAL-028 的 `W-1`**。
    (2) **授权范围（严格限于）**：(i) **新增会话工具实现**（把 canonical 读面接成 SDK 工具），
    并接进生产组合根；(ii) **新增 provider / 扩展配置**（`tool_providers.yaml` /
    `capabilities.yaml` / `skills.yaml`）；(iii) **修实现过程中发现的真缺陷**；
    (iv) 新增判据 / 夹具（落 `tests/**`）；(v) 文档同源更新。
    (3) **明确不做（命中即 BLOCKED）**：改 `default_effect: DENY` / 放宽 §9 默认 deny /
    **新增类别级 allow**；**修改任何既有判据 / 门禁 / 阈值**（**新增**可以）；改
    `PRODUCT_ROOTS` / m0 条数 / 作业结构；**把真实凭据写进任何地方**（源码 / 示例 / 测试 /
    记录 / 日志 / 遥测）；**未经 pin 的 provider**；**token passthrough**；**未批准即用**；
    **放开默认网络**（默认 CI 与默认门**必须仍离线**，`tests/egress_guard.py` 不得放宽）；
    **触达 D 组能力**（`external.publish` / `package.install` / `git.commit` /
    `workspace.delete` —— 它们在 `policy.yaml` 现为 `require_approval` ⇒ 接通审批通道
    **需用户拍板**，本轮只登记）；**Canonical State 边界**（PostgreSQL Domain Entity 是业务
    真相；**写能力**必须经既有 canonical 路径，不得旁路）；读面认证 / 多租户 / RBAC /
    BOLA·BFLA / `G24-4` / `G24-5`；**宣称项目安全**（`R-M1`）；**宣称投递语义为「恰好一次」**。
    (4) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）+
    **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11；真实出网只
    在显式开关 + `requires_live_llm` 口径下放行）。
    (5) **边界（承继）**：GOAL-001…028 **全部只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…028 的未覆盖范围**原样保留**。
    (6) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle
    时等待**。
objective: >-
    把「能力承接面」从 **12/46** 扩起来，并把 GOAL-028 登记的 `W-1`（**映射机制成立 ≠ 出厂即可
    跑**）从一句自我限制变成**可复核的机械事实**：修掉会话工具**真能被调用**这条链上的真缺陷并
    把实现注册接进**生产组合根**（EC-01）→ 为 A 组零依赖读能力建立**声明 + 实现 + 两向反证 +
    射程显式分类**的机械化承接面判据（EC-02）→ 写能力的 canonical 路径与旁路风险**如实判定**
    （EC-03）→ 两树复检的两份**判词文件本身**落档并加 `sha256` / 行尾断言（EC-04）→ 自举收口
    （EC-05）。
    **硬约束**：缺实现 / 缺映射 / 缺 pin / 未批准一律**点名失败**（**不得**静默降级）；**不得**把
    provider id 直接当 SDK 工具名；零真实凭据进树；**pin 先行**；**URL 策略在触网之前**；
    **默认门离线**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1` 仍在）；**不得**宣称投递
    语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **「出厂即可跑」的真形态：会话工具**真能被调用**（主干；收 `W-1`）**。
      建档勘察（见「事实层结论」第 6 条）**实测证伪了本 EC 的原始表述**：今天在**生产组合根**
      的真实缺省下，会话工具**根本不可能被执行** —— 与「装配方没接线」**是两个缺陷**：
      (a) **装配面缺口（`W-1` 的字面）**：两个组合根本体
      （`services/api/composition.py::_sqlite_orchestration` /
      `services/api/pg_composition.py::_build_pg_orchestration`）**都没有**把
      `register_session_tools` 传给 `build_agent_runtime` ⇒ 生产路径上注册面是 `None`，
      回落空操作；只有**判据侧**（`tests/e2e/*` 的 `_attach_session_tools`）会接。
      (b) **策略面缺陷（本轮实测到的真缺陷，非 `W-1` 所述）**：
      `adapters/openhands/policy_enforcing_agent.py::_evaluate` 构造的 `PolicyRequest` 用
      `scope=session_id`，而 `examples/config/policy.yaml` 的带 scope allow 规则要求
      **scope 相等**才匹配 ⇒ `session_id` 永不匹配任何规则 ⇒ **每一条**会话工具调用都落
      `default_effect: DENY`。桥侧 `session_tool_invocation.make_tool_invoker` 经
      `execute_tool_call` 求值，同样**不带** scope（运行链用
      `phase_capabilities.ScopedPolicy` 补这一字段，**会话桥没有对应补法**）。
      **实测（专属工具名 + 真实 `NativePolicyEvaluator(policy.yaml)`）**：
      `artifact.read`（**已放行**能力）⇒ `status=SUCCEEDED` 但 **`executor_reached=[]`**
      —— executor 从未触达；把 scope 换成 `policy_scope_for(capability)` 后 ⇒
      **`executor_reached=['hi']`**（同一进程、同一装配、只差这一个字段）。
      **结论**：GOAL-028 EC-03 的「默认装配实跑」证的是**会话起得来**，**不是**工具跑得动 ——
      `map_tools=True` 之外的「跑通」在工具面从未发生。
      **本 EC 的验收**：
      (a) **修 (b)**：会话面按**既有** scope 表（`policy_scope_for`，**不新造第二张表**）补
      求值 scope，使**已放行**能力的会话工具调用**真触达 executor**（前后对照 + 专属名字，
      两向：已放行 ⇒ 触达；未放行 ⇒ 仍拒且点名）；
      (b) **接 (a)**：把会话工具实现注册接进**两个生产组合根**（`register_session_tools`），
      使出厂配置下声明了绑定的协议在**没有任何测试侧注入**时也能起会话；
      (c) **反证两向（必须合跑一次）**：用**专属名字**证明「未注册 ⇒ 点名失败」
      `ToolDefinition '<名>' is not registered`；用**显式摘除**
      （`registry._REG.pop(name, None)`）证明「有实现 ⇒ 能解析」——承
      `MEM-20261001-180`：SDK registry **进程级且只增不减**，两条反证**单跑都会假绿且方向相反**；
      (d) **实跑**：默认装配（`build_agent_runtime` 真实缺省）下 run 到 `SUCCEEDED`，
      且**工具 executor 真被触达**（可观测证据，不是「没报错」）。
      **判据**：缺陷修复在位 + 两组合根接线 + 两条反证合跑 + 默认装配实跑且 executor 触达。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/openhands/test_policy_enforcement.py
      tests/e2e/<新增判据> -q` ⇒ 全绿（既有判据**逐字节未改**）；
      配套留档：修复前后同一装配的对照（`executor_reached` 两值）、两条反证的**合跑**判词原文
      （点名串逐字）、默认装配实跑终态 + executor 触达证据、按压前后 raw `sha256` 逐字节复原。
    status: PASS
  - id: EC-02
    criterion: >-
      **「出厂即可跑」机械化 + A 组承接面扩容（收 `W-1` 的可复核面）**。
      把「映射机制成立 ≠ 出厂即可跑」这个落差变成**一条判据**，并对 A 组零依赖读能力建立
      声明 + 实现 + 反证 + 射程分类的承接面。
      **建档勘察的实测边界（不得照抄原表述）**：A 组读能力的**执行**需要 `policy.yaml` 的
      `allow` 规则，而差集面被**两条既有判据**钉死 —— 实测（临时目录协议，未动树）：把
      `claim.read` 写进某 phase 的 `required_capabilities` ⇒
      `test_no_protocol_reachable_capability_lacks_a_rule` 判红（`W-A` 同类活缺口）+
      `test_each_row_state_matches_the_mechanical_rule` 判红（文档「该登记」vs 机制「该放行」）；
      而 `tests/application/preflight/test_read_grant_is_per_item.py` 钉着
      `EXPECTED_REGISTERED = 15` 且断言这 15 条**一条都没被放行**。⇒ **给 A 组读能力放行 =
      改既有判据 = 需用户拍板**（`D-02(b)`「读类能力是否成类预放行」至今未决，见
      `docs/architecture/POLICY_SURFACE_AUDIT.md` 的「需拍板的一条口径」）。
      **因此本 EC 的验收分两半，放行那一半登记为待拍板，不放行的那一半必须机械成立**：
      (a) **判据（声明了 ⇒ 一定有实现）**：对每条**已声明承接**的能力，断言
      「声明了绑定 ⇒ 一定有实现注册」；缺实现 ⇒ 判红并**点名能力名与缺失的工具名**；
      (b) **反证两向**：声明了但没实现 ⇒ 判红；实现了但没声明 ⇒ **也**判红（防静默漂移）；
      (c) **射程显式分类**（承 `MEM-20260922-158`）：46 条能力**逐条**要么**在射程内**
      （已承接），要么**登记在案**（带理由：B/C/D/E 组各自的原因 + A 组里**待放行**的子集
      逐条点名）；未分类者判红；
      (d) **不得靠并集掩蔽**（承 `MEM-20260922-160`）：必备清单与文档点名并存时，必须有
      **专门断言清单下界**的判据（清单条数有下界，且下界**随轮次显式上调**）；
      (e) **A 组承接的落地形态 = 声明 + 实现（可执行面待放行）**：为 A 组读能力建立会话工具
      **实现**（canonical 读面 → 工具桥）与**声明**，并**如实断言**它们的执行在缺 `allow` 时
      **点名拒绝**（`POLICY_DENIED`）——「已承接但未放行」与「未承接」因此在判据上**可区分**，
      **不得**用前者冒充后者、**不得**把未放行写成已跑通。
      **判据**：一条判据 + 两向反证 + 射程分类齐备 + 下界断言 + 「已承接/未放行」可区分。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/architecture/python/<新增判据>
      tests/application/preflight -q` ⇒ 全绿（既有判据**逐字节未改**）；
      配套留档：46 条能力的**逐条分类表**（射程内 / 登记在案 + 理由）、缺实现与缺声明的两向判红
      判词原文、清单下界读数、A 组「已承接但未放行」的 `POLICY_DENIED` 点名原文。
    status: PASS
  - id: EC-03
    criterion: >-
      **写能力的 canonical 路径与旁路风险（如实判定）**。
      建档勘察结论（见「事实层结论」第 3 条）：`deliverable.write` / `deliverable.edit` 在
      **域里没有实体**（`packages/domain/` 无 `Deliverable` 类，只有 application 层的未定型
      `dict` + `research_deliverable` artifact），**没有 HTTP 写面**，且两者在差集表里是
      **「该拒绝」**（写类 ⇒ 落 `default_effect: DENY` 即正确）。它们的 canonical 路径是
      `packages/application/m12_reference/persistence.py::persist_completion` →
      `_put_deliverable`（artifact id `f"{run_id}:deliverable.json"`，`source_refs` 绑
      manifest digest / claim_id / eval digest / audit digest），**有** `_succeeded_run` 的
      manifest digest 守卫与 RUNNING→SUCCEEDED 迁移前置校验。
      **本 EC 的验收（不新增写能力、不放行、不旁路）**：
      (a) **判定在树**：写能力**不属** A 组（零依赖读面）的理由逐条落档（无域实体 / 无写面 /
      差集表判「该拒绝」/ 放行需拍板）；
      (b) **canonical 路径断言**：断言 deliverable 的**唯一生产 writer** 是
      `persist_completion`（全仓无第二个生产者写 `{run_id}:deliverable.json`），
      且**写入后读面真能读到**（`GET /runs/{run_id}/deliverable` 的 `available=true` +
      `artifact_digest` 在场）——承 `MEM-20260920-096`：只 `register_evidence` 不
      `attach_relation` ⇒ 读面看不到，**写入与可见性必须一起断言**；
      (c) **反证**：绕过 canonical 路径（直接 `artifacts.put` 同一个 id，不经
      `persist_completion`）⇒ 判红（点名「旁路」）——即让「旁路」在判据上**可被抓住**，而不是
      只在文档里承诺；
      (d) **实验计划写面的漏斗缺口如实登记**：`ExperimentStore.save_plan` 是**无条件 upsert**，
      两个生产写入点（`routers/experiments.py:192` 与 `m12_reference/persistence.py:42`）
      **各写各的**、无共同漏斗、无 provenance 层 —— **登记为残余**（本 GOAL **不改**它：
      收窄它要动既有写路径与判据）。
      **判据**：判定在树 + canonical 唯一性断言 + 写后读得到 + 旁路反证 + 残余登记。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api/test_reports_integrations_lineage_api.py
      tests/application/m12_reference -q` ⇒ 全绿（既有判据**逐字节未改**）+
      新增判据绿；配套留档：canonical 唯一性的全仓检索读数、写后读面读数（`available` /
      `artifact_digest`）、旁路反证的判红原文、实验计划漏斗缺口的残余登记条目。
    status: PASS
  - id: EC-04
    criterion: >-
      **两树判词归档留档（收 GOAL-028 发现的缺口）**。
      GOAL-028 的两树复检只留了日志（且日志是 PowerShell 重定向的 CRLF），**判词文件本身
      没有独立归档** ⇒ 「两树逐行相同」缺**可独立复核的物证**（`scratch/` 在 `.gitignore`
      里，clone 出来的仓库看不到）。
      **本 EC 的验收**：
      (a) 让两树复检的**两份判词都落档**到**记录可引用的位置**（**二进制写盘**：
      `Path.write_text(..., newline="")` —— `tools/two_tree_recheck.py::dump_verdicts`
      **已经**是这个形态，本 EC 只把落点从 `scratch/` 挪到**在树**的位置）；
      (b) **判据**：断言两份归档**都存在**、两份 `sha256` **相同**、且**行尾为 LF**
      （逐字节扫描 `\r`，防 PowerShell 重定向污染 —— 承 `MEM-20260928-152`）；
      (c) **反证两向**：用**文本模式**写一份（Windows 上 `\n` ⇒ `\r\n`）⇒ 判红
      （CRLF 与 LF 的 `sha256` 不同）；**二进制复原** ⇒ 绿；
      (d) **落点选择必须不撞既有判据**：归档落点不得使任何既有判据变红（实测：`.cursor/plans`
      在 `test_reproducibility_wording.py` 的扫描面内、`docs/**` 在
      `docs_consistency_check` 的反引号引用面内 ⇒ 落点与内容都须过那两道门）。
      **判据**：两份归档 + `sha256` 断言 + 行尾断言 + 两向反证 + 既有判据逐字节未改。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/<新增判据> -q` ⇒ 全绿；
      配套留档：两份归档的路径、各自 `sha256`、逐字节 `\r` 扫描读数、文本模式写盘的判红原文
      与二进制复原后的判绿读数。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口**：① 收口验证器进树（`tools/verify_goal029_closeout.py`，**复用**
      `tools/closeout_recheck_assertions.py` 的标准断言集，只写本轮特有断言）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧** ⇒ 只增不删，**450 行硬上限**）；② 两树复检**含 EC-04 的两份判词归档**，
      逐行相同 + `sha256` 相同（`tools/two_tree_recheck.py --script-mode shared`，
      两路判词**二进制写盘**）；③ as-is m0 **23/23**，**在记录写入之后**（独占运行、
      仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**、canonical DSN pin、
      零进程残留）；④ 治理 `validate.py` 绿（含 `DOCS-CHECK` 与 GOAL/PLAN/RECHECK/MEM
      交叉引用）；⑤ CI 台账**逐提交**（承 GOAL-028 EC-04 的机器复核口径；合并行必须显式声明
      覆盖与承担者；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记 + 原因）；
      ⑥ 承继残余逐条在位 + 本轮新增；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进入射程 + 两树同结论 + m0 23/23 在记录之后 + 治理绿 + 台账逐提交 +
      残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script
      tools/verify_goal029_closeout.py --script-mode shared --root .` ⇒ `TWO-TREE PASS` / `EXIT=0`；
      `PASS: profile=m0; 23 deterministic checks`；`validate.py` = `Cursor 治理验证通过`；
      台账经逐提交审计工具复核（`checks>0 failed=0 exit=0`）。
    status: PASS
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
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/egress_guard.py`、
      `tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/e2e/test_multi_role_research_offline.py`、
      `tests/e2e/test_multi_role_on_the_default_assembly.py`、`tests/e2e/test_tool_binding_on_the_default_assembly.py`、
      `tests/contracts/test_mcp_research_server_loopback.py`、
      `tests/contracts/test_mcp_registration_and_refutations.py`、
      `tests/contracts/test_europe_pmc_pin_and_registration.py`、`tests/api/run_fixtures.py` 的
      `_PROVIDERS` 行、`tests/application/preflight/**`、
      `tests/application/test_m2_audit.py`、`tests/architecture/python/**`、
      `tests/tooling/test_tooling_scripts_meet_product_gates.py`、三道记录面判据、
      两树入口判据、规模门禁）—— **新增**判据不受此限
    - >-
      改 `default_effect: DENY` / 放宽 §9 默认 deny / **新增类别级 allow**；或改
      `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` 与 `policy.yaml`
      的镜像并集（两张表由既有测试锁死）；**给 A 组读能力新增 `allow` 规则**（⇒ 改既有判据 +
      属 `D-02(b)` 未决口径 ⇒ **需用户拍板**）
    - >-
      让某条 A 组能力**变为协议可达**（写进任何协议的 `required_capabilities` / 合约）而
      不同时取得放行 —— 实测会同时打红 `test_no_protocol_reachable_capability_lacks_a_rule`
      与 `test_each_row_state_matches_the_mechanical_rule`；取得放行则属上一条
    - >-
      **未经 pin 的 provider**：新增 provider **必须先**在 `examples/contracts/toolpack_*.yaml`
      落 `digest` / `resolved_revision` / `license` / `network_domains` 再登记（AGENTS.md
      §5/§12）；pin 缺失即 fail closed，**不得**静默降级
    - >-
      **新增 provider id**：`examples/config/tool_providers.yaml` 的 **id 集**被既有判据
      精确钉死（`test_existing_providers_are_untouched` 的 `set(catalog) ==` 四元精确相等，
      实测新增 id 即判红）⇒ 扩展承接面的形态只能是**扩展既有 provider 的 capabilities**
      （实测可行，仅需同轮更新 `docs/architecture/POLICY_SURFACE_AUDIT.md` 的声明面列）
    - >-
      **token passthrough**：把模型 / 其它域凭据转发给 provider；或把 `credential_ref` 声明为
      「其实不需要」的凭据（**只有没有它不可用**才声明；离线路径不声明）
    - >-
      **未批准即用**：绕过 `/tool-provider-registrations` 的 `PENDING → APPROVE → ACTIVE`
      状态机使用 provider，或让 `PENDING` / `REVOKED` 进入合并目录
    - >-
      把**任何真实凭据**写进源码 / 示例 / 测试 / 记录 / 日志 / 遥测（凭据**只从环境变量或
      密钥服务读**；示例与夹具一律**明显不可用的合成值**）
    - >-
      **放开默认网络**：放宽 `tests/egress_guard.py`、让默认 CI / 默认门出网、或让真实出网
      成为**默认**（真实出网只允许在显式开关下、按既有 `requires_live_llm` 口径放行）
    - >-
      请求 **localhost / 环回 / 私有 / 保留地址**（服务端 URL 策略：仅 http/https +
      **触网前**校验 host；保留类判据只有 `endpoint_url_refusal` 一处，**不得**另写一份）
    - >-
      **把 provider id 直接当 SDK 工具名**：映射必须是**显式声明**；缺映射、映射到不存在的
      工具、或映射越出会话工具面 —— 一律**点名失败**，**不得**静默丢弃 / 静默回退 / 自动造名
    - >-
      **未注册即静默降级**：缺实现时必须由 SDK **点名** `ToolDefinition '<名>' is
      not registered`；**不得**用空壳工具 / 惰性替身 / `try/except` 掩盖
    - >-
      **旁路 canonical 路径**：`deliverable.write` / `deliverable.edit` 的写入必须经
      `persist_completion`；**不得**直写 ArtifactStore 绕过它；**不得**为读面可见性
      补第二份写路径
    - >-
      改 `PRODUCT_ROOTS` / m0 任一 check / 作业结构 / m0 条数（终态行必须仍是 `23`）
      —— **立即 BLOCKED**
    - >-
      **新增依赖**（`mcp>=1.28,<2` **已是依赖**，不算新增；除此之外不得引入任何新依赖，
      含为判据引入第三方库 —— 一律标准库 + 现有栈）
    - >-
      **Canonical State 边界**：改「PostgreSQL Domain Entity 是业务真相」的口径，
      或把向量 / 索引 / 检索缓存写成业务真相（只允许可重建的 derived index）
    - >-
      给读面（GET / HEAD）加认证，或改读面放行语义（GOAL-019 判词 (i) 不变：保护范围**只有
      写面**）；或引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容，
      或做 **BOLA / BFLA 的专项实现**
    - >-
      动 `G24-4` 的 DTO 契约或 `G24-5` 的运行时拦截器；动 `undici`；改 `ADR-0031` 的
      `Status`；把真实 runtime 设为**默认**（默认必须仍是 Fake）
    - >-
      **触达 D 组能力**（`external.publish` / `package.install` / `git.commit` /
      `workspace.delete`）：接通审批通道**需用户拍板**；本轮只登记，**不得**实现
    - >-
      用 **skip / xfail** 处理取不到的路径，或以「受判集合为空」的空真充当通过
      （承 MEM-156：受判面非空是交付前提）
    - >-
      用**测试里的合成标识**冒充真实科研产物：判据必须断言**真标识**（真 PMID / DOI / 真标题）
      与**内容寻址 digest**，**不得**只断言「调用成功」或「返回了 dict」；
      但**允许**（且要求）用 `httpx.MockTransport` 固定真实响应样本走**真解析**（离线）
    - >-
      台账**合并行漏记**：批量推送的每一个提交都必须在 CI 台账里有对应 run 记录
      （或明确标注覆盖关系 + 由谁承担绿）；`cancelled` 必须如实登记；
      **空集合 / 空字段 = 未取证**，不得记 OK
    - >-
      **留档用文本模式写盘**：判词 / 日志 / 证据一律**二进制写盘**
      （`write_bytes` / `write_text(..., newline="")`）；文本模式在 Windows 会把 `\n` 写成
      `\r\n` ⇒ raw `sha256` 变而 `git diff` 因 `.gitattributes` 归一化**静默吞掉**
      （承 MEM-152）
    - >-
      宣称「项目安全」「授权面已覆盖」或任何形式的安全结论（`R-M1` 未收口）；
      宣称投递语义为「恰好一次」或任何超出实跑证据的可靠性结论
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow —— **立即 BLOCKED**
  - >-
    **给 A 组读能力新增 `allow` 规则**（`D-02(b)`「读类能力是否成类预放行」是未决口径，
    且会打红 `test_read_grant_is_per_item` 的 `EXPECTED_REGISTERED = 15` 与「一条都没被放行」
    两条断言）—— **立即 BLOCKED，等用户拍板**
  - >-
    **新增依赖**（`mcp` 已是依赖，不算新增）—— **立即 BLOCKED**
  - >-
    **真实凭据进树**（任何形式：源码 / 示例 / 测试 / 记录 / 日志 / 遥测 / 夹具）—— **立即 BLOCKED**
  - >-
    **未 pin 接上游**（新增 provider 无 `digest` / `resolved_revision` / `license` /
    `network_domains` 就登记）—— **立即 BLOCKED**
  - >-
    **token passthrough** / **未批准即用**（绕过注册状态机）—— **立即 BLOCKED**
  - >-
    **放开默认网络**（放宽 `egress_guard`、默认门出网）—— **立即 BLOCKED**
  - >-
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**
  - >-
    **宣称投递语义为「恰好一次」**或任何超出实跑证据的可靠性结论 —— **立即 BLOCKED**
  - >-
    **Canonical State 边界**（把向量 / 索引 / 缓存写成业务真相；写能力旁路 canonical 路径）
    —— **立即 BLOCKED**
  - >-
    改 `PRODUCT_ROOTS` / m0 条数 / 作业结构（`23` 这一终态条数）—— **立即 BLOCKED**
  - >-
    **修改**任何既有判据 / 门禁 / 阈值（**新增**判据不受此限）—— **立即 BLOCKED**
  - >-
    **触达 D 组能力**（`external.publish` / `package.install` / `git.commit` /
    `workspace.delete`）—— 需用户拍板，**立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20261004-275-goal-029-ec01-session-tool-actually-executes.md
  - .cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md
  - .cursor/plans/tasks/PLAN-20261005-279-goal-029-ec03-write-capability-canonical-path.md
  - .cursor/plans/tasks/PLAN-20261005-281-goal-029-ec04-05-two-tree-archives-and-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-282-goal-029-ec05-self-bootstrap-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20261004-183-session-tool-scope-must-be-the-capability-scope.md
  - .cursor/memory/entries/MEM-20261005-184-sdk-action-fields-become-the-model-facing-parameter-schema.md
  - .cursor/memory/entries/MEM-20261005-185-verdict-scope-must-be-pressed-too.md
  - .cursor/memory/entries/MEM-20261005-186-two-tree-verdict-write-is-input-output.md
---

## 目标与退出标准

**方向**：承 GOAL-028 的 `W-1`（**映射机制成立 ≠ 出厂即可跑**）—— 让已建成的东西真的被用起来。

### 事实层结论（建档轮**实测**，非照抄）

建档轮的只读勘察**推翻了 prompt 起点的三处表述**。以下每条都带可复核证据；后续 cycle 一律以
本节为准，**不得**回退到 prompt 的原始表述。

**F-1｜承接面 12/46 —— 复核通过**

`examples/config/capabilities.yaml` 共 **46** 条能力；被 `examples/config/tool_providers.yaml`
的四个 provider 承接的 **12** 条（`literature.search`、`literature.read`、`citation.inspect`、
`evidence.read`、`evidence.write`、`workspace.read`、`workspace.write.notes`、
`workspace.write.code`、`artifact.read`、`artifact.write`、`code.execute`、`git.diff`）⇒
**未承接 34 条**。实测命令：按 YAML 解析逐条求交（见 `scratch/goal029-recon.md`）。

**F-2｜A 组读面入口逐条在位（零新增依赖、零凭据、零许可风险）**

| 能力 | 今天的读面入口 | 读自 |
| --- | --- | --- |
| `claim.read` | `GET /runs/{run_id}/claims`（`services/api/routers/inspection.py:131`） | `EvidenceLedger` |
| `deliverable.read` | `GET /runs/{run_id}/deliverable`（`routers/deliverable.py:52`） | `ArtifactStore` |
| `experiment.read` | `GET /runs/{run_id}/experiments`（`routers/experiments.py:98`） | `EvidenceLedger` + `ArtifactStore` |
| `experiment_plan.read` | `GET /experiment-plans`（`routers/experiment_queue.py:127`） | `ExperimentStore` |
| `budget.read` | `GET /runs/{run_id}/usage`（`inspection.py:163`） | `BudgetLedger` |
| `agent_run.read` | **无专用实体与路由**（最近：`routers/runs.py:166` 的 `tasks` + `agent_id`；`TaskKind.AGENT_SESSION`） | `RunStore` / 事件流 |
| `audit.write` | **无路由**；M12 链内 `persist_completion` → `save_audit`（`m12_reference/persistence.py:60`） | `ExperimentStore.save_audit` |
| `deliverable.write` / `deliverable.edit` | **无路由**；canonical = `persist_completion` → `_put_deliverable` | `ArtifactStore`（`{run_id}:deliverable.json`） |
| `experiment_plan.write` | `POST /projects/{project_id}/experiments`（`experiments.py:174`） | `ExperimentStore.save_plan` |

**F-3｜写能力的 canonical 路径与旁路风险**

- **域里没有 `Deliverable` 实体**：`packages/domain/` 全仓无该类；交付物是 application 层的
  未定型 `dict` + `research_deliverable` artifact。API 的 `DeliverableDto` 是**读面形状**，
  不是域类型。
- **canonical writer 唯一**：生产代码中写 `{run_id}:deliverable.json` 的只有
  `persist_completion`（`clean_run.py:174` 是它**唯一**调用点）；`_put_deliverable` 把
  manifest digest / claim_id / eval digest / audit digest 写进 `source_refs` 作 provenance。
  守卫：`_succeeded_run` 的 manifest digest 相等校验 + RUNNING→SUCCEEDED 迁移前置。
- **旁路风险（如实）**：`ArtifactStore.put` 对已存在的 id 是 **update**（不拒绝覆写），
  而 `_put_deliverable` **没有**「已存在则拒」的守卫（`_put_manifest` 有）——保护来自
  run 状态机而非写入点本身。测试夹具（`live_deliverable_fixture.py` 等）**可以**直写同一 id
  且无门 —— 它们是受控夹具，但这也说明 store 层**没有**闸门。
- **实验计划的漏斗缺口（残余）**：`ExperimentStore.save_plan` 是**无条件 upsert**
  （`ON CONFLICT DO UPDATE`），两个生产写入点各写各的
  （`routers/experiments.py:192` 与 `m12_reference/persistence.py:42`），**无共同漏斗、
  无 provenance 层**；唯一的守卫是调用方施加的域状态机 `transition()`。
- **三者都不经 capability 门禁**：`deliverable.write` / `deliverable.edit` /
  `experiment_plan.write` 在策略面**无规则**、在差集表里是**「该拒绝」**，今天**没有**以
  能力名求值的执行点。

**F-4｜SDK registry 的进程级语义（源码实测）**

`openhands.sdk.tool.registry`：`register_tool` 只写 `_REG` / `_USABILITY_REG`（**无撤销入口**，
重复注册只发 warning 后覆盖）；`resolve_tool` 未命中抛
`KeyError: ToolDefinition '<name>' is not registered`。⇒ 承 `MEM-20261001-180`：**同一进程内
先跑过某用例，后跑的「未注册」断言会假绿**；反向的「有实现 ⇒ 能解析」断言同理会被别的用例
预先注册搞成假绿且**方向相反**。**两条反证必须合跑一次**，并各自用专属名字 / 显式摘除。

**F-5｜【决定性】`tool_providers.yaml` 的 id 集被精确钉死 ⇒ 承接面只能靠扩展既有 provider**

实测（打补丁后按字节复原，`sha256sum -c` 逐字节复原通过）：向
`examples/config/tool_providers.yaml` 追加一个新 provider id ⇒
`tests/contracts/test_europe_pmc_pin_and_registration.py::TestRegistration::test_existing_providers_are_untouched`
判红（`set(catalog) == {四元}` 是**精确相等**）。
⇒ **新增 provider id = 改既有判据 = 禁**。
⇒ 改**扩展既有 provider 的 `capabilities`** 则可行：同一实验下只余 **1 条**判红
（`test_each_row_state_matches_the_mechanical_rule`：`agent_run.read` 的文档「声明面」列写
`roles` 而机制算出 `roles、tool_providers`）—— 该条**由同轮更新
`docs/architecture/POLICY_SURFACE_AUDIT.md` 的声明面列即可变绿**，不是放宽判据。

**F-6｜【决定性】会话工具今天**根本不可能被执行**（真缺陷，`W-1` 之外的第二层）**

两条各自独立的成因：

1. **装配面缺口（`W-1` 的字面）**：两个组合根本体
   （`services/api/composition.py::_sqlite_orchestration`、
   `services/api/pg_composition.py::_build_pg_orchestration`）调 `build_agent_runtime(...)` 时
   **都没有**传 `register_session_tools` ⇒ 生产路径注册面是 `None`，回落空操作；
   接线只发生在**判据侧**（`tests/e2e/*` 的 `_attach_session_tools`）。
2. **策略面缺陷（本轮新发现）**：
   `adapters/openhands/policy_enforcing_agent.py::_evaluate` 构造
   `PolicyRequest(capability=tool_name, action="execute", scope=session_id)`，而
   `policy.yaml` 的带 scope allow 规则要求 **scope 相等**才匹配 ⇒ `session_id`（会话 UUID）
   **永不**匹配任何规则 ⇒ **每一条**会话工具调用都落 `default_effect: DENY`。桥侧
   `session_tool_invocation.make_tool_invoker` 经 `execute_tool_call` 求值同样**不带** scope；
   运行链用 `phase_capabilities.ScopedPolicy` 补这一字段（`ScopedPolicy.__doc__` 明写
   「不补这一字段就会出现『preflight 放行、执行期落到 default_effect: DENY』的分裂」），
   **会话面没有对应补法**。

**实测**（专属工具名 `artifact.read.probe` / `artifact.read` + 真实
`NativePolicyEvaluator(policy.yaml)`，同一装配只改 scope 一个字段）：

| 场景 | `status` | `executor_reached` |
| --- | --- | --- |
| `artifact.read`（**已放行**），今天的 `scope=session_id` | `SUCCEEDED` | **`[]`** |
| `artifact.read`（已放行），`scope=policy_scope_for("artifact.read")="project"` | `SUCCEEDED` | **`['hi']`** |
| `claim.read`（A 组，**未放行**），同上补 scope | `SUCCEEDED` | `[]` |

⇒ **GOAL-028 EC-03 的「默认装配实跑」证的是会话起得来，不是工具跑得动** ——
在 `map_tools=True` 之外，「跑通」在**工具面**从未发生。这是本 GOAL 的主干靶子。

**F-7｜【决定性】A 组能力「协议可达」会撞两条被钉死的判据 ⇒ 放行需用户拍板**

实测（临时目录里放一份只有 `claim.read` 的协议，**未动树**）：
把 `claim.read` 写进 `required_capabilities` ⇒

- `tests/application/preflight/test_policy_surface_difference_set.py::test_no_protocol_reachable_capability_lacks_a_rule`
  判红 —— `协议可达却无放行规则（W-A 同类活缺口）：{'claim.read': ['probe_claim.yaml']}`；
- 同文件 `::test_each_row_state_matches_the_mechanical_rule` 判红 ——
  `claim.read：文档判 该登记，机制判 该放行`。

而 `tests/application/preflight/test_read_grant_is_per_item.py` 钉着
`EXPECTED_REGISTERED = 15`（差集表「该登记」**恰好 15 条**）并断言这 15 条
**一条都没被放行**（`D-02(b)` 的机械代理，用户 2026-09-25 拍板「维持逐条放行」）。
⇒ **给 A 组读能力放行 = 改既有判据 + 触碰未决口径 ⇒ 需用户拍板**。
**但**：`session_tool_bindings` 的 `tool_name` **不进入** `reachable()`（该机制只扫
`required_capabilities` + 所引合约的 `required_capabilities`）⇒ **承接**可以走绑定/实现面，
**执行**才需要放行。这两件事必须在判据上**可区分**（EC-02(e)）。

**F-8｜两树判词归档缺口**

`tools/two_tree_recheck.py::dump_verdicts` **已经**用
`Path.write_text(..., encoding="utf-8", newline="")`（二进制安全）；缺的是**落点**：
GOAL-028 的留档落在 `scratch/`（`.gitignore` 第 43 行）⇒ 他人 clone 后**无法独立复核**
「两树逐行相同」这条结论。落点选择须同时过两道既有门：
`.cursor/plans` 在 `test_reproducibility_wording.py` 的 `_SCAN_ROOTS` 内；
`docs/**` 在 `tools/docs_consistency_check.py` 的反引号引用面内。

### 退出标准

| EC | 标准 | 验证命令 | 证据来源 | 状态 |
| --- | --- | --- | --- | --- |
| EC-01 | 「出厂即可跑」真形态：会话工具**真被触达**（修 F-6 两层 + 两组合根接线 + 两向反证**合跑** + 默认装配实跑） | 见 frontmatter `exit_criteria[0].verify` | 前后对照读数 + 合跑判词 + 实跑终态 | PASS |
| EC-02 | 「出厂即可跑」机械化 + A 组承接面：一条判据 + 两向反证 + 射程**逐条**分类 + 下界断言 + 「已承接/未放行」可区分 | 见 frontmatter `exit_criteria[1].verify` | 分类表 + 两向判红原文 + 下界读数 | PASS |
| EC-03 | 写能力判定在树 + canonical 唯一性 + 写后读得到 + 旁路反证 + 漏斗缺口残余登记 | 见 frontmatter `exit_criteria[2].verify` | 检索读数 + 读面读数 + 反证原文 | PASS |
| EC-04 | 两树两份判词落档 + `sha256` 断言 + LF 断言 + 两向反证 | 见 frontmatter `exit_criteria[3].verify` | 两份归档 + `sha256` + `\r` 扫描读数 | PASS |
| EC-05 | 自举收口（验证器进树 + 两树 + m0 23/23 + 治理 + 台账逐提交 + 残余/未覆盖逐条） | 见 frontmatter `exit_criteria[4].verify` | 两树 `TWO-TREE PASS` + m0 终态行 + 治理 + 台账 | PASS |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按**迭代日志最后一行** + **工作树 / 远端实况**
判定续点；任何一步完成后立即回写本文件（状态历史 / 迭代日志），保证任意时刻崩溃后重入可续。
**一切状态在文件与工作树里**，不依赖会话记忆。

1. 最后一 cycle 无记录 ⇒ 开 cycle 1：执行「单 cycle SOP」①（derive 子 PLAN）。
2. 有子 PLAN 且仍 `IN_PROGRESS` ⇒ 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit ⇒ 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 ⇒ 执行 ⑤（等待 / 判定）；**禁止猜绿**。
5. CI 有失败且修复次数未达上限 ⇒ 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 ⇒ 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

**本轮特有纪律（每轮进入时逐条复核）**：

- **反证必须合跑**（承 F-4 / `MEM-20261001-180`）：SDK tool registry **只增不减** ⇒
  「没实现」与「未注册」两种反证都会假绿**且方向相反**；判据必须用**专属名字**或**显式摘除**，
  并**在一次运行里合跑两者**。
- **出厂可跑是可复核事实**：EC-01 / EC-02 的判据必须对**生产装配路径**生效
  （`build_agent_runtime` 的真实缺省 + 两个组合根本体），**不得**靠测试后门
  （`map_tools=True` / `register_inert_tools` / 判据侧 `_attach_session_tools`）。
- **写能力走 canonical**：不得旁路（F-3）；写入与**读面可见性**必须一起断言。
- **点名失败而非静默降级**：缺实现 / 缺映射 / 缺 pin / 未批准 —— 一律点名。
- **留档一律二进制写盘**（承 `MEM-20260928-152` + EC-04）：判词 / 日志 / 证据都不得用文本模式。
- **受判面非空**（`MEM-20260922-156`）、**反证两向**（`MEM-20260922-159`）、
  **射程显式分类**（`MEM-20260922-158`）、**不得靠并集掩蔽**（`MEM-20260922-160`）、
  **按压后 raw `sha256` 逐字节复原**。
- **台账逐提交**（承 GOAL-028 EC-04）：合并行必须显式声明覆盖与承担者；
  **空集合 / 空字段 = 未取证**。
- **进程卫生**：起过子进程 / 后台任务后 `taskkill /T /F` 确认零残留。
- **记录自洽**：GOAL 正文表与 frontmatter 的 EC status **同轮同改**；
  **先写记录 → 记录面判据 → 全量门**（承 `MEM-20260928-168`）。
- **本地假绿**：本机绿不等于 Linux 绿 ⇒ 按既有配方在 Linux 侧复验关键判据。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定**一个可独立验收的最小主题**；用 Plan Mode
  流程写子 PLAN（`.cursor/plans/tasks/PLAN-YYYYMMDD-NNN-*.md`，frontmatter 增加
  `parent_goal: GOAL-20261004-029` 并**投影 `ALL_PLAN.md`**）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（**每 WP 独立 commit，只用显式路径**，
  **绝不 `git add -A`**——并发工作树）。
- **③ 本地验证**：m0 按组（python 6 / typescript 9 / framework 8，DSN 固化配方）+
  受影响定向套件 + web 门（tsc / eslint / unit / build / stub / live e2e）。
  **本地不绿不得 push**。顺序固定：**先写记录 → 记录面判据 → 全量门**；
  m0 **独占**运行（跑门时**不改工作树**）、仓库 `.venv`、
  `uv run --frozen --no-sync python -B`、**不接管道**、canonical DSN pin、零进程残留。
- **④ commit**：子 PLAN 收口（RECHECK 完成且 `DONE`），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（**仅限 main**）
  → 用 `git credential fill` 取令牌走 REST API（`/actions/runs?head_sha=<40 位 SHA>` +
  `/jobs`，需**遍历该 SHA 全部 run**；无 `gh` CLI）→ **轮询至终态**；
  记录 run 链接 + 结论 + `run_attempt`；**空集合 / 空字段 = 未取证**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以**独立 commit** 落 main 并回到 ⑤。
  超过 `fix_policy` 上限或命中 `escalation_triggers` ⇒ `status=BLOCKED`。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、`child_plans`、状态历史；
  未达终态 ⇒ 回到 ①（cycle+1）；触顶预算 ⇒ `BLOCKED`。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先**，禁改断言迁就 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`evolution_state.json` 的 `WinError 5`、draft-contract 排序、CI 资源阈值型 RSS） | 按既有配方**单跑取证后独占重跑**；**绝不动阈值**；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → `BLOCKED`（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；**不得**绕过；**不得**宣称安全 |
| 两树不一致 | `tools/two_tree_recheck.py` 报 `DIFF` / `NOT-GREEN` | 归因到「未提交产物 / 本地残留 / 环境」；**先提交再跑**（第二棵是 HEAD 的 checkout） |

**台账口径**：批量推送时 `cancel-in-progress` 会取消在飞的 run ⇒ 一个 cycle **攒成一次推送**
（承 `MEM-20260925-…` 的 M0 并发教训）；被取消的 run **如实登记为 `cancelled` + 原因**。

## 终止与收口

- **ACHIEVED**：全部 EC `PASS` **且有证据**（实跑读数，不是推测）+
  `latest_recheck` 指向 `PASS` / `PASS_WITH_WARNINGS` 的 RECHECK +
  **两树复检同结论**（含 EC-04 的两份判词归档）+ as-is m0 **23/23 跑在记录写入之后** +
  治理 `validate.py` 绿 + CI 台账**逐提交**到终态 + 残余与未覆盖范围逐条明写。
- **BLOCKED**：命中任一 `escalation_triggers`；或 `budget.max_cycles` 触顶；
  或 `no_progress_stop_cycles` 连续未推进任何 EC；或本机无法验证（记 `PENDING` 并**停止推进**）。
  ⇒ 立即停止循环并留人工决策入口（写明**缺哪一条事实**才能继续）。
- **ABORTED**：用户显式取消，或方向被证明不可达（须写明证伪证据）。
- **收口动作**：① 收口 cycle 的验证器 + `IN_SCOPE`（纯收紧）；② 两树复检 + 判词归档；
  ③ 记录写入**之后**跑 as-is m0；④ 治理校验；⑤ CI 台账逐提交；⑥ 残余/未覆盖逐条；
  ⑦ 收口 PLAN + RECHECK + `latest_recheck` 回填 + 状态历史。
- **明确否认**：本轮**不**宣称项目安全（`R-M1` 未收口），**不**宣称投递语义为「恰好一次」
  （**否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 `BLOCKED`。

### 本 GOAL 特有：需用户拍板的决策（建档轮实测得出）

| 待拍板项 | 内容 | 为什么本 GOAL 不能自行决定 |
| --- | --- | --- |
| `D-02(b)` 复现 | **A 组读能力（`claim.read` / `deliverable.read` / `experiment.read` / `experiment_plan.read` / `budget.read` / `agent_run.read`）是否逐条放行** | 放行任一条会打红 `test_read_grant_is_per_item` 的 `EXPECTED_REGISTERED = 15` 与「一条都没被放行」两条断言（**改既有判据**，禁）；且该口径在 GOAL-016 EC-02 已由用户拍板「维持逐条放行」，属**未决口径**（`POLICY_SURFACE_AUDIT.md` 的「需拍板的一条口径」）。**EC-01 / EC-02 因此只做「承接」不做「放行」**——「已承接但未放行」在判据上必须**可区分**，**不得**冒充成已跑通 |
| D 组能力审批通道 | `external.publish` / `package.install` / `git.commit` / `workspace.delete`（`policy.yaml` 现为 `require_approval`） | 接通审批通道**需用户拍板**；本轮只登记，**不得**实现 |
| `D-02` 相关：读类是否成类预放行 | 一次 `allow` 覆盖整类读能力 | 同 `D-02(b)`；且属「新增类别级 allow」（明文禁） |

### 承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开

### 承继：GOAL-026 / 027 / 028 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子 `scanner_enobufs` 未得完整结论 | **原样保留**（**不得**据此宣称项目安全） |
| `R26-1` … `R26-8` | 死信人工恢复 / 工具面断路器 / 在飞取消 / 补偿 / 事件消费者 / HTTP 幂等 store / 台账原始证据在树外 / GOAL 正文表不在判词面 | **原样保留** |
| `W27-1` … `W27-6` | 新协议与既有检索协议并存 / 点分路径单层 / 性质两向两 adapter 分别取证 / 新协议未重测策略 DENY 面 / 评审契约不声明性质维度 / 实验任务不在任务投影 | **原样保留** |
| `W10` / `W11` / `W12` | 单 token ⇒ 单主体 / BOLA·BFLA 未做 / 部署面未验证 | **原样保留**（本 GOAL 不碰认证面） |
| `G24-4` / `G24-5` | `LineageNodeDto.label` 语义 / 文档条款非运行时拦截器 | **原样保留** |
| 历史遗留 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**脚本加入必备清单） |
| GOAL-028 `W-1` | 映射目标须装配方提供（**机制成立 ≠ 出厂即可跑**） | **本轮靶子**：EC-01 接两个组合根 + 修 F-6 策略面缺陷；**残余**部分（见下）如实登记 |
| GOAL-028 `W-2` … `W-5` | 绑定是 phase 级非全局表 / 桥的 policy 拦截未单钉 / 不支持一 provider 多工具名 / 第三方 MCP 未验证 | **原样保留** |
| GOAL-027 `W27-*` 族 / GOAL-028 `W-1`（活检索） | 活检索真实出网未实跑 / 默认门看不见子进程出站 / 限速是进程内语义 / 活模式只覆盖两个工具名 / 第三方结论是静态判断 / 活检索未接进运行链 | **原样保留**（与 GOAL-027 同姿态） |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261004-275`（EC-01：F-6 修复 + A 组承接 + 组合根接线） | `e52a82c`（F-6 scope 修复 + 判据）+ `fc9314c`（CI 双红修复：探针类提到模块级）+ `53a944e`（canonical 读面 ToolProvider + 出厂绑定表）+ `ea08716`（两组合根接注册面 + 出厂注册面判据 13 例）+ `fd0dbb8`（CI 双红修复：规模门 —— composition 450 行 / read_provider 函数拆分）+ 本条回写提交 | 新增判据 **33 passed**（适配器 7 + canonical 13 + 出厂注册面 13）；`tests/api + tests/adapters + tests/tooling + tests/architecture/python` **2612 passed / 7 skipped**；规模门 **1098 passed**（`composition.py` 恰 450 行）；`ruff` / `format` / `mypy`（1088 files）绿；治理 `validate.py` 绿 | 见「CI 台账」 | **六处按压（全部两向、按 `sha256` 逐字节复原）**：① 撤 agent 门 scope 补齐 ⇒ 2 failed（`bdc1f818…`）；② 撤桥补齐器 ⇒ 1 failed（`f629d302…`）；③ 阈值改回 32 KiB ⇒ 7 failed（`10eae581…`）；④ 删 SQLite 根 wiring ⇒ 1 failed；⑤ 坏版本 `git show e52a82c:…` 与合约文件**合跑** ⇒ 2 failed 逐字复现 CI 签名；⑥ 判据的探针类放函数内 ⇒ 打红**别的文件**（本地单跑看不见）⇒ 已改模块级并**合跑**验证 | EC-01 **仍未收口**（`RECHECK-20261004-276` 的 `W-2`/`W-3`）：两条反证尚未在**默认装配实跑**里合跑一次；默认装配下 run 到 `SUCCEEDED` 且 executor 真被触达（端到端）未做 | cycle 2 = 收 EC-01 的 `W-2`/`W-3`（默认装配端到端实跑） |
| 2 | `PLAN-20261005-277`（EC-01 收口 + EC-02） | `f64a1cf`（action 参数平铺修复 + 端到端判据）+ `df4ddd9`（A 组承接扩到五条 + EC-02 机械化判据）+ 本条回写提交 | 新增判据 **20 passed**（端到端 12 + 承接面 8）；`tests/adapters + architecture/python + application + e2e + api + loaders` **2291 passed / 21 skipped**；`ruff` / `format` / `mypy`（1090 files）绿；治理 `validate.py` 绿 | 见「CI 台账」 | **两处按压（各自独立、两向）**：① 把 action 的 `arguments` 包装字段放回 ⇒ **5 failed**（executor 未触达 + schema 有包装 + 平铺不可校验）；② 删掉 `budget_read` 的实现 ⇒ **2 failed**（下界断言 + 工具面）。两处均复原后全绿 | 承接面 **12/46 → 17/46**；A 组射程内五条（`artifact.read` / `evidence.read` / `workspace.read` / `budget.read` / `deliverable.read`）**EC-01 与 EC-02 双双收口**；余下 EC-03（写能力判定）/ EC-04（判词归档）/ EC-05（自举收口） | cycle 3 = **EC-03**（写能力的 canonical 路径与旁路风险） |
| 3 | `PLAN-20261005-279`（EC-03） | `72b29ef`（EC-03 判据）+ 本条回写提交 | 新增判据 **9 passed**；`tests/architecture/python + tests/application + 读面 API` **995 passed / 1 skipped**；`ruff` / `format` / `mypy`（1091 files）绿；治理 `validate.py` 绿 | 见「CI 台账」 | **一处判据自身缺口（按压暴露并修正）**：首版「先判后写」只扫 `ast.Name` 调用 ⇒ 看不见属性调用式写入（`save_audit`）⇒ 把守卫挪到其后时**判据仍绿**；改为**语句级**顺序断言后 该按压判红（复原绿） | **EC-03 收口**；**残余原样保留**：域无 `Deliverable` 实体 / store 无闸门 / 实验计划写面无共同漏斗（3 写入点 + 无条件 upsert）/ 写能力仍落 `default_effect: DENY` | cycle 4 = **EC-04**（两树判词归档留档） |
| 4+5 | `PLAN-20261005-281`（EC-04 + EC-05） | `e1f2b4b`（EC-04 归档 + 判据）+ `c8e0cd5`（EC-05 验证器 + 工具集 + IN_SCOPE 纯收紧）+ `dcd8387`（去循环依赖 + 重生成归档）+ 本条回写提交 | 验证器本树 **54 PASS / 0 FAIL**；EC-04 判据 **13 passed**；四道门 **8 passed**；`ruff` / `format` / `mypy`（1092 files）绿；治理 `validate.py` 绿（GOAL/A‑PLAN/复检/记忆交叉引用） | as-is m0 **23/23**（`PASS []=24` / `FAILED []=0` / **5080 passed / 21 skipped**，python 段 643.63s；记录写入之后、独占、canonical DSN pin、不接管道、零残留）；CI 见「CI 台账」 | **一处自身设计缺陷（按压暴露）**：EC-05 验证器起初**读**两树入口写回的归档 ⇒ 输入即输出 ⇒ 两棵树读到不同历史残留、**永不收敛**（首跑 current 红 / clean 绿）；修法 = 归档形态归 EC-04 专属判据、验证器不再碰那些文件（沉淀 `MEM-20261005-186`）。另两处：`IN_SCOPE` 是 `AnnAssign` 而读取器只认 `ast.Assign` ⇒ 判据假红；验证器 mypy 两处 | **无剩余差距**（五 EC 全 PASS）；残余与未覆盖范围原样保留（见「不进入循环」节） | GOAL 收口（`ACHIEVED`）|
| 0 | （建档轮，无子 PLAN——交付物是 GOAL 文件本身） | `ff6e0c4` + `ebb6101` | 治理 `validate.py` 绿；勘察脚本与读数留档 `scratch/goal029-recon.md`（**树外**，`.gitignore` 覆盖，承 `R26-7`）；勘察打过的补丁按 `sha256sum -c` **逐字节复原**（`tool_providers.yaml` = `55c302c1…`、`POLICY_SURFACE_AUDIT.md` = `7372c6a4…`）；记录面判据 **45 passed**；`tests/tooling` 全量 **1273 passed**；`DOCS-CHECK PASS: 6 deterministic checks`；`validate_bundle` = `验证通过` | **M0 [`37203151559`](https://github.com/Eswink/research-system-new/actions/runs/37203151559) 八 job 全 `success`**（container-quality / observability-overhead-ubuntu-latest / quality-ubuntu-latest / observability-overhead-windows-latest / eval-gate / console-frontend / collector-quality / quality-windows-latest）+ **Push-on-main [`37203151156`](https://github.com/Eswink/research-system-new/actions/runs/37203151156) 3/3 `success`**（CodeQL：javascript-typescript / actions / python）；两者 `run_attempt=1`；该 SHA 下 `total_count=2`、**无 `cancelled`** | 无（勘察轮不动产品代码） | 五 EC 全 `PENDING`；**F-5 / F-6 / F-7 三条实测结论推翻了 prompt 起点的表述**，已写入「事实层结论」 | cycle 1 = **EC-01**（会话工具真被触达：修 F-6 + 两组合根接线） |

### CI 台账（逐提交）

| 提交 | 自带 run | 结论 | 备注 |
| --- | --- | --- | --- |
| `ff6e0c4`（建档） | [`37203151559`](https://github.com/Eswink/research-system-new/actions/runs/37203151559)（M0）+ [`37203151156`](https://github.com/Eswink/research-system-new/actions/runs/37203151156)（CodeQL） | 两 run 全 `success` | `run_attempt=1`；该 SHA 下 `total_count=2`，逐 run 遍历（无短 SHA 假零） |
| `e52a82c`（F-6 scope 修复） | [`37206225518`](https://github.com/Eswink/research-system-new/actions/runs/37206225518)（M0，**首跑 failure**）+ [`37206225281`](https://github.com/Eswink/research-system-new/actions/runs/37206225281)（CodeQL） | M0 首跑 `quality-{ubuntu,windows}-latest` **双红**（判据侧 `<locals>` 毒化）；CodeQL 全绿 | `run_attempt=1`；红因已由 `fc9314c` 修复并以**合跑**逐字复现签名 |
| `fc9314c`（CI 双红修复） | [`37207673260`](https://github.com/Eswink/research-system-new/actions/runs/37207673260)（M0）+ [`37207672579`](https://github.com/Eswink/research-system-new/actions/runs/37207672579)（CodeQL） | 两 run 全 `success` | `run_attempt=1`；该 SHA 下 `total_count=2` |
| `4fd6e81`（cycle 1 台账回写） | 与 `fc9314c` **同批推送** | `success`（由该批承担） | 合并行**显式声明覆盖**：本条绿由 `fc9314c` 的 run 承担（同批，`head_sha` 归 `fc9314c`） |
| `53a944e`（canonical 读面 ToolProvider） | 与 `ea08716` **同批推送** | 见下行 | 合并行**显式声明覆盖**：本条无自带 run，绿由 `ea08716` 承担 |
| `ea08716`（组合根接线） | [`37210026847`](https://github.com/Eswink/research-system-new/actions/runs/37210026847)（M0，**首跑 failure**）+ [`37210026195`](https://github.com/Eswink/research-system-new/actions/runs/37210026195)（CodeQL，`success`） | M0 首跑 `quality-{ubuntu,windows}-latest` **双红**（规模门：`composition.py` 超 450 行 + `read_provider.py` 有 51 行函数）；CodeQL 全绿 | `run_attempt=1`；红因已由 `fd0dbb8` 修复 |
| `fd0dbb8`（规模门修复） | [`37212899841`](https://github.com/Eswink/research-system-new/actions/runs/37212899841)（M0）+ [`37212899494`](https://github.com/Eswink/research-system-new/actions/runs/37212899494)（CodeQL） | **两 run 全 `success`**（M0 八 job 全绿） | `run_attempt=1`；该 SHA 下 `total_count=2`，逐 run 遍历 |
| `b158451`（cycle 1 台账终态） | [`37214128223`](https://github.com/Eswink/research-system-new/actions/runs/37214128223)（M0）+ [`37214128014`](https://github.com/Eswink/research-system-new/actions/runs/37214128014)（CodeQL） | **两 run 全 `success`**（M0 八 job 全绿、`non-success: none`） | `run_attempt=1`；该 SHA 下 `total_count=2` |
| `f64a1cf`（action 平铺修复 + 端到端判据） | [`37218524934`](https://github.com/Eswink/research-system-new/actions/runs/37218524934)（M0）+ [`37218524605`](https://github.com/Eswink/research-system-new/actions/runs/37218524605)（CodeQL） | **两 run 全 `success`** | `run_attempt=1`（该批 `total_count=2`；本行由该批的绿承担） |
| `df4ddd9`（A 组承接扩到五条 + EC-02 机械化） | [`37220559698`](https://github.com/Eswink/research-system-new/actions/runs/37220559698)（M0，**`cancelled`**）+ [`37220559821`](https://github.com/Eswink/research-system-new/actions/runs/37220559821)（CodeQL，`success`） | M0 **`cancelled`**（`quality-{ubuntu,windows}-latest` 被取消） | **`cancelled` 原因如实登记**：**同一 cycle 内紧接推送下一个提交**（`2c52b41`）⇒ GitHub 的 `cancel-in-progress` 取消了在飞的 run （承 `MEM-20260925-…` 的 M0 并发教训）。**绿由该 HEAD 承担**：`2c52b41` 的 M0 八 job 全 `success` 覆盖本条（见下行）。**不得**把 `cancelled` 记成 OK |
| `2c52b41`（cycle 2 收口记录） | [`37220906258`](https://github.com/Eswink/research-system-new/actions/runs/37220906258)（M0）+ [`37220905441`](https://github.com/Eswink/research-system-new/actions/runs/37220905441)（CodeQL） | **两 run 全 `success`**（M0 **八 job 全绿**） | `run_attempt=1`；该 SHA 下 `total_count=2`；**本条同时承担 `df4ddd9` 的绿**（同批推送，覆盖关系已在其行显式声明） |
| `95c4506`（cycle 2 CI 台账） | [`37221995317`](https://github.com/Eswink/research-system-new/actions/runs/37221995317)（M0，**`cancelled`**）+ [`37221995039`](https://github.com/Eswink/research-system-new/actions/runs/37221995039)（CodeQL，`success`） | M0 **`cancelled`** | **原因如实登记**：同一 cycle 内紧接推送 `72b29ef` ⇒ `cancel-in-progress` 取消在飞 run（与 `df4ddd9` 同一形态，承 `MEM-20260925-…` 的 M0 并发教训）。**绿由 HEAD `6e0b78c` 承担**（下下行）|
| `72b29ef`（EC-03 判据） | **无自带 run**（该 SHA 下 `total_count=0`） | 见下行的 HEAD | **显式覆盖声明**：`covered_by: 6e0b78c`；`coverage_note`：本条与 `6e0b78c` 同批推送，被 `cancel-in-progress` 吞掉 ⇒ **该 SHA 下没有任何 run**（空集合 = 未取证），绿由 HEAD `6e0b78c` 的 M0 八 job 全绿承担；**不得**据此记 OK |
| `e1f2b4b`（EC-04 归档 + 判据） | [`37224687688`](https://github.com/Eswink/research-system-new/actions/runs/37224687688)（M0，**failure**）+ [`37224687586`](https://github.com/Eswink/research-system-new/actions/runs/37224687586)（CodeQL，`success`） | M0 `quality-ubuntu-latest` **failure** | **如实登记**：`test_text_mode_and_binary_mode_differ` 报「文本模式必须与二进制模式产生不同 sha256」——**只在 Linux 暴露**的判据缺陷（平台相关断言），已由 `ada7721` 修复；本地 Windows 全绿，属**假绿**（本地门 ≠ Linux 门，承 `MEM-20260928-152` 的同类） |
| `c8e0cd5`（EC-05 验证器 + IN_SCOPE） | [`37225648490`](https://github.com/Eswink/research-system-new/actions/runs/37225648490)（M0，**`cancelled`**）+ [`37225647672`](https://github.com/Eswink/research-system-new/actions/runs/37225647672)（CodeQL，`success`） | M0 **`cancelled`** | **原因如实登记**：同批紧接推送 `dcd8387` ⇒ `cancel-in-progress` 取消在飞 run（与 `df4ddd9`/`95c4506` 同一形态）。绿由后续 HEAD 承担 |
| `dcd8387`（去循环依赖 + 重生成归档） | [`37225817553`](https://github.com/Eswink/research-system-new/actions/runs/37225817553)（M0，**failure**）+ [`37225817156`](https://github.com/Eswink/research-system-new/actions/runs/37225817156)（CodeQL，`success`） | M0 `quality-ubuntu-latest` **failure** | **同一根因**（平台相关断言）——与 `e1f2b4b` 同签名；修复合入 `ada7721` |
| `94be025`（收口记录） | **无自带 run**（该 SHA 下 `total_count=0`） | 见下行的 HEAD | **显式覆盖声明**：`covered_by: 7345f2f`；`coverage_note`：本条与 `656ae37`/`7345f2f` 同批推送，被 `cancel-in-progress` 吞掉 ⇒ 空集合 = 未取证；绿由 HEAD `7345f2f` 承担 |
| `656ae37`（m0 回填） | [`37227460714`](https://github.com/Eswink/research-system-new/actions/runs/37227460714)（M0，**`cancelled`**）+ [`37227460037`](https://github.com/Eswink/research-system-new/actions/runs/37227460037)（CodeQL，`success`） | M0 **`cancelled`**（**首跑时 `quality-ubuntu-latest` 曾 failure** —— 即平台相关断言那个真红） | **原因如实登记**：该 run 先因判据缺陷判红，修复推送后同批被 `cancel-in-progress` 取消；**红因已由 `ada7721` 修复**，绿由 `ada7721` / `7345f2f` 承担 |
| `ada7721`（**修 CI 判红**：平台分档断言） | [`37228458507`](https://github.com/Eswink/research-system-new/actions/runs/37228458507)（M0）+ [`37228458316`](https://github.com/Eswink/research-system-new/actions/runs/37228458316)（CodeQL） | **两 run 全 `success`**（M0 八 job 全绿） | `run_attempt=1`；**本行同时承担 `94be025` / `656ae37` 的绿** |
| `7345f2f`（RECHECK 补记 W-7） | [`37228458507`](https://github.com/Eswink/research-system-new/actions/runs/37228458507)（M0）+ [`37228458316`](https://github.com/Eswink/research-system-new/actions/runs/37228458316)（CodeQL） | **两 run 全 `success`**（M0 八 job 全绿） | `run_attempt=1`；该 SHA 下 `total_count=2`，逐 run 遍历 |
| `6e0b78c`（cycle 3 收口记录） | [`37222948928`](https://github.com/Eswink/research-system-new/actions/runs/37222948928)（M0）+ [`37222948421`](https://github.com/Eswink/research-system-new/actions/runs/37222948421)（CodeQL） | **两 run 全 `success`**（M0 **八 job 全绿**、`non-success: none`） | **本条同时承担 `95c4506` 与 `72b29ef` 的绿**（两条的覆盖关系已各自在其行显式声明） |
| `ebb6101`（建档轮台账回填） | [`37204488763`](https://github.com/Eswink/research-system-new/actions/runs/37204488763)（M0）+ [`37204488695`](https://github.com/Eswink/research-system-new/actions/runs/37204488695)（CodeQL） | 两 run 全 `success` | `run_attempt=1`；该 SHA 下 `total_count=2` |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | **ACHIEVED** | **收口后 CI 补记**：`e1f2b4b` / `dcd8387` 的 M0 `quality-ubuntu-latest` **failure** —— 根因**同一**：`test_text_mode_and_binary_mode_differ` 断言「文本模式必与二进制模式产生不同 `sha256`」，而**行尾转换是平台相关的**（Windows 转 CRLF、Linux 不转）⇒ 在 Linux 上**假红**（本地 Windows 全绿 = **假绿**，承 `MEM-20260928-152` 同族）。**修法**（`ada7721`，不放宽）：拆两档 —— 跨平台硬断言（入口写法必产纯 LF）+ 平台事实（按 `os.name` 断言转换是否发生）；判据 13 → **14 passed**；沉淀为 `RECHECK-20261005-282` 的 **`W-7`**（与 `W-4` 同族：对象没变，是断言覆盖的**条件集**错了）。**终态 CI**：`ada7721` / `7345f2f` 的 M0 八 job + CodeQL 全 `success`（`run_attempt=1`）。台账逐提交登记：`e1f2b4b` failure（真红，已修）/ `c8e0cd5` cancelled（同批推送）/`dcd8387` failure（同根因）/ `94be025` 无自带 run（`covered_by: 7345f2f` + 说明）/ `656ae37` cancelled（首跑曾真红，修复推送后被取消）/ `ada7721` 与 `7345f2f` 全绿。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-05 | **ACHIEVED** | **cycle 4+5（EC-04 + EC-05 收口）⇒ GOAL 收口**。**EC-04（两树判词归档留档，收 GOAL-028 的缺口）**：两份归档落 `.cursor/plans/goals/evidence/`（各 **2593 字节 / 54 行 / CR=0 / `sha256` 相同** `db4faa07d42532d0…`，二进制写盘）；判据 `test_two_tree_verdicts_are_archived.py`（13 passed）断言落点在树（不被 `.gitignore` 覆盖）、两份 `sha256` 相同、逐行相同、判词纯度、路径无关；**两向反证**：文本模式写一份 ⇒ 2 failed（实测 18 个 CR）⇒ 二进制复原绿；并固定两条「为什么必须读 raw bytes」的实测事实（文本模式写 CRLF；`.gitattributes` 的 `eol=lf` 会静默归一化 ⇒ `git diff` 不足以充当逐字节证据）。**EC-05（自举收口）**：收口验证器 `tools/verify_goal029_closeout.py`（**419 行** ≤450，**复用**`closeout_recheck_assertions.standard_verdicts`，只写本轮特有断言）+ 只读工具集`tools/closeout_recheck_tools.py`（118 行，**按路径加载** —— `tools/` 不是包），两者**双双进 `IN_SCOPE`（纯收紧）**；四道门 8 passed。**两树复检**：`--script-mode shared` ⇒ 两树各 **54 判词**、`sha256` 相同、`COMPARE identical=True`、**`TWO-TREE PASS`**（两树 exit=0）。**本轮实测并修掉的三处自身缺陷**：① **循环依赖**——验证器起初读两树入口写回的归档 ⇒ 输入即输出 ⇒ 两棵树读到不同历史残留且**永不收敛**（首跑 current 红 / clean 绿），修法 = 归档形态归 EC-04 专属判据（沉淀 `MEM-20261005-186`）；② `IN_SCOPE` 是 **`AnnAssign`** 而读取器只认 `ast.Assign` ⇒ 判据**假红**（与 `MEM-20261005-185` 同族：判据射程要按压）；③ 验证器自身 mypy 两处（`literal_eval` 的 Any 返回 / `attr-defined`）。**两树首跑 RED = 正确行为**（干净树是已推送 HEAD 的 checkout，不含未提交验证器）⇒ 提交推送后复跑 PASS，这同时是两树入口**有效性**的正控制。**GOAL 收口**：五 EC 全 PASS + `RECHECK-20261005-282` = **PASS_WITH_WARNINGS**（六条 W-NN）+ 治理 `validate.py` 绿 + **as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` **0** / **5080 passed / 21 skipped / 117 warnings**，python 段 `in 643.63s`；日志 `scratch/goal029-m0-*.log`；**记录写入之后**、独占运行、仓库 `.venv`、canonical DSN pin、不接管道、**零 python 残留**）+ CI 台账逐提交。**承继残余原样保留**（`R-M1` / `R26-*` / `W27-*` / `W10-12` / `G24-4/-5` / 历史 `tools/` 无机器门）；**本轮新增残余**：端到端判据用已放行能力名（专属名会被策略面正确拒绝）/ `arguments` 由字段变方法是对外形状变化 / 计划写面无共同漏斗 / 域无 `Deliverable` 实体 / store 层无闸门。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-05 | ACTIVE | **cycle 3（EC-03 收口）**：把「写能力没有旁路」变成可复核的机械事实。**判定（EC-03 原文允许的第三条路）**：`deliverable.write` / `deliverable.edit` 域里**没有实体**（无 `Deliverable` 类）、**没有 HTTP 写面**、差集表判**「该拒绝」**⇒ 本 GOAL **不实现写工具、不放行**，只做判定与取证。**新增判据**（`test_deliverable_write_stays_on_the_canonical_path.py`，9 passed）五件事：① **canonical 唯一性**（AST 扫生产根：构造该 artifact id 的位置**只有** `m12_reference/persistence.py:107`；`persist_completion` 的生产调用点**只有** `clean_run.py:174`）；② **先判后写**（**语句级**顺序：准入先于任何写入）；③ **写后读得到**（canonical 落点 ⇒ 读面工具 `deliverable_read` 读到同一 payload 与 digest；未产出 ⇒ 点名）；④ **旁路可抓**（准入 = manifest digest 对账 + `RUNNING→SUCCEEDED` 迁移两重）；⑤ **残余登记**（计划写面无共同漏斗：3 个生产写入点 + 无条件 upsert）。**判据自身的一处缺口（按压暴露）**：首版「先判后写」只扫 `ast.Name` 调用 ⇒ 看不见属性调用式写入（`persistence.experiment_store.save_audit(...)`）⇒ 把守卫挪到它后面时**判据仍绿**；改为语句级顺序断言后该按压判红（复原绿）—— 这条修正本身是 EC-03 的一部分：「判据咬不咬得住」也需要按压取证。**残余原样保留**：域无 `Deliverable` 实体 / store 层无闸门（保护来自状态机而非写入点，已钉住）/ 实验计划写面无漏斗 / 写能力仍被策略面判「该拒绝」。**EC-01 / EC-02 / EC-03 三条 PASS**；`RECHECK-20261005-280` = PASS_WITH_WARNINGS（五条 W-NN）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-05 | ACTIVE | **cycle 2（EC-01 收口 + EC-02 收口）**：把 EC-01 从「策略面不再无条件拒绝」推进到「**模型真的调了这个工具、executor 真的跑了**」，并把「出厂即可跑」变成机械事实。**① 第五个真缺陷（本轮实测）**：`SessionToolAction` 声明了 `arguments: dict` **包装字段**，而 SDK 把 action 字段渲染成**模型可见的参数 schema** —— 模型按常理平铺发 `{"artifact_id": "x"}` 撞 base `Schema` 的 `extra="forbid"` ⇒ `Error validating tool 'artifact.read': Extra inputs are not permitted`（**调用到了桥、却在校验处被拒**）。SDK 自己的内建工具一律平铺（`ThinkAction.thought` / `FinishAction.message`）⇒ 改为 `ConfigDict(extra="allow")` + `arguments()` 读 `model_extra`，schema 随之为 `additionalProperties: true`。**② 端到端判据**（新文件 `tests/e2e/test_session_tool_call_on_the_default_assembly.py`，12 passed）：勘察发现**全仓 e2e 的 mock 端点没有一处会发 `tool_calls`** ⇒「会话起得来」与「工具跑得动」的落差**从未被任何东西看着**（这正是 `W-3` 长期开着的原因）；补上唯一会发工具调用的夹具后实测：executor 触达记录 **逐字等于** 模型发出的平铺参数、结果经 `role=tool` 消息回到模型。判据另含**两条反证合跑**（承 MEM-20261001-180：registry 进程级只增不减 ⇒ 带**显式摘除** +
「合跑证据」断言）与**缺口取证**（断言本文件是仓内唯一发 `tool_calls` 的夹具，出现第二个即判红）。**③ A 组承接面扩到五条**（EC-01 的 AC 要求 ≥5；cycle 1 只落 3 条）：新增 `budget_read` / `deliverable_read` 两条**真实现**（都读 canonical state）⇒ **12/46 → 17/46**；出厂目录同轮声明五条 A 组读能力 + 同轮更新 `POLICY_SURFACE_AUDIT.md` 的声明面列（F-5 已实测：扩能力只打红那一列，属**文档同源**而非放宽判据）。**④ EC-02 机械化**（新判据 `test_capability_coverage_is_implemented.py`，8 passed）：主判据「声明了 ⇒ 一定有实现」（缺一即点名能力名 + 工具名）+ **反证两向**（声明了没实现 / 实现了没声明各判红）+ **射程逐条分类**（46 条逐条要么在射程内、要么登记在案带组别与理由；空理由与自相矛盾各判红）+ **下界断言**（承 MEM-160）+ **并集恰好等于词表**。判据当场抓到我的两处疏漏（`gpu.use` 未分类、射程内条目重复登记）。**⑤ 顺带修掉一条真缺陷**：`budget_read` 的 run 归属过滤起初按 reservation_ref 匹配，实测该 ref 是内容摘要（`budget-reservation:<hex>`）、**不含** run 标识 —— 归属只在 `BudgetReservation.scope`；已改读既有字段，不新造第二套归属口径。**按压两处（各自独立）**：包装字段放回 ⇒ 5 failed；删 `budget_read` 实现 ⇒ 2 failed；均复原后全绿。**EC-01 与 EC-02 双双 PASS**；`RECHECK-20261005-278` = PASS_WITH_WARNINGS（六条 W-NN：端到端那半用**已放行**能力名（专属名会被策略面正确拒绝）/ `arguments` 由字段变方法是对外形状变化 / 端到端不驱动 run 编排 / 不覆盖多轮与并行工具调用 / 装配面按压未在本轮重做 / 缺口取证是方法论提示）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-04 | ACTIVE | **cycle 1（EC-01 主干，未收口）**：修掉建档轮实测到的 **F-6 真缺陷** —— 会话工具的求值 scope 曾用会话 id（`PolicyEnforcingAgent._evaluate`），而 `policy.yaml` 的带 scope `allow` 规则要求 scope 相等 ⇒ **每一条**会话工具调用都落 `default_effect: DENY`、executor 一次也不会被触达（run 终态却是 `SUCCEEDED`）。**实测对照**（真实 `NativePolicyEvaluator`、同一装配只差一个字段）：`artifact.read`（已放行）修复前 `executor_reached=[]` → 修复后 `['hi']`；`claim.read`（未放行）与 `external.publish`（需审批）修复后仍 `[]`。**修法**：两条执行期门复用**既有那一张** `policy_scope_for` 表（桥复用既有 `ScopedPolicy`），不新造表、不动任何 allow。**从零到一**：`tool_providers.yaml` 声明的两件 NATIVE provider（`m12_artifact` / `openhands_workspace`）此前**全仓零实现** ⇒ 本轮新增 `adapters/canonical/read_provider.py`（canonical 读面接成可执行工具）；两个组合根本体此前都**不传** `register_session_tools` ⇒ 本轮接上（`session_tool_support` 收拢装配决策，两树只差 Port 实例）。**实测**：`assemble()`（真实 SQLite 生产路径）⇒ 按工具名注册后 `artifact.read` / `evidence.read` / `workspace.read` **全部可解析**。**顺带修掉两条真缺陷**：① 会话桥**永远取不到**小结果（`spill_large_result` 缺省阈值 32 KiB ⇒ 低于阈值不落盘，而桥必须交回内容）⇒ 按消费者要求把阈值设为 1（与运行链 `literature_chain_support.py` 同源约定）；② `composition.py` 恰在 450 行硬上限上，wiring 必须净增 0 行。**六处按压（全部两向、`sha256` 逐字节复原）**：撤 agent 门补齐 ⇒ 2 failed（`bdc1f818…`）；撤桥补齐器 ⇒ 1 failed（`f629d302…`）；阈值改回 32 KiB ⇒ 7 failed（`10eae581…`）；删 SQLite 根 wiring ⇒ 1 failed；坏版本与合约文件**合跑** ⇒ 2 failed 逐字复现 CI 签名。**两轮 CI 双红（均为判据侧自伤，已修）**：① `e52a82c` 探针 `Action`/`Observation` 子类写在函数内（`<locals>`）⇒ SDK 枚举具体子类时毒化**同进程后续所有**事件 round-trip ⇒ 打红 `tests/contracts/test_agent_runtime_contract.py` 两条 fork 判据（**本地单跑看不见**，全量收集才暴露；这正是我在该文件 docstring 里**引用过**的同族教训）⇒ 提到模块级 + 合跑两向取证；② `ea08716` 规模门：`composition.py` 超 450 行 + `read_provider.py` 51 行函数 ⇒ 拆函数 + wiring 压成一行。新增判据 **33 passed**（适配器 7 / canonical 13 / 出厂注册面 13）；`tests/api + tests/adapters + tests/tooling + tests/architecture/python` **2612 passed / 7 skipped**；规模门 1098 passed；`ruff` / `format` / `mypy`（1088 files）绿。**终态 CI**：`b158451` 的 M0 八 job + CodeQL 全 `success`（`run_attempt=1`）。**EC-01 未收口**（`RECHECK-20261004-276` 的 `W-2`/`W-3`：两条反证尚未在默认装配实跑里合跑一次；默认装配下 run 到 `SUCCEEDED` 且 executor 真被触达未做）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-04 | ACTIVE | **建档（cycle 0）**：读 `README.md` 的 GOAL 格式契约 + 只读勘察。**只读勘察推翻了三处起点表述**，逐条实测：**① 承接面 12/46 复核通过**（46 条能力中 12 条被四个 provider 承接）；**② 【F-6】会话工具今天根本不可能被执行** —— `policy_enforcing_agent._evaluate` 用 `scope=session_id` 而 `policy.yaml` 的带 scope allow 规则要求 scope 相等 ⇒ 每条会话工具调用都落 `default_effect: DENY`；桥侧 `execute_tool_call` 同样不带 scope（运行链有 `ScopedPolicy` 补、会话面没有）。**实测对照**（真实 `NativePolicyEvaluator(policy.yaml)`、同一装配只差一个字段）：`artifact.read`（已放行）今天 `status=SUCCEEDED` 但 **`executor_reached=[]`**；换成 `policy_scope_for` 后 **`executor_reached=['hi']`**。⇒ **GOAL-028 EC-03 的「默认装配实跑」证的是会话起得来，不是工具跑得动**；**③ 【F-7】A 组能力「协议可达」撞两条钉死判据**（`test_no_protocol_reachable_capability_lacks_a_rule` 与 `test_each_row_state_matches_the_mechanical_rule` 实测判红），而放行会打红 `test_read_grant_is_per_item` 的 `EXPECTED_REGISTERED = 15` ⇒ **放行需用户拍板**（`D-02(b)`），本 GOAL 只做**承接**并把「已承接/未放行」做成**可区分**的判据；**④ 【F-5】`tool_providers.yaml` 的 id 集被精确钉死**（新增 id 实测打红 `test_existing_providers_are_untouched`）⇒ 承接面只能靠**扩展既有 provider**（实测可行）；**⑤ 【F-3】写能力**：域里**没有** `Deliverable` 实体、无写面、差集判「该拒绝」，canonical 唯一 writer 是 `persist_completion`；`ExperimentStore.save_plan` 是**无条件 upsert** 且两处生产写入无共同漏斗（**残余**）；**⑥ 【F-4】SDK registry 进程级只增不减**（源码实测 `register_tool` 无撤销入口、`resolve_tool` 未命中点名）⇒ 两条反证**必须合跑**。**EC-01…EC-05 全 `PENDING`**；五 EC 的判据与验证命令已按实测事实重写（**不照抄 prompt 起点**）。**CI 台账（逐提交）**：`ff6e0c4` 自带两 run —— M0 `37203151559` **八 job 全绿** + Push-on-main `37203151156` **CodeQL 3/3 全绿**，均 `run_attempt=1`（该 SHA 下 `total_count=2`，无 `cancelled`）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
