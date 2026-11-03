---
id: GOAL-20261103-104
slug: design-gate-and-integration-coverage
title: 设计门禁扩到四组合 + 联调补齐 + 三条悬空样式
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
  把「前端真的被检查了吗」从**名义覆盖**变成**可证伪的覆盖**：三条静默失效的样式引用
  补上机械判据；设计门禁从单一组合扩到四组合（双主题 × 双密度 × 中英文），并让十一相
  进度条的**填充态**进入像素基线（此前它在折叠线以下、两道门都看不见）；把 10 条无前端
  消费者的后端路由按「接线 / 如实登记」两选一处置，并为「路由有消费者或被登记」建立
  机械判据。
exit_criteria:
  - id: EC-01
    criterion: >-
      三条悬空样式修复：① `PhaseProgress.tsx` 的 `styles.muted` 改成**局部**
      `phaseStyles.muted`，并在 `PhaseProgress.module.css` 定义 `.muted { color: var(--fg-muted) }`
      （不外溢到共享模块）；② `CommandCenterPage.module.css` 与 `ConsoleLoading.module.css`
      的 `var(--bg)` → `var(--bg-app)`；③ `LivePage.module.css` 的 `var(--text-dim)` →
      `var(--fg-faint)`。新增 `apps/web/tests/unit/css-token-references.test.ts`：token 面
      （每个 `var(--x)` 必须在 `tokens.css` 或同层叠内被定义）+ 类名面（每个
      `styles.<key>` 必须在被 import 的模块里有对应类）+ 反证臂。
    verify: >-
      `npx tsx --test tests/unit/css-token-references.test.ts` 3 条全绿；
      **反证臂实测**：往 `PhaseProgress.module.css` 插 `var(--not-a-token)` ⇒ 判据点名
      `features/runs/PhaseProgress.module.css: var(--not-a-token) is not defined…`（实测
      已红，随后还原）；类名面在 `PhaseProgress.tsx` 改回 `styles.muted` 时同样判红。
    status: PASS
  - id: EC-02
    criterion: >-
      设计门禁扩到四组合 + 十一相入基线：① `design-fidelity.spec.ts` 的截图用例参数化为
      `COMBINATIONS` 四组合（dark/normal/zh、dark/compact/en、light/normal/en、
      light/compact/zh，对角取法：每轴各出现两次）；② `ALL_ROUTES` 新增
      `run-timeline-phases`（`#/run/timeline?run=eleven-phases`），让**填充态**进基线；
      ③ `design-outlines.json` 重生成，新路由含 **11 个** `phase-node`；④ 新增**元素级**
      像素用例（`toHaveScreenshot` 钉在 `phase-track` 上、`maxDiffPixels: 196`（= 0.15%，
      实测夹在「平台噪声 ≤93 px」与「真实颜色改动 563 px」之间）+ `scale: "css"` +
      `animations: "disabled"`）——整页截图把进度条录在折叠线以下，
      看不见它；⑤ **两个平台**的 PNG 基线都要有（win32 + linux）。
    verify: >-
      win32：`npx playwright test design-fidelity` 3 条全绿（144 张 win32 基线）。
      linux：pinned `mcr.microsoft.com/playwright:v1.56.1-noble` 容器内同样 3 条全绿
      （144 张 linux 基线，与 win32 逐名配对）。**反证臂**：把 `.succeeded` 的
      `border-left` 从 `--success` 改成 `--danger`（DOM 一字未动）⇒ **结构签名判据仍绿**、
      整页像素判据**仍绿**（0.36% < 2% 阈值）、**元素级像素判据判红**（563 px）——
      这同时证明「像素门禁真在看」与「outline 判据不靠颜色」。
      `design-outline-guard.spec.ts` 的「只改颜色 ⇒ 不误报」6 条仍全绿。
    status: PASS
  - id: EC-03
    criterion: >-
      联调补齐（7 条带 UI + 3 条如实登记）：① `GET /runs/{id}/reviews` →
      `inspectionClient.reviews()` + `ReviewPanelSection`（逐条 `verdict` / `findings` /
      `reviewed_by` / `reviewer_model` / `reviewed_at`；**前端不做聚合**）；②
      `PUT /projects/{id}/direction` → `projectsClient.setDirection()` +
      `ProjectDirectionEditor`（空输入 = 清除，发 `null`）；③ programs 四条 →
      `programsClient.ts` + `ProgramsSection`（列表 + 推进按钮，最小读面）；④
      `GET /library/{id}` / `GET /projects/{id}/memory/validity` / `POST /tasks/{id}/retry`
      → 只加 client 方法 + 进 `UNCONSUMED.md` 白名单。
    verify: >-
      `pnpm --dir apps/web test` 全绿（含新增 6 条路由判据）；`npx playwright test` **全量
      106 条 e2e 全绿**（含新桩路由 `stub-routes-integration.ts` —— 未替身的请求会让 e2e
      立刻失败，所以接线必须同轮补替身）。`npx tsc --noEmit` 与 `npx eslint src --max-warnings 0`
      均无错。
    status: PASS
  - id: EC-04
    criterion: >-
      路由覆盖判据 + 登记表：① `apps/web/tests/unit/backend-route-coverage.test.ts` ——
      从 `docs/api/openapi.m13.json` 读**全部**路由，断言「每条要么有 client 形状同形的
      消费者、要么在 `docs/frontend/UNCONSUMED.md` 里」；②
      `apps/web/tests/unit/unconsumed-registry.test.ts` —— 白名单每条理由非空非占位符、
      路径真的存在于 OpenAPI、不重复；③ 读取原语单列成 `unconsumedRegistry.ts`
      （非 `.test.ts`，否则 import 方会把判据注册两遍 —— 实测撞过）。
    verify: >-
      两个判据文件 6 条全绿；**反证臂两条**：把白名单里 `/health` 改成 `/health-typo`
      ⇒ `every whitelisted route really exists…` 判红并点名该行；把 `/health` 的理由改成
      `-` ⇒ `no whitelist entry has an empty or placeholder reason` 判红并点名该行（均实测，
      随后还原）。
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产：`tools/verify_goal104_closeout.py`（标准断言集 + 本轮断言集 + 记录面）与
      `tools/goal104_closeout_assertions.py`（七条 EC 的产品面判据，含 EC-07 的 workflow
      不回退）；两者登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`
      的 `_VERIFIERS` 与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的
      `IN_SCOPE`。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal104_closeout.py --root .
      --verdict-only` 全 PASS、判词不含绝对路径；`_VERIFIERS` / `IN_SCOPE` 两条登记判据
      在 m0 里过（本文件与断言集都要过 ruff / mypy / 规模四道门）。
    status: PASS
  - id: EC-06
    criterion: >-
      宪章记账：程序表追加序 72（紧接序 71、不留空行）；阶梯「复检」行的 `当前级` 追加
      「设计门禁四组合」与「十一相进基线」并在 `依据 GOAL` 收录本 GOAL；`下一级` 逐字不动；
      进展记录与修订记录各追加一行（5 格、表内连续，各 3 行）。
    verify: >-
      `MAINLINE.md` 的程序表 / 阶梯 / 进展 / 修订四处判据（`tests/tooling/
      test_mainline_program_is_intact.py`、`test_mainline_research_ladder_advances.py`、
      `test_mainline_archive_convention.py`）全绿；本 GOAL 的阶梯行**不得**出现
      「视觉回归已完全覆盖」这类过度声称（收口验证器 `ladder-next-level-not-claimed` 判）。
    status: PASS
  - id: EC-07
    criterion: >-
      核对不回退：`W-7`（`console-frontend` 的 `runs-on: ubuntu-24.04`）与 `W-5`
      （`quality` 的 `timeout-minutes: 30`）已在 `bd1482ce` 修好；本轮**只核对**，不改回。
    verify: >-
      `grep -c "runs-on: ubuntu-24.04" .github/workflows/m0-quality.yml` = 1；
      `grep -c "timeout-minutes: 30"` = 1；两者无 `runs-on: ubuntu-latest` /
      `timeout-minutes: 20` 的回退形态。收口验证器按 **job 定位**判（`workflow-<job>-fix-intact`）
      —— 不扫全文件，因为 `eval-gate` / `container-quality` 等 job 合法地写着这两个回退形态。
      **执行纪律 5.9 的凭据面同轮取证**：`tools/credential_audit.py` 四面 **`offenders=0`**
      （`tracked` 5056 文件 / 命中 105 / 放行 105 / offenders 0；`records` 1092 / 5 / 5 / 0；
      `config_db` 1 / 0 / 0 / 0；`logs` 938 / 0 / 0 / 0；终态行
      `PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）`）。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 扩既有判据的受判面（组合集 / 路由集 / 站点集），逐条申报为什么不是放宽
    - 同轮重生成 `design-outlines.json` 与两平台 PNG 基线（结构性新增必然改签名；逐条申报理由）
  forbidden:
    - 修改受保护判据的语义或阈值（视觉基线只在**结构性新增**时重生成，并逐条申报）
    - 收紧 `maxDiffPixelRatio` / `maxDiffPixels` 的**例外**只写在文档里而不落判据
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - git add -A（并发工作树；只加显式路径）
    - 伪造或夸大验证证据（尤其：把「只产 win32 基线」说成两侧都有、把 skip 记成 PASS）
    - "不得用白名单刷覆盖率数字（每条必须有理由，且必须先尝试真消费者）"
    - "不得只产 win32 截图基线就推送"
    - "不得把「环境漂移」记成「真缺陷」（三类 CI 红分开登记）"
    - 宣称项目安全（R-M1 未收口）
    - 宣称投递语义为「恰好一次」（at-least-once + 幂等 + 去重）
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（§9 姿态只放开点名项）
  - 同一失败签名超过 fix_policy 上限
  - 新增第三方依赖
