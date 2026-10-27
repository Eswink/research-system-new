---
id: GOAL-20261027-098
slug: independent-novelty-and-derived-experiment
title: 拆开创新点的作者与评审者，并让实验脚本由计划选择
status: ACHIEVED
created_at: 2026-10-27
updated_at: 2026-10-27
owners: [maintainer]
authorization:
  source: user-goal-mode-instruction
  ref: >-
    序 66 / GOAL-20261027-098（用户 goal-mode 指令）。push-to-main-for-CI：只推 main、
    不 force、不重写历史、不推旁支；RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E
    逐命令传，绝不写进 `.env`。
objective: >-
  序 65 跨过了「产品入口能跑」这道门；本轮修的是**质量**与**自主性**的两处结构性缺陷。
  (1) **自评**（实测，不重新推导）：`direction_to_report_v2.yaml` 的 `novelty` 相与 `review` 相
  **都**点名 `novelty_reviewer`，而 `protocol_compile` 的解析面（`resolution.py` 的
  `agent_candidates` / `assignments.py` 的 `phase_assignments` / `selection.py` 的
  `select_agents`）**只按 `agent.role == role_id` 取候选、不看 phase** ⇒ 同一角色在两相
  **必然**选到同一个 agent 实例（`novelty_a` / `minimax-m3`）⇒ `review` 相那两个
  `review_decision` 里有一个是「评审自己刚写的声明」，而复述是**结构必然**（`novelty_claim`
  本来就在它的提示词里），不构成独立认可。修法：新增专用作者角色 `novelty_author`
  （agent `novelty_writer`，第四个底层模型）⇒ 两个面的角色 id / agent id /
  `(endpoint, model_name)` **三者都不同**，且判据**跨协议**判「评审者不得评自己写的产物」。
  (2) **选择级派生**：实验脚本此前由装配常量决定（`DEFAULT_EXPERIMENT_SCRIPT`），
  `design_source="plan"` 只派生臂与参数 ⇒ 换方向换多少次跑的都是同一个脚本。本轮按用户
  拍板走 **(b) 白名单选择**：计划可以在**出厂脚本闭集**里点一个，真跑用的就是它；越界一律
  点名拒绝。**(a)「模型为新问题写实验脚本」登记为下一轮待拍板**（模型产出的 Python 进容器
  属安全面变更）。
  (3) 顺带补齐三处归档面既有漏洞（承 GOAL-096 `U-3` / GOAL-097）：`progress-075` 无宪章
  链接、10 条 4 格历史修订行未处置、`verify_goal{076,090,095}` **从未存在**。
