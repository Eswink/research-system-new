---
id: MEM-20260928-155
title: "按压「记录面判据」的形态是往被扫描目录注入一条违规记录（不是改判据代码）；且要防「空集合假绿」"
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
scope: repository
confidence: 0.9
review_after: 2027-03-28
source_plans:
  - .cursor/plans/tasks/PLAN-20260928-213-goal-022-ec02-declared-paths-need-their-own-evidence.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260928-214-goal-022-ec02-declared-paths-need-their-own-evidence.md
supersedes: []
tags: [press-testing, record-face, judgement-shape, goal-022, ec-02, vacuous-green]
---

## 做了什么

GOAL-022 EC-02 的判据（`tests/architecture/python/test_declared_recheck_paths_have_evidence.py`）
判的是**记录**（`.cursor/plans/rechecks/*.md` 的 `verify_paths`），不是产品代码。
这类判据的按压**不能**靠「改判据代码」，也不能只靠合成夹具 —— 前者压的是自己、
后者压不到**实时扫描面**。实际采用的**两段按压**：

1. **实时注入**：往 `.cursor/plans/rechecks/` 写一条真实形态的违规记录
   （`slug` 收口、`created_at` 在受判起点之后、两路**共用同一份证据**）
   ⇒ `test_no_obligated_closeout_recheck_has_a_declaration_gap` **1 failed**
   （报文点名「共用同一份证据」）。补齐为两条独立证据 ⇒ **9 passed**；删除注入记录 ⇒ 复原。
2. **中性化判据自身**：在 `declared_path_problems` 首行插 `return []`
   ⇒ **5 failed, 4 passed**（五条「必须判红」的断言全线判红）⇒ 证明夹具断言**非空洞**。
   恢复后 raw `sha256` 一致 ⇒ 9 passed。

**复原的判据形态**：注入记录**删除后**，用「目录文件数回到基线 + 残留计数为 0 +
`git status --short .cursor/plans/rechecks/` 为空」三条一起证明**既有记录字节未动**
（不是靠 `git diff` 单独作证，承 `MEM-20260927-152`）。

## 为什么这样做

- **记录面判据的失效模式是「没有对象可判」而不是「判错了」**。EC-02 的受判集合
  = 「建档日之后的新收口复检」，而当时**一条都没有** ⇒ 判据**全绿但是空真**。
  空真与假绿不同：它没有说谎，但**也没有证明任何事**。
  ⇒ 必须补三条**非空证据**：①扫描面真的产出记录（历史 4 条被识别）；
  ②注入一条违规就判红；③中性化判据就判红。三者齐备，「当前全绿」才可读作
  「**判据在位且有效**」而不是「**恰好没有对象**」。
- **注入的是「真实形态」的记录**：字段与命名都按既有约定写全（含 `plan_id` / `status` /
  `result` / `owners`），这样它走的是**与真实记录完全相同**的解析路径。
  只写一个残缺 fixture 会绕过解析面 ⇒ 按压打偏。
- **注入物必须**当场删除**，且复原要有独立证据**：`.cursor/plans/rechecks/` 下的记录
  会被治理 `validate.py`、话术判据、凭据审计一起扫；残留会污染**别的**判据，
  表现为**别处**判红（极难归因）。

## 怎么做与复现

```bash
# ① 基线：目录文件数
ls .cursor/plans/rechecks/ | wc -l

# ② 注入一条真实形态的违规记录（slug 以 closeout-recheck 结尾、created_at 在受判起点之后、
#    两条路的 evidence 指向同一份归档）后跑判据：
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_declared_recheck_paths_have_evidence.py -q
#    ⇒ 期望：1 failed（test_no_obligated_closeout_recheck_has_a_declaration_gap）

# ③ 删除注入物并复核复原：文件数回到基线、残留 0、既有记录 git status 为空
rm -f .cursor/plans/rechecks/RECHECK-<注入物>.md
git status --short .cursor/plans/rechecks/
```

## 适用边界

- 适用于**一切判「记录文件结构化字段」的判据**（`verify_paths` 这类声明式义务）。
- **不适用于**判产品代码行为的判据 —— 那些按压的形态是破坏被守护的行为本身。
- 「注入真实形态记录」要求**记录格式已稳定**（本仓有 `parse_frontmatter` 与治理校验）。
  格式未定时，注入物本身可能在解析层就被拒 ⇒ 压到的是解析而不是语义。
- 空真与假绿的区分**依赖有人真的去看「受判集合有多大」**；本条的配方把它变成
  **三条可复跑的断言**，但**仍然不能**保证「受判集合该有多大」这件事本身是对的
  （那是条款设计面）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260928-213-goal-022-ec02-declared-paths-need-their-own-evidence.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260928-214-goal-022-ec02-declared-paths-need-their-own-evidence.md`
- 实测：注入 ⇒ `1 failed`；补齐 ⇒ `9 passed`；删除 ⇒ 185→184、残留 0、`git status` 空
- 相关：[[MEM-20260925-141]]（判据要用语法结构判，不要用文本巧合判）、
  [[MEM-20260927-152]]（逐字节复原的证据必须是 raw `sha256`）、
  `MEM-20260927-153`（条款写明的每一路都要各自留档 —— 本判据正是它的机械化）
