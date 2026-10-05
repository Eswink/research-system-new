---
id: PLAN-20261005-289
slug: goal-030-ec04-criterion-scope-self-check
title: GOAL-030 cycle 4（EC-04）：判据射程自查 —— 观察器 + 射程自查表 + 掩蔽形态的可判红用例（并抓到扫描器自身的同族缺陷）
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-290-goal-030-ec04-criterion-scope-self-check.md
memory_entries: []
parent_goal: GOAL-20261005-030
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261005-030 的 **EC-04**。授权沿用该 GOAL 的 `authorization.ref`：
    「新增判据 / 夹具（落 `tests/**`）」+ push-to-main-for-CI 口径（**只推 `main`**、不 force、
    不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面；**不动** `policy.yaml`；
    **零**新依赖；**不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 GOAL-029 的教训（判据曾把受判面写成 `declared ∩ implemented` 而掩蔽缺口）**提前**做成
    机械事实：对**本轮新增的每条判据**检查受判面是否**被收窄**，产出射程自查表，并给出一个
    **能判红的用例**证明自查本身有效。
exit_criteria:
  - id: AC-1
    criterion: >-
      **观察器**（`scan_judge_faces`）：AST 扫描判据文件，识别三种掩蔽形态
      （断言里出现交集 / 遍历面被交集收窄 / 遍历面被差集收窄），并**跟进一层数据流**
      （掩蔽通常藏在赋值里，`missing = [x for x in a & b …]`）。
    status: PASS
  - id: AC-2
    criterion: >-
      **射程自查表**（`SCOPE_TABLE`）：本轮**每条**判据逐条登记四要素（受判面定义 /
      是否可能掩蔽 / 按压形态 / 实测结果）；未登记者、幽灵条目、空理由、断言条数低于下界
      —— 四种形态各自判红。
    status: PASS
  - id: AC-3
    criterion: >-
      **反证（本判据自己的可判红用例）**：① GOAL-029 的**原形**（`for x in declared & implemented`）
      喂给观察器 ⇒ 报出；② 差集收窄遍历面 ⇒ 报出；③ **诚实的缺口计算**
      （`set(expected) - set(actual)`）⇒ **报空**（不得把正确写法判红）；
      ④ 本轮三条真实判据 ⇒ 报空。
    status: PASS
  - id: AC-4
    criterion: >-
      **端到端按压**：把一条**真实判据**（EC-01 的 `test_each_declared_capability_leaves_a_call_evidence`）
      按压成掩蔽形态 ⇒ 主判据判红并点名行号与形态；复原后逐字节一致、全绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **抓到扫描器自身的同族缺陷并修**（本轮实测）：`_assigned_set_ops` 初版用**单值 dict**
      ⇒ 同一名字在文件里被赋值多次时**后写覆盖前写**，被按压成掩蔽形态的那一次被后来的诚实
      写法覆盖 ⇒ 扫描器报空（`MEM-20260922-160` 的形态出现在自查器自己身上）。修法 =
      每个名字保留**全部**赋值 + 单列用例 `test_the_assignment_index_keeps_every_definition`
      （按压：改回单值 ⇒ 该用例判红）。
    status: PASS
  - id: AC-6
    criterion: >-
      **不改既有判据 / 门禁**：本轮只**新增**一个判据文件；既有面逐字节未改且全绿。
    status: PASS
---

# PLAN-20261005-289 — GOAL-030 cycle 4（EC-04）

## 它解决什么

GOAL-029 的 EC-02 主判据曾把受判面写成 `declared ∩ implemented` ⇒ 「声明了但没实现」在
**构造上不可能被报出**；那是**完成核验**时才抓到的（承 `MEM-20260922-160`）。
本 PLAN 把这件事**提前**做成机械事实，并**在自查器自己身上**又抓到同族缺陷一次（`AC-5`）。

## 改动（显式路径）

| 文件 | 改动 |
| --- | --- |
| `tests/tooling/test_criterion_scope_self_check.py` | **新增判据**（439 行，10 passed）：观察器 + 射程自查表 + 合成反证 + 端到端按压 + 自查器自缺陷用例 |

**产品代码零改动**；无新能力、无新放行、无新依赖。

## 掩蔽形态的**定义**（本判据的核心）

不是「集合运算出现在断言里」，而是**受判的那个集合本身被收窄了**：

- `intersection_as_expectation`：断言里出现 `&`；
- `intersection_narrowed_universe`：**遍历面**被交集收窄（`for x in declared & implemented`）
  —— GOAL-029 的原形；
- `difference_narrowed_universe`：**遍历面**被差集收窄（`for x in a - b`）。

**关键区分（观察器初版实测误报过）**：`missing = set(expected) - set(actual)` 后
`assert missing == []` 是**诚实的缺口计算**（遍历面完整 ⇒ 「应有而未有」照样被报出），
**不得**判红。单列用例 `test_honest_gap_computation_is_not_reported` 钉住它。

