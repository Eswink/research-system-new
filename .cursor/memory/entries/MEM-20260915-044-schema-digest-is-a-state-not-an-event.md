---
id: MEM-20260915-044
title: 漂移是"当前 vs 基线"的状态，不是"这次 vs 上次"的事件；未观测不得清除漂移
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-069-provider-health-schema-digest-drift.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-069-provider-health-schema-digest-drift.md
supersedes: []
tags:
  - supply-chain
  - drift-detection
  - schema-digest
  - three-state
  - health-check
---

# 外部提供方的 schema 漂移：判据必须是"当前 vs 基线"，且"没观测到"不等于"没变化"

## 做了什么

Tool provider 的健康复核原来只记三态（HEALTHY/DEGRADED/UNKNOWN）。适配器**早就**算出了
`observed_schema_digest`（MCP/REST/NCBI 三处都填 `ToolHealthReport.observed_schema_digest`），
但 `probe_provider_spec` 只返回 `(status, detail)` 把它丢掉。本轮把它一路接到
`ProviderRegistration`（`schema_baseline_digest` / `last_schema_digest` /
`schema_drift` / `schema_drift_since`）→ DTO → `GET /tool-provider-registrations` →
console 行的漂移标记（带两个可对照的指纹）。

三条口径（都是用例钉住的）：

| 情形 | 结果 |
| --- | --- |
| 首次观测到 digest | 它成为**基线**（此前的漂移检测不到） |
| 之后每次观测 | 拿**当前值 vs 基线**判 `schema_drift`（**不是** vs 上次） |
| 观测到的 digest 为 `None` | **四个字段一律不动**（既不设基线、也不清除漂移） |
| `approve` | 基线换成最后一次观测值、清除漂移（"我看见了并接受"） |

## 为什么这样做

1. **"上次 vs 这次"会让告警自己消失**：A→B 报漂移，下一次 B→B 立刻改口"没漂移"，
   而提供方**仍然不是当初那个**。操作者会看到一个会自愈的告警——它比没有告警更糟。
   改为"当前 vs 基线"后，漂移是一个**状态**：只有在回到基线时才清除。
2. **未知 ≠ 无漂移**：探测失败、无 schema 概念的 kind（NATIVE）、未声明 health_check
   都会得到 `None`。把"没观测到"读成"没变化"会**抹掉已经发现的漂移**——
   这是这类判据里最危险的一步，必须有一条专门的反证用例。
3. **只有"接受"能重置基线**：否则漂移要么永远粘住（无法解除），要么被下一次观测悄悄重置。
   批准的语义天然就是"我看见了并接受当前形态"，复用它比新增一个"承认"接口更干净。
4. **单一探测路径**：写面（health-check）与读面（`build_provider_health`）共用
   `probe_provider_spec`，否则又会出现"复核说 A、目录说 B"的两套真相
   （本仓已有一族这样的教训）。

## 怎么做与复现

```bash
# 域/API 语义（含两条反证：无 digest 不清除、回到基线才清除）
python -m pytest tests/api/test_tool_registrations_api.py -q          # 23 passed
# 存储往返 + 旧行（加字段之前那一版的键集）仍可解码
python -m pytest tests/adapters/sqlite/test_tool_provider_registry_store.py -q   # 3 passed
# console：有漂移 ⇒ 标记可见；无漂移 ⇒ toHaveCount(0)
pnpm --dir apps/web exec playwright test --config playwright.config.ts registry-write.spec.ts
```

给测试用的编排替身：`_ScriptedProvider(script=[D1, D2, None])`——按剧本返回 digest，
这样"这次观测到 A / 这次观测到 B / 这次**没观测到**"可以精确编排
（`FakeToolProvider` 的 digest 由它自己的目录推导，改不动单次观测）。

## 适用边界（踩过的坑）

- **基线只能从首次观测起算**：注册面没有"注册时 schema"可比（`pinned_revision` 是内容寻址
  的 revision，与运行期 schema 不是同一轴）⇒ 首次复核之前发生的漂移检测不到。
- **"可见"不等于"可阻断"**：本轮只让漂移在治理读面可见；目录读面不带 digest、
  preflight 也不消费它 ⇒ schema 变了**不会**自动触发警示或阻断。
- **只有会报 digest 的 kind 才有这条事实**：NATIVE 结构性健康但没有 schema 概念，
  未声明 `health_check` 的 provider 从不被探测 ⇒ 这些行永远是 `null`（不是"没漂移"）。
- **DTO 不许 import domain**：digest 以字符串进出（`api-dto-purity` 会在全量 m0 里判红）。

## 来源

- PLAN-20260915-069 / RECHECK-20260915-069（GOAL-20260915-003 cycle 7 / EC-02 剩余子句）。
- 相关：[[MEM-20260915-035]]（写面必须被读面消费——同族"写下的东西必须有人看得见"）、
  [[MEM-20260915-036]]（注册状态推导信任——同族"信任/形态由事实推导，不由调用方声明"）、
  [[MEM-20260915-042]]（停机上界必须来自停机窗口——同族"不要让某个机制悄悄改变另一个机制的语义"）。