exit_criteria:
  - id: EC-01
    criterion: >-
      `novelty` 相的作者与 `review` 相的评审者**结构上不同**：(i) 角色 id 不同
      （`novelty_author` ∉ `review` 相评审者集合）；(ii) 作者角色**不是** `REVIEWER`
      面板角色（`is_reviewer()` 为假 ⇒ 被评对象不进它的提示词）；(iii) 两相解析到的
      **agent id 不同**；(iv) `(endpoint, model_name)` 也不同（只判 id 会漏「换个名字
      同一个模型」）；(v) **跨 28 份出厂协议**遍历：「某相的评审者不得同时是它评审的那件
      产物的作者」。反证：把作者角色改回 `novelty_reviewer`（真文件）⇒ 判据点名判红，
      按 raw `sha256` 逐字节复原。
    verify: tests/contracts/test_direction_to_report_v2_independence.py（18 条用例）
    status: PASS
  - id: EC-02
    criterion: >-
      **真跑**证明两面独立：`novelty_claim` 的作者与评审它那位的 `reviewer_model` 不同，
      且取证里每个 `review_decision` 都能归因到具体 agent（`reviewer_model` 非空且可区分）。
      反证：改回同一角色 ⇒ 判红（结构面已由 EC-01 判，本 EC 判**运行期读数**）。
      **第四/第五模型凭据不可用 ⇒ 如实登记未达成，不用同一个模型凑。**
      **本轮实测读数**：两次真跑都停在**检索相**（`run-chain capability step failed:
      europe pmc temporarily unavailable`，两次同签名）；独立 `curl` 探针显示该服务
      **连最简单的查询也 503** ⇒ 上游不可用，不是本判据的查询形态问题。产品接线刻意只接
      Europe PMC（理由在 `retrieval_wiring.py` 的 docstring 里）⇒ **不**为让判据变绿而改
      接线。⇒ `review_row_count=0`，评审相从未执行 ⇒ 本 EC **无运行期读数**，保持 `PENDING`。
      结构面（EC-01）已判；运行期面等上游恢复后一条命令补取证。
      **上游恢复后已达成**（`run_id=783e6dc7-30fa-48cd-a1c5-4b34d9c7a6ef`，`state=SUCCEEDED`）：
      `review_row_count=2`，两条 `review_decision` 的 `reviewer_model` 分别是
      `main/glm-5.3`（`gate:reviewer_a`）与 `main/minimax-m3`（`gate:novelty_a`），
      `reviewers_with_no_model=[]`；`novelty_claim` 制品的 `created_by=novelty_writer`
      （作者的 agent id）**不在**两位评审者之列，作者的执行目标
      `main/deepseek-v4-pro-0813` 也不在 `reviewer_models` 里。
      **这一轮的真跑另外抓到一个真缺陷**：`novelty_claim_step.with_novelty` 的判负路径读
      `GateOutcome.verdicts`（字段名是 `evaluations`，`passed` 是只读 property）⇒ 任何一次
      创新点判负都会抛 `AttributeError`。此前从未暴露，因为判负要先跑完检索，而前两次真跑都
      停在检索相。已修 + 判据 `tests/contracts/test_novelty_rejection_turns_the_gate_red.py`
      （8 例，含真文件按压）。
    verify: 真跑取证落 `.cursor/plans/goals/evidence/GOAL-20261027-098-ec02-novelty-independence-run.txt`
    status: PASS
  - id: EC-03
    criterion: >-
      **实验脚本由计划选择**（方案 (b) 白名单）：(i) `experiment_design.script` 从出厂闭集
      里点名 ⇒ 真跑交给沙箱的就是那个脚本（判 `assembly.script`，即被复制进工作区的文件）；
      (ii) 同一装配 + 两份计划 ⇒ 两次派发跑**不同**脚本；(iii) 零回归：没写 `script` ⇒
      **逐字**回到装配面那一个；契约 pin 仍最强（三档优先级）；(iv) 白名单外 / 绝对路径 /
      `..` / 盘符 / 非字符串 ⇒ **点名拒绝**（不静默回落）。反证：删掉
      `plan_selected_script` 那一行调用（真文件 + 子进程）⇒ 行为判据真的判红，按 raw
      `sha256` 逐字节复原。
      **(v) 容器面**（收口前补齐）：派发面判的是 `assembly.script` 这个**输入**，容器读数是
      **输出** —— 只判派发面时，「复制脚本进工作区」那一步出偏差判据会照绿。⇒
      `tests/e2e/test_experiment_script_selection_docker.py`（`requires_docker`）让计划分别点名
      两个脚本各跑**一次真容器**，再按**脚本各自的签名指标**判跑的是哪一个
      （去重：`duplicates_found`；排序：`worst_case_comparisons`）。取证在
      `evidence/GOAL-20261027-098-ec03-container-run.txt`（真镜像摘要 + 各自的指标集）。
      并加一条判据 `ec03-no-dangling-evidence-reference`：docstring 点名了取证文件，
      该文件就必须在树（悬空引用比没写更坏 —— 读起来像取证已存在）。
    verify: tests/application/test_experiment_script_comes_from_the_plan.py（17 条用例）+ 容器面
    status: PASS
  - id: EC-04
    criterion: >-
      归档面三件：(i) `archive/MAINLINE-2026-10-15-progress-075-only.md` 补上宪章链接
      （此前**完全没有**链接 ⇒ 不参与「不漏 / 不重」，因为 `_archive_paths` 只认
      `](archive/...)`）；(ii) 历史归档里的 **10 条 4 格修订行逐条处置** —— 结论是
      **保留 4 格、不补**（原文把「替换为」与「理由」写进同一格，其中 5 份文件自声明不再
      改动；补第 5 格须自定断句 = 编造列边界）⇒ 登记进
      `archive/SHORT-REVISION-ROWS.md` + 双向判据；(iii) `tools/verify_goal{076,090,095}
      _closeout.py` 三个**从未存在**的验证器 + 断言集补建、登记进 `_VERIFIERS` 与
      `IN_SCOPE`、判词跑通。**回填是补齐历史，不是过门禁**（`_CUTOFF_SEQ = 64` 让它们
      不判红；076 的 GOAL 状态是 `PAUSED`、那 10 条长度界从未加进去 ⇒ 它的断言集判的是
      「记录与树一致（未做仍是未做）」）。
    verify: tools/verify_goal{076,090,095}_closeout.py（48/51/54 条判词）+ 两条归档判据
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产齐备：`tools/verify_goal098_closeout.py` + `tools/goal098_closeout_assertions.py`
      在树，登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的
      `_VERIFIERS` 与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`，
      判词跑通（含自指「加载自己那份断言集」）。
    verify: tools/verify_goal098_closeout.py --root . --verdict-only
    status: PASS
  - id: EC-06
    criterion: >-
      **预算长期化**：`max_goals` **70 → 100**，且 `## 修订记录` 里逐行登记扩表
      （原文读数 70 + 新读数 100 + 本轮已用 66 + 理由）。**不删键**（判据要求它存在且为
      正整数）。若后续仍需更多 ⇒ 继续扩，不设上限。
    verify: tests/tooling/test_mainline_program_is_intact.py + 宪章预算行读数
    status: PASS
  - id: EC-07
    criterion: >-
      **上一轮的记录缺陷已修，本轮核对不回退**：序 65 的修订行从 3 格补成 5 格并搬入归档
      （`archive/MAINLINE-2026-10-26-revisions-65-only.md`）；「活跃面修订行 <5 格即判红」的
      判据 `test_no_revision_row_in_the_live_table_is_too_short_to_be_seen` 在树且带反证臂；
      本轮追加的修订行**必须是 5 格**；别处若还有短行 ⇒ 按 EC-04(ii) 处置（本轮已找到
      历史归档的 10 条并登记）。
    verify: tests/tooling/test_mainline_archive_is_continuous.py + 本文件「修订记录」行格数
    status: PASS
