---
id: RECHECK-20261007-304
slug: goal-032-ec01-dead-letter-manual-recovery
title: 复检：GOAL-032 EC-01 死信人工恢复路径（ADR-0033 + 域出边 + 三实现 + 幂等/点名拒绝 + 两向反证 + 实跑）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-07
updated_at: 2026-10-07
plan_id: PLAN-20261007-303
reviewer: root-agent
parent_goal: GOAL-20261007-032
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py
    tests/adapters/sqlite/test_workflow_dead_letter_surface.py
    tests/e2e/test_dead_letter_recovery_full_loop.py -q ⇒ 12 passed（引擎面 8 + 既有面 3 + e2e 1）
  - >-
    RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os
    uv run --frozen --no-sync python -B -m pytest
    tests/contracts/test_dead_letter_manual_recovery_contract.py tests/postgres/test_outbox_pg.py -q
    ⇒ 12 passed（三实现同判，含 PG 实体）
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 EC-01 与 fix_policy。本复检**不改任何既有判据**（除
    GOAL-032 fix_policy 点名的四条同步）；「受判面不得被收窄」逐条自证（见下 `W-4`）。
---

# RECHECK-20261007-304：GOAL-032 EC-01 死信人工恢复路径

## 检查结果

七条 AC 逐条实测：

1. **ADR 依据（AC-1）**：`docs/adr/ADR-0033-dead-letter-manual-recovery.md` 在树、
   `Status: Accepted`；对照 `ADR-0030` 的 A–E 与它的机制观察写了「为什么不是别的选项」
   （不改状态机 / 新增独立状态 / 保持 `terminal()` 不含死信 / 新增事件 / 等 ADR-0030）。
   `tests/tooling/test_pending_validation_failure_registration.py` 绿 ⇒ **ADR-0030 仍是
   `Proposed`**、三处同源指针未断（本 ADR **不改**它）。
2. **恢复路径（AC-2）**：唯一出边 `(DEAD_LETTER, REQUEUE) → QUEUED`；Port `requeue`；
   三实现同判（契约面 7 passed 无 DSN / 12 passed 含 PG）。
3. **幂等 + 点名拒绝 + 终态（AC-3）**：第二次恢复被**点名拒绝**（消息含任务 id 与
   `QUEUED`），事件计数**取样在第二次之前**（`after_first = len(pending_outbox())`，
   承 GOAL-026 EC-03 的假绿教训）；恢复前 `acquire_lease` 仍点名拒绝死信；`DEAD_LETTER`
   仍在 `terminal()`；恢复后交付的 `fence > 死亡时的 attempt`（**不重置预算**）。
4. **实跑（AC-4）**：`max_attempts=1` ⇒ 真编排收敛 `FAILED` + 任务 `DEAD_LETTER`（attempt=1）；
   恢复前自动入口点名拒绝且状态一字不动；`requeue` 后回 `QUEUED`；重建续跑 ⇒ `SUCCEEDED`；
   终态全为 `SUCCEEDED`；事件链含 `task.retry_scheduled`；`runtime.execution_attempts == 2`。
5. **两向反证（AC-5）**：`P1_RED 3 failed, 5 passed`（摘掉出边）/ `P2_RED 5 failed, 10 passed,
   3 skipped`（点名拒绝改静默）/ `FINAL_MATCHES_BASELINE True`。**本轮的实测教训**：首版按压
   用 LF 模式匹配，而 `task_state.py` 是 CRLF ⇒ **替换静默未命中、`P1` 假绿**（"8 passed"）；
   改为行尾自适应后才真判红 —— 这正是 `MEM-20260927-152`（按压必须二进制 / 行尾不能想当然）
   的又一实例，已把该形态写进本复检与记忆。
6. **同步集（AC-6）**：四条逐条 —— ① `RUN_STATE_MACHINE.md`（迁移表 + 终态读法注）；
   ② `test_workflow_dead_letter_surface.py` 的**重新定基**（受判面**扩大**：断言从
   「所有事件非法」变为「恰有 `REQUEUE->QUEUED`、其余仍非法」，且仍逐一遍历**全部**事件）；
   ③ `test_state_machines.py` 的 `DEAD_LETTER + ENQUEUE` 参数行**逐字未动**（新事件名
   `REQUEUE` 不在该行 ⇒ 它继续合法地判「ENQUEUE 从死信出发非法」）；
   ④ `test_task_state_drivers.py` 的 `_DRIVEN_BY` 增列人工入口（该门禁要求"状态有驱动方或
   写明理由"，本状态**两种驱动都在**）。**其余 `tests/**` 既有文件零改动**。
   **⑤（m0 首跑追加）**：`tests/observability/test_privacy_exit_census.py` 的**出口分类清单** ——
   m0 的 `python/tests` 首跑判红于此（`未分类的非 canonical 出口:adapters/postgres/
   workflow_requeue.py [otlp_span]`）：该判据要求**每个新发射点被显式分类**（这正是它存在的
   意义）。处置 = 按**同类既有条目**的最小形态**追加一行**
   `ExemptProducer("adapters/postgres/workflow_requeue.py", EmitterKind.otlp_span,
   _REASON_POSTGRES)`（与兄弟模块 `adapters/postgres/workflow_engine.py` 的既有分类**同形
   同理由**：PG 组合根不在默认路径上）⇒ `git diff --numstat` = **+3 / -0**，**断言一字未改**。
