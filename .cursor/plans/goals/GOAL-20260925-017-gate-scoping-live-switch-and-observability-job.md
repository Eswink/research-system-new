---
id: GOAL-20260925-017
slug: gate-scoping-live-switch-and-observability-job
title: 三条已授权决策落地：门禁 scoping（git 决定输入面）+ live 显式开关 + 观测作业隔离
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-25 用户会话指令（goal 模式）：**建档 GOAL-20260925-017（三条已授权决策落地）并授权
    本驱动自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **判词来源**：用户按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的**建议列**，对三条
    **此前未授权**项拍板授权并**要求实施**（不再是「维持现状」类）：**D-10 → 取 (a)**、
    **D-11 → 取 (a)**、**D-13 → 取 (a) 的协议 + 授权接近 (b) 的作业隔离**。
    来源同时包括 **push-to-main-for-CI 口径**（只推 `main`、**不 force**、**不重写历史**、
    **不推旁支**；push 前 `git pull --ff-only origin main`）与 **默认姿态不变**
    （默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）。
    (1) **D-10 → 取 (a)，授权实施**：`validate_bundle` 的 **Markdown 链接扫描**排除 gitignored
    路径，**跟踪文件照旧全扫**。授权边界（严格）：
    a) 排除规则必须**由 git 决定**（例如经 `git check-ignore` 或
    `git ls-files --others --exclude-standard` 的**等价判据**），**不得**改成「再往
    `NON_SOURCE_DIRS` 里加几个目录名」（那只是治一个目录名），**不得**按 `scratch/` 字面名特判；
    b) **跟踪文件一律照扫**——gitignored 排除**不得**让任何已跟踪文件逃过扫描（**这是本项的安全
    边界**）；c) 判据必须**成对**：gitignored 的坏文件 ⇒ **不**判红；**同内容但已跟踪**的坏文件
    ⇒ **仍**判红；d) 必须同时解决**门禁自身不可用时的行为**：扫描根不可用时**不得静默通过**，
    应**硬失败**（承 GOAL-015 对该脚本 `--root` / `not_a_git_tree` 的处置口径：结论必须**点名**
    未扫成的面）；e) **不得**为了变绿而放宽被扫内容的**任何检查项**（链接存在性 / 版本号 /
    schema 等**一律不动**）。⇒ **交付终态**：as-is 本机 m0 应能到 **23/23**（`R-3` 消失）；
    若达不到，如实登记并说明是哪一条拦着。
    本项**只改扫描输入范围**，不改任何被判内容的判据。
    (2) **D-11 → 取 (a)，授权实施**：`requires_live_llm` 的开门条件改为**显式开关**
    （建议 `RESEARCHOS_LIVE_E2E=1`；开关名以既有命名习惯为准）；**凭据在场从充分条件降为
    必要条件**。授权边界：a) **默认门（无开关）必须保持「离线且不跑 live 用例」**，且行为**可判**；
    b) 开关 + 凭据**齐备**才跑；**只有开关没凭据**也要**如实**表现（skip 或点名失败，**二者择一
    并把口径写清楚**）；c) 所有 live 用例（`tests/e2e/` 下全部 `requires_live_llm` 标记的模块 +
    任何依赖 `LLM_MAIN_KEY` 的判据）必须**同源**走这套开门逻辑，**不得**留下**第二套判据**；
    d) **不得**为了跑通而放宽 `tests/egress_guard.py` 的**放行面**——放行仍**只由 marker 决定**，
    开关只决定「是否进入 run」，**不扩大放行类别**；e) **文档同源**：
    `docs/integration/LIVE_MODEL_RUNBOOK.md` 与 runbook 里的命令**逐字**更新为新口径。本项
    **不做真实出网调用的常备依赖**（默认门离线）；若判据必须实跑一次 live ⇒ 只在**授权范围内的
    最小必要次数**、跑前确认 `EnvCredentialResolver().has('LLM_MAIN_KEY')`、跑后**不得**把开关
    留在环境或 `.env`，且记录里**不得**出现凭据值。
    (3) **D-13 → 取 (a) 的协议 + 授权接近 (b) 的作业隔离**：
    `tests/observability/test_telemetry_overhead.py` 的**整进程资源阈值判据**
    （`_MAX_RSS_GROWTH_MIB = 128.0` 与同文件线程上限 `_MAX_TELEMETRY_THREADS`）**判据与阈值
    一字不动**；授权把它**拆到独立 CI 作业**（不与其余 4400+ 用例**同进程**排队），以消掉负载
    竞争导致的偶发红。授权边界：a) **不得**提高阈值、**不得**改变测量的语义（RSS 仍是**整进程
    RSS**，**不得**改成「相对量」来绕）；b) **不得**把该判据改成**非阻塞 / 告警**（那等于取消
    门禁）；c) 拆作业后**必须保留**「该 job 失败 ⇒ **整体 CI 判红**」的语义；d) workflow 是
    **治理面**：改动必须**最小**且**可复核**（逐行说明改了什么、为什么），并在记录里写明
    **改动前后**的 job 结构与**失败传播路径**。**先核实现状**（`tests/observability` 已独立步骤
    vs 独立 job 的差异），**按最小改动实现**；**若判定「当前结构已足够、偶发红另有原因」⇒
    如实登记「不改 + 证据」**（**不得**为凑一条交付而改）。本项**只改作业结构**，不改判据。
    (4) **明确不授权（本 GOAL 一律不做，命中即 BLOCKED）**：
    a) **`undici` 主版本跳跃升级**（`5.29.0 → 6.24.0+`，占 8 条告警）——**未授权**；本 GOAL
    只允许引用它作为**事实**（D-03 已登记的「因主版本跳跃未做」），**不得**动它；
    b) **`yaml` 升级**（patch 可升、非 high）——**未授权**；维持现状；
    c) **D-01 的 (a)**（组合根自己接执行体缝）——仍未授权；**不碰执行体缝语义**；
    d) **D-04**（hook 侧 L3 检测层）/ **D-05**（450 行）/ **D-06**（路径 (B)）——仍未授权，
    维持现状；
    e) **D-02 的 (a)**（读类能力成类预放行）——仍为 (b)（逐条）；本 GOAL **不得**新增任何
    allow 规则；
    f) **`ADR-0031` 的 `Status`**——仍 `Proposed`，**不得**改；
    g) **授权面 / 威胁建模的 (a)**（BOLA / BFLA 专项测试与门）——D-12 只做到 (b) 文档级；
    本 GOAL **不做** (a)。
    (5) **不做真实出网**：本 GOAL 的默认门**一律离线**；`tests/egress_guard.py` 是**结构判据**，
    D-11 改的是「**是否进入 live run**」，**不得**改放行类别。URL 校验复用 `endpoint_policy`；
    SQL 一律**参数绑定**；Domain **不得**出现厂商名；观测隐私**不记录完整 Prompt**（§10）。
    (6) **边界**：GOAL-001…016 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；如需指名只允许
    按**只追加**补一行事实更正。GOAL-015 的 13 条人工面 + 承继残余**原样保留**（本 GOAL 只把
    本轮获授权的三项落地，其余继续挂着）。
