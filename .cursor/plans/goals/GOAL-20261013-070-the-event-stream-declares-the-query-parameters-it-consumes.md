---
id: GOAL-20261013-070
slug: the-event-stream-declares-the-query-parameters-it-consumes
title: >-
  事件流路由**声明它消费的查询参数** —— 序 37 让**已声明**参数的路由有了纪律（已知集从签名导出），
  而**实测**：`GET /runs/{run_id}/events` **从原始 `request.query_params` 读** `cursor` / `poll`
  （`?poll=0` 关轮询、`?cursor=` 续传），但**签名里一个都没声明** ⇒ ① OpenAPI 里这两个参数
  **不可见**（读面契约不完整）；② 序 37 的守卫按签名跳过它 ⇒ 打错名字**静默吞掉**
  （**实测**：`?po11=0` 与 `?nonsense=1` 都 200 —— 且前者**静默保持轮询**，与调用方意图**相反**）。
  本轮把这两个参数**声明出来**：契约补全 + 守卫自动接管 + 已知/缺省形态逐字不变
status: ACTIVE
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-13 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 38**，由本次到期 replan 的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**全仓扫描** ⇒ 唯一「从原始 `request.query_params`
    读却不声明」的路由 = `services/api/routers/run_events.py`；**实跑**（JSON replay 模式，有界）
    ⇒ `?po11=0`（正确名 `poll`）与 `?nonsense=1` **都 200**（静默吞掉）；**SSE 模式更糟**：
    打错 `poll` 的名字 ⇒ 守卫/路由照默认 `poll=1` 走 ⇒ **静默保持轮询**（无限流，
    实测探针因此挂死 ⇒ 需 `timeout` 收口）。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 37 的守卫**按签名**决定射程
    （**这是对的**：没有声明就没有「已知集」），但它**暴露**了更上游的缺陷：这条路由**该声明
    却没声明** ⇒ 契约面（OpenAPI）与消费面（`query_params.get`）**不一致**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：把 `cursor` / `poll` **声明进签名**
    （`Query(...)` 形态，缺省与现行为**逐字相同**）⇒ ① OpenAPI 里可见；② 序 37 的守卫
    **自动**接管（未知参数 422 点名）；③ 已知/缺省形态**逐字不变**（`?poll=0` 关轮询、
    `?cursor=` 续传、不传参数行为不变）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**改 SSE 的帧格式 / 续传语义 / 去重语义（那是既有契约）；
    **不**给**写面**加参数检查（pydantic 既有校验面）；**不**动序 37 的守卫与判据（它们由
    收口断言集钉住）；**不**改 `Last-Event-ID` 头路径（头不是查询参数）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（消费/声明不一致的读数）**：`scratch/probe-event-stream-params.py` 逐条读出 ——
      ① **扫描**：全仓「引用 `request.query_params`」的文件与「声明查询参数」的路由的**差集**
      （唯一命中 = `run_events.py`）；② **OpenAPI 声明面**：`/runs/{run_id}/events` 的
      `parameters[in=query]` = **空**（实测）；③ **实跑静默吞掉**：JSON replay 模式下
      `?po11=0` / `?nonsense=1` 都 **200**（点名那两条）；④ **SSE 语义危害**：打错 `poll`
      ⇒ 默认 `poll=1` ⇒ **保持轮询**（有界探针要 `timeout`；如实登记探针这一形态）；
      ⑤ 正确形态基线：`?poll=0`（SSE）与 `?cursor=`（replay）**照旧**。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-event-stream-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **声明出来（本轮验收主体）**：`GET /runs/{run_id}/events` 的签名**声明** `cursor` 与
      `poll`（缺省与现行为**逐字相同**；`poll=0` 关轮询、`cursor=` 续传边界不变）；
      OpenAPI 的 `parameters[in=query]` 反映这两个（**契约面与消费面一致**）；
      序 37 的守卫**自动**接管 ⇒ 未知参数 **422 + 逐个点名 + 已知集**（`cursor` / `poll`）。
      **`Last-Event-ID` 头路径不受影响**（头不是查询参数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（声明面 / 未知点名 / `?poll=0` 与 `?cursor=` 逐字 / 头路径不变 / 缺省不变）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：SSE 帧格式 / 续传 / 去重语义**一字不动**（既有 SSE 用例全绿）；
      **序 37 的守卫与判据不回归**（它由收口断言集钉住，本轮**不**改）；
      若动 DTO / 路由签名 ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`（本轮的**预期**是
      快照**会**变 —— 声明进签名 ⇒ 参数进 schema；如实登记）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 新用例（SSE 回归 / 快照同步）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`V-1` 声明被**移除**（退回归零 ⇒ 守卫重新
      跳过它、未知参数静默吞掉）⇒ RED；`V-2` **缺省被改动**（不传参数也报错 / `poll` 缺省
      从 `"1"` 变 `"0"`）⇒ RED；`V-3` **`poll=0` 语义被破坏**（关轮询不再生效）⇒ RED；
      `V-4` **`cursor` 续传被破坏**（`?cursor=` 不再裁剪）⇒ RED。复原用**二进制读写**且
      raw `sha256` 逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal070_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-070-press-two-way.txt`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 38**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal070_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-449-goal-070-ec01-05-the-event-stream-declares-the-query-parameters-it-consumes.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261013-070 — 事件流路由声明它消费的查询参数

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 38**（轴 = **质量**；依赖序 37
> —— 已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 35/36/37 收口后到期），
> 已在 MAINLINE「修订记录」留痕；**GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（消费/声明差集 / OpenAPI 空 / 实跑静默 / SSE 危害 / 正确基线） | **实跑**：`scratch/probe-event-stream-params.py` | PENDING |
| EC-02 | 声明 `cursor` / `poll`；守卫自动接管；头路径不变 | `pytest tests/api -q` + 新用例 | PENDING |
| EC-03 | 射程如实（SSE 语义不动）+ 序 37 不回归 + 快照同轮（**预期会变**） | `pytest tests/api tests/contracts tests/tooling -q` | PENDING |
| EC-04 | 两向反证 `V-1`…`V-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **唯一**「引用 `request.query_params`」却未声明的路由 | `rg -n "request.query_params" services/api/` | 只 `services/api/routers/run_events.py`（`cursor` / `poll` 两处 `.get`） |
| 2 | OpenAPI 声明面为空 | `app.openapi()` 的 `parameters[in=query]` | `/runs/{run_id}/events` ⇒ **空**（只有 `run_id` 路径参数） |
| 3 | **实跑静默吞掉**（JSON replay，有界） | `TestClient` + 真实 run | `?po11=0` ⇒ **200**；`?nonsense=1` ⇒ **200** |
| 4 | **SSE 语义危害** | 有界探针（`timeout`） | 打错 `poll` ⇒ 默认 `poll=1` ⇒ **保持轮询**（探针挂死，须 `timeout` 收口 —— 如实登记） |
| 5 | 正确形态基线 | 既有用例 | `?poll=0`（SSE 关轮询）与 `?cursor=`（replay 续传）**照旧**；`Last-Event-ID` 头路径照旧 |

**结论**：序 37 的守卫**按签名**决定射程（**这是对的**），但它**暴露**了更上游的缺陷 ——
这条路由**该声明却没声明** ⇒ **契约面（OpenAPI）与消费面（`query_params.get`）不一致**。
把参数声明进签名，守卫**自动**接管（不需要改守卫本体）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 声明进**签名**（`Query(...)`），不是把名字塞进手写清单 | 序 37 的 D-1 同源：签名是**唯一**不漂的已知集来源 | 已定 |
| D-2 | **缺省逐字不变**（`poll` 缺省 `"1"`、`cursor` 缺省 `None`） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-3 | 快照**预期会变**（参数进 schema）⇒ **同轮**重生成 + 提交 | 与序 36/37 的「零 diff」形态**相反** —— 本轮**如实登记为会变** | 已定 |
| D-4 | **不**动 `Last-Event-ID` 头路径 | 头不是查询参数；改它属另一面 | 已定 |

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
进程卫生（Windows `taskkill /T /F` + 复验零泄漏；**SSE 探针必须 `timeout` 收口**）；
**显式路径 `git add` 后必须复核 `git status`**；**批量替换前先数锚点命中数**（`== 1` 才替换）；
**受判面清单与实测集合必须相等**（序 37 EC-02 ⑥ 的形态）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：SSE 既有用例 + 快照消费者）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：事件流路由**声明它消费的查询参数**（契约面与消费面一致）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**写面**请求体的额外字段（pydantic 既有校验面）/ 作者鉴权 /
  通配·模糊匹配 / `provenance` 在编排面的披露 / **内容级检测**（`W-2`）/ 三维以上闸门组合；
  `BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` /
  `R-*` / `Q-*` / `P-*` / `O-1`…`O-5` / 序 37 声明的「无查询参数路由的参数检查」面。
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
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 38**（**同轮建档**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 声明进签名 + 守卫自动接管） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 38**（**轴 = 质量**），并写修订记录行（只追加；同轮把序 35 的旧修订行原文搬入新归档）。**实测读数**（逐条见「事实层结论」表）：① 唯一消费原始 `query_params` 却未声明的路由 = `run_events.py`；② OpenAPI 声明面**空**；③ 实跑 `?po11=0` / `?nonsense=1` 都 **200**（静默吞掉）；④ **SSE 模式下打错 `poll` ⇒ 静默保持轮询**（探针需 `timeout` 收口 —— 如实登记）；⑤ 正确形态（`?poll=0` / `?cursor=` / 头路径）照旧。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**改 SSE 语义 / **不**改写面 / **不**动序 37 的守卫。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
