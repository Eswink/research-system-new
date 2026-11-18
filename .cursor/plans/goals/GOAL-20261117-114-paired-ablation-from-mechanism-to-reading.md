---
id: GOAL-20261117-114
slug: paired-ablation-from-mechanism-to-reading
title: 配对消融从「机制」变成「读数」（可比键在真实路径可用 + k=3 两臂实测）
status: ACHIEVED
created_at: 2026-11-17
updated_at: 2026-11-18
owners:
  - root-agent
latest_recheck: .cursor/plans/rechecks/RECHECK-20261118-114-paired-ablation-readings.md
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
authorization:
  source: user-request
  ref: >-
    序 82（GOAL 号 114），charter 由 `tools/next_round_charter.py` 从 GOAL-113 读出。
    沿用用户 2026-10-29 全权限预授权；push-to-main-for-CI：只推 main、不 force、
    不重写历史、不推旁支；`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` /
    `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 逐命令传，绝不写进 `.env`。
    用户 2026-11-17 另拍板三件事：① 本轮做**完整试点**（修机制 + 六次真实 run 一轮跑完）；
    ② 六次 run 跑在**新建 plan-only 消融台协议**上（不复用四相链）；
    ③ 若四列**无位移** ⇒ **测量成立、bar 不升**（「没观察到」不得写成「观察到了」）。
objective: >-
  勘测实测（2026-11-17）：GOAL-109 交付的配对消融机制在**真实 run 上根本用不了** ——
  `comparison_digest` 比较的 27 个字段里含 `accepted_policy_exceptions`，而其中每条都带
  `accepted_at`（冻结那一刻的墙钟，`policy_acceptance.py:157`）⇒ 同一份装配的两次真实 run
  的键**永不相等** ⇒ `AblationPair.__post_init__` 一律点名拒绝。GOAL-109 的夹具把它设成
  `[]`，所以七条 EC 全绿而**零次真实使用**；它的 `U-1` 逐字写着「本轮不宣称任何一次真实
  位移被测到过」。本轮三靶：A）让可比键在真实路径上可用（窄归一化 + 冻结快照携带可比键）；
  B）补齐缺的那一步（读数 → 观测映射）并新建单相消融台协议；C）真实 k=3 × 2 臂 = 6 次
  run，产出第一份**四列分布位移**读数；D）序 82 记账与收口。
exit_criteria:
  - id: EC-01
    criterion: >-
      **上一轮的残余真的可读**：`GOAL-20261114-113` 补 `## 残余与未覆盖范围` 小节
      （`W-1` + 两条未覆盖），`tools/next_round_charter.py` 能从它产出非空骨架；
      `retrieval_context.py` 的过期陈述（「全仓零构造点」）改正；
      新判据 `tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py`
      （四条：可读 / 条目不丢 / 节缺席拒 / 断号拒）。
    verify: >-
      `uv run ... -m pytest tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py -q`
      ⇒ 4 passed；`tools/next_round_charter.py --root . --goal <GOAL-113> --next-goal-id
      GOAL-20261117-114` ⇒ 退出 0 且「二、」节非空。
    status: PASS
  - id: EC-02
    criterion: >-
      **可比键在真实路径可用**：`comparison_digest` 对
      `accepted_policy_exceptions[*].accepted_at` 做**窄归一化**（`NORMALIZED_NESTED_KEYS`
      显式声明一处）；例外表的其余键（capability / phase_id / provider_id /
      policy_version / decision / constraints / 顺序）逐字保留进 digest；
      `EXCLUDED_FIELDS` **仍是那三个身份字段**（不借这条路把整字段剔出去）。
      **实现偏离（有实测理由）**：只剥墙钟，不剔字段 —— 剔字段会让「接受过哪些例外」
      从比较面消失，那是把「装配可比」放宽成「什么都没比」。
    verify: >-
      `tests/application/run_orchestration/test_comparison_digest.py` ⇒ 24 passed
      （含 6 条反证：空/非空、能力、provider、constraints、decision、顺序）；
      `tools/goal109_closeout_assertions.py` 27 条断言仍全 PASS（剔除面未被改宽）。
    status: PASS
  - id: EC-03
    criterion: >-
      **冻结快照携带可比键**：`frozen_payload` 增 `comparison_digest` 键（现算，不另存
      副本）。理由：完整 `RunManifest` **不落库**（run 行只有 digest），事后无从复算 ⇒
      没有这一格，「两次 run 可比」只能在内存里成立、不能审计。
    verify: >-
      `tests/application/run_orchestration/test_frozen_payload_semantic_digest.py` ⇒
      三个 digest 不是别名（身份字段不同 ⇒ 只有可比键相等；语义漂移 ⇒ 可比键也变）。
    status: PASS
  - id: EC-04
    criterion: >-
      **读数 → 观测的映射**（GOAL-109 `W-2` 的采集器缺的那一步）：
      `ablation_observations.observation_from` 把三态读数映射成四列 **`int`**；
      `bool` 明确不产出（`ablation_report._observation` 拒 `isinstance(v, bool)`，
      而 `design_state == "block_present"` 天然产 bool —— 这是最容易假绿的一处）；
      闭集外状态点名拒绝（不回落成 0）。
    verify: >-
      `tests/application/run_orchestration/test_ablation_observations.py` ⇒ 9 passed
      （含 `type(v) is int` 逐列断言 + 三态逐格 + 闭环喂 `build_report` + 两条反证）。
    status: PASS
  - id: EC-05
    criterion: >-
      **单相消融台协议**：`examples/protocols/ablation_plan_probe_v1.yaml`
      （单相 `retrieval`、合约 `research_report_plan`、能力集与
      `research_report_chain_v1` 的 plan 相**集合相等**、`capability_execution: run_chain`、
      不声明会话工具绑定）。相 id 取产品瞄准的那个（`retrieval_wiring.RETRIEVAL_PHASE`）。
    verify: >-
      `tests/contracts/test_ablation_plan_probe_protocol.py` ⇒ 6 passed（含「相 id 就是
      出厂检索面瞄准的那个」+ 两条协议都能 `compile_protocol` 给出 plan）。
    status: PASS
  - id: EC-06
    criterion: >-
      **两臂在真实装配上配得起来**（离线段）：产品组合根 `assemble()` 上跑
      `present`（播种一条 PROJECT 档记忆）/ `absent`（空库）两臂，两 run 的
      `comparison_digest` **相等**、各得四列 `int` 观测、一对观测复制成 k=3 后过
      `ablation_report` 的门。
    verify: >-
      `tests/e2e/test_paired_ablation_offline_arms.py` ⇒ 5 passed。
    status: PASS
  - id: EC-07
    criterion: >-
      **真实 k=3 × 2 臂 = 6 次 run**（`ARM_SEQUENCE` 预先声明 P/A 交替，失败也登记、
      不挑样本、不重试到绿）；每 run 的可比键取自 `manifest.frozen` 事件；产物落
      `.cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json`
      （原始观测 + 语料门 + 四列位移 + 渲染报告）。
    verify: >-
      `RESEARCHOS_AGENT_RUNTIME=openhands` + live 开关 + `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1`
      跑 `tests/e2e/test_paired_ablation_on_the_plan_live.py`；证据 JSON 的 `runs` 六条、
      `corpus_gate` 给出结论。
    status: PASS
  - id: EC-08
    criterion: >-
      **阶梯按读数重判**：「计划」行的 `下一级` **逐字不动**（用户拍板：无位移 ⇒ bar 不升）；
      `当前级` 追加一句**描述性**读数（四列的 n=3 两臂均值与位移，注明「描述性，n=3，
      不判采纳」）。判据：`test_goal109_ladder_pilot_scope.py` 四条仍绿 + 新增一条
      「`下一级` 与 GOAL-109 收口时逐字相同」。
    verify: >-
      `tests/tooling/test_goal109_ladder_pilot_scope.py` ⇒ 全绿；新增判据在
      `tools/goal114_closeout_assertions.py`。
    status: PASS
  - id: EC-09
    criterion: >-
      **记账**：程序表序 82 行（轴 = 深度，能力域 = 计划，依赖 `GOAL-20261111-109`）；
      两表各 4 行 ⇒ 各归档最旧 1 行到 `archive/MAINLINE-2026-11-18-*`（原文搬运、LF、
      末行不带换行、指针插在既有指针块之前）；回填 GOAL-113 的 tip CI 读数。
    verify: >-
      归档后全部 `tools/verify_goal*.py` 零 FAIL；两表各 3 行；归档文件被活跃面
      以 `](archive/<name>.md)` 链接。
    status: PASS
  - id: EC-10
    criterion: >-
      **收口资产**：`tools/verify_goal114_closeout.py` + `tools/goal114_closeout_assertions.py`
      （产品面断言集：四个新件在树、`EXCLUDED_FIELDS` 仍三元、`ablation_report` 的四列名 /
      `MIN_CORPUS` / 措辞闭集逐字未改、协议相数与合约 id、`observation_from` 不出 bool、
      阶梯「计划」行 `下一级` 逐字不动），登记 `_VERIFIERS` 与 `IN_SCOPE`。
    verify: >-
      收口验证器全 PASS（0 FAIL）；两处登记判据绿；
      `tools/credential_audit.py` 四面 `offenders=0`。
    status: PASS