budget:
  max_cycles: 20
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
    - 伪造或夸大验证证据（**尤其**：用同一个模型冒充「独立评审者」、把 skip 记成 PASS、
      把「不可修复的短行」硬补成编造内容）
    - git add -A
    - 宣称项目安全（`R-M1` 未收口）
    - 宣称投递语义为「恰好一次」
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新增第三方依赖或上游版本 pin 变更
  - 改 CI workflow
  - 给 idea.* 加 policy allow
  - 模型写代码进容器（方案 (a)）
  - 定「叙述质量」判定口径
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261027-098-goal-098-independent-novelty-and-derived-experiment.md
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261027-098-goal-098-independent-novelty-and-derived-experiment.md
memory_entries:
  - .cursor/memory/entries/MEM-20261028-232-half-covered-judges-read-as-green.md
---

# GOAL-20261027-098 — 拆开创新点的作者与评审者，并让实验脚本由计划选择

## 目标与退出标准

| EC | 标准（摘要） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 作者 ≠ 评审者：角色 / agent / `(endpoint, model_name)` 三者都不同 + 跨协议自评扫描 | `tests/contracts/test_direction_to_report_v2_independence.py`（18 例）+ 按压 | **PASS** |
| EC-02 | **真跑**：作者与评审者 `reviewer_model` 不同、每个判词可归因 | 取证文件：`783e6dc7` SUCCEEDED，两条判词 = `main/glm-5.3` + `main/minimax-m3`，作者 `novelty_writer` 不在其中 | **PASS** |
| EC-03 | 实验脚本由计划**选择**（白名单）+ 三档优先级 + 点名拒绝 | `tests/application/test_experiment_script_comes_from_the_plan.py`（17 例）+ 子进程按压；**容器面** `test_experiment_script_selection_docker.py`（两个脚本各一次真容器，按签名指标区分） | **PASS** |
| EC-04 | `progress-075` 补链 + 10 条短行逐条登记 + 三个验证器补建登记 | `tools/verify_goal{076,090,095}_closeout.py` + 两条归档判据 | **PASS** |
| EC-05 | `verify_goal098` + 断言集 + 登记 + 判词跑通 | 收口验证器 99 条判词全过 | **PASS** |
| EC-06 | `max_goals` 70 → 100 + 修订记录登记扩表 | 宪章预算行 + 程序表判据 | **PASS** |
| EC-07 | 序 65 记录缺陷不回退 + 本轮修订行 5 格 | 归档判据 | **PASS** |

