---
id: GOAL-20261015-079
slug: experiment-derived-from-the-plan-with-arms
title: 实验由计划派生 + 多臂/对照（实验域 L2 → L3）
status: ACHIEVED
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
    status: PASS
  - id: EC-03
    criterion: >-
      **臂间可比**：读面能回答「**两臂的同一个指标差多少**」——不是「两条记录都在」
      而已；差异由**落库的指标值**算出（可复算），且缺指标时**点名**而不是给 0。
    verify: >-
      读面判据：同一 run 的两个实验记录的指标按**同名列**求差；
      任一侧缺该指标 ⇒ 该指标**不在**对比里且**点名**（不得当成 0 参与比较）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**：真实模型会话产出的**计划声明**（而非夹具）驱动两臂实验，
      读数记档（run id / 各臂参数 / 各臂指标 / 差值）。**若模型侧不可用** ⇒ 按降级梯
      如实登记（记 PENDING + 点名阻塞点），**不得**伪造成真实跑成功。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且两臂读数在树。
    status: PASS
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
  - .cursor/plans/tasks/PLAN-20261015-479-goal-079-ec02-two-arms-with-a-control.md
  - .cursor/plans/tasks/PLAN-20261015-481-goal-079-ec03-the-arms-are-comparable.md
  - .cursor/plans/tasks/PLAN-20261015-483-goal-079-ec04-live-two-arm-run.md
  - .cursor/plans/tasks/PLAN-20261015-485-goal-079-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-486-goal-079-ec05-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
  - .cursor/memory/entries/MEM-20261015-223-closeout-assets-need-ownness-not-just-self-consistency.md
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

## 残余与未覆盖范围（逐条明写）

**残余**（本轮**实测**到的、未做的）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办（它的判词由 `tools/verify_goal079_closeout.py`
  产出）；本节的其余条目是各 cycle 的**真实**残余（逐条对应各自的 RECHECK）。
- `W-2` —— **臂数 > 2 与「哪个臂更好」不在射程内**：本轮做的是「声明的臂各跑一次 +
  同名指标可比」；**多臂择优**（哪个臂赢、按什么判）是**下一格**的事（承 EC-02 `W-2` /
  EC-03 `W-3`）。
- `W-3` —— **参数只支持整数**（脚本侧 `_declared_int`）：现有三个参数都是整数 ⇒ 不假装通用；
  加字符串 / 浮点参数要**同轮**加对应读取与判据（`MEM-20261015-222` 已登记该边界）。
- `W-4` —— **报告第 3 节行数随臂数翻倍**（两臂时 8 指标 × 2 臂 = 16 行）：这是「不丢臂」与
  「逐字可溯源」的取舍结果；臂再多时的**可读性**（分组 / 折叠）无人判（承 EC-04 `W-3`）。
- `W-5` —— **「实验设计本身」仍不由检索 / 立题产出派生**：本 GOAL 让**参数**由装配声明给出、
  臂由声明给出 —— 而**声明是谁写的**（模型 / 计划 / 人）不在射程内；阶梯「实验」域的
  `下一级是什么` 逐字写着这一条 ⇒ 本 GOAL 只把 L2 → L3 的第一半做完。
- `W-6` —— **同族缺陷的第二例已修但未普查**：`verify_goal078_closeout.py` 自洽地加载了
  上一轮断言集（本 cycle 实测）。`test_closeout_verifiers_run_their_own_assertions.py`
  的第三项对拍现在把**所有已登记验证器**都过了一遍（绿），但**旧一代**（`LEGACY_INLINE`，
  断言内联、无外部断言集）**没有**可对拍面 ⇒ 那一代是否存在**其它**同族问题**未普查**。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**（M18 deferred）、**部署面验证**、
  **D 组审批通道** —— 均**不做**；