objective: >
    把用户按简报建议列拍板授权的**三条决定**落地为**可复核的工程事实**——(1) **D-10 门禁
    scoping**：`framework/validate_bundle` 的 Markdown 链接扫描的**输入面**改由 **git 决定**
    （已跟踪 ∪ 未跟踪且未被忽略），从而**别人**的未跟踪在制品（`scratch/`）不再能让本机门判红，
    而**跟踪文件照旧全扫**（安全边界），且**门禁自身不可用 ⇒ 硬失败**（点名未扫成的面）；
    交付后 **as-is 本机 m0 = 23/23**（`R-3` 消失）；(2) **D-11 live 显式开关**：把
    `requires_live_llm` 的开门条件从「环境里恰好有凭据」改为「**显式开关 + 凭据**」，
    使**默认门的结论不再取决于环境里有什么**（默认离线且语义可判），并让**全部** live 判据
    **同源**走同一开门逻辑（**无第二套判据**），runbook 与新口径**逐字同源**；(3) **D-13 观测
    作业隔离**：先**核实现状**，再按**最小改动**把整进程资源阈值判据从「与 4400+ 用例同进程
    排队」的作业里**分离**（或如实登记「现状已足够 + 证据」），**阈值与测量语义一字不动**、
    **失败仍传播为整体 CI 红**；(4) **收口复检 + 残余登记**：两棵树同结论的独立复检脚本 +
    m0 到**可支持的终态行**（**修好 D-10 后应能给出 as-is 23/23**）+ 治理 `validate.py` 绿 +
    CI 台账到终态（M0 六 job + CodeQL，含 `run_attempt`）+ 13 项 `D-NN` 终态表更新。
    **硬约束**：**不放宽/削弱任何判据、检查项或阈值**（D-10 **只**改扫描**输入范围**、
    D-13 **只**改**作业结构**）；不新增策略面 allow；不改 `ADR-0031` 的 `Status`；
    不动 `undici` / `yaml` 的 pin；不改 Canonical State 边界；默认 runtime 仍为 **Fake**、
    默认 CI 仍**离线**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **D-10 门禁 scoping**：`framework/validate_bundle` 的 Markdown 链接扫描的输入面改由
      **git 决定**（已跟踪 ∪ 未跟踪且未被忽略），**不得**按目录名特判、**不得**把名字加进
      `NON_SOURCE_DIRS`。判据**成对**：① gitignored 的坏文件 ⇒ **不**判红；② **同内容但已跟踪**
      的坏文件 ⇒ **仍**判红；③ 扫描根 / git 面**不可用** ⇒ **硬失败**且**点名**未扫成的面
      （不得静默通过）。④ **被扫检查项零放宽**（链接存在性 / 版本号 / schema 一律不动；
      `git diff` 取证）。⑤ **验收终态**：as-is 本机 m0 = **23/23**（`R-3` 消失）；若未达 ⇒
      如实登记是哪一条拦着。
    verify: >-
      ① **反证（先红后绿）**：改动前的同一 gitignored 坏文件（实测证人：
      `scratch/self-governance-bootstrap-prompt.md`，由 `.gitignore:43` 的 `scratch/` 忽略、
      `git ls-files scratch/` 为空）能让门判红 ⇒ 留档为 `scratch/` 的反证记录（`R-3` 的
      m0 日志已是既有证人）；改动后**同一文件在场**仍应判绿。
      ② **成对判据**：判据测试（新增，离线）做三件——(i) 在 gitignored 路径造坏链接文件 ⇒
      该文件**不**出现在判词里；(ii) 把**同内容**的坏链接文件**加进索引**（tracked）⇒ 判词
      **逐字**报出该文件（`Markdown 本地链接不存在`）；(iii) 把 git 面拿掉（`git` 不可用 /
      根不在工作树内）⇒ 判词**点名**未扫成的面且**退出码非 0**；并断言**已跟踪文件仍被扫**
      （例如断言 tracked 集合里某个真实 `docs/**.md` 确实在扫描面内）。
      ③ **零放宽取证**：`git diff` 逐字节证明被扫检查项（`validate_local_markdown_links` 的
      链接存在性、`check_versions` 的版本号 / 旧版本命名、schema / 引用一致性）**未被改**；
      `NON_SOURCE_DIRS` **未新增**任何条目（diff 里不得出现新增目录名）。
      ④ `tests/tooling/` 定向套件 + `ruff` / `format` / `mypy` 绿；`DOCS-CHECK` 绿。
      ⑤ **m0 终态行**：`make validate-all`（独占、仓库 `.venv`、`--keep-going`）到
      `PASS: profile=m0; 23 deterministic checks`（as-is，**不再需要代管**）。
      **Linux 侧复验**：链接 / 路径判据属「Win32 会剥尾点」的假绿面 ⇒ 由 CI 的
      `quality-ubuntu-latest` 复验（本 GOAL 的 CI 台账即该复验证据）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **D-11 live 显式开关**：live 开门条件 = **显式开关 + 凭据**（+ 各模块既有的更强条件），
      开关名 `RESEARCHOS_LIVE_E2E`（`=1` 才算开）；**默认门（无开关）离线且语义可判**。
      全部 live 判据**同源**（**反向搜索证明无第二套**）；`tests/egress_guard.py` 的**放行面
      一字不动**（仍只由 `requires_live_llm` marker 决定，开关**不**扩大放行类别）；
      runbook 与新口径**逐字同源**（含机器判据）。
    verify: >-
      ① **三态各有实跑证据**：(i) **无开关**（本机有凭据）⇒ live 用例**一条都不跑**且
      **零出网**（`egress guard: judged N connection attempt(s); blocked 0`，且无 live 用例
      进入 run）；(ii) **开关 + 无凭据** ⇒ 按**逐字**写明的口径如实表现（本 GOAL 口径 = **skip
      并点名缺哪个条件**，**不是** PASS）；(iii) **开关 + 凭据** ⇒ 至少一条 live 用例**真的
      进入 run**（记录里**不得**出现凭据值）。
      ② **反证**：构造「环境有凭据但**无开关**」⇒ **一次都不出网**（`egress_guard` 判词为证：
      `blocked 0`，且被拦集合为空 / 未出现 live 用例的 nodeid）。
      ③ **同源取证**：反向搜索「谁决定 live 开不开」——`RESEARCHOS_LIVE_E2E` 的读取点
      **唯一**（`packages/application/model_relay/live_run_gate.py`），且既有 gate
      （`evaluate_live_run_gate`）与所有 live 模块的 skip 分支都**经它**决定；把搜索命令与
      输出留档，逐条列出**已消除的第二套判据**（含
      `tests/e2e/test_run_chain_retrieval_live.py` 的 `_live_credentials()` 与各模块的自定义
      skip 条件）。
      ④ **放行面零放宽取证**：`git diff tests/egress_guard.py` **为空**（或逐字证明
      `ALLOWED_KINDS` / `ALLOW_MARKER` / `judge` 判定未被改）。
      ⑤ **runbook 同源**：`docs/integration/LIVE_MODEL_RUNBOOK.md` 的命令逐字更新为新口径；
      `tests/architecture/python/test_runbook_same_source.py`（既有同源判据）**扩充后仍绿**，
      且**可按压**（把 runbook 里的开关名删掉 ⇒ 判红）。
      ⑥ 定向套件（`tests/e2e` + `tests/architecture`）+ `tests/tooling/` + `egress guard`
      = `blocked 0` 绿。
    status: PENDING
  - id: EC-03
    criterion: >-
      **D-13 观测作业隔离**：先**核实现状**再按**最小改动**实现——**阈值与测量语义一字不动**
      （`_MAX_RSS_GROWTH_MIB`、`_MAX_TELEMETRY_THREADS` 与断言行**零改动**，`git diff` 取证）；
      拆作业后**失败仍传播为整体 CI 红**；workflow 改动**逐行**说明；**若判定现状已足够 ⇒
      如实登记「不改 + 证据」**（不得为凑交付而改）。
    verify: >-
      ① **现状核实（先做，留档）**：给出 `tests/observability` 在
      `.github/workflows/m0-quality.yml` 里的**全部**执行点（当前实测：`collector-quality` 是
      独立 **job** 且以 `tests/observability` 为独立**步骤**；`quality-ubuntu-latest` /
      `quality-windows-latest` 经由 `Run all M0 gates` ⇒ `python/tests` 全量套件**同进程**跑到
      它）⇒ 用**证据**说明「偶发红发生在哪一类执行点」（依据：D-13 的实跑证人 =
      run `36071654181` 的 `quality-windows-latest` 判红、同 run `run_attempt=2` 该 job
      `success`，判词 `RSS grew 174.0 MiB (leak suspected)`）。
      ② **判据零改动取证**：`git diff -- tests/observability/test_telemetry_overhead.py`
      **为空**（阈值与断言行均未被改）；`git status` 无该文件条目。
      ③ **作业结构改动**（若做）：workflow 的 `git diff` 逐行说明；`tests/tooling/test_m0_ci_coverage.py`
      （既有 CI 结构判据：跑 Python 门的作业**必须先预热 tokenizer**、`gate_jobs >= 4`、
      `collector-quality` 的 fail-closed 环境变量）**仍绿**；新 job（若有）满足同样约束。
      ④ **失败传播**：证明「该 job 失败 ⇒ 整体 CI 判红」——给出 workflow 层面的事实依据
      （无 `continue-on-error` / 无 `if: always()` 吞失败；run 结论由**任一** job 失败决定），
      并在 CI 台账里记录该 job 的真实结论。
      ⑤ 定向套件（`tests/observability` 独立跑 + `tests/tooling/test_m0_ci_coverage.py`）绿。
    status: PENDING
  - id: EC-04
    criterion: >-
      **收口复检 + 残余登记**：独立复检脚本（**不复用本 GOAL 的叙述**）在**当前树**与
      **干净 checkout** 给出**同一结论**且**非恒真**；m0 到**可支持的终态行**（D-10 修好后
      **as-is 23/23**；若仍只能代管跑法 ⇒ **分行标注**，不得含糊）；治理 `validate.py` +
      `DOCS-CHECK` 绿；CI 台账到终态（M0 六 job + CodeQL + `run_attempt`）；13 项 `D-NN`
      终态表更新（D-10 / D-11 / D-13 从「需授权未实施」→ **已实施 / 已登记**）；承继残余
      **原样保留**。
    verify: >-
      ① 复检脚本（`scratch/goal017-ec04-*`）对每个 EC = 「脚本自己重读树的结构断言」+
      「该 EC 的判据文件在**被测树**里子进程实跑」两路同时成立；② **非恒真**证明：把终态表 /
      开关名 / job 结构之一临时改坏（**只改内存或临时副本，不改仓库文件**）⇒ 脚本判红并逐条报出；
      ③ `--root` 指向工作树与干净 checkout（`git worktree`）两路 `diff`（去掉耗时）**为空**；
      ④ `make validate-all` 的**终态行**与日志留档（含 `size` / `mtime_ns` / `sha256` 复核）；
      ⑤ CI 台账逐行（run id + 链接 + 六 job 逐条 + CodeQL 3/3 + `run_attempt`）；
      ⑥ 治理 `validate.py` = 通过、`DOCS-CHECK PASS`；⑦ 13 项终态表逐行在位；⑧ 承继残余
      （`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-1…W-7`）
      逐条在位。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过（D-10 获授权的**扫描输入面**改动除外）
    - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据使其通过
    - 放宽被扫内容的**任何检查项**（`validate_bundle` 的链接存在性 / 版本号 / schema / 引用一致性）
    - 把目录名加进 `NON_SOURCE_DIRS` 或按 `scratch/` 字面名特判来实现 D-10
    - 放宽 `tests/egress_guard.py` 的目的地判定 / 放行面 / 豁免 fake-IP（`198.18.0.0/15`）
    - 放宽 m0 任一 check 的阈值（含 450 行 / 50 行规模门禁；含 D-13 的 RSS 与线程阈值）
    - 改 `tests/observability/test_telemetry_overhead.py` 的阈值 / 测量语义 / 断言行
    - 把 D-13 的判据改成非阻塞或告警（等于取消门禁）
    - 让 CI 作业失败不再传播为整体判红（`continue-on-error` / `if: always()` 吞失败）
    - skip/删除测试、加 xfail、或调整收集顺序以掩盖顺序依赖
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何策略面 allow 或**类别级规则**（D-02 明文不取 (a)）
    - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）
    - 改 `ModelCompatibilityProfile` 的 Domain 面 / Canonical State 边界
    - 动 `undici` / `yaml` 的 pin 或新增任何依赖（两项均明文不授权）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    **改门禁 / 阈值 / 作业结构超出本授权范围**（本 GOAL 只授权：D-10 的 Markdown 链接扫描
    **输入面**由 git 决定；D-13 的**作业结构**最小改动；两者之外的任何门禁 / 阈值 / 检查项
    改动）—— **立即 BLOCKED**
  - >-
    放宽任一判据 / 门禁 / 放行面 / 阈值（含 `tests/egress_guard.py` 的目的地判定、
    `validate_bundle` 的检查项、m0 任一 check 的阈值、`test_telemetry_overhead.py` 的 RSS
    与线程阈值）—— **立即 BLOCKED**
  - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据 —— **立即 BLOCKED**
  - >-
    以 skip / xfail / 删除测试 / 调整收集顺序的方式让顺序失败「消失」—— **立即 BLOCKED**
  - >-
    放宽 §9 默认 deny，或新增任何策略面 allow / 类别级规则（D-02 明文不取 (a)）——
    **立即 BLOCKED**
  - >-
    **新增依赖或 pin 变更**（含 `undici` 主版本跳跃、`yaml` patch）—— **立即 BLOCKED**
  - Canonical State 边界 —— **立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；只做「显式开关才启用」）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复不开门**，**不得**放宽放行面
  - 明文凭据泄露（**即使是可弃用的免费额度**）—— 立即停止并报告
