---
id: RECHECK-20260915-060
plan_id: PLAN-20260915-060
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-002-cycle6
baseline_ref: 692ef19
checked_head: 692ef19+worktree
---

# RECHECK-20260915-060 — Tool Provider 注册治理写面（GOAL-002 cycle 6 / EC-05）

## 检查范围

PLAN-20260915-060 声称的交付面：`ProviderRegistration` 域（状态机 + 信任推导 + pin 门）、
`ToolProviderRegistry` Port 与 SQLite 实现、6 条注册面端点、ACTIVE 注册合入目录与
`tool_pack_digests` 的消费链、健康复核与读面同源、前端注册面板与 `pageSupport` 收敛、
stub/live e2e、`ops-integrations` 设计基线。其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 状态机与终态语义 | `packages/domain/tool_registry.py`：初始态→ACTIVE→REVOKED；REVOKED 无出边；`updated()` 在 REVOKED 上抛 `InvalidTransitionError`；用例覆盖重复 approve 409、终态 revoke/patch 409 | PASS |
| 信任级别不可自我声明 | `ProviderRegistration.spec()` 用 `trust_for(state)` 推导；`ToolProviderRegisterDto` **没有** trust_level 字段（接口层面无法传入）；用例断言 初始态=UNTRUSTED、ACTIVE=USER_APPROVED | PASS |
| pin 是硬门（AGENTS.md §9） | `__post_init__` 用 `Digest.parse` 校验 `sha256:<64hex>`；用例 `pinned_revision="v1.2.3"` → 422 且 detail 含 "digest"；live e2e 同断言 | PASS |
| 不影子覆盖内置目录 | `register_provider` 先查注册表（重复 409）再查 `load_catalog_snapshot().tool_providers`（占用 409，detail 指 built-in catalog）；用例断言既有行未被改写（pin 仍是 PIN） | PASS |
| **写面被供应链面消费** | `tests/api/test_tool_registrations_api.py::test_preflight_consumes_approved_registration`：同一草稿协议（要求 `dataset.read`）在 未注册 / 初始态 → `TOOL_UNAVAILABLE`；ACTIVE → 消失且无 `SUPPLY_CHAIN_UNPINNED`、出现 `TOOL_HEALTH_UNPROVEN`；REVOKED → 回归 | PASS |
| 消费不是"读了就算" | `merged_catalog_snapshot` 只合并 `state == ACTIVE`；`tool_pack_digests[provider_id] = pinned_revision` 让 `preflight._is_pinned_digest` 通过——即"用户 pin 的那份"就是 preflight 看到的那份 | PASS |
| 健康复核与读面同源 | `preflight_support.probe_provider_spec()` 抽出后，`build_provider_health` 与 health-check 端点共用；用例注入 `FakeToolProvider`：HEALTHY → 目录 HEALTHY；`fail_health` → OPEN_CIRCUIT → 目录同步；无实例 → UNKNOWN + 原因 | PASS |
| 未装配即锁定 | 用例 `deps.tool_provider_registry = None`：读面 200 + `management_available=false` + 原因、写面 503、目录面同样标记不可管理——不伪造成功 | PASS |
| 语义变化的连带更新 | `GET /tool-providers` 的 `management_available` 由恒 false 变为"是否装配"；`test_reports_integrations_lineage_api.py` 与 `live-api-workflow.spec.ts` 的旧断言同步改写（不是删断言，是改成新口径） | PASS |
| 装配两侧同源 | `composition._sqlite_config_stores` 与 `pg_composition._pg_config_stores` 各加一项；`tests/api/conftest.py` 与 `run_fixtures._run_ready_sqlite_stores` 同侧加入 `SqliteToolProviderRegistry`（live harness 因此可走真实注册链） | PASS |
| 队列/派发面的既有约束未破 | `pytest tests/api -q` → **354 passed**（run-ready 装配新增注册表后全量 API 无回归） | PASS |
| OpenAPI 快照一致 | `tools/gen_openapi.py` 重生成（+648 行）；新增 `test_openapi_contains_tool_registration_write_methods` 逐条断言 5 条路径的写方法；契约套件 **358 passed, 56 skipped** | PASS |
| 前端真的能写 | stub e2e `registry-write.spec.ts` 5 用例：登记后目录**不含**该 id；批准后目录含 `USER_APPROVED`；吊销后目录移除且终态行无处置动作、理由落库显示；理由为空时按钮禁用；健康复核事实出现在注册表行 | PASS |
| 真实装配面同性质 | live e2e `live-registry-write.spec.ts` 2 用例（真实 uvicorn HTTP）：登记 201 且处于初始态（不入目录）→ approve 后目录含 `USER_APPROVED` → health-check UNKNOWN（无实例）→ revoke 后退出目录；漂移 pin 422、重复 409 | PASS |
| 替身与后端同因果 | `stub-routes-registry.ts` 承接 `/tool-providers`（原静态替身删除），目录按注册状态生成；approve 对非初始态返回 409（与后端一致），不是宽松替身 | PASS |
| 清单单一来源仍成立 | 新增 live spec 只改 `tests/e2e/live-specs.ts` 一处；`--list` 复核 stub **55 tests / 14 files**、live **30 tests / 8 files** | PASS |
| 设计基线 | `ops-integrations` 的 win32（本地）与 linux（pinned noble 容器）重生成并目检：目录表 + 注册面板（id/kind/能力/pin + 登记按钮）+ "尚无注册项"空态渲染正确，无裁列/溢出 | PASS |
| 前端门禁 | 根 `npx eslint .` = 0 error（2 条既有 soft warning：`live-api-workflow.spec.ts` 443 行、`stub-routes.ts` 335 行，均未超硬上限 450）；web `tsc --noEmit` 通过；单测 76 passed | PASS |
| Python 门禁 | 本地 m0 红 **3 次**才绿：① `python/product-lint`（`test_tool_registrations_api.py:311` 行宽 104 > 100）→ ② `python/format-check`（`tool_registry.py` / `tool_registrations.py` 未格式化）→ ③ `python/typecheck` + `typescript/typecheck`（`iso()`/`_existing()` 返回 Any、`TRUST` 常量索引可能 undefined）→ 逐条修复后 **m0 = `profile=m0; 23 deterministic checks`** | PASS（先失败后修复） |
| 轮内自证的边界（复现 cycle 5 结论） | `scratch/cycle6-baseline-drift/measure.py` 按 Playwright 判据量化"HEAD 基线 vs 重生成后"：win32 **0.79%**、linux **0.66%**，均低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁不会报警（见 W-1） | PASS（含告警） |

