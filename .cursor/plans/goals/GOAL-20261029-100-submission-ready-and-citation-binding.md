---
id: GOAL-20261029-100
slug: submission-ready-and-citation-binding
title: 把「手稿」做成「能投出去的稿」，并把引用标记钉死
status: ACHIEVED
created_at: 2026-10-29
updated_at: 2026-10-29
owners: [maintainer]
authorization:
  source: user-goal-mode-instruction
  ref: >-
    序 68 / GOAL-20261029-100（用户 goal-mode 指令）。用户 2026-10-29 显式授权全部开发权限
    （含 policy allow 扩容 / 模型写代码进容器 / 新增依赖 / 叙述质量口径），以完成
    『用户给方向 → 系统自主选题、设计实验、撰写、投稿、返修』为目标；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 `.env`。
    本轮实际**未**使用「policy allow 扩容」（见 `U-3`：新相只用已放行的读能力）、
    未新增第三方依赖、未让模型写代码进容器、未定叙述质量口径。
objective: >-
  系统上一轮（GOAL-20261028-099）已产出「投稿形状」的手稿（IMRaD + 真参考文献 + 图表
  数据表），但仍有四处结构缺口：**① 模型看不到引用编号**（提示词里是裸标识 ⇒ 它必须
  自己数「这是第几条」，数错了没有判据会红）；**② 没有投稿决策面**（`scientific_editor`
  角色存在却从未被任何协议激活；决定词表只有验收门的 `PASS`/`REJECT`）；**③ 返修闭环
  在结构上不存在**（`ReviewFinding.findings` 是扁平的判据渲染串、没有可应答的条目 id、
  审稿人的 `weakest_link` 从未被解析成记录、`rebuttal` 全仓零命中）；**④ `retmax` 硬编码**
  （References 恒 3 条上下，「Related Work」没有实质内容可写）。本轮把这四处补上，并且
  每一处都**可机械判**（正向 + 反证）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **引用编号注入**：提示词检索段每一条**可引用**来源以 `[n]` 开头，且 `n` 与
      `## References` 的序号**逐条相等**；编号权威**只有一个**（`references.numbered_records`，
      「去重后首次出现顺序、从 1 起」），汇编器与渲染器**都调它**。三向判据：① 正向逐条相等；
      ② 反证「编造编号」（正文写一个大于条目总数的 `[k]`）⇒ 汇编器点名判红；
      ③ 反证「改回裸标识」（把注入那一段从**真文件**里还原成裸标识、写到临时模块里执行）
      ⇒「提示词—References 编号一致」判据**必须**红。**不可引用**的条目（`ids[]` 形状、
      没有著录字段）**不占编号**，逐条标 `[not citable]`（占号会让其后整体错位）。
    verify: tests/application/test_citation_numbers_reach_the_prompt.py（8 条，含两条真文件按压）
    status: PASS
  - id: EC-02
    criterion: >-
      **投稿决策面**：`scientific_editor` 被**激活**（`editorial` 相点名它，且
      `agents.yaml` 有绑定 + `models.yaml` 有声明 + `team_templates.yaml` 的 `standard`
      池收录 —— 三条缺一即编译期/预检失败，实测过）；决定词表落进 `packages/domain/enums.py`
      的 `EditorialDecision`（四值闭集 `accept` / `minor_revision` / `major_revision` /
      `reject`），**四值各可判**；**反证**越界值点名拒绝（含大小写 / 拼写 / 验收门词
      `PASS`/`REVISE` —— 本模块**不**做宽容匹配）；**反证**非 `accept` 而
      `required_changes` 为空 ⇒ 点名判红。既有门词 `PASS`/`REJECT` **逐字未动**（两个面
      刻意分开，取值不重叠亦有判据）。
    verify: tests/application/test_editorial_decision.py（19 条）+ tests/e2e/test_direction_to_manuscript_product_path.py::test_the_editorial_decision_comes_out_of_the_product_entry
    status: PASS
  - id: EC-03
    criterion: >-
      **返修闭环的底座**：评审交付物里的意见**显式化**为可编号的点（`point_id` `P1…Pn` +
      `severity` 三档 + `text`），来源是审稿人真的写了什么（`review_decision` 的
      `weakest_link` 与自述 `findings[]`，此前**从未被解析成记录**）；新增 `author_response`
      契约 + `revision` 相；`response_letter.md` 由汇编器按点逐条装配（模型写回应、汇编器写
      编号与格式），并**注册进读面**（不注册的制品读不到 —— 实测缺口）。三条反证各判红：
      ① **漏答**（有评审点却少一条应答）；② **编造 `point_id`**（应答引用评审从未提出的编号）；
      ③ **删一条应答** ⇒ 判据**必须**红。**不新增任何表 / 列**（点表由已落库制品派生 ⇒ 无迁移）。
    verify: tests/application/test_author_response.py（26 条）+ tests/e2e/test_direction_to_manuscript_product_path.py::test_the_response_letter_answers_every_review_point
    status: PASS
  - id: EC-04
    criterion: >-
      **`retmax` 可配而默认不变**：`DEFAULT_RETMAX = 3` 是具名常量、`RESEARCHOS_RETMAX`
      是配置面、`retrieval_calls(retmax=...)` 可显式覆盖；**默认逐字段等于今天**
      （不传参、不设环境变量 ⇒ `fixed_arguments == {"retmax": 3}`，read 那条调用不受影响）；
      改配置（显式值与环境变量两条通路）⇒ 调用参数随之变；**反证**非法值（非整数 / 0 /
      负数 / 超上界）**点名拒绝**，不静默回落默认。
    verify: tests/api/test_retmax_is_configurable.py（11 条，含真文件按压：把常量改 5 ⇒ 两条判据红）
    status: PASS
  - id: EC-05
    criterion: >-
      **收口资产**：`tools/verify_goal100_closeout.py` + `tools/goal100_closeout_assertions.py`
      在树、登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的
      `_VERIFIERS` 与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的
      `IN_SCOPE`，判词跑通（含自指 `self-loads-its-own-assertions`）。**本 EC 的一个既述
      后果要求本文件 frontmatter 是终态**：`test_terminal_goals_have_closeout_verifiers.py`
      的受判面只认 `_TERMINAL = {ACHIEVED, BLOCKED, ABANDONED}` ⇒ 只要 `status` 还是
      `ACTIVE`，100 **不进**那条判据的受判面。
    verify: tools/verify_goal100_closeout.py --root . --verdict-only
    status: PASS
  - id: EC-06
    criterion: >-
      **宪章记账**：程序表追加**序 68**（能力域 `报告`）；阶梯「报告」行 `依据 GOAL` 收录
      本 GOAL 并写明本轮真实推进的那一格（**投稿决策 + 逐条应答**）；`下一级`
      **逐字保持**「叙述质量与事实一致性可判」（本轮**没做**它，不许声称已判）；
      `进展记录` 追加一行并**插在最上面** ⇒ 3 行；`## 修订记录` 追加一行、**必须 5 格**、
      插在表格全部数据行之后；子 PLAN 登记进 `ALL_PLAN.md` 表格顶部。
    verify: 宪章程序表 / 阶梯 / 进展记录 / 修订记录四处 + ALL_PLAN 首行
    status: PASS
