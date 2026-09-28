---
id: GOAL-20260929-025
slug: privacy-residual-surfaces-and-positive-controls
title: 隐私面剩余未证伪面的判定化（响应头面进扫描 + 正控制矩阵 + 白名单契约派生 + 自举收口）
status: ACHIEVED
created_at: 2026-09-29
updated_at: 2026-09-29
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-29 用户会话指令（goal 模式）：**建档 GOAL-025（隐私面剩余未证伪面的判定化）
    并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为「把 GOAL-024 登记的
    四条未证伪面做成**已判定**」（把「未验证」变成「**有判据的结论**」或「**逐条登记的
    不可判定项**」）：**`G24-2` 响应头面**（读面扫描只扫响应体，响应头未被证伪）、
    **`G24-6` 正控制**（6 条声明载体无正控制、3 条路由取不到）、**`G24-3` 白名单**
    （人工判定 + 机械自审，不是从契约派生）、**`G24-1` 金丝雀源**
    （`task_input` / `tool_arguments` / `tool_output` / `failure_message` 在默认离线链上
    没有注入面 ⇒ 这四源「不出现在非 canonical 出口」未验证）。范围 = 这四条的
    **只收紧部分**。**越界即 BLOCKED**：
    **(i) 新增判据**（一律落 `tests/**`；落在既有 `python/tests` 收集面内 ⇒ m0 条数仍 `23`）、
    **(ii) 测试侧夹具 / 探针 / 工具**（新增脚本进 `tools/` 的，**必须**加入
    `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` 必备清单 —— **纯收紧**）、
    **(iii) 修被新判据证明为真缺陷的问题**（**只允许收紧**：清洗回显内容 / 关闭泄漏通道；
    **不得**借此改任何安全语义、认证面、策略面或门禁）、
    **(iv) 文档同源更新**（`docs/architecture/OBSERVABILITY.md`、`docs/security/THREAT_MODEL.md`
    等 + `docs/INDEX.md`）。**不加新能力、不放宽任何判据、不改任何既有判据。**
    (1) **明确不在本轮授权内（不许开工，命中即 BLOCKED）**：
    **`G24-4`（`LineageNodeDto.label` 字段改名 / 语义修正）** —— 改 DTO 契约（连带动 OpenAPI
    快照与 web 类型）⇒ **需用户单独拍板**，本轮**只允许**把差异与建议**登记**；
    **`G24-5`（把隐私条款做成运行时拦截器）** —— 产品行为变更 ⇒ **需用户单独拍板**，
    本轮**只允许**登记；
    **`G24-1` 中需要真实 runtime / 真实工具面 / 凭据才能取证的部分** —— 本机不可验证
    ⇒ **登记为 PENDING 并说明理由**，**不得**用离线夹具假装取过证。
    (2) **明确不做（命中即 BLOCKED）**：**给读面加认证**、**多租户 / RBAC / organization scope**、
    **BOLA·BFLA 实现**、**逐调用方身份**；**修改任何既有判据 / 门禁 / 阈值 / 放行面**
    （点名：`tests/observability/test_privacy_exit_census.py` /
    `test_privacy_content_canary_end_to_end.py` / `test_privacy_read_face_canary.py` /
    `test_privacy_boundary_clauses_are_pinned.py`、`test_privacy_canary.py`、三道记录面判据、
    多路证据判据、射程边界判据、`test_tooling_scripts_meet_product_gates.py`、
    `tests/egress_guard.py`）—— **新增**可以，**修改**不行；**改 `PRODUCT_ROOTS` / m0 任一 check /
    作业结构 / m0 条数**（终态行必须仍是 `23`）；**新增依赖**（标准库 + 现有栈）；
    **做真实出网调用**（全离线；Kubernetes / 真实 collector / 部署面只允许「登记 + 可复核
    检查项」）；**让金丝雀携带真实内容**（一律**测试内构造的合成串**；**不得**把真实 prompt /
    token / 凭据写进任何地方）；改认证的 401 形态或 `Idempotency-Key` 语义、动 `undici`、
    改 `ADR-0031` 的 `Status`、把真实 runtime 设为默认；**宣称项目安全**（`R-M1` 仍在）。
    (3) **必须写清的边界（否则判据会自伤）**：**canonical state（PG 域实体）允许持有用户自己的
    任务输入**（那是业务真相，不是泄漏）；受判面是**非 canonical 出口**。**不得**用
    「金丝雀出现在 DB 里」判红。
    (4) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (5) **边界（承继）**：GOAL-001…024 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的**全部 13 项 `D-NN`** 已结清、**本 GOAL 不重开**；
    GOAL-019…024 的**未覆盖范围原样保留**。
    (6) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    把 GOAL-20260928-024 收口时登记的**四条未证伪面**（`G24-2` 响应头面 / `G24-6` 正控制 /
    `G24-3` 白名单可复核性 / `G24-1` 四个无注入面的金丝雀源）从一句「**未验证**」推进为
    **有判据的结论**（可复跑、可反证、受判面非空），或推进为**逐条登记的不可判定项**
    （PENDING + 理由，**不得**用离线夹具假装取过证）。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**不修改任何既有判据**
    （只**新增**判据）；**零**新依赖；**零**策略面 allow；**不得**给读面加认证；
    **不得**改 401 形态或 `Idempotency-Key` 语义；**不得**宣称项目安全（`R-M1` 仍在）；
    金丝雀一律**测试内构造的合成串**；**全离线**（无真实出网）；m0 条数**仍是 23**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **响应头面进扫描（收 `G24-2`）**：(a) **新增**判据把读面**响应头**纳入扫描面，
      头部清单**逐条显式分类**为**受判** / **登记豁免（理由非空）**，
      且**分类清单写在判据源码里**（不靠散文；承 MEM-158：**未分类的新头部**在运行期被观测到
      即判红）；(b) 至少覆盖 `Content-Disposition`（文件名 —— **最可能承载用户内容**的一个）、
      `ETag`、`Last-Modified` 与任何回显类自定义头（逐条给出**受判或豁免 + 理由**；
      本仓实测**未观测到** `Last-Modified` ⇒ 必须给出机械理由或以「未观测到 ⇒ 判红」入受判面，
      **不得**静默略过）；(c) **反证**：把金丝雀塞进一个**受判头** ⇒ 判据**判红**且
      失败消息**点名头名与路由 / 字段**；随后**逐字节复原**（raw `sha256`，**二进制读写**）⇒ 复绿；
      (d) **受判面非空**（承 MEM-156）：断言「受判头 ≥ 1 **且** 本次运行中**真的观测到**
      这些头」，否则判红（**不得**空转）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_read_face_headers.py -q`
      ⇒ 全绿；配套留档：逐条头清单（受判 / 豁免 + 理由）、本次运行的头观测计数（每个受判头 ≥ 1）、
      反证红（点名头名 + 路由 / 字段的失败消息）、逐字节复原后 raw `sha256` 回到原值。
    status: PASS
  - id: EC-02
    criterion: >-
      **正控制与「未注入面」的判定化（收 `G24-6` + `G24-1`）**：(a) 为**无正控制**的 6 条声明载体
      （`/protocol-templates`、`/protocol-templates/{template_id}`、`/projects/{project_id}/memory`、
      `/runs/{run_id}/deliverable`、`/library/{resource_id}`、`/projects/{project_id}/library`）
      建立**正控制** —— 证明「这些出口**能**被扫到、且扫到内容时会红」；
      (b) 3 条**取不到的路由**（`/workspace-snapshots/{digest}/files`、
      `/workspace-snapshots/{left}/diff/{right}`、`/library/{resource_id}`）：要么建正控制，
      要么把「为何取不到」断言成**机械事实**（例如缺对象 ⇒ 断言该前置条件在位）；
      **不得** skip、**不得** xfail、**不得**假绿；
      (c) 4 个**无注入面**的金丝雀源（`task_input` / `tool_arguments` / `tool_output` /
      `failure_message`）：把它们当前的状态从一句**散文式**「未验证」**收窄为可判定陈述** ——
      要么在**默认离线链**上找到注入面并给出正控制；要么以**结构化断言**给出
      「该载体在默认离线链上不存在 / 惰性」（例如断言构造该载体的那条路径在离线装配下不被调用），
      并对**需要真实 runtime 才能取证的剩余部分**逐条登记为 **PENDING + 理由**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_positive_controls.py -q`
      ⇒ 全绿；配套留档：**正控制矩阵**（每条载体一行，状态 = 正控制通过 / 机械理由 / PENDING + 理由）、
      反证（正控制面出现内容 ⇒ 判红；复原 ⇒ 复绿）、取不到的路由**无 skip / xfail**
      （`-rs` 输出证明零 skip）。
    status: PASS
  - id: EC-03
    criterion: >-
      **白名单的可复核性（收 `G24-3`）**：产出**新增**的派生判据，把读面白名单从
      「人工判定」推进到**可从既有契约面派生**（**权威面 = `docs/api/openapi.m13.json`
      的 GET 路径集**，理由：该快照由 `tests/contracts/test_openapi_snapshot.py` **重新生成并
      逐字节比对** ⇒ 不会静默漂移，且它就是 web 类型的生成源），并逐条输出与既有白名单
      （`read_face_route_registry.py`）的**差异清单**：`派生 − 既有` 与 `既有 − 派生` 两向。
      - 差异**逐条判定**孰是孰非（派生算法缺陷 ⇒ 修**派生算法**；人工清单缺陷 ⇒
        **不改既有判据**，登记为残余 + 给出建议）；
      - **不得修改** `test_privacy_read_face_canary.py`（既有判据）；
      - 判据必须**可复跑**（运行时重新派生并与现有清单比对，差异非空即打印到判词里）；
      - **非空取证**：断言派生的 GET 路径集**非空**且**本轮真的取到了快照**（缺文件 ⇒ 判红）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_read_face_whitelist_derivation.py -q`
      ⇒ 全绿；配套留档：差异清单（两向，空 / 逐条判定）、反证（人为改一处派生根 ⇒ 判红）、
      逐字节复原后 raw `sha256` 回到原值。
    status: PASS
  - id: EC-04
    criterion: >-
      **自举收口（复用 022 / 023 / 024 的机器）**：① 本轮收口验证器**进树**
      （`tools/verify_goal025_closeout.py`，**复用** `tools/closeout_recheck_assertions.py` 的公共判词，
      只写本轮特有断言），并**显式加入** `IN_SCOPE` 必备清单（**纯收紧**）；
      ② 用 `tools/two_tree_recheck.py` 跑**当前树 + 干净 checkout** ⇒ 两树同结论
      （逐行相同 + `sha256` 相同；**留档一律二进制写盘**）；
      ③ **as-is 本机 m0 到 23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`），
      **运行发生在记录写入之后**（承 MEM-145）；④ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
      ⑤ CI 台账到终态（八 job + CodeQL + `run_attempt`）；
      ⑥ 承继残余逐条在位（12 条承继 + `G24-1`…`G24-6`，其中 `G24-2` / `G24-3` / `G24-6` 应在本轮
      **收口或收窄**，`G24-1` 部分收窄、剩余登记，`G24-4` / `G24-5` **原样保留并注明「需用户拍板」**）；
      ⑦ **未覆盖范围逐条明写**（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` 未收口）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal025_closeout.py
      --script-mode shared --root .` ⇒ 两树判词逐行相同 + `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；
      两路留档二进制一致（`cmp`）；m0 终态行实测；CI 台账逐 run 逐 job 实查（`run_attempt` 由 REST API）。
    status: PASS
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
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/observability/test_privacy_exit_census.py`、
      `test_privacy_content_canary_end_to_end.py`、`test_privacy_read_face_canary.py`、
      `test_privacy_boundary_clauses_are_pinned.py`、`test_privacy_canary.py`、三道记录面判据、
      多路证据判据、射程边界判据、`tests/tooling/test_tooling_scripts_meet_product_gates.py`、
      `tests/egress_guard.py`）—— **新增**判据不受此限
    - >-
      **修改** `read_face_route_registry.py` / `read_face_canary_support.py` /
      `content_canary_support.py` 的**既有清单与既有分类**（它们是 GOAL-024 的受判资产；
      本轮的派生判据只**读**它们并输出差异清单；派生算法的修补只允许落在**新增文件**里）
    - >-
      动 `G24-4` 的 DTO 契约（`LineageNodeDto.label` 改名 / 语义修正、改 OpenAPI 快照与
      web 类型）或 `G24-5` 的运行时拦截器（把隐私条款变成运行时产品行为）
    - >-
      把**真实** prompt / token / 凭据 / 用户内容写进夹具、记录、日志、遥测或以任何形式留档
      （金丝雀一律**测试内构造的合成串**；凭据只登记变量名、绝不留值）
    - >-
      用 **skip / xfail** 处理取不到的路由，或以「受判集合为空」的空真充当通过
      （承 MEM-156：受判面非空是交付前提）
    - >-
      用**真实出网**换取更强取证（真实端点 / 真实 collector / 真实中转站一律**不得**成为本
      GOAL 的取证手段；不可在本机验证者**登记 + 给可复核检查项**）
    - >-
      **给读面（GET/HEAD）加认证**，或改动读面放行语义（GOAL-019 判词 (i) 不变：
      保护范围只有写面）
    - >-
      引入**多租户 / organization scope / RBAC / 角色权限矩阵**或任何 M18 内容；
      或做 **BOLA / BFLA 的专项实现**
    - >-
      新增**任何**依赖（含为判据引入第三方库；一律标准库 + 现有栈；
      判据**可调用**既有 `ruff` / `mypy`）
    - >-
      **改认证的 401 响应形态**（`title` / `detail` / ProblemDetail 结构与点名文本）
    - >-
      改 `Idempotency-Key` 语义，或改 `IdempotencyMiddleware` 的方法分类 / replay / conflict /
      record 行为
    - >-
      把**新判据**写成「被文档引用 / 字面量喂饱」的形态（承 MEM-141：判据必须绑定
      **声明行 / 行为 / 文件面**），或让新判据**跳过按压**
    - >-
      用「金丝雀出现在 **canonical state（PG 域实体 / SQLite 域表）**」判红
      （canonical 允许持有用户自己的任务输入：那是业务真相，**不是泄漏**）；
      亦**不得**用「测试自选的**标识符**（如 `artifact_id`）携带金丝雀」去制造头面假红
      （标识符回显 ≠ 内容回显，两者是两个命题）
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
    或做 **BOLA / BFLA 的专项实现** —— **立即 BLOCKED**
  - >-
    **新增依赖** —— **立即 BLOCKED**（判据只能用标准库 + 既有 `ruff` / `mypy`）
  - >-
    **把 token / 真实凭据 / 真实用户内容写进任何地方**（CI / 文件 / 记录 / 日志 / 遥测 /
    夹具 / 示例 / 前端源码 / **判据源码**）—— **立即 BLOCKED**；真实凭据泄露（即使可弃用）
    ⇒ 立即停止并报告
  - >-
    **改认证的 401 响应形态**，或改 `Idempotency-Key` 语义 —— **立即 BLOCKED**
  - >-
    **放宽 / 削弱任一既有判据 / 门禁 / 阈值 / 放行面**，或**修改**任何既有判据
    （**新增**判据不受此限）—— **立即 BLOCKED**
  - >-
    **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**（`23` 这一终态条数；把 `tools` 纳入
    `PRODUCT_ROOTS` 属另行授权）—— **立即 BLOCKED**
  - >-
    **放宽 §9 默认 deny**，或新增任何策略面 allow / 类别级规则 —— **立即 BLOCKED**
  - >-
    **Canonical State 边界**（改「PostgreSQL Domain Entity 是业务真相」的口径 /
    把「金丝雀出现在 canonical」当成泄漏并据此改域模型）—— **立即 BLOCKED**
  - >-
    **动 `G24-4` 的 DTO 契约或 `G24-5` 的运行时拦截器**（两者**需用户单独拍板**）
    —— **立即 BLOCKED**
  - >-
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**（Mimosa 钩子
    `scanner_enobufs` 未得完整结论）
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20260929-237-goal-025-ec01-response-header-face-in-scan.md
  - .cursor/plans/tasks/PLAN-20260929-239-goal-025-ec02-positive-controls-and-uninjected-sources.md
  - .cursor/plans/tasks/PLAN-20260929-241-goal-025-ec03-whitelist-contract-derivation.md
  - .cursor/plans/tasks/PLAN-20260929-243-goal-025-ec04-closeout-two-tree-self-bootstrap.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-244-goal-025-ec04-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-163-response-headers-are-a-separate-judged-face.md
  - .cursor/memory/entries/MEM-20260929-164-positive-control-means-the-carrier-shows-its-content.md
  - .cursor/memory/entries/MEM-20260929-165-manual-whitelist-needs-a-derivability-check.md
  - .cursor/memory/entries/MEM-20260929-166-closeout-verifier-must-be-in-scope-and-pressable.md
