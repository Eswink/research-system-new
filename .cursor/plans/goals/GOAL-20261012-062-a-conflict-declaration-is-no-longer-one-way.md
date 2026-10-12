---
id: GOAL-20261012-062
slug: a-conflict-declaration-is-no-longer-one-way
title: 冲突声明不再是一扇单向门（反向链接）—— `contradictions` 是**单方向**的声明：A 声明与 B 冲突 ⇒ **B 那侧读不出来**；**实跑取证**：B 的 `contradictions` 是 `[]`、**没有**任何反向键，且 B 的 `disposition` 是 **`USE`（照用）** ⇒ **一条被别人声明冲突的记忆照样进下一步**；而**同类先例已全在**（序 18 的 `superseded_by_index` 正是同一个问题的**反向索引**解法）⇒ 缺的是冲突面的**反向索引与分派**
status: ACTIVE
created_at: 2026-10-12
updated_at: 2026-10-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 30**，由本次**触顶核算**的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：`rg -n "conflicted_by|reverse_conflict|
    contradicted_by|declared_by_others" packages/ adapters/ services/` ⇒ **零命中**；
    **实跑取证**（`FakeMemoryStore` 产品路径）：A 声明 `contradictions=["m-b"]` ⇒
    **A 侧** `disposition=CONFLICTED`，而 **B 侧** `contradictions=[]`、**无**反向键、
    `disposition=USE`（**照用**）⇒ **被声明的对象照样进下一步**；
    而**同类先例已全在**：序 18 的 `superseded_by_index`（`disposition.py`）就是
    「谁取代了我」的**反向索引**（正向链接写在**新**记录上 ⇒ 必须扫同批记录）⇒ 冲突面缺的
    是**同一手法的反向索引**与它在**处置面**的分派。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 19/26 让**声明方**那一侧
    可判定（`CONFLICTED` 五态 + 消解记载），而**被声明方**那一侧**完全看不见** ⇒
    一条记忆**能不能进下一步**取决于「**是不是它**先声明了冲突」，与「有没有冲突」这一事实
    **不对称**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**被声明方**也读得出（反向链接 +
    处置面分派），**缺省形态逐字不变**（没有任何反向声明的记录 ⇒ 与改动前**逐字相同**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做自动消解 / **不**做自动失效（判定仍由**人**给 ——
    序 26 立的边界**一字不动**）；**不**做内容级语义比较（`W-2` 的另一半）；**不**改
    `contradictions` 的**声明**语义（它是历史事实）与**正向**读法。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（实跑 + 零命中）**：`scratch/probe-reverse-conflict.py` 逐条读出 ——
      ① 反向面**零命中**（四组候选标识符 × 三个产品根）；② **实跑**：A 声明与 B 冲突 ⇒
      A 侧 `CONFLICTED` / **B 侧 `USE` 且无反向键**（这就是缺口）；③ **先例**：
      `superseded_by_index` 的形态逐条读出（同一手法的可复用面）；④ 两个读面的
      `contradictions` 读法**逐字仍是一向**（本轮**不**改它）。`git diff --numstat` ⇒ **零改动**。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-reverse-conflict.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **反向链接与分派（本轮验收主体）**：被声明方读面**逐条披露**反向链接（谁是声明方）；
      处置面据此分派（**与正向声明同类不同因**：判词点得出「**是谁**声明了与它冲突」）；
      **缺省形态逐字不变**（无反向声明 ⇒ 与改动前逐字相同）；未知 / 跨范围形态**点名**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q`
      ⇒ 全绿 + 新用例（反向可读 / 缺省逐字不变 / 跨范围不猜）。
    status: PASS
  - id: EC-03
    criterion: >-
      **两个读面同源**：编排消费面与 HTTP 读面**同源**（同一批纯函数）披露反向链接；
      **既有键逐字不变**（`contradictions` 仍是**正向**声明，语义一字不改）；
      动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Y-1` 反向链接被摘掉（被声明方读不到）⇒ RED；
      `Y-2` 处置面**不**按反向分派（仍是 `USE`）⇒ RED；
      `Y-3` **缺省形态**被改动（无反向也改处置）⇒ RED；
      `Y-4` 跨范围被当成同批（看不见 ≠ 不存在）⇒ RED。复原用**二进制读写**且 raw `sha256`
      逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal062_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 30**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal062_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261012-433-goal-062-ec01-05-a-conflict-declaration-is-no-longer-one-way.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-434-goal-062-ec01-04-a-conflict-declaration-is-no-longer-one-way.md
memory_entries: []
---

