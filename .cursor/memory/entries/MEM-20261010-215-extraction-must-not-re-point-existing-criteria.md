---
id: MEM-20261010-215
title: "为守规模门而做的**搬迁**会打断钉住旧位置的判据 —— 既有断言集必须「判关系，不判位置」，否则搬迁即假红"
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
scope: repository
confidence: 0.95
review_after: 2027-04-10
source_plans:
  - .cursor/plans/tasks/PLAN-20261010-383-goal-046-ec01-04-program-human-gate.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261010-384-goal-046-ec01-04-program-human-gate.md
supersedes: []
tags: [scale-gate, assertions, refactor, closeout-assets, goal-046]
---

## 做了什么

GOAL-046 为了让 `program_runner.py` 守住 **450 行硬上限**，把失败重试面的计数口径
（`_RETRY_CLAIM_KINDS` / `_retry_face_state`）**搬到**新模块 `program_retry.py`。
搬迁**行为等价**，但**当场撞红两处既有判据**：

- `tools/goal041_closeout_assertions.py` 的两条（`ec02-both-claim-kinds-counted` /
  `ec02-claim-is-counted-when-not-landed`）**按文本**在 **runner 文件里**找实现
  ⇒ 实现一走，两条**假红**；
- 而**GOAL-043 立的判据**（`test_every_named_assertion_set_reports_no_negative_on_this_tree`）
  **当场把它们报了出来** —— 这正是该判据存在的理由（「断言集在本树上有判负 ⇒ 资产坏了」）。

**处置**：把这两条改成**判关系不判位置**（`_retry_face_text` 同时看执行面与拆出去的判定面；
断言要求的仍是「两类认领都在计数面里」与「未落库的认领也计入」这两件**事**）。

## 为什么这样做

**「搬迁」是最容易被低估的破坏性动作**：它不改行为，所以代码评审会放过它；但它会打断
**任何按位置写死的判据**。本仓的两条纪律在这里叠在一起：

1. **规模门强迫搬迁**（450 行硬上限 ⇒ 功能增长必然导致拆分，这是**常态**不是例外）；
2. **判据不许因搬迁而假红**（否则每次拆分都要「顺手改判据」—— 而那正是
   `MEM-20261009-210` 警告的「改既有判据」高风险动作）。

⇒ 结论：**判据从一开始就要写成「关系」而不是「位置」**。写死位置 = 给未来每次搬迁预留一次
「要么改判据、要么破规模门」的两难。

**为什么这条比 GOAL-043 的那条更值得单独记**：GOAL-043 记的是「**文本锚点**随被引**代码**演进失效」
（`index("<调用签名>")`）；本条记的是「**文件位置**随**重构**失效」（`"... " in runner`）。
两者同族但触发方式不同：前者的触发是**别人的代码**变了，后者的触发是**你自己的搬家**。

## 现象

```
# 搬迁后（实测）
FAILED tests/tooling/test_closeout_verifiers_run_their_own_assertions.py::
       test_every_named_assertion_set_reports_no_negative_on_this_tree
  ['goal041_closeout_assertions.py: [ec02-both-claim-kinds-counted,
                                     ec02-claim-is-counted-when-not-landed]']
# 而产品测试全绿（5138 passed）—— 假红只在**资产面**出现
```

## 根因

| 层 | 事实 |
| --- | --- |
| 规模门 | `program_runner.py` 有 450 行硬上限 ⇒ 新功能必须**拆出去** |
| 判据面 | `goal041` 的两条按**文本**在 `runner` 变量（= 那个文件）里找实现 |
| 落差 | 判据写的是「**在那个文件里**」而不是「**在这件事上**」 |
| 兜底 | GOAL-043 的「零判负」判据把假红**变成可见**（若无它，这条会静默腐烂） |

## 怎么做与复现

**修法（判关系）**：

```python
#: 实现**可能落点**（执行面 / 已拆出去的判定面）—— 逐条找，而不是钉死一处。
_RETRY_FACE_SOURCES = (
    "packages/application/run_orchestration/program_runner.py",
    "packages/application/run_orchestration/program_retry.py",
)

def _retry_face_text(root, runner):
    return "\n".join([runner] + [_text(root, rel) for rel in _RETRY_FACE_SOURCES])
```

断言仍要求**同一件事**（两类认领都在计数面里 / 未落库的认领也计入），只是**不再要求它在哪个文件**。

**复现（合成）**：把任一被文本钉死的实现搬到另一个文件 ⇒ 该断言集立刻出现「判负」，
而产品测试全绿 —— 即「假红只在资产面」。

**设计规则（写判据时）**：

- 要判「**某件事成立**」时，用 **AST / 语义面**（函数名、字段名、集合成员）；
- 只有当**位置本身**是契约的一部分（如「入口必须在 `tools/two_tree_recheck.py`」）时，
  才写死路径 —— 且**同时登记**「搬迁需要同轮改这条判据」。

## 适用边界

- 适用于：本仓一切**多文件实现面**的断言（尤其是「某段逻辑在哪个文件」这种形态）；
  以及任何**为了规模门而拆分**的重构（本仓高频动作）。
- **不**适用于：位置**就是**契约的判据（`IN_SCOPE` 清单、两树入口、规范页点名 —— 那些
  「在哪个文件」本身就是被声明的事）。
- **不声称**：本条不保证所有既有断言都已「判关系」；只保证**本轮撞到的两条**已修，
  且「零判负」判据会让**将来**的同类假红**可见**（不会静默腐烂）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261010-383-goal-046-ec01-04-program-human-gate.md` | 搬迁动因（规模门）与修法 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261010-384-goal-046-ec01-04-program-human-gate.md` | 独立复检：「零判负」判据的当场捕获 + 修后全绿 |
| repository | `tools/goal041_closeout_assertions.py`（修前 / 修后） | 按位置写死的两条与「判关系」的修法 |
| repository | `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | GOAL-043 立的「零判负」判据（把假红变可见） |
