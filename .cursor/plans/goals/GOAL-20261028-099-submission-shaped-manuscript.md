---
id: GOAL-20261028-099
slug: submission-shaped-manuscript
title: 让系统产出投稿形状的手稿（IMRaD + 真参考文献 + 图表数据表）
status: ACHIEVED
created_at: 2026-10-28
updated_at: 2026-10-28
owners: [maintainer]
authorization:
  source: user-goal-mode-instruction
  ref: >-
    序 67 / GOAL-20261028-099（用户 goal-mode 指令）。push-to-main-for-CI：只推 main、
    不 force、不重写历史、不推旁支；RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E
    逐命令传，绝不写进 `.env`。
objective: >-
  系统现在产出的是「研究报告」：四节中文（问题与动机 / 检索与证据 / 实验与指标 / 评审与结论，
  `packages/application/deliverable/research_report.py:26-31`）、确定性汇编、参考文献渲染成
  Python 的 `dict` 字面量（`f"- {dict(item)}"` ⇒ `- {'identifier': '39000001', ...}`）。
  本轮让它产出**投稿形状的手稿**：英文 IMRaD（Abstract + 六个编号节）、**真参考文献表**
  （Vancouver：作者 / 题名 / 刊名 / 年份 / doi / PMID，每个字段逐字取自落盘的工具结果字节）、
  **图表数据表**（数字只出现在汇编器写的那张表里，每行带来源列）、**数字可核**
  （模型正文出现任何 Unicode 十进制数位 ⇒ 点名拒绝，不静默抽掉）。
  三件交付各自可机械判：新八相协议编译零 ERROR + 手稿结构 + 引用双向闭合 + 真元数据 +
  从**产品入口**产出（`TestClient(create_app(deps))`）+ 不开手稿时既有报告零回归。
