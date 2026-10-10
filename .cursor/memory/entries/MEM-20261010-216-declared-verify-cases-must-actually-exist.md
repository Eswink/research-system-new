---
id: MEM-20261010-216
title: "**声明了 verify 命令的用例必须真的存在** —— 「文本在场」不等于「行为被断言」；且快照类判据会自我修复 ⇒ 本地永远看不见漂移"
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
scope: repository
confidence: 0.95
review_after: 2027-04-10
source_plans:
  - .cursor/plans/tasks/PLAN-20261010-387-goal-046-repair-snapshot-sync-and-declared-cases.md
  - .cursor/plans/tasks/PLAN-20261010-383-goal-046-ec01-04-program-human-gate.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261010-388-goal-046-repair-snapshot-sync-and-declared-cases.md
supersedes: []
tags: [verification, evidence-discipline, openapi-snapshot, ci-vs-local, goal-046]
---

## 做了什么

GOAL-046 cycle 1 交付了「程序级人工闸门可声明」，**实现**与**收口断言集的文本判据**都在场；
cycle 2 据此把 GOAL 收口成 ACHIEVED。随后**轮询 CI 实测**发现两处缺口：

1. **真红（产品面缺同步）**：`de9d396` 的 `quality-ubuntu-latest` / `quality-windows-latest`
   **failure**，逐字 `tests/contracts/test_openapi_snapshot.py::test_openapi_snapshot_is_current
   assert regenerated == committed` —— 建程序 DTO 改了而 `docs/api/openapi.m13.json`
   **没有**重生成并提交。
2. **声明的 verify 用例不存在**：EC-02 的 `verify` 行点名「两库各一组 + 缺省 + 非法」、
   EC-04 点名「经 HTTP 面实跑」，而实测 `rg -l human_gate_at_index tests/` 修前**只有**
   判定面那一个文件 —— 两库 / 域 / e2e **零用例**。

本轮把两处逐条补齐（快照按生成器重生成；四类用例各补 1–2 例并钉住例数下界），
并把「快照含本轮字段」写进收口断言集。

## 为什么这样做

**两个陷阱叠加，导致「本地全绿 + 记录看起来自洽」而事实不成立**：

- **陷阱一（快照类判据会自我修复）**：`test_openapi_snapshot.py` 先读**已提交字节**、再
  **重新生成**（生成器**覆写**文件）后比对 ⇒ 本地第一次跑它就把文件改对了，工作树里的文件
  从此**比 HEAD 新**。于是「本地绿」+「工作树里有字段」两条证据**同时为真**，而**提交态
  缺字段**这件事只有 CI 能看到。**那个 `M` 不是 CRLF 伪影，是被本判据改出来的**。
- **陷阱二（「文本在场」冒充「行为被断言」）**：收口断言集当时写的是**文本判据**
  （`"human_gate_at_index" in domain` 之类）⇒ 它证明「某个名字出现在某个文件里」，
  **不**证明「声明的行为有用例」。EC 的 `verify` 行点名的是**行为面**，两者不是一回事。

⇒ 结论：**`verify` 行是承诺**。「我写了验证命令」与「那条命令点名的东西真的存在」必须分别取证：
前者是记录自洽，后者要在**受判面清单**上数一遍。

## 现象

```
# 陷阱一（实测）
$ git show 04123a7:docs/api/openapi.m13.json | grep -c human_gate_at_index
0
$ grep -c human_gate_at_index docs/api/openapi.m13.json     # 工作树
2                                  # ⇐ 「本地有」，提交态没有

# 陷阱二（实测）
$ rg -l human_gate_at_index tests/
tests/application/run_orchestration/test_program_waiting_on_the_run_path.py   # 只有这一个
```

## 根因

| 层 | 事实 |
| --- | --- |
| 判据形态 | 快照判据**重生成后比对** ⇒ 副作用是「把漂移当场修掉」，漂移只在 CI 可见 |
| 证据形态 | 收口断言集用**文本在场**近似「行为被断言」⇒ 声明与用例可以脱钩而无判据报警 |
| 流程 | cycle 2 只轮询到 `04123a7` / `de9d396` 两个 sha，**没见**随后的归档提交 `06e9b01` ⇒ 收口时「CI 到终态」的证据链不完整 |
| 兜底 | 无 —— 本轮两处都是**事后**由人工复核 + CI 才发现的 |

## 怎么做与复现

**修法**：① 产品面按生成器重生成并提交（`uv run --frozen --no-sync python -B tools/gen_openapi.py`）；
② 把该面写进收口断言集（读**提交态**文件里有没有那个字段）；
③ 声明的行为面用例逐条补，并把**例数下界**钉进收口断言集（掉下去即判红）。

**复现（合成 / 现场）**：把某个 DTO 加一个字段但不跑生成器 ⇒ 本地 `pytest` 仍绿
（判据自己把文件改对了），而 `git show HEAD:<snapshot> | grep <field>` 为零 ⇒
CI 的 `quality-*` 会红。**验证纪律**：改 DTO 后**必须**看 `git diff --numstat` 里有没有快照。

**写记录时的规则**：

- EC 的 `verify` 行点名「哪几类用例」时，**同轮**要在受判面上数一遍（`rg -l <符号> tests/`）
  并把读数写进 PLAN/RECHECK；
- 「我在收口断言集里判了它」与「它有用例」是**两条**证据，不得互相顶替；
- 收口前把**全部**相关 commit 的 CI 都读到终态（本仓 `scratch/poll_ci_all.sh <sha>` 逐个来），
  只读到一部分不算「CI 到终态」。

## 适用边界

- 适用于：本仓一切**生成物 + 判据重生成后比对**的形态（OpenAPI 快照、结构签名基线…），
  以及一切「EC 声明了用例种类」的收口。
- **不**适用于：判据**只读不写**的情形（那种判据在本地就会红，无此陷阱）。
- **不声称**：本条不保证所有既有 EC 的 verify 行都已逐条兑现；只保证**本轮查出的两处**已修，
  且「例数下界」这类机械面会让**将来**的脱钩**在资产面可见**。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261010-387-goal-046-repair-snapshot-sync-and-declared-cases.md` | 修复面与申报表 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261010-388-goal-046-repair-snapshot-sync-and-declared-cases.md` | 独立复检：修前复核实测 + 修后逐条读数 |
| repository | `tests/contracts/test_openapi_snapshot.py` | 自我修复式判据（陷阱一的载体） |
| repository | `docs/api/openapi.m13.json`（提交态 vs 工作树） | 漂移的物证 |
