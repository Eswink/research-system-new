---
id: RECHECK-20261005-282
slug: goal-029-ec05-self-bootstrap-closeout
title: GOAL-029 EC-04/EC-05 复检 — 两树判词归档留档 + 自举收口（验证器进树 + TWO-TREE PASS + m0 23/23）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-281
parent_goal: GOAL-20261004-029
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261005-281`（GOAL-20261004-029 的 cycle 4+5 子计划）—— EC-04（两树判词归档留档）
与 EC-05（自举收口）。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 两份判词归档在树（二进制写盘） | **PASS** | `.cursor/plans/goals/evidence/GOAL-20261004-029-verdict-{current,clean}.txt` 各 **2593 字节**、**54 行**、**CR count 0**、`sha256` **相同**（`db4faa07d42532d0dd4793a9d42b8392784ecfb761af07562e7915eb12b9a503`）；判据断言纯度（只有判词行前缀）与路径无关（无盘符）；落点不被 `.gitignore` 覆盖 |
| AC-2 | 两向反证 | **PASS** | 文本模式写一份 ⇒ **2 failed**（`sha256` 不同 + 含 CR，实测 18 个 CR）；二进制复原 ⇒ 绿。另固定两条实测事实：文本模式在 Windows 写 CRLF；`.gitattributes` 的 `* text=auto eol=lf` 会把差异在提交时**静默归一化** ⇒ `git diff` **不足**以充当逐字节证据（已断言 staged blob 仍为纯 LF） |
| AC-3 | 收口验证器进树 + 复用标准集 + 四道门 | **PASS** | `tools/verify_goal029_closeout.py`（**419 行** ≤450）**复用** `closeout_recheck_assertions.standard_verdicts`；只读工具集 `tools/closeout_recheck_tools.py`（118 行）按**路径**加载（`tools/` 不是包）；两者**双双进 `IN_SCOPE`**（纯收紧）；四道门 **8 passed** |
| AC-4 | 两树同结论 | **PASS** | `TREE current` 与 `TREE clean` 各 **54 判词**、`sha256` **相同**、`COMPARE identical=True`、**`TWO-TREE PASS`**（两树 exit=0）；两路判词二进制写盘到归档落点 |
| AC-5 | as-is m0 23/23（记录写入之后） | **PASS** | 见 GOAL「状态历史」的本轮终态行（`PASS: profile=m0; 23 deterministic checks`） |
| AC-6 | 治理与台账 | **PASS** | `validate.py` 绿；CI 台账逐提交（`cancelled` 如实登记 + 原因；`total_count=0` 记未取证 + 显式覆盖声明）；残余与未覆盖逐条 |

## 按压（两向）

| # | 按压形态 | 结果 | 复原 |
| --- | --- | --- | --- |
| P-1 | 把 `clean` 归档用**文本模式**重写（`write_text` 不带 `newline=""`） | **2 failed**：`test_the_two_archives_have_the_same_sha256` + `test_neither_archive_has_carriage_returns`（实测 18 个 CR） | 二进制复原 ⇒ CR=0、`sha256` 与 current 相同 ⇒ 13 passed |

## 复检发现（如实登记，未修）

- **`W-1`（本轮实测并修掉的自身缺陷，值得登记）**：EC-05 验证器起初**读**两树入口写回的判词归档
  做断言 ⇒ **输入即输出**：两棵树**先后**执行同一脚本，第一次执行时归档还是上一轮的内容
  ⇒ 两棵树读到**不同**的历史残留（实测首跑 current 判红 / clean 判绿），且**永不收敛**。
  **修法**：归档形态由 EC-04 的**专属判据**承担（跑在门禁里、在两树写入**之后**）；
  验证器只判 GOAL 自己的交付物。沉淀为 `MEM-20261005-186`。
- **`W-2`**：验证器**不**判 EC-04 归档（见 `W-1`）⇒ EC-05 的判词数是 **54**（若含归档断言会是 57）；
  归档由 EC-04 判据独立判（13 passed）。两者**互补不互相顶替**。
- **`W-3`**：两树第二棵是**已推送 HEAD** 的 checkout（承 GOAL-028 `W-3`）⇒ **必须先提交再跑**；
  本轮实测：首跑 RED（干净树不含未提交的验证器）⇒ 提交推送后 **TWO-TREE PASS**。
  这也是两树入口**有效性**的正控制。
- **`W-4`**：`IN_SCOPE` 的读取起初只认 `ast.Assign`，而该常量是 **`AnnAssign`（带类型标注）**
  ⇒ 恒定读到空元组 ⇒ 判据**假红**（文件其实在表里，实测「表内 12 条」）。改用
  `Assign`/`AnnAssign` 都认的读取器后转绿 —— 与 `MEM-20261005-185`（判据射程要按压）同族。
- **`W-5`**：本文件（RECHECK）与 GOAL 的迭代日志/状态历史里的 `sha256` 是**本轮那次运行**的读数；
  两树入口每次运行都会**重写**归档（内容随树的状态变化）⇒ 引用时必须写明是哪一次
  （本轮的 `db4faa07…` 对应 `dcd8387` 提交后的那次运行）。
- **`W-7`**：CI 首跑判红（**只在 Linux 暴露**）：文本模式行尾转换是平台相关的，
  判据按平台分档断言（详见下节）。
- **`W-6`**：收口验证器只覆盖本轮交付物与标准面，**不**覆盖产品运行语义（承 GOAL-023 的有界射程）；
  前四轮的 `W-NN` 族**原样保留**。

## 复检补充：CI 首跑判红（已修，**只在 Linux 暴露**的判据缺陷）

`656ae37` 的 M0 首跑 `quality-ubuntu-latest` 判红：
`tests/tooling/test_two_tree_verdicts_are_archived.py::test_text_mode_and_binary_mode_differ`
报 `文本模式必须与二进制模式产生不同 sha256` —— **本地 Windows 全绿**。

**根因**：`Path.write_text` 的行尾转换是**平台相关**的 —— Windows 把 `
` 写成 `
`，
**Linux / macOS 不转换**（`newline=None` 时 `
` → `os.linesep` = `
`）。
我那条断言把 Windows 行为写成了跨平台事实 ⇒ Linux 上假红。

**修法（不放宽，只是各自说各自平台的事实）**：
- **跨平台硬断言** `test_the_entry_style_is_lf_only`：入口那种写法（`newline=""`）
  必须产出纯 LF —— 归档纪律的载体，两平台都成立；
- **平台事实** `test_text_mode_hazard_matches_this_platform`：按 `os.name` 分档断言。

**这条与 `W-4` 同族**（判据射程要按压/要按真实条件说事实），登记为 **`W-7`**：
本判据原先把「本机平台的行为」当成「普适行为」—— 与「只扫 `ast.Name`」同类的
**射程错配**（对象没变，是断言覆盖的条件集错了）。

## 结论

`PLAN-20261005-281` 的 **AC-1…AC-6 全 PASS**；
`result = PASS_WITH_WARNINGS`（六条 `W-NN` 如实登记，其中 `W-1`/`W-4` 是本轮实测并修掉的
自身缺陷、`W-3` 是自举时序、`W-2`/`W-5`/`W-6` 是射程与引用边界）。

**GOAL-029 的五个 EC 全 PASS** ⇒ 满足 `ACHIEVED` 的前置条件。

**明确否认**：**不**宣称项目安全（`R-M1` 未收口）；**不**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
