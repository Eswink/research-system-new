---
id: GOAL-20261005-030
slug: capabilities-actually-used-in-a-research-run
title: 承接能力的**真实使用**与科研闭环加深 —— 从「接上了」到「真的被用」
status: ACTIVE
created_at: 2026-10-05
updated_at: 2026-10-05
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-05 用户会话指令（goal 模式）：**建档 GOAL-030（承接能力的真实使用与研究闭环加深）
    并授权本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **方向承 GOAL-029**：GOAL-029 把承接面扩到 **17/46** 并让「出厂即可跑」机械化，但
    **承接面 ≠ 被使用** —— 目前只有**测试判据**在调用这些工具，**没有一次真实科研 run 把它们
    用在真实研究任务上**。本轮收这条：让一次 run **真的用上多种承接能力**，并把「用到了」
    变成**可复核的证据**；同时按 GOAL-029 自己给的候选清单推进 **B 组**。
    (1) **授权范围（严格限于）**：(i) 把承接能力**接进真实 run 的 phase**（协议声明 + 装配
    接线）；(ii) **新增 B 组能力承接**（以核实的可行性为限）；(iii) 修实现过程中发现的
    **真缺陷**；(iv) 新增判据 / 夹具（落 `tests/**`）；文档同源更新；(v) 扩充「科研子迭代」的
    深度（更多 phase / 更多 role / 更真实的科研动作）。
    (2) **明确不做（命中即 BLOCKED）**：改 `default_effect: DENY` / 放宽 §9 / **新增类别级
    allow**；**修改任何既有判据 / 门禁 / 阈值**（**新增**可以）；改 `PRODUCT_ROOTS` / m0 条数 /
    作业结构；**把真实凭据写进任何地方**；未经 pin 的 provider；token passthrough；未批准即用；
    **放开默认网络**（默认门必须仍离线，`tests/egress_guard.py` 不得放宽）；**触达 D 组**
    （`external.publish` / `package.install` / `git.commit` / `workspace.delete` —— 审批通道
    未接通，**需用户拍板**，本轮只登记）；**为了凑承接面数字而声明没有实现的能力**（GOAL-029
    已实测过这个反例：两条假计数被移除）；Canonical State 边界；读面认证 / 多租户 / RBAC /
    BOLA·BFLA / `G24-4` / `G24-5`；**宣称项目安全**（`R-M1`）；**宣称投递语义为「恰好一次」**
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    (3) **来源与授权口径**：来源 = **用户授权** + **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）+
    **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）。
    (4) **边界（承继）**：GOAL-001…029 **全部只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…029 的未覆盖范围**原样保留**。
    (5) **driver** = client-goal、**owner** = root-agent；**另一驱动持有未收口 ACTIVE cycle 时等待**。
