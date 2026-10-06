---
id: GOAL-20261006-031
slug: capability-release-and-the-research-loop
title: 放行面扩容 + citation.validate 接通 + 科研真成环 —— 从「接上了」到「放得开、想得深」
status: ACTIVE
created_at: 2026-10-06
updated_at: 2026-10-06
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-06 用户会话指令（goal 模式）：**建档 GOAL-031（放行面扩容 + citation.validate
    接通 + 科研真成环）并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点：
    (0) **授权变更（本 GOAL 的治理前提）**：用户 2026-10-06 **明确下放全部权限给驱动，
    用户只保留总目标** ⇒ 此前以「需用户拍板」登记的项**全部由驱动决定**（见「决策登记」节
    16 项：五项授权开工 / 十一项决定不做 + 全局禁令三条）。**区分写死**：「所有权限下放」
    = **可以决定**（含有界放宽某条 `allow`），**不等于**可以放宽**判据、门禁、阈值或断言**
    —— 本轮唯一「放宽」= 6 条只读能力的 `allow` + 授权 2 范围内的一处 pin 夹具最小追加；
    **判据/门禁/阈值/断言的强度一律不得动**（记录内逐条自证）。
    (1) **五项授权开工**：(i) **放行面扩容** —— 把 6 条已承接未放行的**只读**能力加入
    `examples/config/policy.yaml` 的 `allow`（`run.read` / `claim.read` / `deliverable.read` /
    `budget.read` / `experiment.read` / `experiment_plan.read`），scope 对齐既有读能力
    （`project`）；`default_effect` / `deny` / `require_approval` / `allow_with_constraints`
    一律不动；镜像表（`policy_check.py::_CAPABILITY_SCOPE`）同轮同步；
    (ii) **`citation.validate` 全链接通** —— 取数复用既有 `_elink`，判定规则显式三态，
    承接面登记 + 放行 + pin 夹具最小追加；(iii) **`G24-4` 读面字段语义修正** ——
    `LineageNodeDto.label` 实测承载 claim 正文 ⇒ 改名使其与内容一致，DTO + OpenAPI 快照 +
    `apps/web` 类型 + e2e 夹具同轮同步；(iv) **`.zcodeignore` 加入 `.gitignore`**（一行）；
    (v) **pin 夹具最小追加授权**（fix_policy 修订：`tests/contracts/**` 的 pin 仅允许
    **追加条目、断言一字不改、`git diff --numstat` 删除行为 0**）。
    (2) **十一项决定不做**（驱动已决定，非待拍板，逐条见「决策登记」节）：默认 runtime 改真
    （AGENTS.md §11）/ 读面认证 / 多租户 · RBAC · BOLA·BFLA（M18 deferred）/ D 组审批通道
    （审批未接通）/ `G24-5` 运行时拦截器 / 部署面验证（标签保持「未验证」）/ `R26-2` /
    `R26-3` / `R26-4` / `R26-6`（条件不满足，逐条写明）/ 把 destructive 能力从
    `require_approval` 改 allow。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**（含 skip /
    降强度）；**宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
    口径只能是 at-least-once + idempotency + deduplication）。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）；
    默认姿态不变（默认 runtime 保持 **Fake**、默认 CI **离线**）。
    (5) **边界（承继）**：GOAL-001…030 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…030 的未覆盖范围**原样保留**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 GOAL-029/030 建成的「承接面」（18/46 声明 + 实现 + 出厂绑定）从「**接上了**」推进到
    「**放得开、想得深**」：① **放行面扩容**——6 条已承接未放行的**只读**能力逐条放行
    （scope 对齐既有读能力、镜像表同轮同步、deny 面逐条零改动、新增判据断言「新增放行项
    全部只读」+「deny 面字节不变」+「default_effect 仍为 DENY」，两向反证 + 默认装配实跑里
    至少 3 条**真的被用**、有调用证据与下游消费证据）（EC-01）→ ② **`citation.validate`
    全链**——取数复用既有 `_elink`（**不得**新造第二套取数）、判定规则**显式三态**
    （成立 / 不成立 / 无法判定，不得二值化含糊）、承接面登记 + 放行 + pin 夹具最小追加
    （`numstat` 删除行 0 自证），两向反证（不被支持 ⇒ 不成立并点名；来源缺失 ⇒ 无法判定，
    不得当成成立）（EC-02）→ ③ **科研真成环**（本轮主干）——一次 run 含**两轮**研究，
    第二轮的问题由第一轮结果的**具名字段声明式派生**（经既有 `arguments_from_input` /
    `ids_from_previous` 形态或等价的声明式映射；**不得**代码硬编码「如果就」）；两条臂都实测
    且**判据能区分**（触发 ⇒ 真跑第二轮且输入逐条可追到第一轮产出；不触发 ⇒ 第二轮被跳过或
    转确认）；迭代留痕落 canonical（artifact / evidence / claim，走既有路径）且第二轮能经
    **读面**读到第一轮结论；两向反证（派生规则改坏 ⇒ 判红；摘掉第二轮读面证据 ⇒ 第二轮判负）
    （EC-03）→ ④ **读面字段语义修正**——`LineageNodeDto.label` 改名使其与承载内容一致，
    旧名全仓零命中（逐字节扫描）+ 快照判据绿 + 反证 + **兼容性实测**（不得为改名破坏兼容）
    （EC-04）→ ⑤ **自举收口**——验证器进树 + 两树复检 + 判词归档进树 + as-is m0 23/23
    （在全部记录写入之后）+ 治理绿 + CI 台账逐提交（EC-05）。
    **硬约束**：缺实现 / 未放行 / 缺 pin / 映射缺失一律**点名失败**（不得静默降级）；
    受判面**不得**是交集 / 过滤（承 `MEM-20260922-160` 与 GOAL-029 EC-02 的实测教训）；
    **真被使用才算数**（调用证据 + 下游消费证据，不得只断言「注册了」/「返回成功」）；
    留档**二进制写盘**、判词归档**进树**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **放行面扩容（授权 1）**。
      (a) 6 条只读能力（`run.read` / `claim.read` / `deliverable.read` / `budget.read` /
      `experiment.read` / `experiment_plan.read`）加入 `policy.yaml` 的 `allow`，scope =
      `project`（与 `workspace.read` / `artifact.read` / `evidence.read` 同形）；
      (b) 镜像表（`packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE`）同轮
      同步；既有镜像一致性判据（`tests/application/test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml`）
      **必须绿且不得改该判据**；
      (c) **New judge**（新增判据，不得改既有断言）：① 本轮新增放行项**逐条断言是只读能力**
      （绑**能力名清单**——来自结构化字段而非散文；受判面 = 6 条**声明集**本身，不得写成
      交集）；② `deny` 面与 `require_approval` 面**逐条零改动**（与**建档基线**字节比较：
      基线片段 `sha256` 写进判据）；③ `default_effect` 仍为 `DENY`；
      (d) **反证两向**：① 把一条放行删掉 ⇒ 该能力在 run 里**被拒且点名**（`POLICY_DENIED`
      判词逐字，不是静默跳过）；② 把一条**非只读**能力塞进放行清单 ⇒ (c)① 判据判红；
      (e) **实跑**：默认装配下 run 里**真的用到**至少 3 条本轮新放行能力（**调用证据**
      ——工具证据的 `tool_refs` 逐条点名 provider/tool）+ **下游消费证据**（下游 phase 的
      返回内容含上游工具证据 id），跑到 `SUCCEEDED`。
      **同轮同步集（建档实测，逐条登记）**：本 EC 的授权状态变化会移动若干**既有判据的
      钉定值**（实测 6 条判据转红，见「事实层结论」第 2 条）——同步方式**只允许**：
      输入登记面（`POLICY_SURFACE_AUDIT.md` 差集表行/计数）更新 + 既有钉定值**保持断言形态与
      强度不变的重新定基**（`EXPECTED_REGISTERED` 15→9；`_REGISTERED_NOT_GRANTED`
      `claim.read`→仍未被放行的 `citation.inspect`；`test_run_read_onboarding` 的「未放行」
      断言按新状态翻转为「已放行」并在记录内**逐条自证强度未降**）。**任何**断言形态/强度
      变化、任何 skip/删除 ⇒ 命中全局禁令 ⇒ **BLOCKED**。
      **判据**：放行 + 镜像同步 + 三条判据（只读/deny 零改动/default_effect）+ 两向反证 +
      实跑使用证据 + 同步集自证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight
      tests/application/test_m2_audit.py tests/adapters/canonical/test_run_read_onboarding.py
      tests/adapters/openhands/test_session_tool_reaches_executor.py
      tests/e2e/test_granted_read_capabilities_used_in_a_run.py -q` ⇒ 全绿；
      新增判据文件（只读面/deny 零改动/default_effect）全绿；配套留档：
      6 条放行项的（能力名, scope）逐条清单、deny 面基线片段 `sha256` 前后对比、
      `EXPECTED_REGISTERED` 等钉定值的 before/after 逐字节对照与「强度未降」自证、
      两向反证判红原文（点名串逐字）、实跑使用证据（≥3 条，调用 + 下游消费）。
    status: PASS
    evidence: >-
      cycle 1（PLAN-20261006-293 / `RECHECK-20261006-293` = PASS_WITH_WARNINGS）。
      判词归档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-{release-ledger,
      refutation-verdicts,run-usage-evidence}.txt`。**实测**：(a) 6 条放行逐条 scope=project；
      (b) 镜像表同轮同步、`test_m2_audit` 镜像判据未改且绿；(c) 三条新判据在场（
      `test_release_expansion_is_read_only.py` 16 条）；deny 面基线 `bf04fa4e…` 前后**逐字节相等**；
      `default_effect` 仍 `DENY`；(d) 两向反证判词原文：`workspace.delete: 末段不是只读后缀` / 删
      `budget.read` 后 `DENY: used default policy effect` + preflight `[POLICY_DENIED] phase:probe:
      policy denied capability budget.read: …`（run 面 `preflight failed: POLICY_DENIED`）；
      (e) 实跑 `SUCCEEDED`：`run.read` / `budget.read` / `claim.read` 三条被调用、probe 的 2 条工具
      证据被 `claim.read` 与 `evidence.read` 各消费一次。EC-01 verify ⇒ 93 passed；定向回归
      `tests/application+adapters+architecture+loaders` ⇒ 1607 passed / 4 skipped。
      残余：`W31-1`（未放行的 3 条未被一次 run 使用）/ `W-2`（run 级消息只带代号，逐能力点名在
      preflight 面）。
  - id: EC-02
    criterion: >-
      **`citation.validate` 全链（授权 2）**。
      (a) **判定规则显式**（常量 + 语义文档 + 判据）：三态 —— **成立**（来源解析出 linkset
      且 ≥1 条 PMC 链接）/ **不成立**（解析出 linkset 但零链接 ⇒ 引用不被来源支持）/
      **无法判定**（无 linkset / 来源缺失 ⇒ 不得当成「成立」）；
      (b) **取数复用既有 `_elink`**（`adapters/research_tools/ncbi.py::NcbiEutilsProvider._elink`
      → `parsing.normalize_elink`；**不得**新造第二套取数）；
      (c) **承接面登记 + 放行**：实现（真工具）+ 出厂绑定 + 目录声明 + `policy.yaml` 放行
      （scope 与取数 provider 形态对齐）+ `POLICY_SURFACE_AUDIT.md` 登记面同步；
      (d) **pin 夹具最小追加**（授权 2 范围内）：受影响的 pin **只允许追加条目**，
      **断言一字不改**，`git diff --numstat` 对受影响的 pin 文件**删除行必须为 0**；
      断言内容与**建档基线**逐字节比较（只有列表变长）；
      (e) **反证两向**：① 造一条**不被来源支持**的引用 ⇒ 判**不成立**且**点名缺口**；
      ② 造一条**来源缺失**的引用 ⇒ 判**无法判定**（**不得**当成「成立」）。
      **判据**：三态规则 + 单取数面 + 承接与放行 + pin 零删除 + 两向反证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts
      tests/application/preflight tests/architecture/python/test_capability_coverage_is_implemented.py
      -q` ⇒ 全绿；新增判据（三态 + 反证两向）绿；配套留档：三态规则常量与语义文档、
      两向反证判词逐字、`git diff --numstat` 对受影响 pin 文件的读数（删除行 0）、
      建档基线 `sha256` 与同步后逐字节对照。
    status: PASS
    evidence: >-
      cycle 2（PLAN-20261006-295 / `RECHECK-20261006-295` = PASS_WITH_WARNINGS）。
      判词归档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec02-release-and-pin-ledger.txt`。
      **实测**：(a) 三态常量 `CITATION_VERDICTS = (SUPPORTED, UNSUPPORTED, UNDETERMINED)`
      在 `parsing.py`；三输入 ⇒ 三判词**两两不等**（二值实现必红，判据 12 passed）；
      (b) 取数面**唯一**：`'elink.fcgi'` 在 `adapters/research_tools/ncbi.py` 出现 **1** 次
      （结构臂）+ 两条能力读到同一 `pmc_links`、各恰好一次请求（行为臂）；
      (c) 放行 `ALLOW` / `matched allow rule`，scope = `approved_tool_providers`（与同取数
      provider 既有放行同栏）；承接 = 目录声明 + 出厂绑定 + toolpack pin + AUDIT 登记面；
      (d) pin 判据文件删除行 **0**（`test_europe_pmc_pin_and_registration` /
      `test_mcp_registration_and_refutations` 逐字节纯追加）；`run_fixtures._PROVIDERS`
      **-1 行**（单行 tuple 形态所致，如实登记为 `W-EC02-1`）；
      (e) 两向反证：`UNSUPPORTED`（linkset 在场零链接，判词含 `zero PMC links`）/
      `UNDETERMINED`（无 linkset，判词含 `no linkset`），两者**不等**。
      合跑：受判面 **586 passed / 69 skipped**；扩展 **1157 passed / 72 skipped**；
      会话注册面 **18 passed**。
      残余：`W-EC02-1`（夹具 1 行重写）/ `W-EC02-2`（两层新增，词表 46 条未变）/
      `W-EC02-3`（判定只在离线 mock 上实测，真实 linkset 形态分布未采样）。
  - id: EC-03
    criterion: >-
      **科研真成环（本轮主干，两轮子迭代）**。一次 run 含**两轮**研究，第二轮的问题由第一轮
      结果派生（不是操作者手写）：
      (a) **派生是声明的**：第二轮的输入来自第一轮结果的**具名字段**（经既有
      `arguments_from_input` / `ids_from_previous` 形态，或等价的**声明式映射**）；
      **不得**在代码里硬编码「如果就」的业务判断（操作系统承接声明，不承接业务）；
      (b) **两条臂都实测**：① 第一轮结果**触发**第二轮（真跑第二轮，且第二轮输入逐条可追到
      第一轮的具体产出）；② 第一轮结果**不触发**（第二轮被跳过或转确认，**点名**不触发原因）；
      且**判据能区分这两条臂**（不能「两条臂都过」同一判据）；
      (c) **迭代留痕**：每轮结论落 canonical（artifact / evidence / claim，走**既有**路径，
      不新造第二套漏斗），且**第二轮能读到第一轮的结论**（**读面**证据，不是内存传递）；
      (d) **反证两向**：① 把派生规则改坏（第二轮输入与第一轮结果脱钩）⇒ 判红；
      ② 把第二轮的读面证据摘掉 ⇒ 第二轮**判负**（承 GOAL-027「评审真能判不通过」形态）。
      **判据**：声明式派生 + 两臂可区分 + canonical 留痕 + 读面可读 + 两向反证 + 实跑终态。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_research_loop_second_round_derived.py
      -q` ⇒ 全绿（含两条臂各自的用例与两向反证）；配套留档：派生声明（协议 YAML 片段 +
      编译产物）、两轮调用/消费证据（工具证据 + claim relation + 读面读数）、
      不触发臂的点名判词、两向反证判红原文。
    status: PASS
    evidence: >-
      cycle 3（PLAN-20261006-297 / `RECHECK-20261006-297` = PASS_WITH_WARNINGS）。
      判词归档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt`
      （由 `scratch/goal031-cycle3/gen_ec03_evidence.py` **实跑**生成，二进制写盘）。
      **实测**：(a) 派生声明在协议（两个 run-chain phase）与装配（`artifact_from_previous`
      = `literature_search` / `ids_from_previous` = `content.ids` / `requires_previous_ids`
      = False）两处逐字在场；触发判定模块 AST 无领域能力名；
      (b)① 触发臂 `SUCCEEDED`，第二轮读取步 operation key **逐字**含第一轮返回的 PMID
      （`literature_read:39000001+39000002`），`artifact.read` 返回内容
      `content.ids == ['39000001','39000002']`（与第一轮检索结果逐字相等）；
      (b)② 不触发臂（同协议同装配、检索零命中）`SUCCEEDED` 且 `run.completed.skipped`
      逐字点名工具/字段/触发形态，读取步零请求零证据；**两臂在同一读数上互斥**
      （证据在场 / 不在场；`skipped` 空 / 非空）；
      (d) 反证① `state=FAILED` 判词含 `carries no 'content.no_such_field'`；反证②
      `state=FAILED` 判词含 `expected exactly one evidence artifact_id ending with
      'no_such_artifact', found []`。
      判据 **13 passed**；定向回归（application+adapters+architecture+loaders+contracts）
      **2125 passed / 73 skipped**；`tests/tooling` **1323 passed**（含规模门与口径判据，
      `phase_runner` 449→402 / `read_provider` 452→411 / `phase_capabilities` 461→441）。
      残余：`W-EC03-1`（判据初版构造缺陷，自己修）/ `W-EC03-2`（相位过滤新机制只被本协议
      证明）/ `W31-4` 延续。
  - id: EC-04
    criterion: >-
      **读面字段语义修正（授权 3，`G24-4`）**。`LineageNodeDto.label` 实测承载 claim 正文
      （`statement`）/ 标识文本 ⇒ **改名使其与内容一致**（新名以实际承载语义为准，常量写死在
      判据里）：
      (a) **同轮同步**：DTO（`services/api/dto/inspection.py`）+ OpenAPI 快照
      （`docs/api/openapi.m13.json`，经 `tools/gen_openapi.py` 再生成）+ `apps/web` 类型
      （`apps/web/src/api/types.ts`；`ProjectLineageNodeDto` 同形字段一并处理）+ e2e 夹具；
      (b) **判据**：旧名**全仓零命中**（**逐字节**扫描 `services/` / `apps/web/` / `tests/` /
      `docs/api/`，不靠人工目检）；既有快照判据（`tests/contracts/test_openapi_snapshot.py`）
      绿；
      (c) **反证**：把旧名放回一处 ⇒ 判红并点名文件；
      (d) **残余**：若改名破坏对外兼容（有既有消费者依赖旧名）⇒ **如实登记** + 双写/弃用
      方案，**不得**为改名破坏兼容 —— **这一条要实测**（全仓消费者普查：`rg` 逐文件），
      不许推定。
      **判据**：改名 + 四处同步 + 旧名零命中 + 快照绿 + 反证 + 兼容性实测结论。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_lineage_label_rename_is_complete.py
      tests/contracts/test_openapi_snapshot.py tests/api/test_reports_integrations_lineage_api.py
      tests/api/test_project_lineage_api.py -q` ⇒ 全绿；`cd apps/web && npx tsc -b` 绿；
      配套留档：消费者普查读数（逐文件）、旧名零命中扫描命令与读数、反证判红原文。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**：① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      与 `tools/closeout_recheck_assertions.standard_verdicts`，只写本轮特有断言）并加入
      `IN_SCOPE`（**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py --script-mode shared`）
      + **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**，CR=0）；③ as-is m0
      **23/23**，在**全部记录写入之后**（独占、仓库 `.venv`、`uv run --frozen --no-sync python -B`、
      不接管道）；④ 治理 `validate.py` 绿；⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 +
      `covered_by`；空集合 = 未取证；自我指涉边界**明写并封闭**，不得循环）；
      ⑥ 承继残余逐条在位 + 本轮「决策登记」节（16 项逐条状态）；⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python tools/verify_goal031_closeout.py --root . --verdict-only`
      ⇒ 全 FAIL 为 0（判词归档进树）；`tools/two_tree_recheck.py --script-mode shared` ⇒
      `TWO-TREE PASS`（两树判词逐行相同、`sha256` 相同、归档进树）；as-is m0 ⇒
      `PASS: profile=m0; 23 deterministic checks`（在全部记录写入之后）；
      `uv run --frozen --no-sync python .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 绿；CI 台账逐提交（每条含 run 结论）。收口复检
      `RECHECK-*-031-*-closeout-recheck` = PASS/PASS_WITH_WARNINGS，`verify_paths` ≥ 2 路。
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
      （承 `MEM-20260922-160`：`declared ∩ implemented` 使「声明了但没实现」在构造上不可能
      被报出）；**只断言「注册了 / 返回成功」而不取调用与下游消费证据**
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据
      （`test_reproducibility_wording.py` / `test_delivery_semantics_wording.py` /
      `test_record_face_is_covered_by_the_gate.py`）、两树入口判据、规模门禁、
      `tests/application/preflight/**`、`tests/application/test_m2_audit.py`、
      `tests/adapters/**`、`tests/e2e/**` 既有文件）—— **新增**判据与新增文件不受此限
    - >-
      **修订一条（相对 GOAL-030 的例外）**：原「不得修改 `tests/contracts/**`」改为
      「**仅授权 2（`citation.validate`）范围内的 pin 夹具最小追加**：只允许追加条目、
      **断言一字不改、`git diff --numstat` 删除行为 0**」；**其余既有判据仍禁改**。
    - >-
      **本 GOAL 特有的同轮同步例外（逐条点名，授权 1 的必然结果，建档实测 6 条判据转红）**：
      仅限 ① `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表行与计数（**输入登记面**，
      判据本体不动）；② `tests/application/preflight/test_read_grant_is_per_item.py` 的
      `EXPECTED_REGISTERED`（15 → 9，**断言形态与强度不变**）；③
      `tests/adapters/openhands/test_session_tool_reaches_executor.py` 的
      `_REGISTERED_NOT_GRANTED`（`claim.read` → 仍未被放行的 `citation.inspect`，
      **断言一字不改**）；④ `tests/adapters/canonical/test_run_read_onboarding.py` 的
      「已承接未放行」断言按新状态翻转（在同一文件内保留「承接 ⇒ 有实现 + 有绑定」与
      「放行 ⇒ ALLOW」两侧断言，**强度不降**）；⑤
      `tests/architecture/python/test_capability_coverage_is_implemented.py` 的**分类/登记表**
      与 `_MIN_NEWLY_承接` 下界（**只上调、不得下调**；仅在承接确实落地时同步）。
      **上述以外的任何既有判据改动 ⇒ BLOCKED**；每条同步都要在记录内给出 before/after
      逐字节对照与「强度未降」自证。
    - >-
      改 `default_effect: DENY` / 放宽 §9 默认 deny（**新增只读 allow 不算**）/ **新增类别级
      allow**；或改 `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` 与
      `policy.yaml` 的镜像并集**使两者不等**（两张表由既有测试锁死并集相等）
    - >-
      **把非只读能力加入放行**；**把 destructive 能力从 `require_approval` 改 allow**；
      **允许未放行能力静默跳过**（缺实现 / 未放行 / 缺 pin / 映射缺失必须**点名**）
    - >-
      **未经 pin 的 provider**；**把真实凭据写进任何地方**；**放开默认网络**（默认门必须仍
      离线）；**触达 D 组**（`external.publish` / `package.install` / `git.commit` /
      `workspace.delete`）；**宣称项目安全**（`R-M1`）；**宣称投递语义为「恰好一次」**
escalation_triggers:
  - 需要修改 `default_effect: DENY` / 放宽 §9 默认 deny（新增只读 allow 不算）
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖 / 上游版本 pin 变更
  - 真实凭据进树 / 未 pin 接上游 / 触达 D 组（审批通道未接通）
  - 把非只读能力加入放行
  - 需要改（同步集以外的）任何既有判据的断言
  - 宣称项目安全 / 宣称投递语义为「恰好一次」
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261006-293-goal-031-ec01-read-capability-release.md
  - .cursor/plans/tasks/PLAN-20261006-295-goal-031-ec02-citation-validate-full-chain.md
  - .cursor/plans/tasks/PLAN-20261006-297-goal-031-ec03-two-round-derived-research-loop.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261006-031 — 放行面扩容 + citation.validate 接通 + 科研真成环

本文件是 GOAL 层编排记录（`GOAL-*` 之上对齐 `PLAN-*` / `RECHECK-*` / `MEM-*` 体系；
单一流程权威见 `.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账；
工程事实、验收与复检仍由 PLAN/RECHECK 承载。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 放行面扩容（授权 1） | 6 条只读能力放行 + 镜像同步 + 三条新判据 + 两向反证 + 实跑使用 ≥3 条 | PENDING |
| EC-02 | `citation.validate` 全链（授权 2） | 三态规则 + 单取数面 + 承接与放行 + pin 零删除 + 两向反证 | PENDING |
| EC-03 | 科研真成环（主干） | 声明式派生 + 两臂可区分 + canonical 留痕 + 读面可读 + 两向反证 + 实跑终态 | PENDING |
| EC-04 | 读面字段语义修正（授权 3） | 改名 + 四处同步 + 旧名零命中 + 快照绿 + 反证 + 兼容性实测 | PENDING |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**宣称项目安全**
（`R-M1`）；不得宣称投递语义为「恰好一次」（口径只能是 at-least-once + idempotency +
deduplication）。观测隐私按 AGENTS.md §10；默认 runtime 保持 Fake、默认 CI 离线（§11）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。勘察在**隔离 worktree**
> （`git worktree add --detach D:/rs-goal031-probe HEAD`，跑完移除）上做按压，未动主树。
> 凡与起点表述不符者，**以实测为准**。

