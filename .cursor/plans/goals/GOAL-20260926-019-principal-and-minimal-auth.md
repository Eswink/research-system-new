---
id: GOAL-20260926-019
slug: principal-and-minimal-auth
title: 主体模型 + 最小认证面（写面认证 / 认证可关 / 请求主体落 canonical）
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-26 用户会话指令（goal 模式）：**建档 GOAL-019（主体模型 + 最小认证面：谁在调用）
    并授权本驱动自动化循环推进、无需逐轮确认**。授权 = 用户判词**「甲」**，
    **必须先落进本文件**。authorization 原文要点如下：
    (0) **建档方式二选一 = 新建 GOAL-019**（**不是**走「恢复条件②」变更 GOAL-018 的 budget
    并置回 ACTIVE）。理由：**「甲」是新范围**（新目标面），而 GOAL-018 已 ACHIEVED 且其
    取证要求是「`git diff` 中 `services/api/middleware.py` 与路由层**零改动**」——
    与「甲」直接冲突 ⇒ 必须在**新 GOAL** 下做，否则两轮授权互相顶替。
    来源同时包括 **push-to-main-for-CI 口径**（只推 `main`、**不 force**、**不重写历史**、
    **不推旁支**；push 前 `git pull --ff-only origin main`）+ **默认姿态不变**
    （默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）+ **默认门一律离线**。
    (1) **保护范围 = 只保护写面**：mutating 方法（`POST` / `PATCH` / `PUT` / `DELETE`）
    需要认证；**读面（GET/HEAD）默认放行**。理由（写进记录）：读面保护会牵动前端全部页面与
    live 夹具，改动面大得多；写面保护挡住最危险的操作（建项目、发 run、改配置、处置审批）。
    **已核实**：幂等中间件 `IdempotencyMiddleware` 已用
    `_MUTATING_METHODS = {POST, PATCH, PUT, DELETE}`（`services/api/middleware.py:23`）
    做同一分类 ⇒ **认证面复用同一分类，不新造第二套**。
    授权边界：**不得**给读面加认证；**不得**改读面放行语义。
    (2) **本地开发体验 = 认证可关**：认证 token **从环境变量读取、不落盘**；
    **环境变量留空 = 认证关闭，并在启动时打印显式警告**（说明「当前无认证，任何人可写」）；
    设了 token ⇒ 强制执行校验。**CI 与现有 live 夹具不受影响**（它们不设该变量）。
    理由（写进记录）：先让能力落地且默认不破坏既有链路；「默认必须有 token」属更强的口径，
    需要同时改 CI 与全部 live 夹具 ⇒ 若要做，**另行授权**。
    授权边界：**不得**把 token 写进任何文件 / CI / 记录 / 日志；**不得**改 CI 离线姿态。
    (3) **主体归因**：请求级主体（谁发起的这一次调用）必须**落 canonical** 并可读，
    替换今天硬编码的占位。**已核实**：`RunOrchestrationDependencies.default_actor: str =
    "system:orchestration"`（`packages/application/run_orchestration/dependencies.py:53`）
    是**硬编码常量**；`services/api/routers/approvals.py:124` 的 `actor="user:console"`
    同样硬编码 ⇒ 今天**没有真实主体**。
    授权边界：**`default_actor` 的改动必须向后兼容**（缺主体时的既有行为**逐字不变**，
    除非该路径已被认证覆盖）。
    (4) **明确不做（本 GOAL 边界，命中即 BLOCKED）**：多租户隔离、organization scope、
    RBAC、角色/权限矩阵、M18 的任何内容；**不**给读面加认证；**不**改 `Idempotency-Key`
    语义；**不**把 token 写进任何文件/CI/记录/日志；**不**新增依赖（token 校验用标准库：
    `hmac.compare_digest` 做常数时间比较，**不得**用 `==` 直接比）；
    **不做** D-12 的 (a) 面（BOLA / BFLA 专项测试与门）。
    (5) **授权实施范围**：本 GOAL 是**唯一**获授权改动**鉴权 / 中间件 / 路由保护**的轮次
    （GOAL-018 的 (6)c 明文把「甲」留给下一轮）。授权动作面 =
    ①`Principal` 域值对象（主体 id + 类型）；②mutating 端点 token 保护（复用
    `_MUTATING_METHODS` 同一分类）；③请求级主体归因落 canonical 并在读面可见；
    ④四处文档与威胁模型同源更新；⑤收口复检 + 残余登记。
    (6) **不做真实出网**：本 GOAL **不需要** `.env` 凭据。若确需校验 URL，仅允许 http/https
    且**发请求前校验 host**并拒绝 localhost / 环回 / 私有 / 保留地址（**复用**
    `endpoint_policy`，不另写判据）；SQL 一律**参数绑定**；凭据**只从环境变量**读取；
    Domain **不得**出现厂商名；观测隐私**不记录完整 Prompt、不记录 token**（§10）。
    (7) **边界**：GOAL-001…018 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-018 的**全部 13 项 `D-NN` 终态表**
    与承继残余**原样承继**（本 GOAL 只把「甲」从「未授权」推进为「有实现」，
    其余继续挂着）。
    (8) **不做真实付费 LLM 调用**；默认 runtime 仍为 **Fake**、默认 CI 仍**离线**。
objective: >
    建立**主体模型与最小认证面**——把「谁在调用」这一层从**完全没有**变成**有实现且可验收**，
    并且**不碰多租户**：(1) **主体模型**：`Principal` 域值对象（**主体 id + 类型**；
    **不含**租户 / 角色字段——那属 M18，本 GOAL 明文不做）+ **请求级主体归因**：
    mutating 请求经认证后，真实主体**落 canonical**（`outbox_events.envelope_json` 的
    `actor`；读面 `GET /runs/{id}/events`）并在读面可见，**替换**今天的硬编码占位
    （`default_actor = "system:orchestration"` / `actor="user:console"`）；
    **反证**：不带 token 的写请求 ⇒ 被拒；带 token ⇒ 主体是**请求带的那个**。
    **向后兼容**：无认证时既有行为与基线**逐字一致**（对照判据，不靠「测试没红」推定）。
    (2) **认证面**：mutating 端点受 token 保护（**复用** `_MUTATING_METHODS` **同一分类**，
    不新造第二套）；token **从环境变量读取**、**常数时间比较**（`hmac.compare_digest`）、
    **不落盘、不进日志 / 事件 / 遥测**；**读面放行**；`/health` 探活端点**排除**
    （否则探活会红）。**三态各有实跑证据**：未设 token ⇒ 认证关闭 + **启动显式警告**
    （写面放行）；设了 token + 不带 / 带错 ⇒ 401/403 且**点名**；设了 token + 带对 ⇒ 放行。
    **反证成对（先红后绿）**：去掉校验 ⇒ 带错 token 也放行（判据红）。
    (3) **既有链路零回归**：前端全部页面、stub e2e、live e2e、worker gateway、
    全部现有测试套件在**未设 token**（= 认证关闭）下行为与基线**逐字节一致**；
    **`Idempotency-Key` 语义一字不动**（`git diff` 取证该中间件未被改）。
    (4) **文档与威胁模型同源**：`docs/security/IDENTITY_AND_ACCESS.md` 与
    `docs/security/THREAT_MODEL.md` 的授权面章节从「未覆盖」更新为
    「**已覆盖写面认证，未覆盖读面与多租户**」，并写明**边界与未覆盖范围**；
    `docs/api/CONTROL_PLANE_API.md` 同步认证口径；`docs/integration/LIVE_MODEL_RUNBOOK.md`
    补充「如何设 token / 如何关认证（含警告）/ 如何在 CI 保持关闭」。
    (5) **收口复检 + 残余登记**：独立复检脚本（当前树 + 干净 checkout 同结论）+
    **as-is 本机 m0 到 23/23** + 治理 validate 绿 + CI 台账到终态
    （M0 八 job + CodeQL，含 `run_attempt`）+ 承继残余逐条在位。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**零**策略面 allow 新增；
    **零**新依赖；**不得宣称项目安全**（`R-M1` 仍在）；**不做** D-12 的 (a) 面。