child_plans: []
latest_recheck: null
memory_entries: []
---

## 目标与退出标准

**一句话**：把用户拍板授权的**三条决定**（D-10 门禁 scoping / D-11 live 显式开关 /
D-13 观测作业隔离）落地为**可复核的工程事实**，且**只动**「扫描输入范围」（D-10）与
「**作业结构**」（D-13）—— 一切被判内容、阈值与测量语义**一字不动**。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **D-10(a)** Markdown 链接扫描的输入面由 **git** 决定 | 判据（成对 + 硬失败）+ 反证留档 + `git diff` 零放宽 + as-is m0 **23/23** | PENDING |
| EC-02 | **D-11(a)** live 开门 = **开关 + 凭据**，全部判据**同源** | 单一开关读取点 + 消除第二套判据 + 三态实跑 + runbook 同源 | PENDING |
| EC-03 | **D-13(a)+(b)** 观测阈值判据的**作业隔离**（或如实登记「不改 + 证据」） | 现状核实 + 最小 workflow 改动 + 失败传播取证 + 阈值零改动 | PENDING |
| EC-04 | 收口复检 + 残余登记 | 两树复检脚本 + m0 可支持终态行 + 13 项 `D-NN` 终态表 + CI 台账 | PENDING |

**依赖关系**：EC-01 / EC-02 / EC-03 **互相独立**（一个门禁脚本 / 一个门开关 / 一个 workflow
作业结构），三者的**判据都不依赖**另外两项；EC-04 **最后**做，且**必须**在三项落地后
重跑 m0（because EC-01 改变 as-is m0 的终态行）。

