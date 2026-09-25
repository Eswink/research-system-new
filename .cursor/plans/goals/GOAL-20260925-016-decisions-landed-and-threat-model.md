---
id: GOAL-20260925-016
slug: decisions-landed-and-threat-model
title: 决策落地：维持类决定的判据化 + 威胁模型草案 + high 依赖升级
status: ACHIEVED
created_at: 2026-09-25
updated_at: 2026-09-25
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-25 用户会话指令（goal 模式）：**建档 GOAL-20260925-016（决策落地）并授权本驱动
    自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **判词来源**：用户按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的**建议列**逐项拍板，
    授权**实施七项决定**（其中 D-01 / D-02 / D-07 / D-08 / D-12 是「**维持现状 + 把决定写成
    判据 / 文档**」，**不是**改产品行为）。
    (1) **D-01 → 取 (b)**：出厂组合根**不**自己接执行体缝（维持 `ApiDeps.tool_providers`
    生产为空）；交付 = 把「缺执行体时 preflight **点名**哪个能力没人执行」钉成**机械判据**。
    已核实点名逻辑**已存在**（`packages/application/preflight/checks.py`：
    `PreflightFindingCode.TOOL_UNAVAILABLE` + `"no provider is available for capability {…}"`）
    ⇒ 交付是**判据 + 反向搜索证据**（证明它真的是稳定事实、而非「它碰巧在场」），
    **不是**新增点名逻辑；若判据要求改点名词，属改产品行为 ⇒ **停下并登记**，不自行改。
    **D-01 的 (a)（组合根自己接执行体缝）明确不取**；等 D-11 的开关语义定下来再谈。
    (2) **D-02 → 取 (b)**：读类能力**维持逐条放行**（**不**成类预放行、**不**新增任何 allow）。
    交付 = 判据钉住「新增读能力必须逐条授权」这条口径 + 引用差集表（该登记 15 条）作为证据面。
    **本项零策略面改动**（`examples/config/policy.yaml` 与 `_CAPABILITY_SCOPE` 都**不动**）。
    (3) **D-03 → 取 (b)**：依赖 pin **分批升级**，**high 先升**，minor/patch 合批，
    **每批单独 cycle 验证**。范围：**4 条 high 先升**（若都在 patch/minor 范围内）。
    这是本轮**唯一动产品依赖**的项。若某条 high 的修复版本落在**主版本跳跃**（breaking）⇒
    **不做该条**、如实登记为下一轮输入（**不改判据、不降级其余项**）。升级必须：改
    `pnpm-lock.yaml` + 相应 `package.json` 后跑**全量 web 门**（lint / typecheck / unit /
    build / stub e2e / live e2e）+ m0；设计基线若漂移 ⇒ 按既有流程**强制重生成 + 目检**
    （**不得**调容差）。**D-03 授权只覆盖「D-03 范围内的 pin 变更」**；越界即 BLOCKED。
    (4) **D-07 → 取 (b)**：`ADR-0031`（`tool_pack.*`）**维持 `Proposed`**，并在该 ADR 内补一节
    **「否证条件」**（什么证据会否证它 / 什么条件下应转为 Accepted 或撤回），避免悬空决策。
    **不改 ADR 的 `Status`**；不实施其内容。
    (5) **D-08 → 取 (b)**：`ModelCompatibilityProfile` **维持派生视图**（**不**建一等域实体、
    **不**动 Canonical State / 迁移）；交付 = 把这条决定写成依据（含「若要 (a) 必须先出 ADR
    说明迁移与回滚」），并钉一条判据 / 登记，使下轮不再重复提问。
    (6) **D-09 → 取 (a)**：出一份 **ADR 记录非 ASCII 路径豁免**（30 条已跟踪路径；
    **不重命名**、不触碰不可变历史资产），引用 AGENTS.md §13「既有历史路径不批量重命名」。
    编号续 **ADR-0032**。
    (7) **D-12 → 取 (b)**：**先出文档级威胁模型草案**（BOLA / BFLA / 授权面覆盖），
    **不改代码、不改门禁、不加判据**。已核实 `docs/security/THREAT_MODEL.md`（106 行）已存在
    但**零处** BOLA/BFLA/越权/多租户字样 ⇒ 交付是**该文档的增量章节**（或同目录新文档 +
    交叉引用），须写明：覆盖了什么、**未覆盖什么**、下一步 (a) 的范围与代价。
    (8) **明确不授权（触及门禁或产品行为，本 GOAL 一律不做，命中即 BLOCKED）**：
    a) **D-10**（`validate_bundle` 排除 gitignored 目录）——**改门禁需另行授权**；本 GOAL 只
    允许把 `R-3` 作为**事实引用**；`R-3` 的现状（as-is 本地 m0 22/23）**原样保留**。
    b) **D-13**（CI 资源阈值判据的负载敏感性）——**改判据 / 阈值 / 作业结构需另行授权**；
    本 GOAL 按简报建议的 **(a)** 处置：**判据与阈值一字不动**，仅在出现 ≥2 次同类偶发红时
    才提请 (b)；本 GOAL **只登记，不改**。
    c) **D-04**（hook 侧 L3 检测层）/ **D-05**（450 行）/ **D-06**（路径 (B)）/ **D-11**
    （live 门开关）——**本轮均不实施**（D-04 / D-11 会改治理面或判据语义；D-05 / D-06 维持
    现状即可）；如实保留为「已拍板为维持现状」或「未拍板」，按简报当前建议列标注。
    (9) **push-to-main-for-CI 授权**：只推 `main`、**不 force**、**不重写历史**、**不推旁支**
    触发 CI；push 前 `git pull --ff-only origin main`。循环预算与纪律以本文件 frontmatter 为准
    （客户端自带的迭代 / 重试 / 超时上限**一律让位于**此）。
    (10) **默认姿态不变**：默认 runtime 保持 **Fake**、默认 CI **离线**（AGENTS.md §11）。
    **本 GOAL 不做真实出网调用**（不需要 `.env` 凭据；依赖升级只需 pnpm 网络，在
    `pnpm install --frozen-lockfile` 之外**不得**手工装包）。
    (11) **边界**：GOAL-001…015 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-015 的 13 条人工面 + 承继残余
    **原样保留**（本 GOAL 只把已拍板的那些写成判据 / 文档，其余继续挂着）。
