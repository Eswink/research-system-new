---
id: RECHECK-20260925-183
plan_id: PLAN-20260925-182
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-017-cycle2（独立复检：按压脚本 `scratch/goal017-d11-press.py` 的 6 处对照 + collect-only 机制取证 + 隔离进程实跑）
baseline_ref: cycle 1 提交 `9cfba09`（推送区间 `25d802b..9cfba09`，CI `run_attempt=2` 六 job 全绿）
checked_head: cycle 2 工作树（未推送；D-11 的产品/测试/文档面 + D-13 的 workflow 面 + 记录面）
---

# RECHECK-20260925-183 — GOAL-017 EC-02（D-11）+ EC-03（D-13）

> **状态**：**已完成**。8 条 AC 逐条复核，结论见文末。

## 检查范围

**D-11 的授权边界 a–e** 与 **D-13 的授权边界 a–d** 逐条落到可复核的证据上：
单一开关声明 / 单一环境读取点（AC-1）、无第二套判据（AC-2）、三态实跑（AC-3）、
门禁面零放宽（AC-4）、runbook 同源（AC-5）、**D-13 判据与阈值零改动**（AC-6）、
D-13 前后结构与失败传播（AC-7）、静态门 + as-is 本机 m0（AC-8）。

## 检查结果

### 一、AC-1｜开关名**一个声明点**、环境**一个读取点**（成立）

- 产品侧常量：`packages/application/model_relay/live_run_gate.py` 的
  `LIVE_RUN_SWITCH = "RESEARCHOS_LIVE_E2E"`，**全产品层仅此一处赋值**（判据
  `test_the_literal_is_assigned_exactly_once_in_product_code`）。
- 环境读取：`tests/e2e/live_switch_support.py::live_e2e_switch_enabled`（**唯一**，单一职责小模块）
  ——判据用 **AST** 找「按开关名取映射项」的表达式（`os.environ.get(X)` / `os.environ[X]` /
  `os.getenv(X)` / `<mapping>.get(X)`），命中集合必须**恰为**该模块。
  **这一条本 cycle 被压过两次**：第一版按**文本**判（`os.environ` 与开关名同现），
  按压 P3（`_os.environ.get('RESEARCHOS_LIVE_E2E')` + 别名）**看着绿**——文本判据把
  docstring 里的口令也算成读取点、却漏掉真正的第二读取点。改成 AST 后 P3 **红**；
  第二次是 **m0 抓出**函数放错家（见「八」）。
- `packages/application/**` **零** `os.environ` / `getenv`（判据全层扫描）⇒ 开关**名称**是产品常量、
  **值**在操作者边界读；门的 `live_switch: bool` 是**必填**参数（漏传 = `TypeError`，不会静默开门）。
- 开关语义**一眼可判**：判据钉住 `"1"` 开、`""`/`"0"`/`"true"`/`"True"`/`"yes"`/`"on"`/`" 1"`/`"1 "` 全关。

### 二、AC-2｜无第二套判据（成立，12/12）

- 12 个带 `requires_live_llm` 的模块**全部**命中「经门（`evaluate_live_run_gate(` + `live_switch=`）
  或「经同一谓词（`live_e2e_switch_enabled(`）」，且模块清单在判据里**逐条列出**
  （`LIVE_MODULES`）⇒ 新加一个 live 模块必须在清单里露头。
- 4 处**旧的两套判据**已消除：`test_run_chain_retrieval_live.py::_live_credentials()` 的调用点、
  `test_ec03_real_runtime_offline_chain.py` 的 live 分支、`test_m12_usage_real_relay.py` 的 live 分支、
  `test_live_model_absence.py::_require_case()`（该样本保留自己的**样本级**预置条件，另加 live 开关这一道）。
