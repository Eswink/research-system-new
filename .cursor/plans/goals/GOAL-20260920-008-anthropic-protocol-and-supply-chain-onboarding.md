---
id: GOAL-20260920-008
slug: anthropic-protocol-and-supply-chain-onboarding
title: 真实供应链接入：anthropic 协议执行路径、模型参数落库、供应链登记与首次真实 run（live-gated）
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-20 用户会话指令（goal 模式）：**新建 GOAL-20260920-008（真实供应链接入）**并授权本
    驱动**自动化循环推进、无需逐轮确认**。四段授权原文如下：
    (1) **真实供应链接入授权**：用户登记一个真实端点与模型（**anthropic 兼容型**，
    `base_url = https://apihub.agnes-ai.com`，模型名 `agnes-2.5-flash`），并授权**一次
    live-gated 真实 run**（最小必要次数；不跑压力/批量、不做模型对比）。协议口径：该端点按
    anthropic 兼容型声明（域内 `LLMEndpoint.protocol` 既有合法值 `ANTHROPIC`）。
    (2) **模型参数口径（用户已声明）**：**上下文窗口 512000 tokens**、**思考强度 Max**；
    必须在文档/读面**如实记录**或**如实登记为不支持**——不得静默丢弃、不得伪称已生效。
    (3) **凭据纪律**：key **只从环境变量或 Credential boundary 读取**（由用户注入）；
    **不得**写入仓库、数据库、CI、记录、日志或提示词，不得回显；**本循环不得索取明文**；
    环境无凭据时，live-gated 路径 **skip 并如实记录，不得伪造**。
    (4) **默认 runtime 保持 Fake、默认 CI 离线**（AGENTS.md §11）；真实 runtime 仅**显式配置
    + policy 允许**时启用，两者缺一即拒绝（fail-closed 姿态不得放松，AGENTS.md §9）；
    **push-to-main-for-CI 授权**沿用 GOAL-001…007 的批准口径：**只推 main、不 force、不重写
    历史、不推旁支触发 CI**；push 前 `git pull --ff-only origin main`（必要时 --rebase，不 force）。
    循环预算与纪律以本文件 frontmatter 为准（客户端自带的迭代/重试/超时上限一律让位于此）。
    GOAL-001…007 全部**只读**（001/002/004/005/006/007 ACHIEVED、003 BLOCKED），本 GOAL 不修改
    它们；如需指名只允许按只追加补一行事实更正（当前不需要）。
objective: >
  把「域里声明了 `protocol: ANTHROPIC` 但没有任何执行路径能跑它」这条**已登记却未收口的边界**
  变成**有终态结论的事实**：`protocol` 从「只被持久化/摘要/DTO 读取的字符串」变成**真正的执行
  选路面**（relay 网关与 OpenHands `llm_factory` 按协议分派，未知协议 fail-closed）；用户声明的
  **模型参数**（上下文窗口 512000、思考强度 Max）有**承载字段 + 契约 + 往返 + 读面 + 快照**，
  缺失即判红而**不静默丢弃**；真实端点与模型**登记入库**且**凭据纪律可反证**（仓库/DB/记录/日志
  无明文凭据），凭据「重启后失效」的**诚实边界**写进读面与文档；在**显式配置 + policy 允许**的
  **live-gated** 路径上跑**一次**真实 run 到终态并记录**运行时指纹**（AGENTS.md §4：结论口径
  =「可重复配置」，**不得**声称「完全模型可复现」）；漂移可见性（返回 model 名 vs 声明值）进读面；
  登记步骤、凭据注入与轮换、Fake↔真实切换与回退、以及「**哪些面仍是 demo**」的清单进 runbook。
  **全程不删测试、不改门禁、不以「未观测到失败」或「扫描没报问题」充当 PASS；不引入新依赖、
  不改上游 pin、不自行修改 Accepted ADR / 核心安全策略 / Canonical State 边界、不把真实 runtime
  设为默认 —— 触及即 BLOCKED。环境无凭据时 live-gated 路径如实 skip 并登记为残余，不伪造。**