**建档当日已核实的文件层事实（决定可行性与判据形态）**：

1. **D-10 的 as-is 机制**（实测，`validate_bundle.py` 1195 行；该路径**不在** 450 行门禁的
   覆盖面内：`tests/tooling/test_python_source_limits.py` 的 `PRODUCT_ROOTS` 只含
   `apps` / `services` / `packages` / `adapters` / `tests`）：
   - 硬编码排除集 `NON_SOURCE_DIRS`（`:42`–`:53`）= `.git` / `.mypy_cache` / `.venv` /
     `node_modules` 等**目录名**集合；
   - `repository_files()`（`:56`–`:60`）用 `os.walk(ROOT, topdown=True)` 遍历**整个工作区**；
   - Markdown 链接扫描 `validate_local_markdown_links()`（`:1147`–`:1163`）逐文件
     `read_text` + 正则找本地链接 ⇒ **别人**的未跟踪在制品能判红；
   - **同一遍历还被另两处消费**：`check_versions()` 的「旧项目版本引用」扫描（`:279`）与
     「旧版本命名文件」扫描（`:297`）⇒ 本 GOAL **只**把 **Markdown 链接扫描**的输入面
     改由 git 决定，**另两处保持全工作区**（边界 e：版本号检查项**不动**）。**这是刻意的
     范围围栏**，不是遗漏。
2. **`R-3` 的现状证人（实测，2026-09-25 建档当日）**：
   `git check-ignore -v scratch/self-governance-bootstrap-prompt.md` ⇒
   `.gitignore:43:scratch/`；`git ls-files scratch/` = **空**（未跟踪）；
   `git ls-files --others --exclude-standard` = **0**（当前没有「未跟踪且未被忽略」的文件）；
   `git ls-files --cached` = **3403**。⇒ 「已跟踪 ∪ 未跟踪且未被忽略」在本仓**当前等价于
   3403 条已跟踪路径**，`scratch/` 整体落在外面。
3. **D-10 的硬失败先例**：`tools/credential_audit.py` 在根不是工作树时记 `not_a_git_tree`
   并**判红**（`UNSCANNABLE_STATUSES`），判据在 `tests/tooling/test_credential_audit.py:125`
   断言「结论必须点名未扫成的面」⇒ 本 GOAL 的 git 面不可用时**沿用同一口径**（点名 + 硬失败）。
4. **D-11 的 as-is 机制**（实测）：
   - **既有单一门**：`packages/application/model_relay/live_run_gate.py`（86 行）的
     `evaluate_live_run_gate(credentials=, endpoint=, agent_runtime=, live_agent_runtime=)`
     —— 条件 = `agent_runtime == live_agent_runtime` **且** `credentials.has(ref)`；
     **没有**任何「显式开关」；**≥8 个** live 模块经它 skip
     （`test_real_protocol_run_live` / `test_real_deliverable_contract_live` /
     `test_evidence_chain_source_live` / `test_ec04_live_first_run` /
     `test_ec02_experiment_live` / `test_real_control_plane_retrieval_live` /
     `test_real_control_plane_experiment_live` / `test_live_failure_paths`）。
   - **第二套判据（要消除的面）**：`tests/e2e/test_run_chain_retrieval_live.py:70` 的
     `_live_credentials()` 只看「端点声明 + 凭据在不在」；另有自定义 skip：
     `tests/e2e/test_ec03_real_runtime_offline_chain.py:383`（`RESEARCHOS_LIVE_E2E_ENDPOINT`
     + `RESEARCHOS_LIVE_E2E_KEY`）、`tests/e2e/test_m12_usage_real_relay.py:127`（同名两变量）、
     `tests/e2e/test_live_model_absence.py:114`（`RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1`）、
     `tests/e2e/test_live_failure_paths.py:64`（`RESEARCHOS_LIVE_FAILURE_CASE`）。
   - **放行面**：`tests/egress_guard.py:59`–`:61` = `ALLOWED_KINDS = {"localhost"}` +
     `ALLOW_MARKER = "requires_live_llm"`；`judge()` 的放行式 = `kind in ALLOWED_KINDS or
     self._allows_egress`，而 `_allows_egress` 只由 `tests/conftest.py:144` 的 marker 决定
     ⇒ **开关不得进入这条式子**（边界 d）。
   - **runbook 同源判据已在树**：`tests/architecture/python/test_runbook_same_source.py`
     （181 行）机器强制「runbook 里反引号引用的**每个仓库路径 / ENV 名 / pytest 目标**都真实
     存在」，且 `test_switching_section_names_the_real_switch` 已锁
     `RESEARCHOS_AGENT_RUNTIME` + `openhands` ⇒ D-11(e) 的「逐字同源」有**现成载体**。
   - **凭据面**：`tests/default_gate_credentials.py` 的 `LIVE_CREDENTIAL_KEYS = ("LLM_MAIN_KEY",)`
     + `tests/conftest.py:39`–`:54` 的 autouse 夹具（未标记 marker 的用例**看不见**出厂凭据）。
