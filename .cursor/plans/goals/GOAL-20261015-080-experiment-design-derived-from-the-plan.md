---
id: GOAL-20261015-080
slug: experiment-design-derived-from-the-plan
title: 实验设计由计划派生（计划/实验域 → 下一级）
status: ACTIVE
created_at: 2026-10-15
updated_at: 2026-10-15
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」有**两行**逐字指向
    同一件事：**计划**域的 `下一级是什么` =「**计划驱动实验**（现由协议静态声明实验，
    模型不参与实验设计）」；**实验**域的 `下一级是什么` =「**实验设计本身由检索/立题派生**
    （现为「参数由计划声明 + 多臂/对照」；尚无判据证明实验设计本身由检索/立题产出派生）」。
    承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动迭代都必须让科研
    能力越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 阶梯「计划」与「实验」两域的**同一个下一格**；它**必须让阶梯
    前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让实验的**设计**（跑几个臂、每臂什么参数）**从计划产物派生**：`experiment` phase
    把计划阶段产出的制品声明为自己的**输入**、从它的**内容**里确定性地读出设计
    （白名单校验、缺设计**点名拒绝**而不是回落装配常量），且「设计因计划而不同」是
    可判定的 —— 换计划内容 ⇒ 设计跟着变。

exit_criteria:
  - id: EC-01
    criterion: >-
      **设计来源成为声明的、且是 run 作用域的读**：装配面可声明「本 run 的实验设计
      取自**计划产物**」（缺省不声明 ⇒ 既有语义逐字不变）；声明后，设计经**确定性读取器**
      从**本 run** 的计划制品（canonical 读面，按 run 过滤）读出 —— 读取器**不建会话、
      不出网**，且**读不到制品 ⇒ 点名拒绝**（不回落装配常量）。
      **★ 建档（cycle 0）实测更正**：本 EC 原写「experiment phase 声明 `research_plan`
      为其 `inputs` 制品」，**实测不可行且不该做** —— `test_declared_input_sources.py`
      要求声明输入是**仓库文件字节可重算、组合根种入**的制品（逐条判据在树），而计划产物
      是**本 run 的模型产物**；`inputs` 的既有口径逐字写着「只声明**外部供应**的输入，
      **不解析** phase 间的产物引用」（`services/api/demo.py`）。⇒ 改走
      **执行期 run 作用域读**（与 GOAL-078 的 `retrieval_context` 同一形态），
      **一条既有判据都不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_design_reader.py -q`
      ⇒ 全绿；判据覆盖：按 run 过滤（他 run 的计划读不到）/ 读不到制品点名 /
      未声明来源 ⇒ 零回归。**反证**：去掉 run 过滤 ⇒ 判据红。
    status: PASS
  - id: EC-02
    criterion: >-
      **设计由计划产物的内容派生**：确定性读取器从计划产物**内容**里读出实验设计
      （臂名 + 参数集），逐键过**既有白名单**（`ALLOWED_PARAMETERS`，不新开口子）；
      **声明了计划来源而设计缺席 ⇒ 点名拒绝**（不是静默回落装配常量 —— 那会让「计划驱动」变成一句空话；**未声明来源时**走既有装配语义，逐字不变）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_design_reader.py -q`
      ⇒ 全绿；判据覆盖：合法设计逐键读出 / 白名单外键点名拒绝 / 缺设计块点名拒绝 /
      畸形设计点名拒绝。**反证**：让读取器对缺失回落缺省 ⇒ 判据红。
    status: PASS
  - id: EC-03
    criterion: >-
      **「设计因计划而不同」可判定**：一次 run 的实验设计**由计划内容决定** ——
      两份不同的计划内容 ⇒ 两套不同的臂/参数；同一份 ⇒ 同设计（确定性）；且真实 run 上
      实验记录里的臂与参数**就是**计划里那套（逐条可溯源），不再来自装配常量。
    verify: >-
      离线 e2e：`tests/e2e/test_experiment_design_from_the_plan.py` ⇒ run `SUCCEEDED`；
      读面逐臂给出计划里声明的那些臂与参数；**反证**：装配面声明臂与计划声明臂不同 ⇒
      判据如实判否并点名（设计来源必须唯一）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**：真实模型会话写出的计划产物**驱动**该 run 的实验臂与参数，
      读数记档（run id / 计划产物 digest / 派生的设计 / 各臂指标）。**若模型侧不可用
      或模型不产出设计块** ⇒ 按降级梯如实登记（记 PENDING + 点名阻塞点），**不得**伪造。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且设计读数在树。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**）+ 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 +
      原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 计划**），使阶梯的「计划」域 `依据 GOAL` 收录本 GOAL
      （「实验」域如有推进亦同轮收录）。
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
      让「设计由计划派生」靠**静默回落**成立（缺设计块 ⇒ 回落装配常量）——
      那会把「计划没写」伪装成「计划驱动」；缺设计必须**点名拒绝**
    - >-
      绕开参数白名单：设计块里的键必须逐键过 `ALLOWED_PARAMETERS`；
      读取器**不得**接受白名单外的键（§9 默认 deny）
    - 为让「计划驱动」成立而**放宽**既有的实验参数 / 臂 / 对比判据（GOAL-079 的判据一字不动）
    - 改沙箱镜像 / 镜像 pin（既有安全面；需要即 BLOCKED 留人工拍板）
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
    需要**改动沙箱镜像或镜像 pin** 才能成立 —— 立即 BLOCKED，留人工拍板
    （镜像 pin 是既有安全面，不得自行改）

