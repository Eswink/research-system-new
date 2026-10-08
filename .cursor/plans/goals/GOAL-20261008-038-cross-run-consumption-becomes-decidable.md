---
id: GOAL-20261008-038
slug: cross-run-consumption-becomes-decidable
title: 跨轮消费**成为可判定** —— 把「读到前一轮结论」推进到「读到的结论**真的影响**本轮产出」（交付物声明 + 编排层求值）
status: ACHIEVED
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 6（保留槽，由前序 GOAL 的发现驱动）开新 GOAL**，
    并授权本驱动自动化循环推进、**收口后立即开下一个 GOAL，不停下来等指令**。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含新增域字段、改产品语义、新增 ADR），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **本 GOAL 的立题依据是 GOAL-037 的实测残余 `O-4`**（原文：「读到 ≠ 影响科学结论」）：
    GOAL-037 证到「后一轮**读到**前一轮的落库结论」（下游消费 = 判决值逐字 + 按 run id
    归属）；**未**证「读到的结论**改变**了后续轮的产出」。本轮把后半句落成**可判定**。
    (2) **实测起点**（建档勘察给出读数）：`AcceptanceCriterionType.CUSTOM_EVALUATOR` 与
    `AcceptanceCriterion.evaluator` **已声明**（域类型 + 合约 schema 字段），但
    `_evaluate_custom_evaluator` 的实现体恒判负并明说「must be executed by the
    orchestration layer」——**全仓没有任何编排层求值器**（`rg` 零命中）⇒ 这是一个
    **已声明、未实现**的扩展点，正是「交付物自己声明它消费了什么」的落点。
    (3) **不做数量目标**：本轮只做这一条判定链（交付物声明 → 编排层求值 → 判词进既有读面）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面** /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/
    宣称投递语义为「恰好一次」（**明确否认**）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
    口径只能是 at-least-once + idempotency + deduplication）；
    **用「加了计数或阈值」冒充质量**（MAINLINE 质量轴的反面）；
    **把「影响」判成文本子串巧合**（判据必须是**结构化**的：声明路径 → 取值 → 与来源比对）。
    (6) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime 保持 **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (7) **边界（承继）**：GOAL-001…037 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…037 的未覆盖范围**原样保留**；
    GOAL-037 的残余 `O-1`…`O-5` / `R26-*` 终态 / 未覆盖范围**原样保留**，本轮**只追加**。
    (8) **driver** = client-goal、**owner** = root-agent。
