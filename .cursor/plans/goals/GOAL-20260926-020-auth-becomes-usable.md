---
id: GOAL-20260926-020
slug: auth-becomes-usable
title: 认证可启用（前端 token 输入与携带 / 记录面门禁覆盖 / 认证运维面）
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-26 用户会话指令（goal 模式）：**建档 GOAL-020（认证可启用：前端消费 + 记录面门禁 + 运维面）
    并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **授权主题**：把 GOAL-019 落地的**写面认证从「能开启但开启后不可用」推进到「可真正启用」**。
    授权实施**严格限于**下述三条，**越界即 BLOCKED**：
    (1) **前端 token 输入与携带**：给前端提供 token 输入面（登录 / 设置入口），使认证**开启**时
    前端写操作**可用**、**关闭**时行为**逐字不变**。**存储方式的决策必须记录理由**
    （`localStorage` / `sessionStorage` / 内存三选一，写明 XSS 面、刷新即失的代价、为什么选它）；
    **token 绝不进日志 / 遥测 / 持久化文件 / 记录**。
    (2) **记录面门禁覆盖（方法论修复）**：把 GOAL-019 发现的缺陷修成**机械保证**——现状是本地 SOP
    顺序为「跑门 → 写记录」⇒ **记录面内容从未被本地门禁覆盖**（`test_reproducibility_wording.py`
    扫描 `.cursor/plans`，而本地 m0 在记录写入前就跑完了；只有 CI 覆盖记录面）。目标：**任何一次
    门禁结论都必须明确覆盖记录面**，且这一点**不能靠人记得**。可选实现（**三选一，写明选了哪条**）：
    ①全量门包含记录面判据、②加一条「记录面判据已执行」的自证判据、③把顺序固化进 SOP 并加一条
    顺序守卫。**本 EC 是本节最要紧的一条**（它影响所有后续轮次结论的可信度）。
    **不得**靠改 `test_reproducibility_wording.py` 的判据或放宽它来达成；改的是**顺序 / 覆盖机制**。
    (3) **认证运维面**：`docs/security/IDENTITY_AND_ACCESS.md` / `docs/integration/LIVE_MODEL_RUNBOOK.md` /
    `docs/api/CONTROL_PLANE_API.md` 补「**如何开启 / 轮换 / 关闭认证 + 如何验证 401 是否正常 +
    部署面注意事项**」，收口 GOAL-019 登记的「deployment face unverified」残余。
    (4) **明确不做（本 GOAL 边界，命中即 BLOCKED）**：**读面认证**（GET/HEAD——仍不保护，
    GOAL-019 口径 (i) 不变；若要做，**另行授权**）；**多租户 / RBAC / organization scope /
    对象级授权（BOLA/BFLA 专项测试）**——M18 范围，**不做**；**调用方自报身份**（沿用 GOAL-019 口径：
    单 token ⇒ 单主体，**不做** caller-declared identity）；**新增依赖**（前端 token 处理用现有栈；
    后端若需改动仍用标准库）；**把 token 写进任何文件 / CI / 记录 / 日志**；**改 `Idempotency-Key`
    语义**、**改认证的 401 响应形态**（前端要**适配**它，**不是**反过来）。
    (5) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (6) **不做真实出网**：本 GOAL **不需要** `.env` 凭据。若确需校验 URL，仅允许 http/https 且
    **发请求前校验 host** 并拒绝 localhost / 环回 / 私有 / 保留地址（**复用** `endpoint_policy`，
    不另写判据）；SQL 一律**参数绑定**；凭据**只从环境变量**读取；Domain **不得**出现厂商名；
    观测隐私**不记录完整 Prompt、不记录 token**（AGENTS.md §10）。
    (7) **边界**：GOAL-001…019 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-018 的**全部 13 项 `D-NN` 终态表**
    与承继残余**原样承继**（本 GOAL **不重开任何一项**）；GOAL-019 的五条新残余
    （`W-10`…`W-14`）由本 GOAL 的 EC-01 / EC-02 / EC-03 **更新为终态**、其余**原样保留**。
    (8) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    把控制面**写面认证从「能开启但开启后不可用」推进到「可真正启用」**，三条互相独立的交付：
    (1) **前端 token 输入与携带**：`apps/web` 提供 token 输入面，并经**既有唯一请求层**把
    `Authorization: Bearer <token>` 加到写请求上 ⇒ 认证**开启**时浏览器侧写操作**可用**、
    **关闭**时前端行为**逐字不变**（对照基线）；**存储方式三选一并记录理由**（XSS 面 /
    刷新即失的代价 / 为什么选它）；**token 值绝不进日志 / 遥测 / 持久化文件 / 记录**。
    (2) **记录面门禁覆盖（方法论）**：让「**任何一次门禁结论都覆盖记录面**」成为**机械事实**，
    不靠人记得——**先红后绿**（按**修前顺序**复现「记录面未覆盖而门却是绿的」）+
    修好后**同一路径下记录面判据必然参与** + **按压证明**；**不得**改 `test_reproducibility_wording.py`
    的判据或放宽它；改的**只是顺序 / 覆盖机制**。
    (3) **认证运维面**：三处文档补「**开启 / 轮换 / 关闭**认证 + **如何验证 401 是否正常** +
    **部署面注意事项**」，并收口 GOAL-019 的「deployment face unverified」残余
    （**要么**给出可复核的验证步骤与结论，**要么**如实登记「为什么在本机不可验证」）。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**零**新依赖；**零**策略面 allow
    新增；**不得**给读面加认证；**不得**宣称项目安全（`R-M1` 仍在）；**不做** D-12 的 (a) 面。
