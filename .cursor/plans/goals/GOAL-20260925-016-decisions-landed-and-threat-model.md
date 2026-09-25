---
id: GOAL-20260925-016
slug: decisions-landed-and-threat-model
title: 决策落地：维持类决定的判据化 + 威胁模型草案 + high 依赖升级
status: ACTIVE
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
    status: PENDING
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
    status: PENDING
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
    status: PENDING
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
    status: PENDING
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-169-missing-executor-must-be-named.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-134-naming-contract-needs-a-pair-and-a-single-source.md
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
| EC-02 | **D-02(b)** 读能力逐条授权、不成类放行 | 逐条存在性判据 + 「无类别级规则」否定判据 + 15 条差集表引用 | **PENDING** |
| EC-03 | **D-03(b)** 4 条 high 升级（patch/minor） | lockfile 版本对照 + 全量 web 门 + m0 + CI 六 job | **PENDING** |
| EC-04 | **D-07 + D-08 + D-09** 决定固化 | ADR-0031「否证条件」节 + D-08 依据 + ADR-0032 + INDEX 登记 | **PENDING** |
| EC-05 | **D-12** 威胁模型草案（**零代码 / 零门禁**） | BOLA / BFLA / 授权面章节（覆盖 / 未覆盖 / (a) 代价） | **PENDING** |
| EC-06 | 收口复检 + 残余登记 | 两树复检 + m0 可支持终态行 + 13 项 `D-NN` 终态表 + CI 台账 | **PENDING** |

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

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `4afb314`（**推送 tip**，推送区间 `a3b2cf3..4afb314`） | 治理 `validate.py` = `Cursor 治理验证通过` | M0 [36092961923](https://github.com/Eswink/research-system-new/actions/runs/36092961923) **六 job 全 success** + CodeQL [36092961168](https://github.com/Eswink/research-system-new/actions/runs/36092961168) **3/3 success**（`run_attempt=1`） | — | EC-01…EC-06 全 PENDING；七项判词已落 frontmatter；起点已定位（点名逻辑已在树 / 该登记 15 条 / 4 条 high 全是 `vite` 且修复版本在 6.x minor / `undici` 主版本跳跃 / ADR-0031 补节且 `Status` 不变 / ADR-0032 编号 / THREAT_MODEL 106 行零 BOLA-BFLA）。**建档时零代码改动**（只增本文件） | cycle 1 = **EC-01 D-01(b) 判据化** |
| 1 | PLAN-20260925-168（EC-01） | 见回合汇报 | 判据 `tests/application/preflight/test_missing_executor_is_named.py` **`4 passed`**（正向逐条点名 / 成对反证 / 单一来源 / 按压）；探针 `scratch/goal016_c1_probe.py`（只读、零出网）实证两条同码链与「恢复 provider ⇒ 计数 0」；`ruff check` = `All checks passed!`、`ruff format --check` = 已格式化；规模 + 命名门禁 = `1054 passed`；`egress guard` = `blocked 0`。**m0 两个终态行分开（冻结树）**：**代管后**（`R-3` 文件临时移出）= `PASS: profile=m0; 23 deterministic checks` + 逐字节复核一致（`size=69944` / `mtime_ns=1790187424185178900` / `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）；**as-is** = **22/23**，唯一红项 = `framework/validate_bundle`，单条直跑复现的判词只有一条（`Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md`）⇒ 归因 = **`R-3`**（与本题改动无关）。日志：`scratch/goal016-c1-m0-quarantined.log` / `-quarantine-run.txt` | 见回合汇报（本 cycle 的推送 run 在其台账行；flake 判定按同一代码复跑对照） | **一次判据自身缺陷如实登记**：首版按**能力名**配对 ⇒ 被 `workspace.read`（**两个 phase** 都需要）判红 ⇒ 改成按 `(phase_id, capability)` 配对（**未**改产品代码） | **EC-01 = PASS**（`RECHECK-20260925-169` = `PASS_WITH_WARNINGS`；W-1 = 另两条同码链不在判据面内、W-2 = `R-3` 仍是本机 as-is 的预置红）。其余五个 EC 仍 PENDING；`M-1` / `D-10` / `D-13` 原样保留 | cycle 2 = **EC-02 D-02(b) 口径判据**（读能力逐条授权、不成类放行；零策略面改动） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档（本行所在提交） | 见回合汇报 | 由**下一次回写**（本 GOAL 口径）；该推送的终态在回合汇报给出 | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | ACTIVE | 建档：用户会话指令（goal 模式）按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板七项（D-01b / D-02b / D-03b / D-07b / D-08b / D-09a / D-12b）并授权实施；六 EC 设计（D-01 判据化 / D-02 口径判据 / D-03 high 升级 / D-07+D-08+D-09 固化 / D-12 威胁模型 / 收口复检）。明确不授权 D-10 / D-13 与 D-04 / D-05 / D-06 / D-11 的实施。**建档时零代码改动**（只增本文件）。 |
| 2026-09-25 | ACTIVE | cycle 1：**EC-01 = PASS**（D-01(b) 判据化）——判据走**产品入口 + 出厂目录**，缝为空时 6 条工具需求**逐条**被逐字点名，恢复 provider ⇒ 点名消失且计数归零（成对反证），模板在生产源里**单一来源**，按压非空；**产品代码零改动**。一次判据自身缺陷如实登记（按能力名配对 ⇒ `workspace.read` 跨两 phase 判红 ⇒ 改按 `(phase_id, capability)`）。其余五 EC 仍 PENDING。 |

## 当前续点

- **GOAL-016 = ACTIVE（2026-09-25 建档）**：cycle 0 完成建档（本文件）。
  `child_plans: []`、`latest_recheck: null`、`memory_entries: []` 待后续 cycle 填充。
- **续点判定**：以「迭代日志最后一行」+ 工作树 / 远端实况为准；建档轮之后进入
  **cycle 1 = EC-01（D-01(b) 判据化）**。
- **开局已核实的文件层事实（决定可行性）**：
  1. **D-01 点名逻辑已在树**：`packages/application/preflight/checks.py` 的 `check_tools`
     在 `not requirement.provider_ids` 时产出 `TOOL_UNAVAILABLE` +
     `"no provider is available for capability {…}"` ⇒ 判据**不改实现**。
  2. **D-02 证据面已在树**：`docs/architecture/POLICY_SURFACE_AUDIT.md` 的「该登记 = 15 条」+
     `tests/application/preflight/test_policy_surface_difference_set.py` 同源比对。
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
  8. 规模门禁贴线：**四个正好 450 行零余量**（见「单 cycle SOP」③）⇒ 改动它们必须先搬代码。
  9. `make validate-all` = `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py
     --profile m0 --keep-going`；m0 = python 6 + typescript 9 + framework 8 = **23** 项。
  10. **全局编号**：建档当日 `PLAN` / `RECHECK` 最大 = `166` / `167` ⇒ 下一个子 PLAN 从
      **`PLAN-20260925-168`** 起；`MEM` 最大 = `133`。