### 1. 6 条读能力的「放行后果」与调用面（授权 1 的射程）

复核命令：

```bash
rg -n "_TOOL_CAPABILITIES|_TOOL_DESCRIPTIONS" adapters/canonical/read_surface.py
rg -n "DEFAULT_SESSION_TOOL_BINDINGS" -A 20 services/api/session_tool_support.py
rg -n "run_chain_tool_ids|CapabilityDeps|execute_run_chain_capabilities" \
  packages/application/run_orchestration/*.py | head
```

读数（逐条）：

| 能力 | 实现面 | 出厂绑定 | 放行后**谁能调用** | 今天的使用面 |
| --- | --- | --- | --- | --- |
| `run.read` | `adapters/canonical/run_read.py`（读 `RunStore.get_run`） | `("run.read","m12_artifact","run_read")` | ① 预检策略（`ToolRequirement` 逐 phase）② 运行链步（`execute_run_chain_capabilities`）③ 会话工具桥（绑定的 invoker） | 协议声明 0 |
| `claim.read` | `read_provider.py::_claim_read` | 有 | 同上 | 协议声明 0 |
| `deliverable.read` | `_deliverable_read` | 有 | 同上 | 协议声明 0 |
| `budget.read` | `_budget_read` | 有 | 同上 | 协议声明 0 |
| `experiment.read` | `_experiment_read` | 有 | 同上 | 协议声明 0 |
| `experiment_plan.read` | `_experiment_plan_read` | 有 | 同上 | 协议声明 0 |

