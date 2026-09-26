# 本地门跑法协议（Local Gate Protocol）

**GOAL-015 EC-02 的交付物**：让「本地 m0 为什么不是 23/23」成为**机械可判**的事实，
而不是每轮现场归因。本协议规定 **canonical 调用方式**、**工作树前置条件**、
**外部文件存在性处理**，以及**三分类判定条件与归因命令**。

配套事实底表：`docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`（红项普查）。
配套脚本：`tools/classify_local_gate_reds.py`（按判据分类）、
`tools/quarantine_and_run_m0.py`（代管 → 跑 → 还原 + 逐字节复核）。

## 1. Canonical 调用（唯一入口）

```bash
# 1) 依赖与容器（一次性）
uv sync --frozen --dev
docker compose --project-directory . -f infra/compose/postgres-test.yaml up -d --wait

# 2) DSN 固化（**必须**）：本机 .env 会被上游 load_dotenv() 注入进程环境
export RESEARCHOS_POSTGRES_DSN='postgresql://research_os:research_os_m14_test@localhost:15432/research_os'
export DATABASE_URL=
export POSTGRES_DSN=

# 3) 全量门（m0 = python 6 + typescript 9 + framework 8 = 23 项）
make validate-all           # = run_all_checks.py --profile m0 --keep-going
```

- **独占运行**：同时只跑一个 m0（并发会让 `evolution_state.json` 报 `WinError 5`，
  也会让共享 Postgres 的测试互相污染）。跑之前确认没有其他 m0 / 全量 pytest 在跑。
- **`--keep-going` 是判据的一部分**：本地必须照抄（Makefile 里就是它），否则第一个红
  会短路后面的 check，读到的不是一个完整剖面。
- **终态行**：全绿时 runner 打印 `PASS: profile=m0; 23 deterministic checks`；有红时打印
  `FAILED: N check(s): …`。**只有前者才算全绿**；`PASS [` 行数比 23 多 1
  （`release-assets-immutable` 在计数之外）属正常。

### 记录面覆盖（GOAL-020 EC-02）：门必须在记录写入**之后**跑

**为什么**：`.cursor/plans` 与 `.cursor/memory/entries` **本来就在**门的扫描面内
（`test_reproducibility_wording.py` 的 `_SCAN_ROOTS`、`tools/credential_audit.py` 的
`RECORDS_DIR`、`validate_bundle` 的版本串与链接检查、治理 `validate.py` 的
plan / recheck / goal 结构检查）。缺陷**不在扫描面，而在时刻**：本地旧 SOP 把全量门跑在
**记录写入之前**，于是那次结论只覆盖**当时还不存在**的记录内容——GOAL-019 cycle 2 的记录提交
`75155b2` 就是这样只在 CI 判红的（本地那次门是绿的）。

**顺序（canonical，不得颠倒）**：

```text
写记录（PLAN / RECHECK / MEM / GOAL 回写）
  → 跑记录面判据（tests/architecture/python + tests/tooling）
  → 跑全量 make validate-all
```

**机械复核**：`tests/architecture/python/test_record_face_is_covered_by_the_gate.py`
把「记录面在受判集合内」变成机器事实——它读**符号值**与**行为**（`_SCAN_ROOTS`、
`_scan_files()` 的实际产出、`credential_audit.RECORDS_DIR`、治理
`iter_cursor_text_files()` 的实际产出、runner 的收集面常量），
并绑定**本节的顺序条款**所点名的**两个**判据文件：受判的记录面判据
`test_reproducibility_wording.py`，以及覆盖的机械保证
`test_record_face_is_covered_by_the_gate.py`
（改名即判红，条款不得悬空）。任何人删掉扫描根、换掉 walker、或把记录面判据挪出门的
收集面，该判据都会红。

**注意**：写记录时**不要**跑 m0（m0 运行中改工作树会让 `framework/validate` 判红，
见 `W-5`）⇒ 正确顺序是「记录写完 → 记录面判据 → 全量门」，不是「门跑到一半去写记录」。

### 支持的跑法 / 不支持的跑法

