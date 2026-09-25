---
id: PLAN-20260925-180
slug: gate-input-face-is-git-decided
title: D-10 门禁 scoping：validate_bundle 的 Markdown 链接扫描输入面改由 git 决定
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-017
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-017 的 **EC-01**（D-10 取 (a)，用户 2026-09-25 拍板授权实施）。
    授权边界（严格）：a) 排除规则必须**由 git 决定**（`git check-ignore` 或
    `git ls-files --others --exclude-standard` 的等价判据），**不得**把目录名加进
    `NON_SOURCE_DIRS`、**不得**按 `scratch/` 字面名特判；b) **跟踪文件一律照扫**
    （gitignored 排除不得让任何已跟踪文件逃过扫描 —— **安全边界**）；c) 判据**成对**：
    gitignored 的坏文件 ⇒ **不**判红，**同内容但已跟踪**的坏文件 ⇒ **仍**判红；
    d) 门禁自身不可用（扫描根不在 git 工作树内）⇒ **硬失败**，**不得静默通过**
    （承 GOAL-015 的 `not_a_git_tree` 口径：结论必须**点名**未扫成的面）；
    e) **不得**放宽被扫内容的任何检查项（链接存在性 / 版本号 / schema 一律不动）。
    **交付终态**：as-is 本机 m0 = **23/23**（`R-3` 消失）。
    **范围围栏（本 PLAN 刻意不做）**：`check_versions()` 的两处 `repository_files()` 扫描
    （旧版本引用 / 旧版本命名）**保持全工作区**（边界 e 点名「版本号不动」）。
    push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-181-gate-input-face-is-git-decided.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-140-gate-input-face-needs-an-authority-and-a-pair.md
---

# PLAN-20260925-180 — D-10 门禁 scoping（GOAL-017 EC-01）

## 目标

让 `framework/validate_bundle` 的 **Markdown 本地链接扫描**只吃**本仓的产物**：
输入面 = 工作区里 `.md` 文件 ∩（**已跟踪** ∪ **未跟踪且未被忽略**），由 **git** 决定；
别人的 gitignored 在制品（`scratch/`）不再能让本机门判红；**跟踪文件照旧全扫**；
git 面不可用 ⇒ **点名 + 硬失败**。被判内容（链接存在性）与其余检查项**一字不动**。

## 验收条件

- **AC-1｜输入面由 git 决定**：实现里**没有**目录名白名单 / 黑名单特判（`NON_SOURCE_DIRS`
  **零新增**），判定经 `git ls-files`（等价判据），且 `-z` 保证非 ASCII 路径不被 `quotepath`
  转义（本仓有 30 条非 ASCII 已跟踪路径，见 `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`）。
- **AC-2｜成对判据**（机器判据，hermetic 夹具；不碰主树索引）：
  ① gitignored 的坏链接文件 ⇒ **不**判红；② **同内容**但**已跟踪** ⇒ **仍**判红；
  ③ **被忽略目录里 force-add 的已跟踪文件** ⇒ **仍**判红（安全边界 b 的直接取证）；
  ④ 非 git 根 ⇒ 判词**点名**未扫成的面且**退出码非 0**。
- **AC-3｜反证（先红后绿，同一个坏文件）**：在**独立 `git worktree`** 里造一个 gitignored 的
  坏链接文件 —— **改动前**的脚本（`git show HEAD:…validate_bundle.py`）必须**判红**，
  **改动后**的脚本必须**判绿**；两跑同一棵树、同一个文件。
- **AC-4｜零放宽取证**：`git diff` 证明 `validate_local_markdown_links` 的链接判据、
  `check_versions`（版本号 / 旧版本命名）、schema / 引用一致性**未被改**；
  `NON_SOURCE_DIRS` 无新增条目。
- **AC-5｜as-is 本机 m0 = 23/23**：`make validate-all` 到
  `PASS: profile=m0; 23 deterministic checks`（**不再需要**代管 `scratch/` 文件）。
- **AC-6｜定向套件 + 静态门**：新判据 + `tests/tooling` 绿；`ruff check` / `ruff format --check`
  / `mypy` 绿；`DOCS-CHECK` 绿。
- **AC-7｜零越界**：改动集**只含** `validate_bundle.py`、新增判据测试、记录面（`.cursor/`）；
  **不含**产品代码、策略面、阈值、依赖、`undici` / `yaml` pin。

## 实施清单

- [x] WP1：`validate_bundle.py` —— git 决定的输入面（`git_decided_inputs()`）+ 链接扫描消费它
      + git 面不可用 ⇒ 点名硬失败（**当场** print + `SystemExit(1)`，不攒进 `ERRORS`）。
- [x] WP2：判据测试 `tests/tooling/test_validate_bundle_git_decided_input_face.py`
      （hermetic 夹具树；AC-2 四条 + 反向对照 + 硬失败；**`3 passed`**）。
- [x] WP3：反证与终态证据（worktree 对证脚本 + as-is m0 23/23 + 零放宽）落在
      `scratch/`（**不入库**），结论回写 GOAL。

