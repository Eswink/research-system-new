---
id: GOAL-20261101-103
slug: phase-events-and-frontend-visible-chain
title: 后端四件收尾 + 前端全链可见 —— 用户能看见每一步
status: ACHIEVED
created_at: 2026-11-01
updated_at: 2026-11-01
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    沿用用户 2026-10-29 的全权限预授权（GOAL-20261029-100 的 authorization.ref；policy allow
    扩容 / 模型写代码进容器 / 新增第三方依赖 / 叙述质量口径，四类已预授权、各带留痕义务）；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 .env。
objective: >-
  把「run 走到哪一步」从事件链的隐含事实变成**三个读面都有的一等事实**：相级 Domain Event
  （`phase.started` / `phase.completed`）→ `RunDetailDto.phases` → 前端十一相进度条；同时补齐
  两个读面漏字段（`Artifact.supersedes` / `ReviewFinding.reviewer_model`）、把 `retmax` 抬进
  项目级配置、把手稿链的九类制品在前端显示成人类可读标签与正文、并把叙述质量的强口径
  逐项论证落进文档。
exit_criteria:
  - id: EC-01
    criterion: >-
      相级事件：`EventType` 新增 `PHASE_STARTED` / `PHASE_COMPLETED`；`phase_runner` 在每个
      phase 组**第一个任务开始前**发 `phase.started`（payload: phase_id / strategy /
      contract_ids）、在**该组全部任务终态后**发 `phase.completed`（payload: phase_id /
      outcome / artifact_ids）；发事件走既有 canonical outbox（`publish` 回调），不另开通道；
      组内失败/停车/重排**不发** `phase.completed`（否则「相完成了」会被伪造）。
      `RunDetailDto` 新增 `phases: list[PhaseProgressDto] | None`，从 run 的冻结协议正文
      反推 phase 分组，字段 phase_id / strategy / state / artifact_ids / started_at /
      completed_at。
    verify: >-
      **真跑取证**：tests/e2e/test_goal103_phase_events_product_path.py —— 用
      `direction_to_manuscript_v1.yaml` 的**11 个 phase** 经产品入口（`POST
      /projects/{id}/runs`）真跑一次，从 `GET /runs/{id}/events` 断言**恰好 11 条
      `phase.started` + 11 条 `phase.completed`**、相集合逐字等于协议、`started` 先于本相
      首个任务且 `completed` 晚于本相末个任务（按 `occurred_at`）、十一相按 DAG 拓扑序开始、
      `outcome` ∈ 闭集且 `artifact_ids` 指向真实落库制品、`RunDetailDto.phases` 长度 == 11
      且全部 SUCCEEDED；+
      tests/application/run_orchestration/test_phase_progress_events.py（两相合成协议的
      时序/失败不发 completed/payload 键）+ tests/api/test_run_detail_phases.py（未冻结 run
      ⇒ None；四态推导）+
      反证臂：删掉 `phase.started` / `phase.completed` 的发射点 ⇒ 判据判红（子进程按压）。
    status: PASS
  - id: EC-02
    criterion: >-
      读面补齐：`ArtifactDto` 新增 `supersedes: str | None = None`（域 `Artifact.supersedes`
      自 GOAL-102 起已有，读面此前不披露）；`ReviewFindingDto` 新增
      `reviewer_model: str | None = None`（域 `ReviewFinding.reviewer_model` 自 GOAL-085 起
      已有，读面此前不披露）。三处同步：Python DTO + `docs/api/openapi.m13.json`（重新生成）
      + `apps/web/src/api/types.ts`。
    verify: >-
      **路由级取证**：tests/e2e/test_goal103_read_face_http.py —— 经产品入口真跑后从
      **真实路由**取回 JSON：`GET /runs/{id}/artifacts` 的**每一件**制品都带 `supersedes`、
      改稿制品的值**指回**本 run 的 v1（非 None / 非自指）；`GET /runs/{id}/reviews` 的
      **每一条**判词都带 `reviewer_model`、至少一条非空、形态是 `endpoint/model`、两位评审
      归到 ≥2 个不同目标；+ tests/api/test_read_face_field_completeness.py（投影函数 +
      OpenAPI + types.ts 三处同步）+ tests/contracts/test_openapi_snapshot.py（快照不漂移）。
    status: PASS
  - id: EC-03
    criterion: >-
      前端 RunPanel 十一相进度：从 `RunDetailDto.phases` 渲染每相一个节点，节点带
      `data-testid="phase-node-<phase_id>"` 与 `data-phase-state` 属性；state 决定着色
      （PENDING / RUNNING / SUCCEEDED / FAILED 四态各有独立 class）；点击节点展开该相的
      制品 id 列表。`NAMED_SSE_EVENTS` 加入两个相级事件名（否则 SSE 帧到了前端不被监听）。
    verify: >-
      tests/api/… 之外的浏览器判据：apps/web/tests/e2e/run-phase-progress.spec.ts（十一相
      节点全部可见、各带状态、点击展开制品列表）+ 结构签名基线同轮重生成（逐条申报理由）。
    status: PASS
  - id: EC-04
    criterion: >-
      链上制品可读：ArtifactBrowser 对 id 后缀命中**闭集映射表**（19 个产物名）的制品显示
      人类可读标签（中英双语），未命中者显示原 id（不伪造标签）；ReportsPage 在
      artifacts 含 `manuscript.md` 时渲染其 Markdown 正文，同屏显示 `editorial_decision`
      与投稿包五件的链接；`types.ts` 新增 `EditorialDecisionDto` 供页面消费。
    verify: >-
      apps/web/tests/e2e/run-artifact-chain-labels.spec.ts（`manuscript.md` 显示为「手稿」
      且不显示裸 id）+ apps/web/tests/e2e/run-manuscript-report.spec.ts（Markdown 正文
      渲染、编辑决定与投稿包链接在场）+ apps/web/src/i18n 两份语言的键集判据。
    status: PASS
  - id: EC-05
    criterion: >-
      后端三件收尾：① 程序表序 70 的能力域保持 `复检`（不回退为轴值；本条只判「不回退」，
      因为归档时已修）；② `ProjectSettings` 新增 `retmax: int = 3`，`retrieval_wiring`
      的 `configured_retmax` 改为「显式参数 > 项目设置 > env > 默认」四级回落，
      **默认逐字段不变**（不声明项目设置时调用表与改动前逐字段相同），非法值仍点名拒绝；
      ③ `docs/architecture/MANUSCRIPT_QUALITY.md` 新增 `## 7. 强口径判定`：对
      `NOT_JUDGED` 五项**逐项**论证「可机械判 / 只能人评」，给出判法或判不了的理由，
      并明确下一轮输入。**只论证不硬实现**。
    verify: >-
      tests/tooling/test_mainline_program_is_intact.py 的域列判据（序 70 仍为 `复检`）+
      tests/application/test_retmax_project_setting.py（四级回落逐级按压：项目设置覆盖 env /
      未声明回落 env / 都未设回落 3 / 非法值点名拒绝）+ 
      tests/tooling/test_manuscript_quality_strong_criterion.py（§7 小节存在、五项逐条有名、
      每条结论 ∈ {机械可判, 只能人评}、结论与 `NOT_JUDGED` 集合一一对应）。
    status: PASS
  - id: EC-06
    criterion: >-
      负判扫描射程补齐（**不是**重做 GOAL-101）：GOAL-101 已把 `_VERIFIERS` 清单内 72 个
      验证器的**主文件** `record_verdicts` 纳入负判扫描；实测残余是 `LEGACY_INLINE` 的 9 个
      早期一代验证器**完全不在任何负判扫描面内**（其中 026/028/029 三个确有
      `record_verdicts`，026 的签名是 `(factory, root)` 与后来的一代不同）。本轮把这三个
      可跑的早期验证器纳入射程（按各自签名调用；不能跑的逐条登记理由），并新增一条
      **反证臂**：在合成树上让被纳入的那个早期验证器报负 ⇒ 判据点名判红。
    verify: >-
      tests/tooling/test_verifier_main_files_report_no_negative.py（射程下界随之上升，
      三个早期验证器登场）+ 同文件的反证臂类（合成树判红，真实树判绿）+ 逐字节复原。
    status: PASS
  - id: EC-07
    criterion: >-
      收口资产：`tools/verify_goal103_closeout.py` + `tools/goal103_closeout_assertions.py`，
      登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的
      `_VERIFIERS` 与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的
      `IN_SCOPE`；两份脚本过四道门（ruff / ruff format / mypy / 规模门）。
    verify: >-
      tools/verify_goal103_closeout.py --root . --verdict-only（零 FAIL）+ 
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py +
      tests/tooling/test_tooling_scripts_meet_product_gates.py +
      tests/tooling/test_verifier_main_files_report_no_negative.py。
    status: PASS
  - id: EC-08
    criterion: >-
      宪章记账：程序表追加序 71（能力域 ∈ 七域闭集，**不得**填轴值）；科研能力阶梯对应行
      收录本 GOAL 并升级 `当前级`（`下一级` 不许声称「叙述质量强口径已判」除非 EC-05 的论证
      真的给出机械判法）；进展记录与修订记录各追加一行（修订行 5 格）；两表各 3 行；子 PLAN
      登记进 ALL_PLAN.md。
    verify: >-
      tests/tooling/test_mainline_research_ladder_advances.py（最新轮被阶梯收录、核心不变式）+
      tests/tooling/test_mainline_archive_is_continuous.py（不漏/不重/可解析）+
      tests/tooling/test_mainline_program_is_intact.py（域列闭集、序号连续）+
      .cursor/skills/governance-check/scripts/validate.py。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 扩既有判据的受判面（相集 / 射程 / 站点集），逐条申报为什么不是放宽
    - 同轮重生成 `design-outlines.json` 基线（结构性新增必然改签名；逐条申报理由）
  forbidden:
    - 改 validator/门禁/快照/断言使其通过
    - 放宽既有判据（受判面只增不减；收窄必须逐条申报）
    - 把受判面写成交集或并集掩蔽
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - git add -A（并发工作树；只加显式路径）
    - 伪造或夸大验证证据（尤其：把「发了事件」说成「前端真的更新了」、把 skip 记成 PASS、
      把「论证可机械判」说成「已实现判据」）
    - 宣称项目安全（R-M1 未收口）
    - 宣称投递语义为「恰好一次」（at-least-once + 幂等 + 去重）
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（§9 姿态只放开点名项）
  - 同一失败签名超过 fix_policy 上限
  - 新增第三方依赖（EC-05 的强口径论证若需新依赖 ⇒ 停在论证，不进实现）
  - Windows quality job 20 分钟超时（已知 W-5：不是本轮新缺陷；改 timeout 属本清单）