exit_criteria:
  - id: EC-01
    criterion: >-
      **前端 token 输入与携带（三态 + 存储决策 + 凭据纪律）**：
      ①**前端有 token 输入面**，并经**既有唯一请求层**把 `Authorization: Bearer <token>`
      加到**写请求**上；**关闭**时前端行为与基线**逐字不变**。
      ②**三态实跑各有证据**：**(甲) 认证关闭** ⇒ 前端行为与**基线一致**（对照判据，
      **不是**靠「测试没红」推定）；**(乙) 认证开启 + 前端无 token** ⇒ 前端**如实呈现
      「需要认证」**（**不得**空白 / 崩溃 / 静默失败）；**(丙) 认证开启 + 前端有 token** ⇒
      **写操作成功**。
      ③**成对反证（先红后绿）**：**去掉请求头的 token 注入** ⇒ 开启态的写操作**失败**、
      对应判据**判红**；逐字节复原 ⇒ 绿。
      ④**存储方式的决策与理由落记录**：`localStorage` / `sessionStorage` / 内存**三选一**，
      **写明 XSS 面、刷新即失的代价、为什么选它**。
      ⑤**凭据纪律**：token **值**不得出现在任何 tracked 文件 / 记录 / 日志 / 遥测 / 测试输出 /
      前端可持久化存储**之外**的任何位置——**grep 反证**（含 AGENTS.md §10 观测隐私面）。
      ⑥**设计基线若漂移** ⇒ 按既有流程**强制重生成 + 目检**，**不调容差**。
    verify: >-
      ① **三态实跑留档**：关闭态对照基线、开启态无 token 的如实呈现（含界面文案与
      **非崩溃**证据）、开启态有 token 的写操作 2xx（含 canonical 侧可核对的落点）；
      ② **成对反证**：临时移除请求头 token 注入 ⇒ 开启态写操作**失败**且判据**红**；
      逐字节复原 ⇒ 绿（留 `git diff` / sha256 证据）；
      ③ **存储决策**在 RECHECK / MEM 记录中**逐条写明**（选的哪一种 + XSS 面 + 刷新代价 + 理由）；
      ④ **grep 反证**：token **值**在仓库（排除 `.git`）与日志 / 遥测 / 记录面**零命中**
      （只允许**变量名**出现）；⑤ **既有安全判据未被绕过也未被改**：
      `tests/api/test_security_scan.py` 的两条持久层断言与 `sk-` 字面量断言**仍绿**且**未改**
      （`git diff` 取证该文件零改动）；⑥ 受影响 web 门（lint / typecheck / unit / build /
      stub e2e / live e2e）逐条实跑；⑦ **设计基线**：若 `design-outlines.json` 漂移 ⇒
      按既有流程重生成 + 目检，**不调容差**。
    status: PASS
  - id: EC-02
    criterion: >-
      **记录面门禁覆盖（方法论修复；本节最要紧的一条）**：让「**门禁结论覆盖记录面**」
      成为**机械事实**而非人记得的 SOP。
      **①先红后绿**：按**修前的顺序**（**跑门 → 写记录**）复现「**记录面内容未被门覆盖 ⇒
      门却是绿的**」这一事实；修好后**同一路径下记录面判据必然参与**（对照证据）。
      **②按压证明**：临时在某记录写入禁止形态（按 `OVERCLAIM_PHRASES` 的**既有**判据口径）⇒
      走**合法顺序**的**完整门必须判红**；**逐字节复原** ⇒ 绿。
      **③不得**改 `test_reproducibility_wording.py` 的判据、词表、扫描面或放宽其任一条
      （`git diff` 取证该文件零改动；**只**允许新增**别的**判据 / 机制）。
      **④不新增 m0 条数**：终态行仍为 `PASS: profile=m0; 23 deterministic checks`
      （**已核实**：`23` 被三处硬编码——`tools/quarantine_and_run_m0.py:34`、
      `tools/classify_local_gate_reds.py:108`、`docs/architecture/LOCAL_GATE_PROTOCOL.md:31`
      ⇒ 新增 m0 check 会同时打断这三处与 EC-04 的 23/23）；因此机制**必须落在既有 check 内**
      （`python/tests` 收集面已覆盖 `tests/**`，新增判据文件天然属于该 check）。
      **⑤记录面扫描面逐一核实**（收口 GOAL-019 的 `W-14`）：把「哪些判据的**结论**依赖
      `.cursor/plans` 内容」列成**逐行清单**并与实测一致。
    verify: >-
      ① **修前对照**：留档证明「按修前顺序 ⇒ 记录面判据**未参与**该次门禁结论」
      （可复核的机制性证据，不是叙述）；② **修后对照**：同一路径下，记录面判据**必然参与**，
      且**改动记录面内容会改变门禁结论**；③ **按压**：临时写入禁止形态 ⇒ 完整门**判红**
      （记录**实际判红的集合**，不只看「红没红」）⇒ 逐字节复原 ⇒ 绿；
      ④ `test_reproducibility_wording.py` **零改动**（`git diff` 取证）；
      ⑤ **终态行仍 23**；⑥ **扫描面清单**与实测逐一相符（含**未覆盖面**明写）；
      ⑦ **`git diff` 反证**：本轮**未**放宽任何阈值 / 门禁 / 放行面。
    status: PASS
  - id: EC-03
    criterion: >-
      **认证运维面（开启 / 轮换 / 关闭 + 401 验证 + 部署面）**：三处文档
      （`docs/security/IDENTITY_AND_ACCESS.md` / `docs/integration/LIVE_MODEL_RUNBOOK.md` /
      `docs/api/CONTROL_PLANE_API.md`）补齐：**如何开启认证**、**如何轮换**、
      **如何关闭**、**如何验证 401 是否正常**（可复核的验证步骤）、**部署面注意事项**；
      并**收口** GOAL-019 登记的「deployment face unverified」残余——**要么**给出
      **可复核的验证步骤与结论**，**要么**如实登记「**为什么在本机不可验证**」。
      **判据不得放宽**：与既有 `tests/architecture/python/test_control_plane_auth_same_source.py`
      的口径**一致**（该判据**零改动**）；**不得**宣称项目安全；**不得**把前端输入面
      写成访问控制（`THREAT_MODEL.md` §6.3 第 3 条已明写前端不构成控制）。
    verify: >-
      ① 三处文档逐处实查：**开启 / 轮换 / 关闭 / 401 验证 / 部署面**五个面**各自**在位
      （**不是**互相顶替）；② **既有同源判据仍绿且零改动**
      （`test_control_plane_auth_same_source.py` 的四处同源句 / 各自未覆盖锚点 /
      零夸大 / AST 断言；`git diff` 取证该文件零改动）；③ **runbook 同源族仍绿**
      （`test_runbook_same_source.py` 的 `## 1.`…`## 5.` 固定节名**不得**改名 / 改号；
      新增内容只走 `###`；新出现的**反引号环境变量名**必须**真实存在于代码**）；
      ④ **零夸大反证**：新写入的文字**不得**命中该判据的 `_FORBIDDEN_PHRASES`（**只增不减**
      的既有词表）到肯定语境；⑤ `docs/INDEX.md` 既有条目判据仍满足；
      ⑥ **未覆盖范围**逐条保留并**据实更新**（读面 / 多租户 / BOLA-BFLA / `R-M1` /
      部署面**终态**）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **收口复检 + 残余登记**：① **独立复检脚本**（不复用本 GOAL 的叙述）在**当前树**与
      **干净 checkout** 两路给出**同一结论**，且**非恒真**（按压必须判红）；
      ② **as-is 本机 m0 到 23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`；
      若不能 ⇒ **如实说明哪种跑法与哪条拦着**，不得含糊）——且该次运行**必须覆盖记录面**
      （按 EC-02 修好的顺序跑，**跑在记录写完之后**）；
      ③ 治理 `.cursor/skills/governance-check/scripts/validate.py` **绿**；
      ④ **CI 台账到终态**（M0 **八 job** + CodeQL，含 `run_attempt`）；
      ⑤ **承继残余逐条在位**：`R-M1`（**不得宣称项目安全**）/ `R-D1`
      （`undici` 归属上游、`yaml` 已升）/ `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6`；⑥ **GOAL-019 的五条新残余更新为终态**：
      `W-10`（单 token ⇒ 单主体）/ `W-11`（BOLA·BFLA 未做）/ `W-12`（部署面未验证）/
      `W-13`（前端无 token 输入面）/ `W-14`（记录面扫描面未逐一核实）——
      逐条写明**本 GOAL 使其变成什么状态**（已收口 / 原样保留 + 归属方）。
    verify: >-
      ① 复检脚本两路输出留档（`scratch/`）且**判词列逐行相同**；整份输出差异只允许出现在
      「本 GOAL 自身的 EC 状态文字」上（干净 checkout 停在更早的提交）；
      ② `make validate-all`（独占、仓库 `.venv`、`--keep-going`）终态行
      `PASS: profile=m0; 23 deterministic checks`，日志留档，且**运行发生在记录写入之后**；
      ③ `validate.py` 输出 `Cursor 治理验证通过`（含 `DOCS-CHECK`）；
      ④ 台账逐 run 逐 job 记录（含 `run_attempt`；flake 判定**必须**靠**同一代码的复跑对照**）；
      ⑤ 残余清单在本文件**逐条**出现且措辞与判词一致；⑥ **未覆盖范围**逐条明写：
      **读面未认证** / **多租户未做** / **D-12(a) 未做** / **R-M1 未收口** /
      **部署面**（`W-12`）的**终态**。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽被扫内容的任何检查项（`validate_bundle` 的链接存在性 / 版本号 / schema / 引用一致性）
    - 放宽 `tests/egress_guard.py` 的目的地判定 / 放行面 / 豁免 fake-IP（`198.18.0.0/15`）
    - 放宽 m0 任一 check 的阈值（含 450 行 / 50 行规模门禁；含 RSS 与线程阈值）
    - 改 `tests/observability/test_telemetry_overhead.py` 的阈值 / 测量语义 / 断言行
    - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据使其通过
    - 让 CI 作业失败不再传播为整体判红（`continue-on-error` / `if: always()` 吞失败）
    - skip / 删除测试、加 xfail、或调整收集顺序以掩盖顺序依赖
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何策略面 allow 或类别级规则（D-02 明文不取 (a)）
    - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）
    - 改 `ModelCompatibilityProfile` 的 Domain 面 / Canonical State 边界
    - 动 `undici` 的 pin，或写 pnpm `overrides` / `resolutions` / `packageExtensions`
    - >-
      **给读面（GET/HEAD）加认证**，或改动读面放行语义（GOAL-019 判词 (i) 不变：
      保护范围只有写面）
    - >-
      引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容
      （含给 `Principal` 加租户 / 角色字段）
    - >-
      新增**任何**依赖（含前端 token 处理引入第三方库；后端仍用标准库
      `hmac.compare_digest`，**不得**用 `==` 直接比）
    - >-
      把 token **值**写进任何 tracked 文件 / CI / 记录 / 日志 / 遥测 / 测试输出
      （含 `.env.example`、workflow、夹具、文档示例、playwright 配置、前端源码）
    - >-
      **改认证的 401 响应形态**（`title` / `detail` / ProblemDetail 结构与点名文本）——
      前端**适配**它，**不是**反过来
    - >-
      改 `Idempotency-Key` 语义，或改 `IdempotencyMiddleware` 的
      方法分类 / replay / conflict / record 行为
    - >-
      改 `tests/architecture/python/test_reproducibility_wording.py` 的
      **判据 / 词表 / 扫描面**，或放宽其中任一条（EC-02 的机制**不得**经由放宽它达成）
    - >-
      改 `tests/architecture/python/test_control_plane_auth_same_source.py` 的
      **同源句 / 未覆盖锚点 / 必需要求措辞 / `_FORBIDDEN_PHRASES` 词表 / AST 断言**
    - >-
      改 `tests/api/test_security_scan.py` 的持久层断言或 `sk-` 字面量断言，
      或用「惰性访问器」等方式**绕过**它而把 token 落进 `localStorage` / `sessionStorage`
    - >-
      改门禁或阈值（`validate_bundle` 检查项、m0 任一 check、`.github/workflows/**`
      的 job 结构、`test_m2_audit.py` 镜像判据），或改 m0 的**条数**（终态行必须仍是 23）
    - >-
      宣称「项目安全」「授权面已覆盖」或任何形式的安全结论（`R-M1` 未收口）；
      把前端 token 输入面当作访问控制
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    **给读面加认证** —— **立即 BLOCKED**（GOAL-019 判词 (i)：保护范围**只有写面**）
  - >-
    **引入多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容 ——
    **立即 BLOCKED**
  - >-
    **新增依赖**（前端或后端；token 处理必须用现有栈 / 标准库）—— **立即 BLOCKED**
  - >-
    **把 token 写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 / 夹具 / 示例 / 前端源码 /
    playwright 配置）—— **立即 BLOCKED**；明文凭据泄露（即使可弃用）⇒ 立即停止并报告
  - >-
    **改认证的 401 响应形态**，或改 `Idempotency-Key` 语义 —— **立即 BLOCKED**
  - >-
    **放宽 `test_reproducibility_wording.py` 或 `test_control_plane_auth_same_source.py`**
    的判据 / 词表 / 扫描面 / 阈值，或用「绕过既有安全断言」的方式达成前端存储 ——
    **立即 BLOCKED**
  - >-
    **改门禁 / 阈值 / 作业结构 / m0 条数**（`validate_bundle` 检查项、m0 任一 check、
    `.github/workflows/**` 的 job 结构、`test_m2_audit.py` 镜像判据、`23` 这一终态条数）
    —— **立即 BLOCKED**
  - >-
    **放宽任一判据 / 放行面 / 阈值**（含 `tests/egress_guard.py` 目的地判定与放行面、
    450 行 / 50 行规模门禁、RSS 与线程阈值）—— **立即 BLOCKED**
  - >-
    **放宽 §9 默认 deny**，或新增任何策略面 allow / 类别级规则 —— **立即 BLOCKED**
  - >-
    **Canonical State 边界**（改「PostgreSQL Domain Entity 是业务真相」的口径 /
    把认证态或 token 写进 canonical 取代域实体）—— **立即 BLOCKED**
  - >-
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**（Mimosa 钩子
    `scanner_enobufs` 未得完整结论）
  - >-
    把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - >-
    改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20260926-196-record-face-is-covered-by-the-gate.md
  - .cursor/plans/tasks/PLAN-20260926-197-console-token-input-and-write-face-carry.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-198-console-token-three-states-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-146-record-face-defect-is-timing-not-scan-surface.md
  - .cursor/memory/entries/MEM-20260926-147-frontend-credential-storage-and-app-path-driving.md
---

## 目标与退出标准

**一句话**：把控制面**写面认证**从「**能开启但开启后不可用**」推进到「**可真正启用**」——
**前端能输入并携带 token**（关闭时逐字不变）、**门禁结论机械地覆盖记录面**（不靠人记得）、
**运维面文档齐备**（开启 / 轮换 / 关闭 / 401 验证 / 部署面）——并且**不给读面加认证**、
**不碰多租户与 RBAC**、**零新依赖**、**不得宣称项目安全**。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **前端 token 输入与携带**（三态实跑 + 存储决策 + 凭据纪律） | 前端输入面 + 请求层携带 + 三态证据 + 成对反证 | **PASS** |
| EC-02 | **记录面门禁覆盖**（先红后绿 + 按压 + 判据零改动 + m0 仍 23） | 顺序 / 覆盖机制 + 扫描面清单（收口 `W-14`） | **PASS** |
| EC-03 | **认证运维面**（开启 / 轮换 / 关闭 / 401 验证 / 部署面） | 三处文档补齐 + 同源判据零改动 + 部署面终态 | **PENDING** |
| EC-04 | **收口复检 + 残余登记** | 两树复检 + as-is m0 **23/23**（覆盖记录面）+ CI 台账 + 残余逐条 | **PENDING** |

**依赖关系**：EC-02 是**方法论**面，独立于 EC-01 / EC-03（它判的是「门禁结论是否覆盖记录面」，
不判产品行为）⇒ **应当最先做**（用户判词明写「本 EC 是本节最要紧的一条」，因为它决定
**后续所有轮次结论的可信度**）。EC-01 与 EC-03 互相独立（前端 / 文档），可分别验收。
EC-04 **最后**做，且其 as-is m0 **必须按 EC-02 修好的顺序跑**。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **前端**已有**唯一请求层**：`apps/web/src/api/http.ts`（108 行）的私有 `send()`（`:70-80`）
   与 `buildHeaders()`（`:30-43`）是**唯一**构造请求头的地方；**19 个领域 client** 与
   `client.ts`（277 行，自述「唯一网络入口」）全部经 `request()` / `requestWithEtag()`；
   全仓 `fetch(` 只有**两处**：`http.ts:71`（共享）与 `artifactClient.ts:26`（**裸 fetch**，
   仅取制品原文，**GET**）。⇒ **写请求 100% 经单一注入点**（实测 15 个 client 文件里
   **60 处** `method: "POST"|"PATCH"|"PUT"|"DELETE"` 字面量）。
   **另一处例外**：`features/runs/useRunEventStream.ts:81` 的 `EventSource`（**GET**，浏览器
   API **不能**设自定义头）⇒ **两处例外都是读面**，而读面**不认证** ⇒ 无需 token。
2. **存储方式事实上被既有安全判据收窄**（本条**改变了**「三选一」的可行性面，落进记录）：
   `tests/api/test_security_scan.py:79-91` 对 `apps/web/src/**/*.ts*` **无条件断言**
   字面量 `localStorage.setItem` 与 `sessionStorage.setItem` **不出现**，其文档串写明该断言
   的意图是「前端持久层无 secret 写入」；`:94-102` 另断言无 `sk-` 前缀字面量。
   **两处细节**：①该断言是**字面量**检查——既有 `preferences.ts:93` / `activeProject.ts:33`
   经**惰性访问器**（`storage()`）调用 `store.setItem(...)` 因而**不命中**字面量；
   ②`preferences.ts:2` 自述是「**唯一允许的** localStorage 面」。
   ⇒ **用访问器把 token 落进浏览器持久化会「绕过字面量断言而违反其意图」**，本 GOAL
   **禁止**该做法（已进 `fix_policy.forbidden` / `escalation_triggers`）；因此
   **token 存储的现实选择是「内存」**（`localStorage` / `sessionStorage` 两条路都要求
   **放宽或绕过**既有安全判据 ⇒ 命中 BLOCKED）。**代价必须如实记录**：刷新即失。
   本 GOAL **不改** `test_security_scan.py`（`git diff` 取证）。
3. **状态管理 = 无第三方库**：`apps/web/package.json` 依赖只有 `react` / `react-dom`；
   既有跨切面状态的范式是**模块级惰性访问器 + Context + 自定义 hook**
   （`layout/preferences.ts` / `api/activeProject.ts` / `navigation/presentationContext.ts` /
   `hooks/useResource.ts`）。⇒ token 面**沿用同一范式**，**零新依赖**（已进 forbidden）。
4. **设置面与「分区」机制**：`features/settings/SettingsPage.tsx` 有 `SECTIONS`
   常量（`preferences` / `workspace` / `account` / `security` / `billing`）+ 按 id 条件渲染；
   而 `navigation/pageSupport.ts:188-193` 把 `settings/settings` 标为 `partial` 并列出
   `disabledOperations: ["account", "security", "billing"]`（唯一来源，由 `isOperationDisabled`
   消费）⇒ 新增 token 分区**必须**同时处理该判定（新增 id 或改既有 id 的禁用面），
   且 `apps/web/tests/unit/page-support-coverage.test.ts` 会对「未登记 → 隐式 gap」
   **判红**（该判据**不得**放宽）。路由是**哈希式 + 注册表驱动**（无 react-router）。
5. **认证实现面（GOAL-019 交付，本 GOAL 只消费、不改语义）**：中间件
   `PrincipalAuthMiddleware`（`services/api/middleware.py:211`，模块 244 行）——
   方法分类**复用** `_MUTATING_METHODS`（`:36`，`{"POST","PATCH","PUT","DELETE"}`）；
   读面靠 `NotIn` 放行（`:225-226`，**无路径白名单**，`/health` 是 GET 故天然豁免）；
   头解析 `_bearer_token`（`:197-208`）；比较 `hmac.compare_digest`（`:194`）；
   环境变量名 `RESEARCHOS_CONTROL_PLANE_TOKEN`（`:127`）/ 可选
   `RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID`（`:128`，缺省 `control-plane`）；
   空值 ⇒ `enabled=False` ⇒ 关闭。**401 响应形态**（`_problem`，`:104-114`）=
   ProblemDetail `{type:"about:blank", title:"Authentication Required", status:401, detail:…, instance:""}`，
   两种 `detail`：「缺 `Authorization: Bearer <token>` 头」与「token 不匹配」。
   **启动警告**在 `app.py` 的 `_lifespan`（`:255-257`）打印，
   文案含 `CONTROL PLANE AUTH IS DISABLED` / `ANY caller` /
   `NOT a statement that the project is secure`（`:167-182`）。
   **注册顺序**：`create_app` 里 `add_middleware(IdempotencyMiddleware)`（`:302`）**先于**
   `_install_write_face_auth(app)`（`:303`）⇒ Starlette `reversed` ⇒ **认证在外层先跑**
   （`app.py` 334 行；`create_app` = **48 行**，50 行函数门禁余量 **2 行**）。
   ⇒ **EC-01 只消费该面**：前端**适配**它的 401 形态，**不得**要求后端改形态。
6. **既存同源判据的硬约束（EC-03 必须精确满足，**不得**放宽）**：
   `tests/architecture/python/test_control_plane_auth_same_source.py`（**437 行 / 11 例；
   450 行硬上限只剩 13 行 ⇒ 本 GOAL 往它加任何东西都会撞门禁，故必须零改动**）要求：
   ①**canonical 同源句**逐字**恰好一次**出现在**四份**文档（`IDENTITY_AND_ACCESS.md` /
   `THREAT_MODEL.md` / `CONTROL_PLANE_API.md` / `LIVE_MODEL_RUNBOOK.md`）——**同源句当前各 1 处，
   新增文字不得复制它**（复制即判红）；
   ②四份**各自**有**自己的**未覆盖锚点 + **自己的**必需措辞，观察窗 **1200 字**
   （`_WINDOW`；**`THREAT_MODEL.md` §6.7 全文约 1241 字 ⇒ 该节在 `零夸大` 条目之前
   **不得**加长**，否则必需措辞会被挤出窗口**）；
   ③**21 条**肯定式安全断言零命中（`_FORBIDDEN_PHRASES`，**只增不减**），豁免 = 同句**前文**
   有否定标记（`不得` / `不是` / `禁止` / `勿` / `杜绝` / `并不` / `而非`），
   且**该豁免自身受判**（宣示 ⇒ 红，引述禁令 ⇒ 绿）；
   ④AST 断言：方法分类**唯一**、认证面**不继承** `_ANALYSIS_ACTIONS`、常数时间比较、
   **`RESEARCHOS_CONTROL_PLANE_TOKEN` 字面量在非测试源码里只允许出现在
   `services/api/middleware.py`**（`_SOURCE_ROOTS` = services / packages / adapters / core / **apps**
   ⇒ **前端源码里不得出现该变量名的 python 侧读取**；前端只出现**字符串名**不构成该断言命中，
   但**仍不得**出现其**值**）、注册顺序。
7. **runbook 同源族的硬约束**：`test_runbook_same_source.py`（181 行 / 10 例）要求
   **`## 1.`…`## 5.` 五个节标题逐字在位**（**不得**改名 / 改号 ⇒ 新增内容只走 `###`）；
   **反引号里的环境变量名式 token**（`^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$`）**必须真实存在于代码**
   （`_CODE_ROOTS` = `adapters, apps/web/src, examples, packages, services, tests, tools`；
   后缀 `.py .ts .tsx .yaml .yml .json`）；反引号里的**仓库路径 / pytest 目标 / `Fake*` 符号**
   必须存在；`docs/INDEX.md` 必须有条目行。**代码围栏内的 shell 片段不做 token 扫描**。
