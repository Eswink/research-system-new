---
id: GOAL-20261008-034
slug: multi-round-research-loop-and-stop-rules
title: 多轮研究循环（至少三轮）+ 结论驱动的停止判据 —— 把 iterative_optimizer / stop_conditions 从「声明面」推进到「真循环且有停止规则」
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 2 推进深度轴**，并授权本驱动自动化循环
    推进、**收口后立即开下一个 GOAL，不停下来等指令**。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含放宽某条 allow、改产品语义、新增 ADR），**不等于**可以放宽**判据、门禁、阈值或
    断言** —— 本轮无例外。
    (1) **本 GOAL 的授权开工**（MAINLINE 程序表序 2 的「一句话目标」逐条落地）：
    (i) **多轮研究循环（至少三轮）** —— 建档实测：最深循环是**两轮**
    （`examples/protocols/two_round_research_loop_v1.yaml`，其注释明文写「不声称多轮迭代的
    上限/收敛」），且 `PhaseStrategy.ITERATIVE_OPTIMIZER` / `POPULATION_SEARCH`
    **只有枚举、零消费点**；⇒ 本轮把「多轮」做成**真的多轮**；
    (ii) **声明的收敛与停止判据** —— 建档实测：`StopConditions`（`max_iterations` /
    `budget_exhausted`）**被解析、被编译（`CompiledStopCondition`）、被 preflight 校验，
    但运行期零消费点**（`rg -n "\.stop_conditions" packages/application/run_orchestration/
    services/api/ adapters/` = **零命中**）⇒ 一个声明了就没人看的字段；
    (iii) 两项带来的**同步集**（声明面 / 文档 / 判据射程 / 镜像表）；
    (iv) 修实现过程中发现的**真缺陷**。
    (2) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足，逐条保持）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面** /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；**宣称项目安全**
    （`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；口径只能是
    at-least-once + idempotency + deduplication）；**静默改 `terminal()` 语义而不留 ADR**；
    **把「固定轮数」当「结论驱动」**（MAINLINE 明文：固定轮数的流水线加长**不算**推进深度轴）。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）；
    默认姿态不变（默认 runtime 保持 **Fake**、默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (5) **边界（承继）**：GOAL-001…033 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…033 的未覆盖范围**原样保留**；
    GOAL-033 的残余 `W-1`…`W-6` / `R26-*` 终态**原样保留**，本轮**只追加**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 MAINLINE 程序表序 2（**深度**轴）推进到「**多轮推进且有停止规则**」：① **多轮研究
    循环（至少三轮）** —— 一次 run 内跑**≥3 轮**研究，且轮与轮之间的**派生是声明的**
    （复用 GOAL-031 EC-03 的 run-chain 派生机制：读上一轮产出 → 按声明路径取标识）；
    ② **停止规则由结论驱动** —— 轮数**不是**写死的固定值：停止判据读**本轮结论**的
    可观察事实（例如「本轮未产生新标识」），触发即停并**可观测**（进 canonical 事件链，
    不是静默）；`max_iterations` 只作**上界护栏**（防失控），**不得**当成唯一的停止理由；
    ③ **跳过/停止可观测** —— 停止与跳过都必须落在读面上（承 GOAL-031 的
    `run.completed.skipped` 形态：点名**哪条**、**为什么**）；④ **自举收口** —— 验证器进树 +
    两树复检 + 判词归档进树 + as-is m0 23/23（在**全部记录写入之后**）+ 治理绿 +
    CI 台账逐提交。
    **硬约束**：先复核再依赖（本 GOAL 的起点事实全部待复核）；受判面**不得**是交集 / 过滤 /
    空集恒真；真被使用才算数（断言调用证据 + 下游消费证据，不得只断言「声明了」/「注册了」）；
    点名失败而非静默；留档**二进制写盘**、判词归档**进树**；m0 条数**仍是 23**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **多轮研究循环（至少三轮）**。
      (a) **勘察前置（实测）**：`PhaseStrategy.ITERATIVE_OPTIMIZER` / `POPULATION_SEARCH`
      的**消费点清单**（逐文件读数，预期为零）；`StopConditions` /
      `CompiledStopCondition` 的**解析 → 编译 → preflight → 运行期**四段各自的消费点；
      `execute_phases` 的循环结构（逐 group 一次，还是可重复）；两轮协议里派生链的
      具体字段（`artifact_from_previous` / `ids_from_previous` / `requires_previous_ids`）；
      (b) **实现**：一次 run 内跑 **≥3 轮**研究。**不建第二套编排**：轮次必须挂在既有
      相位执行链上（`execute_phases` / `_execute_phase_group`），派生链复用既有
      `RunChainCall` 机制（**不新造**「上一轮结果传递」的第二条路）；
      (c) **派生可追**：第 N 轮（N≥2）读到的标识**只可能**来自第 N-1 轮的产出
      （经读面，不是内存传递）—— 由判据断言「第 N 轮读取步的证据里逐字带着第 N-1 轮
      返回的标识」；
      (d) **判据（新）**：三轮实跑（触发臂）⇒ 三个 phase 各产出交付物、证据链可读、
      第 2/3 轮的派生可追到上一轮；
      (e) **反证**：把派生规则改坏（指向不存在的路径）⇒ 判红（点名那条路径）；
      (f) **实跑留档**：三轮全程的状态转移与工具证据计数。
      **同轮同步集（建档实测标定，逐条登记，且**仅限**这些）**：待 cycle 1 勘察后标定
      （预期：协议文档 `docs/architecture/RESEARCH_PROTOCOL.md` 的 phase 字段说明 /
      OpenAPI 快照若无改动则不动 / 新增示例协议的契约夹具）。
      **上述以外的任何既有判据改动 ⇒ BLOCKED**；每条同步都要在记录内给出 before/after 与
      「强度未降」自证。
      **判据**：勘察读数 + 三轮实现 + 派生可追 + 两向反证 + 实跑留档 + 同步集自证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/application
      tests/domain tests/loaders -q` ⇒ 全绿；新增判据文件（三轮实跑 / 派生可追 / 反证）
      全绿；配套留档：消费点清单读数、三轮状态转移、派生链逐轮证据、反证判红原文、
      同步集 before/after 与「强度未降」自证。
    status: PENDING
  - id: EC-02
    criterion: >-
      **停止规则由结论驱动（不是固定轮数）**。
      (a) **勘察前置**：`stop_conditions` 的**四段消费点**（解析 / 编译 / preflight /
      运行期）逐段实测读数；现有文档对它的表述（`RESEARCH_PROTOCOL.md` / schema /
      前端表单）与**实际行为**的差集；
      (b) **实现**：停止判据读**本轮结论的可观察事实**并据此停止 —— 至少一条**非轮数**的
      停止理由（例如「本轮未产生新标识 ⇒ 无新增可追内容 ⇒ 停」）；
      (c) **`max_iterations` 是上界护栏而非唯一理由**：判据必须能区分两种停止
      ——**结论驱动停止**与**上界护栏停止**（两者的读面事实不同），且**不得**让上界成为
      常态（协议里上界 > 结论驱动通常触发的轮数）；
      (d) **停止可观测**：停止事实进 canonical 事件链（点名**哪条判据**触发、**读了哪个
      事实**、**当时的值**）—— **不得**静默停；
      (e) **判据（新）**：① 结论驱动停止臂（用一个会让结论收敛的注入）⇒ 停止理由 = 结论类；
      ② 上界护栏臂（让结论永不收敛）⇒ 停止理由 = 上界类；两臂的**判词不同且互斥**；
      (f) **反证**：把停止判据改坏（去掉结论驱动那条）⇒ 判红（该臂跑到上界才停，
      停止理由变成上界类 ⇒ 与 ① 的断言矛盾）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/application
      tests/loaders -q` ⇒ 全绿；新增判据文件（两臂 + 停止理由可区分 + 反证）全绿；
      配套留档：四段消费点读数、两臂判词对照、反证判红原文。
    status: PENDING
  - id: EC-03
    criterion: >-
      **停止与跳过都落在读面上（可观测，非静默）**。
      (a) 停止事实、跳过事实（含理由与点名对象）都在**既有读面**可读（承 GOAL-031 的
      `run.completed.skipped` 形态；**不新造**平行读面）；
      (b) **判据**：读面断言 —— 停止/跳过事件逐条可读，且**无跳过时载荷逐字节不变**
      （既有语义不因本轮扩张而漂移）；
      (c) **反证**：把「跳过带理由」改成静默跳过 ⇒ 判红。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/observability
      tests/api -q` ⇒ 全绿；新增判据文件全绿；配套留档：读面读出的事件逐条、反证判红原文。
    status: PENDING
  - id: EC-04
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools` +
      `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py`，`--script-mode shared` +
      `--base-ref`）+ **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**、
      `CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（宪章程序面：本 GOAL 的 id 已
      替换 MAINLINE 序 2 的占位，进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 / 空字段 =
      未取证**；自我指涉边界**明写并封闭**）；⑥ 承继残余逐条在位（GOAL-033 的 `W-1`…`W-6` /
      `R26-*` 终态 / 未覆盖范围逐条保持 + 理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal034_closeout.py --root .
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
      **为了凑数而声明没有实现的能力**；**把受判面写成交集 / 过滤 / 空集恒真**
      （承 `MEM-20260928-160` / `MEM-20261005-187`）；**只断言「声明了 / 注册了」而不取
      调用与下游消费证据**；**把「固定轮数的流水线加长」当推进深度轴**（MAINLINE 明文禁止）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据
      （`test_reproducibility_wording.py` / `test_delivery_semantics_wording.py` /
      `test_record_face_is_covered_by_the_gate.py`）、两树入口判据、规模门禁、
      `tests/application/preflight/**`、`tests/contracts/**`、`tests/adapters/**`、
      `tests/e2e/**` 既有文件）—— **新增**判据与新增文件不受此限
    - >-
      **静默改 `terminal()` / 死信语义 / 相位执行语义而不留记录**（相位链的改动必须有
      判据与 before/after 对照）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 多轮循环需要改动 `PhaseStrategy` 的语义（枚举值含义变更）而无法只靠新增类型承载
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261008-034 — 多轮研究循环（至少三轮）+ 结论驱动的停止判据

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 2**（轴 = **深度**）。
> 本文件是 GOAL-033（连续性轴）的后继：GOAL-033 让研究**可中断可恢复**，本 GOAL 让研究
> **能多轮推进且知道何时停**。

