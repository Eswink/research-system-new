---
id: GOAL-20261001-028
slug: research-subiteration-on-the-default-assembly
title: 科研子迭代生产化（provider→SDK 声明式映射 + 活检索 + 第三方 MCP 可行性）
status: ACTIVE
created_at: 2026-10-01
updated_at: 2026-10-01
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-01 用户会话指令（goal 模式）：**建档 GOAL-028（科研子迭代生产化：
    provider→SDK 映射 + 活检索 + 第三方 MCP 可行性）并授权本驱动自动化循环推进、无需逐轮确认**。
    authorization 原文要点如下：
    (0) **方向承 GOAL-027**：GOAL-027 让真实科研能力**接上了**（第二个文献源、自建 MCP 真回环、
    运行链取真标识、3 phase × 3 role 的科研子迭代跑到 `SUCCEEDED`），但留了三条硬限制 ——
    **① 多 role 协议只在测试装配（`map_tools=True`）能跑，生产装配缺 provider→SDK 映射；
    ② MCP 语料是冻结快照，不是活检索；③ 第三方 MCP 的可 pin 性未验证。**
    本 GOAL 收这三条，把「科研子迭代」从**测试里成立**推进到**默认装配下成立**。
    (1) **授权范围（严格限于）**：(i) **新增 provider→SDK 工具映射层**，并把它接进生产组合根
    （本 GOAL 的主干）；(ii) **新增 / 扩展 provider、协议、契约、配置**；
    (iii) **新增真实现的 MCP server 或对既有自建 server 扩展**；
    (iv) **修实现过程中发现的真缺陷**；(v) 新增判据 / 夹具 / 探针（落 `tests/**`）与文档同源更新。
    (2) **明确不做（命中即 BLOCKED）**：改 `default_effect: DENY` / 放宽 §9 默认 deny /
    新增类别级 allow；**修改任何既有判据 / 门禁 / 阈值**（**新增**可以）；改 `PRODUCT_ROOTS` /
    m0 条数 / 作业结构；**把真实凭据写进源码 / 示例 / 测试 / 记录 / 日志**（一律从环境变量或
    密钥服务读；示例与夹具用**明显不可用的合成值**）；**未经 pin 的 provider**（版本 / commit /
    digest；AGENTS.md §5/§12）；**放开默认网络**（默认 CI 与默认门**必须仍离线**，
    `tests/egress_guard.py` 不得放宽；真实出网只在显式开关 + `requires_live_llm` 口径下放行）；
    **请求 localhost / 环回 / 私有 / 保留地址**（服务端 URL：仅 http/https + 触网前校验 host）；
    **Canonical State 边界**；读面认证 / 多租户 / RBAC / BOLA·BFLA / `G24-4` / `G24-5`（需用户拍板）；
    **宣称项目安全**（`R-M1`）；**宣称 exactly-once**。
    (3) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）+
    **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）。
    (4) **边界（承继）**：GOAL-001…027 **全部只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…027 的未覆盖范围**原样保留**。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >-
    把 GOAL-027 留下的三条硬限制收掉，使「科研子迭代」从**测试里成立**推进到**默认装配下成立**：
    新增**声明式** provider→SDK 工具映射层并接进**生产组合根**（EC-01）→ 把 MCP 从**冻结快照**
    推进到**真去取**（含第三方 MCP 可行性勘察结论）（EC-02）→ 在**默认装配**上跑通一次完整
    科研子迭代且每个 phase 的产出**可独立复核**（EC-03）→ 台账**合并行中间提交不漏记**并**新增加判据**
    （EC-04）→ 自举收口（EC-05）。
    **硬约束**：缺映射 / 缺 pin / 未批准 / schema 不符一律**点名失败**（**不得**静默降级）；
    **不得**把 provider id 直接当 SDK 工具名；零真实凭据进树；**pin 先行**；**URL 策略在触网之前**；
    **默认门离线**；真实数据必须真出现（真标识 + 内容寻址 digest）；m0 条数**仍是 23**；
    **不得**宣称项目安全（`R-M1` 仍在）；**不得**宣称 exactly-once（**明确否认**；口径固定为
    **at-least-once + idempotency + deduplication**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **provider→SDK 工具映射（主干，收限制 ①；先勘察再动手）**：
      (a) **勘察结论（本 GOAL 建档轮已实测，见「事实层结论」第 1–5 条）**：生产装配今天
      **根本不注册任何 SDK 工具**（`AdapterDependencies.register_tools` 缺省 `None` ⇒ 会话装配回落
      空操作），而会话工具名字面就是 **provider id**（`Tool(name=<provider id>)`）⇒ 缺映射的当前行为
      是**点名失败**（SDK `resolve_tool` 抛 `KeyError: ToolDefinition '<id>' is not registered`，
      被 `map_unexpected_exception` 收敛为 `PermanentPortError`），**不是**静默丢工具；
      该行为由既有判据固定（`test_unmapped_tool_set_is_named_not_silently_dropped`，且断言
      失败发生在**任何 LLM 调用之前**）。⇒ 修法选定为**声明化分离**（补映射表 = 给每个 provider
      硬编码一个全局 SDK 工具名，会同时撞既有判据的语义）。
      (b) **落地形态**：新增**声明式**绑定层 —— phase 声明「本 phase 的会话工具 = 哪些
      provider 绑到哪个 SDK 工具名」，编译期**原样透传**（不解释），会话解析处解析成绑定列表，
      adapter 侧按绑定注册并装配。**必须**：① 映射是**显式声明**（**不得**把 provider id 直接当
      SDK 工具名 —— 那正是缺映射的成因）；② **缺声明 / 声明指向不存在的工具 / 声明越界
      （不在冻结集内）一律点名拒绝**，且失败发生在**触达 LLM 之前**；③ **OpenHands 类型不得进
      Domain**（绑定层只用字符串与域内类型，SDK 工具类只在 `adapters/openhands/` 内可见）；
      ④ **默认路径逐字不变**：未声明绑定的协议保持今天的行为（点名失败）——
      既有判据 `test_unmapped_tool_set_is_named_not_silently_dropped` 与 `sort_analysis_v1`
      的判据**逐字节不改且仍绿**。
      (c) **接进生产组合根**：装配方（`services/api/runtime_support.py::_openhands_runtime` 及其
      两个调用点）提供 SDK 工具实现与注册面，使 `multi_role_research_v1` 在**默认装配**
      （**非** `map_tools=True`）下可跑。
      (d) **反证两向**：删掉一条映射 ⇒ 会话创建**点名失败**（不得静默降级）；
      映射到**不存在**的工具 ⇒ 同样点名失败。
      (e) **实跑**：默认装配下 `multi_role_research_v1` 跑到 `SUCCEEDED`（离线链）。
      **判据**：映射层在树 + 接进组合根 + 点名失败反证（两向）+ 默认装配实跑终态 +
      既有判据逐字节未改。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec03_real_runtime_offline_chain.py
      tests/e2e/test_multi_role_research_offline.py <新增判据文件> -q` ⇒ 全绿（既有两份判据**逐字节未改**）；
      配套留档：缺映射 / 错误映射两向的点名判词原文、默认装配实跑的 run 终态与逐 phase 产出、
      按压前后 raw `sha256` 逐字节复原。
    status: PASS
  - id: EC-02
    criterion: >-
      **活检索（收限制 ②；含限制 ③ 的勘察结论）**：
      (a) **第三方 MCP 可行性勘察结论**（建档轮已取素材，cycle 内成文并落盘）：逐个候选评定
      **许可证 / 可 pin 性（版本·commit·digest）/ 凭据需求 / 稳定性**，给出**可行或不可行 + 理由**。
      已知硬事实：仓库的 pin 规则是 `sha256:<64hex>`（`ProviderRegistration.pinned_revision`），
      许可证台账 `UPSTREAM_COMPONENTS.yaml` **逐组件**登记（`upgrade_gate.explicit_approval: true`），
      而仓内**没有任何第三方 MCP server** 的 qualification 记录 ⇒ 未登记许可 + 无法给出
      `sha256:` 制品 digest 的 git-only / 托管型 server **本轮判不可行**；判可行的候选必须能给出
      可复核 digest 且**不新增依赖**。
      (b) **扩展现有自建 server 支持真实上游检索**（若 (a) 判不可行则此路为本 EC 的落地形态）：
      复用既有 `EuropePmcProvider` / `NcbiEutilsProvider` 的**限速与解析**语义（阈值、429⇒transient、
      403⇒permanent、字段归一化、内容寻址 digest），**仍走 MCP 协议往返**（stdio 子进程 + 两个工具名
      与能力名对齐）；**默认仍是冻结语料** ⇒ 既有 MCP 判据**逐字节不改且仍绿**。
      (c) **非预置语料判据（活检索的判据必须与快照不同）**：断言「取到的语料**不是预置的**」——
      判据提供**与树内冻结语料不相交**的上游响应（走真协议栈 + 真解析），断言取到的是**上游返回的
      那条**（真标识 + 内容寻址 digest 重算相等），并断言该标识**不在**树内冻结语料中。
      (d) **离线门保持离线**：活检索只在**显式开关**下；默认门用 `httpx.MockTransport` 走真协议栈；
      `tests/egress_guard.py` **不得放宽**；真实出网按既有 `requires_live_llm` 口径。
      **硬约束（事实层第 6 条）**：**不得**往 `examples/config/tool_providers.yaml` 追加 provider id
      （会撞既有判据的「出厂目录 id 集」断言 = 修改既有判据）⇒ 活检索走**自建 server 的模式扩展**
      与既有运行期注册面。
      **判据**：第三方勘察结论在树 + 活检索路径在树 + 非预置语料判据（含正反两向）+ 离线路径仍绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_research_server_loopback.py
      tests/contracts/test_mcp_registration_and_refutations.py tests/e2e/test_literature_chain_run_offline.py
      <新增判据文件> -q` ⇒ 全绿（既有三份判据**逐字节未改**）；
      配套留档：勘察结论文档路径、非预置语料判据的实测标识与 digest、离线路径的零出站取证。
    status: PASS
  - id: EC-03
    criterion: >-
      **多 role 子迭代在默认装配上的完整闭环（合并 ①②的验收）**：在**默认装配**（非
      `map_tools=True`）上跑通一次完整科研子迭代，且**每个 phase 的产出可独立复核**：
      ① 检索 phase 取到**真标识**（PMID / DOI）且 `source_trust_label=RETRIEVED`
      （性质由 provider 声明的 `network_domains` 决定，唯一判定点，**不得**由本步自称）；
      ② 实验 phase 产出**真 metrics**（沙箱实验，四维输入 `tests` / `metrics` / `policy_decision` /
      `schema_check` 接通，且**有对照**：摘掉事实源 ⇒ 门判拒而非静默放行）；
      ③ 评审 phase **真能判不通过**（反证分支：摘掉上游证据 ⇒ 判拒 ⇒ run `FAILED`，判词**点名**
      缺的那一维）；
      ④ 交付物与其覆盖来源之间有 **claim relation**（`GET /runs/{id}/evidence` 真读得到四列：
      `id` / `source_ref` / `content_digest` / `source_trust_label`）；
      ⑤ **HandoffBundle 的 digest 序列可取证**（逐任务一条 `sha256:<64hex>`、互不相同 ——
      承 GOAL-027 修的那处真缺陷）。
      **判据**：默认装配实跑 + 四相位产出逐条 + 评审反证 + 读面四列 + Handoff digest 序列。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件 -q` ⇒ 全绿；
      配套留档：默认装配实跑的 run 终态、逐 phase 的 role / digest / 结构化字段实测表、
      真标识与 metrics 实测值、评审反证的判词原文、读面四列快照。
    status: PASS
  - id: EC-04
    criterion: >-
      **台账合并行的中间 run 不漏记（收 GOAL-027 的实测缺口；建档轮已用原始 API 复核）**：
      实测事实：GOAL-027 台账把 `6e27a14 + edd4de8 + a603267 + 93fa7f7` 四个提交**合并成一行**，
      只记了 `93fa7f7` 的 run；而 `a603267` 的 M0 `36685047472` 是 **cancelled**
      （`6e27a14` / `edd4de8` 在 REST API 上 `total_count=0`，即**无自带 run**），
      该行却写「无 cancelled」。
      (a) **如实补记**该缺口（**只追加，不改历史行**）：写明哪几个提交被合并行覆盖、
      各自的实际 run 结论（含 `cancelled` 如实登记）、以及**由谁的绿承担**。
      (b) **新增加判据**：**每一个推送的提交**都必须能在台账里找到对应的 run 记录
      （或**明确标注**「其 run 被合并行覆盖 + 由谁承担绿」）；缺一项即判红。
      (c) **反证两向**：造一条「合并行漏记中间提交」的台账 ⇒ 判红；补齐 ⇒ 绿。
      (d) **判据不得被散文喂饱**（承 MEM:141）：绑定**结构化字段**（提交 `sha` ↔ run id），
      不接受「写了几个字说覆盖了」。
      **判据**：缺口补记 + 新判据在树 + 反证两向。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest <新增判据文件> -q` ⇒ 全绿；
      反证两向各自先红后绿且 raw `sha256` 逐字节复原；
      配套留档：GOAL-027 台账补记行的原文、原始 REST API 响应（逐 run 的 `conclusion` /
      `run_attempt`）与判据读到的结构化字段实测值。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**：① 收口验证器进树
      （`tools/verify_goal028_closeout.py`，复用 `tools/closeout_recheck_assertions.py` 的公共判词，
      只写本轮特有断言）并**显式加入** `IN_SCOPE`（**纯收紧**；**450 行硬上限**，超限先搬公共部分）；
      ② `tools/two_tree_recheck.py` 跑**当前树 + 干净 checkout** ⇒ 两树同结论（逐行相同 +
      `sha256` 相同；**留档一律二进制写盘**）；③ **as-is 本机 m0 到 23/23**
      （终态行 `PASS: profile=m0; 23 deterministic checks`），**运行发生在记录写入之后**（承 MEM-145）；
      ④ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
      ⑤ **CI 台账到终态**（八 job + CodeQL + `run_attempt`）；**每一个推送的提交都要有对应 run 行**
      （EC-04 的判据在本轮自身台账上生效）；`cancelled` **如实登记**，
      **空集合 / 空字段一律按「未取证」处理**（不记 OK）；
      ⑥ 承继残余逐条在位 + 本轮新增残余（**凡本机不可判定的一律 PENDING + 理由**）；
      ⑦ **未覆盖范围逐条明写**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` 未收口）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal028_closeout.py
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
      `tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/e2e/test_multi_role_research_offline.py`、
      `tests/contracts/test_mcp_research_server_loopback.py`、
      `tests/contracts/test_mcp_registration_and_refutations.py`、
      `tests/contracts/test_europe_pmc_pin_and_registration.py`、`tests/api/run_fixtures.py` 的
      `_PROVIDERS` 行、`tests/application/preflight/**`、
      `tests/tooling/test_tooling_scripts_meet_product_gates.py`、三道记录面判据、两树入口判据、
      规模门禁）—— **新增**判据不受此限
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
      **把 provider id 直接当 SDK 工具名**：映射必须是**显式声明**；缺映射、映射到不存在的工具、
      或映射越出冻结集 —— 一律**点名失败**，**不得**静默丢弃 / 静默回退 / 自动造名
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
      （承 MEM:156：受判面非空是交付前提）
    - >-
      用**测试里的合成标识**冒充真实科研产物：判据必须断言**真标识**（真 PMID / DOI / 真标题）
      与**内容寻址 digest**，**不得**只断言「调用成功」或「返回了 dict」；
      但**允许**（且要求）用 `httpx.MockTransport` 固定真实响应样本走**真解析**（离线）
    - >-
      台账**合并行漏记**：批量推送的每一个提交都必须在 CI 台账里有对应 run 记录
      （或明确标注覆盖关系 + 由谁承担绿）；`cancelled` 必须如实登记；
      **空集合 / 空字段 = 未取证**，不得记 OK
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
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**
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
  - .cursor/plans/tasks/PLAN-20261001-267-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md
  - .cursor/plans/tasks/PLAN-20261001-269-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md
  - .cursor/plans/tasks/PLAN-20261001-271-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261001-272-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md
memory_entries:
  - .cursor/memory/entries/MEM-20261001-180-sdk-tool-registry-is-process-global.md
  - .cursor/memory/entries/MEM-20261001-181-tools-is-not-a-package-so-load-by-path.md
  - .cursor/memory/entries/MEM-20261001-182-run-chain-exclusion-is-per-phase.md
---

## 目标与退出标准

**一句话**：把 GOAL-027 留下的三条硬限制（① 生产装配缺 provider→SDK 映射；② MCP 是冻结快照；
③ 第三方 MCP 可 pin 性未验证）收掉，使「科研子迭代」从**测试里成立**推进到**默认装配下成立**。

**本 GOAL 与 GOAL-027 的差别**：GOAL-027 让能力**接上了**（第二个文献源、自建 MCP 真回环、
运行链取真标识、3 phase × 3 role 跑到 `SUCCEEDED`），但那条链**只在测试装配里成立**
（`map_tools=True` 是测试侧补的映射）。本 GOAL 的验收标准是
「**默认装配（生产组合根）下那条链真的成立**」。

**本 GOAL 允许改产品**：新增**声明式** provider→SDK 工具映射层并接进生产组合根、
扩展自建 MCP server、新增协议 / 契约 / 配置、修实现过程中发现的真缺陷。
**但**：不改任何既有判据 / 门禁 / 阈值、不放宽 §9 默认 deny、不改 `PRODUCT_ROOTS` / m0 条数 /
作业结构、不新增依赖（`mcp` 已是依赖）、不把真实凭据写进任何地方、不放开默认网络。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **provider→SDK 声明式映射**（映射层 + 接进组合根 + 点名失败反证 + 默认装配实跑） | 声明层 + 解析层 + 装配面 + 新判据 | **PASS**（cycle 1 / PLAN-267 / RECHECK-268） |
| EC-02 | **活检索**（第三方勘察结论 + 自建 server 真上游 + 非预置语料判据 + 离线仍绿） | 勘察结论 + server 扩展 + 新判据 | **PASS**（cycle 2 / PLAN-269 / RECHECK-270） |
| EC-03 | **默认装配完整闭环**（真标识 + 真 metrics + 评审反证 + 读面四列 + Handoff digest） | 新判据 + 实跑留档 | **PASS**（cycle 3 / PLAN-271 / RECHECK-272） |
| EC-04 | **台账合并行不漏记**（缺口补记 + 新判据 + 反证两向） | GOAL-027 台账补记 + 新判据 | **PENDING** |
| EC-05 | **自举收口**（验证器进树 + 两树 + m0 + 治理 + 台账 + 残余） | `tools/verify_goal028_closeout.py` | **PENDING** |

**依赖关系**：EC-01 → EC-02（活检索经 MCP 路径）→ EC-03（默认装配上的完整闭环，同时消费
①②的产物）；EC-04 独立（记录面判据，可与前三者并行）；EC-05 **依赖**前四者。
EC-05 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

### 建档当日已核实的**事实层结论**（全部实测，非推测；决定 EC 切分与实现路径）

> 方法：只读勘察**实现面**（产品装配路径 vs 仅测试调用）、**配置面**、**判据面**
> （到底断言了什么 / 没断言什么）、**可注入缝**，并用 GitHub REST API **原始 JSON**
> 复核 CI 台账。所有条目均带 `file:line` 级证据。

1. **生产装配今天不注册任何 SDK 工具（缺映射的准确形状）**：`build_agent_runtime`
   （`services/api/runtime_support.py:225-246`）→ `_openhands_runtime`（`:174-222`）构造
   `AdapterDependencies` 时**不传** `register_tools`；该字段缺省 `None`
   （`adapters/openhands/session_types.py:84`），`SessionBuilder.__init__` 回落到
   `lambda spec: None`（`adapters/openhands/session_builder.py:46`）⇒ 生产侧**没有**任何
   SDK 工具注册动作。两个生产调用点（`services/api/composition.py:299-305`、
   `services/api/pg_composition.py:200-206`）同样不传。
2. **会话工具名字面就是 provider id**：`SessionBuilder.build_session` 先在 `:67` 用
   `session_tool_ids(spec.frozen_tool_set, spec.run_chain_tool_ids)` 算工具列表，
   再在 `:105` 以 `Tool(name=name)` 装配 —— 名字直接取自冻结集，而冻结集由
   `flatten_tool_providers(plan)` 产出（`packages/application/run_orchestration/session_resolution.py:30-34,119`），
   即 **provider id 字符串**。⇒ 「provider id 直接当 SDK 工具名」不是假设，是**今天的实现事实**，
   也正是缺映射的成因（EC-01(b) 的禁止项由此而来）。
3. **缺映射的当前行为 = 点名失败，不是静默丢工具（实测）**：SDK 在 agent 初始化时解析每个
   `Tool(name=...)`；`resolve_tool` 对未注册名字抛
   `KeyError("ToolDefinition '<name>' is not registered")`
   （`.venv/Lib/site-packages/openhands/sdk/tool/registry.py:149-156`），
   `runtime_adapter.create_session` 的兜底把它收敛为
   `PermanentPortError(..., SYSTEM_BUG)`（`adapters/openhands/runtime_adapter.py:150-151` +
   `error_mapping.py:111-116`）⇒ 会话创建失败、失败消息**点名**那个 provider id。
   既有判据把它固定为「今天真实行为」：`test_unmapped_tool_set_is_named_not_silently_dropped`
   （`tests/e2e/test_ec03_real_runtime_offline_chain.py:129-143`）断言 run `FAILED`、
   失败文本含 `is not registered`、且 **mock 端点零请求**（失败在**任何 LLM 调用之前**）。
   ⇒ **这正是本 GOAL 必须保住的语义**：映射层解决「起不来」，但**不得**把它变成静默丢工具。
4. **既有判据是本 EC 的硬约束（决定修法）**：`test_declared_run_chain_capabilities_let_production_assembly_start`
   （同文件 `:146-181`）用 **demo 协议**（不声明 `capability_execution`）在 `map_tools=False`
   下断言「未映射 ⇒ 点名拒绝」；`test_a_two_provider_frozen_set_starts_a_session`
   （`:184-205`）用 `map_tools=True` 断言两件 provider 的冻结集能起。⇒ 若把映射做成
   **全局注册**（给所有 provider id 无条件注册 SDK 工具），第 3 条判据会**判红**
   （demo 协议也将起得来）。所以映射**必须**是**声明作用域**的：只有显式声明绑定的协议改变行为，
   未声明者**逐字保持今天的行为**。这条决定了 EC-01(b) 的形态。
5. **测试侧的「映射」其实是恒等映射，且不是产品面**：`tests/e2e/live_run_support.py`
   的 `real_runtime(..., map_tools: bool)`（`:202-230`）在 `map_tools=True` 时把
   `register_tools=register_inert_tools` 注入 `AdapterDependencies`，而
   `register_inert_tools`（`:96-101`）把**每个冻结 provider id 按自身名字**注册成一个惰性
   `ToolDefinition` 子类（`inert_tool_class_for`，`:74-93`，按名生成类以免两件 provider 同名冲突）
   ⇒ 测试侧走的是**同名字符串**，与真实 SDK 工具名空间无关；`map_tools=False` 则**原样调用**
   `build_agent_runtime` 以测量生产行为。⇒ EC-01 要补的正是**产品侧**那一层（EC-01(c)）。
6. **出厂目录的 provider id 集被既有判据锁死（决定 EC-02 的落地形态）**：
   `tests/contracts/test_europe_pmc_pin_and_registration.py:173-179` 断言
   `set(catalog) == {openhands_workspace, m12_artifact, ncbi_eutils, europe_pmc}`；
   同文件 `:188-205` 另断言「目录内非 NATIVE provider ⊆ 夹具 pin 源」（缺一即
   `SUPPLY_CHAIN_UNPINNED`）。⇒ **往 `examples/config/tool_providers.yaml` 追加 provider id
   会撞既有判据**（= 修改既有判据，本轮禁止）⇒ EC-02 的活检索**不得**新增出厂 provider id，
   只能走**自建 server 的模式扩展**与既有**运行期注册面**（`/tool-provider-registrations`）。
7. **`schemas/tool-provider.schema.json` 是 `additionalProperties: false`**（`:5-6`），
   经 `load_tool_providers`（`adapters/contracts/resource_loaders.py:127-150`）在加载期强校验。
   ⇒ 若要给 provider 加新字段，**必须**同轮改 schema（属「新增 / 扩展配置」，在授权内），
   且不得改动既有字段语义。
8. **协议 schema 的 phase 是闭集合**：`schemas/protocol.schema.json` 的 `$defs.phase`
   为 `additionalProperties: false`（`:20-24`），现有字段含
   `capability_execution: {"enum": ["session","run_chain"]}`（`:59`）。
   ⇒ EC-01 的新声明（session 工具绑定）**必须**同轮加进 schema；这是**扩展**，不是改既有语义
   （既有 `capability_execution` 的枚举与语义一字不动）。
9. **`CapabilityExecution` 是「声明化分离」的既有先例（EC-01 的形态模板）**：
   枚举在 `packages/domain/protocols.py:42-54` 声明（其 docstring 已写明
   「声明缺席的名字依旧会因『未注册』被**点名拒绝**」），loader 在
   `adapters/contracts/protocol_loaders.py:65-66` 读入，编译器**原样透传**
   （`packages/application/protocol_compile/compiler.py:68`），**唯一解释点**在
   `packages/application/run_orchestration/session_resolution.py:37-57`，
   消费点是 `tool_mapping.session_tool_ids`（`adapters/openhands/tool_mapping.py:27-46`，
   越界即 `ValueError` 点名）。⇒ EC-01 的绑定层照此形态：**域内声明 → 编译透传 →
   应用层唯一解释 → adapter 消费**；SDK 工具类只在 adapter 内。
10. **SDK 自带的工具极少（决定「映射到什么」必须由装配方提供）**：
    `.venv/Lib/site-packages/openhands/sdk/tool/builtins/` 只有 `finish` / `think` /
    `invoke_skill` / `switch_llm` / `vision_inspect`；`defaults.py` 里的
    `terminal` / `file_editor` / `task_tracker` 属 **`openhands-tools`**（本仓**未安装**）。
    ⇒ 「provider id → 既有 SDK 工具名」这张表在本仓**基本无目标可选**；映射层必须让
    **装配方**为声明的工具名提供实现（与 `ToolProvider` Port 的 `execute` 面相接），
    这也正是 `build_agent_runtime` 要接的新缝。
11. **`register_custom_tools` 是既有的（但无人调用的）注册面**：
    `adapters/openhands/tool_mapping.py:49-54` 已存在，全仓零调用方（`rg` 实测只命中定义与
    `__all__`）。⇒ EC-01(c) 的自然接入点，属「扩展既有结构」而非新造平行机制。
12. **NATIVE 两件 provider 没有 Python 实现，也没有 Port 实例**：全仓产品代码零命中
    `openhands_workspace` / `m12_artifact`（只在 `tests/`、`examples/`、docs 出现）；
    `ApiDeps.tool_providers`（`services/api/composition.py:135-137`）在**两个**组合根都**从未被赋值**
    （恒为空 dict）⇒ 今天这两件 provider 在运行期**没有执行体**，只有能力声明
    （`examples/config/tool_providers.yaml:2-17`）。NATIVE 的健康探测因此短路
    （`services/api/preflight_support.py:154-155`）。⇒ EC-01 若让这两件进会话工具列表，
    必须由装配方提供**真实（或受控 fake）实现**，**不得**只注册一个空壳充当「已映射」。
13. **MCP server 是冻结快照，且被三份判据钉死（决定 EC-02 必须**加**路径而非改路径）**：
    `tools/research_mcp_server.py`（209 行）服务 7 条 2026-09-30 经 Europe PMC 实取的记录，
    模块 docstring 明写「**不得**把它叙述成『实时检索』」；判据侧
    `tests/contracts/test_mcp_research_server_loopback.py` 断言**字节级确定性**
    （同 query 两次 `result_content` 相同 + `output_digest` 相同，`:148-161`）、
    `tests/contracts/test_mcp_registration_and_refutations.py:428-441` 断言
    `network_domains=[]` 时标签为 `GENERATED`、`:443-448` 断言声明网络域后变 `RETRIEVED`。
    ⇒ EC-02 的活检索**必须是加出来的模式**（默认仍走冻结语料），既有三份判据**逐字节不改**。
14. **Europe PMC 的限速 / 解析 / digest 语义可被 stdio server 复用**：
    `EuropePmcProvider.__init__`（`adapters/research_tools/europe_pmc.py:89-103`）只依赖
    `ArtifactStore` + 可选 `httpx.Client` / `url_policy` / `config`，**不需要 API app、不需要凭据**
    （模块 docstring 明写不解析任何凭据）；限速 `_throttle`（`:188-192`，匿名 0.34s 间隔）、
    429/5xx ⇒ transient、4xx ⇒ permanent（`europe_pmc_runtime.py:97-118`）、
    内容寻址 `Digest.of_bytes`（`:218-226`）。**触网前 URL 策略**在 `assert_url_allowed`
    （`europe_pmc_runtime.py:73-94`：仅 http(s) + `endpoint_url_refusal` + **host ∈ 声明的
    `network_domains`**）。⇒ EC-02(b) 复用面明确；`tools/` 不在 `PRODUCT_ROOTS` 内但在
    `IN_SCOPE` 四道门内（§15），实现须自持判据。
15. **工具脚本射程与规模（实测余量）**：`tools/*.py` 共 **29** 个；
    `IN_SCOPE` 由 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 固化
    （`:52-61`），`LEGACY_OUT_OF_SCOPE` 逐条登记（`:73+`），
    且有一条判据要求「每个脚本都必须被显式分类」（未分类即判红）。
    规模门禁：**单文件 ≤ 450 行、单函数 ≤ 50 行**。
    现有行数：`tools/verify_goal027_closeout.py` **405**、`tools/closeout_recheck_assertions.py`
    **388**、`tools/two_tree_recheck.py` **329**、`tools/research_mcp_server.py` **209**。
    ⇒ EC-05 的验证器**必须**复用 `standard_verdicts` 并保持 ≤450；
    EC-02 的 server 扩展**必须**保持 ≤450 与 ≤50/函数（超限先拆模块）。
16. **CI 台账的缺口已用原始 API 复核（EC-04 的事实基础）**：
    `a603267`（full `a6032676ddbb0e225f4796139784701bf3cc80ed`）命中 **2** 个 run ——
    `36685046965`（Push on main，`completed/success`）与 `36685047472`
    （M0 Quality Gates，`completed/**cancelled**`），均 `run_attempt=1`；
    `6e27a14` 与 `edd4de8` 各自 `total_count=0`（**无自带 run**）；
    `93fa7f7` 命中 `36686124759`（M0，success）与 `36686123873`（Push on main，success）。
    而 GOAL-027 台账把四个提交**合并成一行**、只记 `93fa7f7` 的 run，并写「无 cancelled」。
    ⇒ 缺口属实（EC-04）；**只追加修正行，不改历史行**。
17. **「空集合 = 未取证」在本仓有先例**：GOAL-027 台账两次如实登记取材失误
    （错 JSON 键名得 `jobs=0` ⇒ 不当结论，改键名重取）。⇒ 本 GOAL 的 CI 台账沿用同一口径，
    并对**每一个推送提交**逐条落 run 行（EC-04(b) 的判据约束本轮自身）。
18. **记录面判据会扫本文件（写作时必须避坑）**：
    `tests/architecture/python/test_delivery_semantics_wording.py` 把
    `.cursor/plans/goals` 单列为**规则文本面**（`:47-58`）：文件只要出现
    `exactly[ _-]once`（ASCII lemma），就**必须同时**出现禁令词表的**全部**词
    （`("禁止","不得","否认","不做","BLOCKED","口径")`，`:59-60`），否则判红；
    `tests/architecture/python/test_reproducibility_wording.py` 扫 `.cursor/plans`，
    不带引号且无否定标记的「完全可复现 / fully reproducible」一类**肯定式**表述判红；
    `tests/api/test_control_plane_token_never_leaks.py:258-269` 扫 `.cursor/plans` + `.cursor/memory`
    的凭据**值**（变量名允许）。⇒ 本文件的措辞按此校准（已含全部禁令词）。
19. **治理对 GOAL 的硬性结构要求**：`check_goals()`
    （`.cursor/skills/governance-check/scripts/validate.py:604-642`）要求
    id 匹配 `GOAL-\d{8}-\d{3}`、文件名以 id 开头、七个必含章节
    （`GOAL_HEADINGS`，`:49-57`）、`created_at`/`updated_at` 是日期、
    `exit_criteria` 非空、`budget.max_cycles` 为 ≥1 整数、`authorization` 非空；
    `ACHIEVED` 另有「全部 EC `PASS` + `latest_recheck` 存在且 `result ∈ {PASS,
    PASS_WITH_WARNINGS}`」的额外要求（`:625-642`）。`latest_recheck` 用
    `resolve_repository_path`（`:149-155`）解析 ⇒ **必须是仓库相对路径**（承 MEM:）。
20. **编号与工作树现状**：`.cursor/plans/tasks/` 最大序号 **265**、
    `.cursor/plans/rechecks/` 最大 **266** ⇒ 本 GOAL 的子 PLAN 从 **267** 起（RECHECK 取其后继）。
    工作树有 **4 个与本 GOAL 无关**的 modified 路径
    （`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
    `services/api/dto/models.py`、`services/api/middleware.py`）与 1 个未跟踪文件
    （`.zcodeignore`）⇒ **一律只用显式路径提交，绝不 `git add -A`，绝不碰这些路径**。
21. **基线 m0（实测口径）**：GOAL-027 收口终态行
    `PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24、`4928 passed / 21 skipped`）
    ⇒ 本 GOAL 的终态行**必须仍是 23**，用例数只允许**增加**。m0 必须独占、用仓库 `.venv`、
    经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**。
22. **本 GOAL 的取证默认全离线**：`httpx.MockTransport` + stdio 子进程 + Fake runtime/gateway；
    真实出网只在显式开关下按既有 `requires_live_llm` 口径放行，**默认门必须仍离线**。
    注意一处**结构边界**（如实登记）：`tests/egress_guard.py` 自述射程**不含子进程**
    （`:31-33`）⇒ MCP stdio 子进程内的出站**不在**守卫射程内；因此活检索路径**必须**由
    显式开关 + 判据自身断言（MockTransport 计数 / 零请求）双保险，**不得**只依赖守卫。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-028-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-028**」（**不是**把任何既有 GOAL 置回 ACTIVE）。
理由：新增 provider→SDK 映射层 / 接进生产组合根 / 扩展 MCP server 是**产品行为变更**，
而 GOAL-001…027 的 `forbidden` 明文把「新增能力」列为禁止面或需拍板面 ⇒ 必须由**新的授权**
承载，**不得**在既有 GOAL 上重开。

**本 GOAL 与 GOAL-027 的关系（承继边界）**：GOAL-001…027 **全部只读**
（003 / 011 BLOCKED，其余 ACHIEVED）；本 GOAL **不重开** GOAL-018 的 13 项 `D-NN`
（已全结清），**不消解** GOAL-019…027 的任何残余（原样保留，逐条登记见
「不进入循环 / 需人工拍板」）；**唯一例外**是 EC-04(a) 对 GOAL-027 台账的**只追加**
补记（用户指令明文授权，且不改历史行）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20261001-028` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM:125）。
  规模门禁自查（**50 行函数 / 450 行文件** —— 新判据、映射层、server 扩展同样受门）；
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

- **默认装配必须真的能跑**（本轮与 GOAL-027 的差别）：EC-01 / EC-03 的判据必须在
  **生产装配路径**（`build_agent_runtime` 的真实缺省、**非** `map_tools=True` 的测试后门）
  上实跑；测试后门只允许用于**既有**判据的回归。
- **点名失败而非静默降级**：缺映射、缺 pin、未批准、schema 不符、声明越界 —— 一律**点名**拒绝，
  且失败必须发生在**副作用之前**（LLM 调用 / 子进程 / 网络请求）。
- **真实数据必须真出现**：断言真标识（真 PMID / DOI / 真标题）与内容寻址 digest
  （`Digest.of_bytes` 重算相等），**不得**只断言「调用成功」或「返回了 dict」。
- **pin 先行**（§5/§12）；**URL 策略在触网之前**（仅 http/https + 触网前校验 host + 拒绝
  环回 / 私有 / 保留 + host ∈ 声明的 `network_domains`；保留类判据**只有**
  `endpoint_url_refusal` 一处）。
- **凭据纪律**：只从环境变量 / 密钥服务读；源码、示例、测试**一律不得**出现可用凭据字面量；
  `credential_ref` **只在「没有它不可用」时声明**。
- **受判面非空**（MEM:156）、**反证两向**（MEM:159）、**射程显式分类**（MEM:158）、
  **按压后 raw sha256 逐字节复原 + 二进制写盘**（MEM:152）。
- **不得靠并集掩蔽**（MEM:160）：必备清单（`IN_SCOPE` / 能力承接面 / 残余面）必须有专门断言
  **下界**的判据。
- **默认门离线**（`egress_guard` 不得放宽）；真实出网只在显式开关下。
- **台账逐提交**（本轮的 EC-04）：**每个推送的提交都要有 run 行**；合并行必须写明
  「覆盖了哪几个提交、由谁的绿承担」；`cancelled` **如实登记**；
  **空集合 / 空字段 = 未取证**（不得记 OK）。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本（MCP stdio 回环尤其）teardown
  **必须连整棵树**（Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿 / 跨平台**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在
  Linux 侧复验**（由 CI 承担；本地按同一形态自查）。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」；
  本地门跑在「当时记录已写完」的状态，**记录面的最终覆盖由 CI 承担**；
  **不得**预先声明尚未跑出的结论。
- **批量推送（承 MEM：`cancel-in-progress`）**：一个 cycle 攒成**一次**推送，
  避免取消在飞的 M0 run；被取消的 run **如实记 `cancelled`**，且**在台账里有自己的行**
  （EC-04 的判据约束本轮自身）。
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
| 台账缺行 | EC-04 的新判据在自己或历史台账上报红 | 按「只追加」补记真实 run 结论（含 `cancelled`）；**不得**改历史行迁就判据 |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 **全部 PASS** 且有**实跑证据**（每条含**真标识 + digest** 或
  **先红后绿**的按压证据）+ 独立 RECHECK `PASS` / `PASS_WITH_WARNINGS` + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + **未覆盖范围逐条明写**。
  **未实跑不得记 PASS**；本机无法判定记 PENDING 并停止推进。
  本 GOAL 的收口判词**必须**写明：**① 映射层的落地形态与点名失败证据（两向）**、
  **② 默认装配实跑留档（真标识 + 指标 + 评审判定）**、**③ 第三方 MCP 勘察结论**、
  **④ 台账逐提交的覆盖情况**、**⑤ 未覆盖范围**、**⑥ 下一批可真实现的能力清单**。
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
  ⑤ CI 台账终态（**逐提交**）；⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

**承继：GOAL-026 / 027 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子 `scanner_enobufs` 未得完整结论 | **原样保留**（**不得**据此宣称项目安全） |
| `R26-1` | 死信人工恢复路径不存在（`DEAD_LETTER` 无出边；`ADR-0030` 明文承认） | **原样保留**（实现 = 改 Accepted ADR + 新能力） |
| `R26-2` | 工具面断路器未接通（`tool_plane/health.py` 无产品调用方） | **原样保留 + 注明「需用户拍板」** |
| `R26-3` | 在飞取消信号未接通（`AgentRuntime.cancel` 无产品调用方） | **原样保留 + 注明「需用户拍板」** |
| `R26-4` | 非幂等副作用的补偿未实现（`compensation_actions` 只在文档里） | **原样保留 + 注明「需用户拍板」** |
| `R26-5` | 应用级事件消费者不存在（`consumer_offsets` 是文档独有） | **原样保留 + 注明「需用户拍板」** |
| `R26-6` | HTTP 幂等 store 是节点本地且 `get→call_next→put` 是 check-then-act | **原样保留** |
| `R26-7` | CI 台账的原始证据在树外（`scratch/`，gitignored） | **原样保留**（本 GOAL 沿用同一取证件置放口径） |
| `R26-8` | GOAL 正文的 EC 汇总表不在判词面内 | **原样保留**（本文件按同口径：**表与 frontmatter 同轮同改**） |
| `W-10` / `W-11` / `W-12` | 单 token ⇒ 单主体 / BOLA·BFLA 未做 / 部署面未验证 | **原样保留**（本 GOAL 不碰认证面） |
| `G24-4` / `G24-5` | `LineageNodeDto.label` 语义 / 文档条款非运行时拦截器 | **原样保留 + 注明「需用户拍板」** |
| `W27-1` | 新协议与既有检索协议并存（无机器判据防策略漂移） | **原样保留** |
| `W27-2` | 点分路径只支持单层 | **原样保留** |
| `W27-3` | 性质两向由两个 adapter 分别取证 | **原样保留** |
| `W27-4` | 新协议未重测策略 DENY 面 | **原样保留** |
| `W27-5` | 评审契约不声明性质维度 | **原样保留** |
| `W27-6` | 实验任务不在任务投影（只在 experiment 读面） | **原样保留** |
| 历史遗留 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**脚本加入必备清单） |

**本 GOAL 特有边界（= 用户判词的「明确不做」，命中即 BLOCKED）**：

1. **改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow** —— **不做**；
2. **修改任何既有判据 / 门禁 / 阈值**（**新增**可以）—— **不做**；
3. **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构** —— **不做**（终态行仍是 `23`）；
4. **把任何真实凭据写进源码 / 示例 / 测试 / 记录 / 日志** —— **不做**（只从环境变量 / 密钥服务读）；
5. **未经 pin 的 provider** —— **不做**（`digest` / `resolved_revision` / `license` /
   `network_domains` 先落再登记）；
6. **放开默认网络** —— **不做**（默认 CI 与默认门离线；真实出网仅在显式开关下）；
7. **请求 localhost / 环回 / 私有 / 保留地址** —— **不做**（仅 http/https + 触网前校验 host）；
8. **改动 Canonical State 边界**（向量 / 索引 / 缓存只能是可重建的 derived index）—— **不做**；
9. **读面认证 / 多租户 / RBAC / BOLA·BFLA / `G24-4` / `G24-5`** —— **只登记，需用户拍板**；
10. **新增依赖**（`mcp` 已是依赖）—— **不做**；
11. **真实 runtime / 真实 LLM 出网作为默认** —— **不做**（默认仍 Fake、默认 CI 离线）；
12. **用 skip / xfail 处理取不到的路径** —— **不做**（要么取证，要么登记 PENDING + 理由）；
13. **用「受判集合为空」的空真充当通过** —— **不做**（承 MEM:156）；
14. **把 provider id 直接当 SDK 工具名** —— **不做**（映射必须显式声明；缺映射一律点名失败）；
15. **宣称项目安全**（`R-M1` 仍在）—— **不做**；
16. **宣称 exactly-once**（口径只能是 at-least-once + idempotency + deduplication）—— **不做**。

**本 GOAL 交付的是「默认装配下可跑的科研子迭代链 + 可复跑判据」，不是「科研能力已完备」**：

- 映射层证的是「**生产组合根**能按**显式声明**把 provider 装配成会话工具」，
  **不**证「模型会正确调用它们」——那属会话语义，不在本 GOAL 射程；
- 活检索证的是「**路径存在且语料非预置**」，**不**证「检索质量 / 覆盖面」；
- 第三方 MCP 只给**可行性勘察结论**（可行或不可行 + 理由），**不**证明任何第三方 server
  已可 pin / 已可上线；
- **未覆盖范围（逐条明写；本 GOAL 不消解任何一条）**：

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 配置了外部队列的部署面只在登记面；
5. **R-M1 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称项目安全。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `003a78e`（建档提交，1 文件 = 本文件） | 治理 `validate.py` = `Cursor 治理验证通过`（8 行）；记录面判据 **33 passed in 6.58s**（`egress guard: judged 0 connection attempt(s); blocked 0`）；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAILED [` = 0 / EXIT=0 / **4928 passed / 21 skipped / 106 warnings**，python 段 `in 595.99s`；日志 `scratch/goal028-c0c-m0.log`，记录已写完、独占运行、canonical DSN pin、不接管道、**零进程残留**；**首跑即终态**） | 见下方「CI 台账」（本行结论由后续回填提交补记） | **两处如实登记的取材失误**：① 首跑 m0 的 `RESEARCHOS_POSTGRES_DSN` **端口写错**（写 55432，实际容器映射 **15432**）⇒ 193 条 postgres 用例**静默转 skip**（总数 4949 不变、终态行**仍显示 23/23**），靠与 GOAL-027 基线计数对照（4735 passed vs 4928）发现并改用 canonical DSN 复跑；② 首跑撞 `framework/run_cursor_framework_evals` 的 **`PermissionError WinError 5`**（`evolution_state.json.tmp` 残留）⇒ 按既有 flake 配方单跑取证（`FRAMEWORK EVAL PASS`）后独占复跑，**未改 check** | EC-01…EC-05 全 PENDING。起点已定位：见「事实层结论」22 条，其中**六条**决定 EC 形状：第 **3/4** 条（缺映射今天是**点名失败**、且由既有判据固定 ⇒ 映射必须**声明作用域**）/ 第 **6** 条（出厂 provider id 集被既有判据锁死 ⇒ 活检索不得加出厂 id）/ 第 **10** 条（SDK 自带工具极少 ⇒ 实现须由装配方提供）/ 第 **13** 条（MCP 冻结语料被三份判据钉死 ⇒ 活检索只能**加**路径）/ 第 **16** 条（GOAL-027 台账缺口已用原始 API 复核属实） | cycle 1 = **EC-01**（provider→SDK 声明式映射 + 接进生产组合根 + 点名失败反证两向 + 默认装配实跑） |
| 1 | `PLAN-20261001-267`（EC-01） | `60e0303`（WP-A 声明面）+ `1c5ad78`（WP-B 解释点）+ `50a58c4`（WP-C 实现与组合根）+ `234fb06`（WP-D 判据）+ `cb5c26f`（WP-D2 同源判据）+ 本条回写提交 | 治理 `validate.py` = `Cursor 治理验证通过`；记录面判据 **31 passed**；判据 **13 + 9 passed**；既有判据 `git diff` 为空、连同新判据 **166 passed / 1 skipped**；**按压 P-1 先红后绿 + 逐字节复原**（`session_builder.py` = `00591f58…`、`tool_mapping.py` = `9dbc95b6…`）；ruff / `mypy --strict` / `validate_bundle` 绿；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAILED [` = 0 / EXIT=0 / **4954 passed / 21 skipped / 109 warnings**，python 段 `in 597.05s`；日志 `scratch/goal028-c1c-m0.log`，记录写入后独占运行、canonical DSN pin、不接管道、**零进程残留**） | 见下方「CI 台账」（**逐提交**登记） | **三处判据侧自伤 + 两处规模门超限（全部已修，产品语义未因此改动）**：① 反证二「换实现表」实测 SUCCEEDED（SDK registry **进程级且只增不减**）⇒ 改用**专属名字**；② 反证一**单跑绿、全量 m0 判红**（同根因反向：`map_tools=True` 的判据已把 `openhands_workspace` 注册成惰性替身 ⇒ 「未注册」断言假绿）⇒ 用例内**显式摘除**该名字；③ 协议 fixture 起初只给一个 phase 声明绑定 ⇒ 另一 phase 仍点名失败；④ `_openhands_runtime` 54 行 / `resolve_sessions` 51 行超 50 行门 ⇒ 按仓内形态**抽出小函数**（首版抽出后 mypy 报类型收窄丢失 ⇒ 改为让守卫返回收窄后的二元组）；⑤ `bind_session_tools` 的准入判定从「翻译点查实现表」**移到** SDK registry 的可观测后果（设计更正）。 | EC-01 收口；**残余**：`W-1` 映射目标须装配方提供（默认配置下多 role 协议仍不可跑 = **机制成立 ≠ 出厂即可跑**）/ `W-2` 绑定是 phase 级非全局表 / `W-3` 桥的 policy 拦截由代码路径保证、未单钉 / `W-4` 不支持一 provider 多工具名 / `W-5` 第三方 MCP 未验证（属 EC-02） | cycle 2 = **EC-02**（活检索 + 第三方 MCP 勘察结论） |
| 2 | `PLAN-20261001-269`（EC-02） | `19d52f7`（WP-A 勘察结论 + WP-B 活检索模式）+ `9b53c21`（WP-C 判据）+ 本条回写提交 | 治理 `validate.py` 绿；记录面判据 **19 passed**；新判据 **14 passed**；`tests/contracts` 全量 **1596 passed / 69 skipped**；`tests/tooling` 四道门 **8 passed**；既有三份 MCP 判据 `git diff` 为空；**按压 P-2 先红后绿 + 逐字节复原**（`research_mcp_live.py` = `8049c2a6…`、`research_mcp_server.py` = `c1b8381c…`）；ruff / format / mypy --strict / validate_bundle 绿；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAILED [` = 0 / EXIT=0 / **4969 passed / 21 skipped / 110 warnings**，python 段 `in 680.02s`；日志 `scratch/goal028-c2b-m0.log`，记录写入后独占运行、canonical DSN pin、不接管道、**零进程残留**） | 见下方「CI 台账」（**逐提交**登记） | 首版两处判红（**均已修，判据侧**）：① `tests/contracts/test_mcp_live_retrieval_offline.py` **格式漂移** ⇒ `python/format-check` 判红（`ruff format` 修）；② 协议往返臂直接取 `result.content[0].text` ⇒ mypy `union-attr`（SDK 的 content 是文本/图片/音频/资源链接的联合）⇒ 加 `_text_payload` 按 `type == "text"` 取并如实判错。另首轮一处判据自伤（两模式同形写成全字段相等）已在 WP-C 内改判据侧。 | EC-02 收口；**残余**：`W-1` 活检索的**真实出网**未实跑（只证路径成立）/ `W-2` 默认门看不见子进程出站（对策是开关 + 判据自断言，非守卫）/ `W-3` 限速是进程内语义 / `W-4` 活模式只覆盖既有两个工具名 / `W-5` 第三方结论是**静态判断**（出现满足四条的候选需重做）/ `W-6` 活检索未接进运行链 | cycle 3 = **EC-03**（默认装配上的完整闭环：真标识 + 真 metrics + 评审反证 + 读面四列 + Handoff digest） |
| 3 | `PLAN-20261001-271`（EC-03） | `2849666`（WP-A 协议绑定 + WP-B 判据）+ 本条回写提交 | 治理 `validate.py` 绿；记录面判据 **19 passed**；新判据 **4 passed**（连同既有判据 **32 passed**）；协议改动 **+12 / −0**；**按压 P-3 先红后绿 + 逐字节复原**（`multi_role_research_v1.yaml` = `3134b3c8…`）；ruff / format / mypy --strict / validate_bundle 绿；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24 / `FAILED [` = 0 / EXIT=0 / **4974 passed / 21 skipped / 113 warnings**，python 段 `in 618.78s`；日志 `scratch/goal028-c3b-m0.log`，记录写入后独占运行、canonical DSN pin、不接管道、**零进程残留**） | 见下方「CI 台账」（**逐提交**登记） | **首跑 m0 判红 3 条（`python/tests`）—— 全是我自己 cycle 1 的判据**：它们在 `_UNDECLARED` 清单里钉着「`multi_role_research_v1` 不声明绑定」，而 EC-03 的授权协议改动**正是**给它加绑定 ⇒ 清单与断言同轮**重新分类**（该协议移入 `_BOUND` + 新增 `_EXPECTED_DECLARED` 逐字期望；`_UNDECLARED` 清单缩短，**没有放宽任何断言**，其余三份协议仍钉「未声明 ⇒ 空」）。另：首版只绑三条 ⇒ `europe_pmc` 未绑（run-chain 排除是 **per-phase** 的，实测纠错）。 | EC-03 收口；**残余**：`W-1` 会话工具实现是判据侧惰性桥（出厂仍需装配方接线，承 EC-01 `W-1`）/ `W-2` experiment 的会话工具面不被消费 / `W-3` 惰性桥不驱动模型调工具 / `W-4` 真标识来自离线夹具（非今日可达）/ `W-5` 实验段依赖 Docker | cycle 4 = **EC-04**（台账合并行中间提交不漏记 + 新判据 + 反证两向） |

### CI 台账（逐 run 逐 job 实查；**逐提交**登记 `sha` ↔ run id）

**登记口径（本 GOAL 起适用，含 EC-04 的新判据）**：**每一次推送的每一个提交**都必须在本表里有行；
`total_count=0` 的提交**不得**记 `OK`，必须写「其 run 被同批推送的哪个提交覆盖 + 由谁承担绿」；
`cancelled` 如实登记；**空集合 / 空字段 = 未取证**。

| 推送批 | 提交 | 该提交自带的 run | 结论 |
| --- | --- | --- | --- |
| cycle 0（建档 + 记录回填，一次推送） | `003a78e`（建档：本文件 1 个文件） | **无**（`total_count=0`） | **被同批 `3e05fd6` 的 run 覆盖**（两次提交在同一 `git push` 中上行，GitHub 只为首个触发面之后的 head 建 run）；**由 `3e05fd6` 的绿承担** |
| cycle 0（同上批） | `3e05fd6`（记录回填：本文件 1 个文件） | M0 [`36867097655`](https://github.com/Eswink/research-system-new/actions/runs/36867097655) / Push-on-main [`36867096306`](https://github.com/Eswink/research-system-new/actions/runs/36867096306) | **绿（八 job 全 `success` + CodeQL 3/3 `success`）**，两者 `run_attempt=1`（**一次成功、无 flake**）；原始 JSON 实查（`scratch/goal028-c0b-run-36867097655{,-jobs}.json` / `…-36867096306{,-jobs}.json`）⇒ `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=3e05fd6e1017…` 与推送一致；轮询日志 `scratch/goal028-c0b-ci-poll.log`（`ALL_TERMINAL sha=3e05fd6e1017a3b419a347341c6c67c626b6e632`）。上游 push 回执报 **8 条**依赖告警（6 moderate + 2 low）⇒ **零依赖改动**。 |
| cycle 0 收口（GOAL 台账 + 子 PLAN + ALL_PLAN，3 文件） | `2e2fd3e` | M0 [`36870448644`](https://github.com/Eswink/research-system-new/actions/runs/36870448644) / Push-on-main [`36870447320`](https://github.com/Eswink/research-system-new/actions/runs/36870447320) | **绿（八 job 全 `success` + CodeQL 3/3 `success`）**，两者 `run_attempt=1`；原始 JSON 实查（`scratch/goal028-c0c-run-…`，见轮询日志 `scratch/goal028-c0c-ci-poll.log` 的 `ALL_TERMINAL sha=2e2fd3e0b77e…`）⇒ `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=2e2fd3e0b77e…` 与推送一致。 |
| cycle 1（EC-01：声明面 1 + 解释点 6 + 实现与组合根 6 + 判据 1 + 同源判据 1 + 收口 11） | `60e0303`（WP-A） | **无**（`total_count=0`） | 其 run 被同批 `724b74b` 覆盖；**由 `724b74b` 的绿承担** |
| cycle 1（同上批） | `1c5ad78`（WP-B） | **无**（`total_count=0`） | 同上 |
| cycle 1（同上批） | `50a58c4`（WP-C） | **无**（`total_count=0`） | 同上 |
| cycle 1（同上批） | `234fb06`（WP-D） | **无**（`total_count=0`） | 同上 |
| cycle 1（同上批） | `cb5c26f`（WP-D2） | **无**（`total_count=0`） | 同上 |
| cycle 1（同上批） | `724b74b`（收口） | M0 [`36984630729`](https://github.com/Eswink/research-system-new/actions/runs/36984630729) / Push-on-main [`36984629590`](https://github.com/Eswink/research-system-new/actions/runs/36984629590) | **绿（八 job 全 `success` + CodeQL 3/3 `success`）**，两者 `run_attempt=1`（**一次成功、无 flake**）；原始 JSON 实查（`scratch/goal028-c1-run-36984630729{,-jobs}.json` / `…-36984629590{,-jobs}.json`）⇒ `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=724b74bb5134…` 与推送一致；轮询日志 `scratch/goal028-c1-ci-poll.log`（`ALL_TERMINAL sha=724b74bb5134121bca2c9c99b3de8cc30de52e96`，**44 轮**）。 |

| cycle 2（EC-02：勘察 1 + live 模块 1 + server 1 + 文档 1 + 判据 1 + `IN_SCOPE` 1 + 记录 6） | `19d52f7`（WP-A/WP-B） | **无**（`total_count=0`） | 其 run 被同批 `66e5489` 覆盖；**由 `66e5489` 的绿承担** |
| cycle 2（同上批） | `9b53c21`（WP-C 判据） | **无**（`total_count=0`） | 同上 |
| cycle 2（同上批） | `66e5489`（收口） | M0 [`37086422253`](https://github.com/Eswink/research-system-new/actions/runs/37086422253) / Push-on-main [`37086421530`](https://github.com/Eswink/research-system-new/actions/runs/37086421530) | **绿（八 job 全 `success` + CodeQL 3/3 `success`）**，两者 `run_attempt=1`（**一次成功、无 flake**）；原始 JSON 实查（`scratch/goal028-c2-run-37086422253{,-jobs}.json` / `…-37086421530{,-jobs}.json`）⇒ `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=66e5489665b9…` 与推送一致；轮询日志 `scratch/goal028-c2-ci-poll.log`（`ALL_TERMINAL sha=66e5489665b9487a922abac20cf6a413f2cd6c64`，**47 轮**）。**无 `cancelled`**。逐提交覆盖：前两个 `total_count=0`（同批 head 承担绿），已逐条写明。 |

**cycle 1 批次（6 提交）与 cycle 2 批次（3 提交）的逐提交覆盖情况（EC-04(b) 的口径在本轮自身生效）**：
两批共 **9** 个提交，逐条经 REST API 原始 JSON 复核 —— cycle 1 的前 **5** 个
（`60e0303` / `1c5ad78` / `50a58c4` / `234fb06` / `cb5c26f`）与 cycle 2 的前 **2** 个
（`19d52f7` / `9b53c21`）`total_count=0`，其 run **被同批 head 覆盖**（分别由 `724b74b`
与 `66e5489` 的绿承担）；两个 head 各自自带 M0 + Push-on-main 两个 run，八 job 与
CodeQL 3/3 全 `success`（`run_attempt=1`）。**两批均无 `cancelled`**。
（这正是 GOAL-027 合并行缺口的同一形状 —— 本 GOAL 按新口径**逐条写明覆盖关系**而不是合并成一行。）

本批推送 **6** 个提交，
逐条经 REST API 原始 JSON 复核 —— 前 **5** 个（`60e0303` / `1c5ad78` / `50a58c4` / `234fb06` /
`cb5c26f`）`total_count=0`，其 run **被同批 head `724b74b` 覆盖、由它的绿承担**；
`724b74b` 自带 M0 + Push-on-main 两个 run，八 job 与 CodeQL 3/3 全 `success`（`run_attempt=1`）。
**无 `cancelled`**。（这正是 GOAL-027 合并行缺口的同一形状 —— 本 GOAL 按新口径**逐条写明覆盖关系**
而不是合并成一行。）

**GOAL-027 台账缺口如实补记（EC-04(a)：只追加，不改历史行）**——实测（原始 REST API 复核）：

| 被 GOAL-027 合并行覆盖的提交 | 该提交自带的 run | 实际结论（**与合并行的「无 cancelled」不一致**） |
| --- | --- | --- |
| `6e27a14` | **无**（`total_count=0`） | 其 run 被同批 `93fa7f7` 覆盖；**由 `93fa7f7` 的绿承担** |
| `edd4de8` | **无**（`total_count=0`） | 同上 |
| `a603267` | M0 [`36685047472`](https://github.com/Eswink/research-system-new/actions/runs/36685047472) / Push-on-main [`36685046965`](https://github.com/Eswink/research-system-new/actions/runs/36685046965) | M0 = **`cancelled`**（`run_attempt=1`）；Push-on-main = `success`。⇒ **该行写「无 cancelled」与该提交的实际结论不符**（真正被取消的是 `a603267` 的 M0 作业，而非 `93fa7f7`；`93fa7f7` 的 M0 `36686124759` 确为 `success`）。同批绿由 `93fa7f7` 承担。 |
| `93fa7f7` | M0 [`36686124759`](https://github.com/Eswink/research-system-new/actions/runs/36686124759) / Push-on-main [`36686123873`](https://github.com/Eswink/research-system-new/actions/runs/36686123873) | **绿**（两者 `success`、`run_attempt=1`）—— 合并行记录的正是这一条 |

**为什么 `6e27a14` / `edd4de8` / `a603267` 无自带 run**：三次提交与 `93fa7f7` 在**同一次推送**里上行，
GitHub 只为该批的**最终 head** 建 run（`cancel-in-progress` 语义下的既有行为）⇒ 「无自带 run」
**不等于**「未受门覆盖」，但**必须**在台账里写明「被谁覆盖 + 由谁承担绿」——EC-04(b) 的判据即为此。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | ACTIVE | **cycle 3（EC-03）收口**：把**真实那条**多 role 协议从「只在测试装配（`map_tools=True`）能跑」推进到「**默认装配下跑到 `SUCCEEDED`**」。**① 协议改动 = 纯新增 12 行 / 0 删除**（`git diff --stat` 实测 `1 file changed, 12 insertions(+)`）：只给 `review` phase 加 `session_tool_bindings` 四条（`m12_artifact→artifact.read` / `openhands_workspace→workspace.read` / `ncbi_eutils→literature.search` / `europe_pmc→literature.read`）与注释；phase 的 id / role / 能力 / 契约 / 输出 / 门 / 超时**一字未动**。**② 一处初始误判已按实测纠正（真问题，判据当场抓到）**：首版只绑三条 —— 我以为 review 的工具面不含 `europe_pmc`（它被 scouting 声明为 run-chain），**实测纠错**：run-chain 排除是 **per-phase** 的（`run_chain_tool_ids(plan, phase.id)` 只对**声明了** `run_chain` 的那个 phase 生效）⇒ 在 review 这一相位 `europe_pmc` **仍在会话工具面内**，必须绑定。**③ 判据 4 passed**（`tests/e2e/test_multi_role_on_the_default_assembly.py`），**五件事逐条**：默认装配（`build_agent_runtime` 真实缺省 + `register_session_tools` 注入实现，**非** `map_tools=True`）跑到 `state=SUCCEEDED`、`protocol_id=multi_role_research_v1_0_0`、`manifest_digest` 在场、失败列表**无** `is not registered`；检索 `source_trust_label` 集合 == `{RETRIEVED}` 且含真 PMID（`39284801` / `40601758`）；实验 `image_digest` 在场 + `metrics` 制品在；读面四列（`id` / `source_ref` / `content_digest` / `source_trust_label`）逐条非空；Handoff 三条 `sha256:<64hex>` 且互不相同。**反证臂**：摘掉上游检索接线 ⇒ run `FAILED`、判词点名 `retrieved sources`、工具证据为空（**评审真能判不通过**）。**④ 判据分流（如实登记，不是放宽）**：绑定覆盖断言只对 `strategy: single_agent` 的 phase 成立 —— `experiment` 是 `deterministic` 且合约声明 `experiment: {}` ⇒ 派发按 `phase_runner` 既有语义（`contract.experiment is not None` ⇒ `dispatch_experiment`）**根本不创建会话** ⇒ 其会话工具面**从不被消费**；判据另断言「本协议**恰有一个**带会话面的 phase」以防分流过宽（空真）。**既有判据逐字节未改**（`git diff` 对 `test_multi_role_research_offline` / `test_ec03_real_runtime_offline_chain` / `test_tool_binding_on_the_default_assembly` / `preflight` / `egress_guard` / `run_fixtures` / `test_session_tool_bindings_exposure` 均为空），连同新判据 **10 passed**。**按压 P-3**：从协议删掉 `europe_pmc` 绑定 ⇒ **3 failed**（失败文本正是 `ToolDefinition 'europe_pmc' is not registered`）；恢复后 `sha256sum -c` 逐字节一致（`multi_role_research_v1.yaml` = `3134b3c8…`）且 10 passed。`RECHECK-20261001-272` = **`PASS_WITH_WARNINGS`**（五条 `W-NN`：`W-1` 会话工具实现是判据侧惰性桥 ⇒ **出厂仍需装配方接线**（承 EC-01 `W-1`）/ `W-2` experiment 的会话工具面不被消费 / `W-3` 惰性桥不驱动模型调工具（会话语义不在射程）/ `W-4` 真标识来自离线夹具（非今日可达）/ `W-5` 实验段依赖 Docker）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。下一 cycle = **EC-04**（台账合并行中间提交不漏记）。 |
| 2026-10-01 | ACTIVE | **cycle 2（EC-02）收口**：把自建 MCP server 从「冻结快照」推进到「**另有一条真去取的路**」，并给出第三方 MCP 的勘察结论。**① 第三方 MCP 可行性（限制 ③ 的结论）= 以本仓现有 pin 规则不可行**：逐维给理由与可复核位置 —— 许可（`UPSTREAM_COMPONENTS.yaml` 逐组件登记，`mcp` 条目实测 `spdx: MIT` + `upgrade_gate` 四项，而**仓内没有任何第三方 MCP server 的 qualification 记录**）/ 动态 pin（`ProviderRegistration.pinned_revision` 被 `Digest.parse` 强制 `sha256:<64hex>`，`tool_registry.py:117-121` 注释明写分支名与 tag 一律拒绝 ⇒ git-only 与托管端点给不出制品 digest）/ 静态 pin（toolpack `digest` 是声明值 ⇒ 只对能给出 sdist/wheel/镜像 digest 的**打包型** server 可行）/ 凭据（架构就绪，逐 server 接线与默认门隔离名单未做）/ 稳定性（超时、漂移、健康、错误分类**都已在 adapter 里**）。**② 落地形态 = 自建 server 扩展**：新增 `tools/research_mcp_live.py`（149 行）真打 Europe PMC REST，**复用**既有 `europe_pmc_runtime` 的 `assert_url_allowed`（**触网前**：仅 http(s) + 保留类拒绝 + host ∈ 声明的 `network_domains`）/ `request_document`（429⇒transient、4xx⇒permanent）/ `search_params` 与 `europe_pmc_parsing` 的 `normalize_search` / `ext_id_query`（**不做第二份 HTTP / 解析实现**）；`tools/research_mcp_server.py`（294 行）的 `build_server(live=None)` **缺省不读环境变量、全程冻结语料**，开关 `RESEARCHOS_MCP_LIVE_RETRIEVAL=1` 才启用，且按**路径**加载 live 模块（`tools/` 不是包 ⇒ 静态导入会让同一文件有两个模块身份，mypy 实测判红）。**③ 判据 14 passed**（`tests/contracts/test_mcp_live_retrieval_offline.py`，298 行）：**非预置语料正反两向**（专属 PMID `99000001` **不在** `CORPUS` 里 → 活模式真取回该条且内容寻址 digest **重算相等**；冻结模式下同一 id 落 `missing` 被**点名**）+ **两模式同形**（字段集与冻结语料逐字相同）+ **触网前策略零请求**（声明外 host / 空声明 ⇒ 拒绝且 `settings.requests == []`，判词含 `declared network_domains`）+ **正控制**（合法 host ⇒ 请求真发出，防零请求空真）+ **默认仍离线**（未开关 ⇒ `_live_settings()` 返回 `None` 不构造 client；`true`/`yes`/`0`/`''` 一律不启用）+ **协议往返**（SDK in-memory 会话起**活模式** server，真握手 + 真 `call_tool` ⇒ 工具面与冻结模式**逐字相同**）。**既有三份 MCP 判据逐字节未改且全绿**（`tests/contracts` 全量 **1596 passed / 69 skipped**）；`IN_SCOPE` **纯追加**一条；`tests/tooling` 四道门 **8 passed**。**按压 P-2**：架空 live 模式的触网前策略 ⇒ 两条零请求判据 **2 failed**；恢复后 `sha256sum -c` 逐字节一致（`research_mcp_live.py` = `8049c2a6…`、`research_mcp_server.py` = `c1b8381c…`）且 14 passed。`RECHECK-20261001-270` = **`PASS_WITH_WARNINGS`**（六条 `W-NN`，**尤以 `W-1`**：活检索的**真实出网未实跑**（本机 DNS 走 fake-IP 代理 + 默认门必须离线）⇒ **证的是路径成立，不是「今天上游可达」**；`W-2`：`egress_guard` 射程**不含子进程** ⇒ stdio server 的出站不在守卫内，对策是显式开关 + 判据自断言而**不是守卫**；`W-6`：活检索**未接进运行链**）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。下一 cycle = **EC-03**（默认装配上的完整闭环）。 |
| 2026-10-01 | ACTIVE | **cycle 1（EC-01）收口**：把 provider→SDK 工具映射从「测试侧恒等替身」推进到「**显式声明 + 生产组合根消费**」。**落地形态 = 声明化分离**（照 `CapabilityExecution.RUN_CHAIN` 的先例）：域内 `SessionToolBinding`（**纯字符串**，OpenHands 类型不进 Domain）→ loader 只读不解释（缺省空 ⇒ 既有语义逐字节不变）→ 编译器原样透传 → `session_resolution` 是**唯一解释点**（`session_tool_face` / `session_tool_bindings`，越界与一 provider 两名字各自**点名**）→ adapter `bind_session_tools`（缺声明逐字返回；位置保持替换；不增减工具数）→ `register_tools` 注册面 + `BoundSessionTool` 真实实现（`session_tools.py`）→ 调用桥 `session_tool_invocation.py` 复用**同一个** `execute_tool_call` 走策略+执行门（参数经 `tool-args` 制品 + `argument_digest` 重算，与运行链 / REST / MCP 同口径）。**生产组合根**：`build_agent_runtime(..., register_session_tools=)`（缺省 `None` ⇒ 生产行为逐字不变），复用**既有** `AdapterDependencies.register_tools`（此前全仓零调用方的死缝），**未新增字段**。**判据**：`tests/e2e/test_tool_binding_on_the_default_assembly.py`（292 行，**13 passed**）+ `tests/architecture/python/test_session_tool_bindings_exposure.py`（**9 passed**）+ 三份成对协议（完整 / 只少一条 / 绑到未实现名，差别只有声明行 ⇒ 失败可归因）。**默认装配实跑**：走 `build_agent_runtime` 的真实缺省（**非** `map_tools=True`），run 到 `SUCCEEDED`、`protocol_id=tool_binding_research_v1_0_0`、mock 端点被真实驱动。**两向点名失败（原文）**：删一条绑定 ⇒ `ToolDefinition 'openhands_workspace' is not registered`；绑到未实现名 ⇒ `ToolDefinition 'workspace.read.unwired' is not registered`；**两向的 mock 端点请求数均为 0**（失败在任何 LLM 调用之前）。**既有判据逐字节未改**（`git diff` 对 `test_ec03_real_runtime_offline_chain` / `test_multi_role_research_offline` / `test_run_chain_capability_exposure` / `tests/application/run_orchestration` / `preflight` / `run_fixtures` / `egress_guard` 均为空），连同新判据 **105 passed / 1 skipped**。**按压 P-1**：架空绑定翻译 ⇒ 三条主判据 3 failed（点名的正是 provider id）；恢复后 `sha256sum -c` 逐字节一致（`session_builder.py` = `00591f58…`、`tool_mapping.py` = `9dbc95b6…`）且 13 passed。**三处判据侧自伤已如实处置**（产品代码未因此改动）：① 反证二起初「换实现表 + 复用 `workspace.read`」实测 SUCCEEDED —— 根因是 **SDK registry 进程级且只增不减**（`register_tool` 无撤销入口）⇒ 断言依赖用例顺序；改用**专属名字** `workspace.read.unwired`，单跑与合跑均已复验；该教训沉淀为 `MEM-20261001-180`。② 协议 fixture 起初只给一个 phase 声明绑定 ⇒ 另一 phase 仍点名失败。③ 示例协议误留占位键 ⇒ `validate_bundle` schema 判红。**设计更正**：`bind_session_tools` 起初在翻译点判「实现是否存在」，但注册发生在翻译**之后** ⇒ 判定会与事实分叉；改为只判「绑定是否落在会话工具面内」，准入由 **SDK registry 的可观测后果**承担。`RECHECK-20261001-268` = **`PASS_WITH_WARNINGS`**（五条 `W-NN` 如实登记，**尤以 `W-1`**：映射目标须由装配方提供 ⇒ 默认配置下多 role 协议仍不可跑，**本 EC 证的是机制成立，不是出厂即可跑**）。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。下一 cycle = **EC-02**（活检索 + 第三方 MCP 勘察结论）。 |

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | ACTIVE | **建档**：用户会话指令（goal 模式）授权**把科研子迭代从「测试里成立」推进到「默认装配下成立」**（收 GOAL-027 的三条硬限制），并授权本驱动自动化循环推进、无需逐轮确认。五 EC 设计（映射层 / 活检索 / 默认装配闭环 / 台账逐提交 / 自举收口），budget = 20 / 120 / 2。**建档当日实测 22 条事实层结论**，其中六条决定 EC 形状：**① 生产装配今天不注册任何 SDK 工具**（`register_tools` 缺省 `None` ⇒ 空操作），会话工具名字面就是 **provider id**（`Tool(name=<provider id>)`）；**② 缺映射的当前行为是「点名失败」而不是静默丢工具**（SDK `KeyError: ToolDefinition '<id>' is not registered` ⇒ `PermanentPortError`，且**发生在任何 LLM 调用之前**），该行为由既有判据固定；**③ 因此映射必须是声明作用域的**（全局注册会让既有判据判红 ⇒ 等于修改既有判据）；**④ 出厂 provider id 集被既有判据锁死**（⇒ 活检索不得新增出厂 id，只能扩自建 server 与运行期注册面）；**⑤ SDK 自带工具极少**（`finish`/`think`/`invoke_skill`/`switch_llm`/`vision_inspect`；`terminal`/`file_editor`/`task_tracker` 属未安装的 `openhands-tools`）⇒ 映射目标必须由装配方提供实现；**⑥ GOAL-027 台账缺口属实**（原始 API 复核：`a603267` 的 M0 `36685047472` = **cancelled**；`6e27a14`/`edd4de8` `total_count=0`；合并行却写「无 cancelled」）。**建档时零产品代码改动**（只增本文件）；工作树另有 4 个**与本 GOAL 无关**的并发改动与 1 个未跟踪文件，本 GOAL 一律只用**显式路径**提交。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）；**不得**据此宣称项目安全，**不得**宣称 exactly-once（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
