---
id: GOAL-20260929-027
slug: real-research-capability-onboarding
title: 真实科研能力落地（文献链扩容 + MCP 真实接入 + 多 role 子迭代闭环）
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-29 用户会话指令（goal 模式）：**建档 GOAL-027（真实科研能力落地：MCP 接入 + 文献链扩容 +
    多 role 子迭代）并授权本驱动自动化循环推进、无需我确认**。authorization 原文要点如下：
    (0) **用户明确要求「方向切换为真实科研能力」** —— 前六个 GOAL（021…026）都在**证明既有面**
    （认证 / 隐私 / 可靠性 / 复检装置），本 GOAL 改为**做真能力**：把仓库里**已有但没接通**的科研件
    接成**一次真实的科研子迭代闭环**（真实数据进、真实证据落 canonical、多个 role 各司其职、
    产出可审的科研交付物）。**验收标准从「边界成立」改为「这条链真的产出了科研产物」**
    （真数据 / 可复核 digest / 可审交付物）。
    (1) **授权范围（严格限于）**：(i) **新增 provider**（REST / MCP 均可）并把它们接进运行链
    （`capability_execution: run_chain`）；(ii) **新增 / 扩展协议与 phase 声明**
    （`examples/protocols/`、`examples/contracts/`），使一次 run 能覆盖**多个 role × 多个能力**；
    (iii) **新增真实现的 MCP server**（落 `tools/` 或既有结构，**必须**加进
    `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`）；
    (iv) **修实现过程中发现的真缺陷**；(v) 新增判据 / 夹具 / 探针（落 `tests/**` ⇒ m0 条数仍 **23**）；
    (vi) 文档同源更新（`docs/integration/MCP_TOOL_PROVIDERS.md` 等 + `docs/INDEX.md`）。
    (2) **明确不做（命中即 BLOCKED）**：改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow；
    **修改任何既有判据 / 门禁 / 阈值**（**新增**可以）；改 `PRODUCT_ROOTS` / m0 条数 / 作业结构；
    把任何真实凭据写进源码 / 示例 / 测试 / 记录 / 日志（凭据只从环境变量或密钥服务读；示例与夹具
    一律**明显不可用的合成值**）；**未经 pin 的 provider**（版本 / commit / digest 必须 pin，AGENTS.md §5）；
    **放开默认网络**（默认 CI 与默认门**必须仍离线**，`tests/egress_guard.py` 不得放宽；真实出网只允许
    在显式开关下、按既有 `requires_live_llm` 口径放行）；请求 **localhost / 环回 / 私有 / 保留地址**
    （服务端 URL 策略：仅 http/https + **触网前**校验 host）；**Canonical State 边界**（PostgreSQL Domain
    Entity 是业务真相；向量/索引只能是可重建的 derived index）；读面认证、多租户 / RBAC、BOLA·BFLA、
    `G24-4` / `G24-5`（**仍需用户拍板**，本轮只登记）；**宣称项目安全**（`R-M1` 仍在）；
    **宣称 exactly-once**。
    (3) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、**不 force**、
    **不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）+ **默认姿态不变**
    （默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）+ **默认门一律离线**。
    (4) **边界（承继）**：GOAL-001…026 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    **唯独本 GOAL 允许新增 provider / 接入运行链 / 新增 MCP server**（这是与前六轮的关键差异）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…026 的未覆盖范围**原样保留**。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >-
    把仓库里**已有但没接通**的科研件接成**一次真实的科研子迭代闭环**：在既有 `ncbi_eutils` 之外
    **新增至少一个真实文献源**（EC-01）→ 把 MCP 从「只跑 mock」推进到**真能产出科研数据的 MCP server**
    （EC-02）→ 让**系统确定性执行**检索并把真证据落 canonical（EC-03）→ 让一次 run 覆盖
    **多个 role × 多能力**并产出**可审交付物**（EC-04）→ 自举收口（EC-05）。
    **每条 EC 的验收 = 产出真实科研产物**（真标识 PMID / DOI + 内容寻址 digest + 读面可读 + 可审交付物），
    **不是**「边界成立」。**硬约束**：零真实凭据进树；**pin 先行**（未 pin 即 fail closed）；
    **URL 策略在触网之前**；**默认门离线**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1` 仍在）；
    **不得**宣称 exactly-once（**明确否认**；口径固定为 **at-least-once + idempotency + deduplication**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **真实文献能力扩容（先做宽，风险最低）**：在既有 `ncbi_eutils` 之外**新增至少一个真实文献源**
      （Europe PMC 或 arXiv；**建档勘察结论选定 Europe PMC**，理由见「事实层结论」第 14 条）。
      ① **适配器**按 `adapters/research_tools/ncbi.py` 的形态写（同步 `ToolProvider` Port、
      `httpx`、transient/permanent 错误分类、大结果 spill、内容寻址 digest；**新增的**域内文件，
      **不修改**既有适配器）；② **tool pack 条目**按 `examples/contracts/toolpack_ncbi_eutils.yaml`
      的形态 **pin**（`digest` / `resolved_revision` / `license` / `network_domains` / `tools` /
      `requested_capabilities`）；③ **登记**进 `examples/config/tool_providers.yaml`（`kind: REST`
      + `network_domains` + `capabilities`）；**既有能力名**（`literature.search` / `literature.read`）
      足以承载 ⇒ **不动** `capabilities.yaml` 词表与 `packages/application/preflight/policy_check.py`
      的 `_CAPABILITY_SCOPE` 镜像表与 `policy.yaml`（三者由既有测试锁死并集，**本轮零改动**）；
      ④ **反证（两向）**：把 URL host 换成**非声明域名** ⇒ **触网之前**被拒（断言 transport 零请求）；
      仅 http/https ⇒ 非 http(s) scheme 触网前被拒；把 host 换成环回 / 私有 / 保留地址 ⇒ 触网前被拒
      （复用 `packages/application/model_relay/endpoint_policy.py` 的 `endpoint_url_refusal`
      作为**唯一**保留类判据，不新造第二个 host 谓词）；**正控制**：合法 host ⇒ 请求真的发出且被解析；
      ⑤ **实跑取证（离线）**：`httpx.MockTransport` 走**真解析**，断言产出**内容寻址 digest**
      （`Digest.of_bytes` 重算相等）与**真实结构字段**（真 PMID / DOI / 真标题；**不得**只断言
      「返回了 dict」）。
      **判据**：适配器 + pin + 登记 + 反证两向 + 离线实跑。
    verify: >-
      新增判据文件（`tests/contracts/` 或 `tests/adapters/` 下的新文件）+ pin 契约
      `examples/contracts/toolpack_europe_pmc.yaml` 在树；
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件> -q` ⇒ 全绿；
      配套留档：真标识与 digest 实测值、反证两向的先红后绿、按压后 raw `sha256` 逐字节复原。
    status: PASS
  - id: EC-02
    criterion: >-
      **MCP 真实接入（本轮主打；建档勘察结论选定路线 (A) 自建科研 MCP server）**：把 MCP 从
      「只跑 mock（`tests/mcp_server/` 的 `literature_search` 返回 `"Mock paper"`）」推进到
      「**接一个真能产出科研数据的 MCP server**」。**路线 (A) 的理由**：`mcp>=1.28,<2` **已是仓库
      依赖**（实测安装 1.29.0）⇒ 零新增依赖；自建 server 可**完全 pin**（树内文件 = 版本即 commit）；
      零外部供应链风险；能验证「自建 MCP 走完 **注册 → 审批 → pin → 冻结 → 执行 → 取证**」整条治理链。
      ① **`ToolProviderSpec`**：`kind: MCP` + `transport: stdio`（离线 / CI 优先）+ `protocol_version`
      + `network_domains`（设适用）+ `credential_ref`（**仅在「没有它不可用」时声明**；离线路径不声明）；
      ② **凭据只经 `CredentialResolver`**，**禁止 token passthrough**；③ **真回环实测**：经
      `adapters/mcp/provider.py` 的 `McpToolProvider` **真连**（stdio 子进程）、**真调**、**真取结果**，
      断言工具名与 `literature.search` / `literature.read` 对齐、结果含**真标识**与内容寻址 digest；
      ④ **注册面**：走既有 `/tool-provider-registrations`（`POST` ⇒ `PENDING` → `/approve` ⇒ `ACTIVE`）；
      验证「**未批准不可用**」（`PENDING` / `REVOKED` 不进 catalog ⇒ 不可见 / 不可执行）；
      ⑤ **三条反证**（各自**点名**拒绝，**不得**静默降级）：**未 pin**（缺 toolpack digest /
      `pinned_revision`）⇒ preflight `SUPPLY_CHAIN_UNPINNED` 点名；**未批准**（`PENDING`）⇒ 不进入
      合并目录、执行被拒；**schema 不符**（工具参数 / 结果不匹配声明）⇒ `TOOL_SCHEMA_MISMATCH`。
      **必要的真缺陷修复（授权范围内）**：实测 `adapters/mcp/provider.py:173` 以
      `session.call_tool(tool_name, {})` **空参数**调用工具，且不像 `ncbi.py::_read_args` 那样从
      ArtifactStore 读取并校验 `argument_digest` ⇒ **任何 MCP 工具都收不到 query / ids**，
      EC-03 的运行链在其上**不可能成立**。本 EC **必须**修此缺陷（与 REST 适配器同形：按
      `tool-args:{task_id}:{operation_key}` 读参 + digest 校验），并**按压两向**证明修复非空转。
      **判据**：MCP server 在树 + pin + 真回环 + 注册面流程 + 三条反证 + 空参数缺陷已修且被按压。
    verify: >-
      **新增** MCP server 进树（`tools/` 或既有结构）并**显式加入** `IN_SCOPE`（**纯收紧**）；
      新增判据（真回环 + 注册面 + 三反证）；
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件> tests/contracts/test_tool_provider_contract.py -q`
      ⇒ 全绿（**既有 MCP 契约套件逐字节未改**）；
      配套留档：真回环调用的工具名 / 真标识 / digest 实测值、三条反证的点名拒绝消息、
      空参数缺陷修复前后的先红后绿 + raw `sha256` 逐字节复原。
    status: PENDING
  - id: EC-03
    criterion: >-
      **能力接进运行链（让系统真去取数）**：为**新 provider** 声明 `capability_execution: run_chain`
      的 phase（新增或扩展 `examples/protocols/` 下的协议），使 run 时**系统确定性执行**检索
      （而非依赖模型恰好调工具；既有判词：会话里 `provider id → SDK 工具` 映射在生产装配里是空操作，
      把证据押在「模型恰好调用」上既概率化又会红在装配缺失）。
      ① **`RunChainCall` 声明式给参**（`arguments_from_input` / `fixed_arguments` / `ids_from_previous`），
      **缺一即 fail closed**（既有 `_arguments` 语义：任一声明路径取不到 ⇒ `InvalidInputError`）；
      ② 证据经 **`register_tool_evidence`** 落 canonical，**`trust_label` 由 provider 声明的
      `network_domains` 决定**（声明了外部网络域 ⇒ `RETRIEVED`，否则 `GENERATED`；`_trust_label_for`
      是唯一判定点，**不得**由本步自称）；③ 检索结果与交付物之间**必须有 claim relation**
      （只 `register_evidence` 不 `attach_relation` ⇒ 读面看不到）；④ **实跑**：一次 run 里跑出
      **至少 2 条真实来源**（真 PMID / DOI），且 **`GET /runs/{id}/evidence` 读面真能读到**。
      **判据**：run-chain 声明 + 真标识 + 读面可见 + `trust_label` 正确。
    verify: >-
      新增离线判据（沿 `tests/e2e/test_run_chain_retrieval_offline.py` 的形态：`httpx.MockTransport`
      + 真解析 + 读面快照）：
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件> -q` ⇒ 全绿；
      配套留档：两条真标识进证据链的实测 JSON（`id` / `source_ref` / `content_digest` /
      `source_trust_label` 四列）、读面证据行、反证（去掉 run-chain 声明 ⇒ 零工具观测 ⇒ 门判拒）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **多 role 科研子迭代（本 GOAL 的目标形态）**：让一次 run 覆盖**多个 role × 多能力**，
      产出**可审的科研交付物**。① 协议至少含 **3 个 phase**，各绑**不同 role**
      （如 `literature_scout` 取文献 → `evidence_curator` 建证据 → `scientific_reviewer` 审阅），
      经 **`HandoffBundle`** 传递结构化结果（`packages/application/run_orchestration/handoff_builder.py`
      是既有构造点；**不依赖聊天记录作为唯一上下文**）；② 每个 phase 的产出**可复核**
      （digest / 结构化字段），**评审 phase 必须能对上游产出作出判定**（不是走过场：至少有一条
      **「评为不通过」**的实测用例 + 一条通过的对照）；③ **验收输入面四维接通**（承 GOAL-014）：
      `tests` / `metrics` / `policy_decision` / `schema_check` 必须从**真实事实**构造，
      **`packages/application/run_orchestration/task_phase_helpers.py` 是唯一产品路径构造点**
      （`_experiment_facts` + `_output_schema_check` ⇒ `EvaluationInputs`）；**如实边界**：
      `tests` / `metrics` / `policy_decision` 三维只在**带实验事实**的 phase 上被填充
      （无实验时 `_experiment_facts` 返回空 ⇒ 该维**缺席而非伪造**，fail-closed 语义不变）
      ⇒ 本 EC 的实跑**必须含一个带真实实验的 phase**，并断言四维各自**非伪造**且**有对照**
      （去掉事实源 ⇒ 门判拒，而不是静默放行）；④ **实跑**：默认离线链上跑到**带真实文献
      与真实评审结论的终态**（`SUCCEEDED`）。
      **判据**：多 phase 多 role + Handoff + 评审真判定 + 四维输入 + 离线实跑终态。
    verify: >-
      新增协议（`examples/protocols/`）+ 新增离线判据：
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件> -q` ⇒ 全绿；
      配套留档：run 终态、逐 phase 的 role / digest / 结构化字段实测表、评审「不通过」用例的判词、
      四维输入的实测值、HandoffBundle 的 digest 序列。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**：① 本轮收口验证器进树（`tools/verify_goal027_closeout.py`，
      复用 `tools/closeout_recheck_assertions.py` 的公共判词，只写本轮特有断言）并**显式加入**
      `IN_SCOPE`（**纯收紧**；注意 **450 行硬上限**，超限先搬公共部分）；② `tools/two_tree_recheck.py`
      跑**当前树 + 干净 checkout** ⇒ 两树同结论（逐行相同 + `sha256` 相同；**留档一律二进制写盘**）；
      ③ **as-is 本机 m0 到 23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`），
      **运行发生在记录写入之后**（承 MEM-145）；④ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
      ⑤ **CI 台账到终态**（八 job + CodeQL + `run_attempt`）；**cancelled 如实登记**，
      **空集合 / 空字段一律按「未取证」处理**（不记 OK）；⑥ 承继残余逐条在位 + 本轮新增残余
      （**凡本机不可判定的一律 PENDING + 理由**）；⑦ **未覆盖范围逐条明写**
      （读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal027_closeout.py
      --script-mode shared --root .` ⇒ 两树判词逐行相同 + `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_tooling_scripts_meet_product_gates.py -q`
      ⇒ `IN_SCOPE` 含本轮新脚本且必备清单**下界单调**；
      m0 终态行实测、CI 台账逐 run 逐 job 实查（原始 JSON 复核）。
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
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/egress_guard.py`、
      `tests/contracts/test_tool_provider_contract.py`、`tests/contracts/test_ncbi_provider_contract.py`、
      `tests/e2e/test_run_chain_retrieval_offline.py`、`tests/e2e/test_run_chain_retrieval_live.py`、
      `tests/application/run_orchestration/test_run_chain_capabilities.py`、
      `tests/architecture/python/test_run_chain_capability_exposure.py`、
      `tests/application/test_m2_audit.py`、`tests/application/preflight/**`、
      `tests/tooling/test_tooling_scripts_meet_product_gates.py`、三道记录面判据、两树入口判据、
      规模门禁）—— **新增**判据不受此限；**例外**：EC-02 的 MCP 空参数缺陷修复触及
      `adapters/mcp/provider.py`（**产品实现**，非判据），且**不得**改动其上任何既有判据
    - >-
      改 `default_effect: DENY` / 放宽 §9 默认 deny / **新增类别级 allow**；或改
      `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` 与 `policy.yaml`
      的镜像并集（两张表由既有测试锁死；本轮**零改动**）
    - >-
      **未经 pin 的 provider**：新增 provider **必须先**在 `examples/contracts/toolpack_*.yaml`
      落 `digest` / `resolved_revision` / `license` / `network_domains` 再登记（AGENTS.md §5/§12）；
      pin 缺失即 fail closed，**不得**静默降级
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
      改 `PRODUCT_ROOTS` / m0 任一 check / 作业结构 / m0 条数（终态行必须仍是 `23`）
      —— **立即 BLOCKED**
    - >-
      **新增依赖**（`mcp>=1.28,<2` **已是依赖**，不算新增；除此之外不得引入任何新依赖，
      含为判据引入第三方库 —— 一律标准库 + 现有栈）
    - >-
      **Canonical State 边界**：改「PostgreSQL Domain Entity 是业务真相」的口径，
      或把向量 / 索引 / 检索缓存写成业务真相（只允许可重建的 derived index）
    - >-
      给读面（GET / HEAD）加认证，或改读面放行语义（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
      或引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容，
      或做 **BOLA / BFLA 的专项实现**
    - >-
      动 `G24-4` 的 DTO 契约或 `G24-5` 的运行时拦截器；动 `undici`；改 `ADR-0031` 的 `Status`；
      把真实 runtime 设为**默认**（默认必须仍是 Fake）
    - >-
      用 **skip / xfail** 处理取不到的路径，或以「受判集合为空」的空真充当通过
      （承 MEM-156：受判面非空是交付前提）
    - >-
      用**测试里的合成标识**冒充真实科研产物：判据必须断言**真标识**（真 PMID / DOI / 真标题）
      与**内容寻址 digest**，**不得**只断言「调用成功」或「返回了 dict」；
      但**允许**（且要求）用 `httpx.MockTransport` 固定真实响应样本走**真解析**（离线）
    - >-
      宣称「项目安全」「授权面已覆盖」或任何形式的安全结论（`R-M1` 未收口）；
      宣称 exactly-once 或任何超出实跑证据的可靠性结论
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow —— **立即 BLOCKED**
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
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**（Mimosa 钩子 `scanner_enobufs`
    未得完整结论）
  - >-
    **宣称 exactly-once** 或任何超出实跑证据的可靠性结论 —— **立即 BLOCKED**
  - >-
    **Canonical State 边界**（把向量 / 索引 / 缓存写成业务真相）—— **立即 BLOCKED**
  - >-
    改 `PRODUCT_ROOTS` / m0 条数 / 作业结构（`23` 这一终态条数）—— **立即 BLOCKED**
  - >-
    **修改**任何既有判据 / 门禁 / 阈值（**新增**判据不受此限）—— **立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20260929-255-goal-027-ec01-real-literature-source-expansion.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-256-goal-027-ec01-europe-pmc-literature-source.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-174-provider-capability-reuse-widens-the-pin-face.md
