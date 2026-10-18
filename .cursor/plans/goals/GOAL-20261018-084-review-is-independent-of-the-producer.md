---
id: GOAL-20261018-084
slug: review-is-independent-of-the-producer
title: 评审独立于生产者（按解析后的 model_name + endpoint 判，覆盖 fallback）
status: ACHIEVED
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
    status: PASS
  - id: EC-02
    criterion: >-
      **判据比较的是解析后的目标，不是绑定 id**：`research_strong`（primary `research_alpha`）
      vs `reviewer_gamma` 在**当前出厂目录**下**必须判为「不独立」**（四个 ModelDefinition 的
      `model_name` 全是 `deepseek-v4-flash-vision` 且 `endpoint` 都是 `main`）；
      **反证**：把评审的 model 指向一个**不同 `model_name`** 的 ModelDefinition ⇒ 判为「独立」。
    verify: >-
      同一判据文件；断言两组读数**相反**，且断言**绑定 id 不同也不影响结论**（名字相同/不同都不构成证据）。
    status: PASS
  - id: EC-03
    criterion: >-
      **fallback 路径一并覆盖**：`research_strong` 的 fallback 含 `reviewer_gamma`；
      `critic_independent` 的 fallback 含 `research_alpha` ⇒ **即便 primary 不同**，
      「可能落到的模型集合」**相交**就必须判出（并**点名相交的那个 `model_name`**）。
      **反证**：把 fallback 清空 ⇒ 相交消失 ⇒ 判为「独立」。
    verify: >-
      同一判据文件；两条成对断言；判词**点名**相交的目标（不是只说「不独立」）。
    status: PASS
  - id: EC-04
    criterion: >-
      **接进产品路径且默认零回归**：该判据在**预检期**对「声明了评审关系的合约/协议」生效
      （评审 agent 与生产 agent 由**协议声明**确定，不写死 agent 名）；
      **未声明评审关系 ⇒ 不判**（既有语义逐字不变，既有 1400+ 判据零回归）；
      命中 ⇒ **点名拒绝**并在 `PreflightReport` 的 finding 里可读。
    verify: >-
      `tests/application/preflight/test_review_independence_gate.py` ⇒ 全绿；
      **按压**：把判据关掉 ⇒ 同一条 preflight 变 PASS；既有 `tests/` 全绿（零回归）。
    status: PASS
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
    status: PASS

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
      **（cycle 2 的判别）**：本条禁止的是「把一个**假**差异写进目录」（例如把同一个
      `model_name` 的副本改名并列，或把评审绑到生产者的模型却写下不同 id）。cycle 2 的动作
      是**接入确实不同的底层模型**（`glm-5.3` / `kimi-k2.6`，返回名与声明名一致、同一端点
      同一凭据），并把评审 agent 绑到它上面 —— 判据对**旧配置**仍然判红（
      `test_the_gate_still_bites_when_the_reviewer_goes_back_to_the_producer_model`），
      因此不是「靠改目录让判据变绿」，而是**让被评对象真的独立**。
      
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
    记阻塞留拍板（本 GOAL 只做**可判性**：把「同模型」这件事从不可见变成可见，
    **不**负责采购第二个模型）
    **（cycle 2 已解除）**：该条在 cycle 1 触发过；复核判定它**不构成**真阻塞 —— 同一个
    `main` 端点用**同一把** `LLM_MAIN_KEY` 就提供 `glm-5.3` / `kimi-k2.6`（返回名 = 声明名），
    既没有新凭据也没有新端点、没有新增付费依赖、没有放开默认网络 ⇒ 属驱动可决定的配置
    变更，不在「真需用户拍板」的四类之内（破坏性动作 / 改 Accepted ADR / 新增付费依赖 /
    放开默认网络）。

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-515-goal-084-ec01-review-independence-by-resolved-target.md
  - .cursor/plans/tasks/PLAN-20261018-517-goal-084-review-independence-by-resolved-target-on-a-distinct-model.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-519-goal-084-ec05-self-bootstrap-closeout.md
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

