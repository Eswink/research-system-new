---
id: GOAL-20261008-036
slug: review-read-capability-onboarding
title: 承接面按研究循环实际需要扩容 —— 评审结论的**可读承接**（`review.read`）：从「登记在案」到「端到端真跑」
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 4 推进广度轴**（原文：「按研究循环实际需要
    逐条扩容承接面」），并授权本驱动自动化循环推进、**收口后立即开下一个 GOAL，不停下来等指令**。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含放宽某条 allow、改产品语义、新增 ADR），**不等于**可以放宽**判据、门禁、阈值或
    断言** —— 本轮无例外。本轮**用到**这条的地方：「按需扩容承接面」意味着**新增一条
    `allow`**（`policy.yaml`，与同级读能力对齐）—— 那是**决定**，不是放宽既有判据。
    (1) **本 GOAL 的授权开工**（MAINLINE 程序表序 4 的一句话目标逐条落地）：
    (i) **广度不是一条轴**（MAINLINE 明文）：承接面**只在研究循环真正用到时补**，
    **不做数量目标** —— 本轮只承接**一条**能力，但它必须**端到端真跑**（声明 ⇒ 实现 ⇒
    绑定 ⇒ 放行 ⇒ 被一次实跑真的用上 + 下游消费证据 + 两向反证）。
    (ii) **候选由实测决定**（建档勘察给出读数）：词表 46 条里，`review.read` 的分类理由
    （「今天的评审走 task/handoff 面」）**已被 GOAL-035 EC-01 改变** —— 验收结论现在**落
    canonical**（`ReviewFindingStore`）且**有只读 HTTP 读面**，但 **agent 的能力面读不到**：
    provider 声明面零 `review.read`、`policy.yaml` 无 `allow`（落 `default_effect: DENY`）。
    (iii) **为什么这是「研究循环真正用到」**：MAINLINE 总目标要「产出**可复核**的研究」，
    而「结论驱动」目前只能看制品与停止判据；**下一轮/下一阶段要能读到上一轮的评审结论**
    （逐条判词，不只是分数）才谈得上跨轮质量闭环 —— 这也正是 GOAL-035 登记的未覆盖
    `N-3`（多评审者聚合）的**前置**。
    (2) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面**（本轮只做一条，
    且必须真跑）/ **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/
    宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **用「加了计数或阈值」冒充质量可判定**（MAINLINE 质量轴的反面）；
    **把未放行能力写进协议**（那会让 preflight 差集判据红 —— 本轮必须先放行再声明）。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime 保持 **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (5) **边界（承继）**：GOAL-001…035 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…035 的未覆盖范围**原样保留**；
    GOAL-035 的残余 `N-1`…`N-6` / `R26-*` 终态 / 未覆盖范围**原样保留**，本轮**只追加**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 MAINLINE 程序表序 4（**广度**轴）推进到「按研究循环**实际需要**扩容承接面」：
    ① **勘察定稿** —— 为什么是 `review.read`（读数：词表里有、声明面零承接、`policy.yaml`
    零放行、分类理由过期；GOAL-035 已让评审结论落 canonical 且有 HTTP 只读面）（EC-01）→
    ② **端到端承接链** —— 声明（`tool_providers.yaml`）+ 实现（canonical 读面 provider 的
    新工具，复用 `ReviewFindingStore`）+ 绑定（会话工具表）+ 接线（两个组合根 + 会话工具
    注册面）+ 放行（`policy.yaml` 的 `allow`，scope 与同级读能力对齐）（EC-02）→
    ③ **真的被用上** —— 一次实跑里，后续 phase 通过 `review.read` **读到前序 phase 落库的
    评审结论**（逐条判词在场 ⇒ 下游消费证据），且**两向反证**（缺实现 ⇒ 点名；未放行 ⇒
    点名 `POLICY_DENIED`）（EC-03）→ ④ **登记面与读数** —— 分类判据把 `review.read` 从
    「登记理由」移入**射程内**（**纯收紧**）、夹具同轮同步、覆盖读数 **19/46 → 20/46**
    **逐条**给出（不做数量目标：本轮只做这一条）（EC-04）→ ⑤ **自举收口**（复用
    GOAL-035 的机器：验证器 + 两树 + 归档 + as-is m0 + 治理 + 台账）（EC-05）。
    **硬约束**：承接 = **声明 + 实现 + 绑定 + 放行 + 真跑**五件事**缺一不可**；受判面**不得**
    是交集 / 过滤 / 空集恒真；**点名失败而非静默**（缺依赖点名不可用，不返回空列表冒充
    「没有评审」）；留档**二进制写盘**、判词归档**进树**；m0 条数**仍是 23**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（为什么是 `review.read`）**。(a) 词表与声明面读数：`capabilities.yaml` 46 条
      含 `review.read`；`tool_providers.yaml` **零** provider 声明它；`policy.yaml` 无 `allow`
      ⇒ 落 `default_effect: DENY`；(b) 分类表里它的理由（「B 组：需要评审实体（今天的评审走
      task/handoff 面）」）**已被 GOAL-035 EC-01 改变**（验收结论落 `ReviewFindingStore` +
      `GET /runs/{run_id}/reviews` 只读面）；(c) 承接机制与规模约束读数：`CanonicalReadProvider`
      的**可选依赖**形态（`budget_ledger` / `experiment_store` / `run_store` 三条先例，缺省
      `None` ⇒ 工具**点名**不可用）、`read_provider.py` 行数（450 上限 ⇒ 须另立模块，先例
      `run_read.py`）；(d) **真需要的证据**：多轮/多阶段研究的「结论驱动」目前读不到上一轮的
      评审结论（GOAL-035 的 `N-3` 多评审者聚合是它的下游）。
    verify: >-
      `rg -n "review.read" examples/ services/ adapters/` ⇒ 只在词表与分类表；覆盖读数命令
      （词表 46 / 声明面 19 distinct）与 `policy.yaml` 逐条读数。
    status: PASS
  - id: EC-02
    criterion: >-
      **端到端承接链（声明 + 实现 + 绑定 + 接线 + 放行）**。(a) 实现：canonical 读面的新工具
      （读 `ReviewFindingStore.for_run(run_id)`，**复用** EC-01 的既有 Port），缺依赖时**点名**
      不可用（**不**返回空列表冒充「没有评审」）；(b) 声明：`tool_providers.yaml` 的
      `m12_artifact` capabilities += `review.read`；(c) 绑定：会话工具表（`DEFAULT_SESSION_TOOL_BINDINGS`）
      ← 出厂目录派生；(d) 接线：两个组合根（SQLite / PG）各把自己的 `ReviewFindingStore`
      传进会话工具注册面（`canonical_read_register` 的依赖面扩一条）；(e) 放行：`policy.yaml`
      新增**一条** `allow`（scope 与同级读能力 `artifact.read` / `evidence.read` / `run.read`
      对齐），`default_effect` / `deny` / `require_approval` / `allow_with_constraints`
      **一律未动**（由判据逐条钉住）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical tests/api
      tests/architecture -q` ⇒ 全绿；`rg` 逐条读数（声明 / 绑定 / 两组合根接线 / allow）。
    status: PASS
  - id: EC-03
    criterion: >-
      **真的被一次实跑用上（+ 两向反证）**。(a) 新协议（新增，**既有协议一字不动**）：
      phase 1 产出交付物 ⇒ **验收门落库评审结论**；phase 2 声明 `review.read` 并从工具面
      **读到 phase 1 的逐条判词** ⇒ 工具证据逐条点名 + **下游消费证据**（读到的那条判词与
      phase 1 落库的逐字一致，不是「调了两遍工具」）；(b) 反证①：撤掉 provider 实例 ⇒
      run 失败且**点名** provider / 能力 / 工具；(c) 反证②：把该能力从 `allow` 撤掉 ⇒
      调用点**点名** `POLICY_DENIED`（**不是**静默跳过）；(d) 实跑终态 `SUCCEEDED` +
      `manifest_digest` 在场。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据文件
      全绿；配套留档：三态（用上 / 缺实现 / 未放行）判词逐字。
    status: PENDING
  - id: EC-04
    criterion: >-
      **登记面与读数（纯收紧）**。(a) 分类判据 `_IN_SCOPE` += `review.read`、从
      `_OUT_OF_SCOPE_REASONS` **移除**该条（理由已由 EC-01 实测推翻）——**只增不减其余条目**；
      (b) 夹具同轮同步（`tests/adapters/canonical/` 的出厂形态夹具 capabilities += 一条
      —— **不**放宽任何断言）；(c) 覆盖读数 **19/46 → 20/46** 给出**逐条**名单与命令
      （**不做数量目标**：本轮只承接这一条）；(d) 读能力面判据：新增的放行是**只读**能力
      （`effect_class: READ_ONLY`），写面 / 执行面 / 审批面**零变化**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/architecture/python/test_capability_coverage_is_implemented.py
      tests/architecture/python/test_policy_surface_difference_set.py tests/contracts -q`
      ⇒ 全绿；读数命令与名单。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools` +
      `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py`，`--script-mode shared` +
      `--base-ref`）+ **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**、
      `CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已替换 MAINLINE
      序 4 的占位**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled`
      如实登记 + 原因 + `covered_by`；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）；
      ⑥ 承继残余逐条在位（GOAL-035 的 `N-1`…`N-6` / `R26-*` 终态 / 未覆盖范围逐条保持 + 理由）；
      ⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal036_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <建档基线>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
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
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**`
      **既有文件**）—— **新增**判据与新增文件不受此限
    - >-
      **同轮同步面（例外，且逐条枚举；断言强度不变的纪律见下）**。**修正登记（cycle 1
      实测发现，如实登记）**：建档时只列了两个同步面；实跑门链后实测到「**放行一条读能力**
      必然牵动**策略面登记表**」这一族 —— 它们不是「另一条判据」，而是**同一件事的登记面**。
      例外**仅限**下列五处，每处只做**加法 / 搬迁登记**，**谓词、阈值、受判形态一字未改**：
      ① `tests/adapters/canonical/` 的**出厂形态夹具**（capabilities **加一条**）；
      ② `tests/architecture/python/test_capability_coverage_is_implemented.py` 的**分类清单**
      （目标条目从「登记」移入「射程」）；
      ③ `examples/config/policy.yaml` 的 `allow`（**新增一条**；其余三段与
      `default_effect` 零变化，由 `test_release_expansion_is_read_only.py` 的段指纹钉住）；
      ④ `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE`
      （策略面**镜像表**加一条；并集相等由既有 `test_m2_audit` 判据锁死）；
      ⑤ `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表（该行**离开差集**、
      进交集清单、计数 + 日期化变更注）+ `tests/application/preflight/` 的两处**登记计数**
      （`EXPECTED_REGISTERED` 8→7、`_RELEASED` +1 / `_UNRELEASED_READS` −1 / scope 期望表 +1）。
      **清单外的既有判据仍禁改，触达即 BLOCKED**；本例外**不得**被读成「可以改断言」——
      任何**谓词 / 阈值 / 受判形态**的改动都在禁令内。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮只放行**只读**能力一条）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 扩容需要动写面 / 执行面 / 审批面（本轮范围外）
child_plans:
  - .cursor/plans/tasks/PLAN-20261008-331-goal-036-ec01-02-review-read-onboarding.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-332-goal-036-ec01-02-review-read-onboarding.md
memory_entries:
  - releasing-a-read-capability-moves-registry-pins
---

# GOAL-20261008-036 — 承接面按研究循环实际需要扩容（`review.read`）

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 4**（轴 = **广度**，
> 依赖序 2、3 —— 两者已 ACHIEVED）。
> **MAINLINE 明文约束**：广度**不是一条轴**，承接面**只在研究循环真正用到时补**，
> **不做数量目标** ⇒ 本轮**只承接一条**能力，代价是它必须**端到端真跑**。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 为什么是 `review.read`：词表里有、声明面零承接、policy 零放行、分类理由已被 GOAL-035 推翻 | PASS |
| EC-02 | 端到端承接链 | 声明 + 实现 + 绑定 + 接线 + 放行（五件缺一不可） | PASS |
| EC-03 | 真被用上 | 一次实跑里后续 phase 通过它**读到前序 phase 落库的逐条判词** + 两向反证点名 | PENDING |
| EC-04 | 登记面与读数 | 分类清单纯收紧 + 夹具同轮 + 覆盖 19/46 → 20/46 **逐条** | PENDING |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**为了凑数**声明没有实现的
能力；不得**先声明未放行能力**（先放行再声明）；不得把 destructive / 写 / 执行 / 审批类能力
改成 allow（本轮只放行只读能力**一条**）；不得**宣称项目安全**（`R-M1`）；不得宣称投递语义为
「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**。主树零改动（只读勘察）。

### 1. 为什么是 `review.read`（而不是别的条目）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 词表**有**它 | `examples/config/capabilities.yaml` | 46 条含 `review.read` |
| 1.2 | 声明面**零**承接 | `tool_providers.yaml` 全量反查 | 声明面 distinct **19** 条，**不含** `review.read` |
| 1.3 | 策略面**零**放行 | `examples/config/policy.yaml` | `allow` 里**没有** `review.read` ⇒ 落 `default_effect: DENY` |
| 1.4 | 分类表的理由**已过期** | `tests/architecture/python/test_capability_coverage_is_implemented.py` 的 `_OUT_OF_SCOPE_REASONS` | 原文「B 组：需要评审实体（**今天的评审走 task/handoff 面**）」—— GOAL-035 EC-01 已把验收结论**落 canonical**（`ReviewFindingStore` + `GET /runs/{run_id}/reviews`） |
| 1.5 | **真需要的证据** | GOAL-035 的未覆盖 `N-3`（多评审者聚合）+ 迭代日志 cycle 3/4 行 | 「结论驱动」目前只能看制品与停止判据；**读不到上一轮的评审结论**（逐条判词）⇒ 跨轮质量闭环缺一环 |
| 1.6 | 承接口径是「五件事」 | 既有先例（`budget.read` / `experiment.read` / `run.read` 的承接） | 声明 + 实现 + 绑定 + 接线 + 放行 —— `run.read` 的注释原文：「**承接 ≠ 放行**」 |

### 2. 承接机制与规模约束（本轮实现面的形状由它们决定）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | provider 依赖是**可选**的 | `adapters/canonical/read_provider.py` | `budget_ledger` / `experiment_store` / `run_store` 三条先例；缺省 `None` ⇒ 工具**点名**不可用（不返回空账本 / 空列表冒充） |
| 2.2 | `read_provider.py` 行数 | `wc -l` | **410 / 450** ⇒ 新工具宜另立模块（先例 `run_read.py`，50 行） |
| 2.3 | 工具面映射表 | `adapters/canonical/read_surface.py` 的 `_TOOL_CAPABILITIES` | 9 条现成映射（`artifact_read` … `run_read`） |
| 2.4 | 会话工具表 | `services/api/session_tool_support.py` 的 `DEFAULT_SESSION_TOOL_BINDINGS` + `canonical_read_register` | 两个组合根**共用**一个装配回调（「多一个入口就多一次漂移机会」）；依赖面在签名里列全 |
| 2.5 | 出厂形态夹具 | `tests/adapters/canonical/test_canonical_read_provider.py` 的 `_PROVIDER` | 与目录**同轮同步**的既成纪律（`run.read` 的注释原文：「夹具少列一条会让……判据假红（实测）」） |
| 2.6 | 覆盖读数口径 | 建档实测 | 词表 **46** / 声明面 **19** distinct（其中 12 条在 `_IN_SCOPE`、另 7 条在「已承接」分组里） |

### 3. 既有受判面里**本轮必须同轮同步**的清单（且都是**纯收紧**）

| # | 落点 | 为什么必须同步 | 属于「收紧」还是「放宽」 |
| --- | --- | --- | --- |
| 3.1 | `tests/architecture/python/test_capability_coverage_is_implemented.py` 的 `_IN_SCOPE` | 分类判据要求每条能力**要么在射程内、要么登记理由**；把 `review.read` 移入射程并删除它的登记理由 | **收紧**（射程内集合的**下界**只增不减） |
| 3.2 | `tests/adapters/canonical/test_canonical_read_provider.py` 的 `_PROVIDER.capabilities` | 与出厂目录同轮同步（夹具少列 ⇒ 另一条判据假红） | **收紧**（新增一条，不动其余） |
| 3.3 | `examples/config/policy.yaml` | 放行 = **新增一条 `allow`**（`default_effect` / `deny` / `require_approval` / `allow_with_constraints` 一律未动） | **决定**（授权 (0)），不是放宽判据 |
| 3.4 | `services/api/composition.py` / `pg_composition.py` | 两个组合根各把自己的 `ReviewFindingStore` 传进装配回调 | 接线（无判据放宽） |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 本轮承接**几条**能力 | **一条**（`review.read`）—— 「不做数量目标」；代价是必须端到端真跑 |
| ② | 工具实现落点 | **已定（cycle 1）**：另立 `adapters/canonical/review_read.py`（68 行），`read_provider.py` 只留一行委派（**421 / 450**） |
| ③ | 放行的 scope | **已定**：与同级读能力对齐（`artifact.read` / `evidence.read` / `run.read` = `project`） |
| ④ | 「读到」的判据形态 | cycle 2 定：读到的判词必须与**前序落库的逐字一致**（下游消费证据，不是「调了两遍工具」） |
| ⑤ | 覆盖面继续扩容 | **不做**（MAINLINE：广度不是一条轴，不做数量目标） |
| ⑥ | **同轮同步面清单修正**（cycle 1 实测发现） | **已定**：放行一条读能力会牵动**策略面登记表族**（5 处，逐条枚举进 `fix_policy`）；处置 = **加法/搬迁登记**、**谓词阈值不变**；清单外仍禁改（触达即 BLOCKED） |

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
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-036` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（承 GOAL-035 的实测
  教训：治理校验器是 `governance-check/scripts/validate.py`，**不是** `validate_cursor_framework.py`）；
  m0 按组、**独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；
  受影响的定向套件（`tests/adapters` / `tests/architecture` / `tests/api` / `tests/e2e` /
  `tests/contracts` / `tests/application`）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run。
  **一个 cycle 攒成一次推送**（同批推送只有 HEAD 产生 run ⇒ 逐提交台账按 `covered_by` 登记）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **先放行再声明**：未放行的能力写进协议 ⇒ 差集判据红是**真红**（不是待办）；