objective: >
    把用户按简报建议列拍板的七项决定**落地为可复核的工程事实**——三项「维持现状」类决定
    （D-01 / D-02 / D-08）从「口径」变成**机械判据**，三项文档类决定（D-07 / D-09 / D-12）
    从「悬空 / 缺依据」变成**在位且可引用的文档**，一项依赖决定（D-03）从「明文禁令」
    变成**已执行的 high 升级 + 全量门证据**。具体六件交付物——(1) **D-01(b) 判据化**：
    「缺执行体 ⇒ preflight 逐字点名能力」成为反向搜索 + 行为证据成对的机械判据，**既有
    点名实现一字不动**；(2) **D-02(b) 口径判据**：钉住「读能力逐条授权、不成类放行」，
    含一条「**没有**类别级规则」的否定判据，**零策略面改动**；(3) **D-03(b) high 依赖升级**：
    4 条 high 升到已修复版本（限 patch/minor；主版本跳跃的条目**不做并登记**），
    证据 = lockfile 解析版本变化 + 全量 web 门 + m0 + CI 六 job；(4) **D-07 + D-08 + D-09
    固化**：ADR-0031 补「否证条件」节（`Status` 不变）+ D-08 维持决定的引用依据 +
    新增 **ADR-0032** 记录非 ASCII 路径豁免；(5) **D-12 威胁模型草案**：`docs/security/`
    的授权面（BOLA / BFLA）增量章节，写明**覆盖范围 / 未覆盖范围 / 下一步 (a) 的范围与代价**，
    **零代码 / 零门禁改动**；(6) **收口复检 + 残余登记**：两棵树同结论的独立复检脚本 +
    m0 可支持终态行（**如实标注哪棵树、哪种跑法**）+ 13 项 `D-NN` 终态表。
    **硬约束**：不放宽任何判据 / 门禁 / 放行面 / 阈值；不新增任何策略面 allow 或类别级规则；
    不改 `ADR-0031` 的 `Status`；不改 `test_m2_audit.py` 的镜像一致性判据；不改 Canonical
    State 边界；默认 runtime 仍为 Fake、默认 CI 仍离线；**本 GOAL 零真实出网调用**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **D-01(b) 判据化**：把「缺执行体 ⇒ preflight **逐字点名**哪个能力没人执行」钉成
      **机械判据**。判据口径 = **反向搜索 + 行为证据成对**：① 构造一个「某能力无 provider」
      的计划 ⇒ 报告含 `TOOL_UNAVAILABLE` 且消息**逐字点名该能力**；② **反证成对**——
      补上 provider ⇒ 该 finding **消失**（同一计划、同一判据、只改供给面）。
      **既有实现（`packages/application/preflight/checks.py` 的 `check_tools`）不得改动**；
      若判据要求改点名词，属**改产品行为** ⇒ **停下并登记**，不自行改。
    verify: >-
      离线判据（默认门可跑、零出网）：① 新增判据测试文件，逐字断言
      `TOOL_UNAVAILABLE` + 点名词，并断言「补 provider ⇒ finding 消失」；
      ② **反向搜索证据**：全仓搜索点名句的**唯一来源**（证明它来自单一实现点、不是多处
      巧合），把搜索命令与输出留档；③ **按压判据自身**：把消息模板改坏（临时变体，
      不改仓库文件）⇒ 判据判红；④ `git diff` 证明 `checks.py` 与 `policy_check.py`
      **零改动**。
    status: PASS
    status_note: >-
      2026-09-25 cycle 1 收口（`PLAN-20260925-168` → **DONE**；复检
      `RECHECK-20260925-169` = **PASS_WITH_WARNINGS**；工程记忆 `MEM-20260925-134`）。
      判据 `tests/application/preflight/test_missing_executor_is_named.py` **`4 passed`**：
      走**产品入口 + 出厂目录**（`services.api.catalog` + `compile_and_preflight`），
      缝为空（`tool_providers={}` = D-01(b) 的生产形态）时 6 条 `ToolRequirement`
      **逐条**被 `no provider is available for capability {能力名}` 点名（归属
      `phase:{phase_id}`）；恢复出厂 provider ⇒ **点名全部消失且该码计数归零**（成对反证）；
      **反向搜索**该模板在生产源里**只命中**
      `packages/application/preflight/checks.py` 一处（排除测试 / 夹具目录，理由写进判据）；
      按压（内存内改坏模板）⇒ 匹配器判空。**产品代码零改动**（`checks.py` 一字未动）。
      **残余**：另两条同码链（编译面的 `no tool provider exposes capability …`、
      健康 / 信任面的 `no healthy provider is available …`）**不**在本判据面内。
  - id: EC-02
    criterion: >-
      **D-02(b) 口径判据**：钉住「读能力**逐条授权**、**不成类放行**」。判据口径 =
      ① 策略面**逐条**规则的存在性（每条 allow / allow_with_constraints 的 `capability:`
      都是**具体能力名**）；② 一条**否定判据**证明**没有**类别级规则——`examples/config/policy.yaml`
      的 allow / constraints 里**不存在** `read.*` / 通配 / 前缀形式的 capability；
      ③ 引 `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表（**该登记 = 15 条**）作为
      证据面。**零策略面改动**：`examples/config/policy.yaml` 与 `_CAPABILITY_SCOPE`
      **都不得**出现在本 GOAL 的 diff 里。
    verify: >-
      离线判据：① 新增 / 扩充判据测试，断言「每条策略规则的 capability 是具体名」+
      「不存在类别级 / 通配 capability」；② **按压**：以临时变体（内存内构造，不改仓库文件）
      注入一条 `read.*` 规则 ⇒ 判据判红；③ 差集表 15 条与判据同源（引用计数一致）；
      ④ `git diff --name-only` 证明两个策略面文件**不在**本 GOAL 的改动集里。
    status: PASS
    status_note: >-
      2026-09-25 cycle 2 收口（`PLAN-20260925-170` → **DONE**；复检
      `RECHECK-20260925-171` = **PASS_WITH_WARNINGS**；工程记忆 `MEM-20260925-135`）。
      判据 `tests/application/preflight/test_read_grant_is_per_item.py` **`4 passed`**：
      ① **逐条形态**——策略面每个 `capability:` 都是词表（46 项）的**精确成员**，且**没有**
      任何规则的能力是另一条的**段前缀**（`read` 覆盖 `read.x` = 成类放行的结构特征）；
      ② **否定判据可被按压**——注入 `read.*` / `literature.` ⇒ 检测器**必须命中**；
      ③ **证据面**——差集表的「该登记」行**恰好 15 条**、全为读类、且**一条都没被放行**；
      ④ 读类放行逐条可枚举。**零策略面改动**：`examples/config/policy.yaml` 与
      `packages/application/preflight/policy_check.py` 的 `git status` 输出行数 = 0、
      `git diff --stat` 为空（判据只读，按压用内存内字典）。
      **m0 首跑两处红已逐条归因**：① 本 cycle 自己的 `mypy [no-any-return]`（已修：
      `.get("policy")` + 形状守卫）；② live 检索用例的上游 TLS 瞬时红（归类 (ii)
      环境专属 ⇒ 复跑，**判据未动**），并登记为 **`W-7`**。
  - id: EC-03
    criterion: >-
      **D-03(b) high 依赖升级**：**4 条 high** 升到已修复版本（**限 patch / minor**；
      落在**主版本跳跃**的条目**不做**，如实登记为下一轮输入，**不改判据、不降级其余项**）。
      判据 = `pnpm-lock.yaml` 的**解析版本变化**（逐包 before → after）+ **全量 web 门**
      （lint / typecheck / unit / build / stub e2e / live e2e）+ **m0 全绿** + CI 六 job 全绿。
      设计基线若漂移 ⇒ 按既有流程**强制重生成 + 目检**（**不得**调容差）。
    verify: >-
      ① 升级前后 `pnpm-lock.yaml` 的解析版本对照（含 `package.json` 声明面变化）；
      ② 全量 web 门逐条留档（命令 + 结论）；③ m0 终态行（**标明树与跑法**）；
      ④ CI：M0 六 job + CodeQL 到终态；⑤ **R-2 复查**：依赖升级后默认门**仍不得**看到凭据
      （`tests/egress_guard.py` 不得因升级而失效）；⑥ 未升级条目的**逐条理由**（主版本跳跃 /
      无 high 修复版本）。
    status: PASS
    status_note: >-
      2026-09-25 cycle 3 收口（`PLAN-20260925-172` → **DONE**；复检
      `RECHECK-20260925-173` = **PASS_WITH_WARNINGS**；工程记忆 `MEM-20260925-136`）。
      **4 条 high 全是 `vite`**（`first_patched_version` = `6.4.2` / `6.4.3`），一次上移
      `vite` **`6.3.5 → 6.4.3`**（6.x 内 minor）同时覆盖全部 4 条；`pnpm-lock.yaml` 的 diff
      **9 增 9 删**只含 `vite` 与 `@vitejs/plugin-react` 的 peer 引用行
      （实际安装版本经 `node -e` 复核 = `6.4.3`）。全量 web 门：根 `pnpm run check` = **exit 0**；
      web `lint`/`typecheck`/`test`/`build` **全 PASS**；**stub e2e `98 passed`**
      （**含结构签名门 ⇒ 设计基线零漂移**）；**live e2e `53 passed`**。`R-2` 复查 =
      **`3 passed`** + `egress guard judged 0 / blocked 0` ⇒ 升级后默认门**仍不得**看到凭据。
      **越界项如实登记（不做）**：`undici`（`5.29.0 → 6.24.0+` = **主版本跳跃**，且无 high）、
      `yaml`（patch 但**非 high**）⇒ 排下一批；剩余 19 条（13 medium + 6 low）原样保留。
  - id: EC-04
    criterion: >-
      **D-07 + D-08 + D-09 决定固化**（三处文档在位且可引用）：① `ADR-0031` 补一节
      **「否证条件」**——写清什么证据会否证它 / 什么条件下应转 `Accepted` 或撤回；
      **`Status` 保持 `Proposed` 不变**；② **D-08** 的维持决定写成**可引用依据**
      （`ModelCompatibilityProfile` 维持派生视图；含「若要建一等域实体**必须先出 ADR**
      说明 Canonical State 的迁移与回滚」），并钉一条判据 / 登记使下轮**不再重复提问**；
      ③ 新增 **ADR-0032** 记录**非 ASCII 路径豁免**（30 条已跟踪路径、**不重命名**、
      引用 AGENTS.md §13「既有历史路径不批量重命名」）；④ `docs/INDEX.md` 登记（该目录既有
      ADR 清单格式）。
    verify: >-
      ① 三处文档在位 + 各自**结构判据**（ADR-0031 含「否证条件」节且 `Status: Proposed`
      未变；ADR-0032 含豁免条目数与 §13 引文；D-08 依据含「先出 ADR」要求）；
      ② `docs/INDEX.md` 的 ADR 清单登记 ADR-0032（若既有格式要求）；
      ③ **`Status` 不变的反证**：逐字节对照 ADR-0031 的 `Status:` 行；
      ④ 规模门禁自查（450 / 50 行）与治理 `validate.py` 绿。
    status: PASS
    status_note: >-
      2026-09-25 cycle 4 / PLAN-20260925-174 / RECHECK-20260925-175（`PASS_WITH_WARNINGS`）。
      ① `ADR-0031` 增 `## 否证条件（什么证据会否证本 ADR / 何时该改判）`（三个出口：
      取消两个 D 依赖后仍成立 ⇒ 转 `Status`；事实消失 ⇒ 撤回；维持条件不变 ⇒ 保持），
      **`Status` 仍为 `Proposed`**（第 3 行逐字未动；全文无 `Status: Accepted`）；
      ② `MODEL_COMPATIBILITY.md` §9 记下 D-08(b) 决定（维持派生视图 + 三条理由 + 代价登记 +
      `### 若要改成一等域实体（选项 (a)）的前置条件` 要求 **`必须先出 ADR`** 写明迁移 / 回滚 /
      一致性判据），`DOMAIN_MODEL.md` §5 加一段指回；
      ③ **`ADR-0032-legacy-non-ascii-path-exemption.md`** 新建（`Status: Accepted`，
      30 条逐条清单、引用 `AGENTS.md` §13、记下 `core.quotepath` 枚举陷阱），并登记
      `docs/INDEX.md`（同时给 `ADR-0031` 行加注「补否证条件、`Status` 仍未变」）；
      ④ 判据 `tests/tooling/test_landed_decisions_are_citable.py` **`6 passed`**（含
      非 ASCII 现实↔清单**双向**比对、枚举陷阱双数断言、按压态）；
      ⑤ `docs_consistency_check` 首跑 2 条 `[backtick-ref]` 假路径 ⇒ 改为指向真实对象 ⇒
      **`DOCS-CHECK PASS: 6 deterministic checks`**（**未**动门禁）；
      ⑥ `ruff` / `ruff format --check` / `mypy`（1016 files）与 `tests/tooling` +
      同源判据 **`1162 passed`** 全绿；`egress guard` = `blocked 0`（本 EC 零出网）。
      **零越界**：diff 仅 5 个 docs 文件 + 1 个新判据；不含 `AGENTS.md`、策略面、产品代码、
      门禁脚本、任何 rename、任何 `Status` 改动。**警告**：W-1 = D-07 的 `Proposed`
      **仍是未拍板项**（补否证条件 ≠ 拍板）；W-2 = D-09 的豁免**只管既有 30 条**，
      新建非 ASCII 仍判红（且本 EC 未验证「新路径确实被拦」）。
  - id: EC-05
    criterion: >-
      **D-12 威胁模型草案**：在 `docs/security/THREAT_MODEL.md` **增量补** BOLA / BFLA /
      授权面章节（或同目录新文档 + 交叉引用），写明 **覆盖了什么 / 未覆盖什么 /
      下一步 (a) 的范围与代价**。**不改代码、不改门禁、不加判据**——该 EC 的 diff
      **只含文档**。
    verify: >-
      ① 文档在位 + **关键结构判据**：含「未覆盖范围」节、含 BOLA / BFLA 字样、
      含与 **M18 边界**的关系；② **零代码 / 零门禁改动的证据**：`git diff --name-only`
      该 EC 的提交**只含 `docs/` 下的文档**；③ 现有 106 行的既有内容不被删除（增量）；
      ④ 治理 `validate.py` 绿 + `DOCS-CHECK` 不因新文档判红（backtick 引用须可解析）。
    status: PASS
    status_note: >-
      2026-09-25 cycle 5 / PLAN-20260925-176 / RECHECK-20260925-177（`PASS_WITH_WARNINGS`）。
      `docs/security/THREAT_MODEL.md` **106 → 252 行**，新增 `## 6. 授权面威胁建模
      （BOLA / BFLA）—— 文档级草案`：6.1 术语 / 6.2 覆盖了什么（7 条带出处的事实）/
      **`### 6.3 未覆盖范围`**（8 条）/ **`### 6.4 与 M18 边界的关系`** / 6.5 若取 (a)
      的范围与代价 / 6.6 引用约束。**纯增量**：`git diff --numstat` = **146 增 / 0 删**
      （既有 106 行一字未删）。`BOLA` / `BFLA` 命中 **6** 处；`M18` 关系节在 `:194`。
      **diff 只含 docs**：改动集 = `docs/security/THREAT_MODEL.md` + `docs/INDEX.md`
      （Security 行加注）——**零代码 / 零门禁 / 零判据 / 零阈值 / 零 allow**。
      `DOCS-CHECK PASS: 6 deterministic checks`（首跑即过）。
      核心事实（均带出处）：控制面 **124 条路由逐条零授权依赖**（`Depends(` / `Security(`
      / `current_user` / `HTTPBearer` / `APIKeyHeader` 全仓**零命中**）、**无调用方认证**
      （唯一请求级强制项是 `Idempotency-Key`，是幂等非身份）、策略**只到能力级不到对象级**
      （`packages/domain/policy.py:29` + `packages/application/policy/native.py:47`，
      `examples/config/policy.yaml:2` = `default_effect: DENY`）、域实体**无归属概念**
      （`packages/domain/run.py:37` / `projects.py:5` / `artifacts.py:90` 仅溯源）。
      **M18 边界**：`docs/roadmap/MILESTONES.md:971` 定义为多用户/组织/RBAC，
      `:973` = **DEFERRED「不标记部分完成」**，`:980` 触发条件 ⇒ 授权面空白是
      **「按 M18 deferral 有意未做」而非疏漏**；未来落点唯一 = `docs/security/IDENTITY_AND_ACCESS.md`。
      **警告**：**W-1 = 本节不是安全性只是可见性**（未提高任何访问控制强度）；
      **W-2 = 会过期且不会自己红**（(b) 的固有代价）；**W-3 = (a) 的最小形态也可能立刻全红**
      （124 条路由全不合规 ⇒ 只能退化成「现状白名单快照」，而白名单本身就是待还的债）；
      W-4 = `FRAMEWORK_MANIFEST.json` 该条发布快照**未**刷新（刷新属发布动作；
      实测该快照本就已过期 220 条中 131 条）；W-5 = `R-3` / `R-M1` / `R-D1` 原样保留。
      **6.6 口径围栏**：不得引作「已做威胁建模」「授权面已覆盖」或任何安全结论。
  - id: EC-06
    criterion: >-
      **收口复检 + 残余登记**：① 独立复检脚本在**当前树 + 干净 checkout** 上**同判据同结论**；
      ② m0 到**可支持的终态行**（as-is 若仍因 `R-3` ⇒ **如实标注是哪棵树、哪种跑法**，
      **不得**含糊写成 23/23）；③ 治理 `validate.py` 绿；④ CI 台账到终态（M0 六 job +
      CodeQL，含 `run_attempt`）；⑤ **13 项 `D-NN` 的终态表**落记录（每项：拍板结论 /
      本轮是否实施 / 依据 / 不做会怎样）；⑥ 承继残余**原样保留**。
    verify: >-
      ① 复检脚本两棵树实跑输出（同判据、同结论）；② m0 终态行 + 逐字节 tree 标注；
      ③ `validate.py` = 治理验证通过；④ CI 台账逐 run 逐 job 实查；
      ⑤ 13 项 `D-NN` 终态表在位且与简报条目一一对应；⑥ 独立 RECHECK ∈
      {`PASS`, `PASS_WITH_WARNINGS`}。
    status: PASS
    status_note: >-
      2026-09-25 cycle 6 / PLAN-20260925-178 / RECHECK-20260925-179（`PASS_WITH_WARNINGS`）。
      **7 条 AC 全部成立**：**AC-1 两棵树同结论**（同一脚本 `--root` 指向工作树与
      `c50ee97` 的干净 `git worktree` checkout，**去掉 pytest 耗时后 `diff` 为空** ⇒
      逐 EC 结论逐字相同；两树 `CONCLUSION failures=0`、`REALITY non_ascii=30`）；
      **AC-2 脚本非恒真**（终态表未落盘时逐条报出 **13** 条缺失）；
      **AC-3 m0 双终态行**（**as-is = 22/23**，唯一红 = `framework/validate_bundle`（`R-3`），
      `PASS [` = 23；**代管后 = 23/23**，`PASS [` = 24、`FAIL` = 0、逐字节复核一致）；
      **AC-4** 13 项 `D-NN` 终态表在位（已实施 4 / 部分 2 / 未实施 6）；
      **AC-5** `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS: 6 deterministic checks`；
      **AC-6** 承继残余 `R-3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-7` 逐条在位；
      **AC-7** 入库改动只含记录面（**无**产品代码 / 门禁 / 策略面 / 判据 / 阈值 / 依赖改动）。
      **警告**：W-1 = 收口不是清零（未授权六项与全部残余**原样保留**）；
      W-2 = 两行**不可互换**（只写一个「23/23」就是藏起 as-is 的红）；
      W-3 = 干净 checkout 复检的前提是本仓**没有** editable 安装（靠 `pythonpath = ["."]`）；
      W-4 = 复检脚本会随被测面漂移，改它去迁就现实须按「改判据」同等级别审；
      W-5 = 两处遗留观察项（Temp 里其它 GOAL 的临时检出、`FRAMEWORK_MANIFEST.json` 发布快照过期）。
      **「本 cycle 进行中」的旧记录（如实保留在 RECHECK-179 的时序说明里）**：
      cycle 6 前半曾**刻意不记 PASS** —— 「干净 checkout」那一半必须先有提交才能检出。
      AC-2（复检脚本**非恒真**：终态表未落盘时 `EC-06 FAIL` 并逐条报出 13 条缺失）、
      AC-3（m0 **双终态行**：as-is = `FAILED: 1 check(s): framework/validate_bundle=1`
      ⇒ **22/23** 且点名 `R-3`；代管后 = `PASS: profile=m0; 23 deterministic checks`
      + 逐字节复核一致；`PASS [` 行数 as-is = 23 / 代管 = 24 ⇒ 两行**不可互换**）、
      AC-4（13 项 `D-NN` 终态表已落本文件，含「已实施 4 / 部分 2 / 未实施 6 + 1」汇总）、
      AC-5（`validate.py` = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks`）、
      AC-6（承继残余 `R-3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-7` 逐条在位）、
      AC-7（改动集只含记录面 + gitignored 的 `scratch/`）。
      **AC-1 的「干净 `git worktree` checkout」那一半尚未跑**——它必须先有本 cycle 的提交
      才能检出 ⇒ 按「未实跑不得记 PASS」**留到复检 `RECHECK-20260925-179` 里补**，
      本 EC 在此之前**保持 IN_PROGRESS**。当前树那一半已取到
      `CONCLUSION failures=0`（`scratch/goal016-c6-recheck-worktree.txt`，
      六 EC 全 PASS、`REALITY non_ascii=30`）。
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据使其通过
    - 放宽 `tests/egress_guard.py` 的目的地判定 / 豁免 fake-IP（`198.18.0.0/15`）或任何目的地址类别
    - 放宽 `framework/validate_bundle`（governance-check）的检查项或扫描范围（含 D-10）
    - 放宽 m0 任一 check 的阈值（含 450 行 / 50 行规模门禁；含 D-13 的 RSS / 线程阈值）
    - skip/删除测试、加 xfail、或调整收集顺序以掩盖顺序依赖
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何策略面 allow 或**类别级规则**（D-02 明文不取）
    - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）
    - 改 `ModelCompatibilityProfile` 的 Domain 面 / Canonical State 边界（D-08 明文维持派生视图）
    - 新增依赖或改上游 pin**超出 D-03 授权范围**（D-03 只授权 high 在 patch/minor 内的升级）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    放宽任一判据 / 门禁 / 放行面 / 阈值（含 `tests/egress_guard.py` 的目的地判定、
    `framework/validate_bundle` 的检查项、m0 任一 check 的阈值）—— **立即 BLOCKED**
  - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据 —— **立即 BLOCKED**
  - >-
    以 skip / xfail / 删除测试 / 调整收集顺序的方式让顺序失败「消失」—— **立即 BLOCKED**
  - >-
    **改门禁 / 阈值 / 作业结构**（D-10 的 `validate_bundle` scoping、D-13 的 RSS 与线程阈值、
    CI 作业拆分）—— 均**需另行授权**，触及即 **BLOCKED**
  - >-
    放宽 §9 默认 deny，或新增任何策略面 allow / 类别级规则（D-02 明文不取）—— **立即 BLOCKED**
  - >-
    **新增依赖或 pin 变更超出 D-03 授权范围**（D-03 只覆盖「high 且在 patch/minor 内的升级」；
    `undici` 5.x → 6.x 这类**主版本跳跃**、以及任何新的 dependency）—— **立即 BLOCKED**
  - Canonical State 边界（含 D-08 若被改成一等域实体）—— **立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；只做「显式配置才启用」）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - 本 GOAL 出现真实出网调用（依赖升级只允许 pnpm 网络）—— 需要真实端点的判据不属于本目标
  - 明文凭据泄露（**即使是可弃用的免费额度**）—— 立即停止并报告
child_plans:
  - .cursor/plans/tasks/PLAN-20260925-168-missing-executor-must-be-named.md
  - .cursor/plans/tasks/PLAN-20260925-170-read-grant-stays-per-item.md
  - .cursor/plans/tasks/PLAN-20260925-172-upgrade-high-dependency-vite.md
  - .cursor/plans/tasks/PLAN-20260925-174-landed-decisions-are-citable.md
  - .cursor/plans/tasks/PLAN-20260925-176-authorization-surface-threat-model-draft.md
  - .cursor/plans/tasks/PLAN-20260925-178-goal-016-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-179-goal-016-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-134-naming-contract-needs-a-pair-and-a-single-source.md
  - .cursor/memory/entries/MEM-20260925-135-negative-criteria-need-a-pressable-detector.md
  - .cursor/memory/entries/MEM-20260925-136-pin-bump-needs-a-resolved-version-and-a-full-gate.md
  - .cursor/memory/entries/MEM-20260925-137-exemption-needs-an-adr-and-a-counter.md
  - .cursor/memory/entries/MEM-20260925-138-threat-model-draft-needs-a-scope-fence.md
  - .cursor/memory/entries/MEM-20260925-139-closeout-needs-two-trees-and-two-terminal-lines.md
---

## 目标与退出标准

**一句话**：把用户拍板的七项决定**落地为可复核的工程事实** —— 三项「维持现状」类决定
（D-01 / D-02 / D-08）从「口径」变成**机械判据**，三项文档类决定（D-07 / D-09 / D-12）
从「悬空 / 缺依据」变成**在位且可引用的文档**，一项依赖决定（D-03）从「明文禁令」变成
**已执行的 high 升级 + 全量门证据**。

**建档当日已核实的文件层事实（决定可行性与判据形态）**：

1. **D-01 的点名逻辑确实已在树**：`packages/application/preflight/checks.py` 的
   `check_tools` 在 `not requirement.provider_ids` 时追加
   `PreflightFindingCode.TOOL_UNAVAILABLE` + `f"no provider is available for capability
   {requirement.capability}"`。⇒ 交付是**判据 + 反向搜索证据**，**不是**新增逻辑。
   （**若判据要求改点名词 ⇒ 停下登记，不自行改产品行为**。）
