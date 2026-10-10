---
id: GOAL-20261010-046
slug: program-level-human-gate-becomes-declarable
title: 程序级人工闸门**可声明** —— 程序**只能认得**别人留下的等待（序 12），**自己无法声明**「到第 N 轮停下等人」：程序域实体无闸门声明位、程序面三文件对 `human_gate` 零命中，而 phase/run 面的实现已完整可复用
status: ACHIEVED
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 14**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」；承担者 = `GOAL-037` 的实测残余 `O-2`）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改产品语义、新增判定种类、新增声明字段），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) `ResearchProgram` 的字段表只有
    `id` / `project_id` / `protocol_id` / `max_runs` / `continue_rule` / `max_attempts_per_index`
    —— **无**任何闸门声明位；(b) 程序面三文件（`program.py` / `program_runner.py` /
    `program_waiting.py`）对 `human_gated` / `human_gate` **零命中**；(c) 序 12（GOAL-044）
    只让程序**认得** `WAITING_FOR_APPROVAL` 这个**状态**（别人留下的等待），**没让它自己
    声明闸门**；(d) 但 **phase/run 面的实现完整可复用**：`human_gates.pending_human_gates`
    的语义已是「声明的 `HUMAN_GATE` phase **减** 已裁决审批」，`phase_pause.pause_for_human_gate`
    已含「注册 `ApprovalRecord` + 发 `APPROVAL_REQUESTED` + 落 `WAITING_FOR_APPROVAL`」三步。
    (2) **为什么这属于连续性轴**：轴定义是「研究可中断、可恢复、可交接：中断后能接回，
    恢复不重复已发生的副作用，交接不丢上下文」。**「中断」必须能被程序自己声明** ——
    若程序只能等**别人**（协议里的 phase 闸门 / 外部操作）制造中断，「人在环」就不在
    **编排能力**里，而只是一个恰好发生过的外部事件。这正是 `O-2` 的形态。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**程序级人工闸门可声明、可判定、可点名** ——
    声明「到第 N 轮停下等人」后，推进必须落**可区分**的判定并**点名**等的是哪一次闸门。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建第二套审批存储或第二套闸门机制（复用既有
    `ApprovalStore` 与 `human_gates` / `phase_pause` 的语义）；**不**改 phase 面闸门语义
    （逐字保持）；**不**做自动批准 / 自动放行 / 自动超时（人没拍板就是没拍板）；
    **不**把闸门做成「额外一层检查」（那是「不算推进」的形态）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让程序绕过自己声明的人工闸门**；**静默跳过闸门**（跳过 / 等待必须**点名**）；
    **把「等人拍板」与「还在跑」混用**（承序 12 的判定纪律）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (8) **边界（承继）**：GOAL-001…045 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…045 的未覆盖范围**原样保留**；
    GOAL-045 的 `W-1`…`W-3` / GOAL-044 的 `V-1`…`V-3` / GOAL-043 的 `U-1`…`U-3` /
    GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` /
    GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` /
    `R26-*` 终态**原样保留**（其中 `O-2` 由本轮**推进**），本轮**只追加**。
