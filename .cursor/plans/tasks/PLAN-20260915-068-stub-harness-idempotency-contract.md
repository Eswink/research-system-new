---
id: PLAN-20260915-068
slug: stub-harness-idempotency-contract
title: 替身 harness 校验 Idempotency-Key（EC-05）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 6 = EC-05（替身 harness 校验 Idempotency-Key：缺头 → 422 与真中间件同语义）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-068-stub-harness-idempotency-contract.md
memory_entries:
  - MEM-20260915-043-stub-must-enforce-the-contract-it-stands-in-for
---

# PLAN-20260915-068 — 替身 harness 校验 Idempotency-Key（GOAL-003 cycle 6 / EC-05）

## 目标

让 stub 套件**自己**能证伪客户端漏发 `Idempotency-Key`，而不是把这条契约全部押在 live 套件上。

```text
今天：  stub 完全不看请求头 → 客户端漏发 key，33 条 stub 用例照样全绿
        （只有 live 套件能发现，而 live 要真实 uvicorn + SQLite，覆盖窄、代价高）
本轮：  替身在 handler 之前守门，与真中间件同语义四条 → 漏发 key 的客户端在 stub 上就红
```

## 口径（这轮最容易做错的地方）

1. **不是"打个标记"，是逐条对齐真件**：缺头/空值 → 422
   `Idempotency-Key Required`；同 key + 不同摘要 → 422 `Idempotency-Key Reused`；
   同 key + 同摘要 → **重放首次响应**（不触发第二次状态变更）；分析类 POST 豁免。
   响应体与真件 `_problem()` 同形状（`type/title/status/detail/instance`，`instance` 是**空串**）。
2. **词表用跨语言守卫钉住**：stub 的 `MUTATING_METHODS`/`ANALYSIS_ACTIONS` 与
   `services/api/middleware.py` 的 `_MUTATING_METHODS`/`_ANALYSIS_ACTIONS` 必须逐项相同。
   替身与真件的关系是"同一条契约的两个实现"，词表漂移必须在 Python 套件里红——
   否则替身会悄悄放宽，而放宽的替身比没有替身更危险。
3. **反证必须落在客户端上**：只证明"替身会回 422"是不够的（那是替身自己的单元测试），
   要证明**产品客户端**漏发头时套件会红。做法：临时把 `apps/web/src/api/http.ts` 的
   发送改成别的头名，跑 mutating 用例 → 必须失败；随后还原，工作树不留 diff。
4. **守门顺序与真件一致**：中间件在路由之前（`BaseHTTPMiddleware` 包住 router），
   所以"未知路径 + mutating + 无 key"在真件上也是 422 而不是 404。替身照此顺序：
   先判 key，再判路由（这条顺序会削弱 `assertNoUnmatched` 对该情形的作用，但那是
   真件的真实行为，不是替身的偷懒——写进 RECHECK 告警）。
5. **诚实登记两处刻意不一致**，不假装逐字相同：摘要只做"同/不同"判等（不追求与真件
   sha256 逐字节一致，两者不共享存储）；重放响应不带 `ETag`（真件会回放存储的 ETag，
   替身的响应体里没有它）。
6. **不改真件**：`services/api/middleware.py` 是权威实现，本轮零改动——替身向真件对齐，
   不是真件向替身对齐。

## 范围

- 新增：`apps/web/tests/e2e/stub-idempotency.ts`（契约实现 + 票据类型 + 逐测试重置）、
  `apps/web/tests/e2e/stub-idempotency.spec.ts`（4 条用例）、
  `tests/tooling/test_console_stub_idempotency_parity.py`（词表 + 响应形状守卫，
  同族先例 `tests/tooling/test_console_toolpack_fixtures.py`）。
- 修改：`apps/web/tests/e2e/stub-api.ts`（`stubApi()` 里重置替身存储；handler 之前守门；
  handler 之后记账）。
- **不改**：`services/api/middleware.py`（真件）、`apps/web/src/api/http.ts`
  （只在反证实验里临时改、随后还原）、`apps/web/src/` 任何产品代码。

## 验收条件

