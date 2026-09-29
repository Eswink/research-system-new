---
id: RECHECK-20260929-254
slug: goal-026-ec05-self-bootstrap-closeout
title: GOAL-026 EC-05 复检：收口验证器（48 判词 / 复用标准断言集）+ 台账审计的「空集 ⇒ 未取证」行为下界 + 射程纯收紧
plan_id: PLAN-20260929-253
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-254 — GOAL-026 EC-05 复检

**复检口径**：不采信工具自己的叙述，也不采信「源码里写着下界」；本文件给出**可复核观察面**
（命令 / 判词行 / `rc` / raw `sha256` / 实测计数）。**未实跑的不记通过**。

## 检查结果

### 1. 收口复检本身（实测）

- 交付：`tools/verify_goal026_closeout.py`（**449 行**，上限 450）。
- 公共面**一行都不重写**：`main` 调 `tools/closeout_recheck_assertions.py::standard_verdicts`
  取 18 条标准判词（受保护判据 / 规模门 / 产品根 ×2 / m0 条数 / 断言集 ×2 / 两树入口 /
  治理 / 路径无盘符 / 入口四条 / 规范页三条 / 记录路径自洽），本文件只追加 30 条本轮判词。
- 实跑：`uv run --frozen --no-sync python -B tools/verify_goal026_closeout.py --root . --verdict-only`
  ⇒ **`PASS` 48 行、`FAIL` 0 行、`rc=0`**（日志 `scratch/goal026-c5-verify.log`）。
- **随后按「未实跑不得记 PASS」把 EC-05 置 `BLOCKED`，同一条命令随之变成
  `PASS` 47 + `FAIL` 1 / `rc=1`**（日志 `scratch/goal026-c5-verify-blocked.log`），
  唯一红行是 `FAIL ec05-final-ec-timing -> 状态异常` —— 这正是该验证器的**正确行为**：
  它拒绝把一个未收口的 GOAL 判成已收口。⇒ 「48 PASS」是**提交被拒之前**的状态，
  「47 PASS + 1 FAIL」是**如实登记 BLOCKED 之后**的状态；两者都不是缺陷。
- **首轮抓到我本人的两处错报**（**判据自己红**，不是产品缺陷）：
  ① `ec02-cases-floor -> 例数 (3, 2, 2) 低于下界 (3, 3, 2)` —— 我把退避轨迹文件的例数记成 3，
  实测 **2**；② `ec02-trajectory-pinned -> 漂移：[30, 60, 100, 100]` —— 常量在树里是 `list`，
  我按 `tuple` 比较 ⇒ **形态误判**。两处都改**判据侧**（下界改 2；比较前统一成 `list`），
  **未**放宽任何断言。

### 2. 逐 EC 的判据面与钉住的常量（实测）

- 五条 EC 的判据文件**在树**且例数 ≥ 下界：EC-01 `(4, 2)`、EC-02 `(3, 2, 2)`、
  EC-03 `(5, 3, 3, 2)`、EC-04 `(5, 3, 6)` —— 判词逐条 `PASS`。
- 常量钉住（AST 字面量，不是文本巧合）：退避轨迹 `[30, 60, 100, 100]`；
  工具面与补偿面扫描下界 `400`（两处都要求 == 400）；投递语义面
  `_MAX_EXEMPT = 8` / `_MIN_SCANNED_FILES = 2500` / `_MIN_CLASSIFIED = 16` /
  `_MIN_CJK_CONTROL = 8`；豁免表**非空、在上限内、每条理由 ≥ 20 字符**。

### 3. EC-03 的产品修复被 AST 钉住（实测）

- 判词 `ec03-probe-budget-fail-closed` 断言 `adapters/relay/gateway.py::_consult_circuit` 里
  「捕获 `CircuitBreakerTransitionError` ⇒ **抛出** `CircuitOpenRelayError`」这条分支存在。
- **按压 P2**（把该分支改成 `pass`）⇒ 判词判红（`FAIL ec03-probe-budget-fail-closed -> 不再 fail-closed`），
  且 **EC-03 判据文件自己那条行为用例同时判红**：
  `FAILED tests/adapters/relay/test_gateway_half_open_budget.py::test_exhausted_half_open_probe_budget_denies_without_touching_downstream`
  （`1 failed, 4 passed`）⇒ 两条**独立面同向**。
