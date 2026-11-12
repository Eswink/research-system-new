---
id: RECHECK-20261112-111
slug: panel-grounding
title: GOAL-111 复检 —— 面板判词从「某个模型认为」升级为可核验的结构断言
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-12
updated_at: 2026-11-12
plan_id: PLAN-20261112-111
parent_goal: GOAL-20261111-111
owners:
  - root-agent
verify_paths:
  - packages/application/deliverable/panel_grounding.py
  - packages/application/deliverable/manuscript_panel.py
  - packages/application/deliverable/manuscript_quality.py
  - tests/application/deliverable/test_panel_grounding.py
  - tests/application/test_manuscript_panel.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
---

# RECHECK-20261112-111

## 复检范围

GOAL-20261111-111 的五条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 判词 | `REFUTED` 必须指向正文里**真实存在**的句子 | **不**宣称「论证成立」；射程仍是「某模型认为 + 那句话确实存在」 |
| `NOT_JUDGED` | 五项**逐字不动** | 不宣称叙述质量已判；判定表一字不动 |
| 面板 | 仍 **advisory**（不产生 `Decision`） | 不宣称面板参与验收 |
| 阈值 | 引用充分性阈值仍全 `None` | **不给任何阈值拍板**（`escalation_triggers`） |

## 检查结果

### EC-01 判词引用面（PASS）

`panel_grounding.py`：正文切成**编号句子** `S1…Sn`（确定性；空正文 ⇒ 空元组，不猜）；
`grounding_of` 判一条 rationale 是否**落在正文的字节上**——两条通路（`S<n>` 在范围内 /
引用的 `"…"` 片段是正文真实子串）。

**两种「不成立」分得开**（判据断言 `outcome` 与 `missing` **都不同**）：
`EMPTY_RATIONALE`（模型没写理由）≠ `NOT_GROUNDED`（写了但指不到正文）。

**切句同源**：`SENTENCE_SPLIT` 与 `manuscript_quality._SENTENCE_SPLIT` **同一个正则字面量**
（判据按字面量比对，不按变量名）；不同源会让「编号」与确定性判据看的句子错位。
判据 **19 passed**。

### EC-02 `REFUTED` 必须被指向（PASS）

`ground_verdict(verdict, manuscript_text)`：**只约束 `REFUTED`**。
指向不成立 ⇒ 降级 `AMBIGUOUS` + `UNGROUNDED_REFUTED:` + **保留模型原话**（`model said: …`）
+ 逐条点名缺什么。`SUPPORTED` / `AMBIGUOUS` / `PANEL_UNAVAILABLE` **原样返回**
（身份级 `is` 断言）。

**为什么只约束 `REFUTED`**：`SUPPORTED` 说的是整段成立、`AMBIGUOUS` 说的是判不出来——
两者都**不指句子**。把约束铺到三态会把「模型说支持」也变成必须引句子，那是**收紧射程**
而不是可核验化。

### EC-03 四条判据（PASS）

| 要求 | 判据 | 读数 |
| --- | --- | --- |
| ① 正例指向真实句子 | `test_panel_grounding.py::TestGrounding::test_a_named_sentence_inside_range_is_grounded` + `test_manifest_panel` 侧 | 绿（`GROUNDED(2)`） |
| ② **反证**指向不存在的句子 | `test_an_out_of_range_sentence_is_not_grounded_and_named` + `test_an_unsupported_refutation_is_degraded_and_named` | 绿（点名 `S99 is outside the manuscript (1..3)`） |
| ③ **反证** rationale 空 | `test_an_empty_rationale_is_its_own_outcome` + `test_an_empty_rationale_refutation_is_degraded` | 绿（**独立一类**，与 ② 点名不同） |
| ④ 面板仍 advisory | `test_grounding_does_not_reach_into_decisions` + `test_the_panel_still_only_constructs_findings` | 绿（源码面不触 `Decision`） |

### EC-04 `NOT_JUDGED` 五项不动 + §7 补句（PASS）

- `NOT_JUDGED` **五项逐字未动**：收口断言集拿**原文元组**逐字比对，且 `len == 5`；
  `tests/application/test_manuscript_quality.py` 全绿；
- `docs/architecture/MANUSCRIPT_QUALITY.md` §7 **补一段**：判词现在可核验（`S<n>` / 真实子串 /
  指不到就降级），**但射程仍不充分**，`NOT_JUDGED` 五项与判定表**一字未动**；
- 阶梯「报告」行：追加「面板判词本身可被反驳」，**旧射程声明「这段写得好不好仍无判据」
  逐字保留**（本轮不宣称它消失）。

### EC-05 收口资产与宪章记账（PASS）

- `tools/verify_goal111_closeout.py` + `tools/goal111_closeout_assertions.py`
  ⇒ **69 PASS / 0 FAIL**；断言集**重放**引用面与降级（不只查文件存在）；
- 登记 `_VERIFIERS` 与 `IN_SCOPE`；宪章程序表 / 阶梯 / 进展 / 修订按实际改。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证臂 | 结果 |
| --- | --- | --- |
| `test_panel_grounding` | `S99` 越界 ⇒ 降级；空 rationale ⇒ 降级（与越界点名不同）；引用不存在的句子 ⇒ `NOT_GROUNDED`；无名无引 ⇒ 判负 | 红 |
| `test_goal111_ladder_report_scope` | 六行任一出现「面板判词本身可被反驳」⇒ 红；报告行丢掉旧射程声明 ⇒ 红 | 红 |
| 收口断言集 | `NOT_JUDGED` 任一项改一个字 ⇒ 红；`len != 5` ⇒ 红；`SUPPORTED` 被降级 ⇒ 红 | 红 |

## 结论

**PASS_WITH_WARNINGS**。五条 EC 全 PASS；两条残余（`W-1` 摘录与全文的编号可能错位 /
`W-2` 只认双引号引用）、两条未覆盖（`U-1` 未用真实模型跑过一次降级 / `U-2` 提示词未要求
写 `S<n>` ⇒ 真实降级率可能很高）、两条声称边界（`R-1` 判词可核验 ≠ 叙述质量已判 /
`R-2` 面板仍 advisory）逐条明写。

**本轮一处方法论收获**：**把「不可核验」变成「可核验」不需要判定内容对错**——
只需要要求判词**指向被评对象的一个可复算位置**。降级路径（而不是丢弃）是关键：
它保留了模型原话，同时让「它指不到」成为**可读事实**。