objective: >-
    把 MAINLINE 程序表序 6（保留槽）落成**质量轴的下一次推进**：
    ① **勘察定稿** —— `CUSTOM_EVALUATOR` 是「已声明、未实现」的扩展点（域类型 + 合约字段
    在场、编排层求值器全仓零命中；GOAL-037 的 `O-4` 是它的立题依据）（EC-01）→
    ② **交付物声明它消费了什么** —— 合约的 `CUSTOM_EVALUATOR` 判据声明**结构化路径**
    （本轮消费的产物里，哪一条**逐字**来自前序 run 的落库结论），与 `REVIEW_SCORE` 的
    `metric` 同一口径（声明式、fail-closed：声明缺失 / 路径缺失 / 值不符 ⇒ **点名**，不回落）（EC-02）→
    ③ **编排层求值** —— 在**验收门求值点**执行该求值器：把「本轮产物里那条声明路径的值」与
    「前序 run 落库的结论」**结构化比对**（相等 ⇒ 判过并留痕；不等 ⇒ 判负并点名期望值与实际值），
    判词进**既有** `ReviewFindingStore` 读面（不给读面加第二套真相）（EC-03）→
    ④ **真的被用上（跨轮）** —— 程序跑两轮：第 2 轮的交付物**声明并真的携带**第 1 轮的结论，
    验收门判过且判词可复核；**反证两向**（第 2 轮产物**不带**前序结论 ⇒ 判负点名；
    声明路径不存在 ⇒ 求值器**点名**配置错误）（EC-04）→
    ⑤ **自举收口**（复用 GOAL-037 的机器）（EC-05）。
    **硬约束**：判定必须是**结构化**的（声明路径 → 取值 → 与来源逐字比对），**不得**用文本
    子串巧合冒充「影响」；fail-closed（缺声明 / 缺路径 / 值不符一律点名，不回落默认值）；
    判词进既有读面；m0 条数**仍是 23**；留档**二进制写盘**、判词归档**进树**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（`CUSTOM_EVALUATOR` 是已声明、未实现的扩展点）**。(a) 域与合约面读数：
      `AcceptanceCriterionType.CUSTOM_EVALUATOR` 与 `AcceptanceCriterion.evaluator` 在场
      （`schemas/task-contract.schema.json` 的字段也在场）；(b) **实现面读数**：
      `_evaluate_custom_evaluator` 的实现体**恒判负**且明说「must be executed by the
      orchestration layer」；`rg` 全仓**零命中**该求值器（`packages/` / `services/` /
      `adapters/` / `examples/`）⇒ **没有任何编排层实现**；(c) **立题依据**：GOAL-037 的
      残余 `O-4`（读到 ≠ 影响产出）逐字引述在案；(d) 可复用的缝：`REVIEW_SCORE` 的
      **声明路径**先例（`declared_review_score`，fail-closed 三态）、验收门求值点
      （`evaluation_gate.py`）、既有读面（`ReviewFindingStore`）。
    verify: >-
      `rg -n "CUSTOM_EVALUATOR" packages/ services/ adapters/ examples/` ⇒ 仅域类型与
      域求值器；`rg -n "custom evaluator" .` 读数；`CriterionEvaluation` 的返回逐字。
    status: PASS
  - id: EC-02
    criterion: >-
      **交付物声明它消费了什么（声明式，与 `REVIEW_SCORE` 同口径）**：合约的
      `CUSTOM_EVALUATOR` 判据用**既有** `metric` 字段声明「本轮产物里哪条结构化路径承载
      前序结论」；解析器（新，与 `declared_review_score` 同形）**fail-closed**：
      未声明 / 路径缺失 / 值不是字符串或对象 ⇒ 求值器**点名**（不回落、不猜）。
    verify: >-
      新判据文件：三态（声明在场且路径可取 / 声明在场但路径缺失 / 未声明 ⇒ 点名）逐条。
    status: PASS
  - id: EC-03
    criterion: >-
      **编排层求值（结构化比对 + 判词进既有读面）**：验收门求值点执行该求值器 ——
      「本轮产物里声明路径的值」与「前序 run 落库的结论（逐字）」**结构化比对**：
      相等 ⇒ 判过并留痕（判词含来源 run id 与逐字值）；不等 ⇒ 判负并**点名期望值与实际值**；
      前序结论**不存在** ⇒ 点名（不得把「没有前序」当成「判过」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒
      全绿；新判据逐条。
    status: PASS
  - id: EC-04
    criterion: >-
      **真的被用上（跨轮）+ 两向反证**：(a) 程序跑两轮，第 2 轮交付物**声明并真的携带**
      第 1 轮结论 ⇒ 验收门判过、判词经**既有** `GET /runs/{id}/reviews` 可复核（含来源
      run id 与逐字值）；(b) 反证①：第 2 轮产物**不带**（或带的是**另一个**值）⇒ 判负且
      点名期望值 / 实际值；(c) 反证②：声明路径不存在 ⇒ 求值器**点名**（配置错误，不是静默判负）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据文件全绿。
    status: PASS
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
      序 6 的占位**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled`
      如实登记 + 原因 + `covered_by`；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）；
      ⑥ 承继残余逐条在位（GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态 / 未覆盖范围逐条保持 + 理由）；
      ⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal038_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；`uv run --frozen --no-sync python -B
      .cursor/skills/governance-check/scripts/validate.py` ⇒ 绿；
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 全绿；配套留档：
      两路判词 sha256 相同的归档、m0 日志、CI 台账逐提交行。
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
      **把「影响」判成文本子串巧合**（必须是结构化比对：声明路径 → 取值 → 与来源逐字比）；
      **把「没有前序结论」当成「判过」**（fail-closed：缺席一律点名）
    - >-
      **为了凑数而声明没有实现的能力**；**把受判面写成交集 / 过滤 / 空集恒真**；
      **只断言「判据登记了 / 声明了」而不取求值、判词与反证三条证据**
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**`、
      `tests/application/**`、`tests/domain/**` **既有文件**）—— **新增**判据与新增文件不受此限
    - >-
      **同轮同步面**：仅当本轮新增判定 / 新读面**必需**时，允许对**既有**登记面做
      **加法 / 搬迁登记**（谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**；
      枚举之外的既有判据仍禁改，触达即 BLOCKED。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮不动放行面）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 需要改 `packages/domain/acceptance.py` 的**既有**求值器语义（本轮只**新增**求值路径）
