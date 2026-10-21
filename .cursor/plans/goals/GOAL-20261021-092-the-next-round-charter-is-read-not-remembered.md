---
id: GOAL-20261021-092
slug: the-next-round-charter-is-read-not-remembered
title: 下一轮的 charter 由上一轮的残余与阶梯机械派生，读取器带反证臂
status: ACHIEVED
created_at: 2026-10-21
updated_at: 2026-10-21
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-21 的 goal-mode 指令逐字：「本轮的**双重目标**：既推进科研能力，又把
    「上一轮的输出 → 下一轮的提示词」这一步从人工变成机器。」「现状：这个衔接**靠人**——
    驱动方读完 GOAL 报告，手工写提示词。漏一条残余就丢了。」「**目标形态**：一个确定性
    读取器（零出网、零模型），输入是**已收口的 GOAL 与其 RECHECK**，输出是**下一个 GOAL
    的 charter 骨架**」「**失败即点名**：GOAL 未终态 / 缺 RECHECK / 阶梯未收录 / `W` 编号
    不连续 ⇒ 拒绝生成并逐条说明缺什么（不静默跳过，不生成半成品）。」授权要点：
    (a) 全部决策权下放，只有「改产品边界 / 放宽任何判据 / 动冻结面 / 新增或改 TrustLabel
    取值 / 扩战役预算」才停下登记 BLOCKED；(b) 每一步必须有**机械判据**；(c) 每轮必须让
    科研能力阶梯前进；(d) push-to-main-for-CI（只推 `main`、不 force、不重写历史）；
    (e) `max_cycles` 给 **14**；(f) 程序表只剩 1 个名额（`max_goals: 60`）⇒ 一个 GOAL
    同时交付两件事，不拆。