5. **D-13 的 as-is 机制**（实测）：
   - workflow `.github/workflows/m0-quality.yml`（276 行）的 job 结构 = `quality`（**矩阵**
     `ubuntu-latest` + `windows-latest`，步骤 `Run all M0 gates` ⇒ m0 全量，含
     `python/tests` **全量套件**）/ `eval-gate` / `container-quality` / `collector-quality`
     （**独立 job**，步骤在 `:208`–`:214` 显式跑 `tests/observability` + `tests/postgres` +
     `tests/distributed` + `tests/e2e/test_pg_crash_restart.py`）/ `console-frontend`
     ⇒ **六个** job 结论。
   - **判据 as-is**：`tests/observability/test_telemetry_overhead.py` 的
     `_MAX_TELEMETRY_THREADS = 4`（`:34`，断言 `:138`）、`_MAX_RSS_GROWTH_MIB = 128.0`
     （`:36`，断言 `:150`），测量 = 同一进程内 `_rss_mib()` 前后差（**整进程 RSS**）；
     文件带 `@pytest.mark.timing_sensitive` 的邻条（`:101` / `:153`）。
   - **CI 结构判据已在树**：`tests/tooling/test_m0_ci_coverage.py` 机器强制
     「跑 Python 门的作业必须在跑门前**预热 tokenizer**」+「`collector-quality` 的
     `RESEARCHOS_REQUIRE_COLLECTOR` / `RESEARCHOS_REQUIRE_POSTGRES` = 1」+
     「`container-quality` 必须含 `-m requires_docker`」+ 反证 `gate_jobs >= 4`
     ⇒ **任何新 job 都必须满足同样的预热门位置关系**。
   - **flake 的 as-is 证人**（D-13 简报原文）：run `36071654181` 的 `quality-windows-latest`
     判红（`AssertionError: RSS grew 174.0 MiB (leak suspected)`），**同一 run
     `run_attempt=2` 该 job success**；同一提交的 `quality-ubuntu-latest` 与 CodeQL 全绿。
6. **不动项（明文不授权）**：`undici`（主版本跳跃）/ `yaml`（patch、非 high）/ D-01(a) /
   D-02(a) / D-04 / D-05 / D-06 / `ADR-0031` 的 `Status` / D-12(a) —— **本 GOAL 一律不碰**。
7. **工作树有并发写者**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
   `packages/domain/model_drift.py`、`services/api/dto/models.py`，建档实测**内容 diff 为空**、
   仅行尾差异）⇒ **不碰、不提交**这三处；只按显式路径提交本 GOAL 自己的产物。
8. **承继起点（事实，不是待办）**：GOAL-016 的 13 项 `D-NN` 终态表 + 承继残余
   （`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` + `W-1…W-7`）
   原样保留；本 GOAL 只把**本轮获授权的三项**从「未实施」改为「已实施 / 已登记」。
   `R-3` 是 `R-F3` 的同源事实，**由 EC-01 收口**。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 的默认门一律离线**（本机跑 live 需要显式开关 + 凭据；见 EC-02 的最小必要次数口径）。

## 循环入口协议

驱动方（会话 / 定时自动化 / 客户端 goal 模式）进入时，按**迭代日志最后一行** +
**工作树 / 远端实况**判定续点；**禁止凭记忆假设上一轮状态**：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①（先 derive 子 PLAN）。
2. 有子 PLAN 但仍在 `IN_PROGRESS` → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待 / 判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后**立即回写本文件**（状态历史 / 迭代日志），保证任意时刻崩溃后重入可续。
同时只允许一个驱动持有 ACTIVE cycle 的推进权；**另一驱动持有未收口 ACTIVE cycle 时等待**。

**每轮只读入口必需的最小集**（`per_cycle_minutes=120` 是硬预算）：本文件 + 当前子 PLAN +
其引用的判据 / 证据；不整目录通读。

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-017-*.md` 已存在 ⇒ 跳过建档，直接进循环。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260925-017`
  并投影 `ALL_PLAN`，**同一提交**）。子 PLAN 编号续**全局 NNN**（建档当日实测：
  `.cursor/plans/tasks/` 最大 = `PLAN-20260925-178`、`.cursor/plans/rechecks/` 最大 =
  `RECHECK-20260925-179` ⇒ 下一个 PLAN / RECHECK 从 **180** 起；`MEM` 下一个 = **140**）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查**规模门禁**（50 行函数 / 450 行文件；
  `tests/tooling/test_python_source_limits.py` 的覆盖面 = `apps` / `services` / `packages` /
  `adapters` / `tests` ⇒ **EC-02 要动的测试与产品文件都在覆盖内**，其中
  `tests/e2e/test_ec03_real_runtime_offline_chain.py` = **398 行**（52 行余量）、
  `packages/application/model_relay/live_run_gate.py` = **86 行**；
  `.cursor/skills/**` 的脚本**不在**覆盖内）与**快照类门禁**（OpenAPI / 设计基线），
  再跑 `make validate-all`（m0 全量 23 项，**独占运行**，**用仓库 `.venv`**，
  避免 `evolution_state.json` 的 `WinError 5` 与假红）+ 受影响定向套件 + web 门。
  **默认门一律离线**（`tests/egress_guard.py` 是结构判据——D-11 改的是「**是否进入 live
  run**」，**不得**改放行类别）；**本地不绿不得 push**（承 `MEM-20260924-125`）。
  **写记录时不要跑 m0**（承 `W-5`：m0 运行中改工作树会让 `framework/validate` 判红）。
  **`CURSOR_FRAMEWORK_ROOT` 的作用域**：它重定向**整个 m0 runner**（不是单个 check）
  ⇒ 用它做定向复验时，注意别把「根」指偏而让别的 check 看到别的树。
  **Linux 侧复验（本 GOAL 尤其要紧）**：`...` 形式链接在 Win32 会**剥尾点** ⇒ **EC-01 直接
  改链接扫描**、**EC-02 改 runbook 命令**，两者的判据都必须在 **Linux 侧**（CI 的
  `quality-ubuntu-latest`）复验；本机绿不等于跨平台绿。
- **④ commit**：显式路径；**绝不 `git add -A`**（并发工作树）。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（只推 main）→
  轮询 CI 到终态（`scratch/poll_ci_all.sh <sha>`：M0 六 job + CodeQL），记录 run id / 链接 /
  逐 job 结论 / **`run_attempt`**（**flake 判定必须靠同一代码的复跑对照**，不得只看一次结论）；
  **本机无法验证记 PENDING 并停止推进**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；超 `fix_policy` 或命中 `escalation_triggers`
  ⇒ `status: BLOCKED`。
- **⑦ 回写**：EC / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史；
  **收尾前必须回写**；`child_plans` 与 `memory_entries` 每轮与实际派生对齐。
  **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
  **CI 台账沿用既有闭合约定**：写下本条的那个提交自身的 run 只在**回合汇报**记账。

