---
id: GOAL-20261111-109
slug: paired-ablation-content-adoption-judgeable
title: 配对消融让「内容采纳」成为可判形态（试点计划域 k=3）
status: ACHIEVED
created_at: 2026-11-11
updated_at: 2026-11-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-11 登记序 77…80 五轮程序（与序 76 同一次授权），本轮为序 77：
    「配对消融让『内容采纳』成为可判形态（试点计划域 k=3）」。沿用户 2026-10-29
    全权限预授权；push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E / RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS
    逐命令传，绝不写进 .env。
objective: >-
  阶梯七格里检索 / 计划 / 复检 / 迭代四格的 `下一级` 卡在同一个不可判点：GOAL-082 EC-04
  的记录理由是「模型是否采纳了内容不可机械判，子串判据会假绿」。**那条论证只针对子串判据**
  （`duplicate_pairs` 既在参数白名单又在两种假设下都出现 ⇒ 无区分力），**不针对因果**。
  配对消融消解这个混淆：同一输入、去掉 X、比较输出**分布的位移**——混淆论证是*组内*论证，
  *组间*对比正是中和它的设计。本轮交付四个新件 + 四条判据（缺一即判空）+ 阶梯改写，
  **试点计划域（plan）**：试点意味着只对「计划」这一格改写 `下一级`，其余三格逐字不动。
exit_criteria:
  - id: EC-01
    criterion: >-
      **run 级可比键**：新建 `packages/application/run_orchestration/comparison_digest.py`，
      从 `RunManifest` 投影出**剔除 `run_id` / `frozen_at` / `project_id`** 的 digest
      （形态照 `packages/domain/eval_result.py` 的 `comparison_digest`）。
      **既有 `semantic_digest()` 含 `run_id` ⇒ 两轮永不相等，不能用**——这一点必须由判据
      钉住（两份仅 run_id 不同的 manifest ⇒ semantic_digest 不等、comparison_digest 相等）。
    verify: >-
      `tests/application/run_orchestration/test_comparison_digest.py` ⇒ 正例
      （仅 run_id/frozen_at/project_id 不同的两份 manifest 键相等）+ 反证
      （**任何**声明字段换一个字 ⇒ 键不等 ⇒ 判红）。
    status: PASS
  - id: EC-02
    criterion: >-
      **只差一个 slot 的两臂**：新建 `packages/application/run_orchestration/ablation.py`
      的 `AblationPair(slot, present, absent)`；两臂由**同一份装配**产出，差异**只有那一个
      slot**。「只差一个变量」的机械证明 = 除该 slot 外，两份 prompt 的其余 section digest
      **逐字相等**（判据 ①）。
    verify: >-
      `tests/application/run_orchestration/test_ablation_pair.py` ⇒ ① 正例：两臂
      `comparison_digest` 相等且其余 section digest 逐字相等；② 反证：把 slot 内容换一个字
      ⇒ digest 不等 ⇒ 判红（证明它真在比内容）。
    status: PASS
  - id: EC-03
    criterion: >-
      **可数读数**：新建 `packages/application/run_orchestration/output_readings.py`，从
      计划正文（JSON envelope；`packages/application/experiments/design_from_plan.py` 的
      `design_block_in` 已能严格解析两种形态）抽**可数**读数：是否产出 design block /
      每臂参数取值 / 引用标识数。读不出 ⇒ 点名哪一种「空」，**不猜**。
    verify: >-
      `tests/application/run_orchestration/test_output_readings.py` ⇒ 三种读数各一条正例 +
      「没有 design block」与「读不到正文」两种空**分得开**（点名不同）。
    status: PASS
  - id: EC-04
    criterion: >-
      **读数表 + `MIN_CORPUS=3` 拒绝门**：新建 `tools/ablation_report.py`：k 次重复 ×
      两臂 ⇒ 读数表 + 位移统计 + 拒绝门（照
      `packages/application/deliverable/citation_distribution.py` 的 `calibration_gate`
      形态：**k<3 拒绝认证并点名**）。
    verify: >-
      `tests/tooling/test_ablation_report_gate.py` ⇒ ③ 反证：k=2 ⇒ 门判「不足」并**点名**；
      正例：k=3 ⇒ 认证并给读数表。
    status: PASS
  - id: EC-05
    criterion: >-
      **措辞边界机械化**：`tools/ablation_report.py` 的报告输出里**不得**出现
      `adopt` / `采纳` 类词——判「分布位移」，**不判**「模型采纳了 X」（判据 ④；
      与 AGENTS.md §4「不越级宣称」同姿态）。
    verify: >-
      `tests/tooling/test_ablation_report_wording.py` ⇒ 报告文本扫描闭集词表零命中 +
      反证（往报告里注入一个词表词 ⇒ 判红）。
    status: PASS
  - id: EC-06
    criterion: >-
      **阶梯改写（只动一格）**：阶梯「计划」行的 `下一级` 改写为「**配对消融下，X 的存在使
      输出读数分布发生位移**（k≥3；判「分布位移」，**不判**「模型采纳了 X」）」；
      **其余三格（检索 / 复检 / 迭代）的 `下一级` 逐字不动**——一格的证据不足以推广。
    verify: >-
      `tests/tooling/test_mainline_research_ladder_advances.py` 全绿（表结构 / 连续性）+
      本 GOAL 收口验证器断言四行的 `下一级`：计划行含新句、其余三行与改写前逐字相同。
    status: PASS
  - id: EC-07
    criterion: >-
      **收口资产与宪章记账**：`tools/verify_goal109_closeout.py` +
      `tools/goal109_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`；
      宪章程序表 / 阶梯 / 进展 / 修订按实际改；全仓**无采样控制**
      （`build_llm` 与 `CompletionRequest` 都没有 `temperature` / `seed`）⇒ 只能比**分布**
      不能比逐字——这条写进 `R-NN`；**本轮不引入采样控制**（会改契约面）。
    verify: >-
      收口验证器全 PASS；`tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`
      与 `test_tooling_scripts_meet_product_gates.py` 登记判据绿；
      `tools/credential_audit.py` 四面 `offenders=0`。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压
    - 把本轮点名的「运维数据」值改为结构性断言（附理由）
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把真实 key 写进任何被跟踪文件（只进 gitignored `.env`）
    - 引入 temperature/seed 采样控制（改契约面；登记 `R-NN` 后留待拍板）
    - 给其余三格（检索 / 复检 / 迭代）的 `下一级` 改写任何字
    - 把「分布位移」写成「模型采纳了 X」
    - 改 `.github/workflows/**`（本轮关闭）
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 需要采样控制才能继续 ⇒ 停下登记待拍板（**不自行引入**）
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261111-109-paired-ablation.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-109-paired-ablation.md
memory_entries: []
---

