---
id: MEM-20260923-120
title: "复检脚本的 ROOT 必须由**调用目录**决定；用 `Path(__file__).parents[1]` 会让「两棵树各跑一遍」退化成同一棵树跑两次"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.95
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-152-live-page-read-face-batch-three.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-153-live-page-read-face-batch-three.md
supersedes: []
---

## 做了什么

GOAL-013 的收口判据要求「独立复检脚本在**当前树**与**干净 checkout** 上各跑一遍，两棵树同结论」。
`scratch/verify_goal013_c{1,2,3}.py` 三个脚本初版都写：

```python
ROOT = Path(__file__).resolve().parents[1]
```

从干净 checkout（`git worktree`，如 `/tmp/g013c2`）里调用**主树路径**的脚本时
（`python /d/research-system/scratch/verify_goal013_c2.py`），`__file__` 指向**主树**
⇒ `ROOT` 仍是主树 ⇒ **所谓「两棵树各跑一遍」实际是主树跑了两次**。
前两个 cycle 的记录因此把「同一棵树跑两次」当成「两棵树同结论」：数字一致不是巧合，
是必然；而当时主树恰好处于「尚未收口」状态，让干净树该有的那几条红**看起来**也合理，
缺陷就此隐身。

cycle 3 发现并修掉：

```python
# 复检**哪棵树**由**调用目录**决定（VERIFY_ROOT 可覆盖）
ROOT = Path(os.environ.get("VERIFY_ROOT") or Path.cwd()).resolve()
```

修好后重跑三棵树（实测，2026-09-23）：

| 脚本 | 主树 | 干净 checkout |
| --- | --- | --- |
| `verify_goal013_c1.py` | `checked=219 failures=0` | `checked=218 failures=3`（`@f45d6ec`） |
| `verify_goal013_c2.py` | `checked=33 failures=0` | `checked=32 failures=3`（`@08daf1e`） |
| `verify_goal013_c3.py` | `checked=47 failures=0` | `checked=46 failures=4`（`@94850f8`） |

干净树多出的红**内容**都是「尚未收口」那一类（`PLAN-x not DONE` / `still has unchecked boxes` /
`recheck missing`；cycle 3 还多一条 `EC-02 is not marked PASS` —— EC 状态回写本身属收口提交）
⇒ **前两个 cycle 的结论仍然成立**，但**证据方法此前是错的**，记录已按本节数据更正。

## 为什么这样做

「两棵树同结论」的全部价值在于**第二棵树是独立副本**：它能排除「结论是被主树的工作树状态
或未提交改动喂出来的」。ROOT 指错时这个价值**归零**，而输出看起来完全正常
—— 这是最难自查的一类复检缺陷：**判据没坏，判据指向的树错了**。

## 怎么做与复现

- 复检脚本一律用调用目录定 ROOT（或显式 `VERIFY_ROOT`），**不要**用 `__file__` 的父目录。
- 自查：两棵树的 `checked=` 数字**至少有一个不同的可能**；若两棵树输出**逐字相同**，
  先怀疑 ROOT，而不是先庆贺一致。可用 `git -C "$PWD" rev-parse --short HEAD` 打印被检树。
- 复现旧缺陷：把 `ROOT` 写法改回 `Path(__file__).resolve().parents[1]`，
  在 `/tmp/<worktree>` 里调用主树脚本 ⇒ 它报的是主树的结论。

## 适用边界

- 只在「同一份脚本跑不同工作树」的场景下咬人。若脚本被**复制**进目标树再运行
  （`cp scratch/v.py /tmp/tree/ && cd /tmp/tree && python v.py`），旧写法反而碰巧正确
  —— 所以这不是「旧写法永远错」，而是「旧写法让结论依赖于调用方式」。**统一成调用目录**，
  两种调用都对。
- `VERIFY_ROOT` 只用于显式指定被检树；它不影响脚本的只读性与标准库约束。
- 相关：[[MEM-20260923-119-live-read-face-ownership-and-fixture-anchoring]]（同 cycle 的
  「先确认对象是谁」教训，同一族：**判据指向的对象必须真的是它声称的那个**）。

## 来源

- `scratch/verify_goal013_c1.py` / `-c2.py` / `-c3.py` 的 `ROOT` 注释与三个脚本的两棵树实测输出。
- `RECHECK-20260923-151` / `-152` 第一节的更正说明、`RECHECK-20260923-153` 第一节。
