---
id: PLAN-20260915-069
slug: provider-health-schema-digest-drift
title: 健康复核记录 schema digest 并可比对漂移（EC-02 剩余子句）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 7 = EC-02 未交付子句「健康复核记录 schema digest 并可比对漂移」。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-069-provider-health-schema-digest-drift.md
memory_entries:
  - MEM-20260915-044-schema-digest-is-a-state-not-an-event
---

# PLAN-20260915-069 — 健康复核记录 schema digest 并可比对漂移（GOAL-003 cycle 7 / EC-02 剩余子句）

## 目标

让"provider 的健康复核"不只是三态结论，还**记录被探测方声明的 schema 指纹**，并使**漂移可比对**。

```text
今天：  适配器**已经算出** observed_schema_digest（MCP/REST/NCBI 三处都填了
        ToolHealthReport.observed_schema_digest），但 probe_provider_spec 只返回
        (status, detail) 把它丢掉 → 注册记录、DTO、SQLite、读面全都没有这个事实
        ⇒ schema 变了没人知道，供应链面"pin 住了 revision"却看不见"对方换了能力面"
本轮：  probe 把 digest 一路带到注册记录 → DTO → 读面 → console 行；漂移可判定
```

## 口径（这轮最容易做错的地方）

1. **漂移是"状态"不是"事件"**：判据是"当前观测 vs **基线**"，不是"这次 vs 上次"。
   若按"上次 vs 这次"，A→B 报漂移、B→B 立刻报"不漂移"，而提供方**仍然不是当初那个**
   ——操作者会得到一个会自己消失的告警。基线 = 首次观测到 digest 的那次复核（或最近一次
   批准接受的值）。
2. **未知 ≠ 没有漂移**：这次探测没拿到 digest（NATIVE / 未声明 health_check / 探测异常）
   时，**既不设基线、也不清除已有漂移**。把"没观测"当成"没变化"是最容易犯的错。
3. **批准 = 接受当前形态**：`approve` 把基线重设为最后一次观测到的 digest 并清除漂移
   ——这是漂移唯一的"解除"路径，语义是"我看见了，我接受"。不新增第二套承认机制。
4. **单一探测路径不变**：写面（health-check）与读面（`build_provider_health`）继续共用
   `probe_provider_spec`，否则又出现"复核说 A、目录说 B"的两套真相。
5. **不改适配器**：三个适配器已经在算 digest，本轮只把被丢掉的事实接上；`ToolHealthReport`
   与各 adapter 零改动。
6. **DTO 不许 import domain**（`api-dto-purity`）：digest 以字符串进出，解析与比较都在域里。

## 范围

- 域：`packages/domain/tool_registry.py`（`ProviderRegistration` 新字段 + `record_health`
  接收 digest + `approve` 重基线化）。
- 应用/适配：`services/api/preflight_support.py`（`probe_provider_spec` 返回结构化探测结果，
  不再丢字段）、`services/api/routers/tool_registrations.py`（写面传 digest）、
  `adapters/sqlite/tool_provider_registry.py`（JSON blob 编解码，**表结构不变**）。
- 读面：`services/api/dto/tool_providers.py`（注册 DTO 增四个字段）+ OpenAPI 重生成。
- Console：`apps/web/src/api/types.ts` 镜像 + `features/integrations/registrationColumns.tsx`
  的漂移标记（有 `data-testid`）。
- 测试：`tests/api/test_tool_registrations_api.py`（写面事实 + 漂移三态 + 无 digest 不清除）、
  `tests/application/...`（若既有 provider 健康用例覆盖 probe 返回形状）、
  `apps/web/tests/e2e/registry-write.spec.ts`（stub 里漂移可见 / 无漂移不显示）。
- **不改**：三个 adapter（`adapters/mcp/provider.py`、`adapters/research_tools/ncbi.py`、
  `adapters/fakes/tool_provider.py`）、`packages/domain/tools.py`、policy 面。

## 验收条件

- [x] AC-01：首次带 digest 的复核**建立基线**且 `schema_drift=false`；随后 digest 变化 ⇒
  `schema_drift=true` + `schema_drift_since` 有值；digest 回到基线 ⇒ 漂移**自动清除**（状态语义）。
  ——`test_health_check_records_the_schema_digest_and_flags_drift`（含"第三次仍是 D2 ⇒ 漂移仍为真"
  这条判别式）+ `test_drift_clears_when_the_schema_returns_to_the_baseline`。