exit_criteria:
  - id: EC-01
    criterion: >-
      **ANTHROPIC 协议执行路径（二选一终态，本 GOAL 采取 (a) 实现）**：
      (a) relay 网关与 OpenHands `llm_factory` **按 `endpoint.protocol` 选路**——`ANTHROPIC`
      走 Anthropic Messages 形态（请求体 / 响应解析 / 鉴权头按该形态），`OPENAI_COMPATIBLE`
      保持现有 `api_style` 分派**行为不变**，**未知协议 fail-closed**（拒绝且不发起出站调用）；
      **判据含反证**：`protocol=ANTHROPIC` ⇒ 走该路由，**不再无条件加 `openai/` 前缀**。
      (b) 若实测该端点提供 OpenAI 兼容面并决定按 `OPENAI_COMPATIBLE` 登记——须**如实记录实测
      证据与选择理由**，并把「anthropic 执行路径缺失」作为**一等缺口**写进读面与文档**同源收敛**。
      **不得停在「域里声明了但跑不通」。**
    verify: >-
      结构判据（分派点**按 `protocol` 而非其他字段**裁决；未知协议分支**拒绝**；全仓 `openai/`
      前缀构造点只出现在**按协议的有条件分支内**）+ mock 传输层用例（`ANTHROPIC` 端点收到
      **Messages 形态**请求且响应可解析回既有返回值；`OPENAI_COMPATIBLE` 端点收到的
      chat/completions 形态与响应解析**与改动前一致**）+ 未知协议用例（**拒绝并点名** +
      **出站调用 0**，用可观测传输层计数器证明）+ **反证**（把分派短路回无条件 `openai/` 前缀
      ⇒ 对应用例红，先红后复原）+ 受影响套件 + m0 绿。
    status: PASS
    evidence: >-
      PLAN-20260920-114 / RECHECK-20260920-114（PASS_WITH_WARNINGS，W-1…W-9）。终态 **(a) 实现**。
      交付：域枚举 `LLMProtocol`（唯一词表，`LLMEndpoint.__post_init__` 按它校验，**接受集合与错误
      文本未变**）；`adapters/relay/protocols.py`（`select_wire_shape` 唯一分派点 + `request_headers`
      按协议构造鉴权头 + `ANTHROPIC_VERSION`）；`adapters/relay/anthropic_api.py`（Messages 形态
      请求构造与响应解析）；`complete_any` 经 `select_wire_shape` 分派、新增 `_complete_anthropic`；
      `transport.request_with_retries(headers=…)`（None 时既有默认头**逐字不变**）；
      `gateway.list_models` 走协议头；`CompletionRequest.max_tokens`（可选）+
      `suite.probe_max_tokens`（**只对 ANTHROPIC** 给 probe 常量 256，OpenAI 形态仍不发该键）；
      `resolve_runtime_model_name(*, protocol)` ⇒ `ANTHROPIC` 取 `anthropic/` 前缀，
      `OPENAI_COMPATIBLE` 取值不变，未知协议 `ValueError`。
      **判据**：`tests/adapters/relay/test_anthropic_messages.py`（14：路径 `/messages`、
      `x-api-key` 有而 `authorization` 无、`max_tokens`、`content[]` 合并、`tool_use` ⇒ ToolCallDraft、
      `system_fingerprint is None`、usage 缺失不伪造）+ `TestOpenAiShapeRegression`（chat 形态不变且
      **无 `max_tokens` 键**）+ `TestFailClosed` 4 条**记录型 transport 证明 `seen == []`**
      （未知协议 / 缺 `max_tokens` / `stream=True` / `response_format`）+
      `tests/architecture/python/test_protocol_vocabulary.py`（3：schema enum == DTO Literal ==
      `LLMProtocol`；执行侧 AST **零协议字面量**）+ `tests/adapters/openhands/test_llm_relay.py::
      TestProtocolPrefix`（5）+ `tests/application/test_probe_protocol_requests.py`（3，记录真实
      `CompletionRequest` 证明 probe 常量只发给 ANTHROPIC）。
      **反证三条先红后复原**：F1 前缀分支短路 ⇒ 2 failed；F2 Messages 分派短路 ⇒ 与 F1 合并 9 failed
      （失败日志显示请求落到 `/chat/completions`，即分派本身）；F3 未知协议静默回退 ⇒ 2 failed
      （`DID NOT RAISE`），复原后同命令 **168 passed**。
      **m0 本轮真拦下四处缺陷并按缺陷修**：`python/format-check`（3 文件）、`python/typecheck`
      （7 错误，含布尔量收窄 token 求和不被 mypy 跟随）、**50 行函数门**（`request_with_retries`
      涨到 57 行 ⇒ 抽出 `_execute_request`/`_default_headers`，控制流不变）、`framework/validate_bundle`
      （本地工具里的 TEST-NET-1 网段字面量命中旧版本号正则 ⇒ 改成「显式网段 + 地址分类兜底」，**反更严**）。
      文档同源：`docs/integration/LLM_ENDPOINTS.md` §1 协议表 + 缺口登记、`MODEL_GATEWAY.md` §3、
      `gateway.py` 不再自称 OpenAI-only。门禁：定向 **168 passed** + probe 判据 3 passed +
      **m0 PASS: profile=m0; 23 deterministic checks（4072 passed / 11 skipped）** + 治理 `validate.py` 绿。
       **W**：W-1 真实端点面**未实测**（本机无凭据 ⇒ 不对真实端点发任何调用；「该端点是否真在
      `{base_url}/messages` 提供 Messages 面」仍未验证，属 EC-03/EC-04 live 分支）；
      W-2 流式未实现（点名拒绝，probe 记为 capability failure 且**不写 SUPPORTED**）；
      W-3 `response_format` 无对应参数（同样拒绝）；W-4 `max_tokens` 在 Messages 形态变必填而
      **产品侧暂无调用方**（agent 真实运行走 SDK/litellm，不经此路径）；W-5 `system_fingerprint`
      恒 `None` ⇒ 该端点 `SYSTEM_FINGERPRINT` 能力将永远观测不到（漂移可见性覆盖缺口，EC-05 只能靠
      `returned model name`）；W-6 示例端点**仍未入库**（属 EC-03）；W-7 上游历史记录
      `M5_CORRECTIONS_LOG.md` 未追改；W-8 域值名含厂商词是**既有取值**（本轮前就已被接受），
      EC-02 的厂商中立约束针对新增字段；W-9 `tool_use.input` 非 dict 无用例。
  - id: EC-02
    criterion: >-
      **模型参数落库**：上下文窗口（**512000 tokens**）与思考强度（**Max**）在域实体上有
      **承载字段**（**厂商中立命名**，不得出现模型厂商名，AGENTS.md §1）+ 契约 schema +
      **配置面往返**（写 ⇒ 读，两值可判）+ 读面（DTO/API 响应**可见**）+ OpenAPI 快照同步 +
      web 类型/渲染；**反证：缺字段 ⇒ 用例红**（**禁止静默丢弃**）。
    verify: >-
      往返用例（两值写入后读出可判；**旧行缺键**时解码走**向后兼容**路径——不得因新字段
      让既有数据读不出）+ 契约 schema 校验用例 + 读面字段断言（API 响应含两值；**页面有渲染
      分支**，不是「只在 `types.ts` 里存在」）+ OpenAPI 快照 drift 门绿 + **反证**（摘掉字段/
      摘掉映射 ⇒ 对应用例红，先红后复原）+ 受影响套件 + m0 绿。
    status: PASS
    evidence: >-
      RECHECK-20260920-115 = PASS_WITH_WARNINGS（PLAN-20260920-115，子 PLAN 已 DONE）。
      落点与判据：`ModelDefinition` 加两个**可选**声明字段 `context_window_tokens`（int ≥ 1）
      与 `thinking_intensity`（新域枚举 `ThinkingIntensity` = MINIMAL/LOW/MEDIUM/HIGH/MAX，
      **厂商中立级别词**，用户声明的 "Max" 落为 `MAX`）；契约 `schemas/model-definition.schema.json`
      声明两属性（`additionalProperties: false` ⇒ 不声明就写不进去）；加载器 `load_models` 读取
      两字段并把强度经枚举转换（未知级别拒绝而非存下）；配置面 `SqliteModelStore` 的 JSON blob
      承载两字段且**缺键旧行解码为 `None` 不抛**（无 DDL——配置面没有列可加，也**未**新建 PG 表）；
      读面 = API 三 DTO（create/update/read）+ `model_read_dto` + 路由 create/PATCH 构造与重建 +
      probe 合并重建 + OpenAPI 快照重生成（**+91 行**，drift 门绿）+ web `types.ts` + 详情面板
      `model-declared-parameters` + 目录表「参数声明」列；`model_version` 摘要纳入两字段
      ⇒ 只改这两个字段的 PATCH **会改变 ETag**（否则 If-Match 的丢失更新保护对它们失效）。
      反证 11 条（先红后复原）：摘字段（域 5 red）/ 摘 schema 属性（加载器 2 red）/
      摘 create 构造（2 red）/ 摘 probe 合并重建（1 red）/ 摘 `model_version` 两键（1 red，
      ETag 不变）/ 摘 `types.ts` 两字段（`tsc` 11 处）/ 去掉页面挂载（e2e 3 red）/
      PG 分支各建一个 store（装配判据 1 red）/ `PostgresAssembly` 不带 store（1+2 red）/
      `model_store=None`（2 red）/ 迁移里建 `models` 表（1 red）。
      **两组合根共用同一配置面**有两条独立判据：AST（`assemble` 只构造 1 个实例、PG 根从 `config`
      取同一实例）+ PG 根**运行期**（`build_postgres_assembly` → `build_postgres_apideps`，
      POST/GET/PATCH 两值可判）。门禁：定向 56 + PG 5 + web unit 76 passed；`mypy` 949 files；
      **m0 全量 23/23 PASS**（4097 passed / 11 skipped，冻结树 `40fe55d`；其后仅一段文档改动，
      docs 三门单独复跑绿）。诚实边界（W-1…W-7）：**两值只是声明，不发送给 provider、
      不参与 eligibility/capability/预算**（读面 en+zh 文案与三份文档四处同源）；
      OpenHands 侧未接线（运行时读不到）；`types.ts` 与 OpenAPI 快照**没有**自动比对门
      （耦合来自 `tsc`）；设计对照门对该分支**不可见**（默认替身无 `GET /models`，该路由渲染
      错误态 ⇒ 像素/结构基线零 diff），新分支由自带 stub spec 覆盖（MEM-20260920-088）。
  - id: EC-03
    criterion: >-
      **供应链登记与凭据纪律**：端点与模型**登记入库**（DB 行，配置面 `llm_endpoints` /
      `models`）；端点 **URL 策略语义保持**（https 公网放行；localhost / 环回 / 私有 / 保留
      地址**一律拒绝**，复用既有 `validate_endpoint_url` / `EndpointUrlPolicy`，不新造第二套）；
      仓库 / DB / 记录（`.cursor/plans/**`）/ 日志中**无明文凭据**（grep 反证）；凭据只来自
      **环境变量或 Credential boundary**，且「**重启后凭据失效**」的诚实边界写进 UI/文档
      （**不伪装 Secret Manager**）；端点健康探针在无凭据环境**如实 skip**（不记 PASS、不伪造）。
    verify: >-
      DB 行存在判据（只读查询配置面，端点 + 模型两行可判）+ URL 策略用例（放行 https 公网 /
      逐个拒绝 localhost、环回、私有、保留；被拒时**出站 0**）+ **明文凭据 grep 反证**（扫描
      仓库跟踪文件、`.cursor/plans/**` 记录、DB 文件与日志，命中即可用凭据形态 ⇒ 判红）+
      凭据边界文案**同源**（UI/文档/代码同一口径）+ live-gated 健康探针在无凭据环境**如实
      skip** 并登记 + m0 绿。
    status: PENDING
    evidence: ""
  - id: EC-04
    criterion: >-
      **首次真实 run（live-gated）**：`RESEARCHOS_AGENT_RUNTIME=openhands` + 该端点 +
      `agnes-2.5-flash` 跑**一次真实 run 到终态**；记录**运行时指纹**（endpoint 配置摘要、
      返回的 model 名、白名单响应头、probe 套件版本、usage 归账到 `BudgetLedger`、制品与证据
      落 canonical）；结论口径 =「**可重复配置**」，**不得**声称「完全模型可复现」（AGENTS.md §4）。
      **环境无凭据时 skip 并如实记录，不得伪造。**
    verify: >-
      live-gated 用例/脚本在**无凭据环境如实 skip**（记录 skip 事实，**不记 PASS**）；有凭据时
      产出 run 记录 + 指纹字段可判 + usage 归账（`MODEL_TOKENS` 正向且归因正确）+ 制品/证据
      可读；离线可判部分：**门控存在性**（默认门离线可跑、无网络依赖）+ 结论口径文案同源
      （全仓不得出现把该 run 描述为「完全可复现」的措辞）+ **反证**（把 skip 伪造成 PASS ⇒
      判据红）+ m0 绿。
    status: PENDING
    evidence: ""
  - id: EC-05
    criterion: >-
      **漂移可见性**：probe suite 对该端点跑**一次**，**返回 model 名与声明值对比**、漂移状态
      进**读面**（当前 vs 基线）；无凭据 ⇒ **skip 并如实记录**（不伪装成「无漂移」）。
    verify: >-
      离线可判部分：漂移比较的判据用例（返回名 == 声明值 ⇒ 无漂移；不同 ⇒ **点名差异**；
      字段缺失 ⇒ 判「未知」而非「无漂移」）+ 读面字段/渲染分支断言 + **反证**（去掉比较 ⇒
      用例红）；live-gated 实跑（凭据就位时）或**如实 skip** 登记 + m0 绿。
    status: PENDING
    evidence: ""
  - id: EC-06
    criterion: >-
      **文档与 runbook**：登记步骤（**DB 路径与 YAML 路径**、凭据注入与**轮换**、**重启后重输
      的边界**）、**Fake↔真实切换与回退**、以及「**哪些面仍是 demo**」的清单；
      `docs/INDEX.md` 登记该文档。
    verify: >-
      文档存在且**与代码同源**（其中每个变量名 / 路径 / 命令在代码里**真实存在**——引用不存在的
      字段或变量 ⇒ 判据红）+ DOCS-CHECK 绿 + `docs/INDEX.md` 有对应行 + 上述四类内容逐项可判
      （缺任一项 ⇒ 判据红）+ m0 绿。
    status: PENDING
    evidence: ""
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的解析/传输库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 威胁建模/授权面（BOLA/BFLA）覆盖类决策——需用户或 ADR 拍板，本循环不得自行决定
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，需用户或 ADR 拍板
  - ADR-0031（`tool_pack.*`，Status: Proposed）是否采纳——归用户
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；本循环只做「显式配置才启用」）
  - 新增依赖或改动既有依赖 pin（含为 anthropic 形态引入 SDK——优先用手写 HTTP，见 EC-01 判定细则）