child_plans:
  - .cursor/plans/tasks/PLAN-20261103-104-design-gate-and-integration-coverage.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261103-104-design-gate-and-integration-coverage.md
memory_entries:
  - .cursor/memory/entries/MEM-20261103-238-a-css-module-key-can-be-undefined.md
---

# GOAL-20261103-104 —— 设计门禁扩到四组合 + 联调补齐 + 三条悬空样式

## 目标与退出标准

承用户 goal-mode 指令（序 72）。上一轮（GOAL-103）把「run 走到哪一步」变成一等事实，
但**验证那件事的门禁本身**有三处名不副实；同时后端 132 条路由里有 10 条没有任何前端
消费者。本轮的全部理由就是把「覆盖」从名义变成可证伪。

**缺口一：三条悬空的样式引用，全部静默失效。**
`PhaseProgress.tsx:102,106` 引 `styles.muted`（来自 `LivePage.module.css`），而那个共享
模块**没有** `.muted` ⇒ 两处渲染成 `className={undefined}`。`CommandCenterPage.module.css`
与 `ConsoleLoading.module.css` 用 `var(--bg)`，`tokens.css` 里叫 `--bg-app`。
`LivePage.module.css` 用 `var(--text-dim)`，最接近的是 `--fg-faint`。
**三处都不会让任何一道门变红**：CSS-module 的 TS 类型是
`{ readonly [key: string]: string }` ⇒ 任何键都过 typecheck；`var(--anything)` 同理。

