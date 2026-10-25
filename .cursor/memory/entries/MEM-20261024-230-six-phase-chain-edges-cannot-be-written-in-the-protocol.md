---
id: MEM-20261024-230
title: "六相链的两条边在协议里写不出来：执行体声明位决定 inputs 能不能声明"
status: ACTIVE
created_at: 2026-10-25
updated_at: 2026-10-25
scope: repository
confidence: 0.95
review_after: 2027-04-25
source_plans:
  - .cursor/plans/tasks/PLAN-20261024-096-goal-096-direction-to-report-in-one-run.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261024-096-goal-096-direction-to-report-in-one-run.md
supersedes: []
tags: [cross-phase-inputs, protocol-compile, experiment-design, report-facts, objective, goal-096, first-failure-then-pass]
---

## 做了什么

**三件**，都做成可判：

1. **六相协议** `examples/protocols/direction_to_report_v1.yaml`
   （question → retrieval → plan → experiment → review → report）：一次 run 走完
   方向 → 问题 → 检索 → 立题 → 实验 → 评审 → 报告。
2. **报告第 1 节站在本 run 自己的问题上**：新模块
   `packages/application/run_orchestration/report_question.py`，从**本 run 证据投影**里找
   `:research_question` 制品，信封形态取模型声明块的**原文切片**、直形态取制品原文。
3. **收口资产不再靠人记**：`tools/verify_goal096_closeout.py` + 断言集 +
   **跨 GOAL** 判据 `tests/tooling/test_terminal_goals_have_closeout_verifiers.py`。

## 为什么这样做

- **链真的断了**（建档实测）：23 份协议里**没有一份**同时含 `question` 与 `experiment` 相
  —— `direction_to_question_v1` 止于 `retrieval_report`，`research_report_chain_v1` 从手写
  `input-brief:real_research_v1` 起步 ⇒ 没有一次 run 走过完整链。用户要的「给方向 → 选题 →
  设计实验 → 跑实验 → 写报告」在产品面上**不可达**。
- **报告第 1 节恒空**：`report_facts.report_inputs` 把 `objective=None` 写死 ⇒ 那一节永远
  是「（无：本 run 未声明目标）」。报告因此从不体现「这一轮在研究什么问题」。
- **收口验证器靠人记**：`tools/verify_goal{076,090,095}_closeout.py` **从未存在**，而分类
  判据只查「磁盘上存在的验证器是否被分类」⇒ 缺失文件**两头都不报**。这件固定交付一直是
  人的责任，没有任何判据兜住。

## 可复用的坑

1. **`experiment` / `report` 两相在协议里写不出跨相 `inputs`**：编译门
   `_executor_consumes_declared_inputs` 按**合约的声明位**（`report` / `experiment` 非空）
   判执行体不消费声明输入 ⇒ 写了会被点名拒绝（理由逐字：「the declaration would be a
   source the gate counts and nobody reads」）。**这两条边只能经装配面**
   （`design_source="plan"`）**与 canonical 读面**（`report_facts`）。
2. **`workspace.read` 的连带效应**：六相协议的冻结集比两相版**多一件**
   `openhands_workspace`（立题/评审相声明了 `workspace.read`）⇒ 别的 run_chain 相若不
   一并声明它，它会**漏进会话工具面**而没有注册实现（实测判据红：`('openhands_workspace',) == ()`）。
3. **`objective` 的来源变了要同轮改文案**：旧文案写「目标（来自协议/合约声明）」，
   接通后那句会变成**假话** ⇒ 两处渲染器（确定性汇编 + 模型叙述）必须同轮改口径。
4. **真跑失败要分面归因**：`litellm.RateLimitError: Channel rate limit reached for model`
   属**模型通道可用性**面 —— 离线 e2e 六例在同样装配下全绿即证明链路本身成立。
   「先失败后通过」的两次读数都留在取证文件里，**不抹平**。
5. **继承性判据的盲区**：分类判据只查「磁盘上存在的验证器是否被分类」⇒ 缺失的验证器
   不在任何清单里，**两头都不报**。修法是新增**遍历树**的判据（受判面从程序表 +
   frontmatter 推出），并带空真守卫（`受判面为空 ⇒ 点名判红`）。

## 射程边界（本记忆**不**声称的）

- **不**声称「六相链在真实条件下已达生产质量」：live 通过一次是机械事实，不是质量结论。
- **不**声称问题提得好 / 计划科学 / 评审公正 —— 那要人评、评审面或叙述质量口径
  （后者定口径需用户拍板）。
- **不**声称 `plan` 产物的 `RETRIEVED` 标签是对的（承 GOAL-089 `W-4` 的过宽推导，未改）。
- **不**声称 090/095/076 的验证器缺口已修（只登记，不回填）。

## 怎么做与复现

```bash
# 1) 协议结构（六相 + C-1 + 兄弟协议未改）
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_direction_to_report_protocol.py -q
# 2) 跨相边两向（机制层）
uv run --frozen --no-sync python -B -m pytest   tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py -q
# 3) 报告第 1 节读取面
uv run --frozen --no-sync python -B -m pytest   tests/application/run_orchestration/test_report_question_objective.py -q
# 4) 编排级六相（真容器；Docker 要在跑）
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_direction_to_report_arc_offline.py -q
# 5) 真跑（凭据只由操作者注入；逐命令传开关）
set -a; . ./.env; set +a
RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1   uv run --frozen --no-sync python -B -m pytest tests/e2e/test_direction_to_report_live.py -q -rs
# 6) 跨 GOAL 收口资产覆盖（空真守卫在其中）
uv run --frozen --no-sync python -B -m pytest   tests/tooling/test_terminal_goals_have_closeout_verifiers.py -q
```

**按压（判据真的会咬）**：宪章程序表**尚未**登记序 64 时，第 6 条判红并点名
`受判面为空（下界序 64）⇒ 本条失去判据对象`；从 `_VERIFIERS` 撤掉 096 ⇒ 「未分类」
分支点名。两次按压后按 raw `sha256` 逐字节复原。

## 适用边界

- 适用：在本仓新增**多相协议**、新增**跨相边**、或让报告 / 实验读**上游产物**时。
- 适用：新增任何 `packages/` 下的读取面时 —— 先查规模线（`report_task.py` 433/450、
  `report_facts.py` 260），贴线就**新开模块**，不要压缩既有注释。
- 不适用：改 `TrustLabel` 语义、改叙述质量口径、回填历史 GOAL 记录 —— 都需用户拍板。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261024-096-goal-096-direction-to-report-in-one-run.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261024-096-goal-096-direction-to-report-in-one-run.md`
- 真跑读数：`.cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt`
- 协议：`examples/protocols/direction_to_report_v1.yaml`
- 读取面：`packages/application/run_orchestration/report_question.py`
