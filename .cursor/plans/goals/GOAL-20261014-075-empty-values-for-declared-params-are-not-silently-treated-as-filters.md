---
id: GOAL-20261014-075
slug: empty-values-for-declared-params-are-not-silently-treated-as-filters
title: >-
  声明参数的「空值」形态不再被静默当成筛选值 —— 序 37/40/41/42 把「未知 / 未声明 / 写面 /
  重复」四面接通，而**实测**：**已声明参数给空值**时各路由**不一致** ——
  `?scope=` / `?proposed_by=`（记忆读面）⇒ **200 且筛成 0 条**（调用方以为「没有匹配」）、
  `?state=`（实验计划）⇒ 200，而 `?at=`（validity）⇒ **422**（Invalid Timestamp）、
  `?kind=`（library）⇒ **422** ⇒ 同一形态**一半静默一半报错**。
  本轮统一为 **422 + 点名该参数 + 明写「不接受空值」**，
  **缺省（不传）形态逐字不变**（web 客户端已显式挡空值 ⇒ 不打断既有调用）
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-14 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 43**，由序 42 收口后盘账的**实测缺口**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑** ⇒ `?scope=`（记忆读面）⇒ **200**
    且 `records: []`（**筛成 0 条**，调用方读作「没有匹配」）；`?proposed_by=` ⇒ 200；
    `?state=`（experiment-plans）⇒ 200；而 `?at=`（memory/validity）⇒ **422**
    （`Invalid Timestamp`）、`?kind=`（library）⇒ **422** ⇒ **同一形态两种行为**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 前四面（未知 / 未声明 /
    写面 / 重复）都已接通，而**空值**这一形态**各路由不一致**且**无判据钉住**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：守卫新增**空值臂** —— **已声明**的参数
    在 `query_params` 里出现且值为**空串** ⇒ **422 + 点名该参数 + 明写「不接受空值」**
    （措辞与「未知」「重复」**三分辨**）。`list` 声明的参数**一字不动**（web 合法追加）。
    **不传**（缺省）形态**逐字不变**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**动前四面（序 37/40/41/42 的判据由收口断言集钉住）；
    **不**动 `list` 声明；**不**改各路由**已声明值**的既有语义（`?scope=project` 等一字不动）；
    **不**给无路由路径加检查（404 已是既有语义）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（空值形态 + 影响面）**：`scratch/probe-empty-query-values.py` 逐条读出 ——
      ① **实跑**：已声明参数空值 ⇒ **各路由的两种行为**（静默筛 0 / 422）逐条点名；
      ② **射程清单**：全仓**已声明**参数里哪些给了空值 ⇒ 现行为（供受判面清单）；
      ③ **影响面盘点**：web 与 tests 里**是否**发空值（**实测已见**：web 客户端
      `!== ""` 守卫 ⇒ 不发）；④ **缺省基线**：不传参数的状态码 + 关键键（供「逐字不变」比对）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-empty-query-values.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **纪律扩到空值形态（本轮验收主体）**：**已声明**的参数空值 ⇒ **422 + 点名该参数 +
      明写「不接受空值」**（与「未知」「重复」措辞**三分辨**）；**多个空值逐个点名**；
      **缺省（不传）形态逐字不变**；**`list` 声明一字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（空值点名 / 多个逐个 / 缺省不变 / 与另两臂措辞分辨）。
    status: PASS
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：四面（序 37/40/41/42）判据**全绿**；写面体（序 39）与
      事件流（序 38）不回归；**live e2e** 全绿；快照同轮（**预期零 diff** —— 不动签名；
      如实测有变则如实登记）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + live 套件。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`V5-1` 空值**又被静默当成筛选值**（退回归零）⇒ RED；
      `V5-2` **`list` 声明被误伤**（合法空值/重复被 422 —— 射程越界）⇒ RED；
      `V5-3` **缺省形态被改动**（不传也报错）⇒ RED；`V5-4` **重复臂被误伤**（序 42 的靶子回退）⇒ RED。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；**反证脚本带基线门**；
      判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal075_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261014-075-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 43**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal075_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261014-459-goal-075-ec01-05-empty-values-for-declared-params-are-not-silently-treated-as-filters.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261014-075 — 声明参数的空值形态不再被静默当成筛选值

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 43**（轴 = **质量**；依赖序 42
> —— 已收口）。**本行由实测缺口驱动**（序 42 收口后盘账），已在 MAINLINE「修订记录」留痕；
> **GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（空值两行为 / 射程清单 / 影响面 / 缺省基线） | **实跑**：`scratch/probe-empty-query-values.py` | **PASS** |
| EC-02 | 空值 ⇒ 422 + 点名；缺省与 list 逐字不变 | `pytest tests/api -q`（672 passed）+ 新 6 例 | **PASS** |
| EC-03 | 射程如实（四面 + 写面体 + 事件流不回归）+ live e2e + 快照同轮 | 2680 + 307 + **53 live** passed；快照零 diff | **PASS** |
| EC-04 | 两向反证 `V5-1`…`V5-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/GOAL-20261014-075-press-two-way.txt`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：空值形态**各路由不一致** | `TestClient` + 受控装配（造 1 条记忆） | `?scope=` ⇒ **200** 且 `records: []`（**筛成 0 条**）；`?proposed_by=` ⇒ 200；`?state=` ⇒ 200；**而** `?at=` ⇒ **422**（Invalid Timestamp）、`?kind=` ⇒ **422** |
| 2 | 空值被当成**筛选值**的证据 | 同上（`?scope=` 的载荷） | 载荷键 = `['filtered_out','records','scope','scope_note']` ⇒ 走了「筛」那一支（`filtered_out` 在），而**无参**载荷键 = `['records','scope_note']` ⇒ 空值**不是**「不筛」 |
| 3 | **分界 = 类型面**（关键读数） | 探针第 2 段（四类参数给空值） | **str 型静默**：`endpoint_id` ⇒ 200；**校验型拒绝**：`limit`（int）⇒ 422、`date_from`（date）⇒ 422、`horizon_days`（int）⇒ 422 ⇒ 不一致的**根因**是「str 型没有校验面 ⇒ 空串被当合法筛选值」 |
| 4 | **影响面**（web/tests 是否发空值） | `rg -n '!== ""' apps/web/src/api/` | web 客户端**已显式挡空值**（`datasetId` / `dateFrom` / `dateTo` 都判 `!== ""` 才 `params.set`）⇒ 统一为 422 **不打断**既有调用 |
| 5 | 缺省基线 | 探针第 4 段 | `/projects/example-project/memory`（无参）⇒ 200（键 `['records','scope_note']`，1 条）；`/notifications`（缺省）⇒ 200（键 `['note','notifications']`） |

