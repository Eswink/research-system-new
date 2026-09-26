---
id: MEM-20260926-147
title: "前端凭据存储被既有安全判据收窄为内存；三态实跑必须走**应用自己的请求层**，否则测的是夹具不是产品"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-197-console-token-input-and-write-face-carry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-198-console-token-three-states-recheck.md
supersedes: []
tags: [frontend-credential, storage-decision, e2e-driving, goal-020, ec-01, three-states, pressable]
---

## 做了什么

给控制台前端加了**写面 token 输入面**（设置页「控制面连接」分区）+ 在**唯一请求层**
（`apps/web/src/api/http.ts` 的 `buildHeaders`）对**写请求**注入
`Authorization: Bearer <token>`，并跑通**三态实跑**与**成对反证**（GOAL-020 EC-01）。

## 为什么这样做

### 1. 存储方式的决策与理由（三选一，本仓实测后选**内存**）

| 选项 | 结论 | 理由 |
| --- | --- | --- |
| `localStorage` | **不可取** | `tests/api/test_security_scan.py:79-91` 对 `apps/web/src/**/*.ts*` **无条件**断言不出现 `localStorage.setItem` / `sessionStorage.setItem`，其**自述意图**是「前端持久层无 secret 写入」。用它要么放宽该既有安全判据、要么用「惰性访问器」绕开**字面量**检查——后者是**绕过**，命中 `fix_policy.forbidden` |
| `sessionStorage` | **不可取** | 同上的字面量断言同时覆盖它；且它同样可被同源脚本读取（XSS 面与 localStorage 同级），仅生命周期短一些 |
| **内存（选定）** | **取** | token 不进任何可持久化面（含 XSS 可读的持久层） |

**XSS 面（如实记录）**：内存态**同样**可被同源脚本读取——任何浏览器内方案都如此；
差别在**持久性**：内存态在页面关闭 / 刷新后消失，磁盘上不留副本。

**代价（如实记录）**：**刷新即失**，操作者需重新粘贴。这是本轮**选定**的代价，
不是被忽略的缺陷。

### 2. 三态实跑必须走**应用自己的请求层**

第一版驱动用 `page.evaluate(fetch(...))` 直接发请求 ⇒ **丙态必然失败**：
裸 `fetch` 绕过 `buildHeaders`，当然不带 token。这暴露一条通用纪律：
**「前端携带凭据」的判据必须经应用自己的请求路径**（本仓 = 领域 client → `request()` →
`buildHeaders`），否则测的是驱动脚本，不是产品。

**落地形态**：驱动改为操作**应用界面**——设置页「工作区」分区里「默认模型 Profile」那一行的
「保存此项」按钮（该行经 `useSettingsSave` → `api.saveProjectSettings` → `request()`）。

**教训**：三态里「有 token ⇒ 成功」这一态**只有**经应用路径才有意义；
用裸 `fetch` 测出来的红/绿都不可信。

### 3. 判「携带 / 成功」要看**响应**，不要抓页面文案

第二版驱动用「页面上有没有 `Authentication Required` 文案」判失败 ⇒ **假红**：
该文案会**残留**自上一次失败。改为监听 `page.on("response")`，按
`PUT /api/projects/*/settings` 的**实际状态码**与**请求头**判定——一手事实，不靠文案。

### 4. 既有安全判据是**子串**扫描 ⇒ 文档里写被禁 API 会判红

`test_security_scan.py` 不解析注释：模块**文档注释**里为了说明「为什么不选 localStorage」
而写出 `localStorage.setItem` ⇒ **该判据判红**。修法是把说明改成**不含该调用形态**的措辞
（"浏览器存储的写入调用"），而**不是**改判据。同类坑：新判据若断言「源码含某词」也会被
自己的注释喂饱 ⇒ 本轮的单元判据**先剥注释再判**（`stripComments`，用 `indexOf`/`slice`）。

## 怎么做与复现

```bash
# 三态实跑 + 成对反证（对真实 FastAPI + 真实 vite；token 现场生成、只走 env）
uv run --frozen --no-sync python -B scratch/goal020-ec01-three-states.py
# 前端六门
pnpm --dir apps/web lint ; pnpm --dir apps/web typecheck ; pnpm --dir apps/web test
pnpm --dir apps/web build ; pnpm --dir apps/web test:e2e ; pnpm --dir apps/web test:e2e:live
# 既有安全判据（必须零改动且绿）
uv run --frozen --no-sync python -B -m pytest tests/api/test_security_scan.py -q
```

## 适用边界

- **内存态不是访问控制**：`THREAT_MODEL.md` §6.3 第 3 条明写前端可见性**不是**控制；
  唯一控制点是服务端中间件。本输入面只负责「让开启认证后的写操作可用」。
- **读面永不携带 token**：前端只在 `_MUTATING_METHODS` 同集合（POST/PATCH/PUT/DELETE）
  上注入；GET 不带（后端读面不认证）。
- **两处 GET 例外不需要 token**：`artifactClient` 的裸 `fetch` 与 `EventSource`（SSE）
  都是读面；`EventSource` 也**无法**设自定义头（浏览器 API 限制）。
- **刷新即失是选定代价**，不是遗留缺陷；若将来要持久化，**必须先另行授权**
  （那意味着动 `test_security_scan.py` 的口径）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-197-console-token-input-and-write-face-carry.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-198-console-token-three-states-recheck.md`
- 脚本：`scratch/goal020-ec01-three-states.py`（三态 + 成对反证，逐字节还原）
- 相关记忆：`MEM-20260926-146`（记录面覆盖是机械事实）、`MEM-20260926-145`（门压在记录之前）
