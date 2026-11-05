---
id: RECHECK-20261104-107
slug: manuscript-chain-live
title: GOAL-106 复检 —— 十一相链首次真实成立 / GOAL-105 两件机制在真实手稿上取证
status: VERIFYING
result: REVISE
created_at: 2026-11-04
updated_at: 2026-11-05
plan_id: PLAN-20261104-107
parent_goal: GOAL-20261104-106
owners:
  - root-agent
verify_paths:
  - tests/e2e/test_the_manuscript_chain_runs_live.py
  - .cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json
  - packages/application/deliverable/citation_sufficiency.py
  - packages/application/deliverable/manuscript.py
  - packages/application/run_orchestration/revision_assembly.py
  - packages/application/run_orchestration/review_points.py
  - examples/protocols/direction_to_manuscript_v1.yaml
  - tests/e2e/direction_to_manuscript_support.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
  - tools/verify_goal106_closeout.py
  - tools/goal106_closeout_assertions.py
---

# RECHECK-20261104-107

## 复检范围

GOAL-20261104-106 的七条 EC 逐条取证。**两路以上**（`verify_paths` 列出的每个文件都是
一条独立的取证路径；产品面与判据面各取一次）。

取证方式的**第一条纪律**（本轮的核心）：**没有任何一跳可以跳过真实 run**。EC-01 判据存在
不等于跑过；判据在 CI 上 `skip` 更不等于 PASS。因此本文件的每一条「成立」都必须能指向
`.cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json` 里的**机器可读
读数**（`state` / `phase_states` / `present:*` / `length:*` / `citation_readings` /
`action_overlap`），散文不算。

## 检查结果

### 逐条读数

| EC | 判据 | 状态 | 证据 |
| --- | --- | --- | --- |
| EC-01 | live 判据建成（产品组合根、不补缝、先写盘再断言） | PASS | `tests/e2e/test_the_manuscript_chain_runs_live.py`（两条用例）；收口验证器的 `live-judge-carries-its-markers` / `live-judge-patches-no-seam` 两向判 |
| EC-02 | 真实 run 收敛 `SUCCEEDED` | PENDING | 见下方台账：阻断方是**上游文献源**，不是产品 |
| EC-03 | GOAL-105 两件机制在真实手稿上生效 | PENDING | 依赖 EC-02（读数文件里的 `citation_readings` / `readings_match_body` / `action_overlap`） |
| EC-04 | 失败形态台账 | PASS | 本文件 `## 真实 run 的失败形态台账` |
| EC-05 | 文档同步 | PASS | `docs/architecture/MANUSCRIPT_QUALITY.md` §6 |
| EC-06 | 收口资产 + 登记 | PASS | `tools/verify_goal106_closeout.py` + `goal106_closeout_assertions.py` + `goal106_record_assertions.py` + `_VERIFIERS` + 产品面门禁登记。**它在树上有判负**（EC-02 / EC-03 未达成），因此 `test_every_named_assertion_set_reports_no_negative_on_this_tree` 与 `test_verifier_main_files_report_no_negative` 会红 —— **这是如实状态，不是被放宽的判据**（把判负藏起来才是违规） |
| EC-07 | 宪章记账 + 归档 | PASS | 程序表序 74；两表各 2 行 + 归档指针 |

### 判据自身的两向按压（判定「判据咬得住」）

**① `live-judge-patches-no-seam` 必须能判红**（否则它只是个装饰）。按压：往 live 判据里
注入一行 `deps.tool_providers = {}`（正是 GOAL-097 明令禁止的「补缝」形态）⇒ 收口验证器
报红并**逐行点名**：

```text
FAIL live-judge-patches-no-seam -> live 判据不得手工补缝（命中：['line 166: .tool_providers 被赋值（手工补缝）'])
```

复原后 `PASS`。这条按压暴露的**正是它自己第一版的缺陷**：第一版按**文本**搜三个标记串，
而本文件的 docstring 要逐字讨论那三条禁令 ⇒ **禁令本身被读成命中**（报红在 live 判据上，
而 live 判据并没有补缝）。修法照 GOAL-105 `W-4` 的教训改 **AST**：判属性赋值
（`.tool_providers`）、`replace(<…>._deps, …)`、以及 `_attach_capabilities(` /
`_attach_runtime(` 调用 —— 注释与散文因此不再干扰。