budget:
  max_cycles: 30
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  max_same_signature: 3
  forbidden:
    - 改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据
    - 把受判面写成交集或并集掩蔽
    - 收窄受判面而不逐条申报
    - git push --force / 重写历史 / 推非 main
    - 伪造或夸大验证证据（**尤其**：把「确定性汇编」说成「模型撰写」、把 skip 记成 PASS、
      补造缺失的作者 / 年份、**把 policy allow 扩容说成「默认 deny 未变」**）
    - git add -A
    - 宣称项目安全（`R-M1` 未收口）
    - 宣称投递语义为「恰好一次」
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新增第三方依赖（绘图库 / pandoc / reportlab / weasyprint 全算）或上游版本 pin 变更
  - 改 CI workflow
  - 改或新增 TrustLabel 取值
  - 给新能力加 policy allow
  - 模型写代码进容器（GOAL-098 的 `W-3` / 方案 (a)）
  - 定「叙述质量」或「事实一致性」的判定口径
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261029-100-goal-100-submission-ready-and-citation-binding.md
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261029-100-goal-100-submission-ready-and-citation-binding.md
memory_entries: []
---

# GOAL-20261029-100 — 把「手稿」做成「能投出去的稿」，并把引用标记钉死

## 目标与退出标准

| EC | 标准（摘要） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 提示词每条来源带 `[n]`，与 References 序号**逐条相等**；编号权威唯一；两条反证 | `tests/application/test_citation_numbers_reach_the_prompt.py`（8 条） | **PASS** |
| EC-02 | `scientific_editor` 被激活；决定词表进 domain 且四值可判；越界拒绝；非 accept 空改动判红 | `tests/application/test_editorial_decision.py`（19 条）+ 产品入口用例 | **PASS** |
| EC-03 | `point_id` 显式化 + `author_response` 契约 + `response_letter.md`；漏答 / 编造 / 删答三条反证 | `tests/application/test_author_response.py`（26 条）+ 产品入口用例 | **PASS** |
| EC-04 | `retmax` 可配、默认逐字段不变、改配置可证、非法值点名 | `tests/api/test_retmax_is_configurable.py`（11 条） | **PASS** |
| EC-05 | 收口验证器 + 断言集 + 两处登记 + 判词跑通（含自指） | `tools/verify_goal100_closeout.py --root . --verdict-only`（64 条判词）+ **TWO-TREE PASS**（两棵各 64 条、`sha256` 相同 `320054cf…`，判词归档 `evidence/GOAL-20261029-100-two-tree-{current,clean}.txt`） | **PASS** |
| EC-06 | 序 68 / 阶梯「报告」行写本轮那一格 / 进展记录 3 行 / 修订行 5 格 + ALL_PLAN | 宪章四处 + `ALL_PLAN.md` | **PASS** |