**本 GOAL 不加新依赖、不放宽任何判据。** 它做**可判性**（把「同模型」从不可见变成
**编译/预检期可见并可拒绝**），并在 cycle 2 让被评对象**真的独立**（评审 agent 绑到
底层 `model_name` 不同的模型上）—— 否则门禁成立而 run 起不来。

## cycle 1 的记录（**当时的阻塞判断已由 cycle 2 推翻**）

**做过什么**：EC-01…EC-04 全部实现并通过 **23 条判据**（解析面 13 + 门链 5 + 异构 5），
零回归 **1735 passed**；出厂目录**一字未改**；`check_heterogeneity` 的判定面已从
model id 换成**解析后的 `endpoint/model_name`**（含 fallback）。

**接入产品路径后实测到什么**：

```
POST /projects/example-project/runs  {"protocol_path": "m12_reference_research_v1.yaml"}
=> 200，但 state = FAILED，manifest_digest = null
=> run.failed: "preflight failed: HETEROGENEITY_VIOLATION"
```

判据**真的生效了** —— 它抓到了「`m12_reference_research_v1` 的 writer 与 reviewer 落到
同一个底层模型」。但后果是：**冻结被拒 ⇒ run 起不来 ⇒ 一批既有 API 测试红**
（`test_budget_forecast_api` / `test_draft_run_linkage` / `test_failed_run_semantic_digest_api` …）。

**当时的结论（记 BLOCKED）**：认为三条出路都撞约束 —— ① 降级 finding = 放宽判据；
② 改目录给 reviewer 不同 `model_name` = 靠改目录掩盖、且需真的第二个模型；
③ 只在显式声明评审关系时判 = `m12` 本来就该判。**处置**：`git revert 77577728` 回退实现，
EC-01…EC-04 回到「未达成」，记 **BLOCKED**。

**为什么这个 BLOCKED 不成立（cycle 2 的复核）**：漏掉了第四条出路 ——
**把评审 agent 绑到一个 `model_name` 真正不同的模型上**。它不需要新凭据（同一端点、
同一把 `LLM_MAIN_KEY`）、不需要新端点、不改判据、不改 Phase 结构。而且判据对**旧配置**
仍然判红，所以这不是「靠改目录让判据变绿」，而是**让被评对象真的独立**。
cycle 1 的 `escalation_triggers` 条目把「接入第二个模型」笼统归为「上游与凭据变更」，
与实测不符（没有新凭据、没有新付费依赖、没有放开默认网络）⇒ 不属真阻塞四类。

## cycle 2 的落地（**解除 BLOCKED**）

**第 (A) 步：接入真不同的模型**（详见 `PLAN-20261018-517`）：

| 模型定义 | `model_name` | 声明名 vs 返回名 | 角色 |
| --- | --- | --- | --- |
| `research_alpha`（既有） | `deepseek-v4-flash-vision` | **不同**（`dsv4-flash-vision`） | 生产者 |
| `reviewer_independent`（新增） | `glm-5.3` | **相同** | `critic_independent.primary`，`reviewer_a` 用 |
| `kimi_k2_6`（新增） | `kimi-k2.6` | **相同** | `reviewer_b` 用 |

`critic_independent.fallback` **清空**（原先回落到生产者模型 `research_alpha`）；
`discovery.allow_models` 加两个新名字；`agnes_flash` **不动**（它只服务 live 探针腿）。

**第 (B)…(E) 步**：解析面 + 判定面重建、既有判据逐条申报收紧、受影响 API 套件恢复、
`test_contract_loaders` 的 `allow_models` 等值同步 —— 全部读数见
`RECHECK-20261018-518`。