child_plans:
  - .cursor/plans/tasks/PLAN-20260920-114-anthropic-protocol-execution-path.md
  - .cursor/plans/tasks/PLAN-20260920-115-model-parameter-persistence.md
  - .cursor/plans/tasks/PLAN-20260920-116-supply-chain-registration-and-credential-discipline.md
  - .cursor/plans/tasks/PLAN-20260920-117-model-drift-visibility-three-states.md
  - .cursor/plans/tasks/PLAN-20260920-118-first-live-gated-real-run.md
  - .cursor/plans/tasks/PLAN-20260920-119-live-model-runbook.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-119-live-model-runbook.md
memory_entries:
  - MEM-20260920-087
  - MEM-20260920-088
  - MEM-20260920-089
  - MEM-20260920-090
  - MEM-20260920-091
  - MEM-20260920-092
---

# GOAL-20260920-008 — 真实供应链接入（自迭代循环）

本文件是 **GOAL 记录**（位于 `PLAN-*` 之上的编排层），格式契约见本目录 `README.md`；
工程事实、验收与复检仍由 PLAN/RECHECK/MEM 体系承载（单一流程权威：
`.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账。

## 目标与退出标准

GOAL-007 收口（ACHIEVED）时把「仍未处理的长程项」如实登记进「终止与收口 · 收口结论」，
其中第 7 项写着：**真实端点路径与 live 分支**（门控与离线全链已成立，真端点从未跑过）。
本 GOAL 承接该项，并新增两条用户显式授权的面：**anthropic 协议执行路径**与**模型参数落库**。

**用户已显式授权的边界**（见 frontmatter `authorization.ref`）：真实端点与模型登记
（`https://apihub.agnes-ai.com` / `agnes-2.5-flash`）、**一次** live-gated 真实 run、
模型参数口径（上下文窗口 512000、思考强度 Max）、凭据只从环境读取且不得回显。
**不在授权内**：把真实 runtime 设为默认、引入新依赖、改 Accepted ADR、改 Canonical State 边界。

| EC | 主题 | 来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | ANTHROPIC 协议执行路径（按 `endpoint.protocol` 选路；未知协议 fail-closed；反证：不再无条件 `openai/` 前缀） | GOAL-007 残余第 7 项 + 用户授权 (1) | **PASS**（RECHECK-20260920-114，W-1…W-9） |
| EC-02 | 模型参数落库（上下文窗口 512000 + 思考强度 Max 有承载字段、契约、往返、读面、快照；缺字段即红） | 用户授权 (2) + AGENTS.md §1/§4 | **PASS**（RECHECK-20260920-115，W-1…W-7） |
| EC-03 | 供应链登记与凭据纪律（端点/模型入库；URL 策略放行 https 公网、拒绝本地/私有；明文凭据 grep 反证；重启失效边界如实披露） | 用户授权 (1)(3) + AGENTS.md §9 | **PASS**（RECHECK-20260920-116，W-1…W-7） |
| EC-04 | 首次真实 run（live-gated：该端点 + `agnes-2.5-flash` 跑到终态；指纹/归账/制品/证据；口径=可重复配置；无凭据则如实 skip） | 用户授权 (1)(3) + AGENTS.md §4 | **PASS（离线判据全绿；live 分支如实 skip —— 真实 run 未发生，见 RECHECK-118 W-1）** |
| EC-05 | 漂移可见性（probe 返回 model 名 vs 声明值对比，漂移状态进读面；无凭据则如实 skip） | 用户授权 (1) + AGENTS.md §4 | **PASS**（RECHECK-20260920-117，W-1…W-6；live 分支如实 skip） |
| EC-06 | 文档与 runbook（登记步骤 / 凭据注入与轮换 / 重启重输边界 / Fake↔真实切换与回退 / 「哪些面仍是 demo」清单 + `docs/INDEX.md`） | 用户授权 (2)(3) + AGENTS.md §14 | **PASS** |

**优先级**：EC-01 → EC-02 → EC-03 → EC-05 → EC-04 → EC-06（derive 取 EC 表首个 PENDING；
若某 EC 本轮**部分交付**，其「下一轮输入」优先于表序）。EC-04 / EC-05 的 live 分支依赖
**凭据就位**（用户注入），不阻塞离线部分推进；**凭据缺失不是 BLOCKED 理由**，而是如实登记的
残余（frontmatter 授权 (3) 明文允许 skip）。

**不在本 GOAL 的 EC 内**（登记为背景，不伪装成已收口）：ADR-0031 是否采纳、
威胁建模/授权面（BOLA/BFLA）覆盖、`artifacts/` 明文 token 清理、450 行贴线文件、
依赖 pin 升级、hook 侧 L3 门 —— 见「不进入循环 / 需人工拍板」节。这些**不因本 GOAL 存在
而被宣称已解决**。

### 建档时已探明的现状（事实类，用于判定起点；不当作验收依据）

以下由**只读勘察**在 2026-09-20 建档时确认（路径 + 行号可复核）：

1. **`protocol` 是死的**：`LLMEndpoint.protocol`（`packages/domain/models.py:37`，`str`，无默认）
   在 `__post_init__`（`:51-52`）被校验为 `OPENAI_COMPATIBLE` 或 `ANTHROPIC`，**但没有任何
   执行路径读它做分派**——全部引用都是持久化 / 摘要 / DTO：`model_relay/fingerprint.py:38`、
   `adapters/relay/endpoint_store.py:85,122`、`adapters/sqlite/endpoint_store.py:103,135`、
   `services/api/mappers/endpoints.py:30,71`、`routers/llm_endpoints.py:104,151`。
   仓库里**不存在** `EndpointProtocol` / `LLMProtocol` 之类的枚举。
2. **实际的分派键是 `api_style`**：`adapters/relay/completions.py:29-43` 按
   `endpoint.api_style` 选 `chat_completions`（`POST {base_url}/chat/completions`）或
   `responses`（`POST {base_url}/responses`）。**不存在任何 anthropic 形态的调用路径**
   （全仓无 `messages.create`、无 `anthropic` 包依赖；`ANTHROPIC` 在非测试代码里只出现在
   值校验与 DTO Literal）。
3. **`openai/` 前缀只有一处，且是无条件的兜底**：`adapters/openhands/llm_factory.py:20-32`
   `resolve_runtime_model_name()`——`:27-28` 已带 `/` 的名字直通，否则经
   `LLMProvider.from_model` 取 provider 名，**取不到就 `f"openai/{model_name}"`**（`:31`）。
   这是 `LLM(` 的唯一非测试构造点（`llm_factory.py:51-58`，不读 `endpoint.protocol`）。
4. **示例配置里已经有一条跑不通的 ANTHROPIC 端点**：`examples/config/llm_endpoints.yaml:20-28`
   的 `agnes-anthropic`（`protocol: ANTHROPIC`、同一 `base_url`）——声明合法、**执行必败**
   （走的是 chat/completions 形态 + `openai/` 前缀）。
5. **没有任何字段承载「上下文窗口」或「思考强度」**：`context_window` 只存在于前端 mock
   （`apps/web/src/features/example-console/reference/endpoints-screen/EndpointsSection.tsx:57`）
   与设计参考稿；`max_context_tokens` 只存在于 **agent 侧** `AgentContextConfig`
   （`packages/domain/roles.py:74`），**不在** `ModelDefinition` / `ModelProfile` /
   `LLMEndpoint` / `ModelRuntimeFingerprint` 上；`reasoning_effort` / `reasoning_level` /
   `thinking_budget` **全仓 0 命中**（`ModelCapability.REASONING` 是**布尔能力**不是强度）。
6. **`ModelCompatibilityProfile`（AGENTS.md §1 列在 Domain 里）在代码中不存在**：无类、无
   schema、无 loader，只出现在散文清单（`AGENTS.md:26`、`docs/architecture/DOMAIN_MODEL.md:192`
   等）。当前由 `ModelProfile.hard_capabilities` + `eligibility.py` 承担其描述的角色。
7. **配置面是 SQLite JSON blob，且 PG 路径也走它**：`adapters/sqlite/endpoint_store.py:24-30`
   （`llm_endpoints(endpoint_id, endpoint_json, created_at)`）与 `model_store.py:22-28`
   （`models(model_id, model_json, created_at)`）；**没有任何 PG 表**承载端点/模型，
   `services/api/pg_composition.py:214-220,263-264` 明确配置面仍用 SQLite 存储。
   ⇒ EC-02 的「迁移」在**物理上没有列可加**，其真实含义是**解码向后兼容 + 往返用例**
   （详见判定细则）。