8. **记录面扫描面（EC-02 的 `W-14` 收口清单，建档日实测逐一核实）**——**结论**依赖
   `.cursor/plans`（或 `.cursor/**`）**内容**的判据共 **11 条**，分两类：
   **（A）内容依赖 8 条**：①`tests/architecture/python/test_reproducibility_wording.py:76`
   （`_SCAN_ROOTS` 含 `.cursor/plans`；扫后缀 `.py/.ts/.tsx/.md/.json/.yaml/.yml`；
   跳过 `node_modules/__pycache__/.venv/dist/.git/scratch`）；②`tools/credential_audit.py:38`
   （`RECORDS_DIR = ".cursor/plans"`，由 `tests/tooling/test_credential_audit.py` 驱动，
   五类凭据形态）；③`tests/tooling/test_pending_decisions_briefing.py:29-31`
   （读 **GOAL-015 / GOAL-018 两个 GOAL 文件**的头与 13 项 `D-NN`）；
   ④`tests/architecture/python/test_live_drift_sample_same_source.py:27-28`
   （读**一份指定 RECHECK**）；⑤`validate_bundle.check_versions:320-334`
   （全树版本串扫描，**唯一**豁免是 `.cursor/plans/archive/`）；
   ⑥`validate_bundle.validate_local_markdown_links:1188-1225`（**tracked `.md` 的本地链接必须可达**）；
   ⑦治理 `check_plans_and_rechecks:645-731`（PLAN / RECHECK / GOAL / `ALL_PLAN.md` 的
   frontmatter 与章节）；⑧治理 `check_links_and_secrets:854-869`（`.cursor/**` 的
   `.md/.mdc/.yaml/.yml/.py` 的链接与凭据形态）。
   **（B）仅名称 / 存在性依赖 3 条**：⑨治理 `check_git_history_preservation:801-845`
   （历史 ID vs 当前文件名）；⑩治理 `check_required_structure:296-311`
   （`ALL_PLAN.md` / `archive/README.md` 非空）；⑪`tools/docs_consistency_check.py:151-158`
   （roadmap 记录引用的 PLAN / RECHECK **文件存在**）。
   ⇒ **本 GOAL 的 EC-02 判据与收口记录必须同时满足这 11 条**——尤其**⑧的凭据形态**
   （记录里**不得**出现 `assigned-secret` 形态：行首 `api_key|access_token|password|secret` +
   引号字面量 ≥8 字符）、**⑥的链接可达**、**⑤的版本串**
   （`v?0\.2\.[0-9]+` / `0\.3\.0` 命中即红 ⇒ **本文件与后续记录一律不写这两类版本串**）。