- 既有门判据按三条件**收紧**：`test_ec04_live_gate_offline.py`（每个调用点**显式**写 `switch=`，
  新增 `TestTheSwitchIsAnIndependentCondition` 5 条：**成对**「开关关 ⇒ 有凭据也关 / 开关开 ⇒ 开门」+
  默认姿态三条件逐条点名 + 理由顺序 + skip 记录点名开关）、
  `test_live_failure_paths_same_source.py`（助手 `live_switch=True`；模型不存在那一格拆成
  **三条**行为判据：缺样本预置条件 ⇒ skip 且点名它 / 缺 live 开关 ⇒ skip 且点名开关 / 两者齐备 ⇒ 不再 skip）、
  `test_live_credential_lifecycle_same_source.py`（助手 `live_switch=True`，让「撤销 ⇒ 关门」不被开关掩盖）。

### 三、AC-3｜三态实跑（成立；③ 是本 GOAL 唯一一次真实出网）

| 态 | 输入 | 观测 |
| --- | --- | --- |
| ① 开关关（凭据在场、runtime 配好） | `RESEARCHOS_AGENT_RUNTIME=openhands` | live 用例 **SKIPPED**，理由逐字含 `live run switch is not on (set RESEARCHOS_LIVE_E2E=1 to open)`；`egress guard: judged 0 … blocked 0`；同文件离线判据 `1 passed` |
| ② 开关开、凭据缺 | `LLM_MAIN_KEY= RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands` | live 用例 **SKIPPED**，理由逐字 `credential 'LLM_MAIN_KEY' is not resolvable`（口径 b = **如实 skip 并点名**）；`blocked 0` |
| ③ 开关 + 凭据 + runtime | `RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands` | 门**开**；真实 run 跑到终态，live 用例 **`1 passed`**（四段：终态 / 返回模型标识 / usage ≥ 1 与 tokens > 0 / 制品与证据可读，且 `is_verified`）；`judged 3 connection attempt(s); blocked 0`；**81.14s**；同文件离线判据因门开而 skip（`gate is open on this machine`）。日志 `scratch/goal017-c2b-state3-live.log`（**搬迁后的最终修订版**；搬迁前同一结论在 `scratch/goal017-c2-state3-live.log`，26.50s） |

- **凭据前提**先核实（不物化值）：`EnvCredentialResolver().has('LLM_MAIN_KEY')` 在 pytest 同构导入栈下
  为 `True`；空值注入下为 `False`（dotenv 不覆盖已存在的键）⇒ 三态②可被**隔离**观察。
- **残留核查**：开关只以**命令级内联前缀**给出（未 `export`、未写 `.env`）；凭据值**未**出现在
  任何记录、日志或命令回显里（日志 `scratch/goal017-c2-state3-live.log` 只含判词、计数与 pytest 摘要）。

### 四、AC-4｜门禁面**零放宽**（成立，判据 + 按压）

- `tests/egress_guard.py` **未改**，放行面仍是 marker 一个（`ALLOW_MARKER == "requires_live_llm"`）；
  新判据硬断言该文件**不提**开关（判据 `test_the_egress_guard_does_not_know_the_switch`），
  按压 P6（把开关塞进 guard）⇒ **红**。
- 判据面的变化只有**收紧**：关门理由从「只报一条」变成**逐条点名全部**未满足条件；
  `test_ec04_live_first_run.py` 的离线判据从「`not configured` **或** 凭据名」二选一
  改为**独立重算哪几条不满足并逐条核对**（**本 cycle 实测发现**：只配 runtime、忘开开关时，
  旧写法会误红——门的行为是对的，判据不对）。

### 五、AC-5｜runbook 同源（成立）

- §4：两个开关的**分工表**（runtime 装配 / 是否进 live run）+ 门的**三条**条件 + 操作者命令
  （含逐字 `RESEARCHOS_LIVE_E2E=1`）+ 「值恰为 `1`」的语义 + 「开关不得被持久化」+ 单读取点 +
  回退三件事（现在要求**两个**变量都去掉）。
- §7：两行 live 证据行都点名开关；边界 1 补「三条件里这一条讲的是**凭据那一格**」。
- §8：补「撤销只关三条件里的**一格**」。
- 判据：新判据按**导入的产品常量**比对 §4 的名字与命令（改常量名/改 runbook 任一侧 ⇒ 红，
  按压 P5 取证）；既有 `test_runbook_same_source.py`（反引号路径 / ENV 名 / pytest 目标必须真实存在）
  保持绿。

