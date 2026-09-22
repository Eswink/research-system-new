---
id: PLAN-20260922-137
slug: offline-gate-tokenizer-declaration
title: 「默认 CI 离线」的措辞与判据同源：把 tokenizer 预热做成受判的声明（GOAL-011 EC-05）
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
    GOAL-20260922-011 cycle 8 = EC-05（`R-6` 词表固化，可选）。授权来源：2026-09-22 用户 goal 模式
    指令 frontmatter `authorization.ref`——(1) push-to-main-for-CI（只推 main、不 force、不重写历史）；
    (2) 默认 runtime 保持 Fake、默认 CI 离线；(3) **不得为了跑通而放宽出站判据**
    （`tests/egress_guard.py` 是结构判据，一行不改）、不得放宽放行面；(4) 凭据纪律不放松（本 PLAN
    不需要凭据，不发起任何真实出站）；(5) `git pull --ff-only` 后只推 main。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；放宽验收门凑成功；新增依赖或改上游 pin；
    **引入未 pin 的外部二进制资产**（固化词表的代价见「定案」）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-137 — 「默认 CI 离线」的措辞与判据同源（GOAL-011 EC-05）

## 目标

EC-05（`R-6`）：让「**默认 CI 离线**」这条声明**要么成立、要么如实降级措辞**；
判据 = **断网（或阻断该单一目的地）跑默认门 ⇒ 行为可判定**，且**措辞与事实同源**。

起点实测（derive，只读）：

- **判据已经存在且是结构性的**：`tests/egress_guard.py` 在**任何数据包之前**拦，
  并在会话收尾按记录整轮判红；放行面只有 `requires_live_llm` marker；自证用例在
  `tests/architecture/python/test_default_egress_guard.py`（本 PLAN 实跑：**190 passed**，
  其中 8 条阻断是判据对**文档保留地址** `198.51.100.1` 的故意探测）。
- **下载已被挪到判据进程之外**：`.github/workflows/m0-quality.yml` 在 4 个跑门的作业里
  各有一个 `Prewarm the offline tokenizer cache` 步骤（`uv run --frozen --no-sync python -c "import litellm"`），
  位于 `uv sync` 之后、跑门之前。
- **措辞已经诚实**：`docs/architecture/AGENT_RUNTIME.md:184-190` 逐字写着
  「预热门只是把这次下载挪到**判据进程之外**，CI 每轮仍有一次对外请求（要连这句也消掉，
  得把词表固化进镜像或私有源）——所以「默认 CI 完全离线」**不声称成立**」。
- **缺口（本 PLAN 要补的那一半）**：这条声明**没有任何判据在守**——谁删掉一个作业的预热门，
  默认门在**热缓存**的本机上仍然全绿，只有 CI 的干净安装才会炸；「每轮一次受控外部下载」
  这句也只活在散文里，**没有机器可复核的同源点**。

## 验收条件

- **AC-1 定案写明并落地**：在 (A) 固化词表 / (B) 降级措辞 + 判据 之间选定一条，**写明理由**
  （含代价与不做的原因）。
- **AC-2 声明受判**：新增**离线**判据：**每个跑 Python 门的 CI 作业**都必须在跑门**之前**
  有一个 tokenizer 预热步骤（命令形态受判）；删掉任一预热门 ⇒ 判据**红**（按压）。
- **AC-3 措辞同源且可复核**：`CI 每轮有一次受控外部下载` 这句在**判据自身的文档**与
  **架构文档**里**逐字同源**，并由判据机器校验（不是靠人读）。
- **AC-4 行为可判定**：给出「冷缓存 ⇒ 判据能判红」或「该子集不触及该路径 ⇒ 如实登记」
  的**实跑结论**（不臆测）；`tests/egress_guard.py` **一行不改**。
- **AC-5 规模门禁**：50 行函数 / 450 行文件两道门绿；贴线文件零增长。

## 计划开始前的定案（写死，执行中不得回退）