fix_policy:
  same_signature_retries: 3
  cycle_fix_retries: 10
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把 `accepted_policy_exceptions` 整个从比较面剔除（只许归一化时间戳）
    - 改 `tools/ablation_report.py` 的 `MIN_CORPUS` / `READING_FIELDS` / 措辞闭集
    - 让 `observation_from` 的四列出 `bool`
    - 为凑 k=3 而挑样本或改预先声明的 P/A 顺序
    - 无位移时升 bar（「计划」行 `下一级` 必须逐字不动）
    - 把凭据值写进任何被跟踪文件（只在 gitignore 的 `.env` 的 `LLM_MAIN_KEY`）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 中转站配额耗尽（429）且本轮窗口内不重置
child_plans:
  - .cursor/plans/tasks/PLAN-20261117-114-paired-ablation-readings.md
memory_entries: []
---

# GOAL-20261117-114 — 配对消融从「机制」变成「读数」

## 目标与退出标准

EC 表见 frontmatter `exit_criteria`（编号 / 标准 / 验证 / 状态逐条在列）。
本轮的**核心既有缺陷**是 EC-02/03（GOAL-109 交付的配对键在真实 run 上永不相等）；
EC-04/05 是缺的那一步与消融台；EC-07 是**第一次真实读数**。

**如实登记（不得读成已完成）**：

