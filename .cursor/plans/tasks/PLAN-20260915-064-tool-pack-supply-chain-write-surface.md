---
id: PLAN-20260915-064
slug: tool-pack-supply-chain-write-surface
title: ToolPack 供应链写面：install / approve-update / revoke + 目录消费
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 2 = EC-02（ToolPack install/approve 供应链面）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」，以及 GOAL-20260915-002「收口结论」表第 ② 项与 RECHECK-060 的 W-2/W-3 结转告警；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-064-tool-pack-supply-chain-write-surface.md
memory_entries:
  - MEM-20260915-039-tool-pack-install-binds-content-digest
---

# PLAN-20260915-064 — ToolPack 供应链写面（GOAL-003 cycle 2 / EC-02）

## 目标

把 ADR-0019 的 ToolPack 供应链从"有 use case、无控制面"补成**可执行、可审计、被消费**
的写面：`install` / `approve-update` / `revoke` 三条真实路由 + 持久化 store + 目录消费，
并把 RECHECK-060 结转的两条供应链告警就地关掉（W-2 capabilities 取值域、W-3 pin 与交付物
绑定）。

**为什么这是缺口**：`ToolPackLifecycle`（`packages/application/tool_plane/lifecycle.py`）
已实现内容 digest 校验、policy 门、权限 diff 与事件，但**只被测试调用**——
没有 store adapter（只有 Fake）、没有路由、没有装配、`docs/api/CONTROL_PLANE_API.md`
把三条端点记为"(未提供)"，`pageSupport.GAPS.integrations` 也如实写着"工具包安装（ToolPack）
仍无写面"。于是"供应链治理"只有形状没有执行面。

## 口径（先写清楚，再写代码）

1. **install 的 pin 是内容寻址自证**（关 W-3）：请求体里既有 `digest`（pin）又有全部内容，
   服务端用 `toolpack_content_digest()` **重算**并要求相等——不相等即 422。
   这不是"信任调用方写的 digest"，而是"控制面自己算出来的一致才算数"。
2. **权限扩张必须显式批准且**不生效**（approve-update 的语义）**：同 id 的更新若引入新的
   capability / network domain / credential（`permission_diff` 非空），**不立即生效**——
   登记为待批准更新并返回 **202**，目录里仍是旧版本的 digest；`approve-update` 通过 policy
   `tool_pack.update.expanded` 后才替换。**"已提交"不等于"已生效"**，与 provider 注册的
   与 provider 注册"已登记待批准 → 已批准"同一哲学。
3. **capabilities 取值域**（关 W-2，pack 侧）：`requested_capabilities` 与每个 tool 声明的
   capabilities 必须都在平台词表（`examples/config/capabilities.yaml`，与 bundle validator 同源）
   内，否则 422 并列出未知项。词表读不到 → 503（不降级成"放行"）。
4. **内置 pack 不可影子覆盖**：`examples/contracts/toolpack_*.yaml` 的 id 集是平台自带基线，
   安装同 id 的 pack → 409（沿用 provider 注册的既有规则）。
5. **写面必须被读面消费**（MEM-035）：INSTALLED 的 pack 把 digest 合入
   `CatalogSnapshot.tool_pack_digests`（key = pack id 去掉 `_vN` 后缀），于是同一份草稿协议的
   preflight 结论随 install/revoke/pending 三态改变——这三态就是本计划的消费证明。
6. **REVOKED 是终态**：不可更新、不可重新安装（409），与 provider 注册一致。

## 端点与状态码（写进 docstring 与文档，不只写在记录里）

```text
GET    /tool-packs                     已安装 pack 列表（state / 生效 digest / capabilities / 待批准标记）
POST   /tool-packs/install             201 安装；200 同权限更新生效；202 权限扩张待批准；409 重复/终态/内置 id；422 digest 不符/未知 capability/凭据 scope 违规；503 未装配
POST   /tool-packs/{pack_id}/approve-update  200 应用待批准更新；403 policy 拒绝；404 未知；409 无待批准/终态
POST   /tool-packs/{pack_id}/revoke    200 终态吊销（reason 必填 422）；404 未知；409 已吊销
```

## 范围

- 端口/域：`ToolPackRecord` 增加 `pending_manifest`（默认 None，向后兼容）；
  `ToolPackStore` 契约补一条"待批准更新"语义（沿用既有 `replace`）。