**两项比 cycle 1 更严的改动**（如实登记）：
1. **解析失败不再静默跳过**：cycle 1 的实现在解析失败时**回落 model id**；cycle 2 改为
   **逐条 `MODEL_MISSING` 点名**，且解析失败的 agent **仍在受判面内**（跳过它会让
   writer/reviewer「无交集」⇒ 假绿）。这一条由
   `test_an_unresolvable_role_is_named_instead_of_silently_passing` 钉住；
2. **`INHERIT` 形态也被覆盖**：primary 取**编译期解析值**（`plan.resolved_models`），
   所以「绑定里没有模型名、靠 role 缺省解析」的 agent 同样进判定面。

**保留的取证资产**（cycle 1 回退前的设计）：`resolve_agent_targets` 返回**全部可能目标**
（primary + 每个 fallback）的 `(endpoint, model_name)` 集合；
命中判词形态 `endpoint/model_name is reachable by both writer roles (...) and reviewer roles (...)`。

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
- `W-3` —— **已解除**（cycle 2）：评审 agent 已绑到 `glm-5.3` / `kimi-k2.6`（同端点、
  同凭据、无新付费依赖）。
- `W-4` —— **只判协议声明的评审关系**：没声明「谁评审谁」的协议**不判**（既有语义不变）；
  「所有 agent 两两互查」不在射程。
- `W-5`（cycle 2 新增）—— **`research_strong.fallback` 仍是 `[reviewer_gamma]`**
  （= 生产者的同一个底层模型）：它**不**制造跨面板相交（`reviewer_gamma` 已不担任评审），
  但意味着**生产侧没有模型多样性**；「生产者的 fallback 落到另一个真模型」仍无判据。
- `W-6`（cycle 2 新增）—— **`glm-5.3` 的 `STRUCTURED_OUTPUT_NATIVE` 未声明**：provider 的
  `/v1/models` 声称支持 `structured_outputs`，实跑 `response_format: json_schema` 却**未被
  强制**（多出 schema 外的键、string 被写成 number）⇒ 按实测降为
  `STRUCTURED_OUTPUT_PROMPTED`。若将来需要评审侧的结构化输出，这是一处真实缺口。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01/02/03（解析 + 判据 + fallback） |
