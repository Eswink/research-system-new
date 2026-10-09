---
id: PLAN-20261009-361
slug: goal-041-ec02-04-bounded-retry-on-the-crash-window
title: GOAL-20261009-041 cycle 1（EC-02/EC-03/EC-04）：失败重试面的崩溃窗口去重 + 计数口径 + 实跑取证
status: DONE
created_at: 2026-10-09
updated_at: 2026-10-09
latest_recheck: .cursor/plans/rechecks/RECHECK-20261009-362-goal-041-ec02-04-bounded-retry-on-the-crash-window.md
memory_entries:
  - append-only-needs-a-tie-breaker-in-the-key
  - narrowing-an-existing-predicate-must-be-declared
parent_goal: GOAL-20261009-041
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261009-041 的 **EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**判定种类互不混用**（失败面去重与结论面
    去重各自可区分）；**上界在任意崩溃模式下都成立**；**缺省不重试**（逐字保持）；
    **取消不重试**；既有 `SUCCEEDED` 路径的判定**逐字保持**；**改既有判据必须走自证清单**
    （`MEM-20261009-210`：逐条枚举 + `numstat` 删除行读数 + 逐条谓词比对 + 收窄显式申报）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**声明的重试上界成为真的**：① 失败重试面按「**已用尝试数** = 落库行数 + 未落库的
    认领数 + 被阻塞的推进数」计数（崩溃窗口**也**计入）；② 已认领未落库 ⇒ `DEDUP_FAILED_RUN`
    （**不**再起第二个同序号 run，与结论面的 `DEDUP` **可区分**）；③ 判定序列**必然收敛**
    到 `STOP_RUN_FAILED`（步数 ≤ 声明上界）；④ 实跑 + 反证臂（无界重试不再出现；缺省路径
    逐字不变）；⑤ 收尾时新发现：决策**自然键碰撞静默丢弃**（同一时钟刻度下的多条决策互相
    顶掉）⇒ 驱动把 `decided_at` 归一为**该程序内严格递增**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察复核（读数逐条）**：在**未修**的树上复现「认领即崩 ⇒ 上界被绕过」：
      声明 `max_attempts_per_index=2`、连推 5 次全部 `RETRY_FAILED_RUN`、`attempts=1/2`
      原样不动、`bounded=false`。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal042_probe_unbounded_retry.py`
      ⇒ `unbounded_retry: true`（修前读数，见本 PLAN「证据」）。
    status: PASS
  - id: AC-2
    criterion: >-
      **去重与计数**：`_retry_face_state` 把「未落库的认领」与「被阻塞的推进」都计入
      已用尝试数；`DEDUP_FAILED_RUN` 分支**不**调用启动面（不产生第二个同序号 run）
      且判词点名认领的 run id。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py -q` ⇒ 18 passed
      （含新建的 5 例）。
    status: PASS
  - id: AC-3
    criterion: >-
      **判定面接线（三形态互不混用 + 有界收口）**：「用尽」判在「去重」**之前**
      （排序是硬的：去重是幂等约束、上界是硬约束 —— 反过来就永不收口）；
      `allowed ∈ {1,2,3,4}` 逐组实跑「认领即崩」⇒ 判定序列**必然**在**恰好 allowed 步**内
      收口到 `STOP_RUN_FAILED`，落库 run 始终只有一条（无第二个同序号 run）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal042_probe_retry_faces.py`
      ⇒ 四组 `converged=true` / `steps_within_bound=true` / `no_second_run=true`。
    status: PASS
  - id: AC-4
    criterion: >-
      **实跑取证 + 反证（含既有面无回归）**：新判据文件
      `tests/e2e/test_program_retry_bound_on_the_run_path.py`（6 例，经**既有 HTTP 面**）：
      收口 / 去重可区分且计入 / 缺省逐字不变 / **落库的重试仍走重试面**（不该红时不红）/
      紧循环里每次推进都留下决策；既有 e2e 全绿（`tests/e2e` **319 passed**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_program_retry_bound_on_the_run_path.py -q` ⇒ 6 passed。
    status: PASS
  - id: AC-5
    criterion: >-
      **两向反证（按压 ⇒ 必红 / 二进制复原 ⇒ raw `sha256` 相同）**：三条按压
      （`R-1` 分支顺序 / `R-2` 认领不计入 / `R-3` 挂钟不归一）**全部判红**，
      复原后 raw `sha256` **逐字节相同**；判词归档**进树**（`CR=0`）。
    verify: >-
      `scratch/goal041_press_cycle1.py` ⇒ `PRESS SUMMARY: ALL RED + RESTORED`；
      `.cursor/plans/goals/evidence/GOAL-20261009-041-press-two-way.txt`。
    status: PASS
  - id: AC-6
    criterion: >-
      **门与记录面**：四道门（`ruff format --check` / `ruff check` / `mypy` strict /
      **规模门**（函数 ≤ 50 行、文件 ≤ 450 行））对全部改动文件全绿；治理 `validate.py` 绿；
      主判据例数**只增不减**；m0 与 CI 结论见本 PLAN 末节。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py
      -q` ⇒ 全绿（`_failed_round` 60 行 ⇒ **拆函数**后合规）。
    status: PASS
---

# PLAN-20261009-361 — 序 9 cycle 1：失败重试面的崩溃窗口与有界计数

> **主线归属**：`GOAL-20261009-041`（MAINLINE 程序表**序 9**）的 **EC-02/EC-03/EC-04**。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察复核（修前读数：上界被绕过） | PASS |
| AC-2 | 去重与计数（认领即计入） | PASS |
| AC-3 | 三形态互不混用 + 有界收口（4 组上界） | PASS |
| AC-4 | 实跑取证 + 反证（新 6 例 + 既有面无回归） | PASS |
| AC-5 | 两向反证（3 条按压全红 + 二进制复原 raw sha256 相同） | PASS |
| AC-6 | 门与记录面（含规模门） | PASS |

## 实施清单

- [x] WP-1 立题复核：修前复现「认领即崩 ⇒ 上界被绕过」（`scratch/goal042_probe_unbounded_retry.py`）
- [x] WP-2 域：新增 `DEDUP_FAILED_RUN`（与结论面 `DEDUP` **同类不同面**）
- [x] WP-3 驱动：`_retry_face_state`（认领 + 被阻塞的推进都计入）；`_failed_round` 三形态分派
      （**用尽 → 去重 → 重试**，排序是判据的一部分）
- [x] WP-4 **本轮新发现的第二个缺陷**：决策自然键 `(program_id, after_index, decided_at)`
      在同一时钟刻度下**静默顶掉**（实测：紧循环连录 10 条 ⇒ 只留存 1 条）⇒ `_record`
      把 `decided_at` 归一为**该程序内严格递增**
- [x] WP-5 规模门：`_failed_round` 60 行 ⇒ 拆 `_bounded_stop` / `_returning_claim_stop`
- [x] WP-6 判据：驱动 5 例 + e2e 6 例（经既有 HTTP 面）
- [x] WP-7 两向反证：R-1/R-2/R-3 全红 + 二进制复原 + 归档进树（`CR=0`）
- [x] WP-8 门与台账：四道门 + 治理 + 全量 m0 + 台账

## 证据

### AC-1 修前读数（本轮要消灭的形态）

```
allowed=2 → decision_kinds = [RETRY_FAILED_RUN × 5]
            cited_facts   = [["state=FAILED","attempts=1/2"] × 5]
            bounded=false, unbounded_retry=true, runs_in_store=[[1,"FAILED"]]