- **承接 = 五件事**：声明 + 实现 + 绑定 + 接线 + 放行，缺一即判红并点名缺哪件；
- **「真的被用上」才算数**：要**下游消费证据**（读到前序落库的逐字判词），不是「调了两遍工具」；
- **点名失败而非静默**：缺依赖 / 未放行 / 缺实现一律点名（不返回空列表冒充「没有」）；
- **受判面不得是交集**（承 `MEM-160`）：新判据的受判面必须是**声明集 / 集合本身**；
- **先复核再依赖**：本 GOAL 的起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；
- **新记录落地后立刻跑治理**（承 `MEM-20261008-197` 与 GOAL-035 的实测教训）。

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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-035 的 `N-1`…`N-6`；GOAL-034 的 `W-1`…`W-4`；
GOAL-033 的 `W-1`…`W-6`；GOAL-032 的 `W-1`…`W-8`；历史 `tools/` 目录仍有 73 条旧 lint 与
无机器门的旧脚本；GOAL-019…035 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**其余 26 条未承接能力仍在登记表里**：本轮**只**承接 `review.read`
  （MAINLINE：不做数量目标）；它们的分组与理由**原样保留**。
- （建档时登记）**多评审者聚合（GOAL-035 `N-3`）仍不因本轮而收口**：本轮只让评审结论
  **对后续 phase / 后续轮次可读**；聚合逻辑本身不在本轮范围。