- **n=3 是标定下界，不是统计功效**；全仓无采样控制（无 `temperature` / 无 `seed`）
  ⇒ 只比**分布**，不判因果方向（GOAL-109 `R-1`/`R-2` 逐字未变）。
- **只测「计划」一格**。检索 / 复检 / 迭代三格的机制同构但本轮**逐字未动** ——
  一格的证据不足以推广（GOAL-109 `U-2`）。
- **四列都无位移是合法结论**：那时本轮交付的是「测量能力 + 一份真实读数」，
  **不是**「bar 达成」（用户已拍板）。
- **消融台的相 id 叫 `retrieval`**：出厂检索面把调用表钉在 `RETRIEVAL_PHASE`，不匹配
  的相被**静默跳过**；而产品那份调用表的检索词路径是 `research_question.query`（要一个
  问题相）⇒ 本探针**单相、由声明简报驱动**，调用表由装配方给出。产品面今天不认这份
  协议是既有缺口，如实登记。
- **`plan_fallback` 是一条从未被任何 GOAL 登记的死缝**：`packages/application/model_relay/
  fallback.py` 有实现、`ModelProfile.fallback` 被 preflight 的独立性判据读，但**运行期
  没有任何时候真的按 fallback 切模型**（`adapters/relay/gateway.py` 只有 circuit breaker
  + retry）。它牵涉评审独立性，本轮**只登记不修**。

## 循环入口协议