## 射程自查表（EC-04(b) 的交付物，摘要）

| 判据 | 受判面 | 是否可能掩蔽 | 实测 |
| --- | --- | --- | --- |
| `test_capabilities_really_used_in_a_run.py`（EC-01） | 三条能力 × 两 phase 的调用证据 + 下游返回内容 + 反证终态 | **初版有掩蔽（单键索引后写覆盖）⇒ 已修** | 判红（两处按压） |
| `test_run_read_onboarding.py`（EC-02） | 声明 / 承载 / 绑定（**分别断言**）+ 逐字段比对 + 三种缺失点名 | 无（观察器报空） | 判红（撤回映射 ⇒ 3 failed） |
| `test_scientific_action_depth.py`（EC-03） | 容器产出 + 六字段 + 三读面 + 下游消费 + 目录阈值逐字 + 实测值 | **初版有掩蔽（只判机制漏数值）⇒ 已补齐** | 判红（三处按压） |

（完整四要素版在 `SCOPE_TABLE` 里，逐条带按压读数与断言下界。）

## 按压记录（三处，全部逐字节复原）

1. **合成 GOAL-029 原形** ⇒ 报出 `intersection_as_expectation` + `intersection_narrowed_universe`；
2. **端到端按压 EC-01 的真实判据** ⇒ 主判据判红并点名（文件 + 行号 + 形态）；复原 ⇒ 10 passed；
3. **按压自查器自身的修复**（`_assigned_set_ops` 改回单值 dict）⇒
   `test_the_assignment_index_keeps_every_definition` 判红
   （`('同名多次赋值时，前一次的掩蔽形态被覆盖 ⇒ 扫描器漏报', [])`）；复原 ⇒ 10 passed。

## 本地验证

- `tests/tooling/test_criterion_scope_self_check.py` ⇒ **10 passed**；
- `tests/tooling` ⇒ **1314 passed**；
- `tests/architecture/python + tests/application + tests/adapters + tests/e2e + tests/api +
  tests/loaders` ⇒ **2334 passed / 21 skipped**；
- `ruff check` / `ruff format --check` / `mypy`（1099 files）/ 规模门绿。

## 剩余差距

- EC-05（自举收口）未做；
- 观察器是**形态检测**（AST 层），**不是语义证明** —— 语义级的射程仍靠按压（本 GOAL 各 EC
  都做了）；既有判据不在本轮射程面内。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-6）。

## 实施清单

- [x] **WP-A（观察器）**：`scan_judge_faces` + 三种掩蔽形态 + 一层数据流跟进。
- [x] **WP-B（射程自查表）**：`SCOPE_TABLE`（三条判据 × 四要素 × 断言下界）。
- [x] **WP-C（反证）**：合成原形 / 差集形态 / 诚实计算 / 真实判据 —— 四种输入。
- [x] **WP-D（端到端按压）**：按压真实判据 ⇒ 判红；复原 ⇒ 绿。
- [x] **WP-E（自查器自缺陷）**：抓到并修 `_assigned_set_ops` 的后写覆盖 + 单列用例。
- [x] **WP-F（记录）**：本 PLAN + `RECHECK-20261005-290` + `ALL_PLAN` 投影 + GOAL 回写。

## 证据

- **判据**：`uv run --frozen --no-sync python -B -m pytest tests/tooling/test_criterion_scope_self_check.py -q`
  ⇒ **10 passed**。
- **端到端按压判词**：主判据在按压后点名
  `('本轮判据出现掩蔽形态（受判面被交集/差集收窄 ⇒ 最该被抓的形态发不出声）', [(path, lineno, form), …])`。
- **自查器自缺陷判词**：`('同名多次赋值时，前一次的掩蔽形态被覆盖 ⇒ 扫描器漏报（本判据自己的缺陷形态）', [])`。
- **受判面**：`tests/tooling` 1314 passed；其余六套合跑 2334 passed / 21 skipped。
- **质量门**：`ruff check` / `ruff format --check` / `mypy`（1099 files）/ 规模门（439 行）绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 4 derive）并执行 WP-A…WP-C。 |
| 2026-10-05 | DONE | WP-D/WP-E 抓并修**自查器自身**的同族缺陷；判据 10 passed；`RECHECK-20261005-290` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：新增判据 1 文件（439 行）。**产品代码零改动**。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：无。
- **兼容性/迁移风险**：无（纯新增）。
- **上游版本影响**：无。

## 无可复用事实

本 PLAN 的产出是**自查判据**。其中一条教训值得沉淀但**已有更一般表述**：
「自查器的数据流跟进若用后写覆盖的索引，会把『被按压成掩蔽形态的那一次』吃掉」——
这是 `MEM-20260922-160` 的又一实例，写在 `RECHECK-20261005-290` 的 `W-1`，
**不另立 `MEM`**。