- **改沙箱镜像 / 镜像 pin**（既有安全面）—— **需人工拍板**，本轮一字未动；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；真实 run 由 live 判据在**显式开关下**跑；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

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
| 2 | PLAN-20261015-479 | 见「CI 台账」 | 臂判据 **14 passed**；e2e **6 passed**（含真容器 run 级：读面 2 条实验、两臂比率 **7990.0 vs 178.5**）；五向按压全红且逐字节复原 | 见「CI 台账」 | 3 次（见「cycle 2 的修复记录」） | EC-02 **PASS**；EC-03/04/05 PENDING | cycle 3 = EC-03（臂间可比） |
| 3 | PLAN-20261015-481 | 见「CI 台账」 | 对比判据 **13 passed**；e2e **8 passed**（真容器 run：差值 `178.5 - 7990.0 = -7811.5`，判据自己重算核对；`agreement` 进 `not_numeric`）；七向按压全红且逐字节复原 | 见「CI 台账」 | 1 次（见「cycle 3 的修复记录」） | EC-03 **PASS**；EC-04/05 PENDING | cycle 4 = EC-04（真实中转站） |
| 4 | PLAN-20261015-483 | 见「CI 台账」 | live 实跑 **1 passed**（三次：172.90 / 169.68 / **190.08s**）；两臂各落库（同一镜像 digest）、指标 **7990.0 vs 178.5**；差值落盘 `-7811.5` / `-680` / `-312460` / `0`；`agreement` 进 `not_numeric`；报告第 3 节 4 列 16 行 | 见「CI 台账」 | 0 次（缺陷在 live 取证中一次定位并修复） | EC-04 **PASS**；EC-05 PENDING | cycle 5 = EC-05（自举收口） |
| 5 | PLAN-20261015-485（收口） | 见「CI 台账」 | 本树 **78 条判词全绿**；**两树 `TWO-TREE PASS`**（78 条逐行相同 + `sha256` 一致 `2c9121ae…`、归档 `CR=0`）；家族判据 **9 passed**；按压 `V9-8` 两处红 + 逐字节复原；as-is m0 终态行 `PASS: profile=m0; 23 deterministic checks` | 见「CI 台账」 | 1 次（见「cycle 5 的修复记录」） | **五 EC 全 PASS** ⇒ 阶梯「实验」域 **L2 → L3 成立** | 下一轮 = 收口后按宪章「第四件」开下一个 GOAL |

### cycle 5 的修复记录（逐条如实）

**本 cycle 抓到的真缺陷**（读收口资产时实测，**同族缺陷第二例**）：
`tools/verify_goal078_closeout.py` 的 `ASSERTIONS` 常量与 `_load_assertions()` **双双**
写着 `goal077_closeout_assertions.py` ⇒ ① 「声明 == 实载」成立（首版家族判据放行）；
② `goal078` 的 **29 条自有断言从未运行**（在 078 归档 73 条判词里零命中）；
③ 该验证器自己的 `self-loads-its-own-assertions` 判词**恒绿**（它问的字符串**就是**
当时实载的上一轮文件名）。处置 = 三处：常量与加载行改回自己那份；自指判词**按本文件名推**；
家族判据加**第三项对拍** + 「自洽但非己有」反向反例。按压 `V9-8` 两处红 + 逐字节复原。

**本 cycle 的修复记录（本 GOAL 自身，逐条如实）**：

1. **断言集里我的猜测被自己的判据抓红**（实测）：`ec04` 那条最初写「`for arm in`」——
   而 live 判据**实际**的逐臂遍历形态是 `for entry in entries`（真读出来才发现）
   ⇒ 判据红并**点名**缺哪个标记；改为实测形态。这正是「判据要认**在场的事实**，
   不认我记忆里的形状」。
2. **验证器首跑两红 = 时序而非缺陷**（实测）：`record-RECHECK-20261015-486` 与
   `records-declare-existing-rechecks`（PLAN-485 的 `latest_recheck` 尚未落盘）
   ⇒ 记录按序写入后自消。**不是**放宽任何判据。

3. **as-is m0（在全部记录写入之后）抓到两处真红 —— 都是我自己刚造出来的**（实测）：
   把 RECHECK-486 的 slug 从 `self-bootstrap-closeout` 改成收口复检判据认的形式
   （`closeout-recheck`）时，只改了「声明」面，**两处引用面**没跟着改：
   `MAINLINE.md` 的进展行链接与 `MEM-223` 的 `source_rechecks` 仍指旧文件名 ⇒
   `framework/validate_bundle`（本地链接不存在）与 `framework/validate`
   （工程记忆来源不存在 + Markdown 链接失效）**双双判红**。
   **处置 = 改引用（不是改判据）**：三处全部重新指向真文件名 ⇒ 两条判据复跑绿，
   **再跑一次全量 m0** 得终态行 `PASS: profile=m0; 23 deterministic checks`（24 条 `PASS [`、0 `FAILED`）。
   **这正是 `MEM: record-face-gates-catch-your-own-record` 的同一形态**：改记录的名字，
   受判面（链接/来源）会**自己**找上门 —— 而它们在 m0 里，不在我的记忆里。

### cycle 4 的修复记录（逐条如实 —— **本轮的价值就在这里**）

**live 取证抓出两处产品真缺陷 + 一处判据盲区**（第一次真实多臂 run 就暴露）：

