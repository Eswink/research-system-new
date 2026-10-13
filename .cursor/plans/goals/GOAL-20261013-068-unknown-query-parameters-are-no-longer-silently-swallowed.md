---
id: GOAL-20261013-068
slug: unknown-query-parameters-are-no-longer-silently-swallowed
title: >-
  未知查询参数不再被静默吞掉（记忆读面）—— 序 35 让**已被吞掉的那个**参数接通了，
  但**未知**参数仍被静默忽略；**实跑取证**：`GET /projects/{id}/memory?definitely_not_a_param=1`
  ⇒ **200 且键仍只有 `['records','scope_note']`**（既不当错、也不披露、也不点名）
  ⇒ 调用方**以为筛过了**、拿到的是全量；而对照：**已知**参数（`?scope=` / `?proposed_by=`）
  会筛并**披露**其键 ⇒ 同一读面**已知与未知的待遇不对称**。**零命中复核**：
  `unknown_param` / `unexpected_query` / `strict_query` 在 `services/api/` **全零命中**；
  **先例已全在**（同一读面的两个已知参数各自的披露形态）
status: ACHIEVED
created_at: 2026-10-13
updated_at: 2026-10-13
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-13 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 36**，由本次 replan 的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    **push-to-main 授权**：仅 `main`，禁 `--force`，禁推旁支。
    (1) **立题依据（实测，见「事实层结论」）**：**实跑**（`TestClient` + 受控装配）——
    `GET /projects/example-project/memory?definitely_not_a_param=1` ⇒ **200**，
    载荷键仍只有 `['records','scope_note']`（**不报错 / 不披露 / 不点名**）；
    **对照**：`?proposed_by=agent:x` ⇒ 键含 `['filtered_out','proposed_by','records','scope_note']`
    ⇒ **同一读面已知与未知待遇不对称**；`rg -n "unknown_param|unexpected_query|strict_query"
    services/api/` ⇒ **零命中**。
    (2) **为什么属质量轴**：轴的反面是「把判据做成表层合规」—— 序 35 让**名字对的那个**参数
    通到了 Port，而**打错名字的**参数**照样 200 + 全量** ⇒ 调用方**以为筛过了**
    （承本战役「点名失败而非静默降级」的禁令）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**记忆读面**的未知查询参数**点名拒绝**
    （**422 + 把参数名写进错误正文**），**缺省形态逐字不变**（不传未知参数 ⇒ 与改动前**逐字相同**）。
    **射程**：**只**覆盖**记忆读面的两个 GET**（`/memory` 与 `/memory/validity`）——
    不扩散到全仓 65 条 GET 路由（那需要先定「哪些参数算已知」的全仓口径，登记为后续候选）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**全仓**未知参数拒绝（65 条 GET 的口径未定）；
    **不**改**写面**（POST 的请求体额外字段是 pydantic 的既有校验面，另成一面）；
    **不**影响**已知**参数的既有语义（`?scope=` / `?proposed_by=` / `?at=` 一字不动）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（实跑 + 零命中 + 先例 + 射程逐个）**：`scratch/probe-unknown-query-param.py`
      逐条读出 —— ① **实跑**：未知参数 ⇒ 200 + 键不含任何披露（静默吞掉）；
      ② **对照**：两个已知参数各自**筛 + 披露**；③ **零命中**（三组候选标识符）；
      ④ **射程逐个**：记忆读面的**两个 GET** 逐条读出（本轮只覆盖这两条）；
      ⑤ 全仓 GET 路由**计数**（证明「不做全仓」是**有意的边界**，不是遗漏）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-unknown-query-param.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **未知参数点名拒绝（本轮验收主体）**：记忆读面的两个 GET 收到**未知查询参数** ⇒
      **422 + 错误正文点名那个参数**（**不**静默忽略、**不** 500）；
      **已知**参数与**缺省**形态**逐字不变**；多个未知参数 ⇒ **逐个点名**（不只报第一个）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（未知点名 / 多个未知逐个 / 已知逐字不变 / 缺省逐字不变）。
    status: PASS
  - id: EC-03
    criterion: >-
      **射程如实**：**只**那两个 GET 受此纪律（其余路由**逐条读出**仍然照旧 ——
      受判面 = **对照组的既有行为**，证明本轮**没有**顺手扩散）；
      既有读面键**一字不动**；若动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      + 新用例（对照组逐条 / 既有键不变）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Z-1` 未知参数**被忽略**（静默吞掉原样回来）⇒ RED；
      `Z-2` 已知参数**被误拒**（拒绝面过宽）⇒ RED；
      `Z-3` **缺省形态**被改动（不传参数也报错）⇒ RED；
      `Z-4` 多个未知参数**只报第一个**（逐个点名被破坏）⇒ RED。复原用**二进制读写**且
      raw `sha256` 逐字节相同；**反证脚本带基线门**；判词归档进树（**二进制写盘**、`CR=0`）。
    verify: >-
      `scratch/goal068_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；
      归档 `.cursor/plans/goals/evidence/GOAL-20261013-068-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 36**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal068_closeout.py` ⇒ 全 `PASS`；
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
  - .cursor/plans/tasks/PLAN-20261013-445-goal-068-ec01-05-unknown-query-parameters-are-no-longer-silently-swallowed.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-446-goal-068-ec01-04-unknown-query-parameters-are-no-longer-silently-swallowed.md
