# Research Console Information Architecture

> v2（2026-09-08，PLAN-20260908-034）：八域 33 规范路由外壳。逐页 API/DTO 映射与
> 缺口见 [CONSOLE_PAGE_MAP.md](../frontend/CONSOLE_PAGE_MAP.md)。

## 八域导航（侧栏）

```text
Plan        Overview · Protocol & Preflight · Team
Portfolio   Projects · Experiments · Run History · Compare
Run         Timeline · Approvals · Workspace
Library     Prompts · Datasets · Notebooks · Model Registry · Lineage · Endpoints · Setup
Evidence    Claims
Insights    Reports · Cost Analytics
Ops         Alerts · Incidents · Schedules · Integrations · Data Health · State Matrix · Compute · Observability
Govern      Budget · Audit & Export
```

全局页（顶栏进入，不在域侧栏）：Settings · Notification Center · Command Center（独立大屏）。

## 支持等级（pageSupport.ts / CONSOLE_PAGE_MAP.md）

FULL＝数据与操作真实；PARTIAL＝真实数据 + 部分操作禁用；GAP＝无后端能力，
还原结构并逐操作禁用说明。缺口 G1–G14 登记于 CONSOLE_PAGE_MAP.md。

## Run Timeline

每条记录可展开：Agent / Model / Tool / arguments redacted view / result·artifacts /
cost·latency / policy decision / retry·failure。事件来自服务端具名 SSE 帧 + JSON replay。

## Critical UX

- Model capability warning；
- budget burn-down（未知金额/币种冲突保留真实语义）；
- pending approvals（生产空态如实呈现）；
- workspace diff（无接口禁用）；
- unsupported claims；
- reproducibility status（配置可复现 ≠ 完全模型可复现）。