---

## 目标与退出标准

**一句话**：把仓库里**已有但没接通**的科研件接成**一次真实的科研子迭代闭环** ——
真实数据进、真实证据落 canonical、多个 role 各司其职、产出可审的科研交付物。

**本 GOAL 与前六个 GOAL 的根本不同**：GOAL-021…026 都在**证明既有面**（认证 / 隐私 / 可靠性 /
复检装置），验收标准是「**边界成立**」；本 GOAL 改为「**做真能力**」，验收标准是
「**这条链真的产出了科研产物**」（真数据 / 可复核 digest / 可审交付物）。

**本 GOAL 允许改产品**（这是与前六轮的关键差异）：新增 provider、接进运行链、新增真实现的
MCP server、修实现过程中发现的真缺陷。**但**：不改任何既有判据 / 门禁 / 阈值、不放宽 §9
默认 deny、不改 `PRODUCT_ROOTS` / m0 条数 / 作业结构、不新增依赖（`mcp` 已是依赖）、
不把真实凭据写进任何地方、不放开默认网络。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **真实文献能力扩容**（新 provider + pin + 登记 + 反证 + 离线实跑） | 新适配器 + `toolpack_europe_pmc.yaml` + 新判据 | **PASS**（cycle 1 / PLAN-255 / RECHECK-256） |
| EC-02 | **MCP 真实接入**（自建 server + 真回环 + 注册面 + 三反证 + 空参数缺陷修复） | `tools/` MCP server + 新判据 + 缺陷修复 | **PENDING** |
| EC-03 | **能力接进运行链**（run-chain 声明 + 真标识 + 读面可见 + `trust_label`） | 协议扩展 + 离线判据 | **PENDING** |
| EC-04 | **多 role 科研子迭代**（≥3 phase × ≥3 role + Handoff + 评审真判定 + 四维 + 终态） | 新协议 + 离线判据 | **PENDING** |
| EC-05 | **自举收口**（进树验证器 + 两树 + m0 + 治理 + 台账 + 残余） | `tools/verify_goal027_closeout.py` | **PENDING** |