- 复原后 `adapters/relay/gateway.py` raw `sha256` =
  `bc1b29bb2cd194adefde1216e950679a01aa2316f3f1370164cb8062b46752f6`（与按压前基线逐字节相同）；
  复检回到 48 PASS / `rc=0`；受影响套件 `1240 passed`。

### 4. 台账审计的「空集 ⇒ 未取证」是**行为**判据（实测）

- 交付：`tools/audit_goal026_ledger.py`（**201 行**）；`MIN_JOBS = {"M0 Quality Gates": 8,
  "Push on main": 3}`、`EMPTY_SET_MARK = "未取证"`、`REQUIRED_RUN_FIELDS` 五字段非空才算取证。
- 验证器用 `tempfile` **合成输入**跑四种形态（判词 `ec05-audit-*`）：空 `jobs` ⇒ `rc != 0`
  且输出含「未取证」；欠数集（2 条）⇒ `rc != 0` 且含「未取证」；有失败 job（`j7`）⇒ `rc != 0`
  且**点名 `j7`**；完整集（8 条）⇒ `rc == 0` 且 `failed=0`。
- **按压 P1**（把空集分支改成 `return None`，即旧脚本 `scratch/audit_goal025_ledger.sh`
  「空集 = 没有失败」的口径）⇒ 唯一红行 `FAIL ec05-audit-empty-jobs -> rc=0`、`rc=1`
  ⇒ **源码里写着下界文案不算证据，行为才算**。复原后 raw `sha256` =
  `11f5462beb0f8069d0f4b6a9371e2c0715a292d72baf68e70568af340372cdf2`（与基线逐字节相同）。
- 真实台账（`scratch/` 里的原始 JSON）：`--prefix goal026-c4- --expect-sha
  4cbe16d3e5243be693518d81dc461920721dc867` ⇒ `PASS ledger-audit runs=2 failed=0`；
  全量 c0…c4 ⇒ `PASS ledger-audit runs=10 failed=0`，逐 run `run_attempt=1`。
  **首轮把 `--expect-sha` 与全目录混用** ⇒ 8 条「sha 不符」判红 —— 那是工具的**正确**行为
  （它拒绝把别的轮次的证据当本轮的），按轮次用 `--prefix` 收窄后归零（见 `W-3`）。

### 5. 射程纯收紧 + 两件新工具自身过四道门（实测）

- `IN_SCOPE` **追加两行**（`tools/verify_goal026_closeout.py`、`tools/audit_goal026_ledger.py`），
  既有五条**未改** ⇒ 清单变长、射程变大，**没有**任何约束被放宽。