child_plans:
  - .cursor/plans/tasks/PLAN-20261015-487-goal-080-ec01-the-design-source-is-declared-and-run-scoped.md
  - .cursor/plans/tasks/PLAN-20261015-489-goal-080-ec02-the-design-content-decides-the-experiment.md
  - .cursor/plans/tasks/PLAN-20261015-491-goal-080-ec03-plan-change-means-experiment-change.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-492-goal-080-ec03-plan-change-means-experiment-change.md
memory_entries: []
---

## 目标与退出标准

**一句话**：把「实验设计」从**装配常量**推进到**由计划产物派生** —— 阶梯「计划」域与
「实验」域的**同一个下一格**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进）与**质量**（产出的可判定性）**同时**受益：
  设计的来源从「装配面写死」变成「计划产物里写着」，实验才有「因研究而不同」的资格；
- **能力域** = **计划**（阶梯逐字：`计划驱动实验`（现由协议静态声明实验，模型不参与实验设计））
  且**同时**推进**实验**（阶梯逐字：`实验设计本身由检索/立题派生`）；
- **两者是同一格**：计划域说的「模型/计划参与实验设计」与实验域说的「设计由立题派生」
  在今天指向同一件事 —— 计划产物的**内容**里带着设计，实验读它。

**为什么这一条更近科研**（对照阶梯，**建档实测**）：

- **实测 ①**：`examples/protocols/research_report_chain_v1.yaml` 的 `experiment` phase
  **没有 `inputs:` 声明**（`inputs:` 只出现在 `plan` / `review` / `report` 三处）⇒
  计划产物**从未被声明**为实验的输入 —— 也就是说协议层「实验与立题无关」是**字面事实**；
- **实测 ②**：全仓 `research_plan` 在 `packages/` 与 `services/` 下**零命中**
  （只出现在 `examples/` 的协议与合约里）⇒ 计划制品在**产品代码里没有任何消费者**；
- **实测 ③**：臂与参数今天由**装配常量**给出 —— live run 里就是
  `tests/e2e/test_research_report_chain_live.py` 的 `_LIVE_ARMS = {"control": {}, "treatment": {"n_items": 120}}`
  ⇒ **设计是测试作者写的**，不是计划写的；
- **实测 ④**：`ExperimentPlan` 的字段逐个读出（`id` / `name` / `hypothesis` /
  `task_contract_ref` / `input_spec_digest` / `state` / `created_at` / `updated_at`）——
  **仍然没有参数位**（GOAL-079 建档时如此，现在仍如此）。

⇒ 缺口**不是**参数能不能进容器（GOAL-079 已通），而是「**设计是谁写的**」——
今天写它的是装配面的人；本轮要让它是**计划产物**。

**本 GOAL 不加新依赖、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **设计面纪律**：读取器是**确定性**的（不建会话、不出网），逐键过 `ALLOWED_PARAMETERS`；
  **缺设计 ⇒ 点名拒绝**（fail-closed）。
- **来源唯一性**：设计**只能**有一个来源。装配面若同时声明臂，判据必须**点名冲突**
  （「哪个说了算」不可判定是最坏形态）。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用**或模型不产设计块** ⇒
  记 PENDING + 点名阻塞点；**不伪造**。

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

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办（它的判词由本 GOAL 的收口验证器产出）。
- `W-2` —— **计划的「写法」不在射程内**：本轮判的是「设计**从计划产物读出来**」；
  模型怎么写计划（提示词质量 / 是否真的推理过设计）**无人判**（承 GOAL-079 `W-5` 的另一半）。
