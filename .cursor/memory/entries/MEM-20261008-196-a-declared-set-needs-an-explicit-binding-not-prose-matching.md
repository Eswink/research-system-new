---
id: MEM-20261008-196
title: "声明集与源码的绑定要写成**字段**，不是「关键词出现在散文里」——拿措辞当绑定，换一种写法就误判"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.92
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-315-goal-033-ec03-resume-coverage-declaration.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-316-goal-033-ec03-resume-coverage-declaration.md
supersedes: []
tags: [declared-set, source-reconciliation, prose-matching, ghost-reference, goal-033, plan-315]
---

## 做了什么

GOAL-033 cycle 3 要把「续跑覆盖度」写成**声明集**并与入口源码对账。两版写法与各自的失败形态：

| 版本 | 绑定方式 | 失败形态 |
| --- | --- | --- |
| 首版 | 判据拿**中文关键词**（`服务` / `preflight`）去匹配声明条目的散文 | 英文口径与中文情形描述对不上 ⇒ **判红**，但红的是判据自己的形态（换个措辞就会**误判**） |
| 定版 | `DeclaredCase.source_literals` **字段**显式绑定 | 漏认领 / 重复认领 / 绑定的字面量在源码里不存在 ⇒ **各判红**，且换了措辞不影响 |

同一轮还有第二个自查：首版 `evidence` 里我凭印象写了 **7 个用例名**，**全部不存在**
（真实名是 `test_a_rebuild_from_the_frozen_body_finishes_the_remaining_work` 一类）——
存在性判据（AST 找函数定义）一次全抓出。

## 为什么这样做

**声明集的两条硬要求**（都要机械化，缺一条就退化成散文）：

1. **每条声明的落点必须可机械核对**：`evidence` 写成 `文件::用例名` 并**真的去文件里找**；
   光写「见某某测试」等于没绑定。这条同时是**受判面非空**的证明（抓出 7 个幽灵引用）。
2. **声明与源码的对应关系要显式**：把「这条声明对应对面源码的哪个可枚举物」写成**数据字段**
   （`source_literals`），不要用自然的词句匹配去推。词句匹配的两种误判方向都要防：
   - **误判成覆盖**：声明里碰巧出现某个词 ⇒ 以为对上了；
   - **误判成缺失**：换了措辞 ⇒ 以为覆盖丢了（本轮的实例）。

**边界**：只能对**可枚举**的东西做这种对账（字面量、枚举值、状态名）。**拼装**出来的东西
（异常路径的 `前缀 + 异常名`）没有穷尽集合 ⇒ 在注释里写明该情形**按语义归属**而不按字面量，
不要假装它被穷尽覆盖。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B -m pytest \\
  tests/tooling/test_resume_coverage_declaration_matches_source.py -q   # 6 passed
uv run --frozen --no-sync python -B scratch/goal033-cycle3-press.py
# 期望：P1_RED exit=1 1 failed（幽灵条目）/ P2_RED exit=1 3 failed（规模+面+绑定）
#       RESTORED True（sha 归因）/ FINAL_MATCHES_BASELINE True
```

按压 P2 的脚本自身也踩过一次坑：**字符串切片删条目**会被条目内多行 `reason=(...)` 的
`)` 骗到 ⇒ 产出**语法错** ⇒ `exit=2`（收集错，**不是**判红）。用 **AST 定位**该调用的
行范围再删。`exit=2` 与 `exit=1` 要分开读（前者是「判据根本没跑」，后者才是「判据判红」）。

## 适用边界

- 适用于「声明 ↔ 实现/源码」的成对核对（覆盖度矩阵、能力承接面、事件词表、状态迁移表）。
- **不**适用于无法枚举的对端（拼装字符串、动态生成的标识）。
- 本条的 `source_literals` 是**单向绑定**（声明 → 对端可枚举物）；反向（对端新增而声明没跟）
  由同一条判据的反向断言承担：对端字面量若在声明集里查无认领 ⇒ 判红。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-315-goal-033-ec03-resume-coverage-declaration.md`
- `.cursor/plans/rechecks/RECHECK-20261008-316-goal-033-ec03-resume-coverage-declaration.md`
- 留档：`scratch/goal033-cycle3/press-matrix.log`
