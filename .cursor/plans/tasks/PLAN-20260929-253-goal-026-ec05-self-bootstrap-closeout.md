---
id: PLAN-20260929-253
slug: goal-026-ec05-self-bootstrap-closeout
title: GOAL-026 cycle 5（EC-05）：自举收口 — 收口验证器 + 台账审计下界（行为判据）+ IN_SCOPE 纯收紧 + 两树复检
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-026
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-026 的 **EC-05**（自举收口：复用 GOAL-022 / 023 / 024 / 025 的机器，
    把本轮五条 EC 的判据面钉进**可复跑的收口验证器**，并给 CI 台账审计补上
    「**空集合 / 低于下界 ⇒ 未取证**」的**行为**下界）。授权沿用该 GOAL 的 `authorization.ref`：
    「**新增判据**（一律落 `tests/**` ⇒ m0 条数仍 `23`）」+「新增脚本落 `tools/` **必须**显式加入
    `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）」+
    「文档同源更新」；push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**两个脚本 + 在 `IN_SCOPE` 里**追加两行**（纯收紧：清单变长、
    射程变大，**不放宽**任何既有约束）；**不修改**任何既有判据 / 门禁 / 阈值 / 放行面
    （点名：`tools/two_tree_recheck.py`、`tools/closeout_recheck_assertions.py`、
    `tools/verify_goal023/024/025_closeout.py`、`tests/tooling/test_tooling_scripts_meet_product_gates.py`
    的既有条目、`tests/egress_guard.py`、三道记录面判据、规模门）；**不改** `PRODUCT_ROOTS` /
    m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；**全离线**（不触网、不跑真实 runtime /
    tool provider / 凭据）；测试与夹具一律**合成值**；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称 exactly-once（口径只能是 at-least-once + idempotency + deduplication）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口验证器进树并复用公共面**：新增 `tools/verify_goal026_closeout.py`，
      公共判词（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽）
      **一行都不重写** —— 直接调用 `tools/closeout_recheck_assertions.py::standard_verdicts`；
      本文件只写 GOAL-026 特有断言；协议与两树入口一致（`--root` / `--verdict-only`，
      判词行只有 `PASS` / `FAIL` 且**不含任何树的绝对路径**）。
    status: PASS
  - id: AC-2
    criterion: >-
      **逐 EC 的两向判据面**：五条 EC 的判据文件**在树**且**例数 ≥ 下界**（缺文件、例数掉下去，
      两向都判红）；钉住的常量逐条断言：退避轨迹 `[30, 60, 100, 100]`、工具面与补偿面扫描下界
      `400`、投递语义面四个有界常量（豁免上限 `8` / 扫描下界 `2500` / 分类下界 `16` /
      CJK 正控制下界 `8`）+ 豁免表在上限内且理由非空。
    status: PASS
  - id: AC-3
    criterion: >-
      **EC-03 的产品修复被 AST 钉住**：`adapters/relay/gateway.py::_consult_circuit` 的
      `except CircuitBreakerTransitionError` 分支必须**抛** `CircuitOpenRelayError`
      （fail-closed）；按压 P2 把它改成 `pass` ⇒ 该判词判红，且 EC-03 判据文件自己那条行为用例
      同时判红（两条独立面同向）。
    status: PASS
  - id: AC-4
    criterion: >-
      **台账审计的下界判定是行为判据**：新增 `tools/audit_goal026_ledger.py`
      （`MIN_JOBS = {"M0 Quality Gates": 8, "Push on main": 3}`、`EMPTY_SET_MARK = "未取证"`），
      验证器用**合成输入**跑它四种形态：空 `jobs` ⇒ 判红且输出含「未取证」、欠数集（2 条）⇒ 判红且
      含「未取证」、有失败 job ⇒ 判红且**点名**该 job、完整集（8 条）⇒ 判绿（`failed=0`）；
      按压 P1 把空集分支改成 `return None` ⇒ 唯一红行恰是 `ec05-audit-empty-jobs`
      （**源码里写着下界文案不算证据**）。
    status: PASS
  - id: AC-5
    criterion: >-
      **射程纯收紧 + 与树根无关**：两个新脚本显式加入 `IN_SCOPE`（清单变长 = 射程变大，
      无任何既有条目被删改），验证器断言 `IN_SCOPE` 含入口 / 标准断言集 / 本验证器 / 审计器
      四者，并断言两个新脚本里**没有盘符绝对路径**；两件新工具自身过四道门
      （`ruff format --check` / `ruff check` / `mypy` / 规模：文件 ≤ 450 行、函数 ≤ 50 行）。
    status: PASS
  - id: AC-6
    criterion: >-
      **记录自洽与残余在位**：GOAL 的 EC-01…EC-04 已是 `PASS`、EC-05 取 `PASS ∪ PENDING`
      （时序，不是放宽）、`latest_recheck` 是**仓库相对路径**且可解析、`child_plans` /
      `memory_entries` 无空项；承继残余（12 条 + `G24-1`…`G24-6`，含「需用户拍板」）与
      本轮 6 条 `R26-*`、未覆盖范围五条、**九项义务判定表**逐条在位；台账 run id 有下界（≥ 8）。
    status: PASS
  - id: AC-7
    criterion: >-
      **两树复检 + as-is m0 + 治理 + CI 台账到终态**：`tools/two_tree_recheck.py`
      跑当前树 + 干净 checkout ⇒ 逐行相同 + `sha256` 相同（留档**二进制写盘**）；
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（**跑在记录写入之后**，
      承 MEM-145）；`tools/docs_consistency_check.py` 与治理 `validate.py` 绿；
      CI 到终态（八 job + CodeQL 3/3 + `run_attempt`），台账审计在**本轮证据**上
      `--prefix goal026-c5- --expect-sha <本轮 sha>` ⇒ `rc=0`。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-254-goal-026-ec05-self-bootstrap-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-172-closeout-tools-reuse-standard-face-and-behavioural-floor.md
  - .cursor/memory/entries/MEM-20260929-173-mimosa-git-gate-is-client-side-and-repo-wide.md
---

# GOAL-026 cycle 5（EC-05）：自举收口

## 目标

把前四条 EC 的判据面 **钉进可复跑的收口验证器**（不是靠散文），并给 CI 台账审计补上
GOAL-025 暴露的那条缺口：**空集合 = 未取证**（旧脚本 `scratch/audit_goal025_ledger.sh`
对空 `jobs` 无条件打 OK）。两条都必须**自举**：验证器本身进 `IN_SCOPE`、过四道门，
审计器的下界判定必须由**行为**判据（合成输入 + 按压）证明，而不是「源码里写了 `if not jobs`」。

## 验收条件

- [x] **AC-1 收口验证器进树并复用公共面**（`standard_verdicts` 一行不重写）。
- [x] **AC-2 逐 EC 两向判据面 + 常量钉住**（5 条 EC 的文件与例数下界 + 6 组常量）。
- [x] **AC-3 EC-03 产品修复被 AST 钉住**（fail-closed 分支 + 按压 P2 两向）。
- [x] **AC-4 台账审计下界 = 行为判据**（四种合成输入 + 按压 P1）。
- [x] **AC-5 射程纯收紧 + 与树根无关 + 两件工具自身过四道门**。
- [x] **AC-6 记录自洽与残余在位**（含九项义务判定表）。
- [x] **AC-7 两树复检 + as-is m0 23/23 + 治理 + CI 台账到终态**。
      全部成立：as-is m0 = `PASS: profile=m0; 23 deterministic checks`（推送后、记录写完之后跑）；
      治理 `validate.py` 与 `DOCS-CHECK` 绿；**两树复检 `TWO-TREE PASS`**（48 判词、
      两路 `sha256` 同为 `6da43133…a731`、留档逐字节相同）；**CI 到终态**
      （M0 `36550736379` 八 job 全 `success` + CodeQL `36550735603` 3/3、`run_attempt=1`）
      并按台账审计（本轮 `--expect-sha 6508d9d…` = `runs=2 failed=0`；全量 c0…c5 = `runs=12 failed=0`）。

## 实施清单

- [x] **WP-1**：写 `tools/verify_goal026_closeout.py`（复用标准断言集 + 本轮特有断言）。
- [x] **WP-2**：写 `tools/audit_goal026_ledger.py`（空集 / 低于下界 ⇒ 判「未取证」）。
- [x] **WP-3**：两个新脚本追加进 `IN_SCOPE`（**纯收紧**）。
- [x] **WP-4**：两件新工具过四道门（`ruff format --check` / `ruff check` / `mypy` / 规模）。
- [x] **WP-5**：按压 P1（空集分支返回 `None`）/ P2（吞掉半开预算耗尽）⇒ 判红；
      raw `sha256` 逐字节复原 ⇒ 48 PASS / `rc=0`；留档
      `scratch/goal026-ec05-press-matrix.log`（二进制写盘）。
- [x] **WP-6**：台账证据补齐（c0…c4 逐 run 的 run / jobs 原始 JSON）+ 按轮次 `--prefix`
      + `--expect-sha` 审计 ⇒ `rc=0`。
- [x] **WP-7**：写 `RECHECK-20260929-254` + `MEM-20260929-172`；回写 GOAL-026
      （EC-05 = PASS、九项义务判定表、迭代日志、CI 台账、状态历史、`status: ACHIEVED`）；
      投影 `ALL_PLAN` / `INDEX`。
- [x] **WP-8**：两树复检（当前树 + 干净 checkout，逐行 + `sha256`）+ 收口**补记**提交。

## 证据

- **实跑（收口复检本身）**：`uv run --frozen --no-sync python -B
  tools/verify_goal026_closeout.py --root . --verdict-only` ⇒ **48 行判词、`PASS` 48、`FAIL` 0、
  `rc=0`**（日志 `scratch/goal026-c5-verify.log`）。首轮**抓到本人两处错报**：
  `ec02-cases-floor`（我把退避轨迹文件的例数写成 3，实测 **2**）与 `ec02-trajectory-pinned`
  （常量是 `list`，我按 `tuple` 比 ⇒ 形态误判）—— 两处都改**判据侧**、未放宽断言。
- **按压 P1（审计器空集分支）**：`return None` ⇒ 唯一红行
  `FAIL ec05-audit-empty-jobs -> rc=0`、`rc=1`；复原后 sha256 =
  `11f5462beb0f8069d0f4b6a9371e2c0715a292d72baf68e70568af340372cdf2`（与基线逐字节相同）⇒ 48 PASS。
- **按压 P2（`gateway._consult_circuit` 吞掉迁移异常）**：`FAIL ec03-probe-budget-fail-closed
  -> 不再 fail-closed`，且判据文件实跑 `1 failed, 4 passed`
  （`test_exhausted_half_open_probe_budget_denies_without_touching_downstream`）；复原后
  sha256 = `bc1b29bb2cd194adefde1216e950679a01aa2316f3f1370164cb8062b46752f6`（与基线逐字节相同）；
  受影响套件 `1240 passed`。
- **四道门（两件新工具）**：`ruff format --check` = `2 files already formatted`；
  `ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；
  规模 = **449 行** / **201 行**（上限 450），函数均 ≤ 50 行。