9. **m0 的 `23` 是硬编码判据面（EC-02 的形态约束）**：终态行
   `PASS: profile=m0; 23 deterministic checks` 由
   `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py:232` 打印
   （`len(selected)` = python 6 + typescript 9 + framework 8 = **23**）；
   `23` 还被**硬编码**在 `tools/quarantine_and_run_m0.py:34`（`_GREEN`）、
   `tools/classify_local_gate_reds.py:108`（正则）、`docs/architecture/LOCAL_GATE_PROTOCOL.md:31`
   ⇒ **新增一个 m0 check 会同时打断这三处与 EC-04 的 23/23 要求**。
   **可行路径**：`python/tests` 这一个 check 的收集面是
   `python -m pytest --ignore=tests/architecture/python/test_dependency_boundaries.py`
   （`run_all_checks.py:123-126`）⇒ **新增判据文件放进 `tests/**` 即天然属于既有 check**，
   **条数不变**。EC-02 的机制**必须**走这条路（或等价的不改条数路径）。
10. **本地门入口与顺序**：`Makefile` 的 `validate-all`（`:41-42`）= 唯一的 m0 全量入口
    （`$(UV_PYTHON) $(RUNNER) --profile m0 --keep-going`）；`docs/architecture/LOCAL_GATE_PROTOCOL.md`
    是 SOP 文件，**其中没有**任何「先写记录」的顺序条款（该教训目前只存在于
    `MEM-20260926-145` 与 GOAL-019 / PLAN-194 / RECHECK-195 的叙述里 ⇒ **这正是 EC-02 要修的**：
    把**叙述**变成**机制**）。`LOCAL_GATE_PROTOCOL.md:44` 只有一条散文式禁止
    （「在门跑着时改工作树的被测文件」）。