objective: >-
    把 GOAL-029 建成的**承接面**（17/46 声明 + 实现 + 出厂绑定）从「**接上了**」推进到
    「**真的被用**」：让一次**默认装配**的 run **确定性**地用上多条承接读能力，并让「被使用」
    有**可复核的证据** —— **调用证据**（canonical 工具调用 / 证据的 `tool_refs`）+ **下游消费
    证据**（下游 phase 的 claim relation 引用上游工具证据）+ **反证点名**（摘掉实现 ⇒ run 失败
    并点名，绝不静默继续）+ **实跑终态**（离线链跑到 `SUCCEEDED`）（EC-01）→ 新增 **B 组**承接
    （`citation.validate` 的**判定语义** + `run.read` 的 `RunStore` 接线），**以核实为准、不得为
    凑数硬接**，并把判定规则写成**可复核**的机械事实与射程同源（EC-02）→ 在同一个 run 里加入
    **至少一个真正的科研动作**（结构化产出 + canonical 落盘 + 读面可复核 + 反证）（EC-03）→
    对本轮**新增的每条判据**主动做**射程自查**，并给出一个能**判红的用例**证明自查本身有效
    （EC-04）→ 自举收口（验证器进树 + 两树复检 + 判词归档进树 + as-is m0 23/23 在记录之后 +
    治理绿 + CI 台账逐提交）（EC-05）。
    **硬约束**：缺实现 / 缺映射 / 缺 pin / 未批准 / 未放行一律**点名失败**（**不得**静默降级）；
    承接 ≠ 放行，**已承接但未放行**在判据上必须**可区分**；判据的受判面**不得**是任何形式的
    交集 / 过滤（承 GOAL-029 EC-02 的教训 + `MEM-20260922-160`）；**不得**把受判面写成
    `declared ∩ implemented` 这类使「最该被抓的形态」在构造上不可能出现的形态；零真实凭据进树；
    **默认门离线**；m0 条数**仍是 23**；**不得**宣称项目安全（`R-M1` 仍在）；**不得**宣称投递
    语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **承接能力进入真实 run（主干；受限面如实登记）**。
      **建档勘察推翻了两处起点表述**（见「事实层结论」）：
      (i) **承接面读数 17/46 正确**（provider 声明口径的 distinct capabilities = **17**；
      `capabilities.yaml` 的 46 是**词表**、不是声明面）—— 起点所述「实测 15 条」**不成立**；
      (ii) **起点要求的「协议里声明使用 ≥3 条 GOAL-029 新增读能力」在构造上不可能**：
      实测（临时协议文件，未动树）把 `claim.read` 写进某 phase 的 `required_capabilities` ⇒
      `test_no_protocol_reachable_capability_lacks_a_rule` 与
      `test_each_row_state_matches_the_mechanical_rule` **同时判红**；消红只有两条路，**都命中
      明文不做** —— ① 给它加 `allow` 规则 ⇒ 打红 `tests/application/preflight/test_read_grant_is_per_item.py`
      的 `EXPECTED_REGISTERED = 15` 与「这 15 条一条都没被放行」两条断言；② 减 `EXPECTED_REGISTERED`
      ⇒ **改既有判据**。⇒ 该子集属 `D-02(b)`（读类能力是否成类预放行）**待拍板**，本 GOAL
      **只做可达子集**并**逐条登记**受限面。
      **本 EC 的验收**：
      (a) **确定性使用**：新增一份协议（EC-01 专用），把 **3 条已放行的承接读能力**
      （`artifact.read` / `evidence.read` / `workspace.read` —— 三条都在 GOAL-029 的射程内、
      都在 `policy.yaml` 的 `allow` 内、都有真实现、都在出厂绑定表内）声明为
      `capability_execution: run_chain` ⇒ 这三条**每次 run 都真的执行**（不依赖模型是否调用，
      与 GOAL-011 的既有机制同源）；
      (b) **调用证据**：run 的 canonical 事实里能看到这三条**真被调用**（工具调用记录 +
      证据的 `tool_refs` 逐条点名 provider id 与 tool id），且**产出被下游 phase 消费**
      （下游 phase 的 claim relation 引用上游的工具证据；HTTP 读面
      `GET /runs/{id}/evidence` 与 `GET /runs/{id}/artifacts` 可复核）——**不得**只断言
      「工具已注册」或「调用成功返回」；
      (c) **反证两向（合跑）**：摘掉其中一条的实现（provider 实例从装配里移除 / 从出厂绑定表
      摘除）⇒ run **失败并点名**缺的是哪一条（点名串逐字留档；**不得**静默继续）；复原 ⇒ 绿；
      (d) **实跑终态**：默认装配（`build_agent_runtime` 真实缺省）离线链跑到 `SUCCEEDED`，
      且**每条声明使用的能力都有调用证据**（三条各一条，缺一即判红）；
      (e) **受限面逐条登记**：`claim.read` / `budget.read` / `deliverable.read` /
      `experiment.read` / `experiment_plan.read` **本轮不进入「协议可达 + 被使用」**，理由与
      解除条件（`D-02(b)` 拍板）逐条写进「残余与受限面」节；**不得**用「已承接」冒充「已跑通」。
      **判据**：≥3 条真实使用 + 调用证据 + 下游消费证据 + 反证点名 + 实跑终态 + 受限面登记。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_capabilities_really_used_in_a_run.py
      tests/application/preflight -q` ⇒ 全绿（既有判据**逐字节未改**；新增判据不受此限）；
      配套留档：三条能力的**调用证据**（工具调用记录 + 证据 `tool_refs` 逐字）、**下游消费证据**
      （下游 claim relation 的 `evidence_id` 与上游产出的对应关系）、反证判红原文（点名串逐字）、
      实跑终态与读面读数、按压前后 raw `sha256` 逐字节复原。
      **收口记录（cycle 1）**：`PLAN-20261005-283` + `RECHECK-20261005-284`
      （PASS_WITH_WARNINGS，五条 W-NN）；判据 `tests/e2e/test_capabilities_really_used_in_a_run.py`
      **8 passed**；顺带修掉一处**真缺陷**（同 run 两 phase 调同一工具 ⇒ evidence id 相撞）。
      受限面（五条未放行读能力）逐条登记在「残余与受限面」节。
    status: PASS
  - id: EC-02
    criterion: >-
      **B 组承接（以核实为准，不得为凑数硬接）**。
      **建档勘察的可行性结论（逐条实测）**：
      - `run.read`：`RunStore` **确在 Port 面**（`packages/application/ports/run_store.py`，
      `list_runs` / `get_run` / `save_run`），**两个组合根都持有**（`composition.py:116`
      `runs_store` / `pg_composition.py:114` `"runs_store"`）⇒ **可行**；但起点所述「与
      `experiment_store` 同形」**不完全成立**（后者是裸 store 直传，前者要动组合面签名）。
      - `citation.validate`：取数面**在**（`NcbiEutilsProvider._elink` → `normalize_elink`
      输出 `{pmid, pmc_links}`）⇒ 复用可行；**判定语义是新增**（起点所述正确）。
      **本 EC 的验收**：
      (a) `citation.validate`：在 `NcbiEutilsProvider` 实现（复用 `_elink` 取数），**判定规则
      写死且可复核** —— 结构化返回 `{pmid, pmc_links, validated, rule, reason}`，规则为
      「被 elink 解析出 linkset（即 id 在 PMC 侧有链接结构）**且** ≥1 条 PMC 链接 ⇒ 通过」，
      否则**拒绝并给出 reason**；规则文本进 `docs/architecture/POLICY_SURFACE_AUDIT.md`
      或专门章节（单一来源），判据逐条按压「通过 / 拒绝」两种输入；
      (b) `run.read`：在 `CanonicalReadProvider` 实现 `run_read`（`RunStore.get_run`），
      进 `_TOOL_CAPABILITIES` + 出厂绑定表 + **两个组合根**的 provider 依赖面；`RunStore`
      缺失 ⇒ **点名拒绝**（不返回空壳冒充「没有 run」）；
      (c) **反证**：声明了但没实现 ⇒ 判红并**点名**能力名与工具名（承 GOAL-029 EC-02 的
      机械化判据形态）；**两向**：实现了但没声明 ⇒ 也判红；
      (d) **射程同步**：`tool_providers.yaml` / `POLICY_SURFACE_AUDIT.md` 的声明面列 /
      `tests/architecture/python/test_capability_coverage_is_implemented.py` 的
      `_IN_SCOPE` + `_OUT_OF_SCOPE_REASONS` + `_DECLARED_WITHOUT_IMPLEMENTATION` +
      **清单下界**（`_MIN_NEWLY_承接` 由 8 同步上调）**同一轮**更新；**不得靠并集 / 交集掩蔽**
      （承 `MEM-20260922-160`）；
      (e) **承接 ≠ 放行且可区分**：两条新承接的能力在 `policy.yaml` 里**仍无 `allow`**，
      判据必须断言它们的执行**点名 `POLICY_DENIED`**（**不得**用「已承接」冒充「已跑通」）。
      **判据**：B 组承接（以核实为准）+ 判定规则可复核 + 反证两向 + 射程同源 + 承接/放行可区分。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/architecture/python/test_capability_coverage_is_implemented.py
      tests/application/preflight tests/contracts -q` ⇒ 全绿；新增判据绿；
      配套留档：判定规则的两种输入（通过 / 拒绝）落档读数、反证两向判红原文、
      射程清单与下界的**同一轮**改动清单（文件 + 行 + 前后值）、`POLICY_DENIED` 点名原文。
      **收口记录（cycle 2）**：`PLAN-20261005-285` + `RECHECK-20261005-286`
      （PASS_WITH_WARNINGS，五条 W-NN）。**核实结论分两半**：
      - **`run.read` 可行 ⇒ 已承接**：读既有 `RunStore` Port（两组合根都持有实例），与 HTTP
        读面 `GET /runs/{id}` **同一个 `get_run`**。判据
        `tests/adapters/canonical/test_run_read_onboarding.py`（**10 passed**）四条齐备：
        声明+实现+绑定 / 真读得到（逐字段）/ 缺依赖与未知 id 点名 / **承接≠放行可区分**。
        射程**四面同轮同步**（`tool_providers.yaml` / `_IN_SCOPE`+陈旧条目移除 /
        `POLICY_SURFACE_AUDIT.md` 声明面列 / provider 夹具）。`composition.py` **净增 0 行**（恰 450）。
      - **`citation.validate` 经**实测**判定不可行 ⇒ 登记为受限面，不硬接**：取数面（`_elink`）
        与判定规则都可写，但**声明它**会同时打红两条既有 pin 判据
        （`tests/contracts/test_ncbi_provider_contract.py::…::test_list_tools_schema` 与
        `tests/contracts/test_europe_pmc_pin_and_registration.py::…::test_existing_providers_are_untouched`，
        实测判词：`Left contains one more item: 'citation.validate'`），而 `tests/contracts/**`
        是**明文禁改面** ⇒ 命中「**不得为凑数硬接**」。**解除条件**：该两处 pin 的同轮同步需用户拍板。
      **按压**：撤回 `run_read` 的能力映射 ⇒ **3 failed**（实现面 / 声明-实现落差 / 射程下界，
      三条各自点名 `run.read`）；复原 `sha256` 全 `OK`。
    status: PASS
  - id: EC-03
    criterion: >-
      **科研动作的深度（让研究更像研究）**。
      在 EC-01 的 run 里加入**至少一个真正的科研动作**（**不是**读取与传递）：**结果分析与
      统计** —— 一个分析 phase **消费**实验 phase 的真实 `metrics` 制品（容器产出，非桩），
      产出**结构化**科学结论：`{statement, rationale, falsifiable_prediction,
      supporting_evidence_ids, statistics:{…}}`。
      **四项要求逐条**：
      ① **结构化产出**：字段级可断言（判据逐字段读，不是自由文本 / 不是字符串里找关键词）；
      ② **落 canonical**：经**既有**路径（artifact + claim relation；**不新造第二套漏斗**）；
      ③ **读面可复核**：artifact 读面（`GET /runs/{id}/artifacts`）与 evidence / claim 读面
      （`GET /runs/{id}/evidence`）都能复核到该产出；
      ④ **反证**：该动作的产出被移除 ⇒ **下游 phase 判负并点名**（fail closed，承 GOAL-027
      「评审真能判不通过」的形态；**不得**静默通过）。
      **判据**：真科研动作 + 结构化产出（逐字段）+ canonical 落盘 + 读面 + 反证点名。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_scientific_action_depth.py -q`
      ⇒ 全绿；配套留档：结构化产出的逐字段读数、canonical 落点（artifact id + digest）、
      读面复核读数、反证臂的判负原文（点名串逐字）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **判据射程的自查（承 GOAL-029 的教训；主动做，不等完成核验）**。
      GOAL-029 的 EC-02 主判据曾把受判面写成 `declared ∩ implemented`，**掩蔽了本应报出的
      缺口**（「声明了但没实现」在构造上不可能出现）。本轮**主动**自查：
      (a) 对本轮**新增的每条判据**，用**同一种手法**检查：受判面是否被写成某个**交集 / 过滤 /
      空集可恒真**的形态，使「最该被抓的形态」在构造上不可能出现；
      (b) 产出**射程自查表**（每条判据：受判面定义 / 是否可能掩蔽 / 按压形态 / 实测结果），
      落进本 GOAL 记录（**进树**）；
      (c) **反证**：对至少一条判据，人为把受判面改成「安全」的交集 ⇒ 断言它能被抓到
      （即：**自查本身要有一个能判红的用例**）——判据化，落 `tests/tooling/`。
      **判据**：自查表 + 每条判据的按压记录 + 掩蔽形态的**可判红用例**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_criterion_scope_self_check.py -q`
      ⇒ 全绿（含掩蔽形态被判红的那条）；配套留档：射程自查表（本 GOAL 记录内）、
      每条判据的按压前后读数、掩蔽用例的判红原文。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：① 收口验证器进树（`tools/verify_goal030_closeout.py`，**复用**
      `tools/closeout_recheck_assertions.py` 的标准断言集与 `tools/closeout_recheck_tools.py`，
      只写本轮特有断言）并加入 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的
      `IN_SCOPE`（**纯收紧** ⇒ 只增不删，450 行硬上限）；② 两树复检 + **判词归档进树**
      （`.cursor/plans/goals/evidence/`，**二进制写盘**，逐行相同 + `sha256` 相同）；
      ③ as-is m0 **23/23**，**在记录写入之后**（独占运行、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、**不接管道**、canonical DSN pin、零进程残留）；
      ④ 治理 `validate.py` 绿（含 GOAL/PLAN/RECHECK/MEM 交叉引用与 `DOCS-CHECK`）；
      ⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 / 空字段 =
      未取证**）；⑥ 承继残余逐条在位 + 本轮新增；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进入射程 + 两树同结论 + 判词归档 + m0 23/23 在记录之后 + 治理绿 +
      台账逐提交 + 残余/未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling -q` ⇒ 全绿；
      `uv run --frozen --no-sync python tools/two_tree_recheck.py --script-mode shared` ⇒
      `TWO-TREE PASS`；as-is m0 ⇒ `PASS: profile=m0; 23 deterministic checks`；
      `uv run --frozen --no-sync python .cursor/skills/governance-check/scripts/validate.py` ⇒ 绿；
      配套留档：m0 终态行、两树判词归档（两份 + `sha256`）、CI 台账（逐提交 run URL + 结论）。
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
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **为了凑承接面数字而声明没有实现的能力**（GOAL-029 已实测过这个反例：两条假计数被
      收口审计移除）；**把受判面写成交集 / 过滤**（承 `MEM-20260922-160` 与 GOAL-029 EC-02
      的实测教训：`declared ∩ implemented` 使「声明了但没实现」在构造上不可能被报出）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/egress_guard.py`、
      三道记录面判据（`test_reproducibility_wording.py` / `test_delivery_semantics_wording.py` /
      `test_record_face_is_covered_by_the_gate.py`）、两树入口判据、规模门禁、
      `tests/application/preflight/**`、`tests/application/test_m2_audit.py`、
      `tests/contracts/**`、`tests/e2e/**` 既有文件、`tests/api/run_fixtures.py` 的 `_PROVIDERS` 行）
      —— **新增**判据与新增文件不受此限
    - >-
      **例外（同一轮射程同步，逐条点名允许）**：仅限
      `tests/architecture/python/test_capability_coverage_is_implemented.py` 的
      **分类/登记表**（`_IN_SCOPE` / `_OUT_OF_SCOPE_REASONS` / `_DECLARED_WITHOUT_IMPLEMENTATION`
      / `_MIN_NEWLY_承接` 下界）与 `docs/architecture/POLICY_SURFACE_AUDIT.md` 的**声明面列**，
      且仅在**新承接确实落地**（声明 + 实现 + 绑定三者同轮在场）时同步；**不得**用它放宽
      任何断言语义、**不得**下调下界、**不得**把已实现的能力从清单里移除
    - >-
      改 `default_effect: DENY` / 放宽 §9 默认 deny / **新增类别级 allow**；或改
      `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` 与 `policy.yaml`
      的镜像并集（两张表由既有测试锁死）；**给 A 组读能力新增 `allow` 规则**（⇒ 改既有判据 +
      属 `D-02(b)` 未决口径 ⇒ **需用户拍板**）
    - >-
      让某条**未放行**能力**变为协议可达**（写进任何协议的 `required_capabilities` / 合约）
      而不同时取得放行 —— 实测会同时打红 `test_no_protocol_reachable_capability_lacks_a_rule`
      与 `test_each_row_state_matches_the_mechanical_rule`；取得放行则属上一条
    - >-
      **未经 pin 的 provider**；**把真实凭据写进任何地方**；**放开默认网络**（默认门必须仍
      离线）；**触达 D 组**（`external.publish` / `package.install` / `git.commit` /
      `workspace.delete`）；**宣称项目安全**（`R-M1`）；**宣称投递语义为「恰好一次」**
