---
id: GOAL-20261018-084
slug: review-is-independent-of-the-producer
title: 评审独立于生产者（按解析后的 model_name + endpoint 判，覆盖 fallback）
status: BLOCKED
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**复检**域 `下一级是什么`
    逐字写的是「**评审独立于生产者**（现共用同一模型画像，非独立复算）」；同文件「程序表」序 52
    已登记本 GOAL（**建档实测**驱动）。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令
    （「每一次自动迭代都必须让科研能力越来越近」）。授权要点：
    (1) **本 GOAL 必须让阶梯前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py`
    机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `R-M1` / destructive 能力改 allow / 为凑数扩承接面 /
    宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）/ **不引入新的真实模型或中转站**
    （见 `forbidden`）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E`
    **不进 `.env`**）。

objective: >
    让「评审**独立于**生产者」成为**可判的产品事实**，而不是**声明上的名字差异**：
    在编译/预检期按**解析后的执行目标**（`model_name` + `endpoint`，**含 profile 的 fallback
    路径**）比较「评审 agent」与「被它评审的 agent」，若会落到**同一个底层模型**则**点名拒绝**
    或**点名声明**；判据成对：**同模型 ⇒ 判出（并点名两侧）** + **异模型 ⇒ 通过**。

exit_criteria:
  - id: EC-01
    criterion: >-
      **解析面成立**：给定一个 agent 的 `ModelBinding`（`EXPLICIT_MODEL` 或 `MODEL_PROFILE`，
      含 `fallback` 列表），能解析出**全部可能的执行目标**（`(endpoint_id, model_name)` 集合），
      而不是只取 primary。**确定性纯函数、零出网**；同输入同输出。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_review_independence.py -q`
      ⇒ 全绿；判据覆盖：EXPLICIT_MODEL / MODEL_PROFILE（primary + 多 fallback）/ 缺模型 /
      profile 不存在 ⇒ **点名**（不静默空集）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **判据比较的是解析后的目标，不是绑定 id**：`research_strong`（primary `research_alpha`）
      vs `reviewer_gamma` 在**当前出厂目录**下**必须判为「不独立」**（四个 ModelDefinition 的
      `model_name` 全是 `deepseek-v4-flash-vision` 且 `endpoint` 都是 `main`）；
      **反证**：把评审的 model 指向一个**不同 `model_name`** 的 ModelDefinition ⇒ 判为「独立」。
    verify: >-
      同一判据文件；断言两组读数**相反**，且断言**绑定 id 不同也不影响结论**（名字相同/不同都不构成证据）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **fallback 路径一并覆盖**：`research_strong` 的 fallback 含 `reviewer_gamma`；
      `critic_independent` 的 fallback 含 `research_alpha` ⇒ **即便 primary 不同**，
      「可能落到的模型集合」**相交**就必须判出（并**点名相交的那个 `model_name`**）。
      **反证**：把 fallback 清空 ⇒ 相交消失 ⇒ 判为「独立」。
    verify: >-
      同一判据文件；两条成对断言；判词**点名**相交的目标（不是只说「不独立」）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **接进产品路径且默认零回归**：该判据在**预检期**对「声明了评审关系的合约/协议」生效
      （评审 agent 与生产 agent 由**协议声明**确定，不写死 agent 名）；
      **未声明评审关系 ⇒ 不判**（既有语义逐字不变，既有 1400+ 判据零回归）；
      命中 ⇒ **点名拒绝**并在 `PreflightReport` 的 finding 里可读。
    verify: >-
      `tests/application/preflight/test_review_independence_gate.py` ⇒ 全绿；
      **按压**：把判据关掉 ⇒ 同一条 preflight 变 PASS；既有 `tests/` 全绿（零回归）。
    status: PENDING
    scope_note: >-
      **落点**：不新造门 —— `check_heterogeneity` 早已存在（`preflight/role_checks.py`），
      由 `check_team` → `run_preflight` → `compile_and_preflight` 调用。本轮把它的**判定面**
      从 model id 换成**解析后的 `endpoint/model_name`**（含 fallback）。
      **既有判据随之收紧一条**：`test_heterogeneity_allows_distinct_models` 原先用
      「同 `model_name` 的两个 id」当作「不同模型」⇒ 按新口径那是**同一个底层模型**。
      **处置 = 收紧该用例**（`model-2` 改成不同 `model_name`），并**新增一条反证用例**
      （`test_a_model_with_the_same_underlying_name_is_not_distinct`）钉住「id 不同 ≠ 独立」。
      这是**随产品语义收紧**，不是放宽：原用例考的行为在新语义下**不再成立**。

  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**、**静止工作树**）+ 治理绿 + 凭据审计 + CI 台账**逐提交**
      （`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**；
      自我指涉边界**明写并封闭**）+ 残余与未覆盖范围逐条。**★ 并含阶梯记账（两个面）**：
      阶梯「复检」行的 `依据 GOAL` **与**宪章 `进展记录` 各收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING

budget:
  max_cycles: 14
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - 改 `default_effect: DENY` / 放宽 §9 / 新增任何 allow
    - >-
      **用「绑定 id 不同」当独立性**：`research_strong` vs `reviewer_gamma` **看着不同**
      但是同一个 `model_name` —— 判据必须比较**解析后的目标**（`model_name` + `endpoint`），
      比较 agent 名 / 绑定 id / profile 名一律**不算**判过
    - >-
      **只比 primary 不比 fallback**：`research_strong` 的 fallback 含 `reviewer_gamma` ⇒
      只比 primary 会漏掉「可能回落到同一模型」这条路径
    - >-
      为让判据变绿而**改出厂目录**（`examples/config/models.yaml` / `model_profiles.yaml` /
      `agents.yaml`）以「制造差异」—— 那是掩盖而不是修复；若确需新模型，属新依赖/上游
      变更，走 `escalation_triggers`
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **需要接入一个新的真实模型/中转站才能让评审真正独立** —— 这属上游与凭据变更，
    记 BLOCKED 留拍板（本 GOAL 只做**可判性**：把「同模型」这件事从不可见变成可见，
    **不**负责采购第二个模型）

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-515-goal-084-ec01-review-independence-by-resolved-target.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-516-goal-084-ec01-review-independence-by-resolved-target.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让「评审**独立于**生产者」从**声明上的名字差异**变成**可判的解析事实** ——
阶梯「复检」域的 `下一级`。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：**独立复核**是「结论有来源支持」之外的第二根支柱；
  一个与生产者同模型的评审，其「通过」不构成独立证据）；
- **能力域** = **复检**（阶梯逐字：`评审独立于生产者`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **四个 ModelDefinition 全是同一个底层模型**：`examples/config/models.yaml` 里
   `agnes_flash` / `research_alpha` / `coding_beta` / `reviewer_gamma` ——
   **全部** `model_name: deepseek-v4-flash-vision` 且 `endpoint: main`。
2. **声明上的 agent→model 绑定看着不同**：`examples/config/agents.yaml` 里
   `research_director` = `MODEL_PROFILE research_strong`、`scientific_reviewer` =
   `EXPLICIT_MODEL reviewer_gamma` ⇒ **名字不同**，但 `research_strong.primary` 就是
   `research_alpha`，而 `research_alpha.model_name` 与 `reviewer_gamma.model_name` **相同**。
3. **fallback 让问题更深**：`research_strong.fallback = [reviewer_gamma]`；
   `critic_independent.primary = reviewer_gamma`、`fallback = [research_alpha]` ——
   一个**名字就叫「独立评审者」** 的 profile，可以回落到**生产者用的模型**。
4. ⇒ **后果**：任何「评审者与生产者不同」的检查，只要比的是 agent 名 / 绑定 id / profile 名，
   都会**判过**，而实际上 「独立复核」在产品上**不可判** —— 这正是阶梯那句话的意思。

**本 GOAL 不加新依赖、不接新模型、不放宽任何判据。** 它只做**可判性**：把「同模型」从
不可见变成**编译/预检期可见并可拒绝**。要不要真接第二个模型，属上游变更（见
`escalation_triggers`）。