三个调用点的**语义差别**（写进判据设计，不混为一谈）：
- **预检/执行策略**：`check_policy` 对 `plan.tool_requirements` 逐条求值
  （`_policy_scope(capability)` 补 scope；缺 scope 会落 `default_effect` ⇒ 同一能力两处结论，
  这正是 GOAL-011 EC-01 的既有教训）；
- **运行链**：声明 `capability_execution: run_chain` 的 phase 由
  `execute_run_chain_capabilities` **确定性执行**装配方声明的 `RunChainCall`
  （筛法是 **provider 级**：`call.provider_id in spec.run_chain_tool_ids`；能力仍逐条进
  `tool_requirements`）；
- **会话工具桥**：`session_tool_invokers` 按出厂绑定造「工具名 → 调用」表，**缺一即不进表**
  （不静默顶替）。

放行**不改变**以上任何调用点结构——它只把策略求值从 `DENY（used default policy effect）`
变成 `ALLOW（matched allow rule）`。**「放行 ≠ 被用」**：使用面要靠协议声明 + 装配声明
（EC-01(e) 的实跑证据正是这条区分）。

### 2. ⚠️ 决定性发现：放行 6 条能力会移动 **6 条既有判据的钉定值**（实测）

复核命令（隔离 worktree，逐字复现）：