exit_criteria:
  - id: EC-01
    criterion: >-
      **主体模型 + 请求级主体归因落 canonical**：①`Principal` **域值对象**在位
      （**主体 id + 类型**两要素；**不含**租户 / 角色 / 权限矩阵字段——那属 M18，
      本 EC 明文不做，判据须能证明这些字段**不存在**）；
      ②mutating 请求经认证后，**真实主体落 canonical**（`outbox_events.envelope_json`
      的 `actor` 字段）并在**读面可见**（`GET /runs/{id}/events` 的 `actor`），
      **替换**今天的硬编码占位；③**至少一个真实用例**（建项目 / 发 run / 处置审批
      **之一**）产出的 canonical 事实里，主体是**请求带的那个**，不再是
      `system:orchestration` / `user:console`。
      **反证（成对）**：不带 token 的写请求 ⇒ **被拒**（且非 2xx）；带 token ⇒ 主体正确。
      **向后兼容（本 EC 的硬判据）**：`default_actor` 的改动必须**向后兼容**——
      **无认证时既有行为与基线逐字一致**，判据须含**显式对照**（不是靠「测试没红」推定）。
    verify: >-
      ① `Principal` 值对象在位且有**域层**单元测试（构造 / 校验 / 不含租户与角色字段的
      **反证断言**）；② 一条**端到端实跑**：设 token → 发一个 mutating 请求 →
      读 canonical（`outbox_events` 的 `envelope_json.actor`，或 PG 路径等价实查）⇒
      值 **== 请求带的那个主体**；③ **配对反证**：同一请求**不带** token ⇒ 被拒、
      且 canonical 里**不留**该主体（不能「拒了但写了」）；
      ④ **向后兼容对照**：认证关闭时，同一路径产出的 `actor` 与基线**逐字相同**
      （对照证据须是**实测取值**，不是「套件绿」）；⑤ 取证用 `git diff` 说明
      `default_actor` 的**缺省值语义未被改**（或改了则以对照证明等价）。
    status: PASS
  - id: EC-02
    criterion: >-
      **认证面（写面 token 保护，三态 + 凭据纪律）**：mutating 端点受 token 保护，
      **复用** `_MUTATING_METHODS`（`services/api/middleware.py:23`）**同一分类**——
      **不新造第二套方法集合**（判据须证明分类唯一）；token **从环境变量读取**、
      **常数时间比较**（`hmac.compare_digest`）、**不落盘 / 不进日志 / 事件 / 遥测**；
      **读面（GET/HEAD）放行**；**探活端点排除**（`/health`，否则探活会红）。
      **三态各有实跑证据**：**(甲)** 未设 token ⇒ **认证关闭** + **启动显式警告**
      （警告文案必须**明确说「无认证」**，不得让读者误以为已认证）+ 写面放行；
      **(乙)** 设了 token + **不带 / 带错** ⇒ **401 或 403 且点名**（点名 = 响应体指明
      缺 / 错在何处，不是空体）；**(丙)** 设了 token + **带对** ⇒ 放行。
      **反证成对（先红后绿）**：临时**去掉校验** ⇒ 带错 token 也放行 ⇒ 判据**红**；
      逐字节复原 ⇒ **绿**。
      **凭据纪律**：token **值**不得出现在任何 tracked 文件、记录、日志、遥测、测试输出里
      （含 `AGENTS §10` 观测隐私面）——**grep 反证**。
    verify: >-
      ① **分类唯一性**：认证面引用的是**同一个** `_MUTATING_METHODS` 符号
      （或等价地证明二者同源）；② **三态实跑**各留档：启动日志（含警告原文）、
      401/403 响应体（含点名文本）、带对 token 的 2xx；
      ③ **读面反证**：至少一条 `GET`（含 `/health`）在**设了 token 但请求不带 token**时
      仍**放行** ⇒ 证明保护范围**只有写面**；④ **常数时间**：比较走 `hmac.compare_digest`
      （`==` 直接比 token ⇒ 判据红）；⑤ **凭据纪律 grep 反证**：仓库内（排除 `.git`）
      搜 token **字面值** ⇒ **零命中**（token 值只在运行进程的环境变量里）；
      日志 / 事件 / 遥测面同样零命中；⑥ **反证成对**：去掉校验 ⇒ 带错 token 放行 ⇒ 红；
      逐字节复原 ⇒ 绿。
    status: PASS
  - id: EC-03
    criterion: >-
      **既有链路零回归（认证关闭 = 基线）**：前端全部页面、stub e2e、live e2e、
      worker gateway、**全部现有测试套件**在**未设 token**（= 认证关闭）下
      **行为与基线逐字节一致**。判据 = 受影响套件全绿 **+ 一条显式的「认证关闭时行为不变」
      对照**（**不是**靠「测试没红」推定）；**`Idempotency-Key` 语义一字不动**
      （`git diff` 取证该中间件未被改）。
      **撤回纪律（本 EC 专属）**：认证中间件会改变 **401/403 的响应形态**，
      而既有测试可能拿它当夹具 ⇒ 改共享中间件前**先数清谁拿它的失败形态当夹具**；
      若 CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**。
    verify: >-
      ① **对照判据**：认证关闭时，取一组**基线可比的实测值**
      （如既有夹具产出的 `actor`、幂等 replay 的响应体 / 状态码、`GET /health` 的组成摘要）
      与改动前**逐字比较**，输出「相同」；② 受影响套件逐条实跑并留档：
      `tests/api` / `tests/contracts`（含 **OpenAPI 快照**）/ `tests/e2e`（stub + live）/
      `tests/worker` + `tests/architecture/python`（含 runbook 同源族）+ web 六门
      （lint / typecheck / unit / build / stub e2e / live e2e）；③ **`Idempotency-Key`
      取证**：`git diff` 显示 `IdempotencyMiddleware.dispatch` 的
      **方法分类与 replay / conflict / record 语义零改动**（只允许「新增另一个中间件」
      这类加性变化，且须逐字节证明原有代码块未变）；④ **快照类门禁**：
      OpenAPI 快照若漂移 ⇒ **按既有流程重生成**（`tools/gen_openapi.py`）并说明原因，
      **不得**手改快照使其通过。
    status: PASS
  - id: EC-04
    criterion: >-
      **文档与威胁模型同源（零夸大）**：四处文档同源更新——
      ①`docs/security/IDENTITY_AND_ACCESS.md`：授权面从「未覆盖」更新为
      **已覆盖写面认证、未覆盖读面与多租户**，并写明**边界与未覆盖范围**；
      ②`docs/security/THREAT_MODEL.md`：其**第 6 节**（D-12(b) 草案）的实况**据实更新**
      （原 6.2 第 2 条「控制面无调用方认证」已成**历史事实**），并**保留 / 更新**
      **「未覆盖范围」节**；
      ③`docs/api/CONTROL_PLANE_API.md`：同步认证口径（写面需 token、读面放行、
      认证可关及其警告）；
      ④`docs/integration/LIVE_MODEL_RUNBOOK.md`：补充「**如何设 token / 如何关认证
      （含警告）/ 如何在 CI 保持关闭**」。
      判据 = **四处文档同源** + **结构判据（含「未覆盖范围」节）** + **零夸大**：
      **不得**宣称「项目安全」「授权面已覆盖」或任何形式的安全结论；
      **必须**明文写出**未覆盖范围**（读面 / 多租户 / BOLA-BFLA 的 (a) 面）。
    verify: >-
      ① 四处文档逐处实查：口径**同词**（写面已认证 / 读面未认证 / 多租户未做）；
      ② **结构判据在树内**（新增测试或扩既有测试）且**可被按压**：删「未覆盖范围」节 ⇒
      **红**；把某处改成「已覆盖全部授权面」⇒ **红**；逐字节复原 ⇒ **绿**；
      ③ **同源机器判据**：`docs/integration/LIVE_MODEL_RUNBOOK.md` 的
      **环境变量名**必须真实存在于代码（**既有**判据
      `tests/architecture/python/test_runbook_same_source.py:166` 自动覆盖此面）⇒
      该套件绿；④ **零夸大反证**：全仓搜「项目安全」类断言句子 ⇒ 只允许出现在
      **否定 / 边界声明**语境（如「**不得**宣称项目安全」）；⑤ `docs/INDEX.md`
      若有登记要求 ⇒ 按既有判据满足（runbook 已有条目行判据）。
    status: PENDING
  - id: EC-05
    criterion: >-
      **收口复检 + 残余登记**：① **独立复检脚本**（不复用本 GOAL 的叙述）在**当前树**与
      **干净 checkout** 两路给出**同一结论**，且**非恒真**（按压必须判红）；
      ② **as-is 本机 m0 到 23/23**（终态行
      `PASS: profile=m0; 23 deterministic checks`；若不能 ⇒ **如实说明哪种跑法与哪条拦着**，
      不得含糊）；③ 治理 `.cursor/skills/governance-check/scripts/validate.py` **绿**；
      ④ **CI 台账到终态**（M0 **八 job** + CodeQL，含 `run_attempt`）；
      ⑤ 承继残余**逐条在位**：`R-M1`（**不得宣称项目安全**）/ `R-D1`
      （`undici` 归属上游、`yaml` 已升）/ `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6`；**D-12 的 (a) 面**（BOLA/BFLA 专项测试）**本轮仍不做**，
      如实保留（本 GOAL 只把 (b) 草案推进到「**有实现**」，**不等于** (a)）。
    verify: >-
      ① 复检脚本两路输出留档（`scratch/`）且**判词列逐行相同**；整份输出差异只允许出现在
      「本 GOAL 自身的 EC 状态文字」上（干净 checkout 停在更早的提交）；
      ② `make validate-all`（独占、仓库 `.venv`、`--keep-going`）终态行
      `PASS: profile=m0; 23 deterministic checks`，日志留档；
      ③ `validate.py` 输出 `Cursor 治理验证通过`（含 `DOCS-CHECK`）；
      ④ 台账逐 run 逐 job 记录（含 `run_attempt`；flake 判定**必须**靠**同一代码的复跑对照**）；
      ⑤ 残余清单在本文件**逐条**出现且措辞与判词一致；⑥ **未覆盖范围**逐条明写：
      **读面未认证** / **多租户未做** / **D-12(a) 未做** / `R-M1` 未收口。
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
      **给读面（GET/HEAD）加认证**，或改动读面放行语义（本 GOAL 的保护范围只有写面）
    - >-
      引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容
      （含给 `Principal` 加租户 / 角色字段）
    - >-
      新增**任何**依赖（token 校验必须用标准库 `hmac.compare_digest`；引入
      `passlib` / `jose` / `authlib` 等一律禁止）
    - >-
      把 token **值**写进任何 tracked 文件 / CI / 记录 / 日志 / 遥测 / 测试输出
      （含 `.env.example`、workflow、夹具、文档示例）
    - >-
      用 `==`（或 `!=`）直接比较 token（必须常数时间 `hmac.compare_digest`）
    - >-
      改 `Idempotency-Key` 语义，或改 `IdempotencyMiddleware` 的
      方法分类 / replay / conflict / record 行为
    - >-
      改门禁或阈值（`validate_bundle` 检查项、m0 任一 check、`.github/workflows/**`
      的 job 结构、`test_m2_audit.py` 镜像判据）
    - >-
      宣称「项目安全」「授权面已覆盖」或任何形式的安全结论（`R-M1` 未收口）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    **给读面加认证** —— **立即 BLOCKED**（用户判词 (i)：保护范围**只有写面**）
  - >-
    **引入多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容 ——
    **立即 BLOCKED**（用户判词 (4) 明确不做清单）
  - >-
    **新增依赖**（token 校验必须用标准库；`hmac.compare_digest` 之外的方案）——
    **立即 BLOCKED**
  - >-
    **把 token 写进 CI 或任何文件**（含记录 / 日志 / 遥测 / 夹具 / 示例）——
    **立即 BLOCKED**；明文凭据泄露（即使是可弃用的免费额度）⇒ 立即停止并报告
  - >-
    **改 `Idempotency-Key` 语义**（含 `IdempotencyMiddleware` 的方法分类 /
    replay / conflict / record 行为）—— **立即 BLOCKED**
  - >-
    **改门禁 / 阈值 / 作业结构**（`validate_bundle` 检查项、m0 任一 check、
    `.github/workflows/**` 的 job 结构、`test_m2_audit.py` 镜像判据）—— **立即 BLOCKED**
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
  - .cursor/plans/tasks/PLAN-20260926-190-principal-model-and-write-face-auth.md
  - .cursor/plans/tasks/PLAN-20260926-192-auth-surface-four-doc-same-source.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-193-auth-surface-four-doc-same-source-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-143-auth-face-reuses-the-one-classification.md
  - .cursor/memory/entries/MEM-20260926-144-same-source-docs-need-a-pressable-declaration.md