- **工具面套件**：`pytest tests/tooling -q` ⇒ **1235 passed**（含 `IN_SCOPE` 收紧后的
  逐脚本四道门与规模门）；`tests/adapters/relay/test_gateway_half_open_budget.py`
  + `tests/tooling` ⇒ **1240 passed**。
- **台账审计（行为面）**：合成输入四形态 ⇒ `PASS`（空集与欠数集判红且含「未取证」、
  失败 job 被点名 `j7`、完整集 `failed=0`）；真实台账 ⇒
  `--prefix goal026-c4- --expect-sha 4cbe16d3e5…` = `PASS ledger-audit runs=2 failed=0`，
  全量（c0…c4）= `PASS ledger-audit runs=10 failed=0`（逐 run `run_attempt=1`）。
- **首轮被门抓到的本人错误**（如实记录）：`audit_goal026_ledger.py` 首版有 1 处超长行、
  1 处未用 import、`audit_pair` 复杂度 11 > 10；`verify_goal026_closeout.py` 首版 616 行
  超 450 上限 + 1 处 5 层嵌套 —— 全部按门修（拆 `run_problem` / `jobs_problem`、
  合并 `handler_denies`、复用 `standard_verdicts` 减重到 **449 行**），**未**放宽任何门。

## 阻塞与解除（提交曾被环境级安全门禁拒绝；已按用户拍板解除）

