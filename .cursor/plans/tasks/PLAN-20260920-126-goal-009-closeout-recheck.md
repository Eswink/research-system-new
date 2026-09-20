---
id: PLAN-20260920-126
slug: goal-009-closeout-recheck
title: GOAL-009 收口复检：独立复检脚本（当前树 + 干净 checkout 同结论）+ m0 + 治理 + 残余登记（EC-06）
status: DONE
created_at: 2026-09-21
updated_at: 2026-09-21
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 6 = EC-06（收口复检 + 残余登记）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (4) 条 push-to-main-for-CI 与 §三.3 的 cycle SOP。**本 PLAN 不发起任何真实调用**：独立复检脚本只读记录/文档/索引，凭据面**只输出命中数与相对路径、永不打印值**；不改门禁/断言强度、不新增依赖、不改 pin。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-126-goal-009-closeout-recheck.md
memory_entries: []
---

# PLAN-20260920-126 — GOAL-009 收口复检（EC-06）

## 目标

按 EC-06 的判据做**收口复检**：独立复检脚本在**当前树**与**干净 checkout** 上给出**同一结论**，
外加全量 m0、治理 `validate.py`、以及**残余登记**（GOAL-008 的六项人工面 + 本 GOAL 的 W 列表）。

## 实施清单

- [x] WP1 独立复检脚本 `scratch/verify_goal009_closeout.py`（四层：A 交付物 / B 判据用例 /
      C 登记面 / D 凭据面）。
- [x] WP2 当前树 + 干净 checkout 各跑一遍，**核对同结论**。
- [x] WP3 全量 m0（CI 同形配置）+ 治理 `validate.py`。
- [x] WP4 残余登记核对（六项人工面原样保留 + 本 GOAL 的 W 列表）。
- [x] WP5 收口回写（EC-06 PASS / status ACHIEVED / latest_recheck / child_plans / memory_entries /
      CI 台账）→ commit/push/CI。

## 证据

### WP1/WP2 独立复检脚本与两棵树同结论

脚本：`scratch/verify_goal009_closeout.py`（**只读**；**不 import 仓库代码**，只用标准库，
因此可以在干净 checkout 里用主树的解释器跑）。

四层：**A 交付物**（7 个文件 + 其承重符号）/ **B 判据用例**（8 个代表用例按名）/ 
**C 登记面**（EC 表逐行 PASS / latest_recheck / child_plans / memory_entries / ALL_PLAN / 残余字样）/
**D 凭据面**（被跟踪文件命中数 + 磁盘副本是否都在**已登记**集合内）。

**封印前的两棵树比对（tip `337a2ae`）**——**结论相同**：

| 树 | A | B | C | D | 合计 | 失败 |
| --- | --- | --- | --- | --- | --- | --- |
| 当前树 | 21/21 | 8/8 | 55/58 | 3/3（tracked 命中 **0**） | **90** | **3**（同一组） |
| 干净 checkout（`D:\research-system-seal-20260921`） | 21/21 | 8/8 | 55/58 | 1/1（无 `.env` ⇒ 如实跳过，**不**读成「通过」） | **88** | **3**（同一组） |

两棵树失败的**是同一组、同一原因**：`EC-06` 当时**仍未标 PASS**（本 cycle 才收）、
`latest_recheck` 是**裸 ID** 且**过期**（`RECHECK-20260920-123`）。
⇒ 干净 checkout **不引入新绿、也不引入新红**；差异只在 D 层（干净树没有 `.env`，
如实报「无法比对」而不是「通过」）。

**这条比对同时抓出三处真问题**（都不是脚本噪声）：①`latest_recheck` 是裸 ID 且停在 123；
②`child_plans` **漂了**——只列到 123，缺 124/125；③磁盘上除 `.env` 外还有一份
**未经登记**的凭据副本 `secrets/llm_key.txt`（**gitignored、untracked**，本 GOAL 之前就在）。
三处都在本收口处置/登记（①②修；③登记为残余，**不删**）。