8. **凭据面**：`credential_ref` 即环境变量名（`adapters/relay/credential_resolver.py:14-33`
   `EnvCredentialResolver`，值密封为 `SecretValue`）；`adapters/relay/registry_credential_resolver.py`
   允许**注册表优先、环境变量回退**。**本机当前状态：`DEV_LLM_API_KEY` 在 gitignored `.env`
   中存在但为空串，`DEV_LLM_BASE_URL` / `DEV_LLM_MODEL` 为空**；进程环境无该端点相关变量
   ⇒ **EC-04 / EC-05 的 live 分支在本机只能走「如实 skip」路径**（授权 (3) 明文允许）。
9. **URL 策略已有唯一裁决点**：`packages/application/model_relay/endpoint_policy.py`
   （`validate_endpoint_url`；全仓 `ipaddress` 只出现在这一处）——EC-03 必须**复用它**，
   不得另造第二套 host 判据。

### EC-01 判定细则（ANTHROPIC 协议执行路径）

- **终态选择：本 GOAL 采取 (a) 实现**。理由**如实记录**：(b) 的定义前提是「**实测**该端点
  提供 OpenAI 兼容面并据此登记」——而本机**无凭据**（现状第 8 条），实测不可得；
  于是 (b) 无法满足自身判据，而停在「域里声明了但跑不通」被明文禁止。**这不等于断言
  真实端点不支持 OpenAI 兼容面**——该事实仍**未实测**，必须作为残余登记（EC-03/EC-04 的
  live 分支就位后由实测回答）。
- **形态**：Anthropic Messages 面（`POST {base_url}/messages`；鉴权用 `x-api-key` +
  `anthropic-version` 头；请求体 `model` / `max_tokens`（该形态**必填**）/ `messages` /
  可选 `system`；响应取 `content[].text` 合并、`model`、`usage.input_tokens`/`output_tokens`）。
  **实现优先手写 HTTP**（复用既有 `adapters/relay/transport.py` + `parsing.py`）——
  `tests/architecture/python/test_relay_boundaries.py:4` 已把「relay 适配器不得 import
  `openai`/`litellm`/`anthropic`」写成结构约束，**新依赖是 escalation**。
- **OpenHands 侧**：`resolve_runtime_model_name` 增协议入参——`ANTHROPIC` ⇒ `anthropic/`
  前缀（litellm 既有约定，随 `openhands-sdk` 传递依赖已可用），`OPENAI_COMPATIBLE` ⇒ 现有
  行为**逐字节不变**。判据必须证明既有分支的**回归对照**（未变），不是只看新分支能过。
- **未知协议 fail-closed**：不得静默回退到 `openai`（静默回退会让「配了 anthropic」与
  「跑的是 openai 形态」不可区分——与 GOAL-007 EC-01 对未配置 runtime 的裁定同构）。

### EC-02 判定细则（模型参数落库）

- **承载字段的落点**由子 PLAN 决定（候选：`ModelDefinition` 加两个可选字段，或新建一个
  声明式参数承载实体；**厂商中立命名**是硬约束）。**本 GOAL 不预先选型**，但要求：
  ① 命名不得出现厂商名（AGENTS.md §1）；② 两值必须能被**读面**读到并**渲染**；
  ③ 缺字段时用例**判红**，不得静默丢弃。
- **「迁移」的真实含义（如实登记）**：配置面是 JSON blob（现状第 7 条）⇒ **没有 SQL 列可加**，
  也**不得**为此刻意新建 PG canonical 表（那触及 Canonical State 边界 ⇒ escalation）。
  因此 EC-02 的迁移面 = **旧行缺键时的解码向后兼容**（既有数据不得因新字段读不出）
  + **往返用例**；若子 PLAN 判断需要 SQL 迁移，必须**先停下来**按 escalation 处置。
- **「SQLite/PG 往返」的口径**：两个组合根**共用同一配置面**（现状第 7 条）⇒ 判据须证明
  「PG 组合根下读到的端点/模型仍带这两个值」，而不是新造 PG 表。**不得**把它写成
  「已在 PG 中持久化模型参数」。

### EC-03 判定细则（供应链登记与凭据纪律）

- 登记路径以**既有 API/存储**为准（`POST /llm-endpoints` + `POST /models`，或既有
  store 写入路径）；**不新增登记面**。
- **诚实边界必须写在读面**：凭据值只存在于环境/凭据边界，**进程重启后需要重新注入**——
  UI/文档不得暗示「已保存到 Secret Manager」。
- **grep 反证**的射程要写清楚（哪些目录/文件类型被扫描、为什么某些命中不算泄漏——
  例如不可用的占位串），**不得**用「没扫到」充当 PASS。

### EC-05 判定细则（漂移可见性）

- 判据必须区分**三态**：一致 / 漂移（点名差异）/ **未知**（未探到）。「未知」**不得**
  显示为「无漂移」——这正是 AGENTS.md §4「无法证明一致时必须标注」的读面落实。
- live 探针在无凭据时**如实 skip**（记录 skip 事实），离线判据仍须绿。

### EC-04 判定细则（首次真实 run）

- 门控：`requires_live_llm`（或等价既有门）+ **显式配置 runtime + policy 允许**；
  凭据缺失 ⇒ skip 并登记。**skip 不是 PASS**。
- 指纹口径：`ModelRuntimeFingerprint` 的既有字段逐项如实填写，**取不到的字段写
  `NOT_VERIFIED` 或空并在记录里点名**（不得留空冒充「探了没问题」——GOAL-007 EC-01 的裁定）。
- usage 必须**真的归账**（`BudgetLedger`），制品与证据落 canonical；**不得**只记「跑通了」。

## 循环入口协议

按 README 的 7 步判定执行，一切状态以「文件 + 工作树 + 远端实况」为准：

1. 本文件 `status != ACTIVE` → 只输出终止摘要（ACHIEVED/BLOCKED/ABORTED + 依据），本轮不做改动。
2. 迭代日志最后一行判定续点：无记录 → 开 cycle 1（执行 ①）；有子 PLAN 在
   IN_PROGRESS → 继续 ②；本地验证已过、有未推送 commit → ④⑤；CI 未记录结论 →
   ⑤（等待/判定，禁止猜测绿）；CI 有失败且未达上限 → ⑥。
3. 每 cycle 收口必须：CI 终态已记录 + 本文件（迭代日志/EC 状态/child_plans/
   latest_recheck/状态历史）已回写；未收口不得开新 cycle。
4. 进入 cycle 时在迭代日志声明 `driver=client-goal` / `owner=root-agent`；另一驱动
   持有未收口 ACTIVE cycle 时等待，不并发双写。
5. **live 相关的轮次**：EC-04 / EC-05 的 live 分支前，先确认**凭据来自环境或
   Credential boundary**（不读取、不回显其值）；发现任何明文凭据落入仓库/记录/日志
   ⇒ **立即停止并 BLOCKED 报告**（授权 (3)）。

**当前续点**：**cycle 6 已收口（PLAN-20260920-119 = EC-06，`DONE`；RECHECK-20260920-119 =
PASS_WITH_WARNINGS）** ⇒ **EC-01…EC-06 全 PASS**。
下一步 = **GOAL 的终止判定与收口**（按本文件「终止与收口」小节）：
① 独立复检（不采信实施叙述，按 EC 判据在干净 checkout 上重跑）；② 残余逐条登记
（EC-04 W-1 / EC-05 W-1 的 live 分支未跑 + EC-06 的 W-1…W-6）；③ 干净 checkout 封印
（按 GOAL-007 的收口口径：clean checkout + m0 + live 分支如实 skip 的记录）；
④ CI 台账尾巴（本 cycle 与本收口的 run 与六 job 结论全部记账）。
**仍受无凭据限制**：EC-04/EC-05 的 live 分支在本机**没有发生过**（门两条都关着），
按「终止与收口」的明文，这不自动阻塞 ACHIEVED，但已在两处 `evidence` 与残余里如实登记。
状态以本文件「迭代日志」末行 + 工作树实况为准；不凭记忆假设上一轮状态。

## 驱动

驱动无关（README「驱动适配」）：本实例由客户端 goal 模式驱动（每轮触发 = 一次入口
协议），亦可换会话/定时驱动；仅当 `status=ACTIVE` 时推进。同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 主题顺序：EC 表首个 PENDING（EC-01 → EC-02 → EC-03 → EC-05 → EC-04 → EC-06）；
  若上一 cycle 部分交付，以其「下一轮输入」为准。子 PLAN 必须独立可验收、独立 RECHECK
  （`.cursor/plans/rechecks/`），frontmatter 带 `parent_goal: GOAL-20260920-008` 并投影 ALL_PLAN。
- ② 按子 PLAN 的 WP 推进，**每 WP 独立 commit**（显式路径；并发工作树，禁 `git add -A`）。
- ③ 本地验证：`make validate-all` 全量 23 项（DSN 固化配方）+ 受影响定向套件 + web 门
  （lint/typecheck/unit/build/stub e2e/live e2e）；页面改动时按既有流程重生成设计基线
  与结构签名（`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`，
  跨平台一致性用既有容器配方复核）。实现完成后**先自查规模门禁**（50 行函数 / 450 行文件）
  与快照类门禁（OpenAPI / 设计基线），再跑 m0。本地不绿不得 push。
