---
id: PLAN-20260923-144
slug: experiment-evidence-chain-traceability
title: 实验产出的证据链可追溯：产物/来源进 canonical + 内容 digest 可重算 + 镜像摘要可独立复核（GOAL-012 EC-03）
status: IN_PROGRESS
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）：用户**已拍板路径 (A)**，
    并由 PLAN-20260923-140（冻结通道）与 PLAN-20260923-142（真实实验执行链）落地；本 PLAN 是
    其后的 **EC-03**——**授权真实实验执行**（既有 Docker 后端 `research-os-sandbox:m9-test`、
    本机容器；遵守既有安全姿态：不挂 docker socket、不 privileged、不 host home），
    **不做新的 live LLM 调用**（真实 run 侧复用 EC-02 的样张；本 PLAN 的判据全程离线 + 本机容器）。
    凭据纪律照旧：值**不得**写入任何 tracked 文件 / DB / 记录 / 日志 / 回显；`RESEARCHOS_AGENT_RUNTIME`
    **只作单条命令的内联前缀**、不写入 `.env`。默认姿态不变（默认 runtime=Fake、默认 CI 离线；
    `tests/egress_guard.py` **不放宽**）。
    本 PLAN 明文不做：改产品代码使其通过；改共享夹具缺省语义；放宽 §9 任一条默认 deny 面；
    放宽验收门或降低断言强度；skip/删除测试；`git add -A`；伪造或夸大验证证据。
    **若本 PLAN 必须在「放宽默认 deny / 放宽出站判据 / 放宽验收门」三者中择一才能走通 ⇒ 立即
    停止并记 BLOCKED。**
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-144 — 实验产出的证据链可追溯（GOAL-012 EC-03）

## 目标

让「实验跑过」与「产物已登记且可追溯」成为**同一条可判据的事实**：一次经**既有产品缝**执行的
沙箱实验，其产物（`stdout.log` / `stderr.log` / `experiment_result.json` / 合约声明的
`analysis_report`）与**来源记录**进 canonical，读面可追溯且**可独立复核**（内容 digest 可重算、
镜像摘要可与 daemon 独立比对、语义摘要跨重跑稳定）；**反证成对**：去掉产物（或去掉登记它的那一步）
⇒ 判据红。判据**不得**拿模型自述当实验产物。

## 计划开始前的定案（写死）

- **D-1 判据落点**：新文件 `tests/e2e/test_ec03_experiment_evidence_chain.py`（`requires_docker`，
  **零出网**，复用 EC-02 的离线装配：run-ready + `with_sandbox_experiment` + 会交付的受控执行体）。
  `test_sandbox_experiment_seam_docker.py` **不动**（它判的是缝/容器的机械面，本 PLAN 判的是
  **证据链的读面可追溯性**——两者互不替代）。
- **D-2 「可追溯」判三条，各自独立可判**：
  1. **产物在读面**：`GET /runs/{id}/experiments` 的 `artifact_ids` 覆盖四件产物；
     `GET /runs/{id}/artifacts` 列出**同样的**制品 id（两读面同源）。
  2. **内容可重算**：`GET /artifacts/{id}/content` 取回**字节** ⇒ `Digest.of_bytes(bytes)` 必须等于
     该制品对应证据条目的 `content_digest`（digest 不是声明出来的，是算出来的）。
  3. **来源可独立复核**：实验记录里的 `image_digest` 必须等于**独立查 daemon** 得到的
     `research-os-sandbox:m9-test` 镜像 Id（另一条代码路径，不经产品适配器）；
     `environment_digest` 非空；**语义摘要**（`record.semantic_metrics_digest`，canonical 事实）
     在两次执行之间**相同** ⇒ 「同 seed / 同镜像 ⇒ 同语义」这条复现口径被判据看着。
- **D-3 反证成对（先红后绿）**：同一条链，换一个**不写声明产物**的实验脚本（写 `report.txt` 而
  不是合约声明的 `analysis_report`；其余逐字同构）⇒ ① 验收门**拒收**且判词**点名**
  `analysis_report`；② 产物读面上**没有** `analysis_report`，而 `stdout.log` / `stderr.log` /
  `experiment_result.json` / `report.txt` **仍在** ⇒ 红的理由**恰是「声明产物缺失」**，
  不是「实验没跑」。**按压**（落 RECHECK）：临时去掉登记产物的那一步 ⇒ 判据红 ⇒ 复原绿。
- **D-4 不得拿模型自述充当实验产物**（EC-03 明文）：判据显式检查证据的 `source_origin` 指向
  `<experiment_run_id>:<产品名>`（实验路径），且四件产物的证据 `source_trust_label` 不是
  review 会话交付物那条（`session_message`）。
- **D-5 明确不改**（反证面）：**产品代码零改动**（本 PLAN 只加判据与记录）；不动
  `examples/experiments/sort_analysis_baseline.py`；不动共享夹具缺省 runtime；不动
  `tests/egress_guard.py`；不动策略面；不新增依赖。
