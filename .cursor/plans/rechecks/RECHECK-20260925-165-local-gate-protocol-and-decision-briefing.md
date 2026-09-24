---
id: RECHECK-20260925-165
plan_id: PLAN-20260925-164
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-015-cycle2 + 只读归因脚本（tools/classify_local_gate_reds.py / 零出网）
baseline_ref: 见下方「检查结果」第 1 节（本 cycle 的改动全部在测试装置 / 文档 / 记录面）
checked_head: 当前树（WP1–WP7 实施 + 收口记录）
---

# RECHECK-20260925-165 — 本地判定确定性 + 决策简报（GOAL-015 cycle 2）

## 检查范围

① 跑法协议是否**如实区分**支持的跑法与不支持的跑法（AC-1）；② 归因脚本是否**只读、零出网、
  表外红非零退出**（AC-2）；③ 代管脚本是否**拒绝跟踪文件**、`finally` 还原、**逐字节复核**
  （AC-3）；④ R-4 是否让跳过守卫**与收集面无关**且 fail-closed 仍在（AC-4）；⑤ CI 红的
  **真实根因**是否被修（判据不再污染会话）且按压仍非空（AC-5）；⑥ 决策简报是否齐备、六要素
  非空、与 GOAL 人工面**双向对齐**、三种变体各自判红（AC-6）；⑦ 判据只增不减，`egress_guard`
  / `validate_bundle` / m0 阈值**逐字节未改**（AC-7）。

## 检查结果

### 一、CI 红的真实根因（本 cycle 首先处置：它挡住了 cycle 1 的推送）