```bash
git worktree add --detach D:/rs-goal031-probe HEAD   # 主树零改动
# 在 probe 树上：policy.yaml +6 allow（scope=project）+ 镜像表 +6（“唯一授权放宽”）
cd /d/rs-goal031-probe && git diff --numstat      # 12↑ policy.yaml + 6↑ mirror，删除 0
PYTHONPATH=. <repo>/.venv/Scripts/python.exe -B -m pytest tests/application tests/adapters \
  tests/architecture tests/api tests/contracts tests/loaders -q
```

读数：**6 failed / 4428 passed**（`tests/e2e` / `tests/integration` / `tests/observability` /
`tests/mcp_server` 另跑：`345 passed`，**零红**）。六条判红逐条点名：

| # | 判据 | 钉的是什么 | 形态 |
| --- | --- | --- | --- |
| 1 | `test_policy_surface_difference_set.py::test_the_difference_set_and_the_table_are_two_way_complete` | 差集表 == 机制算出的差集（表有而差集无 ⇒ 红） | **输入登记面**（文档行），判据本体可不动 |
| 2 | `…::test_each_row_state_matches_the_mechanical_rule` | 每行终态 == 机制状态（`该登记` vs `不在差集内`） | 同上 |
| 3 | `test_read_grant_is_per_item.py::test_registered_read_capabilities_are_not_granted_as_a_class` | 差集表「该登记」**恰 15 条**且**一条都没被放行** | **既有钉定值**（常量 15） |
| 4 | `test_run_read_onboarding.py::…::test_the_catalog_declares_it_but_the_policy_does_not_allow_it` | `run.read` 已承接 ⇒ 真实求值器判 **DENY** + `used default policy effect` | **既有钉定值**（状态断言） |
| 5 | `test_session_tool_reaches_executor.py::…::test_a_registered_but_ungranted_capability_is_refused` | `_REGISTERED_NOT_GRANTED = "claim.read"` 未放行 ⇒ executor 不得被触达 | **既有钉定值**（示例能力名） |
| 6 | `…::test_the_declared_scope_table_is_the_only_source` | 同上常量的策略归属（`_GRANTED`/`_REGISTERED_NOT_GRANTED`/`_REQUIRES_APPROVAL` 三态真实归属） | 同上 |

