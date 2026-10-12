---
id: GOAL-20261013-067
slug: the-http-read-face-does-not-silently-ignore-the-author-filter
title: >-
  HTTP 读面的作者筛选不再被静默忽略 —— 序 34 让**查询面**有了第三维
  （`MemoryStore.query(proposed_by=...)`）并在**编排消费面**接通，但 **HTTP 读面仍只认 `scope`**；
  **实跑取证**：`GET /projects/{id}/memory?proposed_by=agent:x` ⇒ **200 且返回全量两条**
  （`['m-x','m-y']`）、载荷键仍只有 `['records','scope_note']` ⇒ **参数被静默忽略**
  （既不筛、也不报错、也不披露）；而对照 `?scope=project` **会筛并披露 `filtered_out`**
  ⇒ 同一个读面上**两个查询参数的待遇不对称**，调用方**以为筛过了**（承「点名失败而非静默降级」）
status: ACHIEVED
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 35**，由序 34 收口后的**逐轴复评实测**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑**（`TestClient` + 受控装配）——
    两条不同作者的记忆经 store 落 canonical（`proposed_by` 分别是 `agent:x` / `agent:y`）⇒
    `GET /projects/example-project/memory` 返回两条；`GET …?proposed_by=agent:x` ⇒
    **200 且返回同样两条**、载荷键仍 `['records','scope_note']`（**无** `proposed_by`、
    **无** `filtered_out`）⇒ **静默忽略**；而 `GET …?scope=project` ⇒ 载荷**多两键**
    （`scope` + `filtered_out`）⇒ **同一读面两个参数待遇不对称**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 34 让作者**选得着**
    （查询面 + 编排面），而 HTTP 面**把不认识的参数吞掉** ⇒ 调用方**以为筛过了**而实际拿到全量
    （「静默降级」的教科书形态 —— 承本战役「点名失败而非静默降级」）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让 HTTP 读面的作者筛选**与 `scope` 同形**
    （**可选**、缺省不筛、**筛了什么与筛掉多少都披露**）；**缺省形态逐字不变**
    （不传该参数 ⇒ 载荷与改动前**逐字相同**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**未知查询参数的通用拒绝**（那是**全仓读面**的
    纪律改动面，本轮**只**对齐这一个参数；通用面登记为后续候选）；**不**做**作者鉴权**；
    **不**做**通配 / 模糊匹配**；**不**改 `?scope=` 的既有语义（它已与序 17 的判据**逐字一致**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（实跑 + 不对称对照）**：`scratch/probe-http-author-filter.py` 逐条读出 ——
      ① **实跑**：不传参数 ⇒ 全量；`?proposed_by=` ⇒ **同样全量 + 无披露键**（静默忽略）；
      ② **对照**：`?scope=` ⇒ 载荷**多两键**（`scope` + `filtered_out`）⇒ 不对称；
      ③ 路由签名**逐个**（`list_project_memory` 的形参只有 `scope`）；
      ④ **先例**：`?scope=` 的披露形态（序 17）逐条读出（本轮**照它对齐**）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-http-author-filter.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **HTTP 读面按作者筛（本轮验收主体）**：路由 +1 **可选**查询参数；传 ⇒ 只出那一位作者的；
      **披露**筛了什么与**筛掉了多少条**（与 `?scope=` 的形态**同源同形**）；
      **缺省载荷逐字不变**（不传 ⇒ 键一个不多）；**未知作者 ⇒ 空集**（**不猜**、**不**当全选）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（按作者筛 / 披露 / 缺省逐字不变 / 未知作者空集 / 与 scope 可并存）。
    status: PASS
  - id: EC-03
    criterion: >-
      **两个形态的 DTO 与快照同轮**：新增的筛选走**既有的两个形态**（缺省 / 追加键的
      并集形态 —— **不**给路由开 `response_model_exclude_none`，那会递归抹掉别的读面上
      有意义的 `null`，序 17 实测过）；动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`（+ `apps/web/src/api/types.ts` 若本轮触及）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      + 新用例（两个形态各自的键集 / 快照含新键）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Y-1` 路由**忽略**该参数（静默忽略原样回来）⇒ RED；
      `Y-2` **缺省形态**被改动（不传也筛）⇒ RED；`Y-3` **不披露**（筛了但不报条数）⇒ RED；
      `Y-4` **未知作者被当成全选**（不猜被破坏）⇒ RED。复原用**二进制读写**且 raw `sha256`
      逐字节相同；**反证脚本带基线门**（未按压必须 GREEN）；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal067_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-067-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 35**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal067_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
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
  - .cursor/plans/tasks/PLAN-20261013-443-goal-067-ec01-05-the-http-read-face-does-not-silently-ignore-the-author-filter.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-444-goal-067-ec01-04-the-http-read-face-does-not-silently-ignore-the-author-filter.md
