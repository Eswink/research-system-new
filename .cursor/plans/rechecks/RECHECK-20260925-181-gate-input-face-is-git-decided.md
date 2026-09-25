---
id: RECHECK-20260925-181
plan_id: PLAN-20260925-180
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-017-cycle1（独立复检：`scratch/goal017-c1-git-face-pair-proof.sh` 的成对对照 + 按压脚本）
baseline_ref: 建档提交 `25d802b`（推送区间 `f1ca9ed..25d802b`）
checked_head: cycle 1 工作树（未推送；`validate_bundle.py` 的改动 + 新增判据 + 记录面）
---

# RECHECK-20260925-181 — GOAL-017 EC-01（D-10 门禁 scoping）

> **状态**：**已完成**。7 条 AC 逐条复核，结论见文末。

## 检查范围

D-10 的授权边界 a–e 逐条落到**可复核**的证据上：输入面由 git 决定（AC-1）、判据成对（AC-2）、
反证先红后绿（AC-3）、被扫检查项零放宽（AC-4）、as-is 本机 m0 = 23/23（AC-5）、
定向套件 + 静态门（AC-6）、零越界（AC-7）。

## 检查结果

### 一、AC-1｜输入面由 **git** 决定（成立）

- 实现（`.cursor/skills/system-spec-check/scripts/validate_bundle.py`）新增
  `git_decided_inputs()`：`git ls-files -z --cached --others --exclude-standard` 的**并集**，
  即「**已跟踪** ∪ **未跟踪且未被忽略**」。
- **没有**目录名特判：`NON_SOURCE_DIRS` 的 diff **零新增条目**（见 AC-4 的逐字节复核）；
  判定只用 git 自己。夹具里的被忽略目录**刻意叫 `ignored-area/`**（不是 `scratch/`）
  ⇒ 若实现是「按目录名排除」，判据 ① 会红（这条是机器取证，不是自述）。
- **`-z` 的必要性**：默认 `core.quotepath` 会把非 ASCII 路径转义成八进制形式，与
  `Path` 算出的相对路径对不上；本仓有 **30 条**非 ASCII 已跟踪路径
  （`docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`），所以必须用 NUL 分隔输出。

### 二、AC-2｜判据**成对**（成立，`3 passed`）

判据 `tests/tooling/test_validate_bundle_git_decided_input_face.py`（hermetic 夹具树，
**不碰主树索引**；`git init` 夹具沿用 `tests/tooling/test_credential_audit.py` 的既有形态）：

| # | 判据 | 结果 |
| --- | --- | --- |
| ① | gitignored 的坏链接文件 ⇒ **不**判红 | 成立（判词里**缺席**） |
| ② | **同内容但已跟踪** ⇒ **仍**判红 | 成立（判词里出现，逐字 `Markdown 本地链接不存在`） |
| ③ | 被忽略目录里 **force-add** 的已跟踪文件 ⇒ **仍**判红（安全边界 b） | 成立 |
| ④ | 未跟踪但**未**被忽略的新文件 ⇒ **仍**判红（输入面不是「只扫已跟踪」） | 成立 |
| ⑤ | 夹具是工作树 ⇒ **不得**出现「输入面不可用」（反向对照，排除「靠罢工变绿」） | 成立 |
| ⑥ | 非 git 根 ⇒ **点名** `not_a_git_tree` + 退出码非 0 | 成立 |

**夹具前提逐条先断言**（否则判据空转）：`git check-ignore` 说该文件**确实**被忽略；
force-add 的那条**确实**在 `ls-files --cached` 里；第四条**确实**在
`ls-files --others --exclude-standard` 里。

### 三、AC-3｜反证：先红后绿（**同一个坏文件**，成立）

`scratch/goal017-c1-git-face-pair-proof.sh`（gitignored，**不入库**）在**独立 `git worktree`**
上做（该 worktree 有自己的索引 ⇒ **主树索引零改动**，实测收尾 `git status` 只剩本 cycle
自己的改动）。留档 `scratch/goal017-c1-pair-proof.txt`：

| 步骤 | 场景 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | **HEAD（改动前）**脚本跑主树（`R-3` 的证人仍在场） | 红 | `验证失败: Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md -> [A-Za-z]:\\|/(home\|mnt\|data\|Users`；`OLD_EXIT=1` |
| 2 | 工作树（改动后）脚本跑**同一棵树** | 绿 | `验证通过`；`NEW_EXIT=0` |
| 3a | worktree 自己的（改动前）脚本 + 同一个坏链接文件 | 红 | 点名 `scratch\ignored-bad-link.md`；`WT_OLD_EXIT=1` |
| 3b | 工作树（改动后）脚本、根指向 worktree、**坏文件仍在场** | 绿 | `WT_NEW_EXIT=0` |
| 3c | 把**同一个**坏文件 force-add 成已跟踪（仍落在被忽略目录里） | 红 | 点名 `scratch/ignored-bad-link.md`；`WT_TRACKED_EXIT=1` |

**另有一次按压（判据非空转）**：`scratch/goal017-c1-criteria-press.py` 在同一夹具上跑
**改动前 vs 改动后**两个脚本 ⇒ 改动前 `TOTAL 4`（gitignored 那条**出现**：判据 ① 会红），
改动后 `TOTAL 3`（那条**缺席**，其余三条仍在）。留档 `scratch/goal017-c1-criteria-press.txt`。

### 四、AC-4｜被扫检查项**零放宽**（成立，逐字节复核）

- 改动的语义面**只有**两处：① 新增 `git_decided_inputs()`；②
  `validate_local_markdown_links()` 在遍历里加一条 `if doc.relative_to(ROOT).as_posix()
  not in inputs: continue`，并把「输入面不可用」改成**当场点名 + `SystemExit(1)`**。
