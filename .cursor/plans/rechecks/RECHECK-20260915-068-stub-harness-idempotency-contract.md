---
id: RECHECK-20260915-068
plan_id: PLAN-20260915-068
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle6
baseline_ref: 3cb5693
checked_head: 3cb5693+worktree
---

# RECHECK-20260915-068 — 替身 harness 校验 Idempotency-Key（GOAL-003 cycle 6 / EC-05）

## 检查范围

PLAN-20260915-068 声称的交付面：`apps/web/tests/e2e/stub-idempotency.ts`（契约实现）、
`apps/web/tests/e2e/stub-idempotency.spec.ts`（4 条用例）、
`apps/web/tests/e2e/stub-api.ts` 的守门与记账接线、
`tests/tooling/test_console_stub_idempotency_parity.py`（跨语言词表守卫），
以及「客户端去掉发送头 → 套件必须红」的反证实验（`apps/web/src/api/http.ts` 临时改后还原）。

**未覆盖**（如实登记，见告警）：替身与真件之间**刻意保留**的两处差异（摘要口径、重放 ETag）、
守门顺序对 `assertNoUnmatched` 的影响、以及 `PUT` 无真实路由可测（由词表守卫覆盖）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 缺头 → 422 与真件同形状（AC-01） | 第 1 条用例对 `POST /api/projects` **逐字段**断言完整 body（`type/title/status/detail/instance`，`instance` 为空串）；对照 `services/api/middleware.py::_problem()` 源码 | PASS |
| mutating 词表四方法（AC-02） | 第 1 条用例对 POST / DELETE（`/api/projects/:id`）/ PATCH（`/api/projects/:id`）各发一条真实请求，均 422；集合本身由 parity 守卫与真件 `_MUTATING_METHODS` 断言相等 | PASS |
| 分析类 POST 豁免（AC-03） | 第 2 条用例：`POST /api/llm-endpoints/:id/test` 无 key ⇒ 断言 `status != 422` 且 `title != "Idempotency-Key Required"` | PASS |
| 同 key 不同摘要 → 422 Reused（AC-04） | 第 3 条用例：同 key 两个不同 body 的 POST ⇒ 第二次 422 且 title 命中 | PASS |
| 同 key 同摘要 → 重放、不二次改状态（AC-05） | 第 4 条用例用 `POST /api/ops/schedules`（重名会 409）：第二次仍是 **201** 且 body 与首次逐字相同。若替身无重放语义，第二次会真的再建一遍并撞 409 | PASS |
| **客户端反证**（AC-06） | 把 `apps/web/src/api/http.ts` 的 `headers.set("Idempotency-Key", …)` 临时改成别的头名后跑 `schedules-write` + `project-delete`：**7 failed / 2 passed**；失败页面上呈现的正是真件的 422 detail `mutating requests require Idempotency-Key`（UI 把 problem 原文显示在面板内）。随后还原，`git diff --stat apps/web/src/api/http.ts` **无输出** | PASS |
| 跨语言词表守卫（AC-07） | `tests/tooling/test_console_stub_idempotency_parity.py` **2 passed**：直接 import 真件的 `_MUTATING_METHODS`/`_ANALYSIS_ACTIONS` 做集合相等断言，并断言豁免清单**非空**（防空集合让"豁免"退化成"全部豁免"）；另一条断言 problem 五字段与两条 detail 文案字面量 | PASS |
| 全量 stub 套件（AC-08） | `pnpm --dir apps/web exec playwright test --config playwright.config.ts`：**81 passed (4.5m)**（77 既有 + 4 新增），零失败——反证说明既有用例本来就发头，本轮没有让任何用例"变绿"或"变红"。两次独立运行同为 81 passed（首次在 eslint/tsc 修复前） | PASS |
| 根 TS 门（AC-08） | **首轮 m0 在 `typescript/lint` 判红 10 个 error**（见下「本轮门禁拦截」），修复后 `npx eslint <三个文件>` 空输出；`npx tsc --noEmit -p apps/web/tsconfig.json` 空输出 | PASS |
| m0 全量（AC-08） | `sh scratch/run-m0-cycle12.sh` → **PASS: profile=m0; 23 deterministic checks** | PASS |
| 记录（AC-09） | RECHECK-068（本文）+ MEM-20260915-043 + EXP-20260916-001 + GOAL-003 的 EC 表／迭代日志／状态历史 + ALL_PLAN | PASS |
| 安全扫描（sealed） | Mimosa deep scan `scan-2026-09-16T12-35-44.199Z-b806ba6e28cc`，seal `sha256:d15c0a99c4c08a2237fc9b53e544eebe45b19d899a6714faa193125c26d32998`：**36 findings（3 high / 28 medium / 5 low），182 packages**——计数与 cycle 4/5 逐项一致。**本轮改动的四个文件（stub-idempotency.ts / stub-idempotency.spec.ts / stub-api.ts / parity 守卫）零命中**；3 条 high 全部落在既有文件（`packages/application/protocol_authoring/service.py:103`、`artifacts/钻孔官方API_v12/**` 两个不可变历史资产），与上一轮同一批。`verdictEffect: none` | PASS |