escalation_triggers:
  - 需要修改 `default_effect: DENY` / 放宽 §9 默认 deny / 新增类别级 allow
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖 / 上游版本 pin 变更
  - 真实凭据进树 / 未 pin 接上游 / 触达 D 组（审批通道未接通）
  - 需要把某条**未放行**能力变为协议可达（= 改既有判据；属 `D-02(b)` 待拍板）
  - 宣称项目安全 / 宣称投递语义为「恰好一次」
  - 同一失败签名超过 fix_policy 上限
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261005-030 — 承接能力的真实使用与科研闭环加深

## 目标与退出标准

承 GOAL-029（承接面 12/46 → **17/46**，出厂即可跑机械化）：**承接面 ≠ 被使用** ——
GOAL-029 承接的读能力**只有测试判据在调用**，**没有一次真实科研 run 把它们用在真实研究
任务上**（建档勘察 (c) 的逐条读数）。本 GOAL 收这条，并按 GOAL-029 的候选清单推进 **B 组**。

| EC | 标准（简） | 验证命令 / 证据来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 承接能力进入真实 run：≥3 条**已放行**承接读能力**确定性执行** + 调用证据 + 下游消费证据 + 反证点名 + 实跑 `SUCCEEDED` + 未放行子集逐条登记 | 见 frontmatter `exit_criteria[0].verify` | PENDING |
| EC-02 | B 组承接（`citation.validate` 判定语义 + `run.read` 的 `RunStore` 接线）+ 反证两向 + 射程同源 + 承接/放行可区分 | 见 frontmatter `exit_criteria[1].verify` | PENDING |
| EC-03 | 真科研动作（结果分析与统计）：结构化产出 + canonical 落盘 + 读面 + 反证点名 | 见 frontmatter `exit_criteria[2].verify` | PENDING |
| EC-04 | 判据射程自查：自查表 + 每条判据按压 + **掩蔽形态的可判红用例** | 见 frontmatter `exit_criteria[3].verify` | PENDING |
| EC-05 | 自举收口（验证器进树 + 两树复检 + 判词归档进树 + m0 23/23 + 治理 + 台账逐提交 + 残余/未覆盖逐条） | 见 frontmatter `exit_criteria[4].verify` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。勘察留档
> `scratch/goal030-recon.md`（树外，`.gitignore` 覆盖）。凡与起点表述不符者，**以实测为准**。