2. **D-02 的证据面已在树**：`docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表已给出
   **该登记 = 15 条**（`agent_run.read`、`budget.read`、`citation.inspect`、
   `citation.validate`、`claim.read`、`dataset.read`、`deliverable.read`、`experiment.read`、
   `experiment_plan.read`、`provenance.read`、`research_map.read`、`research_state.read`、
   `review.read`、`run.read`、`target.read`），且该表由
   `tests/application/preflight/test_policy_surface_difference_set.py` 与文档**同源**比对。
3. **D-03 的 as-is 事实**（`scratch/goal014-c4-residual-probe.txt` 实测，2026-09-25）：
   Dependabot **open 告警 23 条** = `high 4` / `medium 13` / `low 6`；包分布
   `vite` 14 / `undici` 8 / `yaml` 1。**4 条 high 全部是 `vite`**
   （#5 / #7 在 `apps/web/package.json`，#18 / #20 在 `pnpm-lock.yaml`；
   `first_patched_version` = `6.4.2` / `6.4.3`）。as-is 解析版本 `vite@6.3.5`
   ⇒ **修复版本落在 6.x 内的 minor**（`6.3.5 → 6.4.3`）⇒ **属于 D-03(b) 可执行范围**。
   其余两条包：`undici` as-is `5.29.0` 而修复版本为 `6.24.0+` ⇒ **主版本跳跃**（**不做**，
   且它们没有 high）；`yaml` as-is `2.8.1` 而修复版本 `2.8.3` ⇒ patch（**非 high**，排下一批）。
4. **D-07 的 as-is**：`docs/adr/ADR-0031-toolpack-capability-policy.md` 第 3 行
   `Status: Proposed`，第 68 行自述「整体保持 `Status: Proposed`」⇒ 补「否证条件」节时
   **`Status` 一字不动**。
5. **D-09 的编号**：`docs/adr/` 现有最大编号 = `ADR-0031` ⇒ 新 ADR 编号 = **`ADR-0032`**；
   `docs/INDEX.md` 有既有 ADR 清单格式（`- \`adr/ADR-00NN-slug.md\` — 说明`）。
6. **D-12 的 as-is**：`docs/security/THREAT_MODEL.md` = **106 行**，且
   `BOLA` / `BFLA` / `越权` / `多租户` 字样命中数 = **0** ⇒ 交付是**增量章节**。
7. **不动项（明文不授权）**：`R-3`（`framework/validate_bundle` 扫到仓库外 gitignored 文件
   ⇒ as-is 本地 m0 停在 **22/23**）与 `D-13`（CI 上 `tests/observability/test_telemetry_overhead.py`
   的整进程 RSS 阈值偶发红）**原样保留**：本 GOAL 只**引用 / 登记**，**不改**门禁、判据或阈值。

