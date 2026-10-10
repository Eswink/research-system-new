---
id: PLAN-20261010-387
slug: goal-046-repair-snapshot-sync-and-declared-cases
title: GOAL-20261010-046 cycle 3（修复轮）：快照同步真红 + EC 声明的行为面用例补齐 + 归档定格
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-388-goal-046-repair-snapshot-sync-and-declared-cases.md
memory_entries:
  - declared-verify-cases-must-actually-exist
parent_goal: GOAL-20261010-046
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-046 的**修复面**（EC-02 / EC-04 / EC-05 的**证据链缺口**由本轮补齐）。
    授权原文见该 GOAL 的 `authorization.ref`。**本 PLAN 专属边界**：只**补**用例与同步面，
    **不**改任何既有断言的谓词（新增用例的既有文件**一字未删**）；**不**放宽任何阈值；
    **不**动 `tests/contracts/test_openapi_snapshot.py`（它抓到的红照实修产品面）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261010-046 的**证据链缺口**收口：① **真红** —— cycle 1 改了建程序 DTO 却
    未重生成并提交 `docs/api/openapi.m13.json`，CI 的 `quality-*` 在 `de9d396` 上以
    `test_openapi_snapshot_is_current` 判红（本地该判据会**自我修复**地重写文件 ⇒ 只看本地
    看不见）⇒ 按生成器重生成 + 提交，并把「快照含本轮字段」写进收口断言集；② **用例补齐** ——
    EC-02 声明的「两库往返（声明 + 缺省）+ 越界点名」与 EC-04 声明的「经 HTTP 面实跑」
    当时**只有实现与文本在场、没有用例** ⇒ 逐条补（SQLite / PG / 域 / e2e），并把例数下界
    钉进收口断言集；③ **归档定格** —— 进树的归档要**与最终一轮两树同结论**对应，重跑两树并
    提交；④ m0 23/23（**全部记录之后**）+ 治理 + 宪章判据 + CI 台账逐提交。