## 循环入口协议

每一轮 cycle 的开始状态取三件**可提取**事实（不靠记忆）：

1. 上一轮 GOAL 的「残余与未覆盖范围」；
2. 迭代日志最后一行的「下一轮输入」；
3. 工作树 / 远端实况（`git status`、`git log --oneline -5`）。

**本轮开场的读取器读数（如实记拒绝码）**：`tools/next_round_charter.py` 对
GOAL-20261028-099 返回 **`REFUSED RESIDUAL_EMPTY`**。理由（读判据源确认，不是猜）：
`tools/charter_parse.py` 的 `check_residuals` 只认**列表项形态** `- **W-NN**`
（`_W_ITEM` 正则），而 GOAL-099 的残余节把条目写成反引号形态 `` - `W-1`｜… ``
⇒ 读取器读到 0 条。**这是连续第三轮同一个拒绝码**（097→098、098→099、099→100 都是它）。
按纪律：**记拒绝码、改以 GOAL-099 正文「残余与未覆盖范围」为准**（`W-1`…`W-5`），
**不**为让读取器通过而改写历史记录。

本轮逐条处置 GOAL-099 的残余：`W-1`（引用编号，**本轮靶子 1 = EC-01**）、
`W-4`（`retmax` 硬编码，**本轮靶子 4 = EC-04**）均已闭合；`W-2`（检索摘录里同一批记录
出现两次）**本轮改成不重复编号**（同一条重复出现时**沿用同一个 `[n]`**，判据
`test_a_duplicate_record_keeps_the_same_number` 钉住）但仍未改 `retrieval_context` 的
去重行为（那是共用面，见 `W-2`）；`W-3`（多臂指标行序由 uuid 决定）与 `W-5`（叙述质量
无判据）**原样继承**。

## 单 cycle SOP

1. **勘察取证**：任何「已实现 / 未实现」的判断先落 `rg -n` 读数（不用 `-r`，那是替换）。
2. **先量规模**：动 `packages/` 与 `services/` 之前先 `wc -l`（450 行文件门 / 50 行函数门）。
   本轮实测撞了三次：`phase_runner.py` 从 449 → 451（合并一处重复 import 压回 450）、
   `manuscript_assembly.py` 加应答信装配后 439（余量够）、`composition.py` 未动。