**AC-1…AC-6 已成立**（实跑证据见「证据」节）；**AC-7 的前三项已成立**
（as-is m0 23/23、治理绿、`DOCS-CHECK` 绿），**后两项曾不可达**：

1. **两树复检**（`tools/two_tree_recheck.py`）需要「当前树 + 干净 checkout」两路可复现的
   判词与 `sha256`；干净 checkout 要取**本轮的收口提交** —— 提交不存在 ⇒ 无法取证；
2. **CI 台账到终态**需要推送，推送同样被门禁拒绝 ⇒ 无 run 可记（**空集合 = 未取证**）。

**阻断证据**（留档 `scratch/goal026-c5-commit-block.log`，二进制写盘）：

- `.git/hooks/` 无任何已安装钩子 ⇒ 拦截来自 ZCode 客户端层的 Mimosa Git 门禁；
- **仓库级判定**：只暂存两个新工具 ⇒ 拒；`git commit --allow-empty`（零改动）⇒ 拒；
  `git reset` 清空索引后再 `--allow-empty` ⇒ 拒 ⇒ **任何提交都无法落地**；
- 点名的高危 finding 全在既有的、非本轮改动的、gitignored 资产
  （`scratch/keycheck_agnes_surfaces.py:81,96`、`scratch/verify_goal012_c2.py:143`，
  后者属 GOAL-012 的取证资产）；**本轮新工具自身扫描干净**；
- 同一环境的 `4cbe16d` 此前提交成功 ⇒ 阻断在本轮内出现。

**解除（用户 2026-09-29 拍板「按清理归档处置」）**：