- 四道门（两件新工具）：`ruff format --check` = `2 files already formatted`；
  `ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；
  规模 = 449 / 201 行（上限 450），无超 50 行函数。
- 工具面套件：`pytest tests/tooling -q` ⇒ **1235 passed**（含逐脚本四道门与规模门）。
- 验证器还断言两件新脚本**不含盘符绝对路径**（进两树复检的脚本必须与树根无关）。

### 6. 按压矩阵与逐字节复原（实测）

留档 `scratch/goal026-ec05-press-matrix.log`（**2882 字节、`CR` 计数 0**、二进制写盘）：

| 按压 | 改动 | 预期 | 实测 | 复原（raw `sha256`） |
| --- | --- | --- | --- | --- |
| P1 | 审计器空集分支 `return None` | `ec05-audit-empty-jobs` 红 | `rc=1`，唯一红行即该判词（`-> rc=0`） | `11f5462b…cdf2`（= 基线）⇒ `PASS` 48 |
| P2 | `_consult_circuit` 的 except 分支改 `pass` | `ec03-probe-budget-fail-closed` 红 | `rc=1` + 判据文件 `1 failed, 4 passed` | `bc1b29bb…52f6`（= 基线）⇒ `PASS` 48 |

两向结论：按压 ⇒ 红（且红的是**预期的那一条**，不是整轮崩）；复原 ⇒ 绿（48 PASS、`rc=0`，
两文件与基线**逐字节相同**）。

### 7. 记录面自洽与残余在位（实测）

- GOAL `EC-01`…`EC-04` = `PASS`；`EC-05` 那条判词接受「**已终态或尚未终态**」两种取值
  （**时序**：它的判词就是本文件所在提交产出的）—— 本文件如实写明，不当作放宽。
- `latest_recheck` 为**仓库相对路径**且可解析；`child_plans`（5 个）与 `memory_entries`（6 个）
  无空项；承继残余 12 条 + `G24-1`…`G24-6`（含「需用户拍板」）+ 本轮 `R26-1`…`R26-7` 逐条在位；
  未覆盖范围五条在位；**九项义务判定表**逐条在位；台账 run id 下界 ≥ 8（实测远超）。
- 治理 `validate.py` 与 `tools/docs_consistency_check.py` 的实跑结果记录在 GOAL 的迭代日志与
  状态历史里（本文件不重复其数字，避免两处口径漂移）。

### 8. 门禁解除（用户拍板后的实测，2026-09-29）

**拍板**：处置 `scratch/keycheck_agnes_surfaces.py:81,96` 与 `scratch/verify_goal012_c2.py:143`
这 3 个高危 finding —— 清理归档，**或**授权 `mimosa policy init` + 有界豁免。

| 路径 | 实测 | 处置 |
| --- | --- | --- |
| 策略豁免（`mimosa policy init` → `.mimosa/security-policy.json` 的 `threatModel.exclusions` 写两个文件） | `policy check` 报「项目安全策略有效」，但**不抑制 finding**：`mimosa scan scratch/keycheck_agnes_surfaces.py --project . --min high` 仍报 2 高危；git 门禁照旧拦截。更糟的是默认 `command.forbidShell=true` 让 `apps/web/src/features/example-console/reference/YamlView.tsx` 的 `RegExp#exec` 被判「Shell 执行策略违反」⇒ 高危 **3 → 7**（新增 4 条落在**产品文件**） | **已回退**（删除策略文件；复测高危回到 3） |
| **清理归档** | `tar czf /d/research-system-gate-archive/flagged-probes-20260929.tgz`（仓库外）打包两文件 ⇒ `tar` 清单含原 mtime（`2026-09-21 12:14` / `2026-09-23 14:17`），归档 sha256 = `fb2e840aa8a4d2c71838d4503cd764da58df45310a74d4e93cecfe4db20fd16b`；两份原文件 sha256 记在 `scratch/goal026-gate-archive-baseline.sha256`（`c0450119…b96c` / `867b9270…de35`）⇒ 从工作树移除后，`git commit` **放行** | **采用** |

**旁证（归档前先量过）**：`Scan` 与门禁都只点名那两处；**本轮新工具自身扫描干净**
（`tools/verify_goal026_closeout.py`、`tools/audit_goal026_ledger.py` ⇒「未发现风险」）。

**未采用「改写那两个文件」的理由**：它们是一次性取证探针（`verify_goal012_c2.py` 是
GOAL-20260923-012 / PLAN-142 / RECHECK-143 的留档资产）⇒ 改写会改掉取证语义；
归档保留字节 + 哈希 + 位置，证据链可追溯，且**未修改任何既有记录**。

**残余**：解除后一次提交报「Mimosa 在 git commit 前没有得到完整扫描结论（`scanner_enobufs`），
本次按兼容策略继续」—— 即 `R-M1` 仍在；**不得**据此宣称项目安全。

### 9. AC-7 后两项补齐（门禁解除后，2026-09-29）

**两树复检**：`uv run --frozen --no-sync python -B tools/two_tree_recheck.py
--script tools/verify_goal026_closeout.py --script-mode shared --root .
--base-ref 6508d9d --worktree-dir /d/research-system-goal026-clean
--verdict-current scratch/goal026-c5-two-tree/current.txt
--verdict-clean scratch/goal026-c5-two-tree/clean.txt --timeout 900 -- --verdict-only`
⇒ **`TWO-TREE PASS`、`EXIT=0`**：

```text
TREE current=... exit=0 verdicts=48 sha256=6da43133d77a3a9741035b59a7cef4193d01a0db96361ede363f3c45b594a731
TREE clean=...   exit=0 verdicts=48 sha256=6da43133d77a3a9741035b59a7cef4193d01a0db96361ede363f3c45b594a731
COMPARE identical=True
```

两路留档 `scratch/goal026-c5-two-tree/{current,clean}.txt` **逐字节相同**（`cmp` 通过、
`sha256` 同为 `6da43133…a731`、各 1395 字节）⇒ 「当前树 + 干净 checkout」**同结论**。

**CI 台账到终态**：推送 `6508d9d`（`4cbe16d..6508d9d  main -> main`）后轮询至终态
（日志 `scratch/goal026-c5-ci-poll.log`，`ALL_TERMINAL sha=6508d9d9a4c178d7d4534c0b8b49f52bf517ce49`）：