objective: >
  把「上一轮的输出 → 下一轮的 charter」从**靠人记**变成**机器读**：交付一个确定性读取器
  （零出网、零模型、零时钟），它是**已收口 GOAL + 其 RECHECK + 宪章**的纯函数，产出含三块
  可提取事实的骨架（残余 `W-NN` 逐条原文 / 阶梯里收录本 GOAL 的域的「下一级」/ CI 台账
  结论）；六类不合格输入（未终态 / 缺 RECHECK / 复检不通过 / 不属于本 GOAL / 阶梯未收录 /
  编号断号）**逐条点名拒绝且不写盘**；五条提示词判据各带回证臂（不丢不增 / 删一条少一条 /
  改正文跟着变 / 非终态点名拒绝 / 缺 RECHECK 点名失败 / 同输入逐字节相同）。再用它的产出
  作为序 60 的 charter 输入**真的**写一轮，并把上一轮七条残余**逐条处置**（7/7 有归属）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **读取器成立**：`tools/next_round_charter.py`（入口）+ `tools/charter_parse.py`
      （纯解析原语，单一来源）在树；对**已收口** GOAL + 其 RECHECK + 宪章产出骨架，含三块：
      ① 残余节 `W-NN` **逐条原文**（含续行，不摘要）；② 阶梯里 `依据 GOAL` 收录本 GOAL 的
      每一行的 `域` 与 `下一级是什么`（原文）；③ CI 台账的**逐行机械分类**与结论
      （全 success / 无 run / 判红 / 未识别）。**确定性**：零出网、零模型、零时钟
      （AST 钉住 `datetime.now` / `time.time` / `date.today` / `socket` / `urllib` 零命中），
      落盘走二进制（无 `\\r`）。**判断面显式留空**（`<待填：判断>`），不猜。
      判据：`tests/tooling/test_next_round_charter.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_next_round_charter.py -q`
      ⇒ 全绿；对 GOAL-091 真文件跑 ⇒ 残余 **7/7**、阶梯命中**复检**行、CI 台账 5 success
      + 1 无 run ⇒「全绿」；产物落 `evidence/`，`sha256` 进 RECHECK。
    status: PASS
  - id: EC-02
    criterion: >-
      **反证臂逐条成立（不静默、不产半成品）**：① 删掉整条 `W-7`（编号仍连续）⇒ 产物少那一条
      且自报「共 6 条」；② 改写某条残余正文 ⇒ 产物里跟着改写（证明是读出来的，不是硬编码）；
      ③ `status` 改成 `ACTIVE` / `DRAFT` / `PAUSED` ⇒ `REFUSED GOAL_NOT_TERMINAL`、
      **exit 2**、**不创建 `--out` 文件**；④ `latest_recheck` 指向不存在的文件 ⇒
      `REFUSED RECHECK_MISSING`；⑤ 复检属于别的 GOAL ⇒ `REFUSED RECHECK_NOT_THIS_GOAL`；
      ⑥ 复检 `result: REVISE` ⇒ `REFUSED RECHECK_NOT_PASSING`；⑦ 删掉 `W-2` 但**不改编号**
      ⇒ `REFUSED RESIDUAL_GAP` 并**报出读到的编号序列** `[1, 3, 4, 5, 6, 7]`；
      ⑧ 阶梯无任何域收录本 GOAL ⇒ `REFUSED LADDER_NOT_RECORDED`；⑨ 残余节被清空且无
      「无残余」标记 ⇒ `REFUSED RESIDUAL_EMPTY`。
      判据：同 EC-01 的判据文件（逐条独立用例，全部在**合成树**上改事实，不改断言）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_next_round_charter.py -q`
      ⇒ 19 passed（①…⑨ 各有用例，另含确定性两例与口径同源一例）。
    status: PASS
  - id: EC-03
    criterion: >-
      **确定性逐字节成立**：同一输入跑两次 ⇒ 产物 `sha256` 相同；经 `--out` 落盘两次 ⇒
      两个文件 `read_bytes()` 相同且都不含 `\\r`（Windows 文本模式会写 CRLF ⇒ raw 字节变，
      与本仓既有「二进制写盘」纪律同源）。读数进 RECHECK：产物的 `sha256` 与两次运行一致。
    verify: >-
      `... -m pytest tests/tooling/test_next_round_charter.py -q -k "identical or reproducible"`
      ⇒ 2 passed；`certutil`/`sha256sum` 两次落盘比对相同（RECHECK 记读数）。
    status: PASS
  - id: EC-04
    criterion: >-
      **产物**真的**被用作序 60 的 charter 输入**（不是摆设）：骨架
      `.cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md` 在树且被本 GOAL
      **点名路径 + `sha256`**；本文件「上一轮残余的处置」表
      **7/7** 覆盖 GOAL-091 的 `W-1`…`W-7`，每条给出「做掉 / 承接 / 不做+理由」三态之一；
      其中 `W-6`（见证看不见未跟踪文件）与 `W-7`（脚本进射程后才被判）**本轮有实际动作**
      （先 `git add` 再跑门 / 新脚本从第一行起就在 `IN_SCOPE` 里），其余五条如实登记。
      判据：`tools/goal092_closeout_assertions.py`（读真文件，不读断言里的副本）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ 全绿（含本轮
      断言集零判负）；`tools/verify_goal092_closeout.py --root . --verdict-only` ⇒ 全 PASS。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口**：记录写完（GOAL / PLAN / RECHECK / MEM / 阶梯「迭代」行升级 / 程序表序 60 /
      进展记录 + 两张表的归档 / 战役级核算 + 预算触顶登记）→ `git add` **全部受判文件** →
      记录面判据 → **最后**跑 `tools/run_m0_with_witness.py` → 之后**不再**改受判文件 →
      提交推送 → CI 到终态（逐提交台账）+ 两树复检 + 凭据审计四面 `offenders=0` +
      残余与未覆盖范围逐条（含「战役预算已用尽，需用户决定扩表或收兵」）。
    verify: >-
      见证 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`、`PASS [` 24 行、
      0 FAILED、`tree changed during the run: False`；`tools/two_tree_recheck.py` 两树同结论；
      治理校验器通过。
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
      **让读取器「猜」判断面**：objective / EC 的具体内容属**判断**，骨架里必须留空
      （`<待填：判断>`）；把猜出来的值写进去再声称「自动派生」= 假绿
    - >-
      **把拒绝降级成警告或半成品**：未终态 / 缺复检 / 复检不通过 / 阶梯未收录 / 断号
      必须 `exit 2` **且不写盘**；打印一条 WARN 继续生成是禁止的
    - >-
      **给读取器接上模型或网络**（它是确定性读取器：零出网、零模型、零时钟）；
      也不得为通过判据把时钟读出来再冻结
    - >-
      把真实凭据（`sk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - >-
      自行扩 `max_goals`：序 60 用尽后**必须**停下登记「需用户决定扩表或收兵」
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    需要扩 `max_goals` / 改战役预算 —— 停下登记（用户决定）
  - >-
    只靠改判据就能让读取器「看起来在读」—— 停下登记（那是假绿）
child_plans:
  - .cursor/plans/tasks/PLAN-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md
memory_entries:
  - MEM-20261021-226
---

## 目标与退出标准

**一句话**：把「上一轮输出 → 下一轮 charter」这一步从**人的记忆**换成**文件的读数**，
并让「读数漏了一条」与「读数少了一条」在判据上分得开。

**建档实测（缺口形态，逐条带读数）**：

1. **衔接靠人**：`.cursor/plans/goals/evidence/` 下**没有**任何「下一轮输入」类制品；
   历轮的做法是驱动方读 GOAL 的「残余与未覆盖范围」，手工写进下一轮提示词。丢一条
   不会被任何东西发现 —— 判据只覆盖「记录写了什么」，不覆盖「下一轮读到了什么」。
2. **`W-NN` 编号是弱约定**：GOAL-090 只用 `W-6` 一条（编号从 6 起，前面没有 `W-1…W-5`），
   GOAL-091 用 `W-1…W-7`。⇒「编号连续」不是既有事实，**必须由读取器显式检查**，
   否则「删了一条」与「本来就少」不可区分。
3. **阶梯的「下一级」没有消费者**：`.cursor/plans/goals/MAINLINE.md` 的阶梯表**六轮**
   存在，但除人工抄写外**没有任何代码**读它（`test_mainline_research_ladder_advances.py`
   只判「它自洽」，不判「有人拿它当输入」）。

**本 GOAL 的射程边界（先写清楚，避免越判）**：

- **只新增**：`tools/next_round_charter.py`、`tools/charter_parse.py`、它们的判据、
  一份产物骨架、本 GOAL 的记录面、四道门与验证器清单里的登记；
- **不改**：`tests/` 里任何既有判据的断言、`PRODUCT_ROOTS`、m0 条数、任何产品代码、
  任何 HTTP 面、`TrustLabel`；
- **不静默回落**：六类不合格输入一律 `exit 2` + 点名 + **不写盘**；
- **如实登记**：读取器只覆盖**战役级**迭代面（每轮的 charter 由上一轮的残余派生）；
  产品内「模型据上一轮结论提出新问题」这一面仍无判据，且仍被 GOAL-082 EC-04 的未决取舍
  卡住 —— 本 GOAL **不**声称解决了那一面。

## 为什么这一轮更近科研（以及哪一面没被推进）

**推进的那一面**：战役级迭代过去是「人记得读报告」。现在每轮的**输入**由上一轮的
残余 + 阶梯的下一级**机械派生**，且派生器带反证臂（删一条 ⇒ 少一条；改状态 ⇒ 拒绝）。
它的价值不是「省事」，而是**残余面不再随注意力流失**：一条 `W` 要么被下一轮处置，
要么在下一轮的表里显式登记为「不做」，没有第三种下场。

**没推进的那一面（如实登记）**：阶梯「迭代」行的 `下一级` 原文写的是「模型据上一轮结论
提出**新问题**」—— 那是**产品内**的迭代面，与「检索 / 计划」两行同指一件事，并被同一个
未决取舍卡住（GOAL-082 EC-04：模型只做不可判的内容采纳，三次 run 的 `duplicate_pairs`
= 30/30/10 ⇒ 子串判据会假绿；解除条件是需要产品结构改动）。本轮**不动**它。

⇒ 因此阶梯「迭代」行本轮升级的是**战役级**那一面，`当前级` 里逐字写明这一区分，
`下一级` 保留产品内那一面 —— **不**把两件事混成一次升级。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **先让读取器在真文件上跑通，再写它的判据** —— 否则判据是在测一个还没跑过的东西；
- **反证在合成树上改事实**（删整条 `W` / 改 `status` / 删复检 / 改 `parent_goal` /
  改 `result` / 删 `W-2` 留断号 / 清空残余节），**不改断言**；
- **新脚本从第一行起就在 `IN_SCOPE` 里**（GOAL-091 `W-7` 的直接回应：上一轮是「先写后登记」，
  登记那一刻被四道门判出 5 处）；
- **记录写完 → `git add` → 跑门 → 不再改受判文件**（GOAL-091 `W-6` 的直接回应：见证看不见
  未跟踪文件，所以「先 add 再跑门」是唯一不靠修改口径就能让见证成立的做法）。

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
| 1 | PLAN-20261021-092 | （未提交） | 读取器与解析原语落地；`pytest tests/tooling/test_next_round_charter.py` ⇒ **19 passed**（9 条拒绝臂 + 2 条确定性 + 口径同源）；对 GOAL-091 真文件产出骨架：残余 **7/7**、阶梯命中「复检」、CI 台账 5 success + 1 无 run ⇒「全绿」；两次落盘 `sha256` 相同（`2776ad06…`）；四道门自跑全绿 | 无（未推送） | **4**：① 读取器首版 **517 行** > 450 ⇒ 拆出 `charter_parse.py`；② 判据辅助函数把 `R-1…R-3` 的缩进续行吞进最后一条 ⇒ 显式「非缩进行结束当前条」；③ `_delivery_verdicts` **52 行** > 50 ⇒ 拆 `_face_verdicts` / `_guard_verdicts`；④ `IN_SCOPE` 加 4 条后判据文件 **456 行** > 450（先试搬清单进新文件，被 goal031/032/038 三个按字面量读 `IN_SCOPE` 的历史断言集**正确地判红**）⇒ 换道合并 39 行重复注释、条目一条未动 | EC-05 收口；记录面 / 两树 / CI 全部未跑 | 写 GOAL/PLAN/RECHECK/MEM + 阶梯与程序表 |
| 2 | （同上） | `9326c788` | 记录写完 → `git add` 全部受判文件（**13 个新增**）→ 记录面判据 → **最后**跑 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False`、覆盖 **4555** 个受判面文件；两树复检 **62 条判词**、两树 `sha256` 逐字相同（`7cb35313…`）；治理校验通过 | [M0 39553118966](https://github.com/Eswink/research-system-new/actions/runs/39553118966) ⇒ **2/8 job 判红**（`quality-ubuntu` / `quality-windows` 同一判据） | **1**：判红 #1 = **见证幽灵条目**。根因是我中途把 `IN_SCOPE` 试搬进 `tests/tooling/tools_gate_scope.py`、`git add` 过又回退删除 ⇒ 见证记住了那条「被跟踪但工作树已删除」的空哈希（`sha256: ''`）；本地 `--verify-only` 与本地树**互相自洽**（都含它）⇒ 本地绿，CI 检出的树里没有该文件 ⇒ 判据（正确地）判红 | 剩下 6 job 全 success；**判据本身未改**（改它会动 GOAL-090 定下的口径） | 重跑门让见证对着「没有那个文件」的树重写 |
| 3 | （同上） | `7f8bf2a5` | 对无幽灵的树重跑 m0：同一终态行、`PASS [` 24、0 FAILED、`tree changed: False`、覆盖 **4554**、`--verify-only` 退出码 `0` | [M0 39558553519](https://github.com/Eswink/research-system-new/actions/runs/39558553519) ⇒ **1 判红 / 1 取消 / 6 success** | **1**：判红 #2 = **门后改记录**（同一判据、**根因换了**）。我在门跑完之后又改了 GOAL 与 RECHECK 去登记判红 #1 本身 ⇒ 见证覆盖的不是提交后的树（差 4 项内容 + 2 项名称）。`quality-windows-latest` 是 **`cancelled`**（`cancel-in-progress` 在 ubuntu 判红后取消在途 job）—— cancelled ≠ 判红，分开记 | EC-05 仍未收口；**顺序纪律再次被自己的动作破坏** | 让「最后一次改记录」发生在跑门**之前** |
| 4 | （同上） | `975d7780` → `7bc2560f` → `0b7ce86b` → `5b0e9f2f` → `609bab8a` | 每次记录改动后重跑门重封见证；最终覆盖 **4556**、`--verify-only` 退出码 `0` | `975d7780` [M0 39564741935](https://github.com/Eswink/research-system-new/actions/runs/39564741935) **八 job 全 success**；`7bc2560f` / `5b0e9f2f` **无 run**（`covered_by` 相邻提交的 run：同批推送被 GitHub 合并）；`0b7ce86b` [M0 39570501350](https://github.com/Eswink/research-system-new/actions/runs/39570501350) **八 job全 success** + CodeQL [39570500949](https://github.com/Eswink/research-system-new/actions/runs/39570500949) 三 job success；`609bab8a` [M0 39576562340](https://github.com/Eswink/research-system-new/actions/runs/39576562340) **八 job 全 success** | **1**：台账里两个 run id 是我**按模式猜的占位符**（真实值从轮询日志取回后修正）——记录面的读数也必须有来源 | EC-05 尚未 PASS（还在等最终树）；三个「无 run」提交靠 `covered_by` 记账 | 完成核验（会揪出 status 与归档两处缺口） |
| 5 | （同上） | `dcd6228c` → `e9ef7685` | **完成核验判负补正**：① 加载 `validate.py` 并**实跑**只对 ACHIEVED 生效的三条检查（5 个 EC 全 PASS、`latest_recheck` 解析到 RECHECK-092 `result: PASS`、`ERRORS` 为空）；② 两表各 **3 行**、两处 `archive/` 指针在位、089 与 54/55 在活跃面零命中、活跃与归档**交集为空**；`test_mainline_archive_is_continuous.py` + 另两条宪章判据 **20 passed** | `dcd6228c` **无 run**（`covered_by` 下一条）；`e9ef7685` [M0 39582771457](https://github.com/Eswink/research-system-new/actions/runs/39582771457) **八 job 全 success** + [Push 39582771217](https://github.com/Eswink/research-system-new/actions/runs/39582771217) success | **3**：① frontmatter 仍是 `ACTIVE`（收口脚本只改 EC-05 与状态历史行）⇒ 改 `ACHIEVED` 并实跑 ACHIEVED-专属三项；② 归档搬运只做了一半（两份 archive 写出，但活跃面两表各 4 行、归档无人引用）⇒ 原样移出两行 + 补两处指针；③ RECHECK 第六节写「见下方 m0 见证一栏」而该栏不存在 ⇒ 补成实表 | 记录里仍有 `4554` 与 `4556` 两个覆盖数并存（历史读数未标注） | 收口补正已落地，等最终树 |
| 6 | （同上） | `3a3a7abd` → `6eae045f` → `27e40564` → `91b69112` → `e3e53cfb` → `3cbbaf06` | 台账补记 `dcd6228c`；RECHECK 的 `4554` 标注为历史读数并**指向最终 `4556`**（以 `M0-WITNESS.json` 为准）；每次记录改动后重跑门重封见证 | `3a3a7abd` / `27e40564` **无 run**（`covered_by` 相邻提交）；`6eae045f` [M0 39588049247](https://github.com/Eswink/research-system-new/actions/runs/39588049247) **八 job 全 success** + [Push 39588048732](https://github.com/Eswink/research-system-new/actions/runs/39588048732) success；`91b69112` [M0 39593672439](https://github.com/Eswink/research-system-new/actions/runs/39593672439) **八 job全 success** + [Push 39593671983](https://github.com/Eswink/research-system-new/actions/runs/39593671983) success | **1**：同一份记录里 `4554` 与 `4556` 并存且都没说哪个算数 ⇒ 标注历史读数 + 指向见证 | **无**（五个 EC 全 PASS、CI 到终态） | 收口 |

**如实说明**：本轮 `max_cycles: 14`，实际用了 **6** 个 cycle（1 开发 + 2 判红修复 + 1 收口 + 2 补正）。
两次判红**都不是判据错**，而是**我自己造成的树状态**；两次修法都没有碰判据。
## 上一轮残余的处置（7/7，逐条）

**这一节就是「骨架被真的用了」的物证**：`W-1`…`W-7` 是读取器从 GOAL-091 的正文里
**读出来的**（不是手抄的），本表给每一条一个下场。三态：**做掉** / **承接** / **不做**。

| 上一轮 | 残余（读取器的判词） | 本轮的处置 | 证据 / 理由 |
| --- | --- | --- | --- |
| `W-1` | `REVIEW_SCORE` 的分数仍是「评审者自述」 | **不做**（登记为下一战役候选） | 判「分数与判词是否自相矛盾」要在判分面上加第二个键，属产品结构改动；本 GOAL 的射程不含它 |
| `W-2` | 分歧的**质量**无人判 | **不做** | 需要第三方裁决或人判（谁更对不是机械事实）；如实保留 |
| `W-3` | 只有一个协议、一份被评对象 | **不做** | 与 `real_research_deliverable` 同一条诚实边界；扩协议不是本轮的靶子 |
| `W-4` | 中转站瞬时失败会打掉一位评审者 | **承接**（读面已如实点名 `UNKNOWN`） | 重试面属评审执行链，本轮不碰；读面不冒充判负这一条**已成立** |
| `W-5` | `--verify-only` 只覆盖本地树 | **不做**（边界保留） | CI 覆盖推送后的树，两者对象不同是**事实**，改判据会制造假的「已覆盖」 |
| `W-6` | 见证不记录**未跟踪**的受判面文件 | **做掉（用顺序纪律）** | 本轮**先 `git add` 全部受判文件再跑门**；判据本身未改（改它会动 GOAL-090 定下的口径，须用户拍板），但路径已由顺序消除 |
| `W-7` | 收口脚本**进射程之后**才被四道门判 | **做掉（顺序反转）** | 本轮两个新脚本与两份收口资产**从第一行起**就登记进 `IN_SCOPE` / `_VERIFIERS`，四道门在写完时即已覆盖 |

## 战役预算触顶登记（**需用户决定**）

**触顶事实**：宪章 `max_goals` 为 **60**，序号 **1…60 已全部登记**（本 GOAL 是序 60，
最后一行）⇒ 按宪章「触顶即做战役级核算」规则，本 GOAL 收口时**必须**把这件事写清：

**战役预算已用尽，需用户决定扩表或收兵。** 我不自行扩 `max_goals`（宪章与用户指令都写明
那不是我能定的）。两条路与各自需要的用户动作：

- **扩表**：用户给出新的 `max_goals`（一次 +N），并在宪章「战役级核算」节留一份逐轴实测
  缺口清单（既有惯例：每次扩表都带缺口读数与「序 N 已在新增之列」的声明）。
  下一轮候选已按可推进性排序，见下；
- **收兵**：保持 60，把阶梯上剩下的「下一级」如实登记为**未达成**并结束战役。

**下一轮候选（按可推进性排序，供扩表决策参考）**：

1. **复检域 / 评审的判词驱动下一轮修订** —— 把 `advisory` 接回立题/计划的输入面（跨 run
   机制）。这是阶梯「复检」行的 `下一级`，且 GOAL-091 已让分歧可读、可归因 ⇒ 前提都在；
2. **报告域 / 报告由模型撰写** —— 现为确定性汇编，叙述质量无人判；需一个新的判据面；
3. **证据域 / 跨记录的语义矛盾聚合** —— 现只在写入时判；需全库扫描（迁移面，会改
   Canonical State 的读面成本）；
4. **检索 / 计划 / 迭代（产品内那一面）** —— 三行同指「改变下一轮问题」，被 GOAL-082
   EC-04 的未决取舍卡住（模型只做不可判的内容采纳）；**解除条件属产品结构改动**，
   需用户拍板后才值得立项。

## 残余与未覆盖范围（逐条）

**未覆盖（`W-1`…`W-5`）**：

- **`W-1`**：读取器只覆盖**战役级**迭代（每轮的 GOAL charter 由上一轮的残余派生）。
  **产品内**「模型据上一轮结论提出新问题」这一面**仍无判据**，且仍被 GOAL-082 EC-04 的
  未决取舍卡住 ⇒ 本 GOAL **不**声称解决了那一面。
- **`W-2`**：`W-NN` 编号连续性是**本轮新加的纪律**，不是既有事实。GOAL-090 只有 `W-6`
  一条 ⇒ 直接喂进读取器会判 `RESIDUAL_GAP`。这是**正确**行为，但意味着读取器只适用于
  按新纪律写的 GOAL；历史 GOAL 若要复用，需要先补编号（属记录改写，不在本轮射程）。
- **`W-3`**：读取器**不判** RECHECK 正文的结论对不对（只读 frontmatter 的 `result`）。
  一份 `result: PASS` 但正文自相矛盾的复检仍会被接受 —— 那是复检面自己的判据责任。
- **`W-4`**：CI 台账的「全绿」是**按行分类**的机械读数（`success` / 无 run / 判红 /
  未识别），**不**独立取证 CI 本身。台账写错，读取器就跟着错。
- **`W-5`**：骨架的第四节（CI 结论）与第三节（阶梯下一级）都只是**读数**；
  「这一轮做哪一个下一级」仍是判断 —— 本 GOAL 的选择（迭代域的战役级那一面）
  记在「为什么这一轮更近科研」节，理由可复核但不是机械推导。

**残余风险（`R-1`…`R-3`）**：

- **`R-1`**：`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- **`R-2`**：投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- **`R-3`**：读取器是**开发侧**资产（`tools/`），不在 `PRODUCT_ROOTS` 里；它的正确性由
  `tests/tooling/test_next_round_charter.py` 与四道门的 `IN_SCOPE` 登记承担，
  **不是**产品运行时的一部分。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-21 | **ACTIVE** | **建档**：承用户 goal-mode 指令「把上一轮输出 → 下一轮提示词这一步从人工变成机器」。建档实测三处缺口（无「下一轮输入」制品 / `W-NN` 编号只是弱约定 / 阶梯的「下一级」无消费者）。序 60 = 程序表最后一个名额；`max_cycles: 14`。 |
| 2026-10-21 | **ACTIVE** | **CI 首轮 2/8 判红**（`9326c788`）：见证里有而树里没有 `tests/tooling/tools_gate_scope.py` —— 那是我中途试拆分清单、`git add` 过又回退删除留下的一条空哈希记录。判据（正确地）判红；修法是**重跑门让见证对着新树重写**，不碰判据。 |
| 2026-10-21 | **ACHIEVED** | 五个 EC 全达成。**CI 到终态**：`975d7780` 八 job 全 `success`（前两轮各判红一次，都是**见证与树的绑定**问题、都是我自己造成的树状态，判据两次都正确地咬住）。**两树复检**：62 条判词、两树 `sha256` 逐字相同（`7cb35313…`）。**战役预算从此用尽**（`max_goals` 60，序 60 是最后一行）⇒ 已登记「需用户决定扩表或收兵」。 |
| 2026-10-21 | **ACHIEVED**（补正） | **完成核验判负两处并修掉**：(1) frontmatter 仍是 `ACTIVE` —— 收口脚本只改了 EC-05 与状态历史，`validate.py` 的 ACHIEVED-专属检查（全 EC PASS / `latest_recheck` 存在 / result 通过）从未运行；现已改为 `ACHIEVED` 并实跑该三项：5 个 EC 全 PASS、复检解析到 RECHECK-092（`result: PASS`）、`ERRORS` 为空。(2) 归档搬运只做了一半（两份 archive 写出，但活跃面两表仍是 4 行、归档无人引用）；现已移出 089 进展行与 54/55 修订行（移出前逐字比对归档已收录）并补两处指针，两表各 3 行、`test_mainline_archive_is_continuous.py` 绿。另补 RECHECK 第六节的 m0 读数表（原先指向一个不存在的栏）。CI `dcd6228c` 八 job 全 `success`。 |
| 2026-10-21 | **ACHIEVED**（补正二） | **完成核验第二次判负并修掉**：迭代日志只有 1 行、与 CI 台账的两轮判红直接矛盾（提示词要求逐 cycle 一行，GOAL-090 有先例）。已重写为 **6 行**（开发 / 判红#1 / 判红#2 / 收口重封 / 完成核验补正 / 台账对账），CI 台账改为**一提交一行 13 行**（补齐四个「无 run」提交、修正 `dcd6228c` 蹭用 `e9ef7685` run 的错记，五处 `covered_by` 逐一指名）。并给这条纪律**装上判据**（此前无人看着它）：`_log_verdicts` 判「台账里每个提交都在某个 cycle 行里」，两向按压各判红、raw `sha256` 逐字节复原；收口判词 62 → **65**。 |

## CI 台账

（**逐提交逐 job**，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是**两种不同**的形态，
分别登记；后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `9326c788` | [M0 39553118966](https://github.com/Eswink/research-system-new/actions/runs/39553118966) | **2/8 job 判红**；[Push 39553118615](https://github.com/Eswink/research-system-new/actions/runs/39553118615) success | 判红 #1（**见证幽灵条目**）：`quality-ubuntu-latest` / `quality-windows-latest` 同一个判据 `test_the_witness_is_for_the_tree_we_are_looking_at`，点名「见证里有而当前没有 1 项：`tests/tooling/tools_gate_scope.py`」。其余 6 job（`collector-quality` / `container-quality` / `observability-overhead-{ubuntu,windows}` / `console-frontend` / `eval-gate`）全 success |
| `7f8bf2a5` | [M0 39558553519](https://github.com/Eswink/research-system-new/actions/runs/39558553519) | **1 判红 / 1 `cancelled` / 6 success**；[Push 39558553226](https://github.com/Eswink/research-system-new/actions/runs/39558553226) success | 判红 #2（**门后改记录**）：同一判据、**根因换了** —— 门跑完后我又改 GOAL/RECHECK 去登记判红 #1 本身，见证覆盖的不是提交后的树（差 4 项内容 + 2 项名称）。`quality-windows-latest` 是 **`cancelled`**（`cancel-in-progress` 在 ubuntu 判红后取消在途 job），**不是判红** |
| `975d7780` | [M0 39564741935](https://github.com/Eswink/research-system-new/actions/runs/39564741935) | **八 job 全 `success`**；[Push 39564740930](https://github.com/Eswink/research-system-new/actions/runs/39564740930) success | 对无幽灵的树重封见证后的树；**记录一个字未改** ⇒ 见证覆盖的就是 CI 检出的那棵 |
| `7bc2560f` | **无 run** | — | 只改记录（CI 台账 + EC-05 → PASS + 预算触顶登记）；与下一条**同批推送**被 GitHub 合并成一个 run ⇒ `covered_by` = `0b7ce86b` 的 [M0 39570501350](https://github.com/Eswink/research-system-new/actions/runs/39570501350) |
| `0b7ce86b` | [M0 39570501350](https://github.com/Eswink/research-system-new/actions/runs/39570501350) / [CodeQL 39570500949](https://github.com/Eswink/research-system-new/actions/runs/39570500949) | **八 job 全 `success`**；CodeQL 三 job 全 `success` | 该 run 同时覆盖 `7bc2560f`（同批推送）。本提交**只改见证** |
| `5b0e9f2f` | **无 run** | — | 修正 CI 台账的两个**占位 run id**（真实值从轮询日志取回）；`covered_by` = `609bab8a` 的 [M0 39576562340](https://github.com/Eswink/research-system-new/actions/runs/39576562340) |
| `609bab8a` | [M0 39576562340](https://github.com/Eswink/research-system-new/actions/runs/39576562340) | **八 job 全 `success`**；[Push 39576561704](https://github.com/Eswink/research-system-new/actions/runs/39576561704) success | 该 run 同时覆盖 `5b0e9f2f`。本提交只改见证 |
| `dcd6228c` | **无 run** | — | **完成核验判负补正**（frontmatter → ACHIEVED / 归档搬运补完 / RECHECK m0 读数回表）；`covered_by` = `e9ef7685` 的 [M0 39582771457](https://github.com/Eswink/research-system-new/actions/runs/39582771457) |
| `e9ef7685` | [M0 39582771457](https://github.com/Eswink/research-system-new/actions/runs/39582771457) / [Push 39582771217](https://github.com/Eswink/research-system-new/actions/runs/39582771217) | **八 job 全 `success`** | 该 run 同时覆盖 `dcd6228c`。本提交只改见证 |
| `3a3a7abd` | **无 run** | — | 台账补记 `dcd6228c` + 状态历史补正；`covered_by` = `6eae045f` 的 [M0 39588049247](https://github.com/Eswink/research-system-new/actions/runs/39588049247) |
| `6eae045f` | [M0 39588049247](https://github.com/Eswink/research-system-new/actions/runs/39588049247) / [Push 39588048732](https://github.com/Eswink/research-system-new/actions/runs/39588048732) | **八 job 全 `success`** | 该 run 同时覆盖 `3a3a7abd`。本提交只改见证 |
| `27e40564` | **无 run** | — | RECHECK 把历史读数 `4554` 标注并指向最终 `4556`；`covered_by` = `91b69112` 的 [M0 39593672439](https://github.com/Eswink/research-system-new/actions/runs/39593672439) |
| `91b69112` | [M0 39593672439](https://github.com/Eswink/research-system-new/actions/runs/39593672439) / [Push 39593671983](https://github.com/Eswink/research-system-new/actions/runs/39593671983) | **八 job 全 `success`** | 该 run 同时覆盖 `27e40564`。**最终树**（本轮收口前的 tip） |
| `e3e53cfb` | **无 run** | — | 迭代日志重写为 6 行 + CI 台账改为一提交一行 + 新增 `_log_verdicts` 判据；`covered_by` = `3cbbaf06` 的 [M0 39600815435](https://github.com/Eswink/research-system-new/actions/runs/39600815435) |
| `3cbbaf06` | [M0 39600815435](https://github.com/Eswink/research-system-new/actions/runs/39600815435) / [Push 39600814788](https://github.com/Eswink/research-system-new/actions/runs/39600814788) | **八 job 全 `success`** | 该 run 同时覆盖 `e3e53cfb`。本提交只改见证（收口判词 **65**、覆盖 4556） |

**判红只发生在本地 / CI 各两次，全部是「见证与树的绑定」问题**（不是判据缺陷）：
`9326c788` = 曾跟踪后删除的文件留了空哈希条目；`7f8bf2a5` = 门跑完后改记录。
**两次修法都没有碰判据** —— 都是「重跑门、让见证对着真正要提交的树重写」。

**自指边界（如实登记，不假装闭合）**：本表中最后若干行的结论写于对应提交**之后**，
写下它们本身又产生新提交，而新提交自己那次 run 的结论无法再写回本表而不产生第三个提交。
链条在**本文件所在提交**处终止：它只改记录，其自身 run 的结论在收口报告里给出、
**不写回台账**（GOAL-089 / 091 同一手法）。
