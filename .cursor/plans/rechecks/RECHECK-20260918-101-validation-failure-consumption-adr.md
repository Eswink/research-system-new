---
id: RECHECK-20260918-101
plan_id: PLAN-20260918-101
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle2
baseline_ref: 447059f
checked_head: worktree
---

# RECHECK-20260918-101 — 验收门拒收的处置（GOAL-006 cycle 2 = EC-02 (b)）

## 检查范围

PLAN-20260918-101 声称的交付面：ADR 草案（`docs/adr/ADR-0030-validation-failure-consumption.md`，
Status: Proposed）、权威登记（`docs/INDEX.md`）、三处声明面同源指向同一份决策、
把这份登记钉成判据的用例。

**不在本轮**：EC-02 的 (a) 分支（在既有 canonical 边界内实现按声明处置）——勘察判定它被
终态边界挡住（见下）；`on_validation_failure` 的执行期语义本身（属待拍板决策）；
canonical 状态机 / Accepted ADR **未动**（也不允许在本循环内动）。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| (a) 是否真的不可行（先探明） | 读 `packages/domain/task_state.py` 的 `_TRANSITIONS` 与 `terminal()` | PASS（`SUCCEEDED` 是终态、**无**出边；`DEAD_LETTER` 只能从 `RETRY_SCHEDULED` 到达 ⇒ 按声明改写已成功的行必须新增"从终态出发的迁移"或新状态 = canonical 边界） |
| 事实 1：拒收在 durable 成功之后 | 读 `task_executor._attempt_once`（`engine.complete(...)` 在 `register_and_gate` 之前） | PASS |
| 事实 2：拒收只落 run 级 | 读 `task_phase_helpers.failure_step` → `deps.fail` → `phase_runner.fail` → `run_terminals.publish_failed_run`（`run.failed`，message 含 "rejected by acceptance gate"）；`on_task_failure: CONTINUE` 时走 `publish_degraded_run`（`tolerated_failures[].message` 同句） | PASS（两条分支都不改任务行） |
| AC-01 ADR 草案在位且实质 | 读 `docs/adr/ADR-0030-...md` | PASS（`Status: Proposed`；含 Context / Decision needed / Options A–E（逐个代价与收益）/ Why not now / Trigger / Consequences / Evidence） |
| AC-02 权威登记 | 读 `docs/INDEX.md` | PASS（条目含 ADR 文件名与 `Proposed`） |
| AC-03 同源收敛 | 反向搜索 `on_validation_failure`：产品/文档/示例命中逐处对照 | PASS（`failure_policy.py` docstring / `TASK_HANDOFF.md` §2.1 / `examples/contracts/task_contracts.yaml` 三处均提到该键**且**指向 ADR-0030；仓库其余命中为 `.cursor/**` 记录与用例，均属"消费者/说明"两类） |
| AC-04 判据可判定 | `tests/tooling/test_pending_validation_failure_registration.py`（4 条：Proposed / INDEX 登记 / 三处指针 / 未消费仍是声明） | PASS（**4 passed**） |
| AC-04 反证（实跑） | ① 删掉 `task_contracts.yaml` 的 ADR 指针 ⇒ 期望第 3 条红；② 把 ADR 的 `Status` 改成 `Accepted` ⇒ 期望第 1 条红 | PASS（① `AssertionError: task_contracts.yaml 必须指向同一份决策记录（同源收敛）`，**1 failed / 3 passed**；② `AssertionError: 草案必须是 Proposed：它还没被人工拍板`，**1 failed / 3 passed**；两次都还原 ⇒ **4 passed**） |
| AC-05 未越界 | `git diff` 检查 `task_state.py` / Accepted ADR / 迁移 / 依赖 | PASS（零改动：只新增 1 个 ADR、改 3 处文档/注释、加 1 个用例文件、`docs/INDEX.md` 加 1 行） |
| AC-05 门禁 | 定向 + 规模门禁 + 文档门 + lint/format/mypy | PASS（见「反证与实测」） |

### 交付物在位（结构证据）

- `docs/adr/ADR-0030-validation-failure-consumption.md`（**新增**，Proposed）。
- `docs/INDEX.md`：ADR 列表新增 `adr/ADR-0030-...` 条目（写明 Proposed）。
- `packages/domain/failure_policy.py`（docstring 增"待拍板的决策在哪"段）、
  `docs/architecture/TASK_HANDOFF.md` §2.1（ADR 指针）、
  `examples/contracts/task_contracts.yaml`（注释里的 ADR 指针）。