1. **报告静默丢一臂**：`report_facts.metrics_of` 按**指标名**归并 ⇒ 两臂的同名指标**后写覆盖先写**（报告只带一臂的数字，读者看不出）。⇒ 改成**逐臂一行**（带 `experiment_run_id`）。
2. **表格被撑破**：修 ① 后我用 `" | "` 把两臂并进**同一格** ⇒ 那一行变成 **4 列**而 markdown 表头只有 3 列 ⇒ **渲染坏掉**（第二次 live 跑实测）。⇒ 渲染器在指标带实验标识时**表头多一列「实验」**、每个 (指标, 实验) 一行。
3. **判据盲区**：`_assert_live_report` 只查 `entries[0]` ⇒ **判据本身也看不见** ①②。⇒ 改成**逐臂遍历**；汇编器判据补**表格形态**（管道符计数一致）与**单臂零回归**。

三次真实 run 逐次验证（修复前红、修复中红、修复后绿）—— **这就是 live 取证的用途**。


### cycle 3 的修复记录（逐条如实）

1. **判据里把缺指标方向写反了**（实测抓到的**判据自身**缺陷）：`missing_in_left` 的语义是「**左臂缺**的指标」（= 右臂有、左臂没有），我按「右臂缺」写 ⇒ 两条判据红。实现是对的（实测读数逐字见判据开发过程）⇒ 改判据并在 docstring 里**明写方向口径**（免得后来者再猜）。**没有**改实现去迁就写错的判据。
2. **判据里漏了一行 import**（`Decimal`）：用于「判据自己重算差值」的算术核对 ⇒ 补上。


### cycle 2 的修复记录（逐条如实）

1. **`mock_relay` 夹具不在本模块**（实测）：新 e2e 直接引用它会 `fixture not found` ⇒ 从既有离线 e2e **导入**同一夹具（`__all__` 声明），避免两处各写一份。
2. **V9-4 的锚点过宽**（按压实测）：最初压在「`declare_arms` 调用」这一行，而它同时被 EC-01 的判据使用 ⇒ **基线就不绿**。按压的纪律是「未按压必须绿」⇒ 把受判面改成 **EC-02 自己的**用例类（`TestTwoArmsReallyRun`），基线恢复绿、按压真红。
3. **V9-2 锚点随实现演进失配**（实测）：`parameter_environment(assembly.parameters)` 在 EC-02 改成 `parameter_environment(parameters)`（臂可覆盖）⇒ 锚点命中 0 次。按压脚本的锚点是**实现文本**，实现变了就要同轮改 —— 这正是「锚点必须唯一且在场」那条断言的用途（命中 0 次时它**点名**而不是静默跳过）。


### cycle 1 的修复记录（逐条如实）

1. **判据里的域对象手搓错了**（实测）：`RoleDefinition(id=..., title=...)` —— 那个类**没有** `title` 字段；`ID(...)` 还要求**合法 UUID4**（两次实测报错逐字见判据开发过程）⇒ 改用**既有共享夹具**（`tests.contracts.fixtures.role_definition` / `agent_spec`）与 `uuid4()`，**不手搓域对象**。
2. **`examples/experiments/**` 不在 mypy 的 `files` 面内**（如实登记）：脚本侧的类型面由**判据**（真跑子进程 + 逐项断言指标）承担，不由静态检查承担。


## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档（序 47） | `b05b0067` | [M0 38677344100](https://github.com/Eswink/research-system-new/actions/runs/38677344100) / [Push 38677343399](https://github.com/Eswink/research-system-new/actions/runs/38677343399) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 1（EC-01 参数面 + 11 例 + 三向按压） | `f2291483` | [M0 38682201374](https://github.com/Eswink/research-system-new/actions/runs/38682201374) / [Push 38682200974](https://github.com/Eswink/research-system-new/actions/runs/38682200974) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 2（EC-02 多臂 + 逐臂派发 + 20 例 + 七向按压） | `aad54b4d` | [M0 38708199118](https://github.com/Eswink/research-system-new/actions/runs/38708199118) / [Push 38708198186](https://github.com/Eswink/research-system-new/actions/runs/38708198186) | **第 1 次尝试（`run_attempt=1`）：`quality-ubuntu-latest` = `failure`** —— 10 条 `docker.errors.BuildError`（`registry-1.docker.io` 拉 `${python:3.12-slim}` 基础镜像时 `unable to decode token response … Client.Timeout`），**全部**落在 `tests/adapters/execution/test_docker_backend_e2e.py`（**本 commit 未触碰该文件**，同一 job 在上一 run `f2291483` 为 `success`）；同 run 其余七 job 全 `success`，**本 cycle 新增的 `tests/e2e/test_two_arm_experiment_offline.py` 6 例在该 attempt 里全绿** ⇒ 失败分类 = **基础设施（镜像仓库不可达）**，非代码缺陷。**处置** = `rerun-failed-jobs`，**第 2 次尝试（`run_attempt=2`）八 job 全 `success`**（未改任何代码、未动任何阈值） |
| cycle 3（EC-03 臂间可比 + 13 例 + 七向按压 + 台账一行） | `c94ad646` | [M0 38684256082](https://github.com/Eswink/research-system-new/actions/runs/38684256082) / [Push 38684256185](https://github.com/Eswink/research-system-new/actions/runs/38684256185) | **M0 八 job 全 `success`**（`console-frontend` / `observability-overhead-ubuntu` / `quality-windows` / `eval-gate` / `quality-ubuntu` / `container-quality` / `collector-quality` / `observability-overhead-windows`）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 3（EC-03 落地） | `2a4c1692` | [M0 38717129906](https://github.com/Eswink/research-system-new/actions/runs/38717129906) / [Push 38717129517](https://github.com/Eswink/research-system-new/actions/runs/38717129517) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 4（EC-04 live 多臂 + 两处产品缺陷修复 + 判据盲区） | `a07a2532`（**tip**） | [M0 38726525799](https://github.com/Eswink/research-system-new/actions/runs/38726525799) / [Push 38726525638](https://github.com/Eswink/research-system-new/actions/runs/38726525638) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |

| cycle 5（EC-05 收口：同族缺陷修复 + 收口资产 + 阶梯记账） | `a8bff586`（**tip**） | [M0 38746372702](https://github.com/Eswink/research-system-new/actions/runs/38746372702) / [Push 38746371173](https://github.com/Eswink/research-system-new/actions/runs/38746371173) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**（**本 GOAL 的末条实测提交**） |

**台账尾巴的 CI（如实登记）**：尾巴提交 `a9cbf887` 的 run
[M0 38750027650](https://github.com/Eswink/research-system-new/actions/runs/38750027650)
**`conclusion=cancelled`** —— `quality-windows-latest` / `quality-ubuntu-latest` 两 job 被取消，
其余六 job `success`；Push-on-main 三条 CodeQL 全 `success`。**原因** = `cancel-in-progress`：
紧接其后的**序 48 建档**推送（`754d91ed`）把它取消了 —— 这是 `MEM: m0-ci-concurrency-batch-push`
的同一形态。**`covered_by = 754d91ed`**：序 48 的树**包含** `a9cbf887` 的全部内容
（只多新 GOAL 文件与程序表行）⇒ 由 [M0 38751287254](https://github.com/Eswink/research-system-new/actions/runs/38751287254)
（八 job 全 `success`，`run_attempt=1`）覆盖。**不**记绿、**不**跳过取证。

**自我指涉边界（明写并封闭）**：本台账的**末条实测提交 = `a07a2532`**（其 run 已到终态且
**八 job 全绿**）；**cycle 5（EC-05 收口）的提交与其 CI 结论不在本台账内** —— 它的
run 要等本提交推送之后才存在，**台账提交自身不产生可引用的 CI 结论** ⇒
**到 `a8bff586` 为止，不再向后追链**（**不得**循环引用）。收口面（收口复检 / 两树 /
m0 / 治理）由本 GOAL 的 `latest_recheck`（RECHECK-486）承担；**CI 面**由 tip 提交的
run 承担 —— 若该 run 判红，按「CI 失败分类与纠错」回到 cycle 6 处置，
**不**修改本台账的历史行。**失败记录**：本轮 **CI 零真红**（`aad54b4d` 的 `attempt=1`
基础设施红已如实登记 + `rerun-failed-jobs` 后 `attempt=2` 全绿）；
**本地零真红**（三次修复都由判据自己抓出并点名，见 cycle 2/3/5 的修复记录 —— 含 m0 抓到的两处引用面真红）。

**凭据审计**：收口前 `tools/credential_audit.py` 四面 `offenders=0`。

**as-is m0（在全部记录写入之后）**：`PASS: profile=m0; 23 deterministic checks`（24 条 `PASS [` / **0 `FAILED`**） **采点说明**：该实跑发生在**全部交付与记录写入之后**、在本台账尾巴（只改记录的提交）**之前**——台账尾巴与其后仅含记录的提交**不再重跑本地门**，其**记录面**最终覆盖由 CI 承担（承 `MEM: record-face-is-gated-run-the-gate-last`）。**本终态行采自记录写到此处之后的实跑** —— 此前一次同款实跑抓到我改 RECHECK slug 时留下的两处引用面真红（`MAINLINE` 链接 / `MEM-223` 来源），**改引用、零判据改动**后复跑即得此终态行。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | **ACTIVE** | **建档**：承 GOAL-078 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「实验」域 **L2 → L3**（`下一级是什么` 逐字：实验由计划派生，多臂 / 对照组）。**建档实测**（四条）：① 实验脚本参数是**模块常量**（`SEED = 7` / `N_ITEMS = 800` / `N_DUPLICATE_PAIRS = 40`）；② `ExperimentPlan` **无参数位**（字段逐个读出）；③ 域层对 `arm` / `arms` / `control_group` **零命中** ⇒ 臂概念不存在；④ **缝已在**：`ExperimentExecutionRequest.environment` 经 `execute.py` → `docker_backend.py`（`environment = dict(spec.environment)`）**真的进容器**且已被记 digest，而产品路径今天只塞了 `EXPERIMENT_RUN_ID`。这四条就是本 GOAL 的靶子与可行性依据。 |
| 2026-10-15 | ACTIVE | **cycle 1 落地**（EC-01，PLAN-477）：实验参数从**脚本模块常量**变成**声明事实** —— 装配声明经「执行请求 → 容器环境」到脚本（逐键 / 白名单 / 前缀命名空间不相交），**未声明零回归**（请求环境与脚本产出都与改动前逐字相同），**值非法点名失败**。判据 11 例；三向按压全红。**EC-01 → PASS**（RECHECK-478 = PASS）；EC-02/03/04/05 PENDING。 |
| 2026-10-15 | ACTIVE | **cycle 2 落地**（EC-02，PLAN-479）：实验支持**多臂/对照** —— 臂声明（两种形态 + 重复/非法点名拒绝）、臂 id **独立派生**（不复用「一 run 一实验」）、派发体**逐臂各跑一次**、主臂代表任务且消息点名全部臂。真容器 run 上：读面 **2** 条实验、两臂同指标 **7990.0 vs 178.5**（参数不同 ⇒ 读数不同）。判据 14 + 6 例；五向按压全红。**EC-02 → PASS**（RECHECK-480 = PASS）；EC-03/04/05 PENDING。 |
| 2026-10-15 | ACTIVE | **cycle 3 落地**（EC-03，PLAN-481）：臂间**可比** —— 纯函数对比器（消费既有读面载荷，**零 DTO/路由/快照改动**）：`delta = right − left`、**同名列才比**、缺指标**逐臂点名**（不折算成 0）、非数值（布尔等）**排除并点名**、空对比 `comparable=False` **不是**「差值为 0」。真容器 run 上差值 `-7811.5`。判据 13 + e2e 2 例；七向按压全红。**EC-03 → PASS**（RECHECK-482 = PASS）；EC-04/05 PENDING。 |
| 2026-10-15 | ACTIVE | **cycle 4 落地**（EC-04，PLAN-483）：**新站**上的一次真实 run 里声明的**两个臂**各在真容器跑一次、各自落库、指标不同、差值可算且记档。**live 取证抓出两处产品真缺陷 + 一处判据盲区**（报告静默丢一臂 / 表格被撑破 / 判据只查首条）⇒ 三处一次修掉并用**再次真实 run** 验证渲染正确。**EC-04 → PASS**（RECHECK-484 = PASS）；EC-05 PENDING。 |
| 2026-10-15 | **ACHIEVED** | **cycle 5 收口**（EC-05）：本树 **78 条判词全绿**；**两树 `TWO-TREE PASS`**（78 条逐行相同、`sha256` 一致 `2c9121ae…`、归档 `CR=0`、`cmp` 逐字节相同）；as-is m0 终态行 `PASS: profile=m0; 23 deterministic checks`（在全部记录写入之后）；治理 + 三条 MAINLINE 判据全绿；凭据审计四面 `offenders=0`。**同轮修掉一处收口资产同族缺陷**（`verify_goal078_closeout.py` 自洽地加载上一轮断言集 ⇒ 29 条自有断言从未运行）+ 家族判据加第三项对拍。**五 EC 全 PASS** ⇒ 阶梯「实验」域 **L2 → L3**：实验参数由**声明**给出、一次 run 跑**两个臂**（含对照）、臂间**差值可算且记档**（真容器 + 新站真实 run 上 `7990.0 vs 178.5`）。**残余与未覆盖范围逐条在位**；**不得**宣称项目安全（`R-M1`）；投递语义**不是**「恰好一次」（**明确否认**）。 |