exit_criteria:
  - id: EC-01
    criterion: >-
      新协议 `direction_to_manuscript_v1.yaml` **八相**（question / retrieval / novelty /
      plan / experiment / review / manuscript / report）编译通过、**零 ERROR**；
      `manuscript` 相是**会话相**（其合约 `research_manuscript` **不声明** `report:` /
      `experiment:` —— 这是它能合法声明跨相 `inputs` 的唯一理由）且三条跨相边各自解析成
      `(产出方, 产物名, 性质)`；C-1 仍守住（`experiment` / `report` 两相不声明跨相
      `inputs`）；**既有协议一字未改**（v1 六相 / v2 七相 / 两相版 / 四相链的字面相集判据
      仍绿 = 机械证据）。两向反证（真文件按压 + raw `sha256` 逐字节复原）：
      给手稿合约加 `report: {}` ⇒ 编译点名 `CROSS_PHASE_INPUT_INVALID`（ERROR 级）；
      摘掉一条手稿跨相边 ⇒ 边集判据点名判红。
    verify: tests/contracts/test_direction_to_manuscript_protocol.py（38 条用例）
    status: PASS
  - id: EC-02
    criterion: >-
      手稿结构：`manuscript.md` 含 `## Abstract` + 六个编号节（`1. Introduction` …
      `6. Conclusion`）+ `## References`，顺序即文档顺序；正文 `[n]` 与 References
      **逐条一一映射**（越界引用 ⇒ 点名；列出却从不被引用的孤儿条目 ⇒ 点名 —— 两向合起来
      才叫闭合）。**数字只在汇编器写的地方**：正文任何 Unicode 十进制数位（引用标记除外）
      ⇒ `ManuscriptError` **点名哪一节、哪个字符**（不静默抽掉）；数据表在 Results 之下、
      带 `| 类别 | 名称 | 值 | 来源 |` 列头。反证：正文引用不存在的编号 ⇒ 判红；模型正文
      含数字 ⇒ 点名判红（8 个键逐键参数化）。
    verify: tests/application/test_manuscript_assembler.py（24 条用例）
    status: PASS
  - id: EC-03
    criterion: >-
      真参考文献：每行有作者 / 年份 / 刊名，全部逐字取自本 run 落盘的 tool-result 字节；
      **两种作者形态都认**（NCBI 的 `authors` 列表、Europe PMC 的 `authorString` 整串 ——
      实测真实字节里两种都有：6 条列表 / 4 条整串）；改制品 `year` 或 `journal` ⇒ 表随之变；
      缺 `authors` / `journal` ⇒ **点名「哪一条缺什么」**，不填占位符（结构判据：渲染输出里
      不得出现 `Unknown` / `N/A` / `n.d.` / `Anonymous` / `TBD`）；旧的 dict-repr 行不满足
      三条事实（无作者 / 无刊名 / 无年份，也不匹配 `^\d+\. ` 编号形态）⇒ 判红。
      **先量真实缺失率再定策略**：10 条 distinct 记录（本工作树内 17 份 tool-result 制品）
      的 journal / year / title / authors 缺失率均为 **0/10**；样本边界如实登记（不是上游
      服务的普查）。编号顺序 = 提示词里首次出现顺序的**去重后**位置（检索链两步会重复列出
      同一批记录），由判据钉住。
    verify: tests/application/test_manuscript_references.py（20 条）+ tests/application/test_manuscript_reference_order.py（2 条）+ evidence/GOAL-20261028-099-ec03-metadata-census.txt
    status: PASS
  - id: EC-04
    criterion: >-
      手稿**从产品入口产出**：`TestClient(create_app(deps))` → `POST /projects/{id}/runs`
      （`protocol_path` = 新协议）→ run `SUCCEEDED`、八件产物齐（含 `manuscript_narrative`
      与 `manuscript.md`），经既有读面取回 `manuscript.md` 内容字节并判 IMRaD 形状、真
      Vancouver 行、正文无数字、数据表带来源列；**不补任何测试专用缝**（只注入 mock 传输 +
      既有执行体缝）。**零回归**：装配开关关掉 ⇒ `manuscript.md` **不在**库里而报告照出；
      同一 run id 上开/关两臂的报告**字面逐字节相同**（`test_manuscript_assembly.py`）。
    verify: tests/e2e/test_direction_to_manuscript_product_path.py（7 例）+ tests/application/test_manuscript_assembly.py（5 例）+ evidence/GOAL-20261028-099-ec04-product-path.txt；收口两树 `TWO-TREE PASS`（80 条判词、`sha256` 相同）
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产齐备：`tools/verify_goal099_closeout.py` + `tools/goal099_closeout_assertions.py`
      在树，登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的
      `_VERIFIERS` 与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的
      `IN_SCOPE`，判词跑通（含自指「加载自己那份断言集」与反证臂）。**本 EC 的一个既述后果要求本文件 frontmatter 是终态**：`test_terminal_goals_have_closeout_verifiers.py` 的受判面只认`_TERMINAL = {ACHIEVED, BLOCKED, ABANDONED}`（`:48`）⇒ 只要 `status` 还是 `ACTIVE`，099 **根本不进**那条判据的受判面，「不登记就判红」这句话就还没有对象。本 GOAL 收口时把 `status` 改为 `ACHIEVED`，该后果才真的成立。
    verify: tools/verify_goal099_closeout.py --root . --verdict-only
    status: PASS
  - id: EC-06
    criterion: >-
      宪章记账齐全：程序表追加**序 67**（能力域 `报告`）；阶梯「报告」行 `依据 GOAL` 收录
      本 GOAL 并在 `当前级` 写明**「手稿层（IMRaD + 真参考文献）」**、同时写明
      **「手稿层 ≠ 报告层」**（`下一级` **保持**「叙述质量与事实一致性可判」——本轮做的是
      可机械判的结构，**不**声称叙述质量已判）；`进展记录` 追加一行并**插在最上面**
      （该表取 `progress[0]`，不按日期排序）⇒ 3 行；`## 修订记录` 追加一行且**必须 5 格**、
      插在表格全部数据行之后 ⇒ 3 行；子 PLAN 登记进 `ALL_PLAN.md` 表格顶部。
    verify: 宪章程序表 / 阶梯 / 进展记录 / 修订记录四处 + ALL_PLAN 首行
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
    - 伪造或夸大验证证据（**尤其**：把「确定性汇编」说成「模型撰写」、把 skip 记成 PASS、
      补造缺失的作者 / 年份、把「报告没变」写成逐字节相同而实际只归一化比较）
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
  - .cursor/plans/tasks/PLAN-20261028-099-goal-099-submission-shaped-manuscript.md
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261028-099-goal-099-submission-shaped-manuscript.md
memory_entries: []
---