- 适配器：新增 `adapters/sqlite/tool_pack_store.py`（表 `tool_packs`，含 pending 列）。
- 服务：新增 `services/api/routers/tool_packs.py` + `services/api/dto/tool_packs.py` +
  `services/api/tool_pack_support.py`（DTO 投影 / 503 原因 / 词表加载）；
  `services/api/catalog_merge.py` 合并 INSTALLED pack 的 digest；
  `services/api/composition.py` 与 `pg_composition.py` 装配（两路同侧，沿用 registry 的既有口径）。
- 契约/文档：`docs/api/openapi.m13.json` 重生成 + 契约测试断言；`docs/api/CONTROL_PLANE_API.md`
  三条"(未提供)"改写为真实语义；`docs/frontend/CONSOLE_PAGE_MAP.md` G15 行与
  `apps/web/src/navigation/pageSupport.ts` 的 integrations 文案同步收敛（console 操作入口
  仍缺 → 如实写"已有 API、console 尚无入口"，不假装完整）。
- 测试：`tests/api/test_tool_packs_api.py`（新增）、store 契约测试补充、既有 tool_plane 测试同步。

## 明确不在本轮（下一轮输入）

- **console 操作入口 + live e2e 链**：EC-02 的 verify 里含"live e2e 链"，但页面/表单/替身
  是一整块前端工作，本轮先做后端写面；EC-02 记 PARTIAL，cycle 3 承接。
- **W-4 schema digest 漂移**：`ToolHealthReport.observed_schema_digest` 在
  `probe_provider_spec` 被丢掉；落库 + 漂移比对属 provider 侧，与 pack 写面可独立验收。
- **provider 侧 capabilities 词表校验**：本轮只在 pack install 上强制；provider 注册沿用现状
  （RECHECK-060 W-2 的 provider 部分保留到下一轮，不得假装已关）。

## 验收条件

- [x] AC-01：三条路由 + GET 列表存在且语义如上（状态码逐条用例覆盖）。
- [x] AC-02：digest 绑定可证伪——篡改任意内容字段（不改 `digest`）→ 422；未篡改 → 201。
- [x] AC-03：未知 capability → 422 且列出未知项；合法 pack → 201（词表与 bundle validator 同源）。
- [x] AC-04：权限扩张 → `pending_approval` 且**目录 digest 不变**（旧版本仍生效）；
  `approve-update` → 200 后目录 digest 改变。
- [x] AC-05：消费证明——安装后 `merged_catalog_snapshot().tool_pack_digests` 变为 pack 的
  digest、扩张待批准期间**仍是旧 digest**、revoke 后回落到 examples 基线
  （口径限制见 RECHECK-064 W-1：finding 级翻转在当前示例数据下不可达）。
- [x] AC-06：内置 pack id → 409；REVOKED 终态不可再 install/update → 409；未知 id → 404；
  store 未装配 → 503（读面给不可用原因）。
- [x] AC-07：OpenAPI 快照含三条写方法 + GET（+437 行），契约测试锁定路径/方法与
  `digest`/`422`/`409` 语义关键词。
- [x] AC-08：文档与 pageSupport 收敛（三条"(未提供)" 不再存在；console 入口缺口如实保留）。
- [x] AC-09：`pytest tests/api tests/application tests/contracts` = **1354 passed / 3 skipped**；
  根 eslint / `tsc --noEmit` 0 error；本地 m0 = 23 deterministic checks（首跑被 ruff
  行宽/mypy 拦下，逐条修复后复跑绿）。
- [x] AC-10：设计基线不受影响——33 路由像素 + 结构签名双绿且基线**逐字节未动**
  （pageSupport 文案不在这些路由的可见 DOM 中，见 RECHECK-064 W-2）。

## 实施清单

