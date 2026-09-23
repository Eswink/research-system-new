---
id: RECHECK-20260923-146
plan_id: PLAN-20260923-146
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-verify-script + root-agent-goal-012-ec04
baseline_ref: ea06b77
checked_head: 830a72c
---

# RECHECK-20260923-146 — 路径 (B) 的独立否证记录（GOAL-012 EC-04 / PLAN-146）

## 检查范围

本 PLAN 的产物是**一份文档 + 几条登记**，所以复检要判的是三件不同的事，**不采信本 cycle 的自我陈述**：

1. **记录本身**独立成文、状态不含糊、四项事实**逐条**覆盖且各带出处
   （`scratch/verify_goal012_c4.py`，只读 / 只用标准库 / 不 import 仓库代码）。
2. **它是只读记录**：GOAL-011 与 `PLAN-20260922-138` 在两棵树之间**逐字节同指纹**，
   产品/协议/合约/测试/门禁件同样同指纹（本 cycle 只加文档）。
3. **门与治理**：m0 + `docs_consistency_check` + `validate.py`。

## 检查结果

### 一、独立复检脚本（两棵树成对）

| 树 | 结果 | 说明 |
| --- | --- | --- |
| **当前树**（`830a72c`） | `checked=24 failures=0`（exit 0） | 24 条判据全绿：A 记录在位与状态 3 条 + B 四项事实与出处 6 条 + C 只读历史 3 条 + D 登记/未动件 12 条 |
| **基线树**（`ea06b77`） | `checked=24 failures=14`（exit 1） | 14 条红**全部**是本 cycle 新增面（记录文件不存在 / 子 PLAN 不存在 / GOAL 里查不到登记）；**C 组 3 条与 D 组的未动件 9 条在基线树上也绿** ⇒ 本 cycle **零产品改动**、GOAL-011 与 PLAN-138 **一字未改** |

### 二、验收条件（逐条）

| # | 条件 | 实测 |
| --- | --- | --- |
| AC-1 | 独立记录在位、状态明确 | `docs/roadmap/PATH_B_REFUTATION_RECORD.md` 存在；开头即「**已否证（refuted）/ 待重新设计（needs redesign）**」并写明「**不是待办功能，也不是已完成**」 |
| AC-2 | 四项事实逐条（机制 + 出处） | ①单 task 非自产来源上限 3 ②第二次检索调用硬失败（`conflicting source registration`）③`minimum_sources: 10` 与机制不相容 ④`SCHEMA_VALID`/`TEST_PASSES`/`POLICY_COMPLIANT` 无产品调用方；**每条**含「机制」+「实测出处」（`PLAN-20260922-138` 的 `E-3`/`E-4`/`E-5` 与两个 `scratch/` 探针脚本名）；`**实测出处**` 恰 **4** 处 |
| AC-3 | GOAL-011 的登记原样保留 | `git diff --stat HEAD -- <GOAL-011 / PLAN-138 / RECHECK-139>` **空**；`git diff --stat ea06b77 -- <GOAL-011 / PLAN-138>` **空**；`W-P`/`W-Q` 原文抽样仍在；`PLAN-20260922-138` 的 `status: BLOCKED` 未动（`scratch/goal012-c4-readonly.txt`） |
| AC-4 | GOAL-012 残余节登记记录路径 | `R-B1` 行已指向 `docs/roadmap/PATH_B_REFUTATION_RECORD.md`，含四项事实摘要与「`W-P`/`W-Q`/PLAN-138 的 BLOCKED **原样保留**」句，并写明「引用时仍按已否证 / 待重新设计，不得读成待办功能」 |
| AC-5 | 引用可解析 | `python tools/docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks` |
| AC-6 | 门与治理 | m0 ⇒ **`PASS: profile=m0; 23 deterministic checks`**；`validate.py` ⇒ `Cursor 治理验证通过` |

### 三、「只读」的独立证明（`scratch/goal012-c4-readonly.txt`）

