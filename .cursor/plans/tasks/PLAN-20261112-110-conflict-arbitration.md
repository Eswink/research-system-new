---
id: PLAN-20261112-110
slug: conflict-arbitration
title: GOAL-110 子计划 —— 证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）
status: DONE
created_at: 2026-11-12
updated_at: 2026-11-12
parent_goal: GOAL-20261111-110
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-110-conflict-arbitration.md
memory_entries: []
---

# PLAN-20261112-110

## 背景与靶子

序 78：证据格的 `下一级` 是「矛盾处置闭环」。检测面已齐备（不重做）；缺「谁、依据什么
消解」的**决策面**（`arbitration.py` 三值闭集，缺省 `REQUIRE_HUMAN`）与**入口**
（带幂等键的 HTTP 路由）。

## 交付面（checkbox）

- [x] `arbitration.py`（三值闭集 + 可判依据 + 缺省 REQUIRE_HUMAN）
- [x] HTTP 路由 `POST /memory/{id}/conflicts/{other_id}/resolve`（幂等键）
- [x] 判据（域层三正例 + 默认反证；路由层幂等/404/重复消解反证）
- [x] 阶梯「证据」行改写；其余六格逐字不动
- [x] 收口资产 + 宪章记账 + GOAL-109 run id 回填

## 复检

`.cursor/plans/rechecks/RECHECK-20261112-110-conflict-arbitration.md`

## 验收条件

- 五条 EC 全部 PASS；
- 每条新增判据有反证臂且按压后确认判红；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`。

## 实施清单

- [x] EC-01 仲裁闭集
- [x] EC-02 HTTP 路由
- [x] EC-03 判据
- [x] EC-04 阶梯改写
- [x] EC-05 收口资产

## 证据

判据读数（2026-11-12 实跑）：`test_arbitration.py` **14 passed**（三策略正例 +
低置信度反证 + 四缝点名 + 域层重复消解 + 枚举同源）；`test_memory_conflict_resolve_route.py`
**10 passed**（幂等三态 / 缺省不落账 / 自动落账归因 / 无阈值拒 / 404 / 重复消解 /
人来裁决 / 非声明的对）；`test_goal110_ladder_evidence_scope.py` **4 passed**（一格推进）；
收口验证器 **76 PASS / 0 FAIL**；OpenAPI 快照重生成（+182 行）。

## 影响报告

**Domain / API / schema 变化**：新增 **1 条 HTTP 路由**（`POST
/memory/{memory_id}/conflicts/{other_id}/resolve`）与 **3 个 DTO**
（`MemoryConflictResolveDto` / `MemoryConflictVerdictDto` / `MemoryConflictResolveViewDto`），
OpenAPI 快照已重生成。**Domain 零改动**：没有新增或修改域实体、`MemoryRecord` 字段、
`TrustLabel` 枚举或 `ConflictResolution`。

**判据口径**：阶梯「证据」行的 `下一级` 由「仍无判据（需拍板）」**替换**为处置闭环 bar；
其余六行逐字未动（`test_goal110_ladder_evidence_scope.py` 钉住）。

**安全 / 凭据**：写面认证与幂等键的既有姿态**不变**（读面仍不认证、写面仍认证；
幂等由既有中间件强制，本路由不另开口子）。**默认姿态收紧而非放松**：
`REQUIRE_HUMAN` 是缺省，自动化只能显式声明且必须带阈值。

**兼容性 / 迁移风险**：零迁移（不触库结构）。**行为风险**：新增的写路由让「消解」成为
可远程触发的动作——但它仍受 §9 同姿态的缺省拒绝 + 显式声明 + 域层重复消解校验三重约束；
批量自动消解**未接**（`U-1`），前端未接（`U-2`）。

## 工程记忆

（收口时按实际情况填写，或声明无可复用事实。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | IN_PROGRESS | 建档 |