7. **门与留档（AC-7）**：`ruff check` = `All checks passed!`；`ruff format --check` =
   `1124 files already formatted`；`mypy` = `Success: no issues found in 1107 source files`；
   规模门 `1125 passed`。**首轮被门抓到的自己的错**：PG 引擎加 `requeue` 后 **472 行 > 450**
   ⇒ 按本仓拆分先例（`SqliteWorkflowOps` 同形）抽出 `adapters/postgres/workflow_requeue.py`
   （mixin，52 行，**逐行搬运**）；e2e 主用例 **73 行 > 50 行函数门** ⇒ 拆成四个命名步骤
   助手。两处都是按门修，**未**放宽任何门。

## 警告（如实登记）

- **`W-1`｜恢复是「人工、单条、显式」，没有自动恢复**：超时自动重生、按 run 批量恢复、
  恢复的审批门（`require_approval`）**都不在**本 EC 内。§7 的 `manual recovery` 字面满足，
  但「无人值守的自愈」不是本 EC 的承诺。
- **`W-2`｜恢复后 run 的自动继续不在本 EC**：`requeue` 只把**任务**放回可交付面；
  run 若已停在终态 `FAILED`，要它继续跑仍需**人工** `POST /runs/{id}/resume`
  （run 级入口，见 EC-03 的覆盖度矩阵）。两者的协同（恢复任务后自动续跑对应 run）
  **只登记**、未实现。
- **`W-3`｜e2e 的「恢复前捞不回」是**机制级**证据**：本用例直接打自动交付入口
  （`acquire_lease` 的终态守卫）并断言点名拒绝 —— 这是**续跑最终必须经过的那一关**；
  它**没有**逐字复现一次完整的 `resume_rebuilt` 失败路径（那需要另一条 run 级装配，
  属 EC-03 的射程）。
- **`W-4`｜受判面变化的逐条自证**：本轮唯一「既有判据改动」= `test_workflow_dead_letter_
  surface.py` 的重新定基。**强度比较**：旧断言 = 遍历全部事件 × `pytest.raises`；
  新断言 = 遍历全部事件 × 收集合法集 + `legal == [REQUEUE->QUEUED]` 精确相等 +
  `terminal()` 成员断言（**多一条**）。受判面从「全部事件」到「全部事件 + 精确期望集」，
  **扩大**而非收窄；`pytest.raises` 的计数语义（"每个都非法"）被"合法集恰好一条"覆盖
  并更强。`git diff --numstat` 显示该文件 **+22 / -6**（重写该用例与重命名）。
- **`W-5`｜Fake 的起点差异**：Fake 的 `complete` 不跑 `disposition` ⇒ 它**没有**死信到达
  路径（与 `due_retry_task_ids` 同源的既有边界）。为此新增 `mark_dead_letter`（**测试
  装配面**）并在契约用例里**显式断言这条差异**；行为臂（真实失败→死信）只打两个持久化
  实现（引擎面 + e2e）。这是**扩张了一句**测试装配面，不是产品面。
- **`W-6`｜`requeue` 的尝试预算语义是**新增决定**：恢复**不重置** `fence_seq`（M16 单调性）
  也不回写 `attempt` ⇒ 恢复后若再次失败，会**再次**落回死信（人工可再恢复）。
  这条语义写在 ADR-0033 的决定 4 与 Port docstring；**未**逐条征询用户（属本季下放的
  决策权），若用户期望"恢复 = 重置重试预算"，那是**另一条**语义、需改 ADR 与本判据。
- **`W-7`｜按压的行尾陷阱（已修）**：首版反证脚本用 LF 模式匹配 CRLF 文件 ⇒ 静默未命中 ⇒
  `P1` 报 "8 passed"（**假绿**）。改为行尾自适应 + `assert pattern in original` 后真判红。
- **`W-8`｜m0 首跑的 `python/tests` 红（已修，属同步集第 ⑤ 条）**：新 PG 模块发射
  `otlp_span`，隐私出口普查要求每个新发射点被显式分类 ⇒ 按兄弟模块同形追加一行豁免
  （`+3 / -0`）。**这条红是判据在正常工作**（它逼一次「这个新出口算不算受判」的决定），
  处置是登记而非绕过。
- **`R-M1` 未收口**（不得宣称项目安全）；**投递语义仍非 exactly-once**（口径：
  at-least-once + idempotency + deduplication）。

## 反证

- **P1（摘掉恢复出边）**：`3 failed, 5 passed` —— 主判据、终态语义判据与契约面的
  「非死信起态被拒」同时判红（出边一没了，恢复类断言全部失效）。复原后 raw `sha256`
  回到 `3ab0bdf29e5b505501f21a42a38223948ea41b069cfc82b66635d4619946e2dc`。
- **P2（点名拒绝改静默）**：`5 failed, 10 passed, 3 skipped`。复原后 raw `sha256` 回到
  `ec56445c9e5dce45ce8e2b56bdcbe94363e257c65a168c1d67f735fe43b0a23d`。
- **首版按压的假绿（如实登记）**：LF 模式匹配 CRLF 文件 ⇒ 未命中 ⇒ `P1` 报 "8 passed"。
  行尾自适应后真判红。**这条已进 `W-7` 与记忆**。

## 结论

`PASS_WITH_WARNINGS`。七条 AC 全 PASS，两向反证与实跑留档齐备；`W-1`…`W-8` 如实登记
（`W-7` = 按压的行尾陷阱，见上）。**未**放宽任何既有判据的断言（唯一改动为**扩大**受判面
的重新定基）；**未**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
