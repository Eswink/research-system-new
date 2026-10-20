---
id: GOAL-20261020-091
slug: two-models-judge-the-same-artifact
title: 两个不同的评审模型对同一产物各判一次，判词可归因且分歧可读
status: ACHIEVED
created_at: 2026-10-20
updated_at: 2026-10-20
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-20 的 goal-mode 指令逐字：「优先做「复检」：七域里唯一前提全部就位、只差判据的。
    不需要新协议、不需要跨 run 机制。」以及「判据必须证明「不同」，不是「都跑了」」「真跑一次：
    真实中转站 + 真实 runtime，记录两个模型各自的判词全文。**若两个模型总是同判**，那是真实
    读数——如实登记「同质化」，**不要**为了绿而构造人为分歧」。授权要点：(a) 全部决策权下放，
    只有「改产品边界 / 放宽任何判据 / 动冻结面 / 新增或改 `TrustLabel` 取值」才停下登记。
    (b) 每一步必须有**机械判据**。(c) 每轮必须让科研能力阶梯前进。
    (d) push-to-main-for-CI（只推 `main`、不 force、不重写历史）。
    (e) 预算 `max_cycles` 至少 14。
objective: >
    把阶梯「复检」域的 `下一级`（「评审真的用不同模型判出负」）从**结构不可达**推成**可判定**：
    今天两个评审模型即便跑在同一 phase 上，也**判不出不同结果** —— 因为(a)评审者自己写下的
    判词进不了判定面（真实会话的交付物是**信封**，`REVIEW_SCORE` 只读顶层结构化输出 ⇒ 恒
    `review score unknown` ⇒ 恒判负），(b)被评对象进不了评审者的提示词（评审者只看到合约
    purpose ⇒ 两个模型评的不是同一件东西）。本轮补上这两处，并用**成对判据**证明三件事：
    判词可归因到**不同的执行目标**、构造出能引发分歧的产物时两位真的判出**不同 verdict**
    且 `dissent` 非空、以及两条反证（同目标 ⇒ 独立性失效判红；单评审 ⇒ 不聚合）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **评审者自己的判词真的进判定面**：`REVIEW_SCORE` 的取值面在**真实交付物形态**（信封：
      模型正文在 `content` 里）下也能解析 —— 复用既有 `declared_object` 的解信封口径
      （`declared_artifact` + `content` 两个判别键同时成立才解），**不新造第二套解析**。
      取不到 / 解析不出 / 不是数 ⇒ **既有 fail-closed 判词逐字不变**（`review score unknown`）。
      判据：`tests/application/run_orchestration/test_review_score_reads_the_envelope.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_review_score_reads_the_envelope.py -q` ⇒ 全绿；
      两向按压（禁用解信封 ⇒ 判词退回 `review score unknown`；改分数 ⇒ verdict 翻转）。
    status: PASS
  - id: EC-02
    criterion: >-
      **被评对象进评审者的提示词**：`review` phase 声明 `inputs: [author:research_plan]` 时，
      上游产物的**有界摘录**（逐条 ≤ 上限、超限**点名**截断）成为提示词的**第四段**
      （与方向 / 前序知识 / 检索摘录**并列**，不替换）；未声明跨相输入 ⇒ 提示词**逐字节**
      等于既有形态。摘录内容与读面上那份制品的字节**同源**（同一 `declared_object` 解包）。
      判据：`tests/application/run_orchestration/test_review_material_in_prompt.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_review_material_in_prompt.py -q` ⇒ 全绿；
      反证：未声明 ⇒ `compose_prompt(...) == purpose`（逐字）。
    status: PASS
  - id: EC-03
    criterion: >-
      **成对判据：不同模型 + 构造的分歧 + 两条反证**（全部走**产品运行链**，不手写落库记录）。
      ① 两位评审者在同一 phase 上各落一条判词，`reviewer_model` **互不相同**且可归因到
      `(endpoint, model_name)`；② 构造一份**能引发分歧**的产物（分数 0.95 vs 0.4，同一份
      被评对象）⇒ 两条 verdict 相异、`panels[0].dissent` **非空**且逐条点名；③ 反证：把
      `reviewer_b` 指回 `reviewer_a` 的模型 ⇒ 判据判红（独立性失效，`independent is False`）；
      ④ 反证：只声明一位评审 ⇒ `panels == []`（单评审不聚合）。
      判据：`tests/e2e/test_two_models_judge_the_same_artifact.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_two_models_judge_the_same_artifact.py -q` ⇒ 全绿；
      ③④ 两条反证在**真装配**上改事实（不是改断言）后判据必须相反。
    status: PASS
  - id: EC-04
    criterion: >-
      **真跑一次**：真实中转站（`examples/config/llm_endpoints.yaml` 的 `main`）+ 真实 runtime
      （`RESEARCHOS_AGENT_RUNTIME=openhands`），新协议 `dual_model_review_v1.yaml`（两 phase：
      author 写 `research_plan`、review 两位评审者各判一次）跑到终态；**逐字记录**两条判词的
      `reviewer_model` / `verdict` / 逐条判词全文（落 `scratch/`，正文进 RECHECK）。
      **若两个模型总是同判**：如实登记「同质化」并把阶梯 `下一级` 改写成「用第三方模型打破
      同质化」，**不得**为绿构造人为分歧。
    verify: >-
      `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 uv run --frozen --no-sync
      python -B -m pytest tests/e2e/test_two_models_judge_the_same_artifact_live.py -q -rs`
      ⇒ 终态行与两条判词正文进 RECHECK；门关着 ⇒ 如实 skip（skip 不是 PASS）。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口**：记录写完（GOAL / PLAN / RECHECK / 阶梯「复检」行升级 / 程序表序 59 /
      进展记录）→ 记录面判据 → **最后**跑 `tools/run_m0_with_witness.py` → 之后**不再改树**
      → 提交推送 → CI 到终态（逐提交台账）+ 凭据审计四面 `offenders=0` + 残余与未覆盖范围
      逐条。阶梯「复检」行的 `当前级` 与 `下一级` **同轮升级**。
    verify: >-
      见证 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`；
      `tools/two_tree_recheck.py` 两树同结论；治理校验器通过。
    status: PASS
  - id: EC-06
    criterion: >-
      **顺序纪律多一档机器事实**：`tools/run_m0_with_witness.py` 新增 `--verify-only`
      （只重算当前树指纹并与**已有**见证比对，**不跑门、不写见证**，退出码表达三态：
      覆盖成立 / 指纹不等 / 见证缺失）。判据钉住「它不写见证」这一条（写完比对 ⇒ 文件字节不变）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_m0_witness_matches_the_tree.py -q` ⇒ 全绿（新增用例含 verify-only 三态）。
    status: PASS
