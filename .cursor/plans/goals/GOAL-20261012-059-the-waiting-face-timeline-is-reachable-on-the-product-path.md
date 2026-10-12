---
id: GOAL-20261012-059
slug: the-waiting-face-timeline-is-reachable-on-the-product-path
title: 等待面的时限链在产品面上可达 —— 序 24 让等待面**有始点、能判超期**（`gate_nudge_after_seconds`）、序 25 让那条信号**有可注入的出口**，但**实跑取证**整条链是**三层断的**：① 声明面（`ProgramCreateDto` / `ProgramDetailDto`）**没有**该键 ⇒ 界**声明不出来**；② 两库 round-trip **静默丢弃**（实测：进程内声明 `60` ⇒ 落库读回 `None`）⇒ 界**存不下来**；③ `services/` 对 `nudges=` / `NudgeSink` **零命中** ⇒ 出口**从不被注入** ⇒ 「等待面有始点、可催办」在产品面上**不可达**（只在进程内测试里成立）
status: ACHIEVED
created_at: 2026-10-12
updated_at: 2026-10-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 27**，由本次 replan 的**实测读数**驱动（本次按「按实测残余量出缺口」量出
    「时限链在三层上都断」）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改域声明 / 新增列与迁移 / DTO / 组合根注入 / 新增判据），**不等于**可以放宽
    **判据、门禁、阈值或断言**。**push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：(a) 声明面 `rg -n "gate_nudge"
    services/api/dto/programs.py` ⇒ **零命中**；(b) 落库面 `scratch/probe-nudge-reachability.py`
    **实跑** ⇒ 进程内声明 `60`、round-trip 读回 `None`（**静默丢弃**），两库 `rg -n gate_nudge
    adapters/*/program_store.py` ⇒ **零命中**；(c) 出口面 `rg -n "nudges=|NudgeSink" services/`
    ⇒ **零命中**。⇒ **三处都没接线**：界声明不出来、存不下来、出口从来不注入 ⇒
    序 24/25 的产物**只能在进程内测试里成立**。
    (2) **为什么属连续性轴**：轴的反面是「只加了入口而没有可恢复的实跑」—— 序 24/25 建了
    「等太久」的**信号与出口**，而**产品面上没有任何东西能到达它们** ⇒ 中断-恢复闭环的
    **推**侧**实为悬空**。本轮把它接通（不是新造机制）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让这条链**在产品面上可达** ——
    界**可声明**（建程序面 + 读面透传）、**可落库**（两库同契约 + 迁移只加列）、
    **出口可注入**（组合根决定；缺省仍静默）；**缺省形态的既有行为逐字不变**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做真实外发（邮件 / webhook / IM）；**不**做升级链；
    **不**做重试 / 去重 / 投递保证（端口语义一字不动 —— 只保证「信号被交给实现」）；
    **不**做自动放行 / 自动拒绝（超期仍**只点名**「决定权仍在人」）；
    **不**改序 24 的超期判定语义、**不**改序 25 的端口形状与三态纪律。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（三层面逐段实跑）**：`scratch/probe-nudge-reachability.py` 逐条读出 ——
      ① 声明面两个 DTO 的字段表（`model_fields` 逐个读出，键不在）；② 落库面 round-trip
      （进程内声明 `60` ⇒ 读回 `None`，**静默丢弃**）；③ 出口面 `services/` 零命中；
      ④ 迁移目录逐条读出（无该列的迁移）；⑤ 序 24/25 的既有产物在树（判定语义 / 端口 /
      缺省实现**逐条在位**，本轮**一字不动**）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-nudge-reachability.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **界可声明、可落库**：`ProgramCreateDto` 与 `ProgramDetailDto` 各 +1 **可选**键
      （缺省 `None` ⇒ **既有行为逐字不变**）；两库（SQLite `_SCHEMA` + `_ensure_compatible_schema`
      加法式，PG 迁移 `024` 只加列 + `INSERT` / `_PROGRAM_SELECT` 带列）同契约 round-trip
      **声明值原样读回**；**域校验逐字不动**（非正整数仍点名拒绝）。坏形态**点名**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api tests/domain -q`
      ⇒ 全绿 + 新用例（两库往返 / 缺省逐字不变 / 坏界点名）。
    status: PASS
  - id: EC-03
    criterion: >-
      **出口可注入（组合根决定；缺省静默）**：组合根的依赖面 +1 可注入字段（缺省
      `NullNudgeSink` ⇒ 逐字不变），推进路由把界与出口一起交给既有推进入口；
      **只读判定面仍只读**（序 12/14 起的判据钉住）；**不**改端口形状 / **不**做真实外发。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/application tests/architecture -q`
      ⇒ 全绿 + 新用例（注入后收到 / 未注入静默 / 只读面无写方法）+ OpenAPI 快照**同轮**重生成。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`V-1` 落库**去掉新列** ⇒ RED；
      `V-2` DTO **摘掉新键** ⇒ RED；`V-3` 组合根**不注入**（回到零命中形态）⇒ RED；
      `V-4` 三态纪律被改动（缺省也送）⇒ RED。复原用**二进制读写**且 raw `sha256`
      逐字节相同；**反证脚本带基线门**（未按压必须 GREEN，否则非 0 退出）；
      判词归档进树（`.cursor/plans/goals/evidence/`，`CR=0`）。
    verify: >-
      `scratch/goal059_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261012-059-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 27**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal059_closeout.py` ⇒ 全 `PASS`；
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
  - 触达 D 组审批通道 / 真实外发（邮件 / webhook / IM）/ 读面认证 / 多租户
  - 需要放开默认网络 / 需要真实凭据