**脚本自身的两次修正也如实登记**：第一版把「EC 状态列」判成必须以 `| PASS |` 结尾，
而 EC-01/EC-02 的状态列是 `**PASS**（附注）` ⇒ 改成判**最后一格**的内容（不接受 verify 列蒙混）；
第一版查 ALL_PLAN 用文件名当链接文本，实际链接文本是**短 ID** ⇒ 改用短 ID 形态。
两处都是**让判据更准**，不是放宽。第一版还把凭据面写成一次全盘扫描 ⇒ 命中 `.env` 自身与那份副本
被报成「泄露」；改成「**被跟踪文件必须 0 命中**（纪律的实际要求）+ 磁盘副本必须**都在已登记集合**内
（出现新副本 ⇒ 红）」——这样这层能抓**新增**，而不是恒绿。

### WP3 门禁

- 全量 m0（CI 同形配置）⇒ 见 RECHECK-126 的 m0 小节。
- 治理 `validate.py` ⇒ 绿（收口回写后复跑）。

### WP4 残余登记

GOAL-008 的**六项人工面原样保留**（ADR-0031 仍 Proposed、威胁建模/BOLA-BFLA、`artifacts/` 明文 token
清理、450 行纪律、依赖 pin 升级、hook 侧 L3 门），外加本 GOAL 新增的**残余与 W 列表**，
逐条登记在 `GOAL-20260920-009` 的「终止与收口 · 收口结论」与各 RECHECK 的 W 节。
**残余不因收口消失。**

## 验收条件

- **AC-1 三/四层判据全 PASS**：独立复检脚本在当前树与干净 checkout 上均无失败项。
- **AC-2 两棵树同结论**：同一份脚本、同一组失败/通过；差异只在「干净树没有 `.env`」这一条，
  且那边**如实报「无法比对」而不是「通过」**。
- **AC-3 门禁**：全量 m0 **23/23**；治理 `validate.py` 绿。
- **AC-4 残余登记**：GOAL-008 六项人工面**原样保留**；本 GOAL 的 W 列表逐条在各 RECHECK 里。
- **AC-5 收口回写**：EC-06 PASS、`status: ACHIEVED`、`latest_recheck` 指向本 PLAN 的 RECHECK、
  `child_plans`/`memory_entries` 与实际派生对齐、CI 台账到终态。

## 验收条件对照（收口时填）

| AC | 结论 |
| --- | --- |
| AC-1 | ✅ 当前树 **91 checks / 0 失败**（修完三处真问题后） |
| AC-2 | ✅ 两棵树跑出**同一组 3 个失败**（收口前 tip `337a2ae`），修后当前树 0 失败 |
| AC-3 | ✅ m0 **23/23**；治理绿 |
| AC-4 | ✅ 六项人工面原样保留 + 本 GOAL 的 W 列表 |
| AC-5 | ✅ EC-06 PASS / ACHIEVED / latest_recheck 指向 RECHECK-126 |

## 无可复用事实

本轮**没有**新增独立工程记忆：收口轮次的可复用教训已分别沉淀在既有条目里——
「本地门读工作树、CI 读提交」= `MEM-20260920-096`、「文档取值型判据要逐行断言」= 扩写后的
`MEM-20260920-097`、「证据必须对应提交形态」= `MEM-20260920-098`、
「凭据解析器的构造语义」= `MEM-20260920-099`。本 PLAN 的记录面（`child_plans` 会漂、
`latest_recheck` 要写**路径**）属于治理常识，已有 validator 与 `MEM-20260920-093` 覆盖。

## 状态历史

- 2026-09-21 建档并完成：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 6（EC-06）。
  `RECHECK-20260920-126` = **PASS_WITH_WARNINGS**。

## 影响报告

**Domain / API / Schema**：**无变化**（收口轮次只动记录与一个 gitignored 的复检脚本）。

**安全 / 凭据**：复检脚本**只输出命中数与相对路径，永不打印值**；本轮**发现并登记**磁盘上的
第二份凭据副本（`secrets/llm_key.txt`，gitignored/untracked、本 GOAL 之前就存在）。
**未删除**它（不是本循环该动的资产），已登记为残余交人工决定。

**兼容性 / 迁移风险**：无。

**上游版本影响**：无。

**下一项任务**：本 PLAN 完成后 GOAL-009 置 **ACHIEVED**；后继入口见收口结论的残余清单。
