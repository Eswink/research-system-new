---
id: GOAL-20261013-072
slug: routes-without-declared-query-params-also-refuse-them
title: >-
  未声明查询参数的路由也不再静默吞掉查询参数 —— 序 37/38 做了「已声明」的读面
  （签名导出 + 9→10 条）、序 39 做了写面，而**实测**：全仓 **58 条 GET** **未声明**任何查询参数，
  其中收到查询串时**照样 200**（`/projects?definitely_unknown=1` ⇒ 200；`/health?zz=1` ⇒ 200）
  ⇒ 调用方**以为设了筛选**而拿到全量 —— 这是「静默吞掉」族**最后一面**。本轮把它接通：
  「未声明参数」的读面收到**任何**查询参数 ⇒ **422 + 逐个点名**（并明写该路由不接受查询参数），
  **缺省形态逐字不变**（不传参数 ⇒ 一字不动）
status: ACTIVE
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-13 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 40**，由本次**实测缺口**驱动（序 39 收口后盘账）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑** ⇒ 未声明查询参数的 GET 路由收到
    查询串时**照样 200**（`/projects?definitely_unknown=1` ⇒ 200；`/health?zz=1` ⇒ 200）；
    这个面**被序 37 与序 38 两轮显式登记为「另成一面」的后续候选** ⇒ 本轮把它接通。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 「静默吞掉」族已连接通三面
    （读面已声明 37/38、写面 39），**仅剩**「读面未声明」这一面仍静默。
    (3) **本 GOAL 只做这一条**（不做数量目标）：`services/api/query_param_guard.py` 的
    `declared_query_params` 已经用 `None`（不在射程）与空集（读面但无参数）**区分**了两种
    「跳过」—— 本轮把**空集**那一支从「跳过」改成「有任何查询参数 ⇒ 422 + 逐个点名」，
    `None`（非读面）支**一字不动**。**已知/缺省形态逐字不变**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**动写面（序 39 的 DTO 纪律由收口断言集钉住）；
    **不**动已声明读面（序 37/38 的判据）；**不**改 SSE / 事件流（序 38）；**不**给
    **非读面**（POST/PUT/PATCH/DELETE）加查询参数检查（那是另一族；写面已按序列 39 处理）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（未声明面的读数与影响面）**：`scratch/probe-undeclared-query-params.py`
      逐条读出 —— ① **实跑**：未声明路由收到查询串 ⇒ **200**（点名 ≥2 条不同的路由）；
      ② **射程清单**：全仓未声明查询参数的 GET 路由**逐条**（数量读数，供受判面清单）；
      ③ **影响面盘点**：web（`apps/web/src/api/*.ts`）与 tests 里对**这些**路由的带查询串调用
      （有 ⇒ 逐条点名，落地前先处理）；④ **缺省基线**：不传参数时这些路由的响应
      （状态码 + 关键键）逐条记录（供「逐字不变」比对）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-undeclared-query-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **纪律扩到未声明的读面（本轮验收主体）**：**未声明**查询参数的 GET/HEAD 路由收到
      查询参数 ⇒ **422 + 逐个点名 + 明写「该路由不接受查询参数」**；**缺省形态逐字不变**
      （不传参数 ⇒ 与改动前逐字相同）；**非读面**（`None` 支）**一字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（未声明路由点名 / 多个逐个 / 缺省不变 / 非读面不受影响）。
    status: PASS
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：**已声明**读面（序 37/38 判据）与**写面**（序 39）
      判据**全绿**；受影响的全仓调用面（EC-01 ③）逐条处理；若动 DTO / schema ⇒ 同轮
      重生成并提交 `docs/api/openapi.m13.json`（**预期零 diff** —— 本轮不动声明面；
      如实测有变则如实登记）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 新用例（对照组 / 已声明面回归 / 写面回归）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Y-1` 未声明面**又被静默忽略**（退回归零）⇒ RED；
      `Y-2` **已声明面被误伤**（例：把 `None`/已知集处理打坏 ⇒ 正确请求 422）⇒ RED；
      `Y-3` **缺省形态被改动**（不传参数也报错）⇒ RED；`Y-4` **非读面被误伤**
      （写面收到查询参数被 422 —— 射程越界）⇒ RED。复原用**二进制读写**且 raw `sha256`
      逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal072_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-072-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 40**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal072_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
budget:
  max_cycles: 6
  per_cycle_minutes: 90
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
  sync_set:
    - 既有判据**只**在「本轮的共用契约改动打到它」时才可同轮改签（逐条申报 + `git diff --numstat` 删除行读数）
    - 改既有判据一律**按关系**改（不按写法 / 位置），且**两向实测**（该红时红 / 不该红时不红）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 触达 D 组审批通道 / 真实外发 / 读面认证 / 多租户
  - 需要放开默认网络 / 需要真实凭据
child_plans:
  - .cursor/plans/tasks/PLAN-20261013-453-goal-072-ec01-05-routes-without-declared-query-params-also-refuse-them.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261013-072 — 未声明查询参数的路由也不再静默吞掉查询参数

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 40**（轴 = **质量**；依赖序 39
> —— 已收口）。**本行由实测缺口驱动**（序 39 收口后盘账），已在 MAINLINE「修订记录」留痕；
> **GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（实跑 / 射程清单 / 影响面盘点 / 缺省基线） | **实跑**：`scratch/probe-undeclared-query-params.py` | **PASS** |
| EC-02 | 未声明读面收到查询参数 ⇒ 422 + 逐个点名；缺省逐字不变 | `pytest tests/api -q`（653 passed）+ 新 6 例 | **PASS** |
| EC-03 | 射程如实（已声明面 / 写面不回归）+ 快照同轮（**实测零 diff**） | 1999 + 307 + **53 live** passed | **PASS** |
| EC-04 | 两向反证 `Y-1`…`Y-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/GOAL-20261013-072-press-two-way.txt`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：未声明读面收到查询串 ⇒ **200** | `TestClient` + 真实装配 | `/projects?definitely_unknown=1` ⇒ **200**；`/health?zz=1` ⇒ **200** |
| 2 | 未声明查询参数的 GET 路由**条数** | `app.openapi()` 过滤 `parameters[in=query]` 为空 | **58** 条（逐条清单在探针第 2 段） |
| 3 | 现守卫的**语义区分**（`None` vs 空集）在树 | `services/api/query_param_guard.py` | `declared_query_params` 已**区分**：`None` = 非读面（不在射程）/ 空集 = 读面但无参数（**当前跳过**）⇒ 本轮把后者从「跳过」改成「拒绝」 |
| 4 | **影响面（逐条）** | 探针第 3 段（扫 web/tests 对未声明路径的带查询串调用） | **17 处命中**，逐条分类：**12 处是对「已声明」路由的调用**（library/cost-forecast/memory —— 序 37/38 已覆盖、不受影响）；**2 处是 false positive**（`before?.digest` 可选链、`/?source=example#/` 非 API）；**2 处是真受判面**：`/projects?unknown_here=1`（序 36 对照组）与 `/health?definitely_unknown=1` + `/runs/.../telemetry`（序 37 对照臂）—— **本轮纪律正是要改变它们** ⇒ 这两个判据的**对照臂语义失效**，按「射程扩大」同轮改签（逐条申报，见迭代日志） |
| 5 | 缺省基线（不传参数的状态码 + 键） | 探针第 4 段 | `/projects` ⇒ 200（list[1]）；`/health` ⇒ 200（键 `['composition','pricing_degraded','status','version']`） |