### 1. 承接面口径：**17/46 正确**（provider 声明口径）；起点所述「15 条」不成立

复核命令：

```bash
uv run --frozen --no-sync python -c "
import yaml
p=yaml.safe_load(open('examples/config/tool_providers.yaml',encoding='utf-8'))['tool_providers']
d={}
for pid,body in p.items():
    for c in (body or {}).get('capabilities') or []: d.setdefault(c,[]).append(pid)
print('distinct declared =',len(d))
v=yaml.safe_load(open('examples/config/capabilities.yaml',encoding='utf-8'))['capabilities']
print('vocabulary =',len(v))
"
```

读数：**distinct declared = 17**；**vocabulary = 46**。

**口径写明（三者的区分）**：
- **provider 声明** = `tool_providers.yaml` 各 provider `capabilities` 的**去重并集** = **17**
  （`m12_artifact` 9 条 + `openhands_workspace` 5 条 + `ncbi_eutils` 3 条 + `europe_pmc` 2 条，
  其中 `literature.search` / `literature.read` 被两个 provider 共用 ⇒ 去重后 17）；
  **这是 GOAL-029 记录状态历史里 17/46 的那个数**；
- **能力词表** = `capabilities.yaml` 的 46 条 —— **参照系，不是声明面**（由
  `test_policy_surface_difference_set.py::test_the_registry_vocabulary_is_not_part_of_the_declaration_side`
  钉死：词表混入声明面会让差集退化成空集）；
- **实现注册** = `read_surface.py::_TOOL_CAPABILITIES` + `DEFAULT_SESSION_TOOL_BINDINGS`。

起点称「实测 `tool_providers.yaml` 里是 15 条（`agent_run.read` / `audit.write` 不在表中）」：
`agent_run.read` / `audit.write` **确实不在** provider 表（它们在 `roles.yaml` 的**另一个**
声明面里），但 provider 表去重后是 **17** 而不是 15 ⇒ **起点读数不成立，17/46 无需修正**。

### 2. ⚠️ 决定性发现：5 条 GOAL-029 新增读能力**不可**进入「协议可达 + 被使用」

