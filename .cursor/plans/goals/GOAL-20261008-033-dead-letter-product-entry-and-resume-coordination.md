---
id: GOAL-20261008-033
slug: dead-letter-product-entry-and-resume-coordination
title: 死信恢复的产品入口 + 与 run 续跑的自动协同 + 续跑覆盖矩阵机械化 —— 把「引擎会做」推进到「产品能走通且有判据」
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**按
    `.cursor/plans/goals/MAINLINE.md` 程序表序 1 推进连续性轴**，并授权本驱动自动化
    循环推进、**收口后立即开下一个 GOAL，不停下来等指令**。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含放宽某条 allow、改产品语义、新增 ADR），**不等于**可以放宽**判据、门禁、阈值或
    断言** —— 本轮无例外。
    (1) **本 GOAL 的三项授权开工**（MAINLINE 程序表序 1 的「一句话目标」逐条落地）：
    (i) **死信恢复的产品入口** —— GOAL-032 EC-01 已让 `WorkflowEngine.requeue` 在引擎面
    成立（ADR-0033），但**产品面没有入口**（实测：`services/` 内 `requeue` / `DEAD_LETTER`
    零命中、无 HTTP 路由、`engine.requeue` 只有测试调用方）⇒ 本轮把人工恢复接成**产品路径**；
    (ii) **与 run 续跑的自动协同** —— `RetryDispatchScheduler` 只扫 `PAUSED` runs + due
    retries；死信恢复后 run 是否需要 resume 的**自动协同不存在**（GOAL-032 登记为下一轮
    输入）⇒ 本轮实现或**如实登记确切边界**（不得为凑数硬做）；
    (iii) **续跑覆盖矩阵机械化** —— GOAL-032 EC-03 的八行矩阵里「不处理」清单是
    **代表而非穷尽**（`W-4`）⇒ 本轮把受判面做成**声明集穷尽枚举**（不得是交集 / 过滤 /
    空集恒真）。
    (2) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证（标签保持「未验证」）/ `R26-2` `R26-3` `R26-4` `R26-6`（条件不满足，逐条保持）/
    把 destructive 能力从 `require_approval` 改 allow / **为凑数扩承接面** /
    **放宽任何既有判据的断言** / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；**宣称项目安全**
    （`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；口径只能是
    at-least-once + idempotency + deduplication）；**静默改 `terminal()` 语义而不留 ADR**。
    (4) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）；
    默认姿态不变（默认 runtime 保持 **Fake**、默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (5) **边界（承继）**：GOAL-001…032 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…032 的未覆盖范围**原样保留**；
    GOAL-032 的残余 `W-1`…`W-8` / `R26-1` 终态 / `R26-5` 更正**原样保留**，本轮**只追加**。
    (6) **driver** = client-goal、**owner** = root-agent；另一驱动持有未收口 ACTIVE cycle 时等待。
objective: >-
    把 MAINLINE 程序表序 1（**连续性**轴）推进到「**产品能走通且有判据**」：① **死信恢复
    有产品入口** —— `DEAD_LETTER` 任务可经**控制面 HTTP 写面**被人工显式恢复（不是只有
    引擎 API），幂等（控制面 `Idempotency-Key` + 引擎侧点名拒绝两层）、对不可恢复输入
    **点名拒绝**（结构化 409/404 + 消息含任务 id 与原因）、两向反证、实跑留档，且
    **认证面自动覆盖**（写面分类是唯一保护面定义，新端点不得漏网 → 由既有对抗性判据的
    枚举面自动判，其告警线按判据自己的提示更新）（EC-01）→ ② **死信恢复与 run 续跑的
    协同有判据** —— 逐条实测恢复后 run 的三个可观察面（run 状态 / 派发方 / 任务面），
    按实测决定「实现自动协同」或「如实登记确切边界 + 点名理由」，**不得**把未实现写成
    已实现（EC-02）→ ③ **续跑覆盖矩阵机械化** —— 把 `rebuild_and_resume` 的「处理 /
    不处理」从**代表样本**推进到**声明集穷尽枚举**：受判面是声明集本身（承 `MEM-160`
    的反面教训：不得是交集 / 过滤 / 空集恒真），每条要么有实测判据、要么在登记表里
    逐条点名理由（EC-03）→ ④ **自举收口** —— 验证器进树 + 两树复检 + 判词归档进树 +
    as-is m0 23/23（在**全部记录写入之后**）+ 治理绿 + CI 台账逐提交（EC-04）。
    **硬约束**：先复核再依赖（本 GOAL 的起点事实全部待复核）；受判面**不得**是交集 /
    过滤；真被使用才算数（断言调用证据 + 下游消费证据，不得只断言「注册了」/「返回成功」）；
    点名失败而非静默；留档**二进制写盘**、判词归档**进树**；m0 条数**仍是 23**；
    **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **死信恢复的产品入口（连续性轴主干）**。
      (a) **勘察前置（实测）**：`WorkflowEngine.requeue` 的**产品调用方清单**（逐文件读数：
      产品面 / 测试面各自多少处）、控制面写面**现有**的人工干预入口形态（`POST /runs/{id}/resume`
      / `cancel` 的 DTO 与错误码约定）、以及新端点会打红的**已知判据**（逐条实测枚举）；
      (b) **实现**：`DEAD_LETTER` 任务可经控制面 HTTP 被**人工显式恢复**。端点必须：
      走既有 `WorkflowEngine.requeue` Port（**不建第二套恢复逻辑**）；对三类不可恢复输入
      **点名拒绝**（不存在 ⇒ 404；状态不符（含「已恢复」）⇒ 409；写面未装配 ⇒ 503），
      消息含任务 id 与原因；**不改** `terminal()` 语义、**不动** `fence_seq` / 尝试预算
      （沿用 ADR-0033，必要时只**追加** ADR 不静默改）；
      (c) **幂等两层**：控制面 `Idempotency-Key`（同 key 重放不第二次触达引擎）+ 引擎侧
      「第二次恢复被点名拒绝且**事件计数不增**」（计数取样必须在第二次恢复**之前**——
      承 GOAL-026 EC-03 的假绿教训）；
      (d) **认证面自动覆盖**：新端点必须落在写面分类（`_MUTATING_METHODS`）造成的保护面内
      —— 由既有对抗性判据 `tests/api/test_write_face_cannot_be_bypassed.py` 的**代码枚举面**
      自动判（该文件自己声明：树新增写面端点时**不需要改它**就能覆盖）；其 `_MEASURED_MUTATING_COUNT`
      告警线按该文件**自己的提示**更新（**纯同步**，断言强度不得降）；
      (e) **判据（新）**：端点级三态（成功 ⇒ 任务面真的回 `QUEUED` 且可被再交付；三类拒绝
      逐条判词；幂等重放）；**调用证据**（引擎 `requeue` 真的被触达，不是只返回 200）；
      (f) **两向反证**：① 摘掉端点 ⇒ 判红（任务仍死信）；② 把点名拒绝改成静默 200 ⇒ 判红
      （状态不符的输入被放过）；两条各自独立、逐字节复原（`FINAL_MATCHES_BASELINE True`）；
      (g) **实跑留档**：造一条真死信 → HTTP 恢复 → 跑到终态，全程留档（含恢复前后状态转移逐条）。
      **同轮同步集（建档实测标定，逐条登记，且**仅限**这些）**：① `docs/api/CONTROL_PLANE_API.md`
      的写面清单（**输入登记面**）；② OpenAPI 快照 `docs/api/openapi.m13.json`（由
      `tools/gen_openapi.py` 重新生成，**不是手改**）+ `tests/contracts/test_openapi_snapshot.py`
      的路径断言（**追加**一行，纯扩张）；③ 写面告警线计数（见 (d)，纯同步）；
      ④ 前端类型/客户端（若 `types.ts` 由快照生成则同步生成物；若为手写则**如实登记**不动）。
      **上述以外的任何既有判据改动 ⇒ BLOCKED**；每条同步都要在记录内给出 before/after 与
      「强度未降」自证。
      **判据**：端点 + 三态 + 幂等两层 + 认证面自动覆盖 + 调用证据 + 两向反证 + 实跑 + 同步集自证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/adapters
      tests/domain -q` ⇒ 全绿；新增判据文件（端点三态 / 幂等 / 点名拒绝 / 调用证据 / 两向反证）
      全绿；`tests/api/test_write_face_cannot_be_bypassed.py` 全绿（新端点自动入枚举面）；
      配套留档：产品调用方清单读数、端点契约逐条、三类拒绝判词逐字、两向反证判红原文、
      实跑状态转移序列、同步集四条 before/after 与「强度未降」自证。
    status: PENDING
  - id: EC-02
    criterion: >-
      **死信恢复 ↔ run 续跑的协同（实现或如实登记，二者必居其一且有判据）**。
      (a) **实测三面（不得推定）**：死信恢复后，**run 状态**（仍在终态？）/ **派发方**
      （`RetryDispatchScheduler` 会不会碰它？它只扫 `PAUSED`）/ **任务面**（回到可交付面
      之后由谁交付：`claim_next` 的 `Kind`/状态过滤是否够得着）分别是什么读数 —— 三条
      各自给出实测命令与结果；
      (b) **决策（按实测，二选一）**：
      **路径 A（实现自动协同）** —— 若实测表明「恢复后无任何自动交付方」**且**实现它
      不超出本 GOAL 的 sync 集，则在 `RetryDispatchScheduler` 的既有 pass 内扩展
      （**不建第二套调度器**）：恢复后 run 的后续由既有重建续跑链承担，且**必须**满足
      ① 跳过可观测（承 GOAL-031 的判据：跳过要进 `run.completed` 的 `skipped`，不静默
      不失败）；② 不重复已完成的副作用（deliveries 计数为判据）；③ 反证判红。
      **路径 B（如实登记边界）** —— 若实测表明协同需要新机制（例如自动恢复的审批门 /
      run 级状态机变更 / 超预算），则**只登记**：写下确切边界 + 点名理由 + 复现命令，
      并把它逐条列为下一轮输入（**不得**为了收口而做半个实现）。
      **选哪条由实测决定，不预设**；两条都要给出「为什么不是另一条」的判据。
      (c) **判据（新）**：无论 A/B，都要有**可复核的判据文件**把 (a) 的三面读数钉住
      （B 路径下判的是「边界在哪」，形态＝「这些情形逐条不处理且点名理由」）；
      (d) **反证**：把所选路径的机制改坏 ⇒ 判红（A：跳过变静默 / 副作用重复；
      B：把「不处理」写成「处理」⇒ 判红）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/application
      tests/adapters/sqlite -q` ⇒ 全绿；新增判据文件（三面读数 / 所选路径的行为 / 反证）
      全绿；配套留档：三面实测逐条读数、A/B 选择理由与「为什么不是另一条」、
      反证判红原文。
    status: PENDING
  - id: EC-03
    criterion: >-
      **续跑覆盖矩阵机械化（受判面 = 声明集，不得是交集 / 过滤 / 空集恒真）**。
      (a) **受判面穷尽**：`services/api/run_resume.py::rebuild_and_resume` 的**处理面**与
      **不处理面**逐条枚举成**声明集**（每条＝一个可观察情形），且声明集**恰好等于**实测
      覆盖的情形集合（不多不少）；「补充」承 GOAL-032 `W-4`（当时的不处理清单是**代表
      而非穷尽**）；
      (b) **每条三选一且不得含糊**：声明集里每一条必须**要么**有可复核判据（点名文件 +
      用例名）、**要么**在登记表里带**非空理由**、**要么**判红；空理由 / 幽灵条目
      （登记了但情形不存在）/ 未分类情形 ⇒ 各自判红（承 GOAL-029 EC-02 的判据形态）；
      (c) **反掩蔽**：受判面**不得**写成 `declared ∩ implemented` 这类交集（那会让
      「声明了但没判据」在构造上不可能被报出 —— `MEM-20260928-160` / `MEM-20261005-187`）；
      本条由判据自身断言（受判面 == 声明集，且声明集规模有下界）；
      (d) **反证两向**：① 删掉一条判据的引用 ⇒ 判红（该条落「无判据无理由」）；② 往声明集
      加一条不存在的情形 ⇒ 判红（幽灵条目）；
      (e) **同步集**：本 EC 只**新增**判据与登记表；若需改 `docs/` 的描述，属文档同源
      （**不得**改既有判据断言）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling tests/e2e
      tests/application/run_orchestration -q` ⇒ 全绿；新增覆盖矩阵判据全绿（含 (c) 的
      受判面自证与 (d) 的两向反证）；配套留档：声明集逐条（情形 / 判定 / 判据落点或理由）、
      声明集规模读数、两向反证判红原文。
    status: PENDING
  - id: EC-04
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools` +
      `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`tools/two_tree_recheck.py`，`--script-mode shared` +
      `--base-ref`）+ **判词归档进树**（`.cursor/plans/goals/evidence/`，**二进制写盘**、
      `CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（宪章程序面：本 GOAL 的 id 已
      替换 `GOAL-PLACEHOLDER`，且 MAINLINE 的进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；基础设施红按
      GOAL-031 的三条取证口径处理；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）；
      ⑥ 承继残余逐条在位（GOAL-032 的 `W-1`…`W-8` / `R26-*` 终态 / 未覆盖范围逐条保持 +
      理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal033_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <建档基线>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；`uv run --frozen --no-sync python -B
      .cursor/skills/governance-check/scripts/validate.py` ⇒ 绿；
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 全绿；配套留档：
      两路判词 sha256 相同的归档、m0 日志、CI 台账逐提交行。
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
      **为了凑数而声明没有实现的能力**；**把受判面写成交集 / 过滤 / 空集恒真**
      （承 `MEM-20260928-160` / `MEM-20261005-187`：`declared ∩ implemented`
      使「声明了但没实现 / 没判据」在构造上不可能被报出）；**只断言「注册了 / 返回成功」
      而不取调用与下游消费证据**；**为收口而在 EC-02 做半个实现**（A/B 必居其一）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据
      （`test_reproducibility_wording.py` / `test_delivery_semantics_wording.py` /
      `test_record_face_is_covered_by_the_gate.py`）、两树入口判据、规模门禁、
      `tests/application/preflight/**`、`tests/contracts/**`、`tests/adapters/**`、
      `tests/e2e/**` 既有文件）—— **新增**判据与新增文件不受此限
    - >-
      **本 GOAL 特有的同轮同步例外（逐条点名，EC-01 的必然结果，建档实测标定）**：仅限
      ① `docs/api/CONTROL_PLANE_API.md` 的写面清单；② `docs/api/openapi.m13.json`
      （**只能由 `tools/gen_openapi.py` 重新生成**）；③ `tests/contracts/test_openapi_snapshot.py`
      的**路径断言追加**（纯扩张）；④ `tests/api/test_write_face_cannot_be_bypassed.py` 的
      `_MEASURED_MUTATING_COUNT` 告警线（该文件**自己声明**这是它的用途：新增写面端点时
      提示复核，**纯同步、断言强度不得降**）。**上述四条以外的既有判据改动 ⇒ BLOCKED**。
    - >-
      **静默改 `terminal()` / 死信语义而不留 ADR**（ADR-0033 是既有决定；语义若需变更
      必须按 `ADR-0030` 既有方案或**新增 ADR** 走）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同步集四条以外**的既有判据断言
  - 死信自动协同（EC-02 路径 A）需要新审批通道或 run 级状态机变更
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261008-033 — 死信恢复的产品入口 + 与 run 续跑的自动协同 + 续跑覆盖矩阵机械化

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 1**（轴 = **连续性**）。
> 本文件是 GOAL-032 的直接后继：GOAL-032 让死信恢复在**引擎面**成立（ADR-0033），
> 本 GOAL 让它到**产品面**并补上协同与覆盖度两条判据。

## 目标与退出标准

四条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 死信恢复产品入口（主干） | 端点 + 三态 + 幂等两层 + 认证面自动覆盖 + 调用证据 + 两向反证 + 实跑 + 同步集自证 | PENDING |
| EC-02 | 死信恢复 ↔ run 续跑协同 | 三面实测 + 按实测选 A（实现）或 B（如实登记边界）+ 判据 + 反证 | PENDING |
| EC-03 | 续跑覆盖矩阵机械化 | 受判面 = 声明集（穷尽）+ 每条三选一 + 反掩蔽自证 + 两向反证 | PENDING |
| EC-04 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**宣称项目安全**
（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once +
idempotency + deduplication）；不得**静默改 `terminal()` 语义**（必须留 ADR）；
不得**为收口而做半个实现**（EC-02 的 A/B 必居其一）。观测隐私按 AGENTS.md §10；
默认 runtime 保持 Fake、默认 CI 离线（§11）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。凡与提示词起点表述
> 不符者，**以实测为准**（提示词已声明起点事实全部待复核）。主树零改动（只读勘察）。

### 1. 死信恢复**没有产品入口** —— 复核通过（承 GOAL-032 的登记，本轮实测确认）

复核命令与读数：

| # | 事实 | 命令 | 读数 |
| --- | --- | --- | --- |
| 1.1 | `services/` 内 `requeue` 零命中 | `rg -n "requeue" services/` | **零命中**（空输出） |
| 1.2 | `services/` 内 `DEAD_LETTER` 零命中 | `rg -n "DEAD_LETTER" services/` | **零命中**（空输出） |
| 1.3 | `engine.requeue` 的产品调用方 | `rg -n "\.requeue\(" --type py` | 产品面**零调用**（`experiment_queue` 的 `Entry.requeue` 是另一条语义：实验队列条目，非任务死信）；**全部调用方都在 `tests/`**（5 个文件 / 13 处） |
| 1.4 | 无 HTTP 路由 | `rg -n "requeue" services/api/routers/` | **零命中** ⇒ 人工恢复今天只能从**测试或 REPL** 走 |

**结论（与提示词起点一致）**：引擎面成立（GOAL-032 EC-01 / ADR-0033），**产品面无入口**。
这是本 GOAL EC-01 的靶子。

### 2. `requeue` 的既有实现形态（EC-01 必须复用，不得建第二套）

| # | 事实 | 落点 |
| --- | --- | --- |
| 2.1 | Port 声明 | `packages/application/ports/workflow_engine.py` 的 `requeue(task_id) -> str`（成功返回 `"restored"`） |
| 2.2 | 三实现 | SQLite `adapters/sqlite/requeue.py::requeue_task` + `SqliteWorkflowEngine.requeue`；PG `adapters/postgres/workflow_requeue.py` + `workflow_ops.requeue_impl`；Fake `adapters/fakes/workflow_engine.py::requeue` |
| 2.3 | 点名拒绝形态 | `InvalidInputError`，消息含任务 id 与实际状态：`unknown task: {id}` / `task {id} is in state {status}; only DEAD_LETTER can be requeued` |
| 2.4 | 唯一出边 | `(DEAD_LETTER, Transition.REQUEUE) -> QUEUED`（`packages/domain/task_state.py`），**新事件名**（不重用 `ENQUEUE`）；自动派发链**不**引用 `Transition.REQUEUE` |
| 2.5 | 既有判据面 | `tests/contracts/test_dead_letter_manual_recovery_contract.py`（3 处调用）/ `tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py`（6 处）/ `tests/e2e/test_dead_letter_recovery_full_loop.py`（真编排全环） |

### 3. 续跑覆盖度（EC-03 的起点，承 GOAL-032 EC-03）

| # | 事实 | 命令/落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 重建入口 | `services/api/run_resume.py::rebuild_and_resume`（152 行） | 处理：自包含重建 / 来源依赖重建 / 早退拒绝两类 / preflight 不过拒绝 / 语义漂移拒绝 |
| 3.2 | 覆盖度判据已在树 | `tests/e2e/test_research_continuity_coverage_matrix.py` | **八行矩阵**：处理面四项**引用既有判据**、边界四项**新增读数**（自动派发 / 租约过期 / 死信不处理 / 已成功不重跑） |
| 3.3 | **缺口（GOAL-032 `W-4` 登记）** | 该文件 docstring + `RECHECK-20261007-308` | 「不处理」清单是**代表而非穷尽** ⇒ 本 GOAL EC-03 把它做成**声明集穷尽枚举** |
| 3.4 | 反掩蔽警戒线 | `MEM-20260928-160` / `MEM-20261005-187` | 受判面**不得**是 `declared ∩ implemented`（交集让「声明了但没判据」构造上不可能被报出） |

### 4. 死信恢复 ↔ run 续跑的协同（EC-02 的起点）

| # | 事实 | 命令/落点 | 读数 |
| --- | --- | --- | --- |
| 4.1 | `RetryDispatchScheduler` 的扫描面 | `services/api/scheduler.py:320`（`_dispatch_due`） | **只扫 `run.state == PAUSED`** + `due_retry_task_ids(run_id)` ⇒ 终态 run **不在**扫描面 |
| 4.2 | 死信任务使 run 收敛到**终态** | `tests/e2e/test_dead_letter_recovery_full_loop.py` 的断言 | 真编排 `max_attempts=1` ⇒ run `FAILED`、任务 `DEAD_LETTER`（`assert first.state == FAILED`） |
| 4.3 | run 的 `FAILED` 是**真终态** | `packages/domain/run_state.py:78` 的 `terminal()` | `{SUCCEEDED, FAILED, CANCELLED}`；`tests/domain/test_state_machines.py` 钉住 `(FAILED, RESUME)` 非法 |
| 4.4 | 人工恢复**后**的交付方 | GOAL-032 EC-01 (f) 的实跑 | 恢复 ⇒ 任务回 `QUEUED` ⇒ **重建续跑**（`resume_rebuilt`）才把它跑到终态：**恢复本身不驱动 run** |

**推论（待 EC-02 实测确认，不预先写入结论）**：恢复把**任务**放回可交付面，但**run**
停在终态 ⇒ 「谁把 run 带回 RUNNING」是一个**独立**问题。GOAL-032 已登记「自动协同不存在」，
**EC-02 必须逐条实测量出三面读数**再选 A/B。

### 5. 新写面端点的**已知判据影响**（EC-01 的同步集标定）

| # | 判据 | 落点 | 影响形态 |
| --- | --- | --- | --- |
| 5.1 | 写面认证对抗性自检 | `tests/api/test_write_face_cannot_be_bypassed.py` | 枚举面**来自代码**（`app.openapi()`）⇒ 新端点**自动入面**，无需改文件；但 `_MEASURED_MUTATING_COUNT = 60` 会红 —— **该文件自己写明**这是它的用途（「若这是**有意**的增删，请复核保护面并更新本条告警线」）⇒ 纯同步 |
| 5.2 | OpenAPI 快照 | `tests/contracts/test_openapi_snapshot.py` | `test_openapi_snapshot_is_current` 会红 ⇒ 必须由 `tools/gen_openapi.py` **重新生成**；`test_openapi_contains_*` 是**路径断言**（追加一行属纯扩张） |
| 5.3 | 幂等中间件 | `services/api/middleware.py:36`（`_MUTATING_METHODS` / `_ANALYSIS_ACTIONS`） | 新端点是写类 POST ⇒ **必须**带 `Idempotency-Key`（除非尾段落在 `_ANALYSIS_ACTIONS`，**不得**为此扩展分析类词表） |
| 5.4 | 读面白名单 | `tests/observability/read_face_route_registry.py` | 只管**读面**（GET/HEAD）⇒ 写端点**不进**该面（无需分类） |
| 5.5 | 前端类型 | `apps/web/src/api/types.ts` | **实测：本仓没有 types.ts 生成器**（`tools/` 内无写 `types.ts` 的脚本；`gen_openapi.py` 只写 `docs/api/openapi.m13.json`）⇒ 前端类型是手写面，须按 EC-01 (g)④ 如实登记 |

### 6. 起点表述的出入（逐条）

- 提示词称承接面 **19/46**：本 GOAL **不依赖该数**（连续性轴不碰承接面）。本仓历史读数
  为 12/46 → 15/46（收口审计修正）→ 17/46（A 组 5/5）→ 18/46（GOAL-030/031）；
  **未在本轮重新实测**，如实登记为**待复核**（不得据此宣称任何结论）。
- 提示词称 `services/api/run_resume.py::rebuild_and_resume` **不处理死信任务（点名拒绝）**：
  **复核通过** —— 该模块本身不分支死信；死信在续跑链上被 `acquire_lease` 的终态守卫点名拒绝
  （判据 `tests/e2e/test_research_continuity_coverage_matrix.py` 的边界项三）。
- 提示词称「最深研究循环 = 2 轮」：**复核通过** —— `examples/protocols/two_round_research_loop_v1.yaml`
  两轮（`round1` → `round2` 派生），其注释明文写「**不声称**多轮迭代的上限/收敛」。
  **本 GOAL 不推进深度轴**（那是 MAINLINE 序 2）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 新端点走 `WorkflowEngine.requeue` Port（不建第二套恢复逻辑） | **已定**（承 ADR-0033；EC-01 (b)） |
| ② | 端点路径与错误码 | **cycle 1 derive 时定**（须与既有写面约定同形：404 / 409 / 503；路径形态由既有路由表推） |
| ③ | EC-02 路径 A（实现自动协同） vs B（如实登记） | **由实测决定**（EC-02 (a) 三面读数出来后定；**不得预设**） |
| ④ | 是否新增 ADR | **按需**：若只接端口、语义不变 ⇒ 复用 ADR-0033（**不改语义**）；若动 run 级语义 ⇒ 新增 ADR |
| ⑤ | 承接面扩容 | **不做**（MAINLINE：广度不是一条轴） |
| ⑥ | 读面认证 / 多租户 / RBAC / BOLA·BFLA / 部署面 / `G24-5` / `R26-2…4,6` | **保持不做**（承继口径） |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按「迭代日志」最后一行 + 工作树/远端实况
判定续点（与 `goals/README.md` 同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件（迭代日志 / 状态历史 / EC 状态），保证任意时刻崩溃后重入可续；
**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**（进入 cycle 时在迭代日志声明 owner 行）。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；写子 PLAN
  （`.cursor/plans/tasks/PLAN-…`，frontmatter 含 `parent_goal: GOAL-20261008-033` 并投影
  `ALL_PLAN`）；GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 记录面判据 → 全量门**；m0 按组、**独占**、仓库 `.venv`、
  `uv run --frozen --no-sync python -B`、**不接管道**（避免缓冲吞输出）；受影响的定向套件
  （`tests/domain` / `tests/adapters` / `tests/application` / `tests/api` / `tests/contracts` /
  `tests/e2e` / `tests/tooling`）；web 门按改动面（本 GOAL 预期零 web 源码改动 ——
  若动 `apps/web` 则补 tsc/eslint/unit/build）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main、
  不 force、不重写历史）→ 轮询该 `head_sha` 的**全部** run（脚本口径见「CI 台账」节）。
  **一个 cycle 攒成一次推送**（避免 `cancel-in-progress` 取消在飞 run）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤；
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **先复核再依赖**：起点事实全部待复核；出入以实测为准并写进「事实层结论」；
- **EC-02 不做半个实现**：A/B **必居其一**，按实测决定，并写明「为什么不是另一条」；
- **受判面不得是交集**（承 GOAL-029 掩蔽教训 / `MEM-160`）：新判据的受判面必须是**声明集**本身；
- **真被使用才算数**：断言调用证据 + 下游消费证据，不得只断言「注册了」/「返回成功」；
- **点名失败而非静默**：不可恢复输入 / 未装配面 / 缺口一律点名；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**（一个 cycle 一次）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；本地假绿（Linux 侧复验链接类判据）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP DNS 出网判据、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 组合跑顺序） | 按既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | validator / Mimosa / 记录面判据命中新增项 | 按各处置文档修或登记；**不得绕过**；不得宣称安全 |
| 资源阈值型偶发 | 例如 CI 上 RSS < 128MiB 类阈值判据偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类判据红 | **按生成器重新生成**（`tools/gen_openapi.py`），**不得手改** JSON |

## 终止与收口

- **ACHIEVED 前置**：四条 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure`（验证器进树 + 两树 + 归档 + m0 +
  治理 + 台账）并声明 `verify_paths` ≥ 2 路、**用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers`（含「需改同步集四条以外的既有判据断言」）或
  `budget.max_cycles` 触顶（20）；停下留人工决策，逐条写明触发项。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停止并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-032 的 `W-1`…`W-8`；`W31-1`…`W31-4`；
`W27-*` / `W10-12`；历史 `tools/` 目录仍有 73 条旧 lint 与无机器门的旧脚本
（`tools/` 不过四道门，只有**被点名脚本**有界受判）；GOAL-019…032 的未覆盖范围原样保留。

### `R26-*` 终态表（承 GOAL-032，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 已收口**（引擎面）；**本 GOAL 续作产品面** | EC-01 把引擎面接到产品面 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `PgOutboxRelay` 在树且生产启用；`consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 —— 属记录面结构 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**EC-02 的 A/B 未定**：路径选择依赖实测三面读数 ⇒ 建档时不预设。
- （建档时登记）**承接面读数待复核**：提示词的 19/46 未在本轮重新实测（见「事实层结论」第 6 条）。
- （建档时登记）**前端类型面**：本仓无 `types.ts` 生成器 ⇒ 新端点的前端类型若需要，属手写面
  （EC-01 (g)④ 要求如实登记）。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**（标签保持「未验证」）；**D 组审批通道未接通**（`external.publish` /
`package.install` / `git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；
`G24-5` 未做；**`R26-2/3/4/6` 未做**（条件不满足）；**应用级按偏移量物化的消费者仍不存在**
（`consumer_offsets` 只在文档）；**不得**据此宣称项目安全；**不得**宣称投递语义为
「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

### 本 GOAL 三项的「已收口 vs 未覆盖」分界（逐条明写）

- **EC-01 死信恢复产品入口**：**已收口** = 人工、单条、显式的**产品路径**（HTTP 写面 +
  幂等两层 + 点名拒绝 + 认证面自动覆盖）；**未覆盖** = 自动恢复（超时自动重生）、按 run
  批量恢复、恢复的审批门、前端 UI 面（若需要）。
- **EC-02 协同**：**已收口** = 三面实测 + 所选路径的判据；**未覆盖** = 未选路径所代表的那
  一族（A 则「自动协同」为未覆盖，B 则「自动协同」为下一轮输入）—— **逐条明写为哪一族**。
- **EC-03 覆盖矩阵**：**已收口** = 声明集穷尽枚举 + 每条三选一 + 反掩蔽自证；**未覆盖** =
  声明集之外的**未知情形**（枚举的完备性由声明集的定义域承担，本 GOAL 不声称「已穷尽
  宇宙」）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的
> 「回顾性台账」提交自身不产生可引用的 CI 结论（它进入 CI 时其结论尚无 —— 明写并以
> 「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （cycle 1 起逐条追加） | | |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（建档） | （本文件所在提交） | 只读勘察；`tests/tooling/test_mainline_program_is_intact.py` 新增并绿（8 passed）；`ruff` / `format` / `mypy` 绿 | PENDING | — | 四条 EC 全 PENDING；EC-02 的 A/B 待实测 | cycle 1 = EC-01（死信恢复产品入口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **建档（cycle 0）**：读 MAINLINE 宪章 + `goals/README.md` 格式契约 + GOAL-032 全文；只读勘察**复核了提示词的起点表述**（`requeue` 产品面零命中 / 无 HTTP 路由 / `RetryDispatchScheduler` 只扫 `PAUSED` / run `FAILED` 是真终态 / 两轮协议不声称上界）；标定了 EC-01 的**同轮同步集四条**（写面清单 / OpenAPI 生成物 / 快照路径断言追加 / 写面告警线计数）；四条 EC 全 `PENDING`。**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