# GOAL-20261028-099 — 让系统产出投稿形状的手稿

## 目标与退出标准

| EC | 标准（摘要） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 八相协议编译零 ERROR；`manuscript` 是会话相且跨相 `inputs` 合法；既有协议未改；两向按压 | `tests/contracts/test_direction_to_manuscript_protocol.py`（38 例） | **PASS** |
| EC-02 | IMRaD + Abstract + References；`[n]` ↔ References 双向闭合；正文无数字（引用标记除外） | `tests/application/test_manuscript_assembler.py`（24 例） | **PASS** |
| EC-03 | 真参考文献（作者 / 年 / 刊名逐字来自落盘字节）；两种作者形态；缺失点名不填占位符 | `test_manuscript_references.py`（20 例）+ `test_manuscript_reference_order.py`（2 例）+ 元数据普查取证 | **PASS** |
| EC-04 | 从**产品入口**产出 `manuscript.md`；关掉开关 ⇒ 报告字面逐字节不变 | `tests/e2e/test_direction_to_manuscript_product_path.py`（7 例）+ `tests/application/test_manuscript_assembly.py`（5 例） | **PASS** |
| EC-05 | `verify_goal099` + 断言集 + `_VERIFIERS` / `IN_SCOPE` 登记 + 判词跑通 | `tools/verify_goal099_closeout.py --root . --verdict-only`（**82 条判词全过**；两树那次为 80） | **PASS** |
| EC-06 | 宪章记四件：序 67 / 阶梯「报告」行 / 进展记录 3 行 / 修订行 5 格 + ALL_PLAN | 宪章四处 + `ALL_PLAN.md`（判词已过） | **PASS** |

## 循环入口协议

每一轮 cycle 的开始状态取三件**可提取**事实（不靠记忆）：

1. 上一轮 GOAL 的「残余与未覆盖范围」；
2. 迭代日志最后一行的「下一轮输入」；
3. 工作树 / 远端实况（`git status`、`git log --oneline -5`）。

**本轮开场的读取器读数（如实记拒绝码）**：`tools/next_round_charter.py` 对 GOAL-20261027-098
返回 **`REFUSED RESIDUAL_EMPTY`**。理由（读判据源确认，不是猜）：`tools/charter_parse.py:169`
的 `check_residuals` 只认**列表项形态** `- **W-NN**`（`_W_ITEM` 正则），而 GOAL-098 的残余节
把条目写成反引号形态 `` - `W-1`｜… `` ⇒ 读取器读到 0 条。
按纪律：**记拒绝码、改以 GOAL-098 正文「残余与未覆盖范围」为准**（`W-1`…`W-5`、`U-1`…`U-3`、
`R-1`…`R-3`），**不**为让读取器通过而改写历史记录。
本轮逐条处置：`W-3`（模型写脚本进容器）已在本 GOAL 的 `escalation_triggers` 里列为待拍板；
`W-1`（租约心跳）与 `W-2`（检索格 `phase_id` 常量）不在本轮射程；`W-4`（076 交付面）仍是
「未做仍是未做」；`W-5`（上游抖动）是既有环境事实。`U-1` / `U-2` / `U-3` 与 `R-1` / `R-2` /
`R-3` 原样继承到本文件「残余与未覆盖范围」。

## 单 cycle SOP

1. **勘察取证**：任何「已实现 / 未实现」的判断先落 `rg -n` 读数（不用 `-r`，那是替换）。
2. **先量规模**：动 `packages/` 与 `services/` 之前先 `wc -l`（450 行文件门 / 50 行函数门）；
   `report_task.py` 433 → 加手稿分支后仍需守门，故手稿的读面与装配分列两个新模块。