复核命令（真实 `NativePolicyEvaluator(policy.yaml)`，逐条求值）：

```bash
uv run --frozen --no-sync python -c "
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports.policy_evaluator import PolicyRequest
from packages.application.preflight.policy_check import policy_scope_for
from services.api.catalog import load_policy_definition
p=load_policy_definition(); e=NativePolicyEvaluator(p)
for cap in ['artifact.read','evidence.read','workspace.read','claim.read','budget.read','deliverable.read','experiment.read','experiment_plan.read']:
    s=policy_scope_for(cap)
    d=e.evaluate(PolicyRequest(actor='agent:x',capability=cap,action='execute',scope=s,resource=cap))
    print(cap, s, d.decision.value, d.reason)
"
```

读数：

| 能力 | scope | 决策 |
| --- | --- | --- |
| `artifact.read` / `evidence.read` / `workspace.read` | `project` | **ALLOW**（matched allow rule） |
| `claim.read` / `budget.read` / `deliverable.read` / `experiment.read` / `experiment_plan.read` | `None` | **DENY**（used default policy effect） |

**结构链（每环都实测取证）**：
1. `policy.yaml` 的 `allow` 只有 7 条 `capability:` 规则，5 条新增读能力**都不在其中**；
2. 差集机制（`test_policy_surface_difference_set.py::expected_state`）：能力**不在**
   `reachable()` 时 ⇒ 差集侧「声明面独有」+ 读类 ⇒ 终态**「该登记」**；一旦写进某 phase 的
   `required_capabilities` ⇒ `reachable()` 变真 ⇒ 终态变**「该放行」**；
3. **实测（临时协议文件 `examples/protocols/zz_goal030_probe.yaml` 写入 `claim.read`，跑完即删）**：

```
FAILED tests/application/preflight/test_policy_surface_difference_set.py::test_each_row_state_matches_the_mechanical_rule
FAILED tests/application/preflight/test_policy_surface_difference_set.py::test_no_protocol_reachable_capability_lacks_a_rule
E  AssertionError: 协议可达却无放行规则（W-A 同类活缺口）：{'claim.read': ['zz_goal030_probe.yaml']}
2 failed, 9 passed
```

4. 消红只有两条路，**都命中明文不做**：① 加 `allow` ⇒ 打红
   `tests/application/preflight/test_read_grant_is_per_item.py` 的 `EXPECTED_REGISTERED = 15`
   与 `test_registered_read_capabilities_are_not_granted_as_a_class` 的 `touched == []`；
   ② 减 `EXPECTED_REGISTERED` ⇒ **改既有判据**。

**⇒ 起点要求的 EC-01(a)（「协议里声明使用 ≥3 条 GOAL-029 新增读能力」）在构造上不可达。**
本 GOAL 的 EC-01 因此落在**可达子集**（3 条已放行能力：`artifact.read` / `evidence.read` /
`workspace.read`，三者都在 GOAL-029 射程内且都有真实现），并把**不可达子集逐条登记**
（`D-02(b)` 待拍板），**不以「已承接」冒充「已跑通」**。

### 3. B 组可行性（逐条核实）

- **`run.read`**：`RunStore` **确在 Port 面**（`packages/application/ports/run_store.py`；
  `list_runs` / `get_run` / `save_run`），**两个组合根都持有**
  （`composition.py:116` `runs_store: RunStore | None`；`pg_composition.py:114`
  `"runs_store": PostgresRunStore(...)`）⇒ **承接可行**。
  **但起点所述「与 `experiment_store` 同形接线」不成立**：`experiment_store` 是裸 store
  直传 `CanonicalReadProvider(experiment_store=…)`；`RunStore` 要动 provider 依赖面 +
  出厂绑定表 + 两个组合根 + 位置参数入口（`session_tool_face` / `sqlite_session_tools`）。
- **`citation.validate`**：取数面**在**（`adapters/research_tools/ncbi.py:233` `_elink` →
  `parsing.py:114` `normalize_elink` 输出 `{pmid, pmc_links}`；`_TOOL_DESCRIPTIONS` 已有
  `citation_inspect`）⇒ 复用可行；**判定语义是新增**（起点所述正确）。
- **`agent_run.read`**：**不列入** B 组 —— 域里没有 AgentRun 实体（最近的是 task + agent_id），
  与 GOAL-029 的登记一致。

### 4. 现有承接能力的「使用面」（逐条分类）

复核命令：

```bash
rg -o -N "\b(artifact|claim|evidence|budget|experiment|deliverable|workspace|citation|literature)\.[a-z_.]+\b" examples/protocols/ | sed 's/.*://' | sort -u
```

读数（14 份协议，去重 **9 条**能力名）：`artifact.read`(14) / `workspace.read`(11) /
`literature.search`(6) / `literature.read`(6) / `evidence.read`(3) / `artifact.write` /
`code.execute` / `workspace.write.code` / `workspace.read.unwired`（反证协议专用名）。

逐条分类：

| 能力 | 协议声明 | 真被执行 | 说明 |
| --- | --- | --- | --- |
| `literature.search` / `literature.read` | ✅ | ✅ **run-chain** | 三条协议声明 `capability_execution: run_chain`，每次 run 确定性执行 |
| `artifact.read` / `evidence.read` / `workspace.read` | ✅ | ⚪ **仅会话工具面** | 声明在 `required_capabilities`，但**是否真被模型调用取决于模型**；e2e 判据只证「桥可触达」，**没有一次真实 run 消费过它们的产出** |
| `artifact.write` / `code.execute` / `workspace.write.code` | ✅ | ⚪ 声明级 | 会话语义，无产出消费断言 |
| `claim.read` / `budget.read` / `deliverable.read` / `experiment.read` / `experiment_plan.read` | ❌ **零协议声明** | ❌ | GOAL-029 承接了实现，**没有任何协议用过**（审计文档逐行「协议可达 = 否」） |
| `citation.inspect` / `citation.validate` | ❌ | ❌ | provider 声明有、协议使用零 |

**结论**：GOAL-029 承接的 5 条读能力的**使用面 = 0**；已放行的 3 条读能力**只在会话面上
「可能被模型调用」**，从未有「产出被下游消费」的证据。

### 5. run-chain 的筛法是 **provider 级**（不是能力级）—— 设计约束

