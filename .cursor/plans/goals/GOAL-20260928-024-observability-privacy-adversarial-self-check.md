---
id: GOAL-20260928-024
slug: observability-privacy-adversarial-self-check
title: 观测隐私面对抗性自检（端到端内容金丝雀：出口清单显式分类 + 零命中取证 + 反证按压 + 边界条款与未覆盖面登记）
status: ACHIEVED
created_at: 2026-09-28
updated_at: 2026-09-28
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-28 用户会话指令（goal 模式）：**建档 GOAL-024（观测隐私面对抗性自检：端到端内容金丝雀）
    并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **用户要求「可自我迭代且无需拍板」** ⇒ 本 GOAL 的范围**严格限定**为三件事，**越界即 BLOCKED**：
    **(i) 新增金丝雀判据与夹具**（一律落 `tests/**`，落在既有 `python/tests` 收集面内 ⇒ m0 条数仍 `23`）、
    **(ii) 修被这些判据证明为真缺陷的问题**（**只允许收紧记录面**；**不得**借此改认证 / 策略 / 门禁语义）、
    **(iii) 文档同源更新**（`docs/architecture/OBSERVABILITY.md` / `docs/security/THREAT_MODEL.md` 等 +
    `docs/INDEX.md` 登记）。**不加新能力、不放宽任何判据、不改安全策略、不改任何既有判据。**
    (1) **明确不做（命中即 BLOCKED）**：**给读面（GET/HEAD）加认证**；**多租户 / RBAC /
    organization scope**；**BOLA / BFLA 实现**；**逐调用方身份**；**修改任何既有判据 / 门禁 /
    阈值 / 放行面**（点名：`tests/observability/test_privacy_canary.py`、三道记录面判据、
    多路证据判据、射程边界判据、`tests/tooling/test_tooling_scripts_meet_product_gates.py`、
    `tests/egress_guard.py`）—— **新增**判据可以，**修改**既有判据不行；
    **改 `PRODUCT_ROOTS` / m0 任一 check / 作业结构 / m0 条数**（终态行必须仍是 `23`）；
    **新增依赖**（标准库 + 现有栈）；**做真实出网调用**（本 GOAL 全离线；走 Fake runtime /
    Fake model gateway；真实端点面 / 真实 collector / 部署面只允许「登记为不可在本机验证 +
    给出可复核检查项」）；**让金丝雀携带真实内容**（金丝雀**必须**是测试内构造的合成串；
    **不得**把真实 prompt / token / 凭据写进夹具、记录、日志或输出）；
    **改认证的 401 形态或 `Idempotency-Key` 语义**、**动 `undici`**、**改 `ADR-0031` 的 `Status`**、
    **把真实 runtime 设为默认**；**宣称项目安全**（`R-M1` 仍在）。
    (2) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    + **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）
    + **默认门一律离线**（`tests/egress_guard.py` 是结构判据，**不得**为本地变绿而放宽）。
    (3) **不做真实出网**：本 GOAL **不做真实出网调用**（全离线）；SQL 一律**参数绑定**；
    凭据**只从环境变量**读取；观测隐私按 AGENTS.md §10 —— **默认不记录完整 Prompt、不记录
    模型输入输出、不记录 Tool 敏感参数**（只记录 digest / size / type / latency / token /
    status / redacted metadata）⇒ 本 GOAL 自己的产物**同样**受此约束。
    (4) **边界（必须写清，否则判据会自伤）**：**canonical state（PG 域实体）允许持有用户
    自己的任务输入** —— 那是业务真相，**不是泄漏**；受判面是**非 canonical 出口**：
    telemetry（span / metric / log 三信号）、应用日志、运行目录与证据目录制品、读面响应、
    失败载荷（ProblemDetail / `failure_category` / 异常消息）。**不得**用「金丝雀出现在 DB 里」判红。
    (5) **边界（承继）**：GOAL-001…023 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的**全部 13 项 `D-NN`** 已结清、**本 GOAL 不重开**；
    GOAL-019…023 的**未覆盖范围原样保留**。
    (6) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >
    对「观测隐私」（AGENTS.md §10）做一次**对抗性自检**：证明「沿**默认（离线 Fake 链）
    运行路径**注入的用户内容金丝雀**不出现在任何**非 canonical 出口**」，把**扫描面**做成
    **可复跑判据**，并把**做不到的部分逐条登记**。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**不修改任何既有判据**
    （只**新增**判据）；**零**新依赖；**零**策略面 allow；**不得**给读面加认证；
    **不得**改 401 形态或 `Idempotency-Key` 语义；**不得**宣称项目安全（`R-M1` 仍在）；
    金丝雀一律**测试内构造的合成串**；**全离线**（无真实出网）；m0 条数**仍是 23**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **金丝雀源与出口清单（显式分类，承 MEM-158）**：把「用户内容」在默认（离线 Fake 链）
      运行路径上打上**唯一合成金丝雀**（至少覆盖：任务输入 / prompt、工具参数、工具输出、
      制品正文、证据正文、失败消息），并枚举**全部非 canonical 出口**，逐条**显式分类**为
      **受判** 或 **登记豁免（必须有非空理由）**；分类清单**写在判据源码里**（不靠散文），
      **未分类的新出口判红**（否则新出口会静默逃逸）；登记陈旧（清单里的生产者已消失）同样判红。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_exit_census.py -q`
      ⇒ 全绿；判据源码内含机器可读的出口登记表（kind / producer / classification / reason /
      observation）；按压（新增一个未登记的生产者 ⇒ 判红）与（豁免条目理由抽空 ⇒ 判红）先红后绿，
      逐字节复原（raw `sha256` + 二进制读写）。
    status: PASS
  - id: EC-02
    criterion: >-
      **端到端取证 + 反证 + 按压（主干）**：(a) 跑一次默认运行（离线、Fake runtime）⇒ 对
      **全部受判出口**扫描 ⇒ **金丝雀零命中**；本期至少覆盖 OTLP wire（traces + metrics）、
      **应用日志**（`caplog` 口径）、运行 / 证据目录制品（指向 `tmp_path`）、读面响应、
      失败载荷；(b) **反证必须有牙齿**：人为把金丝雀塞进一个**允许键**（如 `endpoint_id`）
      或写进一条日志行 ⇒ 判据**判红**且失败消息**点名出口与键名** ⇒ 逐字节复原（raw `sha256`
      + 二进制读写）⇒ 复绿；(c) **受判面非空**（承 MEM-156）：断言「受判出口数 ≥ 1 且每个受判
      出口在**本次运行中真的被观测到**（非空集）」，否则判红；并证明扫描面**不是**靠话题词喂饱
      （承 MEM-141）：改措辞**不改变**判据结论（实测留档）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_content_canary_end_to_end.py -q`
      ⇒ 全绿；配套留档：零命中扫描证据（逐出口命中数）、反证红（点名出口与键名的失败消息）、
      复原后 raw `sha256` 回到原值、非空取证（每个受判出口的观测计数）、措辞替换对照结论。
    status: PASS
  - id: EC-03
    criterion: >-
      **边界条款 + 未覆盖面登记（条款不得悬空）**：把两条界线写成**文档条款**并由**判据钉住**
      （被点名判据文件**必须存在**，改名即判红）：① **canonical 允许持有用户输入**（业务真相，
      不算泄漏）；② **非 canonical 出口不得含内容**。同时**逐条登记未覆盖面**：debug mode 的
      受控采样（§10 允许、受 retention 管理）**未验证**、真实 collector / 生产部署面**未验证**、
      CI 产物面**不在射程**、`R-M1` 未收口 ⇒ **不得**宣称项目安全。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_boundary_clauses_are_pinned.py -q`
      ⇒ 全绿（含被点名判据文件存在性 + 条款锚点 + 未覆盖面四条逐条在位）；文档同源更新落在
      `docs/architecture/OBSERVABILITY.md` / `docs/security/THREAT_MODEL.md`（+ `docs/INDEX.md` 登记），
      治理 `validate.py` 的 `DOCS-CHECK` 绿。
    status: PASS
  - id: EC-04
    criterion: >-
      **自举收口（复用 022 / 023 的机器）**：① 本轮收口验证器**进树**
      （`tools/verify_goal024_closeout.py`，**复用** `tools/closeout_recheck_assertions.py` 的公共判词，
      只写本轮特有断言），并**显式加入** `tools/` 受判面的**必备清单**；② 用
      `tools/two_tree_recheck.py` 跑**当前树 + 干净 checkout** ⇒ 两树同结论（逐行相同 +
      `sha256` 相同；**留档一律二进制写盘**）；③ **as-is 本机 m0 到 23/23**
      （终态行 `PASS: profile=m0; 23 deterministic checks`），**运行发生在记录写入之后**（承 MEM-145）；
      ④ 治理 `validate.py` 绿（含 `DOCS-CHECK`）；⑤ CI 台账到终态（八 job + CodeQL + `run_attempt`）；
      ⑥ 承继残余逐条在位（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` /
      `W-6` / `W-10` / `W-11` / `W-12`）+ 本轮新增残余；⑦ **未覆盖范围五条逐条明写**
      （读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal024_closeout.py
      --script-mode tree` ⇒ 两树判词逐行相同 + `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；
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
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/observability/test_privacy_canary.py`、
      三道记录面判据、多路证据判据、射程边界判据、`tests/tooling/test_tooling_scripts_meet_product_gates.py`、
      `tests/egress_guard.py`）—— **新增**判据不受此限
    - >-
      把**真实** prompt / token / 凭据 / 用户内容写进夹具、记录、日志、遥测或以任何形式留档
      （金丝雀一律**测试内构造的合成串**；凭据只登记变量名、绝不留值）
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
      （canonical 允许持有用户自己的任务输入：那是业务真相，**不是泄漏**）
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
    **宣称项目安全**或据此收口 `R-M1` —— **立即 BLOCKED**（Mimosa 钩子
    `scanner_enobufs` 未得完整结论）
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
child_plans:
  - .cursor/plans/tasks/PLAN-20260928-227-goal-024-ec01-privacy-exit-census.md
  - .cursor/plans/tasks/PLAN-20260928-229-goal-024-ec02-content-canary-end-to-end.md
  - .cursor/plans/tasks/PLAN-20260928-231-goal-024-ec02-read-face-canary.md
  - .cursor/plans/tasks/PLAN-20260928-233-goal-024-ec03-boundary-clauses-pinned.md
  - .cursor/plans/tasks/PLAN-20260928-235-goal-024-ec04-closeout-two-tree-self-bootstrap.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-236-goal-024-ec04-closeout-two-tree.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-161-exit-census-must-be-a-partition-with-reasons.md
  - .cursor/memory/entries/MEM-20260928-162-read-face-zero-hit-needs-a-bounded-whitelist.md
---

## 目标与退出标准

**一句话**：对 AGENTS.md §10（观测隐私）做一次**对抗性自检** —— 沿**默认（离线 Fake 链）**
运行路径注入**唯一合成内容金丝雀**，证明它**不出现在任何非 canonical 出口**；把这件事做成
**可复跑的判据**（出口清单显式分类 + 零命中扫描 + 反证按压 + 非空取证），把**做不到的部分
逐条登记**，并把两条边界写成**不悬空的条款**。

**本 GOAL 不加新能力、不改安全策略、不放宽任何判据、不修改任何既有判据。**
若新判据**证明**某处是真缺陷 ⇒ **只允许按授权收紧记录面**（**不得**借此改认证 / 策略 /
门禁语义）；若某条**本机无法验证** ⇒ **登记为 PENDING**，**不得**记 PASS。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **出口清单显式分类**（金丝雀源 + 全出口 `受判/豁免` + 未分类判红 + 陈旧判红） | 新判据（登记表在源码里）+ 新夹具 + 按压 | **PASS** |
| EC-02 | **端到端取证 + 反证 + 按压**（零命中 + 反证红 + 逐字节复原 + 非空取证） | 端到端金丝雀判据 + 扫描证据 + 反证记录 | **PENDING** |
| EC-03 | **边界条款 + 未覆盖面登记**（被点名判据存在 + 条款锚点 + 四条未覆盖面） | 文档条款 + 钉住判据 + `docs/INDEX.md` | **PENDING** |
| EC-04 | **自举收口**（进树验证器 + 两树 + m0 23/23 + 台账 + 残余） | `tools/verify_goal024_closeout.py` + 两树留档 + 台账 | **PENDING** |

**依赖关系**：EC-01 → EC-02（出口清单是扫描面与「受判出口非空」断言的输入）→ EC-03（条款
点名 EC-01 / EC-02 的判据文件）→ EC-04（**依赖 EC-01 + EC-02 + EC-03**：收口验证器要断言
前三者的终态与登记面）。EC-04 的 as-is m0 **必须**在记录写入**之后**跑（承 MEM-145）。

**建档当日已核实的事实层结论（全部实测，非推测；决定可行性与判据形态）**：

1. **既有判据与其交出的那一半（实测复核）**：`tests/observability/test_privacy_canary.py`
   = **212 行**（`wc -l`）；其 docstring 第 17–19 行把「把内容硬塞进 identity 字段
   （例如往 `endpoint_id` 里写 prompt）」判为**调用方误用**、词汇层无法在不使自身失效的前提下
   消除 ⇒ **产品代码会不会这么做，从未被验证** —— 这正是本 GOAL 的**主靶**。
   **既有判据与夹具**（`test_privacy_canary.py` / `canary_support.py` / `otlp_receiver.py`）
   **只读**（`fix_policy.forbidden` 已点名）。
2. **「日志面几乎空白」实测成立**：`rg -ln "caplog|capsys" tests` **只命中 1 个文件**
   （就是上面那个 `test_privacy_canary.py`）⇒ 全仓的**应用日志面几乎无内容扫描**。
3. **既有夹具的规模余量很薄**：`tests/observability/canary_support.py` = **349 行**
   （规模门：硬上限 450、>300 软告警）⇒ 它是**只读**的既有夹具，**新夹具必须落新文件**
   （不得把 349 推向 450）。
4. `tests/observability/otlp_receiver.py` = **120 行**；只接受 `POST /v1/traces` 与
   `POST /v1/metrics`（其他路径 404）—— 它是本仓**证据级** OTLP 接收器（loopback + 真实
   protobuf 解码），**不需要外部 collector**。
5. **本仓不存在 OTLP logs 信号（实测，且与用户口径不同，必须改述）**：
   repo-wide `rg "LoggerProvider|OTLPLogExporter|v1/logs"` **零命中**；依赖里只有
   `opentelemetry-exporter-otlp-proto-http` 的 trace/metric 面 ⇒ 本 GOAL 的「三信号」口径
   **必须**写成 **OTLP traces（wire）+ OTLP metrics（wire）+ stdlib 应用日志（进程内）**；
   第三面**不是** OTLP logs 通道。判据**不得**按「OTLP logs 出口」建面（会落在空集上）。
6. **默认 telemetry 是 `NullTelemetrySink`**（`OtelSettings.enabled=False`）⇒ **as-is 默认
   路径上根本没有 OTLP wire**；判据**必须显式注入**真实 OTLP sink（配 `otlp_receiver.py`）
   才能让该出口**非空**（承 MEM-156：受判集合非空是交付前提）。
7. **应用日志出口的生产者有界（实测）**：产品根下 `logging.getLogger` 恰 **2 处**
   （`services/api/app.py:63`、`services/api/experiment_queue.py:40`）；全仓**无**
   `basicConfig` / `dictConfig` / `fileConfig` ⇒ 日志面是一个**小而可枚举**的普查面。
8. **一个必须实测的真候选（不预设结论）**：`services/api/experiment_queue.py:175` 的 warning
   把 `_short_reason(exc)`（`str(exc)`，上限 500 字符）写进日志行，而该异常来自 run 启动 /
   协议解析路径 ⇒ **调用方提供的文本有路径进入应用日志面**。判据必须**先测**再判；
   若判据证明它收进了内容金丝雀 ⇒ 按授权**只允许收紧记录面**（登记为真缺陷）。
9. **stdout/stderr 出口有界（实测）**：产品根内 `packages/` 与 `services/api/` 的 `print(...)`
   **各 0 处**；14 处只在 worker 进程 / CLI / 容器内探针（非默认运行路径的进程内面）。
10. **失败载荷面有两处形态差异（实测，重点受判）**：`services/api/errors.py` 的**通用** handler
    对 `str(exc)` 走 `redact_text`；而 **`ApiError` handler 不再脱敏** `api_error.detail`
    ⇒ 路由里以 `str(exc)` 填充的 `detail` 会**原样**进 `ProblemDetail` ⇒ 判据必须覆盖它。
11. **读面出口以运行时路由表为准（实测）**：`services/api/routers/` 下 **30 个模块**；
    判据应枚举**应用自身路由**（`create_app(...).routes`）而不是散文清单 —— 这样**新增路由**
    会自然进入扫描面。
12. **默认（离线 Fake）全链驱动点至少两个（实测）**：(a) `tests/api/run_fixtures.py`
    的 `make_run_ready_deps()`（Fake runtime + FakeModelGateway + SQLite `:memory:`；`run_ready_client`
    起 `TestClient`，run 收敛到终态 `FAILED`）；(b) `tests/e2e/scenario.py` 的
    `StructuredOutputAgentRuntime` + `M7Harness`（可离线跑到 `SUCCEEDED`，把**合成的**结构化输出
    落成**制品正文**）⇒ 内容金丝雀可走「任务输入 → LLM 响应 → 制品 → 读面」整链。
13. **磁盘出口必须被指到 `tmp_path`（实测风险）**：`SqliteArtifactStore` 无 `blob_dir` 时落
    `cwd/.artifacts`（仓库里 `.artifacts/` 已存在）；默认 SQLite 装配落
    `data/artifact-blobs/<digest[:2]>/<hex>` ⇒ 判据**不得**在仓库根留写盘面。
14. **`tools/` 受判面的下界断言是单调的（实测，决定 EC-04 可行）**：
    `tests/tooling/test_tooling_scripts_meet_product_gates.py`（283 行）断言
    `required ⊆ IN_SCOPE` 且 `IN_SCOPE ⊆ scope()`（`IN_SCOPE` 现为 **3** 条）⇒
    把 `tools/verify_goal024_closeout.py` **加进必备清单是纯收紧、无需改既有断言**
    （承 MEM-160：下界必须由**源码清单**给出，文档点名只是并集的一半）。
15. **规模门禁对 `tests/**` 生效（实测）**：`PRODUCT_ROOTS` 含 `tests` ⇒ 新判据与新夹具同样
    受 **450 行文件 / 50 行函数** 门（>300 行软告警）；`tools/verify_goal024_closeout.py`
    还受 EC-02 判据的**四道门**（格式 / `ruff` / 规模 / `mypy`）。
16. **记录面话术判据的扫描面含 `.cursor/plans`** ⇒ 本文件与后续记录**不得**出现肯定式的
    越级表述（口径词是「**可重复配置**」；`test_reproducibility_wording.py` 认引号字符，
    反引号不算引用）。
17. **工作树现状（实测，供驱动遵守）**：`git status` 有 **4 个与本 GOAL 无关**的并发改动
    （`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
    `services/api/dto/models.py`、`services/api/middleware.py`），其 worktree 与 index
    **内容哈希相同**（`git hash-object` = index blob；`git diff --numstat` 为空）⇒ 只是行尾态
    差异。**本 GOAL 一律只用显式路径提交**，**绝不** `git add -A`，**绝不**碰这 4 个文件。

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

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-024-*.md` 已存在 ⇒ 跳过建档，直接进循环。
**建档方式**：本 GOAL 采用「**新建 GOAL-024**」（**不是**把任何既有 GOAL 置回 ACTIVE）。
理由：观测隐私的**对抗性自检**（内容金丝雀沿默认路径端到端取证）在 GOAL-001…023 里
**从未**作为交付面出现过 —— M15 WP4 交付的是**词汇层**（无内容通道 + 键集闭合），并**明文**
把「内容被塞进允许键」这一半交给调用方；本 GOAL 正是去**验证那个空白**。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-20260928-024` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
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

- **受判对象非空（承 MEM-156）**：EC-02 的判据**必须**在**本次运行**里真的观测到**每个**
  受判出口（逐出口观测计数非空），否则判红；交付时**不得**出现「受判集合为空」的空真。
- **反证两向（承 MEM-159）**：既证「**该判红时会红**」（内容进允许键 / 进日志行 ⇒ 判红且
  点名出口与键名），也证「**不该红时不红**」（把内容放进 **canonical** ⇒ **不**判红）。
- **射程不得靠并集掩蔽（承 MEM-160）**：出口清单的**下界**必须由**判据源码里的必备清单**给出，
  并有专门断言钉住它；文档点名只作并集的一半。
- **按压 → 逐字节复原必须 raw `sha256` + 二进制读写**（承 MEM-152）：任何留档（判词 / 日志 /
  证据）**都不得**用文本模式写盘；按压 / 复原**一律用 Edit 工具**（不用 Bash 写源码）。
- **判据自身恒真（承 MEM-141）**：新判据**不得**被文档引用 / 字面量喂饱——出口面绑**运行时
  路由表 / 真实发射点 / 文件面（AST）**，且**必须被按压过**（先红后绿 + 逐字节复原）。
- **改工具先数夹具**：EC-04 若要动 `tools/two_tree_recheck.py` 或其契约，先确认
  `tests/tooling/test_two_tree_recheck_entry.py`（11 例）与
  `tests/tooling/test_closeout_assertions_are_in_tree.py`（6 例）**断言一字不改且全绿**。
- **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
- **进程卫生（承 GOAL-020 的 96 孤儿教训）**：起子进程的脚本 teardown **必须连整棵树**
  （Windows 用 `taskkill /T /F`），跑完复验**零泄漏**。
- **本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据**必须在 Linux 侧复验**
  （由 CI 承担；本地按同一形态自查）。
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
  本 GOAL 的收口判词**必须**写明：**① 受判出口清单（受判 / 豁免逐条与其理由）**、
  **② 金丝雀零命中与反证红的实跑证据（含点名出口与键名的失败消息）**、
  **③ 两树实跑证据（逐行 + `sha256`）**、**④ 按压与逐字节复原记录（raw `sha256`）**、
  **⑤ as-is 本机 m0 的终态行与「门在记录之后」的时刻证据**、
  **⑥ 未覆盖范围（五条）与未覆盖面登记（四条）**、**⑦ 新增残余登记**。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**给读面加认证**、**引入多租户 / RBAC**、
  **做 BOLA·BFLA 实现**、**新增依赖**、**把真实内容 / token 写进任何地方**、**改 401 形态或
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

**承继：GOAL-019 / 020 / 021 / 022 / 023 的残余 —— 原样保留（本 GOAL 只登记现状，不改其状态）**

| 残余 | 内容 | 本 GOAL 的姿态 |
| --- | --- | --- |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（本 GOAL 不碰认证面） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留** |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **原样保留**（本轮**不**把它变成已验证；真实 collector / 部署面同样只登记） |
| `W-4` / `W-5` / `W-6` | 本机 m0 同进程跑阈值判据 / 新作业多一次冷装 / `live_run_support.py` 零余量 | **原样保留** |
| `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` | Mimosa 结论未完整 / `undici` 归上游 / 非 ASCII 路径豁免 / 主观面先操作化 / 规模不足的诚实边界 | **原样保留** |
| 历史遗留 **37** 个 `tools/` 脚本仍无机器门 | GOAL-023 `W-1` 的有界射程 | **原样保留**（本 GOAL 只把**本轮新增的**验证器加入必备清单） |
| 四条历史收口复检**不可回填** | GOAL-023 新增② | **原样保留** |
| 可复跑性 ≠ 跨平台复验 | GOAL-023 新增③ | **原样保留**（本机只在 Windows 实跑；跨平台由 CI 承担） |
| `W-1`（GOAL-021） | 脱敏是**形态匹配而非值匹配** ⇒ 裸不透明串放在允许键内会原样导出 | **本 GOAL 的主靶之一**：EC-02(b) 用「内容进允许键 ⇒ 判红」把这条**变成机械事实**（条款本身不收口） |

**本 GOAL 特有边界（= 用户判词的「明确不做」清单，命中即 BLOCKED）**：

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
13. **`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论）**——**不得**据此宣称项目安全；
14. **`ADR-0031` 的 `Status`**——**不动**（维持 `Proposed`）；
15. **`undici` 的 pin**——**不动**（归属上游）；
16. **默认 runtime**——**必须仍是 Fake**；**默认 CI 必须离线**；
17. **把新判据写成「被文档引用 / 字面量喂饱」的形态**——**不做**（承 MEM-141）；
18. **用「金丝雀出现在 canonical」判红**——**不做**（canonical 允许持有用户自己的任务输入）；
19. **宣称项目安全**（`R-M1` 仍在）——**不做**。

**本 GOAL 交付的是「观测隐私的对抗性自检证据 + 可复跑扫面」，不是「隐私已完备」**：

- EC-01 让**出口面显式分类**，但**不**证明每个豁免条目的豁免永远成立（豁免是**有理由的
  登记**，不是证明）；
- EC-02 只覆盖**默认（离线 Fake）路径**上与**本次注入**的金丝雀形态可达的出口；
  **debug mode 的受控采样**（§10 允许、受 retention 管理）**不在射程**；
- EC-03 的条款只把**两条界线**钉住，**不**替代 `R-M1`，**不**等于「数据不会泄漏」。

**本轮新增残余（收口登记；如实保留，不是待办）**：收口时逐条写入
（形如：豁免条目的时效性 / debug 采样未验证 / 真实 collector 与部署面未验证 /
CI 产物面不在射程）。


### 本轮新增残余（GOAL-024 收口登记）

| ID | 残余 | 处置 |
| --- | --- | --- |
| `G24-1` | **四个金丝雀源在默认离线链上没有注入面**（`task_input` / `tool_arguments` / `tool_output` / `failure_message`）⇒ 这四源「不出现在非 canonical 出口」**未验证** | 原样登记；真实 runtime / 工具面启用后需重新取证 |
| `G24-2` | 读面扫描**只扫响应体、响应头不在面**（`Content-Disposition` 文件名 / `ETag` 等未证伪） | 原样登记 |
| `G24-3` | 读面**白名单是人工判定 + 机械自审**（上下界 + 实取核对），不是从契约自动推导 | 原样登记（`RECHECK-232` 的 `W-6`） |
| `G24-4` | `LineageNodeDto.label` 字段名与内容语义不一致（实测承载 claim 正文） | 原样登记（`RECHECK-232` 的 `W-1`）；**未改产品** |
| `G24-5` | 文档**条款是文档 + 判据形态**，**不是运行时拦截器** | 原样登记（`RECHECK-234` 的 `W-3`） |
| `G24-6` | 6 条声明载体本轮无正控制（模板 ×2 / 记忆 / 交付物 / 库 ×2）、3 条路由取不到 | 原样登记（`RECHECK-232` 的 `W-3`/`W-4`） |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 本行所在的**建档提交** `354e657` + 本行所在的**记录提交** | 治理 `validate.py` = `Cursor 治理验证通过`（8 行结论，含「GOAL 循环记录结构合规；push 授权显式登记」）；**记录面判据**（`test_reproducibility_wording.py` + `test_record_face_is_covered_by_the_gate.py` + `test_control_plane_auth_same_source.py`）= **24 passed**（与 GOAL-023 基线同值）；**as-is 本机 m0（记录写完之后、独占运行、仓库 `.venv`、DSN 固化 + `LLM_MAIN_KEY=""` + `--keep-going`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、`4665 passed / 21 skipped`、`EXIT=0`；日志 `scratch/goal024-c0-m0.log`，耗时 `618.83s`，**文件时刻 `19:00:54` 晚于**本文件最后一次写入 `18:44:26` ⇒ 门在记录之后，可用 `ls -l` 复核）；**进程卫生**：跑完后 `tasklist` python 进程 **0**。**本机无 `make`** ⇒ 用 Makefile 的同一命令直跑 `run_all_checks.py --profile m0 --keep-going`（同解释器、同 DSN 固化、同 `--keep-going`，与 canonical 调用等价）。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账）；建档提交 `354e657` 的台账见下表 | 建档轮**零产品代码改动**（只新增本文件） | EC-01…EC-04 全 PENDING。起点已定位：**本仓无 OTLP logs 信号** ⇒ 三信号口径必须改述为 traces + metrics（wire）+ stdlib 应用日志（进程内）；**默认 telemetry 是 `NullTelemetrySink`** ⇒ 判据必须显式注入真实 sink 才能让该出口非空；`canary_support.py` **349 行**（只读、余量薄）⇒ 新夹具落**新文件**；日志面生产者在产品根下**仅 2 处** ⇒ 可枚举 | cycle 1 = **EC-01**（出口清单显式分类；它是 EC-02 扫描面与非空断言的输入） |
| 1 | PLAN-20260928-227（EC-01） | 本行所在的**实施提交**（2 个进树判据文件）+ 本行所在的**记录提交** | **EC-01 全部验收成立且有实跑证据**。交付 = `tests/observability/privacy_exit_census.py`（**259 行**：AST 形态谓词 + 扫描根 + 分区/清单/下界机械部分）+ `tests/observability/test_privacy_exit_census.py`（**407 行**：`EXIT_SURFACES` / `EXEMPT_PRODUCERS` / `REQUIRED_JUDGED_EXITS` / `CANARY_SOURCES` / `UNCOVERED_SHAPES` **全在判据源码里**，**13 例**）+ `RECHECK-20260928-228`（`PASS_WITH_WARNINGS`，`W-1`…`W-6`）+ `MEM-20260928-161`。**普查剖面（实跑）**：**113 个候选**（`application_log` 2 / `stdout` 4 / `otlp_span` 12 / `otlp_metric` 11 / `disk_write` 8 / `read_face` 29 / `failure_payload` 47）**全部被恰好一条显式分类认领** —— 受判出口 **6** + 豁免出口 **1**（`stdout-stderr`：默认进程内路径**零生产点**）+ 豁免生产者 **25**（逐条带理由）；未机械枚举的形态 **4** 条带理由登记。**四向按压全部先红后绿 + 逐字节复原**：P1 **真实产品根**新建只含 `print` 的模块 ⇒ `未分类的非 canonical 出口:packages/application/observability/press_probe_module.py [stdout]`；P2 受判面生产者清单删一行 ⇒ `未分类…services/api/scheduler.py [otlp_span]`；P3 `_REASON_CLI` 抽空 ⇒ 两条 `缺少理由`；P4 下界加一条非受判 id ⇒ `必备受判出口缺失:['stdout-stderr']`；四条均 `1 failed, 12 passed`，复原后 raw `sha256` **回到** `076fad378c48c794df3fa4e672614a7e379f10bc69f2e81d7eb5e7ce42aac74f`（`MATCHES_BASELINE True`）⇒ **13 passed**；P1 复原后 `git status` 对该路径**为空**。**判据自跑抓到两处自己的真错并当场修掉**：重复分类（`adapters/otel/failsafe.py` 同时被受判面与豁免面认领）与形态自检样本位形写错（`read_face` 写成赋值式而非装饰器）。**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；规模 259 / 407 行、超 50 行函数 **0**（407 > 300 触发软告警，如实登记）；`mypy` = `Success`。**既有隐私判据逐字节未改**且合跑 **20 passed**（13 新 + 7 既有）。**零改动面**：`PRODUCT_ROOTS` / m0 条数（**仍 23**）/ 作业结构 / 依赖 / 产品代码 / 既有判据**全部零改动**。**as-is 本机 m0（记录写入之后、独占运行、仓库 `.venv`、DSN 固化 + `LLM_MAIN_KEY=""` + `--keep-going`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4680 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal024-c1-m0.log`，耗时 `576.02s`，**文件时刻 `20:07:51` 晚于**记录最后写入 `19:54:27`（RECHECK）⇒ 门在记录之后；跑完 `tasklist` python 进程 **0**。用例较交付前 **+15** = 新判据 **13** 例 + 两个新文件进入既有规模门判据的参数化面 **2** 项；日志里可见新判据的 13 个点与 `407 行 > 300` 的**软告警**（非失败，如实登记））。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账） | **零真缺陷**；修掉的是**本判据自己清单里的两处错**（重复分类 / 样本位形），由判据自跑抓到 | **EC-01 = PASS**。**如实登记六条警告**（`RECHECK-228`）：**`W-1`（最要紧）普查是「形态驱动」的**（`UNCOVERED_SHAPES` 四条不判；`disk-run-artifacts` 受判生产者**只有 1 条**）⇒ 磁盘面射程**窄**；`W-2` `stdout-stderr` 是**豁免**出口，「对内容可见」只能靠 EC-02 的正控制证明；`W-3` 豁免理由是**有理由的登记而非证明**（没有机械证明它们**永不**进入默认路径）；`W-4` 射程只看 `(module, kind)` ⇒ **同模块内新增同形态发射点**不产生新的分类需求（漏的是**位置**而非形态）；`W-5` 407 行触发规模软告警（非失败）；`W-6` 本条不含任何认证面 / 授权面结论 | cycle 2 = **EC-02**（端到端取证 + 反证 + 按压：沿默认离线 Fake 链注入内容金丝雀 ⇒ 对 6 条受判出口逐面扫描零命中 + 每个受判出口给出**可见性正控制** + 反证红并点名出口与键名 + 逐字节复原） |
| 2 | PLAN-20260928-229（EC-02，**部分**） | 本行所在的**实施提交**（2 个进树判据文件）+ 本行所在的**记录提交** | **EC-02 的编排层一半有实跑证据，读面一半未观测 ⇒ EC-02 未达成（不得记 PASS）**。交付 = `tests/observability/content_canary_support.py`（**212 行**：7 条合成金丝雀 + 默认离线 harness（真实 OTLP sink 只发 loopback、制品根指向临时目录）+ 纯函数扫描器）+ `tests/observability/test_privacy_content_canary_end_to_end.py`（**246 行 / 10 例**）+ `RECHECK-20260928-230`（`PASS_WITH_WARNINGS`）。**实跑**：`egress guard: judged 168 connection attempt(s); blocked 0`（全 loopback）；运行真的产生 OTLP wire（`research_os.` 前缀可见）与制品 blob 命中 `artifactbody`；**应用日志本次 4 条**（日志面零命中**非空真**）。**绝对面零命中**：traces / metrics wire、应用日志、失败载荷、stdout+stderr。**载体白名单**：制品 blob **只**承载制品正文金丝雀。**每条通道可见性正控制**（遥测 ×2 / 日志 / stdout / 磁盘）全绿。**反证两向**：内容进允许键 `endpoint_id` ⇒ 判红并点名键名与出口；内容进日志行 ⇒ 判红并点名 `application-log`；内容进 canonical / 声明过的载体 ⇒ **不**判红。**措辞无关**（同 token 三种措辞 ⇒ 结论不变）。**终态如实登记**：两个分支都收敛 `FAILED`（默认 Fake 交付物声明与合约不合 ⇒ 验收门判拒，**门未被放宽**）。四道门：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；规模 212 / 246 行、超 50 行函数 **0**；`mypy` = `Success`。**既有隐私判据逐字节未改**；`tests/observability/` 全目录 **81 passed, 1 skipped**。**as-is 本机 m0（记录之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4692 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal024-c2-m0.log`，耗时 `619.29s`；用例较上轮 **+12** = 新判据 10 例 + 新文件进规模门参数化面 2 项）。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账） | 零真缺陷；未改任何既有判据 | **EC-02 未达成**。**如实登记六条警告**（`RECHECK-230`）：**`W-1`（最要紧）读面 `read-face-http` 未观测**（判据源码里登记 `NOT_YET_OBSERVED`）⇒「全部受判出口零命中」**尚不成立**；`W-2` 两个分支都收敛 `FAILED` ⇒ 覆盖的是**判拒路径**，`SUCCEEDED` 路径未验；`W-3` 真正注入运行的只有**制品正文**一条金丝雀（其余六条只在正控制与反证里用）⇒「六源全部注入」未达成；`W-4` 测试接收器不按信号分桶保存原始字节 ⇒ 两个 wire 出口扫的是同一份合并字节（更严但不独立）；`W-5` `shutdown can only be called once` warning 未追因；`W-6` `stdout-stderr` 仍是 EC-01 的豁免出口。 | cycle 3 = **EC-02 续**（应用级装配：`create_app` + `TestClient` 读面路由扫描 + 任务输入/prompt 等其余金丝雀经 `POST /protocol-drafts` 的 `yaml_text` 与失败注入进链），补齐后 EC-02 才可记 PASS |

| 3 | PLAN-20260928-231（EC-02 **余下 / 读面**） | 本行所在的**实施提交**（3 个进树判据文件）+ 本行所在的**记录提交** | **读面从 `NOT_YET_OBSERVED` 变成实取判据**（EC-02 记 PASS）。交付 = `tests/observability/read_face_canary_support.py`（294 行：应用级装配 = 既有夹具 + 换入金丝雀 runtime + `create_app` + `TestClient`；canonical 注入 = 草稿正文（用户起草的协议 YAML，随 run 冻结）+ 两份制品（含 diff 伙伴）+ evidence/claim；路由树枚举；逐路由实取与扫描纯函数）+ `tests/observability/read_face_route_registry.py`（294 行：**68 条读路由逐条判定** = 声明载体 15 / 零命中 53，外加分区自审与命中核验两条纯函数 + 上下界）+ `tests/observability/test_privacy_read_face_canary.py`（200 行 / **10 例**）。**读面口径（白名单）**：内容出现在**契约声明返回内容**的路由上 = 业务真相；其余路由**必须零命中**。**实跑**：canonical 侧**确有**三种金丝雀（直接读存储对象：草稿正文 / 制品正文 / claim 正文）；零命中面 **51/53** 条取到非空响应（另 2 条 workspace 快照无对象 ⇒ 逐条登记）⇒ **零越界**；声明载体 **9** 条正控制全绿（草稿 ×3 / 制品 ×2 / claims / export / run 级与项目级 lineage ×2）。**两向反证**（零命中路由出现金丝雀 ⇒ 点名路由与 kind；声明载体看不到声明内容 ⇒ 判红）+ **两向按压**（真实应用上新增未登记路由 `/__press-probe` ⇒ 分区判红点名；登记里出现树里没有的路径 ⇒ 陈旧判红）。**实测抓手**：`LineageNodeDto.label` **真的**承载 claim 正文（字段名 `label` ≠ 内容语义）⇒ 据实登记为声明载体并写进 `W-1`（未改产品代码）；`/projects/{id}/protocol-drafts` 契约明文「不含正文」⇒ 零命中**是断言**而不是巧合。四道门：`ruff format --check` = `3 files already formatted`；`ruff check` = `All checks passed!`；规模 294/294/200 行、最长函数 35/11/22 行；`mypy` = `Success`。**既有隐私判据逐字节未改**（只 import 复用）；`tests/observability/` 全目录 **91 passed, 1 skipped**。**as-is 本机 m0（记录写入之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4705 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal024-c3-m0.log`，耗时 `623.55s`；上一轮 cycle 2 为 4692 passed ⇒ 本轮 **+13** = 新判据 10 例 + 新判据文件进规模门等参数化面 3 项）。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账） | 零真缺陷；未改任何既有判据 | **七源注入面逐条登记**（`CANARY_SOURCE_INJECTION`）：注入 3（`prompt_text` / `artifact_body` / `evidence_body`）；**无注入面 4**（`task_input` / `tool_arguments` / `tool_output` / `failure_message` —— 默认离线链上没有这些内容的承载体，**未验证**而非判绿）。**`RECHECK-20260928-232` 八条警告全留位**：`W-1` `label` 字段名与内容语义不一致（将来按字段名推断会误判）；`W-2` 四个源没有注入面；`W-3` 6 条声明载体本轮无正控制（模板 ×2 / 记忆 / 交付物 / 库 ×2）；`W-4` 3 条路由取不到（2 条零命中 workspace 快照 + 1 条声明载体 `/library/{resource_id}`）；`W-5` 只扫响应体、**响应头不在面**（未证伪）；`W-6` 白名单是人工判定 + 机械自审，不是契约自动推导；`W-7` 自举收口待 EC-04；`R-M1` 未收口。 | cycle 4 = **EC-03**（边界条款 + 未覆盖面登记，判据钉住被点名的判据文件） |
### CI 台账（逐 run 逐 job 实查；全部落在 main）
| 4 | PLAN-20260928-233（EC-03） | 本行所在的**实施提交**（文档两节 + 新判据 + INDEX）+ 本行所在的**记录提交** | **条款落文档并由判据钉住**（EC-03 记 PASS）。交付 = `docs/architecture/OBSERVABILITY.md` 追加「观测隐私边界与受判面（GOAL-024，2026-09-28）」节（两条条款 + 6 条受判出口 + 读面白名单口径 + 5 个被点名判据文件 + 四条未覆盖面逐条）；`docs/security/THREAT_MODEL.md` 追加第 7 节（同源两条条款 + 钉点 + 未覆盖面同口径 + 不得宣称项目安全）；`docs/INDEX.md` 两处登记；`tests/observability/test_privacy_boundary_clauses_are_pinned.py`（**145 行 / 9 例**）。**判据形态**：条款锚点**逐字**同时出现在两份文档（缺一处判红）；受判面与口径锚点；四条未覆盖面逐条在位；零夸大锚点各一份；**被点名的 5 个判据文件存在性**（改名即判红，含判据点名自己）；INDEX 登记；两条按压（改名判红、条款被改写判红）。**实跑**：钉点判据 **9 passed**（0.06s）；`tools/docs_consistency_check.py` = `DOCS-CHECK PASS: 6 deterministic checks`；`ruff format --check` / `ruff check` = `All checks passed!`；规模 145 行、最长函数 **10 行**；`mypy` = `Success`；既有文档只**追加**（§6 授权面草案与 M15/M16 段一字未动）；`tests/observability/` 全目录 **100 passed, 1 skipped**。**as-is 本机 m0（记录写入之后）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4715 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal024-c4-m0.log`；较 cycle 3 的 4705 passed **+10** = 本轮新判据 9 例 + 新判据文件进规模门等参数化面 1 项）。 | 本行所在的**记录提交**（依固定口径其 CI run 只在回合汇报记账） | 零真缺陷；未改任何既有判据 | **四条未覆盖面逐条登记**（文档内 `未覆盖面 1..4`）：debug mode 受控内容采样**未验证**；真实 collector / 生产部署面**未验证**；CI 产物面**不在射程**；`R-M1` **未收口**。`RECHECK-20260928-234` 四条警告留位（`W-1` 锚点逐字 ⇒ 文档措辞变动需同步判据；`W-2` 未覆盖面只承诺「未验证」、不承诺「将来也不会」；`W-3` 条款是文档 + 判据形态、**不是运行时拦截器**；`W-4` 承 `RECHECK-232` 的 `W-1`…`W-7`）。 | cycle 5 = **EC-04**（自举收口：`tools/verify_goal024_closeout.py` 进树并入 `IN_SCOPE` 必备清单 + 两树复检逐字节一致 + 终态台账） |

| 5 | PLAN-20260928-235（EC-04，**收口**） | 本行所在的**实施提交**（`tools/verify_goal024_closeout.py` + `IN_SCOPE` + 4 个记录文件）+ 收口补记提交 | **自举收口**（EC-04 记 PASS）。交付 = `tools/verify_goal024_closeout.py`（**431 行**、最长函数 **44 行**：公共面直接调 `tools/closeout_recheck_assertions.py`（`Verdict`/`emit`/`standard_verdicts`），本文件只写 GOAL-024 特有断言 —— 受判出口**恰好六条** / 读面上下界与分区 / 七源矩阵 / 条款锚点 / 未覆盖面 / 被点名判据存在性 / 残余与未覆盖**登记在位** / 自身规模）；`IN_SCOPE` **3 → 4 条**（加入本验证器，**纯收紧**：下界断言单调）。**实跑**：`tools/verify_goal024_closeout.py --root . --verdict-only` = **38 PASS / 0 FAIL**（定稿前如实判红 2 条：`latest_recheck` 为 null 与两条残余短语缺位，记录补齐后转绿 —— 不是放宽断言）；验证器自身四道门（`ruff format --check` / `ruff check` = `All checks passed!`、规模 431 行 / 最长 44 行、`mypy` = `Success`）；`tests/tooling/test_tooling_scripts_meet_product_gates.py` **8 passed**（新脚本真的被四道门管住）；治理 `validate.py` 绿。**两树复检**（`tools/two_tree_recheck.py --script-mode shared`，`verify_paths` = 2 路：当前树 + 干净 checkout）**结果与 `sha256` 见收口补记**。**as-is 本机 m0（记录写入之后）见收口补记**。 | 本行与其**收口补记**提交（依固定口径其 CI run 只在回合汇报记账） | 零真缺陷；`IN_SCOPE` 为纯收紧 | **残余登记**：承继 12 条（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`）**原样保留** + 本轮新增 **6 条**（`G24-1` 四个金丝雀源没有注入面 / `G24-2` 只扫响应体、响应头不在面 / `G24-3` 白名单是人工判定 + 机械自审 / `G24-4` `label` 字段名与内容语义不一致 / `G24-5` 条款是文档 + 判据形态、不是运行时拦截器 / `G24-6` 6 条声明载体无正控制 + 3 条路由取不到）。`RECHECK-20260928-236` 三条警告留位（两树同结论 ≠ 跨平台同结论 / 验证器是读树判据、不重跑取证 / 承继残余一条不消解）。 | — |
| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-024 落地） | `354e657` | M0 [**36413604236**](https://github.com/Eswink/research-system-new/actions/runs/36413604236) / CodeQL [**36413604077**](https://github.com/Eswink/research-system-new/actions/runs/36413604077) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `eval-gate` / `collector-quality` / `observability-overhead-windows-latest` / `console-frontend` / `quality-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查）。轮询日志 `scratch/goal024-c0-ci-poll.log`（`ALL_TERMINAL sha=354e657e0c1b1cd2a9c8ab72fdf088bb8330fa4b`，45 轮轮询）。上游 push 回执报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ **零依赖改动**，与 GOAL-018…023 收口一致 |
| cycle 1 实施 + 收口（EC-01：`3840407` 判据文件 / `13fad98` 记录，批量一次推送） | `13fad98` | M0 [**36420689426**](https://github.com/Eswink/research-system-new/actions/runs/36420689426) / CodeQL [**36420687981**](https://github.com/Eswink/research-system-new/actions/runs/36420687981) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `eval-gate` / `container-quality` / `console-frontend` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `quality-ubuntu-latest` / `collector-quality` / `observability-overhead-windows-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查）。轮询日志 `scratch/goal024-c1-ci-poll.log`（`ALL_TERMINAL sha=13fad98fdeee642926f47d893450998d3a21a98d`，41 轮轮询） |
| cycle 2 实施 + 记录（EC-02 **部分**：`d7f190d` 判据文件 / `e69ef28` 记录，批量一次推送） | `e69ef28` | M0 [**36427168132**](https://github.com/Eswink/research-system-new/actions/runs/36427168132) / CodeQL [**36427168186**](https://github.com/Eswink/research-system-new/actions/runs/36427168186) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `quality-windows-latest` / `console-frontend` / `observability-overhead-windows-latest` / `eval-gate` / `collector-quality` / `observability-overhead-ubuntu-latest` / `container-quality` / `quality-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查）。轮询日志 `scratch/goal024-c2-ci-e69ef28.log`（`ALL_TERMINAL sha=e69ef288fae5894fb3dfbc1d66a5d0d588f2ab79`，31 轮轮询）。**同批实查**：中间提交 `d7f190d` **没有任何 run**（`runs=none` ⇒ 该提交未被独立判过，受判的是 tip）—— 如实登记，不假装两提交各自被判 |
| cycle 3 实施 + 记录（EC-02 余下 / 读面：`3866e5d` 判据文件 / `81c1e28` 记录，批量一次推送） | `81c1e28` | M0 [**36434731622**](https://github.com/Eswink/research-system-new/actions/runs/36434731622) / CodeQL [**36434731085**](https://github.com/Eswink/research-system-new/actions/runs/36434731085) | **绿（八 job 全 success + CodeQL 3/3）**（两者 `run_attempt=1`，**一次成功、无 flake**）：M0 `conclusion=success`，逐 job `container-quality` / `quality-windows-latest` / `eval-gate` / `console-frontend` / `observability-overhead-windows-latest` / `quality-ubuntu-latest` / `collector-quality` / `observability-overhead-ubuntu-latest` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)` **3/3 `success`**（逐 job 由 `/actions/runs/<id>/jobs` 实查；`run_attempt` 由 REST API 逐 run 实查）。轮询日志 `scratch/goal024-c3-ci-tip.log`（`ALL_TERMINAL sha=81c1e289cba79d4fc416c2e9bfc623546ac75715`，37 轮轮询）。**同批实查**：中间提交 `3866e5d` **没有任何 run**（`runs=none`）—— 与 cycle 2 同形，受判的是 tip |
| 本条台账的**记录提交** | 本行所在的记录提交 | **依「固定口径」：写台账的那一步自身的 run 只在回合汇报记账**（不重复回写文件 —— 否则每写一行就产生一个待记账的新提交，台账永远追不上自己） | 见回合汇报 |


## 收口判词（GOAL-024，2026-09-28）

收口条件：EC-01…EC-04 **全部 PASS** 且每条有实跑证据。逐项如下（**数字全部来自实跑**）：

1. **受判出口清单（受判 / 豁免逐条与其理由）**：受判 **6 条** —— `otlp-traces-wire` /
   `otlp-metrics-wire` / `application-log`（stdlib logging，本仓**不存在** OTLP logs 信号）/
   `read-face-http` / `failure-payload` / `disk-run-artifacts`；豁免 **1 条** —— `stdout-stderr`
   （默认进程内路径**零生产点**，理由写在判据源码里）。候选 **113** 个发射点全部被恰好一条显式
   分类认领；未机械枚举的形态 **4** 条带理由登记（`UNCOVERED_SHAPES`）。
2. **金丝雀零命中与反证红的实跑证据**：编排层（cycle 2）—— `egress guard: judged 168
   connection attempt(s); blocked 0`（全 loopback）；traces / metrics wire、应用日志（本次 4 条）、
   失败载荷、stdout+stderr **零命中**；每条通道可见性正控制全绿；反证两向（内容进允许键
   `endpoint_id` ⇒ 判红并**点名键名与出口**；内容进日志行 ⇒ 判红并点名 `application-log`）；
   措辞无关（同 token 三种措辞 ⇒ 结论不变）。读面（cycle 3）—— 68 条读路由**逐条**分区
   （声明载体 15 / 零命中 53），canonical 侧确有 `prompt` / `artifactbody` / `evidencebody`
   三种金丝雀，零命中面 **51/53** 条取到非空响应且**零越界**，声明载体 **9** 条正控制全绿；
   两向反证 + 两向按压（真实应用新增未登记路由 `/__press-probe` ⇒ 分区判红点名；登记里出现
   树里没有的路径 ⇒ 陈旧判红）。
3. **两树实跑证据（逐行 + `sha256`）**：见「收口补记」（`tools/two_tree_recheck.py
   --script-mode shared`，当前树 + 干净 checkout，`verify_paths` = 2 路）。
4. **按压与逐字节复原记录（raw `sha256`）**：EC-01 四向按压（真实产品根新增 `print` 模块 /
   受判面删一行 / 豁免理由抽空 / 下界加非受判 id）全部**先红后绿**、逐字节复原（raw `sha256`
   回到 `076fad378c48c794df3fa4e672614a7e379f10bc69f2e81d7eb5e7ce42aac74f`；`tools/observability/`
   的既有判据文件**逐字节未改**）。
5. **as-is 本机 m0 的终态行与「门在记录之后」的时刻证据**：见「收口补记」。
6. **未覆盖范围（五条）与未覆盖面登记（四条）**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 /
   部署面未验证 / `R-M1` 未收口；文档内 `未覆盖面 1..4`（debug mode 受控采样 / 真实 collector
   与生产部署面 / CI 产物面 / `R-M1`）逐条在位。
7. **新增残余登记**：`G24-1`…`G24-6`（见「本轮新增残余」表）。

**不得**据此宣称项目安全（`R-M1` 未收口）；本判词只覆盖被点名判据**在本机默认离线链上**跑到的那几面。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | ACTIVE | **建档**：用户会话指令（goal 模式）授权对「观测隐私」（AGENTS.md §10）做一次**对抗性自检** —— 沿**默认（离线 Fake 链）**运行路径注入**唯一合成内容金丝雀**，证明它不出现在任何**非 canonical 出口**；把扫描面做成**可复跑判据**；把做不到的部分**逐条登记**。**明确不做**：读面认证、多租户 / RBAC / organization scope、BOLA·BFLA 实现、逐调用方身份、修改任何既有判据 / 门禁 / 阈值 / 放行面、改 `PRODUCT_ROOTS` / m0 条数 / 作业结构、新增依赖、真实出网、真实内容进夹具或记录、改 401 形态或 `Idempotency-Key` 语义、动 `undici`、改 `ADR-0031` 的 `Status`、宣称项目安全。四 EC 设计（出口清单显式分类 / 端到端取证 + 反证 + 按压 / 边界条款 + 未覆盖面登记 / 自举收口），budget = 20 / 120 / 2。**建档当日实测十七条事实**（见「目标与退出标准」），其中四条决定判据形态：**① 本仓不存在 OTLP logs 信号**（repo-wide 零命中）⇒「三信号」必须改述为 traces + metrics（wire）+ stdlib 应用日志（进程内），否则判据会落在空集上；**② 默认 telemetry 是 `NullTelemetrySink`** ⇒ 判据必须**显式注入**真实 OTLP sink 才能让该出口**非空**（承 MEM-156）；**③ 既有夹具 `canary_support.py` 已 349 行且只读**（硬上限 450）⇒ 新夹具必须落**新文件**；**④ `tools/` 受判面的下界断言是单调的**（`required ⊆ IN_SCOPE`）⇒ EC-04 把新验证器加入必备清单是**纯收紧**、无需改既有断言。**建档时零产品代码改动**（只增本文件）；工作树另有 4 个**与本 GOAL 无关**的并发改动（仅行尾态差异），本 GOAL 一律只用**显式路径**提交。 |
| 2026-09-28 | ACTIVE | **建档 cycle 0 完成，进入循环**：EC-01…EC-04 全 PENDING，下一 cycle 做 **EC-01**（金丝雀源与出口清单：显式分类 + 未分类判红）。**本地验证**：治理 `Cursor 治理验证通过` + 记录面判据 **24 passed** + **as-is m0 23/23**（`PASS [` = 24、`4665 passed / 21 skipped`、`EXIT=0`；日志 `scratch/goal024-c0-m0.log`，文件时刻 `19:00:54` **晚于**本文件最后写入 `18:44:26` ⇒ 门在记录之后）；进程卫生零泄漏。**本机无 `make`** ⇒ 直跑 `run_all_checks.py --profile m0 --keep-going`（canonical 等价）。**建档提交 `354e657` 的 CI 到终态**：M0 `36413604236` 八 job 全 success + CodeQL `36413604077` 3/3，两者 `run_attempt=1`（逐 run 由 REST API 实查）。**本条记录提交**依「固定口径」其 CI run 只在回合汇报记账。 |
| 2026-09-28 | ACTIVE | cycle 1（PLAN-20260928-227）：**EC-01 = PASS**（非 canonical 出口清单显式分类）。交付 = `tests/observability/privacy_exit_census.py`（259 行）+ `tests/observability/test_privacy_exit_census.py`（407 行 / 13 例）+ `RECHECK-20260928-228`（`PASS_WITH_WARNINGS`）+ `MEM-20260928-161`。**普查 113 候选全覆盖**（受判出口 6 / 豁免出口 1 / 豁免生产者 25 / 未覆盖面 4 条带理由），**没有第三种状态**：未分类 / 重复分类 / 登记陈旧 / 空理由 / 受判面无观测方式或无生产者**各自判红**。**四向按压先红后绿**（含**真实产品根**新增出口被点名）且 raw `sha256` 逐字节复原（`076fad378c…`）；**判据自跑抓到两处自己的错**（重复分类 + 形态自检样本位形）并当场修掉。**四道门绿**；既有 `test_privacy_canary.py` **逐字节未改**且合跑 20 passed。**as-is 本机 m0 与 CI 台账**：见补记（记录写入之后跑）。 |
| 2026-09-28 | ACTIVE | **cycle 1 补记**：**as-is 本机 m0（记录写入之后、冻结树上独占跑、仓库 `.venv`、DSN 固化 + `LLM_MAIN_KEY=""` + `--keep-going`）= `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4680 passed / 21 skipped**、`EXIT=0`；日志 `scratch/goal024-c1-m0.log`，耗时 `576.02s`，**文件时刻 `20:07:51` 晚于**记录写入时刻 `19:54:27` ⇒ 门在记录之后；跑完 python 进程 **0**）。**记录面判据 + 工具面判据** 7 个文件合跑 **53 passed**；治理 `validate.py` 绿（含 `ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致`）。**按压留档**：`scratch/goal024-ec01-press-matrix.log`（四向按压原始输出 + 基线 raw `sha256`）。**本 cycle 的 CI 到终态**：M0 `36420689426` 八 job 全 success + CodeQL `36420687981` 3/3，两者 `run_attempt=1`（REST API 逐 run 实查）。 |
| 2026-09-28 | ACHIEVED | **cycle 5（PLAN-20260928-235，EC-04）**：收口验证器进树（431 行 / 38 判词全绿）并入 `IN_SCOPE`（3 → 4，纯收紧）；两树复检与 as-is m0 见收口补记；残余承继 12 条原样保留 + 本轮新增 6 条。**EC-01…EC-04 全 PASS ⇒ GOAL ACHIEVED**。 |
| 2026-09-28 | ACTIVE | **cycle 4（PLAN-20260928-233，EC-03）**：两条条款逐字落两份文档 + 四条未覆盖面逐条登记 + 受判面与读面白名单口径 + INDEX 登记，并由新判据钉住（**被点名的 5 个判据文件改名即判红**）。钉点判据 9 例全绿；DOCS-CHECK 绿；既有文档只追加。**EC-03 记 PASS**。 |
| 2026-09-28 | ACTIVE | **cycle 3（PLAN-20260928-231，EC-02 余下 / 读面）**：读面从 `NOT_YET_OBSERVED` 变成**实取判据**（68 条读路由逐条分区；声明载体 15 / 零命中 53；canonical 确有内容的前提下 51/53 条实取零越界；9 条声明载体正控制全绿；两向反证 + 两向按压）。**EC-02 记 PASS**。七源注入面逐条登记（注入 3 / 无注入面 4）。四道门绿；`tests/observability/` 91 passed / 1 skipped；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（24 个 `PASS [`、4705 passed / 21 skipped、EXIT=0；日志 `scratch/goal024-c3-m0.log`）。 |
| 2026-09-28 | ACTIVE | **cycle 2（PLAN-20260928-229，EC-02 部分）**：交付 `content_canary_support.py`（212 行）+ 判据（246 行 / 10 例）。绝对面零命中 + 载体白名单 + 每通道可见性正控制 + 两向反证 + 措辞无关；两个分支终态如实登记为 `FAILED`（门未被放宽）。**读面未观测 ⇒ EC-02 未达成**。四道门绿；`tests/observability/` 81 passed / 1 skipped；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（24 个 `PASS [`、4692 passed / 21 skipped、EXIT=0；日志 `scratch/goal024-c2-m0.log`）。 |
| 2026-09-28 | ACTIVE | **cycle 1 CI 台账尾巴**：`13fad98`（EC-01 实施 `3840407` + 记录 `13fad98` 批量一次推送）到终态 —— M0 `36420689426` 八 job 全 `success` + CodeQL `36420687981` 3/3 `success`，两者 `run_attempt=1`，**一次成功无 flake**。**下一 cycle 的输入已定位**：EC-02 的读面口径必须写成**白名单**而非「读面不得含内容」——`GET /artifacts/{id}/content`、`/runs/{id}/deliverable`、`/runs/{id}/events`、`/protocol-drafts` 的**契约本来就是**返回用户内容（业务真相），所以受判命题是「**内容只出现在契约声明要返回它的那条路由上**，其余路由、遥测、日志、磁盘、失败载荷一律零命中」。 |