**撤回纪律**（承 GOAL-011…016）：改共享夹具 / 契约 / **门禁**时先数清谁拿它的
**失败形态**当夹具 —— **本 GOAL 有两处高危面**：① EC-01 改的是**门禁脚本本身**
（`validate_bundle.py` 被 `framework/validate_bundle` 调用，且
`CURSOR_FRAMEWORK_ROOT` 会把整轮 m0 重定向到它）；② EC-02 改的是 **live 门的语义**
（`R-3` 之外的 `W-7` 现象 = 本机有凭据时 live 用例**真出网**；收紧后**任何**依赖
「凭据在场即跑」的既有判据 / 夹具都可能由绿转红）。CI 判红且根因是夹具语义冲突 ⇒
**优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| **门禁输入面引发的红**（EC-01 主场） | `framework/validate_bundle` 报 `Markdown 本地链接不存在` 但**该路径未跟踪** | 先判「是否 gitignored」：是 ⇒ **属于 EC-01 要消除的那一类**（改**输入面**，不改判词）；否（**已跟踪**）⇒ **真红**，按链接实际修复 |
| **live 门语义变化引发的红**（EC-02 主场） | 收紧后某判据由「跑」变「skip」或由绿转红 | 先判该判据**是否属于 live 面**：是 ⇒ 按 EC-02 口径**如实 skip**并登记；否 ⇒ 真红，修产品 / 夹具（**不得**为了让它绿而放开开关读取点） |
| **作业结构引发的红**（EC-03 主场） | 新 job 报 tokenizer 未预热 / 覆盖缺口 / `test_m0_ci_coverage.py` 判红 | 按既有结构判据补齐（预热步骤位置、`gate_jobs` 反证）；**不得**放宽 `test_m0_ci_coverage.py` |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`R-3` 外来文件、`W-7` live 上游瞬时） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 归因；**D-13 类**若在**新结构**下**再次**偶发红 ⇒ 如实登记（**判据与阈值一字不动**）；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态。**未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**改门禁 / 阈值 / 作业结构超出授权**、
  **放宽 §9 默认 deny**、**新增依赖或 pin 变更**、**Canonical State 边界**、
  **把真实 runtime 设为默认**、改 `ADR-0031` 的 `Status`）、同一失败签名超过
  `fix_policy` 上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles` 个 cycle
  未推进任何 EC ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含 13 项 `D-NN` 终态表）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。
- **本 GOAL 的收口判词必须写明**：**as-is 本机 m0 的终态行**（D-10 修好后应为 **23/23**；
  若未达 ⇒ 如实登记**是哪一条**拦着）、以及 **D-13 是「改了作业结构」还是「登记不改」**。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。
**本节照抄 GOAL-016 的 13 条 + 其特有项 + 承继残余**，并在每条注明**本 GOAL 的拍板结果**
（用户按简报建议列拍板，2026-09-25）。

**GOAL-016 的 13 条编号项（原样承继 + 本 GOAL 拍板结果）**：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——**已拍板：D-07 取 (b)**
   ⇒ 维持 `Proposed` + 已有「否证条件」节（GOAL-016 EC-04 已实施）；
   **本 GOAL 不动它的 `Status`**。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——**已拍板：D-12 取 (b)** ⇒ 文档级草案已在位
   （GOAL-016 EC-05 已实施）；**本 GOAL 不做 (a)**（专项测试与门）。
3. **`artifacts/` token 清理**——**【已完成】**（GOAL-011 建档实测 `git ls-files artifacts/` = 0）
   ⇒ **本项无待办**。
4. **450 行纪律的贴线文件**——**已拍板：D-05 取 (b)** ⇒ 维持「触线即拆」；
   **本 GOAL 不拆分**（本 GOAL 要动的文件均有余量，见「目标与退出标准」第 5 条实测）。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——**已拍板：D-03 取 (b)**，且
   `vite` `6.3.5 → 6.4.3` 已由 GOAL-016 EC-03 实施完毕 ⇒ **本 GOAL 不做任何 pin 变更**：
   `undici`（主版本跳跃）与 `yaml`（patch、非 high）**明文未授权**。**任何越界 pin 变更 = BLOCKED**。
6. **hook 侧 L3 门**——**未拍板**（简报建议 (a)）；**本 GOAL 不实施**，D-04 原样挂着。
7. **把真实 runtime 设为默认**——**标准禁令（无需拍板）**：默认必须仍是 Fake。
8. **为 anthropic 形态引入 SDK / 新依赖**——**标准禁令（无需拍板）**：需要新依赖即 BLOCKED。
9. **把凭据写进 CI**——**标准禁令（无需拍板）**：CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——**已拍板：D-08 取 (b)**
    ⇒ 维持**派生视图**（GOAL-016 EC-04 已把依据写成可引用文档）；**本 GOAL 不碰**。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——**标准禁令（无需拍板）**：明文禁止。
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本）**——**【已完成】**
    （GOAL-011 获删授权并执行完毕）⇒ **本项无待办**。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**——**已拍板：D-09 取 (a)**
    ⇒ `ADR-0032` 已在位（GOAL-016 EC-04）；**不重命名**、不触碰不可变历史资产。

**GOAL-016 特有的项（原样承继 + 本 GOAL 拍板结果）**：

- **路径 (B) 的 5 条重设计项**（`docs/roadmap/PATH_B_REFUTATION_RECORD.md`）——**已拍板：D-06 取 (c)**
  ⇒ 维持「已否证」原状；**本循环不重启**该路线。
- **`W-A` 之外的策略面放宽**——**已拍板：D-02 取 (b)** ⇒ **维持逐条**、**不成类预放行**、
  **不新增任何 allow**；**本 GOAL 零策略面改动**。
- **门禁 scoping 的自我修正**（`R-3`）——**本轮已拍板：D-10 取 (a) 并授权实施**
  ⇒ **本 GOAL 的 EC-01**；授权边界 = 只改 **Markdown 链接扫描的输入面**、必须**由 git 决定**、
  **跟踪文件照旧全扫**、判据**成对**、门禁不可用 ⇒ **硬失败**、**被扫检查项零放宽**。
- **本机环境的 DNS / 代理特殊性**（fake-IP `198.18.0.0/15`）——**不改机器网络配置**，
  也不改判据；只做归因与登记。
- **`M-1`（出厂组合根是否自己接执行体缝 `ApiDeps.tool_providers`）**——**已拍板：D-01 取 (b)**
  ⇒ 维持装配方补执行体；判据已由 GOAL-016 EC-01 落地。
  **D-01 的 (a) 明确不取** ⇒ **本 GOAL 不碰执行体缝语义**。
- **live 判据的开门条件**——**本轮已拍板：D-11 取 (a) 并授权实施** ⇒ **本 GOAL 的 EC-02**；
  授权边界 = 默认门**必须**保持「离线且不跑 live」、开关 + 凭据齐备才跑、**同源无第二套判据**、
  **不得**放宽 `egress_guard` 放行面、runbook **逐字同源**。
- **CI 资源阈值型判据的负载敏感性**——**本轮已拍板：D-13 取 (a) 的协议 + 授权接近 (b)**
  ⇒ **本 GOAL 的 EC-03**；授权边界 = **阈值与测量语义一字不动**、**不得**改成非阻塞、
  拆作业后**必须**保留「该 job 失败 ⇒ 整体 CI 判红」、workflow 改动**最小且逐行可复核**；
  **若现状已足够 ⇒ 如实登记不改**。
- **hook 侧 L3 检测层**（D-04）——**未拍板**；**本 GOAL 不实施**。

**承继的诚实边界（如实保留，不是待办）**：

- `R-F1`｜收敛 / 一致性判定含主观面时必须先**操作化**。
- `R-F2`｜真实数据 / 调用规模不足时的**诚实边界**。
- `R-F3`｜仓库外并发写者文件致 **as-is 本地 m0 可能停在非全绿**（等同 `R-3`）；
  CI 检出无 `scratch/` ⇒ **CI 不受影响**。**EC-01 落地后本项应随之收口**（同一事实）；
  未转绿前**不得**声称本地全绿。
- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
- **`R-D1`｜Dependabot 告警**——`vite` 的 4 条 high 已由 GOAL-016 EC-03 清掉；
  **剩余（`undici` 8 条 + `yaml` 1 条）原样保留**，且**两项升级明文未授权**。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，原样保留。
- **`W-1…W-6`**（GOAL-015 的观察项）——原样保留。
- **`W-7`（live 判据在「环境里恰好有凭据」时会真的出网）**——**本 GOAL 的 EC-02 正是消除
  该现象的授权**：收紧后**默认门**（无开关）不再因「环境里有凭据」而改变行为；
  但**开关 + 凭据**下 live 用例**仍会真出网**（这是设计，不是缺口）⇒ 该观察项的**残余部分**
  （「跑 live 时结论随上游 / 环境变」）**原样保留**。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 见回合汇报 | 治理 `validate.py` = 通过 | 见回合汇报（台账尾巴） | — | EC-01…EC-04 全 PENDING；三条授权判词已落 frontmatter；起点已定位（D-10：`NON_SOURCE_DIRS` + 全工作区 `os.walk` + 链接扫描；`scratch/` 被 `.gitignore:43` 忽略且未跟踪、`--others --exclude-standard` = 0、tracked = 3403；D-11：既有单一门 `live_run_gate.py` 无开关，`_live_credentials()` 等至少 5 处**第二套判据**待消除，`egress_guard` 放行面 = marker，runbook 同源判据已在树；D-13：`collector-quality` 已独立 job 且显式跑 `tests/observability`，但 `quality-*` 的全量套件**同进程**也跑它 ⇒ 最小改动面待 EC-03 核实）。**建档时零代码改动**（只增本文件） | cycle 1 = **EC-01 D-10 门禁 scoping**（git 决定的输入面 + 成对判据 + 硬失败） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-017 落地） | 见回合汇报 | 见回合汇报 | —（台账尾巴：本行所在提交的 run 终态在**回合汇报**给出） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | ACTIVE | 建档：用户会话指令（goal 模式）按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的**建议列**拍板三条并**授权实施**（D-10(a) / D-11(a) / D-13(a)+(b)）；四 EC 设计（D-10 门禁 scoping / D-11 live 显式开关 / D-13 观测作业隔离 / 收口复检）。**明确不授权**：`undici` 与 `yaml` 升级、D-01(a)、D-02(a)、D-04、D-05、D-06、`ADR-0031` 的 `Status`、D-12(a)。**建档时零代码改动**（只增本文件）。 |

## 13 项 `D-NN` 终态表（EC-04④）

口径：**拍板结论** = 2026-09-25 用户会话指令的判词（与
`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的「建议」列同源）；**本轮是否实施** =
GOAL-017 的四个 EC 里**实际做了什么**（未授权项一律「未实施」并给阻断依据）；
**不做会怎样** = 该简报条目的原文口径（缩略引用，**不改判**）。
**「未实施」不等于「不需要」**：未授权项**原样保留**为下一轮输入。
**建档时本表 = 承继 GOAL-016 的终态 + 三处改为「已授权、待实施」**（EC 收口时逐行改为
「已实施 / 已登记」并补证据）。