按迭代日志最后一行 + 工作树实况判定续点；任何一步完成立即回写本文件。
崩溃重入规则见 `.cursor/plans/goals/README.md`（幂等恢复六条）。

## 单 cycle SOP

① 生成子 PLAN（charter 骨架已由 `tools/next_round_charter.py` 产出）→ ② 执行 →
③ 本地验证（定向 + 静态门）→ ④ commit + push（主题点名 goal114；绝不 `git add -A`）→
⑤ CI 八 job 判读（不假设绿）→ ⑥ 失败分类纠错 → ⑦ 收口（全部 EC=PASS ⇒ RECHECK +
m0 witness + 两树复检）。

## CI 失败分类与纠错

| 分类 | 处置 |
| --- | --- |
| (i) 判据实现缺陷（自己的判据错） | 改判据并在迭代日志点名 |
| (ii) 环境资源型（阈值/超时/并发 flake） | 重跑该 job（`rerun-failed-jobs`），绝不动阈值 |
| (iii) 产品真缺陷 | 修复 + 反向按压，新 commit 点名 goal114 |

## 终止与收口

- **ACHIEVED**：十条 EC 全 PASS + 独立 RECHECK PASS/PASS_WITH_WARNINGS + 全量 m0
  witness（`PASS: profile=m0; 23 deterministic checks`，`PASS [` 24，0 FAILED，
  `tree changed during the run: False`）+ 两树复检 sha256 相同 + CI 八 job 全绿。
- **BLOCKED**：连续 2 轮零 EC 推进；或撞上停止条件清单（TrustLabel / RunManifest 的
  声明面被要求删字段 / `.github/workflows/**` / 撤销 §9 / 恰好一次 / github.com 出网不可达）。