---

## 目标与退出标准

**一句话**：把「**谁在调用**」这一层从**完全没有**变成**有实现且可验收**——**主体模型**
（`Principal` 域值对象 + 请求级主体归因落 canonical）+ **最小认证面**（**只保护写面**、
**认证可关**且关时**显式警告**、**常数时间比较**、**不落盘**）——并且 **不碰多租户**、
**不给读面加认证**、**零新依赖**、**不得宣称项目安全**。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **主体模型 + 请求主体落 canonical**（替换硬编码占位；向后兼容对照） | `Principal` 值对象 + 端到端实跑 + 配对反证 + 对照判据 | **PASS** |
| EC-02 | **认证面**（写面 token 保护，三态实跑 + 凭据纪律 grep 反证） | 中间件 + 启动警告 + 401/403 点名 + 读面反证 | **PASS** |
| EC-03 | **既有链路零回归**（认证关闭 = 基线**逐字**一致） | 全门实跑 + 显式对照 + `Idempotency-Key` 零改动取证 | **PASS** |
| EC-04 | **四处文档 + 威胁模型同源**（含「未覆盖范围」节，**零夸大**） | 四文档更新 + 可按压结构判据 + 同源机器判据 | **PASS** |
| EC-05 | 收口复检 + 残余登记 | 两树复检 + as-is m0 **23/23** + CI 台账 + 残余逐条 | **PENDING** |

**依赖关系**：EC-01 与 EC-02 是**同一层**的两半（主体模型 / 认证面），EC-02 落在
HTTP 边界、EC-01 落在 canonical 与读面；**EC-03 必须在 EC-01 与 EC-02 落地后**做
（它判的就是这两者**没有**改变离线基线行为）；EC-04 依赖 EC-01 / EC-02 的**最终形态**
（文档要写实况，不能写意图）；EC-05 **最后**做。

**建档当日已核实的文件层事实（决定可行性与判据形态；全部实测，非推测）**：

