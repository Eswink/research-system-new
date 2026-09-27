---
id: MEM-20260927-152
title: "按压脚本改写文件必须用二进制读写：pathlib.write_text 在 Windows 会把 LF 转 CRLF ⇒ 「逐字节复原」复核会（正确地）判不一致"
status: ACTIVE
created_at: 2026-09-27
updated_at: 2026-09-27
scope: repository
confidence: 0.95
review_after: 2027-03-27
source_plans:
  - .cursor/plans/tasks/PLAN-20260927-209-goal-021-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md
supersedes: []
tags: [press-restore, byte-exact, windows-line-endings, goal-021, ec-05]
---

## 做了什么

GOAL-021 收口复检脚本（`scratch/goal021-ec05-closeout-recheck.py`）首次运行时，
**按压面的「逐字节复原」判 FAIL**。归因：按压/复原用的是
`pathlib.Path.read_text()` + `write_text()`（文本模式）——Windows 上会把文件里的
**LF 统一写成 CRLF** ⇒ raw `sha256` 变了 ⇒ 复核判**不一致**。

**修法**：改用 **`read_bytes()` / `write_bytes()`**，只在字节层做 replace。
改后同一脚本 **28/28 通过**（含逐字节复原）。

## 为什么这样做

- 按压纪律要求「**逐字节**复原」。文本模式读写会让这个要求**在 Windows 上不可能满足**
  （哪怕内容一个字符都没变）。用文本模式 = 复核永远 FAIL（或永远不敢判）。
- **危险的反向情形更重要**：若复核用 `git diff` 而不是 raw `sha256`，这次差异会被
  **静默吞掉**——本仓 `.gitattributes` 是 `* text=auto eol=lf`，git 归一化后
  **报「无改动」**（实测：`git diff --numstat` 0 行，`git diff --quiet HEAD` 通过）。
  ⇒ **`git diff` 不足以证明「逐字节复原」**；raw `sha256` 才是判据。
  这也解释了本工作树里若干文件常年显示 ` M` 但 `numstat` 为 0（CRLF 伪改动）。

## 怎么做与复现

```bash
# 收口复检（含按压 + 逐字节复原复核）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec05-closeout-recheck.py

# 复核 raw 字节 vs git 归一化后的 blob（两者本可不同）
sha256sum services/api/middleware.py            # 工作树 raw
git show HEAD:services/api/middleware.py | sha256sum   # git 归一化后
```

**判定**：按压脚本的复原复核**必须**用 raw `sha256`；若发现不一致，
先怀疑**读写模式**，再怀疑内容。

## 适用边界

- 该结论适用于**任何**「改文件 → 复原 → 证明复原」的脚本（按压矩阵、代管脚本、
  探针）；对**只读**脚本无影响。
- 若某文件**本来就**是 CRLF（本仓混存），文本模式读写可能**恰好**不改变它；
  ⇒ 「文本模式下是否出问题」取决于该文件当前的行尾状态，**不能**靠经验假定。
- `git diff` 仍适合判「**内容**有没有变」（内容层面），但**不适合**判「字节是否复原」。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260927-209-goal-021-closeout-recheck.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md`
- 取证脚本：`scratch/goal021-ec05-closeout-recheck.py`（首次运行即暴露该问题）
- 相关：`MEM-20260927-149` / `MEM-20260927-151`（同为「判据/复核自身形态」类教训）
