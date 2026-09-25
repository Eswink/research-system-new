---
id: PLAN-20260925-178
slug: goal-016-closeout-recheck
title: GOAL-016 收口复检：两棵树同判据同结论 + m0 双终态行 + 13 项 D-NN 终态表 + 承继残余
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-016
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-016 的 **EC-06**：收口复检。① 独立复检脚本在**当前树 + 干净
    `git worktree` checkout** 上**同判据同结论**；② m0 到**可支持的终态行**
    （as-is 若仍因 `R-3` ⇒ **如实标注**是哪棵树 / 哪种跑法，**不得**含糊写成 23/23）；
    ③ 治理 `validate.py` 绿；④ CI 台账到终态（M0 六 job + CodeQL，含 `run_attempt`）；
    ⑤ **13 项 `D-NN` 终态表**落记录（每项：拍板结论 / 本轮是否实施 / 依据 / 不做会怎样）；
    ⑥ 承继残余**原样保留**。**本 PLAN 的边界**：除记录面外**零产品代码 / 零门禁 / 零判据 /
    零阈值 / 零依赖改动**；复检脚本落在 `scratch/`（gitignored、**不入库**）；
    未授权项（D-04 / D-05 / D-06 / D-10 / D-11 / D-13）**一律原样保留**。
    push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-179-goal-016-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-139-closeout-needs-two-trees-and-two-terminal-lines.md
---

# PLAN-20260925-178 — GOAL-016 收口复检（EC-06）

## 目标

把 GOAL-016 从「六个 EC 各自 PASS」变成**可独立复核的收口结论**：一个**不复用 GOAL 叙述**的
复检脚本，在**两棵不同的树**上跑出**同一个结论**；m0 给出**两个**终态行并各自身份明确；
13 项决定全部有终态；承继残余原样保留。

## 验收条件

- **AC-1｜复检脚本两树同结论**：`scratch/goal016-ec06-closeout-recheck.py --root <tree>` 在
  ① 当前工作树、② 干净 `git worktree` checkout 上**都**输出 `CONCLUSION failures=0`，
  且逐 EC 结论逐字相同。
- **AC-2｜脚本非恒真**：脚本在**终态表未落盘时**必须红（实测过：EC-06 报 13 条缺失）；
  ⇒ 它不是「怎么写都绿」的断言。
- **AC-3｜m0 双终态行**：**as-is** 如实给行（若仍因 `R-3` ⇒ 写 22/23 并点名红项）；
  **代管后**写 `PASS: profile=m0; 23 deterministic checks` + 逐字节复核一致。
  **两行各自身份明确，不得互相冒充。**
- **AC-4｜13 项 `D-NN` 终态表**：GOAL-016 在位，每项含「拍板结论 / 本轮是否实施 / 依据 /
  不做会怎样」，且与简报的 13 个条目**一一对应**。
- **AC-5｜治理与文档门**：`validate.py` = `Cursor 治理验证通过`；
  `DOCS-CHECK` = PASS。
- **AC-6｜承继残余原样保留**：`R-3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` 与 `W-7` 逐条在位、
  **未被**本 GOAL 收口或改写。
- **AC-7｜零越界**：本 cycle 的改动集**只含**记录面（`.cursor/`）与 `scratch/`（不入库）；
  **不含**产品代码、门禁、策略面、判据口径、阈值、依赖。

## 实施清单

- [x] WP1：写独立复检脚本 `scratch/goal016-ec06-closeout-recheck.py`
      （六个 EC 各自「结构断言 + 判据文件子进程实跑」两路同时成立才算 PASS）。
- [x] WP2：脚本先**红**取证（终态表未落盘 ⇒ EC-06 报 13 条缺失）⇒ 证明非恒真。
- [x] WP3：13 项 `D-NN` 终态表落进 GOAL-016（含「已实施 4 / 部分 2 / 未实施 6 + 1」汇总）。
- [x] WP4：当前树复检 ⇒ `CONCLUSION failures=0`（六 EC 全 PASS）。
- [x] WP5：as-is m0 ⇒ 如实终态行；代管 m0 ⇒ 23/23 终态行。
- [x] WP6：干净 `git worktree` checkout（`c50ee97`）复检 ⇒ **同结论**（去掉 pytest 耗时后
  `diff` 为空，两树都 `CONCLUSION failures=0` / `REALITY non_ascii=30`）；CI 台账到终态；承继残余清点。

## 证据（本地）

- **复检脚本（当前树）**：`scratch/goal016-c6-recheck-worktree.txt` ⇒
  ```
  EC-01 PASS :: 4 passed in 0.31s
  EC-02 PASS :: 4 passed in 0.04s
  EC-03 PASS :: 7 passed in 5.17s
  EC-04 PASS :: 6 passed in 0.23s
  EC-05 PASS :: （无判据文件：本 EC 的结论由结构断言承载）
  EC-06 PASS :: （无判据文件：本 EC 的结论由结构断言承载）
  CONCLUSION failures=0
  REALITY non_ascii=30
  ```
