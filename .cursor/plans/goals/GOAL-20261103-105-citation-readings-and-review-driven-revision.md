---
id: GOAL-20261103-105
slug: citation-readings-and-review-driven-revision
title: 引用充分性结构读数 + retmax 缺省抹平修复 + 判词驱动改稿
status: ACHIEVED
created_at: 2026-11-03
updated_at: 2026-11-03
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    沿用用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 .env。
objective: >-
  把 §7 判定为「可机械判但未实现」的第 4 项（引用是否充分）落成**结构读数**（三个纯读数、
  默认不判负、三阈值留 None），修掉 `retmax` 的**缺省抹平**缺陷并把它升到协议相级，
  并把「判词内容 → 改稿动作」之间补上一条**可判连接**（实词重叠，且空真必须点名）。
exit_criteria:
  - id: EC-01
    criterion: >-
      `packages/application/deliverable/citation_sufficiency.py` 产出三个纯读数：
      ① 每句的引用数（按 `manuscript_quality._SENTENCE_SPLIT` 切 introduction/results/discussion）；
      ② 每条被引条目在全稿被引几次；③ 单支撑节（某节唯一引用编号在该节只出现一次且全稿只被引一次）。
      `enforce=False` 缺省只返回读数不抛错；三个具名常量 `MIN_MARKS_PER_SENTENCE` /
      `MIN_CITATIONS_PER_REFERENCE` / `MIN_SUPPORT_PER_SECTION` 缺省**全部 None**；
      `NOT_JUDGED` 五项逐字不动。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_citation_sufficiency.py -q`
      四条判据绿：① 三个读数正例逐项等于期望值；② 加一条引用 ⇒ 两个读数都变（读数真从字节来）；
      ③ `enforce=False` 时「每句 0 引用」正文不抛错；④ 三常量默认全 None 且非 None 时 docstring
      必须给出标定语料来源。反证臂实测留证。
    status: PASS
  - id: EC-02
    criterion: >-
      三个读数透出到 `manuscript.md` 的脚注（`manuscript.py:_footnote_lines`，与
      `**Who wrote which face (recorded, not asserted)**` 同一位置）；一条判据断言脚注里
      三个读数的数值与 `citation_sufficiency` 函数返回值**逐字一致**（不是「脚注里有个数字」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_manuscript_assembler.py
      -q` 含新判据；该判据从 `build_manuscript` 产出的 markdown 里取出脚注行，与直接调用
      `citation_sufficiency` 的返回值比对相等。
    status: PASS
  - id: EC-03
    criterion: >-
      ① **修 `retmax` 缺省抹平**：`ProjectSettings.retmax: int | None = None`、`_retmax_of`
      缺省返回 `None` ⇒「未声明」成一等事实，「声明 3」与「未声明」可区分；
      `test_project_settings_defaults_retmax_to_three` 同轮改写为「未声明 ⇒ None」；
      ② **协议相级**：`ProtocolPhase.run_chain_arguments`（带缺省值）+ `CompiledPhase`
      对应字段 + `schemas/protocol.schema.json` 的 `$defs.phase` 属性 + `SessionSpecContext`
      搬运 + `execute_run_chain_capabilities` 处决策；
      ③ 优先级最终形态：**显式参数 > 协议相级 > 项目声明（仅当已声明）> RESEARCHOS_RETMAX > 3**。
    verify: >-
      三条缺陷判据（`tests/application/test_retmax_project_setting.py`）：① `RESEARCHOS_RETMAX=9`
      + 项目未声明 ⇒ 运行期调用表 `[9]`；② `retrieval_calls(7)` + 未声明 ⇒ 运行期 `[7]`；
      ③ 项目显式声明 5 压过 env。协议相级三条（`tests/application/test_retmax_protocol_phase.py`）：
      ① 协议 `retmax: 5` ⇒ tool-args 制品里 `retmax == 5`；② 不声明 ⇒ 逐字节回到第一步修完后的
      各臂行为；③ 非法值（`0`/`-1`/`101`/`"three"`）点名拒绝且判词指出「协议相级」。
    status: PASS
  - id: EC-04
    criterion: >-
      判词驱动改稿：`validate_action_references` 增加 `points` 参数（由
      `review_points.review_points_of_run` 取，调用点 `revision_closure_step` 已有三件）；
      每条 `action_taken` 必须与它回应的那条 `ReviewPoint.text` 有至少一个实词重叠
      （复用 `manuscript_quality.content_words`）；point 文本无实词时**点名**该点不可比较
      （不许静默通过）。docstring 写明射程：「不是无关」≠「解决了那个问题」。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_revision_review_points.py
      -q` 四条绿：① 正例含该 point 实词 ⇒ 通过；② 零重叠 ⇒ 判红并点名 `point_id`；
      ③ `content_words` 换成恒空集 ⇒ 判据全红（证明确实在比词）；④ 无实词 point ⇒ 点名不可比较。
    status: PASS
  - id: EC-05
    criterion: >-
      文档同步：`docs/architecture/MANUSCRIPT_QUALITY.md` §6 残余里「语义支持未判」那条补一句
      「第 4 项已产出结构读数（`citation_sufficiency.py`）但**充分性仍未判**（阈值待真实语料）」。
      §7 判定表**逐字不动**（5 条判据盯着）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_manuscript_quality_strong_criterion.py
      -q` 5 条仍全绿（含 `len(NOT_JUDGED) == 5`）；文档 grep 命中新句且 §7 表逐行未变。
    status: PASS
  - id: EC-06
    criterion: >-
      收口资产：`tools/verify_goal105_closeout.py` + `tools/goal105_closeout_assertions.py`，
      登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 `_VERIFIERS`。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal105_closeout.py --root . --verdict-only`
      全 PASS、判词不含绝对路径；两条登记判据在 m0 里过；脚本过 ruff / mypy / 规模门。
    status: PASS
  - id: EC-07
    criterion: >-
      宪章记账：程序表追加序 73（紧接序 72、**不留空行**）；阶梯「报告」行 `当前级` 加
      「引用充分性有结构读数」、「复检」行 `当前级` 加「改稿与评审点有可判连接」并各自收录本
      GOAL；两行 `下一级` **逐字不动**（结构读数 ≠ 叙述质量已判；词重叠 ≠ 判词改写了立题）；
      进展/修订各追加一行（5 格、表内连续，各 3 行）。
    verify: >-
      `tests/tooling/test_mainline_program_is_intact.py`、`test_mainline_research_ladder_advances.py`、
      `test_mainline_archive_convention.py` 全绿；收口验证器的阶梯判据断言两行 `下一级` 未变。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 改写 `test_project_settings_defaults_retmax_to_three`（它钉住的正是缺陷），但须同轮新增「未声明 ⇒ 不施加」判据
    - 给 `ProtocolPhase` / `CompiledPhase` 加带缺省值的字段并同步 schema（只加字段不加相）
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - "不得给「引用充分性」拍阈值（仓内零真实语料；阈值必须留 None 并写明标定条件）"
    - "不得把结构读数写成「叙述质量已判」（§7 的两条反向误读禁令逐字有效）"
    - "不得用「再叠一层覆盖」修 retmax 优先级（未声明必须是一等事实，不是缺省的副作用）"
    - 改 `.github/workflows/**`（本轮关闭，任何改动停 BLOCKED）
    - 改 `NOT_JUDGED` 五项 / 改 §7 判定表
    - 改十一相相集 / 新增角色或能力
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（§9 姿态只放开点名项）
  - 同一失败签名超过 fix_policy 上限
  - 新增第三方依赖
child_plans:
  - .cursor/plans/tasks/PLAN-20261103-105-citation-readings-and-review-driven-revision.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261103-105-citation-readings-and-review-driven-revision.md
memory_entries:
  - .cursor/memory/entries/MEM-20261103-239-a-field-default-is-not-a-declaration.md
---

# GOAL-20261103-105 —— 引用充分性结构读数 + retmax 缺省抹平修复 + 判词驱动改稿

## 目标与退出标准

承用户 goal-mode 指令（序 73）。三件互相独立、各有边界：

**靶子 1｜引用充分性的结构读数（不拍阈值）。**
`MANUSCRIPT_QUALITY.md` §7 用四条依据（P1 确定性 / P2 反证可写 / P3 不需外部知识 /
P4 不冒充语义）把 `NOT_JUDGED` 五项逐项判过：1/2/3 只能人评（缺 P3），4/5 可机械判但未实现。
本轮**实现第 4 项**。仓内**零真实手稿语料**（实测：排除 `.venv` / `node_modules` 后
`manuscript*.md` 0 命中、`data/e2e.db` 的 `artifacts` 表 0 行、所有手稿字节都是夹具且最大
209 词）⇒ 任何「该引 3 篇」类的阈值都是**编造**。因此本靶子只产**读数**，三阈值留 `None`。

**靶子 2｜`retmax` 缺省抹平（本轮唯一的既有缺陷）。**
文档口径是四级回落，产品路径实测**只有一级**：`ProjectSettings.retmax` 缺省是 `3`（不是
`None`）⇒ `_with_project_retmax` 把「未声明」施加成 `3` ⇒ env 与显式参数都被抹平：
`RESEARCHOS_RETMAX=9` 构造期 `[9]`、运行期 `[3]`；`retrieval_calls(7)` 构造期 `[7]`、
运行期 `[3]`。根因是**字段缺省值被当成声明**。

**靶子 3｜判词内容驱动改稿。**
`AuthorResponse.action_taken` 只要求引用制品名 ⇒「作者说按评审意见改了」与「改的内容与
那条意见无关」在结构上不可分。补一条**实词重叠**判据（必要不充分）。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 七个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住（需用户拍板的面）⇒ 移入「残余与未覆盖范围」的待拍板队列，
   **继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动（并发驱动）⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive（从剩余 EC + 上一轮「剩余差距」圈最小主题）→ ② 执行（WP 逐条 commit）
→ ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错（按分类）→ ⑦ 回写记录 + 下一轮。

**记录顺序（GOAL-019 的教训）**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py`（`.cursor/plans` 在
`test_reproducibility_wording.py` 的扫描面内 ⇒ 先跑门后写记录 = 记录从未被门覆盖）。

**顺序纪律（本轮）**：先做靶子 2 的第一步（既有缺陷），补上两条今天会红的判据并确认它们
**真的红过**，再动两个新面。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品 vs 测试各半）；**修产品优先，禁改断言迁就** |
| 视觉基线漂移 | `design-fidelity` / outline 判红 | 本轮不动前端 ⇒ 若红即真缺陷或环境漂移，逐类登记 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按既有配方重跑；配方不覆盖 ⇒ 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED（infra 非代码缺陷） |
| Windows quality 超时 | job 卡满预算窗口 | **已知 W-5**（预算已抬到 30 分钟）；如仍超时按 infra 重跑，不擅自改 workflow |
| Playwright 装不上 | `does not support chromium on ubuntu26.04-x64` | **W-7**：runner 已钉 `ubuntu-24.04`；若回退形态出现 ⇒ 停 BLOCKED（本轮 workflow 关闭） |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：七个 EC 全 PASS + 独立 RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检（`tools/two_tree_recheck.py --script-mode shared`，两树逐行
  \+ `sha256` 相同）+ 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## CI 台账

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `b712a989` | 与 `9c3a0186`…`f9883a2e` **同一次 push**（`head_sha` = `f9883a2e`，无独立 run） | 该推送的读数见本表 `f9883a2e` 行；**本行不冒领** | **交付 tip**（三件靶子 + 收口资产 + 宪章记账）。本地全量 m0 见证：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 failed、`tree changed during the run: False`（`ran_at_head=80a3e614`）。定向套件 139 passed；`verify_goal105_closeout.py --verdict-only` 0 FAIL；`credential_audit.py` 四面 `offenders=0` |
| `9c3a0186` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **记录提交**：GOAL-105 收口为 ACHIEVED（七条 EC PASS + 状态历史），并按 7.2 一次付清 GOAL-104 的 tip 债（为 `80a3e614` 补台账行）。**同一轮补全所有已知欠账**，不逐个补 |
| `73a45692` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **记录提交**：勾选 PLAN 的九项交付（DONE 不得留未勾选）+ 落本轮可复用事实 `MEM-20261103-239`（「字段缺省值不是声明」）并进 INDEX。治理门 `validate.py` 此前点名这两条 |
| `38b92a7b` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **台账补齐**：`9c3a0186` 在两条链上（它的正文点名 GOAL-104 的 tip 债）⇒ 两个台账各一行，同一轮编辑；同步迭代日志 `commits` 格 |
| `cc010ce3` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **重封见证**（只改 `.cursor/`）：台账写入改动了受判面内容 ⇒ 见证失配是**流程顺序**而非缺陷，按 7.1 在记录定稿后重跑 m0 并只提交见证。本地终态行 `PASS: profile=m0; 23 deterministic checks`、`PASS [` 24 行 |
| `a9c845f2` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **台账补齐**：为 `38b92a7b` / `cc010ce3` 各一行；CI 读数一律写「待推送」——那两个提交没有 run，冒领就是编造证据 |
| `33017ab8` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **两向对账的同一笔钱**：台账行的 `提交` 格与迭代日志的 `commits` 格必须互相覆盖（一个判据查台账→日志，另一个查日志→台账）|
| `1803b066` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **台账链最后一对**：`a9c845f2` / `33017ab8` 入账并把两者写进迭代日志的 `commits` 格（两个判据从相反方向读同一条链）|
| `15f9fb5b` | 与 `f9883a2e` **同一次 push**（无独立 run） | 读数见本表 `f9883a2e` 行；**本行不冒领** | **见证封印**（只改 `.cursor/`）：全量 m0 `PASS: profile=m0; 23 deterministic checks`、`PASS [` 24 行、树未变。本条由反方向判据在它被下一提交推离 HEAD 后点名补记 |
| `f9883a2e` | [M0 41687660848](https://github.com/Eswink/research-system-new/actions/runs/41687660848) / [Push 41687659678](https://github.com/Eswink/research-system-new/actions/runs/41687659678) | **M0 `success`（8/8 job success，含 `console-frontend` 与两条 `observability-overhead`）**；**Push 全 success（3/3 Analyze）** | **推送 tip**（记录 + 见证同一次提交）。本地见证终态行 `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 行、`tree changed during the run: False`）；两树复检 **73 判词**、两树 `sha256` 相同 （`195c41fe336ecfd6898e7277c216fe4483459f5af251c95ceac17674fcdf2d5e`）|
| `747a7a53` | [M0 41696234931](https://github.com/Eswink/research-system-new/actions/runs/41696234931) / [Push 41696233692](https://github.com/Eswink/research-system-new/actions/runs/41696233692) | **M0 `success`（8/8 job success）**；**Push 全 success（3/3 Analyze）** | **收口 tip**（CI 读数回填 + 见证重封）。本地终态行 `PASS: profile=m0; 23 deterministic checks`、`PASS [` 24 行、`tree changed during the run: False` |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261103-105 | `b712a989` → `9c3a0186` → `73a45692` → `38b92a7b` → `cc010ce3` → `a9c845f2` → `33017ab8` → `1803b066` → `15f9fb5b` → `f9883a2e` → `747a7a53` | 定向套件 139 passed；全量 m0 `PASS: profile=m0; 23 deterministic checks`（24 行 `PASS [`，0 failed，树未变）；`verify_goal105_closeout.py` 0 FAIL；两树复检 73 判词 `sha256` 相同 | **M0 `success` 8/8**（`f9883a2e`，含 `console-frontend`）；Push success | 首轮 m0 三条红：① typecheck = **真缺陷**（新判据自造哑对象与 Port 协议不符）② `validate_bundle` = **真缺陷**（`additionalProperties: true` 被禁）③ `python/tests` = **环境**（6 周前残留容器）④ `framework/validate` = **真缺陷**（PLAN 缺三章节）| 七条 EC 全 PASS；残余 `W-1`…`W-3` 与未覆盖 `U-1`…`U-3` 已登记 | 见§「残余与未覆盖范围」|

## 影响报告

（**实测**，非预判。）

- **Domain/API/schema**：`schemas/protocol.schema.json` 的 `$defs.phase` 新增**一个可选属性**
  `run_chain_arguments`（`additionalProperties: true`，值的范围仍由施加点一处判）⇒ 28 份出厂
  协议文档**一个字节都没改**、加载期照旧通过（`test_the_compiler_carries_it_onto_the_compiled_phase`
  断言十一相的 `run_chain_arguments` 全 `None`）。`ProjectSettings.retmax` 的缺省从 `3` 改成
  `None` 是**语义修复**，不进任何 DTO ⇒ `docs/api/openapi.m13.json` **零 diff**、
  `types.ts` 零改动、零 migration。
- **安全/凭据**：零变化（无新凭据、无新出网面、无新工具面）。协议相级 `retmax` 仍在既有的
  `literature.search` 调用面上，非法值点名拒绝（`InvalidInputError`，判词指出来源是协议相级）。
  **实测依据**（执行纪律 5.9，不是断言）：`tools/credential_audit.py` 四面 **`offenders=0`** ——
  `tracked` 5058 / 命中 105 / 放行 105 / **0**；`records` 1097 / 5 / 5 / **0**；
  `config_db` 1 / 0 / 0 / **0**；`logs` 940 / 0 / 0 / **0**。
- **兼容性/迁移**：零 migration。**需登记的行为变化**：`ProjectSettings.retmax is None` 现在是
  「未声明」的**唯一**表示（此前 `3` 兼作两种含义）。既有构造点零改动（它们不传该字段），
  但语义从「声明 3」变成「未声明」—— 这正是修复。
- **上游**：零依赖变化。

## 残余与未覆盖范围

（**没做到**的那部分，逐条明写。空着等于宣称「没有缺口」，那是伪造验证证据。）

### 残余（本轮已交付里仍然存在的缺口）

- `W-1`｜**三个读数没有阈值，也判不出「充分」**：`MIN_MARKS_PER_SENTENCE` /
  `MIN_CITATIONS_PER_REFERENCE` / `MIN_SUPPORT_PER_SECTION` **全部 `None`**。仓内**零真实
  手稿语料**（`manuscript*.md` 0 命中、`data/e2e.db` 的 `artifacts` 0 行、最大夹具 209 词）
  ⇒ 任何数字都是编造。`uncalibrated_thresholds()` 只保证「填了值必须有标定来源」，它**不**
  保证那个来源是真的够用。
- `W-2`｜**词重叠是必要不充分**：`action_taken` 与 `ReviewPoint.text` 共享一个实词就通过 ——
  「已按 reproducibility 相关意见修改」与一个讲 reproducibility 的评审点重叠，但正文可能
  一个字都没改对。判「解决了那个问题」需要语义蕴含 ⇒ 人评。射程已写进 docstring 与阶梯。
- `W-3`｜**协议相级只有 `retmax` 一个键有解释器**：`run_chain_arguments` 的 schema 是
  **封闭对象**（`additionalProperties: false`，只声明 `retmax`）⇒ 写错键名（如 `topk`）在
  **加载期**被点名拒绝，不会静默无效。缺口收窄为「想表达别的调用参数时，schema 里没有那个
  键」—— 那是**明确的拒绝**，不是静默失效。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1`｜**协议相级只能写 `retmax`，不能写别的调用参数**：`literature.read` 的 `pageSize`、
  各 provider 自己的分页/过滤参数都不在射程。
- `U-2`｜**引用读数的「分布」只有本 run 一份**：三个读数是单份手稿的计数，跨 run 的分布
  比较（标定阈值唯一的正经来源）没有做。
- `U-3`｜**`uncalibrated_thresholds()` 只查「来源字符串在 docstring 里」**：它证明不了那个
  来源真的是一份真实语料。文本判据的上限，与 `UNCONSUMED.md` 的理由判据同类。

### 声称边界（**不得宣称**的事）

- `R-1`｜**不得宣称「引用充分性已判」**：只有三个结构读数，阈值全 `None`。
  `NOT_JUDGED` 第 4 项**仍在**那个常量里（移出它 = 冒充，且会让 `len(NOT_JUDGED) == 5` 判红）。
- `R-2`｜**不得宣称「判词驱动了改稿」**：判据只证明回应与评审点**不是无关**
  （`this criterion proves 'not unrelated', never 'solved'`）。
- `R-3`｜**不得宣称「`retmax` 已完全配置化」**：协议相级只解释 `retmax` 一个键（`W-3`）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-03 | ACTIVE | 建档：序 73；七个 EC |
| 2026-11-03 | ACHIEVED | 七条 EC 全 PASS；`RECHECK-20261103-105` PASS；全量 m0 `PASS: profile=m0; 23 deterministic checks`；交付提交 `b712a989` |
