---
id: MEM-20260924-124
title: "一个 FAIL 可以有多个独立来源：放行策略前先枚举 fail 的全部来源，否则判据不可达"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.9
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-155-policy-surface-consistency-main-trunk.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-157-policy-surface-consistency-main-trunk.md
supersedes: []
---

## 做了什么

GOAL-014 EC-01 的目标是「真实控制面对 `sort_analysis_v1` 的 preflight **不再是 `FAIL`**」。
按 `W-A` 的登记，唯一原因是 `evidence.read` 落 `default_effect: DENY`。**实测发现不止一个**：
走产品入口（`services/api/run_execution.execution_inputs()`，`preflight_override=None`）
拿到的 `FAIL` 报告里有**三条 ERROR、分属两个独立来源**：

1. `[POLICY_DENIED] phase:review: policy denied capability evidence.read: used default policy effect`
   —— `W-A`，本 GOAL 的授权面；
2. **两份 `TASK_CONTRACT_MISSING`**（`sort_analysis_execution` / `sort_analysis_review`）
   —— `sort_analysis_v1.yaml` 的 phase 引用了这两份契约，而**出厂目录
   `examples/contracts/task_contracts.yaml` 里没有它们**；它们只存在于测试夹具
   `tests/api/run_fixtures.py` 的 `replace_catalog_with_pins()`（运行期 `setdefault` 注入）。

而 `sort_analysis_v1.yaml` 是**产品面可选模板**（`services/api/routers/protocol_drafts.py`
的 `_TEMPLATE_SOURCES` 第 1 条 =「Sort 分析（2-phase 参考）」）⇒ 产品出厂就带着一个
**在真实控制面上必然预检失败**的模板。只放行策略**不足以**让判据达成；
EC-02 的真实 run 也会死在冻结前。

## 为什么这样做

「一个已知原因」很容易被当成「唯一原因」。`W-A` 是**如实登记**下来的（GOAL-012 cycle 1
就点了名），此后 GOAL-013 原样承继 —— 两轮的记录都**没有错**，但**都不完整**：
它们只覆盖了**策略**那一个来源。如果直接按登记去放行然后宣布达成，
判据会**仍然红**，而红的原因会被误读成「放行没生效」。
⇒ 正确顺序是：**先跑一次真实求值、枚举 fail 的全部来源，再决定要动哪些面**。
本仓的可复用手法：拿产品入口（而不是手工拼上下文）跑一次，把 `findings` **逐条**打出来。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B scratch/goal014_c1_probe.py
```

### 归因纪律（cycle 1 纠错轮实测，代价真实）

**同一个检查的判词块会同时列出多条错误** —— 只读第一条就归因，会把「自己的原因」
盖在「环境原因」下面。实测：`framework/validate_bundle` 判红时，本地判词块里
`R-F3`（并发写者的 gitignored scratch 文档被读成本地链接）与**我自造的
`output_schema` 名不存在**两条**逐行并列**；我只读了第一行就写下「唯一未绿 = R-F3」，
并把它推送了出去 ⇒ CI 判红**同一个检查**（CI 检出**没有 `scratch/`** ⇒ `R-F3` 在那边
不可能成立 ⇒ 那个归因**自相矛盾**）。

两条可复用手法：

1. **归因前把整个判词块读完**，逐条列出，不要停在第一条；
2. **用一条独立面交叉验证环境归因是否自洽**：本仓最方便的是 CI（检出里没有
   `scratch/`）。「这个红交付物只在本地存在」这类归因，一旦 CI 也红在同一检查上，
   就说明归因错了 —— **不要**再去调整环境叙述，回到判词块里找自己那条。

另一个同类陷阱：给 `TaskContract` 补 `output_schema` 时**不要自造名字** ——
`framework/validate_bundle` 要求 `schemas/<name>.schema.json` **存在**，
而本仓既有口径是「schema 描述适配器**真实登记**的内容，不是编出来的形状」
（`real_research_deliverable_v1` 的说明写死了这句）。合约可以**共用**已有的 schema
（`console_demo_deliverable` / `real_retrieval_deliverable` 共用是既有先例）。

要点：

1. **走产品入口**，不要手工拼 `PreflightContext`：装配由 `deps.preflight_override`
   的**在场与否**决定（`execution_inputs()` 内部分岔），手工拼会把「哪一套装配」变成
   脚本的方言。协议参数用**裸文件名**（`sort_analysis_v1.yaml`），项目 id 用**已注册**的
   `example-project`（未注册会 404 在 `merged_project_settings`）。
2. **逐条打印 `findings`**（`code` / `severity` / `subject_ref` / `message`），
   按 `code` 分组数来源；只看 `status` 会漏掉「同一 `FAIL` 两个来源」。
3. 分离来源后再逐条处置；**只处置授权内的那一条**，其余的**具名登记**（本次落成
   PLAN-155 的 `authorization.ref` 扩展段 + 回退面）。

同批实测的两个附带事实（可复用）：

- **`python/tests` 用例数归因法**：改判据/夹具后要能**逐条解释**用例数的差。
  本次 4413 → 4418（skipped 18 不变），差 **+5** = 新增的正好 5 条判据 ⇒ 无隐藏变化。
  数不上就说明改了别的东西 —— 拿上一轮的 m0 日志（`scratch/goal013-c6-m0.log`）当基线。
- **本机 as-is m0 = 22/23 的形状**：唯一未绿项 `framework/validate_bundle` 会被
  并发写者的 gitignored `scratch/` 文档判红（纯文本链接扫描把正则字面量读成本地链接）。
  与 GOAL-013 cycle 6 的 as-is 跑法**同形**（同一项、同一原因）⇒ 归因可复现，
  不必每轮重新论证；**但未转绿前不得声称本地全绿**。

## 适用边界

- 适用于**本仓**的 preflight 判据与策略面改动；手法（枚举 fail 来源、用例数归因）
  可跨项目复用，具体命令与路径名不通用。
- 「先枚举来源」在**判据可达性**上是必要条件：只要有一个未处置的来源，
  `status` 就不会变——但**枚举本身不构成处置授权**。本仓的授权边界由 GOAL 的
  `authorization.ref` 定；枚举出授权外的来源时**登记、不自行放宽**。
- 用例数归因法只对**静态收集**的测试有效；`pytest` 的 skip/parametrize 变化会让
  数字动，归因前先确认 skipped 数是否也变了（本次 skipped 不变才敢下「差 = 新增数」）。
- `R-F3` 那条环境事实**只对本机成立**：CI 检出无 `scratch/`，不要把它读成 CI 现象。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-155-policy-surface-consistency-main-trunk.md`（derive 与执行）
- `.cursor/plans/rechecks/RECHECK-20260924-157-policy-surface-consistency-main-trunk.md`（复检与判词）
- `.cursor/plans/goals/GOAL-20260924-014-policy-surface-consistency.md`（`F-9` 的登记处）
- `scratch/goal014_c1_probe.py`（枚举手法）、`scratch/goal014-c1-criterion-red.txt`（改前判词）、
  `scratch/goal014-c1-m0.log`（本机 m0 终态与用例数）、`scratch/goal013-c6-m0.log`（上一基线）