## 循环入口协议

每一轮 cycle 的开始状态取三件**可提取**事实（不靠记忆）：

1. 上一轮 GOAL 的「残余与未覆盖范围」（本文件 `## 残余与未覆盖范围`）；
2. 迭代日志最后一行的「下一轮输入」；
3. 工作树 / 远端实况（`git status`、`git log --oneline -5`）。

**本轮开场的读取器读数**：`tools/next_round_charter.py` 对 GOAL-097 **`REFUSED RESIDUAL_EMPTY`**
（该轮的残余节写成**表格**，读取器只认列表项 `W-NN`）。按纪律记拒绝码，改以 GOAL-097 正文
「残余与未覆盖范围」逐条处置 —— **不**为让读取器通过而改写历史记录。

## 单 cycle SOP

1. **勘察取证**：任何「已实现 / 未实现」的判断先落 `rg -n` 读数（不用 `-r`，那是替换）。
2. **先量规模**：动 `services/` 与 `packages/` 之前先 `wc -l`；450 行硬上限、50 行函数门
   是**每次**都要过的门（本轮 `experiment_support.py` 一度 450/450 ⇒ 靠压缩三行注释换回）。
3. **判据先写反证臂**：每条新判据至少一个「按掉实现就判红」的按压，且按压在**真文件**上做；
   **按压后必须确认判据真的红了**（本轮两次踩到「按压工具自己有 bug」：`monkeypatch` 改不了
   已导入的字节码、`pytest` 目标名少了类名 —— 两次都是靠「按压后仍绿」发现的）。
4. **记录顺序**：写全部记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 →
   最后跑 `tools/run_m0_with_witness.py` → 之后不再 `git add` 任何受判文件 → 提交推送。
5. **一个 cycle 一次推送**（`cancel-in-progress` 会取消在飞的 M0 run）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| (i) 真缺陷 | job 报 ruff / eslint / tsc / mypy / pytest 断言 | 改**实现**（不改判据）→ fix commit → 重推 |
| (ii) 资源阈值型 | `RSS < 128MiB` 一类偶发红 | `rerun-failed-jobs`，**绝不动阈值** |
| (iii) 基础设施 | Docker registry / 中转站限流 / runner 挂 | 如实记录，重跑；不改代码 |
| (iv) 判据自身时序 | 如 `evolution_state.json` 的 `WinError 5` | 单跑取证后独占重跑 |

同一失败签名超过 `fix_policy.max_same_signature` ⇒ 停 BLOCKED 并写清被堵的路。

## 终止与收口