- **被判内容一字未动**：链接正则、`://` / `mailto:` / `#` 的跳过条件、越界检查、
  存在性判据（`if not resolved.exists()`）**逐字未改**。
- **另两处 `repository_files()` 消费保持全工作区**：`check_versions()` 的「旧项目版本引用」
  （`old_version` 正则）与「旧版本命名文件」两段**未改一行** ⇒ 边界 e 点名的「版本号」面
  没有被动过。**这是刻意的范围围栏**（授权只覆盖 Markdown 链接扫描）。
- `NON_SOURCE_DIRS`：**零新增条目**（无任何目录名被加进去）。
- 静态门：`ruff check`（engineering + product）= `All checks passed!`；
  `ruff format --check` = 已格式化（534 files）；`mypy` = `Success: no issues found in
  1017 source files`。

### 五、AC-5｜as-is 本机 m0 = **23/23**（成立）

- `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/
  run_all_checks.py --profile m0 --keep-going`（**独占**、仓库 `.venv`）
  ⇒ **`PASS: profile=m0; 23 deterministic checks`**，`M0_EXIT=0`，
  `PASS [` = 24（23 项 + 计数外的 `release-assets-immutable`）。
  日志：`scratch/goal017-c1b-m0-as-is.log`（第 1583 行起逐条 `PASS [framework/…]`、
  第 1631 行终态行）。
- **不是靠删证人变绿**：`R-3` 的证人文件仍在场（`scratch/self-governance-bootstrap-prompt.md`，
  `69944` 字节；`git check-ignore -v` ⇒ `.gitignore:43:scratch/`）。
- **不再需要代管**（GOAL-016 时期的 `tools/quarantine_and_run_m0.py` 本 cycle 未使用）。
- **如实登记一次环境红（第 1 跑）**：首跑 `FAILED: 1 check(s): python/tests=1`，
  唯一失败 = `tests/adapters/execution/test_docker_backend_e2e.py::TestFaultInjection::
  test_oom_is_failed`（Docker OOM 故障注入）。**成对对照**：① 隔离跑 **`1 passed` in 1.82s**；
  ② 整个模块 `tests/adapters/execution` = **`89 passed`**（76.77s）；③ 本 cycle 的改动集
  **不含** `adapters/execution` 任何文件。⇒ 归类 **`docs/architecture/LOCAL_GATE_PROTOCOL.md`
  的 (ii) 环境专属**（触发输入 = 容器/daemon 在高负载下的行为，判据描述的行为**是对的**：
  OOM 容器就该判 `FAILED`）；处置 = **不改判据**、复跑取终态（第 2 跑即绿）。

### 六、AC-6｜定向套件 + 静态门（成立）

- `tests/tooling` = **`1158 passed`**（含新判据 3 条），
  `egress guard: judged 3 connection attempt(s); blocked 0`（本 cycle **零出网**）。
- `DOCS-CHECK PASS: 6 deterministic checks`；治理 `validate.py` = `Cursor 治理验证通过`。
- 规模门禁：新增判据文件 **<450 行**、无 >50 行函数（`tests/tooling/test_python_source_limits.py`
  在全量门里通过）。

### 七、AC-7｜零越界（成立）

改动集（`git status --porcelain`）：`validate_bundle.py`（门禁脚本，**授权面**）、
新增判据 `tests/tooling/…`、记录面（`.cursor/plans/…`）。**不含**产品代码、
策略面、阈值、依赖、`undici` / `yaml` pin、`ADR-0031`。
`apps/web/src/features/models/ModelDetails.tsx` / `packages/domain/model_drift.py` /
`services/api/dto/models.py` 是**并发写者**的行尾差异（内容 diff 为空）⇒ **未提交**。

## 结论

**PASS_WITH_WARNINGS**（7 条 AC 全部成立）。

**警告（如实登记，不得读成已完成）**：

- **`W-1`｜范围围栏是刻意的**：另两处 `repository_files()` 消费（版本号 / 旧版本命名）
  **仍扫全工作区** ⇒ 别人未跟踪的 `.py` / `.md` 里若出现旧版本号，**仍**能让本机门判红
  （当前实测无此事：as-is 全绿）。这不是遗漏，而是边界 e 点名的「一律不动」。
  若要收窄它们，属**另一次授权**。
- **`W-2`｜Win32 会剥尾点的假绿面**：`.md` 链接判据在 Win32 上有已知的路径语义差异
  ⇒ 本判据的**跨平台**结论以 CI 的 `quality-ubuntu-latest` 为权威证书（本 cycle 的 CI 台账）。
- **`W-3`｜命名无关性是「契约」而非「不可能」**：判据用**唯一一个**任意目录名取证；
  它证明实现不依赖某个特定名字，但不构成「不可能写出名字列表」的数学证明。
- **`W-4`｜门禁脚本不在 450 行门禁覆盖面内**：`validate_bundle.py` = 1213 行，
  而 `tests/tooling/test_python_source_limits.py` 的 `PRODUCT_ROOTS` 不含 `.cursor/`
  ⇒ 该脚本的规模纪律**不在机器判据里**（本 cycle 只加了 ~40 行）。
- **`W-5`｜`(ii)` 类红的处置是「复跑取终态」**：第 1 跑的 Docker OOM 红**未被**证明消失，
  只是**同一代码**复跑两跑两结果（一红一绿）⇒ 与 `MEM-20260924-132` 的跳过守卫教训同类；
  真正的权威证书是 CI 在同一 tip 上的终态。
- 承继残余（`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-1…W-7`）
  **原样保留**；本 cycle **不**宣称它们已解决。
