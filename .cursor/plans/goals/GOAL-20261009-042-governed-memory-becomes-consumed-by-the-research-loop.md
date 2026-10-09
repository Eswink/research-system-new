---
id: GOAL-20261009-042
slug: governed-memory-becomes-consumed-by-the-research-loop
title: 记忆的**被消费**成为可判定 —— 续 7 让时效**可读**，但**没有任何读路径消费它**：`memory.read` 未声明、运行链零引用、`validity_at` 只到 REST 读面 ⇒ 到期/待复核**不改变任何后续行为**
status: ACTIVE
created_at: 2026-10-09
updated_at: 2026-10-09
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-09 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 10**。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含**新增能力**、改产品语义），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：序 7（GOAL-20261008-039）让记忆的
    **适用范围与时效可读**（`scope` 落库、`review_after`/`expires_at` 声明式、到期/待复核
    经读面逐条披露，**不读挂钟** ⇒ 可复现）。但**没有任何读路径消费它**：
    (a) `examples/config/capabilities.yaml` 里 **`memory.read` 不存在**（只声明了
    `memory.write`）；(b) 研究循环的运行链（`phase_capabilities.py`）对 memory **零引用**；
    (c) `validity_at` 的调用面只有定义处与 REST 读面 ⇒ **到期 / 待复核不改变任何后续行为**。
    这正是 GOAL-039 自己写下的残余 `Q-1`（「只到**事实可读**不到**自动处置**」）。
    (2) **为什么这属于质量轴**：轴定义是「产出的**可判定性**：结论有来源支持 / 实验可复现 /
    覆盖充分，且与评审联动」。**记忆是结论的来源面之一** —— 让「这条记忆还在有效期吗 /
    该复核了吗」成为**真的**判据（而不是只印在读面上没人看），正是「来源支持」的那一环。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**一条记忆的时效状态真的影响研究循环的
    行为**（按声明：到期/待复核的记忆**如何被消费**必须是可判定的、可点名的、可复现的）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / D 组审批通道 / `G24-5` 运行时拦截器 / 部署面验证 / `R26-2/3/4/6` /
    把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：自动删除 / 自动降权 / 自动重建索引（`Q-1` 的另两条子面，
    §8 的这两条由既有 `deactivate` / `delete` 承担）；向量索引侧（`Q-3`）；
    跨项目 / 跨组织的 scope 语义（`Q-2`，多租户 deferred）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让「未声明时效」被读成「已到期」**（§8 原文口径：未声明 ⇒ 不猜）；
    **读挂钟**（时效判定必须由**调用方给时点** ⇒ 可复现）；**静默丢弃**（到期/待复核的记忆
    被跳过时必须**点名**，不得无声略过）。
    (6) **改既有判据的申报纪律（承 GOAL-040 的 `fix_policy` 自证清单 + `MEM-20261009-210`）**：
    任何对**既有**判据文件的改动必须 ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；
    ③ 逐条比对谓词是否等同；④ 收窄受判面**显式申报**，**不得**称「强度不变」；
    ⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (8) **边界（承继）**：GOAL-001…041 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…041 的未覆盖范围**原样保留**；
    GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` /
    GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**
    （**例外**：`Q-1` 的「自动处置」那一半正是本轮靶子 ⇒ 本轮**推进它**，其余原样）。
objective: >-
    让 MAINLINE 序 10（质量轴）落成**被消费**：① **勘察定稿** —— 实测「时效可读但零消费」
    的现状（三条读数：能力未声明 / 运行链零引用 / 调用面只有定义与 REST 读面），并定位可复用的
    缝（`validity_at` 纯函数 / 既有读能力 onboarding 的五件套 / `MemoryRecord.scope`）（EC-01）
    → ② **承接与判定** —— 新增一条**读**能力（`memory.read`：名称待 cycle 1 定，须与既有
    命名面同族）**声明 + 实现 + 策略放行**，其读面**按调用方给的时点**披露每条记忆的时效状态
    与**被跳过/被保留的理由**（`EXPIRED` / `REVIEW_DUE` / `None` 三态各自的处置可判定）（EC-02）
    → ③ **真的影响行为** —— 研究循环的**至少一条路径**按该读面**改变行为**：到期/待复核的记忆
    要么被跳过（**点名**）、要么被标注（**点名**），二者**互不混用**；未声明时效 ⇒ 逐字保持
    既有行为（EC-03）→ ④ **真的被用上（含反证）** —— 实跑：同一份记忆在**两个不同时点**
    （声明的 `expires_at` 两侧）⇒ 研究循环的行为**可区分**且判词点名时点与状态；反证臂：
    未声明时效的记忆**不得**被跳过、不得被误标（EC-04）→ ⑤ **自举收口**（复用既有机器）（EC-05）。
    **硬约束**：判定**不读挂钟**（时点由调用方给 ⇒ 可复现）；三态**互不混用**；
    未声明时效 ⇒ **不猜**（\|逐字保持既有行为）；跳过必须**点名**；
    m0 条数**仍是 23**；判词归档**进树**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 现状：`memory.read` **不在** `examples/config/capabilities.yaml`
      （只有 `memory.write`）；(b) 运行链零引用：`rg -c memory packages/application/run_orchestration/phase_capabilities.py`
      = 0；(c) `validity_at` 的调用面 = 定义处 + `services/api/routers/memory.py`（REST 读面）；
      (d) 可复用的缝：`validity_at`（纯函数、不读挂钟）+ 既有读能力 onboarding 的五件套
      （声明 / 实现 / 绑定 / 两组合根 / 一条只读 allow；承 GOAL-036 的同一手法）+
      `MemoryRecord.scope`（序 7 已落库）。(e) **本轮的落点选择**：把「消费」落在
      **运行链的能力读面**（研究循环真的调用它）—— 而不是再加一个 REST 端点。
    verify: >-
      `rg -n "memory.read" examples/config/capabilities.yaml`（零命中）；
      `rg -n "memory" packages/application/run_orchestration/phase_capabilities.py`（零命中）；
      `rg -ln "validity_at" packages services adapters --glob '*.py'` ⇒ 只有两处。
    status: PASS
  - id: EC-02
    criterion: >-
      **承接与判定（读能力 + 三态可判定）**：新增一条**读**能力（名称与既有命名面同族；
      五件套齐：目录声明 + provider 实现 + 工具/能力映射 + 两组合根接线 + **策略放行一条**
      —— 承 GOAL-036/037 的同一手法，**不含**任何破坏性面）。读面按**调用方给的时点**
      披露每条记忆的 `validity` 与**处置**（`EXPIRED` / `REVIEW_DUE` / `None` 三态各自的
      处置必须**互不混用**且**逐条点名**）；**不读挂钟**（同一记录 + 同一时点 ⇒ 判定相同）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters tests/api -q`
      ⇒ 全绿 + 新用例（三态逐条 + 不读挂钟的可复现判据）。
    status: PASS
  - id: EC-03
    criterion: >-
      **真的影响行为（研究循环的一条路径）**：研究循环的**至少一条**路径按该读面**改变行为** ——
      到期/待复核的记忆**被跳过或被标注**（两者**互不混用**、都**点名**理由与状态）；
      **未声明时效 ⇒ 逐字保持既有行为**（缺省不猜、不跳过）。判定**不读挂钟**：
      同一次运行在**同一时点**下的行为可复现。
    verify: >-
      该路径的判据用例（三态 × 声明面）逐条；缺省面与既有行为**逐字对拍**。
    status: PENDING
  - id: EC-04
    criterion: >-
      **真的被用上（+ 反证）**：(a) 实跑：**同一份**记忆在两个不同时点（`expires_at` 两侧）
      ⇒ 研究循环的行为**可区分**且判词**点名**时点与状态；(b) **反证臂①**：未声明时效的记忆
      **不得**被跳过、不得被误标（构造性反证）；(c) **反证臂②**：**不得**出现「跳过但不点名」
      （静默丢弃是禁令形态）；(d) 未放行 / 缺实现 ⇒ **点名**（承 GOAL-036/037 的同一纪律）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      + `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树
      （**二进制写盘**、`CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、
      仓库 `.venv`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已在程序表
      序 10**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled` 如实登记
      + 原因 + `covered_by`；空集合 = 未取证；自我指涉边界明写并封闭）；⑥ 承继残余逐条在位；
      ⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal042_closeout.py --root .
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
      **让「未声明时效」被读成「已到期」**（§8 口径：未声明 ⇒ **不猜**）；
      **读挂钟**（时点必须由调用方给 ⇒ 判定可复现）；**静默丢弃**（跳过必须**点名**）
    - >-
      **自动删除 / 自动降权 / 自动重建索引**（`Q-1` 的另两条子面，不在本轮）；
      **动向量索引**（`Q-3`）；**跨项目 / 跨组织的 scope 语义**（`Q-2`，多租户 deferred）
    - >-
      **把任何写 / 执行 / 审批类能力改成 allow**（本轮只放行**一条只读**能力，承 GOAL-036/037）；
      **改动既有读能力的 allow 语义**（逐字保持）
    - >-
      **同轮同步面**：仅当本轮新增能力 / 字段**必需**时，允许对**既有**登记面做
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
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
child_plans:
  - .cursor/plans/tasks/PLAN-20261009-365-goal-042-ec01-03-memory-consumption-on-the-run-path.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261009-042 — 记忆的被消费成为可判定

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 10**（依赖序 7、9 —— 均已
> ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 7/8/9 收口后到期），
> 已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 现状：时效**可读但零消费**（`memory.read` 未声明 / 运行链零引用 / `validity_at` 只到 REST 读面） | PASS |
| EC-02 | 承接与判定 | 新增一条**读**能力（五件套齐）+ 按**调用方给的时点**披露三态与处置（互不混用、不读挂钟） | PASS |
| EC-03 | 真的影响行为 | 研究循环**至少一条**路径按该读面改变行为（跳过 / 标注互不混用、都点名；未声明 ⇒ 逐字不变） | PENDING |
| EC-04 | 真的被用上 | 实跑：两个时点下行为可区分且点名；**反证**：未声明不得被跳过 / 不得静默丢弃 / 未放行点名 | PENDING |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得把**未声明时效**读成
**已到期**；不得**读挂钟**；不得**静默丢弃**；不得**宣称项目安全**（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：时效**可读**，但**没有任何读路径消费它**

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | **读能力不存在** | `rg -n "memory.read" examples/config/capabilities.yaml` | **零命中**（该文件只有 `memory.write`） |
| 1.2 | 研究循环**零引用** | `rg -n "memory" packages/application/run_orchestration/phase_capabilities.py` | **零命中** ⇒ 运行链不读 governed memory |
| 1.3 | 时效判定的调用面只有两处 | `rg -ln "validity_at" packages services adapters --glob '*.py'` | `packages/application/memory/validity.py`（定义）+ `services/api/routers/memory.py`（REST 读面披露） |
| 1.4 | **结论** | 1.1–1.3 合起来 | 到期 / 待复核**不改变任何后续行为** —— 正是 GOAL-039 的残余 `Q-1`（「只到**事实可读**不到**自动处置**」） |
| 1.5 | 序 7 的成果（可复用） | `packages/application/memory/validity.py` / `examples/config/capabilities.yaml` 的 `memory.write` 四 tier | `validity_at(record, now)` 是**纯函数**（**不读挂钟**；`None` = 未声明或未到 ⇒ 不猜）；`MemoryRecord.scope` 已落库 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 三态判定已就绪且可复现 | `packages/application/memory/validity.py::validity_at` | 纯函数；`EXPIRED` 优先于 `REVIEW_DUE`；未声明 ⇒ `None` |
| 2.2 | 读能力 onboarding 有现成手法 | GOAL-036（`review.read`）/ GOAL-037（`research_state.read`） | 五件套：目录声明 + provider 实现 + 工具/能力映射 + 两组合根接线 + **一条只读 allow** |
| 2.3 | 运行链调用声明是数据 | `packages/application/run_orchestration/phase_capabilities.py::RunChainCall` | 声明的调用（provider / tool / capability / `run_id_argument`）由组合根注入 |
| 2.4 | 门链与读面 | `packages/application/memory/gate.py` / `services/api/routers/memory.py` | 写入走 §8 五段；读面**只在给了时点时**填 `validity`（不给 ⇒ 不猜） |
| 2.5 | 记忆的候选面 | `MemoryRecord`（tier / scope / confidence / active / 时效三字段） | 处置的判定输入**全部在 canonical**（不需要新表） |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 既有读能力 allow 清单 | `examples/config/policy.yaml` | `workspace.read` / `artifact.read` / `evidence.read` / `research_state.read` / `review.read`（**逐字保持**） |
| 3.2 | 能力目录条目 | `examples/config/capabilities.yaml` | 46 条（GOAL-030 的读数口径）；本轮**只增一条读能力** |
| 3.3 | 承接面读数（口径 = provider 声明，distinct） | GOAL-031 收口读数 | 20/46；本轮**只增 1**（不为凑数扩容） |

### 4. 本轮**不**碰的面（逐条明写）

- 自动删除 / 自动降权 / 自动重建索引（`Q-1` 的另两条子面）；
- 向量索引（`Q-3`）；跨项目 / 跨组织的 scope 语义（`Q-2`，多租户 deferred）；
- 读面认证 / 部署面 / D 组审批通道 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 新读能力的**名称** | **待 cycle 1 定**：须与既有命名面同族（`*.read`），且**不与** `research_state.read` / `review.read` 混淆 |
| ② | 「消费」落在哪条路径 | **已定**：落在**运行链**（研究循环真的调用），**不**再加一个没人用的 REST 端点 |
| ③ | 三态与处置的对应 | **待 cycle 1 定**：`EXPIRED` / `REVIEW_DUE` / `None` 各自「跳过 / 标注 / 照用」——**互不混用**且**逐条点名**；判据是「读面按 kind 即可分派，不靠措辞」 |
| ④ | 缺省（未声明时效） | **已定**：**逐字保持**既有行为（不猜、不跳过） |
| ⑤ | 承接面 | 只增**一条只读**能力（五件套齐） |

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

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261009-042` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/application` / `tests/adapters` / `tests/api` / `tests/e2e`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**不读挂钟**（时点由调用方给）；三态**互不混用**；**跳过必须点名**；
未声明 ⇒ **不猜**；**改既有判据必须走自证清单**（`MEM-20261009-210`）；受判面不得是交集
（承 `MEM-160`）；留档二进制写盘、判词归档进树；台账逐提交；新记录落地后立刻跑治理。

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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-041 的 `S-1`（退避）/ `S-2`（跨序号 / 跨程序认领
去重）/ `S-3`（未落库 run 的归因）；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-2`（跨项目 /
跨组织 scope）/ `Q-3`（向量索引）（**`Q-1` 的「自动处置」那一半由本轮推进**，见下）；
GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门
的旧脚本；GOAL-019…041 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`T-1`…`T-3`）

