---
id: RECHECK-20260926-198
slug: console-token-three-states-recheck
title: GOAL-020 cycle 2（EC-01）独立复检：三态实跑 + 成对反证 + 存储决策 + 凭据纪律 + 关闭态对照
plan_id: PLAN-20260926-197
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-198 — 前端 token 输入与携带（GOAL-020 EC-01）

## 检查结果

**复检口径**：不复用 PLAN 的结论叙述；每一项给出**可复核观察面**（命令、脚本、状态码、日志）。
**未实跑的不记通过**。授权与边界见 GOAL-020 frontmatter。

### 一、三态实跑（甲 / 乙 / 丙）—— 对**真实** FastAPI + **真实** vite 前端

**观察面**：`scratch/goal020-ec01-three-states.py`（现场生成 token，只经 `env=` 传入
uvicorn 子进程；打印掩码）。三态都在 `tests/api/console_api_app`（真实装配、Fake Ports）
+ `pnpm run dev`（真实 vite，`/api` 代理到该 app）上跑；**写操作经应用自己的请求层**
（设置页「工作区」→「默认模型 Profile」行的「保存此项」→ `request()` → `buildHeaders`）。

| # | 状态 | 观测（该次写请求） | 结论 |
| --- | --- | --- | --- |
| 1.1 | **甲 认证关闭** | `PUT …/settings` **200**、`authorization=null`、状态位「未配置」 | 写操作**成功**且**不带**凭据 ⇒ 关闭态与基线一致 |
| 1.2 | **乙 认证开启 + 无 token** | `PUT …/settings` **401**；设置页可见、token 输入面可见、说明文字可读；**零 `pageerror`** | **如实呈现「需要认证」**（非空白 / 非崩溃） |
| 1.3 | **丙 认证开启 + 经界面填 token** | 前置 401 → 经输入面保存 → 状态位「已配置」→ `PUT` **200**、`authorization` **非空**、输入框清空、页面 HTML 不含明文 | 写操作**可用** |

**三态汇总**：`5/5 符合预期`（含下面的反证与复原；摘要 `scratch/goal020-ec01/three-states-summary.json`）。

### 二、成对反证（先绿后红，再逐字节复原）

| # | 动作 | 观测 | 结论 |
| --- | --- | --- | --- |
| 2.1 | 在 `http.ts` 把注入条件改成 `if (false && …)`（**锚点唯一命中**校验通过） | 丙态 `PUT` ⇒ **401**（`auth=null`），用例**退出码 1** | 红**确实由「去掉注入」引起** |
| 2.2 | 逐字节还原 | sha256 `e4b004a3fe23f9e5` 前后一致 | 还原**无残留** |
| 2.3 | 复原后复跑丙 | `PUT` **200**、`authorization` 非空、退出码 0 | 绿 |

### 三、存储方式的决策与理由（三选一）

**选定：内存**（`apps/web/src/api/controlPlaneToken.ts`）。理由与代价逐条见
`MEM-20260926-147`；要点：`tests/api/test_security_scan.py:79-91` 对 `apps/web/src/**`
**无条件**断言无 `localStorage.setItem` / `sessionStorage.setItem`（自述意图 = 前端持久层无
secret 写入）⇒ 选浏览器持久层要么放宽既有安全判据、要么用惰性访问器**绕过**字面量检查
（后者命中 forbidden）。**代价（如实记录）**：**刷新即失**。**XSS 面**：内存态同样可被
同源脚本读取，差别在**持久性**（磁盘不留副本）。

### 四、凭据纪律（grep 反证）

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | 全仓搜 `RESEARCHOS_CONTROL_PLANE_TOKEN` | 命中**均为变量名 / 文档用法**：`services/api/middleware.py:127`（常量定义）、四处文档、前端 i18n 文案、同源判据的常量表 ⇒ **零值** |
| 4.2 | `apps/web/src` 搜 `Bearer <长串>` 形态 | **零命中** |
| 4.3 | `apps/web/src` 搜 `localStorage.setItem` / `sessionStorage.setItem` | **零命中** |
| 4.4 | `tools/credential_audit.py`（四面） | `tracked offenders=0` / `records offenders=0` / `config_db 0` / `logs 0` ⇒ **PASS** |
| 4.5 | `tests/api/test_security_scan.py` | **6 passed**，且 `git diff` **零改动**（判据未被放宽） |
| 4.6 | 脚本自身 | token **现场生成**、只经 `env=` 传递、打印掩码；**不落盘**（脚本不写任何 token 文件） |

### 五、关闭态逐字不变（AC-5）

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | 甲态请求头 | `authorization=null`；既有头（`Idempotency-Key` / `Content-Type` / `Accept`）不受影响 |
| 5.2 | 单元判据 | 新增用例断言「未配置 token 时写请求**不加空头**」且 `Idempotency-Key` 仍在 |
| 5.3 | stub e2e | **98 passed**（与基线**同计数**） |
| 5.4 | live e2e（认证关闭） | **53 passed**（与基线**同计数**） |
| 5.5 | 其余门 | `lint` / `typecheck` / `test`（**94 passed**）/ `build` 全绿 |

### 六、设计基线（AC-6）

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 结构签名漂移面 | **仅 `settings` 一条**（`nav label=设置分区 kids=5 → 6` + 新增按钮「控制面连接」）；**其余 33 条未动** |
| 6.2 | 处置 | 按既有流程 `UPDATE_OUTLINES=1` 重生成 + **目检 diff**（与意图逐字相符），**未调任何容差** |
| 6.3 | 像素基线 | `design-fidelity` 的 68 张基线**未漂移**（settings 截图阈值内）⇒ **未**重生成像素基线 |

## 结论

**PASS_WITH_WARNINGS**。EC-01 的六条验收条件全部有实跑证据：三态（**甲 200/无头**、
**乙 401 且如实呈现**、**丙 200/带头**）、**成对反证**（去掉注入 ⇒ 401 ⇒ 判据红；sha256 逐字节
还原 ⇒ 复绿）、**存储决策三要素落记录**、**凭据纪律零命中**、**关闭态与基线同计数**、
**设计基线漂移仅一条且已按流程重生成**。

**警告**（不影响 PASS）：

- **W-1｜「刷新即失」是选定代价**：内存态意味着刷新后需重新粘贴；若要持久化，
  必须先**另行授权**（那会触及 `test_security_scan.py` 的口径）。
- **W-2｜三态是**本机**实跑**：CI 的 `console-frontend` job 跑的是**认证关闭**态
  （既有 stub + live 套件）；**开启态**的三态证据来自本机脚本，
  **未**进 CI 判据（本轮不改 workflow 结构）。
- **W-3｜前端输入面不是访问控制**：如 `THREAT_MODEL.md` §6.3 第 3 条所述；
  本面只解决「开启认证后可用」。
- **W-4｜两处 GET 例外不携带 token**（裸 `fetch` 取制品原文、`EventSource` SSE）——
  两者都是**读面**，后端不认证 ⇒ 无需凭据；`EventSource` 亦**无法**设自定义头。
- **W-5｜本复检与实施同轮**：独立结论以 GOAL-020 收口轮的两树复检为准（承 GOAL-019 口径）。
- **W-6｜`problemText` 的 401 指引是双语同句**（该函数不带 i18n 上下文，20+ 写面板共用）；
  若将来要按语言分支，需改调用点契约——**本轮不宣称**它已本地化。
