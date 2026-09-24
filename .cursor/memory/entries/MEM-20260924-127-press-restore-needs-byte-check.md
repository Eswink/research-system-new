---
id: MEM-20260924-127
title: "按压还原要逐字节核对：`.gitattributes` 归一化让 `git diff` 看不见行尾偏差"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.95
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-157-policy-surface-difference-set-audit.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-159-policy-surface-difference-set-audit.md
supersedes: []
---

## 做了什么

本仓的「按压」手法（注入一个坏值 ⇒ 判据判红 ⇒ 还原 ⇒ 判据复绿）用 Python 文本模式
`Path.write_text()` 做注入与还原。Windows 上这会**把行尾写成 CRLF**；而本仓
`.gitattributes` 是 `* text=auto eol=lf` ⇒ `git diff` 把 CRLF/LF 归一化后**看不到差异**。

实测偏差：

```bash
git show HEAD:examples/config/skills.yaml > /tmp/skills_head.yaml
cmp /tmp/skills_head.yaml examples/config/skills.yaml   # ⇒ differ: byte 8, line 1
tr -dc '\r' < examples/config/skills.yaml | wc -c       # ⇒ 45（HEAD 版本 0）
git diff --stat examples/config/skills.yaml             # ⇒ 空（什么都看不出来）
```

## 为什么这样做

「按压后 `git diff` 为空 = 逐字节还原」这条**常见但错误**的推论，在本仓会被行尾归一化
无声破坏。按压的价值全在「还原是真的」——若还原其实改了文件（哪怕只是行尾），
后续 m0 / CI 读到的就不是原来那棵树，反证的说服力也随之消失。

## 怎么做与复现

- 注入/还原一律用 `write_text(text, newline="")`（或二进制读写），别依赖默认文本模式。
- 还原证据要**两条一起给**：`git diff --stat`（内容）+ **逐字节核对**
  （`cmp` 与 `git show HEAD:<path>` 比对，或 CR 字节计数）。
- 数行尾**字节**用 `tr -dc '\r' | wc -c`；本机 MSYS 的 `grep -c $'\r'` **读数不可信**
  （对 CRLF 文件报 0）。
- 已经写坏的文件用 `git checkout -- <path>` 恢复（先确认 `git diff` 无内容差异，
  再恢复字节）。

## 适用边界

- 只对**本仓**（`.gitattributes` 为 `* text=auto eol=lf` + Windows 工作树）成立；
  换仓库先看 `.gitattributes`。
- `git checkout --` 会丢弃工作树改动 —— 只在 `git diff` 已证明**无内容差异**时用它恢复行尾；
  并发写者正在改同一个文件时不要用。
- 新增文件不受此影响（没有 HEAD 版本可比对），但仍然建议写成 LF 并在 `git add` 后
  核对暂存 blob（`git show :<path> | tr -dc '\r' | wc -c` 应为 0）。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-157-policy-surface-difference-set-audit.md`（WP5 证据段）
- `.cursor/plans/rechecks/RECHECK-20260924-159-policy-surface-difference-set-audit.md`（第四节）
- `scratch/goal014_c3_press.py` / `scratch/goal014-c3-press-final.txt` /
  `scratch/goal014-c3-press-restore-note.md`