child_plans:
  - .cursor/plans/tasks/PLAN-20261012-427-goal-059-ec01-05-the-waiting-face-timeline-is-reachable.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-428-goal-059-ec01-04-the-timeline-chain-is-reachable.md
memory_entries: []
---

# GOAL-20261012-059 — 等待面的时限链在产品面上可达

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 27**（轴 = **连续性**；依赖序 24/25
> —— 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 24/25/26 收口后到期），
> 已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿：三段读数（声明面 / 落库面 / 出口面）逐段实跑 + 序 24/25 产物在位 | **实跑**：三段读数**逐条与改动前相反**（RECHECK-428 §1） | **PASS** |
| EC-02 | **界可声明、可落库**（两 DTO +1 可选键；两库同契约 round-trip；坏形态点名） | 新用例 **19 passed**（SQLite 14 + PG 5）；快照同轮（`+23 / -0`） | **PASS** |
| EC-03 | **出口可注入（组合根决定；缺省静默）**+ 快照同轮 | 产品路径新用例 **4 passed**（经 HTTP 面注入 ⇒ 出口真收到） | **PASS** |
| EC-04 | **两向反证** `V-1`…`V-4` 全红 + 基线门 + 二进制复原 `sha256` 一致 | 归档 **691 B / `CR=0`**；`all_red_and_restored=True` | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器 **66 判词 / 0 FAIL**；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5704 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 声明面**没有**该键 | `rg -n "gate_nudge" services/api/dto/programs.py` | **（零命中）** |
| 2 | 落库面**静默丢弃** | `uv run --frozen --no-sync python -B scratch/probe-nudge-reachability.py` | 进程内 `60` ⇒ round-trip 读回 **`None`** |
| 3 | 两库**都没有**该列 | `rg -n "gate_nudge" adapters/sqlite/program_store.py adapters/postgres/program_store.py` | **（零命中）** |
| 4 | 迁移目录**没有**该列的迁移 | `ls adapters/postgres/migrations/ \| tail -3` | 最新三条 = `021` / `022` / `023`（无该列） |
| 5 | 出口面**零命中**（组合根从不注入） | `rg -n "nudges=\|NudgeSink" services/` | **（零命中）** |
| 6 | 序 24 的判定语义**在树**（本轮一字不动） | `rg -n "等太久了\|决定权仍在人" packages/application/run_orchestration/program_waiting.py` | 两句都在 |
| 7 | 序 25 的端口与缺省实现**在树**（本轮一字不动） | `rg -n "class NudgeSink\|class NullNudgeSink\|class NudgeNotice" packages/application/ports/nudge_sink.py` | 三个都在 |