- **现象**（CI run [36048265860](https://github.com/Eswink/research-system-new/actions/runs/36048265860)，
  `quality-ubuntu-latest` + `quality-windows-latest`）：`tests/e2e/test_run_chain_retrieval_live.py::test_live_run_chain_retrieval_lands_a_real_identifier`
  **没有 skip**，带着一个无效令牌真去调出厂端点 ⇒ `AuthenticationError: OpenAIException - Invalid token`
  ⇒ 断言 `'FAILED' == 'SUCCEEDED'` ⇒ 默认门判红。**同一提交在本机通过**。
- **根因（自己的装置）**：cycle 1 的隔离判据在**模块导入期**用
  `os.environ.setdefault(...)` 注入 `LLM_MAIN_KEY` 来「制造泄漏」⇒ 泄漏给**整个 pytest 会话**
  ⇒ live 用例的 skip 条件（「环境里有没有凭据」）不再成立。
- **修法**：注入全部搬进**子进程**（只放进子进程的 `env`）；新增会被常规收集的探针
  `tests/architecture/python/test_default_gate_isolation_probe.py`。
- **非空按压**：`LLM_MAIN_KEY=<任意值> pytest --noconftest …test_default_gate_isolation_probe.py -q`
  ⇒ **1 failed**（点名 `LLM_MAIN_KEY` 仍可见）；带根 conftest ⇒ **1 passed**、`blocked 0`。
  **未删用例、未改 live 用例的 skip 条件、未改出站判据。**
- **落盘记忆**：`MEM-20260925-133`（判据的注入必须限定在子进程）。

### 二、AC-1｜跑法协议（`docs/architecture/LOCAL_GATE_PROTOCOL.md`）

- **canonical 调用**：`uv run --frozen --no-sync python -B
  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`，
  DSN 固化（`RESEARCHOS_POSTGRES_DSN` = postgres-test DSN，`DATABASE_URL` / `POSTGRES_DSN` **置空**
  —— 上游 `load_dotenv()` 会注入 operator `.env`），**独占运行**（`evolution_state.json` 的
  `WinError 5`），终态行判据 = `PASS: profile=m0; 23 deterministic checks`。
- **如实写明**：**支持** as-is / 代管后两种跑法；**不支持**用 `CURSOR_FRAMEWORK_ROOT` 跑全量
  （它重定向**整个 runner**，不是单个 check）、不支持并发跑 m0、不支持把 `python/tests` 的
  定向套件当成 m0 的等价物。
- **三分类判定条件 + 归因命令** + 分类表（R-1…R-4）逐条在册。

### 三、AC-2｜只读归因脚本（`tools/classify_local_gate_reds.py`）

- 只读日志、**不 import 仓库代码**、**零出网**；`BY_CHECK` 覆盖 m0 的 8 类红，
  `SUB_SIGNATURES` 覆盖 `python/tests` 内的三条已知子签名；**表外红 `UNCLASSIFIED` + exit 3**
  （不得读成「已忽略」）。
- **实跑（对 cycle 1 的 as-is m0 日志）**：
  `python -B tools/classify_local_gate_reds.py --log scratch/goal015-c1-m0-final.log`
  ⇒ `FAILED 检查项：['framework/validate_bundle']`；`汇总行：FAILED: 1 check(s):
  framework/validate_bundle=1`；分类 `(iii) 门禁 scoping`；exit 0。

### 四、AC-3｜代管脚本（`tools/quarantine_and_run_m0.py`）

- **拒跑面**：路径必须是**未跟踪**文件（`git ls-files --error-unmatch` 命中即拒跑，exit 2）；
  写者静置窗口（`--settle-seconds`，默认 3s）内 `mtime` 变化即拒跑 —— 不动并发写者的在制品。
- **逐字节复核**：代管前 / 归还后各记 `size` / `mtime_ns` / `sha256`，任一不符 ⇒ exit 4 并打印；
  脚本**从不删除**文件。
- **口径**：输出明确标注「本终态行取自**代管后的树**」。
- **实跑**：见第 7 节的终态行与逐字节复核记录。

### 五、AC-4｜R-4（加载无关的跳过守卫）

- **修前（A）**：`RESEARCHOS_POSTGRES_DSN=postgresql://research_os@127.0.0.1:1/research_os
  pytest tests/api/test_worker_plane_composition.py -q` ⇒ 120s 内无输出、被杀（exit 143）——
  **既不跳过也不快失败，而是挂死**。
- **修前（B，同文件 + 顺带收集 `tests/postgres`）** ⇒ `16 passed, 93 skipped in 4.22s`。
- **修后**：`tests/postgres_guard.py` 共享模块 + 根 `tests/conftest.py` 的
  `pytest_collection_modifyitems` 第一步调用 ⇒ 定向跑**快速跳过 / exit 0**；
  `RESEARCHOS_REQUIRE_POSTGRES=1` ⇒ **非零退出**且判词含 `not reachable` / `fail-closed`。
- **判据**：`pytest tests/architecture/python/test_postgres_skip_is_load_independent.py -q`
  ⇒ **2 passed**（跳过方向 + fail-closed 方向，各自子进程、不可达 DSN）。
- **回归面**：`tests/postgres` + `tests/distributed` + 4 个 `postgres` 标记的 API 用例
  ⇒ **143 passed**（改前有 4 个模块 import 失败：它们从 conftest 借 `_postgres_dsn`）。
- **落盘记忆**：`MEM-20260925-132`。

### 六、AC-6｜决策简报与机械对齐（EC-03）

- **文档**：`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` —— **12 条**决策项（D-01…D-12），
  每条**六要素**（要决定什么 / 选项 / 影响与代价 / 证据出处 / 不做会怎样 / 建议）；
  另有一张**对齐表**把 GOAL-015 人工面的 13 条编号项 + 4 条 GOAL 特有项 + 1 条承继残余
  逐条映射到 D-NN 或标明「已了结 / 标准禁令」。
- **判据**：`tests/tooling/test_pending_decisions_briefing.py` ⇒ **5 passed**：
  ① 现状齐备且双向对齐；② 删一条目 ⇒ 判红（`不存在的简报条目`）；③ 清空一个要素 ⇒ 判红
  （`空壳`）；④ 删对齐表一行 ⇒ 判红（`对齐表缺 GOAL 编号项`）；⑤ 删 GOAL 特有项行 ⇒ 判红
  （`非编号行不是预期集合`）。
- **零实施**：本 EC 只增文档 + 判据 + 记录；`git diff --stat` 证明**未触碰**任何门禁 / 策略 /
  阈值 / 依赖 pin / 运行时默认值（见第 8 节）。

### 七、AC-7 + 判据只增不减（逐字节）

- `tests/egress_guard.py`：**逐字节未改**（`git diff --stat` 空）。
- `tests/application/test_m2_audit.py`：**逐字节未改**。
- m0 的 check 阈值（450 行 / 50 行规模门禁）：**未改**——本 cycle 反而**被它抓到一次**
  （见下）。
- **本 cycle 自己撞到、并如实登记的一次红**：新增的 `_problems` 同时触发 ① `ruff`
  `complex-structure（20 > 10）`、② `line-too-long`、③ `tests/tooling/test_python_source_limits.py`
  的 **50 行函数门禁** ⇒ 重构为 6 个小函数（语义不变），`ruff format` + `ruff check` 全绿、
  规模门禁 `1028 passed`。**未加任何豁免、未改任何阈值。**
- **另一次**：探针初版命名 `default_gate_isolation_probe.py`（不以 `test_` 开头）⇒
  `tests/architecture/test_module_file_naming.py` 判红（m0 全量轮实测）⇒ 改名
  `test_default_gate_isolation_probe.py`，三者合计 `33 passed`。**未加豁免名单。**

### 八、m0 终态（as-is 与代管后）

- **as-is 第一轮**（`scratch/goal015-c2-m0-asis.log`）：`FAILED: 5 check(s):
  python/product-lint=1, python/format-check=1, python/tests=1, framework/validate_bundle=1,
  framework/validate=1` —— 其中 4 条是**本 cycle 自己的文件 / 记录未落盘**（已在第 7 节修复
  与登记），第 5 条是 `R-3`。
- **as-is 第二轮（修复后，`scratch/goal015-c2-m0-asis2.log`）**：
  `FAILED: 2 check(s): framework/validate_bundle=1, framework/validate=1`，
  `22 PASS`。两条逐条归因：
  - `framework/validate`（治理）＝ **记录未闭环**：判词三条 —— `DONE 任务仍包含占位内容:
    PLAN-20260925-164`（**误中**：治理脚本按**大写字母子串**检测占位词，而简报的**旧文件名**
    里恰好含那个词 ⇒ 被命中）、`通过的复检仍有占位标记` / `复检缺少检查结果或结论`
    （本 RECHECK 初稿的结论标题用了「终态」而非规约要求的 `## 结论`）。**处置**：简报**改名**
    `OPEN_DECISIONS_BRIEFING.md`（**不改治理脚本的任何检查项**——它是对的，是我的文件名落进了
    它的口径）+ 补 `## 结论`。
  - `framework/validate_bundle` ＝ `R-3`（**唯一**与本 GOAL 无关、且按授权**只登记**的红）。
- **代管后**：终态行与逐字节复核记录见下方「结论」节；执行脚本
  `tools/quarantine_and_run_m0.py`（日志由脚本落盘）。

## 警告与残余（本 cycle 不处置）

- **W-1｜as-is 本机仍不可能 23/23**：`framework/validate_bundle` 扫描**gitignored 工作区**
  （`scratch/`），而 `scratch/self-governance-bootstrap-prompt.md` 是**并发写者**的在制品。
  ⇒ 分类 **(iii) 门禁 scoping**，**只登记**为决策简报 **D-10**，**不改门禁**。
- **W-2｜live 判据的开门条件**（环境里恰好有凭据即真出网）⇒ **只登记**为决策简报 **D-11**，
  **不改判据**。
- **W-3｜两条具名起点的口径更正**：EC-02 起点 (b) 原写「本机 fake-IP DNS 致出站判据判红**两条
  探针**」。实测（cycle 1 普查 + 本轮 CI 红）**否证**该归因：判据放行面只有 `localhost`
  （`ALLOWED_KINDS`），任何**可解析**的非环回目的地都会被拦；本机 DNS 只让判词里的 `kind`
  显示为 `private`。**判红的原因是「凭据在场」**（⇒ R-2，真实缺陷，已修），**不是环境**。
  ⇒ 起点 (b) 的唯一终态 = **判据正确 + 不改判据 + 不改机器网络配置**；可复跑归因命令见
  `LOCAL_GATE_PROTOCOL.md` 第 5 节（**零出网**：只读已落盘判词，不做新的 DNS/网络调用）。
- **W-4｜`M-1` 与本 GOAL 的其余人工面**（13 条 + `R-F1`/`R-F2`/`R-F3`/`R-M1`/`R-D1`/`R-B1`/
  `R-N1`）**原样保留**，逐条登记见决策简报的对齐表。

## 结论

- **结果**：`PASS_WITH_WARNINGS`（W-1…W-4 全部**具名登记**，无一条以「已解决」口径掩盖）。
- **本 cycle 的两处真实修复**（R-4 加载无关守卫 / 判据不再污染会话）各有**非空按压**；
  **EC-03 的产出是文档，零实施**，且由双向对齐判据强制。
- **未改任何判据 / 门禁 / 阈值 / 策略面 / 依赖 pin / 运行时默认值**。