复核命令：`sed -n '136,152p' packages/application/run_orchestration/phase_capabilities.py`

读数：`planned = tuple(call for call in deps.calls if call.provider_id in spec.run_chain_tool_ids)`
—— 按 **provider id** 过滤；`RunChainCall.capability` 不参与筛选。⇒ 把 `m12_artifact` 接进
某 phase 的 run-chain，执行的是**装配方声明的那些 `RunChainCall`**（不是该 provider 声明的
全部能力），但**声明面（`required_capabilities`）仍须逐条在场**（preflight 的策略判定面
按能力逐条判）。EC-01 的协议因此必须**逐条列出**三条能力。

### 6. 记录面与门（本轮受判面）

- `.cursor/plans` 在 `test_reproducibility_wording.py` 的扫描面内 ⇒ 本记录**不得**出现
  肯定式「完全可复现 / fully reproducible」（引用或否定式放行）；
- `.cursor/plans/goals/**` 是 `test_delivery_semantics_wording.py` 的**规则文本面**：
  **凡引用 exactly-once 的 GOAL 文件必须同时含禁令词**（禁止 / 不得 / 否认 / 不做 /
  BLOCKED / 口径）—— 本文件**已含**这六个词；
- 健康顺序（GOAL-019 的教训）：**先写记录 → 记录面判据 → 全量门**；m0 必须**独占**且
  在记录写入**之后**跑。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的**幂等重入**规则：

1. 最后一 cycle 无记录 → 开 cycle 1：执行「单 cycle SOP」①。
2. 有子 PLAN 但仍在 `IN_PROGRESS` → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待 / 判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

**本轮特有纪律**（与既有纪律并列，不替代）：

- **先复核再依赖**：任何「起点事实」在使用前必须复核，并与实测一致；不一致以实测为准并
  写进「事实层结论」；
- **承接面不许凑数**：声明了没实现 ⇒ **移除声明或补实现二选一**，**不得**留在
  「声明了但没实现」的状态；
- **受判面自查**（EC-04）：新判据的受判面**不得**是任何形式的交集 / 过滤；
  **必须有**「最该被抓的形态」可被报出的用例；
- **真被使用才算数**：EC-01 / EC-03 的判据必须断言**调用证据 + 下游消费**，
  **不得**只断言「工具已注册」或「调用成功返回」；
- **点名失败而非静默**：缺实现 / 缺映射 / 缺 pin / 未批准 / **未放行** —— 一律点名；
- **留档二进制写盘**（`Path.write_text(..., newline="")`）；判词归档**进树**；
- **受判面非空**、**反证两向**、**射程显式分类**、**不得靠并集掩蔽**、
  **按压后 raw `sha256` 逐字节复原**；
- **台账逐提交**（`cancelled` + 原因 + `covered_by`；**空集合 = 未取证**）；
- **批量推送**：一个 cycle 攒成一次推送（避免取消在飞的 M0 run）；
- 进程卫生（`taskkill /T /F`）；记录自洽（同提交）；本地假绿须在 Linux 侧复验。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；写子 PLAN
  （`.cursor/plans/tasks/PLAN-YYYYMMDD-NNN-topic.md`，frontmatter 增加 `parent_goal:
  GOAL-20261005-030` 并投影 `ALL_PLAN.md`）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 记录面判据 → 全量门**。定向套件 + 四道门（ruff / format /
  mypy）/ 规模门 + 受影响 e2e；m0 按组（python 6 / typescript 9 / framework 8，DSN 固化配方、
  仓库 `.venv`、`uv run --frozen --no-sync`、独占、**不接管道**）。本地不绿**不得** push。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 `DONE`），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅限 main，
  授权见 frontmatter）→ 按 `head_sha` **遍历该 SHA 全部 run** + `/jobs`（无 `gh` CLI；
  `git credential fill` 取令牌走 REST API；现成脚本 `scratch/poll_ci_all.sh <sha>`）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
  超过 fix_policy 上限或命中 escalation_triggers ⇒ `status=BLOCKED`。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、`child_plans`、状态历史；未达终态 → 回到 ①；
  触顶预算 → `BLOCKED`。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| (i) lint/format/typecheck | job 报 ruff / eslint / tsc / mypy / 规模门 | 直接修复 → fix commit → 重推 |
| (ii) 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品与判据各半）；**修产品优先**，禁改断言迁就 |
| (iii) flake / 环境 | 已知签名（OTLP teardown race、墙钟型负载抖动、DSN 注入、compose 环境、`WinError 5`） | 按既有配方：**单跑取证 → 独占重跑**；分类 (iii) 并如实登记；**绝不动阈值** |
| (iv) 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → `BLOCKED`（infra 非代码缺陷） |
| (v) 治理 / 安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |
| (vi) 已修但被取消 | `cancelled`（`cancel-in-progress`） | 核实是否与失败签名同源；登记 `cancelled` + 原因 + `covered_by` |

## 终止与收口

- **ACHIEVED**：五个 EC 全 `PASS` + 独立 RECHECK = `PASS`/`PASS_WITH_WARNINGS` +
  `latest_recheck` 指向该 RECHECK（**repo 相对路径**）+ 本文件收口（迭代日志 / 状态历史 /
  `child_plans` / EC 表同步）。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。留人工决策，**不静默降级**。
- **连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC** ⇒ `BLOCKED`。
- **收口后**：残余与未覆盖范围逐条明写；**不得**据此宣称项目安全（`R-M1` 仍在）；
  **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once +
  idempotency + deduplication）。

## 残余与受限面

### 受限面：五条已承接但**未放行**的读能力（逐条登记，不以「已承接」冒充「已跑通」）

`claim.read` / `budget.read` / `deliverable.read` / `experiment.read` /
`experiment_plan.read` —— 五条都有**真实现**（GOAL-029 承接）、都在**出厂绑定表**内，
但在 `examples/config/policy.yaml` 里**没有 `allow` 规则**。**cycle 2 新增**：`run.read` 也属此列（已承接、未放行）：