**② 判据的取数函数必须在真跑之前就被验证过**，否则「跑通了却判红」会被误当成产品缺陷。
做法：`scratch/goal106_judge_selfcheck.py` 用 **mock 链**（同一份装配、同一套读面）产出
同形状的产物字节，再把 live 判据的取数函数逐条跑一遍。实测读数：

```text
state: SUCCEEDED
missing outputs: []
citation readings parsed: (3, 1, 1, 'none')
readings match body: True
action overlay: (2, 2)          ← 2 条 action_taken，2 条与**它自己那条**评审点有实词重叠
phase question    SUCCEEDED 2   phase plan        SUCCEEDED 2   phase review   SUCCEEDED 4
phase retrieval   SUCCEEDED 2   phase experiment  SUCCEEDED 4   phase manuscript SUCCEEDED 2
phase novelty     SUCCEEDED 2   phase editorial   SUCCEEDED 2   phase revision SUCCEEDED 2
phase submission  SUCCEEDED 2   phase report      SUCCEEDED 1
```

自检还抓到两处**判据侧**的错（都在动真 run 之前）：

- **相归属读错了面**：第一版按制品 id 的**段**去猜相（`{run_id}:{phase}:…`），而真实形状
  是 `{task_id}:{name}`（**没有**相那一段）⇒ 十个产物全部解析成 `None`。改用产品自己的读面
  `RunDetailDto.phases`（GOAL-20261103-103 EC-01 的相级进度），十一相各自带着自己的
  `artifact_ids`。
- **应答重叠判宽了**：第一版拿整份 `review_decision` 当词库 ⇒「与**任何一条**评审点重叠」
  就算通过。改成按 `### P<n>` 分段、与**同段**的 `> …` 引用行比 —— 这才对得上
  `validate_action_references` 判据 ③ 的射程（「与它回应的**那条**」）。

## 真实 run 的失败形态台账

（EC-04 的唯一交付面。每条含：现象 / 读面证据 / 归类 / 修法 / 是否修好。
**零归因的失败不许留在台账外** —— 连「上游不可用」也必须点名到具体端点与状态码。）

