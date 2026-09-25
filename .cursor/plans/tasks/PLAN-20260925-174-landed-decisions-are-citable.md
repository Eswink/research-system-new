---
id: PLAN-20260925-174
slug: landed-decisions-are-citable
title: D-07(b)/D-08(b)/D-09(a) 三处决定固化：ADR-0031 补「否证条件」+ 派生视图决定 + ADR-0032 非 ASCII 豁免
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
    承 GOAL-20260925-016 的 **2026-09-25 用户拍板（goal 模式）第 (4)/(5)/(6) 条**：
    **D-07 → 取 (b)** —— `ADR-0031` **维持 `Proposed`**，补一节**「否证条件」**，
    **不得改它的 `Status`**。**D-08 → 取 (b)** —— `ModelCompatibilityProfile`
    **维持派生视图**（不升一等 Domain 实体、不动 Canonical State），把该决定写成
    **可引用依据**，并写明「若取 (a)，**必须先出迁移与回滚的 ADR**」。
    **D-09 → 取 (a)** —— 为**非 ASCII 历史路径豁免**出 **ADR**（30 条，**不重命名**），
    引用 `AGENTS.md` §13。**授权边界**：三处都是**文档级**落地 ⇒ 零产品代码改动、
    零策略面改动、零门禁/判据放宽、零 rename。push-to-main-for-CI（只推 main、
    不 force、不重写历史、不推旁支）。**越界即 BLOCKED**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-175-landed-decisions-are-citable.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-137-exemption-needs-an-adr-and-a-counter.md
---

# PLAN-20260925-174 — D-07(b) + D-08(b) + D-09(a) 文档固化（GOAL-016 / EC-04）

## 目标

把三条**维持类**决定从「建议列」搬进**可引用、可复检、可被证伪**的正式依据：

1. **D-07(b)**：`ADR-0031` 仍 `Proposed`，但**补「否证条件」**——写清什么证据会证伪它、
   何时该改判。**`Status` 一行不动**（改了就是越权拍板）。
2. **D-08(b)**：`ModelCompatibilityProfile` **维持派生视图**；决定写入架构文档，
   并写明改成一等实体（选项 (a)）的**前置条件**。
3. **D-09(a)**：为非 ASCII 历史路径豁免出 **ADR-0032**，把「30 条、不重命名、引用 §13」
   变成一次性写清、以后只需引用的依据。

## 验收条件

- **AC-1｜判据（本 EC 的新判据）**：新增结构判据逐条实跑/逐字比对下列**全部**事实，
  且**自身可被按压**（删一条 ⇒ 报出、塞一条 ⇒ 报出）：
  - `ADR-0031` 第 3 行 `Status: Proposed`、全文无 `Status: Accepted`、且含 `否证条件` 节；
  - `MODEL_COMPATIBILITY.md` 含「维持派生视图」「必须先出 ADR」「Canonical State」「回滚」；
  - `ADR-0032` 存在、`Status: Accepted`、列入 `docs/INDEX.md`；
  - 非 ASCII 路径**现实 ↔ 清单双向**一致（`git -c core.quotepath=false ls-files` 数出来）。
- **AC-2｜`Status` 未被改动**：`ADR-0031` 的 `Status:` 行与 `HEAD` 逐字相同（`git diff`
  不含该行）；且既有「待拍板」类判据（`test_toolpack_capability_policy_pending.py`）
  与本 EC 新判据**同轮全绿**。
- **AC-3｜枚举陷阱被钉死**：判据里**同时**断言「朴素枚举（受 `core.quotepath` 转义）
  数为 0」与「带 `-c core.quotepath=false` 数为 30」⇒ 把假绿的口子写进判据本身。
- **AC-4｜零越界**：本 PLAN 的 diff **只含** `docs/` 与 `tests/` 记录面 + 本判据文件；
  **不含** `AGENTS.md`、`examples/config/policy.yaml`、任何域/服务/适配器代码、
  任何门禁脚本、任何 rename。
- **AC-5｜doc 一致性门**：`tools/docs_consistency_check.py` ⇒ **PASS**（首次跑出 2 条
  `[backtick-ref]` 指向不存在的路径 ⇒ 已按「指向真实对象」修正，**未**改门禁）。
- **AC-6｜m0 + 记录**：m0 终态行（标明树与跑法）+ 本 PLAN / RECHECK / MEM + GOAL-016 回写。

## 实施清单

- [x] WP1：`ADR-0031` 增 `## 否证条件（什么证据会否证本 ADR / 何时该改判）`（三个出口），
  `Status: Proposed` 保持不动；同轮跑既有「待拍板」判据确认未见红。
- [x] WP2：`MODEL_COMPATIBILITY.md` 增 §9（D-08(b) 决定 + 三条理由 + 代价登记 +
  `### 若要改成一等域实体（选项 (a)）的前置条件`）；`DOMAIN_MODEL.md` §5 加一段指回。
- [x] WP3：新建 `ADR-0032-legacy-non-ascii-path-exemption.md`（`Status: Accepted`）+
  登记 `docs/INDEX.md`；`ADR-0031` 的 `INDEX` 行加注「补否证条件、Status 仍 Proposed」。
