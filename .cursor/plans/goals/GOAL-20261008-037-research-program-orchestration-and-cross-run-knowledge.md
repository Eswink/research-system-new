---
id: GOAL-20261008-037
slug: research-program-orchestration-and-cross-run-knowledge
title: 研究程序级编排 —— 多轮 run 的**结论驱动**推进 + **跨 run 知识累积**（把「一次多轮研究」推进到「程序级编排」）
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 5 推进（轴 = 深度+质量）**，并授权本驱动
    自动化循环推进、**收口后立即开下一个 GOAL，不停下来等指令**。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含新增域字段、放宽某条 allow、改产品语义、新增 ADR），**不等于**可以放宽**判据、
    门禁、阈值或断言** —— 本轮无例外。
    (1) **本 GOAL 的授权开工**（MAINLINE 程序表序 5 的一句话目标逐条落地）：
    (i) **轴 = 深度 + 质量**：深度 = 「多轮 run 由**结论驱动**推进且有停止规则」；
    质量 = 「跨 run 的**知识累积**真的被后续 run 用上」（来源支持跨轮延续）。
    (ii) **候选由实测决定**（建档勘察给出读数）：run 之间**零关联**（单发启动、无程序实体、
    `RUN_FORKED` 是死名字）；memory 侧**有写入、无读取**（无项目维度、run 路径零读取）
    ⇒ 「上一轮的结论对下一轮不可见」是**已实测**的缺口，本 GOAL 就补这一环。
    (iii) **不做数量目标**：承接面**只为这件事**扩容（如需新能力，逐条走 GOAL-036 的
    五件事承接链）；**不**为「程序」新建一套平行事实面（canonical 是唯一真相）。
    (2) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面** /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/
    宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
    口径只能是 at-least-once + idempotency + deduplication）；
    **用「加了计数或阈值」冒充深度/质量**（MAINLINE 两条轴的反面）；
    **把未放行能力写进协议**（必须先放行再声明）；
    **把程序 ↔ run 的关联落在日志 / 侧表 / 推断里**（不是 canonical ⇒ 判红）。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime 保持 **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10：跨 run 知识在观测面只留 digest/size/type）。
    (5) **边界（承继）**：GOAL-001…036 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…036 的未覆盖范围**原样保留**；
    GOAL-036 的残余 `M-1`…`M-5` / `R26-*` 终态 / 未覆盖范围**原样保留**，本轮**只追加**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 MAINLINE 程序表序 5（**深度 + 质量**轴）推进到「研究程序级编排」：
    ① **勘察定稿** —— 用读数回答「为什么是程序级编排与跨 run 知识」（run 之间零关联；
    memory 有写入无读取；多轮止于 run 边界；可复用的缝逐条）（EC-01）→
    ② **程序编排（深度）** —— 一次实跑里程序**跨至少两次 run** 推进：程序 ↔ run 的关联
    **落 canonical**；续跑/停止**由上一轮落库结论驱动**（声明式规则 + 上界护栏，先结论后
    护栏）；决策与理由**留档可读**（EC-02）→
    ③ **跨 run 知识累积（质量）** —— 后一轮**真的读到并用上**前一轮落库的知识：读到的
    内容与落库**逐字一致**（下游消费证据）；**两向反证**（缺来源 ⇒ 点名；未放行 ⇒
    点名 `POLICY_DENIED`）（EC-03）→
    ④ **幂等与中断（约束）** —— 编排步 **at-least-once + 幂等**（同程序同序号的续跑
    不得产生第二个 run；重放驱动不重复副作用；dedup 键可指认），与既有 resume 边界明写
    （EC-04）→ ⑤ **自举收口**（复用 GOAL-036 的机器：验证器 + 两树 + 归档 + as-is m0 +
    治理 + 台账）（EC-05）。
    **硬约束**：程序 ↔ run 关联**必须在 canonical**（不是日志 / 侧表 / 推断）；「被用上」
    要**下游消费证据**（逐字一致），不是「调了两遍工具」；受判面**不得**是交集 / 过滤 /
    空集恒真；**点名失败而非静默**；m0 条数**仍是 23**；留档**二进制写盘**、判词归档**进树**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（为什么是程序级编排 + 跨 run 知识）**。(a) run 面读数：`ResearchRun`
      字段表**零关联字段**（id / project_id / protocol_id / state / manifest / pricing /
      protocol_source / protocol_body / 时间戳）；启动面是**单发**（`POST
      /projects/{project_id}/runs`）；`RUN_FORKED` 是**死名字**（`packages/domain/events.py`
      有枚举声明、全仓**零发点**）；多轮止于 **run 边界**（GOAL-034 的轮次在 run 内）。
      (b) memory 面读数：run 路径**有**受门写入（`promote_memory` / 逐条
      `promote_memory_from_registration`），但 `MemoryRecord` **无项目字段**、
      `m12_memory` 表**无项目列**、`MemoryStore.query(tier)` **无项目维度**、
      `GET /projects/{id}/memory` **显式 `del project_id`**；**run 路径零 memory 读取**
      （task / handoff 组装面零命中）⇒ 跨 run 知识「有写入、无读取」。
      (c) **真需要的证据**：MAINLINE 总目标 = 一次**多轮**、可中断、产出**可复核**的研究；
      上一轮的落库结论（验收 / 评审 / 停止事实）对**下一轮**不可见 ⇒ 程序级闭环缺一环。
      (d) 可复用的缝：GOAL-036 的承接链五件事（能力 + 策略 + provider + 绑定 + 放行）、
      run 路径的 claim / memory promotion、项目 run 列表读面、phase / handoff 组装面、
      GOAL-034 的停止规则纪律（先结论后护栏 + 跳过可观测）。
    verify: >-
      `rg -n "RUN_FORKED" .` ⇒ 仅枚举声明；`rg -n "project_id" services/api/routers/memory.py`
      ⇒ 显式 `del`；`rg -n "memory" packages/application/run_orchestration/{task_executor,
      phase_call_arguments,handoff_builder}.py` ⇒ 零命中；`ResearchRun` 字段表逐条读数。
    status: PENDING
  - id: EC-02
    criterion: >-
      **程序编排（深度轴）**。(a) 程序 ↔ run 的关联**落 canonical**（域事实，可读面复核；
      不得是日志 / 侧表 / 按时间推断）；(b) 续跑 / 停止**由上一轮落库结论驱动**：
      规则**声明式**（协议或合约面），**先结论后护栏**（与 GOAL-034 同款纪律），
      跳过与停止**可观测**（不是静默）；(c) 一次**实跑**里程序**跨至少两次 run** 推进
      （第 1 轮终止后由编排启动第 2 轮，第 2 轮读第 1 轮的落库结论）；(d) 决策与理由
      **留档可读**：读面逐条点名「第 N 轮：为何继续 / 为何停」+ 上界护栏未触发的证据。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；双 run 实跑的
      终态 + 程序读面逐条判词；两向反证：结论缺失时的停止点名、护栏触顶点名。
    status: PASS
  - id: EC-03
    criterion: >-
      **跨 run 知识累积（质量轴）**。(a) 后一轮**通过真实能力**读到前一轮落库的知识
      （承接链五件事齐：声明 + 实现 + 绑定 + 两组合根接线 + 放行），读到的内容与落库
      **逐字一致**（下游消费证据 —— 不是「调了两遍工具」）；(b) 反证①：撤掉来源 ⇒
      点名不可用（不返回空冒充「没有知识」）；(c) 反证②：撤掉放行 ⇒ 调用点点名
      `POLICY_DENIED`；(d) 承接面**只为这一件事扩容**（新增能力逐条走 GOAL-036 的机制；
      登记面 / 夹具 / 策略面同轮同步、**纯收紧**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/application -q` ⇒
      全绿；新增判据文件全绿；覆盖读数与登记面逐条给出。
    status: PENDING
  - id: EC-04
    criterion: >-
      **幂等与中断（约束，不是轴）**。(a) 编排步 **at-least-once + 幂等**：同一程序同一
      序号的续跑**不得**产生第二个 run（实测：重放编排步两次 ⇒ 只有一个 run + 一次
      dedup 事实）；dedup / idempotency 键**可指认**（逐字给出）；(b) 中断/恢复：程序
      状态可从 canonical 重建（进程重启后重入不重复副作用），与既有 **run resume**
      的边界**明写**（哪些事 resume 管、哪些事编排管）；(c) **明确否认**「恰好一次」：
      记录与判据里只允许 at-least-once + idempotency + deduplication 的口径。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/api -q` ⇒
      全绿；重放实测读数（run 数 / dedup 事实逐条）。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      + `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py`，`--script-mode shared` +
      `--base-ref`）+ **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**、
      `CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已替换 MAINLINE
      序 5 的占位**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled`
      如实登记 + 原因 + `covered_by`；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）；
      ⑥ 承继残余逐条在位（GOAL-036 的 `M-1`…`M-5` / `R26-*` 终态 / 未覆盖范围逐条保持 +
      理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal037_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；`uv run --frozen --no-sync python -B
      .cursor/skills/governance-check/scripts/validate.py` ⇒ 绿；
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 全绿；配套留档：
      两路判词 sha256 相同的归档、m0 日志、CI 台账逐提交行。
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
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **为了凑数而声明没有实现的能力**；**把受判面写成交集 / 过滤 / 空集恒真**；
      **只断言「能力登记了 / 声明了」而不取调用、下游消费与放行三条证据**；
      **把未放行能力先写进协议再补放行**（先放行再声明，否则差集判据红是**真红**）
    - >-
      **把程序 ↔ run 的关联落在日志 / 侧表 / 时间推断里**（canonical 是唯一真相；
      AGENTS.md §6）
    - >-
      **用固定轮数替代结论驱动**（MAINLINE 深度轴的反面：固定轮数的流水线加长**不算推进**）；
      **用「加了计数或阈值」冒充质量**（质量轴的反面）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**`、
      `tests/application/**`、`tests/api/**` **既有文件**）—— **新增**判据与新增文件不受此限
    - >-
      **同轮同步面**：仅当本轮新增能力 / 新读面**必需**时，允许对**既有**登记面做
      **加法 / 搬迁登记**（谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**；
      枚举之外的既有判据仍禁改，触达即 BLOCKED。**新读面**按既有纪律同步
      （OpenAPI 快照 + `types.ts` + 隐私清单/路由登记，二者由既有判据决定）。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮如需新能力，
      只允许**只读**放行且逐条枚举）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 编排需要动写面 / 执行面 / 审批面的放行（本轮范围外）
  - 程序 ↔ run 关联被要求落在 canonical 之外（触犯即 BLOCKED）
child_plans:
  - .cursor/plans/tasks/PLAN-20261008-337-goal-037-ec01-canonical-program-skeleton.md
  - .cursor/plans/tasks/PLAN-20261008-339-goal-037-ec02-program-advance-entry.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-340-goal-037-ec02-program-advance-entry.md
memory_entries:
  - jsonb-decodes-must-accept-parsed-objects
  - a-new-write-route-updates-the-measured-warning-lines
---

# GOAL-20261008-037 — 研究程序级编排（多轮 run + 跨 run 知识累积）

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 5**（轴 = **深度 + 质量**，
> 依赖序 1…4 —— 四条已 ACHIEVED）。
> **建档时的程序表修订（`replan_every_goals: 3` 到期）**：序 5 的行按 033…036 的实测
>  sharpen 后**替换**（原文移入 MAINLINE 修订记录），本 GOAL 即该行的承担者。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 为什么是程序级编排 + 跨 run 知识：run 之间零关联、memory 有写入无读取、多轮止于 run 边界 | PENDING |
| EC-02 | 程序编排（深度） | 双 run 实跑：关联落 canonical + 续跑/停止由上一轮落库结论驱动（先结论后护栏）+ 决策留档可读 | PASS |
| EC-03 | 跨 run 知识累积（质量） | 后一轮**读到并用上**前一轮落库知识（逐字一致）+ 两向反证点名 | PENDING |
| EC-04 | 幂等与中断（约束） | 编排步 at-least-once + 幂等（重放不产生第二个 run）+ 与 resume 边界明写 | PENDING |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**为了凑数**声明没有实现的
能力；不得**先声明未放行能力**（先放行再声明）；不得把 destructive / 写 / 执行 / 审批类能力
改成 allow；不得把程序 ↔ run 关联落在 canonical 之外；不得用固定轮数替代结论驱动；
不得**宣称项目安全**（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**。主树零改动（只读勘察）。

### 1. run 之间**零关联**（程序级编排缺的第一件）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | `ResearchRun` 无「程序 / 前序 run」字段 | `packages/domain/run.py` 字段表 | id / project_id / protocol_id / state / manifest_digest / manifest_semantic_digest / pricing_* / protocol_source / protocol_body / created_at / updated_at —— **零关联字段** |
| 1.2 | 启动面是**单发** | `services/api/routers/runs.py` | `POST /projects/{project_id}/runs`（一次一个 run）；`GET /projects/{id}/runs` 只是**列清单**，不是编排 |
| 1.3 | `RUN_FORKED` 是**死名字** | `rg -n "RUN_FORKED" .` | 只有 `packages/domain/events.py` 的枚举声明，**全仓零发点** |
| 1.4 | 多轮**止于 run 边界** | GOAL-034 的交付（轮次在 run 内） | 「多轮研究循环（至少三轮）」是**同一 run** 内的 phase 轮次；run 与 run 之间没有任何推进机制 |
| 1.5 | 调度面是**运维任务**不是研究编排 | `packages/domain/schedules.py` | `ScheduleJob` = 周期维护作业（租约回收等）；没有「研究推进」类作业 |

### 2. 跨 run 知识：**有写入、无读取**（质量轴缺的那一环）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | run 路径**有**受门写入 | `packages/application/run_orchestration/task_phase_helpers.py` / `memory_promotion.py` | `promote_memory(deps, registration, kind=kind)` + `promote_memory_from_registration`（走 `memory/gate.commit_memory`） |
| 2.2 | memory **无项目维度** | `packages/domain/memory.py` / `adapters/sqlite/memory_store.py` / `ports/memory_store.py` | `MemoryRecord` **无项目字段**；`m12_memory` 表**无项目列**；`MemoryStore.query(tier)` **无项目维度**（`MemoryWriteProposal.scope` 存在但**不落库**） |
| 2.3 | 读面**显式忽略**项目 | `services/api/routers/memory.py::list_project_memory` | `del project_id  # 单项目上下文；scope_note 明示无 principal 过滤` ⇒ 返回全量记录 |
| 2.4 | **run 路径零 memory 读取** | `rg -n "memory" packages/application/run_orchestration/{task_executor,phase_call_arguments,handoff_builder,result_handler}.py` | **零命中**（写入有、读取无）—— 只有交付物导出面 `deliverable/builder.py::_memory_block` 按 **id 单条 `get`** |
| 2.5 | 结论**已落库**（上一轮的事实本来就在） | GOAL-035 / GOAL-036 的交付 | 验收判定、评审结论（`ReviewFindingStore`）、证据链（ledger claims）都在 canonical；缺的是**把上一轮的它们喂给下一轮** |

### 3. 可复用的缝（本轮实现面的形状由它们决定）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 承接链五件事的机制 | GOAL-036（`review.read`） | 声明 + 实现 + 绑定 + 两组合根接线 + 放行（缺一即判红） |
| 3.2 | 读能力形态的**可选依赖**先例 | `adapters/canonical/read_provider.py` | `budget_ledger` / `experiment_store` / `run_store` / `review_store` 四条先例；缺省 `None` ⇒ 工具**点名**不可用 |
| 3.3 | 停止规则的**纪律** | GOAL-034 | 先结论后护栏、跳过必须可观测（进 `run.completed` 的 `skipped`）、路径缺失点名失败 |
| 3.4 | run 的 canonical 读面 | `services/api/routers/runs.py` | `GET /projects/{id}/runs`（清单读面已存在，扩展面有先例） |
| 3.5 | 交付物导出的 memory 块 | `packages/application/deliverable/builder.py` | 单条 `get`（`mem:{run_id}:negative-result` 缺省）—— 「跨 run」目前只在这里出现过名字 |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 程序 ↔ run 关联的落点 | **已定**：**必须落 canonical**（域事实；不得日志 / 侧表 / 时间推断）—— 具体形态（新字段 vs 新实体）由 cycle 1 定并登记 |
| ② | 编排驱动的落点 | **已定（边界）**：`packages/application/run_orchestration/` 下的**应用层**编排（通过既有 start-run use case 启动，不绕过 preflight / manifest freeze）；具体模块由 cycle 1 定 |
| ③ | 跨 run 知识的读取形态 | **已定（边界）**：走 GOAL-036 的承接链形态（能力 + 策略 + provider 工具 + 读面），读**程序内前序 run 的落库结论**；不做「把 memory 表整体暴露」 |
| ④ | memory 的项目维度 | **不开本轮**：本轮不改 `MemoryRecord` / memory 表（那是另一条线）；跨 run 知识走**程序内前序 run 的 canonical 结论**，与 memory 线**并列**、边界在记录里明写 |
| ⑤ | 轮数 | **由结论驱动**（固定轮数不算推进）；上界护栏只作**上界**，与结论判据**可区分**（承 GOAL-034） |
| ⑥ | 承接面扩容 | **只为这一件事**（不做数量目标）；如需新能力，逐条走 GOAL-036 的五件事 + 登记面同轮同步 |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按「迭代日志」最后一行 + 工作树/远端实况
判定续点（与 `goals/README.md` 同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件（迭代日志 / 状态历史 / EC 状态），保证任意时刻崩溃后重入可续；
**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**（进入 cycle 时在迭代日志声明 owner 行）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；写子 PLAN
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-037` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（治理校验器是
  `governance-check/scripts/validate.py`，**不是** `validate_cursor_framework.py`）；
  m0 按组、**独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；
  受影响的定向套件（`tests/application` / `tests/api` / `tests/adapters` / `tests/architecture`
  / `tests/e2e` / `tests/contracts`）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run。
  **一个 cycle 攒成一次推送**（同批推送只有 HEAD 产生 run ⇒ 逐提交台账按 `covered_by` 登记）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **程序 ↔ run 关联落 canonical**（不是日志 / 侧表 / 推断）；
- **结论驱动**：续跑与停止的输入是**上一轮的落库结论**（先结论后护栏；固定轮数不算推进）；
- **「真的被用上」才算数**：要**下游消费证据**（读到的与落库逐字一致），不是「调了两遍工具」；
- **点名失败而非静默**：缺来源 / 未放行 / 缺实现一律点名；
- **受判面不得是交集**（承 `MEM-160`）；
- **先复核再依赖**：本 GOAL 的起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；
- **新记录落地后立刻跑治理**（承 `MEM-20261008-197` / `MEM-20261008-206`）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP DNS 出网判据、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 组合跑顺序） | 按既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | validator / Mimosa / 记录面判据命中新增项 | 按各处置文档修或登记；**不得绕过**；不得宣称安全 |
| 资源阈值型偶发 | 例如 CI 上 RSS < 128MiB 类阈值判据偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类判据红 | **按生成器重新生成**（`tools/gen_openapi.py`），**不得手改** JSON |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure`（验证器进树 + 两树 + 归档 + m0 +
  治理 + 台账）并声明 `verify_paths` ≥ 2 路、**用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers`（含「需改同步集以外的既有判据断言」）或
  `budget.max_cycles` 触顶（20）；停下留人工决策，逐条写明触发项。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停止并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034 的 `W-1`…`W-4`；GOAL-033 的 `W-1`…`W-6`；GOAL-032 的 `W-1`…`W-8`；历史 `tools/`
目录仍有旧 lint 与无机器门的旧脚本；GOAL-019…036 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**memory 的项目维度仍缺**（决策 ④）：跨 run 知识本轮走「程序内前序 run 的
  canonical 结论」；`MemoryRecord` / `m12_memory` / `GET /projects/{id}/memory` 的
  项目语义**不动**（那是另一条线）。
- （建档时登记）**程序级人工闸门未接线**：编排的暂停/人工介入（D 组审批通道）仍不触动。
- （建档时登记）**跨项目 / 跨程序的知识共享不在本轮**：知识面按**程序**（= 项目内的一条
  研究程序）划界。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**；
**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **程序编排**：**已收口** = 双 run 由结论驱动推进且决策留档可读；**未覆盖** = 程序级人工
  介入与跨项目编排。
- **跨 run 知识**：**已收口** = 前序 run 的落库结论被后续 run 的 phase 真的读上（逐字一致）；
  **未覆盖** = memory 的项目维度与跨程序共享。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；**无自己的 run 也如实登记原因**（同批推送时只有 HEAD 产生 run）；
> 现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的「回顾性台账」提交自身
> 不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以「末条提交 + 覆盖说明」封闭，
> **不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `ae1a52c`（GOAL-036 台账尾巴，本轮首行） | `37771735734` **M0 success**（8 job 全 success）+ `37771735588` **Push on main / CodeQL success**（3 分析全 success） | GOAL-036 的最后一个提交（仅 `.cursor/**` 记录改动；本地 `--profile framework` **8/8**）—— **实测取证**；**GOAL-036 台账的自我指涉边界由本行封闭** |
| `b30ffda`（cycle 0 建档） | `37773456975` **M0 success**（8 job）+ `37773457341` **Push on main / CodeQL success**（3 分析） | 建档提交（仅 `.cursor/**`）：程序表序 5 replan + 五 EC + 事实层读数；本地治理 + 宪章判据绿（**实测取证**） |
| `86fd5b7`（cycle 1：EC-01 骨架） | M0 `37781191176` **cancelled**（4 job success：`eval-gate` / 两条 `observability-overhead` / `collector-quality`；4 job cancelled：`console-frontend` / `container-quality` / 两条 `quality-*`）+ CodeQL `37781189555` **success**（3 分析） | **取消原因如实登记**：该 run 在飞时后续推送（`7c0da21`）触发 `cancel-in-progress` ⇒ 本提交的改动由 **`efddc86` 的 M0 覆盖**（`covered_by efddc86`） |
| `7c0da21`（cycle 2 WP-1：驱动） | M0 `37781594902` **failure**（`quality-ubuntu-latest` + `quality-windows-latest` 双平台红：规模门判 `advance_program` 108 > 50 行）+ CodeQL `37781597682` **success**（3 分析） | **真红并修**：处置 = **拆函数**（`_evaluate` / `_after_hit` / 调度三件，各 ≤ 50 行），修在后一条 `efddc86`；本提交的改动由 **`efddc86` 的 M0 覆盖**（`covered_by efddc86`） |
| `efddc86`（规模门修复 = 本批 HEAD） | `37784058017` **M0 success**（8 job 全 success）+ `37784058978` **Push on main / CodeQL success**（3 分析全 success） | 修复提交；**前两条（`86fd5b7` / `7c0da21`）的结论由此行覆盖**（实测取证） |
| `73d13e3`（台账尾 1） | `37786734211` **M0 success**（8 job 全 success）+ `37786731671` **Push on main / CodeQL success**（3 分析全 success） | 只改 GOAL-037 记录的提交；**实测取证**（原先写作「由下一个 GOAL 的台账取证」，现以本行自身读数封闭） |
| （本行所在提交：台账尾 2） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 只改 `.cursor/plans/goals/GOAL-20261008-037-*.md`（记录改动以 `--profile framework` 补全终态）；其结论由**下一个 GOAL 的台账**取证，**不得循环引用** |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（建档） | （见 CI 台账） | 只读勘察（0 改动）；五条 EC 全 PENDING；MAINLINE 序 5 replan（`replan_every_goals: 3` 到期） | （见 CI 台账） | — | 五条 EC 全 PENDING；程序 ↔ run 的关联形态（①）与编排落点（②）待 cycle 1 定 | cycle 1（EC-01 勘察定稿 + EC-02 程序编排落地） |
| 2 | `PLAN-20261008-339` | （见 CI 台账） | **EC-02 全落地**：程序推进驱动 `advance_program`（六条判定：`START` / `CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` / `WAIT` / `DEDUP`；启动面**注入**、缺省点名；`cited_facts` 是判词/状态**原文**；护栏停与结论停**种类可区分**；崩溃窗口 ⇒ `DEDUP` 不产生第二个 run）+ **7 例判据全绿**；四道门绿（mypy 1153 files） | 见 CI 台账（本 cycle 的提交批次） | **规模门真红并修**（`advance_program` 108 行 ⇒ 拆 `_evaluate`/`_after_hit`/调度三件）；**四条登记面同轮同步**（写面告警线 61→63 / 读面登记 +2 / 出口普查 +2 / `create_app` 51 行 ⇒ 拆 `_register_routers`）；**已知类 flake** 一次（OTLP teardown race，单跑两次通过，如实登记） | 三路由 + DTO + 启动面接线（程序归属与 run **同一次**落库）+ 同轮同步 + 双 run 实跑 6 例 + 驱动 7 例全绿；广面 **3209 passed, 91 skipped**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5408 passed, 20 skipped**，收集数 +19 逐文件分解） | EC-02 收口；**下一轮 EC-03**（跨 run 知识的**读入**：承接 `research_state.read` + 下游消费 + 两向反证） |
| 1 | `PLAN-20261008-337` | （见 CI 台账） | EC-01 决策定稿 + **canonical 骨架**：`ResearchRun` 增两字段（同生同灭 + 三个重建函数逐字段复制）、`RunStore.for_program`（SQLite `json_extract` / PG `->>`）、程序域类型 + 端口 + 两个适配器 + **迁移 017**（live PG 实测 `migration_version`=17）+ 两组合根接线；同轮同步（读面 / DTO / OpenAPI 重生成 +22 行 / `types.ts`）；新判据 **15 例全绿**（domain 9 / sqlite 4 / pg 2）；广面 `1590 passed, 5 skipped`（domain+adapters+contracts）/ `1063 passed, 1 skipped`（application+architecture）/ `2516 passed, 76 skipped`（contracts+api+tooling）；四道门绿（mypy 1151 files）；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5389 passed, 20 skipped**；首跑真红于前端型检查 ⇒ 同轮同步 e2e 夹具后重跑取值） | `37773456975` M0 success + `37773457341` Push on main success（cycle 0 建档批，实测） | **门链抓到一次真红并修**（e2e TS 夹具缺两个新字段 ⇒ 同轮同步）；PG JSONB 解码（`str(dict)` 伪 JSON ⇒ 两形态都接住，`MEM-20261008-207`）；**mypy `arg-type` 点名 3 个测试假 RunStore** 缺 `for_program` ⇒ 补假实现（不给 Port 加默认实现、不加 `type: ignore`）；**落地形态修订**：关联查询走 JSON 抽取、不动 `runs` DDL（决策 ① 修订，爆炸半径压到零） | 骨架收口；**下一轮 EC-02**（驱动 + advance 入口 + 双 run 实跑） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **cycle 2 的 CI 真红并修 + 全绿**：`7c0da21` 的 M0 双平台判红于规模门（`advance_program` 108 > 50 行）⇒ **拆函数**修复（`efddc86`），其 M0 `37784058017` **8/8 success** + CodeQL success ⇒ `86fd5b7`（M0 被 `cancel-in-progress` 取消，如实登记）与 `7c0da21` 的结论**由 `efddc86` 覆盖**。EC-02 仍未收口（WP-2…WP-5 未落地）。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 2（EC-02）收口**：程序编排放到「真的跑起来」—— 三路由（建程序 / 推进 / 读面）+ DTO、**启动面接线（程序归属与 run 同一次落 canonical）**、双 run 实跑（`START` / `CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` / 缺启动面点名 / 404）6 例 + 驱动 7 例全绿；**四条登记面同轮同步**（写面告警线 / 读面登记 / 出口普查 / `create_app` 拆函数）。EC-02 `PASS`；EC-03…05 待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 2（EC-02）进行中**：WP-1（推进驱动 + 六条判定 + 7 例判据）落地 —— 判定输入全是落库事实、启动面注入缺省点名、判词原文进决策、护栏停与结论停可区分、崩溃窗口 `DEDUP` 不产生第二个 run。**WP-2…WP-5 未落地**（产品入口 / 读面 / 双 run 实跑 / m0）⇒ EC-02 未收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 1（EC-01 决策定稿 + canonical 骨架）落地**：程序 ↔ run 的关联落 canonical（run 载荷内的 `program_id` / `program_index` + `RunStore.for_program`）、程序域类型与存储（SQLite + PG + 迁移 017）、两组合根接线、同轮同步（读面 / DTO / OpenAPI / 前端类型）；新判据 15 例全绿；四道门绿。**一次真红并修**（PG JSONB 解码 ⇒ 两形态都接住，`MEM-20261008-207`）+ **mypy 点名三处假 RunStore** ⇒ 补假实现。**落地形态修订**：按 JSON 抽取查程序内 run、不动 `runs` DDL。EC-01 收口；EC-02…05 仍待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 程序表序 5 + GOAL-036 收口面；只读勘察把「研究程序级编排：多轮 run + 跨 run 知识累积」落成**两条实测缺口** —— ① run 之间零关联（`ResearchRun` 零关联字段 / 单发启动 / `RUN_FORKED` 死名字 / 多轮止于 run 边界）；② 跨 run 知识**有写入、无读取**（memory 无项目维度 + run 路径零 memory 读取；结论本来就在 canonical）。五条 EC 全 `PENDING`；**程序表序 5 按实测 sharpen 并替换**（原文移入 MAINLINE 修订记录）。**不做数量目标**；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