| ID | 主题 | 拍板结论 | 本轮是否实施 | 依据 | 不做会怎样 |
| --- | --- | --- | --- | --- | --- |
| D-01 | 出厂组合根是否自己接执行体缝（`M-1`） | 取 (b)：缝仍由装配方补，但把「缺执行体必须**点名**」写成机械判据 | **已实施**（GOAL-016 EC-01） | 判据 `tests/application/preflight/test_missing_executor_is_named.py`（`4 passed`）；模板在生产源里**单一来源**；**产品代码零改动** | 装配方各自决定怎么补 ⇒「同协议两套装配」的老问题可能以新形态回来 |
| D-02 | 读类能力是否**成类**预放行 | 取 (b)：维持**逐条**放行（不成类、不新增任何 allow） | **已实施**（GOAL-016 EC-02） | 判据 `tests/application/preflight/test_read_grant_is_per_item.py`（`4 passed`）；**零策略面改动** | 新增读能力会反复撞 `default_effect`，每撞一次就是一次 GOAL 级授权 |
| D-03 | 依赖 pin 升级（`R-D1`） | 取 (b)：**分批升**、**high 先升** | **部分实施**（GOAL-016 EC-03）：4 条 high 全在 `vite`，`6.3.5 → 6.4.3`（6.x 内 minor） | `pnpm-lock.yaml` 解析版本对照 + 全量 web 门 + m0 全绿；**未做**：`undici`（主版本跳跃）、`yaml`（非 high）⇒ **本 GOAL 明文不授权** | 供应链告警持续存在；`undici` 8 条 + `yaml` 1 条**原样保留** |
| D-04 | hook 侧 L3 检测层 | **未授权**（明文不授权 D-04） | **未实施**（**原样保留**） | 用户指令的不授权清单；本 GOAL 未触碰 `.cursor/hooks/` | hook 侧仍然**失败开放**，任何「安全已检查」的宣称都不成立（`R-M1` 原样保留） |
| D-05 | 450 行贴线文件 | **未授权**（明文不授权 D-05） | **未实施**（**原样保留**） | 用户指令的不授权清单；`R-B1` 的四个 450 行零余量文件**未**被本 GOAL 改动 | 贴线文件继续零余量，改动它们必须先搬代码（本 GOAL 的 SOP 已按此执行） |
| D-06 | 路径 (B) 的 5 条重设计项 | **未授权**（明文不授权 D-06） | **未实施**（**原样保留**） | 用户指令的不授权清单 | 该路线保持关闭 —— 已知且**可接受的现状**，不是遗漏 |
| D-07 | `ADR-0031`（`tool_pack.*`）是否采纳 | 取 (b)：维持 `Proposed`，补「否证条件」，**不改 `Status`** | **已实施**（GOAL-016 EC-04）；**本 GOAL 不碰** | `ADR-0031` 有 `## 否证条件` 节；`Status` 逐字仍 `Proposed`；判据硬断言全文无 `Status: Accepted` | 「何时该改判」无人可查 |
| D-08 | `ModelCompatibilityProfile` 是否一等域实体 | 取 (b)：维持**派生视图** | **已实施**（GOAL-016 EC-04）；**本 GOAL 不碰** | `MODEL_COMPATIBILITY.md` §9 记下决定 + 「若要 (a) **必须先出 ADR**」；**Domain 边界零改动** | 现状可用，属**登记**而非缺口 |
| D-09 | 非 ASCII 路径豁免是否需 ADR | 取 (a)：出 ADR 记录豁免（30 条，**不重命名**） | **已实施**（GOAL-016 EC-04） | `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`（`Status: Accepted`）+ 判据「现实 ↔ 清单」**双向**比对 | 豁免继续以「口径」形式存在 |
| D-10 | 门禁 scoping：`validate_bundle` 扫描 gitignored 工作区（`R-3`） | **本轮拍板：取 (a) 并授权实施**——Markdown 链接扫描的**输入面由 git 决定**，跟踪文件照旧全扫 | **已授权、待实施**（**本 GOAL 的 EC-01**） | 授权原文见本文件 `authorization.ref` (1)（边界 a–e）；as-is 事实：`scratch/` 被 `.gitignore:43` 忽略且未跟踪、`--others --exclude-standard` = 0、tracked = 3403 | as-is 本机 m0 停在 **22/23**，且红项来自**别人**的未跟踪文件；CI 不受影响（检出无 `scratch/`） |
| D-11 | live 判据的开门条件 = 环境恰好有凭据 | **本轮拍板：取 (a) 并授权实施**——显式开关 + 凭据（凭据由**充分**降为**必要**） | **已授权、待实施**（**本 GOAL 的 EC-02**） | 授权原文见 `authorization.ref` (2)（边界 a–e）；as-is 第二套判据 ≥5 处（见「目标与退出标准」第 4 条实测） | 默认门结论继续取决于**环境里有没有凭据**；CI 上过期 secret 会让默认门**真出网**并判红 |
| D-12 | 威胁建模 / 授权面覆盖（BOLA / BFLA） | 取 (b)：文档级草案；**(a) 仍需另行拍板** | **已实施 (b)**（GOAL-016 EC-05）；**本 GOAL 不做 (a)** | `docs/security/THREAT_MODEL.md` 第 6 节（含 6.3 未覆盖范围 / 6.4 与 M18 边界）；**diff 只含 docs** | 授权面覆盖缺系统性论证；`R-M1` 无法据此收口 |
| D-13 | CI 上「资源阈值型判据」的负载敏感性 | **本轮拍板：取 (a) 的协议 + 授权接近 (b) 的作业隔离**——判据与阈值一字不动，只改**作业结构** | **已授权、待实施**（**本 GOAL 的 EC-03**；若判定现状已足够 ⇒ 登记不改） | 授权原文见 `authorization.ref` (3)（边界 a–d）；as-is 证人 = run `36071654181` 的 `quality-windows-latest` 判红、同 run `run_attempt=2` success | 同类判据会继续在**负载高**的运行器上偶发判红，每次都要人工复跑 + 归因，且**红绿不一致会削弱结论可信度** |