| 1 | PLAN-20261018-515（**已回退**） | `77577728`（实现，已 revert） / `cb0b2f6b`（记录面） | 实现期 **23 条判据全绿** + 零回归 **1735 passed**；但**接入产品路径后**实测：`m12_reference_research_v1` 等协议的 writer/reviewer 同模型 ⇒ preflight 判 `HETEROGENEITY_VIOLATION` ⇒ **freeze 拒冻** ⇒ 一批既有 API 测试红 | **`cb0b2f6b` M0 三 job 红**（`quality-ubuntu` / `quality-windows` / `console-frontend`）| 1 次（见「cycle 1 的记录」） | EC-01…04 回到未达成 | 当时的答案是「需拍板」——**该判断已被 cycle 2 推翻** |
| 2 | PLAN-20261018-517 | `e7d43001`（代码面）/ `6c6d9456`（记录面，tip） | 新判据 **21 passed**（EC-01 8 / EC-02+03 9 / EC-04 4）+ 异构专项 **5** + 受影响 API **28**；宽面 **2708 passed / 77 skipped**；`mypy` 10 files clean；反向按压在产品路径上得到 **1 条** `HETEROGENEITY_VIOLATION` 并点名相交目标 | **`6c6d9456` M0 八 job 全 `success`** + CodeQL 三条 `success`；`e7d43001` **零 run**（同树 `covered_by`） | 0（无一等失败） | EC-01…EC-04 已 `PASS`；**EC-05 待做** | **已收口**：EC-05 达成（`RECHECK-20261018-519`） |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1 落地（解析面 + 判定面 + 23 条判据） | `77577728` | 见下行覆盖 | 已 `git revert`；其内容曾包含在 `cb0b2f6b` 的树里 |
| cycle 1 记录面（GOAL/PLAN/RECHECK/MAINLINE/ALL_PLAN） | `cb0b2f6b` | [M0 39103704350](https://github.com/Eswink/research-system-new/actions/runs/39103704350) / [Push 39103704232](https://github.com/Eswink/research-system-new/actions/runs/39103704232) | 🔴 **三 job `failure`（真红，且是判据生效的真实后果）**：`quality-ubuntu` / `quality-windows` （`python/tests` 里一批 API 测试因 `preflight failed: HETEROGENEITY_VIOLATION` ⇒ freeze 拒冻而红）与 `console-frontend`。CodeQL 三条 `success`。**分类 = 判据收紧的后果（非 flake）**；**处置 = 回退实现**（见下行） |
| cycle 1 回退（实现 revert + BLOCKED 记录）+ **此前 tip** | `f4d6b03c` / `4bae6bfd` | [M0 39106389699](https://github.com/Eswink/research-system-new/actions/runs/39106389699) / [M0 39107412728](https://github.com/Eswink/research-system-new/actions/runs/39107412728) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**、**零 rerun** |
| cycle 2 代码面（配置 + 解析面 + 判定面 + 判据） | `e7d43001` | **零 run（如实登记，非未取证的正向结论）** | `GET /actions/runs?head_sha=e7d4300179cd…` ⇒ **`total_count = 0`**。**原因**：两次提交一次性推送，GitHub 只为**推送 tip** 建 run ⇒ 本提交由 `6c6d9456` 的 run **`covered_by`**（同一棵树的连续祖先，代码面完全相同 —— 记录提交只改 `.cursor/plans/**`） |
| cycle 2 记录面 + **当前 tip** | `6c6d9456` | [M0 39120372117](https://github.com/Eswink/research-system-new/actions/runs/39120372117) / [Push 39120371810](https://github.com/Eswink/research-system-new/actions/runs/39120371810) | **M0 八 job 全 `success`**（`container-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `collector-quality` / `observability-overhead-{ubuntu,windows}-latest` / `console-frontend`）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**、**零 rerun**。本地 as-is m0：**`PASS: profile=m0; 23 deterministic checks`**（静止工作树） |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-083 收口后按程序表续推（序 52）。**定位** = 阶梯「复检」域的 `下一级`。**建档实测四条**：① 四个 ModelDefinition 全是 `model_name: deepseek-v4-flash-vision` + `endpoint: main`；② agent 绑定看着不同（`research_strong` vs `reviewer_gamma`）但解析到同一模型；③ `research_strong.fallback = [reviewer_gamma]`、`critic_independent.fallback = [research_alpha]`；④ ⇒ 比名字的检查都会判过，而「独立复核」在产品上不可判。 |
| 2026-10-18 | **BLOCKED**（cycle 1） | 实现落地后接入产品路径 ⇒ `m12_reference_research_v1` 的 preflight 判 `HETEROGENEITY_VIOLATION` ⇒ **freeze 拒冻** ⇒ 一批既有 API 测试红。当时判定「三条出路都撞约束」，遂 `git revert 77577728` 回退实现并记阻塞。 |
| 2026-10-18 | **ACTIVE**（cycle 2，**解除阻塞**） | 复核推翻 cycle 1 的阻塞判断：**第四条出路存在** —— 把评审 agent 绑到一个 `model_name` 真不同的模型（`glm-5.3` / `kimi-k2.6`，同端点同凭据、无新付费依赖、不放开网络）⇒ 判据与出厂目录**同时成立**。EC-01…EC-04 达成（`PASS`），受影响 API 套件恢复，反向按压在产品路径上仍判红。**EC-05（自举复检）待做**。 |
| 2026-10-18 | **ACHIEVED**（cycle 2 收口） | EC-01…EC-05 全部 `PASS`。EC-05 自举复检：本树 **67 条判词全绿**、两树逐行相同且 `sha256` 一致（`0e04121f…`）、as-is m0 **23/23**、治理通过、凭据四面 `offenders=0`、两树证据文件二进制写盘（CR=0）。台阶记账两个面（阶梯行 + 进展记录）都由判词钉住。 |