**同步集实测**（probe 上把同步动作全部落地后复跑）：
`3 判据同步 + 1 文档同步 + 2 产品文件 = 60 passed / 0 failed`（含
`tests/application/test_m2_audit.py` 的镜像一致性判据**逐字节未改**而绿）。同步动作与
「强度未降」自证要求已写进 EC-01 与 fix_policy 的点名例外；**集合之外**的任何既有判据
改动 ⇒ BLOCKED。

### 3. `citation.validate` 会打红哪几条 pin 判据（逐条点名，授权 2 的前提）

复核命令（probe 树上分别试两条路线，记录判词）：

```bash
# 路线 A：扩既有 provider（ncbi_eutils.capabilities + citation_validate 工具）
# 路线 F：新增 provider（ncbi_citation，只声明 citation.validate）
cd /d/rs-goal031-probe && PYTHONPATH=. <repo>/.venv/Scripts/python.exe -B -m pytest tests/contracts \
  tests/loaders tests/architecture/python/test_capability_coverage_is_implemented.py -q
```

读数（**路线 A** 判红 5 条，**路线 F** 判红 1 + 2 条，逐条点名）：

| 判据 | 钉的是什么 | 路线 A | 路线 F |
| --- | --- | --- | --- |
| `tests/contracts/test_ncbi_provider_contract.py::…::test_list_tools_schema` | ncbi 工具名集合**恰为** `{literature_search, literature_read, citation_inspect}` | 红 | 绿（该 provider 工具面不变） |
| `tests/contracts/test_europe_pmc_pin_and_registration.py::…::test_existing_providers_are_untouched` | 目录 provider 集合**恰为** 4 条 + ncbi 能力列表逐字 | 红 | 红（**多行 set 字面量 ⇒ 纯追加可行**） |
| `…::test_every_non_native_provider_is_pinned_in_the_fixture_source` | 目录非 NATIVE provider ⊆ 夹具 pin 源 `_PROVIDERS` | 绿 | 红（`_PROVIDERS` 单行 tuple） |
| `tests/contracts/test_mcp_registration_and_refutations.py::…::test_the_fixture_pin_source_covers_the_demo_catalog_providers` | 同上（第二份下界断言） | 绿 | 红 |
| `tests/loaders/test_contract_loaders.py::…::test_load_budget_policy_and_resource_contracts` | ncbi 能力列表逐字 | 红 | 绿 |
| `tests/architecture/python/test_capability_coverage_is_implemented.py::…::test_every_declared_capability_has_an_implementation` | 声明 ⇒ 实现 + 出厂绑定（登记表允许「实现由既有 adapter 承担」） | 红 | 红（登记表同步，属点名例外⑤） |

**⇒ 路线决定（驱动决定，登记在「决策登记」②）**：取**路线 F（新增 provider `ncbi_citation`，
只声明 `citation.validate`）**：它把既有 ncbi 工具面逐字保持；受影响的 pin 中
`test_existing_providers_are_untouched` 的 set 字面量是**多行** ⇒ **纯追加一行**（删除 0）；
`_PROVIDERS` 为单行 tuple ⇒ 需要授权 2 范围内的最小追加（**该文件与两条断言在记录内逐条
登记，并在收口时用 `numstat` 出示删除行读数**）。三态规则、`_elink` 复用与反证设计见 EC-02。

### 4. EC-03 的既有机械面（声明式链式传参；缺「触发/跳过」声明面）

复核命令：

```bash
sed -n '60,145p' packages/application/run_orchestration/phase_capabilities.py   # RunChainCall 四类取值
sed -n '140,200p' packages/application/run_orchestration/phase_capabilities.py  # 逐步执行序列
rg -n "stop_conditions|max_iterations" packages/domain/protocols.py packages/application/protocol_compile/compiler.py
```

读数：
- **既有声明式取值四类**（全部 fail-closed，不猜）：`arguments_from_input`（点分路径读**声明
  输入制品**字段）/ `fixed_arguments`（量）/ `ids_from_previous`（**上一步结果的具名字段**，
  支持点分路径）/ `run_id_argument`（执行期才存在的 run id）。**链式传参已存在**：
  `execute_run_chain_capabilities` 在一个 task 内按声明顺序逐步执行，`previous` 逐步前递。
- **缺口（实测）**：链式当前只有「有 ids ⇒ 执行 / 无 ids ⇒ **抛错**」两种走向
  （判词 `previous step carries no 'ids' ids for run-chain tool …`）——**没有**声明式的
  「**不触发 ⇒ 跳过或转确认**」面。EC-03(b) 的第二条臂要求「被跳过或转确认」且**点名**，
  因此需要在既有编译器/运行链上加一个**声明式**（非硬编码「如果就」）的触发条件字段；
  这是 EC-03 的实现内容，**不改既有四类取值语义**（缺省行为逐字节不变）。
- **跨 phase 的 output→input 自动连线不存在**：`CompiledPhase.inputs` 是**声明**的输入制品
  id（操作者/协议给），phase 间靠 `HandoffBundle` 传结构化结果。EC-03 的「第二轮读到第一轮
  结论」因此**必须**经 canonical（artifact/evidence/claim）+ 读面能力（本轮 EC-01 放行的
  读能力正是它的抓手），而不是内存传递。

### 5. EC-04 的消费者普查（兼容性实测的前置读数）

复核命令：`rg -n "LineageNodeDto|label" services/api/dto/inspection.py
services/api/lineage_projection.py services/api/project_lineage.py apps/web/src/api/types.ts
apps/web/src/features/lineage -g '*.ts' -g '*.tsx'`

读数（逐条）：
- 语义：`label` 节点值 = claim 的 `statement`（正文）/ evidence 的 `source_ref` / artifact id /
  model ref ⇒ 与「label（标签）」的直觉不一致（`G24-4` 的原始登记：**实测承载 claim 正文**）；
- 消费者：`services/api/lineage_projection.py`（构造）、`dto/inspection.py`（DTO）、
  `apps/web/src/api/types.ts`（两类 DTO：`LineageNodeDto` / `ProjectLineageNodeDto`）、
  `apps/web/src/features/lineage/{lineageColumns,projectLineageColumns}.tsx`（列定义）、
  `docs/api/openapi.m13.json`（快照，`tools/gen_openapi.py` 再生成）；
- **兼容性实测**（收口时出示读数）：仓内消费者全部自有（web + tests + 快照）；
  **无外部契约承诺面**（本仓不对外发布该 DTO）。⇒ 改名可行；若有发现外部消费者 ⇒ 按 EC-04(d)
  如实登记 + 双写/弃用方案，**不得**为改名破坏兼容。

### 6. 记录面与门（本轮受判面）

- `.cursor/plans` 在 `test_reproducibility_wording.py` 的扫描面内 ⇒ 本记录**不得**出现
  肯定式「完全可复现 / fully reproducible」（引用或否定式放行）；
- `.cursor/plans/goals/**` 是 `test_delivery_semantics_wording.py` 的**规则文本面**：
  **凡引用 exactly-once 的 GOAL 文件必须同时含禁令词**（禁止 / 不得 / 否认 / 不做 /
  BLOCKED / 口径）——本文件**已含**这六个词；
- 健康顺序（GOAL-019 的教训）：**先写记录 → 记录面判据 → 全量门**；m0 必须**独占**且在
  记录写入**之后**跑；m0 计数口径 = 终局行 `PASS: profile=m0; 23 deterministic checks`
  （`PASS [` 行数 24 含计数外的一条，承 `MEM: m0 profile roots & count`）；
- **一个 cycle 一次推送**（避免 `cancel-in-progress` 取消在飞 M0，承 GOAL-030 的流程自省）。

### 7. 建档基线的 `sha256`（deny 零改动与 pin 零删除的比对基准）

读数（`sha256sum`，建档当日）：

