---
id: GOAL-20261015-079
slug: experiment-derived-from-the-plan-with-arms
title: 实验由计划派生 + 多臂/对照（实验域 L2 → L3）
status: ACTIVE
created_at: 2026-10-15
updated_at: 2026-10-15
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」把**实验**域的
    `下一级是什么` 逐字写为「**实验由计划派生**（现为固定脚本），多臂 / 对照组」。
    承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动迭代都必须让科研
    能力越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 阶梯「实验」域 L2 → L3；它**必须让阶梯前进**
    （由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让**实验的参数由「计划」声明并按臂执行**：实验脚本能从**计划声明的参数**取值
    （而不是模块常量写死），一次 run 能跑**至少两个臂**（含对照），
    且「哪个样本属于哪个臂、两臂的指标差在哪」在既有读面上**可复核**。

exit_criteria:
  - id: EC-01
    criterion: >-
      **参数面存在且经声明传递**：实验参数由**声明**给出（计划/契约声明 → 执行请求 →
      容器环境），而**不是**脚本里的模块常量。判据成对：**声明什么就传什么**（逐键）、
      **脚本读得到**（环境里在场）、**未声明时脚本仍按既有缺省跑**（零回归）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_parameters.py -q`
      ⇒ 全绿；判据覆盖：逐键传递、环境白名单不被绕过、未声明 ⇒ 既有行为不变。
      **反证**：把某个声明键从传参面摘掉 ⇒ 判据红。
    status: PASS
  - id: EC-02
    criterion: >-
      **多臂/对照真跑**：一次 run 里**至少两个臂**（含对照）各执行一次实验，
      两臂的**参数不同、指标各自的落库值可读**，且臂归属**由声明决定**（不是按顺序猜）。
    verify: >-
      离线 e2e：`tests/e2e/test_two_arm_experiment_offline.py` ⇒ run `SUCCEEDED`；
      `GET /runs/{id}/experiments` 上**逐臂**给出实验记录与指标；
      两臂的 `environment_digest`（或等价的可判事实）**不同**；
      **反证**：只声明一个臂 ⇒ 「两臂」判据如实判否并点名。
    status: PENDING
  - id: EC-03
    criterion: >-
      **臂间可比**：读面能回答「**两臂的同一个指标差多少**」——不是「两条记录都在」
      而已；差异由**落库的指标值**算出（可复算），且缺指标时**点名**而不是给 0。
    verify: >-
      读面判据：同一 run 的两个实验记录的指标按**同名列**求差；
      任一侧缺该指标 ⇒ 该指标**不在**对比里且**点名**（不得当成 0 参与比较）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**：真实模型会话产出的**计划声明**（而非夹具）驱动两臂实验，
      读数记档（run id / 各臂参数 / 各臂指标 / 差值）。**若模型侧不可用** ⇒ 按降级梯
      如实登记（记 PENDING + 点名阻塞点），**不得**伪造成真实跑成功。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且两臂读数在树。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**）+ 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 +
      原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 实验**），使阶梯的「实验」域 `依据 GOAL` 收录本 GOAL。
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
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**（记录 / GOAL / PLAN /
      `examples/**` / 测试 / 文档）—— **只在 gitignored 的 `.env` 落位**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - >-
      绕开沙箱白名单把任意环境变量塞进容器（§9 默认 deny）：参数面必须是**声明白名单**，
      判据断言白名单**真的生效**（未声明的键传不进去）
    - 为让「两臂」成立而**放宽**既有的单臂契约判据（`experiment_execution` 的判据一字不动）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **新站不可用**（连通 / 协议面 / 工具调用任一不通）且无替代路径 —— 记 BLOCKED，
    逐条写明阻塞点（**不得**为此放宽任何判据或伪造成功）
  - >-
    两臂实验需要**改动沙箱镜像或镜像 pin** 才能成立 —— 立即 BLOCKED，留人工拍板
    （镜像 pin 是既有安全面，不得自行改）

child_plans:
  - .cursor/plans/tasks/PLAN-20261015-477-goal-079-ec01-experiment-parameters-come-from-the-declaration.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-478-goal-079-ec01-experiment-parameters-come-from-the-declaration.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

## 目标与退出标准

**一句话**：把「实验」从**固定脚本**推进到**由计划声明参数并按臂执行** —— 实验域 **L2 → L3**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进且有停止规则）与**质量**（产出的可判定性）**同时**受益：
  没有臂/对照，「实验」只能给出**一个**数；有臂之后，「哪个条件更好」才成为**可比**的事实；
- **能力域** = **实验**（阶梯上那一行：当前级「真容器实验 + 可否证阈值」
  → 下一级「**实验由计划派生**（现为固定脚本），多臂 / 对照组」）；
- **间接推进**「计划」域：计划从「描述」变成**参数来源**（这一步是「计划驱动实验」的前置）。

**为什么这一条更近科研**（对照阶梯，**建档实测**）：

- `examples/experiments/exact_match_index_benchmark.py` 的参数是**模块常量**
  （`SEED = 7` / `N_ITEMS = 800` / `N_DUPLICATE_PAIRS = 40`，实测逐行如此）；
- `ExperimentPlan` 的字段只有 `id` / `name` / `hypothesis` / `task_contract_ref` /
  `input_spec_digest` / `state`（**没有任何参数位**）；
- `packages/domain/experiments.py` / `experiment_state.py` 对 `arm` / `arms` /
  `control_group` **零命中** ⇒ **臂这个概念在域里不存在**；
- 而**缝已经在**：`ExperimentExecutionRequest.environment`（`Mapping[str, str]`）
  经 `execute.py:397` → `docker_backend.py:389`（`environment = dict(spec.environment)`）
  **真的进容器**，且 `environment_digest` 已被记录 —— 今天产品路径只往里塞了 `EXPERIMENT_RUN_ID`。

⇒ 缺的**不是**执行能力，而是「**参数由声明给出**」+「**多个臂**」这两件**可判定**的事。

**本 GOAL 不加新能力、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **§9 纪律**：参数面是**声明白名单**（不是「任意环境变量转发」）；判据断言未声明的键
  **传不进去**。沙箱镜像 pin 不动（改了即 BLOCKED）。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用 ⇒ 记 PENDING + 点名阻塞点；
  **不伪造**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证
（逐 job annotation / 同时终止时刻 / 状态页 incident），与 `cancel-in-progress`
（`run conclusion=cancelled`）形态区分。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立**（本 GOAL 被某个域的 `依据 GOAL` 收录）。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- **改沙箱镜像 / 镜像 pin** —— 需人工拍板（既有安全面）；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（参数面经声明传递） |
| 1 | PLAN-20261015-477 | 见「CI 台账」 | 参数面判据 **11 passed**（白名单 / 逐键传递 / 零回归 / 脚本真读 / 非法点名 / 命名空间）；三向按压全红且逐字节复原 | 见「CI 台账」 | 2 次（见「cycle 1 的修复记录」） | EC-01 **PASS**；EC-02/03/04/05 PENDING | cycle 2 = EC-02（多臂/对照） |

### cycle 1 的修复记录（逐条如实）

1. **判据里的域对象手搓错了**（实测）：`RoleDefinition(id=..., title=...)` —— 那个类**没有** `title` 字段；`ID(...)` 还要求**合法 UUID4**（两次实测报错逐字见判据开发过程）⇒ 改用**既有共享夹具**（`tests.contracts.fixtures.role_definition` / `agent_spec`）与 `uuid4()`，**不手搓域对象**。
2. **`examples/experiments/**` 不在 mypy 的 `files` 面内**（如实登记）：脚本侧的类型面由**判据**（真跑子进程 + 逐项断言指标）承担，不由静态检查承担。


## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档（序 47） | `b05b0067` | [M0 38677344100](https://github.com/Eswink/research-system-new/actions/runs/38677344100) / [Push 38677343399](https://github.com/Eswink/research-system-new/actions/runs/38677343399) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | **ACTIVE** | **建档**：承 GOAL-078 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「实验」域 **L2 → L3**（`下一级是什么` 逐字：实验由计划派生，多臂 / 对照组）。**建档实测**（四条）：① 实验脚本参数是**模块常量**（`SEED = 7` / `N_ITEMS = 800` / `N_DUPLICATE_PAIRS = 40`）；② `ExperimentPlan` **无参数位**（字段逐个读出）；③ 域层对 `arm` / `arms` / `control_group` **零命中** ⇒ 臂概念不存在；④ **缝已在**：`ExperimentExecutionRequest.environment` 经 `execute.py` → `docker_backend.py`（`environment = dict(spec.environment)`）**真的进容器**且已被记 digest，而产品路径今天只塞了 `EXPERIMENT_RUN_ID`。这四条就是本 GOAL 的靶子与可行性依据。 |
| 2026-10-15 | ACTIVE | **cycle 1 落地**（EC-01，PLAN-477）：实验参数从**脚本模块常量**变成**声明事实** —— 装配声明经「执行请求 → 容器环境」到脚本（逐键 / 白名单 / 前缀命名空间不相交），**未声明零回归**（请求环境与脚本产出都与改动前逐字相同），**值非法点名失败**。判据 11 例；三向按压全红。**EC-01 → PASS**（RECHECK-478 = PASS）；EC-02/03/04/05 PENDING。 |