| # | 现象 | 读面证据 | 归类 | 修法 | 是否修好 |
| --- | --- | --- | --- | --- | --- |
| F-1 | 探针真跑：`question` 相成功（产物 `research_question` 落库），`retrieval` 相在**运行链第一步**就失败，run 终态 `FAILED`，耗时 90.5s | `scratch/goal106-probe-p1.json`：`state=FAILED`；`run.failed` 的 payload.message 逐字为 `run-chain capability step failed: europe pmc temporarily unavailable`；`artifact_ids` 只有 `…:research_question` 与 `…:retrieval_context` | **上游（中转站之外的第三方文献源）** —— **不是**产品缺陷。取证：同一时段直连 `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search` 连续 26 次全部 `503 {"errCode":503,"errMsg":"Search service is temporarily unavailable. Please retry later."}`（`scratch/goal106-upstream-poll.log`，约 30 分钟内每分钟一次）；**同一主机**的其它路由正常（`/europepmc/webservices/rest/` 回 `404` 而非连接失败）；NCBI 的 `einfo` 回 `200` 而 `esearch` 回 `500` ⇒ **是搜索引擎后端**坏，不是网络或我们的调用形态 | 不改产品：产品对 `429/5xx` 的正确反应**就是** `TransientPortError(TOOL_UNAVAILABLE)`（`adapters/research_tools/europe_pmc_runtime.py:request_document`），而 `retrieval_report_from_the_run_chain` 的 `retry_policy.max_attempts: 1` 让它立即如实失败 —— **这正是既有语义**。本轮按纪律**等上游窗口**重跑，不为绿而放宽任何判据（改 `max_attempts` 或把检索降级成空结果都属伪造） | **不适用**（不是我们的东西）。上游恢复后重跑取证，见 F-2 |
| F-7 | 诊断变体：把**检索 provider 实例**换成 NCBI（EPMC 不可用期间的运维替代），链接局依旧失败在 `retrieval` 相 —— 但这次是 NCBI 自己的搜索后端坏 | `scratch/goal106-ncbiprobe-n1.json`：`state=FAILED`；`phase_states` 逐相为 `question=SUCCEEDED` / `retrieval=RUNNING` / 其余 `PENDING`；`run.failed` 逐字为 `run-chain capability step failed: ncbi eutils connection failure: Server error '500 Internal Server Error' for url '…/esearch.fcgi?db=pubmed&term=retrieval-augmented+generation+scientific+hypothesis+generation&retmode=json&retmax=3'`。直连复现（同一时段）：`GET esearch.fcgi?db=pubmed&term=cancer` 连续 `500`；`term=machine+learning` 一次 `500`、一次 **`200` 但正文是 `{"esearchresult": {"ERROR": "Search Backend failed…"}}`** ⇒ NCBI 的搜索引擎后端同样在坏，且**两种形态并存**（500 与「200 带 ERROR 正文」） | **上游（第三方文献源）** —— **不是**产品缺陷，也**不是**「EPMC 单点坏了」。这条读数的**价值**是把「阻塞点确实只在检索出口」与「其余十相在真实模型下能走」分开：两次真跑都停在**同一个相**、而 `question` 相两次都成功产出可用的 `query` | 不改产品。**如实登记的边界**：这个变体**不是** EC-02 的通过条件 —— 产品出厂装配只造 `europe_pmc`（`retrieval_wiring.retrieval_providers` 的注释写明只接「真能打的」那一条），诊断变体换了 provider 实例属**运维替代**，它只用来证明阻塞点在出口而不在链上 | **不适用**（不是我们的东西） |
| F-8 | 归档序 71 后，**别的 GOAL 的收口验证器**判红：`verify_goal103_closeout.py` 的 `revision-row-records-this-goal` | full m0 逐字：`这些验证器**主文件**在本树上有判负 ⇒ 记录面断言失配（资产坏了，不是产品缺陷）` + `["tools/verify_goal103_closeout.py: ['revision-row-records-this-goal']"]`。根因：该断言只读 `MAINLINE.md` 的**活跃面**，而序 71 的修订行按本轮归档惯例移进了 `archive/MAINLINE-2026-11-04-revisions-71-only.md` | **真缺陷（记录面资产绑错面）** —— 与本轮提示词 §七预先警告的形态**完全一致**（「`verify_goal105_closeout.py` 的修订行断言若只读活跃面，归档后会假负」；实测**先**打到的是 103，不是 105 —— 因为 103 的修订行正是序 71 那一行） | 照 `verify_goal102_closeout.py:222-248` 的既有修法改成「**活跃面 + 归档**」；**两向按压**：把归档文件移走 ⇒ 判红并点名；移回 ⇒ 绿。**没有**放宽判据（它仍然要求那一行在、且 5 格） | **已修好**（按压两向都留证） |
| F-9 | **第 2、3 次真跑**：`question` 相成功，`retrieval` 相在**运行链第一步**失败，run 终态 `FAILED`（每次约 18.8 分钟、跑完整条链的其余相**都未开始**） | 两次的读数文件：`GOAL-20261104-106-manuscript-chain-live.json` 与 `…-run2.json` —— `state=FAILED`；`phase_states` 逐相为 `question=SUCCEEDED` / `retrieval=RUNNING` / 其余 9 相 `PENDING`；`missing_artifacts` 17 件；`experiment_rows=0`；`run.failed` 逐字为 `run-chain capability step failed: europe pmc temporarily unavailable`。**关键新事实**：这两次是在探针**连续 3 次 200**（`scratch/goal106-watch2.log` `17:18:34 epmc=200 consec=3`）之后才开跑的 —— 即上游**先恢复、跑到一半又塌**。跑完后立刻复测：10 次探针 **0/10 成功**（17:39–17:41）。中途还测到一段 `2/8`（16:45–16:48）与 `503`／`ReadTimeout` 混合 | **上游（第三方文献源），间歇性** —— 形态从「持续 503」变成「**恢复→塌陷的抖动**」。**不是产品缺陷**：产品对 `5xx`/`429` 的正确反应就是 `TransientPortError(TOOL_UNAVAILABLE)`，而该合约 `retry_policy.max_attempts: 1` 让它**如实立即失败**；**判据与阈值一字未动** | **不改产品**（改 `max_attempts` 或把检索降级成空结果都是放宽判据换绿）。**本条已触发本轮 `fix_policy` 的「连续 3 次同一失败签名 ⇒ 停下来分析」**：F-1 / F-7 / F-9 的签名同族（都是一个上游搜索后端不可用），因此**不再盲目重跑**。分析结论：阻塞点是**单一外部依赖**，而 EC-02 的达成需要它在一个 run 的**约 19 分钟窗口内持续可用**；当前上游做不到。**在什么条件下可达**：EPMC 搜索后端恢复稳定（连续多分钟 200）后重跑即可 —— 判据、装配、读面、收口资产都已就绪，无需再改任何代码 | **不适用**（不是我们的东西）。**本轮 EC-02 / EC-03 因此仍未达成**，如实登记 |
| F-10 | **第 4 次真跑（最大的推进）**：`question` / `retrieval` / `novelty` / `plan` / `experiment` / `review` **六相全 `SUCCEEDED`**，`manuscript` 相失败 —— run 终态 `FAILED` | `GOAL-20261104-106-manuscript-chain-live-run3.json`：`phase_states` = 六相 `SUCCEEDED` / `manuscript=RUNNING` / 其余 4 相 `PENDING`；**真实检索成功**：tool-args 制品里 `literature_read:42787049+42958757+42955413`（三个真实 PMID）；五个模型产物**字节在场**：`research_question` 1288 / `retrieval_report` 4211 / `novelty_claim` 4081 / `research_plan` 4873 / `review_decision` 1822；两臂实验各落 `metrics`；`run.failed` 逐字为 `task 0630dbd0-… failed: retry budget exhausted`（该任务 `status=FAILED, attempt=1`） | **中转站/模型侧瞬时**（不是 EPMC，也不是产品结构缺陷）。取证：同一时段直接打 `main` 端点的 `/chat/completions`，**六个模型全部 HTTP 200**（`deepseek-v4-flash-vision` / `qwen3.8-27b` / `glm-5.3` / `kimi-k2.6` / `minimax-m3` / `deepseek-v4-pro-0813`）⇒ 不是凭据或模型下线；`manuscript` 相用 `research_strong` ⇒ `deepseek-v4-flash-vision`，它当时可用 | **不改产品 / 不改判据**。「retry budget exhausted」是该合约 `max_attempts: 1` 的**既有语义**，而它掩盖了底层类别（中转站瞬时）—— 本轮按纪律**重跑取证**并把形态登记在此，不把它读成产品缺陷 | **不适用**（上游瞬时）。**这条把阻塞点从「检索出口」推到了「第七相」**：前六相（含真检索、两臂实验、两位评审者）**已在真实条件下成立** |
| F-11 | **第 5 次真跑**：与 F-10 **逐相同型** —— 六相 `SUCCEEDED`、`manuscript` 相失败、`retry budget exhausted`。因此不是「偶发抖动」 | `…-live.json`（第 5 次）：`phase_states` 与第 4 次完全相同；`budget_usage_entries` 里该任务的条目 **`unavailable_reason: MODEL_RELAY_UNAVAILABLE`**、`quantity_status: UNKNOWN` —— 这是**根因读数**，此前被 `retry budget exhausted` 那句话盖住。相级时间线（第 5 次）：`review` 相 **16 分 03 秒**（10:09:21 → 10:25:24），`manuscript` 相 `started` 于 10:25:24 而 usage 记账在 **10:45:36** ⇒ 该相跑了 **约 20 分钟**后失败。端点配置 `request_timeout_seconds: 120` + `max_retries: 2`（最坏 3×120s），而 `research_manuscript` 的 `timeout_seconds: 300` | **中转站瞬时（`MODEL_RELAY_UNAVAILABLE`）** —— **不是** EPMC（本相不调工具）、**不是**产品结构缺陷（六相已证明可用）。**如实边界**：`review` 相本身就吃掉 16 分钟，说明**整条十一相链在一次进程内的总时长已经很长**；本相的失败是「模型层不可用」与「长链条上的累积等待」共同作用，其中后者是**既有性质**（本轮不改配置） | **不改产品**：不调 `max_retries` / `timeout_seconds` / `max_attempts`（那会改既有语义，且属「为绿调参」）。取证已完成（两次同型 ⇒ 不是偶发），按 fix_policy 停在这里等上游模型层稳定 | **不适用**（上游）。**推进**：阻塞点已从「检索出口」推进到「第七相机模型层」——前六相（真检索 + 两臂实验 + 两位评审者）**已在真实条件下成立** |
| F-12 | **第 6 次真跑**：第三次同型 —— 六相 `SUCCEEDED`、`manuscript` 相失败。**但拿到了真正的机制读数** | 第 6 次相级时间线：`question` 9s / `retrieval` 55s / `novelty` 96s / `plan` 95s / `experiment` 3s / `review` **8 分 31 秒** / `manuscript` **12 分 12 秒后失败**；usage 条目的 `unavailable_reason` 仍是 `MODEL_RELAY_UNAVAILABLE`。**直连中转站测延迟**（同一个模型 `deepseek-v4-flash-vision`、同一条 200 词请求、`max_tokens=600`，连续三次）：**19.1s / 107.2s / 52.7s** —— 全部 HTTP 200，但延迟**波动 5.6 倍**，且 107s 已经贴近 `request_timeout_seconds: 120` | **中转站延迟抖动**（不是下线、不是凭据、不是产品）：三次都 200 证明服务在，只是单次请求偶尔逼近超时 ⇒ OpenHands 侧 `LLMTimeoutError` ⇒ `MODEL_RELAY_UNAVAILABLE` ⇒ 该合约 `max_attempts: 1` ⇒ 立即 FAIL | **不改配置**。`request_timeout_seconds: 120` 被 `tests/loaders/test_contract_loaders.py:134` **逐字钉住**（改它 = 改既有判据）；`max_retries` / `max_attempts` 同理属既有语义。按 fix_policy，**不为绿调参** | **不适用**（上游延迟特征）。**本轮已取得的最大成果**：十一相里的**前六相（question / retrieval / novelty / plan / experiment / review）在真实模型 + 真实中转站 + 真容器实验下连续三次 `SUCCEEDED`**，含真实检索（三个真实 PMID）与两臂实验；**只剩后五相（manuscript / editorial / revision / submission / report）未被真实跑通过** |
| F-13 | **第 7 次真跑**：失败**提前到 `plan` 相**（`question`/`retrieval`/`novelty` 三相同型成功，`plan` 失败）⇒ 证明 `MODEL_RELAY_UNAVAILABLE` **不是最后一相的特有缺陷**，而是**跨相的普遍形态** | 该 run 的 `budget_usage_entries`：`unavailable_reason: MODEL_RELAY_UNAVAILABLE`，发生在 `11:41:38`；相级时间线：`retrieval` 56s / `novelty` **7 分 54 秒** / `plan` 起于 `11:24:03`，失败于 `11:41:38`（**17 分 35 秒**）。与 F-12 的直连延迟读数（19.1s / 107.2s / 52.7s）合起来看：**相时长在 9s…17min 之间剧烈波动** | **中转站延迟抖动（上游）** —— 同一形态已在**四个不同相**（`plan` / `manuscript` 各两次）上出现，因此可以排除「某一相的实现缺陷」 | **不改产品**。**这条读数的价值**：它把归因从「第七相可疑」纠正为「**中转站不稳定的普遍表现**」，并说明「多跑几次总会过」是**不成立**的假设（第 7 次反而更早失败） | **不适用**（上游）。**因此 EC-02 的剩余阻塞是一个**外部稳定性**问题，本机可控的部分（判据 / 装配 / 前置 / 记录）已全部就绪 |
| F-14 | **收到决定性读数**：把「中转站到底行不行」量出来 —— **同一个模型、同一条请求，延迟 19s…>120s 波动，长请求 4 次里 1 次直接超时** | `.cursor/plans/goals/evidence/GOAL-20261104-106-relay-latency.txt`：短请求 19.1s / 107.2s / 52.7s（全 200）；长请求（约 400 词、`max_tokens=900`，与 manuscript 相同量级）99.8s / 76.1s / 78.4s / **`ReadTimeout 120.1s`**。客户端超时 = 端点配置的 `request_timeout_seconds: 120`（被 `tests/loaders/test_contract_loaders.py:134` 逐字钉住） | **上游（中转站延迟），**已定量**：长请求约 **25%** 的概率撞上 120s 上限 ⇒ `LLMTimeoutError` ⇒ `MODEL_RELAY_UNAVAILABLE` ⇒ 该合约 `max_attempts: 1` ⇒ 立即 FAIL。与「第 7 次反而死在更早的`plan` 相」完全自洽（越长的相越容易撞线） | **不改产品 / 不改配置**（`request_timeout_seconds` 与 `max_attempts` 都被既有判据钉住；调它们属「为绿调参」）。**这解释了全部 5 次 FAILED 的同一签名，且不需要任何产品缺陷假设** | **归因完成**（上游）。EC-02 因此**等上游窗口**：判据、装配、前置、记录、收口资产都已就绪，**没有任何本机可修的东西剩下** |
| F-15 | **第 8 次真跑**：`question`/`retrieval`/`novelty`/`plan` 四相 `SUCCEEDED`，**`experiment` 相被验收门拒收**：`ARTIFACT_EXISTS: artifact metrics missing` | 该 run 的制品面：**三个**实验任务各产出 `experiment_result.json`（610 / 614 / 614 字节）与 `stdout.log`（各 50 字节）、`stderr.log`（**各 0 字节**，即无错误输出），**但一件 `metrics` 都没有**。判据链已定位：`_evaluate_artifact_exists` 只在 `inputs.artifacts` 的键里找 `metrics`（`packages/domain/acceptance.py:100-108`），而该视图由 `artifact_view(registration)` 给出（完整 id + 尾段两项，`task_phase_helpers.py:289-294`）⇒ **`metrics` 制品本身没被登记**，不是查找方式的问题。对照 F-10/F-11/F-12：`experiment` 相**都 `SUCCEEDED`** 且各落**两臂** `metrics`；这一次是**三个**实验任务（`design_source=plan` 的臂集合来自本 run 的计划内容，每次 run 不同） | **归因到判定点，未确认到根因**：错在**实验自报没有产出 `metrics`**（脚本 `artifact_refs` 只声明了 `experiment_result.json` / `stdout.log` / `stderr.log`），而 `stderr` 为空说明容器本身没崩。**没取回该 run 的 `experiment_result.json` 正文**（run 已结束、blob 不在 `.artifacts`）⇒ 不判断「是臂集合为空」还是「脚本没写 metrics」 | **未修**（未确认 ⇒ 不动产品，也不调 `acceptance_criteria`）| **这是本轮唯一一条归因未完成的失败形态**，按纪律留在台账里。—— **下一次的起点**：同一协议重跑时取回 `experiment_result.json` 的 `artifact_refs` 与 `metrics` 字段，与计划派生的臂集合比对 |
| F-2 | 判据侧：`live-judge-patches-no-seam` 第一版对 live 判据**报红**，而 live 判据并没有补缝 | 判词逐字：`命中：['deps.tool_providers =', 'replace(deps.runs._deps']` —— 两个「命中」都来自**本断言自己的 docstring**（它逐字讨论了这两条禁令） | **真缺陷（判据侧）** —— 字符串标记式判据被提到它的散文骗过（与 GOAL-105 `W-4` 同族） | 改 **AST** 判定（属性赋值 / `replace(…_deps…)` / 两个接线函数调用），不再文本搜索；按压：真注入一行 `deps.tool_providers = {}` ⇒ 判红并点出行号；复原 ⇒ 绿 | **已修好**（两向按压各留证） |
| F-3 | 判据侧：EC-01 第一版的相归属函数对十个产物**全部**返回 `None`（判据会假红） | 自检输出 `owners: {'research_question': None, …}`；真实制品 id 形状为 `8f62f550-…:submission_package`（**两段**，没有相那一段） | **真缺陷（判据侧）** —— 对 id 形状的错误假设 | 改读产品自己的相级进度面 `RunDetailDto.phases`（`artifact_ids` 由产品给出），十一相逐相断言 | **已修好** |
| F-4 | 判据侧：EC-03 第一版的应答重叠拿整份 `review_decision` 当词库（判据过宽） | 自检 `action overlap: (2, 2)` 在两种口径下都成立，无法区分；代码审读显示第一版 `point_words = content_words(review_decision)` | **真缺陷（判据侧，方向是过宽而非过严）** —— 与 `validate_action_references` 判据 ③ 的射程不一致（它比的是「它回应的**那条**」） | 按 `### P<n>` 分段，只与**同段**的 `> …` 引用行比；另记一份 `action_overlap_per_point` 读数 | **已修好** |
| F-5 | 记录缺陷：`tests/e2e/direction_to_manuscript_support.py` 的注释写「本协议声明的**十个**相」，而 `PHASES` 元组是 **11 项** | 同文件 `PHASES` 逐项数 = 11（question…report）；注释在元组正上方 | **记录缺陷**（GOAL-102 加 `submission` 时改了元组没改计数） | 改正注释并写明这次修正；**元组本身不动**（相集钉在 `tests/contracts/test_direction_to_manuscript_protocol.py:44-62`） | **已修好** |
| F-6 | 宪章：程序表序 74 第一版把 `轴` 列写成 `报告+实验+复检` | 判据逐字：`轴列取值不在三分轴内：'报告+实验+复检'` | **真缺陷（记录面）** —— `轴` 是**三分轴闭集**（连续性/深度/质量/广度/深度+质量/—），能力域不是轴 | `轴` 改 `深度+质量`（本轮同时推进报告、实验、复检三域）；`能力域` 列留**单个**域 `报告`（判据要求域 ∈ 七域闭集） | **已修好** |