1. **写面的真实规模（实测，本机仓库 `.venv`）**：控制面路由表 =
   **29 个定义 `APIRouter` 的 router 文件** / **123 条路由** / **60 条 mutating**
   （`POST` 41 / `PATCH` 9 / `DELETE` 8 / `PUT` 2）；另有 `create_app()` 直接在 app 上
   注册的 `GET /health` ⇒ **124 条路由**，与 `docs/security/THREAT_MODEL.md` §6.2 第 1 条
   「124 条路由」**对上**。实测命令（可复现；按 `route.methods` 的交集计数）：
   `importlib` 遍历 `services.api.routers` 下每个模块的 `APIRouter`，统计
   `methods & {"POST","PATCH","PUT","DELETE"}`。**注意**：建模档写「约 62 处」是**约数**，
   本 GOAL 一律以**实测 60**（+`/health` 不计入写面）为准，判据不得引用约数。
2. **分类面唯一（实测）**：`_MUTATING_METHODS = frozenset({"POST","PATCH","PUT","DELETE"})`
   在 `services/api/middleware.py:23`，由 `IdempotencyMiddleware.dispatch` 消费
   （`:47` 方法过滤、`:49` 分析类 POST 例外、`:53` 强制 `Idempotency-Key`）。
   ⇒ **认证面复用同一符号**，不新造第二套；`_ANALYSIS_ACTIONS`（`:27`）是**幂等**面的
   例外（分析类 POST 不要 `Idempotency-Key`），**不**自动等于「认证面的例外」——
   两者是否对齐必须在子 PLAN 里**显式决定并留证**（本 GOAL 不预设它对齐）。
3. **主体占位的两处硬编码（实测）**：
   - `packages/application/run_orchestration/dependencies.py:53`
     `default_actor: str = "system:orchestration"`；消费点 = 同一包的
     `service.py:89` `self._event_sink = EventSink(deps.events, deps.default_actor)`。
   - `services/api/routers/approvals.py:124`
     `event = build_approval_event(decided, actor="user:console")`。
4. **产品代码里全部硬编码 actor 字面量（实测，共 6 处）**：
   `adapters/sqlite/outbox.py:38` 与 `adapters/postgres/outbox.py:43`
   （`actor="system:workflow-engine"`）、`services/api/routers/tool_packs.py:50`
   （`actor="console"`）、`services/api/routers/policy.py:75`
   （`actor="system:policy-view"`）、`services/api/routers/approvals.py:124`
   （`actor="user:console"`）、`packages/application/m12_reference/clean_run_stages.py:113`
   （`actor="system:m12"`）。⇒ **哪些属「请求级主体」（该被替换）、哪些是「系统自身动作」
   （本就该是常量）** 必须在子 PLAN 里**逐条判定并留证**；**不得**一律替换。
5. **canonical 的落点与读面（实测）**：事件经 `EventEnvelope.actor`
   （`packages/domain/events.py:78`，字段**必填**、空值构造即 `ValueError`，
   `:94`）写入 outbox；PG 侧表 `outbox_events(event_id, envelope_json JSONB, created_at,
   published_at)`（`adapters/postgres/migrations/001_initial.sql:37`）——
   **actor 在 `envelope_json` 里，没有独立列**；`approvals` 表在
   `002_domain_state.sql:76`。读面 = `services/api/routers/run_events.py:42`
   （`"actor": envelope.actor`）。⇒ 「落 canonical 并可读」的**可验收形态** =
   **查 `outbox_events.envelope_json.actor`（或 SQLite 等价物）与读面输出**。
6. **仓库里唯一有认证的面 = worker 网关，且有可直接复用的原语（实测）**：
   `services/api/worker_gateway/auth.py`：`verify_enrollment` 用
   `hmac.compare_digest`（`:31`，且**空值永不匹配**）、`extract_bearer`
   （`Authorization: Bearer <t>`，`:38`）、`generate_session_token` /
   `hash_session_token`（256-bit；**只存 sha256**，`:21`/`:26`）；
   `assert_bind_allowed` 非 loopback 无 TLS 拒绝启动（`:58`）。另有
   `services/api/worker_gateway/security.py:31` 的 enrollment 常量时间比较。
   ⇒ 本 GOAL 的 token 校验**必须复用同一比较原语 / 同一纪律**，不另立规矩。
7. **控制面今天没有任何 401/403 断言（实测 + 文档一致）**：
   `docs/security/THREAT_MODEL.md` §6.5 明写「今天树上**没有**任何控制面 401/403 断言
   （现有 401 断言全在 worker 网关测试里）」；实测本仓 401/403 相关命中集中在
   `tests/api/test_worker_gateway*.py` / `tests/distributed/`，控制面 DTO 面的
   `api_key` 是**出站**凭据面。⇒ **授权失败的响应语义**（401 还是 403、是否泄露对象
   存在性）今天**未定**，本 GOAL 必须**先定语义再写判据**（§6.5 已点名这是前置）。
8. **`tests/api/console_api_app.py:390` 硬编码 `EventSink(deps.events,
   "system:orchestration")`**（实测）——这是**既有夹具**在「认证关闭」路径上直接构造的
   sink；EC-03 的「逐字一致」对照**必须覆盖它**（它就是「无认证时行为不变」的现成证据面）。
9. **runbook 有既存同源机器判据（实测）**：
   `tests/architecture/python/test_runbook_same_source.py` 强制
   ①五个小节标题（`REQUIRED_SECTIONS`，`:47`）；②**反引号里的环境变量名式 token 必须真实
   存在于代码**（`_ENV_TOKEN` + `_missing_env_tokens`，`:105`/`:166`）；
   ③引用的仓库路径 / pytest 目标 / `Fake*` 符号必须存在；④`docs/INDEX.md` 必须有
   **条目行** `- \`integration/LIVE_MODEL_RUNBOOK.md\``。
   ⇒ EC-04 往 runbook 加「如何设 token」时，**新环境变量名必须同时出现在代码里**
   （本 GOAL 满足：读环境变量的代码就是它的存在性），且**不得**破坏上述五节。
   另有 `test_live_credential_lifecycle_same_source.py`（runbook §8 固定标签表：
   注入 / 轮换 / 撤销 / 可弃用额度）与 `test_live_switch_is_single_source.py` /
   `test_live_failure_paths_same_source.py` / `test_live_drift_sample_same_source.py`
   一族 ⇒ **runbook 改动必须同时过这一族**。
10. **`docs/api/CONTROL_PLANE_API.md` 有既存判据在读它（实测）**：
    `tests/contracts/test_dispatch_ownership_weak_equivalence.py:37`
    （`_DOCS = ("docs/architecture/PORTS.md", "docs/api/CONTROL_PLANE_API.md")`，
    要求某些**上限值只在 port 常量里写一次**）+ `tests/tooling/test_toolpack_capability_policy_pending.py:64`。
    ⇒ 往 CONTROL_PLANE_API.md 加认证口径时**不得**顺手写入数字 / 上限（否则可能撞上
    「值只写一次」判据）。
11. **`docs/security/IDENTITY_AND_ACCESS.md` 今天没有任何测试引用它（实测）**⇒
    EC-04 的「结构判据（含『未覆盖范围』节）」**必须新建**（或扩展既有测试），
    不能假定已有门在管它。该文档现有一节 `## Worker Identity (M16)` 已经是
    「**只有 worker 面有认证**」的书面证据 ⇒ 更新时**必须**与该节口径一致。
12. **OpenAPI 快照链路（实测）**：`tools/gen_openapi.py` 生成
    `docs/api/openapi.m13.json`，由 `tests/contracts/test_openapi_snapshot.py`
    校验（先取已提交字节、再重生成，比较两者）。**纯中间件式认证不新增路径** ⇒
    快照**理论上不动**；但若给路由加 `responses={401: ...}` / `securitySchemes`，
    快照**会漂移** ⇒ **必须按既有流程重生成**，**不得**手改快照使其通过。
