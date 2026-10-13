---
id: GOAL-20261013-071
slug: typos-in-write-body-field-names-are-no-longer-silently-dropped
title: >-
  写面请求体里打错的字段名不再被静默吞掉 —— 序 37/38 把「未知查询参数」的纪律做成两条读面事实
  （签名导出 + 全员覆盖），而**实测**：**写面**（POST/PUT 的 JSON 体）打错字段名**照样 200**
  （`{"protocol_path": ..., "trace_di": "typo"}` ⇒ 200，typo 字段**无声丢弃**）
  ⇒ 调用方**以为设了那个字段**。本轮给**已声明的写面 DTO** 声明「未知字段 ⇒ 422 + 点名该字段」
  （pydantic `extra="forbid"` 形态），**已知/缺省形态逐字不变**；落地前先做**全量盘点**
  （web / tests 有没有依赖「多余字段被忽略」这一既有行为）
status: ACTIVE
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-13 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 39**，由本次**实测缺口**驱动（非 replan 到期 —— 上次 replan 产出序 38）。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑** ⇒
    `POST /projects/example-project/runs` 带 `{"protocol_path": "…", "trace_di": "typo"}`
    ⇒ **200**（typo 字段**无声丢弃**）；对照 `{"protocol_path": "…"}` ⇒ 200（正确形态）。
    这与序 36/37/38 的靶子同族（「静默吞掉 ⇒ 调用方以为设了」），**落点从读面转到写面**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 读面已经三条连接通
    （36/37/38），而写面的同族缺口**仍然静默**；本 GOAL 把纪律**机械扩到写面**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：给**已声明的写面 DTO** 声明
    「未知字段 ⇒ 422 + 点名**那个字段**」，**已知/缺省形态逐字不变**（正确请求的响应与
    副作用一字不动）。做法由 EC-01 实测选定（`extra="forbid"` vs 逐路由校验）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**动**查询参数**面（序 37 的守卫与判据由收口断言集钉住）；
    **不**动响应体形态；**不**把 `extra="forbid"` 装到**响应**模型上（那是另一面）；
    **不**改**未声明**路由（GET 无参数面）的既有行为。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（写面缺口与影响面）**：`scratch/probe-write-face-extra-fields.py` 逐条读出 ——
      ① **实跑**：带打错字段名的请求 ⇒ **200 + 无声丢弃**（点名那条，附正确形态对照）；
      ② **全仓盘点**：所有**写面 DTO**（`services/api/dto/*.py` 的请求模型）**逐条清单**
      （文件名 + 类名 + 是否已 `extra` 设定）；③ **影响面盘点**：web（`apps/web/src/api/*.ts`）
      与 tests 里**是否有任何**写请求带**非声明字段**（有 ⇒ 落地前必须先处理，点名列出）；
      ④ **错误形态基线**：正确请求的响应/副作用（状态码 + 关键键）逐条记录（供「逐字不变」比对）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-write-face-extra-fields.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **纪律扩到已声明的写面 DTO（本轮验收主体）**：未知字段 ⇒ **422 + 点名那个字段**
      （多个未知**逐个点名**）；**已知/缺省形态逐字不变**（EC-01 ④ 的基线逐条对照）；
      做法由 EC-01 实测选定并**写在 GOAL 里**（`extra="forbid"` 形态优先 —— 一次声明全 DTO 生效）。
      **盘点面（EC-01 ③）里发现的既有依赖必须逐条处理**（点名：地址 + 处置）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（逐 DTO 点名 / 多个逐个 / 已知不变 / 缺省不变）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **射程如实 + 既有面不回归**：**查询参数**面（序 37/38 的判据）不回归；
      正确请求的**响应体与副作用**逐字不变；若动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`（**预期会变** —— `extra="forbid"` 会进 schema 的
      `additionalProperties: false`；如实登记）；web（`apps/web`）既有调用**全绿**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 新用例（对照组 / 查询参数面回归 / 快照同步）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`X-1` 未知字段**又被静默忽略**
      （退回归零）⇒ RED；`X-2` **已知字段被误拒**（禁得太宽 ⇒ 正确请求 422）⇒ RED；
      `X-3` **多个未知只报第一个** ⇒ RED；`X-4` 错误**正文不点名**（只给通用消息）⇒ RED。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；**反证脚本带基线门**；
      判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal071_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-071-press-two-way.txt`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 39**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal071_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-451-goal-071-ec01-05-typos-in-write-body-field-names-are-no-longer-silently-dropped.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261013-071 — 写面请求体里打错的字段名不再被静默吞掉

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 39**（轴 = **质量**；依赖序 38
> —— 已收口）。**本行由实测缺口驱动**（非 replan 到期 —— 上次 replan 产出序 38），
> 已在 MAINLINE「修订记录」留痕；**GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（实跑缺口 / 写面 DTO 清单 / 影响面盘点 / 正确形态基线） | **实跑**：`scratch/probe-write-face-extra-fields.py` | PENDING |
| EC-02 | 未知字段 422 + 点名；已知/缺省逐字不变；盘点面逐条处理 | `pytest tests/api -q` + 新用例 | PENDING |
| EC-03 | 射程如实（查询参数面不回归）+ 快照同轮（**预期会变**）+ web 全绿 | `pytest tests/api tests/contracts tests/tooling -q` | PENDING |
| EC-04 | 两向反证 `X-1`…`X-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：打错字段名 ⇒ **200 + 无声丢弃** | `TestClient` + 真实装配 | `{"protocol_path": "…", "trace_di": "typo"}` ⇒ **200**（typo 字段无任何披露） |
| 2 | 正确形态对照 | 同上 | `{"protocol_path": "…"}` ⇒ 200（正常冻结/启动） |
| 3 | 现有 `extra` 设定 | `rg -n 'extra=' services/api/dto/` | （勘察读数：见 EC-01 ③） |
| 4 | 影响面（web/tests 是否带非声明字段） | 逐条盘点（EC-01 ③） | （勘察读数） |

**结论**：读面已三条连接通（序 36/37/38），**写面的同族缺口仍然静默** ——
调用方打错字段名**不报错、不点名**。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 做法 = **`extra="forbid"` 形态**还是逐路由校验，由 EC-01 实测选定 | `extra="forbid"` 一次声明全 DTO 生效（DRY），但要**先量**影响面（web/tests 有没有带多余字段的调用） | **待 EC-01** |
| D-2 | 未知字段 ⇒ **422 + 逐个点名**（与读面同形） | 与序 37 的「点名而非静默降级」同口径 | 已定 |
| D-3 | **已知/缺省形态逐字不变**（正确请求的响应与副作用） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | 快照**预期会变**（`extra="forbid"` 进 schema）⇒ **同轮**重生成 + 提交 | 与序 38 同形（如实登记为预期） | 已定 |
| D-5 | **不**把 `extra="forbid"` 装到**响应**模型 | 响应由我们生成 ⇒ 禁字段没有调用方受益面 | 已定 |

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
进程卫生（Windows `taskkill /T /F` + 复验零泄漏）；**显式路径 `git add` 后必须复核 `git status`**
（★ **改判据文件之后必须重跑 `ruff format`** —— 序 38 本地门两次抓到的真红形态）；
**批量替换前先数锚点命中数**（`== 1` 才替换）；**判据要判调用形态而非散文字符串**
（序 38 的 `query_params` 短语教训）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：**所有写面 DTO** + web/tests 的写调用）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：写面请求体里打错的字段名不再被静默吞掉（未知字段 ⇒ 422 + 点名）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**无查询参数**路由的参数检查（另成一面）/ 作者鉴权 /
  通配·模糊匹配 / `provenance` 在编排面的披露 / **内容级检测**（`W-2`）/ 三维以上闸门组合；
  `BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` /
  `R-*` / `Q-*` / `P-*` / `O-1`…`O-5`。
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
| 0 | —（实测缺口登记 + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 39**（**同轮建档**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 DTO 声明 + 盘点面处理） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | ACTIVE | **实测缺口登记 + 建档（cycle 0）**：MAINLINE 程序表**新增序 39**（**轴 = 质量**），并写修订记录行（只追加；同轮把序 36 的旧修订行原文搬入新归档）。**实测读数**（逐条见「事实层结论」表）：① 打错字段名 ⇒ **200 + 无声丢弃**（`trace_di` typo）；② 正确形态对照 200。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**动查询参数面 / **不**动响应模型 / **不**改未声明路由。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