## 结论

result: **PASS_WITH_WARNINGS**

EC-05 的判定标准成立：`docs/api/openapi.m13.json` 里有真实的注册写方法（5 条路径、
approve/revoke/health-check 均为 POST），`pageSupport` 中 `ops/integrations` 的
`disabledOperations: ["install","approve","revoke"]` 已删除，而这一页现在真的能写——
登记落库后目录不变（初始态），批准后 provider 与其 pin 进入目录并被 compile/preflight
消费（`TOOL_UNAVAILABLE` 消失、无 `SUPPLY_CHAIN_UNPINNED`），吊销后退出。API 与 live e2e 全绿。

本轮的关键判断是"消费证明"必须由**同一份输入在不同状态下的不同结论**给出，而不是
"写了之后读得到"。因此验收用例用一个只被注册 provider 覆盖的能力（`dataset.read`）跑
`POST /projects/{id}/preflight`：未注册 / 初始态报 `TOOL_UNAVAILABLE`，ACTIVE 后消失且
供应链 pin 检查通过，REVOKED 后回归——这条用例同时也是"初始态不进目录"的证明。

门禁依旧是**先红后绿**（3 次），且三次都是"用脚本/新文件写完就交"的典型失误：
行宽、格式、Any 返回与可空推断；逐条修复后 23/23，未跳过任何一道。

## 告警

- W-1（**设计门禁的容差盲区**，本轮再次实测）：新增整块注册面板后旧基线只差
  0.79%（win32）/ 0.66%（linux），阈值 2% ⇒ 门禁不会变红。与 cycle 3（1.73%）、
  cycle 5（1.02%/0.93%）同类；"页面改动必须主动重生成基线并目检"仍是流程要求。
  量化脚本：`scratch/cycle6-baseline-drift/measure.py`（从 `git show HEAD:` 取旧基线，
  不往仓库里堆 PNG）。
- W-2（capabilities 不是授权边界）：登记时的 `capabilities` 只做非空与长度校验，
  不校验取值域（如 `dataset.read` 不在 `examples/config/capabilities.yaml` 也照收）。
  "能力名由 provider 声明"是既有形态，但使用方容易误读为"登记即授权"——
  真正的放行仍由 policy（`POLICY_DENIED`）与 resolver 的 trust/health 过滤决定，
  本计划未改变这一点。
- W-3（pin 只校验形态）：`sha256:<hex>` 只保证"写的是一个内容寻址字面量"，
  控制面不取 provider 内容，无法自证 digest 与实际交付物一致；真正的供应链证明
  仍在未提供的 ToolPack install/approve 面。
- W-4（健康复核无 schema 漂移比对）：`ToolHealthReport.observed_schema_digest`
  未落库，复核只能给出 status/detail；供应商悄悄改 schema 时复核看不出差异。
- W-5（跨 feature 重构需登记）：`useOpsAction` → `hooks/useAsyncAction`、
  `OpsFields` → `components/InlineFields` 是本轮顺带消除的重复（否则会复制第二份）；
  ops-view 的三处调用点已同步，e2e 只依赖 testid/文案，未受影响——但这类"顺手重构"
  应随计划登记，避免变成无主改动。
- W-6（继承，未处理）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）仍开放。

## 复现

```
# 域 / API / 契约
python -m pytest tests/api/test_tool_registrations_api.py -q           # 18 passed
python -m pytest tests/api -q                                          # 354 passed
python -B tools/gen_openapi.py && python -m pytest tests/contracts -q   # 358 passed, 56 skipped
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm exec playwright test --list                         # 55 tests in 14 files
cd apps/web && pnpm exec playwright test --list --config playwrightLive.config.ts  # 30 tests in 8 files
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live              # 55 / 30 passed
cd apps/web && pnpm test                                               # 76 passed
# 设计基线（ops-integrations；linux 在 pinned noble 容器内重生成）
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/ops-integrations-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh ops-integrations
# 门禁漂移量化（HEAD 基线 vs 重生成，Playwright 判据）
python scratch/cycle6-baseline-drift/measure.py                         # 0.79% / 0.66% ⇒ 不报警
# 本地门
sh scratch/run-m0-cycle12.sh                                            # profile=m0; 23 deterministic checks
```
