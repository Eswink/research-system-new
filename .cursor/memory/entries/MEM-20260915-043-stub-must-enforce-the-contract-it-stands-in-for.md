---
id: MEM-20260915-043
title: 替身必须守它替代的那条契约——只对齐"成功路径"的 stub 会让漏发契约头的客户端全绿
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-068-stub-harness-idempotency-contract.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-068-stub-harness-idempotency-contract.md
supersedes: []
tags:
  - stub-harness
  - idempotency
  - cross-language-guard
  - falsification
  - playwright
---

# 替身 harness 不校验 Idempotency-Key：33 条 stub 用例对"客户端漏发头"集体视而不见

## 做了什么

`apps/web/tests/e2e/stub-api.ts` 原来完全不看请求头——客户端漏发 `Idempotency-Key`，
stub 套件照样全绿，这条 mutating 契约只有 live 套件（真实 uvicorn + SQLite）能证伪（EC-05）。
本轮给替身加了与真中间件同语义的守门（新增 `tests/e2e/stub-idempotency.ts`，
在 `match()` **之前**判 key、在 `handler()` **之后**记账）：

| 情形 | 替身行为 | 真件（`services/api/middleware.py`） |
| --- | --- | --- |
| 缺头 / 空值 | 422 `Idempotency-Key Required` | 同 |
| 同 key + 不同摘要 | 422 `Idempotency-Key Reused` | 同 |
| 同 key + 同摘要 | 重放首次响应 | 同（另带存储的 ETag） |
| 分析类 POST（`validate`/`compile`/`preflight`/`dry-run`/`test`/`discover-models`/`probe`） | 豁免 | 同 |

反证做在**产品客户端**上：临时把 `apps/web/src/api/http.ts` 的发送改成别的头名，
`schedules-write` + `project-delete` **7 failed / 2 passed**（失败页面里呈现的正是真件的
422 detail），还原后 `git diff` 为空。

## 为什么这样做

1. **替身只对齐"成功路径"等于没有替身**：stub 的价值在于"能在本地、廉价地证伪客户端契约"。
   如果它只回放 happy path，那它证明的只是"在一切正确时一切正确"。
2. **反证对象必须是产品客户端，不是替身自己**：写一条"缺头 → 422"的用例只证明了替身会拒绝；
   真正的风险是**客户端漏发而替身放行**。所以必须有"去掉产品客户端的发送 → 套件红"的实验。
3. **替身与真件之间必须有跨语言守卫**：`MUTATING_METHODS`/`ANALYSIS_ACTIONS` 是同一契约的
   两份拷贝，替身单方面放宽（例如漏掉 PATCH）不会让任何既有用例变红。
   `tests/tooling/test_console_stub_idempotency_parity.py` 直接 import 真件的
   `_MUTATING_METHODS`/`_ANALYSIS_ACTIONS` 做集合相等断言，并额外断言豁免清单非空
   （空集合会让"豁免"退化成"全部豁免"）。
4. **守门顺序属于语义**：真中间件是 `BaseHTTPMiddleware`（包住 router），所以
   "未知路径 + mutating + 无 key" 在真件上回 **422 而不是 404**；替身照抄这个顺序才叫同语义。
5. **刻意不一致要写出来**：摘要只做"同/不同"判等（不追求与真件 sha256 逐字节一致）、
   重放不带 ETag——两条都写进模块 docstring，不假装逐字相同。

## 怎么做与复现

```bash
# 契约用例（4 条：缺头 422 / 分析类免 key / 同 key 不同 body 422 / 同 key 同 body 重放）
pnpm --dir apps/web exec playwright test --config playwright.config.ts stub-idempotency.spec.ts

# 跨语言词表守卫
python -m pytest tests/tooling/test_console_stub_idempotency_parity.py -q     # 2 passed

# 客户端反证：把 http.ts 的 headers.set("Idempotency-Key", ...) 改成别的头名后
pnpm --dir apps/web exec playwright test --config playwright.config.ts \
  schedules-write.spec.ts project-delete.spec.ts      # 期望 7 failed（随后必须还原）
```

要点：**用 `page.evaluate(fetch(...))` 发原始请求**——`page.request` 不经过 `page.route`，
抓不到替身；`stubApi()` 每次要 `resetIdempotencyStub()`，否则重放存储跨用例污染。

## 适用边界（踩过的坑）

- **不要用 `page.request` 测替身**：它绕过路由拦截，看起来"请求成功了"，其实根本没到替身。
- **重放用例要有真实副作用**：用 `POST /api/ops/schedules`（重名会 409）才能区分
  "重放首次响应"与"真的又建了一遍"；用无副作用的端点等于没测。
- **守门顺序削弱 `assertNoUnmatched`**：未知路径 + mutating + 无 key 现在回 422，
  不再进未匹配清单。这是真件行为，但"手滑写错路径"在缺 key 时不会以 404 的形式被抓到。
- **替身摘要不可当证据**：它只是 `method\npath\nbody` 的拼接，不是真件的 sha256 摘要。

## 来源

- PLAN-20260915-068 / RECHECK-20260915-068（GOAL-20260915-003 cycle 6 / EC-05）。
- 相关：[[MEM-20260915-039]]（安装 pin 必须由控制面重算 digest——同族"自洽 ≠ 与上游一致"）、
  [[MEM-20260915-040]]（待批准必须在 UI 可见——同族"状态必须能被消费方看见"）。
