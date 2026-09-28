---
id: RECHECK-20260929-242
slug: goal-025-ec03-whitelist-contract-derivation
title: GOAL-025 EC-03 复检：读面白名单的契约派生与两向差异清单（含三条独立路径互钉、按压与逐字节复原）
plan_id: PLAN-20260929-241
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-242 — GOAL-025 EC-03 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`），
关键数字用**不经被检模块**的第二条路径重算一遍。**未实跑的不记通过**；警告逐条留位。

## 检查结果

### 1. 派生面存在且非空（AC-1）
- 交付：`tests/observability/read_face_whitelist_derivation.py`（**128 行**）+
  `test_privacy_read_face_whitelist_derivation.py`（**124 行 / 10 例**），实跑 **10 passed**。
- **独立重算（不经被检模块）**：直接 `json.loads(docs/api/openapi.m13.json)` 数 GET =
  **64** 条；正则 `FrameworkRoute\(\s*"(/…)"` 数框架登记 = **4** 条（`/docs`、
  `/docs/oauth2-redirect`、`/openapi.json`、`/redoc`）⇒ 派生面 **68** 条，与判据内自算一致。
- **下界**：`MIN_DERIVED = 40`。按压 P2（把派生根从 GET 改成 PATCH）实测判红
  `快照里的 GET 只有 9 条 < 下界 40` ⇒ 「快照读不到 / 变空」**不会**退化成「无差异 ⇒ 通过」。
- **权威面本身受门钉住（实跑复核）**：`tests/contracts/test_openapi_snapshot.py` **8 passed**
  （该门重新生成快照并与提交前的字节逐字比对）⇒ 「快照不会静默漂移」这句话**在本次运行里成立**。

### 2. 两向差异清单（AC-2）
- 判据内：`derivation_findings`（下界自审 + 两向差分）进失败消息；本轮实测**两向差异 = ∅**。
- **独立重算**：用正则 `ReadRouteRule\(\s*"(/…)"` 直接数 `read_face_route_registry.py` 的
  登记路径（**不 import** 被检模块）= **68** 条，无重复登记；
  `(快照 ∪ 框架) − 清单 = ∅`、`清单 − (快照 ∪ 框架) = ∅` ⇒ 与判据结论一致。
- **反证两向**：R1 清单多一条 `/__extra` ⇒ 判红点名；R2 清单少一条 `/health` ⇒ 判红点名；
  R3 快照读不到（空目录）⇒ 下界判红。三条都在判据内，**不碰源码树**。

### 3. 三条独立路径互钉（AC-3）
- ①**提交的快照**（受 `test_openapi_snapshot.py` 逐字节门钉住）× ②**实时 schema**
  （`app.openapi()`）× ③**运行时路由树**（`read_routes(app)`，含 `_IncludedRouter` 拆包）
  —— 三向差分全为 ∅；实时与快照不一致 ⇒ 判红「快照可能过期」（按压 P2 实测该判据同时判红）。
- R4（判据内，真实应用）：往 `face.app` 挂一条读路由 ⇒ 实时 schema 立刻与快照差异并**点名**该路由。

### 4. 按压、复原与终态（AC-4）
- **按压（源码级，先红后绿）**：P1 框架清单塞入清单里没有的 `/__bogus-frame` ⇒
  `读面白名单与契约派生面不一致:['派生面有而清单没有:/__bogus-frame']`（连带 2 例，3 failed）；
  P2 派生根 `GET`→`PATCH` ⇒ `快照里的 GET 只有 9 条 < 下界 40` + 两向差异长清单（5 failed）；
  P3 两向差异只留一向 ⇒ `test_an_extra_registry_entry_is_red` 判红（**清单陈旧那一向是承重的**）。
- **逐字节复原（承 MEM-152）**：三处均以 Edit 施加 / 复原；`sha256` 用**二进制读**、证据用
  **二进制写**盘；复原后回到 `ae9bf121fdc4f4b1ae15e488d13d8f1707bc2b9a4dce5ef7bc12e6ed1f3aa888`
  （`MATCHES_BASELINE True`），复绿 **10 passed**。证据：`scratch/goal025-ec03-press-matrix.log`
  （4 599 B、`CR` 计数 **0**）。
- **四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` =
  `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；
  规模 **128 / 124 行**（≤450；函数 ≤50 由规模门覆盖），规模门定向跑 **1058 passed**。
- **既有判据逐字节未改**：`git status --porcelain -- tests/observability` 只列出本轮**两个新增**文件
  （无 `M`）；新判据**无 `skip` / `xfail`**（grep 命中 0）；`tests/observability/` 全目录
  **134 passed, 1 skipped**（cycle 2 后为 124 + 1 ⇒ **+10** 恰为本轮新判据）。
- `m0` / 治理 / CI 台账：见 PLAN-20260929-241 的「证据」与 GOAL 迭代日志（**记录写入之后**才跑）。

## 结论

**PASS_WITH_WARNINGS**。EC-03 的三条验收（派生面非空 + 两向差异逐条判定 + 三条独立路径互钉）
**全部有实跑证据**；GOAL-024 的残余 `G24-3`（「白名单是人工判定 + 机械自审，**不是**从契约派生」）
在本轮**收窄为「路径集合已可从权威契约面派生且当下零差异」**，分类面与语义面**仍属人工判定**。

**警告（如实留位，不消解）**：

- `W-1`：派生证明的是**路径集合**的可派生性（集合相等），**不**证明**分类**（`declared_content` /
  `zero_hit`）可派生 —— 分类仍属 GOAL-024 的人工判定 + 机械自审；本轮**不**声称分类面已被契约覆盖。
- `W-2`：框架那一半（4 条）是**人工登记**而非自动派生，且上界写死 `len(FRAMEWORK_ROUTES) == 4`；
  新框架路由必须人工同步（会同时撞「运行时路由树 == 派生面」与「框架路由必须进人工清单」两条判据）。
  **登记一条不存在的路由**会被运行时路由树相等判据挡住 ⇒ 不能靠登记伪造读面。
- `W-3`：权威面只覆盖**应用声明的 GET 路径**：不覆盖 HEAD / OPTIONS 等其它方法，
  也不证明「这些 GET 路由一定返回内容」（后者由 GOAL-024 的实取 + 内容金丝雀面负责）。
- `W-4`：运行时路由树的叶子过滤是「`methods` 含 `GET`」⇒ 若某路由**同时**提供 GET 与写方法，
  它会被算进读面（本仓当前无此形态；将来出现时本判据**不区分**「纯读」与「兼有 GET」）。
- `W-5`：真实应用按压例（R4）**依赖文件内用例顺序**（跑在两条使用同一模块级 `face` 的检查之后）：
  它往共享 app 上挂了一条只存在于内存的路由。若将来引入随机顺序 / 重排，需把该例改成独立 app 实例。
- `W-6`：快照的权威性**依赖** `tests/contracts/test_openapi_snapshot.py` 的重生成门当前在位
  （本轮实跑 8 passed 复核）；若那道门被放宽或移除，本判据的「权威」前提随之失效。
- `R-M1` 未收口：**不得**据此宣称项目安全；本复检只覆盖被点名判据在本机默认离线链上跑到的那几面。
