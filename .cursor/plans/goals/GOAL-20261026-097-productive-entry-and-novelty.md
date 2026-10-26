---
id: GOAL-20261026-097
slug: productive-entry-and-novelty
title: 让产品入口真能跑完整链，并让「创新点」有两面
status: ACTIVE
created_at: 2026-10-26
updated_at: 2026-10-26
owners: [maintainer]
authorization:
  source: user-goal-mode-instruction
  ref: >-
    序 65 / GOAL-20261026-097（用户 goal-mode 指令）。push-to-main-for-CI：只推 main、
    不 force、不重写历史、不推旁支；RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E
    逐命令传，绝不写进 `.env`。
objective: >-
  上一轮（GOAL-096）证明了「方向 → 问题 → 检索 → 立题 → 实验 → 评审 → 报告」在一次 run
  内成立 —— 但**只在 e2e 的手工装配里**。从**产品入口**（真 API，`assemble()` 出来的 deps）
  跑，实验相与报告相会以**点名拒绝**收敛（两道缝缺省 `None`），而「创新点」在域层**结构性
  缺席**（`rg -i novelty packages/ services/ adapters/` 零条；`novelty_reviewer` 是死配置）。
  本轮把这两件事各自补成**可判事实**：(1) 两个产品组合根都接上实验缝与报告缝，且**装配期
  零 Docker 连接**；契约 pin 的 `script`/`image` **真的生效**（此前被静默忽略）；
  (2) 「创新点」有两面 —— 声明面（`novelty` 相 + `novelty_claim` 合约 + 落在检索上的判据）
  与评审面（`novelty_reviewer` 真的被激活、真的收到被评对象、判词引用同一个检索标识）。
exit_criteria:
  - id: EC-01
    criterion: >-
      两个产品组合根都接上实验缝与报告缝，且**装配期零 Docker 连接**。(i) `assemble()` 后
      `experiment_task`/`report_task` 均非 None；(ii) 注入「构造即抛」的后端工厂 ⇒ `assemble()`
      仍成功、首次派发才抛（正反两向）；(iii) PG 根同判（静态判据：两个根都经同一份
      `*_executor_seams`）；(iv) 反证：从 SQLite 根摘掉接缝 ⇒ 判据点名判红。
    verify: tests/api/test_product_roots_carry_the_execution_seams.py（7 条用例）
    status: PASS
  - id: EC-02
    criterion: >-
      从**真 API 入口**跑通六相链：`TestClient(create_app(assemble(...)))` + 真中转站 +
      真 runtime + 真容器 + 装配面 `design_source`，**不经任何测试侧手工 `replace(...)` 补缝**。
      读数落盘到 `.cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt`。
      Docker 不可用 ⇒ `requires_docker` 如实 skip（skip 不是 PASS）。
    verify: tests/e2e/test_productive_entry_runs_the_whole_chain.py + 取证文件
    status: PASS
  - id: EC-03
    criterion: >-
      契约 pin 的 `script`/`image` **真的生效**。两向：(i) 契约 pin ⇒ 跑的是契约那个脚本
      （按压：改契约里的路径 ⇒ 断言随之变）；(ii) 契约空（`experiment: {}`）⇒ 逐字回到装配面。
      反证：摘掉「声明优先」分支 ⇒ 判据点名判红。
    verify: tests/api/test_contract_pinned_experiment_spec_takes_effect.py（9 条用例）
    status: PASS
  - id: EC-04
    criterion: >-
      创新点**两面都在**。(i) 新协议 `direction_to_report_v2.yaml` 七相编译零 ERROR，
      `novelty` 在 `retrieval` 与 `plan` 之间；(ii) 声明的 `nearest_prior` 至少一条命中本 run
      检索证据里真实出现的标识（反证：不存在的标识 ⇒ 判红）；(iii) `novelty_reviewer` 被激活
      （理由逐字 `role is required by protocol`）、`is_reviewer()` 为真、判据面引用同一标识；
      (iv) 新 agent 的执行目标与生产侧、与另两位评审者都不同。
    verify: tests/contracts/test_direction_to_report_v2_novelty.py（14 条用例）
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产齐备：`tools/verify_goal097_closeout.py` + `tools/goal097_closeout_assertions.py`
      在树，登记进 `_VERIFIERS`，且被 `test_terminal_goals_have_closeout_verifiers.py`
      （`_CUTOFF_SEQ = 64` ⇒ 097 自动进入受判面）收录。
    verify: tools/verify_goal097_closeout.py + tests/tooling/ 两条注册判据
    status: PASS
  - id: EC-06
    criterion: >-
      承接上一轮已修正的三处记录（GOAL-096 台账 run 归属 `d683c7d3` 记 `covered_by: 624338c5`、
      `W-1` 的「失败读数在取证文件里」、`W-2` 的因果落点）—— 核对不回退；若别处仍重复旧说法
      则一并改准并写明是哪一版说错了。
    verify: 记录面核对（GOAL-096 正文 + RECHECK + 迭代日志）+ 本轮记录里的更正说明
    status: PASS