child_plans:
  - .cursor/plans/tasks/PLAN-20261101-103-phase-events-and-frontend-visible-chain.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md
memory_entries:
  - .cursor/memory/entries/MEM-20261101-236-project-config-needs-a-per-run-hook.md
  - .cursor/memory/entries/MEM-20261101-237-declared-but-never-constructed-judge-the-call-site.md
---

# GOAL-20261101-103 —— 后端四件收尾 + 前端全链可见

## 目标与退出标准

承用户 goal-mode 指令（序 71）。序 70（GOAL-102）收口后，「能投出去的包」已经在 canonical
里装齐（手稿 v1/v2、编辑决定、应答信、投稿包五件），但**用户看不见它**——这是本轮的全部
理由。建档实测（不重新推导，命令与读数逐条记录在下）：

**缺口一：相级进度在三个读面上都不存在。**
`rg "phase\.started" --include=*.py .` ⇒ **0 命中**（`EventType` 枚举 39 个成员里没有相级）；
`RunDetailDto` 只有 `state` 一个粗粒度状态；前端 `NAMED_SSE_EVENTS` 的 11 个名字里没有相级
事件。后果不是「少了个好看的进度条」，而是：一次 run 停在第九相时，**事件链里可以判出它
停在哪**，而**产品读面和 UI 都只能告诉你「这条 run 是 RUNNING」**。