**依赖关系**：EC-01 → EC-02（MCP server 包真实文献源）→ EC-03（把 MCP/新 provider 接进运行链）
→ EC-04（多 role 协议跑完整闭环）；EC-05 **依赖**前四者。
EC-05 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

### 建档当日已核实的**事实层结论**（全部实测，非推测；决定 EC 切分与实现路径）

> 方法：只读勘察**实现面**（产品装配路径 vs 仅测试调用）、**配置面**、**判据面**
> （到底断言了什么 / 没断言什么）、**可注入缝**。所有条目均带 `file:line` 级证据。

1. **能力词表与 provider 承接是两张面**：`examples/config/capabilities.yaml` 是**46 条**纯名字的
   词表（`schema` 只允许 `id` + `description`，**没有** provider 字段）；承接关系声明在 **provider 侧**
   （`capabilities:` 列表），编译期反查成 `ToolRequirement.provider_ids`
   （`packages/application/protocol_compile/requirements.py:95-100`）。实测 **12 条有能力承接、
   34 条无**；真能执行的原状况只有 **1 条链**（`ncbi_eutils` 的 `literature.search` /
   `literature.read` / `citation.inspect`）。
2. **`tool_providers.yaml` 只有 3 个活跃 provider**：`openhands_workspace`（`NATIVE`）、
   `m12_artifact`（`NATIVE`）、`ncbi_eutils`（`REST` / `VERIFIED` / `network_domains:
   [eutils.ncbi.nlm.nih.gov]` / `health_check: true`）。`docs_mcp` 是**注释掉的 MCP 模板**
   （`streamable_http` + `credential_ref: DOCS_MCP_TOKEN` + `network_domains: [docs.internal.example]`）
   —— 即：**MCP 在配置面从来没有被真正启用过**。