- ④ 子 PLAN 收口（RECHECK DONE）后 GOAL 记录 commit 列表。
- ⑤ `git pull --ff-only origin main`（必要时 --rebase，不 force）→ `git push origin main`
  → 按本机口径查 m0-quality 最新 run（无 gh CLI：`git credential fill` 取已存令牌走
  GitHub REST API，按 head_sha 匹配 + `/jobs` 读六个 job 结论）→ 轮询到终态并记录
  run 链接与结论。只改 `.cursor/**` 的记录提交同样触发六 job CI，按同口径等待。
- ⑥ 按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- ⑦ 回写本文件：迭代日志（含 driver/owner 声明行）、EC 状态、child_plans、
  latest_recheck、状态历史；未达终态且未触顶 → 直接进入下一 cycle ①。
- **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进，不猜测绿。

**本 GOAL 特有的执行纪律**（安全面，来自 authorization.ref）：

- **凭据纪律（每轮自检）**：任何文件中不得出现可用凭据字面量；真实调用前确认凭据来自
  环境或 Credential boundary；**不回显、不写盘、不进日志**；本循环**不得索取明文**。
- 默认 runtime 保持 **Fake**；**CI 与离线开发不依赖网络**；真实 runtime 必须
  **显式配置 + policy 允许**（两者缺一即拒绝）。
- **真实端点调用只走 live-gated 路径**，且**只限用户登记的那一个端点**、**最小必要次数**
  （不跑压力/批量/模型对比）。真实端点调用**永不进默认 CI**。
- **Domain 不得出现厂商名**；**OpenHands 类型不得进 Domain**（adapter 层隔离）。
- **不引入新依赖、不改上游 pin**（EC-01 的 anthropic 形态**手写 HTTP** 实现；需要新依赖即 BLOCKED）。
- 服务端 URL 仅 http/https 且拒绝 localhost / 环回 / 私有 / 保留地址；DB 查询一律**参数绑定**
  （禁拼接 / format / f-string）。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修，先排除环境干扰）：
observability OTLP teardown race（stopped receiver 端口）、m0 全量单跑在负载下的 timing
用例（隔离复跑对照）、DSN 注入（需固化配方：`RESEARCHOS_POSTGRES_DSN` 指向 test DSN、
其余 DSN 键清空，防 litellm `load_dotenv` 注入 operator `.env`）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）、
**kill 后台 m0 会留孤儿 pytest**（复跑前先确认无残留进程/容器，否则污染下一轮）、
`python/dependency-boundaries` 在直接跑 `.venv/Scripts/python.exe` 时会因 `lint-imports`
不在 PATH 而误红（用仓库既定 `uv run --frozen --no-sync` 启动）、
draft-contract 排序用例在**合并 m0（Postgres 污染）**下偶红而**隔离必绿**（先隔离复跑对照）。

`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。
账户级计费阻断（runner_id=0、无 step、2 秒结束）非代码缺陷：不推进 cycle，恢复后先复核
`runner_id != 0` 再回填结论（GOAL-003 cycle 1 的处置模板）。
**M0 CI concurrency 口径**：`cancel-in-progress` 会取消在飞的 run ⇒ 一个 cycle 攒成**一次**
推送；被取消的 run 如实记 `cancelled`，不得记作失败或成功。

**本 GOAL 新增的失败面**：anthropic 形态的离线判据若在 CI 上表现不稳定（例如把 mock 传输层
写成依赖时序的形态），**优先把用例改成不依赖时序**；若确认是环境相关缺陷而无法在既有边界内修，
按 README 的 flake/env 与基础设施两行处置，不得靠重跑掩盖。**live-gated 用例在 CI 上必须
是 skip**（无凭据），若 CI 上出现**真发出了出站调用**，按**产品缺陷**处理并立即修复。

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS 且有实跑证据 + 收口 RECHECK（独立复检，
  `result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK +
  「终止与收口」写明收口结论（含仍未处理项，如有）。
  **live 分支未跑（无凭据）不自动阻塞 ACHIEVED**，但必须在 EC-04/EC-05 的 `evidence` 与
  收口结论里**逐字写明 skip 与原因**，并作为残余登记——**不得**写成「已实测通过」。
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、
  或命中 `escalation_triggers`（含新增依赖、Accepted ADR、Canonical State 边界、
  把真实 runtime 设为默认、明文凭据泄露）。写 BLOCKED 记录（原因/EC 状态表/收口复检/
  安全扫描处置/恢复条件/仍未处理的长程项），恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」如实登记为后继入口（不隐藏缺口），并给出恢复条件
（新建承接 GOAL 或显式变更 budget 并置回 ACTIVE）。

### 收口结论

（未收口。ACHIEVED / BLOCKED 时在此写结论。）

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——归用户拍板；
   本循环不将其置为 Accepted，也不据此改行为。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板，本循环不得自行决定。
3. **`artifacts/` 明文 token 清理**——涉及不可变历史资产与凭据面，需人工确认。
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险，需人工决定是否在本轮内处理。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，
   需用户或 ADR 拍板。
6. **hook 侧 L3 门**——治理面，需人工决定。
7. **把真实 runtime 设为默认**——默认必须仍是 Fake；本循环只做「显式配置才启用」。
8. **为 anthropic 形态引入 SDK / 新依赖**——EC-01 用手写 HTTP；需要新依赖即 BLOCKED。
9. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——涉及 Domain 面
   与可能的 Canonical State 边界，需拍板；本 GOAL 的 EC-02 只在**既有实体**上加承载字段。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `167bdd3` | 治理 `validate.py` 绿 | run 35490147869 = **success**（六 job 全 success） | — | EC-01…EC-06 全 PENDING；本机**无凭据**（`DEV_LLM_API_KEY` 空）⇒ EC-03/04/05 的 live 分支只能走如实 skip | cycle 1 = derive EC-01 子 PLAN |
| 1 | PLAN-20260920-114（EC-01） | `7a28799`（PLAN+ALL_PLAN）、`c9a5caa`、`4693e6b`、`fbe6dee`、`d9e4be9`、`cc704e5`、`691414a`、`5f82071`、`0a04520`、`4e28e93`（记录） | m0 **PASS: profile=m0; 23 deterministic checks**（4072 passed / 11 skipped，冻结树 `0a04520`；0 failed checks）；定向 168 passed + probe 判据 3 passed；`ruff`/`format`/`mypy`(945 files) 绿；治理 `validate.py` / `validate_bundle` / DOCS-CHECK 绿 | **run 35493396918 = success**（`4e28e93`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest） | m0 拦下四处：format-check / typecheck(7) / 50 行函数门 / validate_bundle（G1–G4，均按缺陷修，未动断言与门禁） | EC-01 **PASS**；EC-02…EC-06 PENDING。EC-01 的 W-1（真实端点面未实测）、W-6（示例端点未入库）转由 EC-03/EC-04 承接 | cycle 2 = derive EC-02 子 PLAN（模型参数落库：上下文窗口 512000 + 思考强度 Max） |
| 2 | PLAN-20260920-115（EC-02） | `a6c03bc`（derive）、`3eece38`、`d3eedf7`、`3caf6c2`、`abed221`、`b8f2e9b`、`a0f98bb`、`40fe55d`、`53f4a26`、`1df2e11`（收口记录） | m0 **PASS: profile=m0; 23 deterministic checks**（4097 passed / 11 skipped，461.72s，冻结树 `40fe55d`；其后仅一段文档改动，`validate_bundle` / `docs_consistency_check` / 治理 `validate.py` 单独复跑绿）；定向 56 passed、PG 根 + 装配判据 5 passed、web unit 76 passed、web lint/typecheck 绿、design-fidelity 2 passed（基线零 diff）；`ruff`/`format`/`mypy`(949 files) 绿 | **run 35497734881 = success**（`1df2e11`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest）；cycle 2 的 CI 台账提交 `105b745` → **run 35498375517 = success**（六 job 全 success，与 35497734881 同批，补记于 cycle 3） | — （本轮 m0 全量一次通过，无 G 项：提交前已就地跑格式化与类型门） | EC-02 **PASS**；EC-03…EC-06 PENDING。EC-02 的 W-1（声明值不发送/不生效，需执行侧映射）、W-2（OpenHands 未接线）、W-3（web 类型无自动 drift 门）、W-5（设计门射程）为如实边界 | cycle 3 = derive EC-03 子 PLAN（供应链登记与凭据纪律：端点/模型入库 + URL 策略 + 明文凭据 grep 反证 + 重启失效边界） |
| 3 | PLAN-20260920-116（EC-03） | `dd989b7`（derive）、`b6c7386`、`26f93b3`、`eee4728`、`1e16c40`、`40bddd5`、`94db850`、`18794a1`、`5f43b98`、`fdf0281`（收口记录） | m0 **PASS: profile=m0; 23 deterministic checks**（**4131 passed / 11 skipped**，479.71s，冻结树 `5f43b98`；其后仅 `.cursor/**` 记录改动，`validate_bundle` / `docs_consistency_check` / 治理 `validate.py` 单独复跑绿）；定向 `tests/api + tests/application + tests/architecture + tests/tooling` **2292 passed / 2 skipped**（2 条需 `RESEARCHOS_POSTGRES_DSN` 钉桩，补桩后 6 passed——已知 DSN 条件，非回归）；`ruff format/check` / `mypy`(951 files) 绿；web `lint`(max-warnings 0)/`typecheck`/e2e 新增 spec **2 passed**、`design-fidelity` **2 passed 且基线零 diff**（新文案在未打开的抽屉里 ⇒ 对设计门不可见）；审计工具实跑四面 0 命中 | **run 35503139831 = success**（`fdf0281`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest） | **m0 拦下 1 处**（G1：新用例里 `int(object)` + `# type: ignore` 触发 `unused-ignore` / `call-overload` / `attr-defined`；按缺陷修为先断言类型的助手，`5f43b98`，未动门禁与断言强度） | EC-03 **PASS**；EC-04/EC-05/EC-06 PENDING。残余 7 条：W-1 注册面仍不校验 URL、W-2 出站 0 只在 Fakes 上证明、W-3 措辞判据不覆盖渲染、W-4 向导面未加声明、W-5 审计白名单人维护、W-6 本机仍无凭据、W-7 `.env` 不在扫描面内 | cycle 4 = derive **EC-05**（漂移可见性：probe 返回 model 名 vs 声明值三态；live 分支无凭据 ⇒ 如实 skip） |

