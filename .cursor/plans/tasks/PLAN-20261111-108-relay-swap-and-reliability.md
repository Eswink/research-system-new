---
id: PLAN-20261111-108
slug: relay-swap-and-reliability
title: GOAL-108 子计划 —— 换接入商 + 四个免费模型真分工 + 静默停住四处收口
status: IN_PROGRESS
created_at: 2026-11-11
updated_at: 2026-11-11
parent_goal: GOAL-20261111-108
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261111-108-relay-swap-and-reliability.md
memory_entries: []
---

# PLAN-20261111-108

## 背景与靶子

用户 2026-11-11：换接入商（`http://192.168.101.9:8798/v1`）、只用免费模型、把可靠性解决掉。

## 交付面（checkbox）

- [x] 事实探针（23 模型 / 5 个 x0.00 / 4 个支持 tool_calls，逐个实测）
- [x] 换站：base_url / timeout 120→300 / allow_models 四项
- [x] 四个免费模型真分工（写作组 / 评审 A / 评审 B / 创新点作者）
- [x] R-1 装配面异常边界（`spec_assembly_guard.py`）
- [x] R-2 `review_outcome` 的 resume 阻塞（`NO_PROGRAM`）
- [x] R-3 五份会话合约重试声明
- [x] R-4 live harness 读产品同一开关
- [ ] 真跑一次十一相链（需要凭据与开关，另窗口）
- [ ] 文档同步
- [ ] 收口资产与宪章收口

## 复检

`.cursor/plans/rechecks/RECHECK-20261111-108-relay-swap-and-reliability.md`

## 影响报告

判据口径变化：把写死「具体模型名 / 具体秒数」的判据改为**结构性**断言（详见 GOAL 的
`## 影响报告`）。

## 验收条件

- 十一条 EC 全部 PASS；
- 每条新增判据有反证臂且按压后确认判红；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`。

## 实施清单

- [x] 探针（EC-01）
- [x] 换站（EC-02）
- [x] 模型分工（EC-03）
- [x] R-1…R-4（EC-04…07）
- [ ] 真跑（EC-08）
- [ ] 文档（EC-09）
- [ ] 宪章（EC-10）
- [ ] 收口资产（EC-11）

## 证据

探针读数见 GOAL 的 `## 探针读数`；可靠性四件的判据见：
`tests/application/test_spec_assembly_guard.py`（9 passed）、
`tests/application/test_review_outcome_no_program.py`（6 passed）、
`tests/application/test_session_contract_retries.py`（12 passed）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-11 | IN_PROGRESS | 建档；探针 / 换站 / 分工 / R-1…R-4 已完成 |