3. **判据先写反证臂**：每条新判据至少一个「按掉实现就判红」的按压，按在**真文件**上，
   并按 raw `sha256` 逐字节复原；**按压后必须确认判据真的红了**。
4. **记录顺序**：写全部记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 →
   **最后**跑 `tools/run_m0_with_witness.py` → 之后不再 `git add` → 提交推送。
5. **一个 cycle 一次推送**（`cancel-in-progress` 会取消在飞的 M0 run）。
6. **判据不得在门跑的时候写树**（GOAL-098 实测：无条件追加取证 ⇒ 见证判 `tree changed: True`
   ⇒ 那次终态行作废）；写盘要 opt-in。

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
- **以下不是失败**（照实记录后继续）：`retmax=3` 让 References 只有约 3 条 ⇒ 登记为真实边界，
  不假装文献综述；元数据缺失率高 ⇒ 登记缺失率 + 说明渲染策略，不猜占位符；
  靶子 3 回归太多 ⇒ 单独登记为下一轮，不硬压。
- **BLOCKED**：撞 `escalation_triggers` / 同一签名超上限 / 需用户拍板（改 TrustLabel、
  放宽判据、动冻结面、改 workflow、**新增第三方依赖**、给新能力加 policy allow、
  **模型写代码进容器**、定叙述质量口径）。

## 残余与未覆盖范围

- `W-1`｜**手稿正文里模型看不到编号化的引用标记**：会话提示词由
  `retrieval_prompt.compose_prompt` 拼「合约 purpose + 方向 + 前序知识 + **检索摘录** +
  上一轮评审 + 被评对象」，其中检索那一段（`PROMPT_SECTION_TITLE`）逐条列的是
  **裸标识 + 摘录**（`- 39284801: <title excerpt>`），**不带** `[1]`…`[n]`。于是模型必须
  自己数「这是第几条」才能写对编号。合约正文因此改成**派生规则**（编号 = 该列表里
  **去重后**的首次出现位置），判据钉住「编号顺序 = 去重后首次出现顺序」；但「模型数得对
  不对」**没有**判据（那是模型行为能力，不是结构事实）。修法（把编号写进那一段）要动
  **共用**的提示词渲染器 ⇒ 会回归其余七份协议的提示词字节，属另一轮。
- `W-2`｜**同一批记录在检索摘录里出现两次**（检索链两步：`literature.search` 与
  `literature.read` 各落一份 tool-result 制品）⇒ 模型看到的列表有重复项，而 References
  去重。本轮以「去重后首次出现顺序」定编号并写进合约正文 + 判据；**没有**改
  `retrieval_context` 的去重行为（那是共用面）。
- `W-3`｜**多臂指标的行序由随机 uuid 决定**（`report_facts.metrics_of` → `_metric_rows`
  按 `sorted(per_run)`，而 key 是 `experiment_run_id`）：同一份夹具的两次 run 会**交替**
  出现 `178.5` 在前与 `7990.0` 在前。这是既有确定性汇编的**既有性质**，本轮不改；
  后果是产品入口那一格只能判**内容面**（结构 / 指标名集合 / 读数多重集 / 判词），
  字面逐字节那一臂改在**同一 run id** 上判（`test_manuscript_assembly.py`）。
- `W-4`｜**`retmax` 硬编码 3**（`services/api/retrieval_wiring.py:86`，无配置面）⇒ 真实 run
  的 References 只有约 3 条。**如实登记的边界**：本轮不声称手稿带文献综述。
- `W-5`｜**手稿正文的科学质量与事实一致性无判据**（承 GOAL-096 `U-1` / GOAL-097 `U-2`）。
  本轮判的是三件**结构事实**：谁写的（`model_assisted:` 前缀 + 抬头三行）、数字在哪
  （正文无数字 / 数据表有来源列）、编号是否闭合。**不**判「叙述写得好不好」或「`[2]`
  是否真的支持那句话」—— 定那个口径属 `escalation_triggers`。
- `U-1`｜「创新」是否**真的新**未判：`nearest_prior` 只判「那条标识在本 run 的检索结果里
  真实出现」。
