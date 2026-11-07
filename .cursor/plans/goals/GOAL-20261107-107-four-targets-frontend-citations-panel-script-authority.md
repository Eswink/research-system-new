---
id: GOAL-20261107-107
slug: four-targets-frontend-citations-panel-script-authority
title: 四靶并行：前端补全 / 引用分布 / 外部评审面板 / 脚本执行权威
status: ACHIEVED
created_at: 2026-11-07
updated_at: 2026-11-07
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-07 明文拍板「以上 4 个选项都做，反正是实现我们的终极目标，反复迭代它就行」——
    即授权本轮同时推进四个候选靶子（含**外部评审面板**，它引入付费 / 非确定性模型调用；
    以及 **`W-3` 脚本执行权威**，它触及 §9 默认 deny 的安全姿态）。该授权范围是
    **建机制**，不是「出厂启用」（见 fix_policy.forbidden 第 1 条）。
    沿用用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 .env。
objective: >-
  四件互相独立、各有反证的工作一次推进：① **前端补全**——把已有后端接成可用界面（改稿
  v1/v2 并排 diff、程序页建程序 + 逐轮决定时间线 + `cited_facts` 展开）；② **引用充分性
  分布读数**——把 GOAL-105 留下的三个 `None` 阈值变成「有语料就能标定」的一条命令，但
  **仍不拍阈值**（n=1 < 3）；③ **外部评审面板**——把 §7 判定「只能人评」的三项交给独立模型，
  判词落 `ReviewFinding` 且 `reviewer_model` 可归因，`NOT_JUDGED` 五项逐字不动；
  ④ **脚本执行权威**——把实验脚本从「从 3 个出厂脚本里选」推到「可安全放行模型产出」，
  并**先修**「策略约束声明了但零处执行」这条既有缺陷；出厂默认仍是白名单。