- **D-6 真实 run 侧**：EC-02 的样张 `scratch/goal012-c2-live-sample.json` 已记录「实验产物与证据
  **同时**在场且指向同一个 run」；本 PLAN 把它写进**独立复检脚本**（只用标准库、不 import 仓库代码）
  的数据层断言，**不重跑真实端点**（live 调用取最小必要）。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | **产物进 canonical 且两读面同源** | `pytest tests/e2e/test_ec03_experiment_evidence_chain.py -q` ⇒ 主判据里 `experiments` 与 `artifacts` 两面的制品 id 一致且覆盖四件产物 | 待跑 |
| AC-2 | **内容 digest 可重算** | 同文件：对每件产物 `Digest.of_bytes(content)` == 证据 `content_digest`（逐件断言） | 待跑 |
| AC-3 | **来源可独立复核** | 同文件：`image_digest` == 独立 `docker image inspect` 的 Id；`environment_digest` 非空；两次执行 `semantic_metrics_digest` 相同 | 待跑 |
| AC-4 | **反证（成对）**：去掉声明产物 ⇒ 判据红且**点名** | 同文件第 2 条：run `FAILED`（判词含 `analysis_report`）、产物读面无 `analysis_report`、其它产物仍在 | 待跑 |
| AC-5 | **不得用模型自述冒充**（D-4） | 同文件：四件产物的证据来源指向实验路径（`<experiment_run_id>:<name>`），非会话交付物 | 待跑 |
| AC-6 | **按压**：去掉「登记产物」那一步 ⇒ 判据红 ⇒ 复原绿 | 按压记录落 `scratch/goal012-c3-press-*.txt` + RECHECK | 待跑 |
| AC-7 | **门与治理**：m0 23/23 + 定向套件 + `validate.py` 绿 + `mypy`/`ruff` 干净 | `run_all_checks.py --profile m0 --keep-going`（DSN 固化 + `LLM_MAIN_KEY=""`）+ 治理校验 | 待跑 |
| AC-8 | **零出网 + 凭据纪律** | 逐条 `egress guard: judged N; blocked 0`；无任何凭据读取（本 PLAN 不需要 live key） | 待跑 |
| AC-9 | **真实 run 侧**（EC-02 样张） | 独立脚本对 `scratch/goal012-c2-live-sample.json` 断言「产物与证据同时在场且指向同一 run」 | 待跑 |

## 实施清单

- [ ] **WP1** 判据（离线 + 容器）：`tests/e2e/test_ec03_experiment_evidence_chain.py`
  （主判据 3 条 + 成对反证 1 条 + 来源非自述 1 条）。
- [ ] **WP2** 按压：临时去掉产物登记/收集那一步 ⇒ 判据红 ⇒ 复原绿（记录落 `scratch/`）。
- [ ] **WP3** 独立复检脚本 `scratch/verify_goal012_c3.py`（只读 / 只用标准库 / 不 import 仓库代码；
  当前树 + 基线树成对），含对 EC-02 样张的数据层断言。
- [ ] **WP4** 门与收口：m0 23/23 + 定向套件 + `validate.py`；`RECHECK-*` +（如需）`MEM-*` + GOAL 回写。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 产物读面与内容读面已存在（无需改产品） | `services/api/routers/experiments.py:98`、`artifacts.py:118`、`artifacts.py:165` |
| E-2 | 产品缝已把实验产物登记进 canonical | `services/api/experiment_support.py`（`register_experiment_evidence` 经 `execute_experiment_task`）+ EC-02 的样张（4 件产物 + 6 条证据） |
| E-3 | 镜像摘要是 daemon 的镜像 Id（可独立复核） | `adapters/execution/docker_backend.py:_resolve_image_digest`（`inspect_image(...)["Id"]`） |
| E-4 | 语义摘要是 cross-rerun 稳定的 canonical 事实 | `packages/application/experiments/metric_extraction.py:90-92`（`semantic_metrics_digest`：非观测性子集的 canonical digest） |
| E-5 | 判据结果 | 待跑（落 `scratch/goal012-c3-*.txt`） |

## 影响报告

- **Domain / API / schema**：无（**产品代码零改动**；判据读的是既有读面与既有 canonical 事实）。
- **产品代码**：无。
- **夹具**：不动任何既有夹具与示例脚本；反证用的**不写声明产物**的脚本在判据内生成（`tmp_path`），
  不进仓库。
- **CI / workflow**：不改；新判据挂 `requires_docker`（非 Linux 容器的 daemon 下如实 skip，
  由 `container-quality` 作业真跑）。
- **安全 / 凭据**：零出网、零凭据读取；容器遵守既有姿态（无 docker socket / 非 privileged /
  不挂 host home）；镜像摘要比对只读 `docker image inspect`。
- **上游版本影响**：无。
- **下一项任务**：EC-04（路径 (B) 否证的独立记录）。

## 状态历史

- 2026-09-23：derive（EC-03 子计划）。定案 D-1…D-6 写死；判据与反证在本 cycle 落地。