11. **缺陷的**真实形状**（本条**更正**了用户提示词里的表述，落进记录）**：
    记录面**并非从来没有被门扫过**——`python/tests` 与 framework 组**已经**会扫
    `.cursor/plans`（第 8 条 11 条中的 8 条）。真正的缺陷是**时间上的**：
    **本地 SOP 把全量门跑在记录写入之前 ⇒ 该次门禁结论对「记录面**当时不存在的内容**」
    不成立**（既不是没扫，也不是扫不到，而是**扫描时刻早于内容存在**）
    ⇒ 因此「①全量门包含记录面判据」这一选项**在字面上已经成立、却仍然不足以修复缺陷**；
    修复必须把**门禁结论**与**记录面的内容状态**在**时间上**绑定起来
    （= 选项 ②自证判据 / ③顺序守卫的实质）。**判据形态**据此设计，见 EC-02 的
    `verify`（要求留档「修前 ⇒ 记录面判据未参与该次结论」与「修后 ⇒ 改动记录面内容
    会改变门禁结论」**两条机制性对照**，而不是只跑一次绿）。
12. **号码续接（实测）**：`.cursor/plans/tasks/` 最大 = `PLAN-20260926-194`；
    `.cursor/plans/rechecks/` 最大 = `RECHECK-20260926-195`（PLAN / RECHECK **共用**全局 NNN）
    ⇒ 下一个 PLAN = **196**、下一个 RECHECK = **197**；
    `.cursor/memory/entries/` 最大 = `MEM-20260926-145` ⇒ 下一个 MEM = **146**。
13. **规模门禁余量（实测，`tests/tooling/test_python_source_limits.py`：450 行文件 / 50 行函数；
    覆盖面 = `apps` / `services` / `packages` / `adapters` / `tests`）**：
    `test_control_plane_auth_same_source.py` = **437/450（余量 13 行）**、
    `services/api/app.py` = 334 行且 `create_app` = **48 行（余量 2 行）**、
    `tests/api/console_api_app.py` = 427 行（余量 23 行）、
    `tests/e2e/live_run_support.py` 只剩 **1 行**（`W-6`）；
    前端侧 `eslint.config.mjs` 的规模规则 = softMax 300 / hardMax 450（`apps/web/src/api/types.ts`
    是**唯一**被显式豁免的文件）⇒ **本 GOAL 的改动一律先搬代码再改**。
14. **前端门（实测）**：`pnpm --dir apps/web` 的 `lint`（`eslint src --max-warnings 0`）/
    `typecheck` / `test`（`node:test` + `tsx`，**17 个** `tests/unit/*.test.ts`，**无** testing-library，
    **无** `.test.tsx`）/ `build`（`tsc --noEmit && vite build`）/ `test:e2e`（Playwright **stub** 套件，
    25 个非 `live-*` spec，`page.route("**/*")` 拦截，**未匹配的 `/api/` 请求会让用例失败**）/
    `test:e2e:live`（**20** 个 `live-*.spec.ts`，清单**单一来源** `tests/e2e/live-specs.ts`，
    起 uvicorn:8011 + vite:5174）。**live 配置给 vite 传 env、给 API 服务器不传**
    ⇒ 「开启认证」的实跑需要在**不改既有配置语义**的前提下另开一条受控路径
    （新增 spec 走 `live-specs.ts` 单一来源；**token 值只能来自运行环境**，**不得**落进配置）。
15. **设计基线**：`apps/web/tests/e2e/design-outlines.json` **已含 `settings` 键**
    ⇒ 动设置页**可能**漂移；`design-outline-guard.spec.ts` 是守卫 ⇒ 若漂移
    **按既有流程重生成 + 目检**（`UPDATE_OUTLINES=1` + 单路由 + Linux 侧像素复验），
    **不调容差**（承 `MEM` 的既有配方与 GOAL-019 EC-01 的口径）。
16. **承继起点（事实，不是待办）**：GOAL-018 的 **13 项 `D-NN` 已全部结清**
    （已实施 9 + 部分实施 1 + 已拍板为维持现状 3、**未授权待拍板 0**）；
    GOAL-019 **ACHIEVED**（五 EC 全 PASS，收口提交 `89c3170`；五条新残余 `W-10`…`W-14`）。
    本 GOAL **不重开**任何一项，只把 `W-13`（前端无 token 输入面）/ `W-14`（记录面扫描面
    未逐一核实）/ `W-12`（部署面未验证）**推进为终态**，其余原样保留。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 默认门一律离线**（不需要 `.env` 凭据；web 门的 `pnpm` 网络仅用于既有链路）。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-020-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-020**」（**不是**变更 GOAL-019 的 budget 并置回 ACTIVE）。
