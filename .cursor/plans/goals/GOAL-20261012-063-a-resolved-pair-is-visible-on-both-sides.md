---
id: GOAL-20261012-063
slug: a-resolved-pair-is-visible-on-both-sides
title: 已消解的一对在两端都看得见 —— 序 30 让**冲突声明**的反向可读（`conflicted_by`），但**消解记载**仍是**单向**的；**实跑取证**：A 声明与 B 冲突、人把这一对**消解**掉 ⇒ **A 读 `USE`**，而 **B 仍读 `CONFLICTED`**（`conflicted_by=['m-a']` 未被消解记载抵消）⇒ **同一条已消解的分歧两端处置不一致**；**零命中复核**：`resolved_by_index` / `reverse_resolution` / `resolved_pairs` 三个产品根**全零**；**先例已全在**（序 30 的 `conflicted_by_index` 就是同一手法的第三个实例）
status: ACTIVE
created_at: 2026-10-12
updated_at: 2026-10-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 31**，由序 30 收口后的**逐轴复评实测**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑**（`FakeMemoryStore` 产品路径，
    A 声明 `contradictions=["m-b"]` 后经 `resolve_memory_conflict` 消解这一对）⇒
    **A 侧** `conflict_resolutions=[{other_id: m-b, resolved_by: curator:x, …}]` 且
    `disposition=USE`；**B 侧** `conflict_resolutions=[]`、`disposition=CONFLICTED`、
    `conflicted_by=['m-a']`（**序 30 的反向链接照旧指着那对，无人抵消**）⇒
    **同一条已消解的分歧，两端处置不一致**；`rg -n "resolved_by_index|reverse_resolution|
    resolved_pairs" packages/ adapters/ services/` ⇒ **零命中**；而**先例已全在**：
    序 30 的 `conflicted_by_index`（`disposition.py`）就是「反向链接扫同批记录」的**第三个实例**
    ⇒ 缺的只是**同一手法在消解面的对齐**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 26 让**记载方**那一侧可判定
    （`resolved_by` / `resolved_at`），序 30 让**声明**反向可读，而**消解**这一层**仍是一扇单向门**
    ⇒ 一条记忆「能不能进下一步」取决于「**是不是它**记的消解」，与「这对**有没有**被消解」
    这一事实**不对称**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**已消解的一对在两端都读得出**，
    **缺省形态逐字不变**（没有任何消解记载 ⇒ 与改动前**逐字相同**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做自动消解 / **不**做自动失效（判定仍由**人**给 ——
    序 26 立的边界**一字不动**）；**不**做内容级语义比较（`W-2` 的另一半）；**不**改
    `contradictions` 的**声明**语义、**不**改 `resolutions` 的**记载**语义（它仍是**记载方**
    的记录），**不**改序 30 的 `conflicted_by` 语义。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（实跑 + 零命中 + 先例）**：`scratch/probe-resolved-pair-face.py` 逐条读出 ——
      ① 消解的反向面**零命中**（三组候选标识符 × 三个产品根）；② **实跑**：一对被消解 ⇒
      **A 侧 `USE` / B 侧仍是 `CONFLICTED`**（这就是缺口）；③ **先例**：序 30 的
      `conflicted_by_index` 形态逐条读出（同一手法）；④ `resolutions` 的**记载**读法
      **逐字仍是单向**（本轮**不**改它）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-resolved-pair-face.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **对端可读（本轮验收主体）**：被消解方的读面**逐条披露**「**这一对已被消解**」
      （谁记的 / 何时 —— **由同一批记录算出的反向表**，不新增 Port 方法）；
      处置面据此分派：**已消解的反向冲突不再判 `CONFLICTED`**（与序 30 的
      `conflicted_by` **同源**：先扣掉已消解的，再判）；**缺省形态逐字不变**
      （没有任何消解记载 ⇒ 与改动前逐字相同）；**只消解一对**时其余仍算数（**逐对**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q`
      ⇒ 全绿 + 新用例（对端可读 / 逐对 / 缺省逐字不变）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **两个读面同源**：编排消费面与 HTTP 读面**同源**（同一批纯函数）披露对端可见性；
      **既有键逐字不变**（`resolutions` 仍是**记载方**的记载）；动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Z-1` 反向消解表被摘掉（对端读不到）⇒ RED；
      `Z-2` 处置面**不**扣已消解（对端仍 `CONFLICTED`）⇒ RED；
      `Z-3` **缺省形态**被改动（没有消解也改处置）⇒ RED；
      `Z-4` **只消解一对**却被当成全消解（逐对被破坏）⇒ RED。复原用**二进制读写**且
      raw `sha256` 逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal063_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 31**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal063_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261012-435-goal-063-ec01-05-a-resolved-pair-is-visible-on-both-sides.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261012-063 — 已消解的一对在两端都看得见

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 31**（轴 = **质量**；依赖序 26、30
> —— 均已收口）。**本行是序 30 收口后逐轴复评的产物**，已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（零命中 + 实跑缺口 + 先例 + 记载读法未动） | **实跑**：`scratch/probe-resolved-pair-face.py` | PENDING |
| EC-02 | 对端可读 + 处置面扣已消解（逐对；缺省逐字不变） | `pytest tests/application tests/domain -q` | PENDING |
| EC-03 | 两读面**同源** + 既有键逐字不变 + 快照同轮 | `pytest tests/api tests/adapters tests/contracts -q` | PENDING |
| EC-04 | 两向反证 `Z-1`…`Z-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 消解的反向面**零命中** | `rg -n "resolved_by_index\|reverse_resolution\|resolved_pairs" packages/ adapters/ services/` | **（零命中）** |
| 2 | **实跑**：一对被消解 ⇒ **两端处置不一致** | `uv run --frozen --no-sync python -B scratch/probe-resolved-pair-face.py` | **A 侧 `USE`**（记载在它身上）/ **B 侧 `CONFLICTED`**（`conflicted_by=['m-a']` 未被抵消） |
| 3 | **先例**：反向索引**已全在**（同族手法） | `rg -n "def conflicted_by_index" packages/application/memory/disposition.py` | 序 30 的 `conflicted_by_index`（扫同批记录） |
| 4 | `resolutions` 的**记载**读法**逐字仍是单向**（本轮**不**改） | `rg -n '"conflict_resolutions"' adapters/canonical/memory_read.py` | 仍是 `record.resolutions`（**记载方**的记录） |

**结论**：**消解记载是一扇单向门** —— 序 26 让**记载方**那一侧可判定（`resolved_by` /
`resolved_at`），序 30 让**声明**反向可读，而**消解**这一层**两端读不到同一件事**
⇒ 「能不能进下一步」取决于「**是不是它**记的消解」。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 反向消解表**扫同批记录**算（不新增 Port 方法） | 序 30 的 `conflicted_by_index` **同一手法**（反向信息不在记录自身里） | 已定 |
| D-2 | 处置面**先扣掉已消解的**再判（与序 30 **同源**） | 「同源」是本战役一贯纪律；**逐对**扣（只消解一对 ⇒ 其余仍算数） | 已定 |
| D-3 | **缺省形态逐字不变**（无消解记载 ⇒ 逐字相同） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | **不**改 `resolutions` 的**记载**语义（它仍是记载方的记录） | 与序 26 的边界**一字不动**；本轮的加法是**对端可见性** | 已定 |
| D-5 | 只消解一对 ⇒ **其余仍算数**（逐对） | 序 26 立「逐对」的理由**逐字相同**（多对时整体判会抹掉其余） | 已定 |

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

- **本轮推进**：**消解记载的对端可见性**（已消解的一对在两端都读得出）。
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
| 0 | —（逐轴复评 + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 31** | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 对端可读 + 分派） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | ACTIVE | **逐轴复评 + 建档（cycle 0）**：MAINLINE 程序表**新增序 31**（**轴 = 质量**），并写修订记录行（只追加）。**实测读数**（逐条见「事实层结论」表）：① 消解的反向面**零命中**；② **实跑**：一对被消解 ⇒ **A 侧 `USE` / B 侧 `CONFLICTED`**（两端不一致）；③ 先例 `conflicted_by_index` **已全在**；④ 记载读法**逐字仍是单向**。五条 EC 全 PENDING。**不**做自动消解 / **不**做内容级检测 / **不**改记载语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
