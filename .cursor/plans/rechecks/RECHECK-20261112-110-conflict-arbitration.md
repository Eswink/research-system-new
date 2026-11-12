---
id: RECHECK-20261112-110
slug: conflict-arbitration
title: GOAL-110 复检 —— 证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-12
updated_at: 2026-11-12
plan_id: PLAN-20261112-110
parent_goal: GOAL-20261111-110
owners:
  - root-agent
verify_paths:
  - packages/application/memory/arbitration.py
  - packages/application/memory/lifecycle.py
  - services/api/routers/memory_conflicts.py
  - tests/application/memory/test_arbitration.py
  - tests/api/test_memory_conflict_resolve_route.py
  - examples/config/memory_arbitration.yaml
---

# RECHECK-20261112-110

## 复检范围

GOAL-20261111-110 的五条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 决策面 | 三值闭集 + 可判依据 + 缺省 `REQUIRE_HUMAN` | **不**宣称「矛盾已被自动消解」——缺省拒绝自动化 |
| 检测面 | 逐字不动（`content_conflict` / `conflict_sweep` 已齐备） | 不新造第二套检测 |
| 语义 | `TrustLabel` 序只用于**读序**（VERIFIED > GENERATED > RETRIEVED…） | **不改** `TrustLabel` 枚举本身（`escalation_triggers`） |
| 路由 | 写面认证 + 幂等键的既有姿态 | **不**给读面加认证（既有口径不变） |

## 检查结果

### EC-01 仲裁策略闭集（PASS）

- `memory/arbitration.py`：三值闭集 `NEWER_WINS` / `SOURCE_TRUST_WINS` / `REQUIRE_HUMAN`；
  **缺省 `REQUIRE_HUMAN`**（`policy=None` ⇒ 判词点名「no arbitration policy declared」）；
  `REQUIRE_HUMAN` **不是可声明的策略**（`DeclaredPolicy` 构造即拒）；
- 三策略各一条正例，依据句**机器可读**（点名两边的时间戳 / 两个 `TrustLabel` 值）；
- **`TrustLabel` 枚举逐字未动**：成员集（6 个）与 `TRUST_RANKING` 键集**同源**，
  新增枚举成员而不给读序 ⇒ 判据红（`escalation_triggers` 的那条线由判据守）；
- 阈值：`DeclaredPolicy.min_confidence` **必填**（结构性，不是文档约定）。
- 判据 `tests/application/memory/test_arbitration.py` ⇒ **14 passed**。

### EC-02 HTTP 路由（PASS）

- `POST /memory/{memory_id}/conflicts/{other_id}/resolve`，请求体 `MemoryConflictResolveDto`
  （`strategy` / `min_confidence` / `trust_labels` / `resolved_by`，全部可选）；
- **幂等由既有中间件强制**（本路由不另开口子）：无 `Idempotency-Key` ⇒ 422 点名；
  同 key 同载荷 ⇒ 同响应重放；同 key 不同载荷 ⇒ 422 `Idempotency-Key Reused`；
- **单列模块**：`routers/memory.py` 加完这条路由会到 552 行（450 行硬上限）⇒ 消解路由
  落在 `services/api/routers/memory_conflicts.py`，由 `app.py` 注册。既有四个路由的语义
  **逐字未动**（`memory.py` 只删掉搬走的代码与随之失效的 import）；
- 落账走**既有** `lifecycle.resolve_memory_conflict`（不新造第二套写面）；
  方向判定（谁声明了冲突就记在谁身上）**先于**仲裁——「不是一对」与「裁不出来」是两件事；
- OpenAPI 快照已重生成（新增 182 行，含新路由的 `requestBody`）。
- 判据 `tests/api/test_memory_conflict_resolve_route.py` ⇒ **10 passed**。

### EC-03 判据（PASS —— 三正例 + 两反证）

| 要求 | 判据 | 读数 |
| --- | --- | --- |
| 三策略正例 | `test_newer_wins_names_both_stamps` / `test_source_trust_wins_names_both_labels` / `test_the_default_is_require_human_by_name` | 各自绿 |
| **反证一**：低于阈值必须拒自动 | `test_confidence_below_the_declared_threshold_refuses_automation` | 绿（点名 `0.4 … < 0.6`） |
| **反证二**：同一对不能重复消解 | 域层 `test_the_domain_still_refuses_a_second_resolution` + 路由层 `test_a_second_resolution_is_refused_by_name` | 两层都绿 |

### EC-04 阶梯改写（PASS —— 只动一格）

「证据」行 `下一级` **替换**为「处置闭环成立（策略闭集 + 可判依据）」（旧句「仍无判据」
已消失）；**其余六行逐字未动**（检索 / 计划 / 复检 / 实验 / 报告 / 迭代），
由 `test_goal110_ladder_evidence_scope.py`（**4 passed**）与收口断言集**双向**钉住。

### EC-05 收口资产与宪章记账（PASS）

- `tools/verify_goal110_closeout.py` + `tools/goal110_closeout_assertions.py`
  ⇒ **73 PASS / 0 FAIL**；断言集**重放**缺省 `REQUIRE_HUMAN`（不只查文件存在）；
- 登记 `_VERIFIERS` 与 `IN_SCOPE` 两处；宪章程序表 / 阶梯 / 进展 / 修订按实际改；
- GOAL-109 台账的 run id 回填**留待下一轮首个 `.cursor` 提交**（本轮台账行已如实写
  「与收口提交同一次 push，无独立 run」——**不冒领**）。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证臂 | 结果 |
| --- | --- | --- |
| `test_arbitration` | 声明 `REQUIRE_HUMAN` 当策略 ⇒ 拒；`valid_from` 缺席/平手、标签缺席/越序/平手 ⇒ 全 `REQUIRE_HUMAN` 点名；低置信度 ⇒ 拒 | 红 |
| `test_memory_conflict_resolve_route` | 无幂等键 ⇒ 422；同 key 换载荷 ⇒ 422；重复消解 ⇒ 422；未知 id ⇒ 404；无阈值 ⇒ 422；非声明的对 ⇒ 422 | 红 |
| `test_goal110_ladder_evidence_scope` | 六行任一出现「处置闭环成立」⇒ 红；证据行残留旧句 ⇒ 红 | 红 |

## 结论

**PASS_WITH_WARNINGS**。五条 EC 全 PASS；两条残余（`W-1` 只覆盖二元对 / `W-2`
`trust_labels` 由调用方给）、两条未覆盖（`U-1` 检测面与仲裁面未端到端联调 /
`U-2` 前端未接）、两条声称边界（`R-1` 缺省不自动消解 / `R-2` 判依据不判事实正确）
逐条明写。

**本轮一处方法论收获**：**「拒绝自动化」必须是缺省值而不是可选项**——
把 `REQUIRE_HUMAN` 做成闭集里**不可声明**的那一值（而不是「可以声明的第三个策略」），
让「没有策略」与「策略是人」在**同一个词**上收敛，于是「忘了声明」不会静默走向自动。
