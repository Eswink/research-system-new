---
id: GOAL-20260928-022
slug: recheck-mechanization-and-multi-path-evidence
title: 复检过程的持续保证（两树入口机械化 + 多路证据判据 + 复检脚本规范）
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-28 用户会话指令（goal 模式）：**建档 GOAL-022（自检的持续保证：两树复检过程化 +
    复检脚本规范 + 多路证据判据）并授权本驱动自动化循环推进、无需逐轮确认**。
    authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为三件事，**越界即 BLOCKED**：
    **(i) 新增 / 改造复检工具与 SOP 条款**（可复用入口、两树比较、判词逐行比对）、
    **(ii) 新增机械判据**（覆盖 EC ①~③）、**(iii) 修复被这些判据证明为真缺陷的问题**，
    外加 **文档同源更新**（`docs/` 下的复检与质量门相关文档 + `docs/INDEX.md` 登记）。
    **不加新能力、不放宽任何判据、不改安全策略**；本轮只做**过程机械化 + 判据固化 + 环境口径固化**。
    (1) **明确不做（命中即 BLOCKED）**：**给读面加认证**（GET/HEAD 仍放行）；
    **多租户 / RBAC / organization scope**；**BOLA/BFLA 实现**；**逐调用方身份**；
    **新增依赖**（一律标准库 / 现有栈）；**改任何既有判据、门禁、阈值、放行面**
    （含 `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
    `test_record_face_is_covered_by_the_gate.py`、`test_m2_audit.py`、`tests/egress_guard.py`、
    `tests/tooling/test_m0_ci_coverage.py`）；**把 token 写进任何文件 / CI / 记录 / 日志**；
    **改 401 响应形态或 `Idempotency-Key` 语义**；**部署面验证**（需真实环境 ⇒ 只允许
    「登记为不可在本机验证 + 给出可复核检查项」）；**动 `undici`**、
    **改 `ADR-0031` 的 Status**（维持 `Proposed`）。
    (2) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (3) **不做真实出网**：本 GOAL **不做真实出网调用**（全离线）；SQL 一律**参数绑定**；
    凭据**只从环境变量**读取；观测隐私**不记录完整 Prompt、不记录 token**（AGENTS.md §10）；
    判据中的 token 一律用**测试内构造的假值**，**不得**把真实 token 字面量写进树。
    (4) **边界**：GOAL-001…021 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-018 的**全部 13 项 `D-NN`** 已结清、
    **本 GOAL 不重开**；GOAL-019 / GOAL-020 / GOAL-021 的**未覆盖范围原样保留**
    （本 GOAL 只做**过程机械化与登记**，不把它们变成已覆盖）。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    把 GOAL-020 / GOAL-021 两次**手工补跑**的「两树同结论」从「**这一次做到了**」推进到
    「**每次都必然做到**」：**① 两树复检的机械化**（一个可复用入口对「当前树 + 干净 checkout」
    跑同一组断言并逐行比对判词，含 `sha256` 与**反证判红**）、**② 多路证据判据**
    （RECHECK 声明了几路跑法就必须有几路**各自**的留档证据引用，把 GOAL-021 的 `W-0` 机械化）、
    **③ 复检脚本编写规范**（把历史踩过的环境坑固化成文档 + 判据，每条附可复跑检查）、
    **④ 收口复检与残余登记**（**用 ① 建好的入口自举**本轮自己的收口复检 ⇒ 两树同结论 +
    as-is 本机 m0 到 23/23 + 治理绿 + CI 台账到终态 + 残余与未覆盖范围逐条）。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**零**新依赖；**零**策略面 allow；
    **不得**给读面加认证；**不得**改 401 形态或 `Idempotency-Key` 语义；**不得**宣称项目安全
    （`R-M1` 仍在）；**不得**引入多租户 / RBAC / BOLA·BFLA 实现；**不得**把 token 写进任何地方。
exit_criteria:
  - id: EC-01
    criterion: >-
      **两树复检的机械化**（主干），四条各自可判：
      **(a) 一个可复用入口**：`tools/two_tree_recheck.py` 对「**当前树** + **干净 checkout**」
      跑**同一组断言**（同一个复检脚本、同一个解释器），并把两路判词**逐行比对** ——
      比对结果含**两份判词文件的 `sha256`**；入口以**退出码**表达结论（一致且两路皆绿 ⇒ `0`；
      有任何差异或任一路不绿 ⇒ **非 0**）。
      **(b) 两树环境口径一致**（这三条 GOAL-020 / GOAL-021 都踩过，必须**写进工具**）：
      **① 共用解释器**（干净 checkout 没有自己的 `.venv`；现场建会超时且比的是两套环境
      ⇒ 两树都用**主树**的解释器，等价 `uv run --frozen --no-sync`）；
      **② 输出纯度**（整份输出含耗时 / 路径 ⇒ 天然不同 ⇒ 入口只取**判词行**，
      由复检脚本的 `--verdict-only` 模式产出）；
      **③ 路径无关**（判词行**不得**嵌入随树变化的绝对路径）。
      **(c) SOP 条款 + 判据钉住**：文档写明「**收口复检必须两树**」，且该条款**不得悬空** ——
      由判据钉住（条款所在小节必须点名**存在的**入口文件与判据文件；改名即判红）。
      **(d) 反证必须真的会红**：故意让**第二树**跑出**不同**结果 ⇒ 入口**必须判红**
      （非 0 退出 + 点名差异行），**不能**只是「打印两份」。
      **判据须被按压**：临时破坏入口的比对逻辑（或让两树真的不同）⇒ 判据判红；
      **逐字节复原**（raw `sha256`）⇒ 绿。
    verify: >-
      ① 入口在树：`tools/two_tree_recheck.py`（`tools/` 不在 `PRODUCT_ROOTS` 内 ⇒
      **不被** ruff / mypy / 规模门禁覆盖，见「事实层结论」第 3 条）；
      ② **两树实跑各留档**（判词文件 + `sha256`），且两份判词**逐行相同**；
      ③ 入口的**判据**在树且在门的收集面内（`tests/tooling/test_two_tree_recheck_entry.py`；
      `python/tests` 的 `pytest` 收集面覆盖它 ⇒ m0 条数**仍为 23**）；
      ④ **只跑一路 ⇒ 入口非 0 退出**（closeout 模式缺干净树时必须拒绝，**不得**降级为单树 PASS）；
      ⑤ **反证红**：让第二树产生差异（如注入一处破坏）⇒ 入口**非 0** 且**点名差异行**；
      逐字节复原 ⇒ 复绿；
      ⑥ 三条环境口径**各有一条行为判据**（共用解释器 / 判词纯度 / 路径无关），
      且**每条都被按压过**（逐条报实际判红集合，不是只看红没红）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **多路证据判据**（把 GOAL-021 的 `W-0` 机械化）：RECHECK 的复检条款若声明了
      **多种跑法**（如「当前树 **+** 干净 checkout」、「多平台」、「多入口」），则**每一路
      都必须有各自的留档证据引用**；**只跑一路就记 PASS ⇒ 判据判红**。
      **判据形态（承 MEM-141：判据不得被文档引用 / 字面量喂饱）**：绑定**结构化字段**，
      不绑定散文 —— RECHECK frontmatter 的 `slug` 形如 `goal-*-closeout-recheck`（**收口复检**，
      这是既有记录**已经**在用的结构化字段）且 `created_at` **不早于本 GOAL 建档日**者，
      **必须**携带 `verify_paths` 列表；每项 = **一个具名路径** + **一个证据引用**；
      同一 RECHECK 内各项的证据引用**两两不同**，且**指向存在的文件**。
      **射程边界（如实登记）**：本判据**不**追溯改写历史 RECHECK（既有记录是不可变证据）
      ⇒ 建档日之前的历史记录**不在**受判集合内，该剩余面**逐条登记**，**不得**读成「全仓已覆盖」。
    verify: >-
      ① 新判据在树：`tests/architecture/python/test_declared_recheck_paths_have_evidence.py`
      （落在 `python/tests` 收集面内 ⇒ m0 条数**仍为 23**）；
      ② **按压矩阵逐轮留档**（报**实际判红集合**）：造一条「声明两路但两路**共用同一证据引用**」
      ⇒ 判据**判红**；补齐**互不相同**的证据 ⇒ **复绿**；**逐字节复原**（raw `sha256`）⇒ 绿；
      ③ 判据读的是**结构化字段**（`slug` / `created_at` / `verify_paths`）**加**证据引用的
      **文件存在性**，**不是**文档里的某句话 ⇒ 把条款文字改写成别的说法**不改变**判据结论
      （此点须以实测留档，作为「未被字面量喂饱」的实证）；
      ④ 历史剩余面**逐条登记**（建档日之前的收口复检清单 + 未补 `verify_paths` 这一事实）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **复检脚本编写规范**（环境口径固化）：产出一页规范
      `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`，覆盖本次与历史踩过的坑，**六条**：
      **① 共用解释器**、**② `--verdict-only` 纯度**、**③ 文本 vs 二进制读写**（避免 CRLF 污染
      ⇒ 按压 / 复原必须 `read_bytes` / `write_bytes`）、**④ 落点断言**（`--root` 参数化，
      不硬编码仓库根）、**⑤ 进程卫生**（teardown 必须连**整棵树**，Windows 用 `taskkill /T /F`）、
      **⑥ 路径无关输出**。
      **规范里每条必须附一条判据或可复跑检查，不得只是散文**；**至少半数（≥ 3 条）有机械判据**。
      文档须在 `docs/INDEX.md` **登记**。
    verify: >-
      ① 文档在树：`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`，含六条各自的小节标题
      （**结构性锚点**，逐条可机械定位）；
      ② `docs/INDEX.md` 含该文档路径（登记在位）；
      ③ 判据在树且在门收集面内：`tests/architecture/python/test_recheck_script_conventions_are_pinned.py`；
      它**逐条**断言六条里哪些有机械判据，且**点名存在的**判据文件（承既有
      `test_record_face_is_covered_by_the_gate.py` 的「条款不得悬空」形态：改名即判红）；
      ④ **≥ 3 条**有机械判据（计数断言，写入判据源码，不是散文）；
      ⑤ **按压**：把某条被点名的判据文件改名（或抹掉一条规范小节标题）⇒ 判据**判红**；
      逐字节复原 ⇒ 绿。
    status: PENDING
  - id: EC-04
    criterion: >-
      **收口复检 + 残余登记**（**自举**：本轮必须用 EC-01 建好的入口做自己的收口复检）：
      ① 用 `tools/two_tree_recheck.py` 对**当前树**与**干净 checkout** 跑本轮收口复检脚本
      ⇒ **两树同结论**（判词逐行相同 + `sha256` 相同）；
      ② **as-is 本机 m0 到 23/23**（`PASS: profile=m0; 23 deterministic checks`），
      且**运行发生在记录写入之后**（承 MEM-145：写记录 → 记录面判据 → 全量门）；
      ③ 治理 `validate.py` **绿**（含 `DOCS-CHECK`）；
      ④ **CI 台账到终态**（M0 **八 job** + CodeQL，含 `run_attempt`；flake 判定靠**同一代码的复跑对照**）；
      ⑤ **承继残余逐条在位**：`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`；
      ⑥ **未覆盖范围逐条明写**：**读面未认证** / **多租户未做** / **BOLA·BFLA 未做** /
      **部署面未验证** / **`R-M1` 未收口（不得宣称项目安全）**。
    verify: >-
      ① 两树入口的**实跑**留档（判词文件 + `sha256` + 入口退出码 = `0`），
      且**入口自身在树**（这是 EC-01 的交付物被**真的用起来**的证据，不是又一份手工补跑）；
      ② m0 日志留档含终态行 + 运行时刻（在记录写入之后）+ 零 `FAILED` / `ERROR`；
      ③ `validate.py` 输出 `Cursor 治理验证通过`；
      ④ 台账逐 run 逐 job（含 `run_attempt`）；
      ⑤ 残余清单在本文件**逐条**出现；⑥ 未覆盖范围**逐条**出现。
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
      （含给 `Principal` 加租户 / 角色字段）；或做 **BOLA / BFLA 的专项实现**
    - >-
      新增**任何**依赖（含为两树入口引入第三方库；一律标准库 + 现有栈）
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
      **判据 / 扫描面 / 顺序语义 / `SOP_SECTION` 小节标题 / `SOP_NAMED_CRITERIA`**，
      或放宽其中任一条；也**不得**改 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 里
      该判据点名的那一节（标题与该节内点名的两个判据文件名）
    - >-
      改 `tests/api/test_security_scan.py` 的持久层断言或 `sk-` 字面量断言，
      或用「惰性访问器」等方式**绕过**它而把 token 落进 `localStorage` / `sessionStorage`
    - >-
      改门禁或阈值（`validate_bundle` 检查项、m0 任一 check、`.github/workflows/**`
      的 job 结构、`test_m2_audit.py` 镜像判据），或改 m0 的**条数**（终态行必须仍是 23）
    - >-
      改 `tests/tooling/test_m0_ci_coverage.py` 的判据 / 覆盖面
    - >-
      把**新判据**写成「被文档引用 / 字面量喂饱」的形态（承 MEM-141：判据必须绑定
      **声明行**或**行为**），或让新判据**跳过按压**
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
    **新增依赖**（含为两树入口引入第三方库）—— **立即 BLOCKED**
  - >-
    **把 token 写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 / 夹具 / 示例 / 前端源码 /
    playwright 配置 / **判据源码**）—— **立即 BLOCKED**；明文凭据泄露（即使可弃用）
    ⇒ 立即停止并报告
  - >-
    **改认证的 401 响应形态**，或改 `Idempotency-Key` 语义 —— **立即 BLOCKED**
  - >-
    **放宽 `test_reproducibility_wording.py` / `test_control_plane_auth_same_source.py` /
    `test_record_face_is_covered_by_the_gate.py` / `test_m2_audit.py` /
    `tests/tooling/test_m0_ci_coverage.py`** 的判据 / 词表 / 扫描面 / 阈值、或
    `tests/egress_guard.py` 的目的地判定 —— **立即 BLOCKED**
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
    把复检产物或认证态写进 canonical 取代域实体）—— **立即 BLOCKED**
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
child_plans: []
latest_recheck: null
memory_entries: []
---

## 目标与退出标准

**一句话**：把 GOAL-020 / GOAL-021 两次**手工补跑**的「两树同结论」从「**这一次做到了**」
推进到「**每次都必然做到**」——**两树入口机械化 + 多路证据判据 + 复检脚本规范 + 自举收口**。

**本 GOAL 不加新能力、不放宽任何判据、不改安全策略。** 若新判据**证明**某处是真缺陷
⇒ 在授权范围内修**产品代码**；若某条**本机无法验证** ⇒ **登记为 PENDING**，**不得**记 PASS。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **两树复检的机械化**（可复用入口 + 环境口径 + SOP 条款 + 反证红） | `tools/two_tree_recheck.py` + 行为判据 + 按压矩阵 | **PENDING** |
| EC-02 | **多路证据判据**（每一路各自留档；只跑一路记 PASS ⇒ 判红） | 结构化字段判据 + 按压 + 历史剩余面登记 | **PENDING** |
| EC-03 | **复检脚本编写规范**（六条，每条附判据或可复跑检查，≥ 3 条有机械判据） | 规范文档 + `docs/INDEX.md` 登记 + 钉条款判据 | **PENDING** |
| EC-04 | **收口复检 + 残余登记**（**自举**用 EC-01 的入口 + m0 23/23 + 治理 + CI 台账） | 两树实跑留档 + m0 日志 + 台账 + 残余逐条 | **PENDING** |

**依赖关系**：EC-01 / EC-02 / EC-03 互相独立（各判一个面，可分别验收）；
**EC-04 依赖 EC-01**（必须**用**建好的入口做自己的收口复检，这是「机械化真的可用」的证据，
不是又一份手工补跑）；EC-04 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **`scratch/` 是 gitignored**（`.gitignore:43` 有 `scratch/`）⇒ 依任务书口径
   **工具必须落 `tools/` 才算交付**；判词归档可留 `scratch/`，但**必须在记录里引用**
   （否则记录不可复核）。既有先例：`tools/verify_goal015_closeout.py`。
2. **`tests/tooling/` 是本仓既有的「`tools/` 脚本判据」落点**（先例 5 个：
   `test_backup_cli.py` / `test_credential_audit.py` / `test_docs_consistency_check.py` /
   `test_personal_reference_workflow.py` / `test_restore_cli.py`）⇒ EC-01 的判据沿用该形态。
3. **`tools/` 逃逸四道门（实测，本 GOAL 最要紧的环境事实）**：
   `run_all_checks.py` 的 `PRODUCT_ROOTS = ("apps", "services", "packages", "adapters", "tests")`
   **不含 `tools`**；`pyproject.toml` 的 `[tool.mypy].files` **不含 `tools`**；
   `tests/tooling/test_python_source_limits.py` 的 `PRODUCT_ROOTS` 同样**不含 `tools`**
   ⇒ 落在 `tools/` 的新脚本**不被** `python/product-lint`、`python/format-check`、
   `python/typecheck`、规模门禁覆盖。
   ⇒ **结论**：EC-01 的入口**必须**由 `tests/tooling/` 的判据**按行为**钉住（不能靠 lint 兜底）；
   且新入口**自愿**遵守同样的规模与风格约束（**不得**因为无人检查就放松写法）。
4. **新增判据必须落在既有 check 的收集面内**：`m0` 的 `23` **硬编码**在
   `tools/quarantine_and_run_m0.py:34`、`tools/classify_local_gate_reds.py:108`、
   `docs/architecture/LOCAL_GATE_PROTOCOL.md:31` ⇒ 新判据只能落在 `tests/**`
   （`python/tests` check = `pytest --ignore=<边界判据>`，收集 `tests/` 全树）⇒ **m0 仍是 23**。
   m0 组合实测 = python **6** + typescript **9** + framework **8** = **23**。
5. **RECHECK 没有 `verify` frontmatter 字段（实测）**：多路跑法的声明**写在正文散文里**
   （如 `RECHECK-20260927-210` 的 EC-05 条款①、`RECHECK-20260919-113` 的「当前树 + 干净
   checkout 两处独立」）。⇒ 若判据去匹配这些散文，就正好落进 **MEM-141** 警告的形态
   （**用文本巧合判，而不是用语法结构判**）。**因此 EC-02 必须绑定结构化字段**：
   `slug` 是本仓**已经**在用的结构化字段 —— 既有收口复检的 slug 一律形如
   `goal-*-closeout-recheck`（`-195` / `-200` / `-210` / `-185` / `-189` / `-179` / `-099` /
   `-106` / `-113` / `-120` 等），`created_at` 同样是结构化字段 ⇒
   **「收口复检 ⇒ 必须携带 `verify_paths`」是可判定的结构化义务**，不需要读散文。
6. **「SOP 条款 + 判据钉住该条款」在本仓已有先例形态**：
   `tests/architecture/python/test_record_face_is_covered_by_the_gate.py` 用
   `SOP_SECTION`（小节标题）+ `SOP_NAMED_CRITERIA`（条款内**必须点名**的判据文件名）
   钉住 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 的一节，**改名即判红**（「条款不得悬空」）。
   EC-01(c) 与 EC-03 沿用该形态；**该既有判据本身不得改动**，且
   `LOCAL_GATE_PROTOCOL.md` 里被它点名的那一节（标题与该节内的两个文件名）**不得触碰**。
7. **话术判据的扫描面含 `.cursor/plans`**（`_SCAN_ROOTS`，且 `scratch` 在 `_SKIP_DIRS`）⇒
   本文件与后续记录**不得**出现**肯定式**的「完全可复现」/「完全模型可复现」/
   「fully reproducible」/「fully model-reproducible」这四条越级表述
   （口径词是「**可重复配置**」）。**实测教训**：该判据认的是 `「」`/`"` 这类**引号字符**
   （`_is_quoted` 看相邻字符），**反引号 `` ` `` 不算引用** ⇒ 用反引号列出这四个词
   **仍会被判红**（建档首轮即被本判据抓到一次，已改）。
8. **`RECHECK-20260927-210` 的 `W-0`（本 GOAL 的直接动因）**：GOAL-021 的 EC-05 条款①
   写明两路，**首轮只跑一路且未在「未复核的面」登记，却随 EC-05 记 PASS** ⇒ 被完成核验判负，
   补跑后达成。教训逐字保留：「条款里写明的**每一路**都要**各自留档**；
   「跑了一路 + 结论看起来一样」**不能**替代」——**EC-02 就是这条教训的机械化**。
9. **两树比较的三个环境坑（GOAL-020 / GOAL-021 都踩过，承 `MEM-20260927-153` 与
   `MEM-20260927-152`）**：**① 解释器**（干净 checkout 没有自己的 `.venv`；
   现场建会超时且比的是两套环境 ⇒ 两树共用主树解释器）；**② 输出纯度**
   （整份输出含耗时 / 路径 ⇒ 天然不同 ⇒ 只比**判词行**）；**③ 文本 vs 二进制读写**
   （`pathlib.write_text` 在 Windows 会把 LF 写成 CRLF ⇒ raw `sha256` 变 ⇒
   「逐字节复原」复核（正确地）判不一致；**而 `git diff` 会因 `.gitattributes` 归一化
   静默吞掉该差异** ⇒ `git diff` **不足以**证明逐字节复原，raw `sha256` 才是判据）。
   ⇒ 这三条**必须写进入口**（EC-01(b)），不是只写在文档里。
10. **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本 teardown **必须连整棵树**
    （Windows 用 `taskkill /T /F`）；跑完复验**零泄漏**。两树入口会起子进程
    ⇒ 这是 EC-01/EC-03 的硬约束。
11. **`docs/architecture/` 是本仓「工程协议页」的既有落点**（同目录已有
    `LOCAL_GATE_PROTOCOL.md`、`PORTS.md` 等）⇒ EC-03 的规范页落该目录，
    命名沿用 `SCREAMING_SNAKE_CASE.md` 形态。
12. **默认门一律离线**（`tests/egress_guard.py` 是结构判据）：两树入口**不做任何出网调用**；
    干净 checkout 用 **`git worktree add --detach`**（本机可用、无需网络）。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-022-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-022**」（**不是**把 GOAL-021 置回 ACTIVE）。
理由：**「复检过程的持续保证」是新范围**（把一次性做法变成**每次都必然发生**的机械保证），
而 GOAL-021 的取证面是「**边界是否成立**」——**不重叠**；且 GOAL-021 已 ACHIEVED 收口，
其 `W-0` 是**过程缺陷**（复检范围登记不完整），把它机械化属于**新的交付面**。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260928-022` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件**——新判据文件先算行数；`tools/` 虽逃逸门禁，
  **仍自愿遵守**）；快照类门禁（OpenAPI / 设计基线：**若漂移按既有流程重生成 + 目检，不调容差**）；
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
  本 GOAL 的 EC-02 是这条纪律的**直接对象**：它**必须**绑结构化字段（`slug` /
  `created_at` / `verify_paths`）+ 文件存在性，**不得**去匹配散文。
- **反证必须先验形态**（承 GOAL-021 第 7 条事实）：写「删掉 X ⇒ 判据红」**之前**先实测该反证
  **真的会红**；不可证伪的形态**不得**写进退出标准。
- **多路各自留档**（承 `MEM-20260927-153`，EC-02 正是它的机械化）：任何声明多路的条款，
  **每一路都要有独立证据引用**。
- **逐字节复原的证据必须是 raw `sha256`**（承 `MEM-20260927-152`）：`git diff` 会因
  `.gitattributes` 归一化掩盖行尾变化 ⇒ **不得**用 `git diff` 充当逐字节证据。
- **撤回纪律**：改共享工具 / 夹具时**先数清谁拿它的失败形态当夹具**；
  CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：任何起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧复验**。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」
  （写下门日志本身也是记录）⇒ 本地门跑在「当时记录已写完」的状态，
  **记录面的最终覆盖由 CI 承担**；**不得**为此无限回退。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先，禁改断言迁就**；若红的是**本轮新增判据**且根因是判据自身写错 ⇒ 改判据（并**按压**复验） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、RSS 阈值型、`evolution_state.json` 的 WinError 5） | 按既有配方重跑；**flake 判定必须靠同一代码的复跑对照**；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 **全部 PASS** 且有**实跑证据**（每条含**先红后绿**或
  **边界成立**的证据）+ 独立 RECHECK `PASS` / `PASS_WITH_WARNINGS` + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + **未覆盖范围逐条明写**。
  **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
  本 GOAL 的收口判词**必须**写明：**① 两树入口的实跑证据（含反证红）**、
  **② 多路证据判据的按压记录**（实际判红集合）、**③ 规范六条里哪些有机械判据**、
  **④ as-is 本机 m0 的终态行**、**⑤ 未覆盖范围**、**⑥ EC-02 的历史剩余面**。
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

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`.cursor/plans/goals/GOAL-20260926-018-residual-closeout-and-decision-register.md`
的「不进入循环 / 需人工拍板」节 + `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**（`D-01` / `D-02` / `D-07` / `D-08` / `D-09` / `D-10` / `D-11` / `D-12` / `D-13`）、
**部分实施 1 项**（`D-03`：`vite` 已升 + `yaml` 已升；`undici` 已调研未升）、
**已拍板为维持现状 3 项**（`D-04` / `D-05` / `D-06`）、**未授权待拍板 0 项**。
⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019 / GOAL-020 / GOAL-021 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（本 GOAL 不碰认证面） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留** |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **原样保留**（本轮**不**把它变成已验证） |
| `W-13` | 前端无 token 输入面 | 已由 GOAL-020 **收口**（**不改回**） |
| `W-14` | 记录面判据的扫描面未逐一核实 | 已由 GOAL-020 **收口**（**不改回**） |
| `W-0`（GOAL-021） | 复检**范围登记不完整**（两树条款首轮被静默跳过） | **本 GOAL 的动因**：由 **EC-02** 机械化后收口；**不再**保留为未处置项 |

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

1. **读面认证（GET / HEAD）**——**不做**（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
2. **多租户隔离 / organization scope**——**不做**（M18）；
3. **RBAC / 角色 / 权限矩阵**——**不做**；
4. **BOLA / BFLA 的专项实现**——**不做**（仍归 M18 / 另行授权；**如实保留**）；
5. **逐调用方身份**（caller-declared identity）——**不做**（单 token ⇒ 单主体）；
6. **新增依赖**——**不做**（一律标准库 / 现有栈；两树入口只用标准库 + 既有 `uv` / `git`）；
7. **改任何既有判据 / 门禁 / 阈值 / 放行面**——**不做**（含
   `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
   `test_record_face_is_covered_by_the_gate.py`、`test_m2_audit.py`、`tests/egress_guard.py`、
   `tests/tooling/test_m0_ci_coverage.py`）；
   也**不得**改 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 里被
   `test_record_face_is_covered_by_the_gate.py` 点名的那一节（标题与该节内两个判据文件名）；
8. **改 `Idempotency-Key` 语义**——**不做**；
9. **改认证的 401 响应形态**——**不做**；
10. **把 token 值写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出 / 前端源码 /
    判据源码**——**不做**（**只登记变量名**，**绝不留值**）；判据一律用**测试内构造的合成假值**；
11. **部署面验证**（需真实环境）——**只允许**「登记为不可在本机验证 + 给出可复核检查项」；
12. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
13. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
14. **`undici` 的 pin**——**不动**（归属上游，见 D-03 终态）；
15. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**；
16. **把新判据写成「被文档引用 / 字面量喂饱」的形态**——**不做**（承 MEM-141）；
    新判据**必须**绑声明行 / 行为，且**必须被按压过**。

**承继的诚实边界（如实保留，不是待办）**：

- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（且**不得**用「机械化已完成」替代它——**过程机械化 ≠ 项目安全**）。
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

**本 GOAL 交付的是「复检过程的机械保证」，不是「判据更强」**：
把两树比较做成入口、把多路留档做成判据，**不改变**任何既有判据的强度，
也**不扩大**任何保护面。EC-02 的判据**只判「声明的路数是否各有留档」**，
**不判**「这些路跑出的结论是否正确」——后者仍由各自 RECHECK 承载。
**关键区分**：本 GOAL 让「**跳过一路**」这类过程缺陷**可被判红**；
它**不能**保证「**没有人漏声明**」——未声明多路的记录仍不会被本判据覆盖（如实保留）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | **建档提交**（本行由该提交写入 ⇒ 依「固定口径」其 SHA 与 CI run 只在回合汇报记账，不回写文件） | **治理** `validate.py` = `Cursor 治理验证通过`（8 行结论，含「GOAL 循环记录结构合规；push 授权显式登记」）；**DOCS-CHECK** = `DOCS-CHECK PASS: 6 deterministic checks`；**记录面判据**（`test_reproducibility_wording.py` + `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）= **24 passed**；**凭据四面审计** `tools/credential_audit.py` = `PASS: 四面扫描无明文凭据命中`（tracked 3472 / records 406 / config_db 1 / logs 454，**offenders=0**）；**as-is 本机 m0（记录写完之后、独占运行、仓库 `.venv`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4613 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal022-c0-m0-rerun.log`）。**首轮 m0 = 22/23（如实登记 + 归因 + 复跑对照）**：`framework/run_cursor_framework_evals` 判红，签名为 `PermissionError: [WinError 5]` at `hooks/common.py:161` 的 `os.replace`（`evolution_state.json.tmp` → `evolution_state.json`）⇒ **环境类 (ii)**（与既有配方逐字吻合）；取证：确认无其它 m0 / pytest 在跑（`tasklist` 零 python 进程）→ 清残留 `.cursor/runtime/evolution_state.json.tmp` → **单独**跑该 check 得 `FRAMEWORK EVAL PASS`（exit 0）⇒ **同一代码独占重跑全量门 ⇒ 23/23**。**未改 check、未改阈值、未查产品代码**。**建档轮另踩到一处自己的红（如实登记）**：首版在事实层结论第 7 条用**反引号**列出四个越级表述词 ⇒ 被话术判据判红（`_is_quoted` 只认 `「」`/`"` 这类引号字符，**反引号不算引用**）⇒ 改引号形态后 **24 passed**；该教训已写进第 7 条正文。**本机无 `make`**（实测 `make validate-all` ⇒ `make: command not found`，退出码 127）⇒ 改用 Makefile 的同一命令直跑 `run_all_checks.py --profile m0 --keep-going`，**与 canonical 调用等价**（同解释器、同 DSN 固化、同 `--keep-going`）。 | **待本轮补记**（推送后按 REST API 轮询到终态：M0 八 job + CodeQL + `run_attempt`；依固定口径，本行所在提交的 run 在回合汇报记账） | **零产品代码改动**（只新增本文件）。**本轮修掉的是自己的记录措辞 1 处**（引号形态）；**m0 的 1 条红是环境类 flake**，非缺陷 | EC-01…EC-04 全 PENDING。起点已定位：`tools/` **逃逸四道门**（第 3 条事实）⇒ 入口必须由 `tests/tooling/` 判据**按行为**钉住；RECHECK **无 `verify` 字段** ⇒ EC-02 必须绑 `slug` / `created_at` / `verify_paths` 等**结构化字段**而非散文 | cycle 1 = **EC-01**（两树入口机械化：入口 + 三条环境口径 + SOP 条款 + 反证红，一次做完；它是 EC-04 自举的**前置**） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | ACTIVE | **建档**：用户会话指令（goal 模式）授权把 GOAL-020 / GOAL-021 两次**手工补跑**的「两树同结论」推进到「**每次都必然做到**」——**只做复检过程机械化 + 判据固化 + 环境口径固化**，**不加新能力、不放宽任何判据、不改安全策略**。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA 实现、逐调用方身份、新增依赖、改既有判据 / 门禁 / 阈值、token 进任何地方、改 401 形态或 `Idempotency-Key` 语义、部署面验证、动 `undici`、改 `ADR-0031` 的 `Status`。四 EC 设计（两树机械化 / 多路证据判据 / 脚本规范 / 自举收口），budget = 20 / 120 / 2，`fix_policy` 与 `escalation_triggers` 承 GOAL-021 全套。**建档时零产品代码改动**（只增本文件）。**建档当日实测十二条事实**（见「目标与退出标准」），其中三条决定判据形态：**① `scratch/` 是 gitignored ⇒ 工具必须落 `tools/`**；**② `tools/` 逃逸 ruff / mypy / 规模门禁四道门 ⇒ 入口必须由 `tests/tooling/` 判据按行为钉住**；**③ RECHECK 无 `verify` frontmatter 字段 ⇒ 多路判据必须绑 `slug` / `created_at` / `verify_paths` 结构化字段**（否则落进 MEM-141 警告的「用文本巧合判」形态）。 |
| 2026-09-28 | ACTIVE | **建档 cycle 0 完成**，进入循环：EC-01…EC-04 全 PENDING，下一 cycle 做 **EC-01**（两树入口机械化）。**本地验证**：治理 `Cursor 治理验证通过` + `DOCS-CHECK PASS: 6` + 记录面判据 **24 passed** + 凭据四面 **offenders=0** + **as-is m0 23/23**（`PASS [` = 24、4613 passed / 21 skipped、零 `FAILED`；日志 `scratch/goal022-c0-m0-rerun.log`）。**首轮 m0 曾 22/23**：`framework/run_cursor_framework_evals` 报 `PermissionError [WinError 5]`（`hooks/common.py:161` 的 `os.replace`）⇒ 既有配方判定为**环境类 (ii)**，清残留 tmp + 单跑该 check 得 PASS + 独占重跑 ⇒ 23/23；**未改 check、未查产品代码**。**本轮修掉自己的记录措辞 1 处**（四个越级表述词用反引号仍算肯定式；`_is_quoted` 只认引号字符 ⇒ 改 `「」`）。**本条记录提交**依「固定口径」其 CI run 只在回合汇报记账（见迭代日志末行）。 |