budget:
  max_cycles: 14
  per_cycle_minutes: 90
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - >-
      **为了让两个模型「判出分歧」而人为构造假分歧**：分歧必须来自**同一份被评对象上的
      真实判分**；若真跑同判，如实登记同质化（用户明写这是有效读数）
    - >-
      **改 `TrustLabel` 取值或语义** / 改 `count_retrieved_sources` 口径
    - >-
      **放宽 `REVIEW_SCORE` 的 fail-closed**：解析不出 ⇒ 仍必须 `review score unknown`；
      不得回落到默认分或把「读不到」读成「判过」
    - 让提示词第四段**替换**（而不是并列）既有三段
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **需要新增 `TrustLabel` 取值或改其语义** —— 停下登记
  - >-
    **只靠改判据就能让「两个模型同判」看起来像分歧** —— 停下登记（那是假绿）
child_plans:
  - .cursor/plans/tasks/PLAN-20261020-091-goal-091-two-models-judge-the-same-artifact.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md
memory_entries:
  - MEM-20261020-225
---

## 目标与退出标准

**一句话**：让「两个不同的模型对**同一件上游产物**各判一次、判词不同且可归因」成为**产品路径上
可判定的机械事实**，而不是靠读配置说「它们绑的模型不同」。

**建档实测（三处缺口，逐条带读数）**：

1. **评审者自己的判词进不了判定面**。真实会话的交付物是**信封**
   （`adapters/openhands/runtime_adapter.py::_deliverable`：`{declared_artifact: {content, …}}`），
   而 `evaluation_gate.declared_review_score` 直接从**顶层**结构化输出按点分路径取值 ⇒
   信封形态下恒 `None` ⇒ 判词恒 `review score unknown` ⇒ 恒判负。**实测**（本轮 2026-10-20，
   `uv run` 探针）：同一份分数 `0.5` 直形态取到 `0.5`、信封形态取到 `None`。
   ⇒ **两个模型无论各自判什么，判定面看到的都是同一个「不知道」**，「判出不同结果」结构不可达。
2. **被评对象进不了评审者的提示词**。`session_builder` 的唯一出站消息是
   `compose_prompt(task_contract.purpose, direction, prior_knowledge, retrieval)` —— 上游产物
   只以**证据**身份落库（`cross_phase_evidence`），不计入提示词 ⇒ 两位评审者看到的都只是
   合约 purpose，**评的不是同一件东西**（它们各自的「被评对象」是想象出来的）。
3. **多评审聚合面已就绪但缺真分歧**。GOAL-085/086/087 已把三件事补齐（判词带
   `reviewer_model`、同 phase 聚成一个小组、一位判负不取消同批），但既有判据全部用
   **受控执行体**给出不同交付物 —— 那是「分歧可表达」，**不是**「两个模型在真实路径上
   判出分歧」。