## 目标与退出标准

四条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 多轮研究循环（≥3 轮） | 勘察读数 + 三轮实现 + 派生可追 + 两向反证 + 实跑留档 | PENDING |
| EC-02 | 结论驱动的停止规则 | 四段消费点 + 非轮数停止理由 + 上界护栏可区分 + 停止可观测 + 两臂互斥 + 反证 | PENDING |
| EC-03 | 停止/跳过落在读面 | 既有读面可读 + 无跳过时载荷不变 + 反证 | PENDING |
| EC-04 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**宣称项目安全**
（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）；
不得把**固定轮数的流水线加长**当作推进深度轴（MAINLINE 的「反面」列明文）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**（提示词已声明起点事实全部待复核）。主树零改动（只读勘察）。

### 1. 最深循环 = 两轮 —— 复核通过

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 唯一的多轮协议 | `ls examples/protocols/` + 逐文件数 phase | `two_round_research_loop_v1.yaml` **2 phase**（其余协议 phase 数更少或为单链多相位，非"轮"语义） |
| 1.2 | 该协议**不声称**多轮上界 | 协议原文注释 | 逐字：「**不声称**多轮迭代的上限/收敛（两轮是本轮射程）」 |
| 1.3 | 派生链机制 | `tests/e2e/test_research_loop_second_round_derived.py` + `two_round_loop_support.py` | `RunChainCall` 的 `artifact_from_previous` / `ids_from_previous` / `requires_previous_ids` 三字段；判据逐条钉住 |
| 1.4 | 派生判定是**声明式**的 | `packages/application/run_orchestration/phase_capability_triggers.py` | `should_skip` / `select_artifact_id` 读声明字段；应用层无「如果就」 |