---

## 目标与退出标准

**一句话**：GOAL-024 把观测隐私面对抗性自检做到了「受判出口 6 条 + 读面 68 条路由逐条白名单 +
端到端零命中 + 条款钉住」；收口时**如实登记**了四条**未证伪面**。本 GOAL 去把**那四条**
从「**未验证**」推进为「**有判据的结论**」或「**逐条登记的不可判定项**」——
**只收紧、只新增**，不动任何既有判据。

**本 GOAL 不加新能力、不改安全策略、不放宽任何判据、不修改任何既有判据。**
若新判据**证明**某处是真缺陷 ⇒ **只允许按授权收紧记录面 / 清洗回显内容 / 关闭泄漏通道**
（**不得**借此改认证 / 策略 / 门禁语义）；若某条**本机无法验证** ⇒ **登记为 PENDING**，
**不得**记 PASS。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **响应头面进扫描**（头清单逐条分类 + 零命中 + 反证红 + 复原绿 + 非空取证） | 新判据（头登记表在源码里）+ 反证 / 复原留档 | **PASS**（cycle 1） |
| EC-02 | **正控制矩阵**（6 条无正控制载体 + 3 条取不到路由 + 4 个无注入面源） | 新判据 + 矩阵 + PENDING 登记 | **PASS**（cycle 2） |
| EC-03 | **白名单契约派生**（从 OpenAPI 快照派生 + 两向差异清单逐条判定 + 反证） | 新派生判据 + 差异清单 | **PASS**（cycle 3） |
| EC-04 | **自举收口**（进树验证器 + 两树 + m0 23/23 + 台账 + 残余） | `tools/verify_goal025_closeout.py` + 两树留档 + 台账 | **PASS**（cycle 4） |