**汇总（建档时）**：**已实施 6 项**（D-01 / D-02 / D-03 部分 / D-07 / D-08 / D-09 / D-12）
**+ 已授权待实施 3 项**（D-10 / D-11 / D-13 = 本 GOAL 的 EC-01…EC-03）
**+ 未授权 4 项**（D-04 / D-05 / D-06 与 D-01(a) / D-02(a) / D-12(a) 的 (a) 面）。
**未授权项一律原样保留**，其红 / 缺口**未**被本 GOAL 收口，也**未**被本 GOAL 掩盖。

## 当前续点

- **GOAL-017 = ACTIVE（2026-09-25 建档）**：cycle 0 = 建档（本文件，**零代码改动**）；
  cycle 1 = **EC-01 D-10 门禁 scoping**；cycle 2 = **EC-02 D-11 live 显式开关**；
  cycle 3 = **EC-03 D-13 观测作业隔离**（先核实现状，允许「登记不改」）；
  cycle 4 = **EC-04 收口复检 + 残余登记**。
- **续点判定**：cycle 0 完成后 ⇒ **下一步 = cycle 1（EC-01）**。
- **进度**：EC-01…EC-04 全 **PENDING**（budget `max_cycles: 20`，用掉 0；
  `no_progress_stop_cycles: 2` 未触发）。
- **依赖面**：**本 GOAL 不做任何 pin 变更**（`undici` / `yaml` 明文未授权）；
  `vite` 已由 GOAL-016 EC-03 停在 `6.4.3`。
- **开局已核实的文件层事实（决定可行性）**：
  1. **D-10 的改动点是单点**：`validate_bundle.py` 的 `validate_local_markdown_links()`
     与 `repository_files()`；**同一遍历还被 `check_versions()` 的两处消费** ⇒ 本 GOAL
     **只**把链接扫描的输入面收窄（**刻意围栏**，见「目标与退出标准」第 1 条）。
  2. **R-3 的证人与终态**：`scratch/self-governance-bootstrap-prompt.md`（gitignored、未跟踪）
     是本机 m0 唯一红项的来源 ⇒ EC-01 落地后 as-is 应到 **23/23**。
  3. **D-11 的单一门已在树**：`live_run_gate.py` 被 ≥8 个 live 模块复用 ⇒ 把开关放这里
     是**最小同源改动**；**要消除的第二套判据** ≥5 处（清单见第 4 条实测）。
  4. **runbook 同源判据已在树**：`tests/architecture/python/test_runbook_same_source.py`
     ⇒ EC-02(e) 的「逐字同源」可机器强制（并可按压）。
  5. **D-13 的两类执行点**：`collector-quality`（独立 job、显式步骤）vs
     `quality-*`（全量套件**同进程**）⇒ EC-03 先核实「偶发红属于哪一类」再决定最小改动。
  6. **CI 结构判据在树**：`tests/tooling/test_m0_ci_coverage.py` ⇒ 任何新 job 必须满足
     「跑 Python 门之前先预热 tokenizer」且不得让 `gate_jobs >= 4` 的反证失效。
  7. **跑法**：m0 与代管脚本**一律**走 `uv run --frozen --no-sync python -B …`；
     m0 全量**独占运行**、用**仓库 `.venv`**；**写记录时不要跑 m0**。
  8. **全局编号**：下一个 `PLAN` / `RECHECK` = **180** 起（PLAN 偶、RECHECK 奇）；
     `MEM` 下一个 = **140**。
  9. **工作树并发写者**：`apps/web/src/features/models/ModelDetails.tsx` /
     `packages/domain/model_drift.py` / `services/api/dto/models.py`（内容 diff 为空）
     ⇒ **不碰、不提交**。
