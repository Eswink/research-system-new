---
id: GOAL-20261016-081
slug: retrieved-content-enters-the-prompt
title: 检索内容进提示词（立题因检索而不同）
status: ACTIVE
created_at: 2026-10-16
updated_at: 2026-10-17
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」有**三行**指向同一件事：
    **检索**域的 `下一级是什么` =「**检索内容驱动立题**（现内容进了上下文，但尚无判据证明
    立题/实验设计**因它而不同**）」；**计划**域 =「**计划由检索产出派生**（现设计由计划内容
    派生且已被实验消费，但「立题本身因检索而不同」仍无判据）」；**实验**域 =「**实验设计本身
    由检索/立题派生**」。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动
    迭代都必须让科研能力越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 上述**三域的共同下一格**；它**必须让阶梯前进**
    （由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让**已进上下文的检索内容真的进到模型的提示词里**：会话的首条消息除合约 purpose 之外，
    还必须携带 `context_snapshot` 里那些**有界摘录**（只收 `RETRIEVED`、有字符与条数上限），
    且「模型**拿到了**什么」在既有读面上**可复核**（同一份摘录 + 同一份上限）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **摘录进了提示词**：会话的**首条消息**（`send_message` 那条）在合约 purpose 之外
      **携带检索摘录** —— 逐条标识（PMID / DOI 形态）在消息正文里在场，且带**来源标注**
      （它是系统取回的，不是模型自述）。判据成对：**有摘录 ⇒ 在提示词里**+
      **上游无检索 ⇒ 提示词里没有该段**（不伪造、不留空壳）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/openhands/test_retrieval_context_in_prompt.py -q`
      ⇒ 全绿；判据覆盖：有摘录 ⇒ 正文含每条标识 / 上限截断标注 / 无摘录 ⇒ 不加该段 /
      摘录来自 `ContextSnapshot`（同源，不是第二套查询）。
    status: PASS
  - id: EC-02
    criterion: >-
      **有界**（§10）：进提示词的摘录受**逐条字符上限 + 条数上限**约束，且**截断可见**
      （被截的条目**标注**它被截了，而不是静默变短）；上限值与既有 `retrieval_context`
      的常量**同源**（不改那一份）。
    verify: >-
      判据断言：超长标题被截且**带标注** / 条数超上限时只取前 N 条且**点名**了被省略的条数 /
      上限常量与 `retrieval_context.DEFAULT_MAX_*` **是同一个值**（不新造第二份上限）。
    status: PASS
  - id: EC-03
    criterion: >-
      **可复核**：提示词里那段摘录 == **本 run 上下文制品**里同一批记录（逐条标识与截断后
      文本**逐字**相同）——即「模型拿到了什么」能对着既有读面（`{task_id}:retrieval_context`）
      核对，不靠回忆、不靠日志。
    verify: >-
      e2e：`tests/e2e/test_retrieval_content_reaches_the_prompt.py` ⇒ 会话首条消息里的摘录
      与读面制品**逐条逐字**相同；**反证**：改读面制品 ⇒ 判据红（证明判的是同一份事实）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**：真实模型会话的提示词里携带**真检索标识**（PMID / DOI 形态），
      且该 run 的计划/设计**引用了**其中的标识（立题因检索而不同的**最小可判证据**）。
      **若模型侧不可用或模型不引用** ⇒ 按降级梯如实登记（PENDING + 点名阻塞点），**不得**伪造。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且提示词里的标识读数在树。
      **cycle 4 实跑**：run `36bebc9b-cc28-443c-867d-a1966b13e836` ⇒ `SUCCEEDED`；
      **写计划的会话**（`research_report_plan`）的提示词带三个真标识
      （`42853652` / `10.12688/f1000research.180013.2` / `10.31234/osf.io/w7xpq_v2`），
      且**计划正文引用了全部三条**。归档：`evidence/GOAL-20261016-081-ec04-live-citations.txt`。
    status: PASS
    blocker: >-
      **（已闭合，保留为证据）** cycle 3 实测到的三处阻塞点：
      (a) 运行链证据在上下文装配时没有 claim 关系（由 cycle 3 的求值点修复 + 本轮的协议结构承担）；
      (b) 覆盖门只数本任务（**不改**：按 GOAL 取舍表判定解法 B 会削弱反编造门 ⇒ 明确不做）；
      (c) `inputs` 不能引用上游 phase 的产物（**cycle 4 闭合**：新增跨相引用形态，编译期解析并
      点名非法引用，性质由产出方决定，反编造门并列接受两种来源）。
      **取证**：`evidence/GOAL-20261016-081-ec04-evidence.txt`（cycle 3）；
      `evidence/GOAL-20261016-081-ec04-live-citations.txt`（cycle 4，达成）。
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**）+ 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 +
      原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 检索**），使阶梯的「检索」域 `依据 GOAL` 收录本 GOAL。
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
      把**无界正文**塞进提示词（§10 的有界口径）：摘录必须是**有界**的（逐条字符上限 +
      条数上限），且**截断可见**（标注），不得静默变短或整段原样注入
    - >-
      新造第二套检索查询或第二份上限：摘录**必须**取自既有 `ContextSnapshot`
      （GOAL-078 的唯一生产者），上限必须复用既有常量
    - 为让「进了提示词」成立而**放宽**既有判据（GOAL-078 的判据一字不动）
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
    把检索**正文**无损注入会话与 §10 的有界口径冲突 ⇒ **需人工拍板**（本 GOAL 只做
    **有界摘录**；若「看到全文」成为必需，记 BLOCKED 留拍板）

child_plans:
  - .cursor/plans/tasks/PLAN-20261016-497-goal-081-ec01-retrieval-excerpts-reach-the-prompt.md
  - .cursor/plans/tasks/PLAN-20261016-499-goal-081-ec03-the-prompt-excerpts-are-verbatim-the-read-face.md
  - .cursor/plans/tasks/PLAN-20261016-501-goal-081-ec04-the-model-cites-the-retrieved-identifiers.md
  - .cursor/plans/tasks/PLAN-20261016-503-goal-081-ec04-cross-phase-inputs-close-the-coverage-gap.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-504-goal-081-ec04-cross-phase-inputs.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让**已经进上下文**的检索内容**真的进到模型的提示词里** —— 阶梯「检索」/「计划」/
「实验」三域的**共同下一格**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进：立题站在真材料上才谈得上「下一轮问新问题」）与
  **质量**（产出的可判定性：模型看到什么、基于什么立题，可复核）**同时**受益；
- **能力域** = **检索**（阶梯逐字：`检索内容驱动立题`）；**同时**推进**计划**与**实验**
  （两行的 `下一级` 逐字都指向「因检索而不同」）。

**为什么这一条更近科研**（对照阶梯，**建档实测**）：

- **实测 ①**（本轮 live 取证）：真实 run 上模型**自陈**「This session did **not** receive the
  retrieved literature records referenced in the task … I have no source list, abstracts, or
  retrieved records in my context, so I cannot honestly cite a specific retrieved source by
  name … doing so would require inventing a citation, which I won't do」
  （run `748a56a6…` 的计划正文，逐字在 `evidence/GOAL-20261015-080-ec04-design-evidence.txt` 同源的
  `scratch/goal080-ec04-*.json` 里）⇒ **模型看不见检索结果**是**实测事实**，不是推断；
- **实测 ②**：会话的**唯一**一条出站消息是 `send_message(spec.task_contract.purpose)`
  （`adapters/openhands/session_builder.py:83`）⇒ 提示词里**只有**合约文本；
- **实测 ③**：`context_snapshot` 确实**在** spec 上（`session_builder.py:171` 把它带进
  fork 后的 spec；`task_executor.py:370` 从 `spec_context` 取）⇒ **内容进了上下文**
  （GOAL-078 成立），但**没有消费者把它写成提示词**（全仓 `adapters/` 对
  `context_snapshot` 只有**搬运**、没有**渲染**）。

⇒ 缺口**不是**「检索有没有发生」（GOAL-027/029 已通），也不是「内容有没有进上下文」
（GOAL-078 已通），而是「**上下文有没有进模型的眼睛**」——这正是三域共同的 `下一级`。

**本 GOAL 不加新依赖、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **§10 纪律**：摘录**有界**（逐条字符上限 + 条数上限）且**截断可见**；**不得**把无界正文
  塞进提示词。
- **同源纪律**：摘录**只**取自既有 `ContextSnapshot`（GOAL-078 的唯一生产者），上限**只**
  复用既有常量 —— 不新造第二套查询、不新造第二份上限。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用**或模型不引用标识** ⇒
  记 PENDING + 点名阻塞点；**不伪造**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证
（逐 job annotation / 同时终止时刻 / 状态页 incident），与 `cancel-in-progress`
（`run conclusion=cancelled`）形态区分。

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
- `W-2` —— **「立题质量因检索而不同」只判到「引用了标识」这一格**：模型可能引用标识却
  写出与文献无关的结论；**内容一致性**（说法与摘要是否相符）**无人判**（承 GOAL-080 `W-2`）。
- `W-3` —— **摘录形态受既有上下文限制**：进提示词的是 `ContextSnapshot` 里那些**有界摘录**
  （逐条字符上限），所以「看到全文」仍**不在**射程（§10 与 ADR 口径）。
- `W-4` —— 设计质量 / 臂数 > 2 / 择优不在射程（承 GOAL-080 `W-4`）。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**（M18 deferred）、**部署面验证**、
  **D 组审批通道** —— 均**不做**；
- **无损注入检索正文**（与 §10 冲突）—— **需人工拍板**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；真实 run 由 live 判据在**显式开关下**跑；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 下一 cycle 的取舍表（EC-04 的两条候选解法，含各自代价）

EC-04 的阻塞点已定位到两条（见 EC-04 的 `blocker`）。**两条候选解法互斥，各有明确代价**：

| 解法 | 做法 | 代价（实测/结构） | 会不会碰已钉住的性质 |
| --- | --- | --- | --- |
| **A. 上游产物作下游声明输入** | 让 `phase.inputs` 能引用**上游 phase 的产物**（今天只认组合根种入的制品） | 要改 `declared_input_sources` 的校验口径（今天要求 `created_by=composition-root` + 仓库文件可重算）⇒ 得为「run 内产物」开一条**新**的、可判的来源类别 | **否**（不动 GOAL-078 的按时刻装配语义） |
| **B. 覆盖门按 run 作用域计数** | `EVIDENCE_COVERAGE.minimum_retrieved_sources` 改为数**本 run**的 retrieved 来源 | 那正是**反编造门**：它今天只数本任务**自己看到**的来源；改成 run 作用域 ⇒ 一个任务可以「继承」别的 phase 取回的东西来满足自己的覆盖 | **是**（削弱既有的 anti-fabrication 判据） |

**驱动的判断（如实记录，供下一轮复核）**：**A 才对**——B 放宽的正是「来源必须是自己看到的」
这条既有判据（`count_retrieved_sources` 的注释逐字：「判据面**不接受**调用方的自称」）；
而 A 只是**新增一类合法来源**（run 内产物 + 可重算 digest + 明确 created_by），
**不削弱**任何既有断言。A 的落地还需要：① 新来源类别的判据；② `grounded_report_chain_v1`
的 `plan` 相声明 `inputs: [scouting_report]`；③ 覆盖门对「声明输入」的计数口径确认。

**落地下文（cycle 4 已完成，见 PLAN-503 / RECHECK-504）**：A 按以下形态实现 ——

- 形态 = `{phase_id}:{artifact_name}`（不是裸产物名）：**产出方必须写出来**，否则一个拼错的
  产物名会被当成「本地输入」静默放行；
- **编译期**解析（不是运行期才发现）：六类非法引用各自点名，run 不会带着必死的声明过 preflight；
- ③ 的答案 = **不改覆盖门**：覆盖门仍然只数「本任务登记的证据」，跨相输入作为**一类来源**
  进登记面（与组合根供给并列），性质由产出方决定 ⇒ 门本身一个字都不用改，语义也没被放宽；
- **不做** B（run 作用域计数）：那条会让一个任务「继承」别的 phase 取回的东西来满足自己的覆盖。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- **无损注入检索正文**（与 §10 冲突）—— 需人工拍板；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（摘录进提示词） |
| 1 | PLAN-20261016-497 | 见「CI 台账」 | 渲染器判据 **14 passed**；e2e **7 passed**（下游有那段 + 逐条标识在场；上游没有那段）；受影响套件 **1184 passed, 1 skipped**；规模门 **1267 passed** | 见「CI 台账」 | 2 次（见「cycle 1 的修复记录」） | EC-01/EC-02 **PASS**；EC-03/04/05 PENDING | cycle 2 = EC-03（同源：提示词那段 == 读面制品，逐条逐字） |
| 2 | PLAN-20261016-499 | 见「CI 台账」 | EC-03 判据 **2 passed**（逐条逐字 + 反证两形态）；读面截断判据 **6 passed**；按压 V11-1 **红** + 逐字节复原；既有收口验证器 **68 + 78 全绿**；受影响套件 **1419 passed, 16 skipped** | 见「CI 台账」 | 2 次（见「cycle 2 的修复记录」） | EC-03 **PASS**；EC-04/05 PENDING | cycle 3 = EC-04（真实 run：模型引用检索到的标识） |
| 4 | PLAN-20261016-503 | 见「CI 台账」 | 跨相输入单元判据 **11 passed**（含两条按压）；e2e **2 passed**（两维判词 + 按压臂点名性质维）；离线复现 run **`SUCCEEDED`**；**live 实跑 `SUCCEEDED`，计划正文引用全部 3 条标识**；受影响套件 **1399 passed, 1 skipped**；规模门 **1267 passed** | 见「CI 台账」 | 3 次（见「cycle 4 的修复记录」） | **EC-04 → PASS**；EC-05 PENDING | cycle 5 = EC-05（自举收口） |

### cycle 1 的修复记录（逐条如实）

1. **帮助函数的形参名与调用点不一致**（实测红）：`TypeError: _identifiers_of() got an
   unexpected keyword argument 'read'` —— 定义用 `reads`、调用写 `read=`。判据自己报出来，
   改正调用点。
2. **`_ChainReads` 上没有上下文载荷**（实测红）：我的第一版从 `reads.context_payloads` 取数，
   而那个属性属于**另一个**读写面对象 ⇒ 改成从 `reads.artifacts` 里按后缀挑上下文制品、
   再经 `/artifacts/{id}/content` 取值（**同一读面**，不新造第二条查询）。
3. **本机那份帮助函数是重复实现**（实测发现）：支持件 `retrieval_context_support` 里**已有**
   `context_payloads` —— 我新写的 `_identifiers_of` 是第二份。⇒ 改成复用既有函数
   （`context_identifiers` 进支持件、用例文件 import 它），并把**记录器类**也搬进支持件
   （用例文件曾涨到 **473 行**，超 450 硬上限）。

### cycle 2 的修复记录（逐条如实）

1. **读面不记 `truncated`**（**真缺口**，本 cycle 的主要价值）：提示词那段给被截条目加
   `[truncated]` 标注，而 `context_payload` **不记**这一列 ⇒ 读者拿读面**重建不出**
   「模型看到的那一行」（未截条目无碍、被截条目必然对不上）；旧判据只在**无截断**的
   夹具里跑 ⇒ **假绿**。⇒ 载荷补列 + 用**真被截**条目（`max_chars=8`）走全链的新判据。
2. **digest 重算判据如实判红**（既有判据，形态正确）：它按**字段列表**独立拼 payload
   重算 sha256 ⇒ 加列后读数不一致（`0c0eaded…` vs `edbc6a70…`）。**处置 = 把新列补进
   那份独立重建**（不是放宽它）—— 这正是「判据独立于实现」的证明。
3. **拆文件撞了已收口 GOAL 的受判面**（实测）：首版把 078 的整个类搬进新文件 ⇒
   `cases-test_retrieval_context_reaches_the_session 6 < 7`（078 收口断言钉了**例数下界**）
   与 `press-v8-4-arm-is-asserted`（钉了**类名**）两处红。**处置 = 078 的面原地复原**
   （类 + 两个用例 + 同源用例全搬回），新文件只留 081 新增的两条。
   **教训**：拆文件前**先数谁拿它的例数与类名当受判面** —— 受判面不只钉**内容**，
   也钉**位置与计数**。

| 3 | PLAN-20261016-501（EC-04） | 见「CI 台账」 | live 判据 **2 passed**（离线 skip 形态正确 + 断言成对）；**两次真实 run**：① 修复「求值点在运行链之前」（`with_retrieval_context` 移到 `_execute_one_task` 的运行链之后）—— 提示词那一段**确实**带三个真标识；② 但拿到它的是 `multi_role_review`（下游），写计划的 `plan` 相位**看不见自己这一格取回的**内容 ⇒ 计划正文零引用 | 见「CI 台账」 | 2 次（见「cycle 3 的修复记录」） | EC-04 **PENDING（点名阻塞点：协议结构）**；EC-05 PENDING | 下一 cycle = 加「检索相」在写计划之前（结构改动）|

### cycle 3 的修复记录（逐条如实 —— **本 cycle 的价值在诊断**）

1. **求值点在运行链之前**（**真缺陷，已修**）：`with_retrieval_context` 原先在
   `_run_group_task` 里、即**任务开始前**求值，而 `execute_run_chain_capabilities` 在
   `_execute_one_task` 里、即**任务内部**执行 ⇒ 同一 phase 自己刚取回的检索**它自己看不见**。
   ⇒ 把求值点移到运行链**之后**（`tctx = replace(tctx, spec_context=…)`），并补注释说明
   实测缺口；`phase_runner.py` 因此涨到 451 行 ⇒ 收敛注释回到 449（≤450 硬上限）。
2. **判据里的一处错写法**（实测）：`set().union(*prompt_sections)` 把**字符串**按**字符**并集
   ⇒ 「哪些标识在提示词里」恒判空集。⇒ 改成**逐字拼接**再判包含。
3. **`_run_once` 58 行 > 50**（规模门）：抽出 `_plan_content` 与 `_prompt_sections`。
4. **合约 purpose 补一句**（前提而非缺陷）：原文只说「ground the plan in the material you were
   given」，**从未要求**引用标识 ⇒ 补「cite at least one of them by its identifier」
   （与提示词那段标题「cite these by identifier」同口径）。

**仍未解决（EC-04 的阻塞点）**：即使求值点修好，`plan` 相位的会话**也**看不见本格取回的内容 ——
**检索在它自己的 phase 内执行**。解法需要一个**独立检索相**（写计划之前），属产品结构改动。

### cycle 4 的修复记录（逐条如实）

1. **形态判据与既有 `input-brief:` 前缀冲突**（实测红，`CROSS_PHASE_INPUT_INVALID` × 4）：
   首版按「含恰好一个 `:`」判跨相引用 ⇒ 组合根种入的 `input-brief:real_research_v1` 被当成
   「phase `input-brief` 的产物」。**处置**：判定改成依赖协议本身的两条规则 ——（i）左段是某个
   phase id ⇒ 跨相；（ii）否则右段是某个 phase 声明的产物名 ⇒ 也是跨相（**拼错产出方**必须
   点名，不能静默当成本地输入）。`input-brief:` 两段都不命中 ⇒ 本地输入，既有四条判据零改动。
2. **`phase_runner.py` / `task_phase_helpers.py` 撞 450 行硬上限**（规模门）：跨相通道让两个
   文件都越界。**处置**：拆出三个模块（`session_carry.py` / `experiment_registration.py` /
   运行期 `cross_phase_inputs.py`），并把 `_failure_or_deferred` 搬进 `task_phase_helpers`；
   两个原文件回到 447 / 425 行，**零语义变化**（既有 20 条 e2e 与 1399 条 application 判据全绿）。
3. **按压臂里重建 `ProtocolPhase` 时漏了 `stop_conditions`**（我自己的判据缺陷，实测红）：
   手写字段构造把这一项丢了 ⇒ 任务无限重试、判词被 `retry budget exhausted` 覆盖。
   **处置**：改用 `dataclasses.replace(phase, inputs=...)`（**只改一处，其余逐字继承**）。
   这条也顺带证明按压臂的构造必须**最小改动**，否则量到的是自己的 bug。
4. **按压臂一度走了实时 preflight**（`_live_preflight`）⇒ 去探真实中转站、撞 `invalid API key`。
   **处置**：run-ready 夹具**总是**给出 `preflight_override`（目录已指向本机 mock 端点），
   按压臂据实断言它存在，不再回落到实时探活。


（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档（序 49） | `98131839` | [M0 38821998809](https://github.com/Eswink/research-system-new/actions/runs/38821998809) / [Push 38821999212](https://github.com/Eswink/research-system-new/actions/runs/38821999212) | ⚠️ **M0 `conclusion=cancelled`**（`quality-windows-latest` 一 job；其余七 job `success`；CodeQL 三条 `success`）= `cancel-in-progress`（紧随的 cycle 1 推送 `18d02d9b`）。**`covered_by = 18d02d9b`**。**不**记绿 |
| cycle 1 落地（渲染器 + 接线 + 两向读数） | `18d02d9b` | 见下行覆盖 | 批量推送；其内容包含在 `8bfadce4` 的树里 |
| cycle 1 记录面（PLAN/RECHECK/GOAL/ALL_PLAN） | `8bfadce4`（**tip**） | [M0 38823969492](https://github.com/Eswink/research-system-new/actions/runs/38823969492) / [Push 38823968888](https://github.com/Eswink/research-system-new/actions/runs/38823968888) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**（**本 cycle 的末条实测提交**） |
| cycle 1 台账（只改记录） | `adfb4aa8` | [M0 38825652170](https://github.com/Eswink/research-system-new/actions/runs/38825652170) / [Push 38825651597](https://github.com/Eswink/research-system-new/actions/runs/38825651597) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 2 派生（PLAN-499 + ALL_PLAN） | `f243933f` / `6c6bc1f7` | 见下行覆盖 | 批量推送；其内容包含在 `55c35175` 的树里 |
| cycle 2 落地（逐条逐字 + 反证 + 读面补列） | `9e937a82` | [M0 38829688947](https://github.com/Eswink/research-system-new/actions/runs/38829688947) / [Push 38829688970](https://github.com/Eswink/research-system-new/actions/runs/38829688970) | ⚠️ **M0 `cancelled`**（两 job；其余 job `success`、CodeQL 三条 `success`）= `cancel-in-progress`（紧随的重构推送）。**`covered_by = 55c35175`**。**不**记绿 |
| cycle 2 重构（078 受判面复原） | `276cdf0e` | [M0 38830616150](https://github.com/Eswink/research-system-new/actions/runs/38830616150) / [Push 38830616264](https://github.com/Eswink/research-system-new/actions/runs/38830616264) | ⚠️ **M0 `cancelled`**（多 job）= `cancel-in-progress`（紧随的记录推送）。**`covered_by = 55c35175`**。**不**记绿 |
| cycle 2 记录面（PLAN/RECHECK/GOAL/ALL_PLAN） | `22a58a49` | [M0 38830722643](https://github.com/Eswink/research-system-new/actions/runs/38830722643) / [Push 38830722616](https://github.com/Eswink/research-system-new/actions/runs/38830722616) | 🔴 **`quality-windows-latest` = `failure`（真红）**：新 e2e 漏 `requires_docker` 标记 ⇒ 无 Docker 环境下 run 走不到实验格 ⇒ 上下文为空 ⇒ 两条用例以「恰有一条非空上下文」失败（其余七 job `success`、CodeQL 三条 `success`）。**分类 = 产品缺陷（判据前置条件漏声明）**。**处置见下行** |
| cycle 2 修复（补 `requires_docker` 标记） | `55c35175` | [M0 38832831325](https://github.com/Eswink/research-system-new/actions/runs/38832831325) / [Push 38832831229](https://github.com/Eswink/research-system-new/actions/runs/38832831229) | **M0 八 job 全 `success`**（含此前判红的 `quality-windows-latest`）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 3 派生（PLAN-501 + ALL_PLAN） | `1cc4e428` / `79070840` | 见下行覆盖 | 批量推送；其内容包含在 `667a01d5` 的树里 |
| cycle 3 诊断落地（带侦察相的新协议 + live 判据 + 阻塞点两处） | `e87f1f38` | [M0 39039090555](https://github.com/Eswink/research-system-new/actions/runs/39039090555) / [Push 39039090704](https://github.com/Eswink/research-system-new/actions/runs/39039090704) | 🔴 **`quality-ubuntu` / `quality-windows` 两 job `failure`（真红）**：新 live 模块未在 `LIVE_MODULES` / `LITERAL_MENTIONS` 登记（**同族缺陷第二次**，GOAL-080 也踩过）；其余六 job `success`、CodeQL 三条 `success`。**处置见下行** |
| cycle 3 修复（两处登记 + 口令用法行） | `667a01d5` | [M0 39040691876](https://github.com/Eswink/research-system-new/actions/runs/39040691876) / [Push 39040691660](https://github.com/Eswink/research-system-new/actions/runs/39040691660) | **M0 八 job 全 `success`**（含此前判红的两 job）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 3 记录面（PLAN/RECHECK/GOAL/ALL_PLAN）+ **当前 tip** | `182c31f5`（**tip**） | [M0 39042251468](https://github.com/Eswink/research-system-new/actions/runs/39042251468) / [Push 39042251185](https://github.com/Eswink/research-system-new/actions/runs/39042251185) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 4 落地（跨相输入 + 判据 + 协议接线） | `be84fba5` | 见下行覆盖 | 批量推送；其内容包含在 `f512fc5b` 的树里 |
| cycle 4 记录面（PLAN/RECHECK/GOAL/MAINLINE/ALL_PLAN）+ **当前 tip** | `f512fc5b`（**tip**） | [M0 39058028923](https://github.com/Eswink/research-system-new/actions/runs/39058028923) / [Push 39058028776](https://github.com/Eswink/research-system-new/actions/runs/39058028776) | ⚠️ `attempt 1` 的 `console-frontend` = `failure`（**既有时序型判据**：`live-schedules-write.spec.ts` 期望 `1 次` 读到 `2 次` —— 守卫线程在 5s 窗口内多跑了一轮；本轮**未触碰**任何 web/调度面，`git diff --name-only` 可证）⇒ `rerun-failed-jobs` 后 **`attempt 2` 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`。按纪律**不改阈值**；如实登记首轮红。 |
| cycle 3 阻塞点第三处（只改记录：`inputs` 不能引用上游 phase 产物） | `aecd3515` | [M0 39043807771](https://github.com/Eswink/research-system-new/actions/runs/39043807771) / [Push 39043807448](https://github.com/Eswink/research-system-new/actions/runs/39043807448) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**（2026-10-17 轮询到终态补记） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-17 | **ACTIVE** | **cycle 4 落地**（EC-04，PLAN-503）：**跨相输入闭合第三条阻塞点**。`inputs` 新增
`{phase_id}:{artifact_name}` 形态 —— 编译期解析（六类非法引用**点名**，不留到运行期）、
**性质由产出方决定**（`capability_execution: run_chain` + provider 声明 `network_domains`
⇒ `RETRIEVED`，读取方不得自报）、**反编造门并列接受**「组合根供给」与「有性质的 phase 产出」
（原内容校验一字未改）。`grounded_report_chain_v1` 的 `plan` 相接入
`scouting:scouting_report` ⇒ 覆盖的性质维成立。**离线与 live 两路都到 `SUCCEEDED`**：
真实 run `36bebc9b-…` 上 `research_report_plan` 的提示词带三个真标识，且**计划正文引用了
全部三条**。按压两条：摘掉产出方的 run-chain 声明 ⇒ 性质变 `GENERATED`；摘掉跨相证据 ⇒
覆盖性质维判拒。**EC-04 → PASS**；EC-05 PENDING。 |
| 2026-10-16 | **ACTIVE** | **cycle 2 落地**（EC-03，PLAN-499）：**「模型拿到了什么」逐条逐字可核对** ——
提示词那段与读面制品的 `entries` **行级相同**（含顺序与截断标注），两形态反证（改一条 /
多一条）**都判红**。**抓出并修掉一条真缺口**：读面原本**不记** `truncated` ⇒ 提示词里
`[truncated]` 那行**重建不出来**，而旧判据只在无截断夹具里跑（假绿）。**EC-03 → PASS**
（RECHECK-500 = PASS）；EC-04/05 PENDING。 |
| 2026-10-16 | **ACTIVE** | **cycle 1 落地**（EC-01/EC-02，PLAN-497）：**检索摘录进提示词** ——
新增纯函数渲染器（**有界**：只排既有摘录、不新造第二份上限；**截断可见**：逐条标注；
**同源**：渲染文本就是 `entry.shown`）+ `AgentSessionSpec.retrieval_prompt`（缺省 `None` ⇒
提示词**逐字**不变、fork 继承）+ 会话创建点把那段拼在合约文本**之后**。e2e 两条**相反读数**：
下游有那段且逐条标识在场 / 上游没有那段。**EC-01/EC-02 → PASS**（RECHECK-498 = PASS）；
EC-03/04/05 PENDING。 |
| 2026-10-16 | **ACTIVE** | **建档**：承 GOAL-20261015-080 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「检索」/「计划」/「实验」**三域的共同下一格**。**建档实测**（三条）：① 真实 run 上模型**自陈**没收到检索记录、并拒绝编造引用（`748a56a6…` 的计划正文）；② 会话的**唯一**出站消息是 `send_message(contract.purpose)`（`session_builder.py:83`）；③ `context_snapshot` 在 spec 上且被带进 fork（`session_builder.py:171`）但**没有渲染进提示词的消费者**。这三条就是本 GOAL 的靶子与可行性依据。 |