| 4 | PLAN-20260920-117（EC-05） | `183f588`（derive）、`c6bfdef`、`7b317f6`、`3a955b5`、`3eef7c3`（+收口记录） | 定向：域 `test_model_drift.py` **9 passed**、API `test_models_api.py` **15 passed**、词表同源 **5 passed**、e2e 漂移 spec **4 passed**、`test_openapi_snapshot.py`（快照 +47 行）绿；web `lint`(max-warnings 0)/`typecheck`/unit 绿；`design-fidelity` **2 passed 且基线零 diff**（漂移块只在探测后渲染 ⇒ 对设计门不可见）；`docs_consistency_check` / `validate_bundle` 绿；**m0 全量 23 项**计数见状态历史 cycle 4 段 | **run 35506216814 = success**（`52b4967`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest） | — | EC-05 **PASS**；EC-04/EC-06 PENDING。残余 6 条：W-1 live 语义未实测（无凭据，真实 probe 一次未跑）、W-2 fingerprint 未纳入漂移判定、W-3 drift 未持久化、W-4 严格口径的噪声代价、W-5 UNKNOWN 三种来源未细分、W-6 指纹只在 provider 给出时构建 | cycle 5 = derive EC-04（首次真实 run；仍无凭据 ⇒ 按「skip 不是 PASS」处置）或 EC-06 |
| 5 | PLAN-20260920-118（EC-04） | `8b85f03`（derive）、`08e41f7`、`17464bf`、`8c9d67c`、`97380c1`、`4f54e53`、`7ce833f`（+收口记录） | 定向：域词表 **4 passed**、run 记录 **13 passed**、离线门 **13 passed**、live 用例 **1 passed / 1 skipped**、口径判据 **5 passed**、EC-03 离线全链 **2 passed / 1 skipped**（抽共享模块后复跑）⇒ 合计 **38 passed / 2 skipped**；反证 F1–F5 全部先红后复原；治理 `validate.py` / `validate_bundle` / DOCS-CHECK 绿；**m0 全量 23 项 4190 passed / 12 skipped（499.34s，冻结树 `7ce833f`；cycle 4 为 4146/11）** | **run 35508839524 = success**（`a5f62eb`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest） | **m0 拦下三处（G1–G3）**：G1 新判据用两个字面量枚举成员比较 ⇒ mypy `comparison-overlap`（cycle 4 同族陷阱再现，改走运行期枚举）；G2 新代码两处函数 >50 行（拆助手）；**G3 跨套件污染**——live 用例直接 import EC-03 测试模块 ⇒ 同一文件被两个模块名加载、SDK `Action` 子类被定义两次 ⇒ 6 条 fork 用例红（抽单一名共享模块 `tests/e2e/live_run_support.py`）。均按缺陷修，未动门禁与断言强度 | EC-04 **PASS（离线判据全绿；live 分支如实 skip —— 真实 run 未发生）**；EC-06 未收口。残余 6 条：W-1 真实 run 未发生（能力边界，六项候选凭据环境变量全 absent）、W-2 live 路径的模型绑定不是 anthropic 面（所有模型绑 `main`）、W-3 门只看 runtime 配置 + 凭据可解析、W-4 口径判据的引用-豁免是行级启发式、W-5 记录的 usage/制品字段靠调用方填（live 判据未跑）、W-6 `NOT_VERIFIED` 同时覆盖「无凭据」与「跑了但没终止」 | cycle 6 = derive **EC-06**（文档与 runbook；GOAL 最后一个未收口 EC） |
| 6 | PLAN-20260920-119（EC-06） | `099bd62`（derive）、`96d1897`、`affc063`、`77d3c45`（+收口记录） | 定向同源判据 **10 passed**；`docs_consistency_check`（DOCS-CHECK PASS: 6 checks）/ `validate_bundle` / 治理 `validate.py` 绿；反证 F1–F5 全部先红后复原；**m0 全量 23 项 4201 passed / 12 skipped（489.62s，代码树 `affc063`；cycle 5 为 4190/12）**；其后仅 `.cursor/**` 记录改动，三件文档门单独复跑绿（未重跑全量 m0） | **run 35509830682 = success**（`b3bb96a`，六 job 全 success：console-frontend / collector-quality / eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest） | **反证抓出判据自身两个洞并按缺陷修**：F2——跨行反引号配对被代码围栏打乱 ⇒ 变量名 token 被整段吞掉，判据「看着绿其实没看」；F4——索引判据只判「全文出现过」，快捷问答里的一句引用即可蒙混、清单漏项反而放行。两处都改成更严的形态（按行抽 token / 判条目行），未放宽任何断言 | EC-06 **PASS**；**EC-01…EC-06 全 PASS**。残余 6 条：W-1 同源判据只判存在性（不判行为一致）、W-2 大写变量名判据是启发式、W-3 运行期产物白名单人维护、W-4 demo 清单完备性未判、W-5 live 步骤未实测（无凭据）、W-6 runbook 的 HTTP 片段未实跑 | GOAL 进入**终止判定与收口**（独立复检 + 残余登记 + 干净 checkout 封印 + CI 台账） |

## 状态历史

- 2026-09-20 cycle 6（driver=client-goal / owner=root-agent）：EC-06 **PASS**
  （PLAN-20260920-119 / RECHECK-20260920-119 = PASS_WITH_WARNINGS，W-1…W-6）。
  **交付**：`docs/integration/LIVE_MODEL_RUNBOOK.md`（五节：登记 = YAML 路径 + DB 路径；
  凭据注入与轮换 = 两套面与 ref 形态；重启后重输的边界 = 落到
  `RegistryCredentialResolver._registry` 内存字典这一机制；Fake↔真实切换与回退 =
  `RESEARCHOS_AGENT_RUNTIME` 的开/关与回退三步检查；仍是 demo 的面 = 13 个 `Fake*` 逐条列出，
  并对照已接通的真实件）+ `docs/INDEX.md` 的 Integrations 条目行 + 同源判据
  `tests/architecture/python/test_runbook_same_source.py`：**判据判同源不判文笔**——
  文档里的仓库路径必须存在（运行期产物 `data/research-os-control.db` 走**逐条白名单 + 理由**，
  且白名单条目必须仍被文档引用，避免死条目）、大写变量名必须在代码里出现、pytest 目标必须存在、
  demo 符号必须在代码里存在；五类内容缺一判红。
  **本轮最有价值的产出是反证抓出判据自己的两个洞**：F2（变量名改错一个字符）**第一次没红**——
  跨行 `re.findall` 的反引号配对被 Markdown 代码围栏打乱，文档里明明写着
  `RESEARCHOS_AGENT_RUNTIME` 却没进 token 集合，判据「看着绿其实没看」；F4（索引条目被换掉）
  **第一次也没红**——索引判据只判「全文出现过」，快捷问答里的一句引用就能满足它，
  而清单漏项正是这份索引最容易漂的地方。两处都**按缺陷修判据**（按行抽 token、判条目行），
  修完立刻红；**未放宽任何断言**。这条经过沉淀为 `MEM-20260920-092`。
  **外部检查器也咬到一次**：`docs_consistency_check` 在 runbook 引用判据文件而该文件尚未创建时
  判红（`[backtick-ref]`），说明「文档引用必须存在」这条口径在仓库里有两个独立把守者。
  冻结代码树 m0 **23/23（4201 passed / 12 skipped，489.62s，`affc063`；cycle 5 为 4190/12）**；
  其后仅 `.cursor/**` 记录改动，三件文档门单独复跑绿（**未**重跑全量 m0，如实登记）。
  **如实登记的边界**：W-1 同源判据只覆盖存在性、不保证行为一致；W-2 大写变量名判据是启发式
  （单个大写词不判）；W-3 白名单人维护；W-4 demo 清单的**完备性**未判（漏列不红）；
  W-5 runbook 第 4 节的开/关与回退流程在本机**没有跑过**（无凭据 ⇒ 门两条都关着）；
  W-6 runbook 的 `curl` 片段路径由判据核对存在，但请求体形态未实跑校对。
  **未新增依赖、未改 pin、未改 Policy、未改默认 runtime；ADR-0031 仍是 Proposed。**
  **CI 台账**：本轮推送（`099bd62`…`b3bb96a`）→ **run 35509830682 = success**
  （head_sha `b3bb96a`，六 job 全 success：console-frontend / collector-quality / eval-gate /
  container-quality / quality-ubuntu-latest / quality-windows-latest）。