child_plans:
  - .cursor/plans/tasks/PLAN-20261008-347-goal-038-ec01-03-declared-consumption-evaluator.md
  - .cursor/plans/tasks/PLAN-20261008-349-goal-038-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-350-goal-038-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261008-038 — 跨轮消费**成为可判定**

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 6**（保留槽 —— 由前序 GOAL 的
> 发现驱动）。**立题依据**：GOAL-037 的残余 **`O-4`**（原文「读到 ≠ 影响科学结论」）。
> **轴 = 质量**（产出的可判定性：结论有来源支持）。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | `CUSTOM_EVALUATOR` 已声明未实现（域在场 / 编排层求值器零命中 / `O-4` 是依据） | PASS |
| EC-02 | 交付物声明消费 | 合约用既有 `metric` 声明「哪条路径承载前序结论」；解析器 fail-closed 三态 | PASS |
| EC-03 | 编排层求值 | 结构化比对（声明路径取值 vs 前序落库结论）；相等判过留痕 / 不等点名 / 缺席点名 | PASS |
| EC-04 | 真的被用上（跨轮） | 两轮实跑判词可复核 + 两向反证（不带 ⇒ 判负点名；路径不存在 ⇒ 点名配置错） | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**把「影响」判成文本子串
巧合**（必须结构化比对）；不得**把「没有前序」当成「判过」**；不得**宣称项目安全**（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。主树零改动（只读勘察）。

### 1. `CUSTOM_EVALUATOR`：已声明、未实现（本轮补的那一环）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 域类型在场 | `packages/domain/enums.py` | `AcceptanceCriterionType.CUSTOM_EVALUATOR = "CUSTOM_EVALUATOR"` |
| 1.2 | 合约字段在场 | `packages/domain/tasks.py::AcceptanceCriterion.evaluator` | 字段在（向后兼容的展示字段之外的结构化参数） |
| 1.3 | 域求值器**恒判负** | `packages/domain/acceptance.py::_evaluate_custom_evaluator` | 返回 `CriterionEvaluation(criterion.type, False, f"custom evaluator {criterion.evaluator} must be executed by the orchestration layer")` —— 即「**该由编排层执行**，但这里没有」 |
| 1.4 | **编排层零实现** | `rg -n "CUSTOM_EVALUATOR\|custom evaluator" packages/ services/ adapters/ examples/` | 仅上述两处（域类型 + 域求值器）；**没有任何编排层求值器** |
| 1.5 | 立题依据（GOAL-037 `O-4`） | GOAL-037 的「本轮新增残余」 | 「读到 ≠ 影响科学结论」；本轮把后半句落成可判定 |

