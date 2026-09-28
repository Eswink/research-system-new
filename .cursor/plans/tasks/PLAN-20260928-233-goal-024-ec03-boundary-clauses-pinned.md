---
id: PLAN-20260928-233
slug: goal-024-ec03-boundary-clauses-pinned
title: GOAL-024 cycle 4（EC-03）：观测隐私边界条款落文档 + 未覆盖面逐条登记 + 判据钉住（被点名判据文件改名即判红）
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-024
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-024 的 **EC-03**。授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为
    「**新增金丝雀判据与夹具**（一律落 `tests/**`）+ **文档同源更新**（
    `docs/architecture/OBSERVABILITY.md` / `docs/security/THREAT_MODEL.md` + `docs/INDEX.md` 登记）
    + **修被新判据证明为真缺陷**」；**不加新能力、不放宽任何判据、不改安全策略、不修改任何既有
    判据**；push-to-main-for-CI 口径（**只推 main、不 force**）。
    **本 PLAN 专属边界**：文档只固化**今天树上的事实**与**明确的空白**，**不作安全结论**；
    **不得**修改既有条款（§6 授权面、M15/M16 段一律不动，只**追加**新节）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **两条条款同时落在两份文档且逐字一致**：① canonical 允许持有用户输入（业务真相，不算泄漏）；
      ② 非 canonical 出口不得含内容（内容只允许出现在契约声明返回/保存它的载体上）。
      `docs/architecture/OBSERVABILITY.md` 与 `docs/security/THREAT_MODEL.md` 缺任一处判红。
    status: PASS
  - id: AC-2
    criterion: >-
      **受判面与口径在位**：OBSERVABILITY 新节必须给出 6 条受判出口与**读面白名单口径**，
      并点名钉住条款的判据文件（改名即判红）。
    status: PASS
  - id: AC-3
    criterion: >-
      **未覆盖面逐条登记**：debug mode 受控采样未验证 / 真实 collector 与生产部署面未验证 /
      CI 产物面不在射程 / `R-M1` 未收口 —— 四条在 OBSERVABILITY（全称）与 THREAT_MODEL
      （同口径）各自在位。
    status: PASS
  - id: AC-4
    criterion: >-
      **零夸大**：两份文档都带「不作安全结论」同义锚点；`docs/INDEX.md` 登记两处新增节；
      `tools/docs_consistency_check.py`（DOCS-CHECK）绿；新判据自身过四道门。
    status: PASS
  - id: AC-5
    criterion: >-
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**）；
      治理 `validate.py` 绿；CI 台账到终态。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-234-goal-024-ec03-boundary-clauses-pinned.md
memory_entries: []
---

# PLAN-20260928-233 — GOAL-024 cycle 4（EC-03）：边界条款与未覆盖面登记

**动因**：EC-01/EC-02 把「扫描面」和「零命中取证」做成了**可复跑判据**，但这些结论都还只
活在判据与记录里：**文档没有条款**，读者无法从 `docs/` 得知「canonical 允许持有什么」与
「非 canonical 出口的界线在哪」。EC-03 要求把界线写成**条款**并**由判据钉住**——条款不许
悬空指向不存在的判据（被点名文件改名即判红），未覆盖面**逐条登记**而不是含糊带过。

## 验收条件

见 frontmatter `AC-1`…`AC-5`。

## 实施清单

- [x] WP1：`docs/architecture/OBSERVABILITY.md` 追加「观测隐私边界与受判面（GOAL-024）」节：
      两条条款 + 6 条受判出口 + 读面白名单口径 + 5 个被点名判据文件 + 四条未覆盖面。
- [x] WP2：`docs/security/THREAT_MODEL.md` 追加第 7 节：同源两条条款 + 钉点 + 未覆盖面同口径 +
      「不得宣称项目安全」。
- [x] WP3：`docs/INDEX.md` 登记两处新增节。
- [x] WP4：`tests/observability/test_privacy_boundary_clauses_are_pinned.py`（145 行 / 9 例）：
      条款锚点 × 两份文档 / 受判面与口径锚点 / 未覆盖面逐条 / 零夸大锚点 / 判据文件存在性 /
      INDEX 登记 / 两条按压（改名判红、条款被改写判红）。
- [x] WP5：记录（本 PLAN / RECHECK / GOAL 回写）+ 记录面判据 + as-is m0 + push + CI 台账。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 钉点判据 | 9 例全绿（0.06s；最重的一条是存在性 + 逐字锚点） |
| DOCS-CHECK | `DOCS-CHECK PASS: 6 deterministic checks` |
| 既有文档 | 未改任何既有节（只追加新节）；`§6` 授权面草案与 M15/M16 段一字未动 |
| `tests/observability/` | **100 passed, 1 skipped**（较 cycle 3 的 91 增加 9 = 本轮新判据） |

**无可复用事实**（本 PLAN 不沉淀工程记忆：条款锚点与钉法是本仓文档惯例的直接应用，
无跨任务可复用增量）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 4，EC-03）。 |
| 2026-09-28 | DONE | 两份文档各追加一节（同源条款）、INDEX 登记、钉点判据 9 例全绿；DOCS-CHECK 绿。 |

## 影响报告

- **Domain/API/schema**：无（文档 + `tests/**`）。
- **安全/凭据**：无凭据改动；文档明确「不作安全结论」「`R-M1` 未收口」。
- **兼容性/迁移风险**：无。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-024 **EC-04**（自举收口：收口验证器进树 + 两树复检 + 终态台账）。