- [x] AC-02：**无 digest 的复核不动任何 digest 字段**（既不设基线、也不清除已有漂移）——反证用例。
  ——`test_observation_without_a_digest_neither_sets_nor_clears_drift`：D1→D2→None，
  四个 digest 字段逐字段不变，而 `last_health`/`health_checked_at` 照常更新。
- [x] AC-03：`approve` 重基线化：漂移清除、`schema_baseline_digest` = 最后一次观测值。
  ——`test_approve_accepts_the_current_schema_as_the_new_baseline`。
- [x] AC-04：写面（health-check）与读面（`GET /tool-provider-registrations`）看到的 digest 事实一致
  （同一 `probe_provider_spec` 路径），且 NATIVE 等无 digest 场景诚实为 `null` 而非空串/假值。
  ——同一条用例内比对写面响应与读面列表；`test_registration_without_a_digest_capable_kind_reports_null_honestly`。
- [x] AC-05：SQLite 往返保留四个字段，且**旧行（无这些键）仍可解码**（JSON blob 向后兼容）。
  ——`tests/adapters/sqlite/test_tool_provider_registry_store.py` **3 passed**（往返整体相等 +
  手写"加字段之前那一版键集"的行）；**表结构未变**，无需迁移。
- [x] AC-06：DTO/OpenAPI 收敛（新字段进 schema、契约测试通过）；TS 镜像同步。
  ——`python -B tools/gen_openapi.py` **+39 / −1 行**；`tests/contracts` 通过；
  `lint-imports --config .importlinter.api` **2 kept, 0 broken**。
- [x] AC-07：console 注册表行在有漂移时给出可见标记（stub e2e 断言），无漂移时不显示。
  ——`registry-write.spec.ts` **7 passed**（新增两条）；33 路由**像素与结构签名均未变**。
- [x] AC-08：全量门禁（m0 23 + 定向套件 + web 门 + stub/live e2e）+ 记录（RECHECK-069 + MEM-044 + GOAL 记账）。
  ——stub e2e **83 passed**、live e2e **35 passed**、API+store+contracts+architecture **944 passed / 2 skipped**、
  mypy 860 files clean、m0 见「证据」段；RECHECK-069 + MEM-20260915-044 + GOAL 记账。

## 实施清单

- [x] WP-A 域：字段 + `record_health(observed_schema_digest=...)` + `approve` 重基线化
- [x] WP-B 探测：`probe_provider_spec` 返回结构化结果（不丢字段）+ 写面接线
- [x] WP-C 存储：SQLite 编解码 + 旧行兼容
- [x] WP-D 读面：DTO + OpenAPI + TS 镜像 + console 漂移标记
- [x] WP-E 测试：域/API/store/stub e2e（含 AC-02 反证）
- [x] WP-F 门禁 + 记录 + 收口提交 → CI

## 证据

**WP-A/B（域与探测路径）**

```text
$ python -m pytest tests/api/test_tool_registrations_api.py -q
23 passed in 4.61s          # 18 既有 + 5 新增（漂移三态 / 回基线清除 / 无 digest 不清除 /
                            #   approve 重基线化 / 无 schema 概念的 kind 诚实为 null）
```

**WP-C（存储）**

```text
$ python -m pytest tests/adapters/sqlite/test_tool_provider_registry_store.py -q
3 passed in 0.23s           # 四字段往返（整体相等）+ 旧行键集解码 + list 的漂移投影
```

**WP-D/E（读面与 console）**

```text
$ python -B tools/gen_openapi.py     -> wrote docs/api/openapi.m13.json (+39 / -1 行)
$ lint-imports --config .importlinter.api
Contracts: 2 kept, 0 broken.
$ npx eslint <改动文件>              （空输出）
$ npx tsc --noEmit -p apps/web/tsconfig.json      （空输出）
$ npx playwright test --config playwright.config.ts registry-write.spec.ts
7 passed (28.4s)
$ npx playwright test --config playwright.config.ts    -> 83 passed (4.8m)
```

**WP-F（全量门禁）**