13. **两个插入点（实测）**：`services/api/app.py` 的 `create_app()` 里
    `app.add_middleware(IdempotencyMiddleware)`（`:277` 附近；中间件顺序语义要看清）+
    `_register_health_route(app, resolved, version)`（**探活端点排除点**）。
14. **规模门禁的零余量文件（实测，`tests/tooling/test_python_source_limits.py`：
    450 行 / 50 行函数；覆盖面 = `apps`/`services`/`packages`/`adapters`/`tests`）**：
    **`services/api/composition.py` = 450 行（零余量）**、
    **`packages/application/run_orchestration/service.py` = 450 行（零余量）**、
    `adapters/postgres/workflow_engine.py` / `adapters/execution/docker_backend.py`
    同为 450 行；`tests/e2e/live_run_support.py` 只剩 **1 行**余量（`W-6`）。
    **这两条零余量文件正好压在 EC-01 的缝上**（`composition.py:307` 构造
    `OrchestrationDependencies`；`service.py:89` 消费 `default_actor`）⇒
    **改动它们必须先搬代码**；本 GOAL 的**首选形态**是**新建模块**承载主体解析，
    让这两个文件**零改动**（是否可行由子 PLAN 判定并留证）。
    相关文件的**实测余量**：`services/api/app.py` 307（143 行余量）/
    `middleware.py` 101 / `settings.py` 150 / `approvals.py`(router) 403 /
    `dependencies.py` 56 / `eventing.py` 86 / `tests/api/console_api_app.py` 427（23 行余量）。
15. **配置面命名与范式（实测）**：环境变量一律 `RESEARCHOS_*`；`ApiSettings.from_env()`
    是既有入口（`services/api/settings.py:118`），布尔开关的既有范式 =
    `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` / `RESEARCHOS_WORKSPACE_ALLOW_HOST_SHELL`
    的 `("1","true","yes","on")` 判定；凭据类既有命名 =
    `RESEARCHOS_WORKER_ENROLLMENT_SECRET`（`.env.example:21`，**只是名字**，
    值不入仓库）。⇒ 本 GOAL 的 token 变量名**沿用 `RESEARCHOS_*`**，
    **只登记名字、绝不留值**（`.env.example` 也**不加**——避免任何「值 / 占位值」落盘）。
16. **号码续接（实测）**：`.cursor/plans/tasks/` 最大 = `PLAN-20260926-188`、
    `.cursor/plans/rechecks/` 最大 = `RECHECK-20260926-189`（PLAN / RECHECK **共用**全局
    NNN 序列）⇒ 下一个 PLAN = **190**、下一个 RECHECK = **191**；
    `.cursor/memory/entries/` 最大 = `MEM-20260926-142` ⇒ 下一个 MEM = **143**。
17. **承继起点（事实，不是待办）**：GOAL-018 的 **13 项 `D-NN` 已全部结清**
    （已实施 9 + 部分实施 1 + 已拍板为维持现状 3、**未授权待拍板 0**）；
    本 GOAL **不重开任何一项**，只把「**甲**」从「未授权」推进为「**有实现**」。
    ☆ **`THREAT_MODEL.md` §6.5 已点名**：(a) 面的**前置**是「**必须先有主体模型**——
    没有 principal 就没有『越权』可言；这一步**不能**靠加测试解决」⇒
    本 GOAL 交付的正是**那个前置**，**不**等于 (a)。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 默认门一律离线**（不需要 `.env` 凭据；`pnpm` 网络仅用于既有的 web 门）。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-019-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-019**」（**不是**复活 GOAL-018），
理由见 frontmatter `authorization.ref` 第 (0) 条。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260926-019`
  并投影 `ALL_PLAN`，**同一提交**）。子 PLAN 编号续**全局 NNN**（建档当日实测：
  下一个 PLAN = **190**；RECHECK = **191**；MEM = **143**，见「目标与退出标准」第 16 条）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查**规模门禁**（50 行函数 / 450 行文件；覆盖面 =
  `apps` / `services` / `packages` / `adapters` / `tests`；**`services/api/composition.py`
  与 `packages/application/run_orchestration/service.py` 正好 450 行零余量**，
  且**正好压在 EC-01 的缝上**，见「目标与退出标准」第 14 条）与**快照类门禁**
  （**OpenAPI 快照**——中间件式认证原则上不漂移，但一旦加 `responses` / `securitySchemes`
  就必须按既有流程重生成；**设计基线**），再跑 `make validate-all`（m0 全量 23 项，
  **独占运行**，**用仓库 `.venv`**）+ 受影响定向套件 + **web 门**
  （`pnpm --dir apps/web` 的 lint / typecheck / test / build / test:e2e / test:e2e:live
  + 根 `pnpm run check`）。
  **默认门一律离线**（`tests/egress_guard.py` 是结构判据——**不得**为本地变绿而放宽它）；
  **本地不绿不得 push**（承 `MEM-20260924-125`）。
  **写记录时不要跑 m0**（承 `W-5`：m0 运行中改工作树会让 `framework/validate` 判红）。
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

**撤回纪律**（**本轮尤其要紧**，承 GOAL-011…018）：改共享夹具 / 中间件 / 契约时先数清谁拿它的
**失败形态**当夹具。本 GOAL 有**三处高危面**：
① **认证中间件会改变 401/403 的响应形态**，而既有测试可能拿它当夹具 ⇒
改动前先**静态清点**「谁断言 401/403 / 谁断言 `Idempotency-Key` 的 422 / 谁断言
`GET /health`」；② **`tests/api/console_api_app.py:390`** 直接构造
`EventSink(..., "system:orchestration")` ⇒ 主体解析若改了 `EventSink` 的构造契约，
它会**当场变红**（这是「无认证时逐字一致」的探针，**不是**待改的陈旧夹具）；
③ **runbook 同源族**（第 9 条）以**文本存在性**断言，改 runbook 结构即可能同时打到它们。
CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| **认证面把既有夹具打红**（本 GOAL 主场） | `tests/api` 出现新 401/403/422；`console_api_app` 变红 | 判「是**载体改动**改变了失败形态」还是「夹具陈旧」：**前者 ⇒ 优先撤回载体改动**（承 GOAL-011…018）；**不得**改断言迁就 |
| **主体归因把 canonical 断言打红**（EC-01 主场） | outbox / 事件 `actor` 断言失败 | 判「该路径是否**已**被认证覆盖」：**是** ⇒ 新主体正确、改的是**预期**并留证；**否** ⇒ 必须**逐字保持**基线（`system:orchestration`） |
| **OpenAPI 快照漂移**（EC-03 主场） | `test_openapi_snapshot.py` 判红 | **按既有流程重生成**（`tools/gen_openapi.py`）+ 说明漂移来源；**不得**手改快照 |
| **runbook / 文档同源判据**（EC-04 主场） | `test_runbook_same_source.py` / `test_live_*_same_source.py` 判红 | 判「是文档要写实况」还是「引用了不存在的符号」：**引用了不存在的** ⇒ 改文档；**不得**放宽判据 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`W-7` live 上游瞬时） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 归因；**资源阈值型**判红 ⇒ **(ii) 类 + 复跑对照**，**判据与阈值一字不动** |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态 + **未覆盖范围逐条明写**（读面未认证 / 多租户未做 / D-12(a) 未做 /
  `R-M1` 未收口）。**未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **新增依赖**、**把 token 写进任何地方**、**改 `Idempotency-Key` 语义**、
  **改门禁 / 阈值 / 作业结构**、**放宽 §9 默认 deny**、**宣称项目安全**、
  **Canonical State 边界**）、同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、
  或连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，
  **留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。
- **本 GOAL 的收口判词必须写明**：**as-is 本机 m0 的终态行**（应为 **23/23**；
  若未达 ⇒ 如实登记**是哪一条**拦着、**哪种跑法**）、**认证三态的实跑证据**
  （关闭 / 拒绝 / 放行）、**主体是否真的落 canonical**（含取值）、
  **未覆盖范围**（读面 / 多租户 / D-12(a)），以及 **`Idempotency-Key` 是否一字未动**。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`.cursor/plans/goals/GOAL-20260926-018-residual-closeout-and-decision-register.md`
的「不进入循环 / 需人工拍板」节 + `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**（`D-01` / `D-02` / `D-07` / `D-08` / `D-09` / `D-10` / `D-11` / `D-12` / `D-13`）、
**部分实施 1 项**（`D-03`：`vite` 已升 + `yaml` 已升到 `2.8.4`；`undici` 已调研未升）、
**已拍板为维持现状 3 项**（`D-04` / `D-05` / `D-06`）、**未授权待拍板 0 项**。
⇒ 本 GOAL **不重开任何一项**，只把「**甲**」从 **D-12 的 (b) 草案**推进到「**有实现**」。

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

