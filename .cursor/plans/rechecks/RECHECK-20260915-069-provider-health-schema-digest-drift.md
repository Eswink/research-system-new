---
id: RECHECK-20260915-069
plan_id: PLAN-20260915-069
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle7
baseline_ref: dff9ddd
checked_head: dff9ddd+worktree
---

# RECHECK-20260915-069 — 健康复核记录 schema digest 并可比对漂移（GOAL-003 cycle 7 / EC-02 剩余子句）

## 检查范围

PLAN-20260915-069 声称的交付面：`packages/domain/tool_registry.py`（`ProviderRegistration`
的四个 digest 字段 + `record_health(observed_schema_digest=...)` + `approve` 重基线化）、
`services/api/preflight_support.py`（`ProviderProbe` 结构化探测结果，不再丢字段）、
`services/api/routers/tool_registrations.py`（写面传 digest）、
`adapters/sqlite/tool_provider_registry.py`（JSON blob 编解码 + 旧行兼容）、
`services/api/dto/tool_providers.py` + `docs/api/openapi.m13.json`（读面）、
`apps/web/src/api/types.ts` + `features/integrations/RegistryHealthCell.tsx`（console 漂移标记）、
以及三个测试面（API / store / stub e2e）。

**未覆盖**（如实登记，见告警）：provider **凭据绑定**（相邻长程项，不在本 PLAN）、
`GET /tool-providers` 目录读面**不**带 digest（漂移只在治理读面可见）、
以及漂移**不参与** preflight 决议（本轮不新增警示码）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 首次观测建基线、之后按基线判漂移（AC-01） | `test_health_check_records_the_schema_digest_and_flags_drift`：D1 建基线（drift=false）→ D2 ⇒ drift=true + `schema_drift_since` 有值 + **基线不动（仍是 D1）**；第三次仍是 D2 ⇒ **漂移仍为真**（这一条正是"状态 vs 事件"的判别式） | PASS |
| 回到基线 ⇒ 清除（AC-01） | `test_drift_clears_when_the_schema_returns_to_the_baseline`：D1→D2→D1 ⇒ drift 回到 false、`schema_drift_since=null` | PASS |
| **无 digest 观测不清除漂移**（AC-02，反证） | `test_observation_without_a_digest_neither_sets_nor_clears_drift`：D1→D2→None ⇒ `last_schema_digest`/基线/漂移/`since` **逐字段不动**，且本次复核照常留痕（`last_health`/`health_checked_at` 更新） | PASS |
| `approve` 重基线化（AC-03） | `test_approve_accepts_the_current_schema_as_the_new_baseline`：待批准态下 D1→D2 漂移，approve 后 `schema_drift=false`、基线 = D2 | PASS |
| 写面与读面同一事实（AC-04） | 同一用例内比对 `POST …/health-check` 的响应与 `GET /tool-provider-registrations` 的行：`last_schema_digest`/`schema_drift` 一致（两者共用 `probe_provider_spec`） | PASS |
| 无 digest 的 kind 诚实为 null（AC-04） | `test_registration_without_a_digest_capable_kind_reports_null_honestly`：NATIVE ⇒ `last_schema_digest`/`schema_baseline_digest` 为 `None`、`schema_drift=false`（不是空串、不是假值） | PASS |
| SQLite 往返 + 旧行兼容（AC-05） | `tests/adapters/sqlite/test_tool_provider_registry_store.py` **3 passed**：四字段往返（`loaded == drifted` 整体相等）；手写"加字段之前那一版的键集"的行 ⇒ 解码为 `None/False` 且其它字段不受影响 | PASS |
| DTO/OpenAPI 收敛（AC-06） | `python -B tools/gen_openapi.py` 重生成（**+39 / −1 行**，纯新增四个属性）；`tests/contracts` 通过；`lint-imports --config .importlinter.api` **2 kept, 0 broken**（DTO 仍不 import domain） | PASS |
| console 漂移可见（AC-07） | `registry-write.spec.ts` **7 passed**：有漂移 ⇒ `registry-schema-drift-<id>` 可见且给出 `111111111111→222222222222` 两个指纹；对照组（无漂移）⇒ 该 testid `toHaveCount(0)` | PASS |
| 全量门禁（AC-08） | stub e2e **83 passed (4.8m)**（81 + 2 新增；**33 路由结构签名与像素基线未变**——漂移标记只在真漂移时渲染，这是判据"只在真实变化时判红"的正向证据）；API+store+contracts+architecture **944 passed / 2 skipped**；`npx tsc`/根 eslint 空输出；mypy **860 files clean**；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3605 passed / 10 skipped**） | PASS |
| 安全扫描（sealed） | Mimosa deep scan `scan-2026-09-16T14-21-49.876Z-0d4c3af94894`，seal `sha256:84d72b6742f16d6a1fa8feff15aaa64eec621c2e093b342b997523be7917471f`：**36 findings（3 high / 28 medium / 5 low）**，与 cycle 4/5/6 逐项一致；**本轮 9 个改动/新增文件零命中**；3 条 high 仍是既有文件（`packages/application/protocol_authoring/service.py:103` 与 `artifacts/钻孔官方API_v12/**` 两个不可变历史资产） | PASS |