**依赖关系**：EC-01 与 EC-02 都**只读**复用 `read_face_canary_support.py` 的读面现场
（`open_read_face()`），**互不依赖**；EC-03 **只读** `read_face_route_registry.py` 与 OpenAPI 快照，
**不依赖** EC-01 / EC-02；EC-04 **依赖 EC-01 + EC-02 + EC-03**（收口验证器要断言前三者的终态
与登记面）。EC-04 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **响应头面现状（实测，决定 `G24-2` 的形状）**：`tests/observability/read_face_canary_support.py:272`
   的 `response_text()` **只读** `response.content` ⇒ 响应头**字面上不在扫描面**。
   实跑一次读面（**65 条**路由实取到响应）观测到的**全部**响应头只有 **5 个名字**：
   `content-length`（**65** 条）、`content-type`（**65** 条）、`etag`（**4** 条）、
   `content-disposition`（**1** 条）、`x-content-type-options`（**1** 条）；
   **未观测到** `last-modified`。⇒ **受判头集合非空**（承 MEM-156），EC-01 不会落在空集上。
2. **头的发射点有界且可点名（实测）**：`services/api/routers/artifacts.py:152` 的
   `_content_headers()` 是全仓**唯一**一处显式设置 `Content-Disposition` /
   `X-Content-Type-Options` / `ETag` 的地方；产品根下**没有** `Last-Modified` 的发射点
   ⇒ 头清单可以是**小而有界的**分区，且 `Last-Modified` 的「未观测到」有**机械理由**
   （零发射点），不是「没看见就算数」。
3. **`Content-Disposition` 的取值来自 `artifact.id`（实测，load-bearing）**：
   `filename` = 对 `artifact.id` 做**字符类净化**（非 `isalnum()` 且非 `._-` ⇒ `_`）后
   **取尾部 120 字符**；`ETag` = `"{artifact.digest}"`；`X-Content-Type-Options` = 常量
   `nosniff`。⇒ 「**标识符**（id / digest）回显进头」与「**内容**（正文）回显进头」是
   **两个命题**；本 GOAL 的受判命题是**后者**（内容金丝雀零命中）。
   **不得**用测试自选的 `artifact_id` 携带金丝雀去制造头面假红（那会把标识符当成内容，
   且 id 本来就在 `/artifacts/{artifact_id}` 元数据面上按契约可见）。
   `artifact.id` **来源面**（运行时是否允许它承载用户文本）本轮**只登记**，不判定。
4. **金丝雀形态与净化器兼容（实测）**：`content_canary_support.py` 的 token =
   `Z9< KIND ><run-hex>`（**纯字母数字**）⇒ 它能**穿过** `_content_headers()` 的净化器；
   `hits()` / `iter_hit_details()` 是**纯函数** ⇒ 头面扫描可直接复用，不必新造扫描器。
5. **规模余量（实测，决定判据落点）**：`read_face_canary_support.py` **294 行**、
   `read_face_route_registry.py` **294 行**、`test_privacy_read_face_canary.py` **200 行**
   （规模门硬上限 **450**、>300 软告警）⇒ 三者**只读**，头面判据**必须落新文件**。
6. **契约面存在且受门钉住（实测，决定 EC-03 可行）**：`docs/api/openapi.m13.json`
   （381,115 B）含 **64 条 GET**；`tests/contracts/test_openapi_snapshot.py`（190 行）会
   **重新生成并与提交前快照逐字节比对** ⇒ 该面**不会静默漂移**，是**权威**契约面。
   它与既有白名单（**68** 条）的差集**实测**为：`快照 − 登记 = ∅`；
   `登记 − 快照 = {/docs, /docs/oauth2-redirect, /openapi.json, /redoc}`
   （**4 条 FastAPI 内建框架路由**，既有清单已逐条归入 `_FRAME`）
   ⇒ EC-03 的派生判据有一个**当下差异为空的**基线，任何**真差异**都是新信息。
7. **另一条候选契约面被否（实测，须在 EC-03 里写明理由）**：`docs/api/CONTROL_PLANE_API.md`
   （39,913 B）是**人写**的 API 文档 ⇒ 会漂移、**不作为**权威面。EC-03 只允许在
   **OpenAPI 快照 / 运行时路由表 / DTO 类型**之间选，且必须写明**为何该面权威**
   （本轮选快照：它是 web 类型的生成源 + 有逐字节重生成门）。
8. **既有判据只读点名**（`fix_policy.forbidden` 已含）：`test_privacy_exit_census.py`、
   `test_privacy_content_canary_end_to_end.py`、`test_privacy_read_face_canary.py`、
   `test_privacy_boundary_clauses_are_pinned.py`、`test_privacy_canary.py`、三道记录面判据、
   多路证据判据、射程边界判据、`test_tooling_scripts_meet_product_gates.py`、
   `tests/egress_guard.py`；**追加**：`read_face_route_registry.py` /
   `read_face_canary_support.py` / `content_canary_support.py` 的**既有清单与分类**
   （本轮只**读**它们并输出差异；派生算法修补只落**新文件**）。
9. **无正控制的 6 条声明载体（实测复核 `G24-6`）**：`/protocol-templates`、
   `/protocol-templates/{template_id}`、`/projects/{project_id}/memory`、
   `/runs/{run_id}/deliverable`、`/library/{resource_id}`、`/projects/{project_id}/library`
   —— 在 `DECLARED_CONTENT` 里 `kinds` **为空** ⇒ 既有判据只要求「取得到响应」，
   **没有**要求「看得到它声明的内容」⇒ 它们**不是**正控制。
10. **取不到的 3 条路由（实测）**：`UNEXERCISED_ZERO_HIT` **2** 条
    （`/workspace-snapshots/{digest}/files`、`/workspace-snapshots/{left}/diff/{right}`）+
    `UNEXERCISED_DECLARED` **1** 条（`/library/{resource_id}`）。
11. **四个无注入面的金丝雀源（实测复核 `G24-1`）**：`CANARY_SOURCE_INJECTION` 现为
    **3 注入 / 4 未注入**（`task_input` / `tool_arguments` / `tool_output` / `failure_message`），
    理由是**散文**（判据源码里的字符串常量），**没有**任何机械断言钉住
    「这些源在默认离线链上不存在承载体」⇒ EC-02(c) 要把散文换成结构化断言。
12. **`IN_SCOPE` 现为 4 条且下界断言单调（实测）**：`tools/two_tree_recheck.py` /
    `tools/closeout_recheck_assertions.py` / `tools/verify_goal023_closeout.py` /
    `tools/verify_goal024_closeout.py` ⇒ 加入 `tools/verify_goal025_closeout.py` 是
    **纯收紧**（`required ⊆ IN_SCOPE` 单调）。
13. **收口机器的公共面可复用（实测）**：`tools/closeout_recheck_assertions.py` 暴露
    `Verdict` / `verdict_line` / `emit` / `standard_verdicts` / `protected_judges_verdict` /
    `scale_gate_verdict` / `product_roots_verdicts` / `m0_count_verdict` /
    `record_path_verdicts` / `presence_verdict` / `contains_verdict` ⇒ EC-04 的本轮验证器
    只写**特有**断言。
14. **两树复检入口（实测）**：`tools/two_tree_recheck.py` 的参数为 `--script` / `--root` /
    `--clean-root` / `--base-ref` / `--script-mode {tree,shared}` / `--verdict-current` /
    `--verdict-clean`；GOAL-024 用的形态是 `--script-mode shared` 且 `verify_paths = 2 路`。
15. **文档面（实测）**：`docs/architecture/OBSERVABILITY.md`、`docs/security/THREAT_MODEL.md`
    （GOAL-024 已各有条款节）、`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`、
    `docs/INDEX.md`、`docs/api/CONTROL_PLANE_API.md` 均在树；本 GOAL 的文档更新只**追加**。
16. **记录面判据与顺序（承 MEM-145）**：`tests/architecture/python/test_reproducibility_wording.py`
    （`OVERCLAIM_PHRASES` + 加引号豁免 + 否定标记豁免；扫描面含 `.cursor/plans`）与
    `tests/architecture/python/test_record_face_is_covered_by_the_gate.py`
    （记录面受门覆盖；`.cursor/memory/entries` 是**实测未覆盖面**）⇒ 本文件与其后续记录
    **不得**出现肯定式越级表述。