### 2. `iterative_optimizer` / `population_search` 是**枚举孤儿**（零消费点）

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 枚举定义 | `packages/domain/protocols.py:35-38` | 六种策略都有枚举值 |
| 2.2 | 消费点 | `rg -n "ITERATIVE_OPTIMIZER\|POPULATION_SEARCH\|MAP_REDUCE\|PARALLEL_AGENTS" --type py packages/ services/ adapters/` | **只命中枚举定义处**（`protocols.py`）—— 三个执行面**零消费** |
| 2.3 | 出厂协议**已经在用**它 | `examples/protocols/m12_reference_research_v1.yaml` 的 `execution` phase | `strategy: iterative_optimizer` + `stop_conditions: {max_iterations: 4, budget_exhausted: true}` |
| 2.4 | 执行链不看 strategy | `packages/application/run_orchestration/phase_runner.py` | `rg -n "strategy" phase_runner.py` ⇒ **零命中** ⇒ 策略字段对执行**无影响** |

### 3. `stop_conditions` 是**声明了就没人看**的字段（本轮 EC-02 的靶子）

| # | 段 | 落点 | 消费点 |
| --- | --- | --- | --- |
| 3.1 | 解析 | `adapters/contracts/protocol_loaders.py::_stop_conditions` | **有**（YAML → `StopConditions`） |
| 3.2 | 编译 | `packages/application/protocol_compile/compiler.py::_stop_conditions` | **有**（→ `CompiledStopCondition`） |
| 3.3 | preflight 校验 | `compiler.py::_validate_stop_conditions` | **有**（只校验引用的 phase 存在） |
| 3.4 | **运行期** | `rg -n "\.stop_conditions" packages/application/run_orchestration/ services/api/ adapters/` | **零命中** ⇒ 运行期**从不读它** |

