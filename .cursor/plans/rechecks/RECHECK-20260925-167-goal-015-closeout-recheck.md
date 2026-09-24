---
id: RECHECK-20260925-167
plan_id: PLAN-20260925-166
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-015-cycle3 + 独立只读复检脚本（tools/verify_goal015_closeout.py，零出网）
baseline_ref: 414f2e5（GOAL-015 起点前的基线：判据面逐字节对照的参照）
checked_head: 收口轮冻结树（PLAN-166 + 本记录 + GOAL 收口 + ALL_PLAN 投影）
---

# RECHECK-20260925-167 — GOAL-015 收口复检（EC-04）

## 检查范围

① 独立复检脚本是否**只读、标准库、不 import 仓库代码、零出网**且**两棵树同判据同结论**
（AC-1）；② **判据面逐字节未改**（AC-2）；③ 新判据里**没有 skip/xfail**，共享守卫的 skip
**按设计**且带 fail-closed（AC-3）；④ m0 的**可支持终态行**（as-is 与代管后**分开**写清）
（AC-4）；⑤ 13 条人工面 + 承继残余 + 本 GOAL 的 `W` 列表**原样保留**（AC-5）；⑥ GOAL 收口
（`ACHIEVED` / `latest_recheck` 相对路径 / CI 台账无未记账 run）（AC-6）。

## 检查结果

### 一、独立复检脚本（`tools/verify_goal015_closeout.py`）

- **六组判据**：产物在册（11 个交付物）/ 判据面逐字节（5 个文件对 `414f2e5` 基线）/
  无 skip 掩盖 + 守卫 fail-closed / GOAL 记录自洽（EC 状态、`latest_recheck`、
  `child_plans`、`memory_entries`、13 条人工面编号）/ 决策简报（六要素 + 对齐表 1..13）/
  CI 台账（每行带 run 链接）。
- **实现约束**：标准库（`argparse` / `subprocess` / `pathlib`）+ `git diff --quiet`；
  **不 import 任何仓库模块**、不读写网络、不产出任何文件。
- **两树成对（收口提交 `6f12842` 上实跑，**同判据同结论**）**：
  - 主树：`checked=123 failures=0`（exit 0）；
  - 干净 checkout（`git worktree add --detach 6f12842`）：`checked=123 failures=0`（exit 0），
    **无 `TIMING` 行**（即 EC-04 已 `PASS`）。
  - **时序项归零的实测**：收口记录落盘**前**，干净树会多一条「产物尚未落盘」（`tools/
    verify_goal015_closeout.py` 未提交）的差异；落盘后两树**逐项一致**。这正是 EC-04 允许的
    那一类差异，且**已验证归零**。

### 二、判据面逐字节未改（AC-2，脚本内判据）

`git diff --quiet 414f2e5 HEAD -- <path>` 全绿，覆盖 5 个判据面文件：

| 文件 | 为什么冻结 |
| --- | --- |
| `tests/egress_guard.py` | 出站结构判据（目的地判定 / 放行面） |
| `tests/application/test_m2_audit.py` | 镜像一致性判据（本轮点名**不得**改） |
| `tests/tooling/test_python_source_limits.py` | 450 行 / 50 行规模门禁阈值 |
| `.cursor/skills/system-spec-check/scripts/validate_bundle.py` | `R-3` 涉及的检查项（**只登记不改**） |
| `.cursor/skills/governance-check/scripts/validate.py` | 治理校验器 |

### 三、没有用 skip/xfail 掩盖（AC-3）

- 四条新判据（默认门隔离 / 隔离探针 / postgres 跳过加载无关 / 决策简报对齐）里
  **无** `mark.skip`、**无** `xfail`。
- `tests/postgres_guard.py` **按设计**会加 skip（PG 不可达）；脚本因此改判**另一件事**：
  它是否具备 **fail-closed** 出口（`RESEARCHOS_REQUIRE_POSTGRES` + `pytest.exit`）——
  「跳过」与「通过」在判词上必须分得开。