**结论**：**信号与出口都建好了，但产品面上没有任何东西能到达它们** —— 界**声明不出来**
（DTO 无键）、**存不下来**（两库无列、静默丢弃）、出口**从不被注入**（组合根零命中）
⇒ 序 24/25 的产物**只能在进程内测试里成立**。**这是「只加了入口而没有可恢复的实跑」的
直接形态**（连续性轴的反面），而修法**不是新造机制**——三段先例都已全在
（`human_gate_at_indexes` 的 DTO+两库+迁移形态、`TelemetrySink` 的组合根注入形态）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 界**可声明**（`ProgramCreateDto` + `ProgramDetailDto` 各 +1 可选键） | 与三种闸门声明**同一形态**（缺省 `None` ⇒ 逐字不变）；不新造声明语义 | 已定 |
| D-2 | 界**可落库**（SQLite 加法式列 + PG 迁移 `024` 只加列） | 与 `022`（多点闸门）**同一手法**；`NULL` = 未声明（与 `[]` 语义不同） | 已定 |
| D-3 | 出口**由组合根决定注入**（缺省 `NullNudgeSink`） | 与 `TelemetrySink` 的注入点**同一先例**；缺省静默 ⇒ 逐字不变 | 已定 |
| D-4 | 超期仍**只点名**「决定权仍在人」（**不**自动放行 / 拒绝） | 序 24 的语义**一字不动**；本 GOAL 只接通，不改判定 | 已定 |
| D-5 | 端口形状与三态纪律**一字不动**（不加重试 / 去重 / 外发） | 序 25 的 `escalation_triggers` 已先写死「不做真实外发」 | 已定 |
| D-6 | 组合根注入的**具体落点**（`ApiDeps` 字段 vs 独立注入）由 EC-01 读装配链后定 | 涉及既有 `ApiDeps` 字段面 ⇒ 先量再定 | **待 EC-01** |

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
**未实跑不得记 PASS**；进程卫生（Windows `taskkill /T /F` + 复验零泄漏）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：两个 DTO + 两库 + 迁移 + 组合根）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：`Z-3` 的**产品面可达性**（信号 + 出口**真的接得上**；三段接线不是新造机制）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**真实外发**（邮件 / webhook / IM）/ **升级链** /
  **重试·去重·投递保证**；`Z-1` 的**混合式**；`W-2` 的**内容级**检测；`CC-2`·`CC-3`；
  `BB-3`；`DD-1`…`DD-3`；`AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` /
  `Q-*` / `P-*` / `O-1`…`O-5`。
- **未覆盖范围（逐条明写）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器。
- **明确否认**：投递语义**不是**「恰好一次」（口径只能是 at-least-once + idempotency +
  deduplication）—— 本 GOAL 只保证「信号被交给实现」，**不**保证送达、**不**做重试。
- **观测隐私（逐条明写）**：送进端口的载荷**只含**结构化摘要（标识 / 计数 / 判词片段），
  **不含**完整 Prompt / 模型输入输出 / 内容原文 / 凭据（AGENTS.md §10）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**（并写明 `covered_by`）；`cancelled` / `failure` 如实登记
> + 原因 + `covered_by`。**自我指涉边界**：台账提交自身不产生可引用的 CI 结论
> （明写并以「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| 提交 | CI run / 结论 | 覆盖的 WP |
| --- | --- | --- |
| `107e9e7`（derive：PLAN + ALL_PLAN + 程序表序 27/28/29） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | replan + 建档 |
| `75f761e`（WP-2/WP-3） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | 界可声明可落库 + 出口可注入 + 快照同轮 |
| `44e8946`（WP-4） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | 产品路径判据 + 四向反证归档 |
| `bcf426c`（WP-5 主体） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | 收口验证器 + 断言集进树 + 射程纯收紧 |
| `f6287dd`（收口记录） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | EC 回填 + RECHECK-428 + MAINLINE 进展行 |
| `75d67b0`（m0 真红修复） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | import 排序 / format / 复用名导入 |
| `1f83566`（EC-05 回填） | **`total_count = 0`** ⇒ **`covered_by 38242418003`** | as-is m0 23/23 读数 |
| `c28deac`（**末条实测提交** = 两树归档） | `38242418003` **M0 success**（**8/8 job 全 success**）+ `38242417665` **Push on main success** | 两树判词定格归档 |