- `tests/tooling/test_pending_validation_failure_registration.py`（**新增判据**）。

## 反证与实测

1. **反证 ①（指针）**：删 `task_contracts.yaml` 里的 ADR 指针 ⇒
   `test_every_declaration_surface_points_at_the_same_record` **failed**（其余 3 条绿）；
   还原 ⇒ **4 passed**。
2. **反证 ②（状态）**：把 ADR 的 `Status: Proposed` 改成 `Accepted` ⇒
   `test_the_decision_record_is_a_proposal_not_a_decision` **failed**（其余 3 条绿）；
   还原 ⇒ **4 passed**。
3. **定向**：`tests/domain tests/loaders tests/tooling tests/application/run_orchestration`
   **1537 passed**（9.65s，含规模门禁与既有"声明不改变行为"用例）。
4. **规模门禁**：`tests/tooling/test_python_source_limits.py` 在上一批内全绿
   （新用例 61 行，远低于阈值）。
5. **风格/类型**：`ruff format --check` **938 files already formatted**；
   `ruff check` **All checks passed**；`mypy` **Success: no issues found in 928 source files**。
6. **文档门**：`tools/docs_consistency_check.py` **DOCS-CHECK PASS: 6 deterministic checks**。
7. m0 全量 23 项：见 GOAL-006 迭代日志 cycle 2 行。

## 告警（W）

- **W-1（"待拍板"不是"已解决"）**：本 PLAN 交付的是**决策记录**，不是消费。`on_validation_failure`
  的行为与基线**逐字相同**（声明被点名、不改变判定）。EC-02 的 (b) 分支允许这个终态，
  但不得读作"验收门拒收已有处置"。任何人要把它读成"已解决"，先看 ADR-0030 的
  `Status: Proposed`。
- **W-2（选项 D 的可行性未验证）**：ADR 里把"把门挪到 durable 完成之前"列为可能**不需要**
  新增终态迁移的路径，但那是**分析**，不是实测：门的输入面（`registration`：artifact/evidence
  入册）是否依赖"任务已成功"这一状态、失败路径上的租约与事件次序如何，都还没验。
  拍板前必须先做一次只读验证轮。
- **W-3（历史行未回溯标注）**：既有 run 里"已被门拒收但任务行 `SUCCEEDED`"的行**没有**标记；
  今天只有 run 级事件 message 能读出来。ADR 的 Context 已登记这一点，但没有盘点**存量**
  有多少条（无查询、无数字）。若拍板选 A/B/D，需要先做一次存量盘点。
- **W-4（判据的射程是"同源"，不是"正确"）**：新用例钉的是"三处指向同一份记录 + 该记录
  仍是 Proposed + 键仍未被消费"。它**不判断** ADR 里的选项分析是否正确、代价估计是否准确
  ——那是人的判断。
- **W-5（`ADR-0030` 编号占用）**：ADR 编号按目录内最大号 +1 取（0029 → 0030），仓库没有
  编号权威登记表；若将来有人并行新增 ADR，需自行避免撞号（本节如实登记，不改流程）。

## 结论

**PASS_WITH_WARNINGS**。EC-02 走 (b)：`SUCCEEDED` 的终态无出边这一事实把 (a) 挡在
canonical 边界外（不自行扩大边界）；本轮的交付是**把待拍板的决策写成可决策的形态**——
ADR-0030（Proposed）给出四条可复核事实、五个选项（含"把门挪到 durable 完成之前"这条
不破坏终态语义的路径）与各自代价、以及何时必须拍板；`docs/INDEX.md` 给了唯一入口；
三处声明面同源指向它；一条读真实文件的用例把这份登记钉住，两次反证各红一条（指针 /
状态），还原后全绿。产品行为、canonical 状态机、Accepted ADR、迁移与依赖**零改动**。
W-1…W-5 是适用边界：待拍板≠已解决、选项 D 未实测、存量未盘点、判据只钉同源不钉正确、
ADR 编号无权威登记表。

## 门禁

- 定向 / 规模门禁 / 文档门 / 风格类型：见「反证与实测」第 3–6 条。
- m0 全量 23 项：见 GOAL-006 迭代日志 cycle 2 行。