3. **判据先写反证臂**：每条新判据至少一个「按掉实现就判红」的按压，按在**真文件**上，
   并按 raw `sha256` 逐字节复原；**按压后必须确认判据真的红了**。
4. **记录顺序**：写全部记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 →
   **最后**跑 `tools/run_m0_with_witness.py` → 之后不再 `git add` → 提交推送。
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

- **ACHIEVED**：六个 EC 全达成 ⇒ 跑 `tools/two_tree_recheck.py --script-mode shared`
  （两树判词逐行 + `sha256` 相同）⇒ 归档判词进树 ⇒ 写收口报告与 RECHECK。
- **BLOCKED**：撞 `escalation_triggers` / 同一签名超上限 / 需用户拍板（改 TrustLabel、
  放宽判据、动冻结面、改 workflow、**新增第三方依赖**、给新能力加 policy allow、
  **模型写代码进容器**、定叙述质量口径）。

| 2026-10-29 | **ACHIEVED（CI 全绿）** | **六个 EC 全 PASS**。判据 64 条（EC-01 8 / EC-02 19 / EC-03 26 / EC-04 11）+ 产品入口 9 条全过；三条**真文件按压**证明判据会红（改回裸标识 ⇒ 6 条红；`DEFAULT_RETMAX` 改 5 ⇒ 2 条红；均 `sha256` 逐字节复原）。**修掉五处实现缺陷**（能力面漏声明 / 面板相跨相输入恒 ambiguous / `task.contract` 不存在 / 已渲染字符串被再渲染 / 应答信只 put 不 register），逐条记在 RECHECK。**收口验证器 64 PASS / 0 FAIL**；**TWO-TREE PASS**（两棵各 64 条判词、`sha256` 相同 `320054cf165540ba579121065bc5119691651bc8ce817ff52bbde36ba6130032`，判词归档进树、`cmp` 逐字节一致）。**CI 逐 job 全绿**：`1d94dcca` 的 run 八 job全 `success`；`f15929e5` 那次的两个 `quality-*` 失败是**真缺陷**（见证在记录之前封存 ⇒ 见证点名过期内容），已由重封提交修复，**判据没有放宽**。 |

## 残余与未覆盖范围

- `W-1`｜**`retmax` 的配置面只有环境变量**（`RESEARCHOS_RETMAX`），**没有**
  `ProjectSettings` / 协议相级字段。取舍：加项目级字段要动 `ProjectSettings` 的域形状 +
  两个存储侧的序列化 + 快照（读出面），而本 EC 的判据只要求「可配 + 默认不变」——
  做到环境变量这一层已经满足，且**不引入迁移风险**。下一级是「按协议/项目配」。
- `W-2`｜**检索摘录里同一批记录仍出现两次**（检索链两步各落一份 tool-result 制品）。
  本轮把**编号**改成不重复（同一标识沿用同一 `[n]`），但**没有**改
  `retrieval_context` 的去重行为 —— 模型看到的列表仍有重复行（只是编号相同）。
  改它要动共用面（另七份协议的提示词字节），属另一轮。
- `W-3`｜**多臂指标的行序由随机 uuid 决定**（`report_facts.metrics_of` → `_metric_rows`
  按 `sorted(per_run)`，key 是 `experiment_run_id`）：同一份夹具的两次 run 会**交替**
  出现 `178.5` 在前与 `7990.0` 在前。既有确定性汇编的**既有性质**，本轮不改。
- `W-4`｜**应答信的 `action_taken` 不被判据检查内容**：判据判的是「逐条应答过、
  没有编造编号、没有重复」，**不**判「这条改动真的做了」。判后者需要把改稿与父版本
  对齐（artifact 版本/父指针），属「返修闭环完整版」那一轮。
- `U-1`｜「创新」是否**真的新**未判：`nearest_prior` 只判「那条标识在本 run 的检索结果里
  真实出现」。