- **ACHIEVED**：七个 EC 全达成 + 真跑取证 ⇒ 跑 `tools/two_tree_recheck.py --script-mode shared`
  （两树判词逐行 + `sha256` 相同）⇒ 归档判词进树 ⇒ 写收口报告与 RECHECK。
- **以下不是失败**：中转站限流（如实记录）；Docker 不可用（`requires_docker` 如实 skip，
  **skip 不是 PASS**）；第四个模型凭据不可用（EC-02 如实登记未达成）；读取器拒绝（记拒绝码）。
- **BLOCKED**：撞 `escalation_triggers` / 同一签名超上限 / 需用户拍板（改 TrustLabel、
  放宽判据、动冻结面、改 workflow、新增依赖、给 `idea.*` 加 policy allow、
  **模型写代码进容器**、定叙述质量口径）。

## 残余与未覆盖范围

- `W-1`｜**同步执行路径只在会话开始前心跳一次**（`task_executor._attempt_once`）：真实会话
  超过 `lease_ttl_seconds`（缺省 300s）后租约被回收 ⇒ 下一次心跳抛 `no matching lease` ⇒
  HTTP 422。本轮把 TTL 做成可配（`workflow_lease_ttl_seconds`，缺省 300 逐字不变），真跑用
  3600；**执行语义与错误映射未改**。属产品行为变更，需拍板。
- `W-2`｜**出厂检索调用的 `phase_id` 是常量 `"retrieval"`**：一个把检索格取名成别的 id 的
  协议**不会**在该相执行检索。按协议解析调用归属属新机制，不在本轮射程。
- `W-3`｜**方案 (a) 未做**：让模型为新问题**写**实验脚本并在沙箱里跑它。那是**安全面变更**
  （模型产出的任意 Python 进容器；`policy` / `classify_risk` / `EXECUTE` 类 HIGH 的既有门
  **没有**覆盖「这类产物」，不是「门不够严」而是「它不在受判面里」）⇒ 需用户拍板。本轮只
  做到**选择级**（(b) 白名单）。
- `W-4`｜**076 的交付面从未完成**：GOAL-20261014-076 的状态是 `PAUSED`，那 10 条查询参数的
  显式长度界**从来没有**加进去（实测 `services/api/routers/` 只有 `operations.py` 的两处
  `max_length=10`，正是建档时已有的那两条）。本轮补的是它的**记录面**（判「未做仍是未做」），
  **不是**补它的实现。
- `W-5`｜**上游抖动会让真跑偶发失败**（**已不再阻塞 EC-02**）：本轮 5 次真跑里，2 次停在
  检索相（Europe PMC 503，`curl` 连 `query=cancer` 也 503 ⇒ 服务级）、1 次 `retry budget
  exhausted`（模型侧重试预算）。第 4 次在服务恢复后 **SUCCEEDED** 并取证成功；取证写出面
  已改成**追加**（此前一次抖动把成功的读数盖掉了 —— 「留存证据」被「最后一次尝试」替换）。
  残余口径：**EC-02 已达成**，但「真跑能否一次成功」依赖上游可用性，属既有环境事实。
- `U-1`｜「创新」是否**真的新**未判：`nearest_prior` 只判「那条标识在本 run 的检索结果里
  真实出现」，**不**判「它真的是最接近的前人工作」。需人评或外部检索对照。
- `U-2`｜叙述质量与事实一致性仍无判据（承 GOAL-096 `U-1` / GOAL-097 `U-2`）。未获授权定义口径。
- `U-3`｜`idea.review` / `idea.write` 在词表里而无 policy allow ⇒ 新增的 `novelty_author`
  只用**已放行**的读能力。加 allow = 改默认 deny 姿态 ⇒ 需拍板。
