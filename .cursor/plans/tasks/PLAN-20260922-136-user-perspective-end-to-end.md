---
id: PLAN-20260922-136
slug: user-perspective-end-to-end
title: 用户视角端到端验收 + `partial` 页诚实标注核对（GOAL-011 EC-04）
status: IN_PROGRESS
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260922-011 cycle 7 = EC-04（用户视角端到端验收 + `partial` 页诚实标注核对）。授权来源：
    2026-09-22 用户 goal 模式指令 frontmatter `authorization.ref`——(1) live-gated 真实调用（端点
    `ANTHROPIC` + `agnes-2.5-flash`，凭据仅在本机 gitignored `.env`，键名 `LLM_MAIN_KEY`）；
    (2) **允许真实检索出网**——仅 NCBI E-utilities（`eutils.ncbi.nlm.nih.gov`），只在该 provider 的
    `network_domains` 声明范围内，次数取最小必要；(3) **EC-04 允许在本机启动真实控制面/前端并操作 UI**
    （仅本机、仅该端点；**不上传任何截图/快照到外部服务**；截图或读面快照落 `scratch/` 且**不进仓库**）；
    (4) 凭据纪律不放松（值不得进任何 tracked 文件/DB/记录/日志/回显；`RESEARCHOS_AGENT_RUNTIME`
    只作单条命令内联前缀，不得写进 `.env`）；(5) 默认 runtime 保持 Fake、默认 CI 离线；**不得为了
    跑通而放宽出站判据**（`tests/egress_guard.py` 是结构判据），live 类用例必须挂 `requires_live_llm`；
    (6) push-to-main-for-CI（只推 main、不 force、不重写历史）。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；放宽验收门凑成功；为跑通而放宽出站判据；新增依赖或改上游 pin；
    把真实 runtime 设为默认；把凭据写进 CI；把截图/读面快照提交进仓库；**粉饰 `partial` 页的诚实结论**
    （不一致就记不一致）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-136 — 用户视角端到端 + `partial` 页诚实标注核对（GOAL-011 EC-04）

## 目标

EC-04 要的是**用户视角的端到端验收**：真实数据下走完整流程——**建项目 → 选协议 → 跑真实 run →
看制品/证据/预算/血缘**——并留下**可复核记录**；顺带**复核前端 `partial` 页在真实数据下的诚实标注
是否与实际一致**，不一致如实登记。

起点实测（本 PLAN 的 derive 证据，全部只读）：

- **五步各自都有既有面**：`POST /projects`（`routers/projects.py:81`，201）·
  `GET /protocol-templates`（`routers/protocol_drafts.py:90`）·
  `POST /projects/{project_id}/runs`（`routers/runs.py:91`）· 读面
  `GET /runs/{id}`、`/runs/{id}/artifacts`、`/runs/{id}/evidence`、`/runs/{id}/cost-forecast`、
  `GET /projects/{id}/lineage`（`routers/lineage.py:85`）。**本 PLAN 不新增端点**。
- **真实 run 的装配已存在**（GOAL-011 EC-01/EC-02 的判据用的就是它）：
  `tests/e2e/live_run_support.py::openhands_deps`（run-ready 装配 + 真实 adapter，`map_tools=True`）
  + `with_run_chain_capabilities(deps, ncbi_run_chain_provider(deps))`（运行链检索能力步）。
  载体协议 = `examples/protocols/real_retrieval_research_v1.yaml`（EC-02 的合约
  `real_retrieval_deliverable` 要求 ≥1 条**检索**来源）。
- **`partial` 级已有一层结构判据**：`apps/web/tests/unit/page-support-coverage.test.ts`
  （33 条规范路由必须各有条目、非 `full` 必须有可读 `reason`、`gap` 只允许 `ops/matrix`）。
  **缺口**：它**不判 `reason` 是否与真实行为一致**——那正是 EC-04 要补的那一半。
- **`partial` 理由的声明源**：`apps/web/src/navigation/pageSupport.ts` 的 `GAPS` 常量
  （与 `docs/frontend/CONSOLE_PAGE_MAP.md` 同源维护）。

## 验收条件

- **AC-1 五步在真实数据下走通**：以**既有 API 面**完成「建项目 → 选协议 → 跑真实 run →
  看制品/证据/预算/血缘」，且 run 的 canonical 终态**如实记录**（只有 `SUCCEEDED` 是成功；
  `FAILED` 不得写成成功）。
- **AC-2 可复核记录落 `scratch/`**：读面快照（JSON）+ 步骤说明，覆盖上述五步；
  **不进仓库**、不上传任何外部服务；凭据值不出现在记录里。
- **AC-3 `partial` 页诚实标注逐条核对**：对**与五步相关的** `partial` 页，把 `GAPS` 里声明的
  理由与**真实数据/真实行为**逐条比对，给出「一致 / 不一致 + 证据」；
  不一致 ⇒ 若属**措辞**问题就改措辞（不改判据、不放宽门禁），若属**行为**问题则**如实登记为 W**。
