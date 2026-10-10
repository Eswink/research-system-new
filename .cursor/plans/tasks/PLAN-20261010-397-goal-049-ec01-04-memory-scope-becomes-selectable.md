---
id: PLAN-20261010-397
slug: goal-049-ec01-04-memory-scope-becomes-selectable
title: GOAL-20261010-049 cycle 1（EC-01…EC-04）：记忆范围可选 —— 查询面 + 消费面 + 四向反证
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-398-goal-049-ec01-04-memory-scope-becomes-selectable.md
memory_entries: []
parent_goal: GOAL-20261010-049
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-049 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**边界**：**不**新建记忆存储 / 索引；**不**做语义检索（属 `Q-3` 的
    derived index 面）；**不**把范围当权限（读面认证 / 多租户 / RBAC / BOLA·BFLA 仍属未覆盖）；
    **不**改既有读面字段名（只加**可选**入参与计数）；**不**顺手改缺省路径；改 DTO ⇒ 同轮同步
    OpenAPI 快照（`MEM-20261010-216`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让记忆的「适用范围」**成为可选择的一维**：① 勘察定稿（读数见 GOAL 正文七条）→
    ② **查询面** —— `MemoryStore.query(tier=None, scope=None)`，两维**可并存**、都缺省 ⇒ 全部
    （**既有行为逐字不变**）；**三适配器同契约**（SQLite / PG / **Fake**）→
    ③ **消费面** —— `memory_read` 可传 `scope`，载荷**点名**声明的范围与**筛掉了多少条**
    （`filtered_out`）；**未知范围 ⇒ 点名**；**缺省路径的载荷逐字相同**；HTTP 读面同样可选
    （两个**显式** DTO 形态）→ ④ **两向反证** K-1…K-4 → ⑤ EC-05（自举收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：`scope` 在域声明面逐字在场 / `MemoryStore.query` 的签名
      **只有 `tier`**（三适配器同形）+ **反证**传 `scope=` ⇒ `TypeError` / 全仓三个调用点逐条 /
      读面已逐条披露 / 两库列已在（预期无迁移）/ 计数摘要形态现成。
    verify: >-
      GOAL 正文「事实层结论」的七条读数（`rg` 命令 + `TypeError` 反证 + 实跑）。
    status: PASS
  - id: AC-2
    criterion: >-
      **查询面（可选维度 + 三适配器同契约 + 缺省逐字不变）**：`query` 可按 `scope` 筛；
      `tier` 与 `scope` **可并存**；两者**都缺省 ⇒ 全部**；**三个适配器同契约**
      （SQLite / PG / Fake 一并带上）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/postgres -q`
      ⇒ 全绿 + 新用例（SQLite +1 / PG +1）。
    status: PASS
  - id: AC-3
    criterion: >-
      **消费面（点名筛掉多少 + 缺省逐字不变）**：`memory.read` 可传 `scope`；载荷**点名**
      声明的范围与 `filtered_out`（**不静默丢**）；**未知范围 ⇒ 点名**（不是静默空集）；
      **不传 `scope` 的载荷与改动前逐字相同**（那两键**不出现**）；HTTP 读面同样可选。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical tests/api -q`
      ⇒ 全绿 + 新用例（读面 +4 / API +1）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`K-1` 传了范围却不生效 / `K-2` 没传范围却筛掉了（缺省被改动）/
      `K-3` 未知范围静默空集 / `K-4` 筛掉的条数不点名 —— 四条**全部判红**；复原用**二进制读写**
      且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal049-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-049-press-two-way.txt`（431 B / `CR=0`）。
    status: PASS
---

# PLAN-20261010-397 — GOAL-20261010-049 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-049`（MAINLINE 程序表**序 17**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（七条读数：声明确在场 / 签名单一维度 / `TypeError` 反证 / 三调用点 / 已披露 / 列已在 / 计数形态现成） | PASS |
| AC-2 | 查询面（两维可并存 + 三适配器同契约 + 缺省逐字不变） | PASS |
| AC-3 | 消费面（点名筛掉多少 + 未知范围点名 + 缺省载荷逐字相同） | PASS |
| AC-4 | 两向反证 K-1…K-4 全红 + 二进制复原一致 | PASS |

## 实施清单