## cycle 1 的取舍记录（**BLOCKED 的依据，逐条实测**）

**做过什么**：EC-01…EC-04 全部实现并通过 **23 条判据**（解析面 13 + 门链 5 + 异构 5），
零回归 **1735 passed**；出厂目录**一字未改**；实现期内 `check_heterogeneity` 的判定面已从
model id 换成**解析后的 `endpoint/model_name`**（含 fallback）。

**接入产品路径后实测到什么**（这是本 GOAL 的价值，也是它的终点）：

```
POST /projects/example-project/runs  {"protocol_path": "m12_reference_research_v1.yaml"}
=> 200，但 state = FAILED，manifest_digest = null
=> run.failed: "preflight failed: HETEROGENEITY_VIOLATION"
```

判据**真的生效了** —— 它抓到了「`m12_reference_research_v1` 的 writer 与 reviewer 落到
同一个底层模型」。但后果是：**冻结被拒 ⇒ run 起不来 ⇒ 一批既有 API 测试红**
（`test_budget_forecast_api` / `test_draft_run_linkage` / `test_failed_run_semantic_digest_api` …）。

**为什么这不是「修一下就能过」**（三条出路各自撞约束）：

| 出路 | 撞什么 |
| --- | --- |
| 把 finding 从 ERROR 降为 WARNING（可走 `accepted_policy_exceptions` 通道） | 那是**放宽既有判据**（`fix_policy.forbidden` 第一条），且等于说「不独立也可以跑」—— 与本 GOAL 的目标相反 |
| 改出厂目录，给 reviewer 一个不同 `model_name` | `forbidden` 明确禁止「靠改目录制造差异」；且需要**真的第二个模型/端点**（上游变更，`escalation_triggers`） |
| 只在「协议显式声明评审关系」时判（EC-04 已这么写） | 实测：`m12_reference_research_v1` **确实**有 `scientific_reviewer` 与 `research_writer` 两个 role（`review_panel_role` 已声明）⇒ 它本来就该判 |

⇒ **三条出路都撞到「需人工拍板」**：要么接受「现有出厂协议全部不可跑」，
要么采购第二个模型，要么承认「独立性只在报告里、不在门禁里」。这不是我能单方面决定的。

**处置**：`git revert 77577728` **回退实现**（保留本记录与取证），
`cb0b2f6b` 的记录面留在树里但**其 GOAL 正文以本节为准**；
EC-01…EC-04 回到「未达成」，本 GOAL 记 **BLOCKED**。

**保留的取证资产**（回退后不在树里，但可复现）：
- 解析面设计：`resolve_agent_targets` 返回**全部可能目标**（primary + 每个 fallback）
  的 `(endpoint, model_name)` 集合；
- 关键读数：出厂目录**四个** ModelDefinition 全同 `model_name`；
  `research_strong.fallback = [reviewer_gamma]`、`critic_independent.fallback = [research_alpha]`；
- 门链命中判词：`model ep/shared-name is shared between writer roles (...) and reviewer roles (...)`。

**解除条件（需拍板，逐条）**：

1. **接入第二个真实模型/端点**（唯一能让判据与出厂目录同时成立的路径）——
   给定 endpoint + model id + 凭据，本 GOAL 可原样重做（实现已在 `77577728`，revert 可还原）；
2. 或**明确接受「出厂协议整体不可跑」**，把本判据作为**新增的硬门**上线，
   并同轮把出厂协议逐个配到独立模型上（工作量在目录侧，不在代码侧）；
3. 或**降低本 GOAL 的目标**：只做「**报告**：解析后目标是否相交」而不阻断冻结
   （那需要**新增**一个与 `HETEROGENEITY_VIOLATION` 平行的**信息级** finding，
   **不**改既有 finding 的严重度 —— 但这就不是阶梯说的「独立」，只是「可见」）。

