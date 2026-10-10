---
id: MEM-20261010-212
title: "收口复检资产必须**跑自己的**断言：声明面 ≠ 加载面会静默架空整套断言；文本锚点会随被引代码演进崩溃"
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
scope: repository
confidence: 0.95
review_after: 2027-04-10
source_plans:
  - .cursor/plans/tasks/PLAN-20261010-369-goal-043-ec01-04-closeout-assets-run-own-assertions.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261010-370-goal-043-ec01-04-closeout-assets.md
supersedes: []
tags: [closeout, recheck, assertions, ast, discipline, goal-043]
---

## 做了什么

置两处「复检资产自身」的缺陷并加上机器判据：

1. **声明面 ≠ 加载面**：`tools/verify_goal038/039/040_closeout.py` 声明
   `ASSERTIONS = "tools/goal0NN_closeout_assertions.py"` 却 `_load_assertions()` **加载
   `goal037_closeout_assertions.py`** ⇒ 三处的**自有断言从未在收口复检里运行**
   （实测：`verify_goal040_closeout.py --verdict-only` 的判词里其自有断言名命中 **0**）。
   修为加载**各自**的断言集。
2. **文本锚点随被引代码演进崩溃**：`goal040_closeout_assertions.py` 用
   `runner.index("_non_success_terminal(program, existing, last)")` 判「分派先于结论面」——
   GOAL-041 **正当**给该函数加了 `programs` 形参 ⇒ 文本失配 ⇒ **整条断言集崩溃**
   （`ValueError: substring not found`）。修为 **AST 结构判据**（按**被调函数名**取行号）。
3. **机器判据** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`：
   声明==实载（AST 读）+ 被点名断言集**可执行** + **射程分区不漏项**。

## 为什么这样做

**为什么「加载错」比「判据写错」更危险**：判据写错会在运行时红；加载错则**什么都不发生**——
验证器照常输出一份看起来完整的判词表（只是那份是**别人的**）。收口复检是「结论有来源支持」
那条链的承重件：它没跑或崩了，前面所有 GOAL 的「独立复检 PASS」都会退化成**未经检验的宣称**。

**为什么崩溃也算缺陷**（而不是「判负」）：判负是**结论**（有判词、可复核）；崩溃是**资产坏了**
（没有判词）。两者在读面上完全不同，处置也不同。

**为什么文本锚点是根因而不是偶然**：`index("...")` 把**实参列表**写进了判据 ⇒ 被引函数的
**任何**合法签名演进（加参数、换顺序、改名）都会打断它。判据要盯的是**关系**
（「分派先于结论面」），不是**某一行文本**。

## 现象

```
$ uv run python -B tools/verify_goal040_closeout.py --root . --verdict-only | grep -c "ec02-three-new-kinds"
0                       # 自有断言从未运行（判词表是 037 那份）

$ python -c "…goal040_closeout_assertions.assertion_verdicts(root, toolbox)"
ValueError: substring not found      # 崩溃：文本锚点与真实签名不一致
```

## 根因

| 层 | 事实 |
| --- | --- |
| 加载面 | `_load_assertions()` 里写死了 `goal037_closeout_assertions.py`（复制自上一轮，未改） |
| 声明面 | `ASSERTIONS` 常量在 GOAL-033 起引入；031/032 无该常量（只有加载面） |
| 判据面 | `runner.index("<调用签名字面量>")` —— 把实参写进判据 |
| 演进 | GOAL-041 给 `_non_success_terminal` 加了 `programs` 形参（多轮推进需要 ⇒ **正当**） |

## 怎么做与复现

**复现两处缺陷**（合成形态即可，不必回滚历史）：

```python
# ① 声明/实载不一致：AST 读出两个名字，比较即可
source = 'ASSERTIONS = "tools/goal999_closeout_assertions.py"


'
source += 'def _load_assertions():
'
source += '    path = Path(__file__).resolve().parent / "goal037_closeout_assertions.py"
'
# ⇒ _declared_assertions(source) 与 _loaded_assertions(source) 不同

# ② 文本锚点崩溃：把实参写进 index ⇒ 签名义演进即失效
runner.index("_non_success_terminal(program, existing, last)")   # ⇒ ValueError
```

**正确写法**（两条）：

```python
# 加载面：加载**本 GOAL 的**断言集（声明与实载必须同名）
path = Path(__file__).resolve().parent / f"goal{THIS_GOAL}_closeout_assertions.py"

# 判据面：用 AST 按**被调名**取行号（与实参无关）
def _first_call_line(source, function_name):
    parsed = ast.parse(source)
    lines = [n.lineno for n in ast.walk(parsed)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == function_name]
    return min(lines) if lines else None
```

**机器判据**（本仓已在树）：`tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`
—— 「声明 == 实载」（AST）+「被点名断言集可执行」+「射程分区不漏项」；
两向反例：合成「声明 A 实载 B」与「断言集抛异常」都必须报红。

## 适用边界

- 适用于：本仓一切「**外部断言集 + 加载器**」形态的收口复检资产（GOAL-031 起）；
  以及任何用 `str.index("<code literal>")` 当锚点的判据。
- **不**适用于：GOAL-015/023…030 的旧一代验证器（断言**内联**在验证器里、无断言集文件
  ⇒「声明 == 实载」这条规矩对它们不适用；它们在判据里逐条登记为旧一代）。
- **不声称**：本条的判据**不**禁止文本锚点本身（`U-2`：其它历史断言集的同类脆弱性未普查）；
  也**不**重跑历史收口复检（`U-1`）。
- **射程**：判据只覆盖「加载对」与「跑得动」两件事 —— 断言集**内容**是否正确仍由
  各自 GOAL 的收口复检承担。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261010-369-goal-043-ec01-04-closeout-assets-run-own-assertions.md` | 两处缺陷的读数 / 修法 / 两向反证 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261010-370-goal-043-ec01-04-closeout-assets.md` | 独立复检：对拍 / 0 命中 / 崩溃 / 修后三处跑通 / P-1·P-2 全红 |
| repository | `tools/verify_goal0{38,39,40}_closeout.py` | 声明面与加载面（缺陷现场） |
| repository | `tools/goal040_closeout_assertions.py` | 文本锚点（崩溃现场）与 AST 判据（修后） |