- [x] WP-1 Port：`query(tier=None, scope=None)`（可选参，语义不变）
- [x] WP-2 SQLite：按 `scope` 筛（两维并存；缺省不筛）
- [x] WP-3 PG：同契约
- [x] WP-4 Fake：同契约（**第三个适配器** —— 承 `MEM-20261010-214`：同一缺口会各犯一次）
- [x] WP-5 `memory_read`：`scope` 入参 + `filtered_out` 披露 + 未知范围点名
- [x] WP-6 HTTP 读面：可选 `?scope=` + **两个显式 DTO 形态** + OpenAPI 快照同轮重生成
- [x] WP-7 判据：读面 +4 / SQLite +1 / PG +1 / API +1
- [x] WP-8 两向反证 K-1…K-4 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 读面判据 | `test_memory_read_dispositions.py` **22 passed**（原 18 + 4）|
| SQLite 判据 | `test_memory_scope_and_validity.py` **14 passed**（原 13 + 1）|
| PG 判据 | `test_memory_scope_pg.py` **3 passed**（原 2 + 1）|
| API 判据 | `test_memory_api.py` **10 passed**（原 9 + 1）|
| 两向反证 | `K-1`…`K-4` **全 `RED`**（1/3/1/1 例）+ 二进制复原 raw `sha256` 一致；归档 **431 B / `CR=0`** |
| 定向套件 | `tests/{application,api,e2e,domain,adapters,postgres,contracts,tooling}` **4937 passed, 18 skipped** |
| 四道门 | `ruff check` / `ruff format --check`（1191 files）/ `mypy` strict（**1181** files）/ 规模门 全绿 |
| **下游同步** | **OpenAPI 快照同轮重生成**（`+59 / -1`）+ 判据 **8 passed**（承 `MEM-20261010-216`）|
| **迁移** | **无**（`scope` 列早已在表上 —— 序 13 落的）|
| CI | `e9761b4` **M0 success**（8 job 全 success）|

## 本轮实测到的两处**真缺陷**（如实登记，均已修）

1. **`K-2` 反证臂最初假绿**：SQLite 判据里所有记录**同一 tier** ⇒「缺省被改成按 tier 筛」
   在那份数据上与「不筛」**同结果** ⇒ 按压**判不出来**（实测：`K-2` 报 GREEN）。
   **修法**：判据里加**第二个 tier** 的记录，并把该陷阱写进断言注释 ——
   **反证臂必须能在它的数据上区分两件事**（否则「绿」是数据选得不巧，不是判据在守）。
2. **`response_model_exclude_none` 是**递归**的**：给列表路由开它之后，**validity 读面**的
   `validity: null`（「未到期**或未声明**」是**有意义**的值）被一起抹掉 ⇒ 既有判据当场红
   （`KeyError: 'validity'`）。**修法**：改成**两个显式 DTO 形态**
   （`MemoryFilteredListViewDto(MemoryListViewDto)` 继承复用），该开关**不**再用 ——
   schema 与载荷一致，且**只有**筛过的形态多那两个键。

**申报（承 `MEM-20261009-210`）**：上表四个测试文件**各只增不删谓词**（唯一一处 `-` 是
`_record` 助手的 `scope="project"` **参数化**成 `scope=scope`，**缺省值一字未改**）；
六个源文件的删除行**全部是签名加可选参 / 分支改写**（逐条见 RECHECK 的申报表）。

## 影响报告

- **Domain / API / schema 变化**：Port 读面 **+1 可选参**；`memory.read` 载荷**条件性 +2 键**
  （只在传 `scope` 时出现）；HTTP 读面 **+1 可选 query 参** + 新增一个响应形态
  （`MemoryFilteredListViewDto`）；**无迁移**。
- **安全 / 凭据变化**：无（`scope` 是**声明的范围**，**不是** ACL —— 见 `AA-1`）。
- **兼容性 / 迁移风险**：**低** —— 缺省路径载荷逐字不变（判据钉住）；旧读者不受影响。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本 cycle 的两处可复用教训（**反证臂必须能在其数据上区分两件事**；
**`response_model_exclude_none` 会递归到嵌套模型，抹掉有意义的 `null`**）已由
`MEM-20261010-216` 的同族纪律与 `MEM-20261010-215`（判关系不判位置）覆盖；
**未**沉淀新条目。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | Port + 三适配器 + `memory_read` + HTTP 读面落地；判据 +7 例；四向按压全红。 |
| 2026-10-10 | DONE | 四道门 + 定向套件 4937 例全绿；OpenAPI 快照同轮；`RECHECK-20261010-398` 独立复检。 |
