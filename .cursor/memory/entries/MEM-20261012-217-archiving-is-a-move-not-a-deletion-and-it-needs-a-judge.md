---
id: MEM-20261012-217
title: "归档是「搬运」不是「删除」：活跃面瘦身必须挂一条判据（不漏 / 不重 / 可解析），否则它会退化成两种坏形态"
status: ACTIVE
created_at: 2026-10-12
updated_at: 2026-10-12
scope: repository
confidence: 0.9
review_after: 2027-04-12
source_plans:
  - .cursor/plans/tasks/PLAN-20261012-425-mainline-archive-and-the-history-is-kept-checkable.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261012-426-mainline-archive-and-the-history-is-kept-checkable.md
supersedes: []
tags: [archive, drift, append-only, judged-convention, mainline, press-testing]
---

## 做了什么

战役宪章 `MAINLINE.md` 的两段累积物（进展记录 / 修订记录）是**只追加**的，跑了 26 个
GOAL 后到 **182 行 / 84 KB**。本轮按「活跃面只保留最近 3 条、更早的移入区间归档」
瘦身（→ 116 行），并**给这条惯例挂判据**
（`tests/tooling/test_mainline_archive_is_continuous.py`：不漏 / 不重 / 归档可解析）。

## 为什么这样做

「只追加」保证了历史不被**改写**，但**不保证历史不被丢**。没有判据时，「归档」会退化成
两种坏形态 —— 而两者**静态看都是绿的**：

1. **顺手删掉**：移出的行谁也没留下 ⇒ 历史不可复核；
2. **留而不断**：归档文件在，但内容与声明对不上（少搬 / 多搬 / 搬重）⇒ 读者以为历史在，实际缺一块。

⇒ 判据把三件事变成机器可检：归档文件存在且非空；**活跃面保留 + 归档收录 ≥ 原文行数**
（基线取 `git show HEAD:<charter>`，取不到就**点名失败**而不是跳过）；同一条记录
**不得两处并存**。

**为什么用「行数上界」而不是「逐行集合相等」**：同日同 GOAL 可有多行（修复 cycle
就是这种形态：`| 2026-10-09 | GOAL-20261008-040（…修复 cycle） | … |`），集合相等会把
正当的重复形态判红。行数上界 + 「不重」两条合起来足以抓「少搬」与「搬重」。

## 踩到的三个坑（全部由按压 / 判据当场抓住）

| 坑 | 症状 | 修法 |
| --- | --- | --- |
| **路径重复计数** | 三段指针各提同一归档一次 ⇒ `_archive_paths` 返回 3 个同一路径 ⇒ 21 行算成 63 ⇒ **删一行也不判红**（P1 首跑假绿） | 按相对路径**去重** |
| **正则过严** | 进展行要求 id 后紧跟 `\|` ⇒ 漏判修复 cycle 的既有形态 `\| 日期 \| GOAL-id（说明） \|` | 去掉尾部 `\|` 要求 |
| **保留端取错** | 表是**最新在前**，脚本取 `rows[-3:]`（末 3 = **最旧**）⇒ 留下最旧 3 条、搬走 23 条较新的 | 取 `rows[:3]`；预算块同向 |

第 1、3 两处**只有按压能抓到**（静态看判据是绿的）——「按压先验形态」纪律的又一次兑现。

## 怎么做与复现

```bash
# 三读数：原文 / 保留 / 归档
uv run --frozen --no-sync python -B -c "
import importlib.util
spec = importlib.util.spec_from_file_location('j','tests/tooling/test_mainline_archive_is_continuous.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
charter, orig = m._charter_text(), m._original_charter_text()
paths = m._archive_paths(charter)
arch = sum(len(m._progress_keys(p.read_text(encoding='utf-8'))) for p in paths)
print('baseline', len(m._progress_keys(orig)), '| kept', len(m._progress_keys(charter)), '| archived', arch)
"

# 两条按压 + 逐字节复原
uv run --frozen --no-sync python -B scratch/mainline_archive_press.py
```

## 适用边界

- **行数上界 ≠ 逐行集合相等**：同日同 GOAL 可有多行（修复 cycle 就是这种形态），
  集合相等会把正当重复判红 ⇒ 行数上界 + 「不重」合起来抓「少搬 / 搬重」，
  **抓不住「搬错行」**；那一面由搬运脚本的 `sha256` 留档承担。
- 归档**只追加**：新归档写成**新文件**（文件名带区间），不改旧归档。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

- `PLAN-20261012-425` / `RECHECK-20261012-426`；
- 判据：`tests/tooling/test_mainline_archive_is_continuous.py`（4 例）、
  宪章判据 `test_mainline_program_is_intact.py`（8 例）；
- 归档：`.cursor/plans/goals/archive/MAINLINE-2026-10-12-through-26.md`（112 行 / CR=0）。