3. **pin 不在 `ToolProviderSpec` 里**：静态 pin 来自 `examples/contracts/toolpack_*.yaml` 的
   `digest`（`catalog._load_tool_pack_digests` 读入并剥掉 `_vN` 后缀），动态 pin 来自
   `ProviderRegistration.pinned_revision`（`sha256:<64hex>`，`Digest.parse` 强制）。
   `SUPPLY_CHAIN_UNPINNED` 是 preflight 的既有检查（`packages/application/preflight/checks.py:219-224`）。
   ⇒ **EC-01/EC-02 的「pin 先行」有既有机制可依**，不需要新造。
4. **MCP 适配器完整但有一个真缺陷（本 GOAL 的关键发现）**：
   `adapters/mcp/provider.py:173` 以 `session.call_tool(tool_name, {})` **空参数**调用工具，
   且**不像** `adapters/research_tools/ncbi.py::_read_args`（`:158-166`）那样从 ArtifactStore 读
   `tool-args:{task_id}:{operation_key}` 并校验 `argument_digest`。
   ⇒ **任何 MCP 工具都收不到 query / ids**；EC-03 的运行链在 MCP provider 上**不可能成立**。
   这是「**修实现过程中发现的真缺陷**」的授权对象，**必须**在 EC-02 内修复并按压两向。
   （`transport.py` 的会话 / 超时 / 凭据注入逻辑本身是完整的：stdio 子进程、`streamable_http`、
   `with_hard_timeout`、超时驱动异常链归一化 —— 缺的**只有参数面**。）
5. **MCP 已是依赖，接 MCP 零新增依赖**：`pyproject.toml` 两处 `mcp>=1.28,<2`；实装
   `mcp-1.29.0`。⇒ EC-02 不触发「新增依赖」的 escalation。
6. **`tests/mcp_server/` 是真 stdio 回环但只跑 mock 工具**：`server.py` 的 `literature_search`
   返回 `{"query": ..., "hits": [{"id": "doc-1", "title": "Mock paper"}]}`，
   `citation_inspect` 返回 `{"citation_id": ..., "cited_by": 3}`；故障注入五态
   （`none / tool_error / slow / big / schema`）齐全；`run_stdio.py` 用
   `python -B -m tests.mcp_server.run_stdio` 起真子进程。⇒ **真回环的机关已在**，
   缺的是「**真数据**」与「**参数**」。
7. **`ncbi.py` 是唯一真 provider 的范本**（258 行）：同步 `ToolProvider` Port
   （`execute` / `list_tools` / `check_health` / `close`）、持久 `httpx.Client`、限速
   `_throttle`、429 ⇒ transient / 403 ⇒ permanent、大结果经 `spill_large_result`、
   内容寻址 `Digest.of_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())`。
   ⇒ **EC-01 的适配器照此形态写**（新文件，不动既有文件）。
8. **`toolpack_ncbi_eutils.yaml` 是 pin 的模板**：`id` / `version` / `source` /
   `resolved_revision` / `digest: sha256:947cbb22…` / `license: NLM-TOU` / `tools` /
   `requested_capabilities` / `network_domains` / `credentials`（`required: false`）/
   `compatibility`。⇒ **新 provider 照此形态 pin**。
9. **`RunChainCall` 是声明式给参**（`phase_capabilities.py:71-88`）：`arguments_from_input`
   （点分路径，最后一段即 provider 看到的参数名）/ `fixed_arguments` / `ids_from_previous`；
   `_arguments`（`:284-301`）**任一声明取不到即 `InvalidInputError`**（fail closed，不猜不编造）。
10. **证据的 trust label 由 provider 声明决定**（`_trust_label_for`，`:217-226`）：
    声明了 `network_domains` ⇒ `RETRIEVED`，否则 `GENERATED` —— **正是本 GOAL 要的语义**
    （「系统取得」不得由本步自称）。`register_tool_evidence` 会**重算 digest**（防篡改）并要求
    内容在场 ⇒ 装配方必须让运行链 provider **总是 spill**（`spill_threshold_bytes=1`）。
11. **只 `register_evidence` 不 `attach_relation` ⇒ 读面看不到**：`phase_capabilities.py` 模块
    docstring（`:16-18`）明文写着读面走 claim relations 投影 ⇒ EC-03 ③ 的判据必须打**读面**。
12. **`network_domains` 目前没有运行时出口执法（实测缺口）**：`endpoint_url_refusal`
    （`packages/application/model_relay/endpoint_policy.py`，唯一保留类判据：多播 / 未指定 /
    保留段 / CGNAT / 非全局单播 + 环回 + 私有 + 链路本地）只被 **LLM 端点与探针**调用
    （`services/api/preflight_support.py:80,89`、`runtime_support.py:136`、`model_relay/probe.py:128,262`）；
    **没有任何调用方**校验某个 tool provider 的**出站 host 是否落在它自己声明的
    `network_domains` 内**。⇒ EC-01 ④ 的反证**必须**由新适配器自己实现
    （**复用** `endpoint_url_refusal` 作保留类判据，**不新造第二个 host 谓词**；
    外加「host ∈ 声明域名」这一条声明式检查），且**必须在触网之前**判。