# GOAL-20261111-109 —— 配对消融让「内容采纳」成为可判形态（试点计划域 k=3）

## 目标与退出标准

承序 76（GOAL-20261111-108）之后：七格里检索 / 计划 / 复检 / 迭代四格卡在同一个不可判点。
本轮把「计划」这一格的可判性做出来——**不宣称**解决了其余三格。

### 为什么配对消融是可解的第三条路

GOAL-082 EC-04 的阻塞论证是**混淆论证**：`duplicate_pairs` 既在参数白名单、又在
「有 prior」与「无 prior」两种假设下都出现 ⇒ **子串判据**无区分力。但混淆论证是
*组内*论证——它说「在一份输出里，这个词的出现不能归因于 X」。*组间*对比（同一输入、
去掉 X、比较输出分布）正是中和它的实验设计：如果去掉 X 之后输出读数的**分布**移动了，
「X 影响输出」就有了可判证据——**不需要**在单份输出里指着某个词说「这是 X 的贡献」。

**判什么、不判什么**（写死，判据守）：判「分布位移」；**不判**「模型采纳了 X」——
后者是意图归因，前者是可数事实。

### 试点边界

只改「计划」一格的 `下一级`。检索 / 复检 / 迭代三格的机制同构，但**一格的证据不足以
推广**——逐字不动，等各自域的试点。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 七条 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住 ⇒ 移入「残余与未覆盖范围」，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动 ⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive → ② 执行 → ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错 → ⑦ 回写记录 + 下一轮。

