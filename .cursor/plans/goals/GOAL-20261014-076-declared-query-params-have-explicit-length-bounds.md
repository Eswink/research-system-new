---
id: GOAL-20261014-076
slug: declared-query-params-have-explicit-length-bounds
title: >-
  已声明查询参数的「无长度界」不再静默接受超长值 —— 序 37/40/41/42/43 把「未知 / 未声明 /
  写面 / 重复 / 空值」五面接通，而**实测**：**已声明**的 **str 型**查询参数 **10 / 16 条没有长度界**
  （`?endpoint_id=<5000 字符>` ⇒ **200**、`?state=<5000 字符>` ⇒ 200），而**有界**的 2 条
  （`date_from` / `date_to`，`max_length=10`）与**写面**（`name` 201 字符 ⇒ 422）都拒
  ⇒ 同一形态**读面不设界、写面设界**。本轮给那 10 条补**显式长度界**
  （**在路由签名里声明** ⇒ 框架校验面自动生效，与 `date_from` 同形），
  **缺省与合法值逐字不变**
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-14 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 44**，由序 43 收口后盘账的**实测缺口**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑** ⇒ `?endpoint_id=<5000 字符>` ⇒ **200**、
    `?state=<5000 字符>` ⇒ **200**（**静默接受超长值**）；而 `?kind=<5000 字符>` ⇒ **422**
    （该参数**有界**）⇒ **同一形态读面不一致**；对照**写面** `name` 201 字符 ⇒ 422（写面**全有界**）。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 五面（未知 / 未声明 / 写面 /
    重复 / 空值）已接通，而**长度界**这一形态**读面 10/16 条缺失**且**无判据钉住**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：给那 **10 条**（`endpoint_id` / `cursor` / `poll` /
    `dataset_id` / `state` / `scope` / `proposed_by` / `at` / `date_from`（项目级）/ `date_to`（项目级））
    补**显式长度界**（**在路由签名里声明** `max_length=…` ⇒ 与 `date_from` 同形、框架自动校验），
    **缺省与合法值逐字不变**；`list` 声明的 `expected_digests` 与**已界**参数**一字不动**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**动五面（序 37/40/41/42/43 的判据由收口断言集钉住）；
    **不**改**非法枚举值 ⇒ 空集**的既有设计（**实测确认**那是**文档化行为**：「未知 ⇒ 空集，
    不猜」，序 35/36 立）；**不**给写面加检查（写面**全有界**，实测）；**不**改 `list` 声明。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（长度界盘点 + 影响面）**：`scratch/probe-query-param-length-bounds.py` 逐条读出 ——
      ① **实跑**：超长值在**无界**参数上 ⇒ **200**（点名 ≥2 条）；在**有界**参数与**写面**上 ⇒ 422
      （对照臂）；② **射程清单**：全仓已声明 str 型参数的**长度界盘点**（逐条：有界 / 无界）；
      ③ **影响面盘点**：web 与 tests 里**是否**发超长值（有 ⇒ 逐条点名）；
      ④ **缺省基线**：不传参数的状态码 + 关键键（供「逐字不变」比对）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-query-param-length-bounds.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **长度界补齐（本轮验收主体）**：那 **10 条**无界参数补**显式长度界** ⇒ 超长值 **422 + 点名
      该参数**（框架校验面，与 `date_from` 同形）；**缺省与合法值逐字不变**；
      **已界参数与 `list` 声明一字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（逐条超长拒绝 / 合法值不变 / 缺省不变 / 已界参数不回归）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：五面（序 37/40/41/42/43）判据**全绿**；写面体（序 39）与
      事件流（序 38）不回归；**live e2e** 全绿；快照**同轮**（**预期会变** —— 长度界**进 schema**
      （`maxLength`）；如实测有变则同轮重生成并提交）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + live 套件 + 快照 diff 与声明面一致。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`L-1` 无界参数**又静默接受超长**（退回归零）⇒ RED；
      `L-2` **有界参数被误伤**（`date_from` 的界被改坏 ⇒ 合法值被拒）⇒ RED；
      `L-3` **缺省形态被改动**（不传也报错）⇒ RED；`L-4` **空值臂被误伤**（序 43 的靶子回退）⇒ RED。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；**反证脚本带基线门**；
      判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal076_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261014-076-press-two-way.txt`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 44**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal076_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261014-461-goal-076-ec01-05-declared-query-params-have-explicit-length-bounds.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261014-076 — 已声明查询参数的无长度界不再静默接受超长值

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 44**（轴 = **质量**；依赖序 43
> —— 已收口）。**本行由实测缺口驱动**（序 43 收口后盘账），已在 MAINLINE「修订记录」留痕；
> **GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（超长实跑 / 长度界盘点 / 影响面 / 缺省基线） | **实跑**：`scratch/probe-query-param-length-bounds.py` | PENDING |
| EC-02 | 10 条无界参数补显式长度界；缺省与合法值逐字不变 | `pytest tests/api -q` + 新用例 | PENDING |
| EC-03 | 射程如实（五面 + 写面体 + 事件流不回归）+ live e2e + 快照同轮（**预期会变**） | `pytest tests/api tests/contracts tests/tooling -q` + live | PENDING |
| EC-04 | 两向反证 `L-1`…`L-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：超长值在无界参数上 ⇒ **200** | `TestClient` + 真实装配 | `?endpoint_id=<5000 字符>` ⇒ **200**；`?state=<5000 字符>` ⇒ **200** |
| 2 | **对照臂**：有界参数与写面 ⇒ 422 | 同上 | `?kind=<5000 字符>` ⇒ **422**；写面 `name` 201 字符 ⇒ **422** |
| 3 | **长度界盘点：10 / 16 条无界** | `app.openapi()` 的 `parameters[in=query]` schema（含 `anyOf` 分支的 `maxLength`） | 无界：`endpoint_id` / `cursor` / `poll` / `dataset_id` / `state` / `scope` / `proposed_by` / `at` / 项目级 `date_from` / 项目级 `date_to`；有界：`/cost/daily` 的 `date_from` / `date_to`（`max_length=10`） |
| 4 | **另实测排除**：非法枚举值 ⇒ 空集是**既有设计** | `rg -n "不猜" services/api/routers/memory.py` | 「**未知作者 ⇒ 空集**（**不猜**、**不**当全选）」（序 35/36 立）⇒ **不是**缺口，本轮**不**动 |
| 5 | 影响面（web/tests 是否发超长值） | EC-01 ③ | （勘察读数 —— 预期零命中；web 客户端参数来自用户输入但长度自然受限） |
| 6 | 缺省基线 | 探针第 4 段 | （勘察读数 —— 不传参数的状态码 + 键集，供「逐字不变」比对） |