**结论**：「静默吞掉」族已连接通三面（读面已声明 37/38、写面 39），**仅剩**「读面
**未声明**」这一面仍静默 —— 且序 37/38 两轮都把它登记为后续候选。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 改**空集那一支**（读面但无声明 ⇒ 有查询参数即 422），`None` 支**一字不动** | 现守卫已区分两种「跳过」（见事实 3）；`None` = 非读面 ⇒ 不在本轮射程 | 已定 |
| D-2 | 未知参数 ⇒ **422 + 逐个点名 + 明写「该路由不接受查询参数」** | 与序 37 同形；空集路由的「已知集」= 空 ⇒ 正文要说清楚（否则读者以为漏了清单） | 已定 |
| D-3 | **缺省形态逐字不变**（不传参数 ⇒ 一字不动） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | 快照**预期零 diff**（不动声明面） | 本轮只动校验行为，不动签名 ⇒ 与序 39 同形；如实测有变则如实登记 | 已定 |
| D-5 | 做法 = 改**共享守卫**（`reject_unknown_query_params` 的空集支），不逐路由改 | 与序 37 的机制同源（一处声明、全体生效）；逐路由要改 58 处、且会漏 | 已定 |

## 循环入口协议（幂等重入）

1. 最后一 cycle 无记录 ⇒ 开 cycle 1：执行派生 PLAN 的 WP-1。
2. 有子 PLAN 且 `IN_PROGRESS` ⇒ 继续该 PLAN 的未完成 WP。
3. 本地验证已过、有未推送 commit ⇒ push + 轮询 CI。
4. CI 在跑或未记结论 ⇒ 等待 / 判定，**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 ⇒ 按失败分类纠错。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 ⇒ 派生下一子 PLAN。
7. 按「终止与收口」判 ACHIEVED / BLOCKED / 超预算。

## 单 cycle SOP