- `U-2`｜**叙述质量与事实一致性**仍**无判据**（承 GOAL-096 `U-1` / 097 `U-2` / 099 `W-5`）。
  本轮判的全部是**结构事实**（编号一致 / 决定取值 / 逐条应答 / 配置面），**不**判
  「写得对不对」「`[2]` 是否真的支持那句话」。定那个口径在本轮授权内（用户已预授权
  「叙述质量口径」），但**本轮没做** —— 如实登记为未覆盖，`下一级` 因此**不许**声称已判。
- `U-3`｜**本轮没有扩容 `policy.yaml`**：新增的两个相（`editorial` / `revision`）只声明
  **已放行**的读能力（`artifact.read` / `evidence.read` / `deliverable.read` /
  `literature.search` / `literature.read` / `workspace.read`）⇒ 未触碰
  `POLICY_SURFACE_AUDIT.md` / `_CAPABILITY_SCOPE` / `EXPECTED_REGISTERED` 那一组镜像。
  `deliverable.write` 仍无 allow（`scientific_editor` 的 `forbidden_capabilities` 里也
  没有它 —— 编辑不写稿件正文）。用户预授权的「扩容」**本轮没用到**，如实登记。
- `R-1`｜`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- `R-2`｜投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- `R-3`｜`response_letter.md` 的 `created_by` 是 `system:author-response-assembler`：
  **回应是模型写的、编号与格式是汇编器写的**。不能读成「整封信由模型撰写」，
  也不能读成「确定性汇编」（`fix_policy` 两个方向都禁）。
- `R-4`｜**`scientific_editor` 的能力面本轮被扩了三条**（`claim.read` / `evidence.read` /
  `artifact.read`）。这不是放宽判据：那三条都是**已放行**的读能力，而该角色此前的能力面
  装不下它要做的读（实测三条 `AGENT_PERMISSION_DENIED`）。`forbidden_capabilities`
  四条逐字未动。

## CI 台账

（逐提交逐 job，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是两种形态，分别登记；
后者用 `covered_by` 指名它被哪一条 run 覆盖。）


> **`f15929e5` 的两个 `quality-*` 失败是真缺陷，已修**：`test_m0_witness_matches_the_tree` 判「见证覆盖的文件内容与当前树不一致」—— 原因是**跑完门之后又往树里加了文件**（两树判词归档 `evidence/GOAL-20261029-100-two-tree-*.txt`），于是那次 m0 的终态行失效（与 MEM「见证绑内容、先 add 受判文件再跑最后一次 m0」同一形态）。修法：把那两份归档**先放进树**，再跑一次全量 m0 重封见证，然后把归档 + 见证与台账一起提交。**判据没有放宽**：`tree changed during the run: False`、`PASS [` **24** 行、`PASS: profile=m0; 23 deterministic checks`。
| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `f15929e5` | [M0 40934404446](https://github.com/Eswink/research-system-new/actions/runs/40934404446) / [Push 40934403745](https://github.com/Eswink/research-system-new/actions/runs/40934403745) | Push 三条 Analyze 全 `success`；M0 **六 job `success`**、`quality-ubuntu-latest` 与 `quality-windows-latest` **failure**（原因见下，已由 `f90e4840` 之后的重封提交修复） | **本轮交付**：EC-01…EC-06 六件（引用编号注入 / 编辑决定面 / 返修底座 / `retmax` 可配 / 收口资产 / 宪章记账）+ 五处实现缺陷修复 + **付清 GOAL-099 的两笔台账债**（`b0eb3ff2` / `29ed0d5f`）。本地 m0（记录落盘**之前**）：`PASS [` **23** 行、0 FAILED、`tree changed during the run: False`，仅 `test_goal_commit_chain_reaches_the_ledger` 因「本提交自身把前一条推离 HEAD」而红（结构事实，不是产品缺陷） |
| `f90e4840` | 零 run（**`covered_by: 40946603366`**） | 覆盖：与 `1d94dcca` 同批推送，被合并进那一条 M0 run | **记录提交**（只改 `.cursor/`）：GOAL-100 台账行（`f15929e5` 的真实读数）+ **付清 GOAL-099 的 两笔 tip 债**（`b0eb3ff2` / `29ed0d5f`，债记在被点名的那本账上）+ 重封见证。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `bbb8656b` | 零 run（**`covered_by: 40946603366`**） | 覆盖：同批推送 | **归档两树判词**（两份 64 条、`sha256` 相同 `320054cf…`）+ 台账补两树读数 + 重封见证。该提交的见证**仍被下一次编辑作废**（我在重封之后又改了 GOAL 正文）⇒ 见下一行 |
| `1d94dcca` | [M0 40946603366](https://github.com/Eswink/research-system-new/actions/runs/40946603366) / [Push 40946602926](https://github.com/Eswink/research-system-new/actions/runs/40946602926) | **全 `success`**：M0 **八 job 全 success**（`eval-gate` / `quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `collector-quality` / `container-quality`）、Push 三条 Analyze 全 `success`；run 级 conclusion 也是 `success` | **收口 tip**（本提交即 HEAD）：**最后一次**重封见证 —— 顺序是「记录全部定稿 → 跑门 → 只提交见证 → 不再改树」。本地 m0（记录落盘**之后**）：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False`；`--verify-only` 报「覆盖成立：4705 个受判面文件」 |

| `bce97c13` | [M0 40953804158](https://github.com/Eswink/research-system-new/actions/runs/40953804158) / [Push 40953804292](https://github.com/Eswink/research-system-new/actions/runs/40953804292) | **全 `success`**：M0 **八 job 全 success**、Push 三条 Analyze 全 `success`；run 级 conclusion 也是 `success` | **本 GOAL 的链在此收口**（本提交即 HEAD）：`status` 已置 `ACHIEVED`、台账收录本链全部提交、见证最后一次重封。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False`；`--verify-only` 报「覆盖成立：4705 个受判面文件」 |
## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261029-100 | `f15929e5` → `f90e4840` → `bbb8656b` → `1d94dcca` → `bce97c13`（本 GOAL 的链全部收录；`bce97c13` 自身即 HEAD —— 按 `goal_commit_chain` 的构造豁免）| EC-01：8 条全过（含两条真文件按压，按压后 6 红、逐字节复原）；EC-02：19 条全过；EC-03：26 条全过；EC-04：11 条全过（含按压）；EC-05：判词 64 PASS / 0 FAIL；**TWO-TREE PASS**（两棵各 64 条、`sha256` 相同 `320054cf…`）；套件 `tests/application + contracts + loaders + domain` **2608 passed / 73 skipped**、`tests/api + e2e manuscript` **737 passed / 4 skipped** | （待登记） | 修掉 5 处**实现**缺陷（不是判据）：① `editorial` 相只声明三条能力 ⇒ 另三件的 provider 排不出会话工具面 ⇒ 真实 run 点名 `ToolDefinition 'europe_pmc' is not registered`；② `review:review_decision` 作跨相 `inputs` 在评审面板下**恒 ambiguous**（两个任务）⇒ 改成经提示词那一段送；③ `wants_review_points` 读 `task.contract` 而 `ResearchTask` 只有 `contract_id` ⇒ 静默返回 False、点表从未进提示词；④ 已渲染的**字符串**被当点对象再渲染一次 ⇒ `-  (): ` 空行（与 MEM「已渲染的提示段被当视图再渲染」同一形态）；⑤ 应答信只 `put` 不 `register` ⇒ 读面 `GET /runs/{id}/artifacts` 看不到它 | `W-1`…`W-4` / `U-1`…`U-3` | ① 叙述质量口径（可机械判的形态）；② `retmax` 进项目级设置；③ 返修闭环完整版（改稿 + 父指针）；④ `retrieval_context` 去重（共用面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-29 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 68）。读取器对 GOAL-099 `REFUSED RESIDUAL_EMPTY`（连续第三轮同一拒绝码）⇒ 记拒绝码与理由、改以正文为准。EC-01…EC-06 全部落地并各自取证。 |