**本 GOAL 的射程边界（先写清楚，避免越判）**：

- **只新增**：`REVIEW_SCORE` 的**信封解析**（复用既有 `declared_object`）、提示词的**第四段**、
  一个新协议 `dual_model_review_v1.yaml` 与两份契约、`--verify-only` 模式；
- **不改**：`TrustLabel`、`count_retrieved_sources`、既有三段提示词的拼法、既有合约的既有判据、
  `aggregate_panel` 的任何语义、任何 HTTP 面；
- **不静默回落**：解不出信封 ⇒ 仍 `review score unknown`；未声明跨相输入 ⇒ 提示词逐字节不变；
- **如实登记**：真跑若两位同判，那是**同质化读数**（用户明写这不是失败），阶梯 `下一级`
  改写为「用第三方模型打破同质化」，**不**为绿构造人为分歧。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **先钉缺口存在，再钉修补有效**：每条 EC 的第一条判据都必须先在**未修**的形态上判红
  （EC-01 的 `envelope -> None` 探针已在上表取证）。
- **判据走产品运行链**：EC-03 一律用 `deps.runs.start_run`，不手写 `ScopedReviewFinding`
  替产品搭场景（GOAL-086 的教训）。
- **两条反证在真装配上改事实**（不是改断言）：同模型 / 单评审。
- **顺序纪律当受判对象走**：记录写完 → 记录面判据 → **最后**跑 m0 写见证 → 不再改树。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**，如实登记 + `covered_by`。

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS + 独立 RECHECK + 本文件收口（`latest_recheck` 为
  **仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条 + **阶梯记账成立**（宪章
  `依据 GOAL` 与 `进展记录` 各收录本 GOAL）+ 正式见证的 `terminal_line` 全绿。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261020-091 | 见「CI 台账」 | 建档探针钉住三处缺口；EC-01 判据 4 passed；EC-02 判据 12 passed；EC-03 判据 4 passed；受影响套件 298 + 47 + 282 passed | 见「CI 台账」 | 3（三处自己造成的缺陷，见下） | EC-04 真跑 / EC-05 收口 | 真跑取证 |
| 2 | （同上，真跑 cycle） | 同上 | **真跑**：`glm-5.3` REJECT 0.45 / `kimi-k2.6` PASS 0.82，`dissent` 非空；三轮探针剥出「提示词段被静默丢弃」的既有缺陷并修掉；live 判据 1 passed | 同上 | 3（合约措辞 / 既有缝合线 / 中转站瞬时失败重跑） | 记录 + 收口 | 写 RECHECK / 阶梯 |
| 3 | （同上，收口 cycle） | 同上 | RECHECK + 阶梯「复检」行升级 + 进展记录；记录面判据 → 全量 m0（含见证） | 同上 | 0 | 无（EC 全达成） | **收口** |

**本轮修掉的三处自己造成的缺陷**（都由读数剥出，不是事后发现）：

1. **合约措辞与实际拼法不符**：合约写「artifact is included **before** this task text」，
   而 `compose_prompt` 是把各段**追加在 purpose 之后** ⇒ 模型按指令往前找、找不到，如实
   报告「段不存在」。修法 = 改成「**below** this task text」。
2. **既有缝合线缺陷：已渲染的字符串被当成视图对象再渲染** ⇒ 检索段 / 前序段 / 被评对象段
   **全部被静默丢弃**（真实 run 实测：`send_message` 收到的字符串里 `UNDER REVIEW` 段
   整个不见）。修法 = `_section_of`：`str` 原样用、视图才渲染。**这一条同时修掉了
   GOAL-081 / GOAL-082 在真实会话上从未生效的问题**（它们的判据测的是渲染器与
   `compose_prompt` 的纯函数行为 —— 又一次「判据绑错了对象」）。
3. **中转站对 `glm-5.3` 的一次瞬时失败**（`retry budget exhausted`）⇒ 该位判词为
   `UNKNOWN`（读面如实点名，不冒充 REJECT）。**不是判据缺陷**，重跑取证。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-20 | **ACTIVE** | **建档**：承用户 goal-mode 指令「优先做复检」。建档实测出三处缺口，其中前两处是**结构不可达**的根因（判词进不了判定面 / 被评对象进不了提示词），第三处（聚合面）已由 GOAL-085/086/087 补齐。`max_cycles: 14`。 |
| 2026-10-20 | **ACHIEVED** | EC-01…EC-06 全达成。**真跑取得有效分歧读数**（`main/glm-5.3` REJECT 0.45 / `main/kimi-k2.6` PASS 0.82，`dissent` 非空、`independent is true`），因此**未触发**「同质化」停止条件。过程中修掉一处**既有缺陷**（提示词段在真实会话里被静默丢弃）。如实登记 `W-1`…`W-5` 五条未覆盖范围。 |