理由：**「认证可启用」是新范围**（前端消费面 + 门禁方法论面 + 运维文档面），而 GOAL-019
已 ACHIEVED 且其取证面是「写面认证三态 + 四处文档同源」——与「前端 + 记录面机制」**不重叠但互相顶替**
（在本 GOAL 下改前端才不会让 GOAL-019 的「`apps/web/**` 零改动」判词失效）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260926-020`
  并投影 `ALL_PLAN`，**同一提交**）。子 PLAN 编号续**全局 NNN**（建档当日实测：
  下一个 PLAN = **196**；RECHECK = **197**；MEM = **146**，见「目标与退出标准」第 12 条）。
  **建议顺序**：cycle 1 = **EC-02**（方法论面最先做，因为它决定后续结论的可信度）；
  cycle 2 = **EC-01**（前端三态）；cycle 3 = **EC-03**（运维文档）；cycle 4 = **EC-04**（收口）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：**顺序已按 `MEM-20260926-145` 修正，务必照此执行**——
  **(a) 先写记录**（PLAN / RECHECK / MEM / GOAL 回写）→ **(b) 跑记录面判据**
  （`tests/architecture/python` + `tests/tooling`，含第 8 条那 11 条）→
  **(c) 再跑完整 `make validate-all`**（m0 全量 23 项，**独占运行**，**用仓库 `.venv`**，
  `--keep-going` 照抄 Makefile）+ 受影响定向套件 + **web 门**
  （`pnpm --dir apps/web` 的 lint / typecheck / test / build / test:e2e / test:e2e:live）。
  **门禁结论必须覆盖记录面**；**本地不绿不得 push**（承 `MEM-20260924-125`）。
  **写记录时不要跑 m0**（承 `W-5`：m0 运行中改工作树会让 `framework/validate` 判红）。
  **规模门禁自查**（50 行函数 / 450 行文件——**四个零余量 / 近零余量文件**：
  `services/api/composition.py` / `packages/application/run_orchestration/service.py` /
  `adapters/postgres/workflow_engine.py` / `adapters/execution/docker_backend.py`；
  `test_control_plane_auth_same_source.py` 仅余 13 行；`create_app` 仅余 2 行；
  `tests/e2e/live_run_support.py` 仅余 1 行）与**快照类门禁**
  （**OpenAPI 快照**——本轮前端改动原则上不漂移，但一旦动路由 / DTO 就必须按既有流程重生成；
  **设计基线**——已含 `settings` 键）。
  **默认门一律离线**（`tests/egress_guard.py` 是结构判据——**不得**为本地变绿而放宽它）。
  **`CURSOR_FRAMEWORK_ROOT` 的作用域**：它重定向**整个 m0 runner**（不是单个 check）。
  **Linux 侧复验**：`...` 形式链接在 Win32 会**剥尾点** ⇒ 涉及路径 / 链接的判据必须在
  **Linux 侧**（CI 的 `quality-ubuntu-latest`）复验；本机绿不等于跨平台绿。
- **④ commit**：显式路径；**绝不 `git add -A`**（并发工作树）。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（只推 main）→
  轮询 CI 到终态（`scratch/poll_ci_all.sh <sha>`：M0 **八 job** + CodeQL），记录 run id /
  链接 / 逐 job 结论 / **`run_attempt`**（**flake 判定必须靠同一代码的复跑对照**）；
  **本机无法验证记 PENDING 并停止推进**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；超 `fix_policy` 或命中 `escalation_triggers`
  ⇒ `status: BLOCKED`。
- **⑦ 回写**：EC / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史；
  **收尾前必须回写**；`child_plans` 与 `memory_entries` 每轮与实际派生对齐。
  **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
  **CI 台账沿用既有闭合约定**：写下本条的那个提交自身的 run 只在**回合汇报**记账。

**撤回纪律**（承 GOAL-011…019；**本轮尤其要紧**）：改共享夹具 / 中间件 / 契约时先数清谁拿它的
**失败形态**当夹具。本 GOAL 的**两处高危面**：
① **前端请求层是全部 stub / live e2e 夹具的共用面**——`buildHeaders` / `send` 的任何改动
会让**全部** 60 处写请求与 25 + 20 条 e2e 的请求形态一起变；改动前先**静态清点**
「谁断言请求头 / 谁断言未匹配 `/api/` 请求会失败 / 谁断言 401 行为」；
② **既有安全判据把 token 存储收窄成内存**（第 2 条）⇒ **不得**为了「更好用」而绕开它。
CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| **前端请求层把 e2e 夹具打红**（EC-01 主场） | `console-frontend` job 报 stub / live e2e 红；或「未匹配 `/api/` 请求」类失败 | 判「是**载体改动**改变了请求形态」还是「夹具陈旧」：**前者 ⇒ 优先撤回载体改动**；**不得**改断言迁就 |
| **记录面判据打红**（EC-02 主场） | `python/tests` 报 wording / credential-audit / pending-decisions / drift-sample / 链接 / 版本串 | 判「是记录**内容**违规」还是「**机制**误报」：内容违规 ⇒ 改写记录（**引述形态要带否定标记或引号**，**反引号不算引用**）；机制误报 ⇒ 修机制，**不得**放宽判据 |
| **m0 条数被打断**（EC-02 陷阱） | 终态行不再是 `23 deterministic checks` | **立即回退**到不改条数的路径（把判据放进 `tests/**`），**不得**改那三处硬编码 |
| **安全判据打红**（前端主场） | `tests/api/test_security_scan.py` 的持久层 / `sk-` 断言红 | ⇒ 说明 token 落进了带字面量的持久化或引入了 key 形态字面量：**改产品，不改判据**；**不得**用惰性访问器绕过 |
| **OpenAPI / 设计基线漂移** | `test_openapi_snapshot.py` / `design-outline-guard.spec.ts` 判红 | **按既有流程重生成** + 说明漂移来源 + **目检**；**不得**手改快照 / 调容差 |
| **文档同源族判据**（EC-03 主场） | `test_control_plane_auth_same_source.py` / `test_runbook_same_source.py` / `test_live_*_same_source.py` 判红 | 判「是文档要写实况」还是「引用了不存在的符号 / 复制了同源句 / 把必需措辞挤出 1200 字窗」：**前者** ⇒ 改文档；**不得**放宽判据 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`W-7` live 上游瞬时） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 归因；**资源阈值型**判红 ⇒ **(ii) 类 + 复跑对照**，**判据与阈值一字不动** |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态 + **未覆盖范围逐条明写**（读面未认证 / 多租户与 RBAC 未做 /
  D-12(a) 未做 / `R-M1` 未收口 / 部署面终态）。
  **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **新增依赖**、**把 token 写进任何地方**、**改 401 形态或 `Idempotency-Key` 语义**、
  **放宽 `test_reproducibility_wording.py` / `test_control_plane_auth_same_source.py`**、
  **改门禁 / 阈值 / m0 条数**、**放宽 §9 默认 deny**、**宣称项目安全**、
  **Canonical State 边界**）、同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、
  或连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，
  **留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。
- **本 GOAL 的收口判词必须写明**：**as-is 本机 m0 的终态行**（应为
  `PASS: profile=m0; 23 deterministic checks`；若未达 ⇒ 如实登记**是哪一条**拦着、
  **哪种跑法**）、**前端三态的实跑证据**（关闭 / 无 token / 有 token）、
  **记录面门禁覆盖是否成立（含修前与修后的对照证据）**、**存储方式的选择与理由**、
  **未覆盖范围**（读面 / 多租户 / D-12(a) / 部署面），以及 **`401` 响应形态与
  `Idempotency-Key` 是否一字未动**。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`.cursor/plans/goals/GOAL-20260926-018-residual-closeout-and-decision-register.md`
的「不进入循环 / 需人工拍板」节 + `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**（`D-01` / `D-02` / `D-07` / `D-08` / `D-09` / `D-10` / `D-11` / `D-12` / `D-13`）、
**部分实施 1 项**（`D-03`：`vite` 已升 + `yaml` 已升；`undici` 已调研未升）、
**已拍板为维持现状 3 项**（`D-04` / `D-05` / `D-06`）、**未授权待拍板 0 项**。
⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019 的五条新残余 —— 本 GOAL 更新为终态**

| 残余 | 内容 | 本 GOAL 的目标终态 |
| --- | --- | --- |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（归属方 = 若要做逐调用方身份 ⇒ 另行授权，属 D-12 (a) 面） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留**（归属方 = 另行授权；M18 / D-12(a)） |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **→ 终态**：由 **EC-03** 收口（**要么**给出可复核的验证步骤与结论，**要么**如实登记「为什么在本机不可验证」） |
| `W-13` | **前端无 token 输入面**（认证开启时浏览器侧写操作不可用） | **→ 终态**：由 **EC-01** 收口（前端能输入并携带 token；关闭态逐字不变） |
| `W-14` | **记录面判据的扫描面未逐一核实** | **→ 终态**：由 **EC-02** 收口（11 条扫描面清单逐行核实，见「目标与退出标准」第 8 条） |

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

1. **读面认证（GET / HEAD）**——**不做**（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
2. **多租户隔离 / organization scope**——**不做**（M18）；
3. **RBAC / 角色 / 权限矩阵**——**不做**；
4. **M18 的任何内容**——**不做**（`MILESTONES.md` 的 M18 状态 `DEFERRED` 不变，
   **不得**标记部分完成）；
5. **调用方自报身份**（caller-declared identity）——**不做**（单 token ⇒ 单主体）；
6. **新增依赖**——**不做**（前端 token 处理用现有栈；后端仍用标准库
   `hmac.compare_digest`，**不得**用 `==` 直接比）；
7. **改 `Idempotency-Key` 语义**——**不做**；
8. **改认证的 401 响应形态**——**不做**（前端**适配**它，**不是**反过来）；
9. **把 token 值写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出 / 前端源码 /
   playwright 配置**——**不做**（**只登记变量名**，**绝不留值**；`.env.example` 也不加）；
10. **D-12 的 (a) 面（BOLA / BFLA 专项测试与门）**——**本轮仍不做**，**如实保留**；
11. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
12. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
13. **`undici` 的 pin（含 pnpm `overrides`）**——**不动**（归属上游，见 D-03 终态）；
14. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**。

**承继的诚实边界（如实保留，不是待办）**：

- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（且**不得**用「前端能输 token 了」替代它）。
- **`R-D1`｜Dependabot 告警**——`yaml` 已升、`vite` 已清；**`undici` 8 条原样保留**，
  **归属上游**。**本 GOAL 不动它**。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，**原样保留**。
- **`R-F1`｜收敛 / 一致性判定含主观面时必须先操作化**——**原样保留**。
- **`R-F2`｜真实数据 / 调用规模不足时的诚实边界**——**原样保留**。
- **`W-4`（本机 m0 仍同进程跑阈值判据）/ `W-5`（新作业多一次冷装）/
  `W-6`（`tests/e2e/live_run_support.py` 只剩 1 行余量）**——**原样保留**；
  `W-6` 是**规模门禁的零余量告警**：本 GOAL 若需改该文件**必须先搬代码**。
- **`D-04` 的重启前置**——**先修误报面**；**本 GOAL 不安装检测层、不改 hook 面、
  不改 `MIMOSA_GIT_GATE_MODE`**。

**本 GOAL 交付的是「认证可启用」，不是「授权面已覆盖」**：
前端能携带 token ≠ 有授权模型；`THREAT_MODEL.md` §6.3 第 3 条明写「**不覆盖前端**，
`apps/web` 的按钮可见性 / 路由可见性**不是**访问控制」。本 GOAL **不产生** BOLA / BFLA
的负面测试套件，也**不**把「前端 token 输入面」写成访问控制。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `6cc7561`（**建档提交**，推送区间 `89c3170..6cc7561`） | 治理 `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS`；**判据按压**：改本文件一处章节标题 ⇒ `validate.py` 判红（`GOAL 缺少章节 ## 状态历史: GOAL-20260926-020`）⇒ 证明新建的 GOAL **确实被载入判据**；逐字节复原（sha256 校验）⇒ 绿。**按压方法学附带发现**：`validate.py` 的章节判据是**子串包含** ⇒ 把标题**追加**后缀（`## 状态历史-按压`）**不会**判红（子串仍在）；必须**整个抹掉**字面才判红。**记录面自查**：本文件落在 `test_reproducibility_wording.py` 的扫描面内且**零命中**其词表；`credential_audit` 五类形态零命中（只登记**变量名**，不留值） | M0 [**36246070820**](https://github.com/Eswink/research-system-new/actions/runs/36246070820) **八 job 全 success**（`console-frontend` / `container-quality` / `eval-gate` / `collector-quality` / `quality-ubuntu-latest` / `observability-overhead-ubuntu-latest` / `quality-windows-latest` / `observability-overhead-windows-latest`）+ CodeQL [**36246070729**](https://github.com/Eswink/research-system-new/actions/runs/36246070729) **3/3 success**（`Analyze (actions)` / `Analyze (python)` / `Analyze (javascript-typescript)`；`run_attempt=1`，**一次成功、无 flake**；日志 `scratch/` 轮询 `ALL_TERMINAL`）。**外部旁证**：push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`），与 GOAL-018/019 收口一致 ⇒ 本轮**零依赖改动** | — | EC-01 / EC-03 / EC-04 全 PENDING；EC-02 = PASS。起点已定位（前端**单一注入点** = `http.ts` 的 `buildHeaders`/`send`，60 处写请求全覆盖；**两处 GET 例外**不需 token；**存储方式被 `test_security_scan.py:79-91` 收窄为内存**；**m0 的 23 被三处硬编码** ⇒ EC-02 机制须落在既有 check 内；**记录面扫描面 = 11 条**已逐一核实，可收口 `W-14`） | cycle 1 = **EC-02**（方法论面最先做：它决定后续所有结论的可信度） |
| 1 | PLAN-20260926-196（EC-02） | `（实施提交见回合汇报）` | **记录面覆盖 = 机械事实**。交付 = 新判据 `tests/architecture/python/test_record_face_is_covered_by_the_gate.py`（**215 行 / 8 例**）+ `LOCAL_GATE_PROTOCOL.md` 新增 `### 记录面覆盖（GOAL-020 EC-02）` 顺序节 + `RECHECK-197` + `MEM-146`。**先红（机制性）**：临时向记录面写一条含禁用形态的记录 ⇒ `test_reproducibility_wording.py` **单独判红**（`exit=1`，`test_no_affirmative_fully_reproducible_claim`）⇒ **记录面本来就在扫描面内** ⇒ 缺陷是**时刻**（门跑在记录写入之前），**不是**没扫；删除 ⇒ `5 passed`。**后绿（完整门）**：探针在树时跑 **canonical 全量门** ⇒ `FAILED: 3 check(s): python/format-check=1, python/tests=1, framework/validate=1`，**其中 `python/tests` 的红就是探针**（记录面违规 ⇒ 门判红 = EC-02 要的结论）；另**两条红是本轮真缺陷并已修**（①新判据 1 处该折叠的 assert ⇒ `ruff format --check` 判红；②`MEM-146` 引用的 `RECHECK-197` 未存在 + 未入 INDEX）⇒ **定向套件当时全绿，全量门抓到两处真红**。**按压矩阵 7/7 符合预期**（6 红 + 1 期望不红），每轮报**实际判红集合**，逐字节 sha256 还原、终态复跑 `exit=0`。**判据零改动**：`git diff --stat -- tests/architecture/python/test_reproducibility_wording.py` = 空。**m0 条数不变**：按压轮 `PASS [` = 21 + `FAILED` = 3 ⇒ **24 = 23 + 1**（不计数项）。**终态全量门（记录写完之后）** = `PASS: profile=m0; 23 deterministic checks`（`PASS [` = **24**、`python/tests` = **4559 passed / 20 skipped**、`FAILED`/`ERROR` **0**；日志 `scratch/goal020-c1-m0.log`）。治理 `validate.py` 绿 | `（见回合汇报）` | **两处真红（已修）**：① `python/format-check`（新判据 1 处该折叠的 assert）；② `framework/validate`（记录自洽：`MEM-146` 引用的 `RECHECK-197` 必须**同提交**在位 + `INDEX.md` 登记）。**按压方法学教训（已入 `RECHECK-197` / `MEM-146`）**：①条款类判据必须**按小节**判履行——首版按整篇文档判，而判据名在文档里出现两次 ⇒ 删一处仍满足 ⇒ 改为取小节文本后才判红；②按压探针**不得含自己的意图词**——首版探针写了「本行含禁止形态」，其中「禁止」是 `NEGATION_MARKERS` 之一 ⇒ 被**否定标记豁免**而**没红**（判据按设计工作，是探针写错）；③「按压打偏」必须记为**失败** | **EC-02 = PASS**（先红后绿 + 按压 7/7 + 判据零改动 + m0 仍 23）；`W-14` **已收口**（11 条扫描面清单逐行核实，含未覆盖面：`.cursor/memory/entries` 不在话术判据与凭据审计的记录面内）；`RECHECK-20260926-197` = `PASS_WITH_WARNINGS`。**未覆盖范围**：8 条内容依赖判据中**只有 4 条**各建了断言（其余在清单里登记但未各建断言）；「每次门都跑在记录之后」仍是**人的顺序** | cycle 2 = **EC-01**（前端 token 输入与携带 + 三态实跑 + 成对反证） |

| 2 | PLAN-20260926-197（EC-01） | `（实施提交见回合汇报）` | **三态实跑 5/5**（对**真实** FastAPI + **真实** vite；写操作经**应用自己的请求层**）：**甲（关闭）** `PUT …/settings` **200** 且 `authorization=null` + 状态位「未配置」；**乙（开启 + 无 token）** **401** + 设置页/token 输入面可见、说明可读、**零 `pageerror`**（非空白/非崩溃）；**丙（开启 + 经界面填 token）** 前置 401 → 保存 → 状态位「已配置」→ `PUT` **200** 且 `authorization` **非空**、输入框清空、页面 HTML 不含明文。**成对反证**：把注入条件改成 `if (false && …)`（锚点唯一命中）⇒ 丙态 **401**、退出码 1 ⇒ **红由「去掉注入」引起**；sha256 `e4b004a3fe23f9e5` 逐字节还原 ⇒ 复跑丙 **200**。**存储决策 = 内存**（三选一，理由与代价落 `MEM-147`：浏览器持久层被 `test_security_scan.py:79-91` 的无条件字面量断言收窄；代价 = 刷新即失）。**凭据纪律零命中**：全仓只有变量名、`apps/web/src` 无 `Bearer <长串>` 字面量、无 `localStorage.setItem`/`sessionStorage.setItem`、凭据审计四面 `offenders=0`、`test_security_scan.py` **6 passed 且零改动**。**关闭态对照**：stub e2e **98 passed**（与基线**同计数**）、live e2e **53 passed**（同计数）。**web 六门全绿**（lint / typecheck / **94 unit** / build / stub e2e / live e2e）。**设计基线**：结构签名**仅 `settings` 一条**漂移（`nav kids=5→6` + 新增「控制面连接」按钮），按既有流程 `UPDATE_OUTLINES=1` 重生成 + **目检 diff**，**未调容差**；像素基线 **68 张未漂移** | `（见回合汇报）` | **本轮内被门禁抓到并修掉的真问题**：①`test_security_scan.py` 判红——**模块文档注释**里为说明「为什么不选 localStorage」而写出了被禁的**调用形态**字面量（该判据是**子串**扫描、不解析注释）⇒ 改**说明措辞**而非改判据；②`eslint` 3 处（`max-lines-per-function` 52>50、i18n 两行超 100 字符）⇒ 抽 `TokenActions` + 折行；③驱动侧两处**假红/假绿**教训：裸 `fetch` 绕过请求层（丙态必失败）⇒ 改为经**界面**驱动；抓页面文案判失败会读到**残留**错误 ⇒ 改为监听 `page.on("response")` 的一手状态码 | **EC-01 = PASS**（三态 + 成对反证 + 存储决策 + 凭据纪律 + 关闭态同计数 + 基线按流程重生成）；`W-13` **已收口**；`RECHECK-20260926-198` = `PASS_WITH_WARNINGS`（W-1…W-6）。**未覆盖范围**：三态是**本机**实跑，CI 的 `console-frontend` 跑的是**关闭态**（既有 stub + live 套件），**开启态**证据未进 CI 判据；前端输入面**不是**访问控制 | cycle 3 = **EC-03**（认证运维面文档：开启/轮换/关闭 + 401 验证 + 部署面） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-020 落地） | `6cc7561` | M0 [**36246070820**](https://github.com/Eswink/research-system-new/actions/runs/36246070820) / CodeQL [**36246070729**](https://github.com/Eswink/research-system-new/actions/runs/36246070729) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `console-frontend` / `container-quality` / `eval-gate` / `collector-quality` / `quality-ubuntu-latest` / `observability-overhead-ubuntu-latest` / `quality-windows-latest` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (python)` / `Analyze (javascript-typescript)` **3/3 `success`**。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`） |
| cycle 1 实施（EC-02 记录面覆盖） | `（实施提交见回合汇报）` | **依「固定口径」：写下某条记录的那个提交自身的 run 只在回合汇报记账**（不重复回写文件） | 同上 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | ACTIVE | **建档**：用户会话指令（goal 模式）授权把 GOAL-019 的写面认证从「能开启但开启后不可用」推进到「可真正启用」，三条授权 = **前端 token 输入与携带** / **记录面门禁覆盖（方法论；最要紧）** / **认证运维面**。四 EC 设计（前端三态 / 记录面机制 / 运维文档 / 收口复检），budget = 20 / 120 / 2，`fix_policy` 与 `escalation_triggers` 承 GOAL-019 全套并**新增**：不得改 `test_reproducibility_wording.py` 与 `test_control_plane_auth_same_source.py`、不得改 401 形态、不得改 m0 条数、不得用惰性访问器绕过前端持久层安全断言。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA、调用方自报身份、新增依赖、token 落任何地方、改 `Idempotency-Key` 语义、改 401 形态。**建档时零产品代码改动**（只增本文件）。**建档当日实测并写入的判据形态约束**：①前端**单一注入点**存在（`buildHeaders`）且 60 处写请求全覆盖；②`tests/api/test_security_scan.py:79-91` 把 token 存储**收窄为内存**（选 `localStorage` / `sessionStorage` 都需放宽或绕过既有安全判据 ⇒ 命中 BLOCKED）；③**m0 的 `23` 被三处硬编码** ⇒ EC-02 的机制**必须**落在既有 check 内（`tests/**` 属 `python/tests` 收集面）；④**缺陷的真实形状**是**时间性**的（记录面**已**被扫，但本地 SOP 的门跑在记录写入**之前**）⇒ 「全量门包含记录面判据」字面上已成立却不足以修复，机制必须把**结论**与**记录面内容状态**绑定；⑤**记录面扫描面 = 11 条**（内容依赖 8 + 名称依赖 3），可**收口 `W-14`**。建档提交 `6cc7561` 的 CI = **八 job 全 success + CodeQL 3/3**（`run_attempt=1`）。 |
| 2026-09-26 | ACTIVE | cycle 1（PLAN-20260926-196）：**EC-02 = PASS**（本节最要紧的一条）。交付 = 覆盖判据（215 行 / 8 例）+ `LOCAL_GATE_PROTOCOL.md` 顺序节 + `RECHECK-197` + `MEM-146`。**先红**：探针写入记录面 ⇒ 话术判据**单独判红** ⇒ 记录面**本来就在**扫描面内，缺陷是**时刻**（条④得到实测确认）；**后绿**：探针在树时跑 canonical 全量门 ⇒ `python/tests` 判红（= EC-02 要的结论）。**按压 7/7**（6 红 + 1 期望不红，逐字节还原，报实际判红集合）。**判据零改动** + **m0 条数不变**。**终态全量门（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、`4559 passed / 20 skipped`、零 FAILED；日志 `scratch/goal020-c1-m0.log`）。**本轮被全量门抓到两处真红并已修**（format-check / 治理引用自洽）⇒ 定向全绿 ≠ 全量绿，再次实测。`W-14` 已收口。**EC-01 / EC-03 / EC-04 仍 PENDING** ⇒ GOAL 维持 **ACTIVE**，下一 cycle 做前端 token 面。 |
| 2026-09-26 | ACTIVE | cycle 2（PLAN-20260926-197）：**EC-01 = PASS**。前端拿到 token 输入面（设置页「控制面连接」）+ 唯一请求层对**写请求**注入 `Authorization`（读面永不携带）。**三态实跑 5/5**（真实 FastAPI + 真实 vite，写操作经应用自己的请求层）：关闭 ⇒ **200 且不带凭据**；开启 + 无 token ⇒ **401 且页面如实呈现**（非空白/非崩溃）；开启 + 经界面填 token ⇒ **200 且携带凭据、不回显**。**成对反证**去掉注入 ⇒ **401 判红**、sha256 逐字节还原 ⇒ 复绿。**存储方式 = 内存**（三选一；浏览器持久层被既有安全判据的无条件字面量断言收窄，代价 = 刷新即失，理由落 `MEM-147`）。**凭据纪律零命中** + `test_security_scan.py` 零改动且绿。**关闭态与基线同计数**（stub 98 / live 53）。**web 六门全绿**；设计基线仅 `settings` 一条漂移，按流程重生成 + 目检、**未调容差**。`W-13` 已收口。**本轮被门禁抓到并修掉的真问题**：文档注释写出被禁调用形态（子串判据）⇒ 改措辞；eslint 3 处；驱动侧「裸 fetch 绕过请求层」与「抓残留文案」两处假象 ⇒ 改为经界面驱动 + 观测响应。**EC-03 / EC-04 仍 PENDING** ⇒ GOAL 维持 **ACTIVE**，下一 cycle 做运维文档。 |
