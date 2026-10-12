---
id: GOAL-20261013-066
slug: a-memory-author-is-selectable
title: >-
  记忆的作者可筛选 —— 序 33 让**提议者**读得出（`proposed_by` 落 canonical + 两读面披露），但**选不着**；**实测**：`inspect.signature(MemoryStore.query)` 的形参**只有** `tier` / `scope` 两个维度（`proposed_by` **不在**），传 `proposed_by=` ⇒ **`TypeError: unexpected keyword argument`**；**实跑**：两条不同作者的记忆经产品路径提交 ⇒ 读面**逐条报得出作者**，却**无法只取其中一位作者的**（与序 17 的 `scope` **同一缺口形态**：看得见、选不着）；**先例已全在**（序 17 的 `scope` 第三维就是同一推进的同族形态）| 序 17、33 |
status: ACHIEVED
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 34**，由序 33 收口后的**逐轴复评实测**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：`inspect.signature(MemoryStore.query)` 逐字读出
    —— `(self, tier=None, scope=None)` ⇒ **`proposed_by` 不在**；**实跑**（产品路径）两条不同
    作者的记忆 ⇒ 读面**逐条报得出作者**（`[('m-1','agent:x'), ('m-2','agent:y')]`）而
    **无法只取一位作者的** ⇒ 传 `proposed_by=` 直接 **`TypeError`**；
    **先例**：序 17 的 `scope`（同一形态：读得出 → 选得着）。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 33 让作者面**可判定**，
    但「哪个 agent 记下的知识」**仍然选不着** ⇒ 读者只能**逐条过滤**（把筛选逻辑留给每个调用方，
    两处各写一套 = 漂移无从发现）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**作者**成为 `query` 的可选维度
    （与 `tier` / `scope` **同一形态**：缺省不筛 ⇒ 既有行为逐字不变），并在消费面
    `memory_read` 上**可选**传它（载荷**点名**范围与**筛掉了多少条**）；**缺省形态逐字不变**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**作者鉴权**（筛是**选择**，不是 ACL —— 与 `scope`
    的边界**逐字同形**）；**不**做**通配 / 前缀 / 模糊匹配**（只做**精确**匹配 —— 与 `scope` 同）；
    **不**给 HTTP 读面加作者筛选（本轮**只**做查询面 + 编排消费面；HTTP 面「选得着」另成一面）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（签名逐个 + 实跑 + 先例）**：`scratch/probe-author-selectable.py` 逐条读出 ——
      ① `query` 的形参**逐个**（`tier` / `scope`，**无** `proposed_by`）；② **实跑**：两条不同
      作者的记忆 ⇒ 读面看得到作者、按作者选 ⇒ `TypeError`（**点名**异常类型与消息）；
      ③ **先例**：序 17 的 `scope` 第三维形态逐条读出（同一手法）；④ 三个适配器的 `query` 签名
      **逐个**（同契约）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-author-selectable.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **作者成为可选维度（本轮验收主体）**：`MemoryStore.query` +1 **可选**形参（缺省 ⇒ **不筛**，
      既有行为逐字不变）；**三适配器同契约**（SQLite / PG / **Fake**）；**未知作者** ⇒ 空结果
      （**不猜**：不把未知当「全选」）；与 `tier` / `scope` **可并存**（两维各自独立）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/postgres -q` ⇒ 全绿
      + 新用例（三适配器同契约 / 缺省逐字不变 / 两维可并存 / 未知作者空集）。
    status: PASS
  - id: EC-03
    criterion: >-
      **消费面可传（可选，缺省不变）**：`memory_read` 可传作者 ⇒ 载荷**点名**筛了什么与
      **筛掉了多少条**（与既有 `scope` 的披露形态**同源同形**）；**缺省载荷逐字相同**；
      既有键一字不动。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/memory tests/api -q`
      ⇒ 全绿 + 新用例（载荷点名 / 缺省逐字不变 / 既有键不动）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`X-1` 查询面**忽略**作者筛（当全选）⇒ RED；
      `X-2` 适配器**不带**该维度（往返丢筛）⇒ RED；`X-3` **缺省形态**被改动（不传作者也筛）⇒ RED；
      `X-4` 消费面**不点名**（静默丢条数）⇒ RED。复原用**二进制读写**且 raw `sha256` 逐字节相同；
      **反证脚本带基线门**（未按压必须 GREEN）；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal066_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-066-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 34**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal066_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-441-goal-066-ec01-05-a-memory-author-is-selectable.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-442-goal-066-ec01-04-a-memory-author-is-selectable.md