**我推荐 1**（唯一同时满足「判据成立」与「run 能跑」的路径），但采购属上游变更，需你定。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **解析纪律**：判据只认**解析后的 `(endpoint_id, model_name)`**，不认名字；
- **fallback 纪律**：必须看**全部可能目标**（primary + fallback），只看 primary 不算判过；
- **目录纪律**：**不许**改 `examples/config/**` 来制造差异（那是掩盖）；
- **凭据纪律**：每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**（前一 GOAL 实测过这个形态），如实登记 + `covered_by`。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立（两个面）**。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 残余与未覆盖范围（逐条明写）

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办。
- `W-2` —— **本 GOAL 只判「模型是否同一个」**，不判「评审是否真的独立判断」：同一模型也可以
  给出不同结论（温度/上下文不同），不同模型也可能同质化。**射程边界**：可判的只有
  「底层模型 + endpoint 是否相同」这一格。
- `W-3` —— **不采购第二个模型**：本轮把问题**判出来**（当前出厂目录判「不独立」），
  真正实现独立需要**新 endpoint/model**（上游与凭据变更，需拍板）。
- `W-4` —— **只判协议声明的评审关系**：没声明「谁评审谁」的协议**不判**（既有语义不变）；
  「所有 agent 两两互查」不在射程。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- **接入第二个真实模型/中转站**（靠它才能真正独立）—— 属上游变更，需拍板；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **采购/接入第二个真实模型或中转站** —— 需人工拍板；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01/02/03（解析 + 判据 + fallback） |
| 1 | PLAN-20261018-515（**已回退**） | `77577728`（实现，已 revert） / `cb0b2f6b`（记录面） | 实现期 **23 条判据全绿** + 零回归 **1735 passed**；但**接入产品路径后**实测：`m12_reference_research_v1` 等协议的 writer/reviewer 同模型 ⇒ preflight 判 `HETEROGENEITY_VIOLATION` ⇒ **freeze 拒冻** ⇒ 一批既有 API 测试红 | **`cb0b2f6b` M0 三 job 红**（`quality-ubuntu` / `quality-windows` / `console-frontend`）| 1 次（见「cycle 1 的取舍记录」） | **EC-01…04 回到 PENDING**（实现已回退）；**本 GOAL BLOCKED** | 需拍板：见 blocked_reason |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1 落地（解析面 + 判定面 + 23 条判据） | `77577728` | 见下行覆盖 | 已 `git revert`；其内容曾包含在 `cb0b2f6b` 的树里 |
| cycle 1 记录面（GOAL/PLAN/RECHECK/MAINLINE/ALL_PLAN） | `cb0b2f6b` | [M0 39103704350](https://github.com/Eswink/research-system-new/actions/runs/39103704350) / [Push 39103704232](https://github.com/Eswink/research-system-new/actions/runs/39103704232) | 🔴 **三 job `failure`（真红，且是判据生效的真实后果）**：`quality-ubuntu` / `quality-windows` （`python/tests` 里一批 API 测试因 `preflight failed: HETEROGENEITY_VIOLATION` ⇒ freeze 拒冻而红）与 `console-frontend`。CodeQL 三条 `success`。**分类 = 判据收紧的后果（非 flake）**；**处置 = 回退实现**（见下行） |
| cycle 1 回退（实现 revert + BLOCKED 记录）+ **当前 tip** | `f4d6b03c`（**tip**） | [M0 39106389699](https://github.com/Eswink/research-system-new/actions/runs/39106389699) / [Push 39106389552](https://github.com/Eswink/research-system-new/actions/runs/39106389552) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**、**零 rerun**。本地 as-is m0：**`PASS: profile=m0; 23 deterministic checks`**（回退后，静止工作树） |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-083 收口后按程序表续推（序 52）。**定位** = 阶梯「复检」域的 `下一级`。**建档实测四条**：① 四个 ModelDefinition 全是 `model_name: deepseek-v4-flash-vision` + `endpoint: main`；② agent 绑定看着不同（`research_strong` vs `reviewer_gamma`）但解析到同一模型；③ `research_strong.fallback = [reviewer_gamma]`、`critic_independent.fallback = [research_alpha]`；④ ⇒ 比名字的检查都会判过，而「独立复核」在产品上不可判。 |
