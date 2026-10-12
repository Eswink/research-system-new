---
id: RECHECK-20261013-440
slug: goal-065-ec01-04-who-proposed-a-memory-is-readable
title: 独立复检：GOAL-20261012-065 cycle 1（EC-01…EC-04）—— 谁提议的这条记忆读得出来
plan_id: PLAN-20261013-439
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/domain/memory.py（`MemoryRecord.proposed_by`）+ 三适配器同契约
  - path: 独立重跑判据（披露面 11 例 + PG 往返 1 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-065-press-two-way.txt
---

# RECHECK-20261013-440 — GOAL-20261012-065 cycle 1 独立复检

复检对象：`PLAN-20261013-439`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-memory-author.py` —— 四段读数与 GOAL 表逐条一致
（含**一处实测更正**，见下）：

| # | 事实 | 独立读数（**改动后**） | 改动前 |
| --- | --- | --- | --- |
| 1 | 两处字段表逐个读出 | 提案 **有** / 记录 **有**（本轮补上） | 提案有 / 记录**没有** |
| 2 | 零命中复核 | 读面与三适配器**不再零命中**（新键/新列） | 读面与三适配器**全 0** |
| 3 | 实跑 | `hasattr(record, "proposed_by") == True`；读面键集**含**它 | `False`；20 键里**没有** |
| 4 | `provenance` 与作者是两件事 | 两者各自独立（本轮**不**改 `provenance`） | 同 |

**EC-01 实测更正（如实登记）**：建档表的第 3 行初版写「命中只在提案面与**两个内部调用点**」，
**探针的逐文件计数**读出还含 **`services/api/routers/memory.py`（2 处，写入口把载荷带进提案）**
与 `services/api/dto/memory.py`（写面 DTO）⇒ 已按实测更正建档表：命中**都在写面**、
**读面与三适配器全 0**（该更强的事实正是本 GOAL 的立题依据）。

### 2. EC-02 作者面落 canonical（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_memory_author_read_faces.py tests/postgres/test_memory_conflict_timeliness_pg.py -q`
⇒ **13 passed**。逐条复核：

- **记录**有 `proposed_by`（可选；缺省 `None`）；**提案面**的既有声明位仍在（**不**新造第二个字段）；
- **SQLite 往返**原样读回；**PG 真库往返**同值（迁移 `027` 只加列）；
- **Fake 同契约**（承序 13/45/61 的教训：少带 ⇒ 该路径判据假绿）；
- **未声明** ⇒ 两库都读回 `None`（**不猜**、**不**伪造）；
- **两处声明面同值**（提案写什么，记录就是什么）；
- **其它可选声明面逐条仍在**（反证臂，本轮只加作者面）。

### 3. EC-03 两读面同源披露（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api/test_memory_api.py -q`
⇒ **全绿**。逐条复核：

- 编排面 `row["proposed_by"] = record.proposed_by`；HTTP 面 `"proposed_by": record.proposed_by`
  —— 两处**都直接读**同一份 canonical 字段（**判关系**，不各写一套判定）；
- **既有键逐条仍在**（13 个键逐个点名，含序 29/30/31/32 的四组新键）；
- **来源与作者互不顶替**：记录上 `proposed_by` 与 `provenance` 各自在场、值不同；
- **快照同轮**（`+11 / -0`）；HTTP DTO 同轮披露该键。

### 4. EC-04 两向反证（独立重跑 `scratch/goal065_press.py`）

| 按压 | 读数 | 被哪条判据抓到 |
| --- | --- | --- |
| **BASELINE**（未按压） | **GREEN**（34 passed） | — |
| `W-1` 记录侧字段被摘掉（落库丢作者） | **RED**（1 failed） | `test_the_author_survives_a_sqlite_round_trip` |
| `W-2` 适配器不带该列（往返丢失） | **RED**（1 failed） | 同族的往返臂 |
| `W-3` 缺省形态被改动（伪造未声明） | **RED**（1 failed） | `test_the_undeclared_author_reads_none_verbatim` |
| `W-4` 读面披露被摘掉（canonical 有、读不出） | **RED**（2 failed） | 编排面披露臂 |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**一处两向核实**：`W-1` 与 `W-2` 打**不同层**（写入侧构造 vs 落库取值），已逐条核实
各自被**不同**的判据抓到（不是同一个臂重复计数）。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **PG 判据两向实测**：临时把 PG 写入侧换成 `None` ⇒ **RED**（1 failed）⇒ 该判据**会响**；
- EC-02 的判据按**关系**判（写入侧从**提案**取值 / 三适配器**各自**带该字段），不钉字面写法；
- 例数下界钉进收口断言集（11 / 2 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**作者面落 canonical**
（记录 + 三适配器同契约）、**两读面同源披露**、**缺省形态逐字不变**（未声明 ⇒ `None`）、
**来源与作者互不顶替**。

**WARN（逐条）**：

- **`W-1`（本轮特有的口径边界）**：本轮**不**按作者筛选（`query` 的第三个维度**未做** ——
  与序 17 的 `scope` 同类但**另成一面**）；**不**做作者**鉴权**（作者面是**声明**，不是 ACL ——
  与 `scope` 的边界**逐字同形**）。⇒ 「读得出」已成立，「**选得着**」仍缺（登记为后续候选）。
- **`W-2`（既有口径，承继）**：`provenance`（**来源**）与作者是两件事，本轮**只**让作者可读；
  `provenance` 在**编排读面**上**仍不披露**（它从不在该面上）—— 本轮**未**顺手加
  （那会让「作者面」与「来源面」的射程混在一起）。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