**本 GOAL 的承继起点（事实，不是待办）**：GOAL-015 的 **13 条人工面 + 承继残余
（`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` / `R-N1`）+ `W-1…W-6`** 原样保留；
本 GOAL **不**宣称它们已解决，只把其中**用户已拍板的七项**落地。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **D-01(b)** 缺执行体 ⇒ 逐字点名（机械判据） | 判据测试 + 反向搜索 + 成对反证 + `checks.py` 零改动 | **PASS** |
| EC-02 | **D-02(b)** 读能力逐条授权、不成类放行 | 逐条存在性判据 + 「无类别级规则」否定判据 + 15 条差集表引用 | **PASS** |
| EC-03 | **D-03(b)** 4 条 high 升级（patch/minor） | lockfile 版本对照 + 全量 web 门 + m0 + CI 六 job | **PASS** |
| EC-04 | **D-07 + D-08 + D-09** 决定固化 | ADR-0031「否证条件」节 + D-08 依据 + ADR-0032 + INDEX 登记 | **PASS** |
| EC-05 | **D-12** 威胁模型草案（**零代码 / 零门禁**） | BOLA / BFLA / 授权面章节（覆盖 / 未覆盖 / (a) 代价） | **PASS** |
| EC-06 | 收口复检 + 残余登记 | 两树复检 + m0 可支持终态行 + 13 项 `D-NN` 终态表 + CI 台账 | **PASS** |

**依赖关系**：EC-01 / EC-02 / EC-05 互相独立（判据 / 文档）；EC-03 是**唯一动产品依赖**的
EC，其 web 门与 m0 证据面会被 EC-06 复用；EC-04 三处文档独立于其余 EC；EC-06 **最后**做。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 零真实出网调用**（依赖升级只用 pnpm 网络；不需要 `.env` 凭据）：
若某判据需要真实端点 ⇒ 该判据**不属于本目标**，如实登记为下一轮输入。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-016-*.md` 已存在 ⇒ 跳过建档，直接进循环。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260925-016`
  并投影 `ALL_PLAN`，**同一提交**）。子 PLAN 编号续**全局 NNN**（建档当日最大 = `RECHECK-167`
  ⇒ 下一个 PLAN / RECHECK 从 **168** 起）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查**规模门禁**（50 行函数 / 450 行文件 —— 建档当日实测**四个文件
  正好 450 行零余量**：`services/api/composition.py`、`adapters/postgres/workflow_engine.py`、
  `adapters/execution/docker_backend.py`、`packages/application/run_orchestration/service.py`
  ⇒ 改动它们**必须先搬代码**）与**快照类门禁**（OpenAPI / 设计基线；
  **EC-03 升级 `vite` 后尤其要盯设计基线是否漂移** —— 漂移则按既有流程
  **强制重生成 + 目检**，**不得**调容差），再跑 `make validate-all`（m0 全量 23 项，
  **独占运行**，避免 `evolution_state.json` 的 `WinError 5`）+ 受影响定向套件 +
  web 门（lint / typecheck / unit / build / stub e2e / live e2e）。
  **默认门一律离线**（`tests/egress_guard.py` 是结构判据：默认门出现非环回目的即判红 ——
  **不得为本地变绿而放宽它**；**EC-03 依赖升级后尤其要复查 `R-2` 的修复是否仍有效**：
  默认门**不得**能看到凭据）。
  **本地不绿不得 push**（承 `MEM-20260924-125`：先等本地门到终态再推送）。
  **写记录时不要跑 m0**（承 `W-5`：m0 运行中改工作树会让 `framework/validate` 判红）。
- **④ commit**：显式路径；**绝不 `git add -A`**（并发工作树）。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（只推 main）→
  轮询 CI 到终态（`scratch/poll_ci_all.sh <sha>`：M0 六 job + CodeQL），记录 run id / 链接 /
  逐 job 结论 / **`run_attempt`**（**flake 判定必须靠同一代码的复跑对照**，不得只看一次结论）；
  **本机无法验证记 PENDING 并停止推进**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；超 `fix_policy` 或命中 `escalation_triggers`
  ⇒ `status: BLOCKED`。
- **⑦ 回写**：EC / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史；
  **收尾前必须回写**；`child_plans` 与 `memory_entries` 每轮与实际派生对齐。
  **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
  **CI 台账沿用既有闭合约定**：写下本条的那个提交自身的 run 只在**回合汇报**记账。