budget:
  max_cycles: 14
  per_cycle_minutes: 150
  no_progress_stop_cycles: 2
fix_policy:
  max_same_signature: 3
  forbidden:
    - 改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据
    - 把受判面写成交集或并集掩蔽
    - 收窄受判面而不逐条申报
    - git push --force / 重写历史 / 推非 main
    - 伪造或夸大验证证据（尤其：用补过缝的 deps 冒充产品入口、把 skip 记成 PASS）
    - git add -A
    - 宣称项目安全（R-M1 未收口）
    - 宣称投递语义为「恰好一次」
escalation_triggers:
  - 改产品边界（Domain 写入真实模型厂商 / OpenHands 类型进 Domain）
  - 放宽任何既有判据或动冻结面
  - 改 CI workflow
  - 新增依赖
  - 新增或改 TrustLabel 取值
  - 给 idea.* 加 policy allow 规则（= 改默认 deny 姿态）
  - 定「叙述质量」判定口径
  - 换第三个独立评审模型之外的模型面决策
child_plans:
  - .cursor/plans/tasks/PLAN-20261026-097-goal-097-productive-entry-and-novelty.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261026-097-goal-097-productive-entry-and-novelty.md
memory_entries: []
---

# GOAL-20261026-097：让产品入口真能跑完整链，并让「创新点」有两面

## 目标与退出标准

用户的目标是：**给一个方向，剩下全自动 —— 自动选题、自动设计实验、撰写、自我迭代**。
上一轮交付了「一次 run 走完六相」的机制，但那条机制只在 e2e 的手工装配里成立：从**产品
入口**（真 API）跑，实验相与报告相会点名拒绝。而「创新点」在域层完全没有位置 ——
一项研究**从未被要求说明**它与最近的前人工作差在哪，也**从未被任何模型判过**。

本轮两个靶子：

1. **产品入口可达性** —— 两个组合根接上实验缝 / 报告缝 / 运行链检索面；装配期零 Docker
   连接；契约 pin 的脚本与镜像真的生效。
2. **创新点两面** —— 声明面（新协议 + 新合约 + 落在检索上的判据）与评审面
   （`novelty_reviewer` 真的激活、真的收到被评对象、判词引用同一个检索标识）。

EC-01…EC-06 的判据见 frontmatter；每条都写明「取证形态」与「反证臂」。

## 循环入口协议

每一轮 cycle 的开始状态取三件**可提取**事实（不靠记忆）：