- **AC-4 出站与凭据纪律不变**：默认门离线；live 步骤只用单条命令内联前缀开；
  `tests/egress_guard.py` 一行不改；真实调用取**最小必要次数**并如实记账。
- **AC-5 规模门禁**：50 行函数 / 450 行文件两道门绿；贴线文件（`composition.py` /
  `phase_runner.py` / `service.py`）**零增长**。

## 计划开始前的定案（写死，执行中不得回退）

- **D-1 记录形态 = 读面快照，不是浏览器截图**。EC-04 原文允许二选一（「读面快照**或**本机截图」）。
  选快照的理由：可复核性更高（同样是真实数据、可被任何人重算与比对），且不引入浏览器/前端构建
  这条与验收目标无关的失败面。**若**本轮有余量再补跑既有 live console 套件，作为附加证据
  （**不**作为 AC 的必需项；跑了就记、没跑就如实写没跑）。
- **D-2 「建项目」= 真的建一个新项目**并在其中启动 run（`POST /projects` → 在**该** project_id 下
  `POST /projects/{id}/runs`）。已知边界：run-ready 夹具下**目录**仍钉在夹具项目
  （`routers/runs.py:95-97` 的 docstring 逐字写着），⇒ 本轮要在记录里写明「项目归属跟随路径、
  目录为受控夹具」这条**如实边界**，不把它说成「生产组合根下的多项目隔离」。
- **D-3 载体协议 = `real_retrieval_research_v1.yaml`**：它是 EC-01/EC-02 真实 run 的同一份载体
  （有检索来源、终态可达 `SUCCEEDED`），换协议会让本轮不再是「**用户视角**复现既有真实链」。
- **D-4 诚实核对只对**与五步相关的**页**：`portfolio/projects`（多项目与删除语义）、
  `plan/protocol`（协议选择）、`run/timeline`（run 详情/暂停恢复）、`library/lineage`（血缘）、
  `govern/budget`（预算预测）。其余 `partial` 页本轮**不**逐条核对，如实写明「本轮未覆盖」。
- **D-5 不改产品行为**：本轮是**验收**轮。发现的措辞不一致 ⇒ 改措辞；发现行为与声明不一致 ⇒
  登记为 W 并**不**顺手改产品代码（避免把验收轮变成实现轮，改由下一轮 derive）。

## 实施清单

- [ ] **WP1** live 端到端脚本（`scratch/`，**不进仓库**）：以既有 API 面走五步，
  把每一步的请求/响应落 JSON + 步骤说明。
- [ ] **WP2** `partial` 页诚实标注逐条核对：五页逐条给「一致 / 不一致 + 证据」，
  必要时改措辞（只改 `pageSupport.ts` / `CONSOLE_PAGE_MAP.md` 的**文字**）。
- [ ] **WP3** 判据：若发现「声明与行为会漂」的真空面，补一条**离线**判据钉住（不空转、可按压）；
  若既有判据已覆盖，如实写明「已覆盖」而**不**重复造判据。
- [ ] **WP4** GOAL 回写（EC-04 状态 / 迭代日志 / 台账）+ 本轮记录。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 五步的端点都存在，且**不新增** | `rg -n` 于 `services/api/routers/{projects,runs,lineage,protocol_drafts}.py` |
| E-2 | 真实 run 的装配与载体协议 | `tests/e2e/live_run_support.py`（`openhands_deps` / `with_run_chain_capabilities` / `ncbi_run_chain_provider`）；`examples/protocols/real_retrieval_research_v1.yaml` |
| E-3 | `partial` 已有结构判据、缺「理由是否属实」 | `apps/web/tests/unit/page-support-coverage.test.ts`（65 行，三条断言） |
| E-4 | `partial` 理由的声明源 | `apps/web/src/navigation/pageSupport.ts` 的 `GAPS`（`docs/frontend/CONSOLE_PAGE_MAP.md` 同源） |
| E-5 | run-ready 夹具下目录仍是夹具项目 | `services/api/routers/runs.py:95-97` 的 docstring 逐字 |
| E-6 | 五步走通的读面快照 | `scratch/goal011-c7-e2e/`（本轮产出，不进仓库） |
| E-7 | `partial` 逐条核对结论 | 本 PLAN 的「核对结论」表（下节）+ GOAL 迭代日志 |

## 影响报告

- **Domain / API / schema**：预期**零改动**（验收轮）。若改措辞只动前端文案与文档，不动 DTO/路由/
  OpenAPI 快照。
- **兼容性 / 迁移**：无。
- **安全 / 凭据**：不新增凭据面；记录里不出现凭据值；快照只落 `scratch/`（gitignored）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（`R-6` 词表 pin，可选）或 EC-06（收口复检）；EC-03 需先拍板 (A)/(B)。

## 状态历史

- 2026-09-22：derive（WP0）。只读勘察五步端点、真实 run 装配、`partial` 标注源与其既有判据；
  定案 D-1…D-5；未改产品代码、未发起任何真实调用。
