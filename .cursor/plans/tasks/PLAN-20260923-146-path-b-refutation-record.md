---
id: PLAN-20260923-146
slug: path-b-refutation-record
title: 路径 (B) 的独立否证记录：把 GOAL-011 的四项实测事实落成「已否证 / 待重新设计」（GOAL-012 EC-04）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）的 EC-04：
    **把 GOAL-011 对路径 (B) 的否证写成一份独立记录并登记为「已否证 / 待重新设计」**，
    **不得**因本 GOAL 走通 (A) 就把它抹掉或改写成已完成。本 PLAN **只读 GOAL-011 的既有记录**
    并**新增**一份记录文件；**不改写** GOAL-011 的 `W-P` / `W-Q`，**不改写** PLAN-20260922-138 的
    `status: BLOCKED`，也不改任何产品代码、协议、合约、测试或门禁。零出网、零 live 调用、
    零凭据读取（本 PLAN 不做任何实跑，只做记录与引用核对）。
    **若「记录 (B) 的否证」这一动作本身需要重新设计 (B)（即需要改合约/门禁/协议）⇒ 立即停止并记
    BLOCKED**：重新设计属**需拍板**项，不是本 GOAL 的授权范围。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-146-path-b-refutation-record.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-112-verifier-token-drift-after-amend.md
---

# PLAN-20260923-146 — 路径 (B) 的独立否证记录（GOAL-012 EC-04）

## 目标

给路径 **(B)**（为 `m12_reference_research_v1` 补齐 phase 合约、靠「更多检索调用」凑够
`domain_discovery.minimum_sources: 10`）留一份**独立、可引用、不含糊**的记录：状态是
**已否证 / 待重新设计**，正文逐条覆盖四项实测事实（各带机制与实测出处），并**写明**它与
GOAL-011 既有登记（`W-P` / `W-Q` / `W-R`）和 `PLAN-20260922-138` 的 BLOCKED 状态的关系。

## 计划开始前的定案（写死）

- **D-1 载体**：新文件 `docs/roadmap/PATH_B_REFUTATION_RECORD.md`（仓库相对路径；与
  `docs/roadmap/*_COMPLETION_RECORD.md` 同一目录与命名风格，便于人找；GOAL 迭代日志与残余节
  同时登记该路径）。**不**把内容塞进 GOAL-011（那是只读历史），**不**改 PLAN-138。
- **D-2 四项事实逐条覆盖，各自带「机制」＋「实测出处」**：
  ① 单 task 非自产来源上限 = 3（1 份声明输入 + 1 次检索 + 1 次读取）；
  ② 同一 task 内第二次检索调用**硬失败**（操作键重复 ⇒ `conflicting source registration`）；
  ③ `minimum_sources: 10` 的口径与上述机制**不相容**（量级差 3 vs 10）；
  ④ 三条判据维度**无产品调用方**（`SCHEMA_VALID` / `TEST_PASSES` / `POLICY_COMPLIANT`）。
- **D-3 「待重新设计」要写清「重新设计需要什么」**，但**不**把它写成本 GOAL 的任务清单——
  它属**需拍板**项（改合约/接判据维度），按 escalation 归用户。
- **D-4 只读既有记录**：正文的事实与出处**引用** GOAL-011 的 `W-P`/`W-Q`/`W-R`、
  `PLAN-20260922-138` 的「实测结论」与 `E-3`/`E-4`/`E-5`、`RECHECK-20260923-139` 的 W 列表；
  **不重跑**那些实验（它们已登记在案，重跑不增加信息且要花真实出网）。
- **D-5 不加判据、不改门禁**：本 PLAN 只有一份文档 + 登记；验证靠
  `tools/docs_consistency_check.py`（backtick 引用可解析）+ 治理 `validate.py` + m0 的 framework 组。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | 独立记录在位且状态明确 | `docs/roadmap/PATH_B_REFUTATION_RECORD.md` 存在，开头即写明**已否证 / 待重新设计** | **通过**：`scratch/verify_goal012_c4.py` 的 A 组 3 条（文件在位 + 状态措辞 + 「不是待办功能/也不是已完成」），当前树全绿 |