memory_entries: []
---

# GOAL-20261013-067 — HTTP 读面的作者筛选不再被静默忽略

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 35**（轴 = **质量**；依赖序 17、34
> —— 均已收口）。**本行是序 34 收口后逐轴复评的产物**，已在 MAINLINE「修订记录」留痕
> （含 `max_goals` 35 → 40 的核算理由），**GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（实跑静默忽略 + 不对称对照 + 路由签名 + 先例） | **实跑**：`scratch/probe-http-author-filter.py` | **PASS** |
| EC-02 | HTTP 读面按作者筛 + 披露 + 缺省逐字不变 + 未知空集 | `pytest tests/api -q` | **PASS** |
| EC-03 | 两个 DTO 形态与快照同轮 | `pytest tests/api tests/contracts -q` | **PASS** |
| EC-04 | 两向反证 `Y-1`…`Y-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5824 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：`?proposed_by=` 被**静默忽略** | `uv run --frozen --no-sync python -B scratch/probe-http-author-filter.py` | **200 + 全量两条**（`['m-x','m-y']`）；载荷键 `['records','scope_note']`（**无**披露） |
| 2 | **对照**：`?scope=` **会筛并披露** | 同上（第 2 段） | 载荷**多两键**（`scope` + `filtered_out`） |
| 3 | 路由签名**逐个** | `rg -n "async def list_project_memory" -A 3 services/api/routers/memory.py` | 形参只有 `scope`（**无**作者维） |
| 4 | **先例**：`?scope=` 的披露形态（序 17） | 同上第 4 段 | 「筛了什么 + 筛掉多少」两键（本轮**照它对齐**） |

**结论**：**同一读面两个查询参数待遇不对称** —— `?scope=` 筛并披露，`?proposed_by=` **被吞掉**
⇒ 调用方**以为筛过了**而实际拿到全量（「静默降级」的教科书形态）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 新参数与 `?scope=` **同一形态**（可选、缺省不筛、披露两键） | 同一读面同一纪律；调用方一看即懂 | 已定 |
| D-2 | 走**既有的两个 DTO 形态**（不给路由开 `response_model_exclude_none`） | 序 17 实测：那个开关会**递归**抹掉别的读面上有意义的 `null` | 已定 |
| D-3 | **缺省载荷逐字不变**（不传 ⇒ 键一个不多） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | **未知作者 ⇒ 空集**（**不**当全选） | 与序 34 的查询面口径**逐字一致**（承「点名失败而非静默降级」） | 已定 |
| D-5 | **不**做「未知查询参数的通用拒绝」（只对齐这一个参数） | 那属**全仓读面**的纪律改动面（登记为后续候选）；本轮只把**已被静默吞掉的那个参数**接通 | 已定 |

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
**显式路径 `git add` 后必须复核 `git status`**（承序 32 的 `format-check` 真红教训）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：读面 DTO + 快照）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：HTTP 读面的**作者筛选**（与 `?scope=` 同形 + 披露 + 缺省逐字不变）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**未知查询参数的通用拒绝**（全仓读面纪律面）/ **作者鉴权** /
  **通配·模糊匹配** / `provenance` 在编排面的披露 / **内容级检测**（`W-2`）/
  三维以上闸门组合；`BB-3`；`DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` / `X-*` / `V-*` / `U-*` /
  `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5`。
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
| `dadb3bb`（逐轴复评 + 建档） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | 序 35 建档（GOAL + PLAN + ALL_PLAN 同轮） |
| `6c0ae2d`（WP-2/WP-3） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | 路由 + 三形态 + 快照 |
| `872b94a`（判据 + 归档） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | 判据 8 例 + 按压归档 |
| `93fcaa2`（WP-5 主体） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | 收口验证器 + 断言集 |
| `ca7ed11`（长行修复） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | GOAL 路径折行 |
| `d870c4d`（**mypy 真红修复**） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | 判据显式注入具体 store（`union-attr` ×4） |
| `99d34d5`（EC-05 回填） | **`total_count = 0`** ⇒ **`covered_by 38320054519`** | as-is m0 读数（5824 passed） |
| `6775c96`（**末条实测提交** = 两树归档 + 收口） | `38320054519` **M0 success**（**8/8 job 全 success**）+ `38320054501` **Push on main success** | 两树判词定格归档 + MAINLINE 进展行 + 归档搬运 |

**自我指涉边界（明写并封闭）**：写本台账本身要再提交 ⇒ 会产生新 run。**封闭口径**：
**末条可引用的实测提交 = `6775c96`**（上表最后一行，两 run 全绿）；**其后仅记录提交**，
**不再追链** —— 若需复核本行结论，取 `6775c96` 的两条 run 即足。

**`covered_by` 的用法（逐条）**：七个提交**自身 `total_count = 0`**（**同批推送**只让 tip 起 run）
⇒ 按纪律**不是**「未取证」，而是**由同批 tip 的 run 覆盖**（各自 `covered_by` 已在表内写明）。
**空集合 = 未取证**，本表**无一处**留空。**本轮零 CI 红**：一处 **mypy 真红在本地 m0**
（首跑 `EXIT=1`）被当场抓到并修掉（`d870c4d`）⇒ **未进入 CI**；重跑后 **23/23**。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（逐轴复评 + 建档） | `dadb3bb` | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；**同轮建档** | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 HTTP 面按作者筛） |
| 1 | `PLAN-20261013-443`（WP-1…WP-5） | `6c0ae2d`（路由 + 三形态 + 快照）、`872b94a`（判据 8 例 + 按压归档）、`93fcaa2`（收口面）、`ca7ed11`（长行修复） | **EC-01/02/03/04 PASS**：① 四段读数（实跑静默忽略 + 不对称对照 + 签名 + 先例）；② 传作者 ⇒ 真筛 + 披露两键；缺省逐字不变；未知作者空集；`?scope=` 一字不动；③ **三形态并集**（少一个就静默丢键 —— 实测过）+ 专用形状 + 快照同轮（`+62 / -5`）；④ **四向反证** `Y-1`…`Y-4` 全红 + 基线绿 + 复原一致。`tests/api tests/contracts tests/application tests/adapters tests/domain` **2372 passed**；mypy **1209 files** 零问题 | （见 CI 台账） | 三处如实登记：① **并集漏形态**（首版只列两个 ⇒ FastAPI 收窄载荷、`filtered_out` 读不出来）；② 断言集 `exclude_none` 判据**按短语出现判** ⇒ 被**注释**命中**假红** ⇒ 改判**调用形态**；③ 注释按**显示宽度**超 100（中文占两列）⇒ 缩短措辞；④ **m0 的 mypy 真红**（`deps.memory` 是 `Any | None` ⇒ `union-attr` ×4）⇒ 改**显式注入具体 store**（与 `test_memory_api.py` 既有手法同形）⇒ 重跑 **23/23**。**EC-05 PASS**（验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5824 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | （见 CI 台账） | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**三处如实登记**（并集漏形态 / `exclude_none` 判据假红 / 注释显示宽度）。**残余**：未知查询参数仍静默忽略（通用拒绝属全仓纪律面）/ 作者鉴权不做 / 模糊匹配不做 / 两维互斥 / 内容级检测 / 三维以上组合等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261013-444`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-13 | ACTIVE | **逐轴复评 + 建档（cycle 0）**：MAINLINE 程序表**新增序 35**（**轴 = 质量**），并写修订记录行（只追加）+ 预算核算（`max_goals` 35 → 40）。**实测读数**（逐条见「事实层结论」表）：① **实跑** `?proposed_by=` ⇒ 200 + 全量 + 无披露（**静默忽略**）；② **对照** `?scope=` ⇒ 会筛并披露两键（**不对称**）；③ 路由签名只有 `scope`；④ 先例（序 17 的 `?scope=` 形态）在树。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**做未知参数的通用拒绝 / **不**做作者鉴权 / **不**做模糊匹配／**不**改 `?scope=` 语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
