---
id: MEM-20261010-214
title: "「有类型、零写者」的字段必须**在每个适配器**都补写者 —— 同一条纪律会第二次生效（判据在 Fake 路径上假绿）"
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
scope: repository
confidence: 0.95
review_after: 2027-04-10
source_plans:
  - .cursor/plans/tasks/PLAN-20261010-379-goal-045-ec01-04-memory-conflicts-and-valid-from.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261010-380-goal-045-ec01-04-memory-conflicts-and-valid-from.md
supersedes: []
tags: [memory, adapters, fakes, contract-parity, goal-045]
---

## 做了什么

`MemoryRecord` 上有 `contradictions` / `valid_from` 两个字段，而**没有任何写者**：
`MemoryWriteProposal` 上没有它们（提案无从声明）、SQLite 的 `commit` 从提案构记录时只带
`supersedes`、PG 的 `commit` 把 `contradictions` 硬编码成 `[]`（源码注释自陈 `empty at commit`）。
本轮给提案加可选字段，并把写者补进**三个**适配器（SQLite / PG / **Fake**）＋ 读面披露与点名。

## 为什么这样做

**「同一条纪律会第二次生效」是本条的要害**：Fake 适配器的源码注释**此前就写着**
「假实现必须与两个真适配器**同契约** —— 少带这两个字段会让『落库/时效』判据在 Fake 路径上
**假绿**（实测过）」。本轮新增字段时，Fake **又**漏了一次 ⇒ 读面判据在该路径上当场红
（3 例里 2 例）。**结论**：契约一致性不是「做过一次」的事，是**每次加字段都要重做一遍**的事。

**为什么这类缺陷难发现**：字段在**类型上存在** ⇒ 读代码看着「有」；缺的是**写者**。
判据若只跑一条路径（比如只跑 SQLite）就**永远看不到** Fake/PG 的缺口 —— 所以判据必须覆盖
**声明面 + 每个实现面**（本仓既有纪律：声明面 vs 实现面分列，两者不互相顶替）。

## 现象

```
# 修正前（实测）
MemoryWriteProposal(..., contradictions=["x"])   ⇒ TypeError: unexpected keyword argument
# 读面（经 Fake 路径）
row["contradictions"]                            ⇒ []      # 声明为真，却读不出来
```

## 根因

| 层 | 事实 |
| --- | --- |
| 域 | `MemoryRecord` 有字段、`MemoryWriteProposal` **无** ⇒ 声明路径**根本不存在** |
| SQLite | `commit` 构记录时逐字段复制，漏了这两个（`supersedes` 在场） |
| PG | `commit` 用 `None` / `_json([])` **硬编码**（注释：`empty at commit`） |
| Fake | 同 SQLite（漏字段），而其注释**已经警告过**这一点 |
| 消费面 | 全仓（排除 tests）**零**按冲突判定 ⇒ 既是写不进、也是读不出 |

## 怎么做与复现

**修法（四处，逐条）**：

1. 域：`MemoryWriteProposal` +`contradictions: list[str] = []` / `valid_from: Timestamp | None = None`
   （**可选**，缺省 ⇒ 既有行为逐字不变）+ 冲突项必须是**非空字符串**（非法 ⇒ 点名）；
2. **每个**适配器的 `commit` 都带上这两个字段（SQLite / PG / Fake —— 一个不能少）；
3. 读面：逐条披露两字段；理由**点名**冲突（`[]` ⇒ **不**追加任何文字，不得凭空说有冲突）；
4. 判据：域（可声明 / 缺省 / 非法点名）+ 每个适配器（往返一致）+ 读面（点名 / 披露 / 不凭空）。

**按压（三向反证）**：`C-1` SQLite 不带字段（复现静默丢弃）⇒ 红；`C-2` 点名句变空 ⇒ 红；
`C-3` 未声明也报冲突（凭空）⇒ 红。

## 适用边界

- 适用于：本仓一切**多实现 Port**（`MemoryStore` / `RunStore` / `ProgramStore` / …）——
  **加字段时逐实现核查写者**；也适用于「类型上有、行为上无」的字段（先问「谁写它」）。
- **不**适用于：只在**一个**实现里存在的内部字段（那种可以直接看实现；
  本条的难度来自**契约面**与**多实现**）。
- **不声称**：本条只保证**可声明 / 可落库 / 可点名**；冲突的**检测**（谁和谁冲突）与
  **处置**（自动消解）**不在**（登记为 `W-2` / `W-1`）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261010-379-goal-045-ec01-04-memory-conflicts-and-valid-from.md` | 四处修法 / 三向按压 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261010-380-goal-045-ec01-04-memory-conflicts-and-valid-from.md` | 独立复检：字段表 / 三适配器往返 / 按压 |
| repository | `packages/domain/memory.py`（提案 vs 记录字段表） | 「有类型、零写者」的现场 |
| repository | `adapters/{sqlite,postgres,fakes}/memory_store.py` | 三个实现各自的缺口与 Fake 的既有警告 |
