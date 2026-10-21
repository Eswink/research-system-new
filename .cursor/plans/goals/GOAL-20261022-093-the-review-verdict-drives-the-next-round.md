---
id: GOAL-20261022-093
slug: the-review-verdict-drives-the-next-round
title: 上一轮评审的判词驱动下一轮的会话（第五个提示词槽位 + 跨 run 搬运）
status: ACTIVE
created_at: 2026-10-22
updated_at: 2026-10-22
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-22 的 goal-mode 指令逐字：「`max_goals` 从 **60 扩到 70**，程序表追加序 61。
    扩表**必须**配一次战役级核算」「为什么不是收兵：`tools/next_round_charter.py` 刚落地，
    `W-2` 明写它「只适用于按新纪律写的 GOAL」⇒ 它**还没在真实序列里自举过**。序 61 用合规
    输入跑通一次，才算「迭代」域的战役级那一面闭合。」「预算读数：扩表前 60/60 触顶、
    扩表后 70/61。」授权要点：(a) 全部决策权下放，只有「改产品边界 / 放宽任何判据 / 动冻结
    面 / 新增或改 TrustLabel 取值」才停下登记 BLOCKED；(b) **扩表本轮已授权**；(c) 每一步
    必须有**机械判据**；(d) 每轮必须让科研能力阶梯前进；(e) push-to-main-for-CI（只推
    `main`、不 force、不重写历史）；(f) `max_cycles` 给 **14**。
objective: >
  让**评审的判词真的驱动下一轮**：把上一轮落库的评审结论（面板建议性结论 + **逐条分歧**）
  作为**第五个并列槽位**送进下一轮会话的提示词。判据面此前只走到「两位判出不同结论且分歧
  可读」（GOAL-084…087/091），而判词**出不了本 run** —— `dissent` / `advisory` 在产品三根
  除聚合器与读面自身**零消费者**，四个提示词槽位**没有一个**携带判词 ⇒ 模型在下一轮里根本
  看不见上一轮被判成什么，修订无从谈起。本轮补上这条跨 run 通道，并让它可判：只读 canonical
  零出网 / 只认可归因的判词 / 缺席点名而非留空壳 / 分歧优先于多数票。
