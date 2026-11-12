---
id: PLAN-20261112-112
slug: authored-enablement
title: GOAL-112 子计划 —— 实验生成级的启用面（只交付可启用的网）
status: DONE
created_at: 2026-11-12
updated_at: 2026-11-12
parent_goal: GOAL-20261111-112
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-112-authored-enablement.md
memory_entries:
  - .cursor/memory/entries/MEM-20261112-242-m0-witness-covers-tracked-files-only.md
---

# PLAN-20261112-112

## 背景与靶子

序 80（最后一轮）。GOAL-107 已让三条策略约束在**实验执行边界**生效，但
`tool_plane/resolver` 丢掉它们、`preflight/policy_check` 只复述键名 ⇒ `W-4`。
本轮把**同一张约束表**推到三处，并交付具名安全 profile 作为 `authored` 的唯一放行口。

## 交付面（checkbox）

- [x] `constraint_table.py`（三键判定唯一一份；三处都调它）
- [x] `tool_plane/resolver` 携带约束（不再等价放行）
- [x] `preflight/policy_check` 核验形状（未知键 / 类型错点名）
- [x] `script_source: authored` + `AUTHORED_SAFETY_PROFILE`
- [x] 对抗性反证 4 条 × 3 面
- [x] 收口资产 + 宪章 + 五轮程序完成报告

## 复检

`.cursor/plans/rechecks/RECHECK-20261112-112-authored-enablement.md`

## 验收条件

- 六条 EC 全部 PASS；
- 每条新增判据有反证臂且按压后确认判红；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
- `AUTHORED_ALLOWED_BY_DEFAULT is False` 逐字不动。

## 实施清单

- [x] EC-01 同一张表
- [x] EC-02 工具面
- [x] EC-03 preflight
- [x] EC-04 authored profile
- [x] EC-05 对抗性反证
- [x] EC-06 收口

## 证据

判据读数（2026-11-12 实跑）：`test_constraint_table.py` **23 passed**（表自洽 8 + 实验边界 5
+ 工具面 3 + preflight 2 + 三面同源 4，含 4 条对抗 × 三面）；`test_authored_profile.py`
**23 passed**（默认仍 False + 两道门 + 6 种非逐字 profile 值 + `script_source` 闭集）；
`test_resolver_carries_constraints.py` **4 passed**；`test_policy_check_reads_constraints.py`
**7 passed**。受影响面回归 **235 passed**（preflight + experiments + tool_plane + policy view）。
收口验证器 **92 PASS / 0 FAIL**（首推 66；CI 判红后的补强见 `RECHECK-20261112-112`）。
静态：`ruff check` 全产品根绿、`ruff format --check` 1498 文件绿、`mypy` **1439 文件**绿。

EC-06 的程序完成报告在 `docs/roadmap/ROUNDS_76_80_PROGRAMME_COMPLETION.md`：五轮一览
（序 / GOAL / 轴 / 靶子 / EC 数 / CI 读数）、逐轮交付与证据形态、阶梯推进表、
跨轮残余汇总（`W-1`/`W-2`/`U-1`/`U-2`/`R-1`/`R-2`）与五条方法论收获。

## 影响报告

**Domain / API / schema 变化**：新增 `PreflightFindingCode.POLICY_CONSTRAINTS_INVALID`
一个枚举成员（preflight finding 分类）。**零 HTTP 路由 / DTO / OpenAPI 变化**
（`PreflightFindingCode` 不进 OpenAPI —— 它不是请求/响应体）。`CapabilityResolution`
新增 `constraints` 字段（缺省空映射 ⇒ 既有构造点与语义逐字不变）。

**判据口径**：阶梯「实验」行的 `下一级` 追加「三条约束在全部执行面生效」这一档；
其余六行逐字未动（收口断言集钉住）。

**安全 / 凭据**：**默认姿态不变**（`AUTHORED_ALLOWED_BY_DEFAULT is False` 逐字未动；
§9 的 deny 项一个都没放开）。新增的是**更严的一道门**：`authored_allowed=True` 之外
还要具名安全 profile。`requires_workspace_lease` 进了闭集但**只过形状**（不假装执行）。

**兼容性 / 迁移风险**：**一处行为收紧** —— 形状不合法（未知键 / 类型错）的约束声明
现在会让 preflight 产出 `POLICY_CONSTRAINTS_INVALID`（ERROR 级）。出厂 `policy.yaml`
的四处声明都合法（实测 `policy_surface_consistency` 三条判据绿），因此真实控制面不受影响；
**自制策略文件里写了未知键的会从「静默放过」变成「冻结前点名拒绝」** —— 这正是本轮的意图。

## 工程记忆

`MEM-20261112-242`：全量 m0 的见证只覆盖**已跟踪**文件（`git ls-files` + `git hash-object`）
⇒ 新建的受判文件必须先 `git add` 再跑 m0，否则本地 24 条 `PASS [` 全绿、CI 单条判红
（判词会逐文件点名「内容变了/新增」）。这是本轮第三次 CI 判红的唯一根因，也是可复用的
顺序纪律（8.1 的补充：`git add` 在 m0 **之前**，不只是"提交之前"）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | IN_PROGRESS | 建档 |