### 六、AC-6｜**D-13 判据与阈值零改动**（成立）

- `git diff -- tests/observability/test_telemetry_overhead.py` = **空**；`git status --porcelain` 对该文件
  无输出 ⇒ 文件**完全未被本 cycle 触碰**。
- 阈值常量（`_MAX_RSS_GROWTH_MIB = 128.0`、`_MAX_TELEMETRY_THREADS = 4`、`_PEAK_ALLOC_LIMIT_BYTES`）
  与测量语义（整进程 RSS 增量）**逐字未改**；**未**改成 warning / 非阻断。

### 七、AC-7｜D-13 前后结构与**失败传播**（成立）

- **改动前**（6 个作业）：`quality`（矩阵，跑 `run_all_checks.py --profile m0`，**含**该阈值判据）/
  `eval-gate` / `container-quality` / `collector-quality` / `console-frontend`。
- **改动后**（7 个作业）：`quality` 步骤的 env 增一条
  `PYTEST_ADDOPTS: --ignore=tests/observability/test_telemetry_overhead.py`；新增
  `observability-overhead`（矩阵 `ubuntu-latest` + `windows-latest`，`timeout-minutes: 15`，
  步骤 = checkout / uv / `uv lock --check` / `uv sync --frozen --dev` / **预热 tokenizer** /
  `pytest tests/observability/test_telemetry_overhead.py -q`）。
- **平台覆盖不减**：矩阵与 `quality` 一致（windows 正是观察到这类红的地方）。
- **传播路径**：`grep -cE "continue-on-error|^\s+if:" .github/workflows/m0-quality.yml` = **0**
  ⇒ 新作业与既有作业同形态（无豁免键）⇒「本作业红 ⇒ 整体 CI 红」与拆前**同一条**路径。
  实证：cycle 1 的 run `36163737079` 里只有 `quality-windows-latest` 红 ⇒ 整个 run `conclusion=failure`。
- **机制取证**：`pytest tests/observability --collect-only` 计数 `3 → 0`（带 `PYTEST_ADDOPTS`）⇒ 该文件
  确实被移出 `quality-*` 的进程；`tests/tooling/test_m0_ci_coverage.py`（5 passed）确认新作业
  **按序先预热** tokenizer 且 `gate_jobs >= 4` 的反证仍成立。
- **隔离实跑**：`pytest tests/observability/test_telemetry_overhead.py`（独立进程）`3 passed in 2.71s`
  —— 同一个判据在同一台机器上、独立进程里**远低于**阈值；而在 4400+ 用例的进程里两次实测
  超阈值（174.0 MiB / 175.3 MiB）。

### 八、AC-8｜静态门 + as-is 本机 m0

- `ruff check` = `All checks passed!`；`ruff format --check` = `1029 files already formatted`；
  `mypy` = `Success: no issues found in 1019 source files`。
- 定向套件：`tests/e2e/test_ec04_live_gate_offline.py` + `tests/e2e/test_ec04_live_first_run.py` +
  新判据 + `test_runbook_same_source.py` + `test_live_failure_paths_same_source.py` +
  `test_live_credential_lifecycle_same_source.py` + `test_credential_boundary_wording.py` +
  `tests/tooling/test_m0_ci_coverage.py` = **`92 passed, 1 skipped`**（skip = live 用例在无开关下的如实跳过）。