**缺口二：两个已存在于域层的字段没有读面。**
`Artifact.supersedes`（GOAL-102 EC-01 落地）在 `ArtifactDto` 里**没有**——
`rg supersedes services/api/dto/` ⇒ 0 命中 ⇒ 改稿链在 API 上退化成「两个互不相干的制品」；
`ReviewFinding.reviewer_model`（GOAL-085 EC-01 落地）在 `ReviewFindingDto` 里**没有**
——「这条判词是哪个模型判的」在产品读面上拿不到，而阶梯「复检」域的
「判词可归因到模型」正是靠它成立的。

**缺口三：手稿链在前端是不可读的裸 id。**
`rg "manuscript|editorial_decision|response_letter" apps/web/src/` ⇒ **0 命中**。
`ArtifactBrowser` 把每个制品渲染成 `{artifact.id}` 加字节数与 media type；`ReportsPage`
只渲染 M12 的 `deliverable.json`。于是 GOAL-099/100/102 三轮做出来的东西
（手稿 / 应答信 / 编辑决定 / 投稿包）在 UI 上**与一条 `tool-result:...` 没有区别**。

**缺口四：`retmax` 只到 env，不到项目。**
`configured_retmax` 只读 `RESEARCHOS_RETMAX`（GOAL-100 EC-04 落地的具名默认 + env）；
`ProjectSettings` 没有 `retmax` 字段 ⇒ 一次 run 的检索条数无法按项目声明，只能靠进程级
环境变量——同一控制面上的两个项目无法有不同的检索深度。

