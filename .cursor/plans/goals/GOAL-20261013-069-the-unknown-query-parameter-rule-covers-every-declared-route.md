---
id: GOAL-20261013-069
slug: the-unknown-query-parameter-rule-covers-every-declared-route
title: >-
  未知查询参数的纪律扩到「已声明查询参数」的全体路由 —— 序 36 只在**记忆读面**接通
  （射程 = 那两个 GET，**有意**不扩散）；**实测**：全仓 **9 条 GET 已经声明了查询参数**
  （从路由签名**可导出**），其中 `GET /notifications?limt=5`（`limit` 打错）与
  `GET /projects/{id}/cost-forecast?horizon_day=7`（`horizon_days` 打错）**都返回 200 并静默吞掉**
  ⇒ 调用方**以为设了参数**而实际用的是默认值（与序 36 同形的「静默降级」）。
  **射程可导出**：`inspect` / AST 从**路由签名**取「已知参数」，无需手写清单 ⇒ 扩到全体（那 9 条）是机械动作；
  **先例已全在**（序 36 的守卫 + 已知集形态）
status: ACTIVE
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-13 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 37**，由本次 replan 的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**两个独立面交叉核对** ⇒ 全仓 **9 条 GET 已声明
    查询参数**（面 A = 应用解析后的 OpenAPI `parameters[in=query]`；面 B = 逐模块 router 对象的
    `dependant.query_params`；两面**逐条相同**）；**实跑**（`TestClient` + 受控装配）⇒ `GET /notifications?limt=5`
    （正确名 `limit`）与 `GET /projects/example-project/cost-forecast?horizon_day=7`
    （正确名 `horizon_days`）**都 200**（静默吞掉，用的是默认值）⇒ 打错名字的参数
    **不报错、不点名**；序 36 已在**记忆读面**立了**同形**纪律（422 + 逐个点名 + 已知集），
    但射程**有意**只有那两个 GET。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 36 把**一条**读面接通了
    （局部正确），而**同族形态在其余 7 条已声明路由上仍然静默** ⇒ 调用方**以为设了参数**而拿到默认值
    （承「点名失败而非静默降级」的禁令）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：把序 36 的纪律**机械地扩到「已声明查询参数」
    的全体路由** —— 已知参数**从签名导出**（不手写清单 ⇒ 不会漂），未知参数**点名拒绝**
    （422 + 逐个 + 给出该路由的已知集），**缺省形态逐字不变**（不传未知参数 ⇒ 与改动前**逐字相同**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**无查询参数**路由的检查（没有声明的参数 ⇒ 没有
    「已知集」可言；那种路由收到任何查询参数仍照旧 —— 那**另成一面**，登记为后续候选）；
    **不**改**写面**（POST/PUT 的请求体是 pydantic 的既有校验面）；**不**动**已声明参数**的
    既有语义（`?limit=` / `?scope=` / `?at=` 等**一字不动**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（签名导出 + 实跑 + 零命中 + 射程分类）**：
      `scratch/probe-query-param-coverage.py` 逐条读出 ——
      ① **AST 导出**：全仓 GET 路由里**已声明查询参数**的条数与逐条清单（**9 条**，两个独立面交叉核对）；
      ② **实跑**：两条不同路由上打错参数名 ⇒ **200 + 静默吞掉**（点名那两条）；
      ③ **零命中**：通用守卫在树里**不存在**（只有序 36 的记忆读面守卫）；
      ④ **射程逐条分类**：有参数 / 无参数 / 本轮覆盖 / 本轮**不**覆盖（无参数面）；
      ⑤ 序 36 的守卫**仍在树**（本轮**不**改它 —— 它由收口断言集钉住）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-query-param-coverage.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **纪律扩到全体已声明路由（本轮验收主体）**：未知查询参数在**每一条已声明查询参数的 GET**
      上 ⇒ **422 + 正文点名**（并给出**该路由**的已知集，供自纠）；**多个未知逐个点名**；
      **已知参数与缺省形态逐字不变**；**已知集从签名导出**（加参数**自动**跟着走 ——
      不手写清单，故不会漂）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（逐路由点名 / 多个逐个 / 已知不变 / 缺省不变 / 导出面与签名一致）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：**无查询参数**的路由**不受影响**（受判面 = 那条对照组）；
      **序 36 的记忆读面**判据**全绿**（它由收口断言集与既有用例钉住，本轮**不**改）；
      既有两个已知形态（`?scope=` / `?proposed_by=`）的披露**一字不动**；
      若动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 新用例（对照组 / 记忆读面回归 / 既有键不变）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`W-1` 导出面**返回空集**（守卫失效）⇒ RED；
      `W-2` 导出面**多收**（把路径参数当查询参数 ⇒ 正确请求被误拒）⇒ RED；
      `W-3` **缺省形态**被改动（不传未知参数也报错）⇒ RED；
      `W-4` **只**覆盖记忆读面（射程没扩 ⇒ 其他路由仍静默）⇒ RED。复原用**二进制读写**且
      raw `sha256` 逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal069_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-069-press-two-way.txt`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 37**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal069_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-447-goal-069-ec01-05-the-rule-covers-every-declared-route.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261013-069 — 未知查询参数的纪律扩到「已声明查询参数」的全体路由

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 37**（轴 = **质量**；依赖序 36
> —— 已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 34/35/36 收口后到期），
> 已在 MAINLINE「修订记录」留痕（含 `max_goals` 40 → 45 的核算理由）；
> **GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（AST 导出 / 实跑 / 零命中 / 射程分类 / 序 36 在位） | **实跑**：`scratch/probe-query-param-coverage.py` | PENDING |
| EC-02 | 未知参数在**每条已声明路由**上点名拒绝；已知集**从签名导出** | `pytest tests/api -q` | PENDING |
| EC-03 | 射程如实（无参数路由不受影响）+ 序 36 回归 + 快照同轮 | `pytest tests/api tests/contracts tests/tooling -q` | PENDING |
| EC-04 | 两向反证 `W-1`…`W-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **9 条 GET 已声明查询参数**（签名可导出） | `uv run --frozen --no-sync python -B scratch/probe-query-param-coverage.py` | 逐条清单：`/cost/daily`（`date_from` `date_to`）/ `/evaluations/trend`（`dataset_id` `expected_digests` `limit`）/ `/experiment-plans`（`state`）/ `/models`（`endpoint_id`）/ `/notifications`（`limit`）/ `/projects/{project_id}/cost-forecast`（`date_from` `date_to` `horizon_days`）/ `/projects/{project_id}/library`（`kind`）/ `/projects/{project_id}/memory`（`proposed_by` `scope`）/ `/projects/{project_id}/memory/validity`（`at`） |
| 2 | **实跑**：打错参数名 ⇒ **200 + 静默吞掉** | 同上第 2 段 | `/notifications?limt=5` ⇒ 200；`/cost-forecast?horizon_day=7` ⇒ 200 |
| 3 | **零命中**：通用守卫不存在 | `rg -n "query_param" services/api/` | 只有序 36 的**记忆读面**守卫（`memory_query_guard.py`） |
| 4 | 序 36 的守卫**仍在树**（本轮**不**改） | `rg -n "reject_unknown_query_params" services/api/` | 守卫 + 记忆路由的两处调用 |
| 5 | 全仓 GET 总数（**射程分类**用） | 探针第 4 段 | **68** 条 GET（面 A）/ **67** 条（面 B，差 1 = `/health` 直接注册）；其中 **9** 条已声明查询参数 |

