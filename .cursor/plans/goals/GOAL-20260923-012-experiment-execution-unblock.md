---
id: GOAL-20260923-012
slug: experiment-execution-unblock
title: 实验执行链打通：策略显式允许的 EXECUTE 可冻结（留痕通道）并让实验协议真实跑到终态
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-23 用户会话指令（goal 模式）：**建档 GOAL-20260923-012 并授权本驱动自动化循环推进、
    无需逐轮确认**。authorization 原文要点如下：
    (1) **用户已拍板路径 (A)**：授权把冻结门从「只认 PASS」改为「**策略已显式允许的 EXECUTE
    可冻结算 PASS**」——即新增一条**显式、留痕、可审计**的通道，而**不是**放宽风险分类、
    **不是**让冻结门无条件接受 WARN。授权范围严格限于：
      a) `classify_risk(EffectClass.EXECUTE, …) → HIGH` **保持不变**（风控保守性不动）；
      b) 判据改为：当且仅当「该能力/工具的 EXECUTE 风险已被**显式策略声明**允许（policy 中有
         对应 allow 规则且作用域匹配）、且该允许在 manifest/事件里**留痕**」时，冻结门的 WARN
         可被接受并记为 PASS；**未声明允许时仍拒冻**（默认 deny 不变）；
      c) 拒绝语义必须**点名**缺哪条策略事实（不笼统报 WARN）。
    (2) **live-gated 真实调用授权（承 GOAL-009/010/011，本 GOAL 继续有效）**：用户授权在真实端点
    上做 **live-gated 真实调用**——端点与模型已登记（`ANTHROPIC` 协议 + `agnes-2.5-flash`）；
    **次数取最小必要**，不做压测、批量或重复重跑。凭据仅在本机 **gitignored `.env`**（键名
    `LLM_MAIN_KEY`），其值为**可弃用的免费额度**、用户已明示**不要求保密**（此声明只降低追责
    口径，**不放松下面的凭据纪律**）。
    (3) **授权真实检索出网**：限 **`eutils.ncbi.nlm.nih.gov`**（`examples/config/tool_providers.yaml`
    的 `ncbi_eutils` 项 `network_domains` 声明内），次数取最小必要；无 key 按适配器既有节流。
    (4) **授权真实实验执行**：**Docker 后端、本机容器**（既有 `research-os-sandbox:m9-test`）；
    容器遵守既有安全姿态（不挂 docker socket、不 privileged、不 host home）。
    (5) **凭据纪律（不得放松）**：值**不得写入任何 tracked 文件、DB、记录（PLAN/RECHECK/MEM/GOAL）、
    日志或命令回显**（含片段）。**不得把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`**——它**只作为
    单条命令的内联前缀**；否则默认门会切到真实 runtime、破坏 CI 语义。
    (6) **默认姿态不变**：默认 runtime 保持 **Fake**、默认 CI **离线**（AGENTS.md §11）；live 分支
    必须**显式** `RESEARCHOS_AGENT_RUNTIME=openhands` 才开门（fail-closed，AGENTS.md §9）。
    **不得为了跑通而放宽出站判据**（`tests/egress_guard.py` 是结构判据：默认门出现非环回目的
    即判红）；真实调用类用例**必须挂 `requires_live_llm`（或同一放行面）**才可出网。
    (7) **push-to-main-for-CI 授权**：只推 `main`、**不 force**、**不重写历史**、**不推旁支**触发 CI；
    push 前 `git pull --ff-only origin main`。循环预算与纪律以本文件 frontmatter 为准
    （客户端自带的迭代/重试/超时上限**一律让位于**此）。
    GOAL-001…011 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED），本 GOAL 不修改它们；
    如需指名只允许按**只追加**补一行事实更正。
objective: >
    把 GOAL-011 停在 EC-03 的那条路（用户拍板 **(A)**）走通：给**冻结门**加一条**显式、留痕、
    可审计**的通道——**策略已显式允许的 EXECUTE 风险**（policy 里有对应 allow 规则且作用域匹配）
    可让预检 WARN 的 run 完成冻结并记为 PASS，且该允许在 **manifest/事件**里留痕（哪条策略、
    哪个能力、何时）；**未声明允许时仍拒冻**并**点名缺失的策略事实**。在此通道上让
    `sort_analysis_v1`（真实 LLM 驱动 + **既有** Docker 实验后端）跑到**终态**，
    使**实验产物 + 证据 + 预算归账**三项可从读面取到。同时把 GOAL-011 对路径 (B) 的**否证**
    写成一份**独立记录**（登记为「已否证 / 待重新设计」），**不**因本 GOAL 走通 (A) 而抹掉。
    **不放宽 `classify_risk`、不改 `PreflightStatus.WARN` 语义、不让 WARN 无条件可冻、
    不新增依赖、不改上游 pin、不动 Accepted ADR / 核心安全策略 / Canonical State 边界、
    不把真实 runtime 设为默认、不放宽 §9 任一条默认 deny——触及即 BLOCKED。**
exit_criteria:
  - id: EC-01
    criterion: >-
      **冻结门通道（主干，路径 (A)）**：当且仅当「该能力/工具的 **EXECUTE** 风险已被**显式策略声明**
      允许（policy 中有对应 allow 规则且作用域匹配）」时，**预检报告仍含 WARN** 的 run **可以完成
      冻结**，且这次接受在 **manifest / 事件**里**留痕**（哪条策略、哪个能力、何时）；
      **策略未允许 ⇒ 仍拒冻**，且拒绝消息**点名缺哪条策略事实**（不笼统报 WARN）。
      **反证（成对，先红后绿）**：① 把策略允许撤掉 ⇒ **回到拒冻**；② 把留痕去掉 ⇒ 判据**红**。
      **不得**放宽 `classify_risk`（`EXECUTE → HIGH` 逐字不变）；**不得**改
      `PreflightStatus.WARN` 的语义；**不得**让 WARN 无条件可冻。既有 preflight 语义用例
      （`WARN preflight must not contain ERROR findings`、`PASS preflight must not contain ERROR
      findings`、「只有 PASS 才 `passed`」等）必须**保持或增强**，不得削弱。
    verify: >-
      离线定向判据（默认门可跑、零出网）三条同时成立：① **允许通道**——
      策略显式允许的 EXECUTE 能力 ⇒ `run_preflight` 报告**仍为 WARN** 且 `passed is False`、
      但冻结**可完成**（`freeze_manifest` 返回 manifest），且 manifest 与 `manifest.frozen`
      事件里**留痕**含「策略标识 / 能力 / 时刻」三项；② **拒冻反证**——把该策略允许撤掉
      （或换成未声明的能力）⇒ 同一路径**拒冻**且消息**点名**缺的策略事实；③ **留痕反证**——
      去掉留痕字段 ⇒ 对应判据红。三条各自**先红后绿**可复跑（按压记录落 RECHECK）。
      端到端形态（EC-02 的真实 run）：`manifest_digest` **非空** + 事件链里 `manifest.frozen`
      的 payload 含留痕字段 ⇒ 冻结确已发生且可审计。
    status: PASS
    status_note: >-
      2026-09-23 cycle 2 收口：本条 verify 的**最后一项**（EC-02 的真实 run 形态）已由真实一次 run
      满足 ⇒ **PASS**。样张 `scratch/goal012-c2-live-sample.json`：`manifest_digest` 非空，且
      `manifest.frozen` 事件 payload 的 `accepted_policy_exceptions` **4 条**（`code.execute` /
      `workspace.read` / `workspace.write.code` / review 的 `workspace.read`；`decision=ALLOW`、
      `accepted_at` 非空）——冻结确已发生且可审计。
      以下为 cycle 1 的落地与判据记录（保留，不追溯改写）：
      2026-09-23 cycle 1（`PLAN-20260923-140`，提交 `5ae2d56`）：**通道本体已落、判据成对**，
      但按本条 verify 的最后一项（**EC-02 的真实 run 形态**）尚未发生 ⇒ **本 GOAL 不提前记 PASS**。
      ① **落地**：新模块 `packages/application/preflight/policy_acceptance.py`（接受条件四条 +
      留痕七键 + 点名拒冻消息），`freeze_manifest` 接线，`RunManifest.accepted_policy_exceptions`
      （optional，缺省空列表 ⇒ 既有 digest 逐字不变）+ `frozen_payload` 同源同值。
      **`classify_risk` / `PreflightStatus` / `passed` / `_status()` / finding 生成逐字未动**。
      ② **判据（离线，8 passed）**：允许通道 / 拒冻反证（撤允许 ⇒ 点名 `code.execute`）/
      非 EXECUTE 无通道 / 非 `TOOL_RISK_ELEVATED` 不可转换 / PASS 报告不留痕。
      ③ **三处按压（先红后绿）**：留痕置空 ⇒ **2 红**（恰留痕两条）；停用通道 ⇒ **5 红**
      （含三条**点名**断言逐字失败于旧消息）；让任意警示可转换 ⇒ **2 红**（恰两条不可转换面）。
      ④ **端到端（离线、API 级）**：`POST /projects/{id}/runs`（`sort_analysis_v1`）⇒
      `manifest_digest` 非空、事件链里 `manifest.frozen` 的 payload 含 4 条留痕
      （`code.execute` / `workspace.read` / `workspace.write.code` / review 的 `workspace.read`）；
      run 终态仍是 `FAILED`，但**不再死在冻结门**（逐字 `task … produced malformed result:
      session result … carries no structured output`）⇒ 阻断点已消除，剩下的堵点在会话/结构化输出
      （**W-B**，EC-02 的输入）。⑤ **独立复检** `scratch/verify_goal012_c1.py`（只读/只用标准库/
      不 import 仓库代码）**两棵树成对**：当前树 `checked=28 failures=0`；基线树（`ccb8f3e`）
      `checked=22 failures=19` ⇒ 判据不空转，而「不得放宽」的四条在两棵树都绿。⑥ **门**：
      本机 m0 **23/23**（`python/tests` **4403 passed / 18 skipped / 0 failed**）、`validate.py` 绿、
      zero egress（`judged 779; blocked 8` 的 8 条是判据对 `198.51.100.1` 的故意探针）。
      **新登记**：**W-A**（真实控制面对 `sort_analysis_v1` 的 `evidence.read` 判 `DENY` ⇒ 该协议在
      真实控制面上是 `FAIL` 而非 `WARN`；本循环**不**自行放宽策略面）、**W-B**（见上）、
      **W-C**（同一协议在两套装配下结论不同：`FAIL` vs `WARN`，引用时必须写明装配）。
  - id: EC-02
    criterion: >-
      **真实实验执行链**（GOAL-011 EC-03 的原判据）：真实 LLM 驱动 `sort_analysis_v1`
      （**或** `m12_reference_research_v1`）跑到**终态**，**实验产物 + 证据 + 预算归账**可读。
      执行体 = **既有 Docker 后端**（`research-os-sandbox:m9-test`，M9 已 6 容器 E2E），
      **不新增执行后端、不新增依赖**。判据：run 终态**如实记录**（**只有 `SUCCEEDED` 是成功**；
      `FAILED` **不得**写成成功）+ 读面**三项齐备**（`GET /runs/{id}/experiments` 取到实验产物、
      `GET /runs/{id}/evidence` 取到证据、预算归账可读）。若失败，**如实**归类为缺陷并按
      fix_policy 纠错，**不得**把失败写成 PASS；若预算不足未做，如实登记为下一轮输入。
    verify: >-
      `set -a; . ./.env; set +a` 后
      `RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest
      tests/e2e/<EC-02 live 判据文件> -q -rs` ⇒ **PASS（非 skip）**，且落盘样张
      （`scratch/`，**不进仓库**）记录该 run 的 canonical 终态**恰为 `SUCCEEDED`**、
      三项读面可读、终态与判词逐字。跑前自检
      `EnvCredentialResolver().has('LLM_MAIN_KEY') is True`（**只问存在性，不物化值**）。
      反证（先红后绿）：撤掉策略允许 ⇒ 同一路径**拒冻**、run 终止在**执行之前**（零 task /
      零实验 / 零工具观测）。
    status: PASS
    status_note: >-
      2026-09-23 cycle 2（`PLAN-20260923-142`，提交 `dcade8c`）：**PASS**，四条各有实跑证据。
      ① **真实一次 run 到终态**：`set -a; . ./.env; set +a` + 内联
      `RESEARCHOS_AGENT_RUNTIME=openhands` 跑 `tests/e2e/test_ec02_experiment_live.py` ⇒
      **1 passed（非 skip；`judged 2; blocked 0`）**，样张 `scratch/goal012-c2-live-sample.json`：
      `sort_analysis_v1_0_1` / 终态**恰为 `SUCCEEDED`** / 失败面为空；跑前自检
      `EnvCredentialResolver().has('LLM_MAIN_KEY') is True`（只问存在性，未物化值）。
      ② **三项读面齐备**：`GET /runs/{id}/experiments` 取到**恰 1 次实验**（镜像
      `sha256:e95de2424c65…` = 本机 `research-os-sandbox:m9-test`、环境摘要在场、产物
      `analysis_report` / `experiment_result.json` / `stdout.log` / `stderr.log`、指标
      `corpus_size=2048` / `worst_case_comparisons=19960`）；`/evidence` **6 条**（4 条实验制品
      `GENERATED` + review 会话交付物 + **`USER_PROVIDED`** 的声明输入 `sort_analysis_v1`）；
      `/usage` 归账 `MODEL_TOKENS 9738` / `MODEL_REQUESTS 2`（成本如实 `UNKNOWN`，不补 0）。
      ③ **反证（成对，离线可复跑）**：`tests/e2e/test_ec02_experiment_chain_offline.py` 第 2 条——
      撤掉 `code.execute` 的显式允许 ⇒ **拒冻**（`manifest_digest is None`）且**执行前终止**
      （零 task / 零 experiment）。同文件主判据（`requires_docker`，零出网）另把整条链跑到
      `SUCCEEDED` ⇒ 真实 run 不是孤证。
      ④ **本 cycle 撞到并修掉的真缺陷**（一次真实取样换来的）：第一次 live 取样**冻结成功、实验
      真跑了**，却死在 review 会话——`Duplicate tool names found: {'inert'}`（测试侧惰性工具替身
      把两件 provider 注册成同一个类，而 SDK 由**类名**派生工具名）。修法 = 按注册名分名
      （`inert_tool_class_for`），并**新增离线判据** `test_a_two_provider_frozen_set_starts_a_session`
      钉住；**按压**逐字复现 live 死法（`scratch/goal012-c2-press-duplicate.txt`）。
      **W-B 闭合**（空交付物仍如实拒绝：门禁**一字未改**，改的是判据**显式声明**交付物 +
      `with_sandbox_experiment` 的可选 `runtime` 参数，缺省行为逐字不变）。**W-A/W-C 如实保留**
      （真实控制面 `evidence.read` 判 `DENY` ⇒ 该协议在真实控制面上仍是 `FAIL`；本 cycle **未**改
      策略面，脚本 A4 两棵树同结论）。独立复检 `scratch/verify_goal012_c2.py` 两棵树成对：
      当前树 `checked=29 failures=0`；基线树（`c6cf330`）`checked=29 failures=10`（红项恰为本
      cycle 新增面）。
  - id: EC-03
    criterion: >-
      **实验产出的证据链**：实验产物（`stdout.log` / `stderr.log` / metrics / 语义摘要等）
      与**来源记录**进 **canonical**，读面**可追溯**（产物可从 `GET /runs/{id}/experiments`
      或等价的既有读面取到，且其来源/镜像摘要可独立复核）。
      **反证（成对，先红后绿）**：**去掉产物**（或去掉登记它的那一步）⇒ 判据**红**。
      **不得**用模型自述充当实验产物；**不得**把「实验跑过」写成「产物已登记」。
    verify: >-
      定向判据（离线 + 真实容器两向）：产物随 canonical 落库且读面可取（含 digest 可重算）；
      反证：按压掉产物登记 ⇒ 判据红 ⇒ 复原 ⇒ 绿（按压记录落 RECHECK）。
      真实 run 侧：EC-02 的样张里实验产物与证据**同时**在场且指向同一个 run。
    status: PASS
    status_note: >-
      2026-09-23 cycle 3（`PLAN-20260923-144`，提交 `6ccdf46`）：**PASS**，三条各有实跑证据。
      ① **产物进 canonical 且读面可追溯**（判据 `tests/e2e/test_ec03_experiment_evidence_chain.py`，
      离线 + 真实容器，**2 passed**）：四件产物（`analysis_report` / `experiment_result.json` /
      `stdout.log` / `stderr.log`）在 `GET /runs/{id}/experiments` 与 `GET /runs/{id}/artifacts`
      两面都可见；`GET /artifacts/{id}/content` 的字节经 `Digest.of_bytes` 必须等于**证据条目**与
      **来源记录**两条记录各自登记的 `content_digest`（实测 6 件制品逐件通过）；实验记录的
      `image_digest` == **独立查 daemon**（`docker image inspect`，不经产品适配器）的镜像 Id；
      `environment_digest` 非空；canonical **语义摘要**与指标跨两次执行相同（同 seed / 同镜像 ⇒ 同语义）。
      ② **不得用模型自述冒充**：四件产物的证据 `extracted_by == experiment:<run id>`、
      `source_origin` 以 `<experiment_run_id>:` 起头、信任标签是实验路径的 `GENERATED`。
      ③ **成对反证（先红后绿）**：同构脚本改写成**别名字的产物**（`report.txt`）⇒ run `FAILED`、
      判词**点名** `analysis_report` 与 `acceptance gate`、读面上没有 `analysis_report` 而
      `report.txt` / `experiment_result.json` **仍在** ⇒ 红的理由恰是「声明产物缺失」。
      **四处按压全红**（`scratch/goal012-c3-press{1,2a,2b,3}.txt`：去掉产物登记那一步 / 来源记录
      digest 造假 / 证据 digest 造假 / 反证脚本改回写声明产物），产品代码按 `git diff` **逐字复原**。
      **两处判据自身的问题在 cycle 内修掉并如实记录**：先写成「两读面相等」（实测是**子集**关系：
      run 级面还含别的阶段的产物与声明输入）；「只看证据 digest、不看来源记录」的盲点由按压暴露
      ⇒ 判据**加强**为两条记录各算一遍（加强判据，不是放松）。
      ④ **独立复检** `scratch/verify_goal012_c3.py`（只读/只用标准库/不 import 仓库代码）两棵树成对：
      当前树 **24/24**；基线树（`31dfbd4`）**6 红**（恰为判据文件不存在）；**产品件在两棵树同指纹**
      ⇒ 本 cycle **未改任何产品代码**（纯判据 cycle）。样张侧另判「四件产物各有证据 + 指向同一 run」
      （EC-02 的 live 样张，**未重跑真实端点**）。
      ⑤ **门**：m0 **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c3-m0-rerun.log`：
      24 条 `PASS [` 行、无 `FAILED` 行；`python/tests` **4411 passed / 19 skipped / 0 failed**）；
      `tests/e2e` 118 passed / 10 skipped；`mypy` 996 files 干净；首轮两红（未使用的 `import json`、
      50 行/函数门被 80 行主干函数触发）当轮修掉。**零 live 调用、零出网、零凭据读取。**
  - id: EC-04
    criterion: >-
      **残余路径 (B) 的诚实处置**：把 GOAL-011 对路径 (B) 的**否证**写成一份**独立记录**并登记为
      「**已否证 / 待重新设计**」，**不得**因本 GOAL 走通 (A) 就把它抹掉或改写成已完成。
      独立记录必须**逐条覆盖**四项实测事实：
      ① 单 task **非自产来源上限 = 3**（1 份声明输入 + 1 次检索 + 1 次读取）；
      ② **第二次检索调用硬失败**（同一 task 内操作键重复 ⇒ `conflicting source registration`）；
      ③ `minimum_sources: 10` 的**口径**与上述机制**不相容**（量级差）；
      ④ 三条判据维度**无产品调用方**（`SCHEMA_VALID` / `TEST_PASSES` / `POLICY_COMPLIANT`）。
    verify: >-
      独立记录文件在位（仓库相对路径，由子 PLAN 定案并在 GOAL 迭代日志写明载体）；
      其正文**逐条**覆盖四项否证（各带机制与实测出处）；GOAL-011 的 `W-P` / `W-Q` / `PLAN-138`
      的 BLOCKED 状态**原样保留**（不被本 GOAL 改写）；本文件的残余节登记该记录路径。
    status: PASS
    status_note: >-
      2026-09-23 cycle 4（`PLAN-20260923-146`，提交 `830a72c`）：**PASS**。
      ① **载体**（子 PLAN 定案 D-1，迭代日志已写明）：`docs/roadmap/PATH_B_REFUTATION_RECORD.md`
      ——状态逐字「**已否证（refuted）/ 待重新设计（needs redesign）**」+「**不是待办功能，也不是
      已完成**」。② **四项事实逐条**各带「机制」+「实测出处」（**实测出处恰 4 处**）：①上限 3
      ②`conflicting source registration` 硬失败 ③`minimum_sources: 10` 不相容 ④三条判据无产品
      调用方；出处指向 `PLAN-20260922-138` 的 `E-3`/`E-4`/`E-5` 与两个 `scratch/` 探针脚本。
      ③ **只读历史**（两棵树成对证明）：`git diff --stat` 相对 `HEAD` 与相对基线树 `ea06b77`
      **两次都空**（`GOAL-20260922-011` / `PLAN-20260922-138` / `RECHECK-20260923-139`）；
      `W-P`/`W-Q` 原文可查；`PLAN-138` 仍 `status: BLOCKED`。④ **残余节**：`R-B1` 已指向该记录
      （含四项事实摘要 + 「原样保留」句 + 「不得读成待办功能」）。⑤ **两道检查**：
      `docs_consistency_check` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`；`validate.py` ⇒
      `Cursor 治理验证通过`；m0 **23/23**（`python/tests` 4411 passed / 19 skipped，与 cycle 3 同数
      ⇒ 只加文档）。⑥ **独立复检** `scratch/verify_goal012_c4.py` 两棵树成对：当前树
      `checked=24 failures=0`；基线树 `14 红`**全部**是本 cycle 新增面 ⇒ **零产品改动、零改写历史**。
      ⑦ **顺带查出并处置**一处既有记录缺陷：`RECHECK-145` 的「当前树 24/24」测于一次 amend
      **之前**，且复检脚本 B2 钉了判据的中间形态字面量 ⇒ B2 改判语义（四 token，强度只增）、
      复测同结论同数字、`RECHECK-145` 就地追加「勘误」节、事实进 `MEM-20260923-112`。
      **本 cycle 未改任何产品代码/协议/合约/测试/门禁/策略面**；零出网、零凭据读取。
  - id: EC-05
    criterion: >-
      **前端消费实验读面**（**可选**，视预算）：实验页在**真实数据**下渲染实验产物 / 指标。
      若空间不足，**如实登记为下一轮输入**（写明原因），**不得**为它降级 EC-01/EC-02/EC-03。
    verify: >-
      web 门（typecheck / lint / unit / build / stub 或 live e2e）绿 + 真实数据下的读面
      （截图或读面快照落 `scratch/`，**不进仓库、不上传外部服务**）；
      未做 ⇒ GOAL 残余节有一条**如实的下一轮输入**登记。
    status: PENDING
  - id: EC-06
    criterion: >-
      **收口复检 + 残余登记**：独立复检脚本（**当前树 + 干净 checkout 同结论**）+
      本地 m0 全量 **23/23** + 治理 `.cursor/skills/governance-check/scripts/validate.py` 绿 +
      CI 台账逐 run 到终态（**M0 六 job + CodeQL**）；GOAL-008/009/010/011 遗留的人工面
      **13 条原样保留** + 本 GOAL 自己的 **W 列表**。残余**不得**因收口消失。
      **`ANTHROPIC` run 腿仍为可选验证项**（不进退出的标准）。
    verify: >-
      复检脚本多层判据全 PASS 且两棵树同结论（干净树**无 `.env`** ⇒ 凭据类判据**如实 SKIP**，
      不读成通过）；`make validate-all` ⇒ **23/23**；治理 `validate.py` 绿；本文件
      `latest_recheck` 指向**仓库相对路径**的 PASS/PASS_WITH_WARNINGS RECHECK；
      frontmatter 的 EC 状态与 markdown 状态表**一致**（GOAL-006…011 收口时都出过这一类漏改）。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过（**例外**：本 GOAL 的 EC-01 是用户**授权范围内**
      的冻结门改造——它必须带**成对反证**与**留痕判据**，且**不得**削弱既有 preflight 判据；
      这不是「改门凑绿」）
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
  - >-
    **EC-01 的实现若需要放松 AGENTS.md §9 任一条默认 deny 面**（host shell / host home mount /
    Docker socket / privileged container / unrestricted public network / secret enumeration /
    arbitrary credential forwarding / unpinned plugin / package install / destructive workspace
    action / external publish）⇒ **立即 BLOCKED**（本 GOAL 的授权只覆盖冻结门的**接受口径**，
    不覆盖安全默认面）
child_plans:
  - .cursor/plans/tasks/PLAN-20260923-146-path-b-refutation-record.md
  - .cursor/plans/tasks/PLAN-20260923-144-experiment-evidence-chain-traceability.md
  - .cursor/plans/tasks/PLAN-20260923-142-live-experiment-chain-to-terminal.md
  - .cursor/plans/tasks/PLAN-20260923-140-policy-allowed-execute-freeze-gate.md
latest_recheck: null
memory_entries:
  - .cursor/memory/entries/MEM-20260923-112-verifier-token-drift-after-amend.md
  - .cursor/memory/entries/MEM-20260923-111-experiment-evidence-traceability-judge-shape.md
  - .cursor/memory/entries/MEM-20260923-110-multi-provider-session-judge.md
  - .cursor/memory/entries/MEM-20260923-109-freeze-gate-policy-allowance-channel.md
---

# GOAL-20260923-012 — 实验执行链打通（自迭代循环）

本 GOAL 承接 GOAL-20260921-011 以 **BLOCKED** 收口时留下的**唯一实质缺口**：EC-03
（真实实验执行链）停在两条都需要拍板的路径上。用户于 2026-09-23 就 **路径 (A)** 拍板：
**授权把冻结门从「只认 PASS」改为「策略已显式允许的 EXECUTE 可冻结算 PASS」**——
一条**显式、留痕、可审计**的通道，而**不是**放宽风险分类、**不是**让冻结门无条件接受 WARN。

## 目标与退出标准

| EC | 标准 | 验证命令／证据来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **冻结门通道（路径 A）**：策略**显式允许**该 EXECUTE 能力 ⇒ 预检报告仍含 `WARN` 但冻结**可完成**，且 manifest/事件**留痕**（哪条策略、哪个能力、何时）；策略**未允许** ⇒ **仍拒冻**并点名缺失的策略事实；反证成对（撤允许 ⇒ 拒冻；去留痕 ⇒ 判据红）；**不得**放宽 `classify_risk` / **不得**改 `WARN` 语义 / **不得**让 WARN 无条件可冻 | 离线定向判据三条（允许通道 / 拒冻反证 / 留痕反证，各自先红后绿）+ EC-02 真实 run 的 `manifest_digest` 非空与事件留痕 | **PASS**（cycle 2 收口：真实 run 的 `manifest_digest` 非空 + `manifest.frozen` 留痕 **4 条**——见 `status_note`） |
| EC-02 | **真实实验执行链**（GOAL-011 EC-03 原判据）：真实 LLM 驱动 `sort_analysis_v1` 跑到**终态**，**实验产物 + 证据 + 预算归账**三项可读；执行体 = **既有 Docker 后端** | live 判据 **PASS（非 skip）** + 落盘样张（终态恰为 `SUCCEEDED` + 三项读面 + 判词逐字）；反证：撤策略允许 ⇒ 拒冻、run 终止在执行之前 | **PASS**（cycle 2：真实一次 run 终态**恰为 `SUCCEEDED`**、三项读面齐备（实验 / 证据 / 预算）、反证成对——见 `status_note`） |
| EC-03 | **实验产出的证据链**：实验产物与来源记录进 canonical、读面可追溯；反证：**去掉产物** ⇒ 判据红 | 离线 + 真实容器两向判据；按压记录（先红后绿） | **PASS**（cycle 3：两读面同源 + 证据条目与来源记录**两条**的 digest 可重算 + 镜像摘要独立复核 + 语义摘要跨重跑稳定 + 成对反证红且点名——见 `status_note`） |
| EC-04 | **残余路径 (B) 的诚实处置**：把 GOAL-011 对 (B) 的否证（来源上限 3 / 第二次检索硬失败 / `minimum_sources: 10` 口径 / 三条判据无产品调用方）写成**独立记录**并登记「已否证 / 待重新设计」，**不**抹掉 | 独立记录文件在位且逐条覆盖四项；`W-P`/`W-Q`/`PLAN-138` 状态原样保留 | **PASS**（cycle 4：`docs/roadmap/PATH_B_REFUTATION_RECORD.md` + `RECHECK-20260923-146`；四项事实各带机制与实测出处；两棵树成对证明 GOAL-011 / PLAN-138 **一字未改**——见 `status_note`） |
| EC-05 | **前端消费实验读面**（**可选**）：实验页在真实数据下渲染产物/指标；空间不足则**如实**登记为下一轮输入，**不得**降级 EC-01…EC-03 | web 门绿 + 读面快照落 `scratch/`（不进仓库）；未做 ⇒ 有如实登记 | **PENDING** |
| EC-06 | **收口复检 + 残余登记**：独立复检脚本（当前树 + 干净 checkout 同结论）+ m0 **23/23** + 治理 validate 绿 + CI 台账到终态（M0 六 job + CodeQL）；13 条人工面原样保留 + 本 GOAL 的 W 列表；`ANTHROPIC` run 腿仍为可选 | 复检两树同结论；`make validate-all` 23/23；`validate.py` 绿；`latest_recheck` 为仓库相对路径；frontmatter 与状态表一致 | **PENDING** |

### 建档时已探明的现状（事实类，用于判定起点；**不当作验收依据**）

以下为 2026-09-23 建档当日**直接读代码/配置核对**的结论（不是引用历史记录）：

| # | 事实 | 核对方式 | 结论 |
| --- | --- | --- | --- |
| F-1 | **冻结门只认 PASS** | 读 `packages/application/preflight/preflight.py:173-195` | `freeze_manifest` 的 `if not report.passed: raise ManifestFreezeError("cannot freeze manifest before a passing preflight")`；`PreflightReport.passed` 定义为 `self.status is PreflightStatus.PASS`（`packages/domain/protocols.py:326-328`）⇒ **WARN 与 FAIL 同等拒冻** |
| F-2 | **服务侧只对 FAIL 提前失败** | 读 `packages/application/run_orchestration/service.py:138-150` | `if plan is None or report.status.value == "FAIL": return self._fail_run(...)`；随后 `COMPILE_OK` → `PREFLIGHT_OK` → **`freeze_manifest`** ⇒ WARN 的 run 会**走到冻结门才炸**（GOAL-011 cycle 6 实测：`state: FAILED`、`manifest_digest: null`、零 task / 零实验 / 零工具观测） |
| F-3 | **`classify_risk` 对 EXECUTE 无条件 HIGH** | 读 `packages/domain/tools.py:136-150` | `if effect_class in (EffectClass.SECRET_USE, EffectClass.EXECUTE): return RiskClass.HIGH`——**与 trust level 无关**（`BUILT_IN` 也不例外）⇒ 这是 GOAL-011 登记为 W-K 的那条交叉，**本 GOAL 授权不动它** |
| F-4 | **WARN 的唯一来源是 `TOOL_RISK_ELEVATED`** | 读 `packages/application/preflight/checks.py:202-224` | `_provider_trust_findings` 按 `classify_risk(provider.effect_class, provider.trust_level)` 判 `HIGH/CRITICAL` ⇒ 出 **`FindingSeverity.WARNING`** 的 `TOOL_RISK_ELEVATED`（`subject_ref = provider:<id>`）；`_status()` 见任意 WARNING 即 `WARN`（`preflight.py:51-56`） |
| F-5 | **策略面已经显式允许 `code.execute`** | 读 `examples/config/policy.yaml:33-36` | `allow_with_constraints: - capability: code.execute constraints: {sandbox_required: true, max_seconds: 1800}` ⇒ 今天的 `WARN` **不是**策略拒绝，而是**风险分层提示**；`check_policy` 对它返回 `(None, "policy constraints for code.execute: …")`（`packages/application/preflight/policy_check.py:82-98`，`ALLOW_WITH_CONSTRAINTS` 分支不产 finding） |
| F-6 | **能力 → 求值 scope 的映射表不含 `code.execute`** | 读 `packages/application/preflight/policy_check.py:31-50` | `_CAPABILITY_SCOPE` 覆盖 `workspace.read` / `artifact.read` / `artifact.write` / `literature.search` / `literature.read` / `network.academic`；`code.execute` **不在表内** ⇒ 求值 scope 为 `None`（带 `scope:` 的 allow 规则要求相等才匹配；无 scope 的规则不受此限）。该常量与 policy.yaml 的带 scope 规则的**并集一致性有判据锁死**（注释明写） |
| F-7 | **`openhands_workspace` 是那条 EXECUTE provider** | 读 `examples/config/tool_providers.yaml:2-12` | `kind: NATIVE`、`trust_level: BUILT_IN`、`effect_class: EXECUTE`，能力含 `workspace.read` / `workspace.write.notes` / `workspace.write.code` / `code.execute` / `git.diff` ⇒ 每个引用它的 `ToolRequirement` 各出一条 `TOOL_RISK_ELEVATED`（GOAL-011 实测 `sort_analysis_v1` 共 **4 条**，逐字 `provider openhands_workspace has elevated risk class HIGH`） |
| F-8 | **冻结事件 payload 今天没有留痕槽位** | 读 `packages/application/run_orchestration/eventing.py:57-79` | `frozen_payload` 现有键：`run_id` / `digest` / `semantic_digest` / `pricing_version` / `pricing_digest` / `execution_backend` / `runtime_fingerprint` ⇒ **留痕要新增字段**；注释写明「read 面**回读的仍是本 payload**，不另存一份副本」（少一处可漂移的源） |
| F-9 | **`sort_analysis_v1` 的两份合约是夹具级、不在共享目录** | 读 `examples/protocols/sort_analysis_v1.yaml` + `examples/contracts/task_contracts.yaml`（只有 6 份：`domain_discovery` / `experiment_execution` / `m12_experiment_execution` / `console_demo_deliverable` / `real_research_deliverable` / `real_retrieval_deliverable`）+ `tests/api/run_fixtures.py:60-89` | `sort_analysis_execution`（判据 `ARTIFACT_EXISTS: analysis_report`）与 `sort_analysis_review`（判据 `EVIDENCE_COVERAGE: minimum_sources 1`）由**测试夹具**按 `setdefault` 注入目录；live 路径沿用 GOAL-009/010/011 全部真实 run 的既有载体 —— `tests/e2e/live_run_support.py` 的 `preflight_override`（**协议与共享目录零改动**） |
| F-10 | **实验缝已在 live 装配上接线，镜像本机在** | 读 `tests/e2e/live_run_support.py:96-150`（`declare_sandbox_experiment` / `with_sandbox_experiment`）+ 实测 `docker images` | `declare_sandbox_experiment` 给执行阶段合约加 `ExperimentExecutionSpec(script, image)`；`with_sandbox_experiment` 用**既有** `sandbox_experiment_runner` + `docker_experiment_assembly` 接上 `OrchestrationDependencies.experiment_task`；`research-os-sandbox:m9-test`（`e95de2424c65`）**本机在** |
| F-11 | **本机 Docker 可用（Linux 容器）** | 实测 `docker images` | `research-os-sandbox:latest` / `m9-sandbox-v1` / `m9-test` 三个 tag 在；M9 已 6 容器 E2E。**注意**：CI 的 windows 跑者**没有** Linux daemon ⇒ 走真实装配的判据必须挂既有 `requires_docker`（GOAL-011 cycle 6 的 F-f 教训） |

**结论**：EC-01 的起点是一处**已定位、未拍板的门禁口径**——`sort_analysis_v1` 的 `WARN`
**不是因为策略拒绝**（F-5 明写允许），而是 `EXECUTE → HIGH` 的风险提示（F-3/F-4）撞上
「只认 PASS」的冻结门（F-1）。授权把**接受口径**改成「显式允许 + 留痕」的通道，
**不动**风险分类与 WARN 语义。EC-02 的起点是**已经接好的实验缝**（F-10）+ 夹具级合约（F-9）：
**唯一堵点就是 EC-01 那道门**。

### EC-01 判定细则（冻结门通道，路径 (A)）

- **要建立的通道（且仅此一条）**：预检 `WARN` 的 run 在**满足两个条件**时可完成冻结并记为
  `PASS`：① 该 `TOOL_RISK_ELEVATED` 所涉的 **EXECUTE 风险**已被**显式策略声明**允许
  （policy 中有对应 allow 规则、**作用域匹配**，按既有 `PolicyEvaluator` 求值，不另造第二套求值器）；
  ② 这次接受在 **manifest 与 `manifest.frozen` 事件**里**留痕**（哪条策略、哪个能力、何时）。
- **不得做**：放宽 `classify_risk`（F-3 逐字不变）；改 `PreflightStatus.WARN` 的语义；
  让 `WARN` **无条件**可冻（未声明允许仍拒冻）；把 `report.passed` 的语义改宽（**PASS 才 `passed`**
  这条必须保持——通道走的是**冻结门的接受口径**，不是重定义 `passed`）；削弱既有 preflight 判据。
- **拒绝语义点名**：未声明允许时，错误消息必须**点名**缺的策略事实（哪个能力 / 哪个 provider /
  缺哪条 allow 规则），不得只报「WARN」。
- **反证必须成对（先红后绿）**：① 撤掉策略允许 ⇒ **回到拒冻**；② 去掉留痕 ⇒ 判据**红**。
  只有绿没有红 ⇒ **判据没在看**。
- **成功面（真实形态，落在 EC-02）**：真实 run 的 `manifest_digest` **非空** +
  事件链里 `manifest.frozen` payload 含留痕 ⇒ 冻结发生且可审计。
- **不放松 §9**：本通道**不得**以任何形式依赖或放宽 AGENTS.md §9 的默认 deny 面
  （host shell / Docker socket / package install / 无限制公网 …）；**需要放松即 BLOCKED**。

### EC-02 判定细则（真实实验执行链）

- 执行体 = **既有 Docker 后端**（F-10）；**不新增执行后端、不新增依赖**。
- 终态**如实记录**：只有 `SUCCEEDED` 是成功；`FAILED` **不得**写成成功。
- **预算不足时**：如实登记为**下一轮输入**（写明原因与代价），**不得**记 PASS，
  且**不得**为腾预算而降级 EC-01 / EC-03。
- **live 步骤只以单条命令的内联前缀**开：

      set -a; . ./.env; set +a
      RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest tests/e2e/<EC-02 live 文件> -q -rs

  跑前确认 `EnvCredentialResolver().has('LLM_MAIN_KEY') is True`；**跑后不得把开关留在环境或 `.env`**。

### EC-03 判定细则（实验产出的证据链）

- 实验产物（`stdout.log` / `stderr.log` / metrics / 语义摘要）与其**来源**必须进 **canonical**，
  读面可追溯（含 digest 可独立重算）；**不得**用模型自述或装配方自报充当实验产物。
- **反证成对**：去掉产物（或去掉登记它的那一步）⇒ 判据**红** ⇒ 复原 ⇒ 复绿。

### EC-04 判定细则（残余路径 (B) 的诚实处置）

- **独立记录**的载体由子 PLAN 定案并在迭代日志写明（允许落 `.cursor/memory/entries/` 或
  `.cursor/plans/` 下的独立记录文件）；内容**逐条**覆盖四项否证（各带机制与实测出处）。
- **不修改** GOAL-011 / `PLAN-20260922-138` / `RECHECK-20260923-139` 的既有正文
  （GOAL-001…011 只读）；本 GOAL 只在**自己的**残余节登记该记录路径。

### EC-05 判定细则（前端消费实验读面，可选）

- **可选**，不阻塞 EC-01…EC-04；未做时必须留下**如实的下一轮输入**，不得含糊。
- 允许在本机启动控制面 / 前端并操作 UI（**仅本机**）；截图/快照落 `scratch/`、
  **不进仓库**、**不上传任何外部服务**。

### EC-06 判定细则（收口复检 + 残余登记）

- 独立复检脚本：**只读 / 只用标准库 / 不 import 仓库代码**（形态承
  `scratch/verify_goal011_closeout.py`）；**两棵树同结论**（当前树 + `git clone --depth 1`
  到**仓外**的干净 checkout）。干净树**没有 `.env`** ⇒ 凭据类判据**如实 SKIP**（不读成通过）。
- **判据不得空转绿**：收口**之前**的树必须能判红（反证成立）。
- 治理 `validate.py` 绿；`make validate-all` **23/23**；`latest_recheck` 指向**仓库相对路径**的
  PASS/PASS_WITH_WARNINGS RECHECK；frontmatter 的 EC 状态与 markdown 状态表**一致**。
- **残余不得因收口消失**：GOAL-008/009/010/011 的**人工面 13 条**（见下节）+ 各 RECHECK 的 W 列表
  （`W-L`…`W-R`）+ 本 GOAL 自己的 W 列表。

### 建档时登记的残余（不得因本 GOAL 存在而被读成已解决）

- **R-M1（Mimosa 钩子侧）**：**钩子侧 `scanner_enobufs` 未得完整结论** ⇒ **不得**据此宣称
  项目安全；MCP 侧深扫可跑通（GOAL-004 的既有口径），本 GOAL 沿用，不重开扫描面。
- **R-D1（依赖告警）**：`push` 输出暴露 **23 条 Dependabot 告警**（**4 high / 13 moderate / 6 low**），
  **既有未处置**。本 GOAL **不**处置（依赖 pin 变更命中 `escalation_triggers`），只如实登记；
  若后续需要处置，走用户/ADR 拍板。
- **R-B1（路径 (B)）**：GOAL-011 对 (B) 的否证 → **已由 EC-04 落成独立记录**：
  `docs/roadmap/PATH_B_REFUTATION_RECORD.md`（载体由 `PLAN-20260923-146` 定案）。逐条覆盖四项实测事实
  （单 task 非自产来源上限 3 / 第二次检索调用硬失败 `conflicting source registration` /
  `minimum_sources: 10` 与机制不相容 / `SCHEMA_VALID`·`TEST_PASSES`·`POLICY_COMPLIANT` 无产品调用方），
  并声明与 GOAL-011 的 `W-P` / `W-Q` / `PLAN-138` 的 BLOCKED **原样保留**的关系。
  引用时仍按 **「已否证 / 待重新设计」**，不得读成待办功能。
- **R-N1（非 ASCII 路径）**：30 条已跟踪路径含非 ASCII（AGENTS.md §13）⇒ 按「既有历史路径
  不批量重命名」**登记为豁免**；若判定需要 ADR，则**产出草案**、不自行改判。
- **W-A（cycle 1 新，未修）**：**真实控制面**的 preflight 求值是 `NativePolicyEvaluator` +
  `examples/config/policy.yaml`，而该策略**未放行** `sort_analysis_v1` 的 `evidence.read`
  ⇒ 该协议在真实控制面上是 **`FAIL`**（不是 `WARN`）⇒ 通道不会被走到。本循环**不**自行放宽
  策略面（那是放宽安全面，需用户/ADR 拍板）；EC-02 若要走真实控制面必须先处置这一条。
- **W-B（cycle 2 闭合）**：run-ready 装配下 `sort_analysis_v1` 冻结**之后**曾收敛 `FAILED`，
  逐字判词 `task … produced malformed result: session result for task … carries no structured
  output`。根因已定位为**共享夹具的受控执行体不声明任何交付物**，而 `register_session_result`
  对空交付物**如实拒绝**（既有语义，**一字未改**）。处置：离线判据**显式声明**交付物；
  `with_sandbox_experiment` 增**可选** `runtime` 参数（缺省沿用既有执行体）；
  `make_run_ready_deps` 的缺省 runtime **未动** ⇒ 共享夹具的失败形态不变。
  **本条闭合**（真实一次 run 已跑到 `SUCCEEDED`）。
- **W-E（cycle 2 新，已修）**：冻结集含**两件** provider 时，测试侧惰性工具替身把两者注册成
  同一个类，而 SDK 由**类名**派生工具名 ⇒ 会话创建即失败（`Duplicate tool names found:
  {'inert'}`，零模型调用）。修法 = 按注册名分名 + 新增离线判据（mock 端点 + `map_tools=True`）
  钉住；**按压**逐字复现 live 死法（`scratch/goal012-c2-press-duplicate.txt`）。
  详见 `MEM-20260923-110`。
- **W-C（cycle 1 新，登记口径差异）**：同一个协议在**两套装配**下结论不同——run-ready/live 装配
  （`preflight_override` + 默认放行的 Fake 求值器）给 `WARN`；真实控制面给 `FAIL`。引用
  「该协议今天是 WARN/FAIL」时**必须写明是哪一套装配**（`MEM-20260923-109` 记了这条）。
- **W-D（cycle 1 新，登记）**：4 条**跨套件顺序**失败（`test_worker_plane_composition`×3 +
  `test_pg_crash_restart`）在合并跑里出现、**单独跑全绿**；与本次改动无关（既有签名，
  GOAL-011 亦登记过同类），本 GOAL 不改它们。

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
按**未发生**处理。live 调用（真实 LLM、真实检索、真实实验容器）**次数取最小必要**：
同一 EC 不重复跑；能复用既有样本的不另发调用。

**EC-01 的成对反证纪律**：本 GOAL 的 ① 是**授权范围内的门禁改造**，因此**每一条**新判据都必须
带**按压记录**（先红后绿）；「判据绿」不足以记 PASS——必须同时给出「撤掉通道的关键件 ⇒ 红」。

## 驱动

- owner：`root-agent`；进入 cycle 时在迭代日志声明 `driver=client-goal / owner=root-agent`。
- 另一驱动已持有未收口的 ACTIVE cycle 时**等待**，不并发双写。
- 客户端自带的迭代/重试/超时上限**一律让位于**本文件 frontmatter 的 budget / fix_policy。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；用 Plan Mode 流程写
  子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加 `parent_goal: GOAL-20260923-012` 并投影
  `ALL_PLAN`，**同一提交**）。GOAL 迭代日志登记子 PLAN 路径。**live 类 EC 的子 PLAN 必须先写清
  「判据 + 失败如何落终态 + 反证形态」再跑**。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查规模门禁（**50 行函数 / 450 行文件**）与快照类门禁（OpenAPI / 设计基线），
  再跑 `make validate-all`（m0 全量 23 项）+ 受影响定向套件 + web 门（tsc/eslint/unit/build/stub/live e2e）。
  **默认门一律离线**；`tests/egress_guard.py` 是**结构判据**——**不得为了跑通放宽它**；
  **真实调用类用例必须挂 `requires_live_llm`（或同一放行面）才可出网**。
  本机全量门的 CI 同形前提（GOAL-011 的 W-O 教训）：**钉住测试 DSN + 其余 DSN 键空 +
  `LLM_MAIN_KEY=""`**（litellm 导入期 `load_dotenv` 会把操作者 `.env` 带进进程）。
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

**撤回纪律（承 GOAL-011 cycle 10）**：改动共享契约（协议 / 合约 / 夹具语义 / 门禁）时，
**先数清谁拿它的失败形态当夹具**；若 CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**，
而不是改那批夹具迁就。撤回复核用逐字节 `git diff` 证明。

**凭据自检（每轮，硬要求）**：任何记录/日志/回显中都**不得**出现 key 值或片段；发现泄露
（**即使是可弃用的免费额度**）立即**停止并报告**，按 escalation 处置。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先，禁改断言迁就** |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、**凭据可得性驱动的环境签名**） | 按 `docs`/记忆中的既有配方重跑（**先确认环境与 CI 同形**）；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |
| **live 面（本 GOAL 特有）** | live 用例在 CI 上 skip 是**预期**（CI 离线、无凭据） | **不**为让 CI「看到 live」而把凭据塞进 CI；live 证据**只在本地实跑产生**并落 RECHECK |
| **出站判据（本 GOAL 特有）** | `egress guard: FAIL — … non-loopback destination(s)` | **先判是否判据本身在正确地挡**：默认门出现真实出站**就是红**，**修源头**（把出网挪进 `requires_live_llm` 放行面 / 用既有预热路径），**不**改判据、**不**改放行面语义 |
| **门禁口径改动（本 GOAL 特有）** | EC-01 的改动打红了既有 preflight/冻结语义用例 | **不得**改那批断言迁就；先判断是「既有语义被削弱」还是「夹具拿旧形态当契约」——前者回退设计，后者按**撤回纪律**处理并把冲突登记为**要一次决定**的项 |

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 + EC-06 全 PASS 且**有实跑证据**（EC-05 可选；未做须有如实登记）+
  收口 RECHECK（独立复检，`result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck`
  指向该 RECHECK（**仓库相对路径**）+ 「终止与收口」写明收口结论（含仍未处理项）。
  **EC-02 的实跑证据不可替代**：本 GOAL 的存在理由就是让实验协议**真的跑到终态**，
  因此**不存在**「通道建好但从未跑过真实 run 仍可 ACHIEVED」的退路——若凭据/出网/容器不可用
  导致 live 无法发生，**停止并记 `BLOCKED`（能力边界）**，**不**把 skip 写成完成。
  **可选验证项（`ANTHROPIC` run 腿）不参与 ACHIEVED 判定。**
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、或命中
  `escalation_triggers`（含**明文凭据泄露**、**放宽验收门**、**放宽出站判据**、
  **EC-01 的实现需要放松 §9 任一条默认 deny**、改动 Canonical State 边界、把真实 runtime 设为默认、
  新增依赖、Accepted ADR），或**凭据/出网/容器不可用**导致 live 采样无法发生。
  写 BLOCKED 记录（原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），
  恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」**如实登记**为后继入口（**不隐藏缺口**），并给出恢复条件。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED
（承自 GOAL-008/009/010/011，作为残余保留；第 3 项与第 12 项已在本 GOAL 之前执行完毕）：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——归用户拍板。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板。
3. **`artifacts/` token 清理**——涉及不可变历史资产与凭据面，需人工确认。
   **【GOAL-011 的例外】已获删授权**；**建档当日实测结论：该目标已不在工作树上，无需动作**
   （`artifacts/钻孔官方API_v12` 不存在、`git ls-files artifacts/` = 0）⇒ **本项已完成**。
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险，需人工决定。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——上游 pin 变更，需用户或 ADR 拍板
   （含 `R-D1` 的 23 条 Dependabot 告警）。
6. **hook 侧 L3 门**——治理面，需人工决定。
7. **把真实 runtime 设为默认**——默认必须仍是 Fake；本循环只做「显式配置才启用」。
8. **为 anthropic 形态引入 SDK / 新依赖**——优先用手写 HTTP；需要新依赖即 BLOCKED。
9. **把凭据写进 CI**（哪怕是为了让 CI 里看到 live 或检索分支）——**本循环明文禁止**；CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——涉及 Domain 面与可能的
    Canonical State 边界，需拍板。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——本 GOAL 明文禁止；这是「把门改成不挡路」。
    （**注意**：EC-01 是**冻结门的接受口径**改造，由用户显式授权，**不属于**本项。）
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本）**——**【GOAL-011 的例外】
    已获删授权并在建档当日执行完毕**（核对后零仓库影响）⇒ **本项已完成**。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**——**【本 GOAL 的处置】
    登记为豁免，不改判**：按 AGENTS.md §13 明文「既有历史路径不会仅为满足本规则而批量重命名」
    的口径，本 GOAL **不**批量重命名；若判定需要 ADR，则**产出 ADR 草案**、**不自行改判**。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `<建档提交>`（见下方 CI 台账尾巴） | 治理 `validate.py` 绿（建档后实跑） | 见下方 CI 台账 | — | EC-01…EC-06 全 PENDING；起点已定位（**F-1…F-11**：堵点是「冻结门只认 PASS」×「`EXECUTE → HIGH` 风险提示」的**口径交叉**，而**策略面早已显式允许 `code.execute`**；实验缝与镜像**都已就绪**）。**建档时登记的残余**：`R-M1`（Mimosa `scanner_enobufs` 未得完整结论 ⇒ 不得宣称安全）、`R-D1`（23 条 Dependabot 告警：4 high / 13 moderate / 6 low，既有未处置）、`R-B1`（路径 (B) 已否证，待 EC-04 落独立记录）、`R-N1`（30 条非 ASCII 路径登记豁免） | cycle 1 = derive **EC-01** 子 PLAN（冻结门通道）：先定案「策略事实的判据形态」（哪条 allow 规则算数、scope 如何匹配）+「留痕的落点」（manifest 字段 / 事件 payload）+「拒冻消息如何点名」，再落判据与按压 |

| 1 | PLAN-20260923-140（EC-01） | `5085bc2`（derive：PLAN-140 + ALL_PLAN + `child_plans`）、`5ae2d56`（WP1–WP3：通道本体 + 判据 + 三处夹具重钉）、本 cycle 的收口回写见台账尾巴 | **离线判据 8 passed**（新文件，含按压）；**三处按压** 2 / 5 / 2 条红（`scratch/goal012-c1-press{1,2,3}.txt`）；**端到端（API 级）**：`sort_analysis_v1` 的 run 冻结成功（`manifest.frozen` payload 含 4 条留痕）且终态不再死在冻结门；**独立复检** `scratch/verify_goal012_c1.py` 两棵树成对（**当前树 28/28；基线树 19 失败**）；**m0 23/23**（`python/tests` **4403 passed / 18 skipped / 0 failed**，`judged 779; blocked 8` 的 8 条是故意探针）；`validate.py` / `ruff` / `ruff format --check` / `mypy` / 规模门禁全绿；**零出网** | 见下方 CI 台账 | **一处真回归**（本 cycle 自己撞到并处置）：`test_failed_run_semantic_digest_api.py` 拿 `sort_analysis_v1` 当「永不冻结」的载体 ⇒ 把该 fixture 的允许**撤掉**（`code.execute` 判 `DENY`）⇒ 边界语义（没有 `manifest.frozen` ⇒ 引用必须是 None）被**更精确**地钉住，而不是删掉它。另 4 条红（`test_worker_plane_composition`×3 + `test_pg_crash_restart`）**单独跑 7 passed** ⇒ 既有跨套件顺序签名，与本 cycle 无关 | **EC-01 仍 PENDING**（只差 EC-02 的真实 run 形态；不提前记 PASS）。**新登记 W-A/W-B/W-C**（见残余节）。**既有判据的处置**：`test_runs_api` 与 `test_sandbox_experiment_reachability` 按 D-5 **重钉为新语义 + 原位保留成对反证**——**不是**「改断言迁就」（被测行为本身是被授权的目标） | cycle 2 = **EC-02**（真实实验执行链）：以 `sort_analysis_v1` + `with_sandbox_experiment` 跑真实 LLM（最小必要次数）+ **既有** Docker 后端到终态，判据 = 终态如实（只有 `SUCCEEDED` 是成功）+ 三项读面齐备；**先解 W-B**（会话/结构化输出那条堵点），**W-A 若挡路则登记为需拍板项、不自行放宽策略面** |

| 2 | PLAN-20260923-142（EC-02） | `dcade8c`（同一提交：PLAN-142 + ALL_PLAN 投影 + `child_plans` + 两个判据 + 两件 provider 的会话面修复）、本 cycle 的收口回写见台账尾巴 | **离线全链 2 passed**（主判据 + 成对反证；`requires_docker`，零出网）；**真实一次 run 1 passed**（`judged 2; blocked 0`，样张 `scratch/goal012-c2-live-sample.json`：终态**恰为 `SUCCEEDED`**、4 条留痕、1 次实验含 `analysis_report` + 镜像 `sha256:e95de2424c65…`、6 条证据含 `USER_PROVIDED` 声明输入、`MODEL_TOKENS 9738`）；**离线复现 live 死法**（两件 provider 的会话面，按压逐字红：`Duplicate tool names found: {'inert'}` + mock 端点零请求）；**m0 终局 `PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c2-m0-final.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`，无 `FAILED` 行）；**独立复检** `scratch/verify_goal012_c2.py` 两棵树成对（**当前树 29/29；基线树 10 失败**，红项恰为本 cycle 新增面；「不得放宽」七条两棵树同结论）；`tests/e2e` 116 passed / 10 skipped、`tests/api`+`tests/application` 1212 passed / 1 skipped、`python/tests` **4408 passed / 19 skipped / 0 failed**、`mypy` 995 files 干净；**零出网** | 见下方 CI 台账 | **一处真缺陷（本 cycle 一次真实取样换来的）**：测试侧惰性工具替身把两件 provider 注册成同一个类，而 SDK 由**类名**派生工具名 ⇒ 两件同名 ⇒ 会话建不起来（冻结成功、实验已跑完，死在 review 会话）。处置 = 按注册名分名 + **新增离线判据**钉住（mock 端点 + `map_tools=True`），**不是**改断言迁就。**首轮 m0 另有一处红**：新判据的 `dict[str, dict[str, str]]` 与 `dict[str, object] \| None` 类型不兼容 ⇒ 加显式标注（`mypy` 995 files 干净）。离线判据第一次失败也如实保留：指标名按**被执行的脚本**（`sort_analysis_baseline.py` 的 `corpus_size` / `worst_case_comparisons`）重钉 | **EC-01 / EC-02 双双 PASS**（EC-01 的最后一项 = 真实 run 的留痕形态，已由本 cycle 的 live 样张满足）。**W-B 闭合**（空交付物仍如实拒绝；改的是判据显式声明交付物 + `with_sandbox_experiment` 的可选 `runtime` 参数）。**W-A 仍登记**（真实控制面对 `evidence.read` 判 `DENY`；本 cycle 未改策略面）→ 需拍板。**W-C 口径提醒**保留 | cycle 3 = **EC-03**（实验产出的证据链 + 成对反证：去掉产物 ⇒ 判据红）：把 live 样张里的实验产物 / 来源记录 / 镜像摘要做成**可在两棵树上复跑的判据**，并让「来源可独立复核」这一条有独立脚本；EC-04 的路径 (B) 记录与 EC-06 的收口重检在其后 |
| 3 | PLAN-20260923-144（EC-03） | `6ccdf46`（同一提交：PLAN-144 + ALL_PLAN 投影 + `child_plans` + EC-03 判据）、本 cycle 的收口回写见台账尾巴 | **EC-03 判据 2 passed**（离线 + 真实容器；`judged 2; blocked 0`）；**四处按压全红**（`scratch/goal012-c3-press{1,2a,2b,3}.txt`）后产品代码逐字复原；**独立复检** `scratch/verify_goal012_c3.py` 两棵树成对（**当前树 24/24；基线树 6 红＝判据文件不存在**；**产品件两树同指纹 ⇒ 未改产品代码**）；**m0 `PASS: profile=m0; 23 deterministic checks`**（`python/tests` **4411 passed / 19 skipped / 0 failed**）；`tests/e2e` 118 passed / 10 skipped；`mypy` 996 files 干净；零出网 | 见下方 CI 台账 | **两处判据自身的问题当轮修掉并如实记录**：①「两读面相等」写错（实测是**子集**关系：run 级面还含 review 会话的 `review_decision` 与组合根种入的声明输入）⇒ 改子集方向；②「只看证据 digest、不看来源记录」的盲点**由按压暴露** ⇒ 判据**加强**为两条记录各算一遍；首轮 m0 两红（未使用的 `import json`、50 行/函数门被 80 行主干函数触发）⇒ 删 import + 主干拆成 4 个 ≤50 行判据函数（断言逐条未减） | **EC-03 PASS**（产物 + 来源进 canonical、读面可追溯、镜像摘要可独立复核、语义摘要跨重跑稳定；成对反证红且点名）。**本 cycle 纯判据、未改产品代码**。**W-A/W-C 仍登记**（真实控制面 `evidence.read` 判 `DENY` ⇒ 需拍板） | cycle 4 = **EC-04**（路径 (B) 的独立否证记录）：把 GOAL-011 对 (B) 的四项实测事实（单 task 非自产来源上限 3、第二次检索调用硬失败、`minimum_sources: 10` 口径、三项无产品调用方的判据）落成**独立记录**并登记「已否证 / 待重新设计」；其后 EC-05（可选前端）与 EC-06（收口重检 + 干净 checkout 同结论 + CI 台账终态） |

| 4 | PLAN-20260923-146（EC-04） | `830a72c`（同一提交：PLAN-146 + `ALL_PLAN` 投影 + `child_plans` + 记录正文 + 残余节登记 + `RECHECK-145` 勘误 + `MEM-20260923-112`）、本 cycle 的收口回写见台账尾巴 | **记录正文**：`docs/roadmap/PATH_B_REFUTATION_RECORD.md`（状态逐字「已否证 / 待重新设计」，标明**不是**待办功能、也**不是**已完成；四项事实各带「机制」+「实测出处」，`**实测出处**` 恰 4 处）；**只读证明**：相对 `HEAD` 与相对基线树 `ea06b77`，`GOAL-20260922-011` / `PLAN-20260922-138` / `RECHECK-20260923-139` 的 `git diff --stat` **两次都空**，`W-P`/`W-Q` 原文可查、`PLAN-138` 仍 `status: BLOCKED`（`scratch/goal012-c4-readonly.txt`）；**独立复检** `scratch/verify_goal012_c4.py` 两棵树成对（**当前树 24/24；基线树 `ea06b77` 14 红＝**全部**是本 cycle 新增面**）；**m0 `PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c4-m0.log`；`python/tests` **4411 passed / 19 skipped / 0 failed**，与 cycle 3 同数 ⇒ 只加文档）；`DOCS-CHECK PASS: 6 deterministic checks`；`validate.py` ⇒ `Cursor 治理验证通过`；出站 `judged 787; blocked 8`（**8 条全部**来自故意探针 `tests/architecture/python/test_default_egress_guard.py`） | 见下方 CI 台账 | **顺带查出并处置的既有记录缺陷**（勘误；**不是**本 cycle 引入）：`RECHECK-145` 的「当前树 24/24」是**在 amend 之前**测的，而 cycle 3 的复检脚本把判据的**中间形态字面量**钉住（`"Digest.of_bytes(content)"`）——amend（`919ad2c` → `6ccdf46`，由 m0 的 **50 行/函数**门禁驱动的**纯重构**：内容 digest 两行并一行）之后该检查变红。处置：B2 改判**语义**（四个 token 同时在场，强度**只增不减**）、复测**同结论同数字**（当前树 24/24、基线树 `31dfbd4` 6 红）、`RECHECK-145` 就地追加「勘误」节（**保留原行** + 标明测量时点）、事实进 `MEM-20260923-112`；**被检的判据文件一字未改**，cycle 3 的 PASS 结论不变 | **EC-04 PASS**（(B) 的否证已**独立成文**：四项事实逐条 + 与 `W-P`/`W-Q`/`W-R` 及 `PLAN-138` 的 BLOCKED **原样保留**的关系 + 「重新设计需要什么」5 条列为**需拍板**项）。**本 cycle 只加文档与登记**：零产品代码/协议/合约/测试/门禁改动、零出网、零凭据读取。**W-A/W-C 仍登记**（真实控制面对 `evidence.read` 判 `DENY` ⇒ 需拍板） | cycle 5 = **EC-05**（可选前端：实验读面在**真实数据**下渲染产物/指标；空间不足则**如实**登记为下一轮输入，**不得**为它降级 EC-01…EC-04）；随后 cycle 6 = **EC-06** 收口重检（当前树 + **干净 checkout** 同结论 + m0 **23/23** + CI 台账到终态 + 13 条人工面与本 GOAL 的 W 列表**原样保留**） |
### CI 台账（逐 run 逐 job 实查；全部落在 main）| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-012 落地） | `ccb8f3e` | M0 [35817237386](https://github.com/Eswink/research-system-new/actions/runs/35817237386) | 六 job 全 **success**（`console-frontend` / `container-quality` / `collector-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate`，逐 job 实查，终态 `completed`）；**同一次推送另触发 CodeQL** [35817236465](https://github.com/Eswink/research-system-new/actions/runs/35817236465) = **success**（3/3） |
| cycle 1 派生（PLAN-140 + ALL_PLAN + `child_plans`） | `5085bc2` | 与下一条**同一次推送**（GitHub 只对 tip 触发一个 run）⇒ 该提交的验证由下一行承担 |
| cycle 1 WP1–WP3（通道本体 + 判据 + 三处夹具重钉） | tip `5ae2d56` | M0 [35820350936](https://github.com/Eswink/research-system-new/actions/runs/35820350936) | 六 job 全 **success**（`container-quality` / `console-frontend` / `quality-windows-latest` / `collector-quality` / `eval-gate` / `quality-ubuntu-latest`，逐 job 实查，终态 `completed`）；**CodeQL** [35820350713](https://github.com/Eswink/research-system-new/actions/runs/35820350713) = **success**（3/3：`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)`） |
| 台账尾巴（cycle 1 回写） | 见 cycle 1 回合汇报（**台账尾巴口径**：本条自身触发的 run 在回合汇报里给出终态，**不再回写文件**；cycle 1 尾巴 `c6cf330` 的 M0/CodeQL 均 success） | | |
| cycle 2 派生 + WP1–WP3（两个 EC-02 判据 + 两件 provider 的会话面修复） | `dcade8c` | 与下面 cycle 2 回写**同一次推送**（GitHub 只对 tip 触发一个 run）⇒ 该提交的验证由下一行承担 | |
| 台账尾巴（cycle 2 回写） | 见回合汇报（**台账尾巴口径**：本条自身触发的 run 在回合汇报里给出终态，**不再回写文件**） | | |
| cycle 3 派生 + WP1–WP2（EC-03 判据 + 四处按压） | `6ccdf46` | 与下面 cycle 3 回写**同一次推送**（GitHub 只对 tip 触发一个 run）⇒ 该提交的验证由下一行承担 | |
| 台账尾巴（cycle 3 回写） | 见回合汇报（**台账尾巴口径**：本条自身触发的 run 在回合汇报里给出终态，**不再回写文件**） | | |
| cycle 4 记录（记录正文 + `ALL_PLAN` 投影 + `child_plans` + 残余节登记 + `RECHECK-145` 勘误 + `MEM-112`） | `830a72c` | M0 [35840577534](https://github.com/Eswink/research-system-new/actions/runs/35840577534) | 六 job 全 **success**（`container-quality` / `console-frontend` / `quality-windows-latest` / `quality-ubuntu-latest` / `collector-quality` / `eval-gate`，逐 job 实查，终态 `completed`）；**同一次推送另触发 CodeQL** [35840577991](https://github.com/Eswink/research-system-new/actions/runs/35840577991) = **success**（3/3：`Analyze (python)` / `Analyze (actions)` / `Analyze (javascript-typescript)`） |
| 台账尾巴（cycle 4 回写） | 见回合汇报（**台账尾巴口径**：本条自身触发的 run 在回合汇报里给出终态，**不再回写文件**） | | |

**台账尾巴口径**（沿用 GOAL-005…011，写死在此）：写下**本条**「CI 台账回写」提交自身触发的 run
在**回合汇报**里给出终态，**不再回写文件**。

## 状态历史

- 2026-09-23：**建档**（`status: ACTIVE`）。承用户当日 goal 模式指令：**路径 (A) 拍板**——
  授权把冻结门从「只认 PASS」改为「策略已显式允许的 EXECUTE 可冻结算 PASS」，作为一条
  **显式、留痕、可审计**的通道（不放宽 `classify_risk`、不让 WARN 无条件可冻）。
  建档当日**直接读代码/配置**核对得到 F-1…F-11（**不当作验收依据**），其中三条是本次定题的关键：
  **F-5**（`examples/config/policy.yaml` 早已 `allow_with_constraints: code.execute` ⇒ 今天的 WARN
  是风险提示、不是策略拒绝）、**F-1/F-2**（WARN 会一路走到 `freeze_manifest` 才炸）、
  **F-9/F-10**（`sort_analysis_v1` 的合约由夹具注入、实验缝与 `research-os-sandbox:m9-test` 已就绪）
  ⇒ **唯一堵点就是那道门**。EC-01…EC-06 全 PENDING；`child_plans` / `memory_entries` 为空（收口时对齐）。
  **建档时登记的残余**：`R-M1` Mimosa 钩子侧 `scanner_enobufs` 未得完整结论（**不得**宣称项目安全）、
  `R-D1` 23 条 Dependabot 告警（4 high / 13 moderate / 6 low，既有未处置、本 GOAL 不处置）、
  `R-B1` 路径 (B) 已否证待 EC-04 落独立记录、`R-N1` 30 条非 ASCII 路径按 AGENTS §13 登记豁免。
- 2026-09-23（**cycle 1 收口**）：**EC-01 的通道本体落地**（`PLAN-20260923-140` → **DONE**，
  提交 `5085bc2`（derive）+ `5ae2d56`（WP1–WP3）；复检 `RECHECK-20260923-141` = **PASS_WITH_WARNINGS**；
  工程记忆 `MEM-20260923-109`）。
  **落地形态**：新模块 `packages/application/preflight/policy_acceptance.py`（接受条件**四条**
  + 留痕**七键** + 点名拒冻消息），`freeze_manifest` 接线；`RunManifest.accepted_policy_exceptions`
  是 **optional 字段**（缺省空列表 ⇒ 既有 manifest 的字节与 digest **逐字不变**），
  `frozen_payload` 带**同一份**留痕（读面回读的就是它）。
  **授权边界逐条实测未动**：`classify_risk`（EXECUTE ⇒ HIGH 无条件）、`PreflightStatus`、
  `PreflightReport.passed`、`_status()`、finding 生成与严重级。
  **判据与反证**：离线判据 **8 passed**；三处按压 **2 / 5 / 2** 条红（留痕置空 / 停用通道 /
  任意警示可转换），其中停用通道那一次是三条**点名**断言逐字失败于旧消息 ⇒ 「拒绝语义点名缺哪条
  策略事实」真的被判据看着；独立复检脚本 `scratch/verify_goal012_c1.py`（只读/只用标准库/
  不 import 仓库代码）**两棵树成对**：当前树 **28/28**、基线树（`ccb8f3e`） **19 失败**。
  **端到端（离线、API 级）**：`sort_analysis_v1` 的 run 冻结成功、`manifest.frozen` payload 含
  **4 条**留痕（`code.execute` 在列）；run 终态仍 `FAILED` 但**不再死在冻结门**。
  **如实登记四处残余**：**W-A** 真实控制面对该协议的 `evidence.read` 判 `DENY` ⇒ 真实控制面上
  是 `FAIL` 而非 `WARN`（**本循环不自行放宽策略面**）；**W-B** 冻结后的堵点移到「会话结果的结构化
  输出」；**W-C** 同一协议在两套装配下结论不同（引用必须写明装配）；**W-D** 4 条跨套件顺序失败
  单独跑全绿（既有签名）。**本 cycle 未放宽任何判据/放行面、零真实出网、零凭据读取。**
  **CI 终态**：tip `5ae2d56` 的 M0 [35820350936](https://github.com/Eswink/research-system-new/actions/runs/35820350936)
  **六 job 全 success**、CodeQL [35820350713](https://github.com/Eswink/research-system-new/actions/runs/35820350713)
  **3/3 success**（逐 job 实查，终态 `completed`）。**GOAL 仍 ACTIVE**（**EC-01 PENDING**——
  只差 EC-02 的真实 run 形态；EC-02…EC-06 未完）。
- 2026-09-23（**cycle 2 收口**）：**EC-01 与 EC-02 双双 PASS**（`PLAN-20260923-142` → **DONE**，
  提交 `dcade8c`；复检 `RECHECK-20260923-143` = **PASS**；工程记忆 `MEM-20260923-110`）。
  **真实一次 run**（`set -a; . ./.env; set +a` + 内联 `RESEARCHOS_AGENT_RUNTIME=openhands`；
  跑前自检 `LLM_MAIN_KEY` 存在性 = True，**未物化值**）：`sort_analysis_v1` 的 run **恰为
  `SUCCEEDED`**，样张 `scratch/goal012-c2-live-sample.json` 记录四项：① 冻结留痕 4 条
  （`code.execute` 在列）；② 实验**恰 1 次**（镜像 `sha256:e95de2424c65…` = 本机
  `research-os-sandbox:m9-test`、产物 `analysis_report` / `experiment_result.json` / 日志、
  指标 `corpus_size=2048` / `worst_case_comparisons=19960`）；③ 证据 6 条（含 `USER_PROVIDED`
  的声明输入 `sort_analysis_v1`）；④ 归账 `MODEL_TOKENS 9738` / `MODEL_REQUESTS 2`（成本如实
  `UNKNOWN`）。**第一次取样失败如实保留**：冻结成功、实验真跑了，却死在 review 会话
  （`Duplicate tool names found: {'inert'}`）——测试侧惰性工具替身把两件 provider 注册成同一个
  类，而 SDK 由**类名**派生工具名；修法 = 按注册名分名 + **新增离线判据**（mock 端点 +
  `map_tools=True`，按压逐字复现 live 死法，`scratch/goal012-c2-press-duplicate.txt`）。
  **W-B 闭合**：空交付物仍被如实拒绝（`register_session_result` 一字未改），改的是判据
  **显式声明**交付物 + `with_sandbox_experiment` 的可选 `runtime` 参数（缺省行为逐字不变，
  `make_run_ready_deps` 的缺省 runtime **未动**）。**W-A/W-C 如实保留**：真实控制面对
  `sort_analysis_v1` 的 `evidence.read` 判 `DENY` ⇒ 该协议在真实控制面上仍是 `FAIL`，
  **本 cycle 未改策略面**（独立脚本 A 组在两棵树同结论）⇒ **需拍板项**。**独立复检**
  `scratch/verify_goal012_c2.py` 两棵树成对：当前树 **29/29**、基线树（`c6cf330`） **10 失败**
  （红项恰为本 cycle 新增面）。**门**：`tests/e2e` 116 passed / 10 skipped、`tests/api` +
  `tests/application` 1212 passed / 1 skipped、`python/tests` **4408 passed / 19 skipped / 0 failed**、
  `mypy` 995 files 干净、`judged N; blocked 0`（零出网）；**m0 终局 `PASS: profile=m0; 23 deterministic
  checks`**（`scratch/goal012-c2-m0-final.log`）。**GOAL 仍 ACTIVE**（EC-03…EC-06 未完）。
- 2026-09-23（**cycle 3 收口**）：**EC-03 PASS**（`PLAN-20260923-144` → **DONE**，提交 `6ccdf46`；
  复检 `RECHECK-20260923-145` = **PASS**）。判据 `tests/e2e/test_ec03_experiment_evidence_chain.py`
  （离线 + 真实容器，**2 passed**）判四条：① 四件产物在两读面都可见；② 内容 digest 在**证据条目**
  与**来源记录**两条记录上都可从内容字节重算（实测 6 件制品）；③ `image_digest` 由**独立查 daemon**
  复核、`environment_digest` 非空、**语义摘要与指标跨两次执行相同**；④ 四件产物的证据
  `extracted_by == experiment:<run id>`（实验路径，不是会话自述）。**成对反证**：同构脚本写别名字的
  产物 ⇒ 门拒收且**点名** `analysis_report`，读面上没有它而 `report.txt` / `experiment_result.json`
  仍在 ⇒ 红的理由恰是「声明产物缺失」。**四处按压全红**并复原（产品代码 `git diff` 逐字回到 HEAD）；
  其中一次按压**暴露判据盲点**（只看证据 digest、没看来源记录）⇒ 判据**加强**为两条记录各算一遍。
  **独立复检两棵树成对**：当前树 **24/24**、基线树（`31dfbd4`）**6 红**（恰为判据文件不存在）、
  **产品件两树同指纹 ⇒ 本 cycle 未改产品代码**（纯判据 cycle）。**门**：m0
  **`PASS: profile=m0; 23 deterministic checks`**（`python/tests` **4411 passed / 19 skipped / 0 failed**）、
  `tests/e2e` 118 passed / 10 skipped、`mypy` 996 files 干净、**零出网、零 live 调用**。
  **GOAL 仍 ACTIVE**（EC-04…EC-06 未完）。

- 2026-09-23（**cycle 4 收口**）：**EC-04 PASS**（`PLAN-20260923-146` → **DONE**，提交 `830a72c`；
  复检 `RECHECK-20260923-146` = **PASS**）。路径 (B) 的否证**已独立成文**：
  `docs/roadmap/PATH_B_REFUTATION_RECORD.md`——状态逐字「**已否证（refuted）/ 待重新设计（needs redesign）**」
  并写明「**不是待办功能，也不是已完成**」；四项实测事实（① 单 task 非自产来源上限 **3**
  ② 同一 task 内**第二次检索调用硬失败** `conflicting source registration` ③ `minimum_sources: 10`
  与机制**不相容** ④ `SCHEMA_VALID` / `TEST_PASSES` / `POLICY_COMPLIANT` **无产品调用方**）
  **逐条**各带「机制」与「实测出处」（`PLAN-20260922-138` 的 `E-3`/`E-4`/`E-5` + 两个 `scratch/` 探针脚本）；
  「重新设计需要什么」5 条**只列不做**并标明属**需拍板**项。**只读历史**：相对 `HEAD` 与相对基线树
  `ea06b77`，`GOAL-20260922-011` / `PLAN-20260922-138` / `RECHECK-20260923-139` 的 `git diff --stat`
  **两次都空**；`W-P` / `W-Q` 原文可查；`PLAN-138` 仍 `status: BLOCKED`——**本 GOAL 没有把 (B) 写成
  已完成或抹掉**。**残余节** `R-B1` 已登记该记录路径（含四项事实摘要 + 「原样保留」句 + 「不得读成待办功能」）。
  **本 cycle 只加文档与登记**：零产品代码/协议/合约/测试/门禁/策略面改动（两棵树成对复检
  `scratch/verify_goal012_c4.py`：当前树 **24/24**、基线树 **14 红且全部是新面**）。
  **顺带查出并处置一处既有记录缺陷（勘误）**：cycle 3 的复检脚本把判据的**中间形态字面量**钉住，
  而判据在 m0 的 50 行/函数门禁下被**纯重构**过（`919ad2c` → `6ccdf46`）⇒ `RECHECK-145` 里的
  「当前树 24/24」实为**amend 之前**的测量。处置：B2 改判**语义**（四 token，强度只增不减）、
  复测**同结论同数字**、`RECHECK-145` 就地追加「勘误」节（保留原行 + 标明时点）、事实进
  `MEM-20260923-112`；**被检的判据文件一字未改**。**门**：m0 **`PASS: profile=m0; 23 deterministic
  checks`**（`python/tests` **4411 passed / 19 skipped / 0 failed**，与 cycle 3 同数）、
  `DOCS-CHECK PASS: 6 deterministic checks`、`validate.py` ⇒ `Cursor 治理验证通过`、
  出站 `judged 787; blocked 8`（8 条全是故意探针）。**GOAL 仍 ACTIVE**（EC-05…EC-06 未完）。