- （建档时登记）**读面未认证**（承继）：`review.read` 走的是**能力 + 策略**面（写面认证
  那条线未动）。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**；
**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **`review.read` 承接**：**已收口** = 五件事齐 + 一次实跑真的读到前序落库的逐条判词；
  **未覆盖** = 「读到的评审结论**质量**如何」（那是评审者的事，不在承接范围）。
- **放行面**：**已收口** = 新增**一条只读**放行且 default/deny/审批面零变化；
  **未覆盖** = 写面 / 执行面 / 审批面的放行（本轮范围外，触达即 `escalation_triggers`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；**无自己的 run 也如实登记原因**（同批推送时只有 HEAD 产生 run）；
> 现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的「回顾性台账」提交自身
> 不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以「末条提交 + 覆盖说明」封闭，
> **不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `18a078a`（**建档**） | **无自己的 run**（同批推送） | cycle 0 建档；它与 GOAL-035 的台账尾巴 `512360a` **同一次 push** ⇒ 只有 HEAD 产生 run ⇒ `covered_by 512360a`（实测取证：两个 SHA 的 `head_sha` 查询 `total_count=0`） |
| `512360a`（GOAL-035 台账尾巴，本批 HEAD） | `37753132183` **M0 success**（8 job 全 success）+ `37753131400` **Push/CodeQL success**（3 分析全 success） | 该批 HEAD；**同时承担** `18a078a` 的绿 + **封闭 GOAL-035 台账的自我指涉边界**（两条同批路径都有实测读数） |
| （cycle 1 提交） | 待推送 | EC-01/EC-02 承接链 + 同轮同步面 5 处 + 记录（本 cycle） |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（建档） | `18a078a`（与 GOAL-035 台账尾巴同批） | 只读勘察（0 改动）；五条 EC 全 PENDING | （见 CI 台账） | — | 五条 EC 全 PENDING；实现落点（②）待 cycle 1 定 | cycle 1（EC-01 勘察定稿 + EC-02 实现面） |
| 1 | `PLAN-20261008-331` | （见 CI 台账 cycle 1 行） | EC-01 + EC-02 落地：四道门（ruff/format/mypy/规模 68·421 行）绿；**全量 python 套件 5361 passed, 20 skipped**（相对建档基线收集数 +1 = 新模块进源文件参数化面）；`tests/application/preflight` **60 passed**（同步面改完）；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5359 passed, 20 skipped**，收集数 +1 逐文件分解） | （见 CI 台账） | **门链抓到策略面 4 处登记表**（差集表 / `_CAPABILITY_SCOPE` / 两处登记计数）⇒ 同轮同步（加法/搬迁，谓词不变）并**修正 `fix_policy` 的同步面清单**（决策 ⑥，如实登记） | EC-01/EC-02 收口；**下一轮 EC-03**（真用判据 + 两向反证） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **cycle 1（EC-01/EC-02）**：勘察定稿 + **承接链五件事齐** —— 实现 `adapters/canonical/review_read.py`（读 `ReviewFindingStore.for_run`，缺依赖**点名**不可用）、描述子/能力映射、provider 依赖位与 handler、会话绑定表、装配回调与**两个组合根接线**、出厂目录声明、`policy.yaml` **新增一条只读 `allow`**（scope `project`）。**门链抓到策略面 4 处登记表**（差集表 / `_CAPABILITY_SCOPE` / 「该登记」计数 / 放行集合）⇒ 同轮**加法/搬迁**同步（谓词、阈值、受判形态一字未改），并据此**修正本 GOAL 的 `fix_policy` 同轮同步面清单**（决策 ⑥）。EC-01/EC-02 `PASS`；EC-03/04/05 仍待收口。未覆盖范围原样保留；**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 程序表序 4 + GOAL-035 收口面；只读勘察把「按研究循环实际需要扩容承接面」落成**一条**可实测的目标 —— `review.read`（词表 46 条里有、声明面 19 条里**零**承接、`policy.yaml` 零放行、分类理由已被 GOAL-035 EC-01 推翻；真需要的证据 = 跨轮「结论驱动」读不到上一轮评审结论，且它是 GOAL-035 `N-3` 的前置）。五条 EC 全 `PENDING`。**不做数量目标**（MAINLINE 明文）；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