## 告警

- **W-1（真实缺陷，本轮发现·未修）**：**控制面 SQLite 共享连接不支持并发写**。
  证据：对 live 控制面（`tests/api/console_api_app:app`，uvicorn:8013）并发发 24 个
  `POST /ops/schedules`（12 线程），得 **19×201 / 2×500 / 2×404 / 1×409**；500 的服务端栈是
  `services/api/routers/ops_schedules.py:99 → …:50 → schedule_registry.py:94 →
  adapters/sqlite/schedule_store.py:78` 抛 **`sqlite3.InterfaceError: bad parameter or other API misuse`**
  ——`connect(..., check_same_thread=False)` 允许跨线程，但 sqlite3 连接**不允许两个线程同时使用**；
  FastAPI 的同步端点跑在 threadpool 里，于是并发写直接撞上。
  同一批的 2 个 **404**（"unknown schedule: …"，写成功后立刻读不到的形态）与 500 同源。
  这**不是** cycle 7 的改动引入的（本轮只动 tool provider 注册面），但它让此前
  EC-03 的"live 35 passed"必须被读成**单并发**下的结论。已登记为下一轮的第一项。
- **W-2（口径边界）**：**漂移只在治理读面可见**——`GET /tool-providers`（目录读面）不带
  digest，preflight 也不消费漂移。也就是说：schema 变了**不会**自动触发警示或阻断，
  它只是"可被看见并可比对"。EC-02 的判据是"记录 + 可比对漂移"，本轮到此为止；
  把它接进决议链（例如 `TOOL_SCHEMA_DRIFTED` 警示）是另一件事，未做。
- **W-3（基线语义边界）**：基线来自**首次观测**。若提供方在首次复核之前就已漂移过，
  本轮检测不到（注册面没有"注册时 schema"可比——`pinned_revision` 是内容寻址的
  revision，与运行期 schema 不是同一轴）。不得把这条读成"能发现任意漂移"。
- **W-4（旧行为变化）**：`approve` 现在会重设基线并清漂移。对既有调用方无破坏性
  （待批准 → 已批准 的转移语义不变），但"批准会接受当前 schema 形态"是**新增语义**，
  已写进方法 docstring；若将来需要"批准但不接受当前 schema"，需要另立机制。
- **W-5（实现侧重构，两处门禁拦截）**：
  ① `registrationColumns.tsx` 加标记后函数超 50 行，被**根 eslint 判红** ⇒ 把单元格抽成
  `RegistryHealthCell.tsx`；
  ② `tests/api/test_tool_registrations_api.py` 在本轮新增用例后达 **523 行**，被
  `tests/tooling/test_python_source_limits.py` 的 **450 行硬上限判红** ⇒ 拆出
  `tests/api/test_tool_registration_health_drift.py`（180 行，只放指纹/漂移一族，
  注册生命周期用例留在原文件 361 行）。两处都**未放宽任何规则**（改的是代码/文件划分，
  不是阈值）。

## 结论

EC-02 判据的第四个子句（健康复核记录 schema digest 并可比对漂移）交付完成：适配器早已算出的
`observed_schema_digest` 现在一路走到注册记录、DTO、读面与 console，且**漂移是状态**
（当前 vs 基线）、**未知观测不清除漂移**、**批准 = 接受当前形态**，三条反证都在用例里。
结果为 **PASS_WITH_WARNINGS**：W-1 是**本轮发现、本轮未修的真实并发缺陷**（不属于本 PLAN 的
改动面），W-2/W-3 是口径边界（"可见"不等于"可阻断"、基线只能从首次观测起算），
W-4 是新增语义，W-5 是门禁拦截后的重构。