**撤回纪律**（承 GOAL-011…015）：改共享夹具 / 契约 / **依赖**时先数清谁拿它的
**失败形态**当夹具（既有教训：「补全被复用的参考资产 = 改它的失败形态」；EC-03 改 lockfile
前先数清谁依赖被升级包的**失败形态**）；CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**，
不改那批夹具迁就；撤回复核用**逐字节 `git diff`** 证明。
**本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据必须在 **Linux 侧**
（CI）复验（**EC-04 的 ADR 条目数、EC-05 的文档结构判据尤其要复验**）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，禁改断言迁就 |
| **依赖升级引发的红**（本 GOAL 的 EC-03 主场） | `vite` 升级后 web 构建 / 设计基线 / e2e 判红 | 先判**是否真缺陷**：真缺陷 ⇒ 修产品；**基线漂移** ⇒ 按既有流程**强制重生成 + 目检**（**不得**调容差）；无法在授权内解决 ⇒ **撤回该条升级**并如实登记（**不改判据、不降级其余项**） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`R-3` 外来文件、`R-2` 凭据可见性、**`D-13` 的 RSS 阈值偶发红**） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 归因；**`D-13` 类**按「偶发红 ⇒ 复跑 + 登记」处置（**判据与阈值一字不动**）；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态。**未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**改门禁 / 阈值 / 作业结构**、
  **pin 变更超出 D-03 授权范围**、**放宽 §9 默认 deny**、**Canonical State 边界**、
  **把真实 runtime 设为默认**、改 `ADR-0031` 的 `Status`）、同一失败签名超过
  `fix_policy` 上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles` 个 cycle
  未推进任何 EC ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含 13 项 `D-NN` 终态表）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。
**本节照抄 GOAL-015 的 13 条 + GOAL-015 特有项 + 承继残余**，并在每条注明**本 GOAL 的
拍板结果**（用户按简报建议列拍板，2026-09-25）。

**GOAL-015 的 13 条编号项（原样承继 + 本 GOAL 拍板结果）**：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——**已拍板：D-07 取 (b)**
   ⇒ 维持 `Proposed` + 补「否证条件」节（**本 GOAL 的 EC-04 实施**）；**`Status` 不变**、
   不实施其内容。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——**已拍板：D-12 取 (b)** ⇒ 先出**文档级草案**
   （**本 GOAL 的 EC-05 实施**）；**不改代码、不改门禁、不加判据**；(a) 的范围与代价**写进
   草案**，是否做 (a) 仍**待另行拍板**。
3. **`artifacts/` token 清理**——**【已完成】**（GOAL-011 获删授权；建档实测：
   `git ls-files artifacts/` = 0）⇒ **本项无待办**。
4. **450 行纪律的贴线文件**——**已拍板：D-05 取 (b)** ⇒ 维持「触线即拆」（只在本循环里
   需要改它们时先搬代码）；**本 GOAL 不拆分**。**EC-03 若需改这四个文件之一 ⇒ 必须先搬代码**。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——**已拍板：D-03 取 (b)** ⇒
   **批升级、high 先升**（**本 GOAL 的 EC-03 实施**，范围**仅限 high 且在 patch/minor 内**）。
   **授权边界**：`undici` `5.29.0 → 6.24.0+` 是**主版本跳跃** ⇒ **不做**（如实登记为下一轮输入）；
   `yaml` `2.8.1 → 2.8.3` 是 patch 但**非 high** ⇒ 排下一批；**任何越界 pin 变更 = BLOCKED**。
6. **hook 侧 L3 门**——**未拍板**（简报建议 (a)「先修误报面」；**本 GOAL 不实施**，
   D-04 原样挂着）。
7. **把真实 runtime 设为默认**——**标准禁令（无需拍板）**：默认必须仍是 Fake。
8. **为 anthropic 形态引入 SDK / 新依赖**——**标准禁令（无需拍板）**：需要新依赖即 BLOCKED。
9. **把凭据写进 CI**——**标准禁令（无需拍板）**：CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——**已拍板：D-08 取 (b)**
    ⇒ 维持**派生视图**；**本 GOAL 的 EC-04** 把该决定写成可引用依据（含「若要 (a) **必须先出
    ADR** 说明 Canonical State 的迁移与回滚」）⇒ **下轮不再重复提问**。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——**标准禁令（无需拍板）**：明文禁止。
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本）**——**【已完成】**
    （GOAL-011 获删授权并在建档当日执行完毕）⇒ **本项无待办**。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**——**已拍板：D-09 取 (a)**
    ⇒ **出一份 ADR 记录豁免**（**本 GOAL 的 EC-04 实施**，编号 **ADR-0032**）；
    **不重命名**、不触碰不可变历史资产。

**GOAL-015 特有的项（原样承继 + 本 GOAL 拍板结果）**：

- **路径 (B) 的 5 条重设计项**（`docs/roadmap/PATH_B_REFUTATION_RECORD.md`）——**已拍板：D-06 取 (c)**
  ⇒ 维持「已否证」原状；本循环**不重启**该路线，状态词原样保留。
- **`W-A` 之外的策略面放宽**——**已拍板：D-02 取 (b)** ⇒ **维持逐条**、**不成类预放行**、
  **不新增任何 allow**（**本 GOAL 的 EC-02 把该口径钉成判据**）。
- **门禁 scoping 的自我修正**——**已建议 (a) 但需另行授权**（D-10）：`validate_bundle` 是否
  排除 gitignored 工作区**本 GOAL 不改**，只把 `R-3` 作为**事实引用**；
  `R-3` 的现状（as-is 本地 m0 **22/23**）**原样保留**。**改门禁 = BLOCKED**。
- **本机环境的 DNS / 代理特殊性**（fake-IP `198.18.0.0/15`）——**不改机器网络配置**，
  也不改判据；只做归因与登记。
- **`M-1`（出厂组合根是否自己接执行体缝 `ApiDeps.tool_providers`）**——**已拍板：D-01 取 (b)**
  ⇒ **维持装配方补执行体**（生产路径 `tool_providers` 仍为空），交付是把「缺执行体 ⇒ preflight
  **逐字点名**能力」钉成机械判据（**本 GOAL 的 EC-01**）。
  **D-01 的 (a)（组合根自己接执行体缝）明确不取**——等 **D-11** 的开关语义定下来再谈。
- **live 判据的开门条件**——**未拍板**（简报建议 (a)「加显式开关」）：D-11 **本 GOAL 不实施**
  （会改判据语义 ⇒ 需另行授权）。**不得**改判据、**不得**改 live 用例的 skip 条件。
- **CI 资源阈值型判据的负载敏感性**——**已建议 (a) 但需另行授权**（D-13）：判据与阈值
  **一字不动**；本 GOAL 只**登记**，仅在出现 **≥2 次**同类偶发红时才提请 (b)。
  **改判据 / 阈值 / 作业结构 = BLOCKED**。
- **hook 侧 L3 检测层**（D-04）——**未拍板**；**本 GOAL 不实施**。

**承继的诚实边界（如实保留，不是待办）**：

- `R-F1`｜收敛 / 一致性判定含主观面时必须先**操作化**。
- `R-F2`｜真实数据 / 调用规模不足时的**诚实边界**。
- `R-F3`｜仓库外并发写者文件致 **as-is 本地 m0 可能停在 22/23**（等同 `R-3`）；
  CI 检出无 `scratch/` ⇒ **CI 不受影响**。未转绿前**不得**声称本地全绿。
- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  （EC-05 的威胁模型草案**不改变**本边界；草案须自带「未覆盖范围」节。）
- **`R-D1`｜Dependabot 告警**——`D-03` 只覆盖 **4 条 high**；剩余 19 条（13 medium + 6 low）
  与 `undici` 的主版本跳跃**原样保留**为下一轮输入。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，原样保留（`R-N1` 由 EC-04 的 ADR-0032
  固化为**可引用依据**，**不改变**「不重命名」的事实）。
- **`W-1…W-6`**（GOAL-015 的观察项，含 `W-6` = CI RSS 阈值偶发红）——原样保留。
- **`W-7`（本 GOAL cycle 2 实测新增，只登记不改）｜live 判据在「环境里恰好有凭据」时会**
  **真的出网**：`tests/e2e/test_run_chain_retrieval_live.py` 的 skip 条件只判「凭据在不在」
  ⇒ 本机持有有效凭据 ⇒ 全量 m0 里该用例**不 skip**，真的调 NCBI eutils（与出厂 LLM 端点）。
  cycle 2 的 m0 首跑即因上游 TLS 瞬时故障判红
  （`eutils connection failure: [SSL: UNEXPECTED_EOF_WHILE_READING]`），
  同一代码路径在 cycle 1 的 m0 **通过** ⇒ 归类 **(ii) 环境专属 / 上游瞬时**，
  处置 = 复跑 + 登记（**判据一字未动**）。
  **这是 `D-11` 证据面上的第二个数据点**（第一个 = GOAL-015 的 CI 红 run `36048265860`：
  CI 上放了一个**无效**凭据 ⇒ live 用例不再 skip ⇒ `AuthenticationError`）。
  **`D-11` 明文不在本 GOAL 授权内**（改判据语义需另行拍板）⇒ 本 GOAL **只登记**，
  **不得**改 skip 条件、**不得**改判据、**不得**把默认门变成「不出网」而不拍板。
  **本 GOAL 的口径**：本机全量 m0 的终态行因此**不是纯离线**的；如实标注，
  并在终态行里区分「哪条是环境红、哪条是代码红」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `4afb314`（**推送 tip**，推送区间 `a3b2cf3..4afb314`） | 治理 `validate.py` = `Cursor 治理验证通过` | M0 [36092961923](https://github.com/Eswink/research-system-new/actions/runs/36092961923) **六 job 全 success** + CodeQL [36092961168](https://github.com/Eswink/research-system-new/actions/runs/36092961168) **3/3 success**（`run_attempt=1`） | — | EC-01…EC-06 全 PENDING；七项判词已落 frontmatter；起点已定位（点名逻辑已在树 / 该登记 15 条 / 4 条 high 全是 `vite` 且修复版本在 6.x minor / `undici` 主版本跳跃 / ADR-0031 补节且 `Status` 不变 / ADR-0032 编号 / THREAT_MODEL 106 行零 BOLA-BFLA）。**建档时零代码改动**（只增本文件） | cycle 1 = **EC-01 D-01(b) 判据化** |
| 1 | PLAN-20260925-168（EC-01） | `1e2af55`（推送区间 `4afb314..1e2af55`） | 判据 `tests/application/preflight/test_missing_executor_is_named.py` **`4 passed`**（正向逐条点名 / 成对反证 / 单一来源 / 按压）；探针 `scratch/goal016_c1_probe.py`（只读、零出网）实证两条同码链与「恢复 provider ⇒ 计数 0」；`ruff check` = `All checks passed!`、`ruff format --check` = 已格式化；规模 + 命名门禁 = `1054 passed`；`egress guard` = `blocked 0`。**m0 两个终态行分开（冻结树）**：**代管后**（`R-3` 文件临时移出）= `PASS: profile=m0; 23 deterministic checks` + 逐字节复核一致（`size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）；**as-is** = **22/23**，唯一红项 = `framework/validate_bundle`，单条直跑复现的判词只有一条（`Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md`）⇒ 归因 = **`R-3`**（与本题改动无关）。日志：`scratch/goal016-c1-m0-quarantined.log` / `-quarantine-run.txt` | 见回合汇报（本 cycle 的推送 run 在其台账行；flake 判定按同一代码复跑对照） | **一次判据自身缺陷如实登记**：首版按**能力名**配对 ⇒ 被 `workspace.read`（**两个 phase** 都需要）判红 ⇒ 改成按 `(phase_id, capability)` 配对（**未**改产品代码） | **EC-01 = PASS**（`RECHECK-20260925-169` = `PASS_WITH_WARNINGS`；W-1 = 另两条同码链不在判据面内、W-2 = `R-3` 仍是本机 as-is 的预置红）。其余五个 EC 仍 PENDING；`M-1` / `D-10` / `D-13` 原样保留 | cycle 2 = **EC-02 D-02(b) 口径判据**（读能力逐条授权、不成类放行；零策略面改动） |
| 2 | PLAN-20260925-170（EC-02） | `c2bc8a4`（推送区间 `1e2af55..c2bc8a4`；`git pull --ff-only` 首次因 `SSL: unexpected eof while reading` 失败、重试成功） | 判据 `tests/application/preflight/test_read_grant_is_per_item.py` **`4 passed`**（逐条形态 / 否定判据可按压 / 15 条证据面 / 读类放行逐条可枚举）；**零策略面改动**取证：两个策略面文件的 `git status` 输出行数 = **0**、`git diff --stat` **为空**；`ruff check` = `All checks passed!`、`ruff format --check` = 已格式化；规模 + 命名门禁 + 定向回归 = **`1083 passed`**；`egress guard` = `blocked 0`。**m0 三跑（冻结树，代管 `R-3` 文件）**：第 1 跑 = `FAILED: 2 check(s): python/typecheck=1, python/tests=1`；第 2 跑 = `FAILED: 1 check(s): python/tests=1`；**第 3 跑 = `PASS: profile=m0; 23 deterministic checks`** + 逐字节复核一致（`size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）。日志：`scratch/goal016-c2-m0-quarantined.log` / `-c2b-` / `-c2c-` | **绿**：M0 [36099521368](https://github.com/Eswink/research-system-new/actions/runs/36099521368) **六 job 全 success** + CodeQL [36099519976](https://github.com/Eswink/research-system-new/actions/runs/36099519976) **3/3 success**（`run_attempt=1`） | **三处红如实登记（性质不同）**：① **本 cycle 自己的缺陷（已修）**——新判据 `policy_body()` 触发 `mypy [no-any-return]` ⇒ 改为 `.get("policy")` + `assert isinstance(body, dict)`（**加**形状守卫，**未**加豁免）；修后 `mypy` = `Success: no issues found in 1015 source files`。**教训**：定向套件绿不等于全量绿（`mypy` 只在全量门里跑）。② **环境 / 上游非确定（判据与代码均未动，两跑两签名）**——`tests/e2e/test_run_chain_retrieval_live.py::test_live_run_chain_retrieval_lands_a_real_identifier`：第 1 跑 `eutils connection failure: [SSL: UNEXPECTED_EOF_WHILE_READING]`、第 2 跑 `run-chain capability step failed: previous step carries no 'ids' ids for run-chain tool literature_read`；**成对对照**：隔离跑 **`1 passed` ×2**（`14.81s` / `37.31s`）、`git diff 1e2af55 -- tests/e2e packages adapters services examples` **为空**，且 `1e2af55` 的 m0 中它**通过**；**同一会话内 `git pull` 也命中同一 TLS 签名** ⇒ 归类 **(ii) 环境专属**（三条判定条件逐条成立）⇒ 复跑取终态（**未**动判据 / skip 条件 / 阈值），登记为 **`W-7`** | **EC-02 = PASS**（`RECHECK-20260925-171` = `PASS_WITH_WARNINGS`；W-1 = 本判据只判放行**形态**、不判「该不该放行」；W-2 = `R-3` 仍是本机 as-is 的预置红；**W-7 = live 判据会真出网且结论随环境变**，新登记）。其余四个 EC 仍 PENDING | cycle 3 = **EC-03 D-03(b) 4 条 high 依赖升级**（`vite` 6.3.5 → 6.4.3，minor；`undici` 主版本跳跃不做；`yaml` 非 high 排下一批）+ 全量 web 门 + m0 |
| 3 | PLAN-20260925-172（EC-03） | `8814b49`（推送区间 `c2bc8a4..8814b49`） | **解析版本对照**：`pnpm-lock.yaml` 的 `vite@6.3.5` → `vite@6.4.3`（diff **9 增 9 删**，只含 `vite` 与 `@vitejs/plugin-react` 的 peer 引用行）；实际安装 = `6.4.3`。**全量 web 门**：根 `pnpm run check` = **exit 0**；web `lint`/`typecheck`/`test`/`build` = **全 PASS**；**stub e2e `98 passed`**（含结构签名门 ⇒ **设计基线零漂移**）；**live e2e `53 passed`**。**`R-2` 复查** = `3 passed` + `egress guard judged 0 / blocked 0`。**告警面留档**（升级前）：`scratch/goal016-c3-alerts-before.txt` = open 23（4 high / 13 medium / 6 low）。**m0（冻结树，代管 `R-3` 文件）= `PASS: profile=m0; 23 deterministic checks`**（退出码 0，**首次即过**；`PASS [` = 24 行 = 23 项 + 计数外的 `release-assets-immutable`）+ 逐字节复核一致（`size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）。日志：`scratch/goal016-c3-m0-quarantined.log` / `-quarantine-run.txt` | **绿（CodeQL 3/3 已终态；M0 六 job 中 4 个已 success、2 个写入时仍在飞）**：CodeQL [36101609690](https://github.com/Eswink/research-system-new/actions/runs/36101609690) **3/3 success**（`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)`，`run_attempt=1`）；M0 [36101609755](https://github.com/Eswink/research-system-new/actions/runs/36101609755)（`run_attempt=1`，`created_at 2026-09-25T06:09:22Z`）：`eval-gate` / `container-quality` / `collector-quality` / `console-frontend` = **`success`**；**`quality-windows-latest` / `quality-ubuntu-latest` = `in_progress`**（多次轮询后 `updated_at` 仍停在 `06:09:35Z` ⇒ 表现为**托管 runner 排队**、非本 cycle 改动引发的红）。**该 run 的终态尚未取得** ⇒ 本行**不宣称**「六 job 全绿」；终态由 **cycle 6 收口时回填**（`run_attempt` 一并记）。**说明**：本 cycle 的**本地** m0 已在冻结树上取到 `PASS: profile=m0; 23 deterministic checks`（见上一列），故 CI 侧的排队不阻塞本 cycle 的判据 | **无需返工**：本 cycle 两道格式 / 门禁（`pnpm run check` 全链、web 四项、两个 e2e）**一次通过**；`pnpm install --lockfile-only` 期间有一次 `registry.npmjs.org` 的 `ECONNRESET`（重试成功，属本机网络面，同 `W-7` 一类）。**Dependabot 自身的两个 run 一并登记（非本仓门禁）**：`npm_and_yarn in / for vite, yaml ×2` [36101702449](https://github.com/Eswink/research-system-new/actions/runs/36101702449) = `success`、`npm_and_yarn in /. for undici…yaml` [36101631156](https://github.com/Eswink/research-system-new/actions/runs/36101631156) = `failure`——后者是 **Dependabot 更新分支 / PR 的例行动作**（非质量门、非本 cycle 改动产物），**不计入本 GOAL 的门禁判据**，如实登记为仓库外的 bot 状态 | **EC-03 = PASS**（`RECHECK-20260925-173` = `PASS_WITH_WARNINGS`；W-1 = 4 条 high 只是告警面的 1/6，**不得**读成「依赖告警已清零」；W-2 = `W-7` 继续有效；W-3 = `R-3` 仍在）。**越界项登记**：`undici`（主版本跳跃）、`yaml`（非 high）、剩余 19 条。其余三个 EC 仍 PENDING | cycle 4 = **EC-04 D-07 + D-08 + D-09 三处文档固化**（ADR-0031「否证条件」节 + D-08 依据 + ADR-0032 非 ASCII 路径豁免） |
| 4 | PLAN-20260925-174（EC-04） | `d67f324`（推送区间 `8814b49..d67f324`） | **判据** `tests/tooling/test_landed_decisions_are_citable.py` = **`6 passed`**（非 ASCII 现实↔清单**双向**比对 / 枚举陷阱**双数**断言（朴素 0 且 `\3` 形态存在 + 关转义 30）/ `ADR-0032` 结构与 `INDEX` 登记 / **可按压**（删一条 ⇒ 报出、塞一条 ⇒ 报出）/ `ADR-0031` 第 3 行仍 `Proposed` 且含否证条件节 / `MODEL_COMPATIBILITY` 四个关键词）；**枚举事实**：`git ls-files` 朴素非 ASCII = **0**、`git -c core.quotepath=false ls-files` = 3389 中 **30**；**`ADR-0031` 未越权**：`grep -c "Status: Accepted"` = **0**、既有「待拍板 / 可分别决定」判据 **`18 passed`**；**doc 一致性门**：首跑 `DOCS-CHECK FAILED: 2 finding(s)`（两条 `[backtick-ref]` 假路径）⇒ 改为指向真实对象 ⇒ **`DOCS-CHECK PASS: 6 deterministic checks`**（**未**动门禁）；`ruff check` = `All checks passed!` / `ruff format --check` = 已格式化 / `mypy` = `Success: no issues found in 1016 source files`；`tests/tooling` + 同源判据 = **`1162 passed`**；`egress guard` = `judged 0 / blocked 0`（**本 EC 零出网**）。**m0**（冻结树，代管 `R-3` 文件）= **`PASS: profile=m0; 23 deterministic checks`**（退出码 0、**首次即过**、`PASS [` = 24、`FAIL` = 0；逐字节复核一致 `size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）。日志：`scratch/goal016-c4-m0-quarantined.log` / `-quarantine-run.txt` | **绿（六 job + CodeQL 3/3，`ALL_TERMINAL`）**：M0 [36103914936](https://github.com/Eswink/research-system-new/actions/runs/36103914936) **六 job 全 success** + CodeQL [36103914401](https://github.com/Eswink/research-system-new/actions/runs/36103914401) **3/3 success** | **两处红都是文档措辞、判据未放宽**：① §13 引文在 `ADR-0032` 里被**断行** ⇒ 连续子串匹配不到 ⇒ 把引文收进**同一行**；② 文档写「必须先出**一份** ADR」而判据期望「必须先出 ADR」⇒ 改文档为 `**必须先出 ADR**（且该 ADR 至少写清三件事）`。判据侧**未**加 `in` / 未去空白 / 未降为前缀匹配。另有两处 `[backtick-ref]` 假路径（省略号缩写 `010…012`、臆想文件名 `test_legacy_non_ascii_paths_are_exempt.py`）⇒ 改为真实对象。**另一次红**：治理 `validate.py` 首跑报 `MEM-137` 缺 `## 为什么这样做 / ## 怎么做与复现 / ## 适用边界 / ## 来源` 四节 ⇒ 按既有章节集重写该 MEM（**未**改校验器、**未**加豁免）⇒ 复跑通过 | **EC-04 = PASS**（`RECHECK-20260925-175` = `PASS_WITH_WARNINGS`；**W-1 = D-07 的 `Proposed` 仍是未拍板项**（补否证条件 ≠ 拍板，**不得**读成「`tool_pack.*` 已获准」）；**W-2 = D-09 的豁免只管既有 30 条**，新建非 ASCII 仍判红且本 EC **未**验证新路径被拦；W-3 = `R-3` 仍在）。其余两个 EC 仍 PENDING | cycle 5 = **EC-05 D-12 文档级威胁模型草案**（BOLA / BFLA / 授权面；**diff 必须只含 docs**） |
| 5 | PLAN-20260925-176（EC-05） | 见回合汇报 | **纯增量**：`docs/security/THREAT_MODEL.md` **106 → 252 行**，`git diff --numstat` = **`146  0`**（**删除数 0** ⇒ 既有 106 行一字未删）；新增 `## 6. 授权面威胁建模（BOLA / BFLA）—— 文档级草案`，含 `### 6.1 术语` / `### 6.2 覆盖了什么`（7 条带出处的事实）/ **`### 6.3 未覆盖范围`**（8 条，`:166`）/ **`### 6.4 与 M18 边界的关系`**（`:194`）/ `### 6.5 若取 (a)：范围与代价` / `### 6.6 引用约束`；`BOLA` / `BFLA` 命中 **6** 处。**核心事实（均带出处）**：控制面 **124 条路由逐条零授权依赖**（`Depends(` / `Security(` / `current_user` / `HTTPBearer` / `APIKeyHeader` 全仓**零命中**）、**无调用方认证**（唯一请求级强制项 `Idempotency-Key` = 幂等非身份）、策略**只到能力级不到对象级**（`packages/domain/policy.py:29` + `packages/application/policy/native.py:47`；`examples/config/policy.yaml:2` = `default_effect: DENY`）、域实体**无归属**（`packages/domain/run.py:37` / `projects.py:5` / `artifacts.py:90` 仅溯源）、仓内**唯一**有认证的面 = worker 网关（`services/api/worker_gateway/auth.py:21` / `:58`）。**M18 边界**：`docs/roadmap/MILESTONES.md:971` 定义、`:973` = **DEFERRED「不标记部分完成」**、`:980` 触发条件；`docs/adr/ADR-0028-personal-scale-rebaseline.md:44` ⇒ 空白是**有意未做**而非疏漏；未来落点唯一 = `docs/security/IDENTITY_AND_ACCESS.md`。**门**：`DOCS-CHECK PASS: 6 deterministic checks`（首跑即过）；治理 `validate.py` = 通过；**m0**（冻结树，代管 `R-3` 文件）= **`PASS: profile=m0; 23 deterministic checks`**（退出码 0、**首次即过**、`PASS [` = 24、`FAIL` = 0；逐字节复核一致）。日志：`scratch/goal016-c5-m0-quarantined.log` / `-quarantine-run.txt` | 见回合汇报（本 cycle 的推送 run 在其台账行） | **本 cycle 无返工**（门一次通过）；如实登记两条**边界以外的既有事实**：① `FRAMEWORK_MANIFEST.json` 里该文件的**发布快照未刷新**（刷新属发布动作，且会带进非 docs 文件 ⇒ 违反本 EC 的 diff 只含 docs 约束）；实测该快照**本就已过期**（220 条中 **131** 条 hash 与现树不符）⇒ 非本 cycle 引入。② 本节**无自动发现能力**（树变了它不会红）——(b) 的固有代价，已写进 6.3 第 6 条与 6.5 | **EC-05 = PASS**（`RECHECK-20260925-177` = `PASS_WITH_WARNINGS`；**W-1 = 本节不是安全性只是可见性**（未提高任何访问控制强度，**不得**读成「授权面已处理」）；**W-2 = 会过期且不会自己红**；**W-3 = (a) 的最小形态也可能立刻全红**（124 条路由全不合规 ⇒ 只能退化成「现状白名单快照」，而白名单本身就是待还的债）；W-4 = 发布快照未刷新；W-5 = `R-3` / `R-M1` / `R-D1` 原样保留）。**剩一个 EC** | cycle 6 = **EC-06 收口复检 + 13 项 `D-NN` 终态表 + CI 台账** |
| 6 | PLAN-20260925-178（EC-06） | 见回合汇报 | **独立复检脚本** `scratch/goal016-ec06-closeout-recheck.py`（**不复用本 GOAL 的叙述**）：每个 EC = 「脚本自己重读树的**结构断言**」+「该 EC 判据文件在**被测树**里子进程实跑」两路同时成立。**当前树** ⇒ `CONCLUSION failures=0`，`EC-01 4 passed` / `EC-02 4 passed` / `EC-03 7 passed` / `EC-04 6 passed` / `EC-05 PASS`（结构断言）/ `EC-06 PASS`（结构断言）/ `REALITY non_ascii=30`；**脚本非恒真**（终态表未落盘时 `EC-06 FAIL` 并逐条报出 **13** 条缺失）。**m0 双终态行（身份不同、不可互换）**：**as-is** = `FAILED: 1 check(s): framework/validate_bundle=1` ⇒ **22/23**（唯一红 = **`R-3`**，红项判词逐字 `Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md`）且 `PASS [` = **23**；**代管后** = `PASS: profile=m0; 23 deterministic checks`（退出码 0、首次即过、`PASS [` = **24**、`FAIL` = 0、逐字节复核一致 `size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）。日志 `scratch/goal016-c6-m0-as-is.log` / `-m0-quarantined.log` / `-m0-quarantine-run.txt` / `-c6-recheck-worktree.txt` / `-c6-recheck-clean-checkout.txt`（干净 checkout 的同一结论）/ `-c6b-m0-quarantined.log` 与 `-c6b-m0-quarantine-run.txt`（**收口后终态树复跑**：同一终态行 + 逐字节一致 ⇒ 该行对应**最终记录树**） | **绿（六 job 全 success + CodeQL 3/3）**：见本文件「CI 台账」的 `c50ee97` 行与台账尾巴行（收口后回填终态） | **两处自我纠错（改的是脚本，不是判据）**：① 脚本首版把「朴素枚举必须数到 0」**写反**了（`if not non_ascii(...)`）⇒ 在正确环境下反而判红 ⇒ 修**判断方向**，**未**改判据 / 文档 / `core.quotepath`；② `Path.walk(followlinks=False)` 在本仓解释器上抛 `TypeError` ⇒ 改用 `os.walk(..., followlinks=False)`（悬空 pnpm 链接会让 `Path.rglob` 炸）。**一次治理红如实登记**：`MEM-20260925-139` 必须同时引用计划与复检 ⇒ 先立 `RECHECK-179` 的 `VERIFYING` 版**再**写该 MEM（**未**改校验器） | **EC-06 = PASS**（`RECHECK-20260925-179` = `PASS_WITH_WARNINGS`；**7 条 AC 全成立**：AC-1 两树同结论（去掉耗时后 `diff` 为空）/ AC-2 非恒真（13 条缺失）/ AC-3 双终态行（as-is **22/23** = `R-3`；代管 **23/23**）/ AC-4 13 项终态表 / AC-5 治理 + 文档门 / AC-6 承继残余逐条在位 / AC-7 零越界。**W-1 = 收口不是清零**；W-2 = 两行不可互换；W-3 = 干净 checkout 复检的前提是无 editable 安装；W-4 = 复检脚本会漂移、改它须按改判据审；W-5 = Temp 遗留检出 + 发布快照过期） | **六个 EC 全 PASS ⇒ GOAL-016 = ACHIEVED** |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-016 落地） | `4afb314` | M0 [36092961923](https://github.com/Eswink/research-system-new/actions/runs/36092961923) / CodeQL [36092961168](https://github.com/Eswink/research-system-new/actions/runs/36092961168) | **六 job 全 success** / **CodeQL 3/3 success**（`run_attempt=1`） |
| cycle 1 实施（`1e2af55`） | `1e2af55` | M0 [36095270268](https://github.com/Eswink/research-system-new/actions/runs/36095270268) / CodeQL [36095270579](https://github.com/Eswink/research-system-new/actions/runs/36095270579) | **六 job 全 success**（`eval-gate` / `quality-windows-latest` / `quality-ubuntu-latest` / `collector-quality` / `console-frontend` / `container-quality`）/ **CodeQL 3/3 success**（`run_attempt=1`） |
| cycle 2 实施（`c2bc8a4`） | `c2bc8a4` | M0 [36099521368](https://github.com/Eswink/research-system-new/actions/runs/36099521368) / CodeQL [36099519976](https://github.com/Eswink/research-system-new/actions/runs/36099519976) | **六 job 全 success** / **CodeQL 3/3 success**（`run_attempt=1`） |
| cycle 3 实施（`8814b49`） | `8814b49` | M0 [36101609755](https://github.com/Eswink/research-system-new/actions/runs/36101609755) / CodeQL [36101609690](https://github.com/Eswink/research-system-new/actions/runs/36101609690) | **绿（六 job 全 success + CodeQL 3/3）** —— 轮询到终态：M0 `conclusion=success`，逐 job `console-frontend` / `quality-windows-latest` / `quality-ubuntu-latest` / `eval-gate` / `container-quality` / `collector-quality` **全 `success`**（`run_attempt=1`）；CodeQL `Push on main` `conclusion=success`、3/3 `success`（`run_attempt=1`）。**过程如实登记**：cycle 4 首次写入本行时，`quality-windows-latest` / `quality-ubuntu-latest` 仍 `in_progress`（`created_at 06:09:22Z`，`updated_at` 停在 `06:09:35Z` ⇒ 表现为托管 runner 排队），当时**未**写「全绿」；现由**同一 run 的终态**回填（轮询日志 `scratch/goal016-c3-ci-poll.log` 第 37–56 行）。**Dependabot bot 自身的两个 run**（非本仓门禁）：`vite, yaml ×2` [36101702449](https://github.com/Eswink/research-system-new/actions/runs/36101702449) = `success`、`undici…yaml` [36101631156](https://github.com/Eswink/research-system-new/actions/runs/36101631156) = `failure`（更新分支 / PR 例行动作，**不计入**本 GOAL 判据） |
| cycle 4 实施（`d67f324`） | `d67f324` | M0 [36103914936](https://github.com/Eswink/research-system-new/actions/runs/36103914936) / CodeQL [36103914401](https://github.com/Eswink/research-system-new/actions/runs/36103914401) | **绿（六 job 全 success + CodeQL 3/3）** —— 轮询到 `ALL_TERMINAL`：M0 `conclusion=success`，逐 job `quality-windows-latest` / `eval-gate` / `quality-ubuntu-latest` / `console-frontend` / `container-quality` / `collector-quality` **全 `success`**；CodeQL `Push on main` `conclusion=success`，3/3 `success`。轮询日志 `scratch/goal016-c4-ci-poll.log`（第 36 轮 `completed=2/2`） |
| cycle 5 实施（`2293af9`） | `2293af9` | M0 [36106406335](https://github.com/Eswink/research-system-new/actions/runs/36106406335) / CodeQL [36106405593](https://github.com/Eswink/research-system-new/actions/runs/36106405593) | **绿（六 job 全 success + CodeQL 3/3）**（`run_attempt=1`）：M0 `conclusion=success`，逐 job `console-frontend` / `eval-gate` / `container-quality` / `quality-ubuntu-latest` / `collector-quality` / `quality-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)` **3/3 `success`**。轮询日志 `scratch/goal016-c5-ci-poll.log`（`ALL_TERMINAL`；其中 CodeQL 的 run 详情由 REST 直查补全——轮询脚本那次 JSON 截断，**如实登记**） |
| cycle 6 实施（`c50ee97`，收口） | `c50ee97` | M0 [36109914494](https://github.com/Eswink/research-system-new/actions/runs/36109914494) / CodeQL [36109913562](https://github.com/Eswink/research-system-new/actions/runs/36109913562) | **绿（六 job 全 success + CodeQL 3/3）**（`run_attempt=1`）：M0 `conclusion=success`，逐 job `quality-windows-latest` / `console-frontend` / `collector-quality` / `eval-gate` / `quality-ubuntu-latest` / `container-quality` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**。轮询日志 `scratch/goal016-c6-ci-poll.log`（`ALL_TERMINAL`；轮询脚本对 M0 的 run 详情那次 JSON 截断 ⇒ 由 REST 直查补全，**如实登记**） |
| cycle 6 收口（本行所在提交 = 台账尾巴） | 见回合汇报 | 由**回合汇报**给出终态（本 GOAL 口径：最后一次推送的 run 终态在回合汇报给出） | —（**本 GOAL 全部推送的 run 均逐行登记；除最后一行的终态在回合汇报外，其余全部轮询到终态**） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | ACTIVE | 建档：用户会话指令（goal 模式）按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板七项（D-01b / D-02b / D-03b / D-07b / D-08b / D-09a / D-12b）并授权实施；六 EC 设计（D-01 判据化 / D-02 口径判据 / D-03 high 升级 / D-07+D-08+D-09 固化 / D-12 威胁模型 / 收口复检）。明确不授权 D-10 / D-13 与 D-04 / D-05 / D-06 / D-11 的实施。**建档时零代码改动**（只增本文件）。 |
| 2026-09-25 | ACTIVE | cycle 1：**EC-01 = PASS**（D-01(b) 判据化）——判据走**产品入口 + 出厂目录**，缝为空时 6 条工具需求**逐条**被逐字点名，恢复 provider ⇒ 点名消失且计数归零（成对反证），模板在生产源里**单一来源**，按压非空；**产品代码零改动**。一次判据自身缺陷如实登记（按能力名配对 ⇒ `workspace.read` 跨两 phase 判红 ⇒ 改按 `(phase_id, capability)`）。其余五 EC 仍 PENDING。 |
| 2026-09-25 | ACTIVE | cycle 2：**EC-02 = PASS**（D-02(b) 口径判据）——逐条形态（每条规则只命名一个具体能力、无段前缀规则）+ 否定判据（无通配 / 前缀形态，且检测器**可被按压**）+ 证据面（「该登记」**恰好 15 条**、全为读类、**一条都没被放行**）+ 读类放行逐条可枚举。**零策略面改动**（两个策略面文件的 `git status` 输出行数 = 0、`git diff --stat` 为空）。m0 三跑取到绿（两处红如实登记：自己的 `mypy` 缺陷已修；live 检索用例的上游非确定 = (ii) 类，判据未动，登记 **`W-7`**）。其余四 EC 仍 PENDING。 |
| 2026-09-25 | ACTIVE | cycle 3：**EC-03 = PASS**（D-03(b) 4 条 high 依赖升级）——`vite` `6.3.5 → 6.4.3`（6.x 内 minor，一次覆盖全部 4 条 high；lockfile diff 9 增 9 删只含 `vite` 与 peer 引用行）。全量 web 门全绿（根 `check` exit 0 / web 四项 PASS / **stub e2e 98 passed**（设计基线**零漂移**）/ **live e2e 53 passed**）；`R-2` 复查 `3 passed` + `blocked 0`。**越界项登记**（`undici` 主版本跳跃、`yaml` 非 high、剩余 19 条）。其余三 EC 仍 PENDING。 |
| 2026-09-25 | ACTIVE | cycle 4：**EC-04 = PASS**（D-07(b) + D-08(b) + D-09(a) 三处文档固化）——`ADR-0031` 补 **`## 否证条件`**（三个出口：依赖消失 ⇒ 转 `Status`；事实消失 ⇒ 撤回；维持条件不变 ⇒ 保持），**`Status` 逐字仍 `Proposed`**（判据硬断言全文无 `Status: Accepted`）；`MODEL_COMPATIBILITY.md` §9 记下 **`ModelCompatibilityProfile` 维持派生视图** 的决定 + 「若要 (a) **必须先出 ADR**」前置条件，`DOMAIN_MODEL.md` §5 加指针；**`ADR-0032`** 记录 **30 条非 ASCII 历史路径豁免**（`Status: Accepted`、**零 rename**、引用 §13、记下 `core.quotepath` 枚举陷阱）并登记 `docs/INDEX.md`。判据 `tests/tooling/test_landed_decisions_are_citable.py` = **`6 passed`**（含现实↔清单双向比对、枚举陷阱**双数**断言、按压态）；`DOCS-CHECK` 首跑 2 条 `[backtick-ref]` 假路径 ⇒ 改为指向真实对象 ⇒ **PASS**（**未**动门禁）；`ruff` / `format` / `mypy`（1016 files）/ `1162 passed` 全绿；**diff 零越界**（5 docs + 1 判据；不含 `AGENTS.md`、策略面、产品代码、门禁脚本、rename、任何 `Status` 改动）。其余两 EC 仍 PENDING。 |
| 2026-09-25 | ACTIVE | cycle 5：**EC-05 = PASS**（D-12(b) 授权面威胁模型草案）——`docs/security/THREAT_MODEL.md` **纯增量**补第 6 节（**146 增 / 0 删**，106 → 252 行）：6.1 术语 / 6.2 覆盖了什么（7 条带出处的事实）/ **`### 6.3 未覆盖范围`**（8 条）/ **`### 6.4 与 M18 边界的关系`** / 6.5 若取 (a) 的范围与代价 / 6.6 引用约束；`docs/INDEX.md` Security 行加注。核心事实：控制面 **124 条路由逐条零授权依赖**、**无调用方认证**、策略**只到能力级不到对象级**、域实体**无归属**；M18 = **DEFERRED**（`:973`「不标记部分完成」）⇒ 空白是**有意未做**。**diff 只含 2 个 docs 文件**（零代码 / 零门禁 / 零判据 / 零阈值 / 零 allow）；`DOCS-CHECK PASS`（首跑即过）。其余一 EC 仍 PENDING。 |

## 13 项 `D-NN` 终态表（EC-06⑤）

口径：**拍板结论** = 2026-09-25 用户会话指令的判词（与
`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的「建议」列同源）；**本轮是否实施** =
GOAL-016 的六个 EC 里**实际做了什么**（未授权项一律「未实施」并给阻断依据）；
**不做会怎样** = 该简报条目的原文口径（缩略引用，**不改判**）。
**「未实施」不等于「不需要」**：未授权项**原样保留**为下一轮输入。

| ID | 主题 | 拍板结论 | 本轮是否实施 | 依据 | 不做会怎样 |
| --- | --- | --- | --- | --- | --- |
| D-01 | 出厂组合根是否自己接执行体缝（`M-1`） | 取 (b)：缝仍由装配方补，但把「缺执行体必须**点名**」写成机械判据 | **已实施**（EC-01 / PLAN-168） | 判据 `tests/application/preflight/test_missing_executor_is_named.py`（`4 passed`）走**产品入口 + 出厂目录**，缝为空时 6 条工具需求逐条被逐字点名，恢复 provider ⇒ 点名消失且计数归零（成对反证）；模板在生产源里**单一来源**；**产品代码零改动** | 装配方各自决定怎么补 ⇒「同协议两套装配」的老问题可能以新形态回来 |
| D-02 | 读类能力是否**成类**预放行 | 取 (b)：维持**逐条**放行（不成类、不新增任何 allow） | **已实施**（EC-02 / PLAN-170） | 判据 `tests/application/preflight/test_read_grant_is_per_item.py`（`4 passed`）：逐条形态 + 无通配/前缀的**否定判据**（检测器可被按压）+「该登记」**恰好 15 条**且一条都没被放行；**零策略面改动**取证：`policy.yaml` 与 `policy_check.py` 的 `git status` 行数 = 0、`git diff --stat` 为空 | 新增读能力会反复撞 `default_effect`，每撞一次就是一次 GOAL 级授权 |
| D-03 | 依赖 pin 升级（`R-D1`） | 取 (b)：**分批升**、**high 先升**、minor/patch 合批、每批单独 cycle 验证 | **部分实施**（EC-03 / PLAN-172）：4 条 high 全落在 `vite`，`6.3.5 → 6.4.3`（6.x 内 minor）**一次覆盖全部 4 条**，全量 web 门 + m0 全绿 | `pnpm-lock.yaml` 解析版本对照（diff 9 增 9 删只含 `vite` 与 peer 引用行）；根 `check` exit 0 / web 四项 PASS / stub e2e `98 passed`（设计基线**零漂移**）/ live e2e `53 passed`；`R-2` 复查 `3 passed`；升级后 open 告警 **23 → 9**（**0 high**：`undici` 8 条 + `yaml` 1 条） | 供应链告警持续存在；每条都有 `first_patched_version`，但**不动 pin 是当前明文禁令**（GOAL-015 `escalation_triggers`），所以不拍板就永远不动 |
| D-04 | hook 侧 L3 检测层 | **未授权**（明文「不授权 D-04」） | **未实施**（**原样保留**） | 用户指令的不授权清单第 3 项；本 GOAL 未触碰 `.cursor/hooks/` 任何文件 | hook 侧仍然**失败开放**，任何「安全已检查」的宣称都不成立（`R-M1` 原样保留） |
| D-05 | 450 行贴线文件 | **未授权**（明文「不授权 D-05」） | **未实施**（**原样保留**） | 用户指令的不授权清单第 4 项；`R-B1` 的四个 450 行零余量文件**未**被本 GOAL 改动 | 贴线文件继续零余量，改动它们必须先搬代码（本 GOAL 的 SOP 已按此执行） |
| D-06 | 路径 (B) 的 5 条重设计项 | **未授权**（明文「不授权 D-06」） | **未实施**（**原样保留**） | 用户指令的不授权清单第 5 项 | 该路线保持关闭 —— 这是**已知且可接受的现状**，不是遗漏 |
| D-07 | `ADR-0031`（`tool_pack.*`）是否采纳 | 取 (b)：维持 `Proposed`，**补一节「否证条件」**，**不改 `Status`** | **已实施**（EC-04 / PLAN-174） | `ADR-0031` 增 `## 否证条件`（三个出口）；第 3 行逐字仍 `Status: Proposed`；`grep -c "Status: Accepted"` = **0**；既有「待拍板 / 可分别决定」判据 `18 passed`；判据 `tests/tooling/test_landed_decisions_are_citable.py` 硬断言这两点 | 策略面维持现状；没有当前阻塞（可达面 8/8 已被非 deny 规则覆盖）——但「何时该改判」无人可查 |
| D-08 | `ModelCompatibilityProfile` 是否一等域实体 | 取 (b)：维持**派生视图**（不动 Canonical State） | **已实施**（EC-04 / PLAN-174） | `MODEL_COMPATIBILITY.md` §9 记下决定（三条理由 + 代价登记）+ `### 若要改成一等域实体（选项 (a)）的前置条件` 要求 **`必须先出 ADR`**（迁移 / 回滚 / 一致性判据）；`DOMAIN_MODEL.md` §5 加指针指回；**Domain 边界零改动** | 维持派生视图 —— 现状可用，属**登记**而非缺口 |
| D-09 | 非 ASCII 路径豁免是否需 ADR | 取 (a)：**出一份 ADR** 记录豁免（30 条，**不重命名**） | **已实施**（EC-04 / PLAN-174） | 新建 `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`（`Status: Accepted`、30 条逐条清单、引用 `AGENTS.md` §13、记下 `core.quotepath` 枚举陷阱）并登记 `docs/INDEX.md`；判据做「现实 ↔ 清单」**双向**比对 + 枚举陷阱**双数**断言 | 豁免继续以「口径」形式存在，新读者需要跨记录拼出理由 |
| D-10 | 门禁 scoping：`validate_bundle` 扫描 gitignored 工作区（`R-3`） | **未授权**（明文「不授权 D-10」，`R-3` 按 as-is 停在本地 22/23） | **未实施**（**原样保留**） | 用户指令的不授权清单第 1 项；本 GOAL 只**引用**该红项，**未**改扫描范围、**未**改门禁 | as-is 本机 m0 停在 **22/23**（唯一未绿即此项），且红项来自**别人**的未跟踪文件；CI 不受影响（检出无 `scratch/`） |
| D-11 | live 判据的开门条件 = 环境恰好有凭据 | **未授权**（明文「不授权 D-11」） | **未实施**（**原样保留**） | 用户指令的不授权清单第 6 项；本 GOAL **未**改任何 live 开关语义（`W-7` 已登记该面的环境敏感性） | 默认门的结论继续取决于**环境里有没有凭据**——这正是「质量门可信度」缺口的一类；CI 上只要有人配了一个过期 secret，默认门就会红且**真的出网** |
| D-12 | 威胁建模 / 授权面覆盖（BOLA / BFLA） | 取 (b)：先出**文档级**威胁模型草案（不改代码 / 门禁 / 判据） | **已实施**（EC-05 / PLAN-176） | `docs/security/THREAT_MODEL.md` 纯增量补第 6 节（**146 增 / 0 删**）：6.2 覆盖了什么（7 条带出处的事实：124 条路由逐条零授权依赖 / 无调用方认证 / 策略只到能力级 / 域实体无归属）、**6.3 未覆盖范围**、**6.4 与 M18 边界的关系**（`MILESTONES.md:973` = DEFERRED「不标记部分完成」）、6.5 若取 (a) 的范围与代价；**diff 只含 2 个 docs 文件** | 授权面覆盖继续缺一项系统性论证；`R-M1`（hook 面安全结论）也无法据此收口 |
| D-13 | CI 上「资源阈值型判据」的负载敏感性 | **未授权**（明文「不授权 D-13」，只登记；**只有 ≥2 次同类 flake 才升级到 (b)**） | **未实施**（**原样保留**） | 用户指令的不授权清单第 2 项；本 GOAL **未**动 `tests/observability/test_telemetry_overhead.py` 的 RSS < 128 MiB 与线程上限，**未**改阈值、**未**改作业结构 | 同一类「在同一进程里量整进程 RSS」的判据会继续在**负载高**的运行器上偶发判红，每次都要人工复跑 + 归因（本 GOAL 这类工作已经发生一次），且**红绿不一致会削弱本地/CI 结论的可信度** |

**汇总**：**已实施 4 项**（D-01 / D-02 / D-07 / D-08）**+ 部分实施 2 项**
（D-03 = high 批已升、`undici` 主版本跳跃与 `yaml` 非 high 未做；D-09 与 D-08 同轮）
**+ 未实施 6 项**（D-04 / D-05 / D-06 / D-10 / D-11 / D-13，全部因**明文不授权**）。
**未授权项一律原样保留**，其红/缺口**未**被本 GOAL 收口，也**未**被本 GOAL 掩盖。

| 2026-09-25 | **ACHIEVED** | cycle 6：**EC-06 = PASS** ⇒ **六个 EC 全 PASS，GOAL-016 收口**。独立复检脚本在**当前树**给出 `CONCLUSION failures=0`（六 EC 全 PASS）且**已证明非恒真**（终态表未落盘时逐条报出 13 条缺失）；**13 项 `D-NN` 终态表**落盘（已实施 4 / 部分 2 / 未实施 6 + 1）；**m0 双终态行**取到并各自身份明确（**as-is 22/23** = `framework/validate_bundle`（`R-3`）；**代管后 23/23**）；`validate.py` 与 `DOCS-CHECK` 绿；承继残余 `R-3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-7` 逐条在位。**AC-1 两棵树同结论**（同一脚本 `--root` 指向工作树与 `c50ee97` 的干净 checkout；去掉 pytest 耗时后 `diff` **为空**）；**AC-2** 脚本**非恒真**（终态表未落盘时逐条报出 13 条缺失）；**AC-3** m0 **双终态行**（**as-is 22/23** = `framework/validate_bundle`（`R-3`）；**代管后 23/23**）；**AC-4** 13 项 `D-NN` 终态表；**AC-5** `validate.py` + `DOCS-CHECK` 绿；**AC-6** 承继残余 `R-3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-7` 逐条在位；**AC-7** 入库改动只含记录面。**过程如实保留**：cycle 6 前半曾**刻意不记 PASS**（「干净 checkout」那一半必须先有提交才能检出），该 `IN_PROGRESS` 状态与理由留在 `RECHECK-20260925-179` 的时序说明里。**警告**：收口**不是清零**——未授权六项与全部残余**原样保留**。 |

## 当前续点

- **GOAL-016 = ACHIEVED（2026-09-25 收口）**：cycle 0 建档；cycle 1 = **EC-01 PASS**；
  cycle 2 = **EC-02 PASS**；cycle 3 = **EC-03 PASS**；cycle 4 = **EC-04 PASS**；
  cycle 5 = **EC-05 PASS**；cycle 6 = **EC-06 PASS** ⇒ **六个 EC 全 PASS**。
  `child_plans` = PLAN-168 / PLAN-170 / PLAN-172 / PLAN-174 / PLAN-176 / PLAN-178；
  `latest_recheck` = `RECHECK-20260925-179`；
  `memory_entries` = MEM-134 / MEM-135 / MEM-136 / MEM-137 / MEM-138 / MEM-139。
- **续点判定**：**本轮终态**（不再是续点）。若日后要重启，输入见「残余」与
  13 项 `D-NN` 终态表的「未实施」六项。
- **进度**：**EC-01 … EC-06 全部 PASS** ⇒ **约 6 个 cycle 内收口**（budget `max_cycles: 20`，
  用掉 6；`no_progress_stop_cycles: 2` **未触发**）。
- **待回填**：**cycle 6 推送（`c50ee97`）与其后收口提交的 CI 终态** ⇒ 见「CI 台账」的这两行
  与**台账尾巴**（收口提交后回填）。此前 6 行台账（建档 / cycle 1–5）**均已轮询到终态且全绿**。
- **依赖面**：`vite` 已升到 `6.4.3`（4 条 high 全清）；**其余 pin 变更仍越界**
  （`undici` 主版本跳跃、`yaml` 非 high）⇒ **不得**在后续 cycle 顺带动 pin。
- **开局已核实的文件层事实（决定可行性）**：
  1. **D-01 点名逻辑已在树**：`packages/application/preflight/checks.py` 的 `check_tools`
     在 `not requirement.provider_ids` 时产出 `TOOL_UNAVAILABLE` +
     `"no provider is available for capability {…}"` ⇒ 判据**不改实现**（cycle 1 已证）。
  2. **D-02 证据面已在树**：`docs/architecture/POLICY_SURFACE_AUDIT.md` 的「该登记 = 15 条」+
     `tests/application/preflight/test_policy_surface_difference_set.py` 同源比对
     （cycle 2 已把它接进判据）。
  3. **D-03 可执行范围**：4 条 high 全是 `vite`（as-is `6.3.5`，修复版本 `6.4.3` = minor）⇒
     **可升级**；`undici`（`5.29.0 → 6.24.0+`）= **主版本跳跃 ⇒ 不做**；`yaml`（patch，非 high）
     排下一批。
  4. **D-07 / D-09 的文档面**：`ADR-0031` = `Status: Proposed`（第 3 行）；`ADR-0032` 为下一编号；
     `docs/INDEX.md` 有既有 ADR 清单格式。
  5. **D-12 的文档面**：`docs/security/THREAT_MODEL.md` = 106 行、BOLA/BFLA 命中 **0**。
  6. **不动项**：`R-3`（as-is 本地 m0 **22/23**，唯一未绿 = `framework/validate_bundle`）与
     `D-13`（CI 的 RSS 阈值偶发红）**原样保留**——本 GOAL 只引用 / 登记。
  7. 工作树有**并发写者**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
     `packages/domain/model_drift.py`、`services/api/dto/models.py`，建档实测**内容 diff 为空**、
     仅行尾差异）⇒ **本 GOAL 不碰、不提交**这三处；只按显式路径提交本 GOAL 自己的产物。
     **EC-03 尤其要注意**：`apps/web/src/features/models/ModelDetails.tsx` 在该清单里，
     升级 `vite` 时**不得**把它卷进来。
  8. 规模门禁贴线：**四个正好 450 行零余量**（见「单 cycle SOP」③）⇒ 改动它们必须先搬代码。
  9. `make validate-all` = `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py
     --profile m0 --keep-going`；m0 = python 6 + typescript 9 + framework 8 = **23** 项。
  10. **全局编号**：下一批可用编号 = `PLAN` / `RECHECK` **`172`** 起（已用 `168` = PLAN、
      `169` = RECHECK、`170` = PLAN、`171` = RECHECK）；`MEM` 下一个 = **`136`**。
  11. **跑法**：m0 与代管脚本**一律**走 `uv run --frozen --no-sync python -B …`；
      `R-3` 的取证用 `tools/quarantine_and_run_m0.py`（本轮实测代管后
      `PASS: profile=m0; 23 deterministic checks` + 逐字节复核一致）。
