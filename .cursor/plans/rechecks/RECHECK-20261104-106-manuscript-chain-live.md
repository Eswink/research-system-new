---
id: RECHECK-20261104-106
slug: manuscript-chain-live
title: GOAL-106 复检 —— 十一相链首次真实成立 / GOAL-105 两件机制在真实手稿上取证
status: IN_PROGRESS
result: PENDING
created_at: 2026-11-04
updated_at: 2026-11-05
plan_id: PLAN-20261104-106
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

# RECHECK-20261104-106

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
| EC-06 | 收口资产 + 登记 | PENDING | 验证器与两份断言集**已写成并通过自检**，但**尚未进树**：它们一旦登记，那两条“断言集零判负”的门就会红 —— 红的原因是 EC-02 / EC-03 还没达成。把它们与**真跑读数**放在同一次提交里，门自然转绿；**不放宽判据来换绿** |
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
| F-2 | 判据侧：`live-judge-patches-no-seam` 第一版对 live 判据**报红**，而 live 判据并没有补缝 | 判词逐字：`命中：['deps.tool_providers =', 'replace(deps.runs._deps']` —— 两个「命中」都来自**本断言自己的 docstring**（它逐字讨论了这两条禁令） | **真缺陷（判据侧）** —— 字符串标记式判据被提到它的散文骗过（与 GOAL-105 `W-4` 同族） | 改 **AST** 判定（属性赋值 / `replace(…_deps…)` / 两个接线函数调用），不再文本搜索；按压：真注入一行 `deps.tool_providers = {}` ⇒ 判红并点出行号；复原 ⇒ 绿 | **已修好**（两向按压各留证） |
| F-3 | 判据侧：EC-01 第一版的相归属函数对十个产物**全部**返回 `None`（判据会假红） | 自检输出 `owners: {'research_question': None, …}`；真实制品 id 形状为 `8f62f550-…:submission_package`（**两段**，没有相那一段） | **真缺陷（判据侧）** —— 对 id 形状的错误假设 | 改读产品自己的相级进度面 `RunDetailDto.phases`（`artifact_ids` 由产品给出），十一相逐相断言 | **已修好** |
| F-4 | 判据侧：EC-03 第一版的应答重叠拿整份 `review_decision` 当词库（判据过宽） | 自检 `action overlap: (2, 2)` 在两种口径下都成立，无法区分；代码审读显示第一版 `point_words = content_words(review_decision)` | **真缺陷（判据侧，方向是过宽而非过严）** —— 与 `validate_action_references` 判据 ③ 的射程不一致（它比的是「它回应的**那条**」） | 按 `### P<n>` 分段，只与**同段**的 `> …` 引用行比；另记一份 `action_overlap_per_point` 读数 | **已修好** |
| F-5 | 记录缺陷：`tests/e2e/direction_to_manuscript_support.py` 的注释写「本协议声明的**十个**相」，而 `PHASES` 元组是 **11 项** | 同文件 `PHASES` 逐项数 = 11（question…report）；注释在元组正上方 | **记录缺陷**（GOAL-102 加 `submission` 时改了元组没改计数） | 改正注释并写明这次修正；**元组本身不动**（相集钉在 `tests/contracts/test_direction_to_manuscript_protocol.py:44-62`） | **已修好** |
| F-6 | 宪章：程序表序 74 第一版把 `轴` 列写成 `报告+实验+复检` | 判据逐字：`轴列取值不在三分轴内：'报告+实验+复检'` | **真缺陷（记录面）** —— `轴` 是**三分轴闭集**（连续性/深度/质量/广度/深度+质量/—），能力域不是轴 | `轴` 改 `深度+质量`（本轮同时推进报告、实验、复检三域）；`能力域` 列留**单个**域 `报告`（判据要求域 ∈ 七域闭集） | **已修好** |

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