- [x] WP-A 端口/域：`ToolPackRecord.pending_manifest` + `manifest_document`/`manifest_from_document`
- [x] WP-B 持久化：`adapters/sqlite/tool_pack_store.py` + 两路装配
- [x] WP-C 写面：DTO + 支持模块 + 路由（状态码/docstring 即文档）
- [x] WP-D 消费：`catalog_merge` 合并 INSTALLED pack digest + 三态证明用例
- [x] WP-E 契约/文档/门禁：OpenAPI 重生成 + 契约断言 + 两份文档 + pageSupport 文案 + m0

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/application/test_tool_plane_execution.py` → **12 条生命周期用例**（含"扩张不生效直到批准"、"相同内容不是更新"、"吊销清 pending"）；域编解码被 pytest 往返使用 | PASS |
| WP-B | `tests/api/test_tool_packs_api.py`（9 条）经 SQLite store 全绿；`pytest tests/api` = **370 passed** | PASS |
| WP-C | 错误映射修正：`InvalidInputError` 是 `PermanentPortError` 子类 ⇒ 先判子类（首版"未知 pack"返回 422，被用例抓住） | PASS（先失败后修复） |
| WP-D | `test_installed_digest_is_consumed_by_catalog`：install → 新 digest；pending → **旧 digest**；revoke → 基线 digest | PASS |
| WP-E | OpenAPI **+437 行**；`test_openapi_contains_tool_pack_write_methods` 通过；`pytest tests/api tests/application tests/contracts` = **1354 passed / 3 skipped**；stub e2e **66 passed**、live e2e **31 passed**；根 eslint 0 error、`tsc --noEmit` 通过；m0 **23/23** | PASS |

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：GOAL-003 cycle 2，取 EC-02。设计先行——把
  `ToolPackLifecycle`（已有 use case、只被测试调用）接到真实控制面，并把
  "权限扩张不立即生效"作为 approve-update 的语义写进计划，再写代码。
- 2026-09-16 WP-A/WP-B 完成：`ToolPackRecord.pending_manifest`（生效版本与待批准版本
  同行写入）、域编解码 `manifest_document`/`manifest_from_document`（复用内容口径，
  往返不漂移）、`SqliteToolPackStore`、`_verify_supply_chain` 语义保持。
- 2026-09-16 WP-C/WP-D 进行中：`submit`/`approve_update` 替换旧 `install`/`update`
  （既有测试同步到新语义，含"扩张不生效直到批准"与"相同 manifest 不是更新"两条新用例）；
  `/tool-packs` 四条路由 + 两路装配 + `catalog_merge` 合并 INSTALLED digest 已落地。

## 影响报告

- 改动：域（`packages/domain/tools.py` 新增 `manifest_document`/`manifest_from_document`）、
  端口（`ToolPackRecord.pending_manifest`）、use case（`ToolPackLifecycle.submit`/
  `approve_update` 取代 `install`/`update`）、适配器（`SqliteToolPackStore` 新增、
  `FakeToolPackStore.revoke` 清空 pending）、服务面（新路由/DTO/support，`ApiDeps`、
  两 composition root、`catalog_merge` 消费）。
- lint/typecheck/test：见「证据」段（完成后回填）。
- Domain/API/schema 变化：**有**——新增 `POST /tool-packs/install`、
  `POST /tool-packs/{pack_id}/approve-update`、`POST /tool-packs/{pack_id}/revoke`、
  `GET /tool-packs`（OpenAPI 快照重生成）；`ToolPackRecord` 增加字段（向后兼容默认 None）。
- 安全/凭据变化：无新增凭据面；**供应链语义增强**：pin 由控制面重算校验、权限扩张
  需显式批准、capability 取值域受控、内置 pack id 不可覆盖。
- 兼容性/迁移风险：`ToolPackStore` 端口契约扩展（旧实现需接受 `pending_manifest`）；
  `install`/`update` 方法被 `submit`/`approve_update` 取代（仓内调用点已同步，含测试）。
- 上游版本影响：无（未引入新依赖）。
- 下一项任务：cycle 3 = EC-02 的前端面（console ToolPack 操作入口 + live e2e 链）与
  W-4（provider 健康复核记录 schema digest 并比对漂移）。

## 已知风险

- **路由体量大**：install 的请求体要承载完整 manifest（tools/skills/credentials/…）。
  若 DTO 与 domain 漂移，会出现"控制面收得进、域里建不出"的裂缝——用 Pydantic 校验 +
  域构造异常的显式映射（422）兜住，并写一条"缺字段 → 422"的用例。
- **词表来源**：`examples/config/capabilities.yaml` 是示例目录，但它同时是 bundle validator 的
  词表来源；本轮沿用同一来源以保持"离线校验与运行时校验同源"。若未来词表迁到正式配置面，
  本计划的加载点即唯一改动处（已集中在一个函数）。
- **pending 语义的持久化**：pending manifest 必须与生效 manifest 一起原子写入，否则崩溃后
  可能出现"批准了不存在的东西"或"扩张被静默生效"。SQLite 侧用单行 JSON 列 + 单事务写入。
- **不动前端**：本轮页面不变 ⇒ 结构签名基线应逐字节不变；若基线红了说明"顺手改了前端"，
  必须显式登记（见 AC-10）。
