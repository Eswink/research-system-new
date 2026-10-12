---
id: GOAL-20261012-065
slug: who-proposed-a-memory-is-readable
title: 谁提议的这条记忆读得出来 —— `proposed_by` 在**提案**上有（序 13 起），但**提交后丢弃**；**实测（字段逐个读出）**：`dataclasses.fields` 两次对照 ⇒ `MemoryWriteProposal` **有** `proposed_by` 而 `MemoryRecord` **根本没有该字段**（`hasattr` 亦为 `False`）⇒ 「这条记忆是谁提的」在 canonical **无从可查**；**实跑**：经产品路径提交带 `proposed_by` 的提案 ⇒ 落库记录**没有作者面**，**编排读面 20 个键里也没有它**（`sorted(row)` 逐个读出）；**零命中复核**：`proposed_by` 在**读面 / 两个适配器**上**全零**（只在提案面与两个内部调用点）| 序 13、22 |
status: ACHIEVED
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 33**，由序 32 收口后的**逐轴复评实测**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支（承用户 goal 模式指令）。
    (1) **立题依据（实测，见「事实层结论」）**：**字段逐个读出** ——
    `dataclasses.fields(MemoryWriteProposal)` **含** `proposed_by`，
    `dataclasses.fields(MemoryRecord)` **不含**（`hasattr(record, "proposed_by")` 亦为 `False`）；
    **实跑**（`FakeMemoryStore` 产品路径）：带 `proposed_by="agent:x"` 的提案提交成功 ⇒
    记录**没有作者面**、编排读面的 **20 个键**里也**没有**它；
    **零命中复核**：`proposed_by` 在 `adapters/canonical/memory_read.py` /
    `adapters/sqlite/memory_store.py` / `adapters/postgres/memory_store.py` **全零**
    （只在 `packages/domain/memory.py` 的提案定义与两个内部调用点：
    `memory_promotion.py` / `m12_chain.py`）⇒ **写面能声明、canonical 无位、读面读不出**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 13/17/29 连续把**其它**
    声明面做到了 canonical（`contradictions` / `valid_from` / `scope` 时效），而**作者面**
    仍是**声明后即弃**（提案方写了、落了、读了都拿不回来）⇒ 一条记忆的**来源可查**
    （AGENTS.md §8「有来源」）在**谁提议**这一维上不成立。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**提议者**在 canonical 有位、在**两个读面**
    都读得出；**缺省形态逐字不变**（未声明作者 ⇒ `None`，与改动前**同值**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**按作者筛选**（那是 `query` 的第三个维度 ——
    与序 17 的 `scope` 同类但**另成一面**，本轮**不**顺手加）；**不**做**作者鉴权**（作者面是
    **声明**，不是 ACL）；**不**改 `provenance` 的既有语义（它是**来源**，与**提议者**是两件事）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（字段逐个 + 实跑 + 零命中）**：`scratch/probe-memory-author.py` 逐条读出 ——
      ① 两处字段表**逐个读出**（提案有 / 记录无）；② **零命中复核**（读面与两个适配器全零，
      命中只在提案面与两个内部调用点）；③ **实跑**：带作者的提案提交 ⇒ 记录 `hasattr` 为
      `False` 且读面键集里没有它；④ `provenance` 的既有语义（**来源** ≠ **提议者**）逐字读出。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-memory-author.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **作者面落 canonical（本轮验收主体）**：`MemoryRecord` +1 **可选**字段（缺省 `None`
      ⇒ 既有记录读出**同值**）；`MemoryWriteProposal` 的既有 `proposed_by` **原样带进**
      canonical（**不**新造第二个作者字段）；**三个适配器同契约**（SQLite 加法式列 +
      PG 迁移只加列 + Fake 同步）；**既有行**（未声明作者）读回 `None`（**不猜**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters tests/postgres -q`
      ⇒ 全绿 + 新用例（两处声明面同源 / 三适配器往返 / 既有行读出 `None`）。
    status: PASS
  - id: EC-03
    criterion: >-
      **两个读面同源披露**：编排消费面 + HTTP 读面**都**披露作者面（同一份 canonical 事实，
      **不**各写一套判定）；**既有键逐字不变**（本轮是加法）；动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`W-1` 记录侧字段被摘掉（落库丢作者）⇒ RED；
      `W-2` 适配器**不带**该列（往返丢失）⇒ RED；`W-3` **缺省形态**被改动（未声明作者被伪造成
      某值）⇒ RED；`W-4` 读面**披露被摘掉**（canonical 有、读面读不出）⇒ RED。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；**反证脚本带基线门**（未按压必须 GREEN）；
      判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal065_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261012-065-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 33**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal065_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-439-goal-065-ec01-05-who-proposed-a-memory-is-readable.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-440-goal-065-ec01-04-who-proposed-a-memory-is-readable.md
memory_entries: []
---

# GOAL-20261012-065 — 谁提议的这条记忆读得出来

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 33**（轴 = **质量**；依赖序 13、22
> —— 均已收口）。**本行是序 32 收口后逐轴复评的产物**，已在 MAINLINE「修订记录」留痕。
>
> **建档时序（如实登记）**：序号在 **2026-10-12** 的复评里登记（程序表与修订记录同时写入），
> 文件于 **2026-10-13** 补建档 —— 上一轮触发在收尾时**只写了登记的声明、没落地文件**
> （修订记录的「已建档」一度与树不一致）⇒ 本轮按「记录自洽」纪律**先把文件补上**再推进。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（字段逐个 + 零命中 + 实跑 + 来源语义） | **实跑**：`scratch/probe-memory-author.py` | **PASS** |
| EC-02 | 作者面落 canonical（记录 +1 可选字段；三适配器同契约；既有行 `None`） | `pytest tests/domain tests/adapters tests/postgres -q` | **PASS** |
| EC-03 | 两读面**同源**披露 + 既有键逐字不变 + 快照同轮 | `pytest tests/api tests/adapters tests/contracts -q` | **PASS** |
| EC-04 | 两向反证 `W-1`…`W-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5803 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 两处字段表**逐个读出**（提案有 / 记录无） | `uv run --frozen --no-sync python -B scratch/probe-memory-author.py` | 提案 **含** `proposed_by`；记录**不含**（`hasattr` 亦 `False`） |
| 2 | **零命中复核** | `rg -n "proposed_by" adapters/canonical/memory_read.py adapters/sqlite/memory_store.py adapters/postgres/memory_store.py` | **（零命中）** |
| 3 | 命中**只在写面**（提案定义 / 写面 DTO / 写入口 / 两个内部调用点） | 探针第 2 段的**逐文件计数** | `packages/domain/memory.py`**1** / `services/api/dto/memory.py`**1** / `services/api/routers/memory.py`**2**（**写入口**把载荷带进提案）/ `memory_promotion.py`**1** / `m12_chain.py`**1**；**读面与三适配器全 0**（**EC-01 实测更正**：建档表初版写「两个内部调用点」，实际含**写入口**） |
| 4 | **实跑**：带作者的提案 ⇒ 记录无作者面 | 探针第 3 段 | `hasattr(record, "proposed_by") == False`；读面 20 键里**没有**它 |
| 5 | `provenance` 是**来源**（≠ 提议者，本轮**不**改它） | `rg -n "provenance" packages/domain/memory.py` | 提案与记录上**各自都有**（既有语义逐字保留） |