### 2. 可复用的缝（本轮实现面的形状由它们决定）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | **声明路径**先例 | `packages/application/run_orchestration/evaluation_gate.py::declared_review_score` | 按合约**自己声明**的路径取数；fail-closed 三态（未声明 / 路径缺失 / 值不是数）⇒ **点名**不回落 |
| 2.2 | 验收门求值点 | 同上 `evaluation_gate.py` | `evaluate_contract(...)` → `contract_passes` → `verdict`；判词落库在**求值点**（GOAL-035 EC-01） |
| 2.3 | 既有读面 | `packages/application/ports/review_finding_store.py` | `ReviewFindingStore.for_run`；`GET /runs/{id}/reviews` 只读面 —— 判词**进既有读面**，不加第二套真相 |
| 2.4 | 跨轮结论的来源 | GOAL-037 EC-03 的 `research_state_read` | 前序 run 的 `verdicts`（逐字）+ `run_id` / `program_index` 可复核 |
| 2.5 | 规模纪律 | 450 行 / 函数 50 行 | `evaluation_gate.py` 与 `acceptance.py` 均须留意（新逻辑宜另立模块） |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 「影响」的判据形态 | **已定**：**结构化比对** —— 合约声明路径 → 取本轮产物里的值 → 与**前序 run 落库的结论逐字**比；**不得**文本子串巧合 |
| ② | 求值器的落点 | **已定**：**编排层**（`packages/application/run_orchestration/`，新模块），经验收门求值点调用；域层 `_evaluate_custom_evaluator` 的**既有返回值语义不动**（它明说该由编排层执行） |
| ③ | 声明的载体 | **已定**：复用**既有** `AcceptanceCriterion.metric` 字段（与 `REVIEW_SCORE` 同一条声明口径），**不新增** schema 字段 |
| ④ | 判词落点 | **已定**：进**既有** `ReviewFindingStore`（读面不变） |
| ⑤ | 承接面 | **不动**（不需要新能力；本轮只做判定链） |

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
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-038` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（治理校验器是
  `governance-check/scripts/validate.py`，**不是** `validate_cursor_framework.py`）；
  m0 按组、**独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；
  受影响的定向套件（`tests/domain` / `tests/application` / `tests/e2e` / `tests/contracts`）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run。
  **一个 cycle 攒成一次推送**（同批推送只有 HEAD 产生 run ⇒ 逐提交台账按 `covered_by` 登记）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **结构化比对，不做文本巧合**：「影响」的判据是「声明路径 → 取值 → 与来源逐字比」；
- **fail-closed**：缺声明 / 缺路径 / 值不符 / 前序结论缺席，**一律点名**（不回落默认值）；
- **判词进既有读面**（不加第二套真相）；
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-037 的 `O-1`（memory 项目维度）/ `O-2`（程序级
人工闸门）/ `O-3`（跨程序共享）/ `O-4`（**本轮立项依据**；收口时定格其收口面）/
`O-5`（决策未落的中间态）；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034 的 `W-1`…`W-4`；GOAL-033 的 `W-1`…`W-6`；GOAL-032 的 `W-1`…`W-8`；历史
`tools/` 目录仍有旧 lint 与无机器门的旧脚本；GOAL-019…037 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（收口时逐条定格；`P-1`…`P-3`）

- `P-1`（**只到「携带」不到「因果」**，未覆盖）：「影响」的判定 = 那条声明路径的值与前序落库
  结论**逐字一致**；**未**证「因为读了它才这么写」（因果不可判 —— 那是过程面事实）。
- `P-2`（**跨程序 / 跨项目的知识影响不在本轮**，未覆盖；承 `O-3`）：知识面按**程序**划界，
  入口是本 run 的程序归属。
- `P-3`（**人工闸门式的影响不在本轮**，未覆盖；承 `O-2`）：本轮的消费判定是**自动**的；
  「人看了结论再决定」那条线（D 组审批通道）不触动。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**；
**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **跨轮消费的可判定性**：**已收口** = 本轮产物声明并携带前序结论这条链**判得出来**；
  **未覆盖** = 因果（「因为读了才这么写」）。
- **求值器的射程**：**已收口** = 编排层执行 + 判词进既有读面 + 两向反证；
  **未覆盖** = 自定义求值器的**插件化注册**（本轮只做这一条声明式路径）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；**无自己的 run 也如实登记原因**（同批推送时只有 HEAD 产生 run）；
> 现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的「回顾性台账」提交自身
> 不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以「末条提交 + 覆盖说明」封闭，
> **不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `bf7e61f`（GOAL-037 台账尾巴，本轮首行） | M0 `37836787244` **cancelled**（后续推送触发 `cancel-in-progress`）+ CodeQL `37836786093` **success**（3 分析） | GOAL-037 的最后一个提交（仅 `.cursor/**` 记录改动；本地 `--profile framework` **8/8**）；**取消原因如实登记** ⇒ 其改动由后续批次覆盖（同时**封闭 GOAL-037 台账的自我指涉边界**） |
| `6c42c6f`（cycle 0 建档） | **无自己的 run**（同批推送） | 建档提交（仅 `.cursor/**`）；与 `4090015` 同一次 push ⇒ `covered_by 4090015` |
| `4090015`（cycle 1 = EC-01/02/03 收口） | 读数在台账尾回填 | 声明式消费 + 编排层求值 + 门接线；本地 `tests/application + tests/domain` **2412 passed, 1 skipped** |
| （本行所在提交：台账尾巴） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 台账尾巴 + **cycle 2 起点**：其结论由**下一个 cycle / GOAL 的台账**取证，**不得循环引用** |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `PLAN-20261008-349` | （见 CI 台账） | EC-05 七条 AC | EC-05 七条 AC：验证器进树（复用标准断言集**一行未重写**；起草中间态 **71 PASS / 2 FAIL** 逐条为本轮记录未写 ⇒ 收口态 **73 判词 / 0 FAIL**）+ `IN_SCOPE` 纯收紧（+2 行；判据 8 passed）+ 治理 + 宪章判据 + 承继残余与本轮 `P-1`…`P-3` 逐条定格；**AC-3** 次轮 `--base-ref a0f3a9e` **`TWO-TREE PASS`**（两路 73 判词 / `sha256` 相同 `d6c0e160…`；首轮 bootstrap 红如实登记）+ 归档定格 **2554 B / 73 行 / CR=0 / 0 FAIL** + **AC-4** as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5443 passed, 20 skipped**） | （见 CI 台账） | — | 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261008-350`） |
| 2 | `PLAN-20261008-347`（续） | （见 CI 台账） | EC-04 全 PASS：**合约声明消费路径**（`metric: meta_review.prior_verdict`）+ **编排层求值**在运行路径上真的执行 —— 两轮实跑：第 1 轮判据**不适用**（结构上无前序，判过+点名）、第 2 轮**消费成立**（判词点名来源 run id 与逐字值）；**两向反证**（带另一个值 ⇒ 判负且**两侧值点名**；声明路径缺失 ⇒ **点名配置错误**）；**接线**：`OrchestrationDependencies.prior_conclusion` → `fact_stores()` → `PhaseRunnerDeps`（同一桥，组合根与 run-ready 夹具同侧）；判据 4 例全绿；受影响套件 **5054 passed, 95 skipped** | （见 CI 台账） | **两次真红并修**：① 规模门（`resolve_consumption` 53 行 / `task_phase_helpers.py` 463 行）⇒ 拆函数 + 移函数；② **首版语义把「无前序」一律判负 ⇒ 每个程序第一轮必然失败**（判据不可用）⇒ 改为**两形态区分**（结构上无前序 = 不适用；有前序但读不到 = 判负）| EC-04 收口；**下一轮 EC-05**（自举收口） |
| 1 | `PLAN-20261008-347` | （见 CI 台账） | EC-01/02/03 全 PASS：**声明式消费**（合约 `metric` 路径 + fail-closed 三态 + 未知求值器点名）+ **编排层求值**（结构化比对；相等判过含来源 run id / 不等两侧点名 / 前序缺席点名；**整段文本含来源串不算**）+ **门接线**（`EvaluationInputs.consumption` 贴回判据下标；未注入 ⇒ 域层判词逐字保留）；判据 **12 例全绿**；受影响套件 **2412 passed, 1 skipped**；四道门绿（mypy 1163 files） | （见 CI 台账） | 两处构造面按实际字段名修正（`TaskContract` 无 `trust_level`、`ResearchTask` 无 `title`）—— 属测试夹具写法，非产品缺陷 | EC-01/02/03 收口；**下一轮 EC-04**（两轮实跑 + 两向反证） |
| 0 | —（建档） | （见 CI 台账） | 只读勘察（0 改动）；五条 EC 全 PENDING；MAINLINE 序 6 保留槽换成真实 id | （见 CI 台账） | — | 五条 EC 全 PENDING；求值器落点（②）与声明载体（③）待 cycle 1 定 | cycle 1（EC-01 勘察定稿 + EC-02 声明面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACHIEVED | **GOAL 收口（cycle 3 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、`IN_SCOPE` **纯收紧**、两树 **`TWO-TREE PASS`**（73 判词 / 两路 `sha256` 相同 `d6c0e160…`）、判词归档进树（两份各 2554 B / 73 行 / `CR=0` / 0 FAIL）、as-is m0 **23/23**（记录写完之后：`PASS [` 24 / `FAILED [` 0 / **5443 passed, 20 skipped**）、治理 + 宪章判据绿、CI 台账逐提交。**一处时序如实登记**：两树首轮 bootstrap 红（固有时序）。**收口后不再推进本 GOAL**；残余 `P-1`…`P-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。独立复检：`RECHECK-20261008-350`（PASS_WITH_WARNINGS）。 |
| 2026-10-08 | ACTIVE | **cycle 2（EC-04）收口**：跨轮消费在**运行路径上**被判定 —— 合约声明路径 + 编排层求值；两轮实跑（第 1 轮不适用 / 第 2 轮消费成立且点名来源）、两向反证（另一值 ⇒ 两侧点名；路径缺失 ⇒ 点名配置错）；接线经 `fact_stores()` 同一桥到两个组合根与 run-ready 夹具。**两次真红并修**（规模门拆/移函数；首版「无前序一律判负」会让第一轮必然失败 ⇒ 改为两形态区分）。EC-04 `PASS`；EC-05 待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 1（EC-01/02/03）收口**：`CUSTOM_EVALUATOR` 从「恒判负、由编排层执行」推进到**真的被求值** —— 合约用既有 `metric` 声明消费路径（fail-closed 三态）、编排层按**结构化比对**（声明路径取值 vs 前序落库结论逐字）判定并留痕、结论经注入位贴回**判据下标**且**未注入时域层判词逐字保留**（域层与 schema **零改动**）；判据 12 例全绿。EC-01/02/03 `PASS`；EC-04/05 待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 程序表序 6（保留槽）+ GOAL-037 收口面；只读勘察把「跨轮消费成为可判定」落成**一条已实测的缺口** —— `AcceptanceCriterionType.CUSTOM_EVALUATOR` 与 `AcceptanceCriterion.evaluator` **已声明**（域类型 + 合约字段），但 `_evaluate_custom_evaluator` **恒判负**且明说「must be executed by the orchestration layer」，而**全仓零命中**任何编排层求值器 ⇒ 本轮补这一环（立题依据 = GOAL-037 残余 `O-4`「读到 ≠ 影响科学结论」）。五条 EC 全 `PENDING`；**程序表序 6 保留槽换成真实 id**。**不做数量目标**；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