- 2026-09-20 cycle 5（driver=client-goal / owner=root-agent）：EC-04 **PASS**（离线判据全绿；
  **live 分支如实 skip —— 真实 run 未发生**；PLAN-20260920-118 / RECHECK-20260920-118 =
  PASS_WITH_WARNINGS，W-1…W-6）。
  **交付**：把「一次真实 run」从**可期望**变成**可判、可 skip、且不会说谎**——
  ①`ModelReproducibilityVerdict`（`REPEATABLE_CONFIGURATION` / `NOT_VERIFIED`，**穷举两态**：
  「完全可复现」在类型上不可表达）；②`LiveRunRecord`（必填指纹项缺失 ⇒ 降级并**点名缺项**；
  provider 项缺失只登记不降级；`NOT_VERIFIED` **必须**有理由，构造期就拒空理由）；
  ③`evaluate_live_run_gate`（两条开门条件：runtime 显式配置 + 凭据**可解析**——只问
  `CredentialResolver.has`，**不物化明文**；关门时**不碰 socket**，零出站是结构性保证）；
  ④live 用例 `test_ec04_live_first_run.py`（登记端点 `agnes-anthropic` 的 probe 段 + 生产 runtime 的
  run 段，四段判据各自可判）；⑤口径同源判据（六个面必填 + 全仓**肯定式**越级表述判红，
  引用与否定句放行）。
  **「skip 不是 PASS」由两处独立钉住**：记录层（`is_verified=False` + 理由必填 + F1）与
  门层（`skip_record_for_gate` 拒绝开着的门 + F3）。**反证 F1–F5 全部先红后复原**
  （F1 把跳过说成已验证 ⇒ 3 red；F2 缺失项不再点名 ⇒ 6 red；F3 无凭据也放行 ⇒ 4 red；
  F4 否定改肯定 ⇒ 1 red；F5 删掉口径词 ⇒ 1 red；每步 `git diff --quiet` 复核）。
  **本地门禁拦下三处，均按缺陷修**：G1 新判据里两个字面量枚举成员比较 ⇒ mypy
  `comparison-overlap`（**与 cycle 4 的 G1 同族**：连续两轮同一陷阱，改为运行期枚举派生，
  `97380c1`）；G2 两处函数 >50 行（拆私有助手，`7ce833f`）；**G3 跨套件污染**——
  live 用例直接 `from tests.e2e.test_ec03_… import …` 让**同一测试文件被两个模块名加载**，
  SDK 的 `Action` 子类被定义两次 ⇒ 判别联合在同进程后续任何事件 round-trip 上抛
  `Duplicate class definition` ⇒ 6 条 fork 用例红（`test_fork_override` ×3、
  `test_full_adapter` ×1、`test_agent_runtime_contract` ×2）；抽成**单一名**共享模块
  `tests/e2e/live_run_support.py` 后同进程复跑 **57 passed / 8 skipped**（`4f54e53`）。
  冻结树 m0 **23/23（4190 passed / 12 skipped，499.34s，`7ce833f`；cycle 4 为 4146/11）**。
  **判据在实施中真的咬到一次**：`docs/integration/LLM_ENDPOINTS.md` 原本**没有**「可重复配置」
  这一档 ⇒ 口径判据红 ⇒ **补写 §11**（不是改判据）。
  **沉淀** `MEM-20260920-091`（结论口径要落成穷举词表 + skip 必须有结构 + 枚举守卫走运行期，
  附「空串是任何字符串的子串」这个把行尾误判成引号的陷阱）。
  **如实登记的边界**：**W-1 真实 run 未发生**（本机六项候选凭据环境变量全 absent、
  `RESEARCHOS_AGENT_RUNTIME` 未配置 ⇒ 门两条都关着；EC-04 的靶心要等凭据注入才能命中）、
  W-2 目录里所有模型绑 `main`（OPENAI_COMPATIBLE 面），登记进目录的 anthropic 端点只由 probe 段驱动、
  W-3 门只看两个条件（Policy/预算/端点健康由既有 preflight 负责）、
  W-4 口径判据的引用-豁免是行级启发式、W-5 记录的 usage/制品字段靠调用方填、
  W-6 `NOT_VERIFIED` 同时覆盖两种来源（无凭据 / 跑了但没终止），靠 `reason` 区分。
  **未新增依赖、未改 pin、未新增 PG 表、未触碰凭据值；ADR-0031 仍是 Proposed。**
  **CI 台账**：本轮批量推送（`8b85f03`…`a5f62eb`）→ **run 35508839524 = success**
  （head_sha `a5f62eb`，六 job 全 success：console-frontend / collector-quality / eval-gate /
  container-quality / quality-ubuntu-latest / quality-windows-latest）。

- 2026-09-20 cycle 4（driver=client-goal / owner=root-agent）：EC-05 **PASS**
  （PLAN-20260920-117 / RECHECK-20260920-117 = PASS_WITH_WARNINGS，W-1…W-6）。
  **交付**：AGENTS.md §4 的「同名漂移必须可见」从原则变成**可判事实**——`ModelDriftState`
  三态（`MATCH` / `DRIFT` / **`UNKNOWN`**，`packages/domain/enums.py`）+
  唯一比较点 `assess_model_drift`（纯函数：`strip()` 后精确比较；**大小写/日期后缀差异一律
  `DRIFT` 并点名两个原值**，因为本仓无法证明同一性）；
  `ProbeResultDto.drift`（state / declared / returned / detail，detail 只含两个标识）；
  页面 `probe-drift` 块三套中英文案（`DRIFT` 点名两值，`UNKNOWN` **自带反义**
  「未知不等于无漂移」）+ 自带 stub e2e 4 条；文档两处（`MODEL_PROBE.md` 漂移判定节、
  `LLM_ENDPOINTS.md` §8）。
  **「未知 ≠ 无漂移」由两处独立钉住**：域层（`UNKNOWN` 是独立枚举值；F1 把 `UNKNOWN` 改判
  `MATCH` ⇒ 3 red）与渲染层（F3 令 `UNKNOWN` 用 `MATCH` 文案 ⇒ 1 red）——缺任一侧，
  「没探到」都可能被读成「没问题」。**反证 F1–F3 全部先红后复原**（F2 = 从 DTO 摘掉 `drift`
  ⇒ 3 red；三处注入均逐字节还原并由 `git diff --quiet` 复核）。
  **m0 拦下 1 处**（G1：`assert ... is not MATCH` 写在 `is UNKNOWN` 之后 ⇒ mypy
  `comparison-overlap`；按缺陷修，把「不是一致」那条提前，语义不变、F1 复跑仍 3 red，`3308af5`）。
  冻结树 m0 **23/23（4146 passed / 11 skipped，570.54s，`3308af5`；cycle 3 为 4131 ⇒ 净增 15 条）**。
  **沉淀** `MEM-20260920-090`（三态判定的「未知」必须在**文案**上与「无/一致」分开，
  且域层与渲染层各需一条判据；刻意的严格比聪明的归一化诚实）。
  **如实登记的边界**：W-1 live 语义**未实测**（本机无凭据 ⇒ 真实 probe 一次未跑，
  **skip 不是 PASS**）、W-2 `system_fingerprint` 未纳入漂移判定（跨次版本变化仍不可见）、
  W-3 drift **未持久化**（关页即丢，回看不可能）、W-4 严格口径在真实中转站上可能噪声偏多、
  W-5 `UNKNOWN` 的三种来源未在漂移块内细分、W-6 指纹只在 provider 给出时构建。
  **未新增依赖、未改 pin、未新建 PG 表、未触碰凭据面；ADR-0031 仍是 Proposed。**
  **CI 台账**：cycle 3 的收口记录提交 `c413131` → run **35503858465 = success**（六 job 全 success，
  已在上一条补记）；本轮批量推送（`183f588`…`52b4967`）→ **run 35506216814 = success**
  （head_sha `52b4967`，六 job 全 success：console-frontend / collector-quality / eval-gate /
  container-quality / quality-ubuntu-latest / quality-windows-latest）。

- 2026-09-20 建档（cycle 0）：`status: ACTIVE`。本文件由用户 goal 模式指令创建
  （建档幂等判据：`.cursor/plans/goals/GOAL-*-008-*.md` 不存在）。
  **只读勘察**结论见「建档时已探明的现状」9 条（`protocol` 无执行路径、分派键是 `api_style`、
  `openai/` 前缀只有一处且无条件、示例里已有跑不通的 `ANTHROPIC` 端点、无字段承载上下文窗口/
  思考强度、`ModelCompatibilityProfile` 只存在于散文、配置面是 SQLite JSON blob 且 PG 路径共用、
  `DEV_LLM_API_KEY` 为空、URL 策略唯一裁决点）。GOAL-001…007 全部只读，未做任何修改。
  **EC-01 终态选择 (a) 实现**并记录理由（无凭据 ⇒ (b) 的实测前提不可满足）；
  **EC-02 的「迁移」口径按现状收敛为「解码向后兼容 + 往返」**（无 SQL 列可加，不新建 PG 表）。
