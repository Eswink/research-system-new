---
id: GOAL-20261014-078
slug: retrieved-content-reaches-the-model-context
title: 活检索的结果进模型上下文（检索域 L1 → L2）
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」把**检索**域的
    `下一级是什么` 逐字写为「**活检索的结果进模型上下文**（现只落证据链与报告，
    模型读不到检索到的内容）」。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令
    （「每一次自动迭代都必须让科研能力越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 阶梯「检索」域 L1 → L2；它**必须让阶梯前进**
    （由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让**活检索到的内容真正进入模型上下文**：一次 run 里，运行链取回的文献**内容**
    （标题 / 摘要 / 标识）经**可判定的接缝**进入后续 phase 的会话上下文，
    且「进了多少 / 进了哪些 / 从哪来」在既有读面上**可复核**——
    而不是只落在证据链与报告里（现状：模型读不到它们）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **接缝在树且可判定**：存在一个**声明式**的接缝把「本 run 已取回的检索内容」
      装配成会话上下文（`ContextSnapshot` 的既有槽位），且它**只读 canonical**、
      **不新增出网**、**不绕过脱敏**。判据成对：装配出的上下文里逐条给出
      `selected_refs`（内容寻址 id）与其 `retrieval_digest`；**空集合**时有**点名**
      的理由（不是静默空）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_retrieval_context_seam.py -q`
      ⇒ 全绿；判据覆盖：**逐条 ref 在场**、digest 由内容**重算**、
      `token_allocation` 有界且**不超声明上限**、空集合点名。
    status: PASS
  - id: EC-02
    criterion: >-
      **经产品路径进入会话**：带运行链检索的协议在**产品装配**下跑一次，
      后续（下游）phase 的会话 spec 里 `context_snapshot.selected_refs` **非空**，
      且这些 ref 指向**本 run 真实检索取得**的内容（`TrustLabel.RETRIEVED`）。
    verify: >-
      离线 e2e：`tests/e2e/test_retrieval_context_reaches_the_session.py` ⇒ run
      `SUCCEEDED`；对下游 phase 的会话 spec 断言 `selected_refs` 非空、
      逐条可在 `GET /runs/{id}/evidence` 找到（性质 `RETRIEVED`）、
      且**上游没有检索时该集合为空并点名**（反证臂）。
    status: PASS
  - id: EC-03
    criterion: >-
      **「进了什么」可复核**：上下文装配的结果在**既有读面**上可读——
      同一个 run 的读面能回答「哪些内容进了会话上下文、各自的 digest 与来源」，
      而不是只有进程内对象知道。
    verify: >-
      读面判据：`GET /runs/{run_id}` 或既有制品读面上能取回该 run 的
      `retrieval_digest` 与所选 ref 清单（**逐条**）；判据断言读面值与装配点
      **同源**（不重算第二遍）。
    status: PASS
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**（承 GOAL-077 的 live 门）：上游真实检索取回的内容
      在下游会话的上下文里**真的出现**——判据取的是**这次 run 的**事实
      （run id / 所选 ref / digest 记档）。**若模型侧不可用** ⇒ 按降级梯如实登记
      （记 PENDING + 点名阻塞点），**不得**伪造成真实跑成功。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且
      `selected_refs` 里的标识（PMID 等）能追回**本次**检索结果。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**）+ 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 +
      原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 检索**），使阶梯的「检索」域 `依据 GOAL` 收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING

budget:
  max_cycles: 12
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - 改 `default_effect: DENY` / 放宽 §9 / 新增任何 allow
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**（记录 / GOAL / PLAN /
      `examples/**` / 测试 / 文档）—— **只在 gitignored 的 `.env` 落位**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - >-
      把检索内容的**完整正文**塞进会话（§10 观测隐私）：进上下文的内容必须**有界**
      （逐条截断 + 总数上限），且判据断言这个上界**真的生效**
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **新站不可用**（连通 / 协议面 / 工具调用任一不通）且无替代路径 —— 记 BLOCKED，
    逐条写明阻塞点（**不得**为此放宽任何判据或伪造成功）
  - >-
    接缝需要**把检索正文无损注入**才能成立（与 §10 的有界口径冲突）—— 立即 BLOCKED，
    留人工拍板（**不得**自行放宽隐私边界）

child_plans:
  - .cursor/plans/tasks/PLAN-20261014-469-goal-078-ec01-retrieval-content-reaches-the-session-context.md
  - .cursor/plans/tasks/PLAN-20261014-471-goal-078-ec02-retrieval-context-reaches-a-downstream-session.md
  - .cursor/plans/tasks/PLAN-20261015-473-goal-078-ec03-what-entered-the-context-is-readable.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-474-goal-078-ec03-what-entered-the-context-is-readable.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-221-declared-but-never-constructed-is-a-dead-seam.md
---

## 目标与退出标准

**一句话**：把「活检索的结果」推进到**模型真的读到**——检索域 **L1 → L2**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性）与**深度**（研究能多轮推进）**同时**受益：
  模型看不到检索内容时，「立题由检索派生」只能停在**声明**层（覆盖计数过关），
  而**内容**对结论没有影响；
- **能力域** = **检索**（阶梯上那一行：当前级「真检索 + 真标识 + 检索产出已进报告」
  → 下一级「**活检索的结果进模型上下文**」）；
- **间接推进**「计划」域：立题与实验设计只有在**读到内容**后才可能真正由检索驱动。

**为什么这一条更近科研**（对照阶梯）：宪章读数逐字写着「现只落证据链与报告，
**模型读不到**检索到的内容」。GOAL-077 把检索产出做进了**人类可读报告**，
但**会话**仍拿不到它 —— 一个模型在不知道任何文献内容的情况下写出的「立题」与
「结论」，与它**读过**三篇文献后写出的，是两件不同的事。

**本 GOAL 不加新能力、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **隐私纪律（§10）**：进上下文的内容**有界**（逐条截断 + 总数上限），
  判据断言上界生效；**不**把完整正文塞进会话。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用 ⇒ 记 PENDING + 点名阻塞点；
  **不伪造**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证
（逐 job annotation / 同时终止时刻 / 状态页 incident），与 `cancel-in-progress`
（`run conclusion=cancelled`）形态区分。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立**（本 GOAL 被某个域的 `依据 GOAL` 收录）。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- **无损注入检索正文**（与 §10 冲突）—— 需人工拍板；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1（EC-01 接缝 + 两组合根接线 + 13 例判据） | `bd5d5896` | [M0 38630762702](https://github.com/Eswink/research-system-new/actions/runs/38630762702) / [Push 38630762356](https://github.com/Eswink/research-system-new/actions/runs/38630762356) | **M0 八 job 全 `success`**（quality-windows / quality-ubuntu / observability-overhead × 2 / collector-quality / container-quality / console-frontend / eval-gate）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**；**本 GOAL 的第一次推送 = 第一次全绿**（四处问题在**本地 m0** 抓掉后才推送 —— 逐条见「cycle 1 的修复记录」） |
| cycle 1 台账回填（末条） | `00526faf`（**tip**） | [M0 38636832193](https://github.com/Eswink/research-system-new/actions/runs/38636832193) / [Push 38636831371](https://github.com/Eswink/research-system-new/actions/runs/38636831371) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled**（只改 CI 台账的文档行） |
| cycle 2（EC-02 e2e + 两条补判据） | `a93cd215` | [M0 38650611946](https://github.com/Eswink/research-system-new/actions/runs/38650611946) / [Push 38650611542](https://github.com/Eswink/research-system-new/actions/runs/38650611542) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 3（EC-03 读面 + 同源 + V8-4） | `7bd6068e` | [M0 38661606028](https://github.com/Eswink/research-system-new/actions/runs/38661606028) / [Push 38661606062](https://github.com/Eswink/research-system-new/actions/runs/38661606062) | **M0 八 job 全 `success`** + Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（接缝在树且判定成对） |
| 1 | PLAN-20261014-469 | 见「CI 台账」 | 接缝判据 **13 passed**；既有四套件 **2752 passed, 8 skipped**（+13）；`mypy` 1232 源文件零问题；产品装配实测 `retrieval_context is not None`；**m0 终态行 `PASS: profile=m0; 23 deterministic checks`** | 见「CI 台账」 | 4 次（见「cycle 1 的修复记录」） | EC-01 **PASS**；EC-02/03/04/05 PENDING | cycle 2 = EC-02（经产品路径进入会话 + 反证臂） |
| 2 | PLAN-20261014-471 | 见「CI 台账」 | 新 e2e **5 passed**（正向 / 反证 / 射程 / 自检）；接缝判据 **16 passed**（+3）；三向按压全红且逐字节复原；受影响套件 **997 passed, 1 skipped** | 见「CI 台账」 | 2 次（见「cycle 2 的修复记录」） | EC-02 **PASS**；EC-03/04/05 PENDING | cycle 3 = EC-03（读面可复核「进了什么」） |
| 3 | PLAN-20261015-473 | 见「CI 台账」 | 读面判据 **5 passed**；接缝 16 passed；e2e **7 passed**（含 HTTP 面 + 同源）；四向按压全红且逐字节复原 | 见「CI 台账」 | 1 次（见「cycle 3 的修复记录」） | EC-03 **PASS**；EC-04/05 PENDING | cycle 4 = EC-04（真实中转站实跑） |

### cycle 3 的修复记录（逐条如实）

1. **`AttributeError: 'RetrievalContextView' object has no attribute 'run_id'`**（实测抓到）：读面载荷要 run 标识，而视图没带它 ⇒ 给视图补 `run_id` 字段（缺省 `""`），并在两处构造点**用关键字**写上。
2. **判据模块超 450 行**（504）：EC-03 的 5 例另立模块`test_retrieval_context_read_face.py`（复用既有夹具，不复制）。


### cycle 2 的修复记录（逐条如实）

1. **夹具缺装配**（实测抓到·真缺口）：run-ready 夹具不经产品组合根，因此**不带**`retrieval_context`（与 `capabilities` / `experiment_task` / `report_task` 三条缝同一形态）⇒ 首跑 4 例失败、失败形态正是「下游上下文为 `None`」。判据侧以装配方身份补一行（用**产品件本身** `retrieval_context_builder`，不复制实现）。
2. **两条按压臂首轮没咬住**（实测抓到·**判据覆盖缺口**，不是按压问题）：
   `V8-2`（去掉 run 过滤）与 `V8-3`（性质判据恒真）在 e2e 上**都不变红** ——
   该夹具只有一个 run，「按 run 过滤」这条性质**无处可测**；而协议的声明输入不带`tool-result:` 前缀 ⇒ 被前缀过滤先挡住。**处置 = 补判据不调按压**：新增`TestTheRunFilterBites`（两 run 的证据同时在库）与`TestAToolResultWithoutTheRetrievedLabelDoesNotEnter`（带前缀但性质为 `GENERATED` 的工具结果 —— 这正是 canonical 读面 provider 的真实形态）⇒ 两条臂**全红**。
3. **正对照一度失败**（实测）：`GENERATED` 那一条的「正向对照」用了只有 `content` 键的载荷 ⇒ 装配器认不出记录形状 ⇒ 空集。改用 `ids` 形状（本用例的靶子是**性质分派**，不是形状识别 —— 两者混在一个夹具里会让两种缺陷给出同一条红）。


### cycle 1 的修复记录（逐条如实；本地 m0 抓到的四处，**push 前**）

1. **`mypy` 真红**：判据里的 `imported = set()` 缺类型注解（`var-annotated`）⇒ 加 `set[str]`。
2. **`phase_runner.py` 464 行 > 450**：新增的检索上下文用点让本文件越界 ⇒ 把实现移到
   `retrieval_context.with_retrieval_context`（本模块只留一行调用），并把冗余字段注释按
   「细节留在定义处」收敛；`_run_group_task` 也一度 54 行 ⇒ 抽出 `_task_correlation`。
3. **`pg_composition._build_pg_orchestration` 54 行 > 50**：runtime 装配抽出成 `_pg_runtime`
   （**纯搬运**，与 SQLite 根只差 Port 实例）。
4. **连带发现（判据**误判**，已改正）**：`test_production_session_tool_registration` 判的是
   「注册面是否交给 `build_agent_runtime`」，但实现写成了「关键字必须写在该函数体里」⇒
   把**提取**误判成缺口。改判**一跳可达**（判据**更强**：拆出去却没人调 ⇒ 判红）——
   实测按压：把调用改名 ⇒ 该判据红、逐字节复原一致。


## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | **ACTIVE** | **建档**：承 GOAL-077 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「检索」域 **L1 → L2**（`下一级是什么` 逐字：活检索的结果进模型上下文）。**建档实测**：`ContextSnapshot`（含 `selected_refs` / `retrieval_digest` 槽位）在域层已声明，但**全仓零构造点**（`rg "ContextSnapshot("` 只有定义处与 Port 注解）⇒ 会话上下文里没有任何检索内容；`rg` 在 `packages/`·`services/` 下对 `context_snapshot=` **零命中** ⇒ 该槽位在运行路径上**从未被填充**。这两条读数就是本 GOAL 的靶子。 |
| 2026-10-14 | ACTIVE | **cycle 1 落地**（EC-01，PLAN-469）：`ContextSnapshot` 这个**早就声明、全仓零构造点**的槽位有了**唯一**生产者（`retrieval_context.py`，只读 canonical、零出网、摘录有界、空集合点名），经**两个组合根**接进产品路径（各一行装配 + 一处装配决策模块）并填入 `AgentSessionSpec.context_snapshot`。判据 13 例（含**构造性**的零出网证据 + 两种空分得开）；既有四套件 2752 passed。**EC-01 → PASS**（RECHECK-470 = PASS）；EC-02/03/04/05 PENDING。 |