**缺口五（**本轮实测后重新界定**）：负判扫描射程还差一代。**
用户提示词写的形态是「只跑断言集、不跑主文件」——**该缺陷已由 GOAL-101 EC-02 修掉**：
`tests/tooling/test_verifier_main_files_report_no_negative.py` 在当前树上 **4 passed**，
`_VERIFIERS` 的 72 个验证器主文件已在射程内。**本轮实测的真实残余**是 `LEGACY_INLINE`
登记的 9 个早期一代验证器**不在任何负判扫描面内**（`_VERIFIERS ∪ LEGACY_INLINE` = 81 =
树里全部 `verify_goal*_closeout.py`，但判负扫描只跑 `_VERIFIERS`）；其中 026/028/029 三个
**确有** `record_verdicts`（028 ⇒ 5 判词、029 ⇒ 10 判词、026 ⇒ 签名是
`record_verdicts(factory, root)`，与后来的一代不同）。所以 EC-06 的目标是**补这一代的射程**，
不是重做 GOAL-101。**这条重界定必须写进记录**——照抄提示词会得到一份「已经做完了」的 EC。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 相级事件（两向：发在正确时刻 / 失败不发）+ `RunDetailDto.phases` | `test_phase_progress_events.py` + `test_run_detail_phases.py` + 按压臂 | PENDING |
| EC-02 | `ArtifactDto.supersedes` + `ReviewFindingDto.reviewer_model` + 三处同步 | 两个读面判据 + OpenAPI 快照判据 | PENDING |
| EC-03 | RunPanel 十一相进度条 + SSE 监听相级事件 | `run-phase-progress.spec.ts` + 结构签名基线 | PENDING |
| EC-04 | 19 类制品标签 + 手稿 Markdown 视图 + 编辑决定/投稿包链接 | 两个 e2e spec + i18n 键集判据 | PENDING |
| EC-05 | 序 70 域列不回退 + `retmax` 项目级 + 强口径逐项论证 | 四级回落判据 + §7 结构判据 | PENDING |
| EC-06 | 早期一代验证器纳入负判射程 + 一条反证臂 | `test_verifier_main_files_report_no_negative.py` 射程与反证 | PENDING |
| EC-07 | 收口验证器 + 断言集 + 两处登记 | `--verdict-only` 零 FAIL + 两份清单判据 | PENDING |
| EC-08 | 宪章记账（序 71 / 阶梯 / 两表各 3 行 / ALL_PLAN） | mainline 四条判据 + governance-check | PENDING |