| 能力 | 承接面 | 放行 | 为什么不能进协议 |
| --- | --- | --- | --- |
| `claim.read` | ✅ `CanonicalReadProvider._claim_read` | ❌ | 写进 `required_capabilities` ⇒ 协议可达 ∧ 无放行规则 ⇒ 差集判据判红（实测） |
| `budget.read` | ✅ `_budget_read` | ❌ | 同上 |
| `deliverable.read` | ✅ `_deliverable_read` | ❌ | 同上 |
| `experiment.read` | ✅ `_experiment_read` | ❌ | 同上 |
| `experiment_plan.read` | ✅ `_experiment_plan_read` | ❌ | 同上 |
| `run.read`（**cycle 2 新增承接**） | ✅ `adapters/canonical/run_read.py` | ❌ | 同上（承接 ≠ 放行；判据钉住可区分性） |

### 受限面：`citation.validate`（**经实测判定不可行，不硬接**）

| 项 | 状态 |
| --- | --- |
| 取数面（`_elink` → `normalize_elink`） | ✅ 可复用 |
| 判定规则（`pmc_links` 非空 ⇒ 通过） | ✅ 可写死 |
| **声明**它（`ncbi_eutils.capabilities`） | ❌ 打红两条既有 pin 判据（均在 `tests/contracts/**` = 明文禁改面） |

**解除条件**：`test_ncbi_provider_contract.py::…::test_list_tools_schema` 与
`test_europe_pmc_pin_and_registration.py::…::test_existing_providers_are_untouched`
两处 pin 的同轮同步**需用户拍板**。

**解除条件**（不是本 GOAL 能自行决定的）：`D-02(b)`「读类能力是否成类预放行」需
**用户拍板**。三条消红路径**全部命中明文不做**：① 加 `allow` ⇒ 打红
`test_read_grant_is_per_item.py` 的 `EXPECTED_REGISTERED = 15` 与「一条都没被放行」两条断言；
② 减 `EXPECTED_REGISTERED` ⇒ **改既有判据**；③ 绕过差集 ⇒ 不可能（判据直接对机制断言）。

### 本轮新增残余

- **`W-1`｜判据侧 phase 归属靠交付物名推断**（`_phase_of_task`）：两 phase 交付物同名即失效
  （当前不同，判据自己也断言了）。见 `RECHECK-20261005-284`。
- **`W-2`｜运行链按 provider id 过滤（不是能力级）**：`RunChainCall.capability` 不参与筛选
  ⇒ 「三条能力各一次」由**装配方的 call 列表**保证，不由执行层保证（已单列自检用例固定）。
- **`W-3`｜`run_id_argument` 是新取参来源，仅本协议一个消费者**：有界（缺 run id 点名拒绝），
  但一般性未被第二个消费者证明。
- **`W-4`｜同一 task 内两次调同名工具会撞制品 id**（`operation_key` 相同）：当前每 phase
  各调一次，未触该边界。
- **`W-5`｜不改既有判据是「未改」而非「不可改」**：受限面的解法仍待拍板。

### 承继残余（原样保留）