**结论**：五面已接通，而**长度界**读面 **10/16 条缺失** ⇒ **读面不设界、写面设界**的不一致。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 补界方式 = **在路由签名里声明 `max_length=…`**（不是自造校验臂） | 与**已界**的 `date_from` **同形** ⇒ 框架校验面自动生效、错误形态与既有 422 一致（一处声明、逐路由可读） | 已定 |
| D-2 | 界值取**与同类字段一致**的量级（写面 `max_length` 的既有口径；逐条在 PLAN 里明写） | 「同类形态同界」比自造数字可辩护；如实测需要调整则逐条登记理由 | 已定 |
| D-3 | **缺省与合法值逐字不变**；已界参数与 `list` 声明**一字不动** | 一贯纪律 + 射程边界 | 已定 |
| D-4 | 快照**预期会变**（`maxLength` 进 schema）⇒ **同轮**重生成 + 提交 | 与序 38 同形（如实登记为预期） | 已定 |
| D-5 | **不**动「非法枚举值 ⇒ 空集」（实测确认是文档化设计） | 「未知 ⇒ 空集，不猜」是序 35/36 立的**有意**语义；改它是**语义变更**，不属本轮 | 已定 |

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
**计数/取值面要用 `multi_items()` 而非 `keys()`**（序 42 的 ★ 教训）；
**按压锚点要先验形态**（缩进 / 唯一性 —— 序 43 的现场兑现）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：10 条参数的既有调用 + 快照消费者）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：已声明查询参数补显式长度界（读面与写面在「长度」这一形态上一致）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：作者鉴权 / 通配·模糊匹配 / `provenance` 在编排面的披露 /
  **内容级检测**（`W-2`）/ 三维以上闸门组合；`BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` /
  `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5` /
  **非法枚举值 ⇒ 空集**（**实测确认是文档化设计**，改它属语义变更）。
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
| 0 | —（实测缺口登记 + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 44**（**同轮建档**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 补界 + 影响面处理） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | ACTIVE | **实测缺口登记 + 建档（cycle 0）**：MAINLINE 程序表**新增序 44**（**轴 = 质量**），并写修订记录行（只追加；同轮把序 41 的旧修订行原文搬入新归档）。**实测读数**（逐条见「事实层结论」表）：① 超长值在无界参数 ⇒ **200**（`endpoint_id` / `state`）；② 对照臂：有界参数（`kind`）与写面（`name`）⇒ 422；③ **长度界盘点：10/16 条无界**；④ **另实测排除**：非法枚举值 ⇒ 空集是**文档化设计**（序 35/36 立）⇒ 非缺口。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**动五面 / **不**动已界参数 / **不**改枚举语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