- `R-1`｜`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- `R-2`｜投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- `R-3`｜**`novelty_author` 的能力面不含 `idea.write`**：写声明的产物面走会话交付物通道
  （`artifact.read` 同一个 provider），不是 `idea.write` 那条词表能力。这与「作者能写声明」
  不矛盾，但**不能**读成「`idea.write` 已被放行」。

## CI 台账

（逐提交逐 job，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是两种形态，分别登记；
后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `a93b59a6` | [M0 40480147706](https://github.com/Eswink/research-system-new/actions/runs/40480147706) / [Push 40480147542](https://github.com/Eswink/research-system-new/actions/runs/40480147542) | **全 `success`**：M0 **八 job 全 success**（含 `quality-ubuntu-latest` / `quality-windows-latest` / `collector-quality` / `container-quality`）、Push 三条 Analyze 全 `success` | 本轮唯一一段交付（一 cycle 一推送）：EC-01/03/04/05/06/07 的实现 + 判据 + 三个回填验证器 + 全部记录 + 宪章记账 + 10 条短行处置。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False`。**第一版**（同一提交的前一次本地 m0）曾以 `FAILED: 1 check(s): python/typecheck=1` 收敛 —— 5 条**真缺陷**（新文件里的 `getattr` 默认值类型、`EvidenceRelation.relation` 传了 `str` 而非枚举、缺类型注解、`review_read` 的返回值是 `object`）→ 修完 mypy `Success: 1343 source files` → 重跑全绿。**CI 逐字也是绿的** ⇒ 两类门在这一点上一致 |
| `ee8ff147` | [M0 40485214785](https://github.com/Eswink/research-system-new/actions/runs/40485214785) / [Push 40485214810](https://github.com/Eswink/research-system-new/actions/runs/40485214810) | **全 `success`**：M0 八 job 全 success、Push 三条 Analyze 全 success | 台账补记 + 重封见证（只改记录 + 见证）。**它当时是 HEAD ⇒ 结构例外**；含本行的下一个提交把它推离 HEAD 后，反方向判据会点名 —— 那一刻按点名补记 |
| `1310dee4` | [M0 40495440782](https://github.com/Eswink/research-system-new/actions/runs/40495440782) / [Push 40495439360](https://github.com/Eswink/research-system-new/actions/runs/40495439360) | **全 `success`**：M0 八 job 全 success、Push 三条 Analyze 全 success | E**C-02 的真跑抓到第 8 个真缺陷**：`with_novelty` 的判负路径读不存在的 `GateOutcome.verdicts` ⇒ 任何一次创新点判负都会抛 `AttributeError`。已按真实形状重建（追加 `CriterionEvaluation` + 复用 `_gate_outcome`）+ 8 例判据（含真文件按压：改回旧写法会让 5 条以同一个 `AttributeError` 判红）。**CI 逐字全绿** ⇒ 这条修复确实过门 |
| `8ae07bca` | 零 run（**`covered_by: 1310dee4`**） | 覆盖：同批推送被合并进 `1310dee4` 那条 run（全 `success`） | GOAL → **ACHIEVED** 的收口记录（只改记录）：七个 EC 全 PASS、EC-02 五轮真跑过程如实记账、`latest_recheck` 指向本轮 RECHECK。**当时它是 HEAD ⇒ 结构例外**；下一个提交把它推离 HEAD 后按反方向判据点名补记 —— 本行即该补记 |
| `b63b834e` | 零 run（**`covered_by: 1310dee4`**） | 覆盖：与 `1310dee4` 同批推送 | 台账补 `1310dee4` / `8ae07bca` 两行 + 迭代日志 `commits` 格同步 + 重封见证（只改记录 + 见证） |
| `93db3c5e` | [M0 40504946440](https://github.com/Eswink/research-system-new/actions/runs/40504946440) / [Push 40504946437](https://github.com/Eswink/research-system-new/actions/runs/40504946437) | **全 `success`**：M0 八 job 全 success、Push 三条 Analyze 全 success | **两树判词归档进树 + 重封见证**（`TWO-TREE PASS`：两棵各 101 条判词、`sha256` 相同 `a990c129…`）。归档是受判文件 ⇒ m0 在它们落盘**之后**跑 |
| `c746d3fb` | [M0 40510561050](https://github.com/Eswink/research-system-new/actions/runs/40510561050) / [Push](https://github.com/Eswink/research-system-new/actions/runs?head_sha=c746d3fb) | Push **success**；M0 **run 级结论 = `cancelled`，但八个 job 逐条 `success`** | **如实登记这个形态**（不是绿、也不是红）：第一次 attempt 的 `quality-windows-latest` 被标 `cancelled`，而它**十五个 step 全部 `success`**、零 `failure`；run 一直是 `in_progress` 一小时（无法立即 rerun，API 回 `This workflow is already running`）。run 终态后 `rerun-failed-jobs` （HTTP 201），重跑那条 job **十五个 step 全 `success`**；此刻该 run 的八个 job 全部 `success`，而 **run 级 conclusion 仍是 `cancelled`**（第一次 attempt 的盖章留在 run 上）。归类：**基础设施（iii）**，不改代码、不改门禁；以**逐 job 结论**为判据 |
| `f2f514ee` | [M0 40527953814](https://github.com/Eswink/research-system-new/actions/runs/40527953814) / [Push 40527953575](https://github.com/Eswink/research-system-new/actions/runs/40527953575) | **全 `success`**：M0 **八 job 全 success**（含 `quality-windows-latest`）、Push 三条 Analyze 全 `success`；run 级结论也是 `success` | 收口轮：台账补 `c746d3fb` 的**形态说明**（run 级 `cancelled` 而八 job 全 `success`）+ 重封见证 |
| `967643ef` | 零 run（**`covered_by: f2f514ee`**） | 覆盖：与 `f2f514ee` 同批推送 | 台账补 `f2f514ee` 那一行 + 重封见证（只改记录 + 见证）|
| `fbde73f2` | [M0 40559041743](https://github.com/Eswink/research-system-new/actions/runs/40559041743) / [Push 40559041196](https://github.com/Eswink/research-system-new/actions/runs/40559041196) | **全 `success`**：M0 八 job 全 success、Push 三条 Analyze 全 success | **收口账合上**：EC-03 的悬空取证引用补成真容器取证（`test_experiment_script_selection_docker.py` + `evidence/…-ec03-container-run.txt`）+ 加判据钉住「引用了就必须在树」；取证写出面改**显式开关**（无条件追加会让门改树 ⇒ 见证自判 `tree changed`）；`PLAN` → DONE + `ALL_PLAN` 勾选 + `MEM-20261028-232`；两树复检在最终 HEAD 上重跑（`TWO-TREE PASS`、两棵各 104 条判词、`sha256` 相同 `1535ca78…`）|

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261027-098 | `a93b59a6` → `ee8ff147` → `1310dee4` → `8ae07bca` → `b63b834e` → `93db3c5e` → `c746d3fb` → `f2f514ee` → `967643ef` → `fbde73f2` | EC-01：18 例全过（含真文件按压 + 跨 28 份出厂协议扫描）；EC-03：17 例全过（含**子进程**按压：删掉选择调用 ⇒ 行为判据真的 exit 1）；EC-04：三个回填验证器 **48/51/54** 条判词全过 + 短行登记判据 7 例（含两条真文件按压）；EC-05：收口验证器 **100** 条判词全过；EC-06/07：宪章记账与程序表/阶梯/归档判据 22 例；`ruff check` + `ruff format` 全绿；`validate_bundle` **验证通过**；契约/加载器/四道门/收口注册套件 **634 passed / 72 skipped / 0 failed** | PENDING | 修掉 **8** 个真缺陷（第 8 个由 EC-02 的真跑抓到）：① `importlib.reload` 会污染同会话其它测试 ⇒ 按压改**子进程**；② 按压的 `pytest` 目标名缺类名 ⇒ exit 4（**按压假绿**，被「按压后确认真的红了」抓住）；③ `test_contract_loaders` 的 `len(roles)` 26→27（新增角色的**事实变更**，逐条申报）；④ `validate_bundle` 的「系统 Role 数量 26」同一事实变更；⑤ `goal090` 断言集的块提取偏移错 1（判据自己判红暴露）；⑥ `experiment_support.py` 450/450 零余量 ⇒ 压缩三行注释换回（后又因一行超长再压一次）；⑦ 两个新 `assertion_verdicts` 超 50 行门 ⇒ 按 EC 分组拆函数；⑧ **`novelty_claim_step.with_novelty` 的判负路径必崩**（读 `GateOutcome.verdicts`，而字段名是 `evaluations`、`passed` 是只读 property）—— 只有真跑跑到那条路径才暴露，前两次真跑都被上游 503 挡在检索相 | `W-3` 方案 (a) 待拍板；`W-5` 真跑一次成功率依赖上游可用性（5 次里 3 次被外部原因打断）；`W-1` 租约根因 | 下一轮：① `(a)` 若获拍板则接「模型写脚本」执行面；③ `W-1` 长会话租约根因（会话期心跳 + 错误映射） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-27 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 66）。读取器对 GOAL-097 `REFUSED RESIDUAL_EMPTY` ⇒ 记拒绝码、改以正文为准。`max_goals` 70 → 100。EC-01/03/04/06/07 已 PASS。 |
| 2026-10-28 | **ACHIEVED（收口账合上）** | 验收方点出四处**收口账**缺口，逐条补：① 最后一个 closeout todo 关掉（本行即状态更新）；② `PLAN-20261027-098` 置 **DONE** + `ALL_PLAN` 勾选同步 + 写 `MEM-20261028-232`（DONE 门要求「有记忆引用或声明无可复用事实」）；③ EC-03 的**悬空取证引用**：docstring 曾点名 `evidence/…-ec03-*.txt` 而该文件从未创建（与本轮替 076 修掉的悬空引用同类）⇒ 补**真容器**取证（两个脚本各跑一次，真镜像摘要 + 各自签名指标）+ 加判据 `ec03-no-dangling-evidence-reference` 钉住「引用了就必须在树」；**取证写出面改成显式开关**（`RESEARCHOS_EC03_EVIDENCE=1`）：无条件追加会让门在跑的时候改树 ⇒ 见证自判 `tree changed: True`（本轮实测作废过一次 m0）；④ 两树复检在**最终 HEAD** 上重跑并归档判词：`TWO-TREE PASS`，两棵各 **104** 条判词、`sha256` 相同 `1535ca78…`（此前那份在 `93db3c5e` 上生成）。收口验证器 **104** 条判词、零 FAIL；本地 m0 `PASS: profile=m0; 23 deterministic checks`、24 PASS、0 FAILED、`tree changed: False`。 |
| 2026-10-27 | **ACHIEVED** | **七个 EC 全 PASS**。EC-02 的真跑经历五轮：两次被上游 Europe PMC 503 挡住（连 `query=cancer` 也 503）、第三次在上游恢复后**抓到第 8 个真缺陷**（`with_novelty` 的判负路径读不存在的 `GateOutcome.verdicts` ⇒ 必崩）、第四次 `SUCCEEDED` 取证（`783e6dc7`：两条判词 `main/glm-5.3` + `main/minimax-m3`，作者 `novelty_writer` 不在其中）、第五次 `retry budget exhausted` —— 于是取证写出面改成**追加**。收口验证器 **101 条判词全过**、零 `FAIL`；**两树复检 `TWO-TREE PASS`**（两棵各 101 条判词、`sha256` **相同** `a990c129…`）；本地 m0 `PASS: profile=m0; 23 deterministic checks`、24 PASS、0 FAILED、tree unchanged；CI 逐提交全 `success`。 |