- [x] AC-01：缺 `Idempotency-Key` 的 mutating 请求在替身上得到 **422**，响应体与真件
  `_problem()` 同形状（五字段，`instance` 为空串）。
  ——第 1 条用例对 `POST /api/projects` **逐字段**断言完整 body；与 `middleware.py::_problem()` 源码对照。
- [x] AC-02：mutating 词表四方法（POST/PATCH/PUT/DELETE）全覆盖：POST / DELETE / PATCH
  各有一条真实请求作背书，集合本身由 parity 守卫钉住。
  ——同一条用例里 POST（`/api/projects`）、DELETE、PATCH（`/api/projects/:id`）分别拿到 422；
  `PUT` 在 console 面无真实路由，只有词表守卫覆盖（RECHECK-068 W-4）。
- [x] AC-03：分析类 POST **豁免**（`validate`/`compile`/`preflight`/`dry-run`/`test`/
  `discover-models`/`probe` 无业务写入），不因缺 key 被拒。
  ——第 2 条用例对 `/api/llm-endpoints/:id/test` 断言"不是 422、title 不是 Idempotency-Key Required"。
- [x] AC-04：同 key + **不同**请求摘要 → 422 `Idempotency-Key Reused`。
  ——第 3 条用例：两个不同 body 的 POST 用同一 key，第二次 422 且 title 命中。
- [x] AC-05：同 key + **同**摘要 → 重放首次响应，**不触发第二次状态变更**。
  ——第 4 条用例用 `POST /api/ops/schedules` 证明：若替身没有重放语义，第二次会真的再建一遍
  并命中重名 409；实测第二次仍是 201 且 body 与首次逐字相同 ⇒ 重放而非重做。
- [x] AC-06：**客户端反证**——把产品客户端的头发送去掉后，mutating 的 stub 用例必须失败。
  ——见 WP-C：`schedules-write` + `project-delete` **7 failed / 2 passed**，
  失败页面上呈现的正是真件的 422 detail `mutating requests require Idempotency-Key`。
- [x] AC-07：词表与真件同步守卫（跨语言）：stub 的 `MUTATING_METHODS`/`ANALYSIS_ACTIONS`
  与 `services/api/middleware.py` 逐项相等，且豁免清单非空（防空集合让"豁免"退化成"全部豁免"）。
  ——`tests/tooling/test_console_stub_idempotency_parity.py` **2 passed**。
- [x] AC-08：全量 stub 套件绿 + web 门（lint/typecheck/unit/build）+ 根 TS 门 + m0 23 项。
  ——stub 套件 **81 passed (4.5m)**；根 eslint 与 `tsc -p apps/web/tsconfig.json` 空输出；
  m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3595 passed / 10 skipped**）。
- [x] AC-09：记录（RECHECK-068 + MEM + GOAL 记账），两处刻意不一致与守门顺序写进 RECHECK 告警。
  ——RECHECK-068（PASS_WITH_WARNINGS，W-1~W-5）+ MEM-20260915-043 + EXP-20260916-001 + GOAL 记账。

## 实施清单

- [x] WP-A 替身契约实现（`stub-idempotency.ts`：词表 / `problem()` / 票据 / 重放存储 / 重置）
- [x] WP-B 接线（`stub-api.ts` 守门 + 记账）与用例（4 条，含重放"不二次改状态"的构造）
- [x] WP-C 客户端反证实验（去掉发送 → 期望红 → 还原，工作树零残留）
- [x] WP-D 跨语言 parity 守卫（词表 + 响应形状）
- [x] WP-E 全量门禁（stub 套件 / web 门 / m0 23）
- [x] WP-F 记录（RECHECK-068 + MEM-043 + EXP-001 + GOAL 记账 + 收口提交 → CI 六 job）

## 证据

**WP-A/B（契约与用例）**

```text
$ npx playwright test --config playwright.config.ts stub-idempotency.spec.ts
4 passed (19.3s)
# 1) 缺 key：POST /api/projects 逐字段等于真件 problem body；DELETE、PATCH 同 422
# 2) 分析类 POST 免 key：/api/llm-endpoints/:id/test 不被拒
# 3) 同 key 不同 body → 422 Idempotency-Key Reused
# 4) 同 key 同 body → 重放首次响应（否则第二次会撞重名 409）
```