- **D-1 取 (B) 降级措辞 + 判据，不固化词表**。理由（代价面逐条）：
  (a) tiktoken 的 `cl100k_base` 是一个**外部二进制资产**，固化进仓库/镜像需要引入
  **pin + digest + 更新策略**（AGENTS §12 的上游策略、§5 的「来源必须 pin 到版本/commit/digest」），
  这本身就是一件需要独立记录的工作，远超 EC-05 自称的「成本小」；
  (b) 收益只有**每轮 CI 少一次请求**，而**判据进程内离线**这条真正的性质**今天已经成立且受判**；
  (c) EC-05 原文允许二选一，且明确要求「措辞与事实同源」——把**已经存在的事实**（一次受控下载
  在环境准备阶段发生）**做成受判声明**，是收益/代价比更高的一侧。
  **本 PLAN 不新增依赖、不引入二进制资产、不改 `.github/workflows/m0-quality.yml` 的任何一步。**
- **D-2 判据读的是**workflow 的**结构**，不是注释散文**：按作业切分步骤，按「步骤是否跑 Python 门」
  判定谁需要预热门，要求预热门出现在**同一作业内、跑门步骤之前**。命令形态受判的最小面 =
  含 `import litellm` 且含 `--frozen`（pin 纪律同源）。
- **D-3 同源句写死为**：`CI 每轮有一次受控外部下载`。它同时出现在
  `tests/egress_guard.py` 的模块 docstring（判据自己的家）与 `docs/architecture/AGENT_RUNTIME.md`
  （架构文档）里，由判据逐字校验；**不**把散文整段纳入判据（只锁这一句）。

## 实施清单

- [x] **WP1** 定案 + 判据：`tests/tooling/test_m0_ci_coverage.py` 新增两条用例
  （**结构**：跑门的作业必须在跑门之前预热；**同源句**：两处逐字在场）——判据并入既有
  「CI coverage contracts」文件、复用其 `_workflow()`，**不**新建第二个解析同一文件的模块。
- [x] **WP2** 按压：摘掉 `eval-gate` 的预热门 ⇒ 红（`AssertionError: eval-gate runs the Python
  gate without prewarming the tokenizer cache`，逐字）；复原 ⇒ **5 passed**，且
  `git diff --stat .github/workflows/m0-quality.yml` **为空**（复原无残留）。
- [x] **WP3** 冷缓存实验（**四条，结论与 EC 原文括注不同，按事实写**）：① `TIKTOKEN_CACHE_DIR=<空>`
  跑 `tests/architecture` ⇒ **190 passed**，无词表目的地；② 同条件跑含 SDK 导入的子集
  （`tests/e2e/test_ec03_real_runtime_offline_chain.py` + `tests/application/run_orchestration`）
  ⇒ **81 passed / 1 skipped**、判据 `judged 8 / blocked 0`，仍**无**词表下载；③ 直接量：
  `TIKTOKEN_CACHE_DIR=<空> python -c "import litellm"` ⇒ 导入成功、**缓存目录仍为空**；
  ④ 用**不可达代理**探请求 ⇒ 逐字打印
  `Failed to fetch remote model cost map from https://raw.githubusercontent.com/…/model_prices_and_context_window.json …
  Falling back to local backup` ⇒ **环境准备阶段那一次真实请求是 litellm 的 model cost map，不是词表**。
  ⇒ 同源句按实测收窄为 **`CI 每轮至多有一次受控外部下载`**（不写「恰一次」），
  并把 workflow 四份注释的旧理由（「冷装首次 import 会下载 `cl100k_base`」）**改成实测口径**
  （**不改任何步骤、不放宽判据**）。
- [x] **WP4** GOAL 回写（EC-05 状态 / 迭代日志 / 台账）+ 本轮记录。

## 结论（EC-05 的两问两答）

1. **「默认 CI 离线」成立吗？** —— **判据进程内成立且受判**（`tests/egress_guard.py` 在任何数据包
   之前拦、按记录整轮判红、放行面只有 `requires_live_llm`；自证 **190 passed** 含 8 条故意阻断）。
   **整条 CI 运行不成立**：环境准备阶段**至多**有一次对外请求（实测为 model cost map）。
2. **措辞与事实同源吗？** —— 本轮之前**不同源**：workflow 的四份注释把理由写成「首次 import 会
   下载词表」，而这**在本版本下未能复现**（冷缓存下导入不下载词表）。**已按实测改写**，
   并由 `test_the_one_controlled_download_sentence_is_verbatim_in_both_homes` 把那一句**锁死**。