13. **policy 面已就绪，本轮零改动**：`examples/config/policy.yaml` 的 `allow` 已有
    `literature.search` / `literature.read`（`scope: approved_tool_providers`）与
    `network.academic`（`scope: approved_domains`）；`_CAPABILITY_SCOPE`
    （`packages/application/preflight/policy_check.py:31-41`）是它的镜像，**两张表的并集由
    `tests/application/test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml`
    锁死**（并集相等）。⇒ **新文献源复用既有能力名** ⇒ 三处（词表 / 镜像表 / policy.yaml）
    **一律不动**（任何一边动都会同时撞镜像判据与「修改既有判据」禁令）。
14. **新增文献源选定 Europe PMC**（建档勘察结论）：Europe PMC REST 是公开 JSON API
    （`www.ebi.ac.uk`），**无需凭据**即可检索与按 id 取记录 ⇒ 不声明 `credential_ref`
    （满足「只有没有它不可用才声明」）；返回**真 PMID 与 DOI**（本 GOAL 要求「真标识」）；
    形态与 `ncbi` 同族（search + fetch）⇒ 可复用解析与 spill 范式。**arXiv 作为备选**
    （`export.arxiv.org`，Atom XML，无 DOI），若 Europe PMC 在实现期被证明不可 pin / 不合规则改走。
15. **注册面状态机已在位**：`POST /tool-provider-registrations`（⇒ `PENDING`）、
    `/approve`（`PENDING → ACTIVE`）、`/revoke`（任意非终态 → `REVOKED`，终态）、`/health-check`、
    `PATCH`（改 pin / capabilities / transport）；`trust_for(state)` 由状态**推导**信任级别
    （不接受调用方声明）；`catalog_merge` **只合并 `active` 的行** ⇒
    **`PENDING` / `REVOKED` 天然不进目录**（「未批准不可用」已有结构基础，EC-02 ④ 补判据即可）。
16. **Handoff 与多 phase 的机关都在位**：`packages/application/run_orchestration/handoff_builder.py`
    的 `build_handoff(HandoffPayload)` 产出带 digest 的 `HandoffBundle`；
    `phase_runner.execute_phases`（`:159-192`）按 DAG 拓扑序逐组执行并累积
    `run.handoffs[task.id.value]`，终态返回 `handoff_digests`。⇒ EC-04 ① 的「不依赖聊天记录」
    有既成机制；`examples/protocols/` 已有 9 个协议（11 phase 的 `ai_ml_research_v0_4_0`、
    7 phase 的 `m12_reference_research_v1` 都是多 phase 范例）。
17. **四维验收输入面的真实形状（实测）**：`task_phase_helpers.py` 的 `evaluate_gate` 构造
    `EvaluationInputs(structured_output, artifacts, evidence_source_count, retrieved_source_count,
    schema_check, **tests/metrics/policy_decision)`；其中
    `tests` / `metrics` / `policy_decision` 来自 `_experiment_facts(deps, experiment)`，
    而该函数在 `experiment is None` 时**返回 `{}`**（`:256-264`）；`schema_check` 来自
    `_output_schema_check`（按合约声明的 `output_schema` 向装配方取回调，取不到 ⇒ `None` ⇒
    维持既有「schema validator unavailable」，**不是算过**）。
    ⇒ EC-04 ③ 的实跑**必须带一个真实实验 phase**，且判据要断言「四维各自**非伪造**」+ 对照
    （去掉事实源 ⇒ 门判拒），**不得**把「缺席」写成「通过」。
18. **`task_phase_helpers.py` 的真实路径**：用户指令写的是 `services/api/task_phase_helpers.py`，
    **该路径不存在**；实测唯一实体是
    `packages/application/run_orchestration/task_phase_helpers.py`。**以实测为准**。
19. **既有离线判据的形态可直接沿袭**（EC-01/EC-03 的取证范式）：
    `tests/contracts/test_ncbi_provider_contract.py`（`httpx.MockTransport` + 真解析 + 真结构断言）
    与 `tests/e2e/test_run_chain_retrieval_offline.py`（真跑运行链两步 ⇒ 证据落 canonical ⇒
    读面可读 ⇒ 门按性质裁决；含「去掉能力步 ⇒ 判拒」的反向用例）。⇒ 新判据落**新文件**，
    既有判据**逐字节不改**。
20. **射程与规模（实测余量）**：`IN_SCOPE` 现 **7 条**；`tools/*.py` 共 **27** 个（其余全在
    `LEGACY_OUT_OF_SCOPE` 逐条登记，`test_scope_partitions_every_tools_script_explicitly`
    会把未分类脚本判红）⇒ EC-02 新增的 MCP server 与 EC-05 的验证器**必须显式分类**。
    规模门禁：**单文件 ≤ 450 行、单函数 ≤ 50 行**；
    `tools/verify_goal026_closeout.py` 已 **449/450**（几乎无余量）⇒ 本轮验证器**必须**复用
    `standard_verdicts` 并保持精简。
