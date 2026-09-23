---
id: PLAN-20260923-144
slug: experiment-evidence-chain-traceability
title: 实验产出的证据链可追溯：产物/来源进 canonical + 内容 digest 可重算 + 镜像摘要可独立复核（GOAL-012 EC-03）
status: DONE
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-145-experiment-evidence-chain-traceability.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-111-experiment-evidence-traceability-judge-shape.md
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
| AC-1 | **产物进 canonical 且两读面同源** | 同文件 ⇒ **2 passed**；四件产物在两读面都可见（判据用**子集**方向：run 级面还含别的阶段的产物与声明输入） | **达成** |
| AC-2 | **内容 digest 可重算** | 同文件：**证据条目**与**来源记录**两条记录的 digest 都从内容字节重算（实测 6 件制品逐件通过） | **达成** |
| AC-3 | **来源可独立复核** | 同文件：`image_digest` == 独立 `docker image inspect` 的 Id（CLI 不可用时如实跳过该断言）；`environment_digest` 非空；两次执行 `semantic_metrics_digest` 与指标相同 | **达成** |
| AC-4 | **反证（成对）**：去掉声明产物 ⇒ 判据红且**点名** | 同文件第 2 条：run `FAILED`（判词含 `acceptance gate` 与 `analysis_report`）、读面无 `analysis_report`、`report.txt` / `experiment_result.json` 仍在 | **达成** |
| AC-5 | **不得用模型自述冒充**（D-4） | 同文件：`extracted_by == experiment:<run id>` + `source_origin` 前缀 + 信任标签 `GENERATED`（实验路径），三者逐条断言 | **达成** |
| AC-6 | **按压**：去掉「登记产物」那一步 ⇒ 判据红 ⇒ 复原绿 | **四处按压**全红（`scratch/goal012-c3-press{1,2a,2b,3}.txt`），产品代码按 `git diff` 逐字复原；按压另暴露判据盲点（只看证据 digest、没看来源记录）⇒ 判据**加强**为两条记录各算一遍 | **达成** |
| AC-7 | **门与治理**：m0 23/23 + 定向套件 + `validate.py` 绿 + `mypy`/`ruff` 干净 | 第 2 轮 m0 **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c3-m0-rerun.log`；`python/tests` **4411 passed / 19 skipped / 0 failed**）；首轮两红（未用 import / 50 行函数门）当轮修掉；`tests/e2e` 118 passed / 10 skipped；`mypy` 996 files 干净 | **达成** |
| AC-8 | **零出网 + 凭据纪律** | 逐条 `egress guard: judged N; blocked 0`；本 cycle **未做任何 live 调用、未读凭据值** | **达成** |
| AC-9 | **真实 run 侧**（EC-02 样张） | 独立脚本 C 组 5 条全绿：四件产物各有证据、`experiment_run_id` 与 `run_id` 一致、样张不含凭据值 | **达成** |

## 实施清单

- [x] **WP1** 判据（离线 + 容器）：`tests/e2e/test_ec03_experiment_evidence_chain.py`
  （主干 4 组断言 + 成对反证 1 条）。提交 `6ccdf46`；**2 passed**。
- [x] **WP2** 四处按压全红并复原（`scratch/goal012-c3-press{1,2a,2b,3}.txt`）；按压暴露的判据盲点已**加强判据**修掉。
- [x] **WP3** 独立复检脚本 `scratch/verify_goal012_c3.py`（当前树 **24/24**；基线树 `31dfbd4` **6 红**＝判据文件不存在；产品件两树同指纹）。
- [x] **WP4** 门与收口：m0 **23/23** + 定向套件 + `validate.py`；`RECHECK-20260923-145`（PASS）+ GOAL 回写。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 产物读面与内容读面已存在（无需改产品） | `services/api/routers/experiments.py:98`、`artifacts.py:118`、`artifacts.py:165` |
| E-2 | 产品缝已把实验产物登记进 canonical | `services/api/experiment_support.py`（`register_experiment_evidence` 经 `execute_experiment_task`）+ EC-02 的样张（4 件产物 + 6 条证据） |
| E-3 | 镜像摘要是 daemon 的镜像 Id（可独立复核） | `adapters/execution/docker_backend.py:_resolve_image_digest`（`inspect_image(...)["Id"]`） |
| E-4 | 语义摘要是 cross-rerun 稳定的 canonical 事实 | `packages/application/experiments/metric_extraction.py:90-92`（`semantic_metrics_digest`：非观测性子集的 canonical digest） |
| E-5 | 判据结果 | `pytest tests/e2e/test_ec03_experiment_evidence_chain.py -q` ⇒ **2 passed**；四处按压 `1 failed` ×4 |
| E-6 | 两棵树成对 | 当前树 `checked=24 failures=0`；基线树 `checked=24 failures=6`（B 组）；产品件指纹两树一致 |

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
- 2026-09-23（WP1–WP4，提交 `6ccdf46`）：判据 + 成对反证 + 四处按压落地；两处**判据自身**的问题
  在 cycle 内修掉并如实记录 —— ①「两面相等」的断言错（实测两面是子集关系）⇒ 改子集方向；
  ②「只看证据 digest、不看来源记录」的盲点由按压暴露 ⇒ 判据加强为两条记录各算一遍。
  产品代码**一字未改**（独立脚本两树产品件指纹一致）。复检 `RECHECK-20260923-145` = **PASS**。
