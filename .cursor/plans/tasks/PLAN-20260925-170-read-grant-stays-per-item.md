---
id: PLAN-20260925-170
slug: read-grant-stays-per-item
title: D-02(b) 口径判据：读类能力逐条授权、不成类放行（含否定判据 + 15 条证据面）
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
    承 GOAL-20260925-016 的 **2026-09-25 用户拍板（goal 模式）第 (2) 条**：
    **D-02 → 取 (b)** —— 读类能力**维持逐条放行**（**不**成类预放行、**不**新增任何 `allow`）。
    交付 = 判据钉住「新增读能力必须逐条授权」这条口径 + 引用差集表（**该登记 15 条**）
    作为证据面。**本项零策略面改动**：`examples/config/policy.yaml` 与
    `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` **都不得**出现在
    本 GOAL 的改动集里。**本 PLAN 的边界**：只增一个**判据测试文件** + 记录；
    **零产品代码改动**、**零策略面改动**、**零门禁改动**、**不新增依赖**、**零真实出网调用**。
    push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-171-read-grant-stays-per-item.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-135-negative-criteria-need-a-pressable-detector.md
---

# PLAN-20260925-170 — D-02(b) 口径判据（GOAL-016 / EC-02）

## 目标

把用户拍板的 **D-02(b)**（「读类能力**维持逐条放行**」）从**口径**变成**机械判据**：
让「我们没有成类放行」这句话**可被判红**，并让「15 条该登记的读能力一条都没被放行」
成为**可核对的证据**，而不是口头承诺。

**本 PLAN 不碰策略面**：既有的逐条 `allow` 一条不加、一条不减；`default_effect: DENY` 不动。

## 验收条件

- **AC-1｜逐条形态**：策略面每个 `capability:` 都是能力词表的**精确成员**，且**没有**任何规则
  的能力是另一个能力的**段前缀**（`read` 覆盖 `read.x` 正是「成类放行」的结构特征）。
- **AC-2｜否定判据（且可被按压）**：策略面全部 `capability:` 里**不存在**通配符（`*` / `?`）、
  不以 `.` 结尾；**检测器必须可被按压**——注入 `read.*` ⇒ 命中，注入 `literature.` ⇒ 命中
  （否则该断言是恒真的空转）。
- **AC-3｜证据面 15 条**：从差集表读出的「该登记」行**恰好 15 条**、**全部是读类**、
  且**一条都没有**出现在策略面的任何 `capability:` 里（⇒ 未取成类预放行）。
- **AC-4｜读类放行逐条可枚举**：每条读类放行都必须有**精确命名**它的规则，且不被任何前缀规则
  同时覆盖。
- **AC-5｜零策略面改动**：`git diff --name-only` 证明
  `examples/config/policy.yaml` 与 `packages/application/preflight/policy_check.py`
  **不在**本 GOAL 的改动集里；判据只读这两个文件（按压用**内存内字典**，不落盘）。

## 实施清单

- [x] WP1：写判据 `tests/application/preflight/test_read_grant_is_per_item.py`
  （4 个测试 = AC-1…AC-4；只读两个策略面文件）。
- [x] WP2：`ruff check` + `ruff format` 两道门（首轮 `ruff format --check` 判红 ⇒ 格式化后复跑）。
- [x] WP3：取证「零策略面改动」（逐文件 `git status` 为 0、`git diff --stat` 为空）。
- [x] WP4：定向回归套件 + 规模 / 命名门禁。
- [x] WP5：记录（本 PLAN + RECHECK + MEM）与 GOAL-016 回写。

## 证据（本地）

- 判据：`uv run --frozen --no-sync python -B -m pytest
  tests/application/preflight/test_read_grant_is_per_item.py -q` ⇒ **`4 passed`**。
- lint：`ruff check` = `All checks passed!`；`ruff format --check` = `1 file already formatted`。
- **零策略面改动**：`examples/config/policy.yaml` 与
  `packages/application/preflight/policy_check.py` 的 `git status --short` 输出**行数 = 0**、
  `git diff --stat` **为空**。
- 证据面（15 条「该登记」，判据与文档同源读出）：`agent_run.read`、`budget.read`、
  `citation.inspect`、`citation.validate`、`claim.read`、`dataset.read`、`deliverable.read`、
  `experiment.read`、`experiment_plan.read`、`provenance.read`、`research_map.read`、
  `research_state.read`、`review.read`、`run.read`、`target.read`。
- m0：见 GOAL-016 的 CI 台账与 RECHECK-171（两个终态行分开写清）。

## 残余（本 PLAN 不处置）

- 本判据**不**判定某个读能力**该不该**放行（那是逐次授权时的判断）；它只钉住放行的**形态**。
- 「新增读能力会反复撞 `default_effect`、每次都要一次 GOAL 级授权」这一**摩擦**是 D-02(b) 的
  **已知代价**，**原样保留**；成类预放行属「`W-A` 之外的策略面放宽」，**需另行拍板**。
- 差集表本身（15 条）由 GOAL-014 的判据与文档同源维护；本 PLAN 只**引用**，不改它。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-02 圈定主题（D-02(b) 口径判据），本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP3：判据落盘（`4 passed`）；`ruff format` 判红 ⇒ 格式化后复跑；零策略面改动取证完成。 |
| 2026-09-25 | DONE | WP4–WP5：定向回归 + 门禁绿；记录与 GOAL-016 回写完成；复检 `RECHECK-20260925-171` 见 `latest_recheck`。 |

## 影响报告

- **改动**：新增一个判据测试文件（`tests/application/preflight/`）；无产品代码、无策略面改动。
- **lint / typecheck / test**：`ruff check` = `All checks passed!`、
  `ruff format --check` = 已格式化；判据 `4 passed`；定向回归套件见 RECHECK-171。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：无（判据只读 YAML 与 Markdown；零出网、零凭据）。
- **兼容性 / 迁移风险**：无——纯新增判据；`default_effect: DENY` 与既有逐条 `allow` 一字未动。
- **上游版本影响**：无（未新增依赖、未改 pin）。
- **下一项任务**：GOAL-016 的 **EC-03（D-03(b) 4 条 high 依赖升级）**——本轮**唯一动产品依赖**的 EC。