## 本轮门禁拦截（gate-caught，两处都是真实缺陷）

1. **根 eslint（`typescript/lint`）判红 10 个 error**——`apps/web` 自己的 `eslint src` 配置对
   `tests/**` 有放宽，而根配置 `eslint .` 覆盖 `apps/web/tests/**`：`max-params` 两处
   （`call` 5 参、`beginMutation` 4 参）、`no-restricted-syntax`（内联 `import("@playwright/test").Page`）、
   `dot-notation` 四处（`body["title"]`）、`no-unnecessary-condition` 与
   `no-unnecessary-type-conversion` 各两处。修法是**改代码**（参数表收敛为 options 对象、
   顶层 `import type`、点号访问、去冗余判断），**未改 eslint 配置、未加任何 disable 注释**。
   m0 runner 在首个失败后中止剩余检查，所以这轮只暴露了 lint 一项。
2. **`tsc -p apps/web/tsconfig.json`**（lint 修完后单独跑）——`exactOptionalPropertyTypes`
   与 `noUncheckedIndexedAccess` 拒了两处：`page.evaluate(fn, arg)` 的数组实参被推断为
   `string[]`（解构出 `string | undefined`）、以及 `body: string | undefined` 不可赋给
   `RequestInit`。修法：显式四元组类型 + 条件式装配 `RequestInit`。

两处都不是"为了让门禁通过而放宽"，而是门禁抓住了新代码的真实缺陷；修完后
stub 套件在同一份产物上重跑仍是 **81 passed**，语义未变。

## 告警

- **W-1（刻意不一致·摘要）**：替身的"请求摘要"是 `method\npath\nbody` 的拼接，真件是
  `services/api/idempotency.py::request_digest` 的 sha256。两者对"同/不同"的判定一致
  （同一输入同一结果），但**不可互换、不可互相引用**——替身的摘要不能当作真件摘要的证据。
  已写进 `stub-idempotency.ts` 模块 docstring。
- **W-2（刻意不一致·ETag）**：真件重放时回放存储的 ETag；替身的重放响应不带 ETag
  （替身响应体里没有它）。因此"重放响应带首次 ETag"这条性质**只能在 live 层被证明**，
  stub 层不覆盖。同样写进了模块 docstring。
- **W-3（守门顺序的真实副作用）**：替身在 `match()` **之前**判 key，与真件
  （`BaseHTTPMiddleware` 包住 router）一致，因此"未知路径 + mutating + 无 key"回 **422 而不是
  404**。这条对实现是忠实，但它意味着这类请求**不再进 `unmatchedRequests`**——
  `assertNoUnmatched()` 对该情形失效，"手滑写错路径"在缺 key 时不会以 404 的形式被抓到。
- **W-4（覆盖边界）**：`PUT` 在 console 面上没有真实路由，词表里的 `PUT` 只由 parity 守卫
  （集合相等）覆盖，**没有**端到端请求背书；POST/DELETE/PATCH 有。另外替身只在 **stub** 套件
  生效，live 套件仍走真实中间件——两者是"同一契约的两个实现"，不是同一个实现。
- **W-5（证据采集）**：本轮第一次后台跑 stub 套件时把它 `TaskStop` 了，遗留的
  `npx playwright test` 子进程与第二次运行**共用同一日志文件**，产出过一份 ok 与 x/- 混杂、
  不可判读的日志。已按进程 PID 清理并用唯一文件名重跑（单表头、81 passed）。该教训记在
  `.cursor/experience/entries/EXP-20260916-001.md`；**本 RECHECK 的 81 passed 取自重跑后的
  单头日志**，不是那份混写日志。

## 结论

EC-05 的验收面（头校验 + 反证 + stub 套件绿）全部成立，且反证做在**产品客户端**上而非替身自己
——这条契约现在能在 stub 层被证伪。结果为 **PASS_WITH_WARNINGS**：两处刻意不一致（W-1/W-2）
是替身的已知边界、守门顺序的副作用（W-3）与 `PUT` 的覆盖缺口（W-4）如实登记，均不构成本轮
EC 的缺口，但读者不应把 stub 套件读成"与真中间件逐字等价"。