```

### AC-3 修后读数（同一探针，四组上界）

| allowed | 判定序列 | 收敛 | 步数 ≤ 上界 | 第二个同序号 run |
| --- | --- | --- | --- | --- |
| 1 | `STOP_RUN_FAILED` | ✅ | ✅ | 无 |
| 2 | `RETRY_FAILED_RUN` → `STOP_RUN_FAILED` | ✅ | ✅ | 无 |
| 3 | `RETRY_FAILED_RUN` → `DEDUP_FAILED_RUN` → `STOP_RUN_FAILED` | ✅ | ✅ | 无 |
| 4 | `RETRY_FAILED_RUN` → `DEDUP_FAILED_RUN` ×2 → `STOP_RUN_FAILED` | ✅ | ✅ | 无 |

**对照臂（正常落库的重试，逐字不变）**：`allowed=1` ⇒ `STOP_RUN_FAILED`（started=0）；
`allowed=2` ⇒ `RETRY_FAILED_RUN` → `STOP_RUN_FAILED`（started=1）；
`allowed=3` ⇒ `RETRY_FAILED_RUN` ×2 → `STOP_RUN_FAILED`（started=2）。

### AC-4 定向套件

| 套件 | 读数 |
| --- | --- |
| `tests/application/run_orchestration/test_program_runner.py` | **18 passed**（原 13 + 5 新） |
| `tests/e2e/test_program_retry_bound_on_the_run_path.py`（新增） | **6 passed** |
| `tests/e2e` 全量 | **319 passed, 13 skipped** |
| `tests/domain/test_research_program.py` + `tests/adapters/sqlite/test_program_store_sqlite.py` | 全绿 |
| `tests/tooling/test_python_source_limits.py` | 全绿（规模门） |

### AC-5 两向反证

```
R-1: 按压 RED | sha 复原一致=True | c93a3f67953c     # 交换「用尽/去重」两分支 ⇒ 不收敛
R-2: 按压 RED | sha 复原一致=True | c93a3f67953c     # 认领不计入尝试数 ⇒ 上界被绕过
R-3: 按压 RED | sha 复原一致=True | c93a3f67953c     # 挂钟不归一 ⇒ 决策被静默顶掉
PRESS SUMMARY: ALL RED + RESTORED
```

归档：`.cursor/plans/goals/evidence/GOAL-20261009-041-press-two-way.txt`（199 B / `CR=0`）。

### AC-6 门与治理

- `ruff format --check`（`tests/` + `packages/` **864 文件**）/ `ruff check` / `mypy` strict 全绿；
- 规模门：`program_runner.py` **423 行**（上限 450）、函数全部 ≤ 50 行；
- 治理 `validate.py` 绿；
- **全量 m0 23/23**（在**全部记录写入之后**、独占、仓库 `.venv`、不接管道）：
  终局行 `PASS: profile=m0; 23 deterministic checks`（`PASS [` **24** / `FAILED [` **0** /
  **5278 passed, 228 skipped**）；
- **m0 抓到并已修的一处真红（如实登记）**：`python/typecheck` 在我**自己的**新判据上报
  **2 个 mypy 错误**（`Cannot infer type of lambda` + 两个 `Literal` 之间的
  `Non-overlapping identity check`）⇒ 按「修产品/判据优先，禁改门迁就」处置：
  把 lambda 换成具名函数、把恒真的枚举比较改成 `kind.value == "DEDUP"`（**断言实质未动**），
  复跑后 m0 23/23。
- CI：见本 PLAN 末节台账。

## 改既有判据的申报（承 `MEM-20261009-210` 的自证清单）

本 cycle 对**既有**判据的改动**只有一处**：

| 文件 | 改动 | 谓词比对 | `numstat` |
| --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | `test_decision_kinds_separate_conclusion_from_guardrail` 的期望集合 +1 条目（`"DEDUP_FAILED_RUN"`） | **谓词形态一字未改**（仍是 `kinds == {...}` 集合相等）；**纯加法登记**（新增枚举值必须进集合，否则该用例会红） | 见 RECHECK |

**结论面 / 取消面 / 重试面的既有断言全部未动**；`tests/e2e` 既有 3 个文件**未触碰**。

## 影响报告

- **Domain / API / schema 变化**：枚举 **+1**（`DEDUP_FAILED_RUN`）；**无**迁移
  （决策 kind 是 TEXT 列，无 CHECK 约束）；**无** DTO / OpenAPI 变化（kind 以 `str` 透出，
  前端未枚举它 —— 实测 `apps/web/src` 与 `services/api` 零引用）。
- **安全 / 凭据变化**：无（不动放行面）。
- **兼容性 / 迁移风险**：**低** —— 新增 kind 对旧读者是**未知字符串**（读面本就逐条给原文）；
  计数口径变化只影响**崩溃窗口**这一形态（正常落库路径读数不变，由对照臂实测）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `7c9b35c`（本 cycle = 本批 HEAD） | `37961452386` **M0 success**（8 job 全 success：`container-quality` / `collector-quality` / `console-frontend` / `observability-overhead-windows-latest` / `quality-ubuntu-latest` / `quality-windows-latest` / `observability-overhead-ubuntu-latest` / `eval-gate`）+ `37961452060` **Push on main / CodeQL success**（3 分析全 success） | 域 + 驱动 + 判据 + 归档 + 记录；**实测取证**（`total_count=2`） |
| （本行所在提交：台账尾巴） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 台账尾巴：只改 `.cursor/**` 记录；其结论由**下一个 cycle 的台账**取证 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | IN_PROGRESS | 修前读数取齐；域 + 驱动 + 判据落地；**发现第二个缺陷**（决策静默顶掉）并修；规模门拆函数。 |
| 2026-10-09 | DONE | 两向反证 3 条全红 + 二进制复原 raw `sha256` 相同；四道门 + 治理绿；`RECHECK-20261009-362` 独立复检。 |
