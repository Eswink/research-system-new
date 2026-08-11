---
id: PLAN-YYYYMMDD-NNN
slug: short-slug
title: 任务标题
status: DRAFT
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request | cursor-plan
  ref: ""
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-YYYYMMDD-NNN — 任务标题

## 目标
说明完成后可观察到的结果。

## 范围
- 包含：
- 不包含：

## 架构与数据流
说明所有者模块、输入、输出、Canonical State、Port/Adapter 和策略门禁。

## 验收条件
- [ ] AC-01：可验证条件
- [ ] AC-02：可验证条件

## 实施清单
- [ ] STEP-01：实施项
- [ ] STEP-02：实施项

## 子代理使用
Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据
| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | file/test/digest/check | 待填写 | 待填写 |

## 决策与偏差
| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| YYYY-MM-DD | 初始化 | 用户批准的 Cursor Plan | 无 |

## 状态历史
| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | — | DRAFT | 建立任务计划 | Cursor Plan |

## 影响报告
- Domain/API/schema：
- 安全/凭据：
- 兼容性/迁移：
- 上游版本：
- 下一项任务：