1. 相对 `HEAD` 与相对**基线树** `ea06b77`，`GOAL-20260922-011` / `PLAN-20260922-138` /
   `RECHECK-20260923-139` 的 `git diff --stat` **两次都是空**。
2. `W-P`（来源数口径与机制不相容）与 `W-Q`（三条判据无产品调用方）在 GOAL-011 正文里**原文可查**。
3. `PLAN-20260922-138` 的 frontmatter 仍为 `status: BLOCKED`——本 cycle **没有**「顺手修好」它，
   也没有把它读成待办功能。

### 四、门与套件

| 门 | 结果 |
| --- | --- |
| m0 | **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c4-m0.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行） |
| `python/tests` | **4411 passed / 19 skipped / 0 failed**（与 cycle 3 同数 ⇒ 只加文档，套件计数未变） |
| `docs_consistency_check` | `DOCS-CHECK PASS: 6 deterministic checks`（也是 m0 的 framework 组内一条） |
| `validate.py` | `Cursor 治理验证通过` |
| 出站 | `egress guard: judged 787; blocked 8`——**8 条全部**来自故意探针 `tests/architecture/python/test_default_egress_guard.py`（逐条点名核对）；本 cycle **零真实出网、零凭据读取、零 live 调用** |

### 五、本 cycle 顺带查出并处置的**既有记录缺陷**（勘误，不是自夸）

复检 cycle 3 的独立脚本（`scratch/verify_goal012_c3.py`）时**在当前树上重跑**，得
`checked=24 failures=1`，与 `RECHECK-145` 记的「当前树 24/24」不符。根因**可证明**：

- 判据文件在 cycle 3 的 amend（`919ad2c` → `6ccdf46`，m0 的 **50 行/函数**门禁驱动）里被**纯重构**：
  内容 digest 从两行并成一行；`git diff 919ad2c 6ccdf46 -- tests/e2e/test_ec03_experiment_evidence_chain.py`
  逐字可见这次并句；
- 该脚本的 B2 当时把 `"Digest.of_bytes(content)"` 这个**中间形态的字面量**当判据 ⇒
  RECHECK-145 里那一行数字是**在 amend 之前测的**（先测、后 amend、未复测就落记录）。

处置：B2 改判**语义**（四个 token 同时在场，强度**只增不减**），复测
**当前树 `24/24`、基线树 `31dfbd4` `6 红`** ⇒ 与原记录**同结论同数字**；
`RECHECK-145` 追加「勘误」节（**保留原行** + 标明测量时点 + 复测结果）；事实进 `MEM-20260923-112`。
**被检的判据文件一字未改**，结论（cycle 3 的 PASS）不受影响。

## 诚实边界

- 本复检**验证的是记录与登记**，**不**重跑 (B) 的四项实验：那四项事实是 `PLAN-20260922-138`
  的实测结论与 GOAL-011 的登记，本记录**引用**它们（重跑不增加信息，且其中包含真实出网调用）。
  这一点在记录正文的「诚实边界」节已写明。
- 本记录**不**声称 (B) 永远不可行：否证的是「**不改判据/不改机制**即可靠多次调用凑够来源数」
  这一条具体前提；「重新设计需要什么」的 5 条列在记录里，属**需拍板**项，**不在**本 GOAL 授权内。
- 本 cycle 未改任何产品代码、协议、合约、测试、门禁或策略面（两棵树指纹为证）。

## 结论

**PASS**。路径 (B) 的否证已落成**独立、可引用、不含糊**的记录：状态是「已否证 / 待重新设计」，
四项实测事实逐条覆盖且各带机制与出处，与 GOAL-011 的 `W-P`/`W-Q`/`W-R` 及 `PLAN-138` 的 BLOCKED
**原样保留**的关系已写明；本 GOAL 的残余节登记了该路径；两道文档/治理检查与 m0（23/23）全绿；
两棵树成对复检证明本 cycle **零产品改动、零改写历史**。