- `W-3` —— **参数仍受既有白名单约束**（`seed` / `n_items` / `duplicate_pairs`）：
  设计块能表达的**参数空间**就这三个键；扩容需同轮加白名单与脚本读取（承 GOAL-079 `W-3`）。
- `W-4` —— **臂数 > 2 与择优不在射程内**（承 GOAL-079 `W-2`）。

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

### cycle 1 的修复记录（逐条如实）

1. **规划期实测更正**（**本 cycle 最有价值的那条**）：原设计把 `research_plan` 写进 phase 的
   `inputs:` —— 规划时**实测**发现它与既有判据 `test_declared_input_sources.py` **不相容**
   （该判据要求声明输入是**仓库文件字节可重算 + 组合根种入**的制品，而计划产物是本 run 的
   **模型产物**），且 `inputs` 的既有口径逐字写着「只声明**外部供应**的输入，**不解析**
   phase 间的产物引用」⇒ 改走**执行期 run 作用域读**（与 GOAL-078 同一形态）。
   **一条既有判据未动** —— 这是「不为让新目标成立而改判据」的现场兑现。
2. **读取器首版按 task 前缀猜 run 归属**（实测改进）：那需要一张 run→tasks 表，而本层
   不该持有它 ⇒ 改成**经 claim → relation 投影按 `evidence.run_id` 逐条过滤**
   （与 `GET /runs/{id}/evidence` 同一口径，也是 GOAL-078 的现成形态）。
4. **CI 抓到一处真缺陷，而本地规模门错过了它**（**如实登记**）：`read_design_from_plan`
   **57 行 > 50**（`test_python_source_size_limits.py`）。**为什么本地没抓到** —— 上一次本地跑
   规模门时该函数 48 行；其后我把它从「按 task 前缀扫」改成「经 ledger 投影扫」时**多加了 9 行**
   （下界检查 + 点名分支），而**那一次本地没重跑规模门**（只跑了功能判据）。
   **处置** = 抽出 `_the_one_plan`（**纯搬运**，零行为变化）⇒ 复跑 **1273 passed**。
   **教训**：改完函数体就要重跑规模门 —— 它是**独立的**一道门，功能判据绿不代表它绿。
3. **测试里一处 `pytest.raises(match=...)` 猜错了判词**（实测红）：他 run 登记时本 run 视角是
   「**nothing is registered**」而不是「no readable」—— 判词**分得开**正是本模块的设计，
   改判据去认**实际**的那一句（不是把实现改得含混）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（计划产物成为实验的声明输入） |