1. 上一轮 cycle 的「剩余差距」列（本文件 `## CI 台账

（**逐提交逐 job**，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是**两种不同**的形态，
分别登记；后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `3748213b` | [M0 40381462122](https://github.com/Eswink/research-system-new/actions/runs/40381462122) / [Push 40381462020](https://github.com/Eswink/research-system-new/actions/runs/40381462020) | Push **success**（三条 Analyze 全 success）；M0 **failure**（5/8 job success，3 job 判红） | 本轮全部交付面：三道执行缝 + 惰性后端 + 声明优先 + 七相协议 + novelty 两面 + 收口资产 + 记录 + 真跑取证。**三个红 job 的归因（都不是宽泛失败）**：① `quality-ubuntu-latest` / `quality-windows-latest` ⇒ **同一签名**：`test_m0_witness_matches_the_tree` 判「见证覆盖的内容与当前树不一致」—— 我在跑完本地 m0 之后又改了受判文件（压缩 `composition.py`、改 `experiment_support.py`、修判据、补记录）⇒ 那次终态行按纪律**作废**。② `collector-quality` ⇒ **真缺陷**：`'_PgRuntimeInputs' object has no attribute 'effective'`（我在 `pg_executor_seams` 里从 `inputs` 取设置面；三条 PG e2e 全红）。已修（改从 `config.effective` 取）+ 新增**静态判据**钉住（本机跑不了 PG ⇒ 本地门看不见这类）。本行先记 `failure`，修完的下一提交另记一行 |

## 残余与未覆盖范围

| 编 | 内容 | 状态与理由 |
| --- | --- | --- |
| `W-1` | **REST provider 在默认装配下的健康探测会出网**（预检 `TOOL_HEALTH_UNPROVEN` 是 WARNING 且**没有接受通道** ⇒ `freeze_manifest` 拒冻）。本轮因此只把出厂检索 provider 接进**运行链执行面**，`ApiDeps.tool_providers`（预检探测面）保持空（与今天逐字一致）；EC-02 的真跑用显式 `preflight_override`（既有运维路径）。 | **不做，需用户拍板**（改接受通道 = 动门禁）。这条语义不一致**在本轮之前就存在**，`examples/protocols/real_retrieval_research_v1.yaml:11-19` 已登记。 |
| `W-4` | **同步执行路径只在会话开始前心跳一次**（`task_executor._attempt_once`）：真实会话超过 `lease_ttl_seconds`（缺省 300s）后，租约被 `recover_expired_leases` 回收 ⇒ 下一次心跳抛 `no matching lease for task` ⇒ 冒到 HTTP 层是 **422**（一次 run 的内部失败被报成「请求不合法」）。本轮把 TTL 做成**可配**（`ApiSettings.workflow_lease_ttl_seconds`，缺省 300 逐字不变），真跑用 3600；**执行语义与错误映射未改**。 | 真缺陷，**根因未修**（要改 `_attempt_once` 的会话期心跳 + 错误映射，属产品行为变更，需拍板）。本条如实登记。 |
| `W-2` | **出厂检索调用的 `phase_id` 是常量 `"retrieval"`**：一个把检索格取名成别的 id 的协议**不会**在该相执行检索。 | 如实登记。本轮四份出厂协议的检索格都叫 `retrieval`；按协议解析调用归属属新机制，不在本轮射程。 |
| `W-3` | **实验脚本仍是预置脚本之一**：契约能 pin 脚本/镜像（EC-03 已生效），但脚本本身**不是为新问题生成的实验**。 | 下一轮候选（用户已点名）。 |
| `U-1` | 「创新」是否**真的新**未判：`nearest_prior` 只判「那一条标识在本 run 的检索结果里真实出现」，**不**判「它真的是最接近的前人工作」。 | 需人评或外部检索对照；本轮判的是**可机械判的那一半**。 |
| `U-2` | 叙述质量与事实一致性仍无判据（承 GOAL-096 `U-1`）。 | 未获授权定义「叙述质量口径」。 |
| `U-3` | `idea.review` / `idea.write` 在词表里而无 policy allow ⇒ 任何协议把它们写进 `required_capabilities` 都会让差集判据判红。本轮的 novelt 角色**只用已放行的读能力**。 | 加 allow = 改默认 deny 姿态 ⇒ 需用户拍板。 |
| `R-1` | `R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。 | — |
| `R-2` | 投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。 | — |
| `R-3` | GOAL-096 的 `W-1`（CI 浅克隆）、`W-3`（090/095/076 验证器不回填）状态不变。 | — |

## 迭代日志

`）；
2. `git status --porcelain` 的**非受判**脏文件（他方 4 个 CRLF 文件，不动不提交）；
3. 本文件 `## 状态历史` 最后一行写下的**下一步**。

判断面（本轮该做什么）由我在这里写；不做「读上一轮报告后手抄」那一步 —— 那一步的产物
就是序 60 交付的读取器（`tools/next_round_charter.py`）。

**本轮读取器读数**：`REFUSED RESIDUAL_EMPTY`。理由已取证：GOAL-096 的
`## 残余与未覆盖范围` 写成了**表格**（`| \`W-1\` | … |`），而读取器的
`_W_ITEM`（`tools/charter_parse.py:39`）只认列表项 `- **\`W-1\`**`。按本轮指令：**记录拒绝码
与理由，改以 GOAL-096 正文残余节为准，不为让读取器通过而改写历史记录**。GOAL-096 的
`W-1`/`W-2` 文本在 `7189b498` 已更正，下面按更正后的版本处置。

**GOAL-096 残余逐条处置**：