**缺口二：设计门禁只跑一种组合，且十一相在折叠线以下。**
文件头 docstring 声称测「双主题×双密度×中英文」，实现只跑 `dark/normal/zh`。
`run-timeline` 不选 run、`run-timeline-substrate` 的 run 没有冻结协议正文 ⇒ 两条基线都
只渲染空态；`design-outlines.json` 里 `phase-node` **零命中**。补了路由之后仍然不够：
1280×720 视口里进度条在**折叠线以下**，整页截图把它录进文件却录在不可见区域 ——
实测把 `.succeeded` 的边框色从 `--success` 改成 `--danger`，整页像素判据与结构签名判据
**都仍然绿**。

**缺口三：10 条后端路由没有前端消费者。**
其中 7 条（评审判词 / 研究方向 / 研究程序四条 / 库单件 / 记忆时效 / 任务重试）是用户真的
会问「为什么页面上看不到」的面。另外 3 条（库单件 / 记忆时效 / 任务重试）在本轮接 client
之后**仍然没有 UI** —— 那必须**如实登记**，不能拿「加了方法」冒充「有消费者」。

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

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品 vs 测试各半）；**修产品优先，禁改断言迁就** |
| 视觉基线漂移 | `design-fidelity` / outline 判红 | 本轮的**结构性新增**是预期内的 ⇒ 同轮重生成基线并**逐条申报**为什么不是放宽 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按既有配方重跑；配方不覆盖 ⇒ 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED（infra 非代码缺陷） |
| Windows quality 超时 | job 卡满预算窗口 | **已知 W-5**（预算已抬到 30 分钟）；如仍超时按 infra 重跑，不擅自改 workflow |
| Playwright 装不上 | `does not support chromium on ubuntu26.04-x64` | **W-7**：runner 已钉 `ubuntu-24.04`；若回退形态出现 ⇒ EC-07 判红 |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：七个 EC 全 PASS + 独立 RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## CI 台账

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `e9374172` | [M0 41534081970](https://github.com/Eswink/research-system-new/actions/runs/41534081970) / [Push 41534081435](https://github.com/Eswink/research-system-new/actions/runs/41534081435) | **M0 `failure`**（`quality-ubuntu` / `quality-windows` / `console-frontend` 三条红）；Push 全 success | **交付 tip**（七条 EC + 收口资产 + 宪章记账）。三条红逐条分类：① `console-frontend` = **真缺陷**：元素级像素判据用 `maxDiffPixels: 0`，CI ubuntu 报 60 px 字体抗锯齿差 ⇒ 改 196 px（实测夹在噪声 ≤93 与颜色改动 563 之间）；② `quality-*` = **真缺陷**：`unconsumedRegistry.ts` 的旧名仍在提交里（重命名时 `git mv` 失败而回退的 `mv` 留下了已暂存的旧路径），命名门禁点名它；③ 两条 `quality-*` 还叠加 `test_m0_witness_matches_the_tree` 红 —— 见证在跑门后被记录改动，属**流程顺序**而非缺陷。三件一并修在下一提交 |
| `1c10386b` | [M0 41546893623](https://github.com/Eswink/research-system-new/actions/runs/41546893623) / [Push 41546892869](https://github.com/Eswink/research-system-new/actions/runs/41546892869) | **M0 `success`（8/8 job success）**；**Push 全 success** | **收口 tip**（三件 CI 红逐类修好后）。`console-frontend` 的 `Console e2e` 与 `Console live API e2e` **两步都 `success`** —— 这正是 `W-7` 的目的：此前 34 路由像素门禁在 CI 上**从未执行**。本地见证终态行 `PASS: profile=m0; 23 deterministic checks`（`1c10386b`，跑门期间树未变）。 |
| `04e1f75e` | [M0 41553868343](https://github.com/Eswink/research-system-new/actions/runs/41553868343) / [Push 41553868965](https://github.com/Eswink/research-system-new/actions/runs/41553868965) | **M0 `success`（8/8 job success）**；**Push 全 success** | **ACHIEVED 封印提交**（只改 GOAL 状态 / 台账行 / 见证）。本地见证终态行 `PASS: profile=m0; 23 deterministic checks`（跑门期间树未变）；两树复检 82 判词 `sha256` 相同（`1f1d14f7022f70fc003cef0b7e451a669faa28c82d158f3bd3281561c2a475ca`）。 |
| `e7d189a0` | [M0 41561959463](https://github.com/Eswink/research-system-new/actions/runs/41561959463) / [Push 41561958805](https://github.com/Eswink/research-system-new/actions/runs/41561958805) | **M0 `success`（8/8 job success）**；**Push 全 success** | **凭据面补齐后的收口 tip**：执行纪律 5.9 的 `credential_audit.py` 四面实测 `offenders=0`（当轮 5055 / 1092 / 1 / 938 文件；命中 110 条全落白名单。此后新增判据模块 ⇒ 终局 `tracked` = **5056**），并升级为判据 `credential-faces-clean`（**它自己跑审计**，不依赖记录里的散文）。本地见证 `PASS: profile=m0; 23 deterministic checks`；两树复检 **82** 判词 `sha256` 相同（`1f1d14f7022f70fc003cef0b7e451a669faa28c82d158f3bd3281561c2a475ca`）。 |
| `1f9cb9a0` | [M0 41568071591](https://github.com/Eswink/research-system-new/actions/runs/41568071591) / [Push 41568070839](https://github.com/Eswink/research-system-new/actions/runs/41568070839) | **M0 `success`（8/8 job success）**；**Push 全 success** | **`e7d189a0` 的 CI 读数回填 + 见证重封**（只改 `.cursor/`）。它记录了 `e7d189a0` 那一轮的 `M0 41561959463` 8/8 与两树 82 判词 `sha256`。**这一行是事后补登**：该提交落下时本台账已收口，`test_goal_commit_chain_reaches_the_ledger` 在随后的 m0 里点名它（链 6、台账 4）—— 如实补记读数，不改历史、不改判据。 |
| `f4be0b4e` | [M0 41574142198](https://github.com/Eswink/research-system-new/actions/runs/41574142198) / [Push 41574142323](https://github.com/Eswink/research-system-new/actions/runs/41574142323) | **M0 `success`（8/8 job success）**；**Push 全 success** | **凭据面读数按「所属的树」校正**：`5055` 是 `goal104_credential_faces.py` 加入**之前**那一轮的 `tracked` 文件数，终局树是 `5056`（多出的一个就是那个判据模块）。两个数各自绑到所属的提交，**没有**用后一个覆盖前一个。此提交是当前 HEAD，故对本台账享「结构例外」—— 但按 5.2「一次付清全部欠账」，它与上一行同轮补齐。 |
| `2b13b649` | [M0 41580292093](https://github.com/Eswink/research-system-new/actions/runs/41580292093) / [Push 41580291452](https://github.com/Eswink/research-system-new/actions/runs/41580291452) | **M0 `success`（8/8 job success）**；**Push 全 success** | **收口 tip**（只改 GOAL 记录 + 见证）：为 `1f9cb9a0` 与 `f4be0b4e` 补台账两行、同步迭代日志 `commits` 格到六条、重封见证。当时它是 HEAD ⇒ 结构例外；**序 73 的归档推送把它推离 HEAD 后**，反方向判据按 5.2 点名它，本行即按该点名补记。**这一轮 `quality-windows-latest` 是 `success` 而非 `cancelled`** —— `W-5` 的 timeout 30 修复（`bd1482ce`）在这一轮生效 |
| `202aa9c6` | 与 `a5e6e61c` **同一次 push**（无独立 run） | 该推送的读数见下一行；**本行不冒领** | **序 73 归档**（宪章两表各移出最旧一行）：新建 `archive/MAINLINE-2026-11-01-progress-102-only.md` 与 `archive/MAINLINE-2026-11-01-revisions-70-only.md`（原文搬运、仅修相对链接基准），指针插在**各表最后一个数据行之后**（不是表后），写回 `sha256=e157a5b8…`。两表各剩 2 行、短行 0、CRLF 430/430/430。**主题点名 `goal104` 是因为它改的是那个 GOAL 的记账面**；这一行由反方向判据在其被推离 HEAD 后点名补记 |
| `a5e6e61c` | [M0 41601984903](https://github.com/Eswink/research-system-new/actions/runs/41601984903) / [Push 41601984192](https://github.com/Eswink/research-system-new/actions/runs/41601984192) | **M0 `success`（8/8 job success，含 `console-frontend`）**；**Push 全 success（3/3）** | **归档轮的收口 tip**（两笔记录面欠账一次付清）：① 为 `2b13b649` 补台账行并同步迭代日志 `commits` 格到七条；② `tools/verify_goal102_closeout.py` 的修订行断言改读「活跃面 + 归档」—— 归档把 GOAL-102 那一行搬走后它判负，是**假负**（断言绑错了面），不是回归。本地见证 `PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、`tree changed during the run: False` |
| `80a3e614` | 与 `b712a989` **同一次 push**（无独立 run） | 该推送的读数见序 73 台账；**本行不冒领** | **归档轮的两笔台账欠账一次付清**（只改 `.cursor/`）：为 `2b13b649` 与 `a5e6e61c` 补台账行并同步迭代日志 `commits` 格；本条由反方向判据在它被序 73 的推送推离 HEAD 后点名补记（`test_goal_commit_chain_reaches_the_ledger` 实测点名「链 10 个，台账 9 个」）。**没有冒领 CI**：它与序 73 的交付提交同一次 push，`head_sha` 指向后者 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261103-104 | `e9374172` → `1c10386b` → `04e1f75e` → `e7d189a0` → `1f9cb9a0` → `f4be0b4e` → `2b13b649` → `202aa9c6` → `a5e6e61c` → `80a3e614` | 定向套件全绿（见 RECHECK 读数）+ 全量 m0 见证 + web 97/97 + e2e 106/106 + linux 容器 3/3 | **M0 `success` 8/8**（`1c10386b`；`e9374172` 三条红已逐类修好）；Push success | 三条红：像素容差 0 在 CI 假红（改 196 px）、旧文件名残留、见证顺序 | 七条 EC 全 PASS；残余 `W-1`…`W-4` 与未覆盖 `U-1`…`U-3` 已登记 | 见§「残余与未覆盖范围」（四组合全积、元素级覆盖扩面、阈值标定、路由「真的被调用」） |

## 影响报告

（**实测**，非预判。）

- **Domain/API/schema**：**零后端改动**。新增的 `MemoryValidityDto` / `MemoryValidityViewDto`
  是 `types.ts` 对**既有** OpenAPI schema 的补登记；`docs/api/openapi.m13.json` 零 diff
  ⇒ `test_openapi_snapshot` 不受影响。
- **安全/凭据**：零变化（无新凭据、无新出网面、无新工具面）。新增的读面方法都落在既有
  路由的既有鉴权面；`ProgramsSection` 的「推进一轮」调用的是**已有**的写面。
  **实测依据**（执行纪律 5.9，不是断言）：`tools/credential_audit.py` 四面 `offenders=0` ——
  `tracked` 5056 文件（命中 105 / **放行 105 / offenders 0**）、`records` 1092（5 / 5 / **0**）、
  `config_db` 1（0 / 0 / **0**）、`logs` 938（0 / 0 / **0**）；终态行
  `PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）`。放行数**单独统计**——没有用
  「没扫到」冒充通过。
- **兼容性/迁移**：零 migration。前端新增组件全是**加性**；`.muted` 改局部类**改变观感**
  （两处此前是 `className={undefined}`），那正是修复的目的。
- **上游**：零依赖变化（`@playwright/test` 仍 1.56.1；linux 基线在 pinned `noble` 容器里生成）。
- **视觉基线**：`design-fidelity` 从 68 张（34×2）扩到 **288 张**（35 路由 × 4 组合 × 2 平台
  \+ 4 张元素级 × 2 平台）。**110 组新增**、2 条路由（`portfolio-projects` /
  `run-timeline-substrate`）因 DOM 新增而重生成、其余旧基线**逐字节未动**（13 张被重跑
  产生的 ≤60 px 抗锯齿噪声已 `git checkout` 回退，两平台复跑仍绿）。

## 残余与未覆盖范围

（**没做到**的那部分，逐条明写。空着等于宣称「没有缺口」，那是伪造验证证据。）

### 残余（本轮已交付里仍然存在的缺口）

- `W-1`｜**四组合是对角取样，不是全笛卡尔积**：2 主题 × 2 密度 × 2 语言 = 8 种组合，本轮
  只跑 4 种（每轴各出现两次）。任一轴漂移必然撞上至少一条基线，但**两轴同时**以互相抵消
  的方式漂移（例如深色下密度与语言刚好互换）在原理上不会被这 4 条捕获。8 组合的成本是
  维护面翻倍（288 张基线），本轮没有付。
- `W-2`｜**元素级像素门禁只覆盖 `phase-track` 一个组件**：它是本轮唯一「整页看不见但用户
  真的会看」的面。其它折叠线以下的内容（长列表尾部、抽屉、展开态）仍然只有结构签名覆盖，
  没有元素级像素 —— 同类问题在别处存在但没有判据。
- `W-3`｜**元素级阈值是实测标定的，不是零容差**：`maxDiffPixels: 196`（0.15%）夹在
  「跨机器字体抗锯齿噪声 ≤93 px」与「真实颜色改动 563 px」之间。这个数字**只对这一块
  元素**成立（1002×131）；整页截图仍用 `maxDiffPixelRatio: 0.02`（0.36% 的单色改动不会
  让它红），把整页阈值也收到这个量级会与整页的字体渲染差异冲突。两个阈值都没有被
  系统性地标定过 —— 它们各自只对本轮实测过的两种改动成立。
- `W-4`｜**路由覆盖判据是「形状同形」而不是「真的被调用」**：它读 client 源码里的路径
  字面量（含一跳 helper 拼装），无法证明那个方法**在 UI 里被调用**。三条 client-only 方法
  因此靠**人写的白名单理由**区分于真消费者 —— 判据只能保证「没有完全没人碰的路由」。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1`｜**`ProgramsSection` 只有列表 + 推进**：建程序表单、逐轮决定时间线、
  `cited_facts` 展开、程序与 run 的交叉跳转都不在射程。本轮目标是「路由有消费者」，
  不是「程序页做完了」。
- `U-2`｜**`ReviewPanelSection` 不做面板聚合**：`aggregate_panel` 的 advisory 结论、
  平票、分歧逐票呈现都在领域侧，前端只逐条列原文。把聚合搬到 UI 是刻意不做的（会漂移）。
- `U-3`｜**`UNCONSUMED.md` 的诚实性靠人**：判据能查「理由非空 / 路径存在 / 不重复」，
  查不了「这个理由是不是真的」——一个敷衍但有内容的理由仍然过。这是文本判据的上限。

### 声称边界（**不得宣称**的事）

- `R-1`｜**不得宣称「视觉回归已完全覆盖」**：四组合是对角取样（`W-1`），元素级像素只有
  一个组件（`W-2`），整页阈值仍是 2%（`W-3`）。
- `R-2`｜**不得宣称「每条路由都有消费者」**：`/health` 与三条 client-only 方法是**登记**
  在 `UNCONSUMED.md` 里的，登记 ≠ 消费（`W-4`）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-03 | ACTIVE | 建档：序 72；七个 EC |
| 2026-11-03 | ACHIEVED | 七条 EC 全 PASS；`RECHECK-20261103-104` PASS；全量 m0 `PASS: profile=m0; 23 deterministic checks`；两树复检 82 判词 sha256 相同；CI `1c10386b` M0 8/8 success。残余 `W-1`…`W-4` 与未覆盖 `U-1`…`U-3` 逐条明写 |