### 四、m0 可支持终态行（AC-4）

- **as-is**（不代管、原样工作树）：`FAILED: 1 check(s): framework/validate_bundle=1`，
  `23` 条 `PASS [` ⇒ **22/23**；唯一未绿项 = `R-3`（仓库外 gitignored 在制品），
  判词**只**点名 `scratch\self-governance-bootstrap-prompt.md`。
- **代管后**（`tools/quarantine_and_run_m0.py` 把该文件临时移出）：
  `PASS: profile=m0; 23 deterministic checks`；归还后 `size` / `mtime_ns` / `sha256`
  **全等**，脚本自带口径声明「本终态行取自**代管后的树**」。
- **口径纪律**：本记录**不**把代管后写成 as-is；two lines 逐字见
  `scratch/goal015-c3-m0-asis-final.log` / `scratch/goal015-c3-m0-quarantined-final.log`。
- **一条如实登记的装置教训**：本轮首次代管跑判红 `framework/validate=1` —— 原因是我**在 m0
  跑着的时候写了记录**（治理校验读到「任务未入 ALL_PLAN / 复检不存在」）。该轮**不作终态
  证据**，改为在**冻结树**上重跑；这正好实证了协议第 1 节的「m0 独占 + 不并发改工作树」。

### 五、残余逐条登记（AC-5）

- **13 条人工面**：`GOAL-015` 「不进入循环 / 需人工拍板」节原样保留（3 / 12 标注**已了结**，
  7 / 8 / 9 / 11 为**标准禁令**，其余为**待拍板**），并逐条映射进
  `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的对齐表（**双向对齐由判据强制**）。
- **承继残余**：`R-F1`（主观面须先操作化）/ `R-F2`（规模不足的诚实边界）/ `R-F3`（= 本 GOAL
  的 `R-3`）/ `R-M1`（Mimosa 钩子侧 `scanner_enobufs` **未得完整结论** ⇒ **不得**宣称项目安全）/
  `R-D1`（依赖告警 23 条：4 high / 13 moderate / 6 low）/ `R-B1` / `R-N1`（非 ASCII 路径豁免）
  —— **全部原样保留**。
- **本 GOAL 的 `W` 列表**：`W-1`（as-is 不可能 23/23，`R-3` 只登记）/ `W-2`（live 判据开门
  条件只登记，D-11）/ `W-3`（起点 (b) 承继归因被实测否证 ⇒ 真实缺陷已修，判据未动）/
  `W-4`（人工面原样保留）/ 本轮新增 `W-5`（**m0 跑着时写记录会判红**，见第 4 节）。

### 六、收口记录（AC-6）

- `GOAL-015`：`status: ACHIEVED`；EC-01…EC-04 全 `PASS`；`latest_recheck` =
  `.cursor/plans/rechecks/RECHECK-20260925-167-goal-015-closeout-recheck.md`（**仓库相对路径**）；
  `child_plans` = PLAN-161 / PLAN-164 / PLAN-166；`memory_entries` = MEM-130…133。
- **CI 台账**：建档 → cycle 1（红 → 根因已修）→ cycle 2（三次推送全绿）→ 收口推送，
  逐 run 记 id + 链接 + 六 job/CodeQL 结论。

## 警告与残余（原样保留）

- W-1…W-5（见第 5 节）+ 13 条人工面 + 7 条承继残余：**无一条以「已解决」口径掩盖**。
- `R-3` 是**唯一**指向门禁的条目（分类 (iii)），按授权**只登记**，进决策简报 **D-10**。

## 结论

- **结果**：`PASS_WITH_WARNINGS`。
- 四个 EC 全部 `PASS`，且每条关键主张都有**可复跑**的取证路径（判据 / 脚本 / 日志 / 两棵树的
  同判据复检）；**未改任何判据 / 门禁 / 阈值 / 策略面 / 依赖 pin / 运行时默认值**
  （由脚本对 5 个判据面文件的逐字节对照证明）。