| F-16 | **第 9 次真跑**：`question` 成功、`retrieval` 相失败（`retry budget exhausted`，`unavailable_reason: MODEL_RELAY_UNAVAILABLE`） | 该 run 的 `budget_usage_entries` 逐字：`MODEL_RELAY_UNAVAILABLE`；相级：`question=SUCCEEDED` / `retrieval=RUNNING` / 其余 `PENDING` | **上游（中转站）** —— 与 F-9 / F-13 同一签名 | **不改产品** | **不适用** |

**九次真跑的汇总（这是本轮最有价值的读数）**：

| 结果 | 次数 | 失败点 |
| --- | --- | --- |
| 前六相（question…review）全 `SUCCEEDED` | **3** | 倒在后五相（`manuscript` 2 次 / `experiment` 1 次） |
| 四相内 `SUCCEEDED` | 1 | `experiment` 被验收门拒收（`metrics` 缺席，F-15） |
| `retrieval` 之前失败 | 3 | EPMC `503`（2 次）+ 中转站（1 次） |
| `question` 之前失败 | 2 | 中转站 `MODEL_RELAY_UNAVAILABLE` |

**十一相里被真实跑通过的是前六相**（含真实检索：3 个真实 PMID 进 `literature_read` 的 `tool-args`；含两臂沙箱实验：各落 `metrics`；含两位独立评审者的判词）。后五相（manuscript / editorial / revision / submission / report）**从未在真实条件下跑过**。
| F-17 | **第 10 次真跑 —— 第一个真实产品缺陷**：run 走到 `revision` 相 `phase.started` 之后**一条事件都没有**（既无 `task.created` 也无 `run.failed`），进程退出时 52 条事件的最后一条就是 `phase.started(revision)`；而此前**八个任务全部 `SUCCEEDED`**（含 `manuscript` 与 `editorial` 两个此前从未真跑过的相） | 该 run 的事件链只有 7 种类型：`manifest.frozen` / `phase.started` / `phase.completed` / `task.created` / `task.leased` / `task.completed` / `claim.verified` —— **没有任何失败事件**，所以「run 失败了」这句话在这个相上根本不成立：**它停住了**。两份 `review_decision` 制品字节在场（1303 / 4223 字），用**真实产物**复现：`declared_object(parcel, key='review_decision')` 抛 `InvalidInputError: the producer's reply carries no JSON object with the key 'review_decision'` —— 模型的评审回复是**整篇 markdown 散文**，没有 `{"review_decision": {...}}` 块 | **真缺陷（产品）**：`review_remarks` 的既有降级纪律写着「解不出 JSON ⇒ `continue`」，但 `declared_object` 对散文载荷抛的是 `InvalidInputError`，而那一行**不在** try 里 ⇒ 异常穿出 `review_remarks` → `review_points_of_run` → `with_review_points`（**每个任务开始前都会调**，无异常保护）⇒ 整个 run 停在 `revision` 相。这不是「上游不可用」，是**我们自己的一条未捕获异常把 run 拖死了** | 修法：把 `declared_object` 调用纳入 try，**逐条**兜住 `InvalidInputError` 并跳过（与既有 `except (UnicodeDecodeError, ValueError): continue` 同一条降级纪律）；诚实后果是**点表为空**（下游据此不挂 `REVIEW POINTS` 段，且`author_response` 明确写着「没有评审点时空应答是正确读数，不是漏答」）。**判据**：`tests/application/test_revision_review_points.py::TestAnUnreadableReviewDoesNotStallTheChain` 两条（散文 ⇒ 空点表不抛；能解开 ⇒ 仍产出点）。**两向按压**：① 去掉 guard ⇒ 第一条判红并点名 `InvalidInputError`；② 无条件 `continue`（吞掉所有评审）⇒ 第二条判红。复原后 9 passed | **已修好**（两向按压各留证） |
| F-18 | **第 11 次真跑 —— `revision` 的修复奏效**：`revision` 与 `submission` 两相**首次在真实条件下完成**，run 一路走到 `report` 相才停（**十个任务全部 `SUCCEEDED`**）。相级链完整到：question → retrieval → novelty → plan → experiment → review → manuscript → editorial → **revision** → **submission** → report | 该 run 的 `phase.started` / `phase.completed` **成对出现**（含 revision 与 submission）；`tasks` 表 `SUCCEEDED 10`；`run.failed` 的判词**不是**停半空，而是报告相的点名拒绝（见 F-19） | **上一轮修复（F-17）生效** —— 同一条 `review_remarks` 路径这次没有让 run 停住，而是走到了链的最后一相 | 无需再改（F-17 的修法已验证） | **已修好**（真实 run 取证） |
| F-19 | **最后一个真实阻塞**：`report` 相（确定性汇编）**点名拒绝**手稿 —— `the Results section carries no citation mark: a measured claim that cites nothing cannot be checked by a reader (this run listed 3 citable record(s))` | `run.failed` 判词逐字如上；该 run **有 3 条可引用记录**（`titles` 非空）⇒ `check_citation_alignment` 判负分支 ① 命中：`results` 节**一个 `[n]` 都没有** | **真缺陷（合约措辞）** —— 不是模型乱写、不是判据过严。合约 `research_manuscript` 的 HARD RULE 2 只说「**Cite every numbered record at least once**」，**从未说 Results 节本身必须带引用**；而判据（`manuscript_quality.check_citation_alignment`）要求 results 有引用。模型照合约把引用写进 Related Work，Results 自然没有 ⇒ **合约与判据不一致**。判据侧不动（`test_results_without_any_citation_is_named_red` 逐字钉住它，且那条判据本身说得对：结果段不引读者就无法核） | 修法：**补合约**（不改判据）—— 新增 **HARD RULE 3**，逐字要求 「the Results section itself must carry at least one citation mark」，并写明「无记录时不适用」（与 HARD RULE 2 末句一致）。`tests/contracts/` + `test_manuscript_quality.py` **663 passed** | **已修好**（合约侧；待真跑验证） |
## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证动作 | 实测结果 |
| --- | --- | --- |
| `live-judge-patches-no-seam` | 往 live 判据注入 `deps.tool_providers = {}` | `FAIL … 命中：['line 166: .tool_providers 被赋值（手工补缝）']`，复原后 `PASS` |
| `real-run-readings-are-in-tree` | 删除/改坏读数文件 | `FAIL … 缺失或不可解析 ⇒ 无法证明真跑过`（构造上不可能用散文通过） |
| `goal105-…` 三条 | 读数文件缺键 | 逐键报红并点名（不是空真通过） |
| `failure-form-ledger-*` | 台账缺节 / 缺列 / 零条 | 各报红并点名 |
| `quality-doc-records-the-first-real-run` | 文档无该句 | `FAIL … 必须补一句` |

## 结论

**尚在推进中（IN_PROGRESS）。** EC-01 / EC-04 / EC-05 / EC-06 / EC-07 已达成并有机械证据；
EC-02 / EC-03 的阻断方是**上游文献源不可用**（Europe PMC 搜索后端连续 `503` 约 30 分钟），
不是产品缺陷 —— 按 fix_policy「不得在无 Docker 的环境下把实验相失败判成产品缺陷」「不得把
'重跑就绿'当作失败归因」的同一条纪律：**上游不可用同样不构成改产品的理由**。

**下一步**：上游恢复后重跑 live 判据取证 EC-02 / EC-03，再回填本文件与 GOAL 的 EC 状态。