① 派生**子 PLAN**（`parent_goal` 投影 `ALL_PLAN`，同一提交）→ ② 执行（每 WP 独立 commit，
**只用显式路径**，**绝不 `git add -A`**）→ ③ 本地验证**按既有顺序**（**先写记录 →
记录面判据 → 全量 m0**；m0 **独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、
不接管道）→ ④ commit → ⑤ push（**批量**）+ 轮询 CI 到终态 → ⑥ 按失败分类纠错 →
⑦ 回写本 GOAL（EC / 迭代日志 / 状态历史 / `latest_recheck` / `child_plans`）。

**判定纪律（硬）**：每条 EC **两向反证**；受判面**非空**且**不得是交集 / 并集掩蔽 / 写法清单**；
按压 → 复原用 **raw `sha256` + 二进制读写**；归档一律**二进制写盘**（判词进
`.cursor/plans/goals/evidence/`，`CR=0`）；**点名失败而非静默降级**；**未实跑不得记 PASS**；
进程卫生（Windows `taskkill /T /F` + 复验零泄漏；**live e2e 跑完要杀 node/python 树** —— 序 39 实测）；
**显式路径 `git add` 后必须复核 `git status`**（★ **改判据文件之后必须重跑 `ruff format`**）；
**批量替换前先数锚点命中数**（`== 1` 才替换）；**判据要判调用形态而非散文字符串**；
**共享契约改动前先量调用面**（序 39 的 live e2e 真红形态：spread-into-write）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：**58 条未声明路由**的既有调用）| 同轮修全部受影响面；逐条核对既有数据 |
| (iv) 判据面自身 | 判据按位置 / 写法写死（**假红**）或恒假 | 改判**关系**并**两向实测**；在 RECHECK 如实登记 |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 `PASS`；收口面（验证器 + 断言集）**进树**并过四道门；
  两树 `TWO-TREE PASS`；as-is m0 **23/23**（记录写完之后）；治理 + 宪章判据绿；
  CI 台账**逐提交**；残余与未覆盖范围**逐条在位**；`latest_recheck` 指向 PASS 的 RECHECK。
- **BLOCKED**：命中 `escalation_triggers` 或超 `fix_policy` 上限 ⇒ 记 BLOCKED 并留人工决策。
- **ABORTED**：预算（`budget.max_cycles`）触顶且无进展。
- 收口后**不再推进本 GOAL**；本轮**不**宣称项目安全（`R-M1`），**不**宣称投递语义为
  「恰好一次」（**明确否认**）。

## 残余与受限面（承继 + 本轮）

- **本轮推进**：未声明查询参数的路由也不再静默吞掉查询参数（「静默吞掉」族**四面收口**）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：作者鉴权 / 通配·模糊匹配 / `provenance` 在编排面的披露 /
  **内容级检测**（`W-2`）/ 三维以上闸门组合；`BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` /
  `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5` /
  **非读面**的查询参数检查（另一族）。
- **未覆盖范围（逐条明写）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器。
- **明确否认**：投递语义**不是**「恰好一次」（口径只能是 at-least-once + idempotency +
  deduplication）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**（并写明 `covered_by`）；`cancelled` / `failure` 如实登记
> + 原因 + `covered_by`。**自我指涉边界**：台账提交自身不产生可引用的 CI 结论
> （明写并以「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| 提交 | CI run / 结论 | 覆盖的 WP |
| --- | --- | --- |
| （待开 cycle 1 后回填） | （待轮询） | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（实测缺口登记 + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 40**（**同轮建档**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 空集支改拒绝 + 影响面处理） |
| 1 | PLAN-20261013-453 | `0482d972`（+ 本轮记录提交） | 探针四段读数（58 条 / 影响面逐条）；空集支改拒绝；两处对照臂改签；api 653 / contracts+tooling 1999 / e2e 307 / **live 53** 全绿；快照零 diff；四向按压全 RED（Y-4 首跑 GREEN 抓出判据缺口 ⇒ 补写面带查询参数断言） | （见 CI 台账） | Y-4 缺口（同签名 1 次，未超上限） | EC-01…04 PASS；剩 EC-05 收口 | EC-05（验证器 + 两树 + m0 + 台账） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | ACTIVE | **实测缺口登记 + 建档（cycle 0）**：MAINLINE 程序表**新增序 40**（**轴 = 质量**），并写修订记录行（只追加；同轮把序 37 的旧修订行原文搬入新归档）。**实测读数**（逐条见「事实层结论」表）：① 未声明读面收到查询串 ⇒ **200**（两条不同路由）；② 全仓 **58 条**未声明查询参数的 GET；③ 现守卫**已区分** `None`/空集两种「跳过」⇒ 改后者即可。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**动已声明面 / **不**动写面 / **不**动非读面。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