exit_criteria:
  - id: EC-01
    criterion: >-
      **分歧逐条进提示词**：`ReviewOutcomeView` 从**前序 run 的落库判词**读出面板结论与
      **每一位**未采纳者的 verdict；渲染成提示词第五段（标题
      `PRIOR REVIEW (how the last round was judged; revise against it)`）。一负一过 ⇒
      `advisory` 为 `None`（平票不报结论）、`dissent` **两位都在**、`targets` 同时含两个
      执行目标。段序为 方向 → 前序知识 → 检索 → **上一轮评审** → 被评对象。
      判据：`tests/application/run_orchestration/test_review_outcome_in_prompt.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_review_outcome_in_prompt.py -q` ⇒ 全绿；
      `test_a_split_panel_carries_both_verdicts_and_the_advisory`、
      `test_the_section_sits_between_retrieval_and_the_artifact_under_review`。
    status: PASS
  - id: EC-02
    criterion: >-
      **零回归（逐字）**：五段全缺 ⇒ `compose_prompt("PURPOSE") == "PURPOSE"`；程序**第一轮**
      的每一次会话 spec 上 `review_outcome_prompt is None`（经**产品路径**实跑取证，不是只测
      渲染器）。反证臂：前序 run **有**分歧判词 ⇒ 同一装配下那一段**在场**且含双方 verdict ——
      两条只差「前序有没有判词」。
      判据：同 EC-01 的判据文件（`test_all_segments_absent_returns_the_purpose_verbatim` /
      `test_the_first_rounds_session_carries_no_review_outcome` /
      `test_a_prior_runs_panel_reaches_the_next_sessions_prompt`）。
    verify: >-
      同上命令（13 passed）；`-k "first_rounds or prior_runs_panel or all_segments"` 三条全过。
    status: PASS
  - id: EC-03
    criterion: >-
      **失败即点名**（三态严格区分）：① 没有前序 run ⇒ `reason` 逐字 `NO_PRIOR_RUN`；
      ② 有前序 run 但**读不到可归因判词** ⇒ `reason` 点名 `NO_ATTRIBUTABLE` **且**点名那一轮
      run id（不伪造结论、`advisory` 仍为 `None`）；③ 本 run 的**行还没落库**（第一轮开工那
      一刻的真实形态）⇒ 点名 `NO_RUN_ROW`，**不是**失败（判成失败会让每个程序的第一轮必然
      失败）。未能归因的判词**逐条点名**且**不进任何票**。本 run 不属于任何程序 ⇒ **点名拒绝**。
      判据：同 EC-01 的判据文件。
    verify: >-
      同上命令；`test_no_prior_run_is_named_and_carries_nothing` /
      `test_a_prior_run_without_attributable_findings_is_named` /
      `test_an_unattributable_finding_is_named_not_folded_into_a_vote` /
      `test_a_run_outside_any_program_is_refused_not_guessed`。
    status: PASS
  - id: EC-04
    criterion: >-
      **跨 run 真的连起来（端到端）**：一个**真程序**跑两轮，第二轮开工前经**产品闭包**
      （`services/api/review_outcome_support.review_outcome_builder`，与两个组合根同源）读到的
      前序 run **恰是第一轮**（经 `program_id` 反查，不靠数组位置猜），且第一轮落库的分歧判词
      在那一段里逐条可读。两个组合根（SQLite / Postgres）都把该闭包接上。
      判据：同 EC-01 的判据文件（`test_a_two_round_program_carries_the_first_rounds_panel_to_the_second`）
      + `services/api/composition.py` / `services/api/pg_composition.py` 的接线。
    verify: >-
      同上命令；另 grep 两个组合根的 `review_outcome=`（各一处）。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口**：记录写完（GOAL / PLAN / RECHECK / MEM / 阶梯「复检」行升级 / 程序表序 61 /
      进展记录 + 两表归档 / 战役级核算 + 扩表 `max_goals` 60→70）→ `git add` **全部受判文件**
      → 记录面判据 → **最后**跑 `tools/run_m0_with_witness.py` → 之后**不再**改受判文件 →
      提交推送 → CI 到终态（**逐提交一行**台账）+ 两树复检 + 凭据审计四面 `offenders=0` +
      残余与未覆盖范围逐条。读取器**自举**物证：本 GOAL 的 charter 来自
      `tools/next_round_charter.py` 对 GOAL-092 的读取（产物落 `evidence/`，`sha256` 进 RECHECK），
      且 GOAL-092 的五条残余 **5/5** 有处置。
    verify: >-
      见证 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`、0 FAILED、
      `tree changed during the run: False`；`tools/two_tree_recheck.py` 两树同结论；
      治理校验器通过；`tools/verify_goal093_closeout.py --root . --verdict-only` 全 PASS。
    status: PENDING
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
      **让这一段顶掉既有四段**：`review_outcome` 必须是**第五个并列槽位**；
      把方向 / 前序知识 / 检索 / 被评对象任一段合并进它、或让它替换其中一段 = 改契约
    - >-
      **让判词进判定面**：这一段进的是**提示词**，不得构造或改写 `Decision`、
      不得改 `aggregate_panel` 的票数与 advisory 语义（advisory 不夺真相权是既有边界）
    - >-
      **把「读不到」写成「没有」**：没有前序 run / 有前序但读不到可归因判词 /
      本 run 行未落库，三态必须**各自点名**，不得任两态合并成同一个空视图
    - >-
      **在读取器里读时钟或出网**（只读 canonical：`RunStore.for_program` +
      `ReviewFindingStore.for_run`）
    - >-
      把真实凭据（`sk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - >-
      自行再扩 `max_goals`：本轮扩表**已由用户授权**到 70，**不得**在此基础上继续扩
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    需要**再**扩 `max_goals` / 改战役预算 —— 停下登记（用户决定）
  - >-
    只靠改判据就能让「判词驱动下一轮」看起来成立 —— 停下登记（那是假绿）
child_plans:
  - .cursor/plans/tasks/PLAN-20261022-093-goal-093-the-review-verdict-drives-the-next-round.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261022-093-goal-093-the-review-verdict-drives-the-next-round.md
memory_entries:
  - MEM-20261022-227
---

## 目标与退出标准

**一句话**：让**上一轮评审的判词**成为**下一轮会话的一部分**，并且让「分歧」在搬运中
**不被压成一个多数票**。

**建档实测（缺口形态，逐条带读数；全部在本轮扩表前跑）**：

1. **判词出不了本 run**：`dissent` / `advisory` 在产品三根（`packages/`·`services/`·
   `adapters/`）里，除聚合器自身（`packages/application/evaluation/panel_verdict.py`）与读面
   自身（`adapters/canonical/review_read.py`）**零消费者**；
2. **没有「修订指令」这一类概念**：`revision_directive` / `review_directive` /
   `directive_from_review` / `prior_panel` / `remediation` 五词在产品三根**全零命中**；
3. **四个提示词槽位没有一个携带判词**：`direction` / `prior_knowledge` / `retrieval` /
   `review_material` 的渲染器上 `rg verdict` **零命中** ⇒ 「上一轮判成什么」在下一轮的
   会话里**根本不可见**，修订无从谈起。

