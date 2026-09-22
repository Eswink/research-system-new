---
id: GOAL-20260922-011
slug: real-research-capability
title: 真实研究能力落地：检索进协议、证据由系统取得（把「真实 run 成功」升级为「真实 run 真的做过研究」）
status: ACTIVE
created_at: 2026-09-22
updated_at: 2026-09-22
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-22 用户会话指令（goal 模式）：**建档 GOAL-20260922-011 并授权本驱动自动化循环推进、
    无需逐轮确认**。authorization 原文要点如下：
    (1) **live-gated 真实调用授权（承 GOAL-009/010，本 GOAL 继续有效）**：用户授权在真实端点上做
    **live-gated 真实调用**——端点与模型已登记（`ANTHROPIC` 协议 + `agnes-2.5-flash`，含
    **512000 / MAX** 声明）；**次数取最小必要**，不做压测、批量或重复重跑。凭据仅在本机
    **gitignored `.env`**（键名 `LLM_MAIN_KEY`），其值为**可弃用的免费额度**、
    用户已明示**不要求保密**（此声明只降低追责口径，**不放松下面的凭据纪律**）。
    (2) **新授权：允许真实检索出网**——以 **NCBI E-utilities（`eutils.ncbi.nlm.nih.gov`）**作为
    真实检索来源。出网**只允许在该 provider 的 `network_domains` 声明范围内**
    （`examples/config/tool_providers.yaml` 的 `ncbi_eutils` 项），**次数取最小必要**；
    **无 key 时按适配器既有节流（3 req/s）运行**，`NCBI_API_KEY` **可选、不强制**
    （适配器按 `min_request_interval_seconds` 自行强制间隔）。
    (3) **新授权：授权删除本机 gitignored 的 `secrets/llm_key.txt`**——它是**未被跟踪**的第二份
    凭据副本（GOAL-009/010 登记的残余、泄露面）。**授权范围严格限于该一个文件**：
    只删 `secrets/llm_key.txt`，**不动** `secrets/` 目录本身，**不动**任何其他文件。
    (4) **新授权：EC-04 的用户视角端到端验收**允许在**本机**启动**真实控制面 / 前端**并操作 UI
    （**仅本机、仅该端点**）；**不上传任何截图到外部服务**；若截图/录屏，**落 `scratch/` 且不进仓库**。
    (5) **凭据纪律（不得放松）**：值**不得写入任何 tracked 文件、DB、记录（PLAN/RECHECK/MEM/GOAL）、
    日志或命令回显**（含片段）。**不得把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`**——它
    **只作为单条命令的内联前缀**；否则默认门会切到真实 runtime、破坏 CI 语义。
    (6) **默认姿态不变**：默认 runtime 保持 **Fake**、默认 CI **离线**（AGENTS.md §11）；
    live 分支必须**显式** `RESEARCHOS_AGENT_RUNTIME=openhands` 才开门（fail-closed，AGENTS.md §9）。
    **不得为了跑检索而放宽出站判据**（`tests/egress_guard.py` 是结构判据：默认门出现非环回目的
    即判红）；**检索类用例必须挂 `requires_live_llm`（或同一放行面）才可出网**。
    (7) **push-to-main-for-CI 授权**：只推 `main`、**不 force**、**不重写历史**、**不推旁支**触发 CI；
    push 前 `git pull --ff-only origin main`。循环预算与纪律以本文件 frontmatter 为准
    （客户端自带的迭代/重试/超时上限**一律让位于**此）。
    GOAL-001…010 全部**只读**（003 BLOCKED，其余 ACHIEVED），本 GOAL 不修改它们；
    如需指名只允许按**只追加**补一行事实更正。
objective: >
    把「真实 run 能走到 `SUCCEEDED`」（GOAL-010 达成的终点）升级为「**真实 run 真的做过研究**」：
    让**已声明**的 `ncbi_eutils` 检索能力**真正接进协议与执行链**（一次真实 run 的
    discovery/analysis 阶段**实际调用检索**，留下的工具观测可读），并把证据链从
    「**声明输入**」（`USER_PROVIDED`）升级为「**系统取得**」（`RETRIEVED`）——
    **不得**用模型自述充当外部来源。同时把「默认 CI 离线」这条声明**要么成立、要么如实降级措辞**
    （残余 `R-6`），并做一次**用户视角**的端到端验收。反证必须成对成立：
    **把该能力从协议移除 ⇒ 该阶段无工具观测 / 覆盖率判拒**。
    **不引入新依赖、不改上游 pin、不自行修改 Accepted ADR / 核心安全策略 / Canonical State 边界、
    不把真实 runtime 设为默认——触及即 BLOCKED。**
exit_criteria:
  - id: EC-01
    criterion: >-
      **真实检索进协议（主干）**：把已声明的 `ncbi_eutils` provider 的 `literature.search` /
      `literature.read` 能力**声明进一份真实协议**——二选一并在记录里**写明选了哪条**：
      (a) 在 `real_research_task_v1` 上**加阶段**，或 (b) **新建**一份真实协议。
      使**一次真实 run** 的 discovery/analysis 阶段**实际调用检索**。
      **判据（三件同时成立）**：① run 到**终态**；② 该阶段的**工具观测**
      （`ToolCallRecord` / 工具结果）**存在且可读**；③ 检索返回的**真实标识**
      （PMID / DOI / 标题）**出现在证据链里**。
      **反证（先绿后红成对）**：把该能力**从协议移除** ⇒ 该阶段**无工具观测**。
      **禁止**用 Fake 工具结果 / 桩响应充当证据；**禁止**用模型自述里的 PMID 充当「检索返回」。
    verify: >-
      `set -a; . ./.env; set +a` 后
      `RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest
      tests/e2e/<EC-01 live 判据文件> -v` ⇒ **PASS（非 skip）**，且落盘记录中该 run
      canonical 终态**恰为 `SUCCEEDED`**、该阶段的工具观测**可读**、证据链里出现
      **外部可指认的检索标识**。反证：移除该能力声明 ⇒ 同一命令下该阶段工具观测**为空**
      （先红后绿成对，随后复原）。跑前自检 `EnvCredentialResolver().has('LLM_MAIN_KEY') is True`
      （**只问存在性，不物化值**）。
    status: PASS
    status_note: >-
      2026-09-22 cycle 4 达成（载体取 (b) **新建** `real_retrieval_research_v1.yaml`，cycle 3 定案并附实测理由）。
      **执行侧**：新模块 `phase_capabilities.py` 按 phase 的 run-chain 声明执行
      （`require_frozen_tool_set` → 既有 `execute_tool_call` → provider → 既有
      `register_tool_evidence`），证据经 `register_and_gate` 并入**同一个** session claim。
      证据 ①live 判据 `tests/e2e/test_run_chain_retrieval_live.py` **PASS（非 skip）**，
      同命令连跑 3 次皆 PASS；落盘样张 `scratch/goal011-c4-live-facts.json`：run
      `1c8b23bc-c990-4c3e-9236-6afaefd27c25` 终态 **`SUCCEEDED`**、真实出站**恰 2 次**
      （esearch+efetch，host = `eutils.ncbi.nlm.nih.gov`）、读面两条工具证据可读、
      检索返回 `42767441/42765796/42765769` 且**读取步读的正是这一串**（逐字在
      evidence id / source_ref 里）⇒ ②③ 同时成立。②反证（先红后绿、随后复原）：
      同一条 live 命令下移除两条能力 ⇒ 该阶段工具观测**为空**（`AssertionError: []`），
      复原 ⇒ PASS；离线 e2e 另有一条**成对**判据（不接能力步 ⇒ 零观测）。
      ③**离线**判据（默认门可跑、不出网）三条：机制 7 条 + e2e 主干 1 条 + 成对反证 1 条。
      跑前自检 `EnvCredentialResolver().has('LLM_MAIN_KEY') is True` 已过。
      **残余登记**（不粉饰）：W-C 生产组合根今天不接该步（`composition.py` = 450 行硬上限零余量；
      与 W-A 同源）、W-D 检索内容不进模型上下文（只有 claim relation 这一层 grounded 关系）、
      W-E 覆盖今天仍由**声明输入**满足（EC-02 的靶子）、W-F 失败 run 里已登记的工具证据
      无 claim 可挂 ⇒ 读面看不到（如实行为，非缺陷）。实测发现 F-a（efetch DOCTYPE 守卫会拒掉
      每一次真实响应，已按威胁边界修正并加回归判据）与 F-b（判据取值面过宽导致假红，已收窄）。
  - id: EC-02
    criterion: >-
      **证据链从「声明输入」升级为「系统取得」**：读面**区分来源类型**——
      `USER_PROVIDED`（声明输入）与 **`RETRIEVED`（系统取得）** 必须**可区分且口径诚实**，
      **不得混称**；`EVIDENCE_COVERAGE` 由 **EC-01 的检索来源**满足。
      **判据**：`GET /runs/{id}/evidence` 中满足覆盖的来源**含检索来源**，该来源
      **可追溯到外部标识**（PMID/DOI/URL）且 **digest 可重算**。
      **反证（成对）**：去掉检索来源 ⇒ 覆盖率判拒（`EVIDENCE_COVERAGE` 判 `False`）。
      **不得**用模型自述充当外部来源；**不得**用「计数 ≥ 1」代替来源性质的判据。
    verify: >-
      真实 run 的读面里，满足 `EVIDENCE_COVERAGE` 的来源集合**包含检索来源**，
      其来源记录可读、可追溯到**外部标识**、内容 **digest 可独立重算**；
      反证：把检索来源摘除 ⇒ 同一 run 的 `EVIDENCE_COVERAGE` **必须判拒**
      （先红后绿，随后复原）。
    status: PASS
    status_note: >-
      2026-09-22 cycle 5 达成。**定案（写死）**：① 载体＝`TrustLabel` **加成员** `RETRIEVED`
      （而非读面另造反推字段：`EvidenceDto.source_trust_label` 本就是那条读面，值直取
      `SourceRecord.trust_label`；另造就得用前缀启发式，本仓明文拒绝）。边界论证＝**不触及
      Canonical State 边界**：分类枚举加成员，不改状态机/生命周期、无 CHECK 约束（`trust_label`
      两存储面均 `TEXT NOT NULL`）⇒ **无迁移**，且 EC-02 是 GOAL frontmatter（最高优先级）逐字要求。
      ② 覆盖判据＝**新增可选** `minimum_retrieved_sources`，与既有 `minimum_sources` **两维并存**
      （缺省 `None` ⇒ 既有行为逐字不变）；把计数收窄成「只数检索来源」会**回退** GOAL-010 已判绿的
      语义并把无检索协议一并打红 ⇒ 那是回归不是收紧。③ 盖章点唯一：`ToolEvidenceInput.trust_label`，
      由调用方按 **provider 声明的 `network_domains`** 给值（外部域 ⇒ `RETRIEVED`，否则 `GENERATED`）。
      ④ 新合约 `real_retrieval_deliverable`（`minimum_retrieved_sources: 1`）只绑检索协议；
      共用契约 `real_research_deliverable` 逐字未动（否则 GOAL-010 的 `real_research_task_v1` 会被判拒）。
      **判据**：① 读面区分性质——同一次 run 上 `RETRIEVED`（检索）与 `USER_PROVIDED`（声明输入）、
      `GENERATED`（会话自述）三者并存且不混称；② 覆盖由**检索来源**满足（门判的是
      `SourceRecord.trust_label`，**不是**证据条数）；③ 可追溯＋可重算——检索标识逐字在
      evidence id/source_ref 里，四条证据的 digest 全部由库里字节**独立重算一致**。
      **反证（成对，EC-02 本体）**：去掉检索 ⇒ 同一 run 的 `EVIDENCE_COVERAGE` **判拒**、
      run 收敛 **`FAILED`**，判词逐字 `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (1 >= 1 sources)`
      （1 条声明输入在场却不算数 ⇒ 正是「计数 ≥ 1 不能代替来源性质」）。**按压三次全先红后绿**：
      ① 摘掉合约的性质维度 ⇒ 反证用例红（run 回到 `SUCCEEDED`）；② 盖章强制成 `GENERATED` ⇒
      主干红（`0 < 1 retrieved sources (3 >= 1 sources)`）；③ **live 同一条命令**摘掉协议里两条检索
      能力 ⇒ live 判据红（`0 < 1 retrieved sources (1 >= 1 sources)`）⇒ 复原 ⇒ PASS。
      **live 判据** `tests/e2e/test_run_chain_retrieval_live.py` **PASS（非 skip）**，同命令连跑
      2 次皆 PASS；样张 `scratch/goal011-c5-live-facts.json`：run
      `a93e6b36-619b-4e65-b2af-9865d0c87c7e` 终态 **`SUCCEEDED`**、真实出站**恰 2 次**
      （esearch+efetch）、`trust_labels = [GENERATED, RETRIEVED, USER_PROVIDED]`、返回
      `42768236/42767441/42765796` 且读取步 id/source_ref 逐字含之、四条证据
      `digest_recomputed_matches` 全 `true`。**离线判据**（默认门可跑、不出网）：机制 9 条 +
      e2e 主干 1 条 + 成对反证 1 条。**「模型自述不算外部来源」**由两条判据钉住：只有自述证据时
      性质计数为 0（`count_retrieved_sources` 按 SourceRecord 判），且门的两维互不顶替。
      **残余登记（不粉饰）**：W-C（生产组合根仍不接能力步，与 W-A 同源）、W-D（检索内容不进模型
      上下文）、W-F（失败 run 里已登记的工具证据无 claim 可挂 ⇒ 读面看不到；本 cycle 的按压样张
      再次实测了这一点）、**W-G（新）**：判词此前只在失败消息里，没有单列的「criterion 判词」读面；
      **W-H（新）**：性质维度只对**显式声明**它的合约生效，其他协议不受影响（刻意，非缺陷）；
      **W-I（新）**：`RETRIEVED` 目前只由运行链能力步盖章——将来若有别的外部取得路径，各自准入点
      必须同样盖章（今天的唯一准入入口仍是 `register_tool_evidence`）。**W-E 就此关闭**（覆盖不再
      由声明输入满足）。live 调用记账：本 cycle **5 次真实运行**（判据 3 次 + 样张 1 次 + 按压 1 次），
      其中 4 次各含**恰 2 次**真实检索出网，1 次（按压）只到 LLM。
  - id: EC-03
    criterion: >-
      **真实实验执行链**（视预算；**若空间不足则如实登记为下一轮输入，不得降级 EC-01/EC-02**）：
      真实 LLM 驱动一条**实验协议**（`sort_analysis_v1` **或** `m12_reference_research_v1`）
      跑到**终态**，**实验产物 + 证据 + 预算归账**可读。执行体 = **既有 Docker 后端**
      （已 E2E 验证），**不新增执行后端、不新增依赖**。
    verify: >-
      真实 run 的 canonical 终态如实记录（**只有 `SUCCEEDED` 是成功**；`FAILED` **不得**
      写成成功）；读面可取到该 run 的**实验产物**、**证据**与**预算归账**三项。
      若预算不足未做，如实登记为**下一轮输入**并说明原因——**不得**记 PASS。
    status: PENDING
    status_note: >-
      2026-09-22 cycle 6：**未达成，如实登记为下一轮输入**（EC-03 原文允许：「视预算；若空间不足则
      如实登记为下一轮输入，**不得降级 EC-01/EC-02**」）。**已落地的机械**（`PLAN-20260922-135`，
      `3ee18b3`/`a4c11f2`/`5d5e86f`/`713dce7`）：① 执行缝的**声明化**——`TaskContract.experiment`
      （`ExperimentExecutionSpec`，缺省 `None` = 会话语义逐字不变）+ schema/loader/sqlite 往返；
      `phase_runner` 的派发判据从**字面量 id**（`== "experiment_execution"`）改成
      `contract.experiment is not None`（`phase_runner` 450→**448** 行）；声明了而缝没接 ⇒ **点名拒绝**
      （fail-closed，**不**静默回退到会话）。② **装配面**：`services/api/experiment_support.py` 把
      **既有** `ExperimentExecutor` + `GovernedExperimentExecutor` + **既有 DockerExecutionBackend**
      （M9 已 6 容器 E2E）接进 `OrchestrationDependencies.experiment_task`（`service.py` 450→**449** 行）；
      live/ops 装配 `with_sandbox_experiment` 在**本次 run 的目录**上发声明（协议与共享夹具零改动）。
      ③ 实验脚本 `examples/experiments/sort_analysis_baseline.py`（纯标准库、确定性，产出
      `analysis_report` + `experiment_result.json`）。④ 判据：
      `tests/application/run_orchestration/test_sandbox_experiment_dispatch.py` **4 passed**
      （派发 / 点名拒绝 / 声明形状 / 缺省语义）+ `tests/e2e/test_sandbox_experiment_reachability.py`
      **3 passed**（离线，`judged 0 connection attempt(s)`）。**阻断点（实测，未修，逐字）**：
      `sort_analysis_v1` 过不了真实的 compile→preflight→freeze——预检报告状态 **`WARN`**、四条
      `WARNING TOOL_RISK_ELEVATED | provider openhands_workspace has elevated risk class HIGH`；
      根因是**无条件**分层 `classify_risk(EXECUTE, BUILT_IN) → HIGH`（`packages/domain/tools.py:143-144`，
      与 trust level 无关），而 `freeze_manifest` 的 `if not report.passed: raise ManifestFreezeError`
      （`preflight.py:186-187`）**拒绝冻结** ⇒ run 在**执行之前**终止：`state: FAILED`、
      `manifest_digest: null`、`protocol_body_digest` 非空（编译过）、`/tasks` 与 `/experiments` 均为 `[]`、
      零工具观测。**不是本 cycle 引入的**：同一装配下**不做**任何沙箱实验声明时实测**同一签名**
      （对照组 `NO_DECL=1`）。**为什么不自行修**：可用的「修法」= 放宽 `classify_risk` 的严重级、或让
      `freeze_manifest` 接受 `WARN`、或把 `code.execute` 从合约能力里删掉——三条都是**改门禁/改验收门
      凑成功**，本 GOAL 明文禁止且命中 `escalation_triggers`。**另一份被点名的协议**
      `m12_reference_research_v1` **同样不可执行**（7 个 phase 里 5 个没有 `task_contract` ⇒
      `service._contract_for` 抛 `ValueError("phase declares no task contract")`；其 discovery phase 的
      `EVIDENCE_COVERAGE: minimum_sources: 10` 无诚实 run 路径：该 phase 零声明输入、一次工具调用
      1 条来源 ⇒ 至少 11 次真实出网 × `parallel_agents` 的 2 个会话 = 22 次），且 GOAL cycle 1 迭代日志
      **已登记**它就是「已声明但不可执行」。**下一轮输入（二选一，需拍板）**：(A) 拍板「`EXECUTE` 类
      provider 的 HIGH 风险警告是否应当阻断冻结」——若按既有 WARN 语义应「只警示不阻断」，就改冻结门
      的输入口径（**那是改门禁，需用户/ADR 授权**）；(B) 换载体：给 `m12_reference_research_v1` 补 5 份
      缺的 phase 合约**并**为 discovery phase 找到诚实的 10 条来源路径（例如把它的 `inputs:` 声明与组合根
      种入对齐，或接受 22 次真实检索出网的代价）。**本 cycle 不记 PASS、不降级 EC-01/EC-02。**
  - id: EC-04
    criterion: >-
      **用户视角端到端验收**：真实数据下走完整流程——**建项目 → 选协议 → 跑真实 run →
      看制品/证据/预算/血缘**，留**可复核记录**（读面快照**或**本机截图，落 `scratch/`、**不进仓库**）。
      顺带**复核前端 `partial` 页面在真实数据下的诚实标注是否与实际一致**——
      **不一致即如实登记，不粉饰**。
    verify: >-
      `scratch/` 下有可复核的端到端记录（读面快照或本机截图 + 步骤说明），
      覆盖上述五步；`partial` 页面的诚实标注核对结论**逐条写明**（一致 / 不一致 + 证据）。
      截图**不得**上传到任何外部服务。
    status: PENDING
  - id: EC-05
    criterion: >-
      **`R-6` 词表固化（可选，成本小）**：让「**默认 CI 离线**」这条声明**要么成立、
      要么如实降级措辞**——把 `tiktoken` 词表**固化进镜像/私有源**，
      **或**在文档与判据里明确「**CI 每轮有一次受控外部下载**」。
      **判据**：**断网跑默认门 ⇒ 行为可判定**；**措辞与事实同源**。
      **不得**为了让它变绿而放宽 `tests/egress_guard.py` 的判据或放行面。
    verify: >-
      断网（或阻断该单一目的地）跑默认门 ⇒ 结论**可判定且与记录中的措辞一致**；
      若选择固化，则同一条件下默认门**不产生**该外部下载；若选择降级措辞，
      则文档与判据的措辞**逐字对应**事实（每轮一次受控下载）。
    status: PENDING
  - id: EC-06
    criterion: >-
      **收口复检 + 残余登记**：独立复检脚本（**当前树 + 干净 checkout 同结论**）+
      本地 m0 全量 **23/23** + 治理 `validate.py` 绿 + CI 台账（逐 run 到终态）；
      GOAL-008/009/010 遗留的人工面 **13 条原样保留** + 本 GOAL 自己的 **W 列表**。
      残余**不得**因收口消失。**`ANTHROPIC` run 腿仍为可选验证项**（不进退出的标准）。
    verify: >-
      复检脚本多层判据全 PASS 且两棵树同结论；`make validate-all` ⇒ **23/23**；
      治理 `.cursor/skills/governance-check/scripts/validate.py` 绿；本文件
      `latest_recheck` 指向**仓库相对路径**的 PASS/PASS_WITH_WARNINGS RECHECK；
      frontmatter 的 EC 状态与 markdown 状态表**一致**（GOAL-006/007/008/009/010
      收口时都出过这一类漏改）。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的解析/传输库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 威胁建模/授权面（BOLA/BFLA）覆盖类决策——需用户或 ADR 拍板，本循环不得自行决定
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，需用户或 ADR 拍板
  - ADR-0031（`tool_pack.*`，Status: Proposed）是否采纳——归用户
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；本循环只做「显式配置才启用」）
  - 新增依赖或改动既有依赖 pin（含为 anthropic 形态引入 SDK——优先用手写 HTTP）
  - 明文凭据泄露（**即使是可弃用的免费额度**）——立即停止并报告
  - 放宽验收门（AcceptanceCriteria）以凑成功——本 GOAL 明文禁止，触及即 BLOCKED
  - 改动 Canonical State 边界（例如把验收门结果改成可改写已终态的行）——需拍板
  - 为跑通而**放宽出站判据**（`tests/egress_guard.py` / 放行面 / `network_domains` 声明）——触及即 BLOCKED
  - 把凭据写进 CI（哪怕只是为了让 CI 里看到 live 或检索分支）——本 GOAL 明文禁止
child_plans:
  - .cursor/plans/tasks/PLAN-20260922-133-real-retrieval-into-protocol.md
  - .cursor/plans/tasks/PLAN-20260922-134-retrieved-evidence-nature.md
  - .cursor/plans/tasks/PLAN-20260922-135-sandboxed-experiment-stage.md
  - .cursor/plans/tasks/PLAN-20260922-136-user-perspective-end-to-end.md
latest_recheck: null
memory_entries: []
---

# GOAL-20260922-011 — 真实研究能力落地（自迭代循环）

本 GOAL 承接 GOAL-20260921-010（**ACHIEVED**）收口时如实登记的**残余**，以及 GOAL-011 建档当日
**直接读代码核对**的起点事实。

## 目标与退出标准

| EC | 标准 | 验证命令／证据来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **真实检索进协议（主干）**：`ncbi_eutils` 的 `literature.search`/`literature.read` 声明进一份真实协议（加阶段 **或** 新建协议，二选一写明）⇒ 一次真实 run 的 discovery/analysis 阶段**实际调用检索**；判据 = run 到终态 + 工具观测存在且可读 + 检索来源的真实标识进入证据链；反证 = 移除该能力 ⇒ 该阶段无工具观测 | live 判据 **PASS（非 skip）** + run 终态 + 工具观测可读 + 外部标识在证据链；反证成对（先红后绿） | **PENDING** |
| EC-02 | **证据链升级为「系统取得」**：读面区分 `USER_PROVIDED` 与 `RETRIEVED`，口径诚实不混称；`EVIDENCE_COVERAGE` 由 EC-01 的检索来源满足；判据 = 来源含检索来源 + 可追溯到外部标识 + digest 可重算；反证 = 去掉检索来源 ⇒ 覆盖率判拒 | `GET /runs/{id}/evidence` 来源集合含检索来源且可追溯 + digest 独立重算；反证先绿后红再复原 | **PASS** |
| EC-03 | **真实实验执行链**（视预算）：真实 LLM 驱动 `sort_analysis_v1` 或 `m12_reference_research_v1` 到终态，实验产物 + 证据 + 预算归账可读（执行体 = 既有 Docker 后端） | run 终态如实记录（只有 `SUCCEEDED` 是成功）+ 读面三项齐备；预算不足则如实登记为下一轮输入，**不得**记 PASS | **PENDING**（cycle 6 落机械，**被既有 pre-freeze 阻断点挡住**，如实登记为下一轮输入——见 `status_note`） |
| EC-04 | **用户视角端到端验收**：建项目 → 选协议 → 跑真实 run → 看制品/证据/预算/血缘，留可复核记录（`scratch/`，不进仓库）；顺带复核前端 `partial` 页面的诚实标注与实际是否一致（不一致即如实登记） | `scratch/` 下可复核记录覆盖五步；`partial` 核对结论逐条写明 | **PENDING** |
| EC-05 | **`R-6` 词表固化**（可选，成本小）：让「默认 CI 离线」**成立或如实降级措辞**（固化 `tiktoken` 词表进镜像/私有源，或在文档与判据里写明「CI 每轮一次受控外部下载」）；判据 = 断网跑默认门 ⇒ 行为可判定；措辞与事实同源 | 断网/阻断单目的地跑默认门 ⇒ 结论可判定且与措辞一致 | **PENDING** |
| EC-06 | **收口复检 + 残余登记**：独立复检脚本（当前树 + 干净 checkout 同结论）+ m0 **23/23** + 治理 validate 绿 + CI 台账到终态；13 条人工面原样保留 + 本 GOAL 的 W 列表；`ANTHROPIC` run 腿仍为可选验证项 | 复检两树同结论；`make validate-all` 23/23；`validate.py` 绿；`latest_recheck` 为仓库相对路径；frontmatter 与状态表一致 | **PENDING** |

### 建档时已探明的现状（事实类，用于判定起点；**不当作验收依据**）

以下为 2026-09-22 建档当日**直接读代码/配置核对**的结论（不是引用历史记录）：

| # | 事实 | 核对方式 | 结论 |
| --- | --- | --- | --- |
| F-1 | `ncbi_eutils` provider **已声明** | 读 `examples/config/tool_providers.yaml:23-42` | `kind: REST`、`trust_level: VERIFIED`、`transport: rest`、`effect_class: READ_ONLY`、`protocol_version: eutils-2026-08-22`、能力 `literature.search` / `literature.read` / `citation.inspect`、`network_domains: [eutils.ncbi.nlm.nih.gov]`、`health_check: true`。**刻意不声明** `endpoint_env`（适配器自带 E-utilities 默认端点）与 `credential_ref`（`NCBI_API_KEY` **可选**；声明即「没有它不可用」，故不写） |
| F-2 | **能力面今天只是「校验/治理面」，不是「工具注入面」** | `packages/application/protocol_compile/requirements.py:87-111`（capability → `ToolRequirement(phase, capability, provider_ids)`）+ `packages/application/preflight/checks.py:167-226`（校验 + `TOOL_UNAVAILABLE` / `SUPPLY_CHAIN_UNPINNED`）+ `packages/application/run_orchestration/session_resolution.py:30-34` `flatten_tool_providers()`（把 provider **ID 字符串**并集冻进 `frozen_tool_set`） | 一个 phase 的 capability 最终只变成：预检通过的 `ToolRequirement`（provider id 列表）+ 冻进会话的 **provider id 元组**。**没有任何生产路径**把 capability/provider 变成**可执行的工具实现** |
| F-3 | **真正的 capability → tool 解析器存在，但零生产调用方** | `packages/application/tool_plane/resolver.py:98-138` `resolve_capability()` ⇒ `ToolBinding(capability, provider_id, tool_id, risk_class, pack_digest)`；`freeze_tool_set()` 在 `:163-172`；`build_tool_catalog` / `catalog_from_pack_records` 同目录 | 全仓搜索（排除模块自身与 `tests/`）：`resolve_capability` / `resolve_all` / `freeze_tool_set` / `build_tool_catalog` / `catalog_from_pack_records` 在 `packages/ services/ adapters/ tools/` **零命中** ⇒ **测试专用** |
| F-4 | **会话拿到的「工具」是 provider 名字符串；真实注册是空操作** | `adapters/openhands/session_builder.py:45,88-94`（`self._register_tools(spec.frozen_tool_set)` + `PolicyEnforcingAgent(tools=[Tool(name=name) for name in spec.frozen_tool_set])`）+ `services/api/runtime_support.py:208-221`（`AdapterDependencies(...)` **不传** `register_tools` ⇒ 回落到空操作 lambda）+ `adapters/openhands/tool_mapping.py:18-32`（`tools_for_frozen_set` / `register_custom_tools` **零生产调用方**） | **生产装配的 `register_tools` 缺省为空操作**（`tests/e2e/live_run_support.py:117-136` 也如此自述，测试里注入的是 `register_inert_tools`）⇒ 今天的真实会话**拿到的是 provider id 的占位工具**，**没有**可真正调用的检索实现 |
| F-5 | **`ncbi_eutils` 从未在生产装配里实例化** | 搜索 `NcbiEutilsProvider` 的构造点 | 只出现在 `tools/m12_ncbi_smoke.py:37`、`tools/personal_reference_workflow.py`、`tools/m12_reference_workflow.py` 与 tests ⇒ `services/` 与 `adapters/` 组合根**零命中** |
| F-6 | **可探测 provider 实例注册表在生产里恒为空** | `services/api/composition.py:135-137` `tool_providers: Mapping[str, Any] = field(default_factory=dict)`；搜索 `.tool_providers =` 赋值 | 只在 tests 里被赋值 ⇒ `services/api/preflight_support.py:159-161` 的 `probe_provider_spec` 对 `ncbi_eutils` 返回 `ProviderProbe(EndpointHealth.UNKNOWN, "控制面未注册可探测的 provider 实例")`（**如实 UNKNOWN，不伪装可用**） |
| F-7 | **`register_tool_evidence` 存在且严格，但零生产调用方** | 读 `packages/application/evidence/tool_evidence.py:47-97`；搜索全仓调用点 | 签名 `register_tool_evidence(ledger, artifacts, *, input: ToolEvidenceInput) -> (SourceRecord, Evidence)`；**要求** `ToolResultStatus.SUCCEEDED` + `output_digest` 存在，且**重读 spill 制品重新算 digest**，不等即 `ValueError("…content tampered")`。产出的 `SourceRecord.trust_label = TrustLabel.GENERATED`、`origin = f"tool:{tool_id}:{task_id}:{operation_key}"`。**唯一调用方是 `tests/application/evidence/test_tool_result_not_evidence.py`**（生产链 `result_handler.py` 走的是**另一条**路径） |
| F-8 | **`ToolCallRecord` 有类型、无持久化、无读面** | 读 `packages/domain/tools.py:327-340`；搜索表/仓储/路由 | 类型存在（`task_id / attempt / operation_key / tool_id / capability / argument_digest / status / recorded_at`）。SQLite schema 只有 `tool_packs` / `tool_provider_registrations`，**没有**工具调用表；**没有** tool-call repository；OpenAPI 的 tool 路径只有 `/tool-packs` / `/tool-provider-registrations*` / `/tool-providers` ⇒ **不存在「按 run 读工具调用」的读面**。非测试构造点只有 `tools/m12_ncbi_smoke.py:40` |
| F-9 | **`TrustLabel` 今天恰好 5 个成员，没有 `RETRIEVED`** | 读 `packages/domain/enums.py:244-249` | `TRUSTED_INTERNAL` / `VERIFIED_SOURCE` / `UNTRUSTED_EXTERNAL` / `GENERATED` / `USER_PROVIDED`。生产路径**只赋两种**：声明输入 ⇒ `USER_PROVIDED`（`result_handler.py:230`）、会话自产 ⇒ `GENERATED`（`result_handler.py:162`）。`VERIFIED_SOURCE` / `TRUSTED_INTERNAL` 今天**没有任何路径赋值** ⇒ EC-02 的 `RETRIEVED` 语义**落在读面新增一个成员还是复用既有成员之上**，是子 PLAN 必须**定案并写明理由**的决策（不得默默加域枚举） |
| F-10 | **`EVIDENCE_COVERAGE` 的计数口径** | `packages/domain/acceptance.py:144-155`（`count >= minimum` 即过，缺 `minimum_sources` 或 `count` 缺省时 **fail-closed 判 `False`**）+ `packages/application/run_orchestration/result_handler.py:60-68`（`evidence_source_count = sum(1 for item in self.evidence if item.artifact_id not in self.self_artifact_ids)`） | 只有**非自产**证据计数（声明输入 / 未来的检索来源）；自产制品被 `self_artifact_ids` 排除 |
| F-11 | 证据读面**已存在**且已暴露信任标签 | `services/api/routers/inspection.py:117-127`（`GET /runs/{run_id}/evidence` ⇒ `list[EvidenceDto]`）+ `services/api/dto/inspection.py:16-35`（`source_origin` / `source_trust_label` / `source_access_time`） | 读面齐备；`Evidence.tool_refs` **已持久化**但**未**暴露在 DTO 里。**投影口径（承重）**：`services/api/run_evidence.py` 的 `evidence_of_run()` **只经 claim relations 走** ⇒ 只 `register_evidence` 而不 `attach_relation` 的证据**在这个端点上不可见**（`register_tool_evidence` 今天正是这条形态） |
| F-12 | **真实协议的头部自己写着本 GOAL 要补的缺口** | 读 `examples/protocols/real_research_task_v1.yaml:15-29` | 逐字：「**真实检索来源尚未接线**（需把 `literature.search` 接到真实 provider、并把 `register_tool_evidence` 接进 run 链；GOAL-010 EC-02 登记的残余 W-7）」；并自述「受控范围：1 个 phase、1 件交付物、1 份声明输入」 |
| F-13 | **动 `real_research_task_v1.yaml` 有被判据钉住的后果** | 读 `tests/api/test_real_protocol_identity.py` 头部与 `_REAL` 常量 | 该判据**三面钉死**：文件声明的 `id:` / canonical `Run.protocol_id` / **被解析字节的 sha256 + 库里的冻结正文**。⇒ EC-01 若选 (a)「在 `real_research_task_v1` 上加阶段」，**必然**触及该冻结正文（属**合法维护路径**，但必须**先按压再复绿**、并把理由落记录）；选 (b)「新建协议」则**不动**该文件与其判据 |
| F-14 | 凭据面现状 | 列出 `secrets/` 与本机 `.env` 的**键名**（不读值） | `.env` gitignored、含 `LLM_MAIN_KEY`、**不含** `RESEARCHOS_AGENT_RUNTIME`（只有另一个无关的 `AGENT_RUNTIME=` 键）。`secrets/llm_key.txt` 建档当日**存在**（1 行 / 52 bytes / untracked），其值与 `.env` 的 `LLM_MAIN_KEY` **逐字节相同**（sha256 前 16 位一致）⇒ 重复副本；**已于建档当日按本 GOAL 授权删除**（见「凭据面清理」），删后 `secrets/` 目录仍在、`git status` 无痕 |
| F-15 | 既有 live 判据文件（可复用形态） | 列 `tests/e2e/` | `live_run_support.py`、`test_ec03_real_runtime_offline_chain.py`、`test_ec04_live_first_run.py`、`test_ec04_live_gate_offline.py`、`test_evidence_chain_source_live.py`、`test_live_failure_paths.py`、`test_live_model_absence.py`、`test_m12_usage_real_relay.py`、`test_real_deliverable_contract_live.py`、`test_real_protocol_run_live.py` |

**结论**：EC-01 的起点是 **F-2…F-6 联合构成的一处系统性缺口**——「能力声明」与「可执行工具」之间
**没有生产连线**。这不是「模型不肯调检索」，而是**会话里根本没有可调用的检索实现**：
`ncbi_eutils` 在生产装配里从未实例化、`register_tools` 是空操作、真正的 capability→tool 解析器
零生产调用方。因此 EC-01 是**可落地**的工程任务（把既有 `ToolResolver` / `NcbiEutilsProvider` /
`register_tool_evidence` 三者接进组合根与 run 链），而不是「碰运气让模型自己上网查」。
EC-02 的起点（F-7…F-11）说明：证据读面**已存在**、`register_tool_evidence` **已存在且严格**，
缺的是**接线**与**来源类型的诚实区分**（F-9 明确今天**没有** `RETRIEVED`）。

### EC-01 判定细则（真实检索进协议）

- **两条允许的落地路径**（二选一，**决策必须落记录**）：
  - **(a) 在 `real_research_task_v1` 上加阶段**：语义收敛、协议数不膨胀；代价是**必然**触及
    `tests/api/test_real_protocol_identity.py` 钉住的**冻结正文**（F-13）⇒ 属**合法维护路径**
    （先例：GOAL-010 EC-03 为 `validate_bundle` 注册表补一行），但**必须**先按压再复绿、
    并把「为什么必须动受判据保护的字节」写进记录。
  - **(b) 新建一份真实协议**：`real_research_task_v1` 与其判据**字节不动**，风险最小；
    代价是多一份协议与一份登记面。
  - **推荐 (b)**：本 GOAL 的主干是「把检索接进执行链」，**不**需要顺带改动一份已被三面钉死的
    协议字节；把两件事解耦，能让 EC-01 的 diff 面停在「接线 + 新协议 + 新判据」。
    **最终以子 PLAN 的定案为准，并在 GOAL 迭代日志写明选了哪条。**
- **「实际调用检索」的硬形态**：**一次真实 run** 在**真实执行体**下，其 discovery/analysis 阶段
  留下**可读的工具观测**，且证据链里出现**外部可指认的检索标识**（PMID / DOI / 标题）。
  **不算**：工具「被声明可用」、工具「被冻进 tool set」、模型**在文本里写了**一个 PMID。
- **反证必须成对**：从**绿**出发，把该能力**从协议移除** ⇒ **该阶段无工具观测**（红）⇒ 复原 ⇒ 复**绿**。
  只有绿没有红 ⇒ **判据没在看**。
- **禁止**：用 Fake 工具结果 / 桩响应 / 手写 fixture 充当「检索返回」；**禁止**放宽
  `tests/egress_guard.py` 或它的放行面来让检索用例跑起来（检索类用例**必须**挂
  `requires_live_llm` 或同一放行面）；**禁止**改合约使其匹配现状。
- **预算护栏**：NCBI 出网**只允许** `eutils.ncbi.nlm.nih.gov`（provider 的 `network_domains` 声明），
  **次数取最小必要**（同一 EC 不重复跑；能复用既有样本的不另发调用）；无 key ⇒ 适配器既有
  3 req/s 节流，**不得**为提速引入 `NCBI_API_KEY` 之外的任何东西、**不得**新增依赖。

### EC-02 判定细则（证据由系统取得）

- **要消灭的形态**：证据覆盖由「模型自述」或「声明输入」单独满足，而**没有**任何来源是
  **系统真的去外部取得**的。起点诚实边界（承 GOAL-010 `RECHECK-128` W-3）：声明输入
  `USER_PROVIDED` 证明的是「交付物与它被供应的输入之间有**可核验的 grounding 关系**」，
  **不**证明会话真的读过它——这正是本 EC 要与「系统取得」区分开的那条线。
- **`RETRIEVED` 的落地形态由子 PLAN 定案**（F-9 今天没有该成员）：允许的落点是
  「读面新增可区分的来源类型」或「复用既有枚举 + 读面另加可判字段」，**但必须先论证**：
  是否触及 Domain 面 / Canonical State 边界（**触及即 BLOCKED**，见 escalation）。
  **不得**默默扩域枚举而不落记录。
- **判据**：满足 `EVIDENCE_COVERAGE` 的来源**含检索来源**，该来源**可追溯到外部标识**
  （PMID / DOI / URL）且 **digest 可独立重算**（重算与落盘一致）。
- **反证成对**：去掉检索来源 ⇒ `EVIDENCE_COVERAGE` **判拒** ⇒ 复原 ⇒ 复绿。
- **投影口径提醒**（F-11）：`GET /runs/{id}/evidence` **只经 claim relations 走** ⇒
  接线时**必须**同时 `attach_relation`，否则来源「登记了但读不到」——
  这会表现为「判据说绿、读面看不到」，是必须提前按住的形态。

### EC-03 判定细则（真实实验执行链）

- 执行体 = **既有 Docker 后端**（已 E2E 验证）；**不新增执行后端、不新增依赖**。
- 终态**如实记录**：只有 `SUCCEEDED` 是成功；`FAILED` **不得**写成成功。
- **预算不足时**：如实登记为**下一轮输入**（写明原因与代价），**不得**记 PASS；
  且**不得**为腾预算而降级 EC-01 / EC-02（本 GOAL 的主干）。

### EC-04 判定细则（用户视角端到端）

- 允许在**本机**启动真实控制面 / 前端并操作 UI（授权见 frontmatter 第 (4) 条）；
  **仅本机、仅该端点**；**不上传任何截图到外部服务**；截图/录屏落 `scratch/` 且**不进仓库**。
- 五步必须走全：**建项目 → 选协议 → 跑真实 run → 看制品 → 看证据/预算/血缘**。
- **顺带复核**前端 `partial` 页面在真实数据下的诚实标注是否与实际一致——
  **不一致即如实登记，不粉饰**。

### EC-05 判定细则（`R-6` 词表固化，可选）

- 起点（承 `RECHECK-20260922-131` W-13 与 GOAL-010 R-6）：CI（`uv sync` 全新环境）上
  litellm 首次导入会下载 `tiktoken` 词表（CI 判据抓到 31 条 `57.150.192.193:443`）；
  GOAL-010 的修法只是在 **workflow 作业步骤**加预热门，把下载**挪出判据进程**⇒
  「CI **完全**离线」**仍不成立**。**本机 `judged 0` ≠ 默认门离线**（W-13）。
- 二选一：**固化**（把词表放进镜像/私有源）**或如实降级措辞**（文档与判据都写明
  「CI 每轮有一次受控外部下载」）。**判据**：断网跑默认门 ⇒ 行为**可判定**；措辞与事实**同源**。
- **禁止**为让它变绿而放宽 `tests/egress_guard.py` 的判据或放行面。
- **本项不进主干的达成前提**：它**可选**，未做**不**阻塞 EC-01/EC-02/EC-03/EC-04；
  但若做了，必须**如实**二选一，不得两边都含糊。

### EC-06 判定细则（收口复检 + 残余登记）

- 独立复检脚本：**只读 / 只用标准库 / 不 import 仓库代码**（形态承 `RECHECK-20260922-132`
  的 `scratch/verify_goal010_closeout.py`）；**两棵树同结论**（当前树 + `git clone --depth 1`
  到**仓外**的干净 checkout）。干净树**没有 `.env`** ⇒ 凭据类判据**如实 SKIP**（不读成通过）。
- **判据不得空转绿**：收口**之前**的树必须能判红（反证成立）。
- 治理 `validate.py` 绿；`make validate-all` **23/23**；
  `latest_recheck` 指向**仓库相对路径**的 PASS/PASS_WITH_WARNINGS RECHECK；
  frontmatter 的 EC 状态与 markdown 状态表**一致**。
- **残余不得因收口消失**：GOAL-008/009/010 的**人工面 13 条**（见下节）+ `RECHECK-121…126`
  与 `127…132` 的 W 列表 + 产品侧 `R-1/R-2/R-5/R-6` 与 `W-13` **逐条在位**，
  外加本 GOAL 自己的 W 列表。

## 循环入口协议

驱动方（会话或定时自动化）进入时，按迭代日志最后一行 + 工作树/远端实况判定续点：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit+CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

**本 GOAL 特有的续点判据**（live 面）：**live 调用是否已发生**以**落盘的记录/样本**为准
（不是以「命令跑过」为准）。任何「已跑过 live」的声称若无样本文件与 RECHECK 条目支撑，
按**未发生**处理。live 调用（真实 LLM **与**真实检索）**次数取最小必要**：
同一 EC 不重复跑；能复用既有样本的不另发调用。

## 驱动

- owner：`root-agent`；进入 cycle 时在迭代日志声明 `driver=client-goal / owner=root-agent`。
- 另一驱动已持有未收口的 ACTIVE cycle 时**等待**，不并发双写。
- 客户端自带的迭代/重试/超时上限**一律让位于**本文件 frontmatter 的 budget / fix_policy。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；用 Plan Mode 流程写
  子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加 `parent_goal: GOAL-20260922-011` 并投影
  `ALL_PLAN`，**同一提交**）。GOAL 迭代日志登记子 PLAN 路径。**live 类 EC 的子 PLAN 必须先写清
  「判据 + 失败如何落终态 + 反证形态」再跑**。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查规模门禁（**50 行函数 / 450 行文件**）与快照类门禁（OpenAPI / 设计基线），
  再跑 `make validate-all`（m0 全量 23 项）+ 受影响定向套件 + web 门（tsc/eslint/unit/build/stub/live e2e）。
  **默认门一律离线**；`tests/egress_guard.py` 是**结构判据**——**不得为了跑检索而放宽它**；
  **检索类用例必须挂 `requires_live_llm`（或同一放行面）才可出网**。live 步骤**只以单条命令的内联前缀**开：

      set -a; . ./.env; set +a
      RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest tests/e2e/<live 文件> -q -rs

  跑前确认 `EnvCredentialResolver().has('LLM_MAIN_KEY')` 为 `True`；**跑后不得把开关留在环境或 `.env`**。
  **本地不绿不得 push**。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main）→ 用 GitHub
  REST API 查 main 上 `m0-quality` 最新 run（**head_sha 匹配** + `/jobs` 读六个 job 结论）→
  轮询到终态；失败时取失败 job 日志作为证据。记录 run URL + **真实**终态（**禁止推测**）。
  **CodeQL 亦记账**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
  超过 fix_policy 上限或命中 escalation_triggers → `status=BLOCKED`。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、memory_entries、状态历史；
  未达终态 → 回到 ①（cycle+1）；触顶预算 → BLOCKED。**收尾前必须回写**。

**凭据自检（每轮，硬要求）**：任何记录/日志/回显中都**不得**出现 key 值或片段；发现泄露
（**即使是可弃用的免费额度**）立即**停止并报告**，按 escalation 处置。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先，禁改断言迁就** |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、**凭据可得性驱动的环境签名**） | 按 `docs`/记忆中的既有配方重跑（**先确认环境与 CI 同形**，见 `RECHECK-121` W-7）；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |
| **live 面（本 GOAL 特有）** | live 用例在 CI 上 skip 是**预期**（CI 离线、无凭据） | **不**为让 CI「看到 live 或检索」而把凭据塞进 CI；live 证据**只在本地实跑产生**并落 RECHECK |
| **出站判据（本 GOAL 特有）** | `egress guard: FAIL — … non-loopback destination(s)` | **先判是否判据本身在正确地挡**：默认门出现真实出站**就是红**，**修源头**（把出网挪进 `requires_live_llm` 放行面 / 用既有预热路径），**不**改判据、**不**改放行面语义 |

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS 且**有实跑证据** + 收口 RECHECK（独立复检，
  `result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK（**仓库相对路径**）
  + 「终止与收口」写明收口结论（含仍未处理项）。**EC-01 的实跑证据不可替代**：本 GOAL 的存在理由
  就是把「真实 run 成功」升级为「真实 run 真的做过研究」，因此**不存在**「检索未接线仍可 ACHIEVED」
  的退路——若检索能力无法接进执行链、或凭据/出网不可用导致 live 无法发生，
  **停止并记 `BLOCKED`（能力边界）**，**不**把 skip 或「已声明可用」写成完成。
  **可选验证项（`ANTHROPIC` run 腿）不参与 ACHIEVED 判定。**
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、或命中
  `escalation_triggers`（含**明文凭据泄露**、**放宽验收门**、**放宽出站判据**、
  改动 Canonical State 边界、把真实 runtime 设为默认、新增依赖、Accepted ADR）、
  或**凭据/出网不可用**导致 live 采样无法发生。
  写 BLOCKED 记录（原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），
  恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」**如实登记**为后继入口（**不隐藏缺口**），并给出恢复条件。