```text
$ python -m pytest tests/contracts tests/architecture tests/api tests/adapters/sqlite -q
944 passed, 2 skipped in 96.88s
$ python -m mypy                     -> Success: no issues found in 860 source files
$ sh scratch/run-m0-cycle12.sh       -> PASS: profile=m0; 23 deterministic checks
$ npx playwright test --config playwrightLive.config.ts  -> 35 passed（首轮 1 failed 的处置见 RECHECK-069 W-1）
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 6（EC-05 替身幂等契约）闭环后取 EC-02 剩余子句。
  recon 定位缺口：适配器**已算出** `observed_schema_digest`（`adapters/mcp/provider.py:145`、
  `adapters/research_tools/ncbi.py:150`、`adapters/fakes/tool_provider.py:101`），
  但 `probe_provider_spec`（`services/api/preflight_support.py:88-94`）只取 status/detail、
  `record_health`（`packages/domain/tool_registry.py:156-165`）不接收、DTO 与 SQLite 都不落。
  关键判断：**漂移必须是状态而非事件**（否则 A→B→B 会让告警自己消失），
  且**未知观测不得清除漂移**。
- 2026-09-16 WP-A/B 完成：域加四字段 + `record_health` 接收 digest（None 时四字段一律不动）；
  `probe_provider_spec` 改为返回 `ProviderProbe(status, detail, observed_schema_digest)`，
  两个调用点（读面投影、注册面 health-check）同步。**适配器零改动**——它们本来就在算。
- 2026-09-16 WP-C 完成：SQLite 是 JSON-blob-per-row，因此**表结构不变**（无迁移）；
  `_decode` 对缺键的行按 `None/False` 解码，并用一条手写"历史键集"的用例钉住。
- 2026-09-16 WP-D 完成：DTO + OpenAPI（+39/−1）+ TS 镜像 + `RegistryHealthCell`
  （漂移标记带两个截断指纹，`data-testid=registry-schema-drift-<id>`）。
  **门禁拦截一次**：加标记后 `registrationColumns` 53 行 > 50 上限，被根 eslint 判红 ⇒
  把单元格抽成独立组件（**未放宽规则**）。
- 2026-09-16 WP-E/F 完成（含两次门禁拦截）：stub e2e **83 passed**（33 路由像素与结构签名
  **均未变**——漂移标记只在真漂移时渲染，这是结构判据"只在真实变化时判红"的正向证据）；
  live e2e 首轮 1 failed（`live-schedules-write` 的 500）→ 隔离复跑 2 passed、
  第二轮全量 35 passed；**顺着这条线复现出真实缺陷**：控制面 SQLite 共享连接在并发写下
  抛 `sqlite3.InterfaceError`（12 线程 24 请求 ⇒ 2×500 + 2×404），已记为 RECHECK-069 W-1
  与下一轮第一项（本 PLAN 未修，改动面不含调度面）。
  **门禁拦截两次**：① `registrationColumns` 加标记后 53 行 > 50 上限（根 eslint）⇒
  抽成 `RegistryHealthCell.tsx`；② `tests/api/test_tool_registrations_api.py` 达 **523 行**
  超 450 硬上限（`tests/tooling/test_python_source_limits.py`）⇒ 拆出
  `tests/api/test_tool_registration_health_drift.py`。两处都改代码/文件划分，**未放宽规则**。

## 影响报告

- **Domain/API/schema**：`ProviderRegistration` 增 4 个字段（全部有默认值 ⇒ 旧构造点不受影响）；
  `record_health` 增关键字参数（默认 None ⇒ 旧调用语义不变）；注册 DTO 增 4 个字段 ⇒
  OpenAPI 变化（新增字段，不破坏既有消费者）。
- **安全/凭据**：无凭据面变化；digest 是公开的 schema 指纹，不含内容。
- **兼容性/迁移风险**：SQLite 仍是 JSON-blob-per-row ⇒ **无表结构变更、无迁移**；
  旧行缺键时按 `None/False` 解码（诚实：老记录就是"没观测过"）。
- **可观测性**：无新增遥测。
- **下一项任务**：EC-02 剩余（provider 凭据绑定）、RECHECK-065 W-1（`tool_pack.*` 策略产品决策）、
  EC-06 收口复检。

## 已知风险

- **基线来自首次观测**：注册时若提供方已经漂移过，第一次复核会把漂移后的 schema 当作基线，
  本轮**检测不到这次历史漂移**（注册面没有"注册时 schema"可比——pin 是内容寻址的 revision，
  与运行期 schema 不是同一轴）。如实登记，不宣称"能发现任意漂移"。
- **只有会报 digest 的 kind 才有这条事实**：NATIVE 结构性健康但没有 schema 概念；
  未声明 `health_check` 的 provider 从不被探测 ⇒ 这些行永远是 `null`（不是"没漂移"）。
