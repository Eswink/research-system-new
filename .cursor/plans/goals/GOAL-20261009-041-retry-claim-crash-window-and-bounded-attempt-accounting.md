---
id: GOAL-20261009-041
slug: retry-claim-crash-window-and-bounded-attempt-accounting
title: 重试的**有界性成为可判定事实** —— 「已认领但未落库」的崩溃窗口在**失败重试**面上必须去重，否则声明的 `max_attempts_per_index` **不成立**（上界可被无限绕过）
status: ACTIVE
created_at: 2026-10-09
updated_at: 2026-10-09
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-09 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 9**，由**前序 GOAL 的实测残余**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含**新增判定种类**、改产品语义），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：GOAL-20261008-040 声明「重试**有界**」
    （`max_attempts_per_index`，缺省 1 = 不重试），但它只对**已落库**的失败轮成立 ——
    **认领后未落库**（崩溃窗口）时，`RETRY_FAILED_RUN` 不经 `_after_hit`
    ⇒ **不经过 DEDUP**（`_claimed_but_missing` 只认 `CONTINUE`）⇒ 反复「认领即崩」
    可**无限**重试（实测：声明上界 `2`，连推 5 次全部落 `RETRY_FAILED_RUN`
    且 `attempts=1/2` 原样不动、**永不**升到 `STOP_RUN_FAILED`）。
    这正是 GOAL-040 自己写下的禁令形态：「**让重试变成隐式的无限重跑**（必须**有界**：
    计数落决策、超界点名）」——**该 GOAL 的全局禁令在它的新面上不成立**。
    (2) **为什么这属于连续性轴 + 深度轴**：连续性 = 「恢复不重复已发生的副作用」，
    而**重试**就是那条恢复路径 —— 无界重试 = 恢复路径上的副作用不收敛；深度 = 「轮数由
    结论驱动」，而失败面**没有结论**、由**上界**护栏约束 —— 上界可被绕过 ⇒ 护栏失真。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让「**声明的上界是真的**」成为可判定事实
    —— 认领但未落库时的失败重试**必须**去重（不产生第二个同序号 run）并按**已认领数**
    计入尝试数，用尽 ⇒ 点名失败停。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / D 组审批通道 / `G24-5` 运行时拦截器 / 部署面验证 / `R26-2/3/4/6` /
    把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让重试变成隐式的无限重跑**（正是本轮要消灭的形态）；**把「已认领」当成「已尝试」
    或反之**（两者必须能区分）。
    (6) **改既有判据的申报纪律（承 GOAL-040 的 `fix_policy` 自证清单 + `MEM-20261009-210`）**：
    任何对**既有**判据文件的改动必须 ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；
    ③ 逐条比对谓词是否等同；④ 收窄受判面**显式申报**，**不得**称「强度不变」；
    ⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。driver = client-goal、owner = root-agent。
    (8) **边界（承继）**：GOAL-001…040 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…040 的未覆盖范围**原样保留**；
    GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` /
    GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 9（深度轴 + 连续性轴）落成**上界是真的**：① **勘察定稿** —— 实测
    「认领后未落库 ⇒ 失败重试不去重 ⇒ 上界可被无限绕过」的现状（读数逐条：连推 5 次全部
    `RETRY_FAILED_RUN`、`attempts=1/2` 不动、`STOP_RUN_FAILED` 永不出现），并定位可复用的缝
    （`_claimed_but_missing` / 决策 count 面 / `_Evaluation`）（EC-01）→ ② **去重与计数** ——
    失败重试面补上「已认领但未落库」的**可判定**处置：产生**新的**决策种类（或复用既有
    `DEDUP` 语义并**点名**失败面），**不产生**第二个同序号 run；尝试数按**已认领次数**计入
    （不是只数落库行）⇒ 用尽即点名失败停（EC-02）→ ③ **判定面接线** —— 三种形态
    **互不混用**：已落库的失败（按行数）/ 已认领未落库（去重、不重复起）/ 用尽（失败停
    并点名）（EC-03）→ ④ **真的被用上（含反证）** —— 实跑：反复「认领即崩」⇒ 判定**必须**
    收敛到失败停且点名上界；**不得**再出现「无限重试」形态（反证臂）；缺省（不声明重试）
    行为逐字不变（EC-04）→ ⑤ **自举收口**（复用既有机器）（EC-05）。
    **硬约束**：`max_attempts_per_index` 的**上界**在**任意崩溃模式**下都成立；
    判定与决策**互不混用**；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**）；m0 条数**仍是 23**；判词归档**进树**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 现状失真：`_failed_round` 的 `attempts` 只数
      **落库行**（`sum(1 for run in existing if run.program_index == last_index)`）⇒ 认领后
      未落库的那次**不计入** ⇒ 上界失效；(b) 分派路径：`RETRY_FAILED_RUN` 由 `_failed_round`
      产出、而 `_claimed_but_missing` 只在 `_after_hit`（结论面）里被调用 ⇒ 失败面**不经过**
      去重窗口；(c) **实测复现**：声明上界 `2`、连做 5 次「认领即崩」⇒ 全部
      `RETRY_FAILED_RUN` + `attempts=1/2` + `bounded=false`；(d) 可复用的缝：
      `ProgramDecisionKind`（枚举）/ `ProgramDecision`（append-only，`cited_run_id` 记认领）/ 
      `_claimed_but_missing`（现成的认领检测）/ `_Evaluation`（判定值对象）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal042_probe_unbounded_retry.py`
      ⇒ `unbounded_retry: true` / `bounded: false` / `cited_facts` 全为 `attempts=1/2`；
      `rg -n "只认 CONTINUE|is ProgramDecisionKind.CONTINUE" packages/application/run_orchestration/program_runner.py`。
    status: PASS
  - id: EC-02
    criterion: >-
      **去重与计数（上界成为真的）**：失败重试面按「**已认领次数**」计入尝试数
      （落库行 + 未落库的认领），并用尽即点名失败停；「已认领但未落库」**不产生**第二个
      同序号 run（`run_count` 不变）且**点名**这件事。判定种类 **互不混用**：
      新增的种类（或既有 `DEDUP` 在失败面的显式形态）与 `RETRY_FAILED_RUN` /
      `STOP_RUN_FAILED` 三者**可区分**（读面按 kind 即可分派，不靠措辞）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py -q` ⇒ 全绿 + 新用例
      （含「认领即崩 ⇒ 计数上升 ⇒ 用尽 ⇒ 失败停」逐条）。
    status: PASS
  - id: EC-03
    criterion: >-
      **判定面接线（三形态互不混用）**：① **已落库的失败**（按行数计尝试）；
      ② **已认领未落库**（去重：不重复起、点名认领的 run id 与已认领数）；
      ③ **用尽**（失败停 + 点名上界与已用数）。三者各自的 `cited_facts` 点名**不同事实**
      （不得出现「同一条判词覆盖两种形态」）。
    verify: >-
      同判据文件的形态分派用例（三形态 × 声明重试）逐条；反证臂：任一形态都**不得**
      产出无界的 `RETRY_FAILED_RUN` 序列。
    status: PASS
  - id: EC-04
    criterion: >-
      **真的被用上（+ 反证）**：(a) 实跑：反复「认领即崩」⇒ 判定**收敛**到
      `STOP_RUN_FAILED` 且判词点名「已认领未落库」与上界；(b) **反证臂**：任何形态下
      **不得**出现「同一序号被无限重试」（判定序列必须以失败停收口，且总认领数 ≤ 声明上界）；
      (c) 缺省（`max_attempts_per_index=1`，未声明重试）⇒ 行为 = 失败停，**逐字不变**；
      (d) 结论面与取消面**不受影响**（既有 `CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` /
      `STOP_CANCELLED` / `DEDUP` 逐字保持，由既有判据钉住）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿；
      `tests/e2e/test_program_idempotency_on_the_run_path.py`（既有，5 例）仍全绿。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      + `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树
      （**二进制写盘**、`CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、
      仓库 `.venv`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已在程序表
      序 9**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled` 如实登记
      + 原因 + `covered_by`；空集合 = 未取证；自我指涉边界明写并封闭）；⑥ 承继残余逐条在位；
      ⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal041_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；配套留档：两路判词 `sha256` 相同的归档、
      m0 日志、CI 台账逐提交行。
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
      **让重试变成隐式的无限重跑**（本轮要消灭的形态）；**把「已认领」当成「已尝试」
      或反之**（两者必须能区分）；**改动既有四态语义**（`CONTINUE` / `STOP_RULE` /
      `STOP_GUARDRAIL` / `DEDUP` 在**结论面**的语义逐字保持，由既有判据钉住）
    - >-
      **同轮同步面**：仅当本轮新增判定种类 / 计数口径**必需**时，允许对**既有**登记面做
      **加法 / 搬迁登记**（谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **改既有判据的申报纪律（承 `MEM-20261009-210`，逐条自证）**：任何对**既有**
      判据 / 测试文件的改动必须 ① **逐条枚举**改动面（哪一行 → 改成什么）；② 用
      `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；③ **逐条比对谓词是否
      等同**（不得只写「强度未降」—— 那是一句**需要自证**的断言）；④ **收窄受判面必须
      显式申报**（写明收窄了什么：轮次 / 取值域 / 观测宽度 —— 与理由），**不得**称
      「强度不变」；⑤ 属**同轮同步集之外**的形态 ⇒ 命中 `escalation_triggers`，
      在 RECHECK 里**如实登记**。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮不动放行面）
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
  - .cursor/plans/tasks/PLAN-20261009-361-goal-041-ec02-04-bounded-retry-on-the-crash-window.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261009-362-goal-041-ec02-04-bounded-retry-on-the-crash-window.md
memory_entries:
  - append-only-needs-a-tie-breaker-in-the-key
---

# GOAL-20261009-041 — 重试的有界性成为可判定事实

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 9**（依赖序 8 —— 已
> ACHIEVED）。**本行是 replan 的产物**，已在 MAINLINE「修订记录」留痕。
>
> **轴（逐条说明，避免含糊）**：程序表轴列登记为 **连续性**（该列只接受三分轴与已登记的
> 组合轴`深度+质量`/`广度`/`—`，由 `test_mainline_program_is_intact.py` 钉住 —— 本 GOAL
> **不**为贴标签去放宽那条判据）。本 GOAL **同时推进两条轴**：
> - **连续性**（主）：**恢复不重复已发生的副作用** —— 重试就是那条恢复路径，而它在崩溃窗口
>   下**不收敛**（实测：上界 `2` 可被无限绕过）。反面判据（宪章原文「只加了入口而没有可
>   恢复的实跑」）不适用：本 GOAL 有实跑判据（认领即崩连推 ⇒ 必须收敛）。
> - **深度**：**有停止规则** —— 失败面没有「结论」，由**上界护栏**约束；上界可绕过 ⇒
>   护栏失真。反面（宪章原文「固定轮数的流水线加长」）不适用：本 GOAL 不增加轮数，
>   只让**已声明的上界**成为真的。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 现状：`attempts` 只数落库行 + 失败面不经 `_claimed_but_missing` ⇒ 上界失效（实测：连推 5 次全 `RETRY_FAILED_RUN`、`attempts=1/2` 不动） | PASS |
| EC-02 | 去重与计数 | 按**已认领次数**计入尝试；已认领未落库 ⇒ 不产生第二个 run 且点名 | PASS |
| EC-03 | 判定面接线 | 已落库失败 / 已认领未落库 / 用尽三形态**互不混用** | PASS |
| EC-04 | 真的被用上 | 实跑「认领即崩」⇒ 收敛到失败停且点名上界；**反证**：无界重试不再出现；缺省逐字不变 | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得让重试变成**隐式无限重跑**；
不得把**没有结论**当成**结论说停**（承 GOAL-040）；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：声明的重试上界**不成立**（本轮要消灭的形态）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 尝试数只数**落库行** | `program_runner.py::_failed_round` | `attempts = sum(1 for run in existing if (run.program_index or 0) == last_index)` —— **认领后未落库的那次不计入** |
| 1.2 | 去重窗口只服务**结论面** | `program_runner.py::_claimed_but_missing` | `if decision.kind is ProgramDecisionKind.CONTINUE` —— `RETRY_FAILED_RUN` 不被认 |
| 1.3 | 失败面不经过 `_after_hit` | `program_runner.py::_evaluate` → `_non_success_terminal` → `_failed_round` | 分派在结论面**之前** ⇒ `_claimed_but_missing`（只被 `_after_hit` 调用）够不到 |
| 1.4 | **实测复现** | `scratch/goal042_probe_unbounded_retry.py`（声明 `max_attempts_per_index=2`，连做 5 次「认领即崩」） | 判定序列 = `RETRY_FAILED_RUN` × 5；`cited_facts` 全部 `["state=FAILED", "attempts=1/2"]`；`bounded=false`；`unbounded_retry=true`；落库 run 始终只有 `[(1, FAILED)]` |
| 1.5 | 该形态**违反 GOAL-040 自己写下的禁令** | GOAL-040 `fix_policy.forbidden` 第 5 条 | 「**让重试变成隐式的无限重跑**（必须**有界**：计数落决策、超界点名）」—— 新面上不成立 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 判定种类是枚举（可扩） | `packages/domain/program.py::ProgramDecisionKind` | 九种（原六 + GOAL-040 的三） |
| 2.2 | 决策 append-only 且记**认领** | `packages/domain/program.py::ProgramDecision` | `cited_run_id` 在 `RETRY_FAILED_RUN` 上记的是**认领的 run id** ⇒ 认领数可从决策面数出来 |
| 2.3 | 认领检测现成 | `program_runner.py::_claimed_but_missing` | 形态可复用（按 `after_index` 逆序找最近一条带 `cited_run_id` 的同类决策） |
| 2.4 | 既有 `DEDUP` 判据与语义 | `tests/e2e/test_program_idempotency_on_the_run_path.py`（5 例）+ 驱动判据 | 结论面的崩溃窗口已判；**失败面没有对应判据** |
| 2.5 | 计数面读得到 | 程序读面 `decisions[].cited_facts` | `attempts=N/M` 是**决策原文** ⇒ 新口径同样可读 |

### 3. 判据面现状（改动的申报纪律：本轮新增为主）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 本轮**预判**改动面 | `program_runner.py` + 驱动判据 + 新增 e2e 判据文件 | 既有 e2e 三文件（GOAL-040 刚修过的）**不预期再动**；若必须动 ⇒ 走 `fix_policy` 自证清单 |
| 3.2 | 既有 e2e 三文件当前形态 | `tests/e2e/test_cross_run_{consumption,knowledge}*.py` / `test_program_advance_on_the_run_path.py` | 显式声明形态（成功面恰好两轮 / 失败面恰好一轮），21 passed |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 「已认领未落库」在失败面的处置 | **已定**：**去重**（不产生第二个同序号 run）+ 点名 + **计入**已用尝试数 |
| ② | 计数的口径 | **已定**：已用尝试数 = **落库行数 + 未落库的认领数**（从决策面数，不新增第二套存储） |
| ③ | 判定种类的落点 | **待 cycle 1 决定**：新增 `DEDUP` 的失败面显式形态（新的 kind）**或**复用 `DEDUP` 并让 `cited_facts` 点名失败面 —— 判据是「三形态读面可区分」 |
| ④ | 缺省（不声明重试）行为 | **已定**：逐字不变（失败停，**不**重跑）|
| ⑤ | 承接面 | **不动**（不需要新能力） |

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

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261009-041` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/application` / `tests/e2e` / `tests/domain`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**上界在任意崩溃模式下都成立**（认领未落库也计入）；**判定与决策互不
混用**；**改既有判据必须走自证清单**（`MEM-20261009-210`）；受判面不得是交集（承
`MEM-160`）；留档二进制写盘、判词归档进树；台账逐提交；新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED |
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-040 的 `R-1`（失败面的自动处置：任务级重试不动）/
`R-2`（**重试的退避策略不在本轮**）/ `R-3`（跨程序的失败传播）；GOAL-039 的 `Q-1`…`Q-3`；
GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门
的旧脚本；GOAL-019…040 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`S-1`…`S-3`）

- `S-1`（**退避仍不在本轮**，未覆盖；承 `R-2`）：本轮让**上界**在崩溃模式下也成立；
  **不**引入退避 / 抖动（那属调度面）。
- `S-2`（**跨序号 / 跨程序的认领去重不在本轮**，未覆盖；承 `R-3`）：去重按**序号**划界。
- `S-3`（**「谁是那个未落库的 run」不可能从 canonical 复原**，未覆盖）：认领只留下 id；
  本体为何没落库（进程崩溃 / 存储故障 / 启动面自身失败）**不区分** —— 本轮只保证
  **上界与去重**，不保证归因。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **重试上界**：**已收口** = 在**任意崩溃模式**下，同序号的尝试数不超过声明上界且超界点名；
  **未覆盖** = 退避、跨序号 / 跨程序的认领去重、未落库 run 的归因。
- **去重窗口**：**已收口** = 失败重试面与结论面**各自**有去重且判词可区分；
  **未覆盖** = 两面的统一化（本轮**不**重构为一个统一的认领模型）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `89e0d85`（GOAL-040 修复 cycle = 本 GOAL 建档所在批） | `37948976956` **M0 success**（8 job 全 success）+ `37948976453` **Push on main / CodeQL success**（3 分析全 success） | 同批含**序 9 建档**（程序表 + 五 EC + 事实层读数）；**实测取证**（`total_count=2`） |
| `7c9b35c`（cycle 1 = EC-02/03/04） | `37961452386` **M0 success**（8 job 全 success）+ `37961452060` **Push on main / CodeQL success**（3 分析全 success） | 崩溃窗口去重 + 计数口径 + **静默丢弃缺陷**（`MEM-20261009-211`）；本地 **5278 passed, 228 skipped**（m0 通体）、广面 3799 passed；**实测取证** |
| （本行所在提交：台账尾巴） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 台账尾巴：只改 `.cursor/**` 记录；其结论由**下一个 cycle 的台账**取证 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261009-361` | （见 CI 台账） | EC-02/03/04 全 PASS：**上界成为真的** —— ① 修前读数（`allowed=2`、连推 5 次全 `RETRY_FAILED_RUN`、`attempts=1/2` 不动、`bounded=false`）；② `_retry_face_state` 把「未落库的认领」与「被阻塞的推进」**计入**已用尝试数；③ 三形态分派（**用尽 → 去重 → 重试**，排序是判据的一部分：反过来永不收口）；④ **本轮新发现并修复同轴第二个缺陷** —— 决策自然键 `(program_id, after_index, decided_at)` 在同一时钟刻度下**静默顶掉**（实测：连录 10 条只留存 1 条）⇒ `_record` 归一为**程序内严格递增**；⑤ 四组上界实测**全部收敛且 ≤ 上界**、始终不产生第二个同序号 run；对照臂（正常落库）逐字不变；⑥ 两向反证 **R-1/R-2/R-3 全红** + 二进制复原 raw `sha256` 相同 + 归档进树；⑦ 规模门：`_failed_round` 60 行 ⇒ 拆 `_bounded_stop` / `_returning_claim_stop` | （见 CI 台账） | — | EC-05（自举收口）待做；残余 `S-1`…`S-3` 与 W-1…W-3 见 RECHECK | EC-05 自举收口 |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察 + **一处实测复现**（`scratch/goal042_probe_unbounded_retry.py`：连推 5 次全 `RETRY_FAILED_RUN`、`attempts=1/2` 不动、`bounded=false`）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 9** | （见 CI 台账） | — | 五条 EC 全 PENDING；判定种类落点（③）待 cycle 1 决定 | cycle 1（EC-02 去重与计数 + EC-03 接线） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | ACTIVE | **cycle 1（EC-02/03/04）收口**：**声明的重试上界成为真的** —— 失败重试面按「落库行数 + 未落库的认领数 + 被阻塞的推进数」计数，认领未落库 ⇒ `DEDUP_FAILED_RUN`（与结论面 `DEDUP` 可区分、不产生第二个同序号 run），判定序列**必然**在 ≤ 声明上界内收口到 `STOP_RUN_FAILED`（四组上界实测：`allowed=1/2/3/4` ⇒ 步数 1/2/3/4，全部收敛）；**新发现并修复同轴第二个缺陷**：决策自然键含挂钟 ⇒ 同一刻度内的多条决策被**静默顶掉**（紧循环连录 10 条只留存 1 条）⇒ 驱动侧 `decided_at` 归一为程序内严格递增（沉淀 `MEM-20261009-211`）。两向反证 3 条按压全红 + 二进制复原 raw `sha256` 一致；定向 37 passed、`tests/e2e` 319 passed。独立复检 `RECHECK-20261009-362`（PASS_WITH_WARNINGS）。EC-05 待收口。**不得**宣称安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-09 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 9**。只读勘察 + 一处**实测复现**：GOAL-040 声明「重试有界」（`max_attempts_per_index`），但尝试数只数**落库行**、且失败面**不经过** `_claimed_but_missing`（它只认 `CONTINUE`）⇒ **认领后未落库**时上界失效（实测：声明 `2`、连推 5 次全部 `RETRY_FAILED_RUN`、`attempts=1/2` 原样不动、`STOP_RUN_FAILED` 永不出现）—— 这正是 GOAL-040 自己写下的禁令形态（「让重试变成隐式的无限重跑」）。五条 EC 全 `PENDING`。**不做数量目标**；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