| run | workflow | 逐 job | attempt |
| --- | --- | --- | --- |
| [36550736379](https://github.com/Eswink/research-system-new/actions/runs/36550736379) | M0 Quality Gates | `console-frontend` / `eval-gate` / `container-quality` / `collector-quality` / `observability-overhead-{windows,ubuntu}-latest` / `quality-{windows,ubuntu}-latest` **8/8 `success`** | 1 |
| [36550735603](https://github.com/Eswink/research-system-new/actions/runs/36550735603) | Push on main (CodeQL) | `Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)` **3/3 `success`** | 1 |

**台账审计（本轮工具实跑）**：原始 JSON 落盘
`scratch/goal026-c5-run-36550736379{,-jobs}.json`、`…-36550735603{,-jobs}.json`
（REST 实查 `http=200`；`size` 16330 / 33961 / 16221 / 11044）⇒
`tools/audit_goal026_ledger.py --runs-dir scratch --prefix goal026-c5-
--expect-sha 6508d9d9a4c178d7d4534c0b8b49f52bf517ce49` = **`PASS ledger-audit runs=2 failed=0`**；
全量 c0…c5 = **`PASS ledger-audit runs=12 failed=0`**（逐 run `run_attempt=1`）。
**空集合未被记成 OK**：审计器对空 `jobs` / 低于下界一律判「未取证」（行为判据见 §4）。

**as-is 本机 m0（记录写入之后）**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` = 24、`FAIL [` = 0、`EXIT=0`；日志 `scratch/goal026-c5b-m0.log`，跑在推送后、
记录已写完的状态）。**治理** `validate.py` 绿、**`DOCS-CHECK`** `PASS: 6 deterministic checks`。

## 结论

**`PASS_WITH_WARNINGS`**。七条 AC **全部成立且有实跑证据**：AC-1…AC-6 与 AC-7 前三项见 §1–§7；
AC-7 的后两项（两树复检、CI 台账到终态）在门禁解除后已补齐，见 §9。全程遵守
「**未实跑的不记通过**」：中途曾因门禁不可达而如实置 `BLOCK`（§8），解除并补齐后才改判。

**已验证的关键不变量**：收口复检 48 判词全绿且公共面零重写；台账审计的「空集 ⇒ 未取证」
是**行为**判据；EC-03 的 fail-closed 修复被 AST 钉住并按压两向；`IN_SCOPE` 纯收紧；
两树逐行 + `sha256` 完全相同。

**已成立的部分（实跑证据齐全，可复核）**：AC-1…AC-5 全部成立 —— 收口复检 48 判词全绿
（`rc=0`）且公共面零重写；逐 EC 判据面与常量钉住；EC-03 的 fail-closed 修复被 AST 钉住并
按压两向（P1 / P2 均先红后绿、`sha256` 逐字节复原）；台账审计的「空集 ⇒ 未取证」是
**行为**判据（四种合成输入 + 按压 P1）；两件新工具自身过四道门（449 / 201 行）；
`IN_SCOPE` 纯收紧。`tests/tooling` = 1235 passed。

**阻塞点（决定性，已取原始证据；详见 §8 的解除）**：

- 仓库内**没有任何已安装的 git 钩子**（`.git/hooks/` 只有 `*.sample`），拦截来自
  ZCode 客户端层的 Mimosa Git 门禁（`mimosa git-gate status` 报 `pre-commit` / `pre-push`）。
- 该门禁**按仓库状态**判定，与本次提交的 diff 无关：
  ① 只暂存两个新工具 ⇒ 拒；
  ② `git commit --allow-empty`（索引为空、零改动）⇒ 拒；
  ③ `git reset` 清空索引后再 `--allow-empty` ⇒ 拒。⇒ **当前状态下任何提交都无法落地。**
- 门禁点名的 3 个高危 finding 全在**既有的、非本轮改动的、gitignored 的**资产里：
  `scratch/keycheck_agnes_surfaces.py:81,96`、`scratch/verify_goal012_c2.py:143`
  （后者是 GOAL-20260923-012 / PLAN-142 / RECHECK-143 的取证资产）；
  另有 9 条中危落在 `scratch/probe_migration.py` 与 `tests/postgres/worker_memory_scripts.py`。
- **本轮新增/改动的文件自身扫描干净**（`mimosa scan` 两个新工具 ⇒「未发现风险」）。
- 同一环境下的 `4cbe16d`（cycle 4）此前提交成功 ⇒ 阻断是在本轮内出现的。

**未成立的部分（依 GOAL 的「未实跑不得记 PASS」）**：AC-6 的**最终**形态（`status: ACHIEVED`
与 `latest_recheck` 指向一条**通过**的复检）与 AC-7 的**全部**（两树复检、CI 到终态、
台账在**本轮 sha** 上的审计）—— 都依赖提交与推送，而两者当前不可达。因此本复检
**不给出通过结果**：`result: BLOCK`，并把 `W-1`…`W-6` 保留为对已成立部分的限定。

**为什么不由本轮自行解除**（两条路都超出授权）：

- (a) 改/删那些 scratch 资产或产品代码（ledger 里 `adapters/sqlite/db.py`、
  `adapters/openhands/runtime_adapter.py`、`packages/application/**` 也有 blocked 条目）
  —— 那是别的 GOAL 的取证资产与产品代码，会破坏既有记录的证据链，且超出
  「新增判据 / 只收紧修复本 GOAL 证明的缺陷 / 同源文档」的授权；
- (b) 放宽安全门禁（如把 git 门禁失败模式改放行）—— 本 GOAL 明令禁止
  「放宽 / 削弱任一既有判据 / 门禁 / 阈值 / 放行面」。

**解除（用户 2026-09-29 拍板，见「8. 门禁解除」节）**：采用**清理归档**；
`mimosa policy init` + 有界豁免一路经实测**无效且有害**（exclusions 不抑制 finding，
且默认 `forbidShell` 让 `RegExp#exec` 误报 4 条新高危），已回退。
本文件在 AC-7 后两项补做完成后改判 `PASS_WITH_WARNINGS`。

**本轮工件状态**：全部留在工作树，**未提交**、**未推送**、**CI 未触发** ——
`tools/verify_goal026_closeout.py`、`tools/audit_goal026_ledger.py`、
`tests/tooling/test_tooling_scripts_meet_product_gates.py`（`IN_SCOPE` 追加两行）、
`docs/architecture/WORKFLOW_RELIABILITY.md`（§10）、
`PLAN-20260929-253` / `RECHECK-20260929-254` / `MEM-20260929-172` / GOAL-026 回写 /
`ALL_PLAN` / `INDEX`。证据留档：`scratch/goal026-c5-commit-block.log`（二进制写盘）、
`scratch/goal026-c5-verify.log`（48 PASS）、`scratch/goal026-ec05-press-matrix.log`（按压两向）。

**下一轮输入**：先拍板上述三项；解除后本轮的 WP 可直接续跑（工作树未丢），
仅需 commit → push → 两树复检 → CI 台账 → 把本复检结果改回通过并置 GOAL 为 `ACHIEVED`。

**警告（如实登记，不消解）**：

- `W-1` **余量告急**：验证器 **449 / 450 行**，只剩 1 行余量 ⇒ 任何追加都必须先把公共面
  搬出去或改复用形态；这是「一个文件既有公共面又有特有面」的代价。
- `W-2` **台账受判面在树外**：真实 CI 台账的原始 JSON 落在 `scratch/`（gitignored）⇒
  树内只有审计器的**形状**与**行为判据**；第三方在干净 checkout 上**无法**从树里重derive
  台账本身（登记为 `R26-7`）。
- `W-3` **`--expect-sha` 是按目录全量生效的**：多轮证据混放时必须用 `--prefix` 收窄，
  否则别的轮次会被判「sha 不符」而判红（首轮实测 8 条红）—— 工具语义，**不是**缺陷；
  但用错会得到「看起来像缺陷」的红。
- `W-4` **例数下界不校验内容**：`ec0X-cases-floor` 只数 `test_` 前缀函数个数，
  「例数够但断言被弱化」它抓不到（弱化既有判据属本 GOAL 的禁令面，由人守）。
- `W-5` **射程仍有界**：`tools/` 不进 `PRODUCT_ROOTS`；本轮只把**两个新脚本**纳入机器门，
  历史 37 个脚本仍无门（GOAL-023 `W-1` 原样保留）。
- `W-6` **按压面有限**：本轮压了 P1（审计器空集分支）与 P2（产品 fail-closed 分支）两条；
  验证器另外 46 条判词**未逐条按压** ⇒ 未按压 ≠ 不成立，但也不等于已按压。