| 跑法 | 支持 | 说明 |
| --- | --- | --- |
| `make validate-all`（DSN 固化、独占） | ✅ | canonical；本文所有判定以此为准 |
| 上述 + `tools/quarantine_and_run_m0.py`（代管仓库外文件） | ✅ | 唯一允许的「as-is 不可达」补偿手法，逐字节复核见第 4 节 |
| 单一 check 直跑（`python -B <script>`、`pytest <file>`） | ✅ | 用于**归因**；不作为「门已过」的证据 |
| `CURSOR_FRAMEWORK_ROOT` 指到别处跑**全量** | ❌ | 该变量是**整个 runner 的根**（每个 check 的子进程都继承）⇒ 所有 check 指向无依赖的树，结论无效；只可用于**单条** framework check 的对照 |
| 用**系统解释器**跑 m0（`python -B …run_all_checks.py`、`python -B tools/quarantine_and_run_m0.py`） | ❌ | `sys.executable` 是调用方解释器 ⇒ mypy / lint-imports / pytest 版本全错，产出**假红**（2026-09-25 实测三条：`No module named mypy`、`lint-imports executable is unavailable`、`platform win32 -- Python 3.11 …pytest-8.`）。**一律走 `uv run --frozen --no-sync python -B …`**；`tools/quarantine_and_run_m0.py` 现在优先用仓库 `.venv` 并在缺失时**拒跑** |
| 并发跑两个 m0 / 在门跑着时改工作树的被测文件 | ❌ | 会产生无法归因的红 |

## 2. 三分类判定条件（机械可判）

对**每一条**红，按顺序套用；**先命中者胜**，并各自给出**归因命令**：

### (i) 真实缺陷 ⇒ 修代码

**判定条件（全部满足）**：

1. 该红有**最小复现命令**，且命令**不需要**机器特殊输入（不需要 DNS 代理、不需要仓库外
   文件、不需要某个容器的残留状态）；
2. 存在一条**确定性判据**（进默认门），它对修前代码判红、对修后代码判绿；
3. 修法落在**被测系统或测试隔离**一侧（不是放宽门禁）。

**动作**：修真实共享来源（每线程连接 / 夹具隔离 / 显式 DSN 固化 / 容器与 DB 残留清理 /
全序语义），并留下「先红后绿 + 判据」。
**当前实例**：`R-1`（草稿列表序 tie）、`R-2`（默认门凭据泄漏）、`R-4`（postgres 跳过守卫
依赖收集面）。

### (ii) 环境专属 ⇒ 附证据登记，**不改判据**

**判定条件（全部满足）**：

1. 该红在**干净基线树**（同 commit 的 `git worktree`）上**同样复现**，或在**本机之外**
   （CI 同 tip）不出现；
2. 触发它的是**机器输入**：DNS / 代理、仓库外文件、容器或端口状态、时钟分辨率；
3. 判据本身**描述的行为是对的**（例如「默认门不得出网」——它拦住的东西确实不该发生）。

**动作**：登记为环境项，附 ① 可复现命令 ② 干净基线对照的**成对输出**；**不得**放宽判据、
豁免地址段或 skip 用例。以 CI 在推送树上的终态为权威证书。

### (iii) 门禁 scoping ⇒ **只登记**（去决策简报）

**判定条件**：红的成因是某条门禁**扫描了不属于仓库的输入**（例如 gitignored 工作区目录、
仓库外写者的在制品），而**被判物本身不是本仓的产物**。

**动作**：**不在循环内改门禁**（改检查项/扫描范围 = 放宽门禁，属 `fix_policy.forbidden`）；
登记进决策简报（GOAL-015 EC-03），由用户拍板「检查项 / 扫描范围是否排除 gitignored 工作区」。
**当前实例**：`R-3`（`framework/validate_bundle` 被 `scratch/` 下的仓库外文件判红）。

> 三类的**分界线**：判据描述的行为对不对（不对 ⇒ (i) 或改判据本身，但本 GOAL 禁止放宽）；
> 触发输入是不是本机特有的（是 ⇒ (ii)）；被判物是不是本仓产物（不是 ⇒ (iii)）。

## 3. 分类表（2026-09-25 实测，随门演进更新）