exit_criteria:
  - id: EC-01
    criterion: >-
      改稿 diff 视图：`ReportsPage` 的手稿面板用**既有** `api.artifactDiff` 把
      `manuscript.md` 与 `manuscript_v2.md` 并排呈现（左=v1、右=v2，左右 id 由
      `manuscript_v2.md` 的 `supersedes` 决定），复用 `ArtifactDiffPanel` 的行渲染
      （新增/删除着色）而**不新写 diff 算法**；不可比 / 超上限时如实显示原因。
    verify: >-
      `pnpm --dir apps/web lint && typecheck && test && build` 全绿；
      `pnpm --dir apps/web test:e2e` 里新增用例断言：给定含 v1+v2 的 run，
      `data-testid="revision-diff"` 出现且含 `ADDED` 与 `REMOVED` 行；
      反证：只有 v1 的 run ⇒ 该块**不渲染**（不是空块）。
    status: PASS
  - id: EC-02
    criterion: >-
      程序页补全：`ProgramsSection` 加三件——① 建程序表单（`POST /projects/{id}/programs`，
      并把 `create` 从 `programsClient` 导出进 `client.ts`）；② 逐轮决定时间线
      （读 `GET /programs/{id}` 的 `decisions[]`：`after_index` / `kind` / `reason` /
      `decided_at`）；③ `cited_facts` 逐条可展开。同时补齐 TS 类型漂移：
      `ProgramCreateDto` 加 `max_attempts_per_index` + 四个 `human_gate_*`；
      `ProgramDetailDto` 加 `max_attempts_per_index` / `gate_nudge_after_seconds` /
      `human_gate_hybrid`（以 `services/api/dto/programs.py` 为准）。
    verify: >-
      上面四条命令全绿；e2e 断言建程序表单提交后列表多一行、决定时间线渲染
      `after_index` 与 `kind`、`cited_facts` 默认收起点击后逐条可见；
      反证：无 decisions 的程序 ⇒ 时间线显示空态而非伪造一行。
    status: PASS
  - id: EC-03
    criterion: >-
      设计基线重录：EC-01 / EC-02 新增的 DOM 让 `design-outline-guard` 与像素基线
      失配 ⇒ 按既有配方重录两套（win32 单路由 + linux 容器像素），
      `verify_linux_outlines` 跨平台一致。**阈值一个字不动**（`maxDiffPixels: 196`、
      整页 2%）。
    verify: >-
      `pnpm --dir apps/web test:e2e`（含 design-fidelity / design-outline-guard）全绿；
      `apps/web/tests/e2e/design-outlines.json` 的 `portfolio-projects` 与 `reports`
      条目更新且含新增 testid。
    status: PASS
  - id: EC-04
    criterion: >-
      新建 `packages/application/deliverable/citation_distribution.py`（确定性纯函数：
      零出网、零模型、零时钟、不读文件系统）：`collect_readings`（多份手稿 → 三个读数）、
      `summarize`（分布：计数 / 中位数 / 极值，**不产出阈值建议**）、
      `calibration_gate`（返回「语料不足（n<`MIN_CORPUS`=3）」或「可标定」，并点名缺什么）。
      **`MIN_MARKS_PER_SENTENCE` / `MIN_CITATIONS_PER_REFERENCE` / `MIN_SUPPORT_PER_SECTION`
      三个常量保持 `None`。**
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_citation_distribution.py -q`
      8 passed（四条判据 + 三条门边界 + 短语料参数化）。**实测读数**（2026-11-07 探针）：
      仓内真实手稿 **2 份**（`3142b142` 57 句 / 6 标记 / 3 条；`6446406a` 39 句 / 9 标记 / 3 条），
      `calibration_gate` 判「不足：2 of 3」⇒ 阈值仍全 `None`。反证臂按压留证：把
      `marks=sum(...)` 改成常量 `6` ⇒ **恰好 2 条**判红（`test_adding_one_citation_moves_both_readings`
      与摘要分布那条），复原后 8 passed。
    status: PASS
  - id: EC-05
    criterion: >-
      分布读入 `tools/` 入口：一个脚本扫树内全部**真实** `manuscript.md`（排除测试夹具与
      `node_modules` / `.venv` / `scratch`），调 `citation_distribution` 输出读数与 gate 结论。
      该脚本必须过四道门（ruff format / ruff check / mypy strict / 450 行 + 50 行函数）
      并登记进 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`。
    verify: >-
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 8 passed；实跑
      `tools/citation_corpus_report.py --root .` 对当前树输出 **2 份**手稿与 `gate: CLOSED`。
      **语料来源不是 glob `manuscript*.md`**（实测 0 命中）：真实手稿是内容寻址 blob，
      按 run 库 artifact id 的 `:manuscript.md` 后缀认、按 digest 到 blob store 取字节。
    status: PASS
  - id: EC-06
    criterion: >-
      新建 `packages/application/deliverable/manuscript_panel.py`：`PANEL_RUBRICS` 是**闭集三条**，
      逐条对应 `NOT_JUDGED` 的第 1/2/3 项（复用 `RubricSpec` 形状）；
      `panel_prompt` 产出提示词；`parse_panel_verdict` 给出三态
      `REFUTED` / `SUPPORTED` / `AMBIGUOUS`，**设施失败单独一类**
      （`PANEL_UNAVAILABLE`），绝不折算成 `SUPPORTED`（照 `evaluation/reviewer.py:130-140`）。
      模型调用**直调** `ModelGateway.complete`（照 `report_narrative_task.py:llm_narrator`
      已验证的形态），不经 AgentRuntime。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_manuscript_panel.py -q`
      含：① 三条 rubric 与 `NOT_JUDGED[:3]` 逐条对应；② 正例三态各解析正确；
      ③ **反证**：网关抛错 ⇒ 判词是 `PANEL_UNAVAILABLE` 而**不是**任何一态；
      ④ **反证**：把三态闭集改空 ⇒ 解析判据全红（证明它真在校验）。
    status: PASS
  - id: EC-07
    criterion: >-
      面板判词落 canonical 且可归因：写 `ReviewFinding`（`review_type="manuscript_panel"`、
      `reviewed_by="model:<endpoint>/<model>"`、`reviewer_model="<endpoint>/<model_name>"`），
      经既有读面 `GET /runs/{id}/reviews` 可见，前端 `ReviewPanelSection` 显示「谁判的」。
      **不新增路由**、不改 DTO 契约形状。
    verify: >-
      `tests/application/test_manuscript_panel.py` 与 `tests/api/` 相关套件绿；
      两条反证：① 无 `reviewer_model` 的 finding ⇒ 聚合时点名「不可归因」且**不进票**
      （复用 `panel_verdict._eligible` 口径）；② 面板判词**不**产生 `Decision`
      （advisory 边界：断言 `Decision` 记录数与面板运行前相同）。
    status: PASS
  - id: EC-08
    criterion: >-
      文档同步：`docs/architecture/MANUSCRIPT_QUALITY.md` §7 加一句「第 1/2/3 项已委派给
      **带归因**的外部评审面板（`manuscript_panel.py`），本口径仍不判」；
      **`NOT_JUDGED` 五项逐字不动**（`len(NOT_JUDGED) == 5` 与 §7 表格 5 行两条判据仍绿）。
    verify: >-
      `tests/tooling/test_manuscript_quality_strong_criterion.py` 5 条全绿；
      `tests/application/test_citation_sufficiency.py::test_the_fifth_item_stays_in_not_judged` 绿；
      文档 grep 命中新句。
    status: PASS
  - id: EC-09
    criterion: >-
      新建 `packages/application/experiments/script_authority.py`：`ExecutionAuthority` 闭集
      `SHIPPED`（白名单文件 + digest pin）| `AUTHORED`（模型产出）；
      `authority_for(script_path, digest)` 返回权威判定；`AUTHORED` 需要一份**显式声明**
      才放行（`authored_allowed: bool`，出厂默认 `False`）。`design_script._refuse_unsafe_path`
      的绝对路径 / `..` / 盘符拒绝**逐字保留**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_script_authority.py -q`
      含：① 白名单三条 ⇒ `SHIPPED`；② 白名单文件的 digest 变了 ⇒ 点名拒绝（pin 生效）；
      ③ `AUTHORED` 在未声明时点名拒绝；④ 越界路径仍被既有函数拒绝（回归臂）。
    status: PASS
  - id: EC-10
    criterion: >-
      **策略约束真的被执行**：`sandbox_required` / `path_prefix` / `max_seconds` 三者今天由
      `policy/native.py` 返回但**零处消费**。在实验执行边界
      （`experiments/governed.py` 的 `_enforce_policy`）接上：沙箱未声明 ⇒ 拒；
      写入路径越出 `path_prefix` ⇒ 拒；`max_seconds` 生效于执行超时。
      **不改任何策略规则文件**（只让既有声明生效）。
    verify: >-
      `tests/application/test_experiment_script_authority.py` 与
      `tests/application/test_governed_experiment_*` 全绿；
      三条反证各判红并点名缺哪条约束（无沙箱 / 越界路径 / 超时）。
    status: PASS
  - id: EC-11
    criterion: >-
      对抗性反证臂四条（没有它，判据不可证伪）：构造「恶意」生成脚本夹具，断言
      ① `AUTHORED` 关闭 ⇒ 点名拒绝；② 开启但无沙箱声明 ⇒ 拒；③ 开启但写入越界 ⇒ 拒；
      ④ 开启但执行超 `max_seconds` ⇒ 拒（用可控的等待或注入时钟，不真等）。
    verify: >-
      `tests/application/test_experiment_script_authority.py` 的四条用例各自判红；
      按压后必须确认它们**真的红**（两向按压留证）。
    status: PASS
  - id: EC-12
    criterion: >-
      文档同步：实验脚本白名单说明补 `SHIPPED` / `AUTHORED` 两面与出厂默认；
      `docs/frontend/` 若有页面新增则同步（EC-01/02 若无新路由则只记 UI 行为）。
    verify: >-
      `tests/tooling/` 相关文档判据绿；grep 命中新句。**如实登记**：实验脚本白名单没有独立文档页（说明住在 `design_script.py` 的模块 docstring 里），因此「文档同步」这一项在本轮只落到 `MANUSCRIPT_QUALITY.md` §7 那一句。
    status: PASS
  - id: EC-13
    criterion: >-
      收口资产：`tools/verify_goal107_closeout.py` + `tools/goal107_closeout_assertions.py`，
      登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 `_VERIFIERS`
      与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal107_closeout.py --root . --verdict-only`
      全 PASS 且判词不含绝对路径；四条登记判据在 m0 里过。
    status: PASS
  - id: EC-14
    criterion: >-
      宪章记账：程序表追加序 75（`轴 = 深度+质量`、`能力域 = 报告`、紧跟序 74 **不留空行**）；
      阶梯「报告」行 `当前级` 记本轮实际推进、`下一级` **逐字不动**（结构读数 / 面板判词
      ≠ 叙述质量已判）；「实验」行同理（`AUTHORED` 机制 ≠ 生产级已启用）；
      进展 / 修订各追加一行（5 格、表内连续）。**归档已在 2026-11-07 的
      `320faa78` 完成**（进展移序 72 / 修订移序 72），本轮追加后两表各 3 行，不再归档。
    verify: >-
      `tests/tooling/test_mainline_program_is_intact.py`、
      `test_mainline_research_ladder_advances.py`、`test_mainline_archive_is_continuous.py`、
      `test_record_tables_are_structurally_sound.py` 全绿；
      收口验证器断言两条阶梯行的 `下一级` 未被改写。
    status: PASS
budget:
  max_cycles: 60
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 让既有策略约束（sandbox_required / path_prefix / max_seconds）在执行边界生效
    - 重录设计基线（outline + 像素），阈值一个字不动
    - 补 TS 类型以对齐服务端 DTO
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - "不得为绿而把 AUTHORED 默认打开（出厂默认仍走白名单三条；启用属用户决定）"
    - "不得因实现面板而删 NOT_JUDGED 任何一项（五项逐字不动）"
    - "不得把面板判词折算成 Decision（advisory 边界照 panel_verdict.py 三条）"
    - "不得用「语料不足就填个合理值」的方式拍阈值（MIN_* 三个常量保持 None）"
    - 改 `.github/workflows/**`（本轮关闭，任何改动停 BLOCKED）
    - 改十一相相集 / 新增角色或能力
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（§9 姿态只放开点名项）
  - 同一失败签名超过 fix_policy 上限
  - 新增第三方依赖
  - EC-10 的约束执行面射程超出清单（例如要连同 preflight/policy_check.py、tool_plane/resolver.py、domain/acceptance.py 一起改）⇒ 停 BLOCKED 点名，不缩判据
  - 面板的 live 判据在真实中转站上失败率过高，使判据不可用
child_plans:
  - .cursor/plans/tasks/PLAN-20261107-107-four-targets.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261107-107-four-targets.md
memory_entries: []
---

# GOAL-20261107-107 —— 四靶并行：前端补全 / 引用分布 / 外部评审面板 / 脚本执行权威

## 目标与退出标准

承用户 2026-11-07 goal-mode 指令「以上 4 个选项都做」。四件互相独立、各有反证。

**为什么这四件**（勘察读数，不是推断）：

- 阶梯七个域的 `下一级` 里，**检索 / 计划 / 复检 / 迭代 / 报告** 全部卡在同一个不可判点
  （GOAL-082 EC-04：模型是否采纳内容不可机械判）。唯一不被它卡住的杠杆是**叙述质量轴** ——
  正由靶子 A（外部评审面板）开启。
- 与北极星更直接相关的一条：**实验脚本只能从 3 个出厂脚本里选**
  （`packages/application/experiments/design_script.py:47-51`），「自动设计实验」卡在
  「选择级」。而更严重的既有缺陷是策略约束 `sandbox_required` / `path_prefix` /
  `max_seconds` **声明了但零处执行**（`packages/application/policy/native.py:39-44`
  只返回 `PolicyEvaluation(constraints=...)`，全仓无消费方）⇒ 靶子 D 的第一件事。
- 前端两件（C）是纯补全：后端 100% 就绪，零迁移、零模型调用。

### 靶子顺序（风险递增、价值递增）

| 顺序 | 靶子 | EC | 理由 |
|---|---|---|---|
| 1 | C 前端补全 | EC-01…03 | 最小、确定性、后端已就绪；先把「后端做完了但用户在页面上看不到」这一类收掉 |
| 2 | B 引用分布 | EC-04…05 | 纯确定性函数；把 GOAL-105 的 `W-1` 从「无解」变成「有命令」 |
| 3 | A 外部评审面板 | EC-06…08 | 引入模型调用（用户已授权）；落既有读面 |
| 4 | D 脚本执行权威 | EC-09…11 | 安全面变更；先修「约束不生效」这条既有缺陷，再谈 `AUTHORED` |

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 十四个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住（需用户拍板的面 / 上游不可用 / 射程超清单）⇒ 移入
   「残余与未覆盖范围」，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动（并发驱动）⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive（从剩余 EC + 上一轮「剩余差距」圈最小主题）→ ② 执行（WP 逐条 commit）
→ ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错（按分类）→ ⑦ 回写记录 + 下一轮。

**记录顺序**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py` → 之后不再改树 → 提交推送。

**顺序纪律（本轮）**：先做确定性靶子（C → B），再做引入模型调用的 A，
最后做安全面的 D。每个靶子收口后才开下一个 —— 这样 CI 失败时归因面只有一处。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品 vs 测试各半）；**修产品优先，禁改断言迁就** |
| live 判据在 CI 上 skip | `requires_live_llm` 无凭据 | **这是预期**：live 判据只在操作者本地跑；skip 不是 PASS，如实记 |
| 视觉基线漂移 | `design-fidelity` / outline 判红 | 本轮**动前端** ⇒ 先按配方重录基线；重录后仍红 ⇒ 真缺陷 |
| 设计大纲守卫时序 | `design-outline-guard` 在 CI 红而本地不红 | 既有形态（GOAL-105 `W-5`）：等 loading-state 计数归零；**判据与阈值不动** |
| playwright 平台漂移 | `Playwright does not support chromium on ubuntuXX` | 既有形态（GOAL-104 `W-7`）：`console-frontend` 已钉 `ubuntu-24.04`；若再漂 ⇒ 登记 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入） | 按既有配方重跑；配方不覆盖 ⇒ 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED（infra 非代码缺陷） |
| 模型网关失败 | 超时 / 鉴权 / 中转站不可用（面板 live） | **不是判据缺陷**：落盘归类为 `PANEL_UNAVAILABLE`；不得折算成任一审评态 |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；**不得宣称安全** |

## 终止与收口

- **ACHIEVED**：十四个 EC 全 PASS + 独立 RECHECK（PASS / PASS_WITH_WARNINGS）+
  全量 m0 见证终态行 + CI 到终态 + 两树复检（`tools/two_tree_recheck.py --script-mode shared`，
  两树逐行 + `sha256` 相同）+ 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PLAN-20261107-107 | `99454d40` | e2e **112 passed**、单测 103、lint/typecheck/build 干净；两条反证臂按压（伪造 v2 / 空态分支失效）各判红 | **M0 42297143259 8/8** | 首次 m0 的 `typescript/lint` + `typescript/test` 各 1 红（根 `eslint .` 更宽、前端判词枚举被生产边界禁） | EC-01…03 收口 | 靶子 B |
| 3 | PLAN-20261107-107 | `466afd1f` | `test_citation_distribution` 8 passed；反证臂按压（marks 改常量）恰好 2 条红；语料入口实测 **2 份**手稿 | 见台账 | 手算标记数错一次（7 vs 实测 6），改断言不改产品 | EC-04/05 收口 | 靶子 A |
| 4 | PLAN-20261107-107 | `efbc19dc` | `test_manuscript_panel` 15 passed；反证臂按压（设施失败→SUPPORTED）恰好 2 条红；§7 五条判据仍绿 | 见台账 | 夹具坑两处：`fail_timeout` 只让首调失败、`PortTimeoutError` 需 `failure_category`；规模门抓 `review_manuscript` 51 行 | EC-06…08 收口 | 靶子 D |
| 5 | PLAN-20261107-107 | `227c7573` | `test_experiment_script_authority` 15 passed；反证臂按压（`AUTHORED` 默认改 True）恰好 1 条红；既有 17 条选择判据零回归 | 见台账 | `ruff format` 未跑（`python/format-check` 真红） | EC-09…12 收口 | 收口资产 |
| 6 | PLAN-20261107-107 | `e1cb5f2d` | `verify_goal107_closeout` **72 PASS / 0 FAIL**；全量 m0 见证 | 见台账 | 三条残余标记未写（验证器当场点名） | 十四条 EC 全 PASS | 收口 |
| 1 | PLAN-20261107-107 | `7b9201ae`（历史补登）→ `d6b7e4dd` | 治理门 7 条逐条修完；记录面 `tests/tooling` 1795 passed（见证除外，树已变） | **M0 42284126993 8/8 success**；Push 3/3 | 七条治理缺陷（PLAN frontmatter / 五节缺失 / RECHECK 状态词 / ALL_PLAN 投影 / 裸路径非链接） | EC-01…14 未收口（状态权威在 frontmatter）；靶子 C 的三个 EC 已在本 cycle 实现 | 下一 cycle：靶子 C 提交并取证 |

## 影响报告

（收口时填写：Domain / API / schema 变化、安全与凭据变化、兼容性与迁移风险、上游版本影响。）

## 残余与未覆盖范围

（**没做到**的那部分，逐条明写。空着等于宣称「没有缺口」，那是伪造验证证据。）

### 残余（本轮已交付里仍然存在的缺口）

- `W-1`｜**引用阈值仍然全 `None`**：语料门判 **2 of 3**（实测：`3142b142` 57 句 / 6 标记 /
  3 条；`6446406a` 39 句 / 9 标记 / 3 条）。本轮交付的是「有语料就能标定」的一条命令，
  **不是**阈值本身。差的那一份语料要靠下一次真实 run，不是靠调参。
- `W-2`｜**面板是 advisory，不判「论证成立」**：三条 rubric 给出的是**某个模型**的看法，
  不是形式论证有效性（P4：通过也不代表对）。读面必须带 `reviewer_model` 才可读成
  「谁这么认为」；`Decision` 与验收门**完全不受影响**。
- `W-3`｜**`AUTHORED` 出厂关闭，且只到「可被安全放行」这一步**：`ExecutionAuthority`
  判来源与形状，**不判**脚本写得好不好；`AUTHORED` 要真正启用还差一次安全姿态决定
  （`AUTHORED_ALLOWED_BY_DEFAULT` 改成 `True` 会让 `test_authored_is_off_by_default` 判红
  —— 那条判据就是这次决定的闸门）。
- `W-4`｜**策略约束只在实验执行边界生效**：`sandbox_required` / `path_prefix` /
  `max_seconds` 现在在 `GovernedExperimentExecutor._enforce_policy` 被读，但**工具面**
  （`tool_plane/resolver.py`）与 **preflight**（`preflight/policy_check.py`）仍不读它们。
  同一条声明在不同执行面上的效力**不一致**，这是如实登记的缺口。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1`｜**协议相级仍只解释 `retmax`**（GOAL-105 `U-1` 未推进）：`pageSize` 与各 provider
  自己的分页/过滤参数仍写不进协议。
- `U-2`｜**跨 run 的手稿比较**不在射程：分布读数逐份给值，但「同一项目第 2 轮比第 1 轮
  引得更充分吗」没有判据。
- `U-3`｜**前端只补了这两处**：`ArtifactBrowser` 的详情仍不显示 `supersedes`；
  `ReviewPanelSection` 不渲染 `aggregate_panel` 的 advisory（HTTP 路由
  `GET /runs/{id}/reviews` 只返回 `list[ReviewFindingDto]`，丢掉了 `panels` 那一层）。

### 声称边界（**不得宣称**的事）

- `R-1`｜**不得宣称「引用充分性已判」**：三个阈值仍 `None`，语料门判 2 of 3。分布读数
  不回答「该引几条」。
- `R-2`｜**不得宣称「叙述质量已判」**：面板给的是带归因的第三方判词；`NOT_JUDGED`
  五项逐字不动，§7 判定表一字未改。
- `R-3`｜**不得宣称「模型可以自己写实验脚本了」**：机制在，出厂关（`AUTHORED` 默认
  `False`）；且约束面只在实验执行边界生效（`W-4`）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-07 | ACTIVE | 建档：序 75；十四个 EC；用户拍板「四个选项都做」 |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记，含根因与修法。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `7b9201ae` | **无独立 run**（它落在 GOAL-106 的链中间，与那批提交同一次 push） | 该批的读数见 GOAL-106 台账；**本行不冒领** | **历史提交，非本轮产出**：2026-11-05 的 `fix(goal107): judge read actions and bound the untagged-commit exemption`（Bash 面守卫重写 + 绑定「未命名 GOAL 的代码提交」豁免）。它的主题把编号写成 `goal107`，而当时 GOAL-107 还不存在 —— 那是**编号笔误**，但它让 `test_goal_commit_chain_reaches_the_ledger`按主题归因时把它算进了本轮链。该提交是 HEAD 的祖先、却**从未被任何台账收录**（它出现时GOAL-107 不存在）。本轮如实补登，**不改历史、不改判据** |
| `d6b7e4dd` | [M0 42284126993](https://github.com/Eswink/research-system-new/actions/runs/42284126993) / [Push 42284126448](https://github.com/Eswink/research-system-new/actions/runs/42284126448) | **M0 `success`（8/8 job success）**；**Push 全 success (3/3)** | **建档**：GOAL-107 + 子 PLAN + RECHECK + 程序表序 75 + 阶梯两行 + 进展/修订各一行；同时付清 `320faa78` / `9ddd6360` 两笔 tip 债。治理门首轮点名七条（PLAN 缺 frontmatter / 缺五节 / RECHECK 状态词 / ALL_PLAN 投影 / 裸路径非链接），逐条修完才提交 |
| `99454d40` | [M0 42297143259](https://github.com/Eswink/research-system-new/actions/runs/42297143259) / [Push 42297142744](https://github.com/Eswink/research-system-new/actions/runs/42297142744) | **M0 `success`（8/8 job success）**；**Push 全 success (3/3)** | **靶子 C（EC-01…03）**：改稿并排 diff + 程序页三件 + TS 类型补齐 + 单路由基线重录。本地 e2e **112 passed**、单测 103、m0 见证全绿。**一处真红如实登记**：首次 m0 的 `typescript/lint` 与 `typescript/test` 各 1 红 —— 根 `eslint .` 比 `pnpm --dir apps/web lint` 宽（`tests/e2e/stub-routes-*.ts` 不在 `src` 下），且生产边界判据禁止前端出现判词枚举（`continue_on_verdicts: ["PASS"]` 撞上），两处修完才绿 |
| `466afd1f` | [M0 42340978836](https://github.com/Eswink/research-system-new/actions/runs/42340978836) / [Push 42340978642](https://github.com/Eswink/research-system-new/actions/runs/42340978642) | **M0 `success`（8/8 job success）**；**Push 全 success (3/3)** | **靶子 B（EC-04/05）**：`citation_distribution.py` 三个纯函数 + 语料入口。**实测语料 2 份**（不是建档时以为的 1 份）：`3142b142` 57/6/3、`6446406a` 39/9/3 ⇒ 门判 2 of 3、阈值仍 `None`。反证臂按压（marks 改常量）恰好 2 条红。 |
| `efbc19dc` | [M0 42345728710](https://github.com/Eswink/research-system-new/actions/runs/42345728710) / [Push 42345729288](https://github.com/Eswink/research-system-new/actions/runs/42345729288) | **M0 `success`（8/8 job success）**；**Push 全 success (3/3)** | **靶子 A（EC-06/07/08）**：外部评审面板。15 判据全绿；设施失败独立一类；advisory 边界（不 import `Decision`）；§7 加一句、`NOT_JUDGED` 五项逐字不动（5 条强口径判据仍绿）。**两处夹具坑如实登记**：`fail_timeout` 只让首调失败、`PortTimeoutError` 需 `failure_category`；规模门抓 `review_manuscript` 51 行 ⇒ 拆出 `_one_verdict`。 |
| `227c7573` | [M0 42351056784](https://github.com/Eswink/research-system-new/actions/runs/42351056784) / [Push 42351057004](https://github.com/Eswink/research-system-new/actions/runs/42351057004) | **M0 `success`（8/8 job success）**；**Push 全 success (3/3)** | **靶子 D（EC-09/10/11）**：脚本执行权威 + **修既有缺陷**（`sandbox_required`/`path_prefix`/`max_seconds` 声明了但零处执行）。15 判据全绿、对抗性反证 5 臂各按压判红、既有 17 条选择判据零回归。首次 m0 `python/format-check` 真红（`ruff format` 未跑）⇒ 修完重跑。 |
| `e1cb5f2d` | [M0 42386389966](https://github.com/Eswink/research-system-new/actions/runs/42386389966) / [Push 42386389367](https://github.com/Eswink/research-system-new/actions/runs/42386389367) | **M0 `success`（8/8 job success，含 `quality-windows-latest`）**；**Push 全 success (3/3)** | **序 75 收口**：`verify_goal107_closeout.py` + 断言集（登记 `_VERIFIERS` 与 `IN_SCOPE`）、RECHECK 填实为 `PASS_WITH_WARNINGS`、GOAL 十四条 EC 全 PASS、宪章进展行改实际结论。**收口复检 84 判词 / 0 FAIL**；**两树复检 PASS**（两树各 84 判词、`sha256=474fcf27…` 完全相同）；本地 m0 见证 `PASS: profile=m0; 23 deterministic checks`、`PASS [` 24、0 FAILED、`tree changed: False`。**如实登记两处**：① 首次 m0 点名 `7b9201ae`（2026-11-05 的历史提交，主题写成 goal107 而当时该 GOAL 不存在，从未被任何台账收录）⇒ 补登台账行 + `commits` 格，不改历史不改判据；② 收口提交是 HEAD ⇒ 结构例外，本行即为它的台账行 |