**本 GOAL 的射程边界（先写清楚，避免越判）**：

- **只新增**：`packages/application/run_orchestration/review_outcome.py`、
  `services/api/review_outcome_support.py`、`ReviewOutcomeView` 的第五槽位与它的渲染器、
  两个组合根的一行接线、本 GOAL 的判据与记录；
- **不改**：`aggregate_panel` 的票数与 advisory 语义、`TrustLabel`、`Decision`、
  任何既有判据的断言、m0 条数、`PRODUCT_ROOTS`；
- **如实登记**：本轮**不**判「模型据此真的修订了」—— 那是 live 判据 + 人评，与 GOAL-082
  EC-04 的未决取舍同一条诚实边界。本轮判的是「判词送到了会话门口、可归因、分歧不丢」。

## 为什么这一轮更近科研（以及哪一面没被推进）

**推进的那一面（阶梯「复检」域的 `下一级`，逐字）**：「评审的判词驱动下一轮修订 ——
把分歧变成下一轮的**修订指令**」。上一轮把判词做成了**可读**（可归因 / 可聚合 /
平票也可读），本轮把它做成**可搬运**：下一轮的会话开工时就看见「上一轮谁判了什么、
分歧在哪」。没有这条通道，「评审」在科研循环里就只是**一次性的闸门**而不是**驱动源**。

**没推进的那一面（如实登记）**：**判词 → 指令**的**改写**不在本轮。本模块只做
**搬运 + 有界摘录**：把「该改什么」提炼成指令是**模型**的事（下一轮的会话读这一段），
模块里生成指令会造出一段**没有作者的判词**（与 AGENTS.md §8「记忆不是自由写入的摘要」
同一纪律）。因此本轮的判据面停在「分歧逐条送达且可归因」，不停在「指令质量」。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **先让通道跑通，再写判据**：`review_outcome` 首版在真 run 上直接**打坏了产品路径**
  （`runs.get_run` 对尚未落库的本 run 抛 `KeyError` ⇒ 路由 404）—— 这是「先跑起来」
  才暴露的形态，纯单元测试看不出来；
- **反证在合成记录上改事实**（一负一过 / 同判 / 无可归因 / 无前序 / 行未落库），
  **不改断言**；
- **记录写完 → `git add` → 跑门 → 不再改受判文件**（GOAL-091 `W-6` / GOAL-092 cycle 2-3
  的两次判红都是这条顺序的代价）。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**，如实登记 + `covered_by`。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS + 独立 RECHECK + 本文件收口（`latest_recheck` 为
  **仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条 + **阶梯记账成立**（宪章
  `依据 GOAL` 与 `进展记录` 各收录本 GOAL）+ 正式见证的 `terminal_line` 全绿。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 迭代日志

（**逐 cycle 一行**，不把多次修复压成散文。每一行的「修复」是该 cycle **真的修掉**的东西，
「剩余差距」是该 cycle 结束时**仍未达成**的东西 —— 两者都按当时的读数写。）

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261022-093 | （未提交） | 读取器自举（GOAL-092 → 本 GOAL 的 charter，5 条残余）；宪章扩表 60→70 + 序 61（三条宪章判据 **20 passed**）；`review_outcome` 通道落地（第五槽位 + 渲染器 + 两个组合根接线）；新判据 **13 passed**；受影响套件 **325 passed**；全量 e2e **369 passed / 19 skipped** | 无（未推送） | **4**：① `runs.get_run` 对**本 run 尚未落库**抛 `KeyError` ⇒ 真 run 的产品路径直接 404（新增 `NO_RUN_ROW` 第三态，**不**判失败）；② 测试里先接闭包再装 spec 记录器 ⇒ 两次 `replace` 互相顶掉（改成一次 `replace` 装两件事）；③ `ReviewOutcomeView` 缺 `targets` ⇒ 「两个模型分歧」与「一个模型自言自语」不可区分（补字段并在提示词里逐条列出）；④ `composition.py` 恰在 450 行 ⇒ 接一行就超（合并三处重复注释，条目一条未减） | EC-05 收口；记录面 / 两树 / CI 全未跑 | 写 GOAL/PLAN/RECHECK/MEM + 阶梯「复检」行 + 进展记录 |
| 2 | （同上） | （待填） | 记录写完 → `git add` 全部受判文件 → 记录面判据 → **最后**跑 m0 → 提交推送 → CI 到终态 | （待填） | （待填） | 见下 | 收口 |

## 上一轮残余的处置（5/5，逐条）

**这一节是「读取器自举」的物证**：`W-1`…`W-5` 是读取器从 GOAL-092 正文里**读出来的**
（产物 `evidence/GOAL-20261022-093-next-round-charter.md`，`sha256:419d9542…`），不是手抄。