| 文件 | 基线 `sha256` | 用途 |
| --- | --- | --- |
| `examples/config/policy.yaml` | `e00bdcb3161e17ea485cef2cfe56e772608bcba94b39fbd74f411c5135f22489` | allow 追加前后对照 |
| `packages/application/preflight/policy_check.py` | `cdfa15f393eeb0ca890581c66ce9f764ee058068b6155fcb346402a339e735cb` | 镜像同步前后对照 |
| `examples/config/tool_providers.yaml` | `30bfcbe5d5b66740db38f0d6c312e837f4b4fb3837606e23d0730213c26dc8d3` | EC-02 声明面追加 |
| `adapters/research_tools/ncbi.py` | `f11fc5b2bf6a62d5dcde72ea5d238849d2caff297356a42ff3ae90f1c69afb83` | EC-02 `_elink` 复用基线 |
| `docs/architecture/POLICY_SURFACE_AUDIT.md` | `6518fd26a65dc143e0a13f4a954b46fa0fcd4a65d15d3b1e40883df5012367a1` | 登记面同步基线 |

`require_approval` + `deny` 两段的**基线片段 `sha256`**（自 `require_approval:` 起至文件末）：
`bf04fa4efdbbafb8449c4f0248f4e4dc6ed9daae1f3dc7125f20fc2d4ad537a4` —— EC-01(c)② 的
「逐条零改动」判据直接钉这个值（**新判据内写死**，不含散文判断）。

## 决策登记（16 项逐条状态）

> 触发依据：用户 2026-10-06「所有权限下放给驱动，用户只保留总目标」⇒ 此前登记为「需用户
> 拍板」的项**全部由驱动决定**。**全局禁令三条**（不列入 16 项计数，贯穿全 GOAL）：
> ① 不得**放宽任何既有判据的断言**（含 skip / 降强度）；② 不得**宣称项目安全**（`R-M1`）；
> ③ 不得宣称投递语义为「恰好一次」（**明确否认**）。