| 残余 | 处置 | 理由 |
| --- | --- | --- |
| `W-1`（首两次真跑被限流；失败读数只在三份记录里，取证文件只承载通过那次） | **承接**：本轮 EC-02 的取证文件同时记录**失败路径**（先写盘再断言），使「失败读数在取证文件里」这条口径对 097 成立；096 的历史不追改 | 记录文本已在 `7189b498` 更正为准确表述；本轮的写法是**修机制**而不是改旧记录 |
| `W-2`（跨相性质标签过宽：被推成 `RETRIEVED` 的是 `review` 消费的 `plan:research_plan` 边） | **不做**（改性质语义需拍板） | 补偿：检索「真的发生」由 provider 收到的参数逐字取证 |
| `W-3`（`tools/verify_goal{076,090,095}_closeout.py` 仍不存在） | **不做**（不回填） | 回填等于把今天的要求追认成历史义务；跨 GOAL 判据的祖父条款 `_CUTOFF_SEQ = 64` 只兜本轮及以后 |

## 单 cycle SOP

1. **勘察取证**：任何「已实现 / 未实现」的判断先落 `rg` 读数（`rg -n`，不用 `-r`）。
2. **先量规模**：动 `services/` 与 `packages/` 之前先 `wc -l`；450 行硬上限、50 行函数门
   是**每次**都要过的门（本轮 `composition.py` 一次就撞到）。
3. **判据先写反证臂**：每条新判据至少一个「按掉实现就判红」的按压，且按压在**真文件**上做。
4. **记录顺序**：写全部记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 →
   最后跑 `tools/run_m0_with_witness.py` → 之后不再 `git add` 任何受判文件 → 提交推送。
5. **一个 cycle 一次推送**（`cancel-in-progress` 会取消在飞的 M0 run）。

## CI 失败分类与纠错

- **(i) 真缺陷**：改实现（不改判据）。
- **(ii) 资源阈值型**：`RSS < 128MiB` 一类判据偶发红 ⇒ `rerun-failed-jobs`，**绝不动阈值**。
- **(iii) 基础设施**：Docker registry / 中转站限流 ⇒ 如实记录，重跑；不改代码。
- **(iv) 判据自身时序**：如 `evolution_state.json` 的 `WinError 5` ⇒ 单跑取证后独占重跑。

同一失败签名超过 `fix_policy.max_same_signature` ⇒ 停 BLOCKED 并写清被堵的路。

## 终止与收口

- **ACHIEVED**：六个 EC 全达成 + 真跑取证 ⇒ 跑
  `tools/two_tree_recheck.py --script-mode shared`（两树判词逐行 + `sha256` 相同）⇒
  归档判词进树 ⇒ 写收口报告与 RECHECK。
- **以下不是失败，是有效读数**：Docker 不可用（EC-02 如实 skip，EC-01 仍须成立）；novelty
  评审面被结构性堵住（只做到声明面，**如实登记那一面未达成**）；读取器拒绝残余（记拒绝码）。
- **BLOCKED**：撞 `escalation_triggers` / 同一签名超上限 / `max_cycles` 触顶 / 连续 2 轮未推进
  任何 EC / 需用户拍板（改 TrustLabel、放宽判据、动冻结面、改 workflow、新增依赖、给
  `idea.*` 加 policy allow、定叙述质量口径、换第三个独立评审模型）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261026-097 | `3748213b`（收口提交见下一行/台账） | 判据 9 + 9 + 15 全过；真跑 **1 passed**（`SUCCEEDED`，七相全落库）；m0 见证待跑 | 见「CI 台账」 | 真跑过程中修掉 **3** 个产品缺陷：① 运行链调用未标 `phase_id` ⇒ 问题相也执行检索并失败；② 检索格合约没告诉模型「检索已跑完、本相没有工具」⇒ 模型去探索仓库、不产块；③ 会话工具面缺 `literature.*` 实现 ⇒ 评审相 `ToolDefinition ... is not registered`；另把任务租约 TTL 做成**可配**（同步路径只心跳一次、真实会话常超 300s） | `W-1` REST provider 探测出网（预检拒冻，需拍板）；`W-2` 检索 `phase_id` 是常量；`W-3` 实验脚本仍预置 | 下一轮：让实验脚本也由方向决定；检索结果驱动下一轮问题 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-26 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 65）。读取器 `REFUSED RESIDUAL_EMPTY`（GOAL-096 残余节写成表格，读取器只认列表项）⇒ 记拒绝码、改以正文为准逐条处置。`max_cycles: 14`。 |
