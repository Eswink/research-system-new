---
id: RECHECK-20261008-334
slug: goal-036-ec03-04-consumption-and-registry
title: 独立复检：GOAL-036 cycle 2（EC-03/EC-04）`review.read` 真用 + 登记面与覆盖读数
plan_id: PLAN-20261008-333
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-334 — GOAL-036 cycle 2（EC-03/EC-04）独立复检

复检对象：`PLAN-20261008-333`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 真用的三段事实（AC-1）

| 读法 | 独立读数 |
| --- | --- |
| 判据文件 | `tests/e2e/test_review_read_on_the_run_path.py` **6 passed**（本文件重跑） |
| 实跑终态 | `SUCCEEDED` + `manifest_digest` 在场（冻结真的发生） |
| 调用证据 | `tool_refs = ["m12_artifact","review_read"]`，且该证据**属于 `consume` 任务**（按交付物制品名判 phase，不靠顺序猜） |
| 内容寻址 | 工具结果为 `tool-result:<task>:review_read:review_read`，读面取得到、`content_digest` 在场 |

### 2. 下游消费（AC-2，本 EC 的核心）

**读到的判词 = 落库的判词**（逐字）：
`ARTIFACT_EXISTS: artifact review_decision exists`、`REVIEW_SCORE: review score 0.95 GTE 0.8`。
**按压**（`review_read` 改成空结果）：**1 failed —— 只有下游消费那条判红**，其余 5 条照绿
⇒ 该断言**咬得住**它所声称的那件事（不是被别的臂掩盖）。

**如实边界**：读到的评审结论**内容正确**不在范围；**多评审者聚合**（GOAL-035 `N-3`）仍未
收口 —— 本 EC 只证「结论可读**且被读到**」。

### 3. 两向反证 + 覆盖读数（AC-3/AC-4）

| 臂 | 读数 |
| --- | --- |
| 缺实现 | run `FAILED`；判词点名 provider 与工具 id；**零调用证据**（反证臂不得假绿） |
| 未放行 | run `FAILED`；run 级判词 `preflight failed: POLICY_DENIED`；**报告面** finding 点名能力（`policy denied capability review.read: used default policy effect`） |
| 覆盖读数 | 词表 46（未改）/ 声明面 distinct **19 → 20**；新承接 = `review.read → ['m12_artifact']`（逐条，**不做数量目标**） |
| 只读面 | 分类清单纯收紧（`_IN_SCOPE` +1、登记表 −1）、夹具同轮 +1；写面 / 执行面 / 审批面零变化 |

### 4. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| `tests/e2e` + `tests/contracts` + `tests/loaders` + `tests/application` + `tests/architecture` | **1887 passed, 86 skipped** |
| 新增 3 个文件（协议 / 合约 / 支撑件） | `ruff check` / `format` / `mypy` 绿（既有四道门口径） |
| **as-is m0**（在全部记录写入之后独占跑） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5367 passed, 20 skipped**；收集数 **+8** 逐文件分解 = 新判据 6 例 + 源文件参数化 +2（新判据与支撑件各一条）；`skipped` 20 未升） |

**一次真红并修（如实登记）**：m0 首跑 `python/product-lint` + `python/typecheck` 判红 —— 本轮新判据的 import 未排序（`ruff`）与支撑件的两处 union/None 收窄（`mypy`）。处置是**修代码**（`ruff --fix` + 显式 `assert` 收窄），**未**改任何 lint / mypy 配置或断言；随后广面四道门与全量 m0 重跑通过。

### 5. 未覆盖 / 一等边界

- **只证「读到」**：读到的结论是否**影响了**交付物的科学结论不由本判据把守
  （验收门只判 `meta_review` 存在 —— 与 `real_research_deliverable_v1` 的既有边界同一条）；
- **角色如实登记**：`meta_reviewer` 在 `roles.yaml` 里声明了 `review.read`，但本地离线控制面
  的 agent 池**没有**该角色的实例 ⇒ 本协议按**实际在场**的池选 `scientific_reviewer`
  （**不为了让判据过而往夹具塞 agent**）；
- **不得**声明项目安全（`R-M1` 未收口）；**不得**宣称投递语义为那四个字（**明确否认**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-03、EC-04 逐条独立成立；**无产品缺陷**。

### Warnings

- **W-1（角色池的现实约束）**：`meta_reviewer` 无 agent 实例 ⇒ 用同池的另一位认证评审者读
  前序结论。这不是缺陷，但**必须登记**：多评审者聚合的接线（GOAL-035 `N-3`）仍需该角色的
  实例与聚合逻辑，本轮不涉及。
- **W-2（读结果与科学结论的关系未证）**：见第 5 节第一条。
- **W-3（承继残余原样保持）**：GOAL-035 的 `N-1`…`N-6`、`R26-*` 终态、未覆盖范围逐条保持。
- **W-4（GOAL 级未覆盖）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；**不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