| # | 项 | 状态 | 理由 / 边界 |
| --- | --- | --- | --- |
| ① | **放行面扩容**（6 条只读能力） | **授权开工** | 只读、已有真实现与出厂绑定、零依赖零凭据；同时刻的必然同步集（4 条既有钉定值 + 2 个输入登记面）已在 fix_policy 点名，逐条自证强度未降 |
| ② | **`citation.validate` 全链** | **授权开工**（路线 F：新增 provider `ncbi_citation`） | 取数复用 `_elink`；路线 F 使既有 ncbi 工具面逐字不变，受影响 pin 的同步面最小（见事实层第 3 条） |
| ③ | **`G24-4` 读面字段改名** | **授权开工** | DTO + 快照 + web 类型 + 夹具同轮；兼容性**实测**后定夺双写/弃用 |
| ④ | **`.zcodeignore` 加入 `.gitignore`** | **授权开工** | 一行；客户端产物，非工程资产 |
| ⑤ | **pin 夹具最小追加**（授权 2 范围内） | **授权开工** | `tests/contracts/**` 仅限追加条目、断言一字不改、`numstat` 删除 0；**扩张解释即越界** |
| ⑥ | 默认 runtime 改真 | **决定不做** | AGENTS.md §11（真实 LLM 不得成为默认 CI 依赖）；默认装配保持 Fake |
| ⑦ | 读面认证 | **决定不做** | 读面认证是另一条谱系（GOAL-019/020/021 已把写面收口）；本轮单列范围外 |
| ⑧ | 多租户 · RBAC · BOLA·BFLA | **决定不做** | M18 deferred（既有登记）；无隔离模型时做授权只会造出「看起来安全」的假象 |
| ⑨ | D 组审批通道（`external.publish` / `package.install` / `git.commit` / `workspace.delete`） | **决定不做** | 审批通道未接通 ⇒ 触达即 BLOCKED；本轮不碰 D 组 |
| ⑩ | `G24-5` 运行时拦截器 | **决定不做** | 条款改为运行时产品行为超出本轮射程；原样登记 |
| ⑪ | 部署面验证 | **决定不做** | 标签保持「未验证」（无部署面可验；不推定） |
| ⑫ | `R26-2` 工具面断路器接通 | **决定不做** | 条件不满足：需产品级阈值来源与状态持久化决策（`tool_plane/health.py` 无产品调用方） |
| ⑬ | `R26-3` 在飞取消信号 | **决定不做** | 条件不满足：需 worker 协议与 fencing 语义变更 |
| ⑭ | `R26-4` 非幂等补偿 | **决定不做** | 条件不满足：需「哪些动作非幂等」的产品级声明面 |
| ⑮ | `R26-6` HTTP 幂等 store 跨副本 / check-then-act | **决定不做** | 条件不满足：改动 `IdempotencyMiddleware` 语义（既有禁改面） |
| ⑯ | 把 destructive 能力从 `require_approval` 改 allow | **决定不做** | AGENTS.md §9 默认 deny 的护栏；审批通道未接通 ⇒ 维持阻塞 |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按「迭代日志」最后一行 + 工作树/远端实况
判定续点（与 `goals/README.md` 同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①；建档（cycle 0）未完成 → 先补建档。
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
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261006-031` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 记录面判据 → 全量门**；m0 按组、**独占**、仓库 `.venv`、
  `uv run --frozen --no-sync python -B`、**不接管道**（避免缓冲吞输出）；受影响的定向套件
  （`tests/application/preflight` / `tests/contracts` / `tests/adapters` / `tests/e2e` /
  `tests/architecture`）；web 门（tsc / eslint / unit / build / stub+live e2e）按改动面。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run（脚本口径见「CI 台账」节）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤；
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **放宽只允许发生在 allow 面**：本轮唯一「放宽」= 6 条只读 allow + 授权 2 的 pin 追加；
  **判据/门禁/阈值/断言的强度一律不得动**，且每条同步在记录内**逐条自证**；
- **先复核再依赖**：起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **不得凑数**：任何声明都要有实现；缺实现 ⇒ 移除声明或补实现，二选一；
- **受判面不得是交集**（承 GOAL-029 掩蔽教训）：新判据的受判面必须是**声明集**本身；
- **真被使用才算数**：断言调用证据 + 下游消费证据，不得只断言「注册了」/「返回成功」；
- **点名失败而非静默**：缺实现 / 未放行 / 缺 pin / 映射缺失一律点名；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次，避免取消在飞 run）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；本地假绿（Linux 侧复验链接类判据）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP DNS 出网判据、`evolution_state` WinError 5、共享 DSN 污染） | 按既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | validator / Mimosa / 记录面判据命中新增项 | 按各处置文档修或登记；**不得绕过**；不得宣称安全 |
| 资源阈值型偶发 | 例如 CI 上 RSS < 128MiB 类阈值判据偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |

## 终止与收口

- **ACHIEVED 前置**：五 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure`（验证器进树 + 两树 + 归档 + m0 +
  治理 + 台账）并声明 `verify_paths` ≥ 2 路、**用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers`（含「需改同步集以外的既有判据断言」）或
  `budget.max_cycles` 触顶（20）；停下留人工决策，逐条写明触发项。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停止并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`R26-1` / `R26-5` / `R26-7` / `R26-8`；`W27-*` / `W10-12`；
`G24-5`；历史 `tools/` 目录仍有 73 条旧 lint 与无机器门的旧脚本（`tools/` 不过四道门，
只有**被点名脚本**有界受判）；GOAL-019…030 的未覆盖范围原样保留。

### 本轮新增残余（随 cycle 增补）

- `W31-1`｜**放行 ≠ 被用**：EC-01(e) 只证明「默认装配的一次 run 里 ≥3 条新放行能力被真实
  调用且被下游消费」，不证明全部 6 条在本轮实跑中被用（其余按调用证据与判据覆盖）。
- `W31-2`｜**同步集是「重新定基」而非「不可变」**：4 条既有钉定值的数值/示例随授权状态
  变化而变；强度（谓词形态 / 受判面 / 精确计数）保持 —— 变更前后的逐字节对照与自证随
  EC-01 交付，但「未来再次放行仍会再动一次」这一结构性成本如实登记。
- `W31-3`｜`_PROVIDERS` 为单行 tuple：**追加必然产生 1 行替换**（内容只增不减），
  EC-02 收口时用 `numstat` + 逐字节对照**如实出示**该读数，不得伪称删除为 0。
- `W31-4`｜EC-03 的「触发/跳过」声明面是**新机制**（在既有 `RunChainCall` 上追加声明式
  触发条件）；其一般性只由本协议的用例证明，未被第二个消费者证明。
- `W31-5`｜**CI 全绿已取得并解除**（2026-10-06，Actions 恢复后）：`03c2d5b`（cycle 1 / EC-01）
  的 M0 `37381070426` **八 job 全绿** + CodeQL `37381069457` 3/3 `success`。归档时的读数（如下，
  **保留为历史事实**）：`0e99dbe` 的 M0 在 GitHub Actions
  `major_outage`（runner 供给）窗口内红了两次（首跑五 job `cancelled`；重跑 attempt 2
  转绿一个、另四仍同 annotation `cancelled`）。**基础设施原因、非代码缺陷**，但**不得**
  当成「已通过」——解除条件 = Actions 恢复后对**批次提交**取到全绿结论（cycle 2 的推送会
  自然覆盖，若届时仍 outage 则继续如实登记）。

### 未覆盖范围（逐条明写，不得据此宣称安全）

读面认证未做；多租户 / RBAC / BOLA·BFLA 未做（M18 deferred）；部署面未验证（标签保持
「未验证」）；D 组审批通道未接通（`external.publish` / `package.install` / `git.commit` /
`workspace.delete` 触达即 BLOCKED）；`R-M1` 未收口；`G24-5` 未做；`R26-2/3/4/6` 未做
（条件不满足，见决策登记 ⑫–⑮）；**不得**据此宣称项目安全；**不得**宣称投递语义为
「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的
> 「回顾性台账」提交自身不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以
> 「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| commit | 结论 | run / 说明 |
| --- | --- | --- |
| `0e99dbe`（建档） | **Push-on-main 全绿 / M0 红（基础设施，非代码）** | **Push-on-main `37365192974`**：CodeQL 3/3 `success`。**M0 `37365193558`**：`container-quality` / `eval-gate` / `collector-quality` **`success`**；`quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` **`cancelled`**。**原因（如实登记，取证链三条）**：① 五个 job 的 check-run annotation **逐条**为 `The job was not acquired by Runner of type hosted even after multiple attempts`（`runner_name` 全空 = 从未拿到 runner）；② 五者**同时**在 `19:58:05–06Z` 终止（起点 `19:43:04Z`，即排队 15 分钟后被平台放弃）；③ GitHub 状态页 incident「Incident with Actions」（`created 2026-10-05T19:11:58Z`，**covering 该窗口且仍在 investigating**）：*delays in assigning GitHub-hosted runners*，Actions 组件 `degraded_performance`。⇒ 分类 **(iv) 基础设施**（runner 供给不足，非代码缺陷、非 flake、非并发取消——本例 `run conclusion=failure` + 五 job `cancelled`，与 `cancel-in-progress` 的 `run conclusion=cancelled` 形态不同）。**处置**：按 fix_policy (iv)「等窗口重跑 1 次」执行 `rerun-failed-jobs`（HTTP 201，`run_attempt=2`）；重跑结论见下一行。**覆盖面**：该提交**只**含一个 GOAL 建档文件（`git diff --stat 9c81244..0e99dbe` = 1 file / 598 insertions，零产品改动）⇒ 三个已完成 job 的绿覆盖了「树本身是好的」这一半，五个未跑 job 覆盖当日树上无新签名的改动。 |
| `03c2d5b`（cycle 1 / EC-01） | **全绿** | M0 `37381070426` **八 job 全 `success`**（`quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `container-quality` / `collector-quality` / `eval-gate` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest`）；Push-on-main `37381069457` CodeQL 3/3 `success`；`run_attempt=1`，无 `cancelled`。**该批同时覆盖 `0e99dbe` 的基础设施红**（同一工作树 + cycle 1 增量；Actions 恢复后首次推送即全绿）⇒ `W31-5` 的解除条件达成：**CI 全绿已取得**（`0e99dbe` 本身的基础设施红保留为历史事实，不追溯改写）。 |
| `0e99dbe`（重跑 attempt 2） | **仍红：`quality-windows-latest` 转绿，其余 4 job `cancelled`（同一基础设施原因）** | 同一 run `37365193558` 的 `run_attempt=2`（`rerun-failed-jobs`）：`quality-windows-latest` **`success`**（runner `GitHub Actions 1000015611`）；`quality-ubuntu-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` **仍 `cancelled`**，四者 `runner_name=''`（仍未拿到 runner）且终止时刻**同为** `20:47:41Z`（起点 `20:32:39Z` ⇒ 又是 15 分钟后被平台放弃），annotation **逐条同文**：`The job was not acquired by Runner of type hosted even after multiple attempts`。**状态页在取证时刻已升级**：incident「Incident with Actions」由 `degraded_performance` 升为 Actions 组件 **`major_outage`**（`2026-10-05T20:50Z` 读数：「Actions is experiencing degraded availability. We are continuing to investigate.」）。⇒ 同一基础设施原因**持续中**；fix_policy (iv) 的「等窗口重跑 1 次」**已用完且仍败** ⇒ 按 (iv) 的下一句登记为**基础设施阻塞**（非代码缺陷；树侧证据见下）。**本地覆盖**：五个未跑 job 中，`quality-{ubuntu,windows}` 的 m0 判据面在本机 as-is m0 跑（见「迭代日志」cycle 1 的 m0 终局行）＋定向回归 **1607 passed**；`observability-overhead-*` 的 RSS/线程阈值判据属既有 D-13 专用作业，本轮**零改动**其判据与阈值；`console-frontend` 面本轮**零改动** `apps/web`（`git diff` 零命中）。**不得**把本条读成「全绿」——它是**未取得 CI 全绿**的如实登记。 |
| `9bfbec9`（cycle 2 / EC-02） | **全绿** | 该 `head_sha` 的**全部** run 遍历取证（`scratch/goal031-cycle2/poll.log`，47 轮轮询至 `ALL_TERMINAL`；run 列表 = 该 SHA 的 2 条，无遗漏）：Push-on-main `37386777893` CodeQL 3/3 `success`（`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)`）；M0 `37386776742` **八 job 全 `success`**（`console-frontend` / `observability-overhead-windows-latest` / `eval-gate` / `quality-windows-latest` / `quality-ubuntu-latest` / `collector-quality` / `observability-overhead-ubuntu-latest` / `container-quality`）。无 `cancelled`、无 `failure`（`run_attempt=1`）。**覆盖面**：该批次 = EC-02 三态判据 + `ncbi_citation` provider + pin 夹具最小追加（记录同提交）⇒ 该树在 CI 上全绿。 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `0e99dbe`（见「CI 台账」） | 只读勘察（隔离 worktree 按压 2 组；主树零改动）+ 治理 `validate.py` | `0e99dbe` 两 run 结论见「CI 台账」首两行（Push-on-main 绿 / M0 基础设施红 + 重跑读数） | — | 五 EC 未开启 | cycle 1 = EC-01（放行面扩容的同步集与三条新判据已由建档实测标定） |
| 1 | `PLAN-20261006-293`（EC-01） | cycle 1 批次待推送（记录同提交） | EC-01 verify **93 passed**；定向回归 **1607 passed / 4 skipped**；规模门 **1112 passed**；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（第三次跑，独占、记录定稿后；首跑 4 红 = 2 处真 lint/format + 1 处协议旧版本字面量 + 1 处已知 `evolution_state` flake，逐条处置见 `RECHECK-20261006-293`）；两向反证按压 4 臂（判词归档进树）；实跑使用证据（3 条调用 + 2 条上游消费，`SUCCEEDED`） | `0e99dbe` 建档提交：Push-on-main 绿；M0 五 job `cancelled`（**GitHub runner 供给事件**，非代码）⇒ 按 (iv) 重跑 1 次。**重跑 attempt 2 仍红**：`quality-windows-latest` 转绿，另 4 job 仍同一 annotation `cancelled`（Actions 组件已 `major_outage`）⇒ (iv) 用尽，登记为**基础设施阻塞**（详见「CI 台账」行）。**cycle 1 提交 `03c2d5b` 的 M0 八 job 全绿**（`37381070426`）+ CodeQL 3/3 ⇒ `W31-5` 解除 | 判据自缺口 `W-1`（受判面初版=写法清单）已修 + 注入臂；e2e 判据 535 行触规模门 ⇒ 拆支持件 | EC-02…EC-05 未开启；`W31-1`（3 条未用）/ `W31-2`（同步集结构性成本）/ `W-2`（run 级消息不点名能力） | cycle 2 = EC-02（`citation.validate` 全链：新 provider `ncbi_citation` + 三态 + pin 最小追加） |
| 2 | `PLAN-20261006-295`（EC-02） | `9bfbec9`（记录同提交） | 三态判据 **12 passed**（两向反证 + 自检）；受判面 **586 passed / 69 skipped**；扩展 **1157 passed / 72 skipped**；会话注册 **18 passed** | `9bfbec9` 两 run 全绿（M0 八 job + CodeQL 3/3；详见「CI 台账」行） | **判据初版构造缺陷（自己修）**：`__new__` 克隆 provider 不可靠 + 小结果不落盘（默认 32 KiB 阈值 ⇒ 读不回判定）⇒ 改为直接构造 + `spill_threshold_bytes=1`（与 cycle 1 同配方） | EC-03…EC-05 未开启；`W-EC02-1/2/3` 登记 | cycle 3 = EC-03（两轮派生：触发/跳过声明面 + 两臂实测） |

| 3 | `PLAN-20261006-297`（EC-03） | cycle 3 批次待推送（记录同提交） | 判据 **13 passed**（两臂 + 两向反证 + 自检）；定向回归 **2125 passed / 73 skipped**；`tests/tooling` **1323 passed**（规模门：`phase_runner` 449→402 / `read_provider` 452→411 / `phase_capabilities` 461→441，两处拆分逐行搬运）；判词归档**实跑**生成；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（记录定稿后、独占、仓库 `.venv`、canonical DSN pin、不接管道；`PASS [` **24** / `FAILED [` **0** / **5198 passed / 21 skipped**，python 段 `781.74s`；日志 `scratch/goal031-cycle3/m0.log`，`EXIT=0`）**—— 本行 m0 读数写入于该次运行之后**，按 CI 台账同款自我指涉边界处置：其覆盖由 EC-05 收口的 as-is m0（**全部记录之后**）封闭 | 随批次推送后登记 | **三处规模门判红（自己修）**：① `phase_capabilities` 461 行 ⇒ 判定逻辑拆出 `phase_capability_triggers.py`；② `phase_runner` 449 行且 `_execute_one_task` 53 行 ⇒ parking 路径拆出 `phase_pause.py` + 派发拆出 `_dispatch_task_execution`；③ `read_provider` 452 行 ⇒ 投影拆出 `read_projection.py`。**判据初版构造缺陷**：AST 跳过 docstring（首版扫全文被自己例子误伤） | EC-04 / EC-05 未开启；`W-EC03-1/2` 登记（`W31-4` 延续） | cycle 4 = EC-04（`LineageNodeDto.label` 改名 + 四处同步 + 旧名零命中 + 兼容性实测） |
## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | ACTIVE | **cycle 3（EC-03 科研真成环）落地**：两轮派生链（第二轮经**读面**读到第一轮检索产出 —— `artifact.read` 返回内容与第一轮检索结果逐字相等）＋**声明式触发**（`requires_previous_ids` / `phase_id` / `artifact_from_previous` 三个声明字段，缺省行为逐字节不变）＋**两臂实测且可区分**（触发臂读取步 operation key 含第一轮 PMID；不触发臂 `run.completed.skipped` 逐字点名工具/字段，零请求零证据）＋**两向反证**（改坏派生路径 ⇒ FAILED 点名路径；摘掉读面抓手 ⇒ 第二轮判负并列出候选）。EC-03 = **PASS**（`RECHECK-20261006-297` = PASS_WITH_WARNINGS；`W-EC03-1/2` 登记）。为守 450 行硬上限与 50 行函数门，三处拆分（`phase_capability_triggers` / `phase_pause` / `read_projection`）全部逐行搬运、既有判据一字未改。 |
| 2026-10-06 | ACTIVE | **cycle 2（EC-02 `citation.validate` 全链）落地**：三态判定（成立 / 不成立 / 无法判定 —— **两两不等**）+ 取数面**唯一**（`elink.fcgi` 调用点== 1）+ 承接（provider `ncbi_citation`）+ 放行（scope `approved_tool_providers`）+ pin 最小追加（判据文件删除行 0）。EC-02 = **PASS**。**cycle 1 的 CI 全绿已取得**（`03c2d5b` M0 八 job + CodeQL 3/3）⇒ `W31-5`（CI 基础设施阻塞）**解除**。 |
| 2026-10-06 | ACTIVE | **cycle 1（EC-01 放行面扩容）落地**：6 条只读能力逐条放行（scope `project`）+ 镜像表同轮同步；三条新判据（只读面 / deny 面字节零改动 / `default_effect` 仍 `DENY` / 未放行护栏）+ 两向反证 + **实跑使用证据**（`run.read` / `budget.read` / `claim.read` 被真实调用、上游 2 条工具证据被两个下游各消费一次、run `SUCCEEDED`）。**判词归档进树**（三份 evidence 文件）。同步集四条既有钉定值按授权重新定基并逐条附「强度未降」自证（`RECHECK-20261006-293` = PASS_WITH_WARNINGS）。**判据自缺口抓修**：只读面判据初版只校验写法清单（14 条断言在注入 `workspace.delete` 后全绿）⇒ 改为**从文件算扩集**并加注入臂。`deny` 面基线 `bf04fa4e…` 前后逐字节相等。EC-01 = **PASS**。归档台账：`0e99dbe` 的 M0 五 job `cancelled` 系 **GitHub runner 供给事件**（annotation + 同时终止 + 状态页 incident 三条取证），按 (iv) 重跑 1 次。 |
| 2026-10-06 | ACTIVE | **建档（cycle 0）**：读 `goals/README.md` 的 GOAL 格式契约 + 只读勘察（隔离 worktree `D:/rs-goal031-probe`，主树零改动；后用 `git worktree remove` 清理）。**勘察把起点表述逐条复核并产出三组决定性实测**：**① 6 条读能力的放行后果与调用面**（预检策略 / 运行链 / 会话工具桥三处；「放行 ≠ 被用」）；**② 放行 6 条能力会移动 6 条既有判据的钉定值**（probe 实测 `6 failed / 4428 passed`，逐条点名；同步集落地后 `60 passed` —— 该同步集因此写进 fix_policy 的点名例外并带「强度未降」自证要求）；**③ `citation.validate` 的两条路线及其 pin 碰撞**（逐条点名 6 条判据；**路线决定 = 新增 provider `ncbi_citation`**，使既有 ncbi 工具面逐字不变）。另：EC-03 的既有声明式链式传参面与「触发/跳过」缺口（实测判词）、EC-04 的消费者普查、建档基线 `sha256`（含 `deny`/`require_approval` 片段 `bf04fa4e…`）全部就位。**决策登记 16 项**（⑤ 授权开工 / ⑪ 决定不做）逐条写明。五 EC 全 `PENDING`。**未覆盖范围原样保留**（读面认证 / 多租户 / RBAC / BOLA·BFLA / 部署面 / `R-M1` / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