- **m0 第 1 跑红（真实缺陷，本 cycle 引入并当场处置）**：`FAILED: 1 check(s): python/tests=1`，
  唯一失败 = `tests/tooling/test_python_source_limits.py::test_python_source_size_limits[tests\e2e\live_run_support.py]`
  （`assert 477 <= 450`）。**根因**：把两个开关函数放进了贴着上限的
  `tests/e2e/live_run_support.py`（448 → 477 行）。**处置**：拆出单一职责模块
  `tests/e2e/live_switch_support.py`（43 行）并把 12 处 import 改指向它 ⇒ 该文件回到 **449 行**；
  **未动 450 / 50 这两个阈值**（那是放宽，授权面不允许）。处置后
  `tests/tooling/test_python_source_limits.py` = **`1029 passed`**、
  **按压 6/6 仍全红**、三态①②在最终修订版上**复跑同结论**、三态③**复跑同结论**（`1 passed`）。
  **这条同时是 AC-1 的第二次按压**：一旦「唯一读取点」的实物搬了家，判据的显式清单必须同步
  ——清单是自检的（改错就红），搬迁时正是靠它确认 `SWITCH_PREDICATE_MODULE` 已指向新模块。
- **as-is 本机 m0**：**`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24；
  `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py
  --profile m0 --keep-going`，独占、仓库 `.venv`；日志 `scratch/goal017-c2b-m0-as-is.log`）。
  注：**第 1 跑是红的**（同一命令，日志 `scratch/goal017-c2-m0-as-is.log`），红因见上一条
  ——处置后**复跑取终态**（`(ii)`-式的处置口径，但这次的根因是**真缺陷**且**已修**，不是环境噪声）。

## 结论

**`PASS_WITH_WARNINGS`**：8 条 AC 全部成立；D-11 的边界 a–e 与 D-13 的边界 a–d 逐条落到判据/取证上，
且**判据与阈值零放宽**（本 cycle 的判据改动全是收紧或同源比对）。

**WARNINGS（如实登记，未在本 cycle 处置）**：

- **W-1｜skip 文案双重前缀**：`skip_record_for_gate` 的 `reason` 自带 `live run skipped: `，
  而 6 个 live 模块又加了一次同样的前缀 ⇒ 操作者看到
  `live run skipped: live run skipped: live run switch is not on …`。**行为正确、措辞冗余**，
  且属**既有**形态（GOAL-017 之前对 runtime/凭据理由同样如此）⇒ 不在本轮授权面内（改了要动 6 个 live 模块），
  登记为下一轮可选清理。
- **W-2｜旧名仍可读**：`MEM-20260920-091` / `MEM-20260920-094` 等历史条目写着「门的**两条**开门条件」。
  历史记录**不回改**（append-only 口径）；新判据与新文档写的是**三条**，读者以 `live_run_gate.py`
  与本 runbook §4 为准。
- **W-3｜`test_live_model_absence.py` 有两道门**：live 开关（通用）+ 样本自己的 `_CASE_ENV`
  （该反证会故意失败）。两道都是**预置条件式**且都点名缺哪一个（判据三条），但读者需知道
  「只开 live 开关不会跑这条反证」。
- **W-4｜D-13 只改 CI 结构**：本机 m0 **仍**在 4400+ 用例的同一进程里跑这条阈值判据
  （授权面是 CI 作业结构）⇒ 本机在负载高时仍可能看到同类偶发红，处置口径仍是
  `LOCAL_GATE_PROTOCOL` 的 `(ii)` 类 + 复跑取终态。
- **W-5｜新作业会多一次冷装**：`observability-overhead` 自带走 `uv sync --frozen --dev`（与既有作业同形态），
  拆分的代价是每轮多一个 job 的排队与安装时间；换来的是阈值判据不再受 4400+ 用例的水位影响。
- **W-6｜贴线文件只剩 1 行余量**：`tests/e2e/live_run_support.py` 处置后是 **449/450**——
  下一次往它里面加东西（哪怕一行注释）都会再撞硬上限。**下一轮若还要扩它，先搬代码**
  （本 cycle 已演示一次：搬到单一职责模块，而不是调阈值）。

**残余风险**：CI 上「本作业红 ⇒ 整体 CI 红」是**结构**保证（无豁免键 + 与既有作业同形态），
本 cycle 未**故意**制造一次红来观察（那需要伪造失败或推一次坏提交，代价与收益不成比例）；
实证依据是 cycle 1 的 run `36163737079`（单 job 红 ⇒ run `conclusion=failure`）。
