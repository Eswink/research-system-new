---
id: RECHECK-20261013-452
slug: goal-071-ec01-04-typos-in-write-body-field-names-are-no-longer-silently-dropped
title: 独立复检：GOAL-20261013-071 cycle 1（EC-01…EC-04）—— 写面请求体打错字段名不再被静默吞掉
plan_id: PLAN-20261013-451
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/dto/common.py（StrictRequestDto）+ 37 条请求 DTO 接入
  - path: 独立重跑判据（写面 6 例 + 序 37 读面回归 11 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-071-press-two-way.txt
---

# RECHECK-20261013-452 — GOAL-20261013-071 cycle 1 独立复检

复检对象：`PLAN-20261013-451`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-write-face-extra-fields.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 实跑打错字段名 | `{"protocol_path": …, "trace_di": "typo"}` ⇒ **200**（静默吞掉；改动前） |
| 2 | 正确形态基线 | 200 + **15 键**（含 `id` / `state` / `manifest_digest`） |
| 3 | 写面 DTO 清单 | **37 条**（请求体形态），**全部**在 `services/api/dto/`；**零条**已有 `extra=` 设定 |
| 4 | 机制对照实验 | `extra="forbid"` ⇒ 422，正文 `{"detail":[{"type":"extra_forbidden","loc":["body","<字段>"],…}]}` ⇒ **字段名在 `loc` 里**；与既有 422 形态同形 |
| 5 | **契约-运行时分歧（关键发现）** | `tools/gen_openapi.py::_finalize` **早已**为每个 object schema 强制补写 `additionalProperties: false`（快照 201 处）⇒ 契约**早就**声明闭包，而运行时此前**静默接受** ⇒ 本行把运行时补到与契约一致（`git diff --numstat` 快照**零 diff**） |

### 2. EC-02 写面纪律（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **647 passed**；
新模块 `tests/api/test_write_body_typos_are_named.py` ⇒ **6 passed**。逐条复核：

- **未知字段 ⇒ 422 + 点名**（`loc` 里出现 `trace_di`）；
- **多个未知逐个点名**（`alpha` / `beta` 都在）；
- **已知/缺省逐字不变**（正确请求 200 + 15 键）；
- **多模块覆盖**（`POST /projects` 的 `nam` 被点名）+ **同 DTO 正确形态仍 201**（`X-2` 臂）；
- **机制判据**：`StrictRequestDto.model_config['extra'] == 'forbid'` 且样本 DTO 继承它；
- **射程反证臂**：响应模型（`RunDetailDto` / `ProblemDto`）**不**继承严格基类。

**影响面（实测判定）**：3 处既有调用带多余字段（`POST /projects` 传 `id` —— 该字段本为
**服务端生成**）⇒ 逐条修正调用点（**断言未动**）；其余全绿 ⇒ 影响面为零的行为证据。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/contracts tests/tooling -q` ⇒ **1998 passed / 72 skipped**；
`tests/e2e` ⇒ **307 passed / 13 skipped**。

- **查询参数面（序 37/38 判据）不回归**（11 例全绿）；
- **快照零 diff**（`git diff --numstat docs/api/openapi.m13.json` ⇒ 空）—— 与序 38 的
  `+31/−1` 形态相反；**理由如实登记**：生成器早已补写 `additionalProperties`，
  变的是**运行时行为**而非契约资产；
- **e2e 一次组合跑 flake**（`test_real_experiment_research_offline.py`）：**隔离跑绿 +
  全套重跑绿**（307 passed）⇒ 归类 flake（本仓既有形态），如实登记。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal071_press.py`：

- **BASELINE（未按压）GREEN**（17 passed）；
- `X-1`（未知字段又被静默忽略）/ `X-2`（已知字段被误拒）/ `X-3`（多个未知只报第一个）/
  `X-4`（正文不点名）⇒ **全 RED**；
- `X-2` **首跑 GREEN**（判据面缺口：只判「未知被拒」⇒ 拒绝面过宽会假绿）⇒ 补
  「同一 DTO 的正确形态仍成功（201）」断言后 RED —— **同签名 1 次修复，未超 `fix_policy`**
  （`same_signature_retries: 2`）；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；零进程泄漏（实测）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-071-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原；射程如实
（响应模型不受纪律；查询参数面不回归）；契约-运行时分歧被实测发现并**由运行时侧收口**
（不是改契约）。**残余**：无查询参数路由的参数检查（另成一面）、未声明写面（非 DTO 的
请求体）—— 逐条保留在 GOAL 的「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