- `T-1`（**只有消费面，没有处置面**，未覆盖；推进 `Q-1` 的一半）：本轮让到期/待复核的记忆
  **被消费且可判定**（跳过 / 标注 + 点名）；**不**自动删除 / 降权 / 重建索引。
- `T-2`（**跨项目 / 跨组织的 scope 语义不在本轮**，未覆盖；承 `Q-2`）：消费按**项目内**
  划界。
- `T-3`（**置信度阈值 / 冲突消解不在本轮**，未覆盖）：`confidence` / `contradictions`
  仍是面（序 7 的字段已落库），本轮**只按时效**消费。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **消费**：**已收口** = 时效状态按**调用方给的时点**可判定，且**至少一条**研究循环路径按它
  改变行为（跳过 / 标注 + 点名）；**未覆盖** = 自动处置（删除 / 降权 / 重建索引）。
- **判定**：**已收口** = 三态**互不混用** + 不读挂钟 + 未声明不猜；**未覆盖** = 置信度阈值
  与冲突消解（`T-3`）、跨项目 scope（`T-2`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `988f334`（replan，本 GOAL 建档所在批 = 本批 HEAD） | `37971731889` **M0 success**（8 job 全 success）+ `37971731185` **Push on main / CodeQL success**（3 分析全 success） | replan（序 10 新增）+ 建档（五 EC + 三条实测读数）；**实测取证**（按 `head_sha` 遍历该 SHA 全部 run） |