- `U-2`｜`Related Work` 只是**一条**检索记录的差异面（`retmax=3` + 本 run 只取 2 条），
  不是主题聚类综述。
- `U-3`｜本轮的 `manuscript` 相**只用已放行的读能力**（`artifact.read` /
  `evidence.read` / `deliverable.read` / `literature.search` / `literature.read` /
  `workspace.read`），**没有**新增能力名 ⇒ 未触碰 `policy.yaml` / `POLICY_SURFACE_AUDIT.md` /
  `EXPECTED_REGISTERED` 那一组镜像；`deliverable.write` 仍无 allow（`research_writer` 角色
  的能力面里有它，但本协议的手稿相**不声明**它 ⇒ 不进可达集）。
- `R-1`｜`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- `R-2`｜投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- `R-3`｜手稿制品的 `created_by` 是 `model_assisted:<agent>`：正文是模型写的、数字与
  References 是汇编器写的。**不能**读成「整份手稿由模型撰写」，也**不能**读成
  「确定性汇编」（`fix_policy` 两个方向都禁）。

## CI 台账

（逐提交逐 job，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是两种形态，分别登记；
后者用 `covered_by` 指名它被哪一条 run 覆盖。）


> **继承的 GOAL-098 tip 债不在本表**：`9de93b59` 不属于本 GOAL 的提交链，写进本表会被 `goal_commit_chain` 判成「台账点名了不属于本链的哈希」。那笔债**已补记**在 GOAL-098 自己的两张表里（`## CI 台账` + 迭代日志 `commits` 格）—— 反方向判据按 **GOAL 的链**点名，补记也就落在被点名的那一本账上。

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `a3ac0e47` | 零 run（**`covered_by: a7559222`**） | 覆盖：与 `a7559222` 同批推送，被合并进那一条 run | **本轮交付提交**：手稿三件（八相协议 + 真参考文献 + 数字可核）+ 产品入口开关 + 96 条新判据 + 收口验证器 80 条判词 + 宪章四处记账 + `ALL_PLAN`；**并补记 GOAL-098 的两个债**（`11e2b976` / `9de93b59`）。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `a7559222` | [M0 40657642888](https://github.com/Eswink/research-system-new/actions/runs/40657642888) / [Push 40657642253](https://github.com/Eswink/research-system-new/actions/runs/40657642253) | **全 `success`**：M0 **八 job 全 success**（`eval-gate` / `quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `collector-quality` / `container-quality`）、Push 三条 Analyze 全 `success` | **收口 tip**（只改记录 + 见证，本提交即 HEAD）：台账补 `11e2b976` / `9de93b59`（GOAL-098 的两张表）与本轮的 `a3ac0e47`，并重封见证。本地 m0（记录落盘**之后**跑）：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `ab2837a7` | [M0 40664158717](https://github.com/Eswink/research-system-new/actions/runs/40664158717) / [Push 40664157575](https://github.com/Eswink/research-system-new/actions/runs/40664157575) | **逐 job 全 `success`**（run 级 conclusion 首轮为 `cancelled`，见下）；Push 三条 Analyze 全 `success` | **收口 tip**（只改记录 + 见证，本提交即 HEAD）：CI 台账写入两条 run 的真实读数 + 重封见证。**如实登记这个形态**（不是绿、也不是红）：首轮 attempt 1 里 `quality-windows-latest` 被标 `cancelled` 而其余七 job 全 `success`；`rerun-failed-jobs`（HTTP 201）后该 job **`success`**，此刻八个 job 逐条全 `success`、**run 级 conclusion 也是 `success`（attempt 2）**。归类：**基础设施（iii）**，不改代码、不改门禁；判据以**逐 job 结论**为准 |
| `a19fdd0e` | [M0 40694293516](https://github.com/Eswink/research-system-new/actions/runs/40694293516) / [Push 40694291615](https://github.com/Eswink/research-system-new/actions/runs/40694291615) | **全 `success`**：M0 **八 job 全 success**（`eval-gate` / `quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `collector-quality` / `container-quality`）、Push 三条 Analyze 全 `success`；run 级 conclusion 也是 `success` | **收口 tip**（归档两树判词 + 重封见证，本提交即 HEAD）：两树判词归档进树、「引用了就必须在树」判据扩到那两份归档、CI 台账写入 `ab2837a7` 的真实形态、80/82 两个读数分开登记。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `be663854` | [M0 40703294208](https://github.com/Eswink/research-system-new/actions/runs/40703294208) / [Push 40703293395](https://github.com/Eswink/research-system-new/actions/runs/40703293395) | **全 `success`**：M0 **八 job 全 success**、Push 三条 Analyze 全 `success`；run 级 conclusion 也是 `success` | 收口 tip（ledger `a19fdd0e` + 重封见证；本行由下一个提交补记）。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `32304d96` | 零 run（**`covered_by: f95d3143`**） | 覆盖：与后一个提交同批推送 | **把 frontmatter `status` 改为 `ACHIEVED`**（只改记录 + 见证）：使 099 真的进入 `test_terminal_goals_have_closeout_verifiers.py` 的受判面（`_TERMINAL` 只认 `ACHIEVED`/`BLOCKED`/`ABANDONED`）—— 受判面因此从 3 个 GOAL 变成 4 个。**该提交同时抓到本人一处真记账错**：我把 GOAL-098 的 tip `9de93b59` 写进了本 GOAL 的台账，而它不在本链 ⇒ `goal_commit_chain` 判「台账点名了不属于本链的哈希」；已改成表外散文说明（债补在 GOAL-098 自己的两张表里） |
| `f95d3143` | 零 run（**`covered_by: 441779a3`**） | 覆盖：同批推送 | ledger 上一条（`32304d96`）的 ACHIEVED 翻转 + 重封见证（只改记录）。它是「台账行本身也是提交」这条链上的常规一环：补记前一个非 HEAD 提交，自己的行由下一个补记 |
| `441779a3` | 零 run（**`covered_by: 548790b5`**） | 覆盖：同批推送 | ledger `f95d3143` + 重封见证（只改记录） |
| `548790b5` | 零 run（**`covered_by: <HEAD>`**） | 覆盖：同批推送 | ledger `441779a3`、**一次补完本链剩余的全部非 HEAD 提交**（避免「补一行就多出一个非 HEAD 提交」的递归：本次提交自身即 HEAD，而 `goal_commit_chain` 按构造豁免 HEAD —— 一个提交装不下自己的哈希）|
| `299639fd` | [M0 40736050483](https://github.com/Eswink/research-system-new/actions/runs/40736050483) / [Push 40736049925](https://github.com/Eswink/research-system-new/actions/runs/40736049925) | **全 `success`**：M0 **八 job 全 success**、Push 三条 Analyze 全 `success`；run 级 conclusion 也是 `success` | **本 GOAL 的链在此收口**（本提交即 HEAD）：一次补完所有非 HEAD 提交、`status` 已置 `ACHIEVED`。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False` |
| `7df35741` | [M0 40744287535](https://github.com/Eswink/research-system-new/actions/runs/40744287535) / [Push 40744287820](https://github.com/Eswink/research-system-new/actions/runs/40744287820) | **全 `success`**：M0 **八 job 全 success**、Push 三条 Analyze 全 `success` | **收口 tip**（只改记录 + 见证）：`299639fd` 之后的重封。当时它是 HEAD ⇒ 结构例外；**序 68 的归档推送把它推离 HEAD 后，反方向判据立刻点名它**（`1 个提交不在台账（链 12 个，台账 10 个）`），本行即按该点名补记。**注意**：`b0eb3ff2`（序 68 的归档提交）也点名 `goal099` ⇒ 同属本链，但它是 HEAD ⇒ 豁免；下一轮会按同样的点名补记 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261028-099 | `a3ac0e47` → `a7559222` → `ab2837a7` → `a19fdd0e` → `be663854` → `32304d96` → `f95d3143` → `441779a3` → `548790b5` → `299639fd` → `7df35741`（本 GOAL 的链全部收录；**收尾时一次补完全部非 HEAD 提交**，最后一个自身即 HEAD —— 按构造豁免，否则「补一行」会递归出一个新的非 HEAD 提交）。**序 68 归档轮又补了一个**（`7df35741`）：归档提交本身也点名 `goal099`，但它是 HEAD ⇒ 豁免。**继承的 GOAL-098 tip 债**已补记进 **GOAL-098** 的两张表（那个哈希不属于本链，写在本书会被`goal_commit_chain` 判成越界） | EC-01：38 例全过（含两条真文件按压）；EC-02：24 例全过；EC-03：22 例全过（20 + 2；含两条真文件按压 + 编号顺序判据）；EC-05：收口验证器 **80 条判词全过** + 4 例按压证明它会红；EC-04：产品入口 7 例 + 同一 run 字面逐字节 5 例（`requires_docker` 真容器）；元数据普查取证落盘 | **M0 全绿**（两提交逐 job `success`）+ **TWO-TREE PASS**（两棵各 80 条判词、`sha256` 相同 `44332689…`） | 修掉 6 处**判据自身**的错（不是产品缺陷，逐条见下）：① `cross_phase_inputs` 是三元组不是对象；② 三条跨相边的性质全为 `RETRIEVED`（既有 `producer_trust_label` 的读数，我先猜成 GENERATED）；③ `assert plan is None` 是**假判据**（`compile_protocol` 只在 DAG 阻塞时返回 None，跨相 ERROR 随计划携带）；④ 正文数字扫描把**汇编器写的抬头与节号**算成模型违规；⑤ 缺 `authors` 时填占位符会让「缺失计数」**自己沉默**（判据与被防的动作改同一个量）⇒ 改判结构面（渲染里不得出现占位符词）；⑥ 产品入口跨两次 run **不可能**逐字节相同（uuid + 随机臂序）⇒ 拆成「产品入口判内容面」+「同一 run 判字面字节」 | `W-1` 编号化提示词未做；`W-3` 臂序既有性质；`W-4` `retmax=3`；`W-5` 叙述质量无判据 | 下一轮：① 把 `[1]`…`[n]` 写进检索摘录段（要动共用渲染器 ⇒ 需回归另外七份协议）；② `retmax` 配置化；③ `Related Work` 从单条 `nearest_prior` 扩到主题聚类 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-28 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 67）。读取器对 GOAL-098 `REFUSED RESIDUAL_EMPTY` ⇒ 记拒绝码与理由、改以正文为准。EC-01/02/03/04 已 PASS；EC-05/06 待收口。 |
| 2026-10-28 | **ACHIEVED（CI 全绿）** | **六个 EC 全 PASS**。收口验证器 **80 条判词全过 / 零 FAIL**（两树那次；归档文件加入判据后本地 **82** 条，同样零 FAIL）；三条**真文件按压**证明它会红（摘本 GOAL 的 id / 把 `下一级` 冒认成「已判」/ 给手稿合约加 `report: {}`），另一文件 4 例全过。本轮新判据合计 **96 例**（收集数：38 编译 + 24 结构 + 22 参考文献 + 5 同一 run 字节 + 7 产品入口）；既有报告套件 41 例仍全过（开关缺省关，五处既有调用点逐字沿用旧语义）。**CI 逐 job 全绿**：`a3ac0e47`/`a7559222` 的 run 八 job 全 `success`；`ab2837a7` 的 run 首轮 `quality-windows-latest` 记 `cancelled` ⇒ `rerun-failed-jobs` 后八 job 全 `success`、run 级也 `success`（attempt 2）。**两树复检 `TWO-TREE PASS`**：两棵各 **80** 条判词、`sha256` **相同** `44332689c5bd693a…`，判词归档进树（`evidence/GOAL-20261028-099-two-tree-{current,clean}.txt`，`cmp` 逐字节一致）。**读数先后如实登记**：那一次两树跑的时候验证器是 **80** 条；之后我把两份判词归档文件加进「引用了就必须在树」那条判据 ⇒ 本地现在是 **82** 条（多出的 2 条 = 两份归档在位，本地零 FAIL）。**两树那次的 80 条读数不追改成 82**（那是另一次读数）。 |
