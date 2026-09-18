---
id: PLAN-20260918-093
slug: security-audit-residual-recheck
title: 安全审计残留复核：依赖 advisory 联网署名 + 干净 checkout 重扫封印 + hook 侧 scanner_enobufs 根因（EC-01）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 1 = EC-01（GOAL-004 收口结论表第 1 项 / RECHECK-091 W-1…W-5）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-093-security-audit-residual-recheck.md
memory_entries:
  - MEM-20260918-067
---

# PLAN-20260918-093 — 安全审计残留复核（GOAL-005 cycle 1 = EC-01）

## 目标

GOAL-004 EC-07 把安全审计推到了「扫描跑通 + 36 条逐条处置」，但收口时如实登记了四条
未决（RECHECK-091 W-1…W-5）。本 PLAN 把其中**可复核**的三条做成终态：

| 残留 | 本 PLAN 的终态 |
| --- | --- |
| W-1 依赖 advisory「1 包 1 条」**未署名**，需联网复核 | 413 个锁定包逐一查询 OSV ⇒ **3 包 20 条**，每条带 CVE 别名 / CVSS / 修复版本 / 来源包（§证据） |
| W-3 扫描输入含 `scratch/`（17）+ `artifacts/`（2）等 gitignored 内容 | **干净 checkout**（`git archive` 导出 tracked 内容）重扫 ⇒ 新 scanId + seal，25 条 findings |
| W-2 hook 侧 `scanner_enobufs` 未消除 | **复现 + 根因定位**（检测层 semgrep 未安装）+ 可复现配方 + 人工步骤（§证据） |

W-4（`artifacts/` 内明文 token 未跟踪）与 W-5（威胁建模/授权面零覆盖）**不在本 PLAN**：
前者属操作者清理决策，后者写进「未覆盖范围」并升格为本 GOAL 的「不进入循环」项。

## 口径

- **判 PASS 的依据 = 可复核的署名与封印 + 可重跑命令**；「扫描没报问题」「复核无问题」
  这类空话**不构成**依据。
- **干净 checkout 的硬判据**：导出树文件数 == `git ls-files` 条数，且树内不存在
  `scratch/`、`artifacts/`；扫描根 = 该导出目录（仓库外）。
- **联网复核失败**必须如实记「仍不可判定」并把该 EC 留在未判定状态，**不得**反读为
  「没有已知漏洞」。
- 本 PLAN **不改产品代码、不改依赖版本**：依赖升级属 pin 变更（`escalation_triggers`），
  本轮只交付署名与结论 + 影响面判定，处置留给用户/ADR。

## 验收条件

- AC-01 干净 checkout 导出**可复核**：导出文件数 == `git ls-files` 条数；树内无
  `scratch/`、`artifacts/`。
- AC-02 干净 checkout 上的密封深扫**跑通**并读到 `scanId` / `seal` / `findingCount`；
  三件产物 sha256 与 `seal.json.artifacts` 逐件一致。
- AC-03 输入边界的**判据有效性**：工作树扫描与干净 checkout 扫描的 findings 差异可解释
  （差异应等于落在非仓库内容上的条数）。
- AC-04 依赖 advisory 复核给出**署名与结论**：包名 / 版本 / advisory id / CVE 别名 /
  CVSS / 修复版本 / 谁引入（来源）；查询命令与 lockfile digest 可复跑。
- AC-05 hook 侧 `scanner_enobufs` **复现**（≥2 次一致）+ **根因**（可验证的检出证据）
  + 修复配方与人工步骤；不可复现的话按配方形态交付（本轮可复现）。
- AC-06 findings **逐条处置**（每条：结论 / 依据 / 处置），依据落到可重跑检索或已执行用例。
- AC-07 **未覆盖范围**写明；记录中不出现「项目安全 / 无漏洞」式断言。
- AC-08 记录链完整（PLAN / RECHECK / MEM / ALL_PLAN / GOAL）+ 治理 validator 绿
  + 本地 m0 全绿 + CI 六 job 终态如实记录。