| 路径 | 实测 | 处置 |
| --- | --- | --- |
| `mimosa policy init` + `.mimosa/security-policy.json` 的 `threatModel.exclusions` 有界豁免 | **无效且有害**：exclusions 不抑制 finding（`mimosa scan` 与 git 门禁均照旧点名）；且默认 `command.forbidShell` 把 `RegExp#exec` 误判为「Shell 执行策略违反」⇒ 高危 **3 → 7**（新增 4 条落在产品文件 `apps/web/src/features/example-console/reference/YamlView.tsx`） | **已回退**（删除策略文件，复测回到 3 条高危） |
| **清理归档** | **有效**：两文件 tar 归档到仓库外 `/d/research-system-gate-archive/flagged-probes-20260929.tgz`（含原 mtime；归档 sha256 `fb2e840a…fd16b`；两份原文件 sha256 记在 `scratch/goal026-gate-archive-baseline.sha256`）⇒ 移除后门禁放行 | **采用** |

**为什么归档而不改写**：两者都是一次性取证探针（`verify_goal012_c2.py` 是
GOAL-20260923-012 / PLAN-142 / RECHECK-143 的留档资产）⇒ 改写会改掉取证语义；
归档保留字节 + 哈希 + 位置，证据链可追溯，且**未修改任何既有记录**。

**残余**：解除后 git 门禁报过一次「没有得到完整扫描结论（`scanner_enobufs`），本次按兼容策略继续」
—— 即 `R-M1` 仍在（**不得**据此宣称项目安全）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | DONE | AC-1…AC-7 全部成立且有实跑证据。交付 = `tools/verify_goal026_closeout.py`（449 行）+ `tools/audit_goal026_ledger.py`（201 行）+ `IN_SCOPE` 追加两行（纯收紧）+ `WORKFLOW_RELIABILITY.md` §10；`RECHECK-20260929-254` = `PASS_WITH_WARNINGS`（`W-1`…`W-6`）；沉淀 `MEM-20260929-172` / `MEM-20260929-173`。提交 `6508d9d`（本文件所在的**实施 + 记录提交**，批量一次推送）。**零产品代码改动**。 |
| 2026-09-29 | BLOCKED | （历史行）AC-7 后两项因**提交被环境级安全门禁拒绝**而不可达；工件全部留在工作树、未提交、未推送。本文件初稿曾写 `DONE` + `PASS_WITH_WARNINGS`，在**同一工作树内**按「未实跑不得记 PASS」改为 `BLOCKED` + `BLOCK`（该更正发生在任何提交之前）。 |
| 2026-09-29 | BLOCKED→IN_PROGRESS→DONE | 用户拍板处置两个高危 scratch 资产 ⇒ 采用**清理归档**（策略豁免一路经实测无效且有害，已回退）⇒ 门禁放行 ⇒ 推送 `6508d9d`、CI 到终态、两树复检补齐 ⇒ 恢复为 `DONE`。 |

## 影响报告

- **改动**：新增 `tools/verify_goal026_closeout.py`（449 行）与 `tools/audit_goal026_ledger.py`
  （201 行）；`tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` **追加两行**；
  记录面（PLAN / RECHECK / MEM / GOAL / ALL_PLAN / INDEX）。
- **lint / typecheck / test**：四道门全绿；`tests/tooling` 1235 passed。
- **Domain / API / schema 变化**：**无**（两个脚本只读树内文件与正则可字面求值的常量）。
- **安全 / 凭据变化**：**无**（台账 JSON 里的 `head_sha` 与 run id 是公开 CI 元数据；
  令牌只经 `git credential fill` 取用、不落盘、不写进记录）。
- **兼容性 / 迁移风险**：`IN_SCOPE` 变长 ⇒ 该判据的**射程变大**（属收紧）。
  风险：`tools/` 仍是「不进 `PRODUCT_ROOTS`」的历史面 —— 本轮只把**新脚本**纳入，
  历史 37 个脚本的状态原样保留（GOAL-023 `W-1`）。
- **上游版本影响**：**无**（零新依赖，只用标准库 `ast` / `json` / `re` / `subprocess` / `tempfile`）。
- **未覆盖范围与残余**：台账审计**不覆盖** `scratch/` 之外的部署面与**跨副本**语义；
  收口复检的 48 条判词**只证明本 GOAL 声明的面**成立，不证明「可靠性已完备」；
  九项义务中四项（`R26-1`…`R26-4`）的实现仍是**未做**（需拍板）；`R-M1` 未收口。
- **下一项任务**：GOAL-026 **收口**（`status: ACHIEVED`）—— 本 PLAN 与 `RECHECK-254` 已定稿；
  EC-01…EC-05 全 `PASS`；九项义务判定表、残余与未覆盖范围逐条在位。
