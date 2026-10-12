---
id: GOAL-20261012-060
slug: the-hybrid-form-of-gate-declarations
title: 闸门声明的混合式 —— 序 14（单序号）/ 16（条件式）/ 23（多点）三条声明**互斥**（`_validate_gate_exclusivity` 实测点名拒绝）⇒ 「第 1、3 轮停，**且**判词为 X 时也停」**结构上做不到**；`Z-1` 的混合式形态自 `GOAL-20261010-048` 登记以来**未做**
status: ACTIVE
created_at: 2026-10-12
updated_at: 2026-10-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 28**，由本次 replan 的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：三条闸门声明在 `packages/domain/program.py`
    **互斥**（`rg -n "mutually exclusive" packages/domain/program.py` ⇒ **命中 1 处**，
    `_validate_gate_exclusivity`，序 16/23 立）；三条声明的字段**逐个读出**
    （`human_gate_at_index: int | None` / `_on_verdicts: tuple[str,...] | None` /
    `_at_indexes: tuple[int,...] | None`）⇒ 同时声明即**点名拒绝** ⇒
    「第 1、3 轮停，**且**判词为 X 时也停」**结构上做不到**；而三条各自的机制
    （注册 / 判定 / 恢复，序 14/15/16/23）**都已全在** ⇒ 缺的只是**组合维度**。
    `Z-1` 的混合式形态自 `GOAL-20261010-048` 登记以来**未做**；**深度轴自序 23 起未推进**。
    (2) **为什么属深度轴**：轴的反面是「固定轮数的流水线加长」—— 本条让「在哪里停」
    **可以按多个维度同时声明**，是研究推进的**停止规则**从单一维度到组合维度的扩展。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**混合式**可声明（多点 **且** 条件）
    —— 缺省形态**逐字不变**；**不**解除「同一点上两条声明互斥」的既有纪律
    （那是**同一维度**的重复声明，不在本轮范围）；**不**新造机制。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿**：三条声明的类型逐字读出（单序号 / 条件式 / 多点）+ 互斥判词定位
      （行号 + 逐字）+ 三条各自的机制三段逐条定位 ⇒ 缺口 = **组合维度**。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-gate-hybrid.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **实现面（本轮验收的主体）**：混合式可声明（多点 **且** 条件）；缺省形态**逐字不变**；
      坏形态（空组 / 越界 / 重复 / 坏判词）**点名拒绝**；**不**解除同一维度上的既有互斥。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/application -q`
      ⇒ 全绿 + 新用例（缺省逐字不变 / 坏形态点名）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **读面 / 产品面接线**：推进面按混合式判定（两种触发**各自点名**是哪一条触发的）+
      两库同契约 + DTO 透传（动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例。
    status: PENDING
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`W-1` 混合声明被拒 ⇒ RED；
      `W-2` 只按多点判（条件被忽略）⇒ RED；`W-3` 只按条件判 ⇒ RED；
      `W-4` 缺省形态被改动 ⇒ RED。复原用**二进制读写**且 raw `sha256` 逐字节相同；
      **反证脚本带基线门**（未按压必须 GREEN，否则非 0 退出）；
      判词归档进树（`.cursor/plans/goals/evidence/`，`CR=0`）。
    verify: >-
      `scratch/goal060_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 28**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal060_closeout.py` ⇒ 全 `PASS`；
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
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261012-060 — 闸门声明的混合式

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 28**（轴 = **深度**）。
> **本行是 replan 的产物**（`replan_every_goals: 3` 在序 24/25/26 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = `GOAL-20261010-048` 登记的 `Z-1`（混合式）。
> **建档时 status = ACTIVE；子 PLAN 在开 cycle 1 时派生。**

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（三条声明类型 + 互斥判词 + 三段机制） | **实跑**：`scratch/probe-gate-hybrid.py` | PENDING |
| EC-02 | 混合式可声明（多点 **且** 条件；缺省逐字不变；坏形态点名） | `pytest tests/domain tests/application -q` | PENDING |
| EC-03 | 推进面双触发各自点名 + 两库同契约 + DTO 透传 + 快照同轮 | `pytest tests/api tests/adapters tests/contracts -q` | PENDING |
| EC-04 | 两向反证 `W-1`…`W-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | PENDING |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器全 `PASS`；两树 `TWO-TREE PASS` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 三条声明**互斥**的判词在树 | `rg -n "mutually exclusive" packages/domain/program.py` | **命中 1 处**（`_validate_gate_exclusivity`，序 16/23 立） |
| 2 | 三条声明的字段**逐个读出** | `rg -n "human_gate_at_index:\|human_gate_on_verdicts:\|human_gate_at_indexes:" packages/domain/program.py` | 三行都在（各自可选 ⇒ 缺省逐字不变） |
| 3 | 三条各自的机制**已全在**（不新造） | `rg -n "declared_gate_trigger\|declared_gate_verdict\|register_declared_gate" packages/application/run_orchestration/*.py` | 三段都在（序 14/15/16/23 建） |

**结论**：**声明面结构上只能三选一** —— 「第 1、3 轮停，**且**判词为 X 时也停」写不出来；
而三条机制**都已全在** ⇒ 缺的只是**组合维度**。**深度轴自序 23 起未推进**。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 混合式形态与三条既有声明**同一手法**（不新造机制） | 三条机制已全在 ⇒ 照抄一族 | 已定 |
| D-2 | 缺省形态**逐字不变** | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-3 | 坏形态**点名拒绝**（不静默降级） | 「点名而非静默降级」是本战役的禁令 | 已定 |
| D-4 | **同一点上**两条声明仍互斥（**不**解除既有纪律） | 那是**同一维度**的重复声明（会让「为什么停」读不出是哪一条要求的） | 已定 |
| D-5 | 混合式的**落库形态**（一列复合 vs 并列列）由 EC-01 读两条既有列后定 | 涉及既有列面 ⇒ 先量再定 | **待 EC-01** |

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
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者 | 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：`Z-1` 的**混合式形态**（多点 + 条件的组合声明与判定）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：`Z-3` 的通知外发 / 升级链；`W-2` 的内容级检测；`CC-2`·`CC-3`；
  `BB-3`；`DD-1`…`DD-3`；`AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` /
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
| （待开 cycle 1 后回填） | （待轮询） | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ 实测读数（见「事实层结论」）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 28** | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（按 EC 顺序） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 28**（**轴 = 深度**），并写修订记录行（只追加）。实测读数见「事实层结论」表（命令与读数同在）。五条 EC 全 PENDING。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
