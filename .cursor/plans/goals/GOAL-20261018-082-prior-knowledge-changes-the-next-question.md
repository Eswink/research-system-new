---
id: GOAL-20261018-082
slug: prior-knowledge-changes-the-next-question
title: 前序知识改变下一轮立题（跨 run 记忆/计划进立题）
status: ACTIVE
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」有三行的 `下一级是什么`
    指向同一件事：**检索**域 =「检索改变**下一轮**问题」；**计划**域 =「计划改变**下一轮**问题」；
    **迭代**域 =「跨越新问题的迭代（现一个 program 一个问题，无自我立题）」。
    承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动迭代都必须让科研能力
    越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 上述三域的**共同**下一格（与序 49 的形态同源：那一轮也是三域共指）；
    它**必须让阶梯前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让**前序 run 落库的知识真的改变下一轮立题**：一次 run 的**立题会话**在开工前必须看到
    前序 run 留下的受治记忆（`MemoryTier.PROJECT` 及以上），且「看到了什么」在既有读面上
    **可复核**；**判据成对** —— 有前序知识 ⇒ 立题正文里出现它的**逐字标识**；
    无前序知识 ⇒ 立题正文里**没有**那一段（不伪造、不留空壳）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **前序知识进了立题会话的提示词**：`plan` 相（或等价立题相位）的**会话首条消息**
      除合约 purpose 外，还要携带**受治记忆**的有界摘录（只收 `PROJECT` / `ORGANIZATION`
      两档；逐条字符上限 + 条数上限；**来源标注**说明它是系统取回的既有知识）。
      判据成对：**有前序记忆 ⇒ 在提示词里** + **没有 ⇒ 没有那一段**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_prior_knowledge_in_prompt.py -q`
      ⇒ 全绿；判据覆盖：有记忆 ⇒ 正文含每条标识 / 上限截断标注 / 无记忆 ⇒ 不加该段 /
      摘录来自 **canonical 的 `MemoryStore`**（不是第二套查询）。
    status: PASS
  - id: EC-02
    criterion: >-
      **有界**（§10）：进提示词的记忆摘录受**逐条字符上限 + 条数上限**约束，且**截断可见**；
      上限值与既有 `retrieval_context.DEFAULT_MAX_*` **同源**（不新造第二份上限）。
    verify: >-
      判据断言：超长正文被截且**带标注** / 条数超上限时只取前 N 条且**点名**被省略的条数 /
      上限常量与 `retrieval_context.DEFAULT_MAX_*` **是同一个值**。
    status: PASS
  - id: EC-03
    criterion: >-
      **可复核**：提示词里那段记忆摘录 == 既有读面（`GET /projects/{id}/memory`）上同一批记录
      （逐条 id 与截断后文本**逐字**相同）—— 即「模型拿到了什么」能对着读面核对。
    verify: >-
      e2e：`tests/e2e/test_prior_knowledge_reaches_the_prompt.py` ⇒ 会话首条消息里的摘录与
      项目记忆读面**逐条逐字**相同；**反证**：改一条记忆正文 ⇒ 判据红。
    status: PASS
  - id: EC-04
    criterion: >-
      **前序知识来自前一个 run**（不是同 run 内的传递）：第二轮的立题会话看到的记忆，
      其 `provenance` 必须指向**前一轮 run 的落库结论**；且第二轮立题正文里**引用了**
      那条记忆的逐字标识（立题因前序知识而不同的**最小可判证据**）。
      **若模型侧不可用或模型不引用** ⇒ 按降级梯如实登记（PENDING + 点名阻塞点），**不得**伪造。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且两条读数的归档在树：
      提示词带前序记忆标识 / 计划正文引用它；**按压**：清空前序记忆 ⇒ 第二轮提示词里没有那一段。
    status: PENDING
    blocker: >-
      **实测阻塞点（2026-10-18 cycle 1，三次真实 run）**：**产品路径已成立** —— 立题会话的
      提示词里**两段都在场**（前序知识 302 字符 + 检索 595 字符），`contracts_with_prompts`
      三个会话逐条为真；e2e 判据 `3 passed`（含**空库按压**：无记忆 ⇒ 无该段）。但**模型侧
      不引用**：三次真实 run 的计划正文里 `memory_id` **零命中**，尽管合约 purpose 已**明写**
      「cite at least one of those entries by its memory id」（第二次 run 后补的措辞）。
      模型**确实采纳了内容**（第二次 run 的 `duplicate_pairs: 30` 正是那条 lesson 的参数），
      但**不做标识层面的引用**；它只引用「本次检索」那一段的标识（DOI / PMID）。
      **取证**：`evidence/GOAL-20261018-082-ec04-evidence.txt`（三次 run 的逐条读数）。
      **分类**：**模型侧行为**（不是产品缺陷：提示词与读面逐字对得上）。
      **按降级梯记 PENDING + 点名阻塞点**，**不**伪造。
      **可能的下一步（需拍板，不在本 cycle 射程）**：把「前序知识」的呈现形态改成与检索段
      **同一形状**（例如给每条记忆一个 PMID/DOI 式的稳定短标识并放进同一段），或允许
      「内容采纳」作为可判证据（例如判「计划里的参数值来自前序记忆」而非「引用了 id」）。

  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**、**静止工作树**）+ 治理绿 + CI 台账**逐提交**
      （`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 迭代**），使阶梯的「迭代」域 `依据 GOAL` 收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING

budget:
  max_cycles: 14
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - 改 `default_effect: DENY` / 放宽 §9 / 新增任何 allow
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**（记录 / GOAL / PLAN /
      `examples/**` / 测试 / 文档）—— **只在 gitignored 的 `.env` 落位**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - >-
      把**无界正文**塞进提示词（§10）：记忆摘录必须**有界**（逐条字符上限 + 条数上限），
      且**截断可见**（标注），不得静默变短或整段原样注入
    - >-
      新造第二套记忆查询或第二份上限：摘录**必须**取自 canonical 的 `MemoryStore`
      （`query(tier=...)`），上限必须复用既有常量
    - >-
      绕过 `MemoryWriteProposal → gate → commit` 的写入链直接落记忆（AGENTS.md §8）；
      本轮**只加读取面**，写入链一字不动
    - 为让「进了提示词」成立而**放宽**既有判据（GOAL-078/081 的判据一字不动）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **新站不可用**（连通 / 协议面 / 工具调用任一不通）且无替代路径 —— 记 BLOCKED，
    逐条写明阻塞点（**不得**为此放宽任何判据或伪造成功）
  - >-
    把记忆**全文**无损注入会话与 §10 的有界口径冲突 ⇒ **需人工拍板**
    （本 GOAL 只做**有界摘录**）

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-507-goal-082-ec01-prior-knowledge-reaches-the-plan-prompt.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-508-goal-082-ec01-prior-knowledge.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让**前序 run 落库的知识真的改变下一轮的立题** —— 阶梯「检索」/「计划」/「迭代」
三域的**共同下一格**（与序 49 同形）。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进：下一轮**从上一轮的结论出发**，而不是每次重新开始）
  与 **质量**（产出的可判定性：模型看到什么、基于什么立题，可复核）**同时**受益；
- **能力域** = **迭代**（阶梯逐字：`跨越新问题的迭代`）；**同时**推进**检索**与**计划**
  （两行的 `下一级` 逐字都是「改变下一轮问题」）。

## 为什么这一条更近科研（**建档实测**，逐条带命令与读数）

1. **`memory.read` 已放行、有实现、有测试，但没有任何协议或合约声明它** ——
   逐条扫描 `examples/protocols/*.yaml`（**23 份**）与 `examples/contracts/task_contracts.yaml`：
   `required_capabilities` 里出现 `memory.read` 的 **0 份**。
   ⇒ 一次 run 里**从不消费既有记忆**（能力面在那里，但没人接线）。
2. **记忆只在 `RUN` 层写入**：`memory_promotion.MemoryPromotionContext.tier` 缺省
   `MemoryTier.RUN`，而 `memory.read` 按 `tier` 筛 ⇒ 运行链写入的记忆**下一轮读不到**
   （`PROJECT` / `ORGANIZATION` 才是跨 run 的档位）。
3. **提示词装配面零记忆**：`session_resolution.py` / `session_carry.py` / `retrieval_context.py`
   三处对 `memory` 的提及为 **0 / 0 / 1（仅类型）** ⇒ 即便记忆在库，也没有消费者把它写成提示词
   （与序 49 建档时 `context_snapshot` 的形态**同源**）。
4. **既有「跨 run 消费」不证明立题改变**：`cross_run_knowledge_v1.yaml` 自陈边界逐字
   「本协议不声称：读到的结论改变了后续 run 的**科学结论**」⇒ 已判到的是「读到了」，
   **不是**「立题因它而不同」。

⇒ 缺口**不是**「记忆有没有写」（M10 已通）、也不是「能不能读」（`memory.read` 已通），
而是「**写下来的知识有没有回到下一轮的立题里**」—— 这正是三域共同的 `下一级`。

**本 GOAL 不加新依赖、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **§10 纪律**：记忆摘录**有界**（逐条字符上限 + 条数上限）且**截断可见**。
- **同源纪律**：摘录**只**取自 canonical 的 `MemoryStore.query`；上限**只**复用既有常量。
- **写入链纪律**：`MemoryWriteProposal → gate → commit` **一字不动**（本轮只加读取面）。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用**或模型不引用** ⇒
  记 PENDING + 点名阻塞点；**不伪造**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证
（逐 job annotation / 同时终止时刻 / 状态页 incident），与 `cancel-in-progress`
（`run conclusion=cancelled`）形态区分。**时序型 flake**（如 `live-schedules-write` 的计数窗口）
按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立**（本 GOAL 被某个域的 `依据 GOAL` 收录）。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 残余与未覆盖范围（逐条明写）

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办（它的判词由本 GOAL 的收口验证器产出）。
- `W-2` —— **「立题质量因前序知识而不同」只判到「引用了标识」这一格**：模型可能引用标识
  却写出与前序结论无关的立题；**内容一致性**（立题是否真的**推进**了前序结论）**无人判**
  （承 GOAL-080 `W-2` / GOAL-081 `W-2`）。
