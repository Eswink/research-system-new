---
id: GOAL-20261008-035
slug: research-quality-decidable-and-review-linked
title: 研究质量三类可判定（来源支持 / 可复现 / 覆盖充分）+ 与评审联动 —— 把「判据存在」推进到「研究循环里真的被判定」
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 3 推进质量轴**，并授权本驱动自动化循环
    推进、**收口后立即开下一个 GOAL，不停下来等指令**。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含放宽某条 allow、改产品语义、新增 ADR），**不等于**可以放宽**判据、门禁、阈值或
    断言** —— 本轮无例外。
    (1) **本 GOAL 的授权开工**（MAINLINE 程序表序 3 的「一句话目标」逐条落地）：
    (i) **来源支持** —— 建档实测：`EVIDENCE_COVERAGE` 判据**两维**（计数 + 性质
    `TrustLabel.RETRIEVED`）都已实现，**且 16 个合约声明计数维、4 处声明性质维、
    多数已进研究协议**（`real_literature_chain_v1` 等）⇒ 靶子是**「判定 + 读面关系
    两条是否同时成立且可复核」**（承 `MEM: evidence-read-face-claim-relation`：
    只登记证据不挂 relation ⇒ 判据绿而读面空）；
    (ii) **可复现** —— `build_reproducibility_audit` / `verify_reproducibility_audit`
    只在 `packages/application/m12_reference/clean_run_stages.py`（遗留参考链）被调用，
    **研究循环的 run 路径零调用**；`experiments/metric_extraction.py` 有 semantic
    reproducibility digest 的口径但同样不在判决面；
    (iii) **覆盖充分** —— 与 (i) 同源（`minimum_sources` / `minimum_retrieved_sources`）；
    (iv) **与评审联动** —— 建档实测：`CriterionInputs.review_score` 在**产品路径从不赋值**
    （`rg -n "review_score="` 只命中 tests/），而 `REVIEW_SCORE` 判据**仅在 tests 里被喂值**
    ⇒ 任何协议声明 `REVIEW_SCORE` 都会 fail-closed「review score unknown」；
    **评审环节**（`ReviewPanel` / 异构评审）在域里有类型，但运行路径的**联动**需要实测。
    (2) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面** /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；**宣称项目安全**
    （`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；**静默改
    `terminal()` 语义而不留 ADR**；**用「加了计数或阈值」冒充质量可判定**
    （MAINLINE 明文：质量轴的反面就是「只加计数或阈值」）。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime 保持 **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (5) **边界（承继）**：GOAL-001…034 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…034 的未覆盖范围**原样保留**；
    GOAL-034 的残余 `W-1`…`W-4` / `R26-*` 终态**原样保留**，本轮**只追加**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 MAINLINE 程序表序 3（**质量**轴）推进到「**产出可判定且与评审联动**」：
    ① **来源支持可判定** —— 结论与证据之间有**可复核的关系**（不是「登记过就算」：
    承 `MEM: evidence-read-face-claim-relation` 的口径），且**研究循环里真的用到**
    （出厂协议/合约至少有一条声明 `EVIDENCE_COVERAGE` 并在实跑中被判定）（EC-01）→
    ② **可复现可判定** —— 「这一次 run 的产出能不能被独立复核」在**研究循环的 run 路径**
    上产出一份**可判定的结论**（复用既有 `reproducibility` 域类型与 digest 口径，
    **不建第二套**），且**反证**能判红（改坏一个输入 ⇒ 判词点名）（EC-02）→
    ③ **覆盖充分 + 评审联动** —— `EVIDENCE_COVERAGE` 的**两维**（计数 + 性质）在实跑中
    被判定；**评审结论进入判据面**（`review_score` 在**产品路径**被赋值，而不是只在
    tests 里；`REVIEW_SCORE` 判据在实跑中可判过/判负）（EC-03）→
    ④ **自举收口** —— 验证器进树 + 两树复检 + 判词归档进树 + as-is m0 23/23（在**全部
    记录写入之后**）+ 治理绿 + CI 台账逐提交（EC-04）。
    **硬约束**：先复核再依赖（本 GOAL 的起点事实全部待复核）；受判面**不得**是交集 /
    过滤 / 空集恒真；真被使用才算数（断言调用证据 + 下游消费证据，不得只断言「判据存在」）；
    点名失败而非静默；留档**二进制写盘**、判词归档**进树**；m0 条数**仍是 23**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **来源支持可判定（结论 ↔ 证据的关系可复核）**。
      (a) **勘察前置（实测）**：`EVIDENCE_COVERAGE` 的两维实现读数；**出厂协议 / 合约里
      哪些声明了它**（预期零命中）；`TrustLabel.RETRIEVED` 的**唯一盖章点**
      （provider 声明的 `network_domains`）与 `count_retrieved_sources` 的取证口径；
      结论（claim）与证据的关系如何进**读面**（`attach_relation` 的既有要求）。
      (b) **实现**：**研究循环里真的用到** —— 至少一条出厂协议/合约声明
      `EVIDENCE_COVERAGE`（两维都声明），且实跑时**被判过**（判词可读）。
      **不建第二套**：复用既有 `evaluate_criterion` / `count_retrieved_sources`；
      **不得**为了让它过而放宽 `minimum_sources` 到 0（那等于不判）。
      (c) **判据（新）**：实跑一条两维都声明的合约 ⇒ 覆盖判据**判过**且判词逐字读出
      「count ≥ min」与「retrieved ≥ min_retrieved」两条事实；读面能读到
      claim↔evidence 的关系（不是「登记过」）。
      (d) **反证两向**：① 把 `minimum_sources` 提到实际值之上 ⇒ 判负并点名计数；
      ② 把检索来源数打到 0（换一个不返回标识的检索）⇒ **性质维**判负并点名
      `retrieved` 那一维（**两维都会被单独触发**，不是只看总数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/domain
      tests/application -q` ⇒ 全绿；新增判据文件（两维判定 / 读面关系 / 两向反证）全绿；
      配套留档：勘察读数、判词逐字、两向反证判红原文。
    status: PASS
  - id: EC-02
    criterion: >-
      **可复现可判定（run 路径上产出可复核的结论）**。
      (a) **勘察前置**：`build_reproducibility_audit` / `verify_reproducibility_audit`
      的**调用点清单**（实测：只在 `m12_reference` 遗留链）；`ReproducibilityAudit` 域类型的
      字段与判定口径；semantic reproducibility digest 的既有算法与它的输入面。
      (b) **实现**：在研究循环的 **run 路径**（真实 run 跑到终态后）产出一份
      **可判定的可复现结论** —— 复用既有域类型与 digest 口径（**不建第二套**）；
      结论必须落在**读面**（可读、可复核），而不是只在内存里算一下。
      (c) **判据（新）**：实跑一条 run ⇒ 可复现结论**可读**且其**判定口径可复核**
      （digest 重算一致 / 审计字段逐条在场）。
      (d) **反证**：改坏一个输入（例如篡改审计里的某个 digest / 换掉一个关键引用）⇒
      判红并**点名**那一项。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/application
      tests/domain -q` ⇒ 全绿；新增判据文件全绿；配套留档：调用点清单、结论读数、
      反证判红原文。
    status: PASS
  - id: EC-03
    criterion: >-
      **覆盖充分 + 评审联动（评审结论进判据面）**。
      (a) **勘察前置（实测）**：`CriterionInputs.review_score` 的**赋值点清单**
      （预期：产品路径零赋值、仅 tests）；`REVIEW_SCORE` 在出厂协议/合约里的使用
      （预期零命中）；`ReviewPanel` / 异构评审的域类型与**运行路径**的关系（是否接线）。
      (b) **实现**：评审结论**进入判据面** —— `review_score` 在**产品路径**被赋值
      （来源必须**点名**：哪条既有事实 / 哪个契约声明的产出；**不得**凭空编一个分数），
      并让 `REVIEW_SCORE` 判据在实跑中**可判过 / 可判负**。
      (c) **判据（新）**：① 声明 `REVIEW_SCORE` 的合约在实跑中**判过**（判词含分数与
      阈值）；② 低于阈值 ⇒ **判负**并点名分数；③ 分数**缺来源**时维持既有 fail-closed
      （`review score unknown`）—— **不得**把它改成默认通过。
      (d) **反证**：把分数来源摘掉 ⇒ 判据回落到 fail-closed 并点名（不是静默通过）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/domain
      tests/application -q` ⇒ 全绿；新增判据文件全绿；配套留档：赋值点清单读数、
      三态判词逐字、反证判红原文。
    status: PASS
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
      替换 MAINLINE 序 3 的占位，进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 / 空字段 =
      未取证**；自我指涉边界**明写并封闭**）；⑥ 承继残余逐条在位（GOAL-034 的 `W-1`…`W-4` /
      `R26-*` 终态 / 未覆盖范围逐条保持 + 理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal035_closeout.py --root .
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
      **只断言「判据存在 / 注册了」而不取调用与下游消费证据**；
      **用「加了计数或阈值」冒充质量可判定**（MAINLINE 质量轴的反面）；
      **为了让覆盖判据通过而把 `minimum_sources` 降到 0**（那等于不判）；
      **用 Tests 之外的本地夹具**（受判对象必须是产品路径）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/application/preflight/**`、`tests/contracts/**`、
      `tests/adapters/**`、`tests/e2e/**` 既有文件）—— **新增**判据与新增文件不受此限
    - >-
      **静默改判据的 fail-closed 语义**（`review score unknown` / `retrieved source count
      unknown` 这类点名拒答**不得**被改成默认通过或默认拒绝之外的第三种状态）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 评审联动需要新增审批通道 / 改 `ReviewPanel` 域语义
child_plans:
  - .cursor/plans/tasks/PLAN-20261008-323-goal-035-ec01-finding-store-and-two-dimensional-coverage.md
  - .cursor/plans/tasks/PLAN-20261008-325-goal-035-ec02-reproducibility-conclusion-on-the-run-path.md
  - .cursor/plans/tasks/PLAN-20261008-327-goal-035-ec03-review-score-linkage-on-the-run-path.md
  - .cursor/plans/tasks/PLAN-20261008-329-goal-035-ec04-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-330-goal-035-ec04-self-bootstrap-closeout.md
memory_entries:
  - a-judged-verdict-needs-a-recorded-read-face-not-a-recomputation
  - existing-judges-decide-where-a-new-read-face-may-land
  - an-unpersisted-conclusion-does-not-exist-for-the-read-face
  - no-score-is-not-a-low-score
  - verdict-archive-is-written-by-the-entry-it-archives
---

# GOAL-20261008-035 — 研究质量三类可判定 + 与评审联动

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 3**（轴 = **质量**）。
> 序 1（连续性）与序 2（深度）已 ACHIEVED。

## 目标与退出标准

四条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 来源支持可判定 | 两维覆盖判据在**研究循环里真的被判定** + 读面关系 + 两向反证 | PASS |
| EC-02 | 可复现可判定 | run 路径上产出**可复核的结论**（复用既有域类型）+ 反证点名 | PASS |
| EC-03 | 覆盖充分 + 评审联动 | `review_score` 在**产品路径**赋值 + `REVIEW_SCORE` 三态可判 + 反证 | PASS |
| EC-04 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**宣称项目安全**
（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）；不得用「加计数或阈值」
冒充质量可判定（MAINLINE 质量轴的反面列）；不得把覆盖判据的 `minimum_sources` 降到 0。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**。主树零改动（只读勘察）。

### 1. 来源支持 / 覆盖充分：**两维都已产出、已进研究协议，但计数维 > 1 的那条不成立**（**建档首版读错，本版为更正**）

> **更正记录（同轮修正，如实登记）**：建档首版我断言「出厂协议零使用 `EVIDENCE_COVERAGE`」
> —— 那是**看错了扫描面**（只扫了 `examples/protocols/` 而没有扫
> `examples/contracts/task_contracts.yaml`）。实测：**16 个合约声明 `minimum_sources`、
> 4 处声明 `minimum_retrieved_sources`**，且多数已在研究协议里被引用。本版按实测重写。

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 两维判据已实现 | `packages/domain/acceptance.py::_evaluate_evidence_coverage` | 计数维（`minimum_sources`）+ **性质维**（`minimum_retrieved_sources`，要求 `TrustLabel.RETRIEVED`）；缺维度 fail-closed 并**点名缺哪一维** |
| 1.2 | **两维在合约里都被声明** | `rg -c "minimum_sources:" examples/contracts/task_contracts.yaml` = **16**；`rg -c "minimum_retrieved_sources:"` = **4** | 性质维出现在 `real_retrieval_deliverable`、`multi_role_scouting` 等 |
| 1.3 | **且已进研究协议** | 逐协议反查 | `real_retrieval_deliverable` ← `real_literature_chain_v1` / `real_experiment_research_v1` / `real_retrieval_research_v1`；`multi_role_scouting` ← `multi_role_research_v1` |
| 1.4 | 评审契约的**如实边界**写得很好 | `multi_role_review` 的注释 | 它**不**声明性质维，并**说明理由**（评审不检索 ⇒ 要求它就是让评审者为没做的事背书）；检索那一维由侦察 phase 承担 |
| 1.5 | 检索来源数有取证口径 | `count_retrieved_sources` | 由 canonical 的 `SourceRecord` 判；与读面同源 |
| 1.6 | 读面要求关系 | `MEM: evidence-read-face-claim-relation` | 只 `register_evidence` 不 `attach_relation` ⇒ **读面看不到**（判据绿、读面空） |

**更正后的结论**：EC-01 的靶子**不是**「协议不用它」（那条被实测推翻），而是
**「两维的判定与读面关系是否在同一次实跑里同时成立且可复核」** —— 即
**判据判定 + 读面关系**两条同时在场（承 1.6：判据绿而读面空是已知的假绿形态）。

### 1.7 cycle 1 实测：**通过路径原本没有读面**，且两处既有判据决定了新读面不得落在哪里

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 1.7 | 逐条判词的既有读面 | `rg -n "gate_rejection_reason" packages/ services/` | **只在被拒路径**（拼进失败消息）；通过路径**零读面** |
| 1.8 | `ReviewFinding` / `Decision` 的持久化 | `rg -n "ReviewFinding" --glob '*.py'`（排除定义/构造/本轮新模块） | **从不落库**；`handoff.decision_refs` 指向一个**不存在**的对象（既有空引用，本轮**未**收口，原样登记） |
| 1.9 | 事件面不得放判词 | `tests/e2e/test_vertical_slice_happy_path.py::test_artifact_content_is_not_in_domain_json` | 该断言要求**任何**事件 payload 里零出现 `analysis_report`；而 `ARTIFACT_EXISTS` 判词逐字点名合约声明的制品名 ⇒ 判词进事件面即撞（**不放宽**） |
| 1.10 | 制品面不得放结论 | `tests/e2e/test_idempotency.py` | 断言 `list_refs()` 条数**精确值** ⇒ 每任务新增一份「结论制品」即撞（**不放宽**） |
| 1.11 | 新读面必须登记隐私清单 | `tests/observability/read_face_route_registry.py` + 派生一致性判据 | 未分类读面 ⇒ 两条判据点名判红（实测：`未分类的读面路由:/runs/{run_id}/reviews`） |
| 1.12 | 实跑两维读数 | cycle 1 判据取样 | count=**3**（1 声明输入 + 2 检索来源）、retrieved=**2** ⇒ 判词 `3 >= 1 sources; 2 >= 1 retrieved` |
| 1.13 | 判词渲染此前有**一处**（失败消息） | `gate_rejection_reason` | cycle 1 把它收成**唯一渲染点** `criterion_line`，落库面与失败消息共用（不各说一套） |

**由此得出的设计约束**（cycle 1 已落地）：结论**在求值点落库**、经**独立只读路由**
（`GET /runs/{run_id}/reviews`）读取；事件面与制品面都不动；读面必须登记并写明
**一等边界**（`SCHEMA_VALID` 判负时判词含校验器错误文本、可能引用输出片段 ⇒
「按模板不含正文」**而非**「结构性保证零正文」）。

### 2. 可复现：**审计只在遗留参考链里**（本轮 EC-02 的靶子）

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 审计实现存在 | `packages/application/experiments/repro_audit.py` | `build_reproducibility_audit` / `verify_reproducibility_audit`；域类型 `ReproducibilityAudit` |
| 2.2 | **调用点只有遗留链** | `rg -n "build_reproducibility_audit" --type py` | 产品侧**唯一**调用点是 `packages/application/m12_reference/clean_run_stages.py`（M12 参考链），其余是 `__init__` 导出与自身定义 |
| 2.3 | semantic reproducibility digest 口径存在 | `packages/application/experiments/metric_extraction.py` | 有「哪些指标不进 semantic digest」的声明（允许重跑 variance） |
| 2.4 | 研究循环零调用 | 同上 | `packages/application/run_orchestration/` 内**零命中** `reproduc` |

### 3. 覆盖充分 + 评审联动：**分数在产品路径从不赋值**（本轮 EC-03 的靶子）

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 判据已实现 | `_evaluate_review_score` | 读 `operator` + `threshold` + `inputs.review_score`；缺分 ⇒ `review score unknown`（fail-closed） |
| 3.2 | **产品路径零赋值** | `rg -n "review_score=" --type py packages/ services/` | 只命中 `tests/`（`test_runtime_scorers.py` / `test_tasks_acceptance.py`）⇒ **任何协议声明 `REVIEW_SCORE` 都会 fail-closed** |
| 3.3 | 出厂协议零使用 | `rg -n "REVIEW_SCORE" examples/` | **零命中** |
| 3.4 | 评审域类型存在 | `ReviewPanelRole`（`packages/domain/enums.py`） | 域里有异构评审的**类型**；它与**运行路径**的关系待 cycle 1 实测 |

### 4. 起点表述的出入（逐条）

- 提示词称「质量三类可判定与评审联动」：**本 GOAL 把它落成三条可实测的缺口**（见上三节）。
- 提示词称承接面 19/46：**本 GOAL 不依赖该数**；未在本轮重新实测，如实登记为**待复核**。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 三类判定**复用既有判据实现**（不建第二套） | **已定**（EC-01/02/03 的 (b)） |
| ② | 覆盖判据的**出厂协议选择**（哪条协议/哪个合约声明两维） | **cycle 1 derive 时定** |
| ③ | `review_score` 的**来源**（哪条既有事实产出分数） | **cycle 1/3 勘察后定**；**不得**凭空编分数 |
| ④ | 可复现结论的**读面落点** | **cycle 2 勘察后定**（复用既有读面，不新造平行面） |
| ⑤ | 承接面扩容 | **不做**（MAINLINE：广度不是一条轴） |

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
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-035` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（承 GOAL-033 `W-1`）；
  m0 按组、**独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；
  受影响的定向套件（`tests/domain` / `tests/application` / `tests/e2e` / `tests/loaders`）；
  web 门按改动面（本 GOAL 预期零 web 源码改动）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run。
  **一个 cycle 攒成一次推送**（承 GOAL-033 `W-3` 与 GOAL-034 台账的**三次**取消在飞 run
  的实测教训：连续推送会 `cancel-in-progress`）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **先复核再依赖**：起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **「真的被判定」才算数**：判据存在 ≠ 研究循环用它（本轮靶子就是三条这样的缺口）；
  受判对象必须是**产品路径**上的实跑；
- **不得用计数/阈值冒充质量**（MAINLINE 质量轴的反面列）；
- **受判面不得是交集**（承 `MEM-160`）：新判据的受判面必须是**声明集**本身；
- **点名失败而非静默**：缺口 / 拒绝 / 回落一律点名；
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-034 的 `W-1`…`W-4`；GOAL-033 的 `W-1`…`W-6`；
GOAL-032 的 `W-1`…`W-8`；历史 `tools/` 目录仍有 73 条旧 lint 与无机器门的旧脚本；
GOAL-019…034 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（收口时逐条定格；`N-1`…`N-6`）

- `N-1`（**已收口**）三类判定的**出厂协议落点**：cycle 1 定为**既有研究协议 + 既有合约**
  （`real_literature_chain_v1` 等，两维覆盖）与本次**新增**的 `review_scored_deliverable`
  （评审分数）；判定全部落在实跑路径上（决策登记 ②③ 已由 cycle 1/3 落地）。
- `N-2`（**已收口，口径已收窄**）`ReviewPanel` 与运行路径的关系：实测 = 异构评审的
  **角色面**只在 preflight 的 `role_checks` 里有线；评审**分数**的来源由合约声明
  （EC-03）⇒ 运行路径上可判，但那是**单评审者交付物自述分数**。
- `N-3`（**未覆盖**）**多评审者分数聚合**：`ReviewPanelRole`/异构评审的分数**聚合**在 run
  路径上仍未接线；EC-03 只证「评审结论能进判据面且三态可判」。
- `N-4`（**未覆盖**）**承接面读数**：提示词的「19/46」未在本轮重新实测（本轮不以该数为
  判据，也不据此宣称能力面扩大）。
- `N-5`（**未覆盖**）**跨机器位级复现**：本仓只声称「可重复配置」（EC-02 的已收口/未覆盖
  分界逐条写在下面）。
- `N-6`（**未覆盖**）**结论内容正确性**：EC-01 只判「结论 ↔ 证据的关系 + 覆盖两维」，
  不判结论内容真假。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**；
**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 三条「已收口 vs 未覆盖」分界（逐条明写）

- **EC-01 来源支持**：**已收口** = 出厂协议里两维覆盖判据被实跑判定 + 读面关系；
  **未覆盖** = 「结论**内容**是否正确」（那是另一条谱系，本仓只判关系与覆盖）。
- **EC-02 可复现**：**已收口** = run 路径产出可判定结论 + 反证；**未覆盖** = 跨机器的
  位级复现（`R-M1` 同族的口径边界：本仓只声称「可重复配置」）。
- **EC-03 评审联动**：**已收口** = 分数在**产品路径**有来源 + 三态可判；**未覆盖** =
  多评审者聚合（`ReviewPanel` 的异构评审若未接线则如实登记）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；**无自己的 run 也如实登记原因**（同批推送时只有 HEAD 产生 run）；
> 现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的「回顾性台账」提交自身
> 不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以「末条提交 + 覆盖说明」封闭，
> **不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `40bb507` | **无自己的 run** | cycle 0 建档提交；与 `dbb3971` **同一次 push**（同批 ⇒ 只有 HEAD 产生 run，`git merge-base --is-ancestor` 已证）⇒ `covered_by dbb3971` |
| `dbb3971` | `37711331007` **M0 success**（8 job 全 success）+ `37711330653` **Push/CodeQL success**（3 分析全 success） | 建档事实层更正（同轮修正扫描面） |
| `c1cd752` | `37726029644` **M0 success**（8 job 全 success）+ `37726029238` **Push/CodeQL success**（3 分析全 success） | **cycle 1（EC-01）**：代码 + 记录同批；本地 as-is m0 **23/23** |
| `26cfa63` | `37739875935` **M0 success**（8 job 全 success）+ `37739876177`-族 **Push/CodeQL success**（3 分析全 success） | **cycle 2（EC-02）**：可复现结论在 run 路径产出并进读面；本地 as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / 5354 passed, 20 skipped）|
| `5219c4b` | `37727602180` **M0 success** + Push/CodeQL **success** | cycle 1 台账尾巴（仅 `.cursor/**` 记录改动；本地 `--profile framework` 8/8 补全终态）⇒ **上一行的自我指涉边界已由此行封闭**（实测取证，非循环引用）|
| （本行所在提交） | **无自己的 run**（自我指涉边界的下一条） | 台账尾巴：本表末行的提交自身在进入 CI 时其结论尚未产生 ⇒ 以「**末条已取证提交**（`c1cd752`）+ **仅台账改动**（`.cursor/**`，按 `MEM: local-gate-protocol-and-flake-classes` 第 6 条只需 `--profile framework` 补全）」封闭，**不得循环引用** |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（建档） | （本文件所在提交） | 只读勘察（0 改动）；四条 EC 全 PENDING | PENDING | — | 四条 EC 全 PENDING；出厂协议落点待定 | cycle 1（EC-01 勘察 + 出厂协议落点） |
| 1 | `PLAN-20261008-323` | （见 CI 台账 cycle 1 行） | EC-01 六条 AC 全 PASS：`tests/e2e/test_two_dimensional_coverage_and_claim_relation.py` **5 passed**；`tests/contracts/test_review_finding_store_contracts.py` 3 passed；PG 8 passed；`python` profile **6 项确定性检查全绿**（mypy 1139 文件 0 错）；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5350 passed, 20 skipped**；收集数 +19 逐文件分解：3+5+3 新判据 + 8 源文件参数化；skipped 未升）；按压 P-1 **4 failed** / P-2 **1 failed** 且复原 | （见 CI 台账） | 首跑两处红并修：判据文件 2 处 `no-any-return`（mypy）、新读面未登记隐私清单（observability ×2）；规模门：`composition.py` 457 行、`service.py` 451 行 ⇒ 搬迁 + 归组（418 / 450） | EC-01 收口；**下一轮 EC-02**（可复现可判定：审计只在遗留 M12 链，run 路径零调用） |
| 2 | `PLAN-20261008-325` | （见 CI 台账 cycle 2 行） | EC-02 五条 AC 全 PASS：`tests/e2e/test_reproducibility_conclusion_on_the_run_path.py` **3 passed**；`tests/application/experiments` + 既有离线链 **96 passed**；`tests/e2e` **252 passed**；`tests/observability` **133 passed**；mypy 1140 文件 0 错；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5354 passed, 20 skipped**，收集数 +4 逐文件分解）；按压 P-1 **3 failed** / P-2 **1 failed** 且复原 | （见 CI 台账） | 首版**自写可审态门**与既有 `is_auditable_state` 分叉 ⇒ 同轮改为复用；断言从「空发现列表」改为「零 FAIL」（域口径里 WARNING 是诚实标注）；首版 import 顺序错 ⇒ `UnboundLocalError` 39 failed，判据当场抓到 | EC-02 收口；**下一轮 EC-03**（评审联动：`review_score` 产品路径赋值 + `REVIEW_SCORE` 三态） |
| 3 | `PLAN-20261008-327` | （见 CI 台账 cycle 3 行） | EC-03 四条 AC 全 PASS：`tests/e2e/test_review_score_linkage_on_the_run_path.py` **3 passed**；`tests/loaders+contracts+domain+application+api` **2372 passed**；`tests/e2e`+`tests/tooling` **1636 passed**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5358 passed, 20 skipped**，收集数 +4 逐文件分解：新判据 3 例 + 源文件参数化 +1；`skipped` 20 未升）；按压 P-1 **1 failed** 且复原 | （见 CI 台账） | 首版判据多写了一个无用的 runtime 包装类 ⇒ 已简化；设计上**新增**合约与协议而不是给 `sort_analysis_review` 加判据（后者会让既有夹具连环判负） | EC-03 收口；**下一轮 EC-04**（自举收口：验证器 + 两树 + 归档 + m0 + 治理 + 台账） |
| 4 | `PLAN-20261008-329` | （见 CI 台账 cycle 4 行） | EC-04 七条 AC：**AC-1** 验证器进树（复用标准断言集**一行未重写**；收口态 **70 判词 / 0 FAIL**，非判词行 0 / 绝对路径 0；中途态 65 PASS / 5 FAIL 逐条为「归档未生成 + 记录声明先行 + 残余标记待定格」）+ **AC-2** `IN_SCOPE` 纯收紧（+2 行；判据 8 passed；两脚本四道门绿：ruff/format/mypy/规模 238·191 行）+ **AC-5** 治理 `validate.py` 绿 + 宪章判据绿 + **AC-6** 残余 `N-1`…`N-6` 与未覆盖逐条在位；**AC-3（两树 + 归档形态）与 AC-4（as-is m0 终局行）读数在 `RECHECK-20261008-330` 逐条回填** | （见 CI 台账） | — | 四条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261008-330`） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **cycle 4（EC-04 自举收口）落地**：收口验证器 + 本轮断言集进树（复用标准断言集**一行未重写**），`IN_SCOPE` **纯收紧**（+2 行），两脚本过四道门；两树复检（`--script-mode shared`）与判词归档进树、as-is m0、治理 + 宪章判据、CI 台账逐提交 —— 读数逐条在 `RECHECK-20261008-330`（bootstrap 时序如实登记）。GOAL 收口。未覆盖范围与残余 `N-1`…`N-6` 逐条明写；**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 3（EC-03）**：**评审结论进入判据面**。`REVIEW_SCORE` 此前产品路径从不喂分（`review_score=` 只在 tests）、出厂合约零声明 ⇒ 本轮让**合约自己声明分数的结构化输出路径**（`metric: review_decision.score`，schema 既有字段，零 schema 改动），产品路径按该路径取数，判定仍走既有 `_evaluate_review_score`。三态判词逐字：判过 `review score 0.95 GTE 0.8` / 判负点名分数 `review score 0.5 GTE 0.8` / 缺来源 `review score unknown`（**不回落默认分**）；判词经 EC-01 的既有读面读。**新增**合约与协议（既有受判面一字不动）。EC-03 `PASS`；EC-04 待收口。未覆盖：异构评审的分数聚合仍未接线。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 2（EC-02）**：**可复现结论在 run 路径产出并进读面**。实验跑到科学终态时封存 `ReproducibilityAudit` 并**随实验落库**（复用既有 use case / 既有可审态谓词 `is_auditable_state` / 既有 id 派生，**未建第二套**）；读面 `GET /runs/{id}/experiments` 给出 `audit_digest` / `audit_status` / **重算的** `audit_verified` / 逐条 `audit_findings`（无审计则 honest unavailable）；主干判据**独立重算**与读面一致；反证两向（篡改载荷 ⇒ 重算判红；换掉引用 ⇒ 发现里点名制品 id）。EC-02 `PASS`；EC-03/EC-04 仍待收口。未覆盖范围原样保留；**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **cycle 1（EC-01）**：两维覆盖判据与读面 claim↔evidence 关系**在同一次实跑**成立且可复核。产品面新增：验收结论**落 canonical**（`ReviewFindingStore` + SQLite/PG 实现 + 迁移 `016` + 组合根写读同实例）+ **只读路由** `GET /runs/{run_id}/reviews`（503/404 **不假装**）。判据 5 例（主角 + 计数维反证 + 性质维两式反证 + 读面边界）；两向反证判词逐字留档。**设计改变过一次并如实登记**：首版把判词放进新事件 payload，实测撞既有内容隐私金丝雀 ⇒ **改设计而非改判据**（制品面同样被既有条数断言挡下）。EC-01 `PASS`；EC-02/03/04 仍 `PENDING`。未覆盖范围原样保留；**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 宪章 + `goals/README.md` 格式契约 + GOAL-034 全文；只读勘察把「质量三类可判定与评审联动」落成**三条可实测的缺口** —— ① `EVIDENCE_COVERAGE` 两维**实现完备但出厂协议零使用**（`rg examples/` 零命中）；② `build_reproducibility_audit` **只在遗留 M12 链被调用**，研究循环 run 路径零调用；③ `review_score` 在**产品路径从不赋值**（只在 tests 里喂值），而 `REVIEW_SCORE` 判据缺分即 fail-closed ⇒ 出厂协议声明它会一律判负。四条 EC 全 `PENDING`。**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