21. **编号与工作树现状**：`.cursor/plans/tasks/` 最大序号 **253**、`.cursor/plans/rechecks/` 最大 **254**
    ⇒ 本轮子 PLAN 从 **255** 起（RECHECK 取其后继）；工作树有 **4 个与本 GOAL 无关**的 modified
    路径（`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
    `services/api/dto/models.py`、`services/api/middleware.py`，`git diff --stat` 为空 ⇒ 仅行尾态差异）
    ⇒ **一律只用显式路径提交，绝不 `git add -A`，绝不碰这 4 个文件**。
22. **基线 m0（实测口径）**：GOAL-026 收口终态行 `PASS: profile=m0; 23 deterministic checks`
    （`PASS [` = 24、`4807 passed / 21 skipped`）⇒ 本 GOAL 的终态行**必须仍是 23**，
    用例数只允许**增加**。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 的取证默认全离线**（`httpx.MockTransport` + stdio 子进程 + Fake runtime/gateway）：
真实出网只在显式开关下按既有 `requires_live_llm` 口径放行，**默认门必须仍离线**。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-027-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-027**」（**不是**把任何既有 GOAL 置回 ACTIVE）。
理由：新增 provider / 接进运行链 / 新增 MCP server 是**产品行为变更**，而 GOAL-001…026
**全部**把「新增能力」列为禁止面或需拍板面（GOAL-026 的 `forbidden` 明文列了「新增能力 ⇒
立即 BLOCKED」）⇒ 必须由**新的授权**承载，**不得**在既有 GOAL 上重开。

**本 GOAL 与前六轮的关系（承继边界）**：GOAL-001…026 **全部只读**（003 / 011 BLOCKED，
其余 ACHIEVED）；本 GOAL **不重开** GOAL-018 的 13 项 `D-NN`（已全结清），
**不消解** GOAL-019…026 的任何残余（原样保留，逐条登记见「不进入循环 / 需人工拍板」）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260929-027` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件** —— 新判据、新适配器、新 server 同样受门）；
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

- **真实数据必须真出现**（本 GOAL 与前面几轮的差别）：每条 EC 的判据必须断言**真标识**
  （真 PMID / DOI / 真标题）与**内容寻址 digest**（`Digest.of_bytes` 重算相等），
  **不得**只断言「调用成功」或「返回了 dict」。
- **pin 先行**（§5/§12）：任何外部 provider **先 pin 再登记**；pin 缺失即 **fail closed**
  （`SUPPLY_CHAIN_UNPINNED` 点名），**不得**静默降级。
- **URL 策略在触网之前**：仅 http/https，**触网前**校验 host（拒绝 localhost / 环回 / 私有 /
  保留地址；保留类判据**只有** `endpoint_url_refusal` 一处），并校验 host 落在**声明的
  `network_domains`** 内；反证必须断言**transport 零请求**（否则只是「请求后被拒」）。
- **凭据纪律**：只从环境变量 / 密钥服务读；源码、示例、测试**一律不得**出现可用凭据字面量；
  `credential_ref` **只在「没有它不可用」时声明**。
- **受判面非空**（MEM-156）、**反证两向**（MEM-159）、**射程显式分类**（MEM-158）、
  **按压后 raw sha256 逐字节复原 + 二进制写盘**（MEM-152）。
- **不得靠并集掩蔽**（MEM-160）：必备清单（`IN_SCOPE` / 能力承接面 / 残余面）必须有专门断言
  **下界**的判据。
- **默认门离线**（`egress_guard` 不得放宽）；真实出网只在显式开关下。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本（MCP stdio 回环尤其）teardown
  **必须连整棵树**（Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿 / 跨平台**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在
  Linux 侧复验**（由 CI 承担；本地按同一形态自查）。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」；
  本地门跑在「当时记录已写完」的状态，**记录面的最终覆盖由 CI 承担**；
  **不得**预先声明尚未跑出的结论。
- **批量推送（承 MEM：`cancel-in-progress`）**：一个 cycle 攒成**一次**推送，
  避免取消在飞的 M0 run；被取消的 run **如实记 `cancelled`**。
- **改工具先数夹具**：若动 `tools/two_tree_recheck.py` 或其契约，先确认
  `tests/tooling/test_two_tree_recheck_entry.py` 与
  `tests/tooling/test_closeout_assertions_are_in_tree.py` 的断言**一字不改且全绿**。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品**或**测试各半）；**修产品优先，禁改断言迁就**；若红的是**本轮新增判据**且根因是判据自身写错 ⇒ 改判据（并**按压**复验） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、RSS 阈值型、`evolution_state.json` 的 WinError 5、draft-id 排序、stdio 子进程残留） | 按既有配方重跑；**flake 判定必须靠同一代码的复跑对照**；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |
| 默认门出网 | `egress_guard` 判红 | **不得**放宽放行面；修复方向是**恢复离线**（判据本身是结构判据） |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 **全部 PASS** 且有**实跑证据**（每条含**真标识 + digest** 或
  **先红后绿**的按压证据）+ 独立 RECHECK `PASS` / `PASS_WITH_WARNINGS` + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + **未覆盖范围逐条明写**。
  **未实跑不得记 PASS**；本机无法判定记 PENDING 并停止推进。
  本 GOAL 的收口判词**必须**写明：**① 新增了哪些真实能力（逐条）**、
  **② 真实科研产物的证据（真标识 + digest）**、**③ MCP 接入路径与 pin 记录**、
  **④ 多 role 子迭代的实跑留档**、**⑤ 未覆盖范围**、**⑥ 下一批可真实现的能力清单**。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**新增依赖**、**真实凭据进树**、
  **未 pin 接上游**、**token passthrough / 未批准即用**、**放开默认网络**、
  **改 `default_effect` / 放宽 §9**、**Canonical State 边界**、**改 `PRODUCT_ROOTS` / m0 条数**、
  **修改任何既有判据 / 门槛 / 阈值**、**宣称项目安全**、**宣称 exactly-once**）、
  同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、
  或连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，
  **留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**与**需拍板项**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

**承继：GOAL-026 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子 `scanner_enobufs` 未得完整结论 | **原样保留**（**不得**据此宣称项目安全） |
| `R26-1` | 死信人工恢复路径不存在（`DEAD_LETTER` 无出边；`ADR-0030` 明文承认） | **原样保留**（实现 = 改 Accepted ADR + 新能力） |
| `R26-2` | 工具面断路器未接通（`tool_plane/health.py` 无产品调用方） | **原样保留 + 注明「需用户拍板」**（本 GOAL 新增 provider，但**不**接通断路器） |
| `R26-3` | 在飞取消信号未接通（`AgentRuntime.cancel` 无产品调用方） | **原样保留 + 注明「需用户拍板」** |
| `R26-4` | 非幂等副作用的补偿未实现（`compensation_actions` 只在文档里） | **原样保留 + 注明「需用户拍板」** |
| `R26-5` | 应用级事件消费者不存在（`consumer_offsets` 是文档独有） | **原样保留 + 注明「需用户拍板」** |
| `R26-6` | HTTP 幂等 store 是节点本地且 `get→call_next→put` 是 check-then-act | **原样保留**（改语义 = 改 `IdempotencyMiddleware`） |
| `R26-7` | CI 台账的原始证据在树外（`scratch/`，gitignored） | **原样保留** |
| `R26-8` | GOAL 正文的 EC 汇总表不在判词面内 | **原样保留**（本文件按同口径：**表与 frontmatter 同轮同改**，不靠判词钉） |
| `W-10` / `W-11` / `W-12` | 单 token ⇒ 单主体 / BOLA·BFLA 未做 / 部署面未验证 | **原样保留**（本 GOAL 不碰认证面） |
| `G24-4` / `G24-5` | `LineageNodeDto.label` 语义 / 文档条款非运行时拦截器 | **原样保留 + 注明「需用户拍板」** |
| 历史遗留 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**脚本加入必备清单） |

**本 GOAL 特有边界（= 用户判词的「明确不做」，命中即 BLOCKED）**：

1. **改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow**——**不做**；
2. **修改任何既有判据 / 门禁 / 阈值**（**新增**可以）——**不做**；
3. **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**——**不做**（终态行仍是 `23`）；
4. **把任何真实凭据写进源码 / 示例 / 测试 / 记录 / 日志**——**不做**（只从环境变量 / 密钥服务读）；
5. **未经 pin 的 provider**——**不做**（`digest` / `resolved_revision` / `license` /
   `network_domains` 先落再登记）；
6. **放开默认网络**——**不做**（默认 CI 与默认门离线；真实出网仅在显式开关下）；
7. **请求 localhost / 环回 / 私有 / 保留地址**——**不做**（仅 http/https + 触网前校验 host）；
8. **改动 Canonical State 边界**（向量 / 索引 / 缓存只能是可重建的 derived index）——**不做**；
9. **读面认证 / 多租户 / RBAC / BOLA·BFLA / `G24-4` / `G24-5`**——**只登记，需用户拍板**；
10. **新增依赖**（`mcp` 已是依赖）——**不做**；
11. **真实 runtime / 真实 LLM 出网作为默认**——**不做**（默认仍 Fake、默认 CI 离线）；
12. **用 skip / xfail 处理取不到的路径**——**不做**（要么取证，要么登记 PENDING + 理由）；
13. **用「受判集合为空」的空真充当通过**——**不做**（承 MEM-156）；
14. **宣称项目安全**（`R-M1` 仍在）——**不做**；
15. **宣称 exactly-once**（口径只能是 at-least-once + idempotency + deduplication）——**不做**。

**本 GOAL 交付的是「一条真实的科研子迭代链 + 可复跑判据」，不是「科研能力已完备」**：

- 新增的文献源**只覆盖两个来源**（NCBI + Europe PMC），检索语义 / 覆盖度不等于系统综述；
- MCP 接入走**自建 server**（路线 A），**不证明**任何**第三方** MCP server 可 pin 可用；
- 证据链证的是「**来源性质**（`RETRIEVED` vs `GENERATED`）+ **内容寻址** + **读面可读**」，
  **不**证「结论正确」——科研结论的对错不在本 GOAL 射程；
- **未覆盖范围（逐条明写；本 GOAL 不消解任何一条）**：

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 配置了外部队列的部署面只在登记面；
5. **R-M1 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称项目安全。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `8bb7d75`（建档提交，1 文件 = 本文件） | 见左侧（治理绿 + 记录面 30 passed + as-is m0 = 23/23、4807 passed） | M0 [**36568655997**](https://github.com/Eswink/research-system-new/actions/runs/36568655997) / CodeQL [**36568655008**](https://github.com/Eswink/research-system-new/actions/runs/36568655008) | 建档轮**零产品代码改动**（只新增本文件）；**零真缺陷**（门抓到的两处是**本人记录**里的措辞缺词，非产品缺陷） | EC-01…EC-05 全 PENDING。起点已定位：见「事实层结论」22 条（其中 **5 条**决定 EC 形状：第 **4** 条 MCP 空参数真缺陷 / 第 **12** 条 `network_domains` 无运行时出口执法 / 第 **13** 条 policy 三处镜像本轮零改动 / 第 **17** 条 四维输入只在带实验的 phase 上填充 / 第 **20** 条 `verify_goal026` 已 449/450 行） | cycle 1 = **EC-01**（真实文献能力扩容：Europe PMC 适配器 + pin + 登记 + 反证两向 + 离线实跑） |
| 1 | `PLAN-20260929-255`（EC-01） | （本 cycle 收口提交 = 本条回写所在提交） | 见「状态历史」：四道静态门全绿（ruff / format / mypy 1067 files）+ `tests/contracts` 455 passed / `tests/api` 580 passed / 定向消费者全绿；**按压四条**先红后绿 + 逐字节复原；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAIL [` = 0 / EXIT=0 / 4866 passed，日志 `scratch/goal027-c1c-m0.log`） | **M0 `36606591243` 八 job 全 `success` + CodeQL `36606590109` 3/3 `success`**（两者 `run_attempt=1`；原始 JSON 实查 `jobs=8 ok=8` / `jobs=3 ok=3`，轮询 44 轮到终态） | 首版 4 处本人代码判红（未 import / 6 参 / unused ignore / arg-type）+ 1 处规模门超行 ⇒ 全部按形态修（未用 noqa / type: ignore 掩盖）；P4 首轮**按压假绿** ⇒ 改判据侧复压 | EC-01 收口；**残余**：`W-1` 出口执法只覆盖本 provider / `W-2` `digest` 是声明值 / `W-4` Europe PMC 只做 search + 按 id 取记录 / `W-5` `execute` 语句级绑定 / `W-6` 按压面有限 | cycle 2 = **EC-02**（MCP 真实接入 + `McpToolProvider` 空参数真缺陷修复） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| cycle 1（EC-01 Europe PMC：适配器 3 + pin/登记 2 + 判据 4 + 夹具 pin 面 1 行 + 记录 5） | `83f5150` | M0 [**36606591243**](https://github.com/Eswink/research-system-new/actions/runs/36606591243) / CodeQL [**36606590109**](https://github.com/Eswink/research-system-new/actions/runs/36606590109) | **绿（八 job 全 `success` + CodeQL 3/3 `success`）**，两者 `run_attempt=1`（**一次成功、无 flake**）：M0 逐 job `eval-gate` / `quality-ubuntu-latest` / `quality-windows-latest` / `collector-quality` / `container-quality` / `observability-overhead-ubuntu-latest` / `console-frontend` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**。轮询日志 `scratch/goal027-c1-ci-poll.log`（`ALL_TERMINAL sha=83f515019cdc19b3637dd30ab9c4eec531a830b5`，**44 轮**）。**台账复核（原始 JSON 实查，不靠摘要）**：`scratch/goal027-c1-run-36606591243{,-jobs}.json` / `…-36606590109{,-jobs}.json` ⇒ `status=completed` / `conclusion=success` / `run_attempt=1` / `head_sha=83f51501…`；**`jobs=8 ok=8 bad=[]`** 与 **`jobs=3 ok=3 bad=[]`**。**如实登记一次本人的取材失误**：首轮用错 JSON 键名（读 `workflow_jobs` 而响应是 `jobs`）而得到 `jobs=0` ⇒ 按「空集合一律按**未取证**」口径**没有**把它读成通过，改按真实键名重取后才落盘。上游 push 回执报 **8 条**依赖告警（6 moderate + 2 low）⇒ **零依赖改动**。 |
| 建档（GOAL-027 落地，1 文件 = 本文件） | `8bb7d75` | M0 [**36568655997**](https://github.com/Eswink/research-system-new/actions/runs/36568655997) / CodeQL [**36568655008**](https://github.com/Eswink/research-system-new/actions/runs/36568655008) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `console-frontend` / `quality-windows-latest` / `observability-overhead-windows-latest` / `collector-quality` / `quality-ubuntu-latest` / `eval-gate` / `container-quality` / `observability-overhead-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**。轮询日志 `scratch/goal027-c0-ci-poll.log`（`ALL_TERMINAL sha=8bb7d7561ad5bbb73940c448aed929075c8d4469`，**34 轮**）。**台账复核（原始 JSON 实查，不靠摘要）**：`scratch/goal027-c0-run-36568655997{,-jobs}.json` / `…-36568655008{,-jobs}.json` ⇒ `status=completed` / `conclusion=success` / `run_attempt=1` / `head_sha=8bb7d7561ad5…`；**`jobs=8 ok=8 bad=[]`** 与 **`jobs=3 ok=3 bad=[]`**。**如实登记一次取材打嗝**：轮询第 3–7 轮出现 5 次「unparseable API response」⇒ 按「空集合 / 空字段 = 未取证」口径**不当结论**，改取原始 JSON 复核后才落盘（**未**把打嗝读成不一致，也**未**把不一致读成打嗝）。上游 push 回执报 **8 条**依赖告警（6 moderate + 2 low）⇒ **零依赖改动**。 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | ACTIVE | **cycle 1（EC-01）收口**：新增**第二个真实文献源 Europe PMC**（适配器三文件 + pin 契约 + 登记 + 三份新判据），AC-1…AC-6 全 PASS，`RECHECK-20260929-256` = `PASS_WITH_WARNINGS`，`MEM-20260929-174` 落档。**真标识实测**（线上取回、逐字进判据）：PMID `38000001` / DOI `10.1177/0310057x231212211` / 期刊 Anaesth Intensive Care；第二条 PMID `31452104` / DOI `10.1007/978-1-4939-9752-7_10`；内容寻址 digest 由 `Digest.of_bytes` **双向重算**相等。**URL 策略触网前**（EC-01 的净增量）：13 条反证**每条断言 transport 请求计数 == 0** + 正控制（真发出真解析）+ 反向控制（声明内即放行 ⇒ 判的是**声明**）；保留类判据**只有** `endpoint_url_refusal` 一处。**pin 记成声明值**（配方写进文件注释，实测既有 pack 的声明同样既不等于文件字节也不等于任何重算值）。**最大杀伤半径按预测命中并处置**：复用能力名 ⇒ 5 份协议 `provider_ids` 扩宽 ⇒ 夹具 `_PROVIDERS` **单行追加**，`tests/api` 由 3 failed 转 **580 passed**；新增**下界断言**（目录内非 NATIVE provider ⊆ 夹具 pin 源，受判集合非空）防静默落后。**按压四条**（P1 策略整体 / P2 白名单单点 / P3 夹具 pin 面 / P4 参数防篡改）全部先红后绿且逐字节复原；**P4 首轮假绿**（篡改值本身非法 ⇒ 断言被另一分支满足）⇒ **改判据侧复压**，未改产品代码、未放宽断言。**本地门**：ruff / format / mypy（1067 files）全绿；`tests/contracts` 455 passed、`tests/api` 580 passed、`tests/adapters` 553 passed。**一条环境类干扰已归因**：`test_worker_plane_composition` 的 3 个 postgres 用例首跑失败于 `.env` 的 `RESEARCHOS_DATABASE_URL` 覆盖测试 DSN（既有 DSN pinning 类）⇒ 按 canonical 口径 pin 后 580 passed，**未改门禁 / 断言 / 阈值**。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）；**不得**据此宣称项目安全，**不得**宣称 exactly-once（口径只能是 at-least-once + idempotency + deduplication）。**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAIL [` = 0 / EXIT=0 / **4866 passed** / 21 skipped；日志 `scratch/goal027-c1c-m0.log`，跑在记录写完**之后**、独占运行、canonical DSN pin、不接管道、零进程残留）；治理 `validate.py` 绿 + `DOCS-CHECK PASS: 6 deterministic checks`。**两处首跑判红已如实处置**：① `validate_bundle`「旧项目版本引用」—— 我用的 TEST-NET-1 地址 `192.0.<b>2</b>.<b>10</b>` 里的子串命中全仓版本号守卫 ⇒ 换成 TEST-NET-3（语义等价，**未改门禁**）；② `python/tests` 1 条资源阈值型 flake（`test_m12_reference_e2e` 满负荷下真子进程实验超时）⇒ 同代码单跑 **6 passed in 98.65s** 复跑对照，**未改用例、未动阈值**，第三次全量运行 `python/tests` 绿。**CI 到终态**：推送 `83f5150` ⇒ M0 **`36606591243` 八 job 全 `success`** + CodeQL **`36606590109` 3/3 `success`**，两者 `run_attempt=1`（原始 JSON 实查 `jobs=8 ok=8` / `jobs=3 ok=3`）；轮询 44 轮到终态（`scratch/goal027-c1-ci-poll.log`）。**如实登记一次取材失误**：首轮复核用错 JSON 键名（读 `workflow_jobs`，实际是 `jobs`）得 `jobs=0` ⇒ 按「空集合 = **未取证**」口径**没有**读成通过，改键名重取后落盘。下一 cycle = **EC-02**（MCP 真实接入）。 |
| 2026-09-29 | ACTIVE | **建档 cycle 0 完成，进入循环**：EC-01…EC-05 全 PENDING，下一 cycle 做 **EC-01**（真实文献能力扩容）。**本地验证（顺序承 MEM-145）**：治理 `validate.py` = `Cursor 治理验证通过`（8 行）；记录面判据 **24 passed**（补禁令词后复跑 **30 passed in 3.81s**，`egress guard: judged 0 connection attempt(s); blocked 0`）；**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`FAIL [` = 0、**4807 passed / 21 skipped / 95 warnings**（python/tests 段 `in 556.25s`）、`EXIT=0`；日志 `scratch/goal027-c0b-m0.log`，**日志时刻 `20:23:05` 晚于**本文件写入 `20:10:28`）；独占运行 + 进程卫生零泄漏；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令（canonical 等价）。**门抓到本人两处记录措辞错**（缺「否认」禁令词 ⇒ `assert not ['否认']`）并**改记录复绿，未动判据**。**CI 到终态**：推送 `8bb7d75` ⇒ M0 `36568655997` **八 job 全 `success`** + CodeQL `36568655008` **3/3 `success`**，两者 `run_attempt=1`（**一次成功、无 flake**；原始 JSON 实查 `jobs=8 ok=8` / `jobs=3 ok=3`）。 |
| 2026-09-29 | ACTIVE | **建档**：用户会话指令（goal 模式）授权**方向切换为真实科研能力** —— 把仓库里已有但没接通的科研件接成一次真实的科研子迭代闭环，并授权本驱动自动化循环推进、无需逐轮确认。五 EC 设计（文献扩容 / MCP 真实接入 / 接进运行链 / 多 role 子迭代 / 自举收口），budget = 20 / 120 / 2。**建档当日实测 22 条事实层结论**（见「目标与退出标准」），其中五条决定 EC 形状：**① `adapters/mcp/provider.py:173` 以空参数 `{}` 调用 MCP 工具且不读 ArtifactStore 参数 ⇒ 任何 MCP 工具收不到 query / ids，EC-03 在其上不可能成立（真缺陷，授权范围内必修）**；**② `network_domains` 没有运行时出口执法（`endpoint_url_refusal` 只服务 LLM 端点与探针）⇒ EC-01 ④ 的反证必须由新适配器自己在触网前实现**；**③ policy 三处（词表 / `_CAPABILITY_SCOPE` / `policy.yaml`）由既有测试锁死并集 ⇒ 复用既有能力名，三处一律不动**；**④ 四维验收输入（`tests`/`metrics`/`policy_decision`/`schema_check`）只在带实验事实的 phase 上被填充 ⇒ EC-04 的实跑必须含真实实验 phase**；**⑤ `tools/verify_goal026_closeout.py` 已 449/450 行 ⇒ 本轮验证器必须复用 `standard_verdicts` 并保持精简**。**建档时零产品代码改动**（只增本文件）；工作树另有 4 个**与本 GOAL 无关**的并发改动（仅行尾态差异，`git diff --stat` 为空），本 GOAL 一律只用**显式路径**提交。 |