**自我指涉边界（明写并封闭）**：写本台账本身要再提交 ⇒ 会产生新 run。**封闭口径**：
**末条可引用的实测提交 = `c28deac`**（上表最后一行，两 run 全绿：M0 `38242418003` 8/8 +
Push on main `38242417665`）；**其后仅记录提交**，**不再追链** —— 若需复核本行结论，
取 `c28deac` 的两条 run 即足。

**`covered_by` 的用法（逐条）**：七个提交**自身 `total_count = 0`**（**同批推送**只让 tip 起 run）
⇒ 按纪律**不是**「未取证」，而是**由同批 tip 的 run 覆盖**（各自 `covered_by` 已在表内写明）。
**空集合 = 未取证**，本表**无一处**留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（replan + 建档） | `107e9e7` | 只读勘察（0 改动）+ **三段实测读数**（声明面零命中 / 落库静默丢弃 / 出口零命中）⇒ 定位时限链的三层断点 | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 声明 + 落库） |
| 1 | `PLAN-20261012-427`（WP-1…WP-3） | `107e9e7`（derive）、`75f761e`（界可声明可落库 + 出口可注入 + 快照同轮） | **EC-01/02/03 PASS**：三段接线逐段落地 —— ① 声明面两 DTO +1 可选键（缺省 `None` ⇒ 逐字不变）；② 落库面 SQLite 加法式列 + PG 迁移 `024` 只加列 + 两条 SELECT 带列；③ 出口面组合根 +1 可注入字段（缺省 `NullNudgeSink`）+ 推进路由交出。`tests/adapters tests/domain tests/api tests/application tests/contracts` **3104 passed / 80 skipped**；PG **5 passed** | （见 CI 台账） | 三处自纠（如实登记）：① e2e 共享助手需 +1 可选 kwarg（**加法式**，缺省不发键 ⇒ 既有请求逐字不变）；② 新用例初版误用 harness 预建行（`INSERT OR IGNORE` ⇒ 二次建是静默空操作）⇒ 改直写一行；③ 断言集两处 ruff 门（长行 + 引号风格）⇒ 抽局部变量 | EC-04/05 待做 | cycle 2（EC-04 按压 + EC-05 收口） |
| 2 | `PLAN-20261012-427`（WP-4、WP-5） | `44e8946`（产品路径判据 + 四向反证归档）、`bcf426c`（收口验证器 + 断言集进树 + PG 判据）、本轮回写提交 | **EC-04 PASS**：`V-1`…`V-4` **全红** + 基线 **GREEN** + 四条 `sha 复原一致=True`；**首轮 `V-3`/`V-4` 按 GREEN ⇒ 两条反证臂失效**，按「该红时红」改判据面后全红（**如实登记** —— 这正是该纪律的现场兑现）。**EC-05 PASS**（验证器 **66 判词 / 0 FAIL**；两树 **`TWO-TREE PASS`**；as-is m0 **23/23** （`PASS [` 24 / `FAILED [` 0 / **5704 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | `c28deac`：M0 `38242418003` **8/8** + Push on main `38242417665` **success**；同批七条提交 `total_count = 0` ⇒ `covered_by` 逐条写明 | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**两处如实登记**：① `V-3`/`V-4` 首轮按 GREEN（反证臂失效）⇒ 改判据面后全红；② 新用例初版误用 harness 预建行（`INSERT OR IGNORE` 静默空操作）⇒ 改直写。**残余**：真实外发 / 投递保证 / `Z-1` 混合式 / `W-2` 内容级检测 / `CC-3` 等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261012-428`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-12 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 27**（**轴 = 连续性**），并写修订记录行（只追加）。**三段实测读数**（逐条见「事实层结论」表，命令与读数同在）：(a) 声明面两个 DTO **无该键**；(b) 落库面 round-trip **静默丢弃**（`60` ⇒ `None`）；(c) 出口面 `services/` **零命中**。⇒ **信号与出口建好了，产品面上没有任何东西能到达它们**。五条 EC 全 PENDING。**不**做真实外发 / **不**做升级链 / **不**改序 24/25 的语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