| `fe5d661`（本 GOAL 建档） | `37974448170` **M0 cancelled** —— `cancel-in-progress` 形态（**非失败**） | **实测取证**：该 run 于 `18:39:45Z` 终止，而 `ab436e2` 的 M0 run `37974796397` 于 `18:39:28Z` **更早创建** ⇒ 同 ref 同 workflow 的新 run 取消了排队中的旧 run（`.github/workflows/*.yml` 的 `concurrency.cancel-in-progress: true`，逐字复核）。其结论由 `ab436e2` 所在批覆盖（`covered_by 37974796397`）|
| `ab436e2`（cycle 1 子 PLAN 建档 = 本批 HEAD） | `37974796397` **M0 success**（8 job 全 success）+ `37974795395` **Push on main / CodeQL success**（3 分析全 success） | cycle 1 子 PLAN（`PLAN-20261009-365`）+ GOAL `child_plans` 投影 + `ALL_PLAN`；**实测取证** |
| `01606d2`（cycle 1 = EC-01/EC-02）：`memory.read` 承接 | `37989487322` **Push on main / CodeQL success**（3 分析全 success）；`37989487618` **M0 cancelled** —— `cancel-in-progress` 形态（**非失败**；**实测取证**：该 run 于 `21:06:04Z` 终止，而 `a0822ea` 的 M0 run 于 `21:05:56Z` 创建 ⇒ 同 ref 同 workflow 的新 run 取消了在飞的旧 run）⇒ `covered_by a0822ea 所在批` | 五件套 + 三态处置 + 15 判据 + 两向反证 + 改既有判据逐条申报；本地 **m0 23/23**（`PASS [` 24 / `FAILED [` 0 / 5295 passed, 228 skipped）；**M0 的 CI 结论待下一个 cycle 的台账取证** |
| （本行所在提交：台账尾巴） | **自身结论在本行写入时尚不存在**（自我指涉边界） | 台账尾巴：只改 `.cursor/**` 记录；其结论由**下一个 cycle 的台账**取证 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261009-365` | `01606d2`（实现）+ `a0822ea`（记录） | EC-01/EC-02 **PASS**：① 五件套齐（目录声明 + 新模块 `adapters/canonical/memory_read.py` + `read_surface` 描述子与映射 + 两组合根（SQLite `ports.memory_store` / PG `c["memory"]`）+ **一条只读 allow**）；② 读面按**调用方给的时点**（`now` **必填**）给三态与处置：`EXPIRED ⇒ SKIP` / `REVIEW_DUE ⇒ ANNOTATE` / `None ⇒ USE`（**不猜**，§8 口径），理由点名被引声明值 + `dispositions` 计数摘要；③ 三条硬约束判据打满（**不读挂钟** / 未声明不猜 / 缺依赖与非法时点逐条点名）；④ 新增判据 **15 passed**；⑤ 两向反证 **M-1/M-2/M-3 全红** + 二进制复原 raw `sha256` 一致 + 归档进树（314 B / `CR=0`）；⑥ 改既有判据**逐条申报**（三文件：`+3/-0`、`+6/-0`、`+14/-5`；删除行**仅** 5 处 `46` 字面，谓词形态一字未改）；广面 **2325 passed**；**全量 m0 23/23** （5295 passed, 228 skipped）| `37989487322` Push/CodeQL **success**；M0 **待终态取证** | **四道门抓到三处真红并已修**：mypy 6 个 `object` 不可索引（测试面）/ 两处函数超 50 行 （`read_provider.__init__` 借 `_SPILL_RATIONALE` 移出长 docstring；`canonical_read_register` 抽 `_canonical_reader` 工厂）/ 一处 import 序 | EC-03（研究循环按处置改变行为）与 EC-04（两时点实跑 + 反证）待做 | cycle 2（EC-03 + EC-04） |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **三条实测读数**（`memory.read` 未声明 / 运行链零引用 / `validity_at` 只到 REST 读面）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 10** | （见 CI 台账） | — | 五条 EC 全 PENDING；读能力名称与三态处置（①③）待 cycle 1 定 | cycle 1（EC-02 承接与判定 + EC-03 影响行为） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | ACTIVE | **cycle 1（EC-01/EC-02）收口**：**`memory.read` 承接落地** —— 该能力此前**从未声明**、研究循环零引用、`validity_at` 只到 REST 读面 ⇒ 记忆时效**不改变任何后续行为**；本轮补齐**消费面**：读面按调用方给的时点（**必填** ⇒ 不读挂钟）给每条记忆三态（`EXPIRED` / `REVIEW_DUE` / `None`）与**处置**（`SKIP` / `ANNOTATE` / `USE`，**互不混用**）并逐条点名理由；五件套齐（含**只增一条只读 allow**）。新增判据 15 passed；两向反证 3 条按压全红 + 二进制复原 raw `sha256` 一致；广面 2325 passed；**全量 m0 23/23**（`PASS [` 24 / `FAILED [` 0 / **5295 passed, 228 skipped**）。EC-03/EC-04 待做。**不得**宣称安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-09 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 10**（保留槽 → 本 GOAL）。只读勘察 + **三条实测读数**：`memory.read` **不在**能力目录（只有 `memory.write`）、研究循环的运行链对 memory **零引用**、`validity_at` 的调用面只有定义处与 REST 读面 ⇒ 序 7 让时效「**可读**」但**没有任何读路径消费它**（正是 GOAL-039 的残余 `Q-1`）。五条 EC 全 `PENDING`。**不做数量目标**（只增一条只读能力）；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
