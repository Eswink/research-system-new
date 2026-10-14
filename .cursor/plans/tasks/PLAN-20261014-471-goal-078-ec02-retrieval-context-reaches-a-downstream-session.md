---
id: PLAN-20261014-471
slug: goal-078-ec02-retrieval-context-reaches-a-downstream-session
title: GOAL-078 cycle 2 — 检索内容经产品路径到达下游会话（EC-02）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261014-078
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-472-goal-078-ec02-retrieval-context-reaches-a-downstream-session.md
memory_entries: []
---

# PLAN-20261014-471 — GOAL-078 cycle 2

## 验收条件

- [x] 新产品路径 e2e 判据在树（`tests/e2e/test_retrieval_context_reaches_the_session.py`）
- [x] 正向臂：下游 phase 的会话 spec `context_snapshot.selected_refs` **非空**
- [x] 正向臂：逐条 ref 可在 `GET /runs/{id}/evidence` 找到且性质为 `RETRIEVED`
- [x] 反证臂：无检索证据时集合为空**且点名**（同一次 run 的另一个会话）
- [x] 既有判据零放宽（定向套件 + 架构判据 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-02**：证「检索内容**经产品路径**进入会话」——不是「装配器能被调用」，
而是「一次真实装配下的 run 里，**下游** phase 的会话 spec 带上了上游取回的内容」。

## 设计（为什么这样取证）

### 1. 取证面：**会话 spec**，不是内部对象

`AgentSessionSpec.context_snapshot` 就是「会话拿到的上下文」这一事实本身。
判据读它 ⇒ 判的是**产品路径的产物**，而不是装配器的返回值。

**怎么拿到 spec**：包一层**记录型 runtime**（与 `OutcomeRecorder` 同一手法 ——
装配方包装、不改产品代码、原样透传），在 `create_session` 时留一份 spec 引用。
按 `task_contract.id` 索引（**声明事实**），不按顺序猜 phase。

### 2. 用哪份协议：既有的 `research_report_chain_v1`（**不新造协议**）

它天然有「上游检索 → 下游会话」的形状：

| phase | 执行体 | 与 EC-02 的关系 |
| --- | --- | --- |
| `plan` | 运行链检索 + 会话 | **它自己的会话开始时，检索还没跑** ⇒ 反证臂 |
| `experiment` | 沙箱 | （不建会话） |
| `review` | 会话 | 下游 ⇒ **正向臂**（应看到 plan 格取回的内容） |

⇒ **一次 run 同时给出两向**：
`multi_role_review` 的 spec 应**非空**；`research_report_plan` 的 spec 应**空且点名**。
两向写在同一次实跑上，且都是产品路径的产物。

### 3. 逐条 ref 的**性质**要与证据读面对上

`selected_refs` 是 `tool-result:` 命名的制品 id。判据把它们与
`GET /runs/{id}/evidence` 里 `source_trust_label == "RETRIEVED"` 的
`artifact_id` **求对应**（逐条，不是「非空」了事）—— 这样「检索内容」不是自称，
而是与读面同源的**性质事实**。

### 4. 边界（如实登记）

- 判据测的是**链路与装配**（run-ready 夹具 + 装配方接的执行体缝），与 GOAL-027/029/077
  的离线判据同一条路径；它**不**声称模型读了上下文（那要观测面）；
- 实验格是真容器 ⇒ 本文件挂 `requires_docker`（与 `test_research_report_arc_offline.py` 同）。

## 实施清单

1. **WP-A：记录型 runtime**（判据文件内）：`create_session` 留 spec，其余经
   `__getattr__` 原样委派（不改产品代码）。
2. **WP-B：判据**（`tests/e2e/test_retrieval_context_reaches_the_session.py`）：
   正向臂 + 反证臂 + ref↔证据读面的逐条对应 + 「非本 run 的证据不进上下文」。
3. **WP-C：记录 + 门**：本文件 + RECHECK + GOAL 回写 / ALL_PLAN 同提交；
   定向套件 → 记录面判据 → 全量 m0。

## 影响报告（预估，收口时按实测改写）

- **产品代码零改动**（本 cycle 只加判据：装配器与接线在 cycle 1 已落地）。
- **判据面**：新增 1 个 e2e 模块；既有判据**零放宽**。

## 残余与未覆盖（如实登记）

- EC-03（读面可复核「进了什么」）/ EC-04（真实中转站）/ EC-05（收口）**不在本 cycle**；
- 模型是否真的读了上下文 —— 属观测面，不在本 GOAL 的射程内。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 新 e2e 判据 | **5 passed** | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_retrieval_context_reaches_the_session.py -q` |
| 接缝判据（+3 新例） | **16 passed** | `… -m pytest tests/application/test_retrieval_context_seam.py -q` |
| 三向按压 | `V8-1…V8-3` 各 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True`，`all_red_and_restored=True` | `… -B scratch/goal078c2_press.py` |
| 受影响套件 | **997 passed, 1 skipped** | `… -m pytest tests/application + 两个 e2e 模块 -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 2 建档（EC-02 的取证面与两向臂设计）。 |
| 2026-10-15 | DONE | WP-A…WP-C 落地：记录型 runtime + 5 例 e2e（正/反/射程/自检）；按压实测**抓出两条未被覆盖的性质**并补判据；三向按压全红。 |