# GOAL-20261012-062 — 冲突声明不再是一扇单向门

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 30**（轴 = **质量**；依赖序 26、29
> —— 均已收口）。**本行是触顶核算的产物**（序号 1…30 全登记时按宪章逐轴实测），
> 已在 MAINLINE「修订记录」留痕（含 `max_goals` 30 → 35 的理由）。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（反向面零命中 + 实跑缺口 + 先例 + 正向读法未动） | **实跑**：`scratch/probe-reverse-conflict.py` | **PASS** |
| EC-02 | 反向链接可读 + 处置面分派（缺省逐字不变；跨范围点名） | `pytest tests/application tests/domain -q` | **PASS** |
| EC-03 | 两读面**同源** + 既有键逐字不变 + 快照同轮 | `pytest tests/api tests/adapters tests/contracts -q` | **PASS** |
| EC-04 | 两向反证 `Y-1`…`Y-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5768 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 反向面**零命中** | `rg -n "conflicted_by\|reverse_conflict\|contradicted_by\|declared_by_others" packages/ adapters/ services/` | **（零命中）** |
| 2 | **实跑**：被声明方读不出、且**照用** | `uv run --frozen --no-sync python -B scratch/probe-reverse-conflict.py` | A 侧 `CONFLICTED` / **B 侧 `contradictions=[]` 无反向键、`disposition=USE`** |
| 3 | **先例**：反向索引**已全在**（同族手法） | `rg -n "def superseded_by_index" -A 12 packages/application/memory/disposition.py` | 「正向写在**新**记录上 ⇒ 扫同批记录」的**反向索引** |
| 4 | 正向读法**逐字仍是一向**（本轮**不**改） | `rg -n '"contradictions"' adapters/canonical/memory_read.py services/api/routers/memory.py` | 两处都是 `list(record.contradictions)`（**正向**声明） |
| 5 | 处置面按 `conflicted` 布尔分派（序 19） | `rg -n "disposition_of(" packages/application/memory/disposition.py` | 布尔入参 ⇒ 反向分派要在**调用方**那一侧合并 |

**结论**：**冲突声明是一扇单向门** —— 序 19/26/29 让**声明方**那一侧可判定（五态 / 消解 /
时效），而**被声明方**那一侧**完全看不见** ⇒ 「能不能进下一步」取决于「**是不是它**先声明了」。
**质量轴自序 19 起**连续多轮做「声明侧」，本轮补**被声明侧**。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 反向链接**扫同批记录**算（不新增 Port 方法） | 序 18 的 `superseded_by_index` **同一手法**（反向信息不在记录自身里） | 已定 |
| D-2 | 处置面**与正向同类不同因**（判词点得出「**是谁**声明了与它冲突」） | 「互不混用」是本战役一贯纪律（序 19 的五态同理） | 已定 |
| D-3 | **缺省形态逐字不变**（无反向声明 ⇒ 逐字相同） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | **不**改 `contradictions` 的**声明**语义与**正向**读法 | 它是**历史事实**（序 22 已收口其完整性校验） | 已定 |
| D-5 | 跨范围（看不见 ≠ 不存在）**点名**而不是假装没有 | 承序 21 的 `OUT_OF_VIEW` 同一纪律 | 已定 |

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
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：处置面 + 两读面 + DTO）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：冲突面的**被声明方**一侧（反向链接 + 处置面分派）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**自动消解** / **内容级检测**（`W-2`）/ 三维以上闸门组合；
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
| 0 | —（触顶核算 + 建档） | `c6af848` | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 反向链接 + 分派） |
| 1 | `PLAN-20261012-433`（WP-1…WP-5） | `f20b0e3`（反向索引 + 两成因 + 两读面同源）、`060dcd7`（判据 16 例 + 按压归档）、`a7c3269`（收口面 + 规模门三处抽函数） | **EC-01/02/03/04 PASS**：① 四段读数（零命中 + 实跑缺口 + 先例 + 正向未动）；② `conflicted_by_index` 扫同批记录 + 处置面按其分派 + **两成因可区分**（受判面 = 两个形态）；③ 两读面**都引用**同一纯函数 + 缺省逐字不变 + 快照同轮（`+7 / -0`）；④ **四向反证** `Y-1`…`Y-4` 全红 + 基线绿 + 复原一致。`tests/application tests/api tests/adapters` 全绿；mypy **1205 files** 零问题。**EC-05 PASS**（验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5768 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿）。**一处如实登记**：规模门三处触顶（`_record_dto` 54 / `memory_read` 59 / `_memory_row` 56）⇒ 抽三处助手（语义一字未动） | （见 CI 台账） | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**残余**：`conflicted_by` 为派生事实（跨范围读不到，如实点名）/ 自动消解 / 内容级检测 / 三维以上组合 / `BB-3` 等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261012-434`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-12 | ACTIVE | **触顶核算 + 建档（cycle 0）**：MAINLINE 程序表**新增序 30**（**轴 = 质量**），并写修订记录行（只追加）+ 预算核算（`max_goals` 30 → 35）。**实测读数**（逐条见「事实层结论」表）：① 反向面**零命中**；② **实跑**：A 声明与 B 冲突 ⇒ A 侧 `CONFLICTED` / **B 侧 `USE` 且无反向键**；③ 先例 `superseded_by_index` **已全在**；④ 正向读法**逐字仍是一向**。五条 EC 全 PENDING。**不**做自动消解 / **不**做内容级检测 / **不**改声明语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