## 实施清单

### WP-A — 干净 checkout 重扫（已完成）

- 导出：`git archive HEAD | tar -x -C <仓库外目录>`；实测 **3025 个文件** == `git ls-files`
  3025 条；树内无 `scratch/` / `artifacts/`。
- 扫描：MCP `security_scan_start(project=<导出目录>, depth=deep)` → `completed`；
  `scanId scan-2026-09-18T05-00-08.268Z-e6e01fa153c8`、`seal sha256:1e549272…`、
  `findingCount 25`（high 1 / medium 19 / low 5）。
- 封印复核：三件产物逐件重算 sha256 与 `seal.json.artifacts` **全 OK**。
- 差异解释：`artifacts/` 2 条 HIGH + `scratch/` 17 条 MEDIUM 在新剖面里**归零**；
  `tools/` 由 10 条升到 18 条（旧扫描在文件上限下漏扫了部分 `tools/` 文件）。

verify：导出计数对照、`security_scan_status` 的 result 字段、逐件摘要重算输出（已执行）。

### WP-B — 依赖 advisory 联网复核（已完成）

- 新增 `tools/probes/probe_dependency_advisories.py`：**不含网络代码**，只读 lockfile、
  构造 OSV `querybatch` payload、合并响应；出网由操作者的 `curl` 完成（命令写进记录）。
- 查询 413 个锁定包（PyPI 149 + npm 264）⇒ **3 包 20 条**：`undici@5.29.0`（12，
  来源 `@cursor/sdk@1.0.30`）、`vite@6.3.5`（7，`apps/web` devDep）、`yaml@2.8.1`
  （1，`apps/web` devDep）；全部带 CVE 别名与 `fixedVersions`。
- 证据文件 `docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20260918.json`（含 lockfile
  sha256、复跑命令、每条 advisory 的 CVE / CVSS / 修复版本）。
- **影响面判定**：三个包均不在生产运行依赖链上（`apps/web` 运行依赖只有 react/react-dom），
  但 dev 链仍跑在开发者机器与 CI 上 ⇒ 只登记，不改版本（pin 变更 = escalation）。

verify：`probe_dependency_advisories.py` 两步（build / merge）实跑输出；`curl` 的
HTTP 200 与响应包数；对照 `pnpm-lock.yaml` 的 importers/snapshots 溯源。

### WP-C — hook 侧 `scanner_enobufs` 复现与根因（已完成）

- 复现：手工喂 PreToolUse(Bash/`git commit`) payload 给 `git-gate-hook.mjs`，
  **2/2 次**同样输出 `INCONCLUSIVE（scanner_no_output）`（790 ms / 767 ms）。
- 根因：`cli.js semgrep status --json` ⇒ `installed:false` / `healthy:false` /
  `reason:install_metadata_missing`，`installDir`（`~/.zcode/mimosa-runtime/semgrep-1.136.0`）
  不存在；`which semgrep` 与 `pip show semgrep` 均无。
- 旁证：`~/.zcode/mimosa-debug.log` 的 stop-hook 批量扫描
  `spawnSync D:\environment\nodejs\node.exe ETIMEDOUT`（224 行，2026-09-02 起）与
  `scan-profiles.json` 的 `gate` 时限（`hardTimeoutMs 1000`）同源。
- 交付：安装配方 + 验证命令 + **执行前须知的后果**（`graded` 模式下 medium=ask 会挡住
  无人值守提交）——**本轮不安装**（环境变更 + 安全策略决定）。

verify：hook 复现命令与逐字输出；`semgrep status --json` 原文；debug log 取证行。

### WP-D — 记录与门禁（已完成）