**结论**：**序 36 是局部正确** —— 一条读面接通了，而**同族形态在其余 7 条已声明路由上仍然静默**
⇒ 调用方**以为设了参数**而拿到默认值。而「已知参数」**可从签名导出** ⇒ 扩散是**机械动作**，
**不是**新造机制（序 36 的守卫与点名形态可照）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 已知参数**从路由签名导出**（**不**手写清单） | 手写清单会**漂**（加参数忘了改 ⇒ 正确请求被误拒 = 序 36 `Z-2` 的形态）；导出则不漂 | 已定 |
| D-2 | 未知参数 ⇒ **422 + 逐个点名 + 给出该路由的已知集** | 与序 36 **同一形态**（调用方可自纠） | 已定 |
| D-3 | **缺省形态逐字不变**（不传未知参数 ⇒ 逐字相同） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | **无查询参数**的路由**不受影响**（本轮**不**覆盖那种面） | 没有「已知集」可言；那种面另成一条（登记为后续候选） | 已定 |
| D-5 | 走**既有中间件层**还是**逐路由调用**，由 EC-01 读 app 装配后定 | 涉及请求处理链 ⇒ 先量再定（`add_middleware` 的**顺序语义**在 `AGENTS`/既有判据里有钉住的先例） | **待 EC-01** |

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

**判定纪律（硬）**：每条 EC **两向反证**；受判面**非空**且**不得是交集 / 并集掩蔽 / 写法清单**
（承 `MEM-156`）；按压 → 复原用 **raw `sha256` + 二进制读写**；归档一律**二进制写盘**
（判词进 `.cursor/plans/goals/evidence/`，`CR=0`）；**点名失败而非静默降级**；
**未实跑不得记 PASS**；进程卫生（Windows `taskkill /T /F` + 复验零泄漏）；
**显式路径 `git add` 后必须复核 `git status`**（承序 32 的 `format-check` 真红教训）；
**在宪章里插入表格行必须是追加**（承上一轮实测的「顶掉旧行」形态）；
**新写 `raise ApiError` 要同步隐私出口普查清单**（承序 36 的实测）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：请求处理链 + 9 条已声明路由的既有测试）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：未知查询参数的纪律**扩到 9 条已声明路由**（已知集**从签名导出**）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**无查询参数**路由的参数检查（另成一面）/ **写面**请求体
  额外字段（pydantic 既有面）/ 作者鉴权 / 通配·模糊匹配 / `provenance` 在编排面的披露 /
  **内容级检测**（`W-2`）/ 三维以上闸门组合（语义边界未定）；`BB-3`；`DD-1`…`DD-3`；
  `AA-*` / `Z-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` /
  `O-1`…`O-5`。
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
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 37**（**同轮建档**）+ 预算 40→45 | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 导出面 + 全员覆盖） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 37**（**轴 = 质量**），并写修订记录行（只追加）+ 预算核算（`max_goals` 40 → 45）。**实测读数**（逐条见「事实层结论」表）：① **9 条 GET 已声明查询参数**（两个独立面交叉核对，逐条相同）；② **实跑**两条不同路由打错参数名 ⇒ **200 + 静默吞掉**；③ 通用守卫**零命中**（只有序 36 的两文件）；④ 全仓 68 条 GET 的射程分类（9 已声明 / 59 无参数）；⑤ 序 36 的守卫仍在树。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**覆盖无参数路由 / **不**改写面 / **不**动已知参数语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