- [x] WP4：新增判据 `tests/tooling/test_landed_decisions_are_citable.py`（6 条）。
- [x] WP5：doc 一致性门 + lint/format/mypy + 相关套件；m0 + 记录回写。

## 证据（本地）

- **判据**：`uv run --frozen --no-sync python -B -m pytest
  tests/tooling/test_landed_decisions_are_citable.py -q` ⇒ **`6 passed`**；
  `egress guard: judged 0 connection attempt(s); blocked 0`。
- **枚举事实（判据断言 + ADR-0032 正文同源）**：
  `git ls-files` 朴素枚举 ⇒ 非 ASCII **0** 条（`core.quotepath` 转义 + `\3` 形态）；
  `git -c core.quotepath=false ls-files` ⇒ 3389 条中 **30** 条。
- **`ADR-0031` 未被越权**：`Status:` 行仍 `Proposed`；`grep -c "Status: Accepted"` = **0**；
  `pytest tests/tooling/test_toolpack_capability_policy_pending.py
  tests/architecture/python/test_real_deliverable_contract_same_source.py -q`
  ⇒ **`18 passed`**（既有的「待拍板 / 可分别决定」口径未被本次改动破坏）。
- **套件回归**：`pytest tests/tooling tests/architecture/python/
  test_real_deliverable_contract_same_source.py -q` ⇒ **`1162 passed`**。
- **doc 一致性门**：`tools/docs_consistency_check.py` ⇒
  **`DOCS-CHECK PASS: 6 deterministic checks`**。
- **静态检查**：`ruff check` ⇒ `All checks passed!`；`ruff format --check` ⇒ 已格式化；
  `mypy` ⇒ `Success: no issues found in 1016 source files`。
- **m0**：见 GOAL-016 的 CI 台账与 RECHECK-175（终态行标明树与跑法）。

## 残余（本 PLAN 不处置）

- **D-07**：`ADR-0031` 仍是 `Proposed`——**「否证条件」不是拍板**。真正的拍板仍待
  人；本轮只把「什么会证伪、何时该改判」写清（这正是 (b) 的交付物）。
- **D-08**：选项 (a)（升一等域实体）**未做**，且**已写明前置条件**
  （必须先出迁移 + 回滚 + 一致性判据的 ADR）⇒ 谁想做谁先出 ADR。
- **D-09**：30 条路径**仍在原位**。豁免**不覆盖新路径**：新建非 ASCII 仍判红（规则与
  判据都未动）。若其中某条因**别的原因**被重命名，新名字**必须**满足 §13 并同步改清单。
- **`ADR-0032` 的 `Status: Accepted`** 是本轮按用户拍板 (a) 落的——与 `ADR-0031` 的
  `Proposed` **不冲突**：前者是「不再重命名」这一已执行事实的记录，后者是「要不要
  给 `tool_pack.*` 开口子」这一未拍板的问题。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-04 圈定三个决定（D-07/D-08/D-09），本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP3：三处文档落地（`ADR-0031` 否证条件 / `MODEL_COMPATIBILITY` §9 + `DOMAIN_MODEL` 指针 / `ADR-0032` + `INDEX`）。 |
| 2026-09-25 | IN_PROGRESS | WP4：判据先红后绿（`UNRENAMED_CLAUSE` 断行、`PRECONDITION_CLAUSE` 字面不一致 ⇒ 修的是**文档措辞**使其可被逐字引用，**未**放宽判据）⇒ `6 passed`。 |
| 2026-09-25 | IN_PROGRESS | WP5：doc 一致性门首跑 2 条 `[backtick-ref]` 假路径 ⇒ 改为指向真实对象（`010/011/012_*.sql`、本判据文件）⇒ `DOCS-CHECK PASS`。 |
| 2026-09-25 | DONE | WP5 收尾：静态检查 + 套件回归全绿；m0 与记录回写完成；复检 `RECHECK-20260925-175` 见 `latest_recheck`。 |

## 影响报告

- **改动**：`docs/adr/ADR-0031-toolpack-capability-policy.md`、
  `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`（新）、
  `docs/architecture/MODEL_COMPATIBILITY.md`、`docs/architecture/DOMAIN_MODEL.md`、
  `docs/INDEX.md`、`tests/tooling/test_landed_decisions_are_citable.py`（新）；记录文件。
- **lint / typecheck / test**：`ruff` / `ruff format` / `mypy` 全绿；
  `tests/tooling` + 同源判据 **`1162 passed`**；本 EC 判据 **`6 passed`**。
- **Domain / API / schema 变化**：**无**。D-08 的结论恰恰是「**不**改 Domain 边界」。
- **安全 / 凭据变化**：**无策略面改动**——`policy.yaml` 与 `_CAPABILITY_SCOPE`
  均不在 diff 内。
- **兼容性 / 迁移风险**：**零 rename、零改 `Status`** ⇒ 既有引用面不变。
  `ADR-0032` 的豁免是**一次性历史豁免**，不给新路径开口子。
- **上游版本影响**：无。
- **下一项任务**：GOAL-016 的 **EC-05（D-12 文档级威胁模型草案，零代码/门禁改动）**。