- 新增 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md`（§1 干净 checkout / §2 依赖
  advisory / §3 enobufs 根因 / §4 25 条逐条处置 / §5 未覆盖范围 / §6 结论 / §7 复现配方）
  与证据 JSON；`docs/INDEX.md` 登记两件。
- **方法学更正**：上一轮「产品树动态 SQL 零命中（grep）」被本轮的 **AST 结构判据**
  （`tools/probes/probe_dynamic_sql_forms.py`）更正为「22 处构造，逐处核对为模块常量 /
  固定 `now()`|`%s` 记号，取值全部参数绑定」——结论（安全）不变，**依据**升级；
  探针自带 `--selftest`（合成 AST 节点，8/8 ok）证明判据非空转。
- 写 RECHECK-20260918-093、MEM-20260918-067、PLAN DONE、`ALL_PLAN` 行、GOAL-005 回写。

verify：治理 validator 绿；`make validate-all` 全量 23 项 + 定向套件；CI 六 job 终态记账。

## 证据

- **干净 checkout**：导出 3025 文件 == `git ls-files` 3025；无 `scratch/` / `artifacts/`；
  `scanId scan-2026-09-18T05-00-08.268Z-e6e01fa153c8`；
  `seal sha256:1e549272da4ebf65a87b02d195bf714ed3ef75b29b2db6d689331a617b51116d`；
  三件产物 sha256 复核 **OK / OK / OK**；剖面 25 = 1 / 19 / 5。
- **差异表**（判据有效性）：工作树 36（`artifacts/` 2 HIGH + `scratch/` 17 MEDIUM +
  `packages/` 1 HIGH + `services/` 1 + `tools/` 10 + `examples/` 5）→ 干净 checkout 25
  （`packages/` 1 + `services/` 1 + `tools/` 18 + `examples/` 5）。
- **依赖 advisory**：`docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20260918.json`；
  lockfile digest（`uv.lock` `98af1c42…` / `pnpm-lock.yaml` `fb03b4db…`）；
  413 查询（149 + 264）⇒ 3 包 20 条；扫描器自报两次互相矛盾（182/1 与 11/0）。
- **hook 根因**：hook 逐字输出（`scanner_no_output`，2/2 次）；`semgrep status --json`
  原文；`mimosa-debug.log` 的 `ETIMEDOUT` 取证行；`scan-profiles.json` gate 时限。
- **动态 SQL 结构判据**：`probe_dynamic_sql_forms.py --selftest` 8/8 ok；
  `--root packages --root services --root adapters` ⇒ 510 文件 / **22 处**（逐处核对）；
  `--root tools` ⇒ 33 文件 / 0 处。
- **已执行用例**（沿用并复跑）：`tests/application/protocol_authoring/test_draft_service.py`
  **13 passed**；`tests/tooling/test_python_source_limits.py` **930 passed**。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 1 = EC-01，driver=client-goal /
  owner=root-agent）：`status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A/WP-B/WP-C/WP-D 完成；干净 checkout 重扫封印成立（25 条逐条处置，
  全部误报/开发工具，**无产品代码变更**）；依赖面首次拿到**署名**（3 包 20 条，全在 dev 链，
  升级留人工）；hook 侧根因定位为检测层缺失；`status: DONE`。

## 影响报告

- **Domain / API / schema**：无变化（本 PLAN 只新增审计文档、证据 JSON 与两个开发探针）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无凭据面变更。登记两条**待人工决策**的安全事项：① 依赖 pin 升级
  （`undici` / `vite` / `yaml`，全在 dev 链）；② hook 侧 L3 门修复（安装 semgrep 或调整
  门模式），两者都命中 `escalation_triggers`。
- **兼容性 / 迁移风险**：无（新增文件均为文档与 `tools/probes/` 下的一次性探针）。
- **上游版本影响**：**未变更**任何依赖或 pin（探针只用 stdlib + 既有 `yaml`）。
- **下一项任务**：GOAL-005 cycle 2 = EC-02（`resume_after_approval` 同形未补偿入口）。