**结论**：`max_iterations: 4` 是**装饰性声明** —— 没有任何执行路径会因它而停。这正是
MAINLINE 深度轴要消灭的形态（「轮数由结论驱动，不靠固定轮数」的前提是**先真的有一套
停止规则**）。

### 4. 相位执行链是**单遍**拓扑序（无轮次概念）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 4.1 | 主循环 | `phase_runner.py::execute_phases` | `for index, group in enumerate(groups)` —— 每组**恰好一次** |
| 4.2 | 分组 | `_phase_groups(specs)` | 按 phase 分组；组间拓扑序，组内并发 |
| 4.3 | 续跑 | `service.resume_rebuilt` | 重算**剩余**工作（`_remaining_specs`）⇒ 无「再来一轮」语义 |

**结论**：「多轮」今天只能靠**在协议里写死多个 phase** 实现（两轮协议就是这么写的）
⇒ 那是**固定轮数的流水线加长**，正是 MAINLINE 明文列出的「不算推进深度轴」的反面形态。

### 5. 跳过事实的既有读面形态（EC-03 复用，不新造）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 5.1 | 跳过进事件链 | `phase_runner.py::execute_phases` 的 `skips` | 无跳过 ⇒ **不带该键**（既有 payload 逐字节不变） |
| 5.2 | 跳过理由来源 | `phase_capability_triggers.skip_reason` | 点名**工具 + 字段**（不是静默） |
| 5.3 | 判据 | `tests/e2e/test_research_loop_second_round_derived.py` | 两臂**互斥**断言（触发臂有工具证据无跳过事实；不触发臂反之） |

### 6. 起点表述的出入（逐条）

- 提示词称「最深研究循环 = 2 轮」：**复核通过**（见 1.1 / 1.2）。
- 提示词未提 `stop_conditions`：**建档勘察新增的事实**（见第 3 节）——
  它是深度轴上**比"再多一轮"更根本**的缺口（没有停止规则的多轮 = 固定轮数）。
- 提示词称承接面 19/46：**本 GOAL 不依赖该数**（深度轴不碰承接面）；未在本轮重新实测，
  如实登记为**待复核**。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 轮次挂既有相位链（不建第二套编排） | **已定**（EC-01 (b)） |