objective: >-
    让 MAINLINE 序 14（连续性轴）落成**程序级人工闸门可声明**：① **勘察定稿** —— 实测
    「程序面零闸门声明」的完整形状 + 定位 phase/run 面的可复用实现（`pending_human_gates`
    的语义与 `pause_for_human_gate` 的三步副作用）（EC-01）→ ② **声明面** ——
    `ResearchProgram` 可**声明**闸门（候选：`human_gate_at_index` / 一组序号；缺省 ⇒
    **既有行为逐字不变**），并**真的落库**（两库同契约）（EC-02）→ ③ **判定与推进** ——
    推进在声明点**停下等人**：判定种类**可区分**（复用序 12 的 `WAIT_FOR_APPROVAL` 面或新增）、
    判词**点名**「第 N 轮是声明的人工闸门」与**待审批标识**（经既有 `ApprovalStore`，**只读**）
    （EC-03）→ ④ **真的被用上（含反证）** —— 实跑：声明闸门 ⇒ 推进在**该轮之后**停下且点名；
    **在该轮之前不停**（反证①）；**未声明 ⇒ 行为逐字不变**（反证②）；**不**自动放行（反证③）
    （EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：不声明 ⇒ **逐字不变**；**不**新建第二套审批/闸门机制；phase 面语义**逐字保持**；
    **不**自动批准 / 跳过 / 超时；等待**点名**；m0 条数**仍是 23**；判词归档**进树**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) `ResearchProgram` 字段表**无**闸门声明位（逐字列出）；
      (b) 程序面三文件 `rg -c "human_gated|human_gate"` **全 0**；(c) 序 12 只做「认得状态」的
      证据（`_AWAITING_HUMAN` / `WAIT_FOR_APPROVAL` 在树，而**声明**面零）；(d) **可复用的缝**：
      `human_gates.pending_human_gates` 的语义（声明的 `HUMAN_GATE` − 已裁决）与
      `phase_pause.pause_for_human_gate` 的三步副作用（注册审批 / 发事件 / 落 `WAITING_FOR_APPROVAL`）；
      (e) **两库的程序表**是否已有可承载的列（决定要不要迁移）。
    verify: >-
      `uv run --frozen --no-sync python -B -c "…dataclasses.fields(ResearchProgram)"` ⇒ 字段表；
      `rg -c "human_gated|human_gate" packages/domain/program.py
      packages/application/run_orchestration/program_{runner,waiting}.py` ⇒ 全 0；
      `rg -n "def pending_human_gates" -A12 packages/application/run_orchestration/human_gates.py`；
      `rg -n "max_attempts_per_index|human" adapters/{sqlite,postgres}/program_store.py`。
    status: PASS
  - id: EC-02
    criterion: >-
      **声明面（可选 + 两库同契约）**：`ResearchProgram` 可**声明**闸门（候选：
      `human_gate_at_index: int | None` 或序号集合）；**缺省 ⇒ 既有行为逐字不变**；
      **两库**（SQLite / PG）**真的落库并往返一致**（含缺省值）；非法声明（越界 / 负数）⇒ **点名**；
      建程序面（DTO / 路由）可传该声明。**若无新迁移**要给出证据（列已在表上或声明不需落库）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters/sqlite
      tests/postgres tests/api -q` ⇒ 全绿 + 新用例（两库各一组 + 缺省 + 非法）。
    status: PASS
  - id: EC-03
    criterion: >-
      **判定与推进（点名）**：推进在**声明的闸门轮**停下等人 —— 判定种类**可区分**于
      「还在跑」与「结论判停」（复用或扩展序 12 的 `WAIT_FOR_APPROVAL` 面）；
      判词**点名**「第 N 轮是**声明的人工闸门**」与**待审批标识**（经既有审批面**只读**查询；
      查不到 / 缺面 ⇒ **点名**，不静默）；**不**自动放行、**不**消耗审批。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration -q` ⇒ 全绿 + 新用例（在闸门轮 / 不在闸门轮 / 未声明）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真的被用上（+ 三条反证）**：(a) 实跑：程序声明「第 2 轮是人工闸门」⇒ 第 1 轮跑完后的推进
      落**闸门判定**且**点名**；解掉审批后（**经既有审批面**）⇒ 继续推进；(b) **反证臂①**：
      在第 2 轮**之前**的推进**不得**被闸门挡住；(c) **反证臂②**：**未声明** ⇒ 行为与修正前
      **逐字相同**（`START` / `CONTINUE` 序列不变）；(d) **反证臂③**：推进**不**改变审批状态
      （`ApprovalRecord` 未被写 / 未被消耗）；(e) 缺审批面 ⇒ **点名**（不静默当成无闸门）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单
      （GOAL-043 立的判据要求）；② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档
      进树（**二进制写盘**、`CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、
      仓库 `.venv`、不接管道）；④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py`
      绿（**本 GOAL 的 id 已在程序表序 14**）；⑤ CI 台账**逐提交**；⑥ 承继残余逐条在位；
      ⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal046_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL（修复轮后 **74 判词 / 0 FAIL**）；
      `tools/two_tree_recheck.py --script-mode shared --base-ref <含交付面的提交>` ⇒
      `TWO_TREE PASS`（按入口实际措辞）；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`。**修复轮**（`PLAN-20261010-387`）补的
      证据链：快照同步（`docs/api/openapi.m13.json` 含 `human_gate_at_index`）+
      EC-02/EC-04 声明的行为面用例（SQLite `/` PG `/` 域 `/` e2e 逐条在场，例数下界钉住）。
    status: PASS
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
      **让程序绕过自己声明的人工闸门**；**静默跳过闸门**（跳过 / 等待必须**点名**）；
      **把「等人拍板」与「还在跑」混用**（承序 12）
    - >-
      **新建第二套审批存储或第二套闸门机制**（复用既有 `ApprovalStore` / `human_gates` /
      `phase_pause`）；**改 phase 面闸门语义**（逐字保持）；
      **自动批准 / 自动放行 / 自动超时**（人没拍板就是没拍板）
    - >-
      **同轮同步面**：仅当本轮新增可选声明**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
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
  - .cursor/plans/tasks/PLAN-20261010-383-goal-046-ec01-04-program-human-gate.md
  - .cursor/plans/tasks/PLAN-20261010-385-goal-046-ec05-self-bootstrap-closeout.md
  - .cursor/plans/tasks/PLAN-20261010-387-goal-046-repair-snapshot-sync-and-declared-cases.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-388-goal-046-repair-snapshot-sync-and-declared-cases.md
memory_entries:
  - extraction-must-not-re-point-existing-criteria
  - declared-verify-cases-must-actually-exist
---

# GOAL-20261010-046 — 程序级人工闸门可声明

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 14**（轴 = **连续性**；依赖序 12 ——
> 已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 11/12/13 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = `GOAL-037` 的实测残余 `O-2`。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 程序面**零**闸门声明（域实体无字段 / 三文件零命中）+ phase/run 面实现可复用 | PASS |
| EC-02 | 声明面 | `ResearchProgram` 可声明闸门（可选、缺省逐字不变）；两库落库往返；非法点名 | PASS |
| EC-03 | 判定与推进 | 在闸门轮停下等人：判定可区分 + 点名闸门与待审批；不自动放行 | PASS |
| EC-04 | 真的被用上 | 实跑停在该轮；**反证**：轮前不停 / 未声明逐字不变 / 审批不被消耗 / 缺面点名 | PASS |
| EC-05 | 自举收口 | 验证器进树（两处射程）+ 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**绕过或静默跳过**声明的人工闸门；
不得把「等人拍板」与「还在跑」**混用**；不得**自动**批准 / 放行 / 超时；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：程序**只能认得**等待，**不能声明**闸门

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 程序域实体**无**闸门声明位 | `packages/domain/program.py::ResearchProgram` | 字段表 = `id` / `project_id` / `protocol_id` / `max_runs` / `continue_rule` / `max_attempts_per_index` / 两个时间戳 —— **无**任何闸门位 |
| 1.2 | 程序面三文件对闸门**零命中** | `rg -c "human_gated\|human_gate" packages/domain/program.py packages/application/run_orchestration/program_{runner,waiting}.py` | **全 0** |
| 1.3 | 序 12 只做了「认得状态」 | `program_waiting.py::AWAITING_HUMAN` / `ProgramDecisionKind.WAIT_FOR_APPROVAL` | 两者在树（**状态**面），而**声明**面零 ⇒ 程序只能等**别人**制造的中断 |
| 1.4 | phase/run 面实现**完整可复用** | `human_gates.py::pending_human_gates` | 语义 = 「声明的 `HUMAN_GATE` phase **−** 本 run 已裁决审批（`status != "PENDING"`）」；无 store ⇒ 空集（fail-closed） |
| 1.5 | 闸门的**副作用**三步已在 phase 面 | `phase_pause.py::pause_for_human_gate` | 注册 `ApprovalRecord` + 发 `APPROVAL_REQUESTED` + 落 `WAITING_FOR_APPROVAL`（剩余 specs 经 `on_pause` 交回 service 暂存） |
| 1.6 | 闸门**集**由 service 注入 | `phase_runner.py`（`human_gated: frozenset[str]`）/ `service.py`（`pending_human_gates(...)`） | 集合是**按 run** 算出来的（phase 维度）⇒ 程序维度**不存在** |
| 1.7 | **结论** | 1.1–1.6 | 「人在环」目前只是**恰好发生过的外部事件**，不是**编排能力**；`O-2` 的形态即此 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 审批存储是既有 Port（**只读**面已够） | `packages/application/ports/approval_store.py` | `register` / `list_pending` / `list_for_run` / `get` / `replace`；序 12 的判定面**只用** `list_for_run` |
| 2.2 | 程序推进的判定面 | `program_runner.py` / `program_waiting.py` | 已有 `WAIT` / `WAIT_FOR_APPROVAL` 两类等待（序 12）⇒ 本条的「闸门等待」可**复用**该面而不是新造 |
| 2.3 | 程序声明面的既有形态 | `ResearchProgram.max_attempts_per_index`（序 9 加） | 「**可选声明** + 缺省逐字不变 + 两库落库 + 建程序 DTO 透传」这一整套手法**现成**（照抄） |
| 2.4 | 判据面 | `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py`（7 例）/ `tests/e2e/test_program_advance_on_the_run_path.py`（7 例）/ `tests/domain/test_research_program.py` | 本轮新增用例与它们**同族** |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 判定种类的域判据是**集合相等** | `tests/domain/test_research_program.py::test_decision_kinds_separate_conclusion_from_guardrail` | 若新增种类 ⇒ **同轮加进集合**（纯加法登记，谓词形态一字未改） |
| 3.2 | 程序表的两库实现 | `adapters/sqlite/program_store.py` / `adapters/postgres/program_store.py` + `migrations/019_program_attempts.sql` | 列清单与迁移手法**现成** ⇒ 若需新列，照 `019` 的形态（只加列 + 缺省回填） |
| 3.3 | 本轮**预期**改动面 | 域（+1 可选声明）+ 两库（落库）+ 建程序 DTO/路由 + 判定面 + 判据 | 逐条枚举进 RECHECK（含 `numstat`） |

### 4. 本轮**不**碰的面（逐条明写）

- phase 面的人工闸门语义（逐字保持）；
- 审批通道本身（D 组面，触达即 BLOCKED）：不放开 `external.publish` / `package.install` /
  `git.commit` / `workspace.delete` 的放行；
- 自动处置（催办 / 升级 / 超时取消）—— 承 `GOAL-044` 的 `V-1`；
- 读面认证 / 多租户 / 部署面 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 声明形态 | **待 cycle 1 定**：候选 = `human_gate_at_index: int \| None`（单点）或序号集合（多点）；判据是「可点名 + 缺省逐字不变 + 可落库」 |
| ② | 是否新增判定种类 | **待 cycle 1 定**：**优先复用**序 12 的 `WAIT_FOR_APPROVAL`（同一件事：等人拍板）；只有读面无法区分「声明闸门」与「别人留下的等待」时才新增 |
| ③ | 要不要新迁移 | **待 cycle 1 复核**：照 `019` 的形态（只加列 + 缺省回填）或复用既有列 |
| ④ | 何时停下 | **已定**：**该轮跑完之后**的推进停下（不是「起该轮之前」）—— 闸门语义是「这一轮的结果要人看」 |
| ⑤ | 承接面 | **不动**（复用既有审批面，不新增能力） |

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

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261010-046` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/domain` / `tests/adapters` / `tests/postgres` / `tests/application` / `tests/e2e`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**不声明 ⇒ 逐字不变**；**不**新建第二套审批/闸门机制；phase 面语义**逐字保持**；
**不**自动批准 / 跳过 / 超时；闸门等待与「还在跑」**互不混用**且**点名**；
**改既有判据必须走自证清单**（`MEM-20261009-210`）；受判面不得是交集（承 `MEM-160`）；
留档二进制写盘、判词归档进树；台账逐提交；新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 / **Docker registry 5xx 或限流** | 等窗口重跑 1 次；仍败 → 记录三条取证后 BLOCKED |
| 治理/安全门禁 | validator / Mimosa / 记录面判据 | 修或登记；**不得绕过** |
| **EC-05 时序红** | 断言集含「归档存在性」而归档尚未提交 | **时序**（非缺陷、非放宽）⇒ 归档提交后复取证 |
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
GOAL-037 的 `O-1` / `O-3` / `O-4` / `O-5`（**`O-2` 由本轮推进**）；
GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；
历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；GOAL-019…045 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`X-1`…`X-3`）

- `X-1`（**闸门的处置不在本轮**，未覆盖；承 `V-1`）：本轮让闸门**可声明 / 可判定 / 可点名**；
  **不**做催办 / 升级 / 超时取消。
- `X-2`（**多点闸门 / 条件闸门不在本轮**，未覆盖）：本轮最多到「按序号声明」（是否支持
  多个序号或条件式声明由 cycle 1 的决策①定；**条件式**（如「分数低于 X 才停」）**不在**）。
- `X-3`（**D 组审批通道本身不在本轮**，未覆盖；触达即 BLOCKED）：闸门用的审批面是**既有**实例；
  不放开任何 destructive 能力的放行。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **闸门声明**：**已收口** = 程序**自己**能声明闸门、推进在该点停下且点名；
  **未覆盖** = 条件式 / 多点声明（`X-2`）与闸门后的自动处置（`X-1`）。
- **人在环**：**已收口** = 「人在环」成为**编排能力**（可声明、可判定、可点名）；
  **未覆盖** = D 组审批通道本身（`X-3`）与审批的用户体验面。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （本 GOAL 建档提交） | 待取证 | replan（序 14 新增，承担者 `O-2`）+ 建档（五 EC + 事实层读数） |
| （后续逐条填） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `PLAN-20261010-387` | （见 CI 台账） | **修复轮**：① **CI 真红照实修** —— 快照按生成器重生成（`+23 / -0`），`test_openapi_snapshot.py` **一字未改**且 8 passed，并把该面写进收口断言集（**74 判词 / 0 FAIL**）；② **EC-02 / EC-04 声明的行为面用例补齐** —— SQLite 5 / PG 3 / 域 10 / e2e 9（含**成对**的「声明闸门拦下」vs「未声明逐字不变」），例数下界钉进断言集（**纯收紧**）；③ 两树 + 归档重新定格（**76 判词** / `sha256` 相同 `9d1c8a1c…` / 归档两份各 **2897 B / 76 行 / `CR=0`**）；④ 四道门 + 定向套件 41 例全绿；⑤ **as-is m0 23/23**（在**全部记录之后**、独占、仓库 `.venv`、不接管道：`PASS [` 24 / `FAILED [` 0 / **5565 passed, 21 skipped**；PG 容器本轮已启 ⇒ PG 标记用例实跑）| （见 CI 台账）| 判据抓到「实现与文本在场但**用例不存在**」+ 本地看不见的快照漂移 | 五条 EC 收口（证据链补齐）| GOAL 收口复检（`RECHECK-20261010-388`）|
| 2 | `PLAN-20261010-385` | `de9d396` | EC-05 五条 AC 全 PASS：收口验证器 **69 判词 / 0 FAIL**（标准断言集**一行未重写**）+ 两处射程**纯收紧**（`IN_SCOPE` +2 行 / **GOAL-043 立的分区清单** +1 行、下界 15→16）+ **两树 `TWO-TREE PASS`**（两路 **69 判词** / `sha256` 相同 `91de2b87…`）+ 归档定格（两份 **2585 B / 69 行**、`CR=0`）+ 治理 + 宪章判据 + **as-is m0 23/23** | （见 CI 台账）| — | 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261010-386`）|
| 1 | `PLAN-20261010-383` | （见 CI 台账） | EC-01…EC-04 全 PASS：**程序级人工闸门可声明** —— ① 域 +1 **可选** `human_gate_at_index`（缺省 `None` ⇒ 逐字不变；越界**点名**）；② **两库同契约**（SQLite schema + 迁移 **020** 只加列；PG `INSERT` 带列）；③ DTO / 路由 / 读面透传；④ 第 N 轮**跑完之后**的推进被拦住（**复用**序 12 的 `WAIT_FOR_APPROVAL`）+ **点名**声明值与待审批；语义**照抄** phase 面 `pending_human_gates`（声明的闸门 − 已裁决）；⑤ **三向反证 G-1/G-2/G-3 全红**（绕过 / 轮前误拦 / 已裁决仍拦）+ 二进制复原 raw `sha256` 一致；⑥ **规模门逼出的搬迁撞红既有判据**—— `goal041` 的两条按**位置**写死 ⇒ 搬迁即假红，**被 GOAL-043 立的「零判负」判据当场捕获** ⇒ 改成**判关系不判位置**（沉淀 `MEM-20261010-215`）| （见 CI 台账）| 判据抓到「搬迁打断按位置写死的断言」| EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **四条实测读数**（域实体无闸门位 / 程序面三文件零命中 / phase 面实现可复用（语义 + 三步副作用）/ 闸门集按 run 算）⇒ 定位 `O-2` 形态；五条 EC 全 PENDING；MAINLINE 程序表**新增序 14** | （见 CI 台账） | — | 五条 EC 全 PENDING；声明形态（①）与判定种类（②）待 cycle 1 落 | cycle 1（EC-02 声明面 + EC-03 判定与推进） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | ACTIVE | **cycle 3（修复轮 `PLAN-20261010-387`）—— 收口依据更正 + 三处缺口收口**：**CI 实测**在 `de9d396` 上抓到**真红**（`tests/contracts/test_openapi_snapshot.py` 的 `assert regenerated == committed`）—— cycle 1 改了建程序 DTO 却**未**重生成并提交 `docs/api/openapi.m13.json`；**为什么本地看不见**：该判据**重生成后比对**（会覆写文件）⇒ 本地跑一次就「自我修复」，工作树里的快照从此比 HEAD 新（**那个 `M` 的来源，不是 CRLF 伪影**）。另复核发现 **EC-02 / EC-04 的 `verify` 行点名的行为面用例当时并不存在**（实测 `rg -l human_gate_at_index tests/` 只有判定面那一个文件）。**已修**：① 快照按生成器重生成并提交（`+23 / -0`），判据**一字未改**且 8 passed，并把「快照含本轮字段」写进收口断言集；② 补齐 SQLite **5** / PG **3** / 域 **10** / e2e **9** 例（含**成对**的声明闸门拦下 vs 未声明逐字不变），例数下界钉进收口断言集（**纯收紧**）；③ 两树 + 归档重新定格。沉淀 `MEM-20261010-216`（「声明的 verify 用例必须真的存在」）。**收口状态在修复轮完成前不成立** —— 本行即为按实测的更正。独立复检：`RECHECK-20261010-388`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、**两处射程纯收紧**（`IN_SCOPE` + GOAL-043 立的射程分区清单）、两树 **`TWO-TREE PASS`**（两路 **69 判词** / `sha256` 相同 `91de2b87…`）、判词归档进树（两份各 2585 B / 69 行 / `CR=0`）、as-is m0 **23/23**（记录写完之后）、治理 + 宪章判据绿、CI 台账逐提交。**一处时序如实登记**：两树首轮红（bootstrap：归档在提交之后才存在）。**收口后不再推进本 GOAL**；残余 `X-1`…`X-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261010-386`（PASS_WITH_WARNINGS）。 |
| 2026-10-10 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**程序级人工闸门可声明** —— 此前程序只能**认得**别人留下的等待（序 12），**自己无法声明**闸门（域实体无字段 / 程序面三文件零命中）。**已修**：域 +1 可选声明（缺省逐字不变、越界点名）+ 两库同契约落库（迁移 **020** 只加列）+ DTO/路由透传 + 第 N 轮跑完后**被拦住并点名**（复用 `WAIT_FOR_APPROVAL`；语义照抄 phase 面 `pending_human_gates`）+ **不**自动放行。三向反证全红。**一处实测**：为守 450 行规模门所做的**搬迁**撞断了 `goal041` 的两条**按位置写死**的断言 —— **被 GOAL-043 立的「零判负」判据当场捕获** ⇒ 改成「判关系不判位置」，沉淀 `MEM-20261010-215`。EC-05 待收口。**不得**宣称安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 14**（承担者 = `GOAL-037` 的实测残余 `O-2`）。只读勘察 + **四条实测读数**：(a) `ResearchProgram` 字段表**无**任何闸门声明位；(b) 程序面三文件（`program.py` / `program_runner.py` / `program_waiting.py`）对 `human_gated` / `human_gate` **零命中**；(c) 序 12 只让程序**认得** `WAITING_FOR_APPROVAL` **状态**（别人留下的等待），**没让它自己声明闸门**；(d) **phase/run 面实现完整可复用** —— `human_gates.pending_human_gates` 的语义 = 声明的 `HUMAN_GATE` phase **减**已裁决审批（无 store ⇒ fail-closed），`phase_pause.pause_for_human_gate` 已含「注册审批 + 发事件 + 落 `WAITING_FOR_APPROVAL`」三步。**结论**：「人在环」目前只是**恰好发生过的外部事件**，不是**编排能力**。五条 EC 全 `PENDING`。**不做数量目标**；**不**新建第二套审批/闸门机制；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