- 2026-09-20 cycle 1（driver=client-goal / owner=root-agent）：EC-01 **PASS**
  （PLAN-20260920-114 / RECHECK-20260920-114 = PASS_WITH_WARNINGS）。
  **交付**：`protocol` 从「只被持久化/DTO 读取的字符串」变成**真正的执行选路面**——
  域枚举 `LLMProtocol` 为唯一词表；`adapters/relay/protocols.py::select_wire_shape` 是唯一分派点
  （未知协议**抛分类错误且不发起请求**）；新增 Messages 形态实现
  （`adapters/relay/anthropic_api.py` + `_complete_anthropic`，`x-api-key` + `anthropic-version`）；
  `llm_factory.resolve_runtime_model_name(*, protocol)` 按协议取 `anthropic/` 前缀。
  **三处不伪造**：缺 `max_tokens` 拒绝（不编默认值）、流式拒绝（不降级）、
  `system_fingerprint`/usage 不编造。**三条反证先红后复原**（F1/F2/F3，最重 9 failed），
  复原后定向 **168 passed**。**m0 本轮真的拦下四处缺陷**（G1–G4：format / mypy 7 错 /
  **50 行函数门** / validate_bundle 旧版本号误判）——全部按缺陷修，**未动任何断言与门禁**；
  G3 抽出 `_execute_request`（控制流不变），G4 改成「显式网段 + 地址分类兜底」**反而更严**。
  冻结树 m0 **23/23（4072 passed / 11 skipped）**。**沉淀** `MEM-20260920-087`
  （validate_bundle 扫全树 .py 含 gitignored `scratch/`，TEST-NET-1 网段字面量会命中旧版本号正则）。
  **如实登记的边界**：W-1 真实端点面**未实测**（本机无凭据，一次出站都没发）、W-2/W-3 流式与
  `response_format` 缺口、W-5 `system_fingerprint` 恒空、W-6 示例端点未入库（属 EC-03）、
  W-8 域值名含厂商词属**既有**取值。**ADR-0031 仍是 Proposed；未新增依赖/未改 pin。**
  **CI 台账**：建档推送 `167bdd3` → run **35490147869 = success**（六 job 全 success）；
  cycle 1 攒成一次推送 `167bdd3..4e28e93`（10 个提交）→ run **35493396918 = success**
  （六 job 全 success）。只改 `.cursor/**` 的记录提交按同口径等待并记录。
- 2026-09-20 cycle 2（driver=client-goal / owner=root-agent）：EC-02 **PASS**
  （PLAN-20260920-115 / RECHECK-20260920-115 = PASS_WITH_WARNINGS）。
  **交付**：用户声明的两个参数（上下文窗口 **512000 tokens**、思考强度 **Max**）从「只在对话里
  说过」变成可判事实——域 `ModelDefinition` 两个**可选**字段 + 新域枚举 `ThinkingIntensity`
  （级别词、厂商中立，`"Max"` 落为 `MAX`）；契约 schema 两属性（`additionalProperties: false`
  ⇒ 不声明就写不进去）；加载器读取并拒绝未知级别；配置面 JSON blob 往返 + **缺键旧行向后兼容
  解码**；API 三 DTO + 映射 + 路由构造/PATCH/probe 重建全部携带；**`model_version` 纳入两字段**
  ⇒ 改这两个字段的 PATCH 会改变 ETag；OpenAPI 快照重生成 **+91 行**；web `types.ts` + 详情面板
  + 目录表列 + 自带 stub e2e。**11 条反证先红后复原**（域 5 / 加载器 2 / API 2+1+1 /
  `tsc` 11 处 / e2e 3 / 装配 1+1+2 / 迁移 1）。**补了两条此前只是叙述的判据**：AST 装配判据
  （`assemble` 只构造一个配置面实例并喂给两个分支；PG 根不自建、从 `config` 取同一实例；
  PG 迁移无 `models` 表）+ **PG 根运行期**判据（无事后替换，POST/GET/PATCH 两值可判）。
  冻结树 m0 **23/23（4097 passed / 11 skipped）**，其后仅一段文档改动并单独复跑 docs 三门。
  **沉淀** `MEM-20260920-088`（新渲染分支可能对设计门**不可见**：默认替身没注册该路由的
  `GET /models` ⇒ 该路由渲染错误态，像素/结构基线零 diff；要自带 stub spec 钉住分支）。
  **如实登记的边界**：W-1 **声明值不生效**（不发送给 provider、不参与 eligibility/capability/
  预算——读面 en+zh 文案与三份文档四处同源）、W-2 OpenHands 侧未接线、W-3 `types.ts` 与
  OpenAPI 快照**没有**自动比对门（耦合来自 `tsc`）、W-4「迁移」= 解码向后兼容而非 DDL、
  W-5 设计门射程、W-6 既存「显式 null 被忽略」未改。**未新增依赖、未改 pin、未新建 PG 表、
  未触碰凭据面；ADR-0031 仍是 Proposed。**
  **CI 台账**：cycle 2 攒成一次推送 `490ced3..1df2e11`（10 个提交）→ run **35497734881 = success**
  （`1df2e11`，六 job 全 success：console-frontend / collector-quality / eval-gate /
  container-quality / quality-ubuntu-latest / quality-windows-latest）。
  收口记录提交的 run 结论在下一轮（cycle 3）按同口径登记。
- 2026-09-20 cycle 3（driver=client-goal / owner=root-agent）：EC-03 **PASS**
  （PLAN-20260920-116 / RECHECK-20260920-116 = PASS_WITH_WARNINGS，W-1…W-7）。
  **交付**：① URL 策略**补严**——`_host_kind` 新增 `reserved` 类（多播 / 未指定 / 保留段 /
  CGNAT `100.64.0.0/10` / 非全局单播）、环回全段（`127.0.0.0/8`、`::1`）统一归 `localhost`，
  保留类**不设放行开关**（只走既有 `allowed_hosts` 点名豁免）；② 出站 0 判据
  （被拒 URL / 缺凭据三情形 `gateway.calls == ()` + 一条对照证明放行时确实进 gateway）；
  ③ `tools/credential_audit.py` **四面明文审计**（跟踪文件 3146 / 记录 259 / 配置面 DB 1 /
  日志 147，命中 0；放行项**按值**逐条给理由；`--root` 可审计另一份 checkout；
  「该扫而扫不成」记 `not_a_git_tree` **判红**）；④ **真实端点与模型登记入库**
  （经既有 API：端点 `e7f210a2-…` `protocol=ANTHROPIC` / `base_url=https://apihub.agnes-ai.com`、
  模型 `5bec513d-…` `agnes-2.5-flash` + `context_window_tokens=512000` / `thinking_intensity=MAX`，
  二跑走复用路径；配置面 blob 只有 `credential_ref` 名字，**无密钥**；**凭据未注入**，
  `credential=missing`）；⑤ **重启失效边界三面同源**（文档 §9 三层事实表 + 控制台详情抽屉
  声明 + 解析器 docstring；措辞判据另有**禁止半**：`Secret Store` / `凭据已保存` 不得出现），
  并把「重启后凭据消失」从措辞变成**生产解析器**的跨装配判据；⑥ 无凭据时 `/test`、`/health`、
  `/discover-models` 三处**点名失败且不触网**（`CONFIGURATION` / 422 Credential Missing）。
  **反证 F1–F8 先红后复原**（保留类短路 5 红 / link-local 降序 2 红 / 多播不短路 1 红 /
  真树注入陌生键 audit exit=1 / 删措辞 + 塞假声明 / 类级注册表 2 红 / 摘掉 UI 挂载 e2e 2 红）。
  **实跑揪出并修掉 2 处缺陷**：link-local **空开关 + 拒因指错类别**（`1e16c40`）、
  新用例的类型门失败 G1（`5f43b98`，m0 fail-fast 拦下）。**沉淀** `MEM-20260920-089`
  （读面谎言抓不到功能测试：要用措辞判据钉；且「文件里有这些字」与「这些字被渲染」是两条判据）。
  冻结树 m0 **23/23（4131 passed / 11 skipped，479.71s，`5f43b98`）**，其后仅 `.cursor/**` 记录改动
  并单独复跑 docs 三门。**如实登记的边界**：W-1 注册面仍不校验 URL（存疑 URL 可入库，一跑就被拒）、
  W-2 出站 0 只在 Fakes 上证明（未做网络级观测）、W-3 措辞判据不覆盖渲染、W-4 录入向导面未加声明、
  W-5 审计白名单人维护、W-6 本机仍**无凭据**（候选环境变量全 absent、`endpoint:*` 0 个）、
  W-7 `.env` 不在审计四面内（靠「保持 untracked」兜住）。**未新增依赖、未改 pin、
  未改 Canonical State 边界、未把真实 runtime 设为默认；ADR-0031 仍是 Proposed。**
  **CI 台账**：cycle 2 的记录提交 `105b745` → run **35498375517 = success**（六 job 全 success，
  与本轮一并补记）；cycle 3 攒成一次推送 `dd989b7..fdf0281`（9 个提交）→ run
  **35503139831 = success**（`fdf0281`，六 job 全 success：console-frontend / collector-quality /
  eval-gate / container-quality / quality-ubuntu-latest / quality-windows-latest，
  jobs 逐一核过 `status=completed conclusion=success`）；cycle 3 的收口记录提交 `c413131` →
  run **35503858465 = success**（六 job 全 success，补记于 cycle 4）。