| 上一轮 | 残余（读取器的判词） | 本轮的处置 | 证据 / 理由 |
| --- | --- | --- | --- |
| `W-1` | 读取器只覆盖战役级迭代；产品内「模型据上一轮结论提出新问题」仍无判据 | **不做**（如实保留） | 仍被 GOAL-082 EC-04 的未决取舍卡住（改判会假绿）；解除条件属产品结构改动 |
| `W-2` | `W-NN` 编号连续性是**新纪律**，历史 GOAL 喂不进读取器 | **做掉（本轮即自举）** | 本轮就是第一份「按新纪律写的 GOAL 被读取器读出来」的真序列：GOAL-092 的 `W-1…W-5` 连续 ⇒ `exit 0`、5 条全读、不写半成品。历史 GOAL 的补编号仍不在射程（那是记录改写） |
| `W-3` | 读取器**不判** RECHECK 正文结论对不对 | **不做**（边界保留） | 那是复检面自己的判据责任；读取器只读 frontmatter 的 `result` 是**声明**而非**判断**，扩到正文会把「格式检查」变成「语义裁决」 |
| `W-4` | CI 台账的「全绿」是机械分类，不独立取证 CI | **不做**（边界保留） | 台账写错它就跟着错 —— 这是如实的射程；本 GOAL 的 CI 结论仍逐提交记在「CI 台账」节并由人可复核 |
| `W-5` | 骨架第三节/第四节只是读数，「做哪一个下一级」是判断 | **承接**（本轮即示范） | 本轮的靶子（复检域的 `下一级`）就是**判断**：读取器把七个域的 `下一级` 都读出来了，选哪一个记在「为什么这一轮更近科研」节，理由可复核 |

## 残余与未覆盖范围（逐条）

**未覆盖（`W-1`…`W-5`）**：

- **`W-1`**：**判词 → 指令**的改写未做。本模块只搬运判词与分歧；把「该改什么」提炼成
  指令是下一轮**模型**的事。因此「评审驱动修订」在本轮的含义是**判词送达**，不是
  「修订一定发生」—— 后者需要 live 判据 + 人评。
- **`W-2`**：**模型是否真的据它改了**无判据。与 GOAL-082 EC-04 同一条诚实边界：
  模型对「内容采纳」不可判，子串判据会假绿。
- **`W-3`**：**只有一个被评对象、一个协议**。分歧来自两位评审者（两个执行目标），
  但「多个被评对象 / 多轮评审链」不在射程。
- **`W-4`**：**只取序号最大的那个前序 run**。若上一轮没有判词（例如那一轮根本没到评审
  阶段），本模块**不会**继续往前找更早的 run —— 它点名 `NO_ATTRIBUTABLE` 而不是猜一个
  「最近一次有判词的轮次」。这是有意的：跨过空轮去取旧的评审结论会让「上一轮」这个说法
  失真。
- **`W-5`**：**`RECHECK` 只覆盖本地树**。CI 覆盖推送后的树，两者对象不同（既有边界，
  逐轮如实登记）。

**残余风险（`R-1`…`R-3`）**：

- **`R-1`**：`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- **`R-2`**：投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- **`R-3`**：这一段进的是**提示词**，不是**判定面**。判词仍不夺真相权：`Decision` 由验收门
  给出，`aggregate_panel` 的票数语义**一行未动**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-22 | **ACTIVE** | **建档**：承用户 goal-mode 指令（扩表 60→70 + 序 61）。**扩表理由有两半**：① 「迭代」域的**战役级**那一面从未在真实序列自举（GOAL-092 `W-2` 明写读取器只适用于按新纪律写的 GOAL）—— 本轮以 GOAL-092 为输入跑通 `exit 0` / 5 条残余 / 阶梯命中「迭代」/ CI 台账 17 行；② 「复检」域的 `下一级` 实测**可推进**（判词在产品三根零消费者、四个提示词槽位无一携带判词）。`max_cycles: 14`。 |
| 2026-10-22 | **ACTIVE** | **收口面落地**：五个 EC 全 PASS（EC-01…04 判据面 13 例；EC-05 记录面）；读取器**自举**（GOAL-092 → 本 GOAL charter，5 条残余 5/5 处置）；扩表 60→70 + 序 61；阶梯「复检」行升级。收口验证器 `tools/verify_goal093_closeout.py` **68/68 PASS**。CI 台账待推送后回填。 |

## CI 台账

（**逐提交逐 job**，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是**两种不同**的形态，
分别登记；后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| （待填） | （待填） | （待填） | 收口时逐提交回填 |
