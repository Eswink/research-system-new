---
id: MEM-20261015-223
title: "收口资产的「名副其实」不只是声明==加载：**自洽地加载上一轮**会让自有断言静默退役，而恒绿的自我判词会替它盖章"
status: ACTIVE
created_at: 2026-10-15
updated_at: 2026-10-15
scope: repository
confidence: 0.95
review_after: 2027-04-15
source_plans:
  - .cursor/plans/tasks/PLAN-20261015-485-goal-079-ec05-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261015-486-goal-079-ec05-self-bootstrap-closeout.md
supersedes: []
tags: [closeout, recheck, assertions, own-ness, self-reference, goal-079]
---

## 做了什么

修掉 `tools/verify_goal078_closeout.py` 的一处**同族缺陷第二例**：它的 `ASSERTIONS`
常量与 `_load_assertions()` **双双**写着 `goal077_closeout_assertions.py`。后果三条
（逐条实测）：

1. 「**声明 == 实载**」**成立** ⇒ `test_closeout_verifiers_run_their_own_assertions.py`
   的首版判据放行；
2. `goal078_closeout_assertions.py` 的 **29 条自有断言从未运行** —— 在 GOAL-078 的
   收口复检归档（73 条判词）里这些名字**零命中**（逐条 grep）；
3. 该验证器自己的 `self-loads-its-own-assertions` 判词**恒绿**：它问的是
   「`'goal077_closeout_assertions.py"'` 这个串在不在加载函数里」，而写的名字
   **恰好就是当时实载的**那个。

处置：① 两处改回自己那份（真跑 29 条、本树 0 判负）；② 自指判词改为**按本文件名推**
应载文件名（写死那版在构造上不可能再通过）；③ 家族判据加**第三项对拍**
（`loaded == expected`）+ 一条「自洽但非己有」的反向反例。

## 为什么这样做（三条可复用）

- **「声明 == 加载」不是「名副其实」**：一致性是**两处互相同意**，名副其实要求**同指自己**。
  一个**自洽地**复制上一轮下来的错误在一致性面**永久隐身** —— 这与 [[declared-but-never-constructed-is-a-dead-seam]]
  同族：**有人声明、无人校验**。
- **自我判词写死「证据串」= 恒绿**：判词问「某个字符串在不在」而该字符串**正好就是缺陷
  现场**（上一轮文件名）⇒ 判词替缺陷盖章。自指判词必须**从本文件推**应然值
  （`Path(__file__).name` → 编号 → `goal0NN_closeout_assertions.py`），再与实载对拍。
- **归档里的「条数」不能证明「是谁的判词」**：GOAL-078 归档 73 条、全绿、判词行像模像样 ——
  但那份是**别人**的断言集。判「这份归档属于哪个断言集」要靠**断言名的在场**，不是条数。

## 怎么做与复现

```bash
# ① 症状：归档里自有断言名零命中（对比两个名字集）
grep -c "ec01-the-seam-is-in-tree" .cursor/plans/goals/evidence/GOAL-20261014-078-verdict-current.txt   # ⇒ 0
grep -c "ec01-the-assembler-is-in-tree" .cursor/plans/goals/evidence/GOAL-20261014-078-verdict-current.txt  # ⇒ 1（上一轮那份）

# ② 修复后：本树真跑自己那份、0 判负
uv run --frozen --no-sync python -B tools/verify_goal078_closeout.py --root . --verdict-only | grep -c "^PASS"   # ⇒ 68（= 标准 18 + 自有 29 + 记录面 21）

# ③ 按压：两处锚点同时改回上一轮 ⇒ 家族判据红 + 自指判词 FAIL，逐字节复原
uv run --frozen --no-sync python -B scratch/goal079c5_press.py
```

**判据形态**（`test_closeout_verifiers_run_their_own_assertions.py`）：三项对拍
`declared == loaded == _expected_assertion_file(relative)`；反例三条 ——
「声明 A 实载 B」、「自洽但非己有」、「断言集抛异常」都必须报红。

## 适用边界

- 适用于：本仓一切「外部断言集 + 加载器」形态的收口资产（GOAL-031 起，现 49 个验证器）；
  以及任何**自指判词**（判词里带被判对象的字面名）。
- **不**适用于：旧一代验证器（`LEGACY_INLINE`：断言内联、无外部断言集）⇒ 没有可对拍面，
  那一代是否存在别种同族问题**未普查**（如实登记，不假装覆盖）。
- **不**适用于：`tools/` 之外。`tools/` 的整体射程仍受 `IN_SCOPE` + `LEGACY_OUT_OF_SCOPE`
  的分区纪律约束（95 条旧 lint 错误是历史资产，不因本条而解封）。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261015-485-goal-079-ec05-self-bootstrap-closeout.md` | 缺陷读数 / 三处修复 / 按压设计 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261015-486-goal-079-ec05-self-bootstrap-closeout.md` | 独立复检：零命中 / 修复后真跑 / 两树 PASS |
| repository | `tools/verify_goal078_closeout.py` | 缺陷现场与修后形态（自指判词按文件名推） |
| repository | `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 第三项对拍 + 三条反例 |
| evidence | `.cursor/plans/goals/evidence/GOAL-20261015-079-c5-ownness-press.txt` | 按压两处红 + 逐字节复原 |
| memory | [[closeout-assets-must-run-their-own-assertions]] (MEM-212) | 第一例（声明 A 实载 B）；本条是第二例（自洽但非己有） |
