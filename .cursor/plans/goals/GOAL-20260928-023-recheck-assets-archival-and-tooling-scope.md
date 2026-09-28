---
id: GOAL-20260928-023
slug: recheck-assets-archival-and-tooling-scope
title: 复检资产归档化与受判面收口（收口断言集进树 + tools/ 受判面以新增判据收口 + 受判射程边界机械化）
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-28 用户会话指令（goal 模式）：**建档 GOAL-023（复检资产归档化与受判面收口）
    并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为三件事，**越界即 BLOCKED**：
    **(i) 复检资产归档化**（把「任何收口复检都要断言的那组公共事实」做成**进树、可复用**的断言集，
    使未来的收口复检**只写自己特有的断言**）、
    **(ii) `tools/` 受判面以「新增判据」形式收口**（对**被点名的**脚本集执行与产品同款的
    格式 / 类型 / 规模门）、
    **(iii) 受判射程边界机械化**（把「受判起点 + 射程外四条历史收口复检」从散文变成机械事实），
    外加 **修被新判据证明的缺陷** + **文档同源更新**（`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`
    等 + `docs/INDEX.md` 登记）。**不加新能力、不改安全策略、不放宽任何判据。**
    (1) **明确不做（命中即 BLOCKED）**：**给读面加认证**；**多租户 / RBAC / organization scope**；
    **BOLA/BFLA 实现**；**逐调用方身份**；**修改任何既有判据 / 门禁 / 阈值 / 放行面**
    （含 `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
    `test_record_face_is_covered_by_the_gate.py`、`test_declared_recheck_paths_have_evidence.py`、
    `test_recheck_script_conventions_are_pinned.py`、`test_two_tree_recheck_entry.py`、
    `test_m2_audit.py`、`tests/egress_guard.py`、`tests/tooling/test_m0_ci_coverage.py`、
    `tests/tooling/test_python_source_limits.py`）；
    **改 `PRODUCT_ROOTS`**、**改 m0 任一 check 的构成**、**改 `.github/workflows/**` 的作业结构**、
    **改 m0 条数**（终态行必须仍是 `23`）；**新增依赖**（一律标准库 + 现有栈；判据**可调用**
    既有 `ruff` / `mypy`）；**把 token 值写进任何地方**（判据一律用测试内构造的假值）；
    **改 401 响应形态或 `Idempotency-Key` 语义**；**部署面验证**（需真实环境 ⇒ 只允许
    「登记 + 可复核检查项」）；**动 `undici`**、**改 `ADR-0031` 的 `Status`**、
    **把真实 runtime 设为默认**；**宣称项目安全**（`R-M1` 仍在）；
    **把历史遗留 `tools/` 脚本纳入射程**（会把既有 73 条 lint 错误与 10 个待重排文件拉进来
    ⇒ 逼改历史资产）。
    (2) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (3) **不做真实出网**：本 GOAL **不做真实出网调用**（全离线）；SQL 一律**参数绑定**；
    凭据**只从环境变量**读取；观测隐私**不记录完整 Prompt、不记录 token**（AGENTS.md §10）；
    判据中的 token 一律用**测试内构造的假值**，**不得**把真实 token 字面量写进树。
    (4) **边界**：GOAL-001…022 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-018 的**全部 13 项 `D-NN`** 已结清、
    **本 GOAL 不重开**；GOAL-019 / 020 / 021 / 022 的**未覆盖范围原样保留**。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    把 GOAL-022 收口时**如实登记的三条决策-free 缺口**收口：
    **① 收口断言集进树**（`W-3`：GOAL-022 的 12 条收口断言落在 gitignored 的 `scratch/`
    ⇒ **可复跑但不可归档**，他人 clone 后无法直接复核）、
    **② `tools/` 的「自愿纪律」升级为机械判据**（`W-1` / `W-4`：入口无格式 / 类型 / 规模门）、
    **③ 受判射程边界机械化**（`RECHECK-218` 的 `W-1`：四条历史收口复检在射程外，目前只是散文）。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**不修改任何既有判据**
    （只**新增**判据）；**零**新依赖；**零**策略面 allow；**不得**给读面加认证；
    **不得**改 401 形态或 `Idempotency-Key` 语义；**不得**宣称项目安全（`R-M1` 仍在）；
    **不得**把 `tools/` 纳入 `PRODUCT_ROOTS`（那属另行授权）；m0 条数**仍是 23**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **标准收口断言集进树**（收 `RECHECK-20260928-218` 的 `W-3`）：把「任何 GOAL 的收口复检
      都要断言的**那一组公共事实**」做成**进树、可复用**的断言集，使未来的收口复检**只写自己
      特有的断言**，公共面不再各写一遍。四条各自可判：
      **(a) 进树**：断言集落在 `tools/closeout_recheck_assertions.py`（落点与既有入口**同目录**；
      `scratch/` 在 `.gitignore` 里 ⇒ 放那里**不算交付**）；标准库；`--root` 参数化；
      `--verdict-only` 模式；**判词纯**（只 `PASS` / `FAIL` 行）且**路径无关**（不含任一棵树的
      绝对路径）——这三条即规范页的既有环境口径。
      **(b) 两树实跑各留档**：用入口 `tools/two_tree_recheck.py` 对「当前树 + 干净 checkout」
      跑**同一份断言集字节**（`--script-mode tree`：断言集在树 ⇒ 两棵树各取自己 checkout 里的
      同一份字节），两路判词**各自落盘** + `sha256` + `cmp`。
      **(c) 规范页点名它**：`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` 的条款小节
      **必须点名该断言集文件**，且**条款不得悬空** —— 由判据断言**被点名的文件存在**
      （按**文件面 / AST** 判：被点名的模块必须真的定义公开入口，**不是**按散文判）。
      **(d) 反证**：抽走 / 改名该断言集 ⇒ 判据**判红**；**逐字节复原**（raw `sha256`）⇒ 绿。
      **(e) 跨提交形态实测**（承 `W-2`）：用入口的 `--base-ref` 指向**非 HEAD** 的提交跑同一
      断言集，**如实登记**观察到的形态（入口必须如实报 `DIFF` / `NOT-GREEN`，**不得**归一化）。
      这一项**只作形态实测与登记**，**不作**「必须一致」的判据。
    verify: >-
      ① 断言集在树：`tools/closeout_recheck_assertions.py`（且其判据在树、
      落在 `tests/**` ⇒ m0 条数**仍为 23**）；
      ② 两树实跑留档（判词文件 + `sha256` + `cmp`，入口退出码 = `0`）；
      ③ 规范页条款小节点名该文件，判据按文件面 / AST 复核（改名即判红）；
      ④ 按压：抽走 / 改名 ⇒ 判红；raw `sha256` 逐字节复原 ⇒ 绿；
      ⑤ 跨提交形态**如实登记**（含入口原样报出的 `DIFF` / `NOT-GREEN` 行）。
    status: PASS
  - id: EC-02
    criterion: >-
      **`tools/` 受判面收口**（收 GOAL-022 EC-01 的 `W-1`：入口无格式 / 类型 / 规模门）。
      **形式必须是「新增判据」**，**不得**改 `PRODUCT_ROOTS` / 任何既有 check / 作业结构 / m0 条数。
      **(a) 与产品同款的检查**：新判据对**被点名脚本集**逐个执行 —— `ruff format --check`、
      `ruff check`（既有配置已含 `max-complexity = 10` 与 `line-length = 100`）、
      **函数 ≤ 50 行**与**文件 ≤ 450 行**（计数口径照既有规模门：函数 = `end_lineno - lineno + 1`，
      文件 = `len(text.splitlines())`）、以及**既有解释器下的 `mypy`**。
      `mypy` 在本机对被测脚本**可稳定机械执行**（已实测 `Success: no issues found`）⇒
      **必须**机械执行；若将来某脚本不能稳定执行，**逐条登记原因**，**不得**假绿。
      **(b) 射程有界**：射程 = 判据源码里**固化的必备清单**（至少含 `tools/two_tree_recheck.py`
      与 EC-01 的断言集）**加**规范页点名的文件；**不得**用「扫整个 `tools/`」——
      实测 `tools/` 既有 `ruff check` **73 条**错误、`ruff format --check` **10 个文件**待重排，
      属历史遗留资产；历史遗留以**清单 + 理由**登记（不纳入射程），清单增删须**显式**；
      **只靠文档取射程会被改文案绕过**（承 MEM-141）⇒ 必备清单**必须写在判据源码里**。
      **(c) 首个受判对象现在就是红的**（**必须实测复核**）：建档时已实测入口
      `tools/two_tree_recheck.py` 的 `main` = **53 行 > 50**、`ruff check` 报
      `complex-structure: main is too complex (14 > 10)` ⇒ 本 EC **第一步是修入口**
      （重构 `main`；**不得**改既有行为判据的断言迁就；`tests/tooling/test_two_tree_recheck_entry.py`
      的 **11 例必须保持全绿**）⇒ 判据拿到「**真红 → 绿**」，而不是「受判集合为空」的空真（承 MEM-156）。
      **(d) 反证**：把入口去格式化 / 重新引入复杂度 / 把某函数撑过 50 行 ⇒ 判据**判红**；
      逐字节复原（raw `sha256`）⇒ 绿。
      **注意**：新判据自身落在 `tests/**` ⇒ 受既有 50/450 门与格式门约束，**必须自洽通过**。
    verify: >-
      ① 新判据在树（`tests/tooling/` 或 `tests/architecture/python/`）且落在 m0 的 `python/tests`
      收集面内 ⇒ m0 条数**仍为 23**；
      ② **真红取证**：交付**之前**实测入口 `main` = 53 行 + `ruff check` 报复杂度 14 > 10
      （判据会对它判红）；修入口后判据**转绿**；
      ③ 入口的既有行为判据 **11 例全绿**（**未改**其断言）；
      ④ 按压矩阵：去格式化 / 复杂度 / 超长函数三项**各自**判红，raw `sha256` 复原 ⇒ 绿；
      ⑤ 历史遗留清单**显式**（逐条理由），射程内外可区分。
    status: PASS
  - id: EC-03
    criterion: >-
      **受判射程边界机械化**（收 `RECHECK-20260928-218` 的 `W-1`）：把「既有判据
      `tests/architecture/python/test_declared_recheck_paths_have_evidence.py` 的受判起点 =
      **2026-09-28**，射程外 = **四条历史收口复检**（`goal-018` / `goal-019` / `goal-020` /
      `goal-021` 的 `closeout-recheck`）」从**散文**变成**可复核的机械事实**。
      **必须用「新增判据」实现；不得修改既有那条判据。**
      **(a)** 新判据输出并断言：**受判起点**、**射程外清单**（**逐条点名四个 slug**）、
      **射程内计数**（下界 ≥ 1 且与清单互斥）。
      **(b) 反证两向**：① 把一条**新**收口复检的 `created_at` 回填到**起点之前** ⇒ **判红**
      （防「backdate 逃逸」）；② 把一条**历史**记录改成**在射程内** ⇒ **判红**（防「回填历史」）。
      两次均**逐字节复原**（raw `sha256`）⇒ 绿。
      **(c)** 明确登记该判据**不**判「射程内记录的实质质量」，只判**边界本身**。
    verify: >-
      ① 新判据在树且落在 m0 的 `python/tests` 收集面内 ⇒ m0 条数**仍为 23**；
      ② 判据输出含受判起点 + 四个射程外 slug + 射程内计数；
      ③ 反证两向各判红一次，raw `sha256` 逐字节复原 ⇒ 绿；
      ④ 既有那条判据**零改动**（逐字节）。
    status: PASS
  - id: EC-04
    criterion: >-
      **自举收口复检 + 残余登记**：
      ① 用 `tools/two_tree_recheck.py` 对**当前树**与**干净 checkout** 跑**本轮自己的收口复检**
      （**必须**用 EC-01 的标准断言集 + **本轮特有**断言）⇒ 两树同结论（逐行相同 + `sha256` 相同）；
      ② **as-is 本机 m0 到 23/23**（`PASS: profile=m0; 23 deterministic checks`），且
      **运行发生在记录写入之后**（承 MEM-145）；
      ③ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
      ④ **CI 台账到终态**（M0 八 job + CodeQL，含 `run_attempt`）；
      ⑤ 承继残余逐条在位（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`），并**新增**登记本轮收口后的剩余：
      「历史遗留 `tools/` 脚本仍不受任何判据覆盖」（收口需另行授权）、
      「射程外四条历史收口复检仍不可回填」、「断言集可复跑性 ≠ 跨平台复验」；
      ⑥ **未覆盖范围逐条明写**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      **`R-M1` 未收口（不得宣称项目安全）**。
    verify: >-
      ① 两树入口实跑留档（判词文件 + `sha256` + 入口退出码 = `0`），且断言集**在树**
      （不是 `scratch/` 探针 —— 这正是 `W-3` 的收口面）；
      ② m0 日志留档含终态行 + 零 `FAILED` / `ERROR`，其文件时刻**晚于**记录写入时刻；
      ③ `validate.py` 输出治理通过；
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
      **修改任何既有判据 / 门禁 / 阈值 / 放行面**（含
      `test_control_plane_auth_same_source.py`、`test_reproducibility_wording.py`、
      `test_record_face_is_covered_by_the_gate.py`、
      `test_declared_recheck_paths_have_evidence.py`、
      `test_recheck_script_conventions_are_pinned.py`、`test_two_tree_recheck_entry.py`、
      `test_m2_audit.py`、`tests/egress_guard.py`、`tests/tooling/test_m0_ci_coverage.py`、
      `tests/tooling/test_python_source_limits.py`）——
      **只允许新增判据**；也**不得**改 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 里被
      `test_record_face_is_covered_by_the_gate.py` 点名的那一节
    - >-
      **改 `PRODUCT_ROOTS`**（把 `tools` 纳入其中）、**改 m0 条数**（终态行必须仍是 `23`）、
      或改 `.github/workflows/**` 的**作业结构** / m0 任一 check 的构成
    - >-
      把**历史遗留 `tools/` 脚本纳入射程**，然后**为使其变绿而改历史资产**
      （会把既有 73 条 lint 错误与 10 个待重排文件拉进来）
    - >-
      **给读面（GET/HEAD）加认证**，或改动读面放行语义（GOAL-019 判词 (i) 不变：
      保护范围只有写面）
    - >-
      引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容
      （含给 `Principal` 加租户 / 角色字段）；或做 **BOLA / BFLA 的专项实现**
    - >-
      新增**任何**依赖（含为判据引入第三方库；一律标准库 + 现有栈；
      判据**可调用**既有 `ruff` / `mypy`）
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
      改 `tests/architecture/python/test_recheck_script_conventions_are_pinned.py` 的
      **条款映射 / 被点名判据集合 / 结构性锚点**使其通过（EC-01(c) 需要规范页
      **增补**一次点名 ⇒ 若该既有判据因此判红，**正确处置是让规范页的增补满足它**，
      **不是**改它）
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
    **新增依赖** —— **立即 BLOCKED**（判据只能用标准库 + 既有 `ruff` / `mypy`）
  - >-
    **把 token 写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 / 夹具 / 示例 / 前端源码 /
    playwright 配置 / **判据源码**）—— **立即 BLOCKED**；明文凭据泄露（即使可弃用）
    ⇒ 立即停止并报告
  - >-
    **改认证的 401 响应形态**，或改 `Idempotency-Key` 语义 —— **立即 BLOCKED**
  - >-
    **放宽 / 削弱任一既有判据 / 门禁 / 阈值 / 放行面**，或**修改**任何既有判据
    （**新增**判据不受此限）—— **立即 BLOCKED**
  - >-
    **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**（含把 `tools` 纳入 `PRODUCT_ROOTS`；
    `23` 这一终态条数）—— **立即 BLOCKED**（把 `tools/` 纳入 `PRODUCT_ROOTS` 属**另行授权**）
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
child_plans:
  - .cursor/plans/tasks/PLAN-20260928-219-goal-023-ec01-standard-closeout-assertions-in-tree.md
  - .cursor/plans/tasks/PLAN-20260928-221-goal-023-ec02-tooling-scripts-meet-product-gates.md
  - .cursor/plans/tasks/PLAN-20260928-223-goal-023-ec03-recheck-scope-boundary-is-mechanical.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-224-goal-023-ec03-recheck-scope-boundary.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-157-a-naming-can-be-satisfied-twice-inside-one-section.md
  - .cursor/memory/entries/MEM-20260928-158-bounded-scope-must-be-partitioned-explicitly.md
  - .cursor/memory/entries/MEM-20260928-159-mechanizing-a-scope-claim-needs-two-way-reverse-proof.md
---

## 目标与退出标准

**一句话**：把 GOAL-022 收口时**如实登记的三条决策-free 缺口**收口 ——
**断言集进树**（`W-3`）、**`tools/` 受判面机械化**（`W-1` / `W-4`）、**受判射程边界机械化**
（`RECHECK-218` 的 `W-1`）。

**本 GOAL 不加新能力、不改安全策略、不放宽任何判据、不修改任何既有判据。**
若新判据**证明**某处是真缺陷 ⇒ 在授权范围内修（本轮**预期命中一个**：入口自身的规模 / 复杂度）；
若某条**本机无法验证** ⇒ **登记为 PENDING**，**不得**记 PASS。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **标准收口断言集进树**（可复用 + 两树留档 + 规范页点名 + 反证 + 跨提交登记） | `tools/closeout_recheck_assertions.py` + 判据 + 规范页点名 + 两树留档 | **PENDING** |
| EC-02 | **`tools/` 受判面收口**（新增判据：格式 / lint / 类型 / 规模；含修入口） | 新判据 + 入口 `main` 重构 + 按压矩阵 | **PENDING** |
| EC-03 | **受判射程边界机械化**（起点 + 射程外四条 + 射程内计数；**新增**判据） | 新判据 + 反证两向 | **PENDING** |
| EC-04 | **自举收口复检 + 残余登记**（用 EC-01 断言集 + 本轮特有断言做两树） | 两树留档 + m0 日志 + 台账 + 残余逐条 | **PENDING** |

**依赖关系**：EC-01 → EC-02（EC-02 的必备清单含 EC-01 的断言集文件）→ EC-03（独立于 EC-01/02，
但同一「判据形态」族）→ EC-04（**依赖 EC-01 + EC-02**：必须**用**建好的断言集与**已被门约束的**入口
做本轮自己的收口复检）。EC-04 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **`EC-02` 的首个受判对象确实是红的（实测复核，非推测）**：
   `tools/two_tree_recheck.py` 的 `main` = **53 行**（口径 `end_lineno - lineno + 1`，AST 实测）；
   `ruff check tools/two_tree_recheck.py` ⇒ `complex-structure: main is too complex (14 > 10)`，
   **退出码 1**；`ruff format --check` 该文件**当前干净**（已格式化）。
   ⇒ 本 EC **第一步是修入口**，判据因此拿到「**真红 → 绿**」，而不是 MEM-156 警告的空真。
2. **`mypy` 可稳定机械执行（实测）**：`mypy tools/two_tree_recheck.py` ⇒
   `Success: no issues found in 1 source file`（`pyproject.toml` 的 `[tool.mypy]` 是
   `strict = true`；`files` 列表**不含** `tools`，但**显式传路径**即按该配置检查）。
   ⇒ EC-02 的 (a) 项**必须**机械执行 `mypy`，**没有**「不能稳定执行」的豁免理由。
3. **`tools/` 的既有存量（实测）**：`ruff check tools/` ⇒ **73 条**错误；
   `ruff format --check tools/` ⇒ **10 个文件**待重排 / 30 个已格式化。
   ⇒ 射程**不得**是「扫整个 `tools/`」（会把历史资产拉进来）；必须**有界清单**。
4. **既有 ruff 配置（实测，`pyproject.toml`）**：`line-length = 100`、
   `select = ["E4","E7","E9","E501","F","I","C90","PLR0913","PLR1702"]`、
   `max-complexity = 10`（`[tool.ruff.lint.mccabe]`）、`max-args = 5`、`max-nested-blocks = 4`。
   ⇒ EC-02 的「与产品同款」= **同一份 `pyproject.toml` 配置**，判据只传路径。
5. **规模门的既有计数口径（实测，`tests/tooling/test_python_source_limits.py`）**：
   文件 = `len(path.read_text(encoding="utf-8").splitlines())`（上限 **450**，> 300 软告警）；
   函数 = `node.end_lineno - node.lineno + 1`（上限 **50**）；`PRODUCT_ROOTS =
   ("apps", "services", "packages", "adapters", "tests")` —— **不含 `tools`**。
6. **`m0 = 23` 是硬编码在三处的**（`tools/quarantine_and_run_m0.py`、
   `tools/classify_local_gate_reds.py`、`docs/architecture/LOCAL_GATE_PROTOCOL.md`）；
   新增判据**只能落 `tests/**`**（`python/tests` check 收集 `tests/` 全树）⇒ m0 仍是 23。
7. **射程外清单是四个确定 slug（实测）**：`.cursor/plans/rechecks/` 下 `slug` 以
   `closeout-recheck` 结尾者共 **5** 条 —— `RECHECK-20260926-189-goal-018-closeout-recheck`、
   `-195-goal-019`、`-200-goal-020`、`-210-goal-021`（**射程外 4 条**）与
   `-218-goal-022`（**射程内 1 条**）。受判起点 = **2026-09-28**（`CUTOFF`，既有判据的 `date(2026, 9, 28)`）。
8. **既有的 12 条收口断言埋在 gitignored 的 `scratch/`**（`W-3` 的实证）：
   `scratch/goal022-ec04-closeout-recheck.py` 仍在本机，但**不在 git 里** ⇒ 他人 clone 后
   **无法直接复核**那 12 条判词。EC-01 就是把它**一般化 + 进树**。
9. **`tools/` 里已有「GOAL 专属 tracked 收口验证器」先例**：`tools/verify_goal015_closeout.py`
   （205 行，没被任何门覆盖）⇒ EC-04 沿用该形态（`tools/verify_goal023_closeout.py`），
   并把它**纳入 EC-02 的判据清单**（即「先例」与「新交付」都被同一个门覆盖）。
10. **既有入口的 `--script-mode`**：`tree` 模式把脚本**相对每棵树根**解析 ⇒
    **断言集进树后**，`tree` 模式即可保证「两树用同一份断言集字节」，
    不需要 `shared` 模式（后者是为 `scratch/` 探针准备的）。
11. **话术判据的扫描面含 `.cursor/plans`**（`_SCAN_ROOTS`；`scratch` 在 `_SKIP_DIRS`）⇒
    本文件与后续记录**不得**出现**肯定式**的「完全可复现」/「完全模型可复现」/
    「fully reproducible」/「fully model-reproducible」这四条越级表述
    （口径词是「**可重复配置**」）。该判据认的是 `「」` / `"` 这类**引号字符**
    （`_is_quoted` 看相邻字符），**反引号不算引用**（承 `MEM-20260928-154`）。
12. **规范页的既有判据会被 EC-01(c) 触碰**：`test_recheck_script_conventions_are_pinned.py`
    按**小节标题字面 + 结构签名**钉住规范页 ⇒ 增补内容时**必须保持既有小节标题与
    结构性锚点不变**；若它因增补判红，**正确处置是让规范页的增补满足它**，
    **不是**改它（`fix_policy.forbidden` 已点名）。
13. **进程卫生（承 GOAL-020 的 96 孤儿教训）**：两树入口会起子进程；
    teardown 必须连**整棵树**（Windows 用 `taskkill /T /F`）；跑完复验**零泄漏**。
14. **逐字节复原的证据必须是 raw `sha256`**（承 MEM-152）：`git diff` 会因
    `.gitattributes` 归一化掩盖行尾变化 ⇒ **不得**用 `git diff` 充当逐字节证据；
    按压 / 复原**一律用 Edit 工具**（Bash 写源码会被 Mimosa 拦截）。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-023-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-023**」（**不是**把 GOAL-022 置回 ACTIVE）。
理由：那三条缺口都是 GOAL-022 **收口时如实登记**的**新交付面**（把落在 `scratch/` 的断言集
**进树**、把 `tools/` 的**自愿纪律**变成**机械判据**、把射程边界从**散文**变成**机械事实**），
与 GOAL-022 的「复检过程机械化」**不重叠**；且 GOAL-022 已 ACHIEVED 收口。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260928-023` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件**——**新判据与新工具脚本同样自愿遵守**）；
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

- **受判对象必须非空（承 MEM-156）**：EC-02 的判据**必须在交付当轮就抓到入口的真实红
  并修掉**；交付时**不得**出现「受判集合为空」的空真。若某项检查无法机械执行
  ⇒ **逐条登记原因**，**不得**假绿。
- **逐字节复原的证据必须是 raw `sha256`**（承 MEM-152）：**不得**用 `git diff` 充当；
  按压 / 复原**一律用 Edit 工具**（`fix_policy.forbidden` 已含「Bash 写源码」的既有约束）。
- **判据自身恒真（承 MEM-141）**：新判据**不得**被文档引用 / 字面量喂饱——射程来自
  **判据源码里固化的必备清单** + **规范页点名**（且**被点名的文件必须真的存在**，
  按**文件面 / AST** 判，**不**按散文判），且**必须被按压过**（先红后绿 + 逐字节复原）。
- **改工具先数夹具**：入口被 `tests/tooling/test_two_tree_recheck_entry.py`（**11 例**）
  按行为钉住 ⇒ 重构 `main` 后**必须全绿**；行为判据的断言**不得**为迁就实现而改。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧复验**
  （由 CI 承担；本地按同一形态自查）。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」
  （写下门日志本身也是记录）⇒ 本地门跑在「当时记录已写完」的状态，
  **记录面的最终覆盖由 CI 承担**；**不得**为此无限回退。
- **批量推送（承 MEM：`cancel-in-progress`）**：一个 cycle 攒成**一次**推送，
  避免取消在飞的 M0 run；被取消的 run **如实记 `cancelled`**。

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
  本 GOAL 的收口判词**必须**写明：**① 断言集进树与两树实跑证据**、
  **② EC-02 的首个真实受判对象（入口自身的红）与修复证据**、
  **③ 按压与逐字节复原记录**、**④ 受判射程边界（起点 + 四条 + 计数）**、
  **⑤ as-is 本机 m0 的终态行**、**⑥ 未覆盖范围**、**⑦ 新增残余登记**。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **做 BOLA·BFLA 实现**、**新增依赖**、**把 token 写进任何地方**、**改 401 形态或
  `Idempotency-Key` 语义**、**放宽或修改任何既有判据 / 门禁 / 阈值**、
  **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**、**放宽 §9 默认 deny**、**宣称项目安全**、
  **Canonical State 边界**、**真实 runtime 设为默认**）、
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
**已实施 9 项**、**部分实施 1 项**（`D-03`：`undici` 已调研未升）、
**已拍板为维持现状 3 项**、**未授权待拍板 0 项**。⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019 / 020 / 021 / 022 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（本 GOAL 不碰认证面） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留** |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **原样保留**（本轮**不**把它变成已验证） |
| `W-4` / `W-5` / `W-6` | 本机 m0 同进程跑阈值判据 / 新作业多一次冷装 / `live_run_support.py` 零余量 | **原样保留** |
| `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` | Mimosa 结论未完整 / `undici` 归上游 / 非 ASCII 路径豁免 / 主观面先操作化 / 规模不足的诚实边界 | **原样保留** |
| `W-3`（GOAL-022） | 收口断言集落在 gitignored 的 `scratch/` ⇒ 可复跑**不可归档** | **本 GOAL 的动因**：由 **EC-01** 收口 |
| `W-1` / `W-4`（GOAL-022） | `tools/` **不在** `PRODUCT_ROOTS` ⇒ 入口不被 ruff / mypy / 规模门覆盖 | **本 GOAL 的动因**：由 **EC-02** 以**新增判据**形式**部分**收口 —— **注意** `PRODUCT_ROOTS` 本身**仍不动**，所以这是「**有界射程里有机器门**」，**不是**「`tools/` 已被门覆盖」 |
| `W-1`（RECHECK-218） | 四条历史收口复检在**射程外**，目前只是散文 | **本 GOAL 的动因**：由 **EC-03** 机械化 |
| `W-2`（RECHECK-218） | 两树比的是**同 tip** ⇒ 不证明跨提交 / 跨平台 | **EC-01(e) 做形态实测与登记**；**不作**「必须一致」的判据；跨平台面**原样保留**未复验 |

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

1. **读面认证（GET / HEAD）**——**不做**（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
2. **多租户隔离 / organization scope**——**不做**（M18）；
3. **RBAC / 角色 / 权限矩阵**——**不做**；
4. **BOLA / BFLA 的专项实现**——**不做**（仍归 M18 / 另行授权；**如实保留**）；
5. **逐调用方身份**（caller-declared identity）——**不做**（单 token ⇒ 单主体）；
6. **新增依赖**——**不做**（一律标准库 + 现有栈；判据**可调用**既有 `ruff` / `mypy`）；
7. **修改任何既有判据 / 门禁 / 阈值 / 放行面**——**不做**（列出见 `fix_policy.forbidden`）；
   **新增**判据**可以**；也**不得**改 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 里被
   `test_record_face_is_covered_by_the_gate.py` 点名的那一节；
8. **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**——**不做**（把 `tools/` 纳入 `PRODUCT_ROOTS`
   属**另行授权**）；
9. **改 `Idempotency-Key` 语义**——**不做**；
10. **改认证的 401 响应形态**——**不做**；
11. **把 token 值写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出 / 前端源码 /
    判据源码**——**不做**（**只登记变量名**，**绝不留值**）；判据一律用**测试内构造的合成假值**；
12. **部署面验证**（需真实环境）——**只允许**「登记为不可在本机验证 + 给出可复核检查项」；
13. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
14. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
15. **`undici` 的 pin**——**不动**（归属上游，见 D-03 终态）；
16. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**；
17. **把新判据写成「被文档引用 / 字面量喂饱」的形态**——**不做**（承 MEM-141）；
    新判据**必须**绑声明行 / 行为 / **文件面**，且**必须被按压过**；
18. **把历史遗留 `tools/` 脚本纳入射程**——**不做**（会把既有 73 条 lint 错误与
    10 个待重排文件拉进来 ⇒ 逼改历史资产）；
19. **宣称项目安全**（`R-M1` 仍在）——**不做**。

**承继的诚实边界（如实保留，不是待办）**：

- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（且**不得**用「受判面已收口」替代它 —— **有机器门 ≠ 项目安全**）。
- **`R-D1`｜Dependabot 告警**——`yaml` 已升、`vite` 已清；**`undici` 8 条原样保留**，
  **归属上游**。**本 GOAL 不动它**。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，**原样保留**。
- **`R-F1`｜收敛 / 一致性判定含主观面时必须先操作化**——**原样保留**。
- **`R-F2`｜真实数据 / 调用规模不足时的诚实边界**——**原样保留**。
- **`W-4` / `W-5` / `W-6`**——**原样保留**；`W-6` 是**规模门禁的零余量告警**：
  本 GOAL 若需改 `tests/e2e/live_run_support.py` **必须先搬代码**。
- **`D-04` 的重启前置**——**先修误报面**；**本 GOAL 不安装检测层、不改 hook 面、
  不改 `MIMOSA_GIT_GATE_MODE`**。

**本 GOAL 交付的是「复检资产的归档化 + 有界受判面 + 射程边界的机械化」，不是「判据更强」**：

- EC-02 让**被点名的** `tools/` 脚本**也有**格式 / 类型 / 规模门 —— 它**不**扩大保护面到
  历史遗留脚本，也**不**改 `PRODUCT_ROOTS`；
- EC-03 **只判边界本身**（起点 / 射程外清单 / 计数），**不判**射程内记录的**实质质量**；
- EC-01 让收口断言集**可归档**，但「**断言集完备**」仍不被任何判据覆盖（原样保留）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 本行所在的**建档提交** | **治理** `validate.py` = `Cursor 治理验证通过`（8 行结论，含「GOAL 循环记录结构合规；push 授权显式登记」）；**记录面判据**（`test_reproducibility_wording.py` + `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）= **24 passed**（与 GOAL-022 基线同值）；**as-is 本机 m0（记录写完之后、独占运行、仓库 `.venv`、DSN 固化）= `PASS: profile=m0; 23 deterministic checks`**，`PASS [` = **24**、**4642 passed**、零 `FAILED` / `ERROR`（日志 `scratch/goal023-c0-m0.log`，**文件时刻 `12:45:16` 晚于**本文件建档写入时刻 `12:27:39` ⇒ 门在记录之后，可用 `ls -l` 复核）；**进程卫生**：跑完后 `tasklist` python 进程 **0**。**本机无 `make`** ⇒ 用 Makefile 的同一命令直跑 `run_all_checks.py --profile m0 --keep-going`（同解释器、同 DSN 固化、同 `--keep-going`，与 canonical 调用等价）。 | 本行所在的**建档提交**（依固定口径其 CI run 只在回合汇报记账） | 建档轮**零产品代码改动**（只新增本文件） | EC-01…EC-04 全 PENDING。起点已定位：`tools/` 射程**必须有界**（既有 73 条 lint 错误 / 10 个待重排文件）；`mypy` **可机械执行**（实测）⇒ 无豁免理由 | cycle 1 = **EC-01**（标准收口断言集进树；它是 EC-02 必备清单的前置） |
| 1 | PLAN-20260928-219（EC-01） | `743297d`（断言集）+ `da6e904`（判据）+ `a895093`（规范页小节）+ 本行所在的**记录提交** | **EC-01 六条验收全部成立且有实跑证据**。交付 = `tools/closeout_recheck_assertions.py`（**388 行 / 18 条公共判词**）+ 判据 `tests/tooling/test_closeout_assertions_are_in_tree.py`（**145 行 / 6 例**）+ 规范页 `## 标准收口断言集` 小节 + `RECHECK-20260928-220`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260928-157`。**① 两树同结论（`--script-mode tree` ⇒ 两树各取自己 checkout 里的同一份断言集字节）**：18 条判词**逐行相同**、`sha256` **同为** `b6ae3dac32b8ed54905b81a65605a71ebddea8d8599146f1c517e1f15597a0e5`、两路各自落盘且 `cmp` **一致**、`TWO-TREE PASS` / `EXIT=0`；落档 `scratch/goal023-ec01-verdict-{current,clean}.txt`、运行记录 `scratch/goal023-ec01-two-tree.log`。**② 规范页点名且条款不悬空**：小节点名断言集与其判据；判据按 **AST** 复核被点名文件真的声明 `standard_verdicts`。**③ 按压两处 + 逐字节复原**：① 公开入口 `standard_verdicts` **改名** ⇒ **`3 failed, 3 passed`**；② 小节点名**两处**全抽走 ⇒ **`2 failed, 4 passed`**（**注意：第一次只抽一处 ⇒ `6 passed`，按压无效 —— 谓词说「存在一处」，按压就得让所有出现消失；教训已沉淀 `MEM-20260928-157`**）；两次 raw `sha256` **逐字节复原**（`dc18919b…` / `5ec43a99…`）⇒ 复绿。**④ 空树不空转（承 MEM-156）**：判据在空树上要求 **≥ 5 条判红**且退出码非 `0`。**⑤ 跨提交形态实测（承 `W-2`，只作登记）**：`--base-ref 743297d`（**非 HEAD**，那棵树上还没判据与规范页小节）⇒ 干净树 `exit=1`、`sha256=09f01ace…`、`COMPARE identical=False`、**3 条 `DIFF`**、**2 条 `NOT-GREEN`**、`TWO-TREE RED` / `EXIT=1` —— **入口原样报出，未归一化**。**自查全绿**：`ruff check` + `ruff format --check` + `mypy`（`strict`）；388 / 145 行、无超 50 行函数；定向套件 **32 passed**（新 6 + 入口 11 + 规范钉条款 6 + 多路证据 9）。**零产品代码改动、零既有判据改动、零依赖**；**m0 条数仍 23**（断言集自跑的第 5 条判词就由**门运行器自己算出 23**）。**as-is 本机 m0（记录写完之后、独占、仓库 `.venv`、DSN 固化）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4649 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c1-m0.log`，文件时刻 `13:24:29` **晚于**记录写入 `13:07:28` ⇒ 门在记录之后；进程卫生零泄漏）。用例数较交付前 **+7** = 新判据 6 例 + 新文件进入既有规模门判据的参数化面 1 项。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账）；`743297d` / `da6e904` / `a895093` 与本行**批量一次推送** | **零真缺陷**；**按压第一次无效**已按实登记并沉淀 MEM | **EC-01 = PASS**。**如实登记五条警告**（`RECHECK-220`）：`W-1` 断言集只判**结构性事实**，不判交付物实质质量；`W-2` 两树比的是**同 tip** ⇒ 跨提交那一跑只是**形态实测**，**不是**一致性保证，跨平台**未复验**；**`W-3`（最要紧）`tools/` 仍逃脱 ruff / mypy / 规模门**（本条收的是「断言集不可归档」，**不是**「`tools/` 无机器门」——后者归 **EC-02**）；`W-4` 对**被追踪文件真实删除 / 改名**的按压未做（「抽走」由**空树**覆盖）；`W-5` 本条不含任何授权面 / 认证面新结论 | cycle 2 = **EC-02**（`tools/` 受判面以**新增判据**收口。**首个受判对象现在就红**：`tools/two_tree_recheck.py` 的 `main` = **53 行**、`ruff check` 报 `complex-structure 14 > 10` ⇒ **第一步是修入口**，且 `tests/tooling/test_two_tree_recheck_entry.py` 的 **11 例必须保持全绿**） |
| 2 | PLAN-20260928-221（EC-02） | `44bfb31`（修入口）+ `507b250`（新判据）+ `341038c`（规范页同步）+ 本行所在的**记录提交** | **EC-02 五条验收全部成立且有实跑证据**。交付 = 入口重构（`main` **53 → 21 行**、拆出 `resolve_worktree_dir` / `prepare_clean_tree` / `run_assertions` / `dump_verdicts` / `report`）+ 新判据 `tests/tooling/test_tooling_scripts_meet_product_gates.py`（**8 例**）+ 规范页同源更新 + `RECHECK-20260928-222`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260928-158`。**① 首个受判对象「真红 → 绿」（可复跑、零写盘）**：用 `git show HEAD:tools/two_tree_recheck.py \| ruff check --stdin-filename … -` 对**修复前**内容复测 ⇒ **1 条错误** `complex-structure: main is too complex (14 > 10)`、AST 超 50 行函数 `[('main', 53)]`；修复后 ⇒ `All checks passed!`、`[]`、`main` = 21 / `report` = 19。**② 既有 11 例行为判据断言一字未改且全绿**（`19 passed` = 8 新 + 11 既有）。**③ 射程有界且分类显式**：必备清单（**写在判据源码里**）∪ 规范页点名 = **2** 条；历史遗留 **37** 条**逐条带理由**；`tools/` 下 **39** 个 `.py` **全部显式分类**（无第三种状态），未分类 / 陈旧清单 / 空理由**都判红**。**④ 反证三向各自只红一道门 + 逐字节复原**：A 去格式化 ⇒ 只 `…_are_formatted` 红；B 重新引入复杂度（`report()` 9 段 if/elif ⇒ `complex-structure 14 > 10`）⇒ 只 `…_pass_ruff_check` 红；C 把 `report()` 撑到 **52 行** ⇒ 只 `…_respect_the_size_limits` 红（`ruff check` 仍绿）；三次均 raw `sha256` 回到 `1e867ea5…`。**⑤ hermetic 判据自身按压**：`tmp_path` 人造坏脚本 ⇒ 四道门**各自**报出问题（格式 / `unused-import` / `mypy` / `有超过 50 行的函数`）。**⑥ mypy 豁免关闭**：实测可稳定机械执行 ⇒ **必须**执行，**无**登记理由。**零改动面**：`PRODUCT_ROOTS` / 既有 check / 作业结构 / m0 条数（**仍 23**）/ 既有判据 / 产品代码 / 依赖**全部零改动**；新判据自洽通过既有规模与格式门。**as-is 本机 m0（记录写完之后、独占、仓库 `.venv`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4658 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c2-m0.log`，时刻 `14:02:18` 晚于记录写入 `13:50:25`；进程卫生零泄漏；用例较交付前 **+9** = 新判据 8 例 + 规模门参数化面 1 项）。**本 cycle 内另有一处自查缺陷**：新判据第一次自跑判红 `6 failed`，根因是它把规范页散文里的通配泛指 `tools/**.py` 当成真实脚本路径 ⇒ **被它自己的配对断言抓到**，修复 `c2f3330`（改按真实路径形态匹配）—— 已如实登记在 `RECHECK-222` 第六节。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账）；`44bfb31` / `507b250` / `341038c` / `c2f3330` 与本行**批量一次推送**；cycle 1 的台账见上表 `4c7db75`（M0 `36382312658` + CodeQL `36382312355`，八 job + 3/3 全 success，`run_attempt=1`） | **零真缺陷**；修掉的是**被新判据证明的**入口自身缺陷（53 行 `main` + 复杂度 14），**既有行为判据零改动** | **EC-02 = PASS**。**如实登记五条警告**（`RECHECK-222`）：**`W-1`（最要紧）射程只覆盖被点名的 2 条**，历史遗留 **37** 条 `tools/` 脚本**仍不受任何判据覆盖** ⇒ 交付的是「**有界射程里有机器门**」，**不是**「`tools/` 已被门覆盖」；`W-2` 新脚本的纳入**不是自动的**（写进 `LEGACY_OUT_OF_SCOPE` 加一行理由即可继续逃逸 ⇒ 防的是**静默**逃逸，不是「有人决定不纳入」）；`W-3` `mypy` 面用的是既有缓存（冷缓存耗时未测）、跨平台同结论**未逐条复验**；`W-4` 按压用三种**行为不变**的形态（未做「删整段逻辑」那类会与 11 例冲突的按压）；`W-5` 本条不含任何授权面 / 认证面新结论 | cycle 3 = **EC-03**（受判射程边界机械化：设判起点 = **2026-09-28**、射程外 = **四条历史收口复检**（`goal-018` / `019` / `020` / `021-closeout-recheck`）、射程内计数；**新增**判据，**不得修改**既有那条判据；反证两向：backdate 逃逸 ⇒ 判红、回填历史 ⇒ 判红） |
| 3 | PLAN-20260928-223（EC-03） | `86cffaa`（新判据）+ 本行所在的**记录提交** | **EC-03 五条验收全部成立且有实跑证据**。交付 = `tests/architecture/python/test_recheck_scope_boundary_is_mechanical.py`（**192 行 / 6 例**）+ `RECHECK-20260928-224`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260928-159`。**① 边界事实实测**：受判起点 `CUTOFF` = **2026-09-28**（读既有判据，另有一条用例断言它没漂移）、slug 约定 `closeout-recheck`、路数下界 `2`；扫描面 **5**；**射程内 1**（`RECHECK-20260928-218-goal-022-closeout-recheck.md`）；**射程外恰好 4**（`goal-018` / `019` / `020` / `021`，**逐条点名**）；两集互斥、两侧都非空。**② hermetic 反证两向**（`tmp_path` 夹具）：基线不判红；把新记录回填到 `2026-09-27` ⇒ **判红并点名**；把 `…-189-goal-018-…` 改成 `2026-09-28` ⇒ **判红并点名**。**③ 仓库级按压两向 + 逐字节复原**：`RECHECK-218` 的 `created_at` 回填 ⇒ **`2 failed, 4 passed`**，复原 raw `sha256` 回到 `b46e551f…`；`RECHECK-210` 改成射程内 ⇒ **`1 failed, 5 passed`**，复原回到 `b459e3a3…`；复原后两条判据合跑 **15 passed**、`git status --short .cursor/plans/rechecks/` **为空**（**零回填**）。**④ 交叉观察**：按压 ② 状态下**既有那条判据也同时判红** ⇒ 两条判据在「回填」形态上**结论一致**。**⑤ 「只判边界不判质量」以行为证明**：质量全坏（无 `verify_paths`）但边界正确的记录**不判红** ⇒ 不越权。**⑥ 既有判据逐字节未改**：`git diff HEAD -- tests/architecture/python/test_declared_recheck_paths_have_evidence.py` **为空**。**自查全绿**：`ruff check` + `ruff format --check` + `mypy`；192 行、无超 50 行函数。**零产品代码改动、零既有判据改动、零依赖、零历史回填**；m0 条数仍 **23**。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账）；`86cffaa` 与本行**批量一次推送**；cycle 2 的台账见上表 `6dcde26` | **零真缺陷**（本轮无产品缺陷） | **EC-03 = PASS**。**如实登记五条警告**（`RECHECK-224`）：`W-1` 期望清单是**本轮实测快照写死在源码里** ⇒ 能把**后续变化**判红，但**不**声称「所有历史收口复检已被穷尽识别」（不以 `closeout-recheck` 结尾命名的不进扫描面）；**`W-2` `created_at` 是记录自述字段** ⇒ 本判据判的是「**声明的**边界」，**不**校验日期真实性 ⇒ **过程纪律**，**不得**据此宣称「边界不可伪造」；`W-3` 只判边界，射程内记录的**实质质量**不在其断言范围内；`W-4` 只按压「改 `created_at`」一种形态（改名 / 删除会破坏扫描面）；`W-5` 本条不含任何授权面 / 认证面新结论 | cycle 4 = **EC-04**（自举收口复检 + 残余登记：**用 EC-01 的标准断言集 + 本轮特有断言**做两树复检；as-is m0 23/23 在记录之后；治理绿；CI 台账到终态；承继残余 12 个 ID + **新增三条残余登记**；未覆盖范围逐条明写） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-023 落地） | `6bf3c9c` | M0 [**36379693650**](https://github.com/Eswink/research-system-new/actions/runs/36379693650) / CodeQL [**36379695232**](https://github.com/Eswink/research-system-new/actions/runs/36379695232) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `collector-quality` / `observability-overhead-ubuntu-latest` / `eval-gate` / `quality-windows-latest` / `console-frontend` / `container-quality` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (python)` / `Analyze (javascript-typescript)` **3/3 `success`**。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ **零依赖改动**，与 GOAL-018…022 收口一致。轮询日志 `scratch/goal023-c0-ci-poll.log`（`ALL_TERMINAL sha=6bf3c9c332b8e1a42b1a0c774b4c083988ef7c20`） |
| cycle 1 实施 + 收口（EC-01：`743297d` / `da6e904` / `a895093` + 记录 `4c7db75`，批量一次推送） | `4c7db75` | M0 [**36382312658**](https://github.com/Eswink/research-system-new/actions/runs/36382312658) / CodeQL [**36382312355**](https://github.com/Eswink/research-system-new/actions/runs/36382312355) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `eval-gate` / `observability-overhead-ubuntu-latest` / `console-frontend` / `quality-ubuntu-latest` / `container-quality` / `collector-quality` / `quality-windows-latest` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (javascript-typescript)` / `Analyze (actions)` **3/3 `success`**。轮询日志 `scratch/goal023-c1-ci-poll.log`（`ALL_TERMINAL sha=4c7db75522f3990e9fbdc7deae471f63e29d24c6`） |
| cycle 2 实施 + 收口（EC-02：`44bfb31` / `507b250` / `341038c` / `c2f3330` + 记录 `6dcde26`，批量一次推送） | `6dcde26` | M0 [**36385375400**](https://github.com/Eswink/research-system-new/actions/runs/36385375400) / CodeQL [**36385374850**](https://github.com/Eswink/research-system-new/actions/runs/36385374850) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `collector-quality` / `quality-ubuntu-latest` / `console-frontend` / `eval-gate` / `container-quality` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**。轮询日志 `scratch/goal023-c2-ci-poll.log`（`ALL_TERMINAL sha=6dcde267cd1bcc46a595bb8b02fb3f0913d17b6d`） |
| 本条台账的**记录提交** | 本行所在的记录提交 | **依「固定口径」：写下某条记录的那个提交自身的 run 只在回合汇报记账**（不重复回写文件） | 见回合汇报 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | ACTIVE | **建档**：用户会话指令（goal 模式）授权把 GOAL-022 收口时**如实登记的三条决策-free 缺口**收口 —— **① 收口断言集进树**（`W-3`）、**② `tools/` 的「自愿纪律」升级为机械判据**（`W-1` / `W-4`）、**③ 受判射程边界机械化**（`RECHECK-218` 的 `W-1`）。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA 实现、逐调用方身份、修改任何既有判据 / 门禁 / 阈值、改 `PRODUCT_ROOTS` / m0 条数 / 作业结构、新增依赖、token 进任何地方、改 401 形态或 `Idempotency-Key` 语义、部署面验证、动 `undici`、改 `ADR-0031` 的 `Status`、把历史遗留 `tools/` 脚本纳入射程、宣称项目安全。四 EC 设计（断言集进树 / 受判面收口 / 射程边界 / 自举收口），budget = 20 / 120 / 2。**建档当日实测十四条事实**（见「目标与退出标准」），其中三条决定判据形态：**① 入口 `main` = 53 行 + `ruff check` 复杂度 14 > 10 ⇒ EC-02 的首个受判对象现在就红**（真红 → 绿的取证不是空真）；**② `mypy` 对被测脚本可稳定机械执行 ⇒ 无豁免理由**；**③ `tools/` 既有 73 条 lint 错误 + 10 个待重排文件 ⇒ 射程必须有界（固化清单 + 规范页点名），不得整目录扫**。**建档时零产品代码改动**（只增本文件）。 |
| 2026-09-28 | ACTIVE | **建档 cycle 0 完成**，进入循环：EC-01…EC-04 全 PENDING，下一 cycle 做 **EC-01**（标准收口断言集进树）。**本地验证**：治理 `Cursor 治理验证通过` + 记录面判据 **24 passed** + **as-is m0 23/23**（`PASS [` = 24、4642 passed、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c0-m0.log`，其文件时刻**晚于**建档写入时刻 ⇒ 门在记录之后）；进程卫生零泄漏。**本机无 `make`** ⇒ 直跑 `run_all_checks.py --profile m0 --keep-going`（canonical 等价）。**本条记录提交**依「固定口径」其 CI run 只在回合汇报记账（见迭代日志末行）。 |
| 2026-09-28 | ACTIVE | cycle 1（PLAN-20260928-219）：**EC-01 = PASS**（标准收口断言集进树）。交付 = `tools/closeout_recheck_assertions.py`（388 行 / **18 条公共判词**）+ 判据（145 行 / **6 例**）+ 规范页 `## 标准收口断言集` 小节 + `RECHECK-20260928-220` + `MEM-20260928-157`。**两树实跑**（`--script-mode tree`）⇒ 18 条判词逐行相同、`sha256` 同为 `b6ae3dac…`、两路落档 `cmp` 一致、`TWO-TREE PASS` / `EXIT=0`。**跨提交形态实测**（`--base-ref 743297d`，非 HEAD）⇒ `COMPARE identical=False` + **3 条 `DIFF`** + **2 条 `NOT-GREEN`** + `TWO-TREE RED` / `EXIT=1`，**原样报出未归一化**。**按压两处逐字节复原**（`dc18919b…` / `5ec43a99…`）；**第一次按压无效**（只抽一处点名仍 `6 passed`）已如实登记，教训 = **谓词说「存在一处」，按压就得让所有出现消失**（`MEM-20260928-157`）。**空树不空转**（≥ 5 条判红 + 退出码非 0）。**零产品代码改动、零既有判据改动、零依赖**；m0 条数仍 23（断言集自己算出）。**as-is 本机 m0（记录写完之后、独占）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、4649 passed / 21 skipped、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c1-m0.log` 时刻晚于记录写入）；治理绿。**本 cycle 的 CI 到终态**：M0 `36382312658` 八 job 全 success + CodeQL `36382312355` 3/3，两者 `run_attempt=1`。 |
| 2026-09-28 | ACTIVE | cycle 2（PLAN-20260928-221）：**EC-02 = PASS**（`tools/` 受判面以新增判据收口）。**首个受判对象是真的红的，且已修掉**：入口 `main` = **53 行**、`ruff check` 报 `complex-structure 14 > 10`（用 `--stdin-filename` 对修复前内容复测 ⇒ 可复跑、零写盘）⇒ `main` → **21 行**（拆出 5 个助手），既有 **11 例行为判据断言一字未改且全绿**。新判据 **8 例**：四道门（`ruff format --check` / `ruff check` / 规模 / `mypy`）对**有界射程**（必备清单 ∪ 规范页点名 = **2** 条）执行；历史遗留 **37** 条逐条带理由；`tools/` 下 **39** 个 `.py` **全部显式分类**（未分类 / 陈旧 / 空理由都判红）。**反证三向各自只红一道门**（去格式化 / 重新引入复杂度 / 函数撑到 52 行）且 raw `sha256` 逐字节复原（`1e867ea5…`）；另有一条 hermetic 四门检测。**零改动面**：`PRODUCT_ROOTS` / 既有 check / 作业结构 / **m0 条数仍 23** / 既有判据 / 产品代码 / 依赖。**as-is 本机 m0（记录写完之后、独占）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、**4658 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c2-m0.log` 时刻晚于记录写入；进程卫生零泄漏）；治理绿。**另有自查缺陷 1 处（如实登记）**：新判据第一次自跑判红 `6 failed`，根因是它把规范页散文里的通配泛指 `tools/**.py` 当成真实脚本路径，**被它自己的配对断言抓到**，修复 `c2f3330`。 |
| 2026-09-28 | ACTIVE | cycle 3（PLAN-20260928-223）：**EC-03 = PASS**（受判射程边界机械化）。交付 = 新判据（192 行 / **6 例**）+ `RECHECK-20260928-224` + `MEM-20260928-159`。**边界事实**：起点 `2026-09-28`、扫描面 **5**、射程内 **1**、射程外**恰好 4**（逐条点名）。**两向反证**（hermetic + 仓库级各一轮）：backdate 逃逸 ⇒ `2 failed, 4 passed`；回填历史 ⇒ `1 failed, 5 passed`；两次 raw `sha256` **逐字节复原**（`b46e551f…` / `b459e3a3…`），`git status` 对 rechecks 目录**为空**（零回填）。**交叉观察**：按压 ② 时**既有那条判据也同时判红** ⇒ 两条判据结论一致。**「只判边界不判质量」以行为证明**（质量全坏但边界对 ⇒ 不判红）。**既有判据逐字节未改**。**as-is 本机 m0（记录写完之后、独占、仓库 `.venv`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4665 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal023-c3-m0.log`，时刻 `14:37:56` 晚于记录写入 `14:22:03`；进程卫生零泄漏；用例较交付前 **+7** = 新判据 6 例 + 规模门参数化面 1 项）。 |