| AC-2 | 四项事实**逐条**覆盖（各带机制 + 出处） | 正文有 ①…④ 四条编号事实，每条含机制描述与仓库内出处（文件路径 / 脚本名 / E 编号） | **通过**：①…④ 四条各带「机制」与「实测出处」（`PLAN-20260922-138` 的 `E-3`/`E-4`/`E-5` + 两个 `scratch/` 探针脚本名）；B 组 6 条判据（四条事实 + 出处引用 + `**实测出处**` 恰 4 处）全绿 |
| AC-3 | GOAL-011 的登记**原样保留** | `git diff` 对 `GOAL-20260922-011-*.md` 与 `PLAN-20260922-138-*.md` **零改动** | **通过**：`git diff --stat HEAD -- …` 与 `--stat ea06b77 -- …` **两条都空**；`W-P`/`W-Q` 原文抽样仍在；`PLAN-138` 的 `status: BLOCKED` 未动（`scratch/goal012-c4-readonly.txt`） |
| AC-4 | 本 GOAL 残余节登记该记录路径 | GOAL-012 的残余节新增一条指向该文件 | **通过**：`R-B1` 行已改为指向 `docs/roadmap/PATH_B_REFUTATION_RECORD.md`（含四项事实摘要与「原样保留」句）；C/D 组判据绿 |
| AC-5 | 引用可解析 | `python tools/docs_consistency_check.py` exit 0（backtick 引用的仓库路径都存在） | **通过**：`DOCS-CHECK PASS: 6 deterministic checks` |
| AC-6 | 门与治理 | m0 23/23 + `validate.py` 绿（本 PLAN 只加文档，`python/tests` 计数不变） | **通过**：m0 终局 `PASS: profile=m0; 23 deterministic checks`（`scratch/goal012-c4-m0.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行；`python/tests` **4411 passed / 19 skipped / 0 failed**，与 cycle 3 同数 ⇒ 只加文档未动套件计数）；`.cursor/skills/governance-check/scripts/validate.py` ⇒ `Cursor 治理验证通过`；出站 `judged 787; blocked 8`，**8 条全部**来自故意探针 `tests/architecture/python/test_default_egress_guard.py` |

## 实施清单

- [x] **WP1** 载体与投影：本 PLAN + `ALL_PLAN` 行 + GOAL `child_plans`（同一提交）。
- [x] **WP2** 记录正文：`docs/roadmap/PATH_B_REFUTATION_RECORD.md`（四项事实 + 关系声明 + 待重新设计）。
- [x] **WP3** 登记：GOAL-012 残余节指向该文件；迭代日志写明载体。
- [x] **WP4** 门与收口：`docs_consistency_check` + m0 + `validate.py`；`RECHECK-20260923-146`（PASS）+ GOAL 回写
  （EC-04 状态、迭代日志第 4 行、状态历史、`memory_entries`）。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | (B) 的前提被否证的四项事实已在案 | `PLAN-20260922-138` 的「实测结论」§被实测否证 + `E-3` / `E-4` / `E-5` |
| E-2 | GOAL-011 的登记原文 | `GOAL-20260922-011` 的 `W-P`（来源数口径与机制不相容）/ `W-Q`（三条判据无产品调用方）/ `W-R`（接线未派发过） |
| E-3 | PLAN-138 的 BLOCKED 与撤回 | `PLAN-20260922-138`（`status: BLOCKED`）与 GOAL-011 cycle 10 的撤回记录 |
| E-4 | 本 PLAN 的产物 | 落盘：记录文件 + 登记 + `ALL_PLAN` 行；两道独立检查 `python tools/docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`、`.cursor/skills/governance-check/scripts/validate.py` ⇒ `Cursor 治理验证通过`；只读证明 `scratch/goal012-c4-readonly.txt`；两棵树复检 `scratch/verify_goal012_c4.py`（当前树 `checked=24 failures=0`；基线树 `ea06b77` `checked=24 failures=14`，14 条红**全部**是本 cycle 新增面：记录文件 / 子 PLAN / GOAL 登记不在基线树） |

### E-5（本 PLAN 核对时发现并处置的一处既有记录缺陷）

复检 cycle 3 的独立脚本时**在当前树上复跑**得到 `checked=24 failures=1`，与 `RECHECK-145` 记的
「当前树 24/24」不符。根因可证明：该脚本的 B2 把判据文件的一句实现当**字面量**钉住
（`"Digest.of_bytes(content)"`），而判据文件在 cycle 3 的 amend（`919ad2c` → `6ccdf46`，
m0 的 50 行/函数门禁驱动）里被**纯重构**成一行式 ⇒ 记录里的数字是在 amend **之前**测的。
处置：B2 改判**语义**（四个 token，强度只增不减），复测当前树 24/24、基线树 `31dfbd4` 6 红
⇒ **同结论同数字**；`RECHECK-145` 追加「勘误」节（保留原行 + 标明测量时点）；
事实进工程记忆 `MEM-20260923-112`。**被检的判据文件一字未改。**

## 影响报告

- **Domain / API / schema**：无。
- **产品代码 / 测试 / 协议 / 合约 / 门禁**：**零改动**（本 PLAN 只有文档与登记）。
- **CI / workflow**：不改。
- **安全 / 凭据**：零出网、零凭据读取、零 live 调用。
- **上游版本影响**：无。
- **下一项任务**：EC-05（可选前端：实验读面在真实数据下渲染）或 EC-06（收口重检）。

## 状态历史

- 2026-09-23：derive（EC-04 子计划）。定案 D-1…D-5 写死；记录正文与登记在本 cycle 落地。
- 2026-09-23：记录正文 + 投影 + 登记落盘（WP1–WP3）；`docs_consistency_check` 与 `validate.py`
  双绿；两棵树复检 `scratch/verify_goal012_c4.py`（当前树 24/24、基线树 `ea06b77` 14 红＝全部新面）。
  核对中另查出 `RECHECK-145` 的一处**时序错误**（数字测于 amend 之前）并就地勘误（E-5）。

## 收口（cycle 4）

- **复检**：`RECHECK-20260923-146` = **PASS**（独立脚本两棵树成对 + 逐条 AC + 只读证明 + 门）。
- **状态**：`DONE`；`latest_recheck` 指向该复检（仓库相对路径）。
- **工程记忆**：`MEM-20260923-112`（复检脚本不要钉被检对象的中间形态字面量；amend 之后必须复测）。
- **零改动确认**：本 PLAN 未改任何产品代码、协议、合约、测试、门禁、策略面；未改 GOAL-011 与
  `PLAN-20260922-138`（`git diff --stat` 两次为空）。零出网、零凭据读取。