17. **工作树现状（实测，供驱动遵守）**：`git status` 有 **4 个与本 GOAL 无关**的路径显示为
    modified（`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
    `services/api/dto/models.py`、`services/api/middleware.py`），而 `git diff --numstat` 与
    `git diff --ignore-cr-at-eol` 均为**空** ⇒ 只是**行尾态**差异。
    **本 GOAL 一律只用显式路径提交，绝不 `git add -A`，绝不碰这 4 个文件。**
18. **基线 m0（实测）**：GOAL-024 收口时为 `PASS: profile=m0; 23 deterministic checks`
    （`PASS [` = **24**、**4715 passed / 21 skipped**、`EXIT=0`）⇒ 本 GOAL 的终态行
    **必须仍是 `23`**，用例数只允许**增加**。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-025-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-025**」（**不是**把任何既有 GOAL 置回 ACTIVE）。
理由：GOAL-024 交付的是**主命题的取证**（受判出口零命中 + 读面白名单 + 条款钉住），
它**明文登记**了四条未证伪面；把这四条**判定化**（响应头进扫描 / 正控制矩阵 /
白名单契约派生 / 无注入面源的结构化陈述）在 GOAL-001…024 里**从未**作为交付面出现过。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260929-025` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证（承 MEM-145 的顺序，不得颠倒）**：
  (a) **先写记录**（PLAN / RECHECK / MEM / GOAL 回写）；
  (b) **跑记录面判据**（写入记录 ⇒ 记录面判据必须参与，且**结论覆盖记录面**）；
  (c) **再跑完整 `make validate-all`**（m0 全量 **23 项**、**独占运行**、**用仓库 `.venv`**、
      经 `uv run --frozen --no-sync python -B` 走 canonical 调用口径、**不接管道**以免缓冲）
  + 受影响定向套件 + web 门（tsc / eslint / unit / build / stub e2e / live e2e）。
  **本地不绿不得 push**（承 MEM-125）。
  规模门禁自查（**50 行函数 / 450 行文件**——新判据与新夹具同样受门）；
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

- **正控制先行（承 MEM-156）**：每条载体 / 每个受判头**必须**在本轮**真的被观测到**
  （逐条观测计数非空），否则判红；**不得**出现「受判集合为空」的空真。
- **反证两向（承 MEM-159）**：既证「**该红时会红**」（内容进受判头 / 正控制面内容缺失
  ⇒ 判红且点名头名与路由 / 字段），也证「**不该红时不红**」（内容放进 **canonical**
  ⇒ **不**判红）。
- **射程显式分类（承 MEM-158）**：每个**候选头** / 每个**载体**要么在射程内、要么登记在案
  （理由非空）；**运行期观测到的未分类头 ⇒ 判红**。
- **不得靠并集掩蔽（承 MEM-160）**：若必备清单与文档点名是两个来源，**必须**有一条专门
  断言清单**下界**的判据（本轮：`IN_SCOPE` 与头 / 载体清单的下界都写在**判据源码**里）。
- **按压 → 逐字节复原必须 raw `sha256` + 二进制读写**（承 MEM-152）：任何留档（判词 / 日志 /
  证据）**都不得**用文本模式写盘；按压 / 复原**一律用 Edit 工具**（不用 Bash 写源码）。
- **判据自身恒真（承 MEM-141）**：新判据**不得**被文档引用 / 字面量喂饱——头面绑**运行时
  响应对象**、载体面绑**真实夹具注入**、白名单面绑**受门钉住的 OpenAPI 快照**，
  且**必须被按压过**（先红后绿 + 逐字节复原）。
- **台账审计口径（承 GOAL-024 的好做法）**：轮询出现空字段 / 解析失败时，**必须单独取原始
  JSON 复核**再定论；**不得**把解析打嗝写成不一致、也**不得**把不一致读成打嗝。
- **改工具先数夹具**：若动 `tools/two_tree_recheck.py` 或其契约，先确认
  `tests/tooling/test_two_tree_recheck_entry.py` 与
  `tests/tooling/test_closeout_assertions_are_in_tree.py` 的断言**一字不改且全绿**。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧
  复验**（由 CI 承担；本地按同一形态自查）。
- **记录 / 门先后（承 GOAL-021 的澄清）**：本地门**不可能**跑在「记录**最后一次**编辑之后」；
  本地门跑在「当时记录已写完」的状态，**记录面的最终覆盖由 CI 承担**；
  **不得**预先声明尚未跑出的结论（承 GOAL-023 的「见补记」做法）。
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
  本 GOAL 的收口判词**必须**写明：**① 响应头清单（受判 / 豁免逐条与其理由）**、
  **② 正控制矩阵（每条载体一行：状态 = 正控制通过 / 机械理由 / PENDING + 理由）**、
  **③ 白名单差异清单与逐条判定（两向）**、
  **④ 两树实跑证据（逐行 + `sha256`）**、**⑤ 按压与逐字节复原记录（raw `sha256`）**、
  **⑥ as-is 本机 m0 的终态行与「门在记录之后」的时刻证据**、
  **⑦ 未覆盖范围（五条）与新增残余登记**。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **做 BOLA·BFLA 实现**、**新增依赖**、**把真实内容 / token 写进任何地方**、**改 401 形态或
  `Idempotency-Key` 语义**、**放宽或修改任何既有判据 / 门禁 / 阈值**、
  **动 `G24-4` / `G24-5`**、**Canonical State 边界**、**真实 runtime 设为默认**）、
  同一失败签名超过 `fix_policy` 上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles`
  个 cycle 未推进任何 EC ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含**未覆盖范围**）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。

**承继：GOAL-016 / 017 / 018 的 13 项 `D-NN` —— 已全部结清，本轮不重开**

终态表引用 GOAL-018 的收口结论（`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的终态表）：
**已实施 9 项**、**部分实施 1 项**（`D-03`：`undici` 已调研未升）、
**已拍板为维持现状 3 项**、**未授权待拍板 0 项**。⇒ 本 GOAL **不重开任何一项**。

**承继：GOAL-019 / 020 / 021 / 022 / 023 / 024 的残余 —— 原样保留（本 GOAL 只登记现状，
不改其状态；`G24-2` / `G24-3` / `G24-6` 与本轮收口或收窄，`G24-1` 部分收窄）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子 `scanner_enobufs` 未得完整结论 | **原样保留**（**不得**据此宣称项目安全） |
| `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` | `undici` 归上游 / 非 ASCII 路径豁免 / 主观面先操作化 / 规模不足的诚实边界 | **原样保留** |
| `W-4` / `W-5` / `W-6` | 本机 m0 同进程跑阈值判据 / 新作业多一次冷装 / `live_run_support.py` 零余量 | **原样保留** |
| `W-10` / `W-11` / `W-12` | 单 token ⇒ 单主体 / BOLA·BFLA 未做 / 部署面未验证 | **原样保留**（本 GOAL 不碰认证面） |
| 历史遗留 **37** 个 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**验证器加入必备清单） |
| 四条历史收口复检**不可回填** | GOAL-023 新增② | **原样保留** |
| 可复跑性 ≠ 跨平台复验 | GOAL-023 新增③ | **原样保留**（本机只在 Windows 实跑；跨平台由 CI 承担） |
| `G24-1` | 四个金丝雀源在默认离线链上没有注入面 | **本轮部分收窄**：离线可判定的部分做成**结构化断言**；**真实 runtime / 工具面**所需部分 ⇒ **PENDING + 理由** |
| `G24-2` | 读面扫描只扫响应体、响应头不在面 | **本轮收口**（EC-01） |
| `G24-3` | 读面白名单是人工判定 + 机械自审，不是从契约派生 | **本轮收窄**（EC-03 加派生判据；人工清单若被证明有缺陷 ⇒ **不改既有判据**，登记 + 建议） |
| `G24-4` | `LineageNodeDto.label` 字段名与内容语义不一致 | **原样保留 + 注明「需用户拍板」**（改 DTO 契约连带 OpenAPI 快照与 web 类型） |
| `G24-5` | 文档条款是文档 + 判据形态，不是运行时拦截器 | **原样保留 + 注明「需用户拍板」**（产品行为变更） |
| `G24-6` | 6 条声明载体无正控制、3 条路由取不到 | **本轮收口或收窄**（EC-02；取不到的路由要么建正控制、要么断言成机械事实，**不得** skip） |

**本 GOAL 特有边界（= 用户判词的「明确不做」+「不在授权内」清单，命中即 BLOCKED）**：

1. **读面认证（GET / HEAD）**——**不做**（GOAL-019 判词 (i) 不变：保护范围**只有写面**）；
2. **多租户隔离 / organization scope**——**不做**；
3. **RBAC / 角色 / 权限矩阵**——**不做**；
4. **BOLA / BFLA 的专项实现**——**不做**；
5. **逐调用方身份**（caller-declared identity）——**不做**（单 token ⇒ 单主体）；
6. **新增依赖**——**不做**（一律标准库 + 现有栈；判据**可调用**既有 `ruff` / `mypy`）；
7. **修改任何既有判据 / 门禁 / 阈值 / 放行面**——**不做**（`fix_policy.forbidden` 已点名）；
   **新增**判据**可以**；
8. **改 `PRODUCT_ROOTS` / m0 条数 / 作业结构**——**不做**（终态行仍是 `23`）；
9. **改认证的 401 响应形态**、**改 `Idempotency-Key` 语义**——**不做**；
10. **把真实 prompt / token / 凭据 / 用户内容写进任何地方**——**不做**；金丝雀一律
    **测试内构造的合成串**；
11. **用真实出网换取更强取证**——**不做**（真实端点 / 真实 collector / 真实中转站
    一律登记为「不可在本机验证 + 给出可复核检查项」）；
12. **部署面验证**（需真实环境）——**只允许**「登记 + 可复核检查项」；
13. **`G24-4` 的 DTO 契约改动**（`LineageNodeDto.label` 改名 / 语义修正 + OpenAPI 快照 +
    web 类型）——**只允许登记差异与建议**，**需用户单独拍板**；
14. **`G24-5` 的运行时拦截器**（把隐私条款做成产品行为）——**只允许登记**，
    **需用户单独拍板**；
15. **用 skip / xfail 处理取不到的路由**——**不做**（要么建正控制，要么断言成机械事实）；
16. **用「测试自选的标识符携带金丝雀」制造头面假红**——**不做**（标识符回显 ≠ 内容回显）；
17. **`R-M1`**——**不得**据此宣称项目安全；
18. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
19. **`undici` 的 pin**——**不动**（归属上游）；
20. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**；
21. **把新判据写成「被文档引用 / 字面量喂饱」的形态**——**不做**（承 MEM-141）；
22. **用「金丝雀出现在 canonical」判红**——**不做**（canonical 允许持有用户自己的任务输入）；
23. **宣称项目安全**（`R-M1` 仍在）——**不做**。

**本 GOAL 交付的是「四条未证伪面的判定结果 + 可复跑判据」，不是「隐私已完备」**：

- EC-01 只把**读面响应头**纳入扫描面，**不**证明「头面永不承载内容」——
  它证明的是「**本次注入的内容金丝雀在受判头上零命中**」，且**未分类的新头会判红**；
- EC-02 的「机械理由 / PENDING」是**有理由的登记**，**不是**证明软件永远不会那样做；
  需要真实 runtime / 真实工具面才能取证的部分**本轮仍不可判定**（PENDING）；
- EC-03 的派生判据只证明「**白名单与契约面当下一致**（或差异被逐条判定）」，
  **不**证明人工清单**永远**正确；
- **`G24-4` / `G24-5` 仍未处置**（需用户拍板）。

**未覆盖范围（逐条明写；本 GOAL 不消解任何一条）**：

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— Kubernetes / 真实 collector / 真实中转站 / 配置了快照根的真实环境只在登记面；
5. **R-M1 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称项目安全。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 本行所在的**建档 + 记录提交**（**同一提交**：新增本文件 + 回填门结果——建档轮的「记录」就是本文件自身，故不拆两笔） | 治理 `validate.py` = `Cursor 治理验证通过`（8 行结论，含「GOAL 循环记录结构合规；push 授权显式登记」）；**记录面判据**（`test_reproducibility_wording.py` + `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）= **24 passed**（与 GOAL-024 基线同值；`egress guard: judged 0 connection attempt(s); blocked 0`）；**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4715 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal025-c0-m0.log`，耗时 **641.20s**，**日志文件时刻 `01:55:11` 晚于**本文件最后一次写入 `01:37:04`（`ls -l` 实测）⇒ 门跑在「本文件已写完」的状态；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令 `run_all_checks.py --profile m0 --keep-going`（同解释器 `.venv`、同 DSN 固化 + `LLM_MAIN_KEY=""`、同 `--keep-going`，与 canonical 调用等价）；**独占运行**（跑前 `tasklist` 零 python 进程、`research-system-postgres-1` healthy）；**进程卫生**：跑完 `tasklist` python 进程 **0**；**记录面最终覆盖由 CI 承担**（本行数字写于门之后 ⇒ 依 GOAL-021 的澄清，**不**声称本地门覆盖了本行的最终文本） | 建档（`f39cdee`）到终态：M0 `36462665808` 八 job 全 `success` + CodeQL `36462663487` 3/3 `success`，两者 `run_attempt=1`，**一次成功无 flake**（逐 run 由 REST API 实查；台账见下） | 建档轮**零产品代码改动**（只新增本文件） | EC-01…EC-04 全 PENDING。起点已定位：**① 受判头集合非空且小**（实测 5 个头名，`content-length`/`content-type` 各 65 条、`etag` 4 条、`content-disposition` 1 条、`x-content-type-options` 1 条；`last-modified` 未观测且产品根零发射点）；**② 头的唯一发射点是 `artifacts.py:152` 的 `_content_headers()`**；**③ `Content-Disposition.filename` 取自 `artifact.id`（净化 + 尾 120 截断）、`ETag` 取自 digest** ⇒ 标识符回显与内容回显必须分成两个命题；**④ 6 条无正控制载体与 3 条取不到路由已逐条点名**；**⑤ 四个无注入面源的登记是散文** ⇒ 要换成结构化断言；**⑥ OpenAPI 快照 64 条 GET 是权威契约面且与白名单当下差异 = 4 条框架路由**；**⑦ 三个既有读面文件余量薄（294/294/200）⇒ 新判据必须落新文件** | cycle 1 = **EC-01**（响应头面进扫描：头清单逐条分类 + 零命中 + 反证红 + 复原绿 + 非空取证） |
| 1 | PLAN-20260929-237（EC-01） | 本行所在的**实施提交**（2 个进树判据文件 + PLAN / ALL_PLAN）+ 本行所在的**记录提交** | **EC-01 全部验收成立且有实跑证据**。交付 = `tests/observability/read_face_header_inventory.py`（**217 行**：受判 2 / 豁免 3 / 登记为不发射 1 的**分区**，写在判据源码里；七条纯函数自审 + 头值扫描）+ `tests/observability/test_privacy_read_face_headers.py`（**245 行 / 13 例**）+ `RECHECK-20260929-238`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-20260929-163`。**实跑**：逐路由实取**响应头**，**65 条**读路由取到响应（下界 40）；头部观测计数 `content-type` **65** / `content-length` **65** / `etag` **4** / `content-disposition` **1** / `x-content-type-options` **1** / `last-modified` **0** ⇒ **受判面非空**（承 MEM-156）。**零命中**：全部 65 条路由的全部头逐值扫描 ⇒ **零违规**（豁免头的机械值形态亦全绿）。**正控制**：`Content-Disposition` 实测 = `inline; filename="canary-artifact_<run>"`（`filename` **逐字符等于**净化后的 `artifact.id`）、`ETag` **逐字符等于** `f'"{meta.digest}"'` ⇒ 受判头**确实在发**且是**标识符**回显面。**三条源码按压先红后绿 + 逐字节复原**：P1 删 `content-disposition` 规则 ⇒ `未分类的响应头:content-disposition` + `受判面低于下界:1 < 2`；P2 抽空 `etag` 理由 ⇒ `理由为空:etag`；P3 `last-modified` 由 `ABSENT` 改判 `EXEMPT` ⇒ `豁免头缺少机械值形态:last-modified` + `登记陈旧(本轮未观测到):last-modified`；复原后 raw `sha256` 回到 `9e9a51ea65603f03cc76d4ea050bdd5555d917138ed9cca41d2bbd37c4e0babd`（`MATCHES_BASELINE True`）⇒ **13 passed**；证据 `scratch/goal025-ec01-press-matrix.log`（**二进制写盘**）。**判据内两向反证**（真实应用 + 真实响应）：受判头带金丝雀 ⇒ 判红点名**路由 + `etag` + `artifactbody`**；未分类新头 ⇒ 判红点名；登记为不发射的头出现 ⇒ 判红点名；内容进 canonical / 正文 ⇒ **头面零命中**（不该红时不红）。**边界钉住**：断言夹具**全部标识符**（两个制品 id + `face.ids`）都不含金丝雀 token ⇒ 防止将来把「标识符回显」误判成泄漏。**判据自跑抓到一处自己的真错并当场修掉**：正控制最初把处置词写死成 `attachment`，实测是 `inline`（由制品 `media_type` 决定）⇒ 改成「两值之一」，**不是**放宽断言。**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；规模 **217 / 245 行**（规模门定向跑 **2 passed**）；`mypy` = `Success: no issues found in 2 source files`。**既有隐私判据逐字节未改**（`git diff --stat -- tests/observability/` 为空）且 `tests/observability/` 全目录 **113 passed, 1 skipped**（GOAL-024 cycle 4 收口时 100 + 1 ⇒ **+13** 恰为新判据）。**零改动面**：`PRODUCT_ROOTS` / m0 条数（**仍 23**）/ 作业结构 / 依赖 / 产品代码 / 既有判据**全部零改动**。 | 见下方 CI 台账（本行所在提交的 run 在台账尾回填） | **零真缺陷**；修掉的是**本判据自己的一处过严断言**（处置词写死），由判据自跑抓到 | **EC-01 = PASS**（`G24-2` 收口）。**如实登记六条警告**（`RECHECK-238`）：`W-1` 受判面**有界且头名清单是人工登记**的（能挡新头，挡不住人工把受判头改判成豁免，但会在陈旧 / 值形态两条上被挡）；`W-2` 豁免是**形态**断言而非「永不承载内容」的证明（以「任何头值零命中」绝对扫描兜底）；`W-3` `Content-Disposition.filename` 的**取值来源面**（`artifact.id` 能否承载用户文本）**未判定** ⇒ 列入本轮残余；`W-4` 按压是**源码级 + 判据内**，**未**在产品侧（`_content_headers()`）施加按压；`W-5` 只覆盖**读面（GET）**，**写面响应头不在射程**；`W-6` 草稿三条路由的 `ETag` 取值面未逐条取证（只在零命中扫描里被覆盖）；`R-M1` 未收口 | cycle 2 = **EC-02**（正控制矩阵：6 条无正控制载体 + 3 条取不到路由 + 4 个无注入面源） |
| 2 | PLAN-20260929-239（EC-02） | 本行所在的**实施提交**（2 个进树判据文件 + PLAN / ALL_PLAN）+ 本行所在的**记录提交** | **EC-02 全部验收成立且有实跑证据**。交付 = `tests/observability/positive_control_support.py`（**250 行**：载体判定矩阵「正控制 6 / 机械理由 2」+ 源判定矩阵「4 条，各带机械证据与非空 PENDING 理由」+ 富化读面现场）+ `tests/observability/test_privacy_positive_controls.py`（**196 行 / 11 例**）+ `RECHECK-20260929-240`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）。**必做面不是另写一份清单**：必做集合**从 GOAL-024 的登记推出**（`DECLARED_CONTENT` 里 `kinds` 为空的行 ∪ `UNEXERCISED_DECLARED` ∪ `UNEXERCISED_ZERO_HIT`）并与矩阵比对。**6 条载体逐条正控制（实跑）**：模板 ×2（**换入**金丝雀模板目录，**不动** `examples/protocols/` 参考资产）／记忆（经**产品写面** `POST /memory/proposals`，provenance 走已登记 evidence source）／交付物（seed `<run>:deliverable.json`）／库 ×2（经**产品写面** `POST /projects/{id}/library`）—— 每条都**看到**它声明承载的金丝雀。**3 条取不到路由判定化**：`/library/{resource_id}` 变成**可取到**（200 + 声明的正文）；2 条快照路由**真跑**并断言 `deps.workspace_snapshots is None` ⇒ 实测 **503**（守卫在位），**无 skip / xfail**。**4 个无注入面源收窄为结构化断言**：`task_input`（`StartRunCommand.notes` 为空、`protocol_body` 为 None）／`tool_arguments` + `tool_output`（Fake 无 `execute_tool`/`call_tool`/`invoke_tool`/`tools` 属性，而 `RuntimeEventKind.TOOL_CALL_REQUESTED` **真实存在** ⇒ 非空转）／`failure_message`（失败分支结构化输出为空 + 实跑失败载荷非空且零金丝雀）；四条各带**非空 PENDING 理由**（真实 runtime 面）。**两向反证**：①**不加**注入时 `/protocol-templates` 看不到金丝雀 ⇒ 正控制由本轮注入造成；②载体看不到声明内容 ⇒ 判红点名路由与 kind。**三条源码按压先红后绿 + 逐字节复原**：Q1 抽空一条机械理由 ⇒ `这些行没有理由:[…]`；Q2 下界 6→7 ⇒ `正控制载体只有 6 条 < 下界 7`；Q3 把一条正控制降级成机械理由 ⇒ `正控制载体只有 5 条 < 下界 6`（承 MEM-160）；复原后 raw `sha256` 回到 `d9f85f1cb79dfc0b1fbe10985be26e8d77ce84a29257b2c8612611d9e24f2faf`（`MATCHES_BASELINE True`）⇒ **11 passed**；证据 `scratch/goal025-ec02-press-matrix.log`（**二进制写盘**）。**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模 **250 / 196 行**（规模门定向跑 **2 passed**）。**既有判据逐字节未改**（只新增文件）且 `tests/observability/` 全目录 **124 passed, 1 skipped**（cycle 1 后为 113 + 1 ⇒ **+11** 恰为新判据）。**零改动面**：`PRODUCT_ROOTS` / m0 条数（**仍 23**）/ 作业结构 / 依赖 / 产品代码 / `examples/` 参考资产 / 既有判据**全部零改动**。 | 见下方 CI 台账（本行所在提交的 run 在台账尾回填） | **零真缺陷**；修掉的是**本轮新判据自己的两处错**（记忆 provenance 未登记 evidence source；失败文本的「产品标记」是猜测而非机械事实）—— 由判据自跑抓到并改成结构断言 | **EC-02 = PASS**（`G24-6` 收口；`G24-1` **离线可判定部分收窄**）。**如实登记六条警告**（`RECHECK-240`）：`W-1` 正控制证明的是**出口能力**（route-level），模板走的是**换入的注入实例**而非产品目录；`W-2` tool 两源的证据是**属性面断言**，不证明真实工具面启用后的行为；`W-3` `task_input` 的字段面断言**不会自动跟随**新增自由文本字段（需人工同步）；`W-4` `failure_message` 的结论锚在「该分支结构化输出为空」上，对真实 runtime 的失败文本**不成立**；`W-5` 库条目 `content_ref` 指向的正文**未判定**；`W-6` 快照 503 是**离线装配**的事实，配置了快照根的真实部署面**未验证**；`R-M1` 未收口 | cycle 3 = **EC-03**（白名单契约派生：从 OpenAPI 快照派生 + 两向差异清单逐条判定 + 反证） |
| 3 | PLAN-20260929-241（EC-03） | 本行所在的**实施提交**（2 个进树判据文件 + PLAN / ALL_PLAN）+ 本行所在的**记录提交** | **EC-03 全部验收成立且有实跑证据**。交付 = `tests/observability/read_face_whitelist_derivation.py`（**128 行**：提交快照派生 + 任意 schema 派生 + 框架内建登记 4 条（逐条理由）+ 两向差异 + 派生面下界 `MIN_DERIVED = 40`）+ `tests/observability/test_privacy_read_face_whitelist_derivation.py`（**124 行 / 10 例**）+ `RECHECK-20260929-242`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-20260929-165`。**实跑**：提交快照 GET **64** 条 + 框架内建 **4** 条 = 派生面 **68** 条；人工清单 **68** 条；**两向差异 = ∅**。**独立重算**（`json.loads` 直读快照 + 正则直读清单源码，**不经被检模块**）同值 ⇒ 结论不是自证。**三条独立路径互钉**：提交快照 × 实时 `app.openapi()` × 运行时路由树（`read_routes`）—— 三向差异全 ∅。**权威性受门钉住（实跑复核）**：`tests/contracts/test_openapi_snapshot.py` **8 passed**（重生成 + 与提交前字节逐字比对）。**三条源码按压先红后绿 + 逐字节复原**：P1 框架清单塞入 `/__bogus-frame` ⇒ `读面白名单与契约派生面不一致:['派生面有而清单没有:/__bogus-frame']`（3 failed）；P2 派生根 `GET`→`PATCH` ⇒ `快照里的 GET 只有 9 条 < 下界 40` + 两向长清单（5 failed）；P3 两向差异**只留一向** ⇒ 主判据仍绿、只有「清单多一条」那条反证例红 ⇒ **证明「清单陈旧」那一向是承重的**；复原后 raw `sha256` 回到 `ae9bf121fdc4f4b1ae15e488d13d8f1707bc2b9a4dce5ef7bc12e6ed1f3aa888`（`MATCHES_BASELINE True`）⇒ **10 passed**；证据 `scratch/goal025-ec03-press-matrix.log`（**二进制写盘**，4 599 B / `CR` 计数 0）。**判据内两向反证**（不碰源码树）：清单多一条 `/__extra` ⇒ 判红点名；清单少一条 `/health` ⇒ 判红点名；快照读不到 ⇒ 下界判红；**真实应用**挂一条新读路由 ⇒ 实时 schema 与快照立刻差异并点名该路由。**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模 **128 / 124 行**（规模门定向跑 **1058 passed**）。**既有判据逐字节未改**（`git status --porcelain -- tests/observability` 只有两个**新增**文件）；新判据**无 skip / xfail**；`tests/observability/` 全目录 **134 passed, 1 skipped**（cycle 2 后 124 + 1 ⇒ **+10** 恰为新判据）。**零改动面**：`PRODUCT_ROOTS` / m0 条数（**仍 23**）/ 作业结构 / 依赖 / 产品代码 / 权威快照（**只读**）/ 既有判据**全部零改动**。 | 见下方 CI 台账（本行所在提交的 run 在台账尾回填） | **零真缺陷**；修掉的是**我自己复检方法的一处错**（首轮独立重算用 `path="…"` 正则，对 `ReadRouteRule` 的**位置参数**写法零命中 ⇒ 换成 `ReadRouteRule\(\s*"…"` 重算并复得同值），**不是**产品 / 判据缺陷 | **EC-03 = PASS**（`G24-3` 收窄为「**路径集合**可从权威契约面派生且**当下零差异**」；**分类面仍是人工判定**）。**如实登记六条警告**（`RECHECK-242`）：`W-1` 派生的是**路径集合**、不证明**分类**（`declared_content` / `zero_hit`）可派生；`W-2` 框架那一半是 **4 条人工登记**（上界写死 `== 4`），但**登记不存在的路由**会被「运行时路由树 == 派生面」挡住；`W-3` 权威面只覆盖**声明的 GET 路径**（不含 HEAD / OPTIONS，也不证明 GET 一定返回内容）；`W-4` 运行时树叶子过滤是「`methods` 含 `GET`」⇒ 兼有 GET 与写方法的路由会被算进读面（本仓当前无此形态）；`W-5` 真实应用按压例**依赖文件内用例顺序**（共享模块级 `face`）；`W-6` 权威性**依赖**快照重生成门在位；`R-M1` 未收口 | cycle 4 = **EC-04**（自举收口：`tools/verify_goal025_closeout.py` 进树 + `IN_SCOPE` 纯收紧 + 两树复检 + as-is m0 + CI 台账 + 残余逐条） |
| 4 | PLAN-20260929-243（EC-04） | 本行所在的**收口提交**（`tools/verify_goal025_closeout.py` + `IN_SCOPE` 一行收紧 + PLAN / RECHECK / MEM / GOAL 收口；**零产品代码文件**）+ 本行所在的**补记提交**（两树实测 + 台账尾巴） | **EC-04 全部验收成立且有实跑证据**。交付 = `tools/verify_goal025_closeout.py`（**447 行 / 37 判词**：标准面 18 + 本轮特有 19）+ `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` **4 → 5**（**纯收紧**：必备清单 ⊆ 推导射程 单调）+ `RECHECK-20260929-244`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-20260929-166`。**自举复检（当前树）**：`--root . --verdict-only` ⇒ 收口前 **36 PASS / 1 FAIL**（唯一一条红 = `ec04-latest-recheck-resolves`，因 `latest_recheck` 尚未指向本轮的 RECHECK ⇒ 由本 PLAN 的 RECHECK 落地后转绿）。**四道门（本验证器逐条）**：`ruff format --check` = `1 file already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 1 source file`；规模 **447 行**（≤450）且无超 50 行函数 —— 这是 `IN_SCOPE` 收紧带来的**新增覆盖**（此前 `tools/` 下的脚本不过这四道门）。`tests/tooling/` 三件套（射程门 / 断言集在树 / 两树入口）**25 passed**（**改工具先数夹具**：既有断言一字未改）。**按压与两树**：三条按压（改 EC 状态 / 改 `latest_recheck` / 往派生面塞未登记路由）先红后绿 + raw `sha256` 逐字节复原见 `RECHECK-244` 与 `scratch/goal025-ec04-press-matrix.log`；两树实测：当前树 + 干净 checkout **判词逐行相同**（各 **37** 条）+ **`sha256` 相同**（`a2ca399e…1d73`）+ `TWO-TREE PASS` / `EXIT=0`（两路留档 `cmp` 二进制一致、`CR` 计数 0）。**残余与未覆盖**：12 条承继残余 + `G24-1`…`G24-6`（`G24-4` / `G24-5` 注明**需用户拍板**）+ 五条未覆盖范围逐条明写，并由验证器**逐条断言在位**。**零改动面**：`PRODUCT_ROOTS` / m0 条数（**仍 23**）/ 作业结构 / 依赖 / 产品代码 / 既有判据 / `tools/two_tree_recheck.py` 与 `tools/closeout_recheck_assertions.py`（**只调用，未改**）全部零改动。 | 见下方 CI 台账 | **零真缺陷**；判据自跑抓到的是**我自己**的两处记录/工具问题（`IN_SCOPE` 收紧前 `tools/` 脚本不过门；本轮新增验证器一度 470 行超规模门 ⇒ 按门修到 447 行），**不是**产品缺陷 | **GOAL-025 = ACHIEVED**（EC-01…EC-04 全 PASS）。残余：`G24-1` 的**真实 runtime / 工具面**部分仍为待取证项（离线不可判定）；`G24-4` / `G24-5` **原样保留 + 需用户拍板**；`R-M1` 未收口 | 无（本 GOAL 收口）；如需推进 `G24-4` / `G24-5` 需**用户单独拍板**后另立 GOAL |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-025 落地） | `f39cdee` | M0 [**36462665808**](https://github.com/Eswink/research-system-new/actions/runs/36462665808) / CodeQL [**36462663487**](https://github.com/Eswink/research-system-new/actions/runs/36462663487) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `container-quality` / `collector-quality` / `quality-windows-latest` / `quality-ubuntu-latest` / `observability-overhead-windows-latest` / `eval-gate` / `observability-overhead-ubuntu-latest` / `console-frontend` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (javascript-typescript)` / `Analyze (actions)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查）。轮询日志 `scratch/goal025-c0-ci-poll.log`（`ALL_TERMINAL sha=f39cdee9c519923254628b5beb25ec3e168deccd`，34 轮轮询）。**台账审计口径**：第 26 轮出现一次「unparseable API response; retrying」⇒ 按既有口径**单独取原始 JSON 复核**（`scratch/goal025-c0-run-36462665808.json` / `…-36462663487.json`，两者 `status=completed` / `conclusion=success` / `run_attempt=1`）⇒ **未把解析打嗝写成不一致，也未把不一致读成打嗝**。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ **零依赖改动**，与 GOAL-018…024 收口一致 |
| cycle 1 实施 + 记录（EC-01：`6ded362` 两个判据文件 / `f1a867b` 记录，批量一次推送） | `f1a867b` | M0 [**36471034397**](https://github.com/Eswink/research-system-new/actions/runs/36471034397) / CodeQL [**36471033610**](https://github.com/Eswink/research-system-new/actions/runs/36471033610) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `eval-gate` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `collector-quality` / `console-frontend` / `container-quality` / `quality-windows-latest` / `quality-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查：`scratch/goal025-c1-run-36471034397.json` / `…-36471033610.json`）。轮询日志 `scratch/goal025-c1-ci-poll.log`（`ALL_TERMINAL sha=f1a867bffc2f3f347bd3b0b3046f38adc8c980d2`，32 轮轮询，**无解析打嗝**） |
| cycle 2 实施 + 记录（EC-02：`dfac6fa` 两个判据文件 / `8fc61bd` 记录，批量一次推送） | `8fc61bd` | M0 [**36480572117**](https://github.com/Eswink/research-system-new/actions/runs/36480572117) / CodeQL [**36480572079**](https://github.com/Eswink/research-system-new/actions/runs/36480572079) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `container-quality` / `console-frontend` / `observability-overhead-ubuntu-latest` / `eval-gate` / `observability-overhead-windows-latest` / `collector-quality` / `quality-windows-latest` / `quality-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**（逐 run 的 `run_attempt` / `status` / `conclusion` 与逐 job 由 REST API 实查：复核脚本 `scratch/audit_goal025_ledger.sh`、输出 `scratch/goal025-ledger-audit.log`）。轮询日志 `scratch/goal025-c2-ci-poll.log`（`ALL_TERMINAL sha=8fc61bdc4e506b01c833449c29dead9c98d9c414`，**37 轮轮询，无解析打嗝**） |
| cycle 3 实施 + 记录（EC-03：`7e1b16c` 两个判据文件 / `f31150e` 记录，批量一次推送） | `f31150e` | M0 [**36489799431**](https://github.com/Eswink/research-system-new/actions/runs/36489799431) / CodeQL [**36489800413**](https://github.com/Eswink/research-system-new/actions/runs/36489800413) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `container-quality` / `console-frontend` / `observability-overhead-ubuntu-latest` / `eval-gate` / `observability-overhead-windows-latest` / `collector-quality` / `quality-windows-latest` / `quality-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**（逐 run 的 `run_attempt` / `status` / `conclusion` 与逐 job 由 REST API 实查：复核脚本 `scratch/audit_goal025_ledger.sh`、输出 `scratch/goal025-ledger-audit.log`）。轮询日志 `scratch/goal025-c3-ci-poll.log`（`ALL_TERMINAL sha=f31150eacdb0422af19e301e75cafa27ac49e585`，**39 轮轮询，无解析打嗝**） |
| 本条台账的**记录提交** | 本行所在的记录提交 | **依「固定口径」：写台账的那一步自身的 run 只在回合汇报记账**（不重复回写文件 —— 否则每写一行就产生一个待记账的新提交，台账永远追不上自己） | 见回合汇报 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | ACTIVE | **建档**：用户会话指令（goal 模式）授权把 GOAL-024 登记的四条未证伪面（`G24-2` 响应头面 / `G24-6` 正控制 / `G24-3` 白名单可复核性 / `G24-1` 四个无注入面的金丝雀源）**判定化**，并授权本驱动自动化循环推进、无需逐轮确认。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA 实现、逐调用方身份、修改任何既有判据 / 门禁 / 阈值 / 放行面、改 `PRODUCT_ROOTS` / m0 条数 / 作业结构、新增依赖、真实出网、真实内容进夹具或记录、改 401 形态或 `Idempotency-Key` 语义、动 `undici`、改 `ADR-0031` 的 `Status`、宣称项目安全；**不在授权内**（只允许登记，需用户单独拍板）：`G24-4` 的 DTO 契约改动、`G24-5` 的运行时拦截器。四 EC 设计（响应头面进扫描 / 正控制与未注入面判定化 / 白名单契约派生 / 自举收口），budget = 20 / 120 / 2。**建档当日实测十八条事实**（见「目标与退出标准」），其中六条决定判据形态：**① 受判头集合非空**（实测 65 条路由只发出 5 个头名，`content-disposition` 与 `etag` 确实在发）⇒ EC-01 不会空转；**② 头的唯一发射点可点名**（`artifacts.py:152`）且 `Last-Modified` 零发射点 ⇒ 「未观测到」有机械理由；**③ `Content-Disposition.filename` 取自 `artifact.id`、`ETag` 取自 digest** ⇒ 必须把「标识符回显」与「内容回显」分成两个命题，否则判据会自伤（用自选 id 制造假红）；**④ 三个既有读面文件是 294/294/200 行且只读** ⇒ 新判据必须落新文件；**⑤ OpenAPI 快照（64 条 GET，受 `test_openapi_snapshot.py` 逐字节重生成门钉住）是权威契约面**，与既有白名单当下差异恰为 4 条 FastAPI 框架路由 ⇒ EC-03 有干净基线；**⑥ 四个无注入面源的登记目前是散文**（判据源码里的字符串）⇒ EC-02(c) 要换成结构化断言。**建档时零产品代码改动**（只增本文件）；工作树另有 4 个**与本 GOAL 无关**的并发改动（仅行尾态差异，`git diff --numstat` 为空），本 GOAL 一律只用**显式路径**提交。 |
| 2026-09-29 | ACTIVE | **建档 cycle 0 完成，进入循环**：EC-01…EC-04 全 PENDING，下一 cycle 做 **EC-01**（响应头面进扫描）。**本地验证（顺序承 MEM-145）**：记录（本文件）先写完（`01:37:04`）→ 治理 `Cursor 治理验证通过` → 记录面判据 **24 passed** → **as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4715 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal025-c0-m0.log`，耗时 `641.20s`，**日志时刻 `01:55:11` 晚于**本文件写入 `01:37:04`）；进程卫生零泄漏；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令（canonical 等价）。**本行数字写于门之后** ⇒ 记录面最终覆盖由 CI 承担。**建档提交**的 CI 到终态后在下方台账回填。 |
| 2026-09-29 | ACTIVE | **cycle 1（PLAN-20260929-237）：EC-01 = PASS**（响应头面进扫描，收 `G24-2`）。交付 = `read_face_header_inventory.py`（217 行：受判 2 / 豁免 3 / 登记为不发射 1 的分区，写在判据源码里）+ `test_privacy_read_face_headers.py`（245 行 / **13 例**）+ `RECHECK-238`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-163`。**实跑**：65 条读路由实取头，观测到 5 个头名（`etag` 4 条 / `content-disposition` **1** 条）；全部头逐值扫描**零命中**；**正控制**证明受判头是活的且是**标识符**回显面（`filename` 逐字符等于净化后的 `artifact.id`）。**三条源码按压先红后绿 + raw `sha256` 逐字节复原**（回到 `9e9a51ea…babd`）；判据内两向反证含真实应用按压路由。四道门绿；既有隐私判据逐字节未改；`tests/observability/` **113 passed, 1 skipped**（+13）。**零产品代码改动**；m0 与 CI 台账见下方（记录写入之后才跑）。 |
| 2026-09-29 | ACTIVE | **cycle 0 CI 台账**：建档提交 `f39cdee` 到终态 —— M0 `36462665808` **八 job 全 `success`** + CodeQL `36462663487` **3/3 `success`**，两者 `run_attempt=1`（**一次成功、无 flake**，逐 run 由 REST API 实查）。轮询第 26 轮一次 API 响应不可解析 ⇒ 按台账口径单独取原始 JSON 复核后定论。 |
| 2026-09-29 | ACTIVE | **cycle 1 CI 台账**：`f1a867b`（EC-01 实施 `6ded362` + 记录 `f1a867b` 批量一次推送）到终态 —— M0 `36471034397` 八 job 全 `success` + CodeQL `36471033610` 3/3 `success`，两者 `run_attempt=1`（**一次成功、无 flake**）。 |
| 2026-09-29 | ACTIVE | **cycle 2（PLAN-20260929-239）：EC-02 = PASS**（收 `G24-6`；`G24-1` 离线可判定部分收窄）。交付 = `positive_control_support.py`（250 行：载体矩阵「正控制 6 / 机械理由 2」+ 源矩阵 4 条）+ `test_privacy_positive_controls.py`（196 行 / **11 例**）+ `RECHECK-240`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）。**实跑**：6 条载体逐条看到它声明承载的金丝雀；库条目路由从「取不到」变**可取到**；2 条快照路由**真跑**并实测 503 守卫（**无 skip / xfail**）；4 个源收窄为**结构化断言** + 非空 PENDING 理由。**三条源码按压先红后绿 + raw `sha256` 逐字节复原**（回到 `d9f85f1c…2faf`）。四道门绿；既有判据逐字节未改；`tests/observability/` **124 passed, 1 skipped**（+11）。**零产品代码改动**（含 `examples/` 参考资产未动）；m0 与 CI 台账见下方（记录写入之后才跑）。 |
| 2026-09-29 | ACTIVE | **cycle 2 CI 台账**：`8fc61bd`（EC-02 实施 `dfac6fa` + 记录 `8fc61bd` 批量一次推送）到终态 —— M0 `36480572117` 八 job 全 `success` + CodeQL `36480572079` 3/3 `success`，两者 `run_attempt=1`（**一次成功、无 flake**；逐 run 由 REST API 实查，复核脚本 `scratch/audit_goal025_ledger.sh`）。 |
| 2026-09-29 | ACTIVE | **cycle 3 CI 台账**：`f31150e`（EC-03 实施 `7e1b16c` + 记录 `f31150e` 批量一次推送）到终态 —— M0 `36489799431` 八 job 全 `success` + CodeQL `36489800413` 3/3 `success`，两者 `run_attempt=1`（**一次成功、无 flake**；逐 run 由 REST API 实查）。 |
| 2026-09-29 | ACHIEVED | **cycle 4（PLAN-20260929-243）：EC-04 = PASS ⇒ GOAL-025 收口**。交付 = `tools/verify_goal025_closeout.py`（**447 行 / 37 判词**）+ `IN_SCOPE` **4 → 5**（纯收紧）+ `RECHECK-244`（`PASS_WITH_WARNINGS`，`W-1`…`W-5`）+ `MEM-166`。**自举复检**：收口前 36 PASS / 1 FAIL（唯一红 = `latest_recheck` 未指向本轮 RECHECK），落地后 **37 PASS / 0 FAIL**。**四道门（本验证器）**全绿 + `tests/tooling/` 三件套 **25 passed**（既有断言一字未改）。**四条 EC 全 PASS**：EC-01 响应头面 / EC-02 正控制矩阵 / EC-03 白名单派生 / EC-04 自举收口；`G24-2` / `G24-3` / `G24-6` **收口**，`G24-1` **离线可判定部分收窄**、真实 runtime / 工具面部分**登记为待取证**；`G24-4` / `G24-5` **原样保留（需用户拍板）**。**未覆盖范围五条逐条明写**（读面未认证 / 多租户 / BOLA·BFLA / 部署面未验证 / R-M1 未收口）。**零产品代码改动**；按压与两树实测以**补记**落下方。 |
| 2026-09-29 | ACHIEVED | **cycle 4 两树复检（收口补记）**：`tools/two_tree_recheck.py --script tools/verify_goal025_closeout.py --script-mode shared --root .` ⇒ 当前树 + 干净 checkout（`git worktree add --detach HEAD`）**判词逐行相同**（各 **37** 条）+ **`sha256` 相同**（`a2ca399e5c22cc53901ccf3fb94366735b6831244187097593206d997ebb1d73`）+ **`TWO-TREE PASS`** / `EXIT=0`；两路留档 `scratch/goal025-c4-verdicts-current.txt` / `…-clean.txt`（`cmp` 二进制一致，各 1 335 B / `CR` 计数 0）；日志 `scratch/goal025-c4-two-tree.log`。**运行发生在收口提交 `57c7134` 之后**（干净树 = 该提交的 checkout）⇒ 该判词描述的是**收口态的树**，不是工作树里的中间态。**本行写在两树之后** ⇒ 依 GOAL-021 的澄清，本地门不覆盖本行；**记录面最终覆盖由 CI 承担**。 |
| 2026-09-29 | ACTIVE | **cycle 3 本地 m0（as-is，记录写入之后）**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = **24**、`FAIL [` = 0、`4755 passed / 21 skipped`、`596.43s`；日志 `scratch/goal025-c3-m0.log`，**文件时刻 `05:46:54` 晚于**本文件最后一次写入 `05:28:05`（`ls -l` 实测）⇒ 门跑在「记录已写完」的状态）。**独占运行**（跑前 `tasklist` 零 python 进程、`research-system-postgres-1` healthy），**进程卫生**：跑完 python 进程 **0**。解释器/口径与 canonical 一致（仓库 `.venv` 经 `uv run --frozen --no-sync python -B`、`--profile m0 --keep-going`、DSN 固化 + `LLM_MAIN_KEY=""`；**本机无 `make`** ⇒ 直跑 Makefile 的同一命令）。**用例数 +12 = 本轮新判据 10 例 + 规模门按文件参数化 2 例**（`test_python_source_limits.py` 对 `PRODUCT_ROOTS` 下**每个** `.py` 参数化 ⇒ 新增两个文件各 +1）。**本行数字写于门之后** ⇒ 依 GOAL-021 的澄清，**不**声称本地门覆盖了本行的最终文本；**记录面最终覆盖由 CI 承担**。**退出码未捕获**（后台分离运行，未回写 `EXIT=`）⇒ 本行**只**记实测到的终态行与分项计数，**不**声称 `EXIT=0`。 |
| 2026-09-29 | ACTIVE | **cycle 3（PLAN-20260929-241）：EC-03 = PASS**（收 `G24-3` 的**路径集合可派生性**这一半；分类面仍是人工判定）。交付 = `read_face_whitelist_derivation.py`（128 行：快照派生 + 框架登记 4 条 + 两向差异 + 下界 `MIN_DERIVED = 40`）+ `test_privacy_read_face_whitelist_derivation.py`（124 行 / **10 例**）+ `RECHECK-242`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-165`。**实跑**：快照 GET **64** + 框架 **4** = 派生面 **68** = 人工清单 **68**，**两向差异 ∅**；独立重算（直读快照 + 正则直读清单，不经被检模块）同值；三条独立路径（快照 / 实时 schema / 运行时路由树）三向全 ∅；快照重生成门 **8 passed** 复核「权威面不漂移」。**三条源码按压先红后绿 + raw `sha256` 逐字节复原**（回到 `ae9bf121…a888`；P3 证明「清单陈旧」那一向承重）。四道门绿；既有判据逐字节未改（`git status --porcelain -- tests/observability` 只有两个新增文件）；`tests/observability/` **134 passed, 1 skipped**（+10）。**零产品代码改动**（权威快照只读）；m0 与 CI 台账见下方（记录写入之后才跑）。 |