**WP-C（客户端反证：去掉发送头 → 套件红）**

```text
$ # 临时把 http.ts 的 headers.set("Idempotency-Key", ...) 改成错误头名后：
$ npx playwright test --config playwright.config.ts schedules-write.spec.ts project-delete.spec.ts
7 failed
   tests\e2e\project-delete.spec.ts:47:1 › 有引用的项目：删除被拒并呈现引用清单，行保留
   tests\e2e\project-delete.spec.ts:56:1 › 无引用项目：删除后从注册表消失
   tests\e2e\project-delete.spec.ts:67:1 › 删除活动项目后活动上下文回退到默认项目
   tests\e2e\schedules-write.spec.ts:35:1 › 登记：新定义出现在表里，运行事实诚实为「未运行」
   tests\e2e\schedules-write.spec.ts:45:1 › 触发：运行事实在读到的那一行上变化（写面被读面消费）
   tests\e2e\schedules-write.spec.ts:55:1 › 启停：停用后启用位翻转，且触发按钮禁用
   tests\e2e\schedules-write.spec.ts:74:1 › 服务端拒绝（重名 409）落在面板内，不是静默失败
  2 passed (1.6m)
# 失败页面上呈现的正是真件的 422 detail（UI 把 problem 原文显示在面板内）：
#   - alert: generic "mutating requests require Idempotency-Key"
$ git diff --stat apps/web/src/api/http.ts     # 还原后：无输出（工作树零残留）
```

**WP-D（跨语言 parity 守卫）**

```text
$ python -m pytest tests/tooling/test_console_stub_idempotency_parity.py -q
2 passed in 0.39s
```

**WP-E（全量门禁）**

