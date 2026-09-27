---
id: MEM-20260928-154
title: "话术判据的引用豁免只认引号字符：用反引号列出被禁词仍是肯定式宣称（会被判红）"
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
scope: repository
confidence: 0.9
review_after: 2027-03-28
source_plans:
  - .cursor/plans/tasks/PLAN-20260928-211-goal-022-ec01-two-tree-recheck-entry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260928-212-goal-022-ec01-two-tree-recheck-entry.md
supersedes: []
tags: [wording-gate, record-face, quoting, goal-022, record-hygiene]
---

## 做了什么

GOAL-022 建档首轮，全量记录面判据里 `test_reproducibility_wording.py` 判红一次。
被点名的行是「**不得**出现肯定式的 `完全可复现` / `fully reproducible` …」这句的**续行**：

```text
   `fully reproducible` / `fully model-reproducible`（口径词是「**可重复配置**」）。
```

它在语义上显然是**否定式列举**（上一行有「不得」），但判据**按行**判：

- `_has_negation(line)` 只看**本行**有没有否定标记 ⇒ 续行没有 ⇒ 不豁免；
- `_is_quoted(line, start, end)` 只看词**紧邻**的字符是否属于
  `_QUOTE_OPEN = 「“‘"'` / `_QUOTE_CLOSE = 」”"'’` ⇒ **反引号 `` ` `` 不在集合里**。

⇒ 用**反引号**包裹被禁词，**不被**当成「引用」，仍按肯定式宣称判红。
把同四个词改成 `「」` 包裹（或把否定标记放到**同一行**）后即绿。

## 为什么这样做

- **判据的豁免面是「引用」与「否定」，不是「看起来像代码」**。反引号在 Markdown 里
  是代码跨度，在这个判据里**没有**语义；把它当引号是一种**想当然**。
  这类误判的代价不是「判据说错了」，而是写记录的人**以为**自己已经按引用写、实际没有 ⇒
  红出现在**别人**的提交里（本次就是本地记录面判据在推送前抓到）。
- **按行判意味着跨行排版会改变判定**。把一个否定句拆成两行，第二行就变成肯定式。
  ⇒ 列举被禁词时，**否定标记与词必须在同一行**，或用 `「」` 逐词包裹（后者更稳）。

## 怎么做与复现

```bash
# 记录面判据（扫 .cursor/plans；scratch/ 不在扫描面内）
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_reproducibility_wording.py -q
```

判红时的读法：失败消息会给出 `文件:行号: 该行原文` ⇒ 按**行号**去看那一行有没有
否定标记、词的紧邻字符是不是 `「」`/`"`。**不要把判据改成认反引号**——那是放宽
（`fix_policy` 明令禁止）。

## 适用边界

- 适用于**一切**会扫 `.cursor/plans` / `docs` / `tests` 的**话术类**判据：
  它们的豁免面是「**引用**」与「**否定**」两种**行级**形态，不是「看起来像代码」。
- **不适用于**其它判据的引用面：例如治理的链接扫描认的是路径字符串本身，
  与引号无关；`credential_audit` 认的是**值的形态**，也与引号无关。
- 本条的结论**依赖判据的实现细节**（`_is_quoted` 看相邻字符）。若该判据将来改成
  认 Markdown 代码跨度，本条需要复核——它的失效触发器就是那次改动。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260928-211-goal-022-ec01-two-tree-recheck-entry.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260928-212-goal-022-ec01-two-tree-recheck-entry.md`
- 实测：GOAL-022 建档首轮 `test_reproducibility_wording.py` 判红（续行无反引号豁免）
- 相关：[[MEM-20260926-145]]（同为「记录写入本身会被判据扫到」的形态）