`R-M1` 未收口；`R26-*` / `W27-*` / `W10-12` / `G24-4` / `G24-5`；历史 `tools/` 目录仍有
无机器门的旧脚本。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档轮，无子 PLAN —— 交付物是 GOAL 文件本身） | 见下方回写提交 | 治理 `validate.py` 绿；勘察留档 `scratch/goal030-recon.md`（树外）；探针协议跑完即删（`git status` 零残留） | 见下方「CI 台账」 | 无（勘察轮不动产品代码） | 五 EC 全 `PENDING` | cycle 1 = **EC-01**（承接能力进入真实 run） |
| 1 | `PLAN-20261005-283`（EC-01） | 见下方回写提交 | 新增判据 **8 passed**；`tests/application/preflight + architecture/python + loaders + tooling + application/evidence + application/run_orchestration` **1746 passed**；`tests/e2e + tests/api` **770 passed / 17 skipped**；`ruff` / `format` / `mypy` 绿 | 见下方「CI 台账」 | **两处按压（各自独立、两向、逐字节复原）**：① 撤回缺陷修复（evidence id 去 `task_id`）⇒ **2 failed**，判词逐字复现 `conflicting evidence registration`；② 协议改回会话语义 ⇒ **4 failed**（含判据自检那条） | **EC-01 收口**；**受限面**：五条未放行读能力仍不可协议可达（`D-02(b)` 待拍板）。`RECHECK-20261005-284` = PASS_WITH_WARNINGS（五条 W-NN） | cycle 2 = **EC-02**（B 组承接：`citation.validate` 判定语义 + `run.read` 接线） |
| 2 | `PLAN-20261005-285`（EC-02） | 见下方回写提交 | 新增判据 **10 passed**；`tests/architecture/python + application/preflight + application/evidence + contracts + loaders + tooling + adapters + e2e + api` **3471 passed / 89 skipped**；`ruff` / `format` / `mypy`（1097 files）绿；`composition.py` 恰 **450 行** | 见下方「CI 台账」 | **按压（两向）**：撤回 `run_read` 能力映射 ⇒ **3 failed**（各自点名 `run.read`）；复原 `sha256` 全 `OK` | **EC-02 收口**；`run.read` 已承接**未放行**（与另五条同）⇒ 不可协议可达；`citation.validate` **不可行** ⇒ 受限面（解除条件 = 两处 pin 同轮同步授权）。`RECHECK-20261005-286` = PASS_WITH_WARNINGS（五条 W-NN） | cycle 3 = **EC-03**（科研动作深度：结构化产出 + canonical 落盘 + 读面 + 反证） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | ACTIVE | **建档（cycle 0）**：读 `README.md` 的 GOAL 格式契约 + 只读勘察。**只读勘察推翻了起点的一处表述、并把一处「不可达」变成可复核的机械事实**，逐条实测：**① 承接面 17/46 正确**（provider 声明口径去重 = 17；`capabilities.yaml` 的 46 是词表、不是声明面）—— 起点所述「实测 15 条」**不成立**；**② ⚠️ EC-01(a) 的原始表述不可达**：把 `claim.read` 写进某 phase 的 `required_capabilities`（临时协议文件，未动树）⇒ `test_no_protocol_reachable_capability_lacks_a_rule` 与 `test_each_row_state_matches_the_mechanical_rule` **同时判红**（判词逐字留档）；消红的两条路（加 `allow` / 减 `EXPECTED_REGISTERED`）**都命中明文不做**（改既有判据）⇒ 该子集属 `D-02(b)` 待拍板 ⇒ EC-01 重构为**可达子集**（`artifact.read` / `evidence.read` / `workspace.read`，三条都在射程内且已放行）+ **受限面逐条登记**；**③ B 组核实**：`run.read` 的 `RunStore` **确在 Port 面**且两组合根都持有（承接可行；但「与 `experiment_store` 同形」不成立）、`citation.validate` 取数面可复用（判定语义新增）、`agent_run.read` 域无实体（不列入）；**④ 使用面逐条分类**：GOAL-029 承接的 5 条读能力**使用面 = 0**，3 条已放行读能力**只在会话面「可能被模型调用」**、从无「产出被下游消费」的证据 —— 这正是本 GOAL 要收的落差；**⑤ run-chain 按 provider id 过滤**（不是能力级）⇒ EC-01 的协议仍须逐条声明能力；**⑥ 记录面门**：`.cursor/plans` 在措辞判据扫描面内、GOAL 面是 exactly-once 的规则文本面（本文件已含六个禁令词）。五 EC 全 `PENDING`。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-05 | ACTIVE | **cycle 1（EC-01 收口）**：让一次 run **真的用上**三条已放行的承接读能力，并把「用到了」变成可复核证据。**新增协议** `capabilities_used_in_a_run_v1.yaml`（2 phase，均 `capability_execution: run_chain`，逐条声明 `artifact.read` / `evidence.read` / `workspace.read`）+ 两份契约（`capabilities_used_probe` / `capabilities_used_review`）。**产品改动两处**：① `RunChainCall` 新增取参来源 `run_id_argument`（**执行期才存在**的 run 标识：协议/装配方无从写死，既有三类取值都不覆盖）+ `_StepInputs.run_id` + 缺它点名拒绝；② **真缺陷修复** —— `register_tool_evidence` 的 evidence id 省略了 `result.task_id`（而 `source_origin_for` 与 `_spilled_artifact_id` 都带它）⇒ **同一 run 的两个 phase 调同一工具时相撞**（实测 `conflicting evidence registration`）；修法 = id 与另两者**同粒度**。**判据** `tests/e2e/test_capabilities_really_used_in_a_run.py`（**8 passed**）五件事：调用证据（三条**逐条**在场，且**逐 phase** 各查一遍）/ 产出可复核（`tool-result:` + digest）/ **下游消费**（`review` 的 `evidence_read` **返回内容**里含 `probe` 三条工具证据 id —— 「调了但没人用」不成立）/ 反证点名（不给实例 ⇒ `FAILED` + 点名 provider/能力/工具）/ 判据自检。**判据初版的一处自查缺陷（实测抓到并修）**：`_tool_evidence` 单键索引在**两 phase 同名工具**时**后写覆盖前写** ⇒ 上游/下游被这个覆盖**掩蔽**（正是 `MEM-160` 的形态）⇒ 改为**按 phase 分索引**。**两处按压**（各自独立、两向、逐字节复原）：① 撤回缺陷修复 ⇒ **2 failed**，判词逐字复现缺陷签名；② 协议改回会话语义 ⇒ **4 failed**。**受限面逐条登记**（见「残余与受限面」：五条已承接未放行读能力 + 解除条件 `D-02(b)` 拍板）。`RECHECK-20261005-284` = **PASS_WITH_WARNINGS**（五条 W-NN）。本地门：`ruff` / `format` / `mypy` 绿；`tests/application/preflight + architecture/python + loaders + tooling + application/evidence + application/run_orchestration` **1746 passed**；`tests/e2e + tests/api` **770 passed / 17 skipped**。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
| 2026-10-05 | ACTIVE | **cycle 2（EC-02 收口）**：按核实结论推进 B 组，**可行才接、不可行如实登记**。**`run.read` 可行 ⇒ 已承接**：`RunStore` **确在 Port 面**（`list_runs` / `get_run` / `save_run`），**两个组合根都持有实例**；新增 `adapters/canonical/run_read.py`（读 `get_run`，逐字段；缺 store / 缺 id / 未知 id 一律**点名拒绝**，不返回空壳），与 HTTP 读面 `GET /runs/{id}` **同一个查询口径**。**装配**：绑定表 + 四个入口（`session_tool_face` / `sqlite_session_tools` / `canonical_read_register` / 组合根）透传 `run_store`；`_SqliteStoreParts.runs_store` **复用同一实例**给 `ApiDeps`（消灭第二个 store 实例）⇒ `composition.py` **净增 0 行**（恰 450）。**判据** `tests/adapters/canonical/test_run_read_onboarding.py`（**10 passed**）四条：声明+实现+绑定 / 真读得到（逐字段，未冻结回 `null`）/ 缺依赖与未知 id 点名 / **承接≠放行可区分**（同一用例内同时断言「目录声明」与「真实 `NativePolicyEvaluator(policy.yaml)` 判 `DENY` + `used default policy effect`」）。**射程四面同轮同步**（`tool_providers.yaml` / `_IN_SCOPE`+陈旧条目移除 / `POLICY_SURFACE_AUDIT.md` 声明面列 / provider 夹具）。**`citation.validate` 经实测判定不可行 ⇒ 受限面，不硬接**：取数面（`_elink`）与判定规则都可写，但**声明它**会同时打红两条既有 pin 判据 —— `tests/contracts/test_ncbi_provider_contract.py::…::test_list_tools_schema`（实测 `Left contains one more item: 'citation.validate'`）与 `tests/contracts/test_europe_pmc_pin_and_registration.py::…::test_existing_providers_are_untouched`（实测 `assert ['literature....ion.validate'] == ['literature....tion.inspect']`），两条都在 `tests/contracts/**`（**明文禁改面**）⇒ 命中「**不得为凑数硬接**」；**解除条件** = 该两处 pin 的同轮同步**需用户拍板**。**按压（两向）**：撤回 `run_read` 的能力映射 ⇒ **3 failed**（实现面 / 声明-实现落差 / 射程下界，三条各自点名 `run.read`）；复原 `sha256sum -c` 三文件全 `OK`。`RECHECK-20261005-286` = **PASS_WITH_WARNINGS**（五条 W-NN，含 `runs_store` 共享实例属行为面变化、`composition.py` 结构性压力未解）。本地门：`ruff` / `format` / `mypy`（1097 files）/ 规模门绿；`tests/architecture/python + application/preflight + application/evidence + contracts + loaders + tooling + adapters + e2e + api` **3471 passed / 89 skipped**。**未覆盖范围原样保留**（读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 / D 组审批通道未接通）；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。 |