exit_criteria:
  - id: AC-1
    criterion: >-
      **真红照实修**：`uv run --frozen --no-sync python -B tools/gen_openapi.py` 重生成后
      `docs/api/openapi.m13.json` **含** `human_gate_at_index`（两个 DTO 各一处）；
      `tests/contracts/test_openapi_snapshot.py` **一字未改**且 8 passed；
      收口断言集新增两条（快照含字段 / 生成器在场）。
    verify: >-
      `git diff --numstat -- docs/api/openapi.m13.json` ⇒ `+23 / -0`；
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_openapi_snapshot.py -q`
      ⇒ 8 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **EC-02 声明的行为面用例补齐（两库 + 缺省 + 越界点名）**：SQLite 与 PG 各 +1 例
      （声明值往返一致 / 缺省读回 `None`）；域 +1 例（缺省 `None` / `max_runs` 边界合法 /
      越界（>max_runs、0、负）**点名** `human_gate_at_index must be within`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_program_store_sqlite.py
      tests/postgres/test_program_store_pg.py tests/domain/test_research_program.py -q`
      ⇒ 5 + 3 + 10 passed。
    status: PASS
  - id: AC-3
    criterion: >-
      **EC-04 声明的实跑臂补齐（经既有 HTTP 面）**：声明 `human_gate_at_index=1` ⇒ 第 1 轮
      跑完后推进落 `WAIT_FOR_APPROVAL` 且点名声明值、不起第 2 轮、读面回显声明；
      **配对反证**：同一实跑**未声明** ⇒ `CONTINUE` 且两轮照常起（被引事实只有判词）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_program_advance_on_the_run_path.py -q` ⇒ 9 passed。
    status: PASS
  - id: AC-4
    criterion: >-
      **归档定格与门链**：两树复检（`--script-mode shared` + `--base-ref`）⇒ `TWO-TREE PASS`
      （两路判词数与 `sha256` 相同）；判词归档**二进制写盘 / `CR=0`** 且与最终一轮同结论；
      as-is m0 **23/23**（在**全部记录之后**）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      终局行 `TWO-TREE PASS`；归档两份、非空、`CR=0`；
      `PASS: profile=m0; 23 deterministic checks`。CI 台账见 GOAL 正文。
    status: PASS
---

# PLAN-20261010-387 — GOAL-20261010-046 cycle 3（修复轮）

> **主线归属**：`GOAL-20261010-046`（MAINLINE 程序表**序 14**）的修复面。
> **为什么有这一轮**：cycle 2 把 GOAL 收口成 ACHIEVED 之后，**CI 实测**在 `de9d396` 上
> 判红（快照漂移），且复核发现 EC-02 / EC-04 声明的**行为面用例**当时并不存在
> ⇒ 收口依据不足。本轮把三处如实登记并逐条修好（**不**把没做的事留在记录里）。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 真红照实修（快照重生成 + 收口断言集加两条） | PASS |
| AC-2 | EC-02 行为面用例补齐（SQLite / PG / 域） | PASS |
| AC-3 | EC-04 实跑臂补齐（HTTP 面 + 配对反证） | PASS |
| AC-4 | 归档定格 + 两树 + m0 23/23（记录之后）+ 治理 + 台账 | PASS |

## 实施清单

- [x] WP-1 重生成 OpenAPI 快照（`tools/gen_openapi.py`）并提交
- [x] WP-2 收口断言集 +2 条（快照含字段 / 生成器在场）+ 例数下界 +3 文件
- [x] WP-3 SQLite / PG 两库往返用例（声明 + 缺省两臂）
- [x] WP-4 域用例（缺省 / 边界合法 / 三种越界点名）
- [x] WP-5 e2e 实跑臂（声明闸门拦下 + 未声明逐字不变，成对）
- [x] WP-6 两树复检 + 归档定格 + 全量 m0 + 治理 + 宪章判据
- [x] WP-7 CI 台账逐提交（failure/cancelled 逐条归因）

## 证据

| 门 | 读数 |
| --- | --- |
| 快照同步 | `+23 / -0`（两个 DTO 各 +1 属性块）；`test_openapi_snapshot.py` **一字未改**且 **8 passed** |
| 新增用例 | SQLite **5** / PG **3** / 域 **10** / e2e **9** / 判定面 **14**（共 41，定向套件全绿） |
| 收口验证器（本树） | **74 判词 / 0 FAIL** |
| 两树复检 | 终局行 `TWO-TREE PASS`（两路判词数与 `sha256` 相同，见 GOAL 台账读数） |
| 判词归档 | 两份、非空、`CR=0`（二进制写盘） |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict / 规模门 全绿 |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（见 GOAL 正文的门读数行） |

### 本轮实测到的**真红**（如实登记，不是时序）

`de9d396` 的 CI `quality-ubuntu-latest` / `quality-windows-latest` **failure**，逐字：

```
tests/contracts/test_openapi_snapshot.py::test_openapi_snapshot_is_current
assert regenerated == committed
```

**成因**：cycle 1 改了 `ProgramCreateDto` / `ProgramDetailDto` 却**没有**重生成并提交
`docs/api/openapi.m13.json`。**为什么本地看不见**：该判据先读已提交字节、再**重生成**
（重生成会**覆写**文件）后比对 ⇒ 第一次本地跑它就「自我修复」了，工作树里的文件从此比
HEAD 新 —— 这正是先前工作树里那个 `M` 的来源（曾被误读成 CRLF 伪影）。
**处置**：按生成器重生成 + 提交 + 把该面写进收口断言集（**不**动判据本身）。
**另两处如实登记**：同一次 run 的
`test_every_named_assertion_set_reports_no_negative_on_this_tree` 报
`['verdict-archive-current', 'verdict-archive-clean']` —— 那是**归档时序**
（归档在该提交之后才写入），与本条**不同类**。

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_program_store_sqlite.py` | **追加** 1 例 + `dataclasses.replace` import | — | `+16 / -0` | **0** |
| `tests/postgres/test_program_store_pg.py` | **追加** 1 例 | — | `+34 / -0` | **0** |
| `tests/domain/test_research_program.py` | **追加** 1 例 | — | `+28 / -0` | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例 + 1 常量 | — | `+50 / -0` | **0** |
| `tests/e2e/program_advance_support.py` | `create_program` +1 **可选**形参（缺省**不发键**） | 缺省路径的请求体与旧字面量**逐键相同** | `+13 / -7` | 7 行 = 同一字面量**改名**成 `payload` 变量（键值一字未改） |
| `tools/goal046_closeout_assertions.py` | 例数下界 +3 文件；新增 2 条判词函数 | **纯收紧**（只加） | `+41 / -2` | 2 行 = 原有 `CASE_FLOORS` 表头那两行的**改写**（`8` → `10` 与列表扩项） |

**`tests/contracts/test_openapi_snapshot.py` 一字未改**（它抓到的红按产品面修）。

## 影响报告

- **Domain / API / schema 变化**：无（本轮只同步快照 + 补用例）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。
- **上游版本影响**：无。
- **下一项任务**：GOAL-046 收口回写（EC-05 证据链）。**另**：序 1…14 全部收口 ⇒ 到期再规划（序 15）。

## 无可复用事实

本轮的机械面与 `MEM-20261010-216` 承载（「声明的 verify 用例必须真的存在」）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 快照重生成 + 四类用例补齐 + 收口断言集加两条。 |
| 2026-10-10 | DONE | 四道门 + 定向套件 41 例全绿；`RECHECK-20261010-388` 独立复检；两树 + 归档定格；全量 m0 读数见 GOAL 正文。 |