## 证据面（实跑）

| 证据 | 命令 / 位置 | 结果 |
| --- | --- | --- |
| 成对判据 | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_validate_bundle_git_decided_input_face.py -q` | **`3 passed`**（`egress guard: judged 0 / blocked 0`） |
| 反证（先红后绿） | `bash scratch/goal017-c1-git-face-pair-proof.sh` → `scratch/goal017-c1-pair-proof.txt` | 旧脚本红（点名 `scratch/self-governance-bootstrap-prompt.md`，`OLD_EXIT=1`）/ 新脚本绿（`NEW_EXIT=0`）/ worktree 3a 红 3b 绿 / 3c force-add 后**又红**（`WT_TRACKED_EXIT=1`） |
| 判据按压 | `uv run … scratch/goal017-c1-criteria-press.py` → `scratch/goal017-c1-criteria-press.txt` | 改动前 `TOTAL 4`（gitignored 那条出现）/ 改动后 `TOTAL 3`（缺席，其余三条仍在） |
| 零放宽 | `git diff -- .cursor/skills/system-spec-check/scripts/validate_bundle.py` | 判据面（链接正则 / 跳过条件 / 存在性）**逐字未改**；`NON_SOURCE_DIRS` **零新增**；`check_versions()` 的两段**未改** |
| as-is m0 | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` | **`PASS: profile=m0; 23 deterministic checks`**（`M0_EXIT=0`，`PASS [` = 24）——日志 `scratch/goal017-c1b-m0-as-is.log` |
| 第 1 跑的红（如实登记） | 同上 → `scratch/goal017-c1-m0-as-is.log` | `FAILED: 1 check(s): python/tests=1`，唯一失败 = `test_docker_backend_e2e.py::TestFaultInjection::test_oom_is_failed`；隔离跑 `1 passed` / 模块 `89 passed` ⇒ **(ii) 环境专属**，判据未动 |
| Linux 侧复验 | CI `quality-ubuntu-latest`（本 cycle 的推送） | 见 GOAL 的 CI 台账 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive（GOAL-017 cycle 1）。WP1 已落：`git_decided_inputs()`（`git ls-files -z --cached --others --exclude-standard` 的并集）+ 链接扫描消费它 + git 面不可用**当场点名**（`not_a_git_tree`）硬失败。WP2 已落：判据 `tests/tooling/test_validate_bundle_git_decided_input_face.py` **`3 passed`**（`egress guard` = `judged 0 / blocked 0`）。 |
| 2026-09-25 | DONE | WP3 收口：反证（worktree 先红后绿 + force-add 后**又红**）+ 判据按压（改动前 `TOTAL 4` → 改动后 `TOTAL 3`）+ **as-is 本机 m0 `PASS: profile=m0; 23 deterministic checks`**（`R-3` 消失，**不再需要代管**；证人文件仍在场）。复检 `RECHECK-20260925-181` = **PASS_WITH_WARNINGS**（7 条 AC 全成立；`W-1…W-5`）。工程记忆 `MEM-20260925-140`。 |

## 影响报告

- **改动**：`.cursor/skills/system-spec-check/scripts/validate_bundle.py`（门禁脚本：**只**改
  Markdown 链接扫描的**输入面** + 输入面不可用时的失败形态）、新增判据
  `tests/tooling/test_validate_bundle_git_decided_input_face.py`、记录面（`.cursor/plans/`）。
  `scratch/` 的反证与日志被 gitignore ⇒ **不入库**。
- **lint / typecheck / test**：`ruff check`（engineering + product）= `All checks passed!`；
  `ruff format --check` = 已格式化；`mypy` = `Success: no issues found in 1017 source files`；
  `tests/tooling` = **`1158 passed`**；治理 `validate.py` = 通过；`DOCS-CHECK` = PASS；
  **as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`M0_EXIT=0`）。
- **Domain / API / schema 变化**：无（门禁脚本不是 Domain / 产品代码）。
- **安全 / 凭据变化**：**收紧**而非放宽 —— 排除**只**作用于 gitignored 路径，
  **已跟踪文件一律照扫**（判据 ②③ 直接取证）；git 面不可用 ⇒ 硬失败（不再有「静默通过」的
  可能）。**未**放宽任何被判内容。
- **兼容性 / 迁移风险**：**输入面变小**（gitignored 路径不再被扫）是**有意的授权变更**；
  对 CI（干净检出）**无行为变化**；对本地**只**消除「别人的在制品污染本机门」这一现象。
  另两处 `repository_files()` 消费（`check_versions` 的版本号 / 旧版本命名）**保持全工作区**
  ⇒ 别人未跟踪文件里的旧版本号**仍**能判红（如实登记为 `RECHECK-181` 的 `W-1`，属**另一次
  授权**的范畴）。
- **上游版本影响**：无（零依赖变更）。
- **下一项任务**：GOAL-017 cycle 2 = EC-02（D-11 live 显式开关）。