### EC-05 与主干的独立性

EC-05（`R-6` 词表固化）**可选**，且**不**阻塞 EC-01…EC-04；但 **EC-06 要求它已作出明确处置**
（做了 → 二选一如实；未做 → 如实登记为下一轮输入）。**不得**让「可选」变成「含糊」。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED
（前 11 项**原样承自 GOAL-008/009/010**，作为残余保留；第 3 项与第 12 项**本 GOAL 已获删授权**）：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——归用户拍板。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板。
3. **`artifacts/` token 清理**——涉及不可变历史资产与凭据面，需人工确认。
   **【本 GOAL 的例外】已获删授权**（授权范围严格限于该一个目标文件；其余不可变历史资产仍不动）。
   **建档当日实测结论：该目标已不在工作树上，无需动作。** 目标文件是
   `artifacts/钻孔官方API_v12/配置/官方API本地_v12.local.yaml`（据 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md`
   §6-U3 与 `RECHECK-20260917-091` W-4 登记：含明文 token、**从未提交**、未被仓库代码
   import/构建/CI 执行）。2026-09-22 实测：`ls -d artifacts/钻孔官方API_v12` ⇒ **No such file**；
   `find artifacts/ -type f` ⇒ 只剩 3 个 gitignored 的 `eval/*.json`（**零** token 形状命中：
   对 `sk-[A-Za-z0-9_-]{16,}` / `LLM_MAIN_KEY` / `api[_-]?key` / `Bearer ` 逐个计 0）。
   `git ls-files artifacts/` ⇒ **0 条**（确证从未跟踪）。⇒ **本项按「目标已不存在」如实登记**，
   **不**声称「本 GOAL 完成了清理」（没有可清理的对象），授权保留以备再现。
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险，需人工决定。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——上游 pin 变更，需用户或 ADR 拍板。
6. **hook 侧 L3 门**——治理面，需人工决定。
7. **把真实 runtime 设为默认**——默认必须仍是 Fake；本循环只做「显式配置才启用」。
8. **为 anthropic 形态引入 SDK / 新依赖**——优先用手写 HTTP；需要新依赖即 BLOCKED。
9. **把凭据写进 CI**（哪怕是为了让 CI 里看到 live 或检索分支）——**本循环明文禁止**；CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——涉及 Domain 面与可能的
    Canonical State 边界，需拍板。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——本 GOAL 明文禁止；这是「把门改成不挡路」。
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本，GOAL-009/010 登记的残余）**
    ——**【本 GOAL 的例外】已获删授权**：授权范围**严格限于该一个文件**（只删
    `secrets/llm_key.txt`，**不动** `secrets/` 目录本身、**不动**任何其他文件）。
    **建档当日已执行**（见下「凭据面清理」）。执行后**只追加**登记一条事实更正，
    **不得**改写 GOAL-009/010 的既有记录。

### 凭据面清理（本 GOAL 的授权动作，2026-09-22 建档当日执行）

- **动作**：删除 `secrets/llm_key.txt`。
- **删除前的核对（先看再删，不靠记述）**：该文件 1 行、52 字节，其**值**与
  `.env` 的 `LLM_MAIN_KEY` **逐字节相同**（两侧 sha256 前 16 位一致）⇒ 确系**重复副本**，
  删除**不丢失**任何唯一信息（`.env` 那份仍在）。**核对过程只比 digest、未回显任何值或片段。**
- **删除后核对**：`secrets/` 目录**仍存在**（授权要求不动目录）；`git status --porcelain secrets/`
  **无输出** ⇒ 该文件本就**未被跟踪**，删除对仓库**零影响**（不进任何提交）。
- **如实更正（只追加）**：GOAL-009 与 GOAL-010 的残余第 12 项登记的是「**未**在本循环授权内、
  如实登记为**泄露面**」——该记述**在 GOAL-011 建档当日失效**：文件已删。
  **不修改 GOAL-009/010 的原文**，仅在 GOAL-011 的「状态历史」追加这条事实。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**（GOAL-010 cycle 2 WP1 审计时
    **实测**发现）。核对方式：`git -c core.quotePath=false ls-files | grep -P '[^\x00-\x7F]'`
    ⇒ **30 条**（**注意**：不带 `-c core.quotePath=false` 时 git 会把非 ASCII 字节转义成八进制，
    该命令**返回 0 条**）。分布覆盖产品代码、migration、测试与工具链。
    **【本 GOAL 的处置】登记为豁免，不改判**：按 **AGENTS.md §13** 明文
    「**既有历史路径不会仅为满足本规则而批量重命名**」的口径，这 30 条属**既有历史路径**，
    本 GOAL **不**批量重命名，**登记为豁免**并把该口径写进记录（批量重命名 = 大 diff + 断引用，
    且 §13 本身给出豁免依据）。若判定需要 ADR，则**产出 ADR 草案**、**不自行改判**。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `1b3fc2f` | 治理 `validate.py` 绿 | M0 [35678978342](https://github.com/Eswink/research-system-new/actions/runs/35678978342) 六 job 全 **success** + CodeQL [35678977687](https://github.com/Eswink/research-system-new/actions/runs/35678977687) 3/3 **success**（逐 job 实查，终态 `completed`） | — | EC-01…EC-06 全 PENDING；起点已定位（**F-2…F-6**：能力声明与可执行工具之间**无生产连线**；**F-7…F-11**：证据读面与 `register_tool_evidence` 已存在但零生产调用方、`TrustLabel` 无 `RETRIEVED`）。**附带办结**：第 12 项残余（`secrets/llm_key.txt` 重复副本）已按授权删除（核对后零仓库影响）；第 3 项（`artifacts/` 明文 token）目标**已不在工作树**⇒ 按「目标已不存在」登记；30 条非 ASCII 路径**登记为豁免**（AGENTS §13 口径） | cycle 1 = derive **EC-01** 子 PLAN（真实检索进协议），**先定案 (a) 加阶段 还是 (b) 新建协议** |
| 1 | PLAN-20260922-133（EC-01，主干） | `934f7fc`（derive：PLAN-133 + ALL_PLAN 投影）、本 cycle 的 WP1 提交（定案 + GOAL 回写；**见下方 CI 台账尾巴**） | 治理 `validate.py` 绿（derive 后） | 见下方 CI 台账 | — （**WP1 只读**：未改产品代码、未发起任何真实/检索调用） | **EC-01 仍 PENDING**（定案已落，接线未落）。**WP1 定案**：① 载体取 **(a) 扩展 `real_research_task_v1`**，且**不新增 phase**、只在其既有 `analysis` phase 上加 `literature.search`/`literature.read` 两条声明（逐字满足 EC 的「analysis 阶段」表述；仍为 **1 次真实会话**；不引入同义协议增殖；与既有三面身份判据兼容）；`m12_reference_research_v1` **不做载体**（4+ phase / parallel_agents / min 10，属「已声明但不可执行」）。② 接线取「**run 链能力步**」而**非**「模型自己调工具」——生产装配 `register_tools` 是空操作、会话里的工具只是 provider ID 字符串 ⇒ 押在模型行为上会红在装配缺失且是概率性的；四个接入点 I-1…I-4 **全部复用既有件**（`resolve_sessions` / `OrchestrationDependencies` / `execute_tool_call` / `register_tool_evidence`），并给出 `phase_runner` **净增 ≤ 7 行**硬预算（`composition.py` **零余量**、`phase_runner.py` **7 行**，源自 `test_python_source_limits.py` 的 450/50 门）。③ 反证四层 R-1…R-4：**R-1 = 从协议删掉能力 ⇒ 该 phase 无工具观测**（EC-01 判据本体）；R-2 = 改协议 `id:` ⇒ 身份判据必须红（判据不空转）；R-3 = 读面查不存在的 run ⇒ 必须**如实报「无」**；R-4 属 EC-02。**同时更正一条 derive 判断**：D-13 担心的「改协议要同步改冻结快照」**实测证伪**——`test_real_protocol_identity.py` 的摘要**运行时现算**（对被测文件）+ 与**该次 run 自己冻结的正文**比对，**无**硬编码摘要常量 ⇒ 改正文该判据自动复绿（但**必须按压**证明它仍在看）。**WP3 先做两个离线探针**：P-1 会话健康（新增的 `ncbi_eutils` 进 `frozen_tool_set` 会不会让真实会话初始化失败）、P-2 投影（只 `register_evidence` 不 `attach_relation` 确实读不到）。**cycle 1 尾段更正（只追加，推翻本行早先的一句）**：我先写「生产装配对未注册名字的行为**未经验证**」——**错**。该行为**有文档、有判据、机制可查**：`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的 `test_unmapped_tool_set_is_named_not_silently_dropped` 用 `map_tools=False`（**生产装配**）断言 run **`FAILED`** + 消息含 **`"is not registered"`** + **工具解析前零 LLM 调用**；`docs/architecture/TOOL_RUNTIME.md` 逐字写着「**provider id → SDK tool name 的映射不存在**…缺映射时会话创建**点名失败**」；`resolve_tool()` 对未注册名字 `raise KeyError`；实测进程启动时 `list_registered_tools() == []`。⇒ **三条改变范围的结论**：①**今天生产装配跑不动任何真实会话**——冻结集里的 `m12_artifact` 本身就未映射 ⇒ 会话创建点名失败；GOAL-010 那三次 `SUCCEEDED` 是在 `map_tools=True`（测试侧惰性注册）下取得的 ⇒ 它证明的是「**有映射时**可达」，**不是**「生产可达」。②**「provider → SDK 工具映射」由「不做」改为「必做」**：否则声明新能力之日就是 run 全红之日（这条缺口是 GOAL-007 EC-05 命名过但未落地的）。③对 `ncbi_eutils` 应注册**真实**工具（复用 `NcbiEutilsProvider`，与运行链能力步**同源**），而**不是**惰性桩；但**模型是否真的调用它不作判据**（概率性），EC-01 的证据仍由**运行链能力步**确定性产出 | cycle 2 = 执行 **WP2**（工具观测的读面；因 `_run_artifact_ids` 已覆盖 evidence 引用的 artifact，最小形态可能是**纯加性**补一处读面，落笔前先确认哪些面已够用）+ **WP3**（**provider → SDK 工具映射**：必做项，先离线判据可测）+ P-2 投影探针 |
| 2 | PLAN-20260922-133（EC-01，续） | 见下方 CI 台账尾巴（本 cycle 的提交在回合汇报中给出终态） | **P-2 探针**：`scratch/probe133_evidence_projection.py`（离线/内存/无出网）实测 —— 证据**只登记不挂 relation** ⇒ `evidence_of_run` 返回 `[]`（读面**看不到**）；同一证据**挂上 relation** ⇒ 可见，且 `tool_refs`/`source_origin` 可取 ⇒ **接线必须 `attach_relation`**（I-4 由推断升级为实测）。**WP2 落地**：`EvidenceDto.tool_refs`（纯加性）+ `_evidence_dto` 填充 + `docs/api/openapi.m13.json` 重生成（diff **恰 7 行、只有新字段**）+ `apps/web/src/api/types.ts` 与 `apps/web/tests/unit/consoleFixtures.ts` 同步。**判据**：`tests/api/test_inspection_api.py::test_evidence_read_face_distinguishes_tool_origin`（同 run 两条证据的 `tool_refs` 必须**不同**）；**已按压**（把填充改成 `[]` ⇒ 该用例 FAILED，复原 ⇒ 9 passed，diff 只剩 1 行新增、无残留）。**门**：`tests/api/test_inspection_api.py` 9 passed；`tests/contracts/test_openapi_snapshot.py` 8 passed；`ruff`/`ruff format --check`/`mypy` 全绿；web `typecheck`+`lint`+`unit 76/76` 全绿 | 见下方 CI 台账尾巴 | — （**未改判据强度、未放宽出站判据**） | **EC-01 仍 PENDING**（读面已具备，接线未落）。**本 cycle 实测的本地环境签名（与本 cycle 改动无关，已用基线对照证明）**：本机全量 `python/tests` 会因**出站结构判据按设计判红**而 exit 1——`egress guard: FAIL … 2 non-loopback destination(s)`，两条均指向 **`198.18.0.178:443`（`kind=private`）**，归因链 `tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure` → `preflight_support.build_endpoint_health` → `… → transport._execute_request`；真因是**本机 DNS 走 fake-IP 代理（198.18/15）**，例示 endpoint 被解析成私网 fake-IP ⇒ 真实连接发起 ⇒ 判红。**基线对照**：`git stash` 掉本 cycle 的三处 Python 改动后**在原始树上跑同一命令** ⇒ **同样的 2 条与同样的 FAIL**（`4337 passed, 1 failed`）⇒ **不是本 cycle 引入**。**未改判据、未放行、未 skip**（那是明文禁止的「为跑通而放宽出站判据」）。**一条被自己证伪的推断**（保留教训）：曾把 exit 1 归因为「缺 otel collector ⇒ metric exporter 退出时 flush 失败」；按既有 compose 起了 collector（loopback-only、镜像本机已有、无构建无出网）**重跑仍是同一条红** ⇒ 推断错误，已更正；collector 已 `down`，机器恢复原状 | cycle 3 = **WP3 定案的岔路必须先选并写明理由**：**(M-1)** 逐 provider 造真实 SDK 工具（模块级定义；executor 集成点待探）/ **(M-2)** 在声明面把「运行链执行的能力」与「会话工具」**声明化**地分开（**不得**改 `test_unmapped_tool_set_is_named_not_silently_dropped` 的强度；若触及 provider 规格/Domain 边界 ⇒ **BLOCKED** 归人工拍板）。定案前**不得**动 `flatten_tool_providers` 或那条判据 |
| 3 | PLAN-20260922-133（EC-01，续） | 见下方 CI 台账尾巴（本 cycle 的提交在回合汇报中给出终态） | **WP3 定案（M-2）+ 映射落地 + 两条判据（都按压过）**：① 定案 **M-2 声明化分离**，理由**实测**——M-1（造真实 SDK 工具）收益侧被证伪：会话工具调用在 `PolicyEnforcingAgent._evaluate` 里以 `capability=<provider id>` 送 policy，而 `policy.yaml` 词汇表全是**能力名**且 `default_effect: DENY` ⇒ 注册了也一调用即被拒；且任何**全局**修法都会打红 `test_unmapped_tool_set_is_named_not_silently_dropped`（它跑的就是**生产组合根**）。② 承载**由 (a) 改为 (b)**（EC-01 原文允许二选一）：把两条 `literature.*` 声明进 `real_research_task_v1` 会**立刻打红 4 条既有判据**（产品路径可达性 + 指纹读面 3 条），归因链逐段实测——声明 REST provider ⇒ `ncbi_eutils` 进冻结集 ⇒ 默认装配下健康诚实 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN`（WARNING）⇒ 报告 `WARN` ⇒ `freeze_manifest` 要求 `PASS` 而**拒绝冻结**（service 侧门却只在 `FAIL` 时失败 ⇒ **既有语义不一致**，本协议是第一条踩到的）⇒ 新载体 = `examples/protocols/real_retrieval_research_v1.yaml`。③ 落地面全部**加性**：`CapabilityExecution` → `ProtocolPhase`/`CompiledPhase` 透传 → protocol schema 一项 enum → loader（缺省 `session` = 旧行为）→ `run_chain_tool_ids`（**按 phase 作用域**）→ `SessionSpecContext`/`AgentSessionSpec` → `tool_mapping.session_tool_ids`（越界**点名拒绝**）→ `session_builder`（建会话与 fork 两条路径都过滤）。**两个面都不减**：能力仍在 `tool_requirements`、provider 仍在冻结集（`require_frozen_tool_set` 仍拦越权），只把「会话工具列表」这一面拿掉。**判据**：新增 `tests/architecture/python/test_run_chain_capability_exposure.py`（6 条；删掉声明行 ⇒ **4 红**，复原 ⇒ 6 passed）+ `tests/e2e/test_ec03_real_runtime_offline_chain.py::test_declared_run_chain_capabilities_let_production_assembly_start`（**生产装配**下会话建得起来、无 "is not registered"、run `SUCCEEDED`；删声明 ⇒ 红，实测原因为 `ToolDefinition 'm12_artifact' is not registered`）。**门**：`tests/api`+`tests/contracts`+`tests/loaders`+`tests/architecture` **1122 passed / 69 skipped**（余 3 条 `test_worker_plane_composition` 经**基线对照**证明与本次改动无关）；`tests/tooling` 1107 passed；`ruff`/`ruff format --check` **全绿**；全量 `mypy` **982 files Success**；本地 m0 **21/23**——一红是本 cycle 判据的 mypy 标注（**已修并用同一命令复验绿**），一红是本机 **fake-IP DNS** 撞出站结构判据（`198.18.0.178:443`，与 cycle 2 同两条同归因链；pytest 自身 **4346 passed / 0 failed**，**未改判据、未放行、未 skip**） | 见下方 CI 台账尾巴 | — （**未改任何门禁语义、未动 `test_unmapped_tool_set_is_named_not_silently_dropped` 一个字、未放宽出站判据**） | **EC-01 仍 PENDING**（本 cycle 只让它**可验**：声明面 + 装配面已落地并被判据钉住；**能力步本体**——运行链真的调检索并登记证据——未落）。**如实登记的 W 列表**：**W-A** 新协议在**默认装配**下的产品路径**今天跑不动**（上面那条既有 `WARN`/`freeze` 不一致）；**W-B** 协议编辑器往返会**丢** `capability_execution`（`protocolSerialize.ts` 逐键构造 phase body、没有这一键；丢的是声明、失败仍是**点名**失败）；**W-C** 4 条既有判据红线已归因并**只追加**记录在 PLAN 的「决策 1 的更正」节 | cycle 4 = **WP3 后半（能力步）**：按 I-1…I-4 把「运行链执行该 phase 的 run-chain 能力」落成确定性步骤（解析 provider → 既有 `execute_tool_call`（策略在其内）→ 既有 `register_tool_evidence` → **必须** `attach_relation`，P-2 已实测），离线（Fake provider）先绿；再 **WP4** live 判据（`requires_live_llm`，最小必要次数的真实检索 + 外部标识进证据链 + 按压 R-1 反证）。**定案已写死，不得回退**；`phase_runner` 净增 ≤ 7 行的预算不变 |

| 4 | PLAN-20260922-133（EC-01，收口） | 见下方 CI 台账尾巴（本 cycle 的提交在回合汇报中给出终态） | **能力步本体落地 + 四条判据全部实跑**。落地：新模块 `phase_capabilities.py`（运行链执行 phase 声明的 run-chain 能力：`require_frozen_tool_set` → 既有 `execute_tool_call` → provider → 既有 `register_tool_evidence`；证据经 `register_and_gate` 并入**同一个** session claim）+ `ScopedPolicy`（把 preflight 那张 capability→scope 表补进执行期策略请求；`execute_tool_call` 未改，仍是唯一裁决点）+ `PhaseRunnerDeps/OrchestrationDependencies.capabilities`（缺省 None ⇒ 不启用）。判据：① 机制 7 条（真实 provider + MockTransport；含 5 条 fail-closed 面与「未声明 ⇒ 零请求」）；② e2e 主干 1 条（生产装配 `map_tools=False` 下 `SUCCEEDED` + **两次**请求 + 读面两条工具证据 + PMID 逐字在 evidence id/source_ref 里）；③ 成对反证 1 条（不接能力步 ⇒ 零观测）；④ **live 判据 PASS（非 skip）**，同命令连跑 3 次皆 PASS。**按压（先红后绿）**：删 `capability_execution` 行 ⇒ run `FAILED`（`ToolDefinition 'm12_artifact' is not registered`）且主干红；保留声明删两条能力 ⇒ e2e 红在 `AssertionError: []`；**live 同一条命令**做同样按压 ⇒ `AssertionError: []`（该 phase 无工具观测），复原 ⇒ PASS。**live 样张**（`scratch/goal011-c4-live-facts.json`）：run `1c8b23bc-c990-4c3e-9236-6afaefd27c25` 终态 **`SUCCEEDED`**、零失败，真实出站**恰 2 次**（esearch+efetch，https/`eutils.ncbi.nlm.nih.gov`），esearch 的 query = 声明输入的 `retrieval.query`（命中 `count=85908`），返回 `42767441/42765796/42765769`，**读取步读的正是这一串**；两条工具证据读面可读；`trust_label` 仍是 **`GENERATED`**（EC-02 的靶子）。**本地门**：`ruff`/`ruff format --check`/`mypy`（984 files）全绿；`tests/{application/run_orchestration,integration,architecture,loaders,contracts}` **718 passed**；`tests/e2e` 全绿；`tests/api` 496 passed + **3 条既有跨套件顺序失败**（`test_worker_plane_composition`，**已用 `git stash` 基线对照证明与本次改动无关**）；m0 **23/23 项全跑**，唯一红项是**既有本机签名** `python/tests`（`egress guard: FAIL … 2 non-loopback destination(s)` → `198.18.0.178:443 (kind=private)`，pytest 自身 **4361 passed, 17 skipped, 0 failed**）——**未改判据、未放行、未 skip** | 见下方 CI 台账尾巴 | **F-a**：`parse_efetch_xml` 的 PA-1 守卫"拒绝一切 DOCTYPE"会拒掉**每一次真实 efetch**（真实响应带外部 DOCTYPE；离线夹具不带 ⇒ 从未被测到）⇒ 按威胁本身收边界（拒 `<!ENTITY` 与带内部子集的 DOCTYPE、放行外部 DOCTYPE），新增两条判据、两条既有拒绝用例**仍然拒绝**；**F-b**：live 判据第一版用正则扫整个 `source_ref` 取标识，把 task UUID 的十六进制段当 PMID ⇒ **真实运行里假红**，改为只解 operation_key 一段 | **EC-01 = PASS**（见 EC-01 `status_note`）。**残余 W**：W-A/W-B（cycle 3）+ 本 cycle **W-C**（生产组合根不接该步：`composition.py` = 450 行硬上限零余量，与 W-A 同源）、**W-D**（检索内容不进模型上下文）、**W-E**（覆盖今天仍由声明输入满足）、**W-F**（失败 run 里已登记的工具证据无 claim 可挂 ⇒ 读面看不到）。**另**：`phase_runner.py` 450 / `service.py` 450 / `composition.py` 450 —— 三份文件同时贴在硬上限（下一轮任何净增都要先拆分）。live 调用计数如实登记：本 cycle 真实检索 **7 次运行 × 2 请求**（含按压与判据复跑），最小必要口径下全部记账 | cycle 5 = **EC-02**：`TrustLabel` 加 `RETRIEVED`（含读面 `source_trust_label` 区分）+ 检索来源**可追溯到外部标识** + `EVIDENCE_COVERAGE` 由**检索来源**满足（反证：去掉检索来源 ⇒ 覆盖率判拒，先绿后红再复原）；不得用模型自述充当外部来源、不得用「计数 ≥ 1」代替来源性质 |
| 5 | PLAN-20260922-134（EC-02） | `2241087`（derive）、`46dfe82`（WP1 Domain）、`1d4dc85`（WP2 编排）、`3a5f706`（WP3 合约+判据）、`acaf3fb`（WP4 文档）；本 cycle 的收口提交见下方 CI 台账尾巴 | **来源性质成为一等事实 + 覆盖按性质判**。落地：`TrustLabel.RETRIEVED`（分类枚举加成员，**无迁移**）、`AcceptanceCriterion.minimum_retrieved_sources`（**可选**；缺省 `None` ⇒ 既有行为逐字不变）、`CriterionInputs.retrieved_source_count` + 覆盖判据**两维**（计数 + 性质，缺一 fail-closed 且**点名**缺哪一维）、`ToolEvidenceInput.trust_label`（盖章点唯一，按 provider 的 `network_domains` 声明给值）、`count_retrieved_sources`（从 **canonical 的 SourceRecord** 判性质 ⇒ 与读面 `source_trust_label` **同源**）、新合约 `real_retrieval_deliverable` 只绑检索协议、门被拒时失败消息带**逐条判词**（此前被换成 `None` 丢掉，GOAL-010 收口 W-9「诊断更钝」同源）。**判据四层**：机制 9 条（domain 5 + application 4）、e2e 主干 1 条（生产装配、离线）、**成对反证** 1 条（不接能力步 ⇒ 零工具观测 **且** 覆盖判拒 ⇒ run `FAILED`）、**live 判据 PASS（非 skip）×2**。**按压三次全先红后绿**：① 摘合约性质维度 ⇒ 反证用例红（run 回 `SUCCEEDED`）；② 盖章强制 `GENERATED` ⇒ 主干红，判词 `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (3 >= 1 sources)`（3 条来源在场、0 条检索 ⇒ 逐字证明「计数」顶替不了「性质」）；③ **live 同一条命令**摘协议里两条检索能力 ⇒ live 红，判词 `0 < 1 retrieved sources (1 >= 1 sources)`（1 条声明输入在场），复原 ⇒ PASS。**live 样张**（`scratch/goal011-c5-live-facts.json`）：run `a93e6b36-619b-4e65-b2af-9865d0c87c7e` 终态 **`SUCCEEDED`**、真实出站**恰 2 次**（esearch+efetch）、`trust_labels = [GENERATED, RETRIEVED, USER_PROVIDED]`（**三种性质在同一 run 上可区分**）、返回 `42768236/42767441/42765796` 且**读取步 id/source_ref 逐字含之**、四条证据 `digest_recomputed_matches` **全 `true`**（拿库里字节重算，非自证）。**本地门**：`ruff`/`ruff format --check`/`mypy` 全绿；定向 `tests/{api,loaders,contracts,architecture,integration}` **1215 passed / 2 skipped**；`tests/e2e`+`tests/tooling` **1104 passed / 8 skipped**；m0 **23/23 项全跑**，唯一红项是**既有本机签名** `python/tests`（`egress guard: FAIL … 2 non-loopback destination(s)` → `198.18.0.200:443 (kind=private)`，pytest 自身 **4370 passed, 17 skipped, 0 failed**）——**未改判据、未放行、未 skip**；治理 `validate.py` 与 DOCS-CHECK 绿 | 见下方 CI 台账尾巴 | **F-c（本 cycle 自己撞上并修好，两次）**：新增判据把 `tests/e2e/test_ec03_real_runtime_offline_chain.py` 顶到 **470 行**（>450 硬上限）⇒ 把运行链检索两条用例**移出**到 `tests/e2e/test_run_chain_retrieval_offline.py`（原文件回落到 372 行，判据**只增不减**：两条用例原样搬、断言不变）；live 判据的测试函数涨到 **63 行**（>50 函数上限）⇒ 拆成 `_assert_identifier_landed` + `_assert_source_nature` 两个辅助函数，断言逐条保留。两条都是**规模门禁在本地 m0 里抓出来的**，不是自查发现 | **EC-02 = PASS**（见 EC-02 `status_note`）。**残余 W**：W-C/W-D/W-F（承 cycle 4，本 cycle 未动）、**W-G（新）**判词只在失败消息里、没有单列 criterion 判词读面、**W-H（新）**性质维度只对显式声明的合约生效（刻意）、**W-I（新）**`RETRIEVED` 今天只由运行链能力步盖章（将来别的外部取得路径须在各自准入点盖章）。**W-E 关闭**（覆盖不再由声明输入满足）。live 调用记账：**5 次真实运行**（判据 3 + 样张 1 + 按压 1），其中 4 次各含**恰 2 次**检索出网 | cycle 6 = **EC-03**（真实实验执行链）：真实 LLM 驱动 `sort_analysis_v1` **或** `m12_reference_research_v1` 跑到终态，**实验产物 + 证据 + 预算归账**三项可从读面取到；执行体＝**既有 Docker 后端**，不新增后端/依赖；**只有 `SUCCEEDED` 是成功**，预算不足则如实登记为下一轮输入（不得记 PASS）。随后 EC-04（用户视角端到端 + `partial` 页诚实核对）/ EC-05（`R-6` 词表 pin，可选）/ EC-06（收口复检）。**收口待办（登记，不遗漏）**：EC-01/EC-02 的子 PLAN（133/134）在 **EC-06 收口时**一并收口——写 RECHECK（result=PASS/PASS_WITH_WARNINGS）、置 DONE、填 `latest_recheck`，并把可复用事实写成 MEM 条目（GOAL 的 `memory_entries` 同步）；本 cycle 未提前收口子 PLAN，是为了让复检覆盖整段工作而不是逐 cycle 半成品 |
| 6 | PLAN-20260922-135（EC-03） | `457dd39`（derive + ALL_PLAN）、`3ee18b3`（WP1 声明面）、`a4c11f2`（WP2 声明式派发）、`5d5e86f`（WP3 既有 Docker 实验链接入装配 + live 夹具）、`713dce7`（WP4 实验脚本 + 判据）；本 cycle 的收口提交见下方 CI 台账尾巴 | **实验阶段从「按合约 id 特判」变成「按合约声明派发」，并把既有 Docker 实验链首次接进运行编排**。落地四件：① **声明面**——`TaskContract.experiment`（`ExperimentExecutionSpec`：script / image / command / timeout_seconds，构造期拒空 command 与 <1 超时；**缺省 `None` = 会话语义逐字不变**）+ `schemas/task-contract.schema.json` 的 `$defs.experimentExecution` + loader（未知键**点名拒绝**）+ sqlite 往返 + `examples/contracts/task_contracts.yaml` 两份实验合约（`experiment_execution` 空映射 = 脚本由装配上下文给；`m12_experiment_execution` 把脚本/镜像 pin 在契约里）。② **派发面**——`phase_runner` 由字面量 id（`== "experiment_execution"`）改成 **`contract.experiment is not None`** → `dispatch_experiment`（450 → **448** 行，净减）；声明了而缝没接 ⇒ `outcome="FAILED"` + `failure_category=CONFIGURATION` + 消息点名合约 id 与 `no experiment runner is wired`（**fail-closed，不静默回退到会话**）。③ **装配面**——`services/api/experiment_support.py` 用**既有** `ExperimentExecutor` + `GovernedExperimentExecutor` + **既有 `DockerExecutionBackend`**（`research-os-sandbox:m9-test`，M9 已 6 容器 E2E）接进 `OrchestrationDependencies.experiment_task`（`service.py` 450 → **449** 行；**首次有组合根接上这条缝**），live/ops 由 `tests/e2e/live_run_support.py::with_sandbox_experiment` 在**本次 run 的目录**上发声明（协议与共享夹具零字节改动）。④ **实验脚本** `examples/experiments/sort_analysis_baseline.py`（纯标准库、确定性归并排序基准，产出 `analysis_report` + `experiment_result.json` 并按 `EXPERIMENT_RUN_ID` 回显）。**判据**：`tests/application/run_orchestration/test_sandbox_experiment_dispatch.py` **4 passed**（声明 ⇒ 缝被调用 / 声明+未接 ⇒ 点名 FAILED / 声明形状 ValueError / 缺省保持会话语义）+ `tests/e2e/test_sandbox_experiment_reachability.py` **3 passed**（离线，`judged 0 connection attempt(s)`；把阻断点钉成可复核形态）。**阻断点（实测，未修）**：`sort_analysis_v1` 过不了真实的 compile → preflight → freeze——预检报告 **`WARN`**、4 条 `WARNING TOOL_RISK_ELEVATED \| provider openhands_workspace has elevated risk class HIGH`，根因是**无条件**的 `classify_risk(EXECUTE, BUILT_IN) → HIGH`（`packages/domain/tools.py:143-144`，与 trust level 无关）+ `freeze_manifest` 的 `if not report.passed: raise`（`preflight.py:186-187`）⇒ run 在**执行之前**终止：`state: FAILED`、`manifest_digest: null`、`protocol_body_digest` 非空、`/tasks` 与 `/experiments` 均 `[]`、零工具观测；**对照组**（同一装配、`NO_DECL=1` 不发任何声明）**同一签名** ⇒ **既有**，非本 cycle 引入。**为什么不自修**：可选修法（放宽 `classify_risk` 严重级 / 让 `freeze_manifest` 接受 `WARN` / 把 `code.execute` 从合约能力里删掉）**三条都是改门禁凑成功**，明文禁止且命中 `escalation_triggers`。**本地门**：第一轮 **20/23**，三条红**全是本 cycle 自己的**——`python/format-check`（新判据文件 1 个待重排）、`python/typecheck`（同文件 3 条 `attr-defined`：`EffectClass`/`RiskClass`/`TrustLevel` 应从 `packages.domain.enums` 导入）、`python/tests`（**既有判据的真实回归**：`tests/integration/test_ig1_phase_runner.py::test_phase_runner_experiment_promotes_claim_and_memory` 报 `AssertionError: assert 'FAILED' == 'SUCCEEDED'`——它的 fixture 合约**没有**声明，派发判据改动后按会话派发）。三条全部修好（**给 fixture 补声明，断言一字未改**；反方向由新判据钉住）：`ruff format --check apps services packages adapters tests` = **999 files already formatted**、`mypy` = **Success: no issues found in 989 source files**、三文件 `pytest` = **8 passed**；第二轮 m0 = **23/23**（`PASS: profile=m0; 23 deterministic checks`；`python/tests` **4379 passed / 18 skipped / 0 failed**；本轮的 env 配方同既有规矩 `LLM_MAIN_KEY=""` + 钉住测试 DSN + 其余 DSN 键空，**未出现**此前几轮那条本机 fake-IP 出站判红）。治理 `validate.py` exit 0；`phase_runner` 448 / `service.py` 449 / `composition.py` 450（**未增长**）| 见下方 CI 台账尾巴 | **F-d（本 cycle 自伤，m0 抓出）**：派发判据由「按 id」改「按声明」打红了既有 `test_ig1_phase_runner.py` 的 fixture（它自带合约、不读目录）。处置 = 给 fixture 补 `ExperimentExecutionSpec` 声明，**断言逐条保留**；教训与 cycle 5 的 F-c 同形——**三道门与既有判据的回归都是本地 m0 抓出来的，不是自查发现的**。**F-e**：新判据文件同时踩 `ruff format` 与 `mypy attr-defined` 两道门（导入路径应为定义处 `packages.domain.enums`），已修。**F-f（CI 抓到的自伤）**：新判据里的**装配用例**走真实装配 ⇒ 构造 `DockerExecutionBackend`，而 CI 的 windows 跑者**没有 Linux daemon** ⇒ 台账提交 `cdd7b7d` 的 M0 在 `python/tests` 判红（`1 failed, 4136 passed, 260 skipped`，`DockerException: Error while fetching server API version`）。**修法 = 挂既有 `requires_docker` 标记**（判据内容不变、不 skip 产品行为），使它落到既有 `container-quality` 作业（`-m requires_docker`）里**真跑**；本地三向实跑已验（3 passed / `-m requires_docker` 1 passed+2 deselected / `-m "not requires_docker"` 2 passed+1 deselected） | **EC-03 = PENDING**（见 EC-03 `status_note`：机械已落，被既有 pre-freeze 阻断点挡住，如实登记为下一轮输入）。**残余 W**：W-C/W-D/W-F（承 cycle 4）、W-G/W-H/W-I（承 cycle 5）、**W-J（新）**沙箱实验缝只在 run-ready/live 装配上接线（生产组合根未接，与 W-C 同源）、**W-K（新）**`EXECUTE` 类 provider 的 HIGH 风险警告**阻断冻结**这条既有语义交叉需用户/ADR 拍板。live 调用记账：**本 cycle 未发起任何真实检索、未建立任何真实会话、未起任何实验容器**——两次真实 run 尝试（声明组与对照组）都在**冻结之前**终止（零 task / 零实验 / 零工具观测 ⇒ 模型侧零调用）。**只追加的更正**：本行原写「零 LLM 调用、**零出网**」——**「零出网」这一句撤回**：本 cycle 没有对「预检是否发生端点健康探测」做任何观测（前两轮那类「恰 2 次」由判据内的显式计数器给出，本 cycle 无对应计数器）⇒ 只保留**有证据的部分**（无会话、无工具观测、无实验容器），**不声称出网次数** | 下一轮输入**二选一（需拍板）**：**(A)** 拍板「`EXECUTE` 类 provider 的 HIGH 风险警告是否应当阻断冻结」——若按既有 `WARN` 语义「只警示不阻断」，就改**冻结门的输入口径**（那是改门禁，需用户/ADR 授权）；**(B)** 换载体：给 `m12_reference_research_v1` 补 5 份缺的 phase 合约**并**为其 discovery phase 找到诚实的 10 条来源路径（或接受 ≥22 次真实检索出网的代价）。拍板后 EC-03 的真实链（产物 + 证据 + 预算归账三读面）才可能跑到 `SUCCEEDED`；随后 EC-04（用户视角端到端 + `partial` 页诚实核对）/ EC-05（`R-6` 词表 pin，可选）/ EC-06（收口复检） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档 | `1b3fc2f` | M0 [35678978342](https://github.com/Eswink/research-system-new/actions/runs/35678978342) | 六 job 全 **success**（`console-frontend` / `collector-quality` / `container-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate`；terminal `status=completed conclusion=success`，逐 job 实查）；**同一次推送另触发 CodeQL** [35678977687](https://github.com/Eswink/research-system-new/actions/runs/35678977687) = **success**（3/3） |
| cycle 1 派生（PLAN-133 + ALL_PLAN） | `934f7fc` | 与下一条**同一次推送**（GitHub 只对 tip 触发一个 run）⇒ 该提交的验证由下一行承担，**不**意味着它没进 CI |
| cycle 1 WP1（定案 + GOAL 回写） | `d81ba38` | M0 [35682001003](https://github.com/Eswink/research-system-new/actions/runs/35682001003) | 六 job 全 **success**（`collector-quality` / `quality-windows-latest` / `container-quality` / `eval-gate` / `console-frontend` / `quality-ubuntu-latest`，逐 job 实查）；**CodeQL** [35682000340](https://github.com/Eswink/research-system-new/actions/runs/35682000340) = success（3/3） |
| cycle 1 P-1 探针（离线，无出网） | `39e7c92` | M0 [35682911157](https://github.com/Eswink/research-system-new/actions/runs/35682911157) | 六 job 全 **success**（逐 job 实查）；**CodeQL** [35682911380](https://github.com/Eswink/research-system-new/actions/runs/35682911380) = success（3/3） |
| cycle 1 收口（台账到终态 + WP2 收缩） | `c80d907` | M0 [35683930419](https://github.com/Eswink/research-system-new/actions/runs/35683930419) | 六 job 全 **success**（逐 job 实查）；**CodeQL** [35683930086](https://github.com/Eswink/research-system-new/actions/runs/35683930086) = success（3/3） |
| 台账尾巴（cycle 2 回写） | 见回合汇报（**台账尾巴口径**：本条自身触发的 run 不再回写文件） | | |
| cycle 3 收口（M-2 落地 + 两条判据按压 + GOAL 回写） | `edef420` | M0 [35697806645](https://github.com/Eswink/research-system-new/actions/runs/35697806645) | 六 job 全 **success**（`quality-ubuntu-latest` / `quality-windows-latest` / `container-quality` / `console-frontend` / `collector-quality` / `eval-gate`，逐 job 实查，终态 `completed`）；**CodeQL** [35697806055](https://github.com/Eswink/research-system-new/actions/runs/35697806055) = success（3/3） |
| 台账尾巴（cycle 4 回写） | 见回合汇报（**台账尾巴口径**同上） | | |
| cycle 5 WP0–WP4（derive + Domain + 编排 + 判据 + 文档；**同一次推送**，GitHub 只对 tip 触发一个 run） | tip `acaf3fb` | M0 [35717806500](https://github.com/Eswink/research-system-new/actions/runs/35717806500) | 六 job 全 **success**（`container-quality` / `console-frontend` / `eval-gate` / `quality-ubuntu-latest` / `collector-quality` / `quality-windows-latest`，逐 job 实查，终态 `completed`、`conclusion=success`）；**CodeQL** [35717806354](https://github.com/Eswink/research-system-new/actions/runs/35717806354) = success（3/3：`Analyze (actions)` / `Analyze (python)` / `Analyze (javascript-typescript)`） |
| 台账尾巴（cycle 5 收口回写） | 见回合汇报（**台账尾巴口径**同上） | | |
| cycle 6 WP0–WP4 + 3 条门禁修复 + 记录（**同一次推送**，GitHub 只对 tip 触发一个 run） | tip `9d85862` | M0 [35733068236](https://github.com/Eswink/research-system-new/actions/runs/35733068236) | 六 job 全 **success**（`console-frontend` / `eval-gate` / `quality-windows-latest` / `container-quality` / `collector-quality` / `quality-ubuntu-latest`，逐 job 实查，终态 `completed`、`conclusion=success`）；**CodeQL** [35733067165](https://github.com/Eswink/research-system-new/actions/runs/35733067165) = success（3/3：`Analyze (python)` / `Analyze (javascript-typescript)` / `Analyze (actions)`） |
| cycle 6 台账回写（GOAL 状态历史 + 台账行） | `cdd7b7d` | M0 [35735119552](https://github.com/Eswink/research-system-new/actions/runs/35735119552) = **failure**（**本 cycle 自伤，已修**：`quality-windows-latest` 的 `python/tests` —— `tests/e2e/test_sandbox_experiment_reachability.py::test_the_declaration_and_the_seam_land_on_the_run_assembly` 在**没有 Linux daemon** 的跑者上构造 `DockerExecutionBackend` ⇒ `docker.errors.DockerException: Error while fetching server API version`；`1 failed, 4136 passed, 260 skipped`；其余五 job 全 success）；**CodeQL** [35735119571](https://github.com/Eswink/research-system-new/actions/runs/35735119571) = success（3/3） |
| 台账尾巴（cycle 6 收口回写） | 见回合汇报（**台账尾巴口径**同上） | | |

**台账尾巴口径**（沿用 GOAL-005…010，写死在此）：写下**本条**「CI 台账回写」提交自身触发的 run
在**回合汇报**里给出终态，**不再回写文件**。

## 状态历史

- 2026-09-22：建档（`status: ACTIVE`）。承 GOAL-010「收口结论」的残余清单
  （`R-1` / `R-2` / `R-5` / `R-6`、`RECHECK-20260922-131` 的 **W-13**、13 条人工面）
  与 `RECHECK-20260921-127…132` 的 W 列表。EC-01…EC-06 全 PENDING。
  起点事实 F-1…F-15 为建档当日直接读代码/配置核对所得（**不当作验收依据**）。
- 2026-09-22（只追加，事实更正）：**凭据面清理**——`secrets/llm_key.txt` 已按本 GOAL 授权删除。
  该文件是第 12 项残余，GOAL-009/010 的原文称「**未**在本循环授权内…如实登记为**泄露面**」，
  **该记述自本日起失效**。核对：删除前其值与 `.env` 的 `LLM_MAIN_KEY` 逐字节相同（重复副本，
  删除不丢信息）；删除后 `secrets/` 目录仍在、`git status` 无痕（本就 untracked，零仓库影响）。
  **不修改 GOAL-009/010 原文**，仅在此追加。同时：第 3 项（`artifacts/` 明文 token）目标目录
  `artifacts/钻孔官方API_v12/` **已不在工作树上**（实测 No such file；`git ls-files artifacts/` = 0）
  ⇒ 按「目标已不存在」登记，**不**声称完成了清理。
- 2026-09-22（只追加，30 条非 ASCII 路径）：**登记为豁免**。实测
  `git -c core.quotePath=false ls-files | grep -P '[^\x00-\x7F]'` ⇒ **30 条**（与 GOAL-010 记载一致）。
  按 **AGENTS.md §13** 明文「既有历史路径不会仅为满足本规则而批量重命名」的口径，
  这 30 条属**既有历史路径**，本 GOAL **不**批量重命名、**不**自行改判；
  若后续判定需要 ADR，则**产出 ADR 草案**交人工。
- 2026-09-22（cycle 4 收口）：**EC-01 = PASS**——检索由运行链真实执行并落进证据链
  （详见下方迭代日志第 4 行与 EC-01 的 `status_note`）。GOAL **仍 ACTIVE**（EC-02…EC-06 未完）。
  本 cycle 的两条实测发现（F-a 真实 efetch 被 DOCTYPE 守卫全拒、F-b 判据取值面过宽导致假红）
  已当轮处置并加回归判据；残余 W-C…W-F 与「三份文件同时贴 450 行硬上限」一并登记。
  **CI 终态**：`42171fa` 的 M0 [35705918737](https://github.com/Eswink/research-system-new/actions/runs/35705918737)
  六 job 全 success、CodeQL [35705918073](https://github.com/Eswink/research-system-new/actions/runs/35705918073)
  3/3 success（逐 job 实查，终态 `completed`）。
- 2026-09-22（cycle 5 收口）：**EC-02 = PASS**——证据链的**来源性质**成为一等事实，
  `EVIDENCE_COVERAGE` 由**系统取得**的检索来源满足（详见下方迭代日志第 5 行与 EC-02 的
  `status_note`）。GOAL **仍 ACTIVE**（EC-03…EC-06 未完）。要点：`TrustLabel.RETRIEVED`
  是**分类枚举加成员**（不触及 Canonical State 边界、无迁移）；覆盖判据新增**可选**性质维度
  （缺省语义逐字不变）；盖章点唯一且按 provider 的 `network_domains` **声明**给值；判据取自
  canonical 的 `SourceRecord`，与读面**同源**。**按压三次全先红后绿**，反证判词逐字
  `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (N >= 1 sources)`。**本 cycle 自己撞上并修好的
  两条规模门禁失败**（F-c：e2e 文件 470 行、live 判据函数 63 行）已如实登记在迭代日志里。
  **W-E 关闭**；新增残余 W-G/W-H/W-I。
- 2026-09-22（cycle 6 收口）：**EC-03 仍未达成，如实登记为下一轮输入**（EC-03 原文允许「视预算；
  若空间不足则如实登记为下一轮输入」）。本 cycle 把**实验执行阶段**从「按合约 id 特判」做成
  **按合约声明派发**（`TaskContract.experiment`，缺省 `None` = 会话语义逐字不变；声明了而缝没接
  ⇒ **点名 fail-closed** 拒绝），并把**既有** `DockerExecutionBackend`（M9 已 6 容器 E2E）
  **首次**接进 `OrchestrationDependencies.experiment_task`；7 条离线判据（4 + 3）钉住新语义与
  **阻断点**。**阻断点（实测、既有、未修）**：`sort_analysis_v1` 过不了真实的
  compile → preflight → freeze——`classify_risk(EXECUTE, BUILT_IN) → HIGH` **无条件**
  ⇒ `TOOL_RISK_ELEVATED`(WARNING) ⇒ 报告 `WARN` ⇒ `freeze_manifest` 的 `if not report.passed`
  **拒冻** ⇒ run 在**执行之前**终止（`state: FAILED`、`manifest_digest: null`、零 task / 零实验 /
  零工具观测 / **零 LLM 调用**）；**对照组**（同一装配、不发任何声明）同一签名 ⇒ **非本 cycle 引入**。
  可选修法三条都属**改门禁**，明文禁止 ⇒ 交人工拍板（下轮的 (A)/(B) 二选一已写在迭代日志第 6 行）。
  **GOAL 仍 ACTIVE**（EC-03…EC-06 未完；预算 20 用 6，`no_progress_stop_cycles: 2` 未触）。**本 cycle
  自伤三条**（`python/format-check` / `python/typecheck` / `python/tests` 的既有判据回归）**全部由本地
  m0 抓出并修好**（20/23 → 23/23），其中回归的修法是**给既有 fixture 补声明、断言一字未改**。
  **CI 终态**：tip `9d85862` 的 M0 [35733068236](https://github.com/Eswink/research-system-new/actions/runs/35733068236)
  六 job 全 success、CodeQL [35733067165](https://github.com/Eswink/research-system-new/actions/runs/35733067165)
  3/3 success（逐 job 实查，终态 `completed`）。新增残余 **W-J**（实验缝只在 run-ready/live 装配上接线）
  与 **W-K**（`EXECUTE` 类 provider 的 HIGH 风险警告**阻断冻结**这条既有语义交叉待拍板）。
- 2026-09-22（cycle 6 只追加，CI 抓到的一条自伤与其修复）：`9d85862` 的 M0/CodeQL 双绿之后，
  紧随的台账提交 `cdd7b7d` 的 M0 **判红**——`quality-windows-latest` 的 `python/tests` 里
  `tests/e2e/test_sandbox_experiment_reachability.py::test_the_declaration_and_the_seam_land_on_the_run_assembly`
  抛 `docker.errors.DockerException: Error while fetching server API version`
  （`1 failed, 4136 passed, 260 skipped`）。**根因**：该用例走**真实装配** ⇒ 构造
  `DockerExecutionBackend`，而 CI 的 windows 跑者**没有 Linux 可用的 daemon** ⇒ 构造期即抛。
  **修法 = 挂既有 `requires_docker` 标记**（判据内容与断言一字未改、**不** skip 产品行为），
  使它落到**既有的 `container-quality` 作业**（`pytest -m requires_docker`，该作业会 build
  沙箱镜像）里**真跑**；本地三向实跑已验（全跑 3 passed；`-m requires_docker` 1 passed +
  2 deselected；`-m "not requires_docker"` 2 passed + 1 deselected）。
  ⇒ 本 cycle 的**四处自伤**（本地 m0 抓三条：format / mypy / 既有判据回归；CI 抓一条：Docker 装配）
  **全部如实登记，无一条被掩盖**。