| 红项 | 判词 | 分类 | 归因命令（可复跑） | 终态 |
| --- | --- | --- | --- | --- |
| R-1 草稿列表序 tie | `test_list_orders_by_recency_and_filters_project` 断言 `['…0001','…0002'] == ['…0002','…0001']` | (i) | `pytest tests/contracts/test_protocol_draft_store_order_tie.py -q` | **已修**（三实现全序 + 判据先红后绿） |
| R-2 默认门凭据泄漏 | `egress guard: FAIL … 198.18.0.83:443 by tests/api/test_runs_api.py::…` | (i) | `LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q`（修前 `blocked 2` / 修后 `blocked 0`） | **已修**（夹具隔离 + 双向对齐判据） |
| R-3 仓库外文件 | `FAILED [framework/validate_bundle]` 点名 `scratch/self-governance-bootstrap-prompt.md` | (iii) | 见第 5 节（主树红 / 干净树绿成对） | **只登记**（进 EC-03） |
| R-4 postgres 跳过依赖收集面 | 定向跑在 PG 不可达时**挂死**（无判词，超时被杀） | (i) | `RESEARCHOS_POSTGRES_DSN=postgresql://x@127.0.0.1:1/db pytest tests/api/test_worker_plane_composition.py -q` vs 同一命令 + `tests/postgres` | **已修**（守卫提为加载无关） |

**读法**：一张 m0 日志里的每一条红，都应该能落到上表某一行的**同一分类**；落到表外的红，
按第 2 节的三条判定条件**当场分类并补进本表**（表是随门演进的事实底表，不是白名单）。

## 4. 外部文件存在性处理（代管 → 跑 → 还原）

当某条红属 (ii)/(iii) 且由**仓库外文件**造成时，允许**代管**该文件取得终态行：

```bash
uv run --frozen --no-sync python -B tools/quarantine_and_run_m0.py \
  --path <仓库外或 gitignored 的判红文件>
```

> 必须走 `uv run …`：脚本用**仓库 `.venv`** 跑 m0（缺 `.venv` 时**拒跑**）。用系统解释器
> 直接跑 `python -B tools/…py` 会让 m0 在没有 mypy / lint-imports 的解释器里跑出**假红**
> （2026-09-25 实测三条）；归因脚本的**跑法层签名**会点名这种轮次。

脚本的三条纪律（缺一不可）：

1. **写者检查**：代管前记录 `size` / `mtime` / `sha256`，若 `mtime` 在静置窗口内变化则
   **拒跑**（说明并发写者仍活跃 ⇒ 不要动别人的在制品）；
2. **逐字节复核**：归还后重新核对 `sha256` / `size` / `mtime`，任一不符即**非零退出**并
   打印差异；
3. **口径如实**：脚本输出会明确打印「本行取自代管后的树」，**不得**把「代管后 23/23」
   写成「本机一直 23/23」。

> 代管是**取证**动作，不是修门禁：它不改判据、不改文件内容、不留任何仓库改动。

## 5. 当前两条具名起点的终态

**起点 A｜`R-F3` / `R-3`（仓库外 gitignored 文件致 `framework/validate_bundle` 红）**

- **分类**：**(iii) 门禁 scoping**。
- **终态**：**只登记**——不改门禁、不改该检查项、不删不改外来在制品；条目进 EC-03 决策简报
  （「`validate_bundle` 的链接扫描是否应排除 gitignored 工作区」）。
- **归因命令（成对）**：
  ```bash
  # 主树：判红，且判词点名那个仓库外文件
  python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py
  # 干净树对照（同 commit 的 worktree，无 scratch/）：应全绿
  CURSOR_FRAMEWORK_ROOT=<干净的同 commit worktree> python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py
  ```
- **as-is 影响**：本机全量 m0 = **22/23**（唯一未绿即此项）；CI 检出无 `scratch/` ⇒ 不受影响。
- **代管后实测（`scratch/goal015-c2-m0-quarantined2.log`，2026-09-25）**：
  `PASS: profile=m0; 23 deterministic checks`；归还后 `size=69944` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2` /
  `mtime_ns=1790187424185178900` **全等**。该终态行**取自代管后的树**。

**起点 B｜本机 fake-IP DNS 与出站判据（两条探针）**

- **分类**：**(i) 真实缺陷**（**不是**环境项——这是本协议对既有记录的一处事实更正）。
- **终态**：**已修**（`R-2` 夹具隔离）。判据一字未动；**没有**豁免 `198.18.0.0/15`，
  也**没有** skip 任何用例。
- **归因命令**：`LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q`
  （修前：`egress guard: FAIL … blocked 2`；修后：`blocked 0` / `16 passed`）。
- **为什么不是「机器特殊」**：判据放行面只有 `localhost`（`tests/egress_guard.py` 的
  `ALLOWED_KINDS`），任何**可解析**的非环回目的地都会被拦并判红；本机 DNS 只是让判词的
  `kind` 显示为 `private`。CI 全绿的原因是**没有可解析的凭据**（无 `.env`），不是 DNS 不同。