1. **多租户隔离 / organization scope**——**不做**（M18）；
2. **RBAC / 角色 / 权限矩阵**——**不做**；
3. **M18 的任何内容**——**不做**（`MILESTONES.md` 的 M18 状态 `DEFERRED` 不变，
   **不得**标记部分完成）；
4. **给读面（GET/HEAD）加认证**——**不做**（用户判词 (i)：保护范围**只有写面**）；
5. **改 `Idempotency-Key` 语义**——**不做**（判据：`git diff` 取证该中间件未被改）；
6. **把 token 写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出**——**不做**
   （只登记**变量名**，**绝不留值**；`.env.example` 也不加）；
7. **新增依赖**——**不做**（token 校验**必须**用标准库
   `hmac.compare_digest`；**不得**用 `==` 直接比）；
8. **D-12 的 (a) 面（BOLA / BFLA 专项测试与门）**——**本轮仍不做**，**如实保留**
   （本 GOAL 只把 (b) 草案推进到「有实现」，**不等于** (a)；见 `THREAT_MODEL.md` §6.5）；
9. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
10. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
11. **`undici` 的 pin（含 pnpm `overrides`）**——**不动**（归属上游，见 D-03 终态）；
12. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**。

**承继的诚实边界（如实保留，不是待办）**：

- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（且**不得**用「认证面已落地」替代它）。
- **`R-D1`｜Dependabot 告警**——`yaml` 已升（GOAL-018 EC-01）、`vite` 已清
  （GOAL-016 EC-03）；**`undici` 8 条（6 medium + 2 low）原样保留**，
  **归属上游**（升级面不在本仓）。**本 GOAL 不动它**。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，**原样保留**。
- **`R-F1`｜收敛 / 一致性判定含主观面时必须先操作化**——**原样保留**。
- **`R-F2`｜真实数据 / 调用规模不足时的诚实边界**——**原样保留**。
- **`W-4`（本机 m0 仍同进程跑阈值判据）/ `W-5`（新作业多一次冷装）/
  `W-6`（`tests/e2e/live_run_support.py` 只剩 1 行余量）**——**原样保留**；
  `W-6` 是**规模门禁的零余量告警**：本 GOAL 若需改该文件**必须先搬代码**。
- **`D-04` 的重启前置**——**先修误报面**（正则字面量 / `f-string` SQL / URL 形状 /
  大文件写盘被拒仍在发生）；**本 GOAL 不安装检测层、不改 hook 面、
  不改 `MIMOSA_GIT_GATE_MODE`**。