memory_entries: []
---

# GOAL-20261013-066 — 记忆的作者可筛选

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 34**（轴 = **质量**；依赖序 17、33
> —— 均已收口）。**本行是序 33 收口后逐轴复评的产物**，已在 MAINLINE「修订记录」留痕，
> **GOAL 文件与子 PLAN 在同一轮触发内建档**（承序 33 的教训：修订记录写「已建档」必须与树一致）。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（签名逐个 + 实跑 TypeError + 先例 + 三适配器签名） | **实跑**：`scratch/probe-author-selectable.py` | **PASS** |
| EC-02 | 作者成为查询面可选维度（三适配器同契约；缺省不筛；未知作者空集） | `pytest tests/adapters tests/postgres -q` | **PASS** |
| EC-03 | 消费面可传 + 载荷点名（缺省逐字不变） | `pytest tests/application/memory tests/api -q` | **PASS** |
| EC-04 | 两向反证 `X-1`…`X-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5815 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | `query` 形参**只有**两个维度 | `inspect.signature(MemoryStore.query)` | `(self, tier=None, scope=None)` —— **无** `proposed_by` |
| 2 | **实跑**：读得出作者、**选不着** | `uv run --frozen --no-sync python -B scratch/probe-author-selectable.py` | 读面 `[('m-1','agent:x'), ('m-2','agent:y')]`；传 `proposed_by=` ⇒ **`TypeError`** |
| 3 | **先例**：序 17 的 `scope` 第三维（同一手法） | `rg -n "scope: str \| None = None" packages/application/ports/memory_store.py` | 在（那一轮把「看得见」做成了「选得着」） |
| 4 | 三适配器的 `query` 签名**逐个**（同契约） | 探针第 4 段 | 三个都只有 `tier` / `scope` |

**结论**：**看得见、选不着** —— 序 33 让作者面可判定，但「哪个 agent 记下的知识」仍**选不出来**
⇒ 每个调用方只能**逐条过滤**（筛选逻辑散在各处 = 漂移无从发现）。
**与序 17 的 `scope` 是同一缺口形态**（那一轮已把 `scope` 从「读得出」推进到「选得着」）。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 新维度与 `tier` / `scope` **同一形态**（缺省 `None` ⇒ 不筛） | 「缺省形态逐字不变」是本战役一贯纪律；同一形态让调用方一看即懂 | 已定 |
| D-2 | **精确匹配**（**不**做通配 / 前缀 / 模糊） | 与 `scope` 的匹配语义**逐字同形**；模糊匹配会引入未定义的边界 | 已定 |
| D-3 | 三适配器**同契约** | 承序 13/45/61/65 的实测教训（Fake 漏带 ⇒ 该路径判据**假绿**） | 已定 |
| D-4 | **未知作者 ⇒ 空结果**（**不**当全选） | 「点名失败而非静默降级」；把未知当全选会让「筛了什么」读不出来 | 已定 |
| D-5 | **不**给 HTTP 读面加该筛选（本轮只做查询面 + 编排消费面） | 两读面「选得着」另成一面（与序 17 的边界同形：那一轮 HTTP 面也只做了 `?scope=`） | **待 EC-01 复核** |

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
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：`MemoryStore` Port + 三适配器 + 消费面）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：记忆的**作者筛选**（`query` 的第三个维度 + 消费面可传 + 载荷点名）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**作者鉴权** / **通配·模糊匹配** / **HTTP 面的作者筛选** /
  `provenance` 在编排面的披露 / **内容级检测**（`W-2`）/ 三维以上闸门组合；`BB-3`；
  `DD-1`…`DD-3`；`AA-*` / `Z-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` /
  `Q-*` / `P-*` / `O-1`…`O-5`。
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
| `171dfa0`（逐轴复评 + 建档） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | 序 34 建档（GOAL + PLAN + ALL_PLAN 同轮） |
| `139f527`（frontmatter 修复） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | title 冒号 ⇒ 块标量 |
| `2df0a40`（WP-2/WP-3） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | Port 第三维 + 三适配器 + 消费面 |
| `73a305b`（判据 + 归档） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | 判据 10 例 + 按压归档 |
| `97fc003`（WP-5 主体） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | 收口验证器 + 断言集 + PG 判据 + 049 改签 |
| `58835e6`（规模门 / 格式修复） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | 452→448 + 049 格式化 + 长行 |
| `568128e`（EC-05 回填） | **`total_count = 0`** ⇒ **`covered_by 38311523270`** | as-is m0 读数（5815 passed） |
| `b80ff32`（**末条实测提交** = 两树归档 + 收口） | `38311523270` **M0 success**（**8/8 job 全 success**）+ `38311522581` **Push on main success** | 两树判词定格归档 + MAINLINE 进展行 + 归档搬运 |

**自我指涉边界（明写并封闭）**：写本台账本身要再提交 ⇒ 会产生新 run。**封闭口径**：
**末条可引用的实测提交 = `b80ff32`**（上表最后一行，两 run 全绿）；**其后仅记录提交**，
**不再追链** —— 若需复核本行结论，取 `b80ff32` 的两条 run 即足。

**`covered_by` 的用法（逐条）**：七个提交**自身 `total_count = 0`**（**同批推送**只让 tip 起 run）
⇒ 按纪律**不是**「未取证」，而是**由同批 tip 的 run 覆盖**（各自 `covered_by` 已在表内写明）。
**空集合 = 未取证**，本表**无一处**留空。**本轮无 `failure` / 无 `cancelled`**（两处本地真红
—— 回归与规模门 —— 都在**本地门**阶段被发现并修掉，**未进入 CI**）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（逐轴复评 + 建档） | `171dfa0`（同轮建档）、`139f527`（frontmatter 修复） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」） | （见 CI 台账） | `139f527`（**治理判据当场抓到** title 里的冒号破坏 YAML ⇒ 改块标量） | 五条 EC 全 PENDING | cycle 1（EC-02 查询面第三维） |
| 1 | `PLAN-20261013-441`（WP-1…WP-5） | `2df0a40`（Port 第三维 + 三适配器 + 消费面）、`73a305b`（判据 10 例 + 按压归档）、`97fc003`（收口面 + PG 判据 + 049 改签） | **EC-01/02/03/04 PASS**：① 四段读数；② Port +1 可选形参 + 三适配器**各自真筛** + 缺省不筛 + 未知作者空集；③ 消费面可传 + 载荷点名（含筛掉条数）+ 缺省逐字不变 + **序 17 的 `scope` 支一字不动**；④ **四向反证** `X-1`…`X-4` 全红 + 基线绿 + 复原一致。`tests/application tests/adapters tests/api tests/contracts tests/domain tests/postgres` 全绿；mypy **1208 files** 零问题 | （见 CI 台账） | 四处如实登记：① **回归**：`_filtered_out` 初版把 `scope` 传进分母 ⇒ 序 17 的判据当场红 ⇒ **分母只按 tier 维**（与序 17 逐字一致）；② `X-4` 锚点**不唯一**（`payload["filtered_out"]` 出现 2 次）⇒ 改打作者支整段；③ **049 断言集改签**（字面锚 → 关系锚，`+6 / -1`，两向实测）；④ 治理判据抓到 title 冒号 ⇒ 改块标量；⑤ 规模门 452 行 ⇒ **压实到 448**（守 450 行硬上限；**语义一字未动**）。**EC-05 PASS**（验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5815 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | （见 CI 台账） | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**四处如实登记**（`_filtered_out` 回归当场红 / `X-4` 锚点不唯一 / 049 断言集改签 / frontmatter 冒号）。**残余**：未知作者与不存在不可分（无作者注册面）/ 作者鉴权不做（选择非 ACL）/ HTTP 面未加该筛选 / 模糊匹配不做 / 内容级检测 / 三维以上组合等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261013-442`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-13 | ACTIVE | **逐轴复评 + 建档（cycle 0）**：MAINLINE 程序表**新增序 34**（**轴 = 质量**），并写修订记录行（只追加）。**实测读数**（逐条见「事实层结论」表）：① `query` 形参只有 `tier` / `scope`；② **实跑**两条不同作者的记忆 ⇒ 读面报得出作者而**选不着**（传 `proposed_by=` ⇒ `TypeError`）；③ 先例（序 17 的 `scope`）在树；④ 三适配器签名同缺。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**（承序 33 的教训）。五条 EC 全 PENDING。**不**做作者鉴权 / **不**做模糊匹配 / **不**给 HTTP 面加该筛选。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