- **非恒真取证**：终态表落盘**前**同一条命令的输出里 `EC-06 FAIL` 并逐条报出
  「终态表缺 D-01 … D-13」（13 条）⇒ 表被删会被抓。
- **as-is m0**：`FAILED: 1 check(s): framework/validate_bundle=1`
  ⇒ **22/23**，唯一红项 = `R-3`。日志 `scratch/goal016-c6-m0-as-is.log`。
- **代管 m0**：`PASS: profile=m0; 23 deterministic checks`（逐字节复核一致）。
  日志 `scratch/goal016-c6-m0-quarantined.log`。
- **干净 checkout 复检**：`git worktree add <tmp> c50ee97`（`HEAD is now at c50ee97`）⇒
  `--root <checkout>` 跑同一脚本 ⇒ `CONCLUSION failures=0`，
  留档 `scratch/goal016-c6-recheck-clean-checkout.txt`；与工作树的输出
  **去掉 pytest 耗时后 `diff` 为空**。收口后 `git worktree remove --force` 清理。
  **前提**（为什么这不假绿）：`.venv` 里**没有**本项目的 editable 安装、也**没有**指向仓库的
  `.pth` ⇒ 导入只能经 `pyproject.toml` 的 `pythonpath = ["."]`（rootdir）⇒
  checkout 里跑的就是**那棵树自己的代码**。
- **m0 双行的判据**：`PASS [` 行数在 as-is = **23**（22 项过 + 计数外的
  `release-assets-immutable`）、在代管后 = **24**（23 项过 + 计数外的那一项）
  ⇒ 两个终态行**分别**对应 22/23 与 23/23，**不可互换**。
- **治理门**：`validate.py` ⇒ `Cursor 治理验证通过`。
- **doc 门**：`DOCS-CHECK PASS: 6 deterministic checks`。

## 残余（本 PLAN 不处置，原样保留）

- **`R-3`**（门禁 scoping：`validate_bundle` 扫到仓库外的 `scratch/` 文件）
  ⇒ as-is 本机 m0 **22/23**。属 **D-10**，**需另行授权**；本 GOAL 只引用。
- **`R-M1`**（hook 面安全结论）与 **`R-D1`**（依赖告警未清部分）**原样保留**；
  D-12(b) 的第 6 节**明确不覆盖**它们（6.3 第 8 条）。
- **`R-B1`**（四个 450 行零余量文件）与 **`R-N1`**（非 ASCII 历史路径）**原样保留**；
  后者由 `ADR-0032` 记录豁免（**不重命名**）。
- **`W-7`**（live 判据会真出网、结论随环境变）**原样保留**；本 GOAL **未**改任何
  live 开关语义（属 **D-11**）。
- **未授权六项**（D-04 / D-05 / D-06 / D-10 / D-11 / D-13）**原样保留**为下一轮输入。
- **D-03 未清部分**：`undici`（主版本跳跃，8 条告警）、`yaml`（non-high，1 条）
  ⇒ 升级后 open 告警 **9**（0 high / 7 medium / 2 low），**未**清零。
- **`ADR-0031` 仍 `Proposed`**（D-07 维持）⇒ `tool_pack.*` 的开口问题**仍未拍板**。
- **授权面空白仍在**（D-12 只做了 (b)）⇒ 控制面**无认证**这一事实**未**被修复。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-06 圈定收口范围，本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP3：复检脚本落盘；先红取证（13 条缺失）；13 项终态表落 GOAL-016。 |
| 2026-09-25 | IN_PROGRESS | WP4–WP5：当前树复检 `failures=0`；m0 双终态行取到（as-is 22/23 = `R-3`；代管 23/23）。 |
| 2026-09-25 | DONE | WP6：**AC-1 两棵树同结论**（工作树与 `c50ee97` 的干净 `git worktree` checkout；去掉 pytest 耗时后 `diff` **为空**）⇒ 7 条 AC 全成立。复检 `RECHECK-20260925-179` 见 `latest_recheck`。 |

## 影响报告

- **改动**：**只有记录面**（`.cursor/plans/`、`.cursor/memory/`）+ `scratch/` 的复检脚本与日志
  （`scratch/` 被 gitignore ⇒ **不入库**）。**无产品代码 / 门禁 / 判据 / 阈值 / 依赖改动**。
- **lint / typecheck / test**：无源码改动 ⇒ 不适用；治理 `validate.py` = 通过；
  `DOCS-CHECK` = PASS；m0 = 两个终态行（as-is 22/23 = `R-3`；代管 23/23）。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：无。**未**宣称任何安全改进——`D-12` 只做了文档级 (b)。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无（本 cycle 未动 pin）。
- **下一项任务**：GOAL-016 收口后，下一轮的输入 = **未授权六项 + `D-03` 未清三条 +
  `ADR-0031` 仍未拍板 + 授权面空白**（见「残余」）。