| 1 | PLAN-20261015-487 | 见「CI 台账」 | 读取器判据 **18 passed**（正向 / run 作用域 / fail-closed 六态 / 白名单 / 非目标 / 自检）；三向按压 V10-1…V10-3 **全 RED** 且逐字节复原；受影响套件 **1056 passed, 1 skipped** | 见「CI 台账」 | 1 次（**CI 抓到的真红：`read_design_from_plan` 57 行 > 50**；见「cycle 1 的修复记录」） | EC-01 **PASS**；EC-02/03/04/05 PENDING | cycle 2 = EC-02（设计的内容真正决定臂与参数） |
| 2 | PLAN-20261015-489 | 见「CI 台账」 | 设计判据 **11 passed**（正向 / 来源唯一 / fail-closed / 零回归）；三向按压 V10-4…V10-6 **全 RED** 且逐字节复原；受影响套件 **1064 passed, 1 skipped** | 见「CI 台账」 | 0 次 | EC-02 **PASS**；EC-03/04/05 PENDING | cycle 3 = EC-03（换计划 ⇒ 换实验：端到端读数） |
| 3 | PLAN-20261015-491 | 见「CI 台账」 | e2e 判据 **8 passed**（换计划 / 逐键参数 / 不撞命名空间 / 来源唯一派发前拒绝 / 零回归 ×2 / 确定性 ×2）；合计 **21 passed**；规模门 **1278 passed** | 见「CI 台账」 | 0 次 | EC-03 **PASS**；EC-04/05 PENDING | cycle 4 = EC-04（真实中转站上模型写出的设计驱动实验） |

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档（序 48） | `754d91ed`（**tip**） | [M0 38751287254](https://github.com/Eswink/research-system-new/actions/runs/38751287254) / [Push 38751286129](https://github.com/Eswink/research-system-new/actions/runs/38751286129) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**（**本 GOAL 的第一次推送 = 第一次全绿**） |
| cycle 1 派生（子 PLAN + ALL_PLAN + 规划期实测更正） | `65b41271` | [M0 38755298688](https://github.com/Eswink/research-system-new/actions/runs/38755298688) / [Push 38755298578](https://github.com/Eswink/research-system-new/actions/runs/38755298578) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 1 落地（读取器 + 18 例 + 三向按压） | `fd5b3bb1` | [M0 38758868844](https://github.com/Eswink/research-system-new/actions/runs/38758868844) / [Push 38758869619](https://github.com/Eswink/research-system-new/actions/runs/38758869619) | ⚠️ **M0 `conclusion=cancelled`**（`quality-windows` / `container-quality` / `quality-ubuntu` / `console-frontend` 四 job `cancelled`，其余四 job `success`；Push-on-main 三条 CodeQL 全 `success`）。**原因** = `cancel-in-progress`：紧随其后的 cycle 1 记录推送（`a58deb60`）把它取消了。**`covered_by = 05d57dc3`**（tip）：其后两批（记录 + 规模门修复）的树**包含** `fd5b3bb1` 的全部改动。**不**记绿 |
| cycle 1 记录面（PLAN/RECHECK/GOAL/ALL_PLAN） | `a58deb60` | [M0 38759244297](https://github.com/Eswink/research-system-new/actions/runs/38759244297) / [Push 38759243279](https://github.com/Eswink/research-system-new/actions/runs/38759243279) | 🔴 **M0 两 job `failure`**（`quality-ubuntu-latest` / `quality-windows-latest`）：`test_python_source_size_limits` 判 `read_design_from_plan` **57 行 > 50**；其余六 job `success`、CodeQL 三条 `success`。**分类** = **产品缺陷（真红）**，非基础设施 —— 修见下行 |
| cycle 1 修复（抽 `_the_one_plan`，纯搬运） | `05d57dc3`（**tip**） | [M0 38763219901](https://github.com/Eswink/research-system-new/actions/runs/38763219901) / [Push 38763218727](https://github.com/Eswink/research-system-new/actions/runs/38763218727) | **M0 八 job 全 `success`**（含此前判红的两个 quality job）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 1 台账补齐（只改记录） | `873aa2e8` | [M0 38766994494](https://github.com/Eswink/research-system-new/actions/runs/38766994494) / [Push 38766994632](https://github.com/Eswink/research-system-new/actions/runs/38766994632) | ⚠️ **M0 `conclusion=cancelled`**（`quality-windows-latest` 一 job `cancelled`，其余七 job `success`；CodeQL 三条全 `success`）= `cancel-in-progress`（紧随的对齐提交 `f2573c0f`）。**`covered_by = f2573c0f`**（它包含本提交全部内容）。**不**记绿 |
| 对齐提交（两树归档按收口态补交 —— 见 GOAL-079 台账） | `f2573c0f`（**tip**） | [M0 38770559732](https://github.com/Eswink/research-system-new/actions/runs/38770559732) / [Push 38770560475](https://github.com/Eswink/research-system-new/actions/runs/38770560475) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| 台账尾巴（只改记录） | `652d4489` | [M0 38774047858](https://github.com/Eswink/research-system-new/actions/runs/38774047858) / [Push 38774047321](https://github.com/Eswink/research-system-new/actions/runs/38774047321) | ⚠️ **M0 `conclusion=cancelled`**（`quality-windows-latest` 一 job；其余七 job `success`；CodeQL 三条 `success`）。**`run_attempt=1`**：该 job 各 **step 全 `success`** 而 job 结论是 `cancelled`（20 分钟运行后）；**`run_attempt=2`（`rerun-failed-jobs`）仍为 `cancelled`** —— 被紧随的 cycle 2 推送取消（`cancel-in-progress`）。**`covered_by = 25b9176c`**（tip 包含其全部内容）。**不**记绿 |
| cycle 2 落地（装配面 `design_source` + 11 例 + 三向按压） | `5c3da6ee` | [M0 38779284279](https://github.com/Eswink/research-system-new/actions/runs/38779284279) / [Push 38779281492](https://github.com/Eswink/research-system-new/actions/runs/38779281492) | ⚠️ **M0 `conclusion=cancelled`**（被紧随的记录推送 `25b9176c` 取消；CodeQL 三条全 `success`）。**`covered_by = 25b9176c`**。**不**记绿 |
| cycle 2 记录面（PLAN/RECHECK/GOAL/ALL_PLAN） | `25b9176c`（**tip**） | [M0 38779425336](https://github.com/Eswink/research-system-new/actions/runs/38779425336) / [Push 38779424610](https://github.com/Eswink/research-system-new/actions/runs/38779424610) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 2 台账（只改记录） | `2d268ee2` | [M0 38782081897](https://github.com/Eswink/research-system-new/actions/runs/38782081897) / [Push 38782083008](https://github.com/Eswink/research-system-new/actions/runs/38782083008) | ⚠️ **M0 `conclusion=cancelled`**（`quality-windows` / `quality-ubuntu` 两 job；其余六 job `success`；CodeQL 三条 `success`）= `cancel-in-progress`（紧随的 cycle 3 推送 `99af4cbc`）。**`covered_by = 99af4cbc`**。**不**记绿 |
| cycle 3 落地（换计划 ⇒ 换实验的 e2e 判据） | `99af4cbc`（**tip**） | 见「状态历史」（轮询中） | 待回填 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | **ACTIVE** | **建档**：承 GOAL-20261015-079 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「计划」域与「实验」域的**同一个下一格**（两行逐字都指向「设计由计划/立题派生」）。**建档实测**（四条）：① `experiment` phase **没有 `inputs:` 声明**（`research_report_chain_v1.yaml` 里 `inputs:` 只在 plan/review/report 三处）⇒ 计划产物从未被声明为实验的输入；② 全仓 `research_plan` 在 `packages/`·`services/` **零命中** ⇒ 产品代码里没有消费者；③ 臂与参数由**装配常量**给出（live 就是 `_LIVE_ARMS`）⇒ 设计是测试作者写的；④ `ExperimentPlan` 字段逐个读出，**仍无参数位**。这四条就是本 GOAL 的靶子与可行性依据。 |
| 2026-10-15 | **ACTIVE** | **cycle 3 落地**（EC-03，PLAN-491）：**「设计因计划而不同」在产品派发路径上可判定** —— 同一装配 + 两份计划 ⇒ 两套不同的实验（逐条对派生 id 与参数）；来源唯一在**派发之前**拒绝；未声明来源 ⇒ 既有语义逐字不变**且不读计划**；臂 id 判**确定性 + 换 run 会变**（哈希派生的正确判法）。八条 e2e 判据（执行体是受控替身 ⇒ 本 cycle **不**声称跑了容器）。**EC-03 → PASS**（RECHECK-492 = PASS）；EC-04/05 PENDING。 |
| 2026-10-15 | **ACTIVE** | **cycle 2 落地**（EC-02，PLAN-489）：**设计的内容真正决定实验** —— 装配面可声明 `design_source="plan"` ⇒ 臂从**本 run 的计划产物**读出（执行期解析）；**来源唯一**（与装配声明臂并存 ⇒ 点名拒绝）、**未认得的来源点名拒绝**（即使有臂也不放行）、计划不可读 ⇒ fail-closed（不回落装配常量）；未声明来源 ⇒ 既有语义逐字不变**且不读计划**。判据 **11 例**；三向按压**全 RED** 且逐字节复原。**EC-02 → PASS**（RECHECK-490 = PASS）；EC-03/04/05 PENDING。 |
| 2026-10-15 | **ACTIVE** | **cycle 1 落地**（EC-01，PLAN-487）：计划的**设计来源可声明**，读取器
确定性（只读 canonical、零出网）/ **run 作用域**（经 claim → relation 投影按 `evidence.run_id`
过滤）/ **fail-closed**（六态点名：无登记 / 无制品 / 无设计块 / 畸形 / 空臂 / 多制品）；
设计块里的键**逐键**过既有白名单（§9）。判据 **18 例**；三向按压**全 RED** 且逐字节复原。
**EC-01 → PASS**（RECHECK-488 = PASS）；EC-02/03/04/05 PENDING。 |
| 2026-10-15 | **ACTIVE** | **cycle 0 建档更正（实测驱动）**：EC-01 原文写「experiment phase 声明 `research_plan` 为其 `inputs` 制品」——**规划期实测判定不可行**：`tests/architecture/python/test_declared_input_sources.py` 的两条判据要求声明输入是**仓库文件字节可重算 + 组合根种入**（`created_by == "composition-root"`），而计划产物是**本 run 的模型产物**；且 `inputs` 的既有口径逐字写着「只声明**外部供应**的输入，**不解析** phase 间的产物引用」。⇒ 改走**执行期 run 作用域读**（与 GOAL-078 的 `retrieval_context` 同一形态）——**不为让新目标成立而改任何既有判据**。EC-01 同轮改写，EC-02 补「未声明来源 ⇒ 既有语义逐字不变」的边界。 |
