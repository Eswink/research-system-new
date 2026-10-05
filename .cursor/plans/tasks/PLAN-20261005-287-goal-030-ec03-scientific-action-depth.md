---
id: PLAN-20261005-287
slug: goal-030-ec03-scientific-action-depth
title: GOAL-030 cycle 3（EC-03）：科研动作的深度 —— 真容器实验 + 可否证的指标判据 + 下游消费 + 反证点名
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-288-goal-030-ec03-scientific-action-depth.md
memory_entries: []
parent_goal: GOAL-20261005-030
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261005-030 的 **EC-03**。授权沿用该 GOAL 的 `authorization.ref`：
    「扩充『科研子迭代』的深度（更多 phase / 更多 role / 更真实的科研动作）」+
    「新增判据 / 夹具（落 `tests/**`）」+ push-to-main-for-CI 口径（**只推 `main`**、不 force、
    不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面；**不动** `policy.yaml` /
    `default_effect`；**不让任何未放行能力变为协议可达**；**零**新依赖（实验脚本纯标准库）；
    **不放开默认网络**（实验不出网）；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once +
    idempotency + deduplication）。
objective: >-
    在 EC-01 的读能力之上加一个**产生新知识**的动作：真实容器里跑一次确定性基准实验，
    给它的科学结论下一道**可否证**的判据（`METRIC_THRESHOLD`），让下游 phase 消费它留下的
    证据，并用「抬高阈值 ⇒ 判拒并点名那个数」证明那道判据**真的在判**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **真科研动作**：实验由**真实容器**执行（`image_digest` 在场），产出的指标是**科学测量**
      （两法各自的比较次数 / 一致性 / 比值），不是流程计数。
    status: PASS
  - id: AC-2
    criterion: >-
      **结构化产出**：`metrics` 制品存在，**逐字段**可断言（字段名与实验脚本写死的一致，
      判据不 import 脚本当预言机）。
    status: PASS
  - id: AC-3
    criterion: >-
      **canonical 落盘 + 读面可复核**：制品经 `GET /runs/{id}/artifacts` 与
      `GET /artifacts/{id}/content` 取得到；实验记录经 `GET /runs/{id}/experiments` 可见；
      实验证据在 `GET /runs/{id}/evidence` 上（带 `experiment_run_id`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **下游消费**：`verdict` phase 在 experiment **之后**运行，其 `evidence.read`
      **返回内容**含实验留下的证据 id ⇒ 「跑完没人看」不成立。
    status: PASS
  - id: AC-5
    criterion: >-
      **反证（下游判负并点名）**：把那条判据的阈值抬到实验达不到的水平 ⇒ 该 phase **判拒**、
      run `FAILED`，且判词**点名指标与断言**（`comparison_reduction_ratio` + 算子 + 阈值）。
      ⇒ 证明那道阈值**真的在判**（不是装饰）。
    status: PASS
  - id: AC-6
    criterion: >-
      **判据自身的射程缺口（本轮实测抓到并已闭合）**：反证臂改的是**运行时快照**，
      它证明「阈值被判了」；但**出厂目录里那个数**若被改小（实测 100 → 1）反证臂**仍通过**
      ⇒ 「本协议对科学结论下了可否证的判据」这句话**没有受判**。补 `TestTheFalsifiable
      CriterionIsPinnedInTheCatalog`：目录里判据在场 / 指标名 / 算子 / **阈值逐字**，
      且实验**实测值确实越过阈值**（非空真）⇒ 改小阈值**判红**。
    status: PASS
  - id: AC-7
    criterion: >-
      **不改既有判据 / 门禁**：`tests/contracts/**` 等既有面**逐字节未改**且全绿；
      新增协议与三份契约只追加。
    status: PASS
---

# PLAN-20261005-287 — GOAL-030 cycle 3（EC-03）

## 它比 EC-01 多什么

EC-01 证的是「承接的读能力真的被用上」，那三条读的是**已经存在**的 canonical 状态。
本 PLAN 加一个**产生新知识**的动作，并给它的结论下一道**可否证**的判据。

## 改动（显式路径）

| 文件 | 改动 |
| --- | --- |
| `examples/protocols/scientific_action_depth_v1.yaml` | **新增协议**：3 phase（`probe` 读 / `experiment` 真科研动作 / `verdict` 下游消费） |
| `examples/contracts/task_contracts.yaml` | **追加**三份契约；其中 `scientific_action_experiment` 带 `METRIC_THRESHOLD: comparison_reduction_ratio GTE 100` |
| `tests/e2e/test_scientific_action_depth.py` | **新增判据**（9 passed） |

## 科研动作是什么（为什么它「像研究」而不是「跑个脚本」）

- **问题**：在一份**确定性语料**（800 条、注入 40 对重复）上做精确重复检测，
  两两比较 O(n²) 与哈希索引 O(n) **结果一致**时，比较次数差多少？
