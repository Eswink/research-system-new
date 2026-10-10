---
id: GOAL-20261010-044
slug: program-wait-reasons-become-distinguishable
title: 程序推进的**等待理由可区分** —— run 面已有「等审批」/「暂停」两个非终态，而**程序面**把「这一轮还在跑」与「这一轮停在人工闸门等人拍板」读成同一个 `WAIT`（恢复路径无法回答「该等谁」）
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 12**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含**新增判定种类**、改产品语义），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) **run 面已可区分** ——
    `packages/domain/run_state.py` 有「等审批」与「暂停」两个状态常量（`terminal()` 只含
    SUCCEEDED/FAILED/CANCELLED ⇒ 两者**非终态**）；(b) **程序面混用** ——
    `program_runner.py::_evaluate` 只按 `last.is_terminal` 分派：非终态一律落 `WAIT`，
    理由串是 `state=<s>` ⇒ 「还在跑（机械等待）」与「停在人工闸门等人拍板（需要人）」
    **同一个种类**；(c) 人工闸门在 **phase 面**已有（`phase_pause.pause_for_human_gate`
    注册审批 + `APPROVAL_REQUESTED` + 交回 service 暂存剩余 specs），但**程序推进**不知道
    「这一轮在等人」⇒ 恢复路径无法回答「该等谁」。
    (2) **为什么这属于连续性轴**：轴定义是「研究可中断、可恢复、可交接：中断后能接回，
    **恢复不重复已发生的副作用**，交接不丢上下文」。程序推进的 `WAIT` 是**恢复路径的入口判定**：
    它若把「等人」与「等机器」混成一体，恢复侧就无法决定「该不该重试 / 该找谁 / 该等多久」——
    这是**交接不丢上下文**在编排层的直接失真。**同族**：序 8 消灭的是「没有结论 vs 结论说停」
    的**范畴错误**（结论面上「跑失败了」被读成「结论说停」）；本条是**同一病**在**非终态面**的形态。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**等待理由可区分且可判定** ——
    「还在跑」/「等人拍板（含等的是谁、等什么）」互不混用，且判词**点名**可复核的事实。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建第二套审批存储（复用既有 `ApprovalStore` 与
    `APPROVAL_REQUESTED` 事件面）；**不**改 phase 面的人工闸门语义（逐字保持，由既有判据钉住）；
    **不**让程序推进**自动**批准或**自动**跳过人工闸门（人没拍板就是没拍板）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **把「等人拍板」读成「还在跑」**（那正是本轮要消灭的混淆）；**让程序推进绕过人工闸门**；
    **静默等待**（等待必须**点名**：等的是哪个审批 / 哪条 run）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (8) **边界（承继）**：GOAL-001…043 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…043 的未覆盖范围**原样保留**；
    GOAL-043 的 `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` /
    GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` /
    GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 12（连续性轴）落成**等待理由可区分**：① **勘察定稿** —— 实测现状
    （程序面 `WAIT` 混用「还在跑」与「停在人工闸门」）+ 定位可复用的缝（run 面的两个非终态常量 /
    phase 面的 `pause_for_human_gate` 与 `APPROVAL_REQUESTED` / 既有 `ApprovalStore`）（EC-01）
    → ② **判定种类扩齐** —— 新增**可区分**的种类（候选：`WAIT_FOR_APPROVAL`；「还在跑」仍用
    `WAIT`），且**互不混用**（读面按 kind 即可分派）（EC-02）→ ③ **点名面** —— 等待审批时的
    判词**点名**可复核事实：等的是**哪个审批**（`ApprovalRecord` 的标识）/ 哪条 run /
    什么状态（`cited_facts` 是原文）（EC-03）→ ④ **真的被用上（含反证）** —— 实跑：
    一轮停在人工闸门 ⇒ 推进落新种类且**点名审批**；同一装配下「还在跑」的轮**仍落** `WAIT`
    （两向可分）；**不得**自动批准 / 自动跳过（反证臂）（EC-04）→ ⑤ **自举收口**（复用既有机器）（EC-05）。
    **硬约束**：等待理由**互不混用**；等待**点名**（不静默）；**不**新建第二套审批存储；
    phase 面语义**逐字保持**；缺省（本 run 没有待审批）⇒ 行为 = 既有 `WAIT`（逐字不变）；
    m0 条数**仍是 23**；判词归档**进树**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 现状混用：`program_runner.py::_evaluate` 只按
      `last.is_terminal` 分派，非终态落 `WAIT`，`reason` 为 `第 N 轮尚未终止（state=<s>）⇒ 本轮不推进`；
      (b) run 面**已可区分**：`packages/domain/run_state.py` 有「等审批」/「暂停」两个常量且
      **不在** `terminal()` 集合内；(c) phase 面的人工闸门：`phase_pause.pause_for_human_gate`
      的入口条件（`human_gated` 集 + `approvals` store，缺一 fail-closed）与其副作用
      （注册 `ApprovalRecord` + `APPROVAL_REQUESTED` 事件 + 交回 service 暂存剩余 specs）；
      (d) 可复用的缝：`ApprovalStore` 的查询面（按 run 找待审批）/ `ProgramDecisionKind` 枚举 /
      `cited_facts` 原文面。
    verify: >-
      `rg -n "is_terminal|WAIT" packages/application/run_orchestration/program_runner.py`；
      `rg -n "WAITING_FOR_APPROVAL|PAUSED|terminal" packages/domain/run_state.py`；
      `rg -n "def pause_for_human_gate" -A20 packages/application/run_orchestration/phase_pause.py`；
      `rg -n "class ApprovalStore" -A12 packages/application/ports/`。
    status: PASS
  - id: EC-02
    criterion: >-
      **判定种类扩齐（可区分）**：`ProgramDecisionKind` 增一个**等待审批**的种类
      （候选名 `WAIT_FOR_APPROVAL`；「还在跑」仍是 `WAIT`）；域判据按集合相等钉住；
      **既有六态逐字保持**（`START` / `CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` /
      `WAIT` / `DEDUP` 与序 8/9 新增的四种一律不动）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py tests/domain -q` ⇒ 全绿 + 新用例。
    status: PASS
  - id: EC-03
    criterion: >-
      **点名面（等待不静默）**：等待审批时的 `reason` 与 `cited_facts` **点名**可复核事实 ——
      至少：哪条 run（`cited_run_id`）、运行的**状态原文**、以及**待审批的标识**
      （`ApprovalRecord` 的 id；查得到就点名，查不到 ⇒ **点名「查不到」**而不是编一个）。
      「还在跑」的判词**保持既有的 `state=<s>` 形态**（逐字不变）。
    verify: >-
      该判定的用例逐条（待审批在场 ⇒ 点名审批 id；无待审批 ⇒ 走既有 `WAIT`）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真的被用上（+ 反证）**：(a) 实跑：一轮停在人工闸门（经既有 `APPROVAL_REQUESTED` 面）
      ⇒ 推进落新种类且**点名审批**；(b) **反证臂①**：同一装配下「还在跑」的轮**仍落** `WAIT`
      （两向可分，不是把 `WAIT` 全改名）；(c) **反证臂②**：**不得**自动批准 / 自动跳过 ——
      推进**不**改变 `ApprovalRecord` 的状态、**不**消耗审批；(d) 缺省（无待审批）⇒
      行为**逐字不变**（`WAIT` + 既有理由串）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 12**，进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**；⑥ 承继残余逐条在位；⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal044_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **把「等人拍板」读成「还在跑」**（本轮要消灭的混淆）；**让程序推进绕过人工闸门**
      （不得自动批准 / 自动跳过）；**静默等待**（等待必须点名：等的是哪个审批 / 哪条 run）
    - >-
      **新建第二套审批存储**（复用既有 `ApprovalStore` / `APPROVAL_REQUESTED`）；
      **改 phase 面的人工闸门语义**（逐字保持，由既有判据钉住）
    - >-
      **同轮同步面**：仅当本轮新增判定种类**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
      （谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **改既有判据的申报纪律（承 `MEM-20261009-210`，逐条自证）**：任何对**既有**
      判据 / 测试文件的改动必须 ① **逐条枚举**改动面；② 用
      `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；③ **逐条比对谓词是否
      等同**（不得只写「强度未降」—— 那是一句**需要自证**的断言）；④ **收窄受判面必须
      显式申报**（写明收窄了什么与理由），**不得**称「强度不变」；⑤ 属**同轮同步集之外**
      的形态 ⇒ 命中 `escalation_triggers`，在 RECHECK 里**如实登记**。
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
child_plans:
  - .cursor/plans/tasks/PLAN-20261010-375-goal-044-ec01-04-program-wait-reasons.md
  - .cursor/plans/tasks/PLAN-20261010-377-goal-044-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-376-goal-044-ec01-04-program-wait-reasons.md
memory_entries: []
---

# GOAL-20261010-044 — 程序推进的等待理由可区分

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 12**（轴 = **连续性**；依赖序 8、11 ——
> 均已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 9/10/11 收口后到期），
> 已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 现状：程序面 `WAIT` 混用「还在跑」与「停在人工闸门」（实测 `_evaluate` 只按 `is_terminal` 分派） | PASS |
| EC-02 | 判定种类扩齐 | 新增等待审批的种类；既有各态**逐字保持** | PASS |
| EC-03 | 点名面 | 等待审批时判词点名 run / 状态 / **待审批标识**（查不到也点名）；「还在跑」逐字不变 | PASS |
| EC-04 | 真的被用上 | 实跑停在闸门 ⇒ 落新种类且点名；**反证**：「还在跑」仍落 `WAIT`；不得自动批准 / 跳过 | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得把**等人拍板**读成**还在跑**；
不得让程序推进**绕过人工闸门**；不得**静默等待**；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：程序面把两种「非终态」读成同一个种类

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 程序面只按 `is_terminal` 分派 | `packages/application/run_orchestration/program_runner.py::_evaluate` | `if not last.is_terminal:` ⇒ `WAIT` + `reason=f"第 {last_index} 轮尚未终止（state={last.state}）⇒ 本轮不推进"` |
| 1.2 | run 面**已可区分** | `packages/domain/run_state.py` | 有「等审批」/「暂停」两个状态常量；`terminal()` 只含 SUCCEEDED/FAILED/CANCELLED ⇒ 两者**非终态** |
| 1.3 | 人工闸门在 **phase 面** | `packages/application/run_orchestration/phase_pause.py::pause_for_human_gate` | 入口条件 = `phase_id in deps.human_gated` 且 `deps.approvals is not None`（**缺一 fail-closed**）；副作用 = 注册 `ApprovalRecord` + `APPROVAL_REQUESTED` 事件 + 剩余 specs 经 `on_pause` 交回 service 暂存 |
| 1.4 | **结论** | 1.1 + 1.2 + 1.3 | 程序推进**不知道**「这一轮在等人」⇒ 恢复路径无法回答「该等谁」；`cited_facts` 只有 `state=<s>` |
| 1.5 | 同族 | 序 8（GOAL-040）的立题 | 序 8 消灭的是「**没有结论** vs **结论说停**」的范畴错误；本条是同一病在**非终态面**：把「**需要人**」读成「**等机器**」 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 审批存储是既有 Port | `packages/application/ports/`（`ApprovalStore`） | 与 API 的审批面同一实例（**不**新建第二套） |
| 2.2 | 判定种类是枚举（可扩） | `packages/domain/program.py::ProgramDecisionKind` | 十种（原六 + 序 8 的三 + 序 9 的一） |
| 2.3 | 决策 append-only 且带原文 | `packages/domain/program.py::ProgramDecision` | `cited_facts`（被引事实**原文**）—— 点名面据此落档 |
| 2.4 | 既有判据面 | `tests/e2e/test_program_advance_on_the_run_path.py`（7 例）/ `tests/application/run_orchestration/test_program_runner.py`（18 例） | 本轮新增用例与它们**同族** |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 判定种类的域判据是**集合相等** | `tests/domain/test_research_program.py::test_decision_kinds_separate_conclusion_from_guardrail` | 新增种类必须**同轮加进集合**（纯加法登记，谓词形态一字未改） |
| 3.2 | 本轮**预期**改动面 | `packages/domain/program.py`（+1 枚举）+ `program_runner.py`（分派 + 点名）+ 驱动判据 + e2e 判据 + 上述域判据的集合 | 逐条枚举进 RECHECK（含 `numstat`） |
| 3.3 | **不**改 phase 面语义 | `phase_pause.py` / 既有 e2e（人工闸门） | 只读；本轮**不**触碰 |

### 4. 本轮**不**碰的面（逐条明写）

- phase 面人工闸门的语义与实现（逐字保持）；
- D 组审批通道（`external.publish` / `package.install` / `git.commit` / `workspace.delete`）——
  **本轮不接通**；
- 读面认证 / 多租户 / 部署面 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 新种类的**名称** | **已定**：`WAIT_FOR_APPROVAL`（「还在跑」仍是 `WAIT`） |
| ② | 审批标识从哪来 | **待 cycle 1 定**：从既有 `ApprovalStore` 按 `run_id` 查（查不到 ⇒ **点名「查不到」**，不编一个） |
| ③ | 分派顺序 | **已定**：`is_terminal` **先**判（既有语义不动）⇒ 非终态内部再分「等审批 / 还在跑」 |
| ④ | 缺省（无待审批） | **已定**：**逐字保持**既有 `WAIT`（含理由串） |
| ⑤ | 承接面 | **不动**（复用既有 `ApprovalStore`，不新增能力） |

## 循环入口协议（幂等重入）

驱动方进入时，按「迭代日志」最后一行 + 工作树/远端实况判定续点（与 `goals/README.md`
同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件；**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**。

## 单 cycle SOP

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261010-044` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/application` / `tests/domain` / `tests/e2e`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：等待理由**互不混用**；等待**点名**（不静默）；**不**新建第二套审批存储；
phase 面语义**逐字保持**；**不**自动批准 / 跳过；缺省逐字不变；**改既有判据必须走自证清单**
（`MEM-20261009-210`）；受判面不得是交集（承 `MEM-160`）；留档二进制写盘、判词归档进树；
台账逐提交；新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 / **Docker registry 5xx 或限流** | 等窗口重跑 1 次；仍败 → 记录三条取证后 BLOCKED |
| 治理/安全门禁 | validator / Mimosa / 记录面判据 | 修或登记；**不得绕过** |
| 资源阈值型偶发 | CI 上 RSS 类阈值偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类 | **按生成器重新生成** |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS` + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  本文件收口；收口动作照 `MEM: goal-closeout-procedure` 并声明 `verify_paths` ≥ 2 路、
  **用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers` 或 `budget.max_cycles` 触顶（20）。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门
的旧脚本；GOAL-019…043 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`V-1`…`V-3`）

- `V-1`（**程序级自动处置不在本轮**，未覆盖）：本轮让「等人」**可判定且点名**；
  **不**做「等太久 ⇒ 自动催办 / 自动升级 / 自动超时取消」（那是审批处置，属 D 组面）。
- `V-2`（**跨程序的等待传播不在本轮**，未覆盖；承 `T-3`）：等待按**程序**划界。
- `V-3`（**等待的时长 / SLA 不在本轮**，未覆盖）：判词给**事实**（等的是谁），不给时限策略。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **等待理由**：**已收口** = 「等人拍板」与「还在跑」**互不混用**且判词**点名**审批标识；
  **未覆盖** = 等待的处置（催办 / 升级 / 超时）与 SLA（`V-1` / `V-3`）。
- **人闸门**：**已收口** = 程序推进**认得**闸门并**不绕过**它；**未覆盖** = D 组审批通道本身
  的接通（触达即 BLOCKED）与跨程序等待传播（`V-2`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `82ac5ba`（replan） | **无自己的 run**（同批推送） | 序 12 新增（保留槽）+ 修订记录行 |
| `7bed255`（本 GOAL 建档） | `38019098501` **Push on main / CodeQL success**；`38019098883` **M0 cancelled** —— `cancel-in-progress`（被 `905e602` 的推送取消）⇒ `covered_by 38019928888` | 五 EC + 三条事实层读数 |
| `905e602`（cycle 1 = EC-01…EC-04） | `38019928888` **M0 success**（8 job 全 success）+ `38019928509` **Push on main / CodeQL success** | 等待理由可区分 + 点名四态 + 判据 + 两向反证；本地 **m0 23/23**（5335 passed, 228 skipped）；**实测取证** |
| `7a203d5`（cycle 1 记录回写 = 本批 HEAD） | `38021171660` **Push on main / CodeQL success** + `38021172370` **M0 success**（8 job 全 success） | EC 终态 + 迭代日志 + 状态历史；**实测取证**；覆盖 `82ac5ba` / `7bed255` 的记录面 |
| （本行所在提交：台账尾巴） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 台账尾巴：只改 `.cursor/plans/goals/GOAL-20261010-044-*.md`；其结论由**下一个 cycle 的台账**取证 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261010-375` | `905e602` | EC-01…EC-04 全 PASS：**等待理由可区分** —— ① 域 +`WAIT_FOR_APPROVAL`；② 新模块 `program_waiting.py`（`program_runner.py` 有 450 行硬上限）：`WAITING_FOR_APPROVAL` / `PAUSED` ⇒ 新种类 + **点名待审批 id**（经既有 `ApprovalStore.list_for_run`，**只读**）；其余非终态 ⇒ `WAIT`（理由串与 `cited_facts` **逐字保持**）；③ **点名四态**全点名（查到待决 / 无待决「查不到」/ 缺审批面「未提供审批面」/ 面抛异常点名异常）；④ 新判据 **7 passed**（含反证：RUNNING 即便有待决也仍 `WAIT` 逐字相同、非「待决」不算、只读面）；⑤ 两向反证 **W-1/W-2 全红** + 二进制复原 raw `sha256` 一致；⑥ **按压发现并清掉一处死值**（`pending_approval` 早先返回的 id 串无人用）；广面 2464 passed；**全量 m0 23/23**（5335 passed） | （见 CI 台账）| 规模门拆文件（`test_program_runner` 552→427 + 新 151）；mypy 的 Literal 恒真比较 ⇒ 改比 `.value` | EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **三条实测读数**（程序面只按 `is_terminal` 分派 ⇒ 非终态一律 `WAIT`；run 面已有两个非终态常量；phase 面人工闸门经 `pause_for_human_gate` + `APPROVAL_REQUESTED`）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 12** | （见 CI 台账） | — | 五条 EC 全 PENDING；新种类名与审批查询面（①②）待 cycle 1 落 | cycle 1（EC-02 种类 + EC-03 点名 + EC-04 实跑） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**等待理由可区分** —— 程序推进此前把「这一轮**还在跑**（等机器）」与「停在**人工闸门**等人拍板（等人）」读成同一个 `WAIT`（实测：`_evaluate` 只按 `is_terminal` 分派）。**已修**：新增 `WAIT_FOR_APPROVAL`（`WAITING_FOR_APPROVAL` / `PAUSED` ⇒ 等人）+ 判词**点名待审批 id**（经既有 `ApprovalStore.list_for_run`，**只读**、**不**自动批准/跳过）；其余非终态仍 `WAIT` 且理由串**逐字保持**。**点名四态全点名**（查到待决 / 查不到 / 缺审批面 / 面故障）。新判据 7 passed（含反证）；两向反证 W-1/W-2 全红；**按压还发现并清掉一处死值**。广面 2464 passed；**全量 m0 23/23**（`PASS [` 24 / `FAILED [` 0 / **5335 passed, 228 skipped**）。EC-05 待收口。**不得**宣称安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 12**。只读勘察 + **三条实测读数**：(a) `program_runner.py::_evaluate` 只按 `last.is_terminal` 分派 ⇒ 非终态一律落 `WAIT`（理由串 `state=<s>`）；(b) `packages/domain/run_state.py` 已有「等审批」/「暂停」两个非终态常量（**run 面可区分**）；(c) 人工闸门在 phase 面（`pause_for_human_gate` 注册审批 + `APPROVAL_REQUESTED`），但**程序推进不知道这一轮在等人** ⇒ 恢复路径无法回答「该等谁」。**同族**：序 8 消灭的范畴错误在**非终态面**的形态。五条 EC 全 `PENDING`。**不做数量目标**；**不**新建第二套审批存储；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