**记录顺序**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py` → 之后不再改树 → 提交推送。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读失败输出定位；**修产品优先，禁改断言迁就** |
| live 判据在 CI 上 skip | `requires_live_llm` 无凭据 | **预期**：live 只在操作者本地跑；skip 不是 PASS |
| 行尾漂移 | 一条 LF 锚点判据突然红 | 检查是不是自己把文件写成 CRLF（`ruff format` 在 Windows 会写 CRLF） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |

## 终止与收口

- **ACHIEVED**：七条 EC 全 PASS + RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过上限，或 `max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实，不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261111-109 | `e003bfcc` | 消融四判据 + 阶梯射程判据 **55 passed**；收口验证器 **70 PASS / 0 FAIL**；governance 通过；ruff/format/mypy 三道具名 | 与收口提交同一次 push（无独立 run；run id 由下一笔 `.cursor` 提交回填——不冒领） | 两处真缺陷（夹具视图 dict 被渲染器静默丢段 ⇒ 两臂假相等；frozen dataclass 异常收不了消息） | `U-1` live k=3 未做 | 序 78（证据处置闭环） |

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- `W-1` **位移统计只有均值差，没有显著性检验与方差刻画**：`MIN_CORPUS=3` 是**标定下界**
  不是统计功效——k=3 时一列读数从全 0 到全 1 与从 0.67 到 0.33 在门眼里都是「位移」。
  要更强的判读需要更多重复或配对检验（Wilcoxon 类）——那是**统计口径**决策，待拍板，
  本轮**不**引入（引入即改变「什么算位移」的判定面）。
- `W-2` **观测汇总靠调用方喂 JSON**：`tools/ablation_report.py` 的输入契约由跑消融实验的
  一方产出；「从 run 库自动汇总 k×2 观测」的采集器本轮未交付（它是 live 测量的配套件，
  见 `U-1`）。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **未做一次 live k=3 配对消融实测**：四件交付与四条判据全部**离线**可跑（这是本轮
  的判法）；「X 的存在使输出读数分布发生位移」在**真实模型**上是否出现、位移多大，
  是下一轮（或本轮后续 cycle）用 4+ 次真实 run 取证的事。**本轮不宣称任何一次真实位移
  被测到过。**
- `U-2` **试点只面向「计划」一格**：检索 / 复检 / 迭代三格的机制**同构但未验证**——
  它们的 `下一级` 逐字未动（`test_goal109_ladder_pilot_scope.py` 钉住推广禁令），
  各自域的试点是各自 GOAL 的事。

### 声称边界（**不得宣称**的事）

- `R-1` **全仓无采样控制**：`build_llm` 与 `CompletionRequest` 都没有 `temperature` /
  `seed` ⇒ 配对消融**只能比分布，不能比逐字**；同输入两次 run 的输出文本本就不同。
  **本轮不引入采样控制**（会改契约面，属 `fix_policy.forbidden`）——「要不要采样控制、
  给哪几个实验合约加」是待拍板项。
- `R-2` **判「分布位移」，不判「模型采纳了 X」**：位移是**可数读数的分布事实**；
  「采纳」是意图归因。措辞闭集（`adopt` / `采纳` 类词）由工具出口守卫 + 判据两向按压
  守住——报告文本里出现这些词即判红。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-11 | ACTIVE | 建档：序 77；七条 EC；试点计划域 |
| 2026-11-12 | ACHIEVED | 七条 EC 逐条落地；判据全离线（live k=3 实测留 `U-1`）；阶梯只改「计划」一格；`R-1` 无采样控制只比分布 |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `e003bfcc` | 与收口提交（HEAD）**同一次 push**，无独立 run | 该 run 跑在收口树（含本行所指提交的全部内容）；run id 由下一笔 `.cursor` 提交回填 | 机制半场：四件交付 + 六个判据文件。同一次 push 的多个提交只有一个 M0 run ⇒ 本行不冒领（不点名 run） |