- **ABORTED**：用户叫停。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261117-114-paired-ablation-readings | `25fa8887`、`2260b7eb`、`453898c8` | EC-01…06 落地 + 定向套件全绿；真实 k=3 六次 run 全 SUCCEEDED（26m29s） | [M0 44272246406](https://github.com/Eswink/research-system-new/actions/runs/44272246406) **8/8 `success`** / [Push 44272246485](https://github.com/Eswink/research-system-new/actions/runs/44272246485) 3/3 `success` | 4（拒冻不落事件 / 相 id 静默跳过 / assemble 缺 runtime 回落 Fake / citation 缺分母恒 0） | W-1（采集器未产品化）、W-2（plan_fallback 死缝）、U-1（只测一格）、U-2（n=3 非统计功效） | 下一轮 charter 由本文件读出 |

## 真实 k=3 实测（EC-07 的现场记录）

**六次 run 全部登记**（顺序预先声明 P/A 交替；失败不补跑）。读数见
`.cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json`。

**真跑过程中抓到的三个实现缺陷**（只有真跑才暴露，逐条已修且有判据）：

1. **`TOOL_HEALTH_UNPROVEN` 没有接受通道** ⇒ `freeze_manifest` 拒冻，而拒冻抛出后控制面
   **不落任何事件**（`manifest_digest` 为 null、事件列表为空）⇒ 读面表现为「六次 run 在
   0.4–0.7 秒内秒失败而读不到原因」。处置：走既有 live 判据同一条**显式运维上下文**路径
   （`_live_preflight` 现算 URL 裁决/端点健康/策略面，只把 provider 那一面声明 HEALTHY）。
2. **相 id 必须与出厂检索面瞄准的那个一致**（`RETRIEVAL_PHASE = "retrieval"`）：取名成
   `plan` ⇒ `planned_in_this_phase` 静默跳过 ⇒ run 在合约的 `minimum_retrieved_sources`
   上判拒，归因错位。与 GOAL-113 `F-2` 同一形态（**跳过的路径必须可观测**）。
3. **`assemble(ApiSettings(...))` 不传 `agent_runtime` ⇒ 回落 Fake 执行体**：Fake 只发
   `analysis_report` 这一件事实 ⇒ 探针的 `research_plan` 恒缺 ⇒ run 在验收门判拒。这是
   GOAL-107 `U-1` 的第二面（「组合根缺执行体缝」的姊妹形态：**执行体选择面也不能漏**）。

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- **`W-1` 采集器仍是「判据侧驱动」**：`tests/e2e/paired_ablation_live_support.py` 把六次 run
  汇总成观测，**产品面没有一个「从 run 库自动汇总 k×2」的命令**（GOAL-109 `W-2` 的那一半
  仍未交付）。本轮把它推到了「可用」，不是「可运维」。
- **`W-2` `plan_fallback` 是一条从未被任何 GOAL 登记的死缝**：
  `packages/application/model_relay/fallback.py` 有实现、`ModelProfile.fallback` 被 preflight
  的独立性判据读，但**运行期没有任何时候真的按 fallback 切模型**
  （`adapters/relay/gateway.py` 只有 circuit breaker + retry）。它牵涉评审独立性的穷举结论
  ⇒ 接线要重算那些结论，属另一件事。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **只测「计划」一格**：检索 / 复检 / 迭代三格的 `下一级` 仍无真实读数（机制同构，
  但一格的证据不足以推广）。
- `U-2` **n=3 不是统计功效**：无显著性检验、无方差刻画、无采样控制 ⇒ 只能读「分布位移」，
  不能读「位移的因果方向」。

### 声称边界

- `R-1` **不宣称「模型采纳了前序知识」**：判的是四列**读数**的分布位移；
  正文里那句 `mem-ablation-live-prior` 是 `citation_count` 的证据，不是「采纳」的证据
  （「采纳」仍被 GOAL-082 EC-04 的未决取舍挡着）。
- `R-2` **不宣称消融台是生产协议**：产品面今天不认 `ablation_plan_probe_v1.yaml`
  （检索调用表由装配方给出 —— 产品那份的检索词路径是 `research_question.query`，
  单相简报驱动的探针没有那个字段）。

## 状态历史

- 2026-11-17：建档（charter 由 `next_round_charter.py` 从 GOAL-113 读出）。
- 2026-11-18：EC-01…06 落地 + 判据全绿；真跑抓到并修复三个实现缺陷 + 一个**判据缺陷**
  （`citation_count` 缺分母恒 0，已修并按同一批产物字节重算）；EC-07 六次真实 run 全部
  `SUCCEEDED`、六条可比键逐字相同、三列位移；EC-08/09/10 落地；RECHECK-20261118-114
  `PASS_WITH_WARNINGS`。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。行随收口 chore 提交回填 ——
提交哈希写不进它自己携带的内容，链在下一个提交收敛。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `25fa8887` | [M0 44272246406](https://github.com/Eswink/research-system-new/actions/runs/44272246406) / [Push 44272246485](https://github.com/Eswink/research-system-new/actions/runs/44272246485) | **8/8 job `success`**；Push 3/3 `success` | 代码 + 判据 + 记录（EC-01…10 全部交付）；六次真实 run 的读数见 `evidence/GOAL-20261117-114-ablation-k3.json` |
| `2260b7eb` | 同上（同一批 push 的 tip 读数为准） | 同上 | 记录面收敛：两条台账对齐 + 两处规模门（451→450 行 / `_arm_deps` 拆分）。**M0 真红一条**：`python/tests`——该 chore 主题点名`goal114` ⇒ 提交链判据把它算进本轮，而台账里没有它（连环 tip 债） |
| `453898c8` | 同上（同一批 push 的 tip 读数为准） | 同上 | 子 PLAN + 工程记忆（MEM-244）+ 三个判据文件的 ruff format；同样因主题点名 `goal114` 进入本轮链 |

**本轮的 CI 读数已齐**：五个提交一次推送（`25fa8887`…`f9402826`），GitHub 只为 tip 起 run ——
[M0 44272246406](https://github.com/Eswink/research-system-new/actions/runs/44272246406) **8/8 job `success`**、
[Push 44272246485](https://github.com/Eswink/research-system-new/actions/runs/44272246485) 3/3 `success`。
本台账的回填提交（本次）由下一轮 prep 按惯例登记（见 GOAL-112 / 113 台账尾的同形先例）。