**结论**：前四面已接通，而**空值**这一形态**一半静默（筛 0 条）一半报错（422）** ⇒ 调用方
**读不出**「我给空了」还是「确实没有匹配」。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 统一为 **422 + 点名 + 明写「不接受空值」**（不是「静默当不筛」也不是「静默筛 0」） | 「点名失败而非静默降级」是本战役的一贯禁令；两种静默都让调用方读不出真相 | 已定 |
| D-2 | 措辞与「未知」「重复」**三分辨** | 读者要能区分「名字不对」/「给多了」/「给空了」 | 已定 |
| D-3 | **缺省（不传）逐字不变**；`list` 声明**一字不动** | 一贯纪律 + 射程边界（web 合法追加） | 已定 |
| D-4 | 快照**预期零 diff**（不动签名） | 与序 40/41/42 同形 | 已定 |
| D-5 | 做法 = 改**共享守卫**（新增空值臂），不逐路由改 | 与序 37/40/41/42 同源（一处声明、全体生效） | 已定 |

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
进程卫生（Windows `taskkill /T /F` + 复验零泄漏；live e2e 跑完杀 node/python 树）；
**显式路径 `git add` 后必须复核 `git status`**（★ 改判据文件之后必须重跑 `ruff format`）；
**批量替换前先数锚点命中数**（`== 1` 才替换）；**判据要判调用形态而非散文字符串**；
**共享契约改动前先量调用面**；**改纪律会把旧「对照臂」变成新「受判面」**（改签必须留申报）；
**改共享守卫的射程语义前，先 `rg` 全部收口断言集里对该文件的字面断言**；
**计数/取值面要用 `multi_items()` 而非 `keys()`**（`keys()` 去重 —— 序 42 的 ★ 教训）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：全部已声明参数的既有调用 + web 客户端）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：声明参数的空值形态统一为点名拒绝（不再一半静默一半报错）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：作者鉴权 / 通配·模糊匹配 / `provenance` 在编排面的披露 /
  **内容级检测**（`W-2`）/ 三维以上闸门组合；`BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` /
  `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5`。
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
| 0 | —（实测缺口登记 + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 43**（**同轮建档**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 空值臂 + 影响面处理） |
| 1 | PLAN-20261014-459 | `2e195bf3`（+ 本轮记录提交） | 探针四段读数（分界 = 类型面）；空值臂落地（措辞三分辨）；6 例新判据；api 672 / contracts+tooling 2001 / e2e 307 / **live 53** 全绿；快照零 diff；四向按压全 RED（两条锚点首跑未命中 ⇒ 改唯一锚点后全红） | （见 CI 台账） | — | EC-01…04 PASS；剩 EC-05 收口 | EC-05（验证器 + 两树 + m0 + 台账） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | ACTIVE | **实测缺口登记 + 建档（cycle 0）**：MAINLINE 程序表**新增序 43**（**轴 = 质量**），并写修订记录行（只追加；同轮把序 40 的旧修订行原文搬入新归档）。**实测读数**（逐条见「事实层结论」表）：① 空值形态**各路由不一致**（`?scope=` / `?proposed_by=` / `?state=` ⇒ 200 且筛 0 条；`?at=` / `?kind=` ⇒ 422）；② 空值走「筛」支（载荷含 `filtered_out`）；③ web 客户端**已挡空值** ⇒ 统一为 422 不打断既有调用。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**动前四面 / **不**动 `list` 声明 / **不**改已声明值的语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