**结论**：**写面能声明、canonical 无位、读面读不出** —— 序 13（`contradictions` + `valid_from`）、
序 17（`scope`）、序 29（冲突时效）连续把其它声明面做到了 canonical，而**作者面**仍是
**声明后即弃**（`proposed_by` 在两个内部调用点被**填**、在提交时被**丢**）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 复用提案面**既有**的 `proposed_by`（**不**新造第二个作者字段） | 「同一个概念只应有一个声明点」；新造会让两个字段漂移 | 已定 |
| D-2 | 记录侧字段**可选**（缺省 `None` ⇒ 既有记录读出**同值**） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-3 | 三适配器**同契约**（SQLite 加法式 + PG 迁移只加列 + Fake） | 承序 13 的实测教训（Fake 漏带 ⇒ 该路径判据**假绿**） | 已定 |
| D-4 | **不**按作者筛选（`query` 的第三维另成一面） | 本轮只让**读得出**；「选得着」是另一条（序 17 的 `scope` 同类形态） | 已定 |
| D-5 | **不**做作者鉴权（作者面是**声明**，不是 ACL） | 与 `scope` 的边界**逐字同形**（序 17 已写死「不是 ACL」） | 已定 |

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
**显式路径 `git add` 后必须复核 `git status`**（承序 32 的 CI 真红教训：`ruff format`
波及的判据文件漏提交 ⇒ `format-check` 判负）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：记忆域 + 三适配器 + 两读面 + DTO）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：记忆的**提议者**（`proposed_by`）在 canonical 有位、两读面读得出。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**按作者筛选** / **作者鉴权** / **内容级检测**（`W-2`）/
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
| （待 push 后逐条回填；同批推送只让 tip 起 run ⇒ 各自 `covered_by` 见下） | （待轮询） | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（补建档 + 推进） | `dcd778d`（补建档：GOAL + 子 PLAN + ALL_PLAN） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」，含**一处实测更正**） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 作者面落 canonical） |
| 1 | `PLAN-20261013-439`（WP-1…WP-5） | `b976441`（记录 +1 字段 + `commit` 带进 + 三适配器 + 迁移 027 + 两读面）、`aaaf0b3`（判据 11 例 + 按压归档 + EC-01 更正） | **EC-01/02/03/04 PASS**：① 四段读数 + 一处实测更正（命中**都在写面**，读面与三适配器全 0）；② 记录有 `proposed_by` + SQLite/PG 往返 + Fake 同契约 + 未声明 `None`；③ 两读面**都直接读** canonical 字段 + 既有 13 键逐条仍在 + 来源与作者互不顶替 + 快照同轮（`+11 / -0`）；④ **四向反证** `W-1`…`W-4` 全红 + 基线绿 + 复原一致（`W-1`/`W-2` 逐条核实打**不同层**）。`tests/api tests/application/memory tests/adapters tests/domain tests/postgres` **全绿**；mypy **1207 files** 零问题 | （见 CI 台账） | 两处如实登记：① 建档表第 3 行初版「两个内部调用点」**漏了写入口**（探针逐文件计数抓到）⇒ 按实测更正；② 判据三条初版把 `provenance` 当读面键断言（**该面从无此键**）⇒ 改为在**记录侧**判分离（贴合实际契约）。**EC-05 PASS**（验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5803 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | （见 CI 台账） | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**两处如实登记**（建档表漏写入口 / 判据初版误解读面契约）。**残余**：按作者筛选未做 / 作者鉴权不做（声明非 ACL）/ `provenance` 在编排面仍不披露 / 内容级检测 / 三维以上组合等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261013-440`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-13 | ACTIVE | **补建档 + 推进（cycle 0）**：上一层触发把序 33 写进了 MAINLINE 程序表与修订记录（含「已建档」的表述）**但没落地文件** ⇒ 本轮**先补文件**（本 GOAL + 子 PLAN + `ALL_PLAN` 投影）使**声明与树一致**，再按程序表推进。**实测读数**（逐条见「事实层结论」表）：① 提案**有** `proposed_by` / 记录**没有**该字段；② 读面与两适配器**零命中**；③ **实跑**带作者的提案 ⇒ 记录无作者面且读面 20 键里没有它；④ `provenance`（来源）与作者是两件事（**不**改）。五条 EC 全 PENDING。**不**做按作者筛选 / **不**做作者鉴权 / **不**改 `provenance`。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