```text
$ pnpm --dir apps/web exec playwright test --config playwright.config.ts
81 passed (4.5m)                       # 77 既有 + 4 新增；零失败（两次独立运行同为 81 passed）

$ npx eslint apps/web/tests/e2e/stub-idempotency.ts \
    apps/web/tests/e2e/stub-idempotency.spec.ts apps/web/tests/e2e/stub-api.ts
（无输出 = 0 error 0 warning）        # 首轮 m0 的 typescript/lint 判红 10 error，见「状态历史」

$ npx tsc --noEmit -p apps/web/tsconfig.json
（无输出）                             # exactOptionalPropertyTypes / noUncheckedIndexedAccess 会拒 `body: string | undefined`

$ python -m pytest tests/tooling/test_console_stub_idempotency_parity.py -q
2 passed

$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks
# 全量 pytest：3595 passed, 10 skipped（460.66s）
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 5（EC-04 worker SIGTERM 有界退出）闭环后按 EC 表
  顺序取 EC-05。derive 时的关键判断：**反证对象必须是产品客户端**——只证明"替身会回 422"
  等于替身自己测自己；真正的风险是客户端漏发头而 stub 放行，所以必须有"去掉发送 → 套件红"
  的实验，否则这条 EC 只能算装饰。
- 2026-09-16 WP-A/B 完成：`stub-idempotency.ts` 实现四条语义（缺头 422 / 同 key 不同摘要 422 /
  同 key 同摘要重放 / 分析类 POST 豁免），`stub-api.ts` 在 `match()` **之前**守门、`handler()`
  **之后**记账；4 条用例全绿。**刻意保留的两处不一致**（摘要只判等、重放不带 ETag）写进
  模块 docstring，不假装与真件逐字相同。
- 2026-09-16 WP-C/D 完成：反证实验在**产品客户端**上做——临时改 `http.ts` 的头发送后，
  `schedules-write` + `project-delete` **7 failed / 2 passed**，失败页面里呈现的正是真件的
  422 detail（说明这条契约现在能在 stub 层被证伪）；随后还原，`git diff` 为空。
  parity 守卫（2 passed）把 stub 词表与 `middleware.py` 钉在一起，防止替身单方面放宽。
- 2026-09-16 WP-E 完成（含两处门禁拦截）：全量 stub 套件 **81 passed (4.4m)**。首轮 m0 在
  `typescript/lint` 判红 **10 个 error**（`max-params` 两处：`call` 5 参、`beginMutation` 4 参；
  `no-restricted-syntax` 的内联 import type；`dot-notation` 四处 `body["title"]`；
  `no-unnecessary-condition` / `no-unnecessary-type-conversion` 各两处）——`apps/web` 自己的
  lint 只覆盖 `src`（且对 `tests/**` 有放宽），根配置 `eslint .` 才覆盖 `apps/web/tests/**`。
  按规则**改代码**（参数表收敛为 options 对象、顶层 `import type`、点号访问、去冗余判断），
  **未动任何 eslint 配置、未加 disable 注释**；接着 `tsc -p apps/web/tsconfig.json` 又暴露两处
  （元组推断成 `string[]` ⇒ 解构出 `string | undefined`；`body: string | undefined` 不可赋给
  `RequestInit`（`exactOptionalPropertyTypes`））⇒ 显式四元组类型 + 条件式装配 `RequestInit`。
  修完后三文件 eslint/tsc 空输出，全量 stub 套件重跑 **81 passed (4.5m)**，m0
  **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3595 passed / 10 skipped**）。
- 2026-09-16 WP-E 的一次证据采集失误（已纠正）：第一次后台跑 stub 套件时把它 `TaskStop` 了，
  遗留的 `npx playwright test` 子进程与第二次运行**共用同一日志文件**，产出一份 ok 与 x/-
  混杂、不可判读的日志 ⇒ 按 PID `taskkill //T //F` 清理后用唯一文件名重跑（单表头、
  81 passed）。教训记为 EXP-20260916-001；**本 PLAN 的 81 passed 取自重跑后的单头日志**。

## 影响报告

- **Domain/API/schema**：零产品变化——本轮只动测试替身与一个测试守卫；真中间件
  `services/api/middleware.py` 未改，OpenAPI 未重生成，契约套件无需更新。
- **安全/凭据**：无凭据面变化。替身不引入任何新的网络/存储面（重放存储是进程内 Map，
  逐测试重置）。Mimosa deep scan `scan-2026-09-16T12-35-44.199Z-b806ba6e28cc`
  （seal `sha256:d15c0a99c4c08a2237fc9b53e544eebe45b19d899a6714faa193125c26d32998`）：
  36 findings（3 high / 28 medium / 5 low）、182 packages，计数与 cycle 4/5 逐项一致；
  **本轮四个改动文件零命中**。
- **测试面（本轮的实质影响）**：stub 套件从"不看请求头"变成"守 mutating 契约"。
  任何未来漏发 `Idempotency-Key` 的客户端改动现在会在 stub 层红，而不是等到 live 层。
  代价：新增一条跨语言守卫（读一个 TS 文件的正则），无运行时代价。
- **兼容性/迁移风险**：既有 77 条 stub 用例全部通过（客户端本来就发头，见 WP-C 反证）；
  没有任何既有断言被放宽。替身多了一个进程内 Map，`stubApi()` 每次重置。
- **可观测性**：无。
- **下一项任务**：EC-06（每 cycle m0/CI 全绿 + 收口复检 + 安全扫描处置），以及
  EC-02 剩余子句（provider 侧健康复核 schema digest 漂移 + 凭据绑定、RECHECK-065 W-1
  的 `tool_pack.*` 策略产品决策）。

## 已知风险

- **替身重放不带 ETag**：真件回放存储的 ETag，替身没有。若将来有用例断言"重放响应带
  首次 ETag"，它只能在 live 层被证明——这条差异已写进模块 docstring 与 RECHECK-068 W-2。
- **摘要口径不共享**：替身用 `method\npath\nbody` 做判等，真件用 sha256 摘要。
  两者对"同/不同"的判定一致（同一输入同一结果），但**跨实现不可互换**——不要把替身
  的摘要当成真件摘要的证据（W-1）。
- **守门顺序削弱 `assertNoUnmatched`**：未知路径 + mutating + 无 key 现在回 422 而不是
  进未匹配清单。这是真件的真实行为（中间件在路由之前），但会让"手滑写错路径"这类问题
  在缺 key 时以 422 的形式出现，而不是以 404 的形式被 harness 抓住（W-3）。