memory_entries: []
---

# GOAL-20261013-068 — 未知查询参数不再被静默吞掉（记忆读面）

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 36**（轴 = **质量**；依赖序 17、34、35
> —— 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 33/34/35 收口后到期），
> 已在 MAINLINE「修订记录」留痕；**GOAL 文件与子 PLAN 同轮建档**。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（实跑 + 对照 + 零命中 + 射程逐个 + 全仓计数） | **实跑**：`scratch/probe-unknown-query-param.py` | **PASS** |
| EC-02 | 未知参数**点名拒绝**（422 + 点进正文；多个逐个）；已知与缺省逐字不变 | `pytest tests/api -q` | **PASS** |
| EC-03 | 射程如实（对照组逐条仍照旧）+ 既有键不变 + 快照同轮 | `pytest tests/api tests/contracts -q` | **PASS** |
| EC-04 | 两向反证 `Z-1`…`Z-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5836 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | **实跑**：未知参数**被静默吞掉** | `uv run --frozen --no-sync python -B scratch/probe-unknown-query-param.py` | **200** + 键 `['records','scope_note']`（不报错 / 不披露 / 不点名） |
| 2 | **对照**：已知参数**筛 + 披露** | 同上第 2 段 | `?proposed_by=` ⇒ 键含 `filtered_out` / `proposed_by` |
| 3 | **零命中** | `rg -n "unknown_param\|unexpected_query\|strict_query" services/api/` | **（零命中）** |
| 4 | **射程逐个**（本轮只覆盖两条） | 探针第 4 段 | `/memory` 与 `/memory/validity` 两个 GET |
| 5 | 全仓 GET 路由**计数**（「不做全仓」是**有意边界**） | 探针第 5 段 | **65** 条 GET（本轮**不**扩散） |

**结论**：**已知与未知待遇不对称** —— 名字对的参数通到了 Port，**打错名字的**照样 200 + 全量
⇒ 调用方**以为筛过了**（「静默降级」）。修法**不是**新造机制：同一读面已有**两个**已知参数的
披露形态可照。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 未知参数 ⇒ **422 + 点名**（**不**静默忽略、**不** 500） | 「点名失败而非静默降级」是本战役的禁令；422 与既有参数校验同形 | 已定 |
| D-2 | **射程只**覆盖记忆读面的**两个 GET** | 全仓 65 条 GET 的「已知参数」口径**未定** ⇒ 扩散会撞出大量未定义行为（登记为后续候选） | 已定 |
| D-3 | **缺省形态逐字不变**（不传未知参数 ⇒ 逐字相同） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-4 | **已知**参数（`?scope=` / `?proposed_by=` / `?at=`）**一字不动** | 它们是序 17/34/35 三轮立的形态，各有判据钉住 | 已定 |
| D-5 | 多个未知参数 ⇒ **逐个点名** | 只报第一个会让「还有哪些打错了」读不出来（与「不静默」同一理由） | 已定 |

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
**插入记录行必须是追加**（承本轮实测的「顶掉旧行」形态 —— 新判据当场抓到过一次）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **中概率**：读面路由 + 既有测试的调用形态）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：记忆读面的**未知查询参数点名**（射程 = 那两个 GET；对照组如实照旧）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：**全仓**未知参数拒绝（65 条 GET 口径未定）/ **写面**请求体
  额外字段（pydantic 既有面）/ 作者鉴权 / 通配·模糊匹配 / `provenance` 在编排面的披露 /
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
| （待 push 后逐条回填；同批推送只让 tip 起 run ⇒ 各自 `covered_by` 见下） | （待轮询） | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（replan + 建档） | `9721c90`（序 36 登记）、`d89b974`（建档） | 只读勘察（0 改动）+ 实跑读数（见「事实层结论」）；**同轮建档** | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 未知参数点名） |
| 1 | `PLAN-20261013-445`（WP-1…WP-5） | `5b5743f`（守卫 + 射程）、`73b770e`（判据 8 例 + 按压归档） | **EC-01/02/03/04 PASS**：① 五段读数；② 未知 ⇒ **422 + 逐个点名**（含已知集）；**两个 GET** 都受判；已知与缺省**一字不动**；③ **射程如实**（不装全局；对照组照旧）+ **不动 DTO** ⇒ 快照零 diff（如实登记理由）；④ **四向反证** `Z-1`…`Z-4` 全红 + 基线绿 + 复原一致。`tests/api tests/contracts tests/application tests/adapters tests/e2e` 全绿（**621 + 1586**）；mypy **1211 files** 零问题 | （见 CI 台账） | 三处如实登记：① 判据初版**来源必须同时注册 store 白名单与 ledger**（`SourceRecord`）+ PROJECT 层级要策展人批准 ⇒ 走 SESSION；② `?at=` 的 `+` 必须 **percent-encode**（否则被解成空格）；③ 收口断言集 **f-string 的 AST 分片**（`FormattedValue` 读不到）⇒ 改判**源码文本**；④ 规模门 **457 行** ⇒ 守卫**单列成模块**（判据 / 按压 / 断言集**随之重定向**）；⑤ **m0 真红**：隐私出口普查抓到新模块的 `ApiError.detail` 出口 ⇒ 归入既有 **JUDGED `failure_payload`** 面（**不是**豁免）。**EC-05 PASS**（验证器判词全 `PASS`；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5836 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | （见 CI 台账） | — | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**三处如实登记**（ledger 注册 / `+` 编码 / AST 分片）。**残余**：**全仓 65 条 GET** 的未知参数仍被静默吞掉（有意边界）/ 写面请求体另成一面 / 参数值语义未校验 / 内容级检测 / 三维以上组合等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261013-446`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-13 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 36**（**轴 = 质量**），并写修订记录行（只追加）。**实测读数**（逐条见「事实层结论」表）：① **实跑**未知参数 ⇒ 200 + 无披露（**静默吞掉**）；② **对照**已知参数 ⇒ 筛 + 披露；③ 零命中（三组标识符）；④ 射程 = 记忆读面两个 GET；⑤ 全仓 65 条 GET（**不扩散**是有意边界）。**GOAL 文件 / 子 PLAN / `ALL_PLAN` 投影同轮落地**。五条 EC 全 PENDING。**不**做全仓拒绝 / **不**改写面 / **不**动已知参数语义。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