- **可否证**：合约对 `comparison_reduction_ratio` 下 `GTE 100` 的**真实阈值** ——
  索引法若没把比较次数降两个数量级，判据**判拒并点名那个数**。
- **不自证**：脚本自己校验 `agreement` 与 `duplicates_found`，不一致即非零退出
  （不给「跑完了但没结论」留后门）。

## 按压记录（三处，全部逐字节复原）

1. **抬高阈值**（运行时快照：`1e6`）⇒ 实验 phase **判拒**，判词含
   `comparison_reduction_ratio` + `GTE` + `1000000`，run `FAILED`。**这条是本 EC 的主反证。**
2. **改小出厂目录里的阈值**（100 → 1）⇒ **最初未被抓到**（判据只判了机制、漏了那个数）
   ⇒ **补齐** `TestTheFalsifiableCriterionIsPinnedInTheCatalog` ⇒ 复压**判红并点名**
   `阈值必须是写死的那个数（改小它 = 让这条判据不再可否证）`；复原 ⇒ 9 passed。
   **这条修正本身是 EC-03 的一部分**（判据咬不咬得住也要按压取证）。
3. **实验脚本的实测值**（`test_the_experiment_output_actually_clears_the_threshold`）：
   直接跑脚本取 `metrics` 读数 ⇒ 断言越过阈值（**非空真**：阈值可达，不是恒假装饰）。

## 本地验证

- `tests/e2e/test_scientific_action_depth.py` ⇒ **9 passed**；
- `tests/architecture/python + tests/application + tests/contracts + tests/loaders +
  tests/tooling + tests/adapters + tests/e2e + tests/api` ⇒ **4142 passed / 90 skipped**（无回归）；
- `ruff check` / `ruff format --check` / `mypy`（1098 files）/ 规模门绿。

## 剩余差距

- EC-04（判据射程自查表）/ EC-05（自举收口）未做；
- **`metrics` 判据落在执行它的那个 phase**（既有语义）：下游 `verdict` 消费的是
  **run 级证据投影**，**不**读 `metrics` 字段 —— 本 PLAN **不**声称「指标跨 phase 传播」；
- 五条未放行读能力 + `citation.validate` 仍属受限面。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7）。

## 实施清单

- [x] **WP-A（协议）**：`scientific_action_depth_v1.yaml`（3 phase；读能力与 EC-01 同一组）。
- [x] **WP-B（契约）**：三份契约；实验契约带**可否证**的 `METRIC_THRESHOLD`。
- [x] **WP-C（判据）**：`tests/e2e/test_scientific_action_depth.py`（9 passed）。
- [x] **WP-D（按压三处）**：抬高阈值（主反证）/ 改小目录阈值（**抓到判据缺口并补齐**）/
      实验实测值越阈值（非空真）。
- [x] **WP-E（记录）**：本 PLAN + `RECHECK-20261005-288` + `ALL_PLAN` 投影 + GOAL 回写。

## 证据

- **判据**：`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_scientific_action_depth.py -q`
  ⇒ **9 passed**。
- **主反证判词**：`metric comparison_reduction_ratio ... GTE 1000000`（抬高阈值臂）。
- **判据缺口修正判词**：`('阈值必须是写死的那个数（改小它 = 让这条判据不再可否证）', Decimal('1'))`。
- **容器证据**：`entry["image_digest"]` 非空 + `metrics` 在 `artifact_ids` 里（来自容器，不是桩）。
- **下游消费证据**：实验证据 id 出现在 `verdict` 那次 `evidence.read` 的返回内容里。
- **受判面**：`tests/architecture/python + tests/application + tests/contracts + tests/loaders +
  tests/tooling + tests/adapters + tests/e2e + tests/api` ⇒ **4142 passed / 90 skipped**。
- **质量门**：`ruff check` / `ruff format --check` / `mypy`（1098 files）/ 规模门绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 3 derive）并执行 WP-A…WP-C。 |
| 2026-10-05 | DONE | WP-D 抓到并闭合一处**判据射程缺口**；判据 9 passed；`RECHECK-20261005-288` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：新增协议 1 + 追加契约 3 + 新增判据 1。**产品代码零改动**（读能力与实验缝都是既有）。
- **Domain/API/schema 变化**：无 DTO / OpenAPI 变化；无新能力、无新放行。
- **安全/凭据变化**：无。实验**不出网**（纯标准库、语料脚本内生成）；`policy.yaml` 未动。
- **兼容性/迁移风险**：无（纯追加）。
- **上游版本影响**：无。

## 无可复用事实

本 PLAN 的产出是**协议 + 契约 + 判据**。其中「反证臂改运行时快照 ⇒ 抓不到出厂目录里的数值」
这一条是**判据设计**的一般教训（受判面写窄的又一形态），但 `MEM-20260922-160` 与 GOAL-029
已给出更一般的表述；本轮的**具体**证据写进 `RECHECK-20261005-288` 的 `W-1`，**不另立 `MEM`**。
