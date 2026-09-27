---
id: GOAL-20260927-021
slug: auth-adversarial-self-check
title: 认证面的对抗性自检（证明既有边界真的成立；不加新能力、不放宽判据）
status: ACHIEVED
created_at: 2026-09-27
updated_at: 2026-09-27
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-27 用户会话指令（goal 模式）：**建档 GOAL-021（认证面的对抗性自检：证明现有边界
    真的成立）并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为三件事，**越界即 BLOCKED**：
    **(i) 新增对抗性判据（测试）**、**(ii) 修复被这些判据证明为真缺陷的问题（修产品代码）**、
    **(iii) 文档同源更新**（把自检结论与**未覆盖范围**写进 `docs/security/IDENTITY_AND_ACCESS.md`
    与 `docs/security/THREAT_MODEL.md`）。**不加新能力、不放宽任何判据、不改安全策略**。
    (1) **明确不做（命中即 BLOCKED）**：**给读面加认证**（GET/HEAD 仍放行）；
    **多租户 / RBAC / organization scope**；**BOLA/BFLA 的专项实现**（本轮只做**可在本机验证**的
    对抗性自检；对象级授权实现仍归 M18 / 另行授权）；**调用方自报身份**（单 token ⇒ 单主体不变）；
    **新增依赖**（一律标准库 / 现有栈）；**改任何既有判据、门禁、阈值、放行面**
    （含 `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
    `test_record_face_is_covered_by_the_gate.py`、`tests/egress_guard.py`、`test_m2_audit.py`）；
    **把 token 写进任何文件 / CI / 记录 / 日志**；**改 401 响应形态或 `Idempotency-Key` 语义**；
    **部署面验证**（需真实环境 ⇒ 只允许「登记为不可在本机验证 + 给出可复核检查项」）。
    (2) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (3) **不做真实出网**：本 GOAL **不做真实出网调用**（认证自检全离线）；若判据确需校验 URL，
    仅允许 http/https 且**发请求前校验 host** 并拒绝 localhost / 环回 / 私有 / 保留地址
    （**复用** `endpoint_policy`，不另写判据）；SQL 一律**参数绑定**；凭据**只从环境变量**读取；
    Domain **不得**出现厂商名；观测隐私**不记录完整 Prompt、不记录 token**（AGENTS.md §10）；
    判据中的 token 一律用**测试内构造的假值**，**不得**把真实 token 字面量写进树。
    (4) **边界**：GOAL-001…020 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-018 的**全部 13 项 `D-NN`** 已结清、
    **本 GOAL 不重开**；GOAL-019 / GOAL-020 的**未覆盖范围原样保留**（本 GOAL 只做**自检与登记**，
    不把它们变成已覆盖）。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    对 GOAL-019 / GOAL-020 已落地的**写面认证**做**对抗性自检**：**只新增证明边界的判据**
    （并修复判据**证明为真**的缺陷），回答「这些边界**是否真的成立**」，并**如实登记**
    哪些边界在本机**不可验证**。四条自检面：**①认证不可绕过**（写面全覆盖 + 枚举来自代码 +
    豁免面不被继承 + 顺序被钉住 + 读面按设计放行）、**②token 不泄漏**（日志 / 遥测 / 响应 /
    事件 / 前端持久层 / 记录面）、**③主体归因不可伪造**（不能自报 + 读面不污染 + 不串）、
    **④前端 token 面不是访问控制**（仅内存 + 后端独立成立）。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**零**新依赖；**零**策略面 allow；
    **不得**给读面加认证；**不得**改 401 形态或 `Idempotency-Key` 语义；**不得**宣称项目安全
    （`R-M1` 仍在）；**不得**引入多租户 / RBAC / BOLA·BFLA 实现。
exit_criteria:
  - id: EC-01
    criterion: >-
      **认证不可绕过（写面全覆盖）**，四条各自可判：
      **(a) 枚举来自代码而非手工清单**：从**构建出的 app**（`create_app()` 的 OpenAPI /
      路由表）**机械枚举**全部 mutating 端点，逐个在**认证开启**下发**无 token** 请求 ⇒
      **一律 401**；清单**不得**是手写常量（手写清单会漏网，且会随树漂移而过期）。
      **(b) `_ANALYSIS_ACTIONS` 豁免面不可被滥用为写面**：分析类 POST 的豁免是**幂等**面的语义，
      **不是**认证面的豁免 ⇒ 须**结构地**证明 `PrincipalAuthMiddleware` **没有**继承它
      （既不引用 `_ANALYSIS_ACTIONS`、也不引用 `_is_analysis_post`），且**行为地**证明
      分析类端点（如 `POST /projects/{id}/validate` / `compile` / `preflight`）在认证开启时
      **无 token 同样 401**——即「**幂等面放行 ⟹ 认证面放行**」这一推理是**假的**。
      **(c) 中间件顺序有判据钉住**：`PrincipalAuthMiddleware` 注册在 `IdempotencyMiddleware`
      **之后**（⇒ 后注册者在外层 ⇒ 未认证请求**不**消耗幂等槽位、**不**触达下游）。
      **(d) 读面与探活按设计放行且该设计被显式断言**：`GET/HEAD` 与 `/health` 在认证开启、
      **不带 token** 时放行——**且**这一点是**断言出来的设计**（不是碰巧没拦）。
      **判据须被按压**：临时把某端点移出保护（或把认证面改成继承豁免）⇒ 判据**判红**；
      **逐字节复原** ⇒ 绿。
    verify: >-
      ① 枚举面**来自代码**：判据内调用 `create_app()` 并遍历其路由 / OpenAPI，**不是**手写列表
      （审查判据源码可取此证）；实测计数**写入判据的断言**，并与建档期实测值一致；
      ② 逐个 mutating 端点无 token ⇒ **401**（记录实测计数与失败项，失败项必须为空）；
      ③ 分析类端点无 token ⇒ **401**（与 `(b)` 的结构证明**成对**：结构证明 + 行为证明各一份）；
      ④ `PrincipalAuthMiddleware` 的 AST 面**不引用** `_ANALYSIS_ACTIONS` / `_is_analysis_post`
      （结构判据，读的是**声明**而不是文档话术）；
      ⑤ 注册顺序判据在位（要么复用既有 `test_control_plane_auth_same_source.py` 的 AC-5，
      要么新增**不与之冲突**的判据；**不得**改既有判据）；
      ⑥ 读面 / 探活放行的**显式断言**在位（断言的是「放行是设计」这件事，不只是「200」）；
      ⑦ **按压矩阵**逐轮留档：每一轮报**实际判红的集合**（不是只看红没红），
      sha256 **逐字节复原**后复跑绿；按压打偏（探针自身写错导致没红）**记为失败**。
    status: PASS
  - id: EC-02
    criterion: >-
      **token 不泄漏**（AGENTS.md §10 观测隐私面），五个出口各自可判：**(i) 日志**、
      **(ii) 遥测 / span 属性**、**(iii) 错误响应体**（含 401 的 `detail`）、
      **(iv) 事件 payload**、**(v) 前端持久层**（浏览器存储）+ **记录面**（`.cursor/plans`）。
      判据 = **结构判据**（读**声明 / 代码**，不读文档话术）+ **行为判据**（带 token 发一次写请求，
      检查日志 / 遥测导出里**没有**该值）。**判据自身不得把真实 token 字面量写进树**——
      一律用**测试内构造的合成假值**。
      **反证**：临时把一个 token 值写进日志（或让某出口回显它）⇒ 判据**判红** ⇒ **逐字节复原**。
    verify: >-
      ① **行为判据**：认证开启 + 带合成 token 发写请求，在**捕获的日志记录**与**遥测 span 属性**
      中检索该值 ⇒ **零命中**；
      ② **响应面**：401 的 `title` / `detail` / 整个 body **不含**token 值（且**不**因本轮而改形态）；
      ③ **事件面**：canonical 事件的 payload **不含**token 值（只允许主体**标识**，不允许凭据）；
      ④ **前端持久层**：结构判据证明 `apps/web/src` **零**浏览器持久层写入调用
      （既有 `test_security_scan.py` 已覆盖 ⇒ **不得**改它；新增判据只补**别的**面）；
      ⑤ **记录面**：`.cursor/plans` 与 `.cursor/memory` 中 token **值**零命中（只允许**变量名**）；
      ⑥ **反证**：临时注入一处泄漏 ⇒ 判据红 ⇒ sha256 逐字节复原 ⇒ 复跑绿。
    status: PASS
  - id: EC-03
    criterion: >-
      **主体归因不可伪造**，三条各自可判：
      **(a) 不能自报身份**：请求**无法**影响主体身份——带对 token 时主体**恒为配置主体**；
      任何试图自报的输入（如 `X-Principal-Id` / body 字段 / query 参数）**都不改变**主体；
      **单 token ⇒ 单主体**不变。
      **(b) 读面无认证路径的既有行为与基线一致**：认证开启时**读请求**不带 token ⇒ 主体为
      **`None`**（不被前一个写请求污染、也不被猜成某个身份）。
      **(c) 请求之间不串**：多个请求交错时主体上下文不互相污染。**注意形态**——建档期探针
      **实测**：`asyncio.gather` 并发形态下 `contextvar` 按 **Task** 隔离 ⇒ 即使**去掉**
      `finally: reset_current_principal`，并发判据**仍 0 violations** ⇒ 该形态**不可证伪**；
      **可证伪的形态 = 同一任务内的顺序**（带 token 的写请求之后，紧接一个**不带 token 的读请求**
      ——后者必须看不到前者的主体）。判据**必须**采可证伪形态，并**保留**并发用例作为补充覆盖。
      **（cycle 3 设计期实测补强）** 并发形态**不能**作为唯一判据：其实测结果**取决于父任务上下文**
      （干净 ⇒ **0 violations**；已被污染 ⇒ **20 violations**，子任务继承父上下文）
      ⇒「并发 0 violations」在干净父上下文下可能是**假绿**（只证明「本次没被继承污染」）。
      **顺序形态才是唯一可判红的判据**；并发用例的断言**必须写明前提**（父上下文干净）。
      **反证**：把 `reset_current_principal` 换成 no-op（等价于删掉 `finally` 收尾）⇒
      **可证伪形态判据判红**（读请求看到写请求的主体）⇒ **逐字节复原** ⇒ 绿。
    verify: >-
      ① **自报不可生效**：带对 token + 各种自报输入 ⇒ 主体**仍是**配置主体（逐项留档）；
      ② **三态在位**：认证关闭 ⇒ 放行且主体 `None`；开启 + 无 token ⇒ 401；
      开启 + 对 token ⇒ 放行且主体 = 配置主体；
      ③ **读面基线**：另有一个**写请求在前**的情形下，读请求主体仍 `None`；
      ④ **反证（可证伪形态）**：no-op reset ⇒ 顺序判据**红**（证据须含「哪个断言红了」）；
      sha256 **逐字节复原** ⇒ 绿；
      ⑤ **并发用例**作为**补充覆盖**在位（声明其**不可证伪**的边界，**不得**把它写成
      「已证明并发安全」——它证明的是**该形态下无观察到的污染**）。
    status: PASS
  - id: EC-04
    criterion: >-
      **前端 token 面不是访问控制**（诚实边界），两条各自可判：
      **(a) 仅内存**：`apps/web/src` 的 token 存储**零**浏览器持久层写入（结构判据）；
      **刷新即失**是**已记录的代价**（GOAL-020 的三选一决策，理由见 `MEM-20260926-147`）；
      **(b) 后端独立成立**：**绕过前端**、直接用 HTTP 调 API ⇒ 带 token 成功 / 不带 token **401**
      ——结论**与前端是否存在无关**（后端不依赖任何前端状态）。
      **文档须写明**「**前端 token 面是便利面，不是访问控制**」，并同步进
      `docs/security/IDENTITY_AND_ACCESS.md` 与 `docs/security/THREAT_MODEL.md`。
    verify: >-
      ① **结构判据**：`apps/web/src/**` 零持久层写入调用（既有 `test_security_scan.py` 已覆盖，
      **不得**改它；新增判据补**别的**面，如「token 模块不导出任何持久化通道」）；
      ② **行为判据**：**不经前端**直接带 / 不带 token 调 API ⇒ 200 / 401（后端独立成立）；
      ③ **文档同源**：两处安全文档各含「前端 token 面**不是**访问控制」的同源表述
      （**断言该句在位**，且**不得**被读成更强结论）；
      ④ **文档结论覆盖未覆盖范围**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` **不得**宣称项目安全——**逐条**在位。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口复检 + 残余登记**：
      ① 独立复检脚本（`scratch/`）对**当前树**与**干净 checkout** 跑出**同结论**
      （判词列逐行相同；差异只允许出现在「本 GOAL 自身的 EC 状态文字」上）；
      ② **as-is 本机 m0 到 23/23**（`PASS: profile=m0; 23 deterministic checks`），
      且**运行发生在记录写入之后**（承 MEM-145：写记录 → 记录面判据 → 全量门）；
      ③ 治理 `validate.py` **绿**（含 `DOCS-CHECK`）；
      ④ **CI 台账到终态**（M0 **八 job** + CodeQL，含 `run_attempt`；flake 判定靠**同一代码的复跑对照**）；
      ⑤ **承继残余逐条在位**：`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`；
      ⑥ **未覆盖范围逐条明写**：**读面未认证** / **多租户未做** / **BOLA·BFLA 未做** /
      **部署面未验证** / **`R-M1` 未收口（不得宣称项目安全）**。
    verify: >-
      ① 复检脚本两路输出留档（`scratch/`）且判词列一致 —— **两路 = 当前树 + 干净 checkout**
      （脚本 `--root` 指定树；`--verdict-only` 只输出判词行以利逐行比对；
      两树**共用主树解释器**，否则比的是两套环境）。
      **留档**：`scratch/goal021-c5-verdict-current.txt` / `-clean.txt` ⇒
      **28 行判词全 PASS、`diff` IDENTICAL、`sha256` 相同（`5bb9bc08…`）**；
      **过程缺陷如实登记**：该路**首轮被静默跳过**（未登记且随 EC-05 记 PASS）⇒ 被完成核验判负，
      本轮补跑；**跳过本身记为过程缺陷**（复检范围登记不完整），**非**产品缺陷；
      ② m0 日志留档含终态行 + 运行时刻（在记录写入之后）+ 零 `FAILED` / `ERROR`；
      ③ `validate.py` 输出 `Cursor 治理验证通过`；
      ④ 台账逐 run 逐 job（含 `run_attempt`）；
      ⑤ 残余清单在本文件**逐条**出现；⑥ 未覆盖范围**逐条**出现。
    status: PASS
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
      （含给 `Principal` 加租户 / 角色字段）；或做 **BOLA / BFLA 的专项实现**
    - >-
      新增**任何**依赖（含前端 token 处理引入第三方库；后端仍用标准库
      `hmac.compare_digest`，**不得**用 `==` 直接比）
    - >-
      把 token **值**写进任何 tracked 文件 / CI / 记录 / 日志 / 遥测 / 测试输出
      （含 `.env.example`、workflow、夹具、文档示例、playwright 配置、前端源码、
      **本 GOAL 的判据源码**——判据一律用**测试内构造的合成假值**）
    - >-
      **改认证的 401 响应形态**（`title` / `detail` / ProblemDetail 结构与点名文本）——
      前端**适配**它，**不是**反过来
    - >-
      改 `Idempotency-Key` 语义，或改 `IdempotencyMiddleware` 的
      方法分类 / replay / conflict / record 行为
    - >-
      改 `tests/architecture/python/test_reproducibility_wording.py` 的
      **判据 / 词表 / 扫描面**，或放宽其中任一条
    - >-
      改 `tests/architecture/python/test_control_plane_auth_same_source.py` 的
      **同源句 / 未覆盖锚点 / 必需要求措辞 / `_FORBIDDEN_PHRASES` 词表 / AST 断言**
    - >-
      改 `tests/architecture/python/test_record_face_is_covered_by_the_gate.py` 的
      **判据 / 扫描面 / 顺序语义**，或放宽其中任一条
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
    **引入多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容，
    或做 **BOLA / BFLA 的专项实现** —— **立即 BLOCKED**（对象级授权仍归 M18 / 另行授权）
  - >-
    **新增依赖**（前端或后端；token 处理必须用现有栈 / 标准库）—— **立即 BLOCKED**
  - >-
    **把 token 写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 / 夹具 / 示例 / 前端源码 /
    playwright 配置 / **判据源码**）—— **立即 BLOCKED**；明文凭据泄露（即使可弃用）
    ⇒ 立即停止并报告
  - >-
    **改认证的 401 响应形态**，或改 `Idempotency-Key` 语义 —— **立即 BLOCKED**
  - >-
    **放宽 `test_reproducibility_wording.py` / `test_control_plane_auth_same_source.py` /
    `test_record_face_is_covered_by_the_gate.py`** 的判据 / 词表 / 扫描面 / 阈值 ——
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
  - .cursor/plans/tasks/PLAN-20260927-201-auth-cannot-be-bypassed-on-the-write-face.md
  - .cursor/plans/tasks/PLAN-20260927-203-control-plane-token-never-leaks.md
  - .cursor/plans/tasks/PLAN-20260927-205-principal-attribution-cannot-be-forged.md
  - .cursor/plans/tasks/PLAN-20260927-207-frontend-token-face-is-not-access-control.md
  - .cursor/plans/tasks/PLAN-20260927-209-goal-021-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260927-149-enumeration-must-come-from-code-and-be-pressable.md
  - .cursor/memory/entries/MEM-20260927-150-credential-leak-is-per-exit-and-shape-based.md
  - .cursor/memory/entries/MEM-20260927-151-testclient-hides-contextvar-bleed.md
  - .cursor/memory/entries/MEM-20260927-152-press-restore-must-use-binary-io.md
  - .cursor/memory/entries/MEM-20260927-153-every-declared-recheck-path-needs-its-own-evidence.md
---

## 目标与退出标准

**一句话**：对 GOAL-019 / GOAL-020 已落地的**写面认证**做**对抗性自检**——**只新增证明边界的
判据**（并修复判据**证明为真**的缺陷），回答「这些边界**是否真的成立**」，并**如实登记**
哪些边界在本机**不可验证**。

**本 GOAL 不加新能力、不放宽任何判据、不改安全策略。** 若自检**证明**某边界不成立
⇒ 那是**真缺陷**，修**产品代码**（在授权范围内）；若某边界在本机**无法验证** ⇒
**登记为 PENDING**，**不得**记 PASS。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **认证不可绕过**（枚举来自代码 + 豁免面不被继承 + 顺序钉住 + 读面按设计放行） | 枚举式对抗测试 + 结构判据 + 按压矩阵 | **PASS** |
| EC-02 | **token 不泄漏**（日志 / 遥测 / 响应 / 事件 / 前端持久层 / 记录面） | 结构判据 + 行为判据 + 反证 | **PASS** |
| EC-03 | **主体归因不可伪造**（不能自报 + 读面不污染 + 不串） | 可证伪形态判据 + 反证（no-op reset）+ 并发补充 | **PASS** |
| EC-04 | **前端 token 面不是访问控制**（仅内存 + 后端独立成立） | 结构判据 + 行为判据 + 文档同源 | **PASS** |
| EC-05 | **收口复检 + 残余登记** | 独立复检 28/28 + as-is m0 **23/23** + CI 台账 + 未覆盖范围 | **PASS** |

**依赖关系**：EC-01 / EC-02 / EC-03 互相独立（各判一个面），可分别验收；EC-04 依赖 EC-01 的
枚举面（复用同一套枚举夹具即可，**不**依赖其结论）；**EC-05 最后**，且其 as-is m0 **必须**
在记录写入**之后**跑（承 MEM-145）。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **mutating 端点实测 = 60 处**（`POST` 41 / `PATCH` 9 / `DELETE` 8 / `PUT` 2），分布在
   **17 个 router 文件**（`services/api/routers/` 下共 **29** 个 router 模块，其余 12 个只有读面）。
   两个独立口径**互相印证**：① AST 扫描 `services/api/routers/*.py` 的
   `@router.<method>` 装饰器（含 `async def`）⇒ **60**；② 构建 app 后读 OpenAPI
   `paths` 的 mutating 操作 ⇒ **60**。**用户任务书写的「约 62 处、29 个 router」是近似值**：
   实测 **60 处**；**29** 是 **router 模块总数**（不是「有 mutating 端点的 router 数」= 17）。
   ⇒ **判据必须从代码枚举**（两口径之一），**不得**把任何一个数字写死成手工清单。
2. **写面全覆盖已实测成立**：认证开启 + 60 个 mutating 端点**逐个**发无 token 请求 ⇒
   **60/60 全部 401**（失败项 0）。这是**建档期探针**结论，EC-01 要把它变成**受门禁保护的判据**。
3. **认证在路由之前**：对**不存在**的路径发 `POST` **无 token** ⇒ **401**（不是 404）⇒
   认证中间件**先于**路由匹配执行 ⇒ 「未知路径」不构成绕过面。
   （带 token 时同一请求得 **422**（缺 `Idempotency-Key`）⇒ 形状符合预期。）
4. **认证面未继承幂等豁免（结构证明已得）**：`PrincipalAuthMiddleware` 的 AST 命名面
   **不含** `_ANALYSIS_ACTIONS`，也**不含** `_is_analysis_post` ⇒ 「幂等面放行 ⟹ 认证面放行」
   在**声明层**即为假。EC-01(b) 要再加**行为**证明（分析类端点无 token ⇒ 401）。
5. **中间件顺序已实测**：`app.user_middleware` = `['PrincipalAuthMiddleware', 'IdempotencyMiddleware']`
   ⇒ 认证在外层（先执行）。既有判据 `test_control_plane_auth_same_source.py` 的 AC-5 已钉住
   注册顺序（该文件**不得改动**）。
6. **401 响应体不含 token**（实测）：缺头与错 token 两种 401 的 body 均不含 token 值；
   两种 `detail` **各自点名**成因（缺 Bearer 头 / 不匹配）。
7. **EC-03 的反证形态必须修正（建档期实测所得，最要紧的一条）**：任务书原拟「**去掉
   `finally: reset` ⇒ 并发判据红**」。**实测该形态不可证伪**——把 `reset_current_principal`
   换成 **no-op** 后，`asyncio.gather` **60 个读写请求混发**仍为 **0 violations**（`contextvar`
   按 **Task** 隔离，每个请求各在自己任务里跑）。
   **可证伪的形态**是**同一任务内的顺序**：带 token 的写请求**之后**紧接一个**不带 token 的
   读请求** ⇒ 基线（`finally` 在位）**读请求主体 = `None`**；no-op reset 后**读请求主体 =
   `service:probe-principal`**（**污染**，判据红）。⇒ EC-03 的判据**必须**采顺序形态才可证伪；
   并发用例保留为**补充覆盖**并**明写其不可证伪的边界**（**不得**写成「已证明并发安全」）。
   **这条修正同时是一条方法学结论**：把「删掉某行 ⇒ 判据红」写进退出标准**之前**，
   必须**先实测该反证真的会红**，否则该 EC **不可证伪**、会卡死循环。
   **cycle 3 设计期进一步实测（把上面「并发不可证伪」一句说准）**：
   `asyncio.gather` 形态的结果**取决于父任务上下文状态**——
   `scratch/goal021-ec03-probe-concurrency-precondition.py` 实测：
   **父上下文干净 ⇒ 0 violations**；**父上下文已被泄漏污染 ⇒ 20 violations**
   （子任务**继承**父上下文）。⇒ 结论：**并发形态不能作为唯一判据**——
   它的「0 violations」在**干净父上下文**下可能是**假绿**（看上去像「并发安全」，
   其实只证明了「本次没被继承污染」）。**EC-03 的判据组合**：
   **① 顺序形态（可证伪，唯一可判红的判据）** + **② 并发形态（补充覆盖，
   且必须在断言里写明前提「父上下文干净」）**；**③ 自报不可生效**（实测：
   带对 token 时 `X-Principal-Id` / `X-Actor` / query 参数 / body 字段全部无效，
   请求照常 201 ⇒ 身份不变）。
8. **主体上下文在读面正确回退**（实测）：认证开启时无 token 的 `GET` ⇒ 主体 `None`；
   带 token 的写请求 ⇒ 主体 `Principal(id=<配置>, kind=SERVICE)`（`actor` = `service:<id>`）。
9. **记录面 / 凭据审计面**：`tools/credential_audit.py` 是本仓既有凭据审计入口（五类形态）；
   `test_reproducibility_wording.py` 的扫描面含 `.cursor/plans`（承 GOAL-020 EC-02）。
   ⇒ 写本 GOAL 与其记录**不得**出现 token **值**（只允许**变量名**）。
10. **规模门禁**：单文件 ≤ 300 行通过 / 301–450 警告 / **> 450 硬失败**（`.cursor/rules/40-python.mdc`
    与 `41-typescript.mdc`）；单函数 **> 50 行**受限。新增判据文件须**先算行数**，
    必要时拆多文件（`tests/egress_guard.py`、`tests/e2e/live_run_support.py` 等零/近零余量文件
    **不在本轮改动面内**；`W-6` 明写 `tests/e2e/live_run_support.py` 只剩 1 行余量）。
11. **m0 的 `23` 被硬编码**在 `tools/quarantine_and_run_m0.py:34`、
    `tools/classify_local_gate_reds.py:108`、`docs/architecture/LOCAL_GATE_PROTOCOL.md:31`
    ⇒ **新增判据必须落在既有 check 的收集面内**（`tests/**` 属 `python/tests`），
    **不得**新增 m0 check（否则三条硬编码与终态行同时打断）。
12a. **`framework/run_cursor_framework_evals` 的偶发红（cycle 3 实测并归因）**：该 check 会向
   `.cursor/runtime/evolution_state.json` 做「写 tmp + `os.replace`」。**并发/残留 tmp** 下
   Windows 会抛 `PermissionError: [WinError 5]`（栈顶 `hooks/common.py` 的 `os.replace`）⇒
   **环境类**红，**不是**代码缺陷。**取证配方**：确认无其它 m0 / pytest 在跑 → 清残留
   `.cursor/runtime/evolution_state.json.tmp` → **单独**跑该 check（得 `FRAMEWORK EVAL PASS`）
   ⇒ 独占重跑完整门。**不得**改该 check 的阈值或断言。
12. **worker 网关是独立 app**（`create_worker_app`），**不**挂在控制面 app 上 ⇒ 本 GOAL 的
    写面枚举面**只**覆盖控制面（worker 面有自己的信任域，**不在**本轮范围）。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 默认门一律离线**（不需要 `.env` 凭据；**不做真实出网调用**）。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-021-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-021**」（**不是**把 GOAL-020 置回 ACTIVE）。
理由：**「对抗性自检」是新范围**（证明边界**是否成立**），而 GOAL-019 / 020 的取证面是
「边界**被实现**」与「认证**可启用**」——**不重叠**；且 GOAL-020 的判词含
「`apps/web/**` 新增判据」等面，本 GOAL 的**新增测试面**需在新 GOAL 下才不互相顶替。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260927-021` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      **不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件**——新增判据文件先算行数）；
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

- **判据自身恒真（承 MEM-141）**：新判据**不得**被文档引用 / 字面量喂饱——必须绑定
  **声明行**或**行为**，且**必须被按压过**（临时破坏 ⇒ 判红 ⇒ **逐字节复原**）。
- **反证必须先验形态**（承第 7 条事实）：写「删掉 X ⇒ 判据红」**之前**先实测该反证**真的会红**；
  不可证伪的形态**不得**写进退出标准。
- **撤回纪律**：改共享夹具 / 中间件时**先数清谁拿它的失败形态当夹具**；
  CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：任何起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧复验**。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先，禁改断言迁就**；若红的是**本轮新增判据**且根因是判据自身写错 ⇒ 改判据（并**按压**复验） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、RSS 阈值型） | 按既有配方重跑；**flake 判定必须靠同一代码的复跑对照**；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 **全部 PASS** 且有**实跑证据**（每条含**先红后绿**或
  **边界成立**的证据）+ 独立 RECHECK `PASS` / `PASS_WITH_WARNINGS` + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + **未覆盖范围逐条明写**。
  **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **做 BOLA·BFLA 实现**、**新增依赖**、**把 token 写进任何地方**、**改 401 形态或
  `Idempotency-Key` 语义**、**放宽任何既有判据 / 门禁 / 阈值**、**改 m0 条数**、
  **放宽 §9 默认 deny**、**宣称项目安全**、**Canonical State 边界**、**真实 runtime 设为默认**）、
  同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles`
  个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。
- **本 GOAL 的收口判词必须写明**：**四条自检各自的结论**（各附**先红后绿**或
  **边界成立**的证据）、**自检中发现的真缺陷清单**（若有；**空必须明写是空**）、
  **as-is 本机 m0 的终态行**（若未达 ⇒ 如实登记**是哪一条**拦着、**哪种跑法**）、
  **未覆盖范围**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1`），
  以及 **401 响应形态与 `Idempotency-Key` 语义是否一字未动**。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`.cursor/plans/goals/GOAL-20260926-018-residual-closeout-and-decision-register.md`
的「不进入循环 / 需人工拍板」节 + `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**（`D-01` / `D-02` / `D-07` / `D-08` / `D-09` / `D-10` / `D-11` / `D-12` / `D-13`）、
**部分实施 1 项**（`D-03`：`vite` 已升 + `yaml` 已升；`undici` 已调研未升）、
**已拍板为维持现状 3 项**（`D-04` / `D-05` / `D-06`）、**未授权待拍板 0 项**。
⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019 的五条残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（本 GOAL 的 EC-03(a) **只证明「不能自报」**，**不**实现逐调用方身份——那属另行授权 / M18） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留**（本 GOAL 的对抗性自检**不**做对象级授权） |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **原样保留**（GOAL-020 已给检查项与不可验证登记；本轮**不**把它变成已验证） |
| `W-13` | 前端无 token 输入面 | 已由 GOAL-020 **收口**（**不改回**） |
| `W-14` | 记录面判据的扫描面未逐一核实 | 已由 GOAL-020 **收口**（**不改回**） |

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

1. **读面认证（GET / HEAD）**——**不做**（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
2. **多租户隔离 / organization scope**——**不做**（M18）；
3. **RBAC / 角色 / 权限矩阵**——**不做**；
4. **BOLA / BFLA 的专项实现**——**不做**（本轮只做**可在本机验证**的对抗性自检；
   对象级授权实现仍归 M18 / 另行授权；**如实保留**）；
5. **调用方自报身份**（caller-declared identity）——**不做**（单 token ⇒ 单主体）；
6. **新增依赖**——**不做**（一律标准库 / 现有栈）；
7. **改任何既有判据 / 门禁 / 阈值 / 放行面**——**不做**（含
   `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
   `test_record_face_is_covered_by_the_gate.py`、`tests/egress_guard.py`、`test_m2_audit.py`）；
8. **改 `Idempotency-Key` 语义**——**不做**；
9. **改认证的 401 响应形态**——**不做**（前端**适配**它，**不是**反过来）；
10. **把 token 值写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出 / 前端源码 /
    判据源码**——**不做**（**只登记变量名**，**绝不留值**）；判据一律用**测试内构造的合成假值**；
11. **部署面验证**（需真实环境）——**只允许**「登记为不可在本机验证 + 给出可复核检查项」；
12. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
13. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
14. **`undici` 的 pin**——**不动**（归属上游，见 D-03 终态）；
15. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**。

**承继的诚实边界（如实保留，不是待办）**：

- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（且**不得**用「对抗性自检通过了」替代它——**自检通过 ≠ 项目安全**）。
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

**本 GOAL 交付的是「边界的自检证据」，不是「授权面已覆盖」**：
证明「认证不可绕过 / token 不泄漏 / 主体不可伪造 / 前端不是访问控制」**不等于**有授权模型；
`THREAT_MODEL.md` §6.3 明写**读面未认证**、**BOLA·BFLA 未做**、**不覆盖前端**。
本 GOAL **不产生**对象级授权实现，也**不**把自检结论写成安全结论。
**关键区分**：本 GOAL 的判据证明的是「**已声明的边界成立**」；
它**不能**证明「**不存在未声明的缺口**」（那是另一类工作，且本机不可穷尽）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `8d36605`（**建档提交**，推送区间 `75cb667..8d36605`） | 治理 `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS`；**判据按压**：临时抹掉本文件一处章节标题字面（`## 状态历史` ⇒ `## TAMPERPROBE`）⇒ `validate.py` 判红（`GOAL 缺少章节 ## 状态历史: GOAL-20260927-021`）⇒ 证明新建的 GOAL **确实被载入判据**（报的是**本 GOAL 的 ID**，不是碰巧）；逐字节复原（sha256 `8f758379e1cf2f71…` 前后一致）⇒ 绿。**按压方法学（承 GOAL-020 的既有发现）**：该章节判据是**子串包含** ⇒ 必须**整个抹掉**字面才判红，追加后缀**不会**判红。**建档当日实测（六项，写入上文「事实层结论」）**：mutating 端点 **60**（两口径互证）/ 无 token **60/60 全 401** / 未知路径 POST **先 401 后路由**（**带 token 才 422**）/ `PrincipalAuthMiddleware` AST **不引用** `_ANALYSIS_ACTIONS` / `user_middleware` 顺序 **认证在外层** / 401 body **不含** token。**最要紧**：**EC-03 的反证形态实测修正**——`asyncio.gather` 并发形态**不可证伪**（no-op reset 后仍 **0 violations**；contextvar 按 Task 隔离），**可证伪形态 = 同一任务内顺序**（no-op reset 后读请求看到写请求的主体）。**记录面自查**：本文件落在 `test_reproducibility_wording.py` 扫描面内且**零命中**其词表；**零** token 值（只登记**变量名**）；`credential_audit.py` 四面 **offenders=0**。**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4558 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c0-m0-final.log`）。**建档轮实测并修掉一处调用侧假红**：首跑直接调 `.venv/Scripts/python.exe` ⇒ `tests/architecture/python/test_dependency_boundaries.py` 抛 `RuntimeError: lint-imports executable is unavailable`，**连坐 12 条**边界套件（`dependency-boundaries` 1 + `domain/otel/relay/services-api/worker` 11）⇒ 改用 **canonical `uv run --frozen --no-sync python -B`**（`uv run` 才把 `.venv/Scripts` 放进子进程 `PATH`）后**同一条命令全绿** ⇒ 那 12 条是**调用错误**、**零**产品缺陷 | M0 [**36298094585**](https://github.com/Eswink/research-system-new/actions/runs/36298094585) **八 job 全 success**（`container-quality` / `observability-overhead-ubuntu-latest` / `collector-quality` / `quality-windows-latest` / `eval-gate` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` / `console-frontend`）+ CodeQL [**36298094168**](https://github.com/Eswink/research-system-new/actions/runs/36298094168) **3/3 success**（`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)`）；**两者 `run_attempt=1`，一次成功、无 flake**；日志 `scratch/goal021-c0-ci-poll.log`（`ALL_TERMINAL sha=8d366050a214debc24835a4a96f40d784fecee39`）。**外部旁证**：push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`），与 GOAL-018/019/020 收口**一致** ⇒ 本轮**零依赖改动** | — | EC-01…EC-05 全 PENDING。起点已定位：枚举面**两个可达口径**（AST 装饰器 / OpenAPI paths，均为 60）；判据须落 `tests/**`（属 `python/tests` 收集面）以免动 m0 的 23；反证形态**必须**先实测可证伪性 | cycle 1 = **EC-01**（认证不可绕过：枚举来自代码 + 豁免不继承 + 顺序 + 读面设计，四条一次做完；它是其余 EC 的**枚举夹具来源**） |

| 1 | PLAN-20260927-201（EC-01） | `96508dc`（derive）；实施 + 记录见回合汇报 | **EC-01 四条全部成立且有实跑证据**。交付 = 新判据 `tests/api/test_write_face_cannot_be_bypassed.py`（**285 行 / 18 例**，零超长函数）+ `RECHECK-20260927-202`（`PASS_WITH_WARNINGS`）+ `MEM-20260927-149`。**枚举来自代码**：两口径互证 **60**（AST 装饰器 = OpenAPI paths；覆盖 **17** 个 router 文件；任务书写「约 62 处、29 router」⇒ **如实更正**：60 处，29 是 router 模块总数）。**(a) 全覆盖 401**：60 个端点无 token **全 401**、错 token **全 401**（`leaked == []`）。**(b) 豁免不被继承**：结构面由既有 AC-4 判（**未改该文件**）+ **行为面新增**：8 条分析类 POST（`validate` ×2 / `compile` / `preflight` / `dry-run` / `test` / `discover-models` / `probe`）无 token **全 401**，并有带对 token 的**配对对照**。**(c) 顺序**：由既有 AC-5 判（**未改该文件**）。**(d) 读面按设计放行**：`/health` + 读面不带 token 放行，且断言的是**机制**（分类不含 GET/HEAD）而非观察值；另有「**写面路径上的 GET 不被挑战**」这条最锋利形态（区分「按方法分类」与「按路径保护」）。**按压矩阵 3/3 红**（逐轮报**实际判红集合**）：PRESS-1 删 `DELETE` ⇒ **3 failed**；PRESS-2 加 `GET` ⇒ **4 failed**；PRESS-3 继承 `_is_analysis_post` 豁免 ⇒ **10 failed**（8 个分析类路径**逐个**红）。三轮 `sha256` 复原一致（`ca03dac3…`）+ `git diff` **IDENTICAL TO HEAD**；定向套件 **53 passed**。**既有判据零改动**（四个受保护文件 `git diff --quiet` 全 UNCHANGED）。**零产品代码改动**（判据**未证明**任何缺陷 ⇒ **边界成立**，不是「修好了」）。**本轮被全量门抓到并修掉一处真红**：`python/typecheck` 判红 **7 处**——`TestClient.app` 静态类型是 ASGI callable（非 `FastAPI`）⇒ 收敛一处 `_app_of()` 类型收窄（按本仓既有 `cast(Any, client.app)` 约定），**不是**加 `# type: ignore` 抑制；⇒ **定向套件绿 ≠ 全量门绿**（该 check 只有全量门跑到）。**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4577 passed / 21 skipped**、零 `FAILED`；日志 `scratch/goal021-c1-m0-final.log`） | M0 [**36304309642**](https://github.com/Eswink/research-system-new/actions/runs/36304309642) **八 job 全 success** + CodeQL [**36304309147**](https://github.com/Eswink/research-system-new/actions/runs/36304309147) **3/3 success**（`run_attempt=1`，一次成功、无 flake） | **零真缺陷**（自检结论 = 边界成立）。**如实登记五条警告**（`RECHECK-202` 的 `W-1`…`W-5`）：①`_MEASURED_MUTATING_COUNT = 60` 是**会失效的告警线**（增删端点会红以提示复核，非保护面定义 ⇒ 只误报不漏洞）；②本轮覆盖**只限控制面 app**（worker 网关是独立 app、未挂载 ⇒ 实测控制面 35 条路由**零** worker 路由）；③枚举覆盖的是 **app 声明过的**端点——绕过 FastAPI 路由的写（SSE 内副作用 / 调度器触发）**不覆盖**；④按压是**内存态**破坏，证明「判据对这类破坏敏感」，不证明「CI 会拦住提交」（后者由判据本身在 CI 中覆盖）；⑤合成假 token ⇒ **不**验证真实 token 的熵 / 轮换 | **EC-01 = PASS**（四条 + 按压 3/3 + 判据零改动 + 零产品缺陷）。**未覆盖范围**原样保留：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 不得宣称项目安全 | cycle 2 = **EC-02**（token 不泄漏：日志 / 遥测 / span / 401 body / 事件 payload / 前端持久层 / 记录面；结构判据 + 行为判据 + 反证） |

| 2 | PLAN-20260927-203（EC-02） | `7ff26dd` | **EC-02 六出口全部成立且有实跑证据**。交付 = 新判据 `tests/api/test_control_plane_token_never_leaks.py`（**312 行 / 12 例**）+ `RECHECK-20260927-204`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260927-150`。**逐出口判**（不笼统断言）：**日志**三类请求捕获 ⇒ token 零命中，**且捕获装置自证有效**（哨兵记录能被截到 ⇒ 排除「没捕到」的假绿）；**遥测**未知键（`authorization` / `raw_headers` / `request_body`）**整个丢弃**（闭集 allow-list）+ 允许键 + bearer 形态**必被脱敏** + 允许键 + **裸不透明串会留下**（**如实断言现状**）；**401 body** 两个 401 零命中且成因**各自点名**；**成功响应**不回显；**事件 payload** 零命中且 `actor` 是**标识**；**记录面** 凭据值零命中且**变量名**在位（排除扫描面选错）。**反证 1/1 红**（中间件里记一条含 `provided` 的日志 ⇒ `test_no_log_record_contains_the_token` **1 failed**）⇒ `sha256` 复原一致（`ca03dac3…`）+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **12 passed**。**既有判据零改动**（五个文件 `git diff --quiet` 全空）。**受影响套件 745 passed / 4 skipped**。**本轮修掉的缺陷 = 判据自身 1 处**（记录面判据首版用 `__next__()` 取任意文件 ⇒ 自己判红且理由错），**零产品代码改动** | M0 [**36308760177**](https://github.com/Eswink/research-system-new/actions/runs/36308760177) **八 job 全 success** + CodeQL [**36308760234**](https://github.com/Eswink/research-system-new/actions/runs/36308760234) **3/3 success**（`run_attempt=1`，一次成功、无 flake；日志 `scratch/goal021-c2-ci-poll.log`） | **零真缺陷**（自检结论 = 边界成立）。**如实登记五条警告**：**`W-1`（最要紧）** 脱敏是**形态匹配**而非**值匹配** ⇒ **裸不透明串**在**允许键内会被原样导出**（已独立复现）——这要求「允许键的值不得承载凭据」靠**上游纪律**保证，**未收口**；②日志面只覆盖**本进程捕获到的记录**（外部采集链不在范围）；③记录面判据依赖「变量名至少出现一次」⇒ 记录归档后会红（属提示）；④前端持久层是**引用**既有判据（该文件未改）而非独立复验；⑤合成假 token ⇒ 不验证真实 token 的形态分布 | **EC-02 = PASS**（六出口 + 反证 1/1 + 判据零改动 + 零产品缺陷）。**未覆盖范围**原样保留：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 不得宣称项目安全 | cycle 3 = **EC-03**（主体归因不可伪造：不能自报 + 读面不污染 + 不串；**注意**：`TestClient` 会让该类判据**不可证伪**（每请求各起任务）⇒ 必须用 **ASGITransport + 同任务 await**；并发形态的结果**取决于父任务上下文**（干净 0 / 已污染 20）⇒ 只能作补充覆盖） |

| 3 | PLAN-20260927-205（EC-03） | `14c5c02` | **EC-03 三条全部成立且有实跑证据**。交付 = 新判据 `tests/api/test_principal_cannot_be_forged.py`（**311 行 / 15 例**）+ `RECHECK-20260927-206`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260927-151`。**自报不可生效**：`X-Principal-Id` / `X-Actor` / `X-Principal` 头、query 参数、body 字段**全部无效**（真实 app 带自报头照常 201 但主体不变）；**`Principal` 字段集恰为 `{id, kind}`**（无 tenant / role ⇒ **M18 边界是机械事实**）；`id` 含 `:` 抛 `ValueError`。**读面无主体**：在前有写请求、连续 5 写、交替 4 轮、被拒写请求之后 —— 读请求**全部** `None`（认证关闭亦然）。**顺序形态可判红**。**本轮最要紧的发现（先红后绿的关键）**：首版判据用 `TestClient` ⇒ **按压不红（14 passed）** ⇒ 该驱动**每请求各起任务**把「写请求主体残留」遮住 ⇒ 判据**不可证伪（假绿）**；改用 **`ASGITransport` + 同任务 `await`** 后同一按压 **4 failed** ⇒ **按纪律记为「按压打偏」并改正**。**反证**：`finally: reset` 换 `pass` ⇒ **4 failed** ⇒ `sha256` 复原一致（`ca03dac3…`）+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **15 passed**。**既有判据零改动**（四文件 `git diff --quiet` 全空）；**零产品代码改动** | M0 [**36314808492**](https://github.com/Eswink/research-system-new/actions/runs/36314808492) **八 job 全 success** + CodeQL [**36314808285**](https://github.com/Eswink/research-system-new/actions/runs/36314808285) **3/3 success**（`run_attempt=1`，一次成功、无 flake；日志 `scratch/goal021-c3-ci-poll.log`） | **零真缺陷**（自检结论 = 边界成立）；**修掉判据自身 1 处**（驱动形态选错）。**如实登记五条警告**：**`W-1`（最要紧）** **并发形态不能单独读作「并发安全」**——实测结果**取决于父任务上下文**（干净 **0** / 已污染 **20**，子任务继承父上下文）；并发用例**已写明前提且不作安全结论**，**未收口**（`contextvar` 语义固有）；② `TestClient` 与 `ASGITransport` 在该面行为不同 ⇒ 本仓**其它**依赖请求级 `contextvar` 的判据**可能**同属不可证伪而未自知（本轮**只修本 EC**，**未普查**全仓）；③ 只覆盖**控制面请求级主体**——后台线程 / 调度器路径**无请求主体**（按设计回退常量），**不覆盖**其归因；④ 单 token ⇒ 单主体，「不可伪造」只到「主体 == 配置主体」这一层，**逐调用方身份不存在**、**BOLA·BFLA 未做**；⑤ 合成假 token ⇒ 不验证真实 token 形态分布 | **EC-03 = PASS**（三条 + 按压 4/4 红 + 判据零改动 + 零产品缺陷）。**未覆盖范围**原样保留：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 不得宣称项目安全 | cycle 4 = **EC-04**（前端 token 面不是访问控制：仅内存结构性 + 后端独立成立的行为判据 + 两处安全文档同源） |

| 4 | PLAN-20260927-207（EC-04） | `0693d89`（含 cycle 3 台账） | **EC-04 两条全部成立且有实跑证据**。交付 = 新判据 `tests/api/test_frontend_token_is_not_access_control.py`（**163 行 / 6 例**）+ `RECHECK-20260927-208`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ 两处安全文档同源登记。**判定点只在后端**：绕过前端直调 API ⇒ 无 token **401** / 有 token **201**（同一请求，差别只在请求头）；中间件源码**不含** `localStorage` / `apps/web` / `window.` / `document.` 等前端概念；被拒的写请求**不改动 canonical**。**仅内存且单一持有**：token 模块**代码**（剥注释后）零持久化命中 + 两条反向对照；`apps/web/src` 里**无别处**保存 token 值。**文档同源**：`IDENTITY_AND_ACCESS.md` 未覆盖范围新增**第 8 条** + `THREAT_MODEL.md` §6.3 第 3 条追加实况更新；既有同源 / 话术 / 安全扫描判据 **22 passed**；**未触发** `_FORBIDDEN_PHRASES`；同源句与锚点**仍恰好一次**。**反证 1/1 红（含一次按压打偏的如实登记）**：临时给 `setControlPlaneToken` 加持久层写入 ⇒ 既有 `test_security_scan.py` **1 failed**，但**首版本 EC 判据 6 passed（未红）** ⇒ 首版只断言**导出函数名**、**不绑定行为** ⇒ **不可证伪** ⇒ **记为「按压打偏」并修正**（改为剥注释后扫代码）⇒ 修正后同一按压 **1 failed**；复原后 `sha256` 一致（`32d7c4fc…`）+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **12 passed**。**既有判据零改动**（三文件 `git diff --quiet` 全空）；**web 门** lint / typecheck 通过、unit **94 passed**；**零产品代码改动** | M0 [**36317696507**](https://github.com/Eswink/research-system-new/actions/runs/36317696507) **八 job 全 success** + CodeQL [**36317695934**](https://github.com/Eswink/research-system-new/actions/runs/36317695934) **3/3 success**（`run_attempt=1`，一次成功、无 flake；日志 `scratch/goal021-c45-ci-poll.log`） | **零真缺陷**（自检结论 = 边界成立）；**修掉判据自身 1 处**（断言不绑定行为）。**如实登记五条警告**：**`W-1`** 结构判据与前端既有判据**方向一致、互为冗余**（**冗余是刻意的**：EC-04 要在**后端套件**里独立发现该回归，不必依赖 web 门被跑到；代价 = 改纪律要顾及两处）；②「前端不是判定点」是**结构判据**（扫源码无授权逻辑），**不能**排除「授权判断藏在别的模块」（属代码审查面）；③**XSS 未测**——内存态同样可被同源脚本读取，本 EC 只证明**不落持久层**；④行为判据是**本机**实跑，CI 的 `console-frontend` 跑**关闭态**⇒ 开启态浏览器侧证据**未进 CI 判据**；⑤刷新即失是**选定的代价**（非缺陷），长期操作者会反复粘贴 | **EC-04 = PASS**（两条 + 反证 1/1 + 判据零改动 + 零产品缺陷）。**未覆盖范围**原样保留：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 不得宣称项目安全 | cycle 5 = **EC-05**（收口复检：两树同结论 + as-is m0 23/23 + 治理 validate 绿 + CI 台账到终态 + 残余与未覆盖范围逐条） |

| 5 | PLAN-20260927-209（EC-05 收口） | 收口提交（**本行由该提交写入** ⇒ 依「固定口径」其 SHA 只在回合汇报记账、不回写文件） | **独立复检 28/28**（`scratch/goal021-ec05-closeout-recheck.py`；六面）：交付面 6（4 判据 **285/312/311/163** 行 + 4 PLAN 在位）/ **按压面 3**（收窄保护面 ⇒ EC-01 判据 **exit=1**；复原 ⇒ **exit=0**；raw **sha256 逐字节一致**）/ 受保护判据零改动 5（`test_security_scan` / `test_secret_redaction` / `test_reproducibility_wording` / `test_record_face_is_covered_by_the_gate` / `test_control_plane_auth_same_source` 全 UNCHANGED）/ 残余 5（`R-M1` / `R-D1` / `W-10` / `W-11` / `W-12` 逐条在位）/ 未覆盖范围 5（读面未认证 / 多租户 / BOLA / 部署面 / `R-M1` 逐条在位）/ 凭据面 2（扫 9 文件**零** `Bearer <长串>` 字面量；变量名**正确落点** 3/3）。**as-is 本机 m0（记录写完之后）** = `PASS: profile=m0; 23 deterministic checks`（`PASS [` = **24**、**4613 passed / 21 skipped**、零 `FAILED`；日志 `scratch/goal021-c4-m0-final.log`）。治理 `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS`；**as-is 本机 m0（记录写完之后，ACHIEVED 态）** = `PASS: profile=m0; 23 deterministic checks`（`PASS [` = **24**、**4613 passed / 21 skipped**、零 `FAILED`；日志 `scratch/goal021-c5-m0.log`）；**补跑两树对照后复跑**（记录再写完）仍为 `PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24、4613 passed / 21 skipped、零 `FAILED`；日志 `scratch/goal021-c5-m0-twotree.log`） | 本行所在的记录提交（依固定口径只在回合汇报记账） | **本轮修掉复检脚本自身 2 处缺陷（非产品）**：①按压复原用**文本模式**读写 ⇒ Windows 把 LF 写成 CRLF ⇒ raw `sha256` 不一致（而 `git diff` 因 `.gitattributes` 归一化**报无改动** ⇒ 只有 raw sha256 能抓该假象）⇒ 改 **`read_bytes`/`write_bytes`**，落 `MEM-20260927-152`；②凭据面「变量名应在 GOAL 正文」断言写错（变量名落在**实现 / 安全文档**面）⇒ 改为扫**正确落点** ⇒ 3/3 在位 | **两树同结论（补跑）**：`git worktree add --detach ../goal021-clean-tree HEAD` ⇒ 同脚本 **`--root`** 跑两树 ⇒ 各 **28 行判词全 PASS**、`diff` **IDENTICAL**、判词文件 `sha256` **相同**（`5bb9bc08…`）；按压后两树均干净（干净 checkout `git status` 空 / 主树 `middleware.py` `numstat` 空）⇒ 逐字节复原在两树都成立。**首轮曾静默跳过该条款**（未登记、却随 EC-05 记 PASS）⇒ 被完成核验判负，本轮**补跑并留档**，**该跳过记为过程缺陷**（复检**范围登记不完整**） | **EC-01…EC-05 全 PASS** ⇒ GOAL 置 **ACHIEVED**。**残余终态**：全部**原样保留**（本 GOAL 只做自检与登记，**不把任何未覆盖面变成已覆盖**）——`W-10`（单 token ⇒ 单主体）/ `W-11`（BOLA·BFLA 未做）/ `W-12`（部署面未验证）/ `R-M1`（**不得**宣称项目安全）/ `R-D1`（`undici` 归属上游）。**未覆盖范围**：读面未认证 / 多租户与 RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口。**四条自检的结论**（各附证据形态）：**①认证不可绕过** = 边界成立（60/60 无 token 全 401 + 按压 3/3 红）；**②token 不泄漏** = 边界成立（六出口 + 反证 1/1 红；`W-1` 脱敏是**形态匹配**）；**③主体不可伪造** = 边界成立（自报全无效 + 按压 4/4 红，**含一次按压打偏的如实登记**）；**④前端不是访问控制** = 边界成立（判定点只在后端 + 反证 1/1 红，同样**含一次按压打偏**）。**自检中发现的真缺陷清单 = 空**（四条自检**均未**证明产品缺陷；本轮修掉的都是**判据 / 复检脚本自身**的问题） | —（**终态，无下一轮输入**）。后续若要推进：**BOLA·BFLA 与逐调用方身份需另行授权**；**部署面验证需要真实拓扑** |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-021 落地） | `8d36605` | M0 [**36298094585**](https://github.com/Eswink/research-system-new/actions/runs/36298094585) / CodeQL [**36298094168**](https://github.com/Eswink/research-system-new/actions/runs/36298094168) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `container-quality` / `observability-overhead-ubuntu-latest` / `collector-quality` / `quality-windows-latest` / `eval-gate` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` / `console-frontend` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ 零依赖改动。轮询日志 `scratch/goal021-c0-ci-poll.log` |
| cycle 1 实施（EC-01） | `746e320` | M0 [**36304309642**](https://github.com/Eswink/research-system-new/actions/runs/36304309642) / CodeQL [**36304309147**](https://github.com/Eswink/research-system-new/actions/runs/36304309147) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `collector-quality` / `container-quality` / `console-frontend` / `eval-gate` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `quality-ubuntu-latest` / `quality-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**。轮询日志 `scratch/goal021-c1-ci-poll.log`（`ALL_TERMINAL sha=746e3208c03c6a8252fd7c8be4de911b5b25dd85`） |
| cycle 2 实施（EC-02） | `7ff26dd` | M0 [**36308760177**](https://github.com/Eswink/research-system-new/actions/runs/36308760177) / CodeQL [**36308760234**](https://github.com/Eswink/research-system-new/actions/runs/36308760234) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：逐 job `container-quality` / `observability-overhead-windows-latest` / `console-frontend` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `eval-gate` / `collector-quality` / `quality-ubuntu-latest` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c2-ci-poll.log`（`ALL_TERMINAL sha=7ff26ddb50ef045b8ba9783b4056e49fd34a8afe`） |
| cycle 3 实施（EC-03） | `14c5c02` | M0 [**36314808492**](https://github.com/Eswink/research-system-new/actions/runs/36314808492) / CodeQL [**36314808285**](https://github.com/Eswink/research-system-new/actions/runs/36314808285) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：逐 job `console-frontend` / `eval-gate` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `collector-quality` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c3-ci-poll.log`（`ALL_TERMINAL sha=14c5c02bad94b9ef7f4fa768e0263107bf04932b`） |
| cycle 3+4 实施（EC-03 台账 + EC-04） | `0693d89` | M0 [**36317696507**](https://github.com/Eswink/research-system-new/actions/runs/36317696507) / CodeQL [**36317695934**](https://github.com/Eswink/research-system-new/actions/runs/36317695934) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：逐 job `collector-quality` / `container-quality` / `quality-ubuntu-latest` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `quality-windows-latest` / `console-frontend` / `eval-gate` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c45-ci-poll.log`（`ALL_TERMINAL sha=0693d89619faab8cd9b48e74776422f34d32103a`） |
| 收口（EC-05） | `ba7efcd` | M0 [**36320330361**](https://github.com/Eswink/research-system-new/actions/runs/36320330361) / CodeQL [**36320329653**](https://github.com/Eswink/research-system-new/actions/runs/36320329653) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功、无 flake**）：逐 job `eval-gate` / `observability-overhead-windows-latest` / `collector-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `console-frontend` / `container-quality` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c5-ci-poll.log`（`ALL_TERMINAL sha=ba7efcd12f52f57fae73a44d6d15e9cf9714e4af`） |
| **补跑两树对照**（EC-05 条款①） | `ff7a979` | M0 [**36325875133**](https://github.com/Eswink/research-system-new/actions/runs/36325875133) / CodeQL [**36325875053**](https://github.com/Eswink/research-system-new/actions/runs/36325875053) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`）：逐 job `eval-gate` / `observability-overhead-ubuntu-latest` / `console-frontend` / `collector-quality` / `quality-windows-latest` / `container-quality` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c5bis-ci-poll.log`（`ALL_TERMINAL sha=ff7a97932a2209f1690aec1b7fdc0ef4685799e3`） |
| 收尾记录（台账 + 先后口径澄清） | `b741bf8` | M0 [**36328538591**](https://github.com/Eswink/research-system-new/actions/runs/36328538591) / CodeQL [**36328538220**](https://github.com/Eswink/research-system-new/actions/runs/36328538220) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`）：逐 job `container-quality` / `quality-windows-latest` / `quality-ubuntu-latest` / `console-frontend` / `collector-quality` / `observability-overhead-ubuntu-latest` / `eval-gate` / `observability-overhead-windows-latest` **全 `success`**；CodeQL **3/3 `success`**。轮询日志 `scratch/goal021-c5ter-ci-poll.log`（`ALL_TERMINAL sha=b741bf829b1af01bb8e2deb3bbf439e010814b85`） |
| 本条台账的**记录提交** | 本行所在的记录提交 | **依「固定口径」：写下某条记录的那个提交自身的 run 只在回合汇报记账**（不重复回写文件） | 见回合汇报 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | ACTIVE | **建档**：用户会话指令（goal 模式）授权对 GOAL-019 / 020 已落地的**写面认证**做**对抗性自检**——**只新增证明边界的判据**（并修被证明为真的缺陷），**不加新能力、不放宽任何判据、不改安全策略**。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA 专项实现、调用方自报身份、新增依赖、改既有判据 / 门禁 / 阈值、token 进任何地方、改 401 形态或 `Idempotency-Key` 语义、部署面验证。五 EC 设计（不可绕过 / 不泄漏 / 不可伪造 / 前端非访问控制 / 收口复检），budget = 20 / 120 / 2，`fix_policy` 与 `escalation_triggers` 承 GOAL-020 全套并**新增**：不得做 BOLA·BFLA 实现、不得把 token 写进**判据源码**、不得改 `test_record_face_is_covered_by_the_gate.py`。**建档时零产品代码改动**（只增本文件）。**建档当日实测六项事实**（见「目标与退出标准」）：①mutating 端点 **60 处**（两口径互证；任务书的「约 62 处、29 router」中 29 是**router 模块总数**，有 mutating 端点的 router 为 **17**）；②无 token **60/60 全 401**；③**认证先于路由**（未知路径 POST 得 401 而非 404）；④认证面 **AST 层面不继承** `_ANALYSIS_ACTIONS` 豁免；⑤`user_middleware` 顺序**认证在外层**；⑥401 body **不含** token。**最要紧的方法学修正**：**EC-03 的反证形态**——原拟「去掉 `finally: reset` ⇒ **并发**判据红」**实测不可证伪**（`asyncio.gather` 形态下 no-op reset 仍 **0 violations**，contextvar 按 Task 隔离）⇒ 改为**同一任务内顺序**形态（no-op reset 后读请求看到写请求的主体 = 污染 ⇒ **可判红**）；并据此确立本 GOAL 的执行纪律：**写「删掉 X ⇒ 判据红」之前必须先实测该反证真的会红**。**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`4558 passed / 21 skipped`、零 `FAILED`；日志 `scratch/goal021-c0-m0-final.log`）；首跑的 **12 条边界假红**确认为**调用侧错误**（`uv run` 才把 `.venv/Scripts` 放进 `PATH` ⇒ `lint-imports` 可解析），**非**产品缺陷。**建档提交 `8d36605` 的 CI = 八 job 全 success + CodeQL 3/3**（`run_attempt=1`）。 |
| 2026-09-27 | ACTIVE | **建档 cycle 0 完成**，进入循环：EC-01…EC-05 全 PENDING，下一 cycle 做 **EC-01**（认证不可绕过）。**本条记录提交**依「固定口径」其 CI run 只在回合汇报记账（见迭代日志末行）。 |
| 2026-09-27 | ACTIVE | cycle 1（PLAN-20260927-201）：**EC-01 = PASS**（认证不可绕过，四条全成立）。交付 = 新判据（274 行 / 18 例）+ `RECHECK-202`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-149`。**枚举来自代码**（两口径互证 **60**，覆盖 17 个 router）；**60/60 端点**无 token 与错 token **全 401**；**8 条分析类 POST** 无 token 全 401（豁免**结构 + 行为**双证不继承）；读面放行断言的是**机制**（分类）而非观察值。**按压 3/3 红**（3 / 4 / 10 failed，逐轮报实际判红集合），三轮逐字节复原（`ca03dac3…` + `IDENTICAL TO HEAD`），定向套件 **53 passed**，**既有判据零改动**。**零产品缺陷** ⇒ 该 EC 的判词是「**边界成立**」而非「已修复」。**如实更正任务书数字**：写面端点实测 **60 处**（任务书「约 62 处、29 router」中 29 是 router 模块总数、有写面端点的为 17）。**本轮被全量门抓到并修掉一处真红**（`python/typecheck`）：判据自身对 `TestClient.app` 的静态类型写法有误 ⇒ 收敛一处类型收窄；⇒ 再次实测「**定向套件绿 ≠ 全量门绿**」。**cycle 1 CI 到终态**：M0 `36304309642` 八 job 全 success + CodeQL `36304309147` 3/3（`run_attempt=1`）。 |
| 2026-09-27 | ACTIVE | cycle 2（PLAN-20260927-203）：**EC-02 = PASS**（token 不泄漏，六出口）。交付 = 新判据（312 行 / 12 例）+ `RECHECK-202`（`W-1`…`W-5`）+ `MEM-150`。**逐出口**判定（日志含**捕获装置自证**/ 遥测三档 / 401 两个点名文案 / 成功响应 / 事件 `actor` 是标识 / 记录面变量名在位）。**反证 1/1 红** + 逐字节复原（`ca03dac3…`）+ 既有判据**零改动** + 受影响套件 **745 passed**。**零产品缺陷**；修掉**判据自身** 1 处（记录面判据首版取任意文件）。**最要紧的诚实边界（`W-1`）**：脱敏是**形态匹配** ⇒ **裸不透明串**在**允许键内会原样导出**（已独立复现）⇒ 该风险由**上游纪律**兜底，**未收口**、如实保留。 |
| 2026-09-27 | ACTIVE | cycle 3（PLAN-20260927-205）：**EC-03 = PASS**（主体归因不可伪造）。交付 = 新判据（311 行 / 15 例）+ `RECHECK-20260927-206`（`W-1`…`W-5`）+ `MEM-20260927-151`。**自报不可生效**（头 / query / body 全无效）；**读面无主体**（连续 5 写、交替 4 轮、被拒写之后全部 `None`）；**`Principal` 字段集恰为 `{id, kind}`**（M18 边界为机械事实）。**本轮最要紧的发现**：首版判据用 `TestClient` ⇒ **按压不红**（该驱动每请求各起任务，遮住 `contextvar` 残留）⇒ 判据**不可证伪**；改走 **`ASGITransport` + 同任务 `await`** 后同一按压 **4 failed**，`sha256` 逐字节复原 ⇒ 15 passed。**这条把「判据自身恒真」从一个原则变成一个具体失效模式的实例**（`MEM-151`）。**零产品代码改动**。 |
| 2026-09-27 | ACTIVE | cycle 4（PLAN-20260927-207）：**EC-04 = PASS**（前端 token 面不是访问控制）。交付 = 新判据（163 行 / 6 例）+ `RECHECK-20260927-208`（`W-1`…`W-5`）+ 两处安全文档同源登记。**判定点只在后端**（绕过前端直调 API：无 token 401 / 有 token 201；中间件源码不含前端概念；被拒请求不改 canonical）。**反证 1/1 红**，其中**首版本 EC 判据按压不红**（只断言导出函数名、不绑定行为）⇒ **记为「按压打偏」并修正**（改为剥注释后扫代码）⇒ 修正后判红；逐字节复原（`32d7c4fc…`）。web 门 lint / typecheck 通过、unit 94 passed。**零产品代码改动**。⇒ 四个 EC 全部 PASS，**只剩 EC-05 收口复检**。 |
| 2026-09-27 | **ACHIEVED** | cycle 5（PLAN-20260927-209）：**EC-05 = PASS** ⇒ **五个 EC 全部达成**，GOAL 置 **ACHIEVED**。**独立复检 28/28**（六面：交付 / 按压 / 受保护判据零改动 / 残余 / 未覆盖范围 / 凭据）；按压面**独立重跑**：收窄保护面 ⇒ EC-01 判据 **exit=1**，复原 ⇒ **exit=0**，raw `sha256` **逐字节一致**。**as-is 本机 m0（记录写完之后）** = `PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24、4613 passed / 21 skipped、零 FAILED）。治理 `validate.py` 绿 + `DOCS-CHECK PASS`。**本轮修掉复检脚本自身 2 处缺陷**（文本模式读写 ⇒ 行尾变化；变量名落点断言写错），**非**产品缺陷 ⇒ **自检发现的真缺陷清单 = 空**。**残余全部原样保留**（本 GOAL 只做自检与登记）。**四条自检结论均为「边界成立」**，其中两条（③④）**各含一次「按压打偏」的如实登记**。**不得**据本 GOAL 宣称项目安全（`R-M1` 未收口）。 |
| 2026-09-27 | **ACHIEVED**（补跑后维持） | **补跑 EC-05 的显式条款「两树同结论」**：`git worktree add --detach ../goal021-clean-tree HEAD`（同 tip、独立目录）⇒ 同脚本 `--root` 跑两树（**共用主树解释器**，避免比两套环境）⇒ 各 **28 行判词全 PASS**、`diff` **IDENTICAL**、判词文件 **`sha256` 相同**（`5bb9bc08398eac789f9a07814b71b0586f7b1b34252a3c3cbb797efe119487f3`）；按压后**两树均干净**（干净 checkout `git status --short` 空 / 主树 `middleware.py` `git diff --numstat` 空）⇒ **逐字节复原在两树都成立**。**过程缺陷如实登记**：该路**首轮被静默跳过**（既未跑、也未在 RECHECK 的「未复核的面」里登记，却随 EC-05 一起记 PASS）⇒ 被完成核验判为**未达成**；本轮**补跑并留档**，并把该跳过记为**过程缺陷**（复检**范围登记不完整**，`RECHECK-210` 的 `W-0`），**非**产品缺陷。⇒ EC-05 的**每一路**（当前树 / 干净 checkout / 两树比对）现均有独立留档。 |