**如实登记的残余 W-N**：预热门**当前的必要性未被证实**——两条最可能触发的子集在冷缓存下都没有
出现词表下载，唯一实测到的请求（cost map）在门内又被 `LITELLM_LOCAL_MODEL_COST_MAP=True` 关掉。
本 PLAN **不因此删除预热门**（在没有复现的前提下删掉它 = 改 CI 行为），只登记为**待复现项**。

3. **「阻断该单一目的地跑默认门」的结论可判定吗？** —— **可判定，且方向是双向可归因的**
   （E-8）：**无代理 ⇒ 绿**（81 passed / 1 skipped、`blocked 0`）；**注入不可达代理 ⇒ 红**
   （3 failed、`blocked 18`），红线**只落在真实 runtime 链那三条**上，而同子集在无代理时全绿
   ⇒ 红**可归因于注入的代理**（代理跳本身是非环回目的地 ⇒ 判据 fail-closed 照拒）。
   进程内触发那次下载（面 B）⇒ 判据**在数据包之前拒绝**、litellm 回落本地副本。
   **边界**：**不跑**「无代理直连」版本——那需要为 `raw.githubusercontent.com` 做 DNS 解析，
   该域名不在任何 provider 声明的 `network_domains` 内；因此**拒绝发生在代理跳**这一点是实测，
   而「直连时在成本表域名处被拒」**未实测**（不臆测）。

## 收尾时**实测到**的一处「本机默认门不密闭」（如实登记，**不在本轮修**）

收尾跑本机全量门时 `python/tests` **判红**（`4383 passed / 17 skipped`、`egress guard: judged 785;
blocked 10`、exit 1）——红**不是**任何用例失败，而是**判据自己的整轮判决**：两条非环回连接尝试、
无 live 标记。**按要求查到底**（**未改任何代码/门禁/断言**）：

- **目的地**：`198.18.0.200:443 (kind=private)` —— 本机 DNS 走 **fake-IP 代理**时给出的**保留网段**
  地址（`198.18.0.0/15`），**不是**产品写死的地址。