| ② | 派生复用 `RunChainCall`（不新造结果传递路径） | **已定**（EC-01 (b)） |
| ③ | 「结论驱动停止」的判据取哪个事实 | **cycle 1/2 勘察后定**（须是**本轮结论**的可观察事实，不是轮数） |
| ④ | `max_iterations` 的语义（上界护栏） | **已定**：保留上界语义，但**不得**是唯一停止理由（EC-02 (c)） |
| ⑤ | `PhaseStrategy` 枚举值语义 | **不改**（若要改须 ADR ⇒ escalation）；新多轮能力尽量用**新增**类型承载 |
| ⑥ | 承接面扩容 | **不做**（MAINLINE：广度不是一条轴） |

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
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-034` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（承 GOAL-033 的
  `W-1` 教训：新 PLAN/RECHECK 落地后**立刻**跑治理，别等到 CI）；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响的定向套件
  （`tests/domain` / `tests/application` / `tests/e2e` / `tests/loaders` / `tests/api`）；
  web 门按改动面（本 GOAL 预期零 web 源码改动）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run。
  **一个 cycle 攒成一次推送**（承 GOAL-033 `W-3`：本 GOAL 我在上一轮实测被
  `cancel-in-progress` 取消过一次在飞 run）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤；
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **先复核再依赖**：起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **「结论驱动」不是修辞**：判据必须能**区分**结论驱动停止与上界护栏停止，且两者的
  读面事实不同（EC-02 (c)(e)）；
- **受判面不得是交集**（承 `MEM-160` / `MEM-20261005-187`）：新判据的受判面必须是**声明集**本身；
- **真被使用才算数**：断言调用证据 + 下游消费证据，不得只断言「声明了」/「注册了」
  （本轮靶子正是「声明了就没人看」的字段）；
- **点名失败而非静默**：停止 / 跳过 / 缺口一律点名；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；
- **新记录落地后立刻跑治理**（承 GOAL-033 `W-1` 与 `MEM-20261008-197`）。

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

- **ACHIEVED 前置**：四条 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure`（验证器进树 + 两树 + 归档 + m0 +
  治理 + 台账）并声明 `verify_paths` ≥ 2 路、**用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers`（含「需改同步集以外的既有判据断言」）或
  `budget.max_cycles` 触顶（20）；停下留人工决策，逐条写明触发项。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停止并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-033 的 `W-1`…`W-6`；GOAL-032 的 `W-1`…`W-8`；
`W31-1`…`W31-4`；历史 `tools/` 目录仍有 73 条旧 lint 与无机器门的旧脚本；
GOAL-019…033 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 收口（引擎面）+ GOAL-033 收口（产品面）** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**EC-02 的停止判据事实未定**：「读哪个结论事实」由 cycle 1/2 勘察后定
  （决策登记 ③）；建档时不预设。
- （建档时登记）**`PhaseStrategy` 零消费是既有事实**：本轮修复面**只覆盖研究循环用到的那部分**
  （`iterative_optimizer` 相关的多轮语义）；`population_search` / `map_reduce` 若同样零消费，
  **如实登记**而不是顺手全实现（广度不是一条轴）。
- （建档时登记）**承接面读数待复核**：提示词的 19/46 未在本轮重新实测。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**
（`consumer_offsets` 只在文档）；**不得**据此宣称项目安全；**不得**宣称投递语义为
「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 三条「已收口 vs 未覆盖」分界（逐条明写）

- **EC-01 多轮循环**：**已收口** = ≥3 轮的实跑 + 派生可追 + 反证；**未覆盖** = 并行多轮
  （`parallel_agents` / `map_reduce`）、跨 run 的知识累积（那是 MAINLINE 序 5）。
- **EC-02 停止规则**：**已收口** = 结论驱动 + 上界护栏可区分 + 落事件链；**未覆盖** =
  预算驱动的停止（`budget_exhausted` 若不在本轮射程则如实登记）、跨 run 的收敛判定。
- **EC-03 读面**：**已收口** = 停止/跳过在既有读面可读；**未覆盖** = 前端展示面
  （若需要，属手写面）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的
> 「回顾性台账」提交自身不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以
> 「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （cycle 1 起逐条追加） | | |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（建档） | （本文件所在提交） | 只读勘察（0 改动）；四条 EC 全 PENDING | PENDING | — | 四条 EC 全 PENDING；EC-02 的停止判据事实待定 | cycle 1（EC-01 勘察 + 三轮实现） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 宪章 + `goals/README.md` 格式契约 + GOAL-033 全文；只读勘察**复核并新增**了起点事实 —— ① 最深循环确为 2 轮（协议明文不声称上界）；② `ITERATIVE_OPTIMIZER` / `POPULATION_SEARCH` 是**枚举孤儿**（零消费点），而 `m12_reference_research_v1.yaml` 已在用 `iterative_optimizer`；③ **`stop_conditions` 运行期零消费**（解析 / 编译 / preflight 三段有、运行期无）⇒ `max_iterations: 4` 是装饰性声明；④ 相位执行链是**单遍**拓扑序（无轮次概念）⇒ 今天的「多轮」只能靠写死多个 phase。四条 EC 全 `PENDING`。**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
