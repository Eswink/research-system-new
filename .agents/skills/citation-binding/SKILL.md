---
name: citation-binding
description: Use when work involves source numbering or citation adequacy — injecting `[n]` marks into a prompt, building a reference list, rendering retrieval context, or measuring whether citations are sufficient. Covers single-authority numbering, ineligible ids that must not consume a number, and readings that must never become a verdict. Not for judging whether a specific citation supports a specific sentence, and not for picking thresholds without a real corpus.
---

# Citation Binding

交付物里「第 n 条来源」必须只有**一个**编号权威；充分性只能给**读数**，不能给判词。这两条都是被真实缺陷逼出来的，不是风格偏好。

## 硬规则

1. **编号只有一个构造点**：`numbered_records(identifiers)`（`packages/application/deliverable/references.py`）按「去重后首次出现顺序、从 1 起」编号。汇编器 `reference_table` 与提示词 `render_retrieval_prompt` 都调它。
2. **不可引用条目不占号**：`ids[]` 形状的记录标 `[not citable]`（可见、有位置、不编号）。给它们编号会让其后每一条**整体错位**——错位不会让任何判据变红，只会让模型引错。
3. **读数不是判据**：`measure_citation_sufficiency(sections)` 缺省 `enforce=False`，三阈值全部 `None`。读数写进交付物时必须带限定语（`readings, not a judgement`），不得改写成「引用充分」。
4. **阈值必须有语料来源**：填任何阈值前先有标定语料，并把来源写进 `CALIBRATION_SOURCES`（键与常量名逐字一致）；`uncalibrated_thresholds()` 会点名无来源的阈值。

## 流程

1. 先确认「谁在数编号」。全仓搜 `enumerate(` 与 `\[{`，凡是把来源序号写成字面量的地方都是候选漏点。
2. 新增渲染点时**只调** `numbered_records`，不复制去重循环。两处各写一遍去重能让判据两边都绿而两边不一致（重复项在一侧的过滤条件变化只影响那一侧）。
3. 交付物脚注里的每个数必须**逐项等于**函数返回值（同一来源），并写清「读数」二字；把读数升级成判词属于越界。
4. 引用语法正则只允许存在一份。`manuscript.CITATION_PATTERN` / `manuscript_quality._CITATION` / `citation_sufficiency` 必须同形（后者从 `manuscript_quality` 导入，不写第三份 `re.compile`）。

## 反证臂

- 把读数临时硬编码成常量 ⇒ 必须**恰好**预期条数（本仓实测 3 条）判红 ⇒ 复原。若不红，说明读数不是从字节算出来的。
- 给一条 `ids[]` 记录编号 ⇒ 其后每条编号整体 +1 的判据必须红。
- 在新增渲染点里自己数编号并故意差一 ⇒ 提示词与 References 的逐条相等判据必须红。

## 陷阱

- **两处都绿但两边不一致**：同源之前，判据只能证明「各自自洽」。修法是让缝在结构上不存在，不是加一条对比判据。
- **把「有读数」当成「已判定充分性」**：`NOT_JUDGED` 清单里「引用集是否足以支撑每一条主张」这一项仍然在，删它才是缺陷。
- **零语料下的数值**：本仓真实手稿数为 0 时，任何具体阈值都是编的。宁可留 `None` 并显式记为残余，也不要先填后补来源。