- `W-3` —— **摘录形态受既有上下文限制**：进提示词的是**有界摘录**，「看到全文」仍**不在**射程。
- `W-4` —— **只做一层跨 run**（前一轮 → 这一轮）；多轮的**累积衰减**（哪条记忆该退休）
  不在射程。写入链的 `RUN → PROJECT` 提升策略也不在本轮（本轮只保证 `PROJECT` 档可读）。
- `W-5` —— **记忆的时效门与冲突面**（`review_after` / `expires_at` / `CONFLICTED`）在
  **读取侧**如何呈现，本轮只做「带标注」；不改变既有 gate 语义。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**（M18 deferred）、**部署面验证**、
  **D 组审批通道** —— 均**不做**；
- **无损注入记忆全文**（与 §10 冲突）—— **需人工拍板**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；真实 run 由 live 判据在**显式开关下**跑；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- **无损注入记忆全文**（与 §10 冲突）—— 需人工拍板；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261018-507 | 见「CI 台账」 | EC-01/02/03 判据 **9 + 3 + 3 passed**（含读面同源与两条反证）；**三次真实 run**：提示词两段都在场（302 + 595 字符），`memory_id` **零命中** ⇒ **EC-04 未达成**；受影响套件 **1408 passed, 1 skipped**；受撞 e2e **24 passed** | 见「CI 台账」 | 2 次（见「cycle 1 的修复记录」） | EC-01/02/03 **PASS**；**EC-04 未达成（点名阻塞点：模型不按 id 引用）**；EC-05 待办 | 下一 cycle = EC-04 的第二条路（判「内容采纳」而不是「id 引用」，或改呈现形态）|
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（记忆摘录进立题会话） |

### cycle 1 的修复记录（逐条如实）

1. **判据第一版考了模型没被要求做的事**（**本轮最重要的发现**）：首轮 live 失败后核查
   `research_report_plan` 的 purpose —— 它**只**要求引用「检索标识」（PMID / DOI），
   **从未**要求引用前序知识。⇒ 先补 purpose 措辞（**前提**，不是放宽判据：它让判据考的
   行为在指令里**存在**），再重跑两次；**仍不引用** ⇒ 才归为模型侧行为。
   **纪律**：live 判据失败时**先查指令里有没有这件事**。
2. **`FakeMemoryStore` 是 deny-by-default**（实测红）：直接 `commit` 报
   `memory store has no registered provenance sources`。⇒ 判据里显式 `allow_source(provenance)`
   —— **不改** store 的安全语义（那是既有面）。
3. **「上限同源」判据第一版用 `__defaults__`**（实测红）：keyword-only 参数不进 `__defaults__`
   ⇒ 改用 `inspect.signature(...).parameters[...].default`，并加 `is` 判（新造同值常量会让
   弱判据仍绿）。
4. **新 live 模块漏登记两处清单**（`LIVE_MODULES` / `LITERAL_MENTIONS`）：这是**同族缺陷第三次**
   （GOAL-080 / 081 各一次）。本轮的处置是**同轮补齐**并在 PLAN 里点名；纪律条目已进工程记忆。

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |

**自我指涉边界（明写并封闭）**：台账每补一行都会产生一个新提交、从而产生一次新的 CI ——
若要求「台账最后一行的 CI 也登记」，则永远有下一行。封闭规则：受判的是**代码面**与**收口面**
的 CI；只改 `.cursor/plans/**` 的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在
「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **cycle 1 落地**（PLAN-507）：**前序知识进立题会话**。新增装配器（只读 `MemoryStore.query`、只收 `PROJECT`/`ORGANIZATION`、`expires_at` 过 ⇒ 排除、`review_after` 过 ⇒ 标注、逐条截断**复用** `retrieval_context` 上限）+ 渲染器（与检索段**并列**、先前序后检索）+ 两个组合根接线。**EC-01/02/03 → PASS**（9 + 3 + 3 passed，含读面同源与两条反证）。**EC-04 未达成**：三次真实 run 上提示词两段都在场（302 + 595 字符），但模型**不按 `memory_id` 引用**（只采纳内容：`duplicate_pairs: 30` 来自那条 lesson）⇒ 按降级梯记未达成 + 点名阻塞点，**不**伪造。EC-05 待办。 |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-081 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「检索」/「计划」/「迭代」**三域的共同下一格**。**建档实测四条**（逐条带命令）：① 23 份协议 + 全部合约**零**声明 `memory.read`；② 记忆写入缺省 `MemoryTier.RUN`（跨 run 读不到）；③ 提示词装配面三处对 `memory` 的提及为 0/0/1；④ `cross_run_knowledge_v1` 自陈「不声称改变了后续 run 的科学结论」⇒ 已判到的是「读到了」而不是「立题因它而不同」。 |