- **发起处**：`tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
  → `preflight_support.py:43:build_endpoint_health` → `_probe_endpoint` → `gateway.py probe_connectivity`
  → `list_models`。该用例调**生产装配** `assemble(settings)`，目录里的 endpoint
  （`examples/config/llm_endpoints.yaml`，两条都 `credential_ref: LLM_MAIN_KEY`）会被**实时探测**。
- **开关是「凭据在不在」（成对实验，单条用例，1 分钟可复核）**：
  `LLM_MAIN_KEY=<任意非空值> pytest <该用例>` ⇒ **blocked 2**（逐字见上）；
  `LLM_MAIN_KEY= pytest <该用例>` ⇒ **judged 1 / blocked 0**。该用例**两次都 passed**
  ——红只来自判据的整轮判决。
- **凭据从哪来**：`python -c "import os; import litellm; ..."` 实测
  **导入 litellm 之前 `LLM_MAIN_KEY` 不在环境、导入之后在**（litellm 的 `load_dotenv` 读了仓库根的
  操作者 `.env`）。⇒ 全量套件里**先有某个用例导入 litellm**，之后所有用到生产装配的用例都会
  看见这个真实凭据；**是否命中取决于导入顺序**（这也解释了为什么同一条命令在相邻两次全量跑里
  一次绿一次红：那次 `passed/skipped` 计数差 1，顺序变了）。
- **CI 不受影响（结构性）**：`.env` 是 **gitignored 且未跟踪**（`git check-ignore` 命中
  `.gitignore:1`、`git ls-files` 计数 0），**没有任何 workflow 写它** ⇒ CI 的干净安装里
  `LLM_MAIN_KEY` 不存在 ⇒ 探测拿到 `UNKNOWN`、**不连线**。所以这条红是**本机带 `.env` 时**的现象。
- **本轮的处置（不粉饰、也不越权改测试）**：① **判据判得对**——「默认门内出现非环回尝试」正是它
  要拦的事，**不因为它是本机现象就去关掉/放宽它**；② 也不在本 cycle 去改那条既有用例
  （它的注释自称 hermetic，却只清数据库类环境变量、没清 LLM 凭据——**这属于真实发现，登记为
  W-O，交给后续 cycle 决断**）；③ 最终的全量门跑在**与 CI 同形**的环境下（把 `LLM_MAIN_KEY`
  与 `DEV_LLM_API_KEY` **置空**再跑：dotenv **不覆盖**已存在的变量，因此这两个键在本轮进程里
  始终为空 ⇒ 与 CI 的「没有 `.env`」等效），**判据一行未改、放行面未动**。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 判据是结构性整轮判据、放行面唯一 | `tests/egress_guard.py` 的模块 docstring（拦 + 判两条机制、fail-closed、环回放行） |
| E-2 | 判据自证 | `pytest tests/architecture -q` ⇒ **190 passed**（其中 8 条为其对 `198.51.100.1` 的故意阻断） |
| E-3 | 预热门在 4 个跑门作业里 | `rg -n "Prewarm\|import litellm" .github/workflows/m0-quality.yml` ⇒ 4 处 |
| E-4 | 措辞已诚实但不被判 | `docs/architecture/AGENT_RUNTIME.md:184-190` |
| E-5 | 冷缓存实跑（四条） | 本 PLAN 的 WP3 逐字记录（190 passed / 81 passed+1 skipped / 缓存目录仍空 / 不可达代理下的 cost map 请求） |
| E-6 | 新判据按压 | 本 PLAN 的 WP2 逐字记录（先红后绿，且 workflow 复原后 diff 为空） |
| E-7 | 措辞改动未打红既有门 | `pytest tests/tooling -q` ⇒ **1116 passed**；`pytest tests/architecture -q` ⇒ **190 passed**（**收尾复核重测**：本行初记的 195 与 E-2 的 190 自相矛盾，`git status --porcelain tests/architecture` 为空、该目录无新增用例，两次重测均为 **190**，195 系误记——见「状态历史」的更正条）；`python -B tools/docs_consistency_check.py` ⇒ **DOCS-CHECK PASS**（6 项） |
| E-8 | **阻断该单一目的地跑默认门（EC-05 的 verify 句）三面实跑** | `scratch/goal011-c8-ec05-blocked-destination.py`（脚本自身**不出网**：不可达代理是 IP 字面量 + RFC 5737 文档保留网段），结果落 `scratch/goal011-c8-ec05/blocked-destination.json`。**A0 对照（无代理）**：`pytest tests/e2e/test_ec03_real_runtime_offline_chain.py tests/application/run_orchestration -q` ⇒ **81 passed / 1 skipped**、`egress guard: judged 8 connection attempt(s); blocked 0`、exit **0**；**A1 阻断（同一子集 + `HTTP(S)_PROXY` 指向不可达地址）**⇒ **3 failed / 78 passed / 1 skipped**、`judged 22; blocked 18`、exit **1**，三条失败逐字为 `test_declared_run_chain_capabilities_let_production_assembly_start` / `test_real_runtime_offline_chain_segments` / `test_real_runtime_offline_chain_rejects_a_non_unique_declaration`（**全部是真实 runtime 链上那几条**，且 A0 同子集全绿 ⇒ 红线**可归因于注入的代理**，不是子集自带失败）；**B 进程内触发那次下载**（`guard.arm()` + 关掉 `LITELLM_LOCAL_MODEL_COST_MAP`，同一阻断条件）⇒ 判据**在任何数据包之前拒绝**并记 `blocking_failures=1`，litellm 逐字回落本地副本（`Failed to fetch remote model cost map … blocked a private destination 198.51.100.9:9 … Falling back to local backup`） |
| E-9 | **本机默认门不密闭的开关 = 凭据在不在**（成对实验） | `LLM_MAIN_KEY=<非空> pytest tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure` ⇒ `judged 3; blocked 2`（`198.18.0.200:443 (kind=private)`，发起链 `preflight_support.py:43:build_endpoint_health <- …:96:_probe_endpoint <- gateway.py:228:probe_connectivity`）；`LLM_MAIN_KEY= pytest <同一条>` ⇒ `judged 1; blocked 0`；**两次用例都 passed**。凭据来源实测：`python -c "import os; print('LLM_MAIN_KEY' in os.environ); import litellm; print('LLM_MAIN_KEY' in os.environ)"` ⇒ `False` → `True`（litellm 的 `load_dotenv`）。CI 面：`git check-ignore -v .env` 命中 `.gitignore:1`、`git ls-files \| grep -c '^\.env$'` = 0、workflow 无一处写 `.env` |

## 影响报告

- **Domain / API / schema**：零改动。
- **CI / workflow**：**不改**任何步骤；只新增一条读它的判据。
- **兼容性 / 迁移**：无。
- **安全 / 凭据**：不新增凭据面；本 PLAN **不发起任何真实出站**（冷缓存实验的目标是让判据拦下尝试）。
- **上游版本影响**：无。
- **下一项任务**：EC-06（收口复检：133/134/135/136/137 一并收口 + 两树 + W 列表）。

## 状态历史

- 2026-09-22：derive（WP0）。只读勘察判据、workflow 预热门、架构文档措辞与缺口；定案 D-1…D-3；
  未改任何文件、未发起任何出站。
- 2026-09-22（WP1–WP4）：先补判据并**按压到红**（摘掉 `eval-gate` 预热门 ⇒ 逐字红，复原 ⇒ 绿、
  workflow diff 为空）；冷缓存四条 + 不可达代理探针**改写了同源句的措辞**（「恰一次」⇒「**至多一次**」，
  实测那次请求是 **model cost map** 而非词表）；四份 workflow 注释的旧理由按实测改写。
- 2026-09-22（收尾复核）：**更正一处误记**——E-7 与「结论」§1 初记的 `tests/architecture`
  **195 passed** 与 E-2 的 **190 passed** 自相矛盾。复核方式：`git status --porcelain tests/architecture`
  **为空**（该目录本轮无任何改动，不可能新增 5 条），并**两次重测** `pytest tests/architecture -q`
  ⇒ 均为 **190 passed**。故 195 系误记，已按实测改为 190。**判据强度、结论方向均不受影响**
  （190 与 195 都远大于判据数，两处命令均为绿）。
- 2026-09-22（收尾复核 2）：补 **E-8**（EC-05 verify 句的「阻断该单一目的地跑默认门」三面实跑）。
  **A1 的结果与预期相反**：注入代理后默认门**判红**（18 条阻断），原因是**代理跳本身就是非环回
  目的地**——判据 fail-closed 照拒。**如实按这个方向写**（不改成「绿」）：EC-05 的 verify 要的是
  「结论**可判定**」，A0/A1 成对给出**可归因的绿与红**。**刻意不跑**「无代理的直连版本」：
  那要为 `raw.githubusercontent.com` 做 DNS 解析，而该域名**不在任何 provider 声明的
  `network_domains` 内**（边界登记在 E-8 与脚本 docstring）。
- 2026-09-22（收尾复核 3）：本机 m0 首跑出现**一处自伤**——`tests/egress_guard.py` 追加段
  第 41 行 103 字符超 `ruff` 的 100 上限（`python/product-lint=1`）。**只做折行、不改内容**
  （同源句与实测口径逐字不动），`ruff check` + `ruff format --check` 复绿后**重跑全量 m0**。
  本轮 `python/tests` **4382 passed / 18 skipped / 0 failed**（比 cycle 7 的 4380 多 2 条 =
  本轮新增的两条判据），`egress guard: judged 779; blocked 8`（8 条是判据对 `198.51.100.1` 的
  **故意**探针）。
- 2026-09-22（**收口口径**）：实施清单**全部 `[x]`**、EC-05 已 PASS，但本 PLAN 的 `status`
  **保持 `IN_PROGRESS`**，与同族 `PLAN-133/134/135/136` 一致——**子 PLAN 在 EC-06 收口时一并关闭**
  （GOAL 的「下一轮输入」已写明）。这样不会出现「同形的 136 留着、137 单独关掉」的口径分裂。
- 2026-09-22（收尾复核 4）：登记 **W-O**（本机默认门不密闭 = 凭据在环境里）+ 定下本机跑全量门的
  同形前提（`LLM_MAIN_KEY=""`、`DEV_LLM_API_KEY=""`），并把这条前提写进
  `docs/architecture/AGENT_RUNTIME.md`（**只加段落，不改判据/不放宽放行面**）。全量门最终
  **23/23、EXIT=0**（`PASS: profile=m0; 23 deterministic checks`；`python/tests` **4382 passed /
  18 skipped / 0 failed**、`judged 778 / blocked 8`）。**文档段落是在 m0 跑到一半时加的**，
  因此把会读它的两个目录**在段落后重跑**：`tests/architecture tests/tooling` ⇒ **1306 passed**。