**四条硬边界的姿态（本轮逐条对照，全部未动）**：① 真实模型厂商不进 Domain、OpenHands 类型
不进 Domain——本轮新增的 DTO 字段只装 `str | None`，相级事件的 `strategy` 取自域枚举
`PhaseStrategy`，不引入任何 vendor 名；② 不假装恰好一次——相级事件走既有 outbox，
`EventEnvelope` 的 `event_id` 语义与去重面不变，**不引入**任何「相只发一次」的承诺；
③ 观测默认不记 Prompt / 模型输入输出 / Tool 敏感参数——新增 payload 只有
`phase_id` / `strategy` / `contract_ids` / `outcome` / `artifact_ids`，**制品 id 不是内容**，
与既有 `task.created` 的 `task_id` 同层；④ §9 默认 deny 只放开点名项——本轮不新增任何
工具/网络/凭据面。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 八个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
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

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品 vs 测试各半）；**修产品优先，禁改断言迁就** |
| 视觉基线漂移 | `design-fidelity` / outline 判红 | 本轮的**结构性新增**是预期内的 ⇒ 同轮重生成基线并**逐条申报**为什么不是放宽 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按既有配方重跑；配方不覆盖 ⇒ 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED（infra 非代码缺陷） |
| Windows quality 超时 | job 卡满 20 分钟 | **已知 W-5**（不是新缺陷）；不擅自改 `.github/workflows/**`，如实记 `cancelled` |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：八个 EC 全 PASS + 独立 RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 `PASS: profile=m0; 23 deterministic checks` + CI 到终态 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；`covered_by` 只写真实覆盖者哈希。首行记本地见证证据；
CI run 的链接与结论由其后的记录提交回填 —— 回填提交用中性主题（只改 `.cursor/`），不进本
GOAL 的链。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `24e3418b` | 本地全量 m0 见证（`evidence/M0-WITNESS.json`，重封于 `ef755a99`） | **本地 m0 终态行 `PASS: profile=m0; 23 deterministic checks`**（24 条 `PASS [` 行 = 23 + 计数外的 `release-assets-immutable`）；**零 run（`covered_by: ef755a99`）** —— 同批推送 | 交付提交：相级事件 + `RunDetailDto.phases` + 读面两字段 + 前端两件 + `retmax` 项目级 + §7 论证 + 早期一代射程。首轮见证为**诚实红**（5 个 check：product-lint / format / typecheck / tests / typescript-lint），逐类修复后复跑；第二轮回落后只剩 `python/tests`（5 条真实失败），再修后绿 |
| `bcc42d9a` | [M0 41325992369](https://github.com/Eswink/research-system-new/actions/runs/41325992369) / [Push 41325992361](https://github.com/Eswink/research-system-new/actions/runs/41325992361) | **M0 `success`（8/8 job success，含 `quality-windows-latest`）**；**Push 全 success** | **真跑取证的封印提交**（GOAL 记录 + 见证）。**这一轮 windows 也绿** ⇒ `W-5` 的 20 分钟窗口在「只改记录」的提交上通常不触发；三次 cancelled 的对照证据见前两条。 |
| `ea4b94fb` | [M0 41329347922](https://github.com/Eswink/research-system-new/actions/runs/41329347922) / [Push 41329347914](https://github.com/Eswink/research-system-new/actions/runs/41329347914) | **M0 `cancelled`**（七 job `success`，`quality-windows-latest` `cancelled`）；Push 全 `success` | **最终收口 tip**（只改记录 + 见证）。当时它是 HEAD ⇒ 结构例外；**序 72 的归档推送把它推离 HEAD 后，反方向判据点名它**。**它的 windows 是 `W-5` 的第四次实例**：`Run all M0 gates` 卡到 20 分钟被取消（实测 1206 秒 = 20 分 6 秒，日志无测试失败）⇒ 这是「`bcc42d9a` 绿、最终 tip 红」的成因，**不是新一轮缺陷** |
| `79d02c28` | 本地（记录提交，只改 GOAL 记录 + 见证） | 零 run（`covered_by: 52f7ed35`） | 上一轮的收口封印：CI 读数回填 + 见证重封 |
| `52f7ed35` | 本地 m0 见证（`evidence/M0-WITNESS.json`；终态行 `PASS: profile=m0; 23 deterministic checks`，跑门期间树未变） | 交付提交；CI 读数见下（本行为本轮的**真跑取证**提交） | **补收口复检指名的两条判据**：① `tests/e2e/test_goal103_phase_events_product_path.py`（十一相**真跑**：恰好 11 对相级事件、时序按 `occurred_at`、DAG 拓扑序、制品真实落库、`phases` 长度 11 全 SUCCEEDED）；② `tests/e2e/test_goal103_read_face_http.py`（**路由级**：两个补字段经真实 `GET /runs/{id}/artifacts` / `/reviews` 回得来）。**同轮修掉真跑暴露的实现缺陷**（`experiment` 相无任务行 ⇒ 读面曾读成「未开始」） |
| `478d39ed` | [M0 41316718426](https://github.com/Eswink/research-system-new/actions/runs/41316718426) / [Push 41316718390](https://github.com/Eswink/research-system-new/actions/runs/41316718390) | **M0 `cancelled`（7/8 success，`quality-windows-latest` 撞窗口；实测 `14:32:44Z → 14:52:52Z` = 满 20 分钟、非成功步骤只有 `Run all M0 gates` = `cancelled`、无 failure）**；Push 全 success | **封印提交**（只改 GOAL 记录 + 见证）。**这条与前一条的对照是 `W-5` 归因的决定性证据**：**同一份代码**在 `ad17cb22` 上 8/8 全 success、在 `478d39ed` 上撞窗口 —— 差异只在 runner 的时间预算，不在内容。如实记 `cancelled`。 |
| `ad17cb22` | [M0 41313339542](https://github.com/Eswink/research-system-new/actions/runs/41313339542) / [Push 41313339410](https://github.com/Eswink/research-system-new/actions/runs/41313339410) | **M0 `success`（8/8 job success，含 `quality-windows-latest`）**；**Push 全 success** | **收口封印提交**（只改 GOAL 记录 + `M0-WITNESS.json`）。**这一轮的 `quality-windows` 是 success** ⇒ 前两条 `cancelled` 归因为 20 分钟窗口（`W-5`）**得到证实**：同一套代码在同一 runner 上这次跑完了 8/8。本地见证终态行 `PASS: profile=m0; 23 deterministic checks`（`dcf6f764`，跑门期间树未变）。 |
| `dcf6f764` | [M0 41308666269](https://github.com/Eswink/research-system-new/actions/runs/41308666269) / [Push 41308665897](https://github.com/Eswink/research-system-new/actions/runs/41308665897) | **M0 `cancelled`（7/8 job success，`quality-windows-latest` 再次撞 20 分钟超时窗口 —— `W-5`）**；**Push 全 success** | **收口 tip**（CI 读数回填 + 见证重封）。`quality-windows-latest` 实测 `12:54:12Z → 13:14:18Z` = **满 20 分钟**，非成功步骤只有 `Run all M0 gates` 一条、其结论是 `cancelled`（**无任何 step 报 failure**，与 `ef755a99` 同一形态）；其余 7 个 job（含 `quality-ubuntu` / `container-quality` / `collector-quality` / 两条 `observability-overhead`）全 success。**如实记 `cancelled`，不冒充绿。** |
| `a889872f` | 本地（记录提交，只改 `.cursor/` 与两份测试的门内注释） | 零 run（`covered_by: ef755a99`） | 台账补登：GOAL-102 的 `d9d6e301` / `c974223f` 两行（判据未改）；GOAL-103 的 CI 台账建表 |
| `ef755a99` | [M0 41304287810](https://github.com/Eswink/research-system-new/actions/runs/41304287810) / [Push 41304287338](https://github.com/Eswink/research-system-new/actions/runs/41304287338) | **M0 `cancelled`（7/8 job success，`quality-windows-latest` 撞 20 分钟超时窗口 —— `W-5` 的同一形态）**；**Push 全 success**（CodeQL 三语言 success） | **交付 tip**（含见证）。`quality-windows-latest` 实测 `11:59:03Z → 12:19:09Z` = **满 20 分钟**，卡在 `Run all M0 gates` 这一步被 `cancelled`（**没有任何 step 报 failure**）；`quality-ubuntu` / `console-frontend` / `eval-gate` / `container-quality` / `collector-quality` / 两条 `observability-overhead` 全 success。**不是绿**，也不冒充绿：如实记 `cancelled` |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261101-103 | `24e3418b` → `a889872f` → `ef755a99` → `dcf6f764` → `ad17cb22` → `478d39ed` → `79d02c28` → `52f7ed35` → `bcc42d9a` → `ea4b94fb`（序 72 归档轮补记） | 定向套件全绿（见 RECHECK 读数）+ 全量 m0 见证 + web 105/105 | **M0 `success` 8/8**（`ad17cb22`；此前两条 `cancelled` 证实为 W-5 窗口）；Push success | 无 | 八条 EC 全 PASS；残余 `W-1`…`W-5` 与未覆盖 `U-1`…`U-3` 已登记 | 见 §7「结论」与残余节（续跑取证 / 批量相进度读面 / 阈值标定 / 外部评审面板） |


## 残余与未覆盖范围

（**没做到**的那部分，逐条明写。空着等于宣称"没有缺口"，那是伪造验证证据。）

### 残余（本轮已交付里仍然存在的缺口）

- `W-0`｜**已修（真跑才发现）**：`experiment` 相是**确定性执行缝**，它**不注册
  `ResearchTask` 行** ⇒ `run_phase_view` 第一版只按任务行推状态，把一个 `SUCCEEDED`、
  `phase.completed` 在场、两份 `experiment_result.json` 已落库的 run 读成
  `experiment: PENDING`。**两相合成协议发现不了它**（合成协议每相都有任务行）——
  是十一相真跑判据抓到的。修法：`state` 改为**相级事件优先、任务行兜底**
  （`_state_from`），制品取两条来源的并集。
- `W-1`｜**相级事件的时刻在事件本身，而 `state` 从任务状态推**：`started_at` /
  `completed_at` 取自 `phase.started` / `phase.completed` 的 `occurred_at`，而
  `PhaseProgressDto.state` 走的是**任务 canonical 状态**。两者在正常情况下一致，
  但**续跑（resume）后重放**的相可能出现「有 completed 时刻而任务状态仍是 RUNNING」
  （或反之）；读面此时以任务状态为准。**没有判据覆盖这个分叉** —— 它需要一次真正的
  续跑取证，本轮没有跑（`U-1`）。
- `W-2`｜**`phases` 只在详情路径给**：列表路径（`GET /projects/{id}/runs`）恒为 `null`。
  这是刻意的（避免 N+1：逐 run 解析冻结协议正文 + 扫制品表），但**用户在多 run 列表上
  看不到进度**。要做就要一条批量读面，本轮不做。
- `W-3`｜**相级事件的 payload 没有 `task_ids`**：`phase.started` 带 `contract_ids`（声明面），
  但「本相实际派了哪几个任务」要从 `task.created` 序列里对。前端展开某相时显示的是
  **该相声明的**制品，不是「按任务归属的制品」（后者要额外的读面字段）。
- `W-4`｜**`retmax` 只在检索类调用上生效**：`apply_retmax` 只改带 `retmax` 键的调用。
  一个声明了别的条数参数（如 `page_size`）的 provider **不会被本项目声明影响** ——
  射程如实登记在 `apply_retmax` 的 docstring 里，没有为它造通用机制。
- `W-5`｜**Windows quality job 20 分钟超时**（GOAL-101 `W-5` 的同一形态，**不是本轮新缺陷**）：
  本轮 CI 可能再次出现 `cancelled`。改 `.github/workflows/**` 属 `escalation_triggers`，
  本轮**未动**。如实记 `cancelled`，不冒充绿。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1`｜**续跑（resume）路径上的相级事件**：`phase_runner` 的两处发射点覆盖首跑与
  多轮循环；`resume` 重建路径（`phase_id` 为空）**不发**相级事件（刻意：否则读面会
  多出一个不存在的相）。「续跑后相进度如何续接」无判据、无真跑取证。
- `U-2`｜**相级事件的读面消费者只有前端**：除 `run_phase_view` 与 `PhaseProgress.tsx`
  外没有别的消费者（通知、审计、报表都不读它）。本轮不做「事件驱动告警」这类下游。
- `U-3`｜**叙述质量强口径仍然未判**：§7 只做论证。三项（引用支持 / 论证成立 /
  方法学合适）判为**只能人评**，两项（引用充分性 / 文风）判为**可机械判但本轮不实现**
  —— 前者需要外部评审面板，后者需要先标定阈值。**下一轮的输入**写在 §7 的「结论」里。

### 声称边界（**不得**被读成的事实）

- `R-1`｜**本轮不宣称「用户能看见每一步」已经完整**：十一相进度可看、制品标签可读、
  手稿正文可读，但 `W-1`/`W-2`/`W-3` 三条缺口在真实续跑与多 run 列表上仍然存在。
- `R-2`｜**本轮不宣称项目安全**：`R-M1` 未收口；`§9` 默认 deny 的姿态未动
  （本轮不新增任何工具 / 网络 / 凭据面）。控制面认证仍是本地开发姿态。

### 修正的事实（记录面自查，不粉饰）

- 用户提示词的靶子 4 说「序 70 的能力域我已修掉，你核对不回退」—— **核实为真**：
  `| 70 | GOAL-20261031-102 | 深度+质量 | ... | 序 69 | 复检 |`，第 5 格是轴
  `深度+质量`、第 6 格是能力域 `复检`。本轮 EC-05 只判「不回退」，没有改动它。
- 用户提示词的靶子 5 说「负判扫描只跑断言集模块，不跑主文件 `record_verdicts`」——
  **该缺陷已由 GOAL-101 EC-02 修掉**（`test_verifier_main_files_report_no_negative.py`
  在本树上 4 passed，`_VERIFIERS` 的 72 个主文件已在射程内）。**本轮实测的真实残余**
  是 `LEGACY_INLINE` 的 9 个早期验证器**完全不在任何负判扫描面内**，其中 026/028/029
  确有 `record_verdicts`（026 的签名是 `(root, factory)`）。EC-06 因此按**实测残余**
  重新界定，而不是照抄提示词做一件已经做完的事。
- GOAL-20261031-102 的台账**漏了 `d9d6e301`**（归档搬运 + 序 70 域修正），由
  `test_goal_commit_chain_reaches_the_ledger` 在本轮 cycle 3 抓到（链 6 / 台账 4）。
  补登该行时**判据一字未改**，只补事实。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-01 | ACTIVE | 建档（承用户序 71 指令）。五个靶子建档实测；其中「负判扫描只跑断言集」已被 GOAL-101 EC-02 修掉 ⇒ EC-06 按实测残余重新界定为「早期一代验证器不在射程内」。 |
| 2026-11-01 | ACHIEVED | 八条 EC 全 PASS；收口复检 PASS（`RECHECK-20261101-103`）；残余与未覆盖逐条登记。 |