**本 GOAL 交付的是 D-12(a) 的「前置」，不是 (a) 本身**：
`THREAT_MODEL.md` §6.5 明写「(a) 的前置是**必须先有主体模型**——没有 principal 就没有
『越权』可言」。本 GOAL 交付**主体模型 + 最小认证面**（= 那个前置），
但**不产生** BOLA / BFLA 的负面测试套件，也**不**把「授权面」宣称成已覆盖。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `d4e559e`（**建档提交**，推送区间 `f8f6a8c..d4e559e`） | 治理 `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS: 6 deterministic checks`；**判据按压**：把 GOAL 的 `## 状态历史` 标题改名 ⇒ `validate.py` 判红（`GOAL 缺少章节 ## 状态历史: GOAL-20260926-019`）⇒ 证明**新建的 GOAL 确实被载入判据**；逐字节复原 ⇒ 绿 | M0 [**36206487801**](https://github.com/Eswink/research-system-new/actions/runs/36206487801) **八 job 全 success** + CodeQL [**36206486979**](https://github.com/Eswink/research-system-new/actions/runs/36206486979) **3/3 success**（`run_attempt=1`，轮询 `ALL_TERMINAL`；日志 `scratch/goal019-c0-ci-poll.log`）。**外部旁证**：push 回执报 **8 条**告警（6 moderate + 2 low），与 GOAL-018 收口时的残留面一致（全为 `undici`）⇒ 本轮**零依赖改动** | — | EC-01…EC-05 全 PENDING；授权与边界已落 frontmatter；起点已定位（写面 **60 条 mutating** / 29 个 router 文件 / 124 条路由；分类面 = `_MUTATING_METHODS`（`middleware.py:23`）；主体占位 = `dependencies.py:53` + `routers/approvals.py:124`，产品侧共 **6 处** actor 字面量；canonical 落点 = `outbox_events.envelope_json.actor`，读面 `routers/run_events.py:42`；**两个 450 行零余量文件正压在 EC-01 缝上**；`console_api_app.py:390` 是「无认证=基线」的现成探针） | cycle 1 = **EC-01 + EC-02**（主体模型 + 认证面） |
| 1 | PLAN-20260926-190（EC-01 + EC-02，并产出 EC-03 的证据面） | `（本轮回写提交 = 本行所在的提交；推送 tip 见回合汇报）` | **18 条新判据全绿**（`tests/api/test_principal_auth.py`）：三态（关闭⇒**200** 且端点回报 `actor=None`；不带/带错⇒**401** 且 `detail` 点名 `Bearer` / `does not match`；带对⇒**200** 且端点内 `current_principal().actor == service:fixture-principal`）+ **读面反证**（`GET /health` 与 `GET /runs/{id}` 在设了 token 但不带 token 下仍 **200**）+ **主体落 canonical**（`POST /approvals/{id}/decide` ⇒ `GET /runs/{id}/events` 的 `approval.decided` actor == 配置主体，且 `"user:console" not in actors`）+ **配对反证**（不带/带错 ⇒ 401 且决策事件**零条**、run 仍在 `WAITING_FOR_APPROVAL`）+ **向后兼容实测对照**（认证关闭 ⇒ `actors == ["user:console"]` **逐字**）。**三次按压**：A 去校验 ⇒ **2 failed**、B 强制回退常量 ⇒ **1 failed**（判词 `['user:console'] == ['service:fixture-principal']`）、C 读面也拦 ⇒ **5 failed**；全部逐字节复原。**`Idempotency-Key` 一字未动**：AST 源码段 + `sha256[:16]` 对 HEAD 比较 `IdempotencyMiddleware`/`.dispatch`/`_is_analysis_post`/`_problem` **四个哈希全等**（`78072fb10f633ffe` / `621b1605c11d18b7` / `7740b6009048f164` / `9ddb50204466a888`），两个常量字面量逐字相同。**凭据纪律四条反证全零命中**：变量名全工作树**恰好 1 次**（名字常量）、`…TOKEN\s*=` **零命中**、唯一比较是 `hmac.compare_digest`、`token ==` 形态零命中；`.env.example` 未改。**定向**：`tests/api`+`tests/contracts` **924 passed / 73 skipped**（含 **OpenAPI 快照绿 ⇒ 无漂移**）、`tests/architecture/python`（canonical `uv run`）**175 passed**、`ruff check` = `All checks passed!`、`ruff format --check` = **1032 files already formatted**、规模门禁 **1032 passed**。**全量 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`python/tests` = **4538 passed / 20 skipped**、`FAILED`/`ERROR` 零命中；日志 `scratch/goal019-c1-m0-rerun.log`）。**前端 e2e**（认证关闭）：stub **98 passed**、live **53 passed**（与 GOAL-018 基线**计数一致**）。治理 `validate.py` 绿 + `DOCS-CHECK PASS` | M0 [**36228978492**](https://github.com/Eswink/research-system-new/actions/runs/36228978492) **八 job 全 success** + CodeQL [**36228978213**](https://github.com/Eswink/research-system-new/actions/runs/36228978213) **3/3 success**（`run_attempt=1`，**一次成功**、无 flake；轮询 `ALL_TERMINAL`；日志 `scratch/goal019-c1-ci-poll.log`）⇒ 详见下方 **CI 台账** | **本轮内被全量 m0 抓到两处真红（已修）**：① `python/format-check` —— 新测试文件**未**纳入我先前的 `ruff format --check` 文件清单（3 处该折叠的签名/调用）；② `python/tests::…[services\api\app.py]` —— 新增 6 行把 **`create_app` 从 47 行推到 53 行**、越过 **50 行函数门禁**（该文件此前只剩 1 行余量）⇒ 抽 `_install_write_face_auth(app)` 后回到 48 行。**两处定向套件当时全绿** ⇒「受影响套件全绿」**不能**替代全量门。**实施期新增 D-9**：**不**复用 worker 网关的 `extract_bearer`（其包 `__init__` 急切导入 `create_worker_app`/`WorkerGatewayDeps`/`WorkerGatewaySettings` ⇒ 会把 **worker 信任域**拉进控制面导入图），改为自带 7 行解析器、只沿用同一原语与不变量 | **EC-01 / EC-02 = PASS**；**EC-03 = PASS**（全量 m0 + 两条 e2e 计数一致 + 显式对照 + `Idempotency-Key` 逐字节未动）；`RECHECK-20260926-191` = `PASS_WITH_WARNINGS`（W-1…W-9）。**EC-04（四处文档同源）与 EC-05（收口复检）仍 PENDING** | cycle 2 = **EC-04**（`IDENTITY_AND_ACCESS.md` / `THREAT_MODEL.md` 第 6 节 / `CONTROL_PLANE_API.md` / `LIVE_MODEL_RUNBOOK.md` 四处同源 + 可按压结构判据 + 零夸大），随后 **EC-05** 收口 |
| 2 | PLAN-20260926-192（EC-04） | `957fe05`（4 文档 + 判据；**推送 tip = 本行所在的记录提交，SHA 见回合汇报**） | **四处文档同源 + 一条可按压判据**：`git diff --stat` = **5 文件 / 146 插入 / 2 删除**（`IDENTITY_AND_ACCESS.md` 新增 `## Control Plane 写面认证（GOAL-019）` L99 + `### 未覆盖范围` L127 七条；`THREAT_MODEL.md` §6.2/§6.3/§6.5 就地标注 + §6.6 引用纪律收紧 + 新增 `### 6.7` L264；`CONTROL_PLANE_API.md` 文首 canonical 句 L3 + 认证段 + 更正「无 principal 概念」旧句；`LIVE_MODEL_RUNBOOK.md` §2 下新增 `### 2.1` L90）——**`## N` 编号零漂移**（新内容只加 `###`）；**产品代码零改动**（`services/**`、`packages/**`、`apps/web/**` 无本次改动）。**新判据** `tests/architecture/python/test_control_plane_auth_same_source.py` = **437 行 / 11 passed**：AC-1 同源声明句四份**各恰好一次逐字相同**；AC-2 四份各有**自己的**未覆盖锚点与**自己的**必需措辞（不许互相顶替）；AC-3 **21 条**肯定式安全断言零命中且**豁免机制自身受判**；AC-4 六条 AST（分类**复用** `_MUTATING_METHODS` 且全模块只有这一处方法字面集合 / 读面靠 `NotIn` 明确放行 / 认证面**不引用** `_ANALYSIS_ACTIONS` / `hmac.compare_digest` 且**无** `==` / 变量名单个读取点 / **无新增依赖**）；AC-5 `create_app` 里认证注册**在幂等之后**（`reversed` ⇒ 外层先跑）。**14 条按压**：**13 条按预期判红**（改一处口径 / 删整句 / 删未覆盖内容 / 删锚点 / 插肯定式断言 / 第二处方法集合 / 分类放宽含 GET / 例外集泄漏 / 换 `==` / 第二读取点 / `import requests` / 抹掉警告后果 / 反转注册顺序）+ **1 条期望不红**（插入**引述禁令** ⇒ 豁免按设计工作，证明豁免不是漏洞）；脚本强制 `old` **唯一命中**（防"按压打偏"）+ **sha256 14/14 逐字节还原**，终态基线复跑 `exit=0 failed=无`。**定向** architecture+tooling+`test_principal_auth.py` = **1377 passed**。**全量 m0 = `PASS: profile=m0; 23 deterministic checks`**（`M0_EXIT=0`、`PASS [` = **24**、`python/tests` = **4550 passed / 20 skipped**、`FAILED`/`ERROR` **0**；较 cycle 1 的 4538 **+12** = 11 条新用例 + 1 条规模门禁参数化条目；日志 `scratch/goal019-c2-m0.log`）。治理 `validate.py` = `Cursor 治理验证通过` + `DOCS-CHECK PASS: 6 deterministic checks` | M0 [**36232944933**](https://github.com/Eswink/research-system-new/actions/runs/36232944933) **八 job 全 success** + CodeQL [**36232944628**](https://github.com/Eswink/research-system-new/actions/runs/36232944628) **3/3 success**（`run_attempt=1`，**一次成功、无 flake**；轮询 `ALL_TERMINAL`；日志 `scratch/goal019-c2-ci-poll.log`）⇒ 详见下方 **CI 台账** | **本轮被门禁抓到两处真红（已修）**：① **规模门禁** —— 新判据首版 **451 行**，越 450 行硬上限 **1 行** ⇒ 压缩 `_HTTP_METHODS`（逐行集合 → `frozenset("…".split())`）与 `_DOC_UNCOVERED` 短条目 ⇒ **437 行**；② **判据首版 4 处自红（AST 形状假设）** —— `frozenset({…})` 是 `ast.Call`（`literal_eval` 直接抛）、`os.environ` 是 `Attribute`（属性名集合相等恒不成立）、f-string 里的变量名是 `FormattedValue`（不是字面量常量）、`async def dispatch` 是 `AsyncFunctionDef`。另有一处**按压自身的连带**：P5 首版替换文本顺手删掉了「零夸大」一词，而它是 **AC-2** 的必需措辞 ⇒ 一次按压打红两组，已改为保留该词——**教训**：按压的替换文本会改到别的判据的输入面，所以按压要报「**实际判红的集合**」而不是「红没红」 | `RECHECK-20260926-193` = `PASS_WITH_WARNINGS`（**W-1** 本复检与实施同轮不同源 ⇒ 独立结论以 cycle 3 两树复检为准；**W-2** 禁止面是**词表下限**（21 条只增不减）+ 文档集合写死四元组；**W-3** 同源句现有 **5** 处副本（有意摩擦）；**W-4** AC-2 观察窗 1200 字有界 ⇒ 可能假红但不得改成全文搜索；**W-5** P6 是"期望不红"的按压，读"14/14"必须读表；**W-6** 新判据 437/450 行余量 13 行；**W-7** 部署面（反代/TLS/多副本）**仍未验证**；**W-8** 前端仍无 token 输入面） | cycle 3 = **EC-05**（两树独立复检 + as-is 本机 m0 **23/23** + CI 台账到终态 + 残余 `R-M1`/`R-D1`/`R-B1`/`R-N1`/`R-F1`/`R-F2`/`W-4`/`W-5`/`W-6` 逐条登记 ⇒ `status: ACHIEVED`） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-019 落地） | `d4e559e` | M0 [36206487801](https://github.com/Eswink/research-system-new/actions/runs/36206487801) / CodeQL [36206486979](https://github.com/Eswink/research-system-new/actions/runs/36206486979) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，一次成功）：M0 `conclusion=success`，逐 job `quality-ubuntu-latest` / `console-frontend` / `quality-windows-latest` / `observability-overhead-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `eval-gate` / `collector-quality` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)` **3/3 `success`**。轮询日志 `scratch/goal019-c0-ci-poll.log`（第 40 轮 `completed=2/2`、`ALL_TERMINAL`）。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`） |
| cycle 1 实施（EC-01 + EC-02 + EC-03 证据） | `c87823e`（代码）+ `8ed413b`（记录；**推送 tip**） | M0 [**36228978492**](https://github.com/Eswink/research-system-new/actions/runs/36228978492) / CodeQL [**36228978213**](https://github.com/Eswink/research-system-new/actions/runs/36228978213) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，**一次成功**，无 flake、无重跑）：M0 `conclusion=success`，逐 job `console-frontend` / `quality-windows-latest` / `quality-ubuntu-latest` / `eval-gate` / `observability-overhead-windows-latest` / `container-quality` / `collector-quality` / `observability-overhead-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (python)` / `Analyze (actions)` **3/3 `success`**。轮询日志 `scratch/goal019-c1-ci-poll.log`（第 41 轮 `completed=2/2`、`ALL_TERMINAL`） |
| cycle 2 实施（EC-04 四处文档 + 可按压判据） | `957fe05`（文档 + 判据；**记录提交的 run 见回合汇报**） | M0 [**36232944933**](https://github.com/Eswink/research-system-new/actions/runs/36232944933) **八 job 全 success**（container-quality / console-frontend / collector-quality / eval-gate / quality-windows-latest / observability-overhead-ubuntu-latest / quality-ubuntu-latest / observability-overhead-windows-latest）+ CodeQL [**36232944628**](https://github.com/Eswink/research-system-new/actions/runs/36232944628) **3/3 success**（`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)`；`run_attempt=1`，**一次成功、无 flake**；轮询 `ALL_TERMINAL sha=957fe05…`；日志 `scratch/goal019-c2-ci-poll.log`）。**外部旁证**：push 回执报 **8 条**告警（6 moderate + 2 low），与 cycle 1 / GOAL-018 收口一致（全为 `undici`）⇒ 本轮**零依赖改动** |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | ACTIVE | 建档：用户会话指令（goal 模式）判词**「甲」** ⇒ **主体模型 + 最小认证面（谁在调用）**，**不碰多租户**。**建档方式 = 新建 GOAL-019**（不是复活 GOAL-018；理由：新范围 + GOAL-018 的取证要求是「鉴权 / 中间件 / 路由保护零改动」，两者互相顶替）。**三条口径**（判词 (i)(ii)(iii)）与边界、push 授权一并落 frontmatter：**(i) 只保护写面**（复用 `_MUTATING_METHODS` 同一分类）、**(ii) 认证可关**（环境变量留空 ⇒ 关闭 + 启动显式警告；CI 与 live 夹具不受影响）、**(iii) 主体归因落 canonical**（替换 `default_actor` 占位，**向后兼容**）。五 EC 设计（主体模型 / 认证面 / 零回归 / 文档同源 / 收口复检）。**明确不做**：多租户、RBAC、读面认证、改 `Idempotency-Key` 语义、把 token 写进任何地方、新增依赖、D-12(a)。**建档时零代码改动**（只增本文件）。**判据按压**：GOAL 标题改名 ⇒ `validate.py` 判红 ⇒ 逐字节复原 ⇒ 绿。建档提交 `d4e559e` 的 CI = **八 job 全 success + CodeQL 3/3**（`run_attempt=1`）。 |
| 2026-09-26 | ACTIVE | cycle 1（PLAN-20260926-190）：**EC-01 + EC-02 落地并 PASS**，EC-03 的完整证据面同时产出并 **PASS**。交付 = `packages/domain/principal.py`（`Principal` + `PrincipalKind`；**无**租户/角色字段）+ `packages/application/principal_context.py`（请求级主体上下文）+ 写面认证中间件（并入 `services/api/middleware.py`，**复用** `_MUTATING_METHODS`）+ `eventing.publish_event` 读点回退 + 审批路径归因（回退历史常量）。**认证三态 + 读面反证 + 主体落 canonical + 配对反证 + 向后兼容实测对照**全部实跑；**三次按压**判红并逐字节复原；`Idempotency-Key` **AST 哈希对 HEAD 全等**；凭据纪律四条反证全零命中；**全量 m0 = 23/23**；前端 e2e = 98 / 53（与基线计数一致）。**本轮内被 m0 抓到并修掉两处真红**（format-check / `create_app` 撞 50 行函数门禁）⇒ 再次证明全量门不可被定向套件替代。**EC-04 / EC-05 仍 PENDING** ⇒ GOAL 维持 **ACTIVE**，下一 cycle 做四处文档同源。 |
| 2026-09-26 | ACTIVE | cycle 2（PLAN-20260926-192）：**EC-04 = PASS**。四处文档用**同一条逐字重复**的 canonical 声明句登记「写面已认证 / 读面未认证 / 多租户与 RBAC 未实现」，并**各自**写明未覆盖范围（`IDENTITY_AND_ACCESS.md` 七条 / `THREAT_MODEL.md` §6.7 / `CONTROL_PLANE_API.md` 文首 / `LIVE_MODEL_RUNBOOK.md` §2.1）；runbook 只加 `###` ⇒ `## N` 编号**零漂移**。新增判据 `test_control_plane_auth_same_source.py`（**437 行 / 11 例**，AC-1…AC-5）把「同源 / 各有未覆盖范围 / 零夸大 / 判据绑代码 / 注册顺序」变成**可机械判**的事实，并新增一条**自判**：零夸大判据的**否定语境豁免自身受判**（宣示 ⇒ 红，引述禁令 ⇒ 绿）。**14 条按压**：13 条按预期判红 + 1 条期望不红（证明豁免按设计），`old` 唯一命中 + sha256 **14/14 逐字节还原**。**产品代码零改动**；定向 1377 passed；**全量 m0 = 23/23**（`python/tests` 4550 passed，较 cycle 1 的 4538 **+12** = 11 例 + 1 参数化条目）；CI = M0 八 job + CodeQL 3/3（`957fe05`，一次成功）。**本轮内被门禁抓到并修掉两处真红**（规模门禁 451 行 → 437 行；判据首版 4 处 AST 形状自红）。`RECHECK-20260926-193` = `PASS_WITH_WARNINGS`（W-1…W-8）。**EC-05 仍未完成** ⇒ GOAL 维持 **ACTIVE**，下一 cycle 做收口复检。 |
