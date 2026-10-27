---
id: PLAN-20261027-098
slug: goal-098-independent-novelty-and-derived-experiment
title: GOAL-098 子计划 —— 拆开作者与评审者 + 实验脚本由计划选择
status: DONE
created_at: 2026-10-27
updated_at: 2026-10-27
parent_goal: GOAL-20261027-098
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261027-098-goal-098-independent-novelty-and-derived-experiment.md
memory_entries:
  - .cursor/memory/entries/MEM-20261028-232-half-covered-judges-read-as-green.md
---

# PLAN-20261027-098

## 背景与靶子

序 65 跨过了「产品入口能跑」这道门。本轮修**质量**与**自主性**两处结构性缺陷，并把三处
归档面既有漏洞补齐。

### 靶子 1（最硬）：创新点的作者与评审者是同一个模型 —— 自评

**取证（`rg -n` 读数，本轮不重新推导）**：

- `examples/protocols/direction_to_report_v2.yaml` 的 `novelty` 相与 `review` 相**都**点名
  `novelty_reviewer`；
- `packages/application/protocol_compile/resolution.py` 的 `agent_candidates` 只按
  `agent.role == role_id` 过滤 + 排序、**不看 phase**；`assignments.py` 按
  `agent_candidates.get(role)` 取前 N 个；`selection.py::select_agents` 同样只吃 `role_id`；
- ⇒ 同一角色在两相**必然**选到同一个 agent 实例（`novelty_a` / `minimax-m3`）⇒ `review` 相
  两个 `review_decision` 里有一个是「评审自己刚写的声明」；
- 判据数的是「正文里出现了那个标识」，而 `novelty_claim` 本来就在 `novelty_a` 的提示词里
  （`review` 的 `inputs` 含 `novelty:novelty_claim`）⇒ 复述是**结构必然**。

### 靶子 2：实验脚本仍由装配常量决定

`services/api/executor_wiring.py::DEFAULT_EXPERIMENT_SCRIPT` 是模块常量；`declared_or_assembled`
只在**契约 pin**（静态文件）时改它 ⇒ 换方向换多少次跑的都是 `exact_match_index_benchmark.py`。
上一轮的 `design_source="plan"` 只让**臂与参数**由计划派生。

### 靶子 3：归档面三处既有漏洞（承 GOAL-096 `U-3` / GOAL-097）

1. `archive/MAINLINE-2026-10-15-progress-075-only.md` **未被宪章链接**（`_archive_paths` 只认
   `](archive/...)` 形态 ⇒ 它完全不参与「不漏 / 不重」）；
2. 历史归档里的短修订行（4 格 vs 表头 5 格）从未处置；
3. `tools/verify_goal{076,090,095}_closeout.py` **从未存在**（GOAL-076 的 EC-05 正文里那句是
   悬空引用）；`_CUTOFF_SEQ = 64` 的祖父条款让它们不判红。

## 工作包

### WP-1（EC-01）作者与评审者分开

1. `examples/config/roles.yaml` 新增 `novelty_author`：`role_type: NoveltyAuthor`（schema 是自由
   字符串，无需改枚举）、`default_model_profile: research_strong`、
   `activation_default: REQUIRED_BY_PROTOCOL`、`requested_capabilities` **只用已放行的读能力**
   （`artifact.read` / `literature.search` / `literature.read` / `evidence.read`）、
   `workspace_policy: read_only`、**不写 `review_panel_role`**（作者不是评审者）。
   **不写 `idea.write` / `idea.review`**（`policy.yaml` 零 allow；加 allow = BLOCKED）。
2. `examples/config/models.yaml` 新增 `novelty_author_model`（`deepseek-v4-pro-0813`）——
   与生产侧（`deepseek-v4-flash-vision`）及三位评审者（`glm-5.3` / `kimi-k2.6` / `minimax-m3`）
   **都不同**。读数：`GET /v1/models` 在 13 个之列；`POST /v1/chat/completions` 返回名 = 声明名；
   `tool_choice: required` 真返回 `tool_calls`；`usage` 逐次回报。
   **不声明 `STRUCTURED_OUTPUT_NATIVE`**（只实测了 chat 与 tool_calls —— 按实测声明是本仓纪律）。
3. `examples/config/agents.yaml` 新增 `novelty_writer`（`role: novelty_author`，
   `EXPLICIT_MODEL: novelty_author_model`，`workspace_policy: read_only`）。
4. `examples/config/team_templates.yaml` 的 `standard` 加 `novelty_author: {1,1}`。
5. `examples/protocols/direction_to_report_v2.yaml` 的 `novelty` 相改点名 `novelty_author`；
   `review` 相**保留** `novelty_reviewer`。
6. `docs/catalog/SYSTEM_ROLES.md` 新增 `NoveltyAuthor` 条目并重编号（`validate_bundle` 的
   catalog parity 判据要求两侧集合相等）。
7. 判据 `tests/contracts/test_direction_to_report_v2_independence.py`（18 例）+ 按压。

**连带申报（事实变更，不是放宽）**：

| 文件 | 改动 | 为什么不是放宽 |
| --- | --- | --- |
| `tests/loaders/test_contract_loaders.py:50,246` | `len(roles) == 26` → `27` | 判据问的是「加载器读到出厂文件的每一个条目」；新增一个角色 ⇒ 条目数变了是**事实**。下面逐条断言一字未动 |
| `.cursor/skills/system-spec-check/scripts/validate_bundle.py:445` | `!= 26` → `!= 27` | 同一事实变更；「catalog 与 fixture 一致」那条**未动** |
| `docs/catalog/SYSTEM_ROLES.md` | 新增一条 + 后续重编号 | `validate_bundle` 要求 `catalog_types == fixture_types` |

### WP-2（EC-03）实验脚本由计划选择（方案 (b)）

1. 新模块 `packages/application/experiments/design_script.py`：`SHIPPED_EXPERIMENT_SCRIPTS`
   闭集（3 个出厂脚本）、`declared_script`（越界 / 绝对路径 / `..` / 盘符 / 非字符串 ⇒
   **点名拒绝**）、`script_override`、`plan_selected_script`（三档优先级）。
2. `packages/application/experiments/design_from_plan.py` 新增 `plan_design_block`（只读出
   `(制品 id, 设计块)`，不解析臂 —— 否则「只选脚本、臂用装配面」这种合法组合会不可能）。
3. `services/api/experiment_support.py` 的 `run()` 里插一行调用（文件当时 449/450 ⇒ 压缩三行
   注释换回）。
4. `examples/contracts/task_contracts.yaml` 的 `research_report_plan` 合约把新键写进任务书
   （否则模型无从知道可以选）。
5. 判据 `tests/application/test_experiment_script_comes_from_the_plan.py`（17 例）+ 子进程按压。

**(a) 登记为下一轮**：模型为新问题**写**脚本并在沙箱里跑 —— 模型产出的任意 Python 进容器属
安全面变更（`policy` / `classify_risk` / `EXECUTE` 类 HIGH 的既有门**不覆盖这类产物**）⇒
需用户拍板。

### WP-3（EC-04）归档面三件

1. 宪章补 `progress-075` 的链接。
2. 10 条 4 格历史修订行**逐条登记**进 `archive/SHORT-REVISION-ROWS.md`（结论：保留 4 格、
   不补 —— 原文把「替换为」与「理由」写进同一格，其中 5 份文件自声明不再改动，补第 5 格
   须自定断句 = 编造列边界），配双向判据（覆盖面 / 无过期条目 / 理由非空 + 两条按压）。
3. 三个验证器 + 断言集补建：`verify_goal{076,090,095}_closeout.py` +
   `goal0{76,90,95}_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`。
   **076 的断言集判的是「记录与树一致（未做仍是未做）」** —— 它的 GOAL 是 `PAUSED`，那 10 条
   长度界从未加进去。**回填是补齐历史，不是过门禁。**

### WP-4（EC-05/06/07）收口与记账

1. `tools/verify_goal098_closeout.py` + `tools/goal098_closeout_assertions.py` + 两处登记。
2. `max_goals` 70 → 100 + 修订记录登记扩表。
3. 核对序 65 的记录缺陷不回退（3 格 → 5 格 + 搬入归档 + 判据在位）。

## 记录顺序（不可调换）

写全部记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 → **最后**跑
`tools/run_m0_with_witness.py` → 之后不再 `git add` 任何受判文件 → 提交推送。

## 完成判据

七个 EC 逐条 PASS（EC-02 若凭据不可用则如实登记未达成，不凑）+ 真跑取证 +
`tools/verify_goal098_closeout.py` 全 PASS + m0 终态行 + CI 逐提交台账。

## 验收条件

1. `tests/contracts/test_direction_to_report_v2_independence.py` 全过（18 例），且它的按压臂在
   真文件上真的判红、按 raw `sha256` 逐字节复原；
2. `tests/application/test_experiment_script_comes_from_the_plan.py` 全过（17 例），且子进程
   按压真的 exit 非零、复原后真的 exit 0；
3. `tools/verify_goal{076,090,095}_closeout.py --root . --verdict-only` 零 `FAIL`；
4. `tests/tooling/test_short_archive_revision_rows_are_registered.py` 全过（含两条按压）；
5. `tools/verify_goal098_closeout.py --root . --verdict-only` 零 `FAIL`；
6. 宪章：程序表序 66、`max_goals: 100`、阶梯两行收录本 GOAL、进展与修订各一行（修订 5 格）；
7. `ruff check` 与 `ruff format --check` 对全部改动文件全绿；`validate_bundle.py` 验证通过；
8. m0 终态行 `PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、
   `tree changed during the run: False`。

## 实施清单

- [x] WP-1 角色 / 模型 / agent / 模板 / 协议五处（`roles.yaml` / `models.yaml` / `agents.yaml` /
      `team_templates.yaml` / `direction_to_report_v2.yaml`）+ `SYSTEM_ROLES.md` 目录同步
- [x] WP-1 判据 `test_direction_to_report_v2_independence.py`（18 例，含跨 28 份协议的自评扫描 + 真文件按压）
- [x] WP-1 连带申报：`test_contract_loaders.py` 26→27（两处）、`validate_bundle.py` 26→27
- [x] WP-2 `design_script.py`（闭集 / 点名拒绝 / 三档优先级）+ `plan_design_block` + 派发体一行接线
- [x] WP-2 合约任务书写明可选 `script` 键与闭集
- [x] WP-2 判据 `test_experiment_script_comes_from_the_plan.py`（17 例 + 子进程按压）
- [x] WP-3 宪章补 `progress-075` 链接 + `SHORT-REVISION-ROWS.md` 登记表 + 双向判据
- [x] WP-3 `verify_goal{076,090,095}` 三个验证器 + 断言集 + 两处登记
- [x] WP-4 `verify_goal098` + 断言集 + 两处登记
- [x] WP-4 宪章记账（程序表 / 预算 / 阶梯 / 进展 / 修订）+ ALL_PLAN
- [x] WP-5 收口验证器 100 条判词全过
- [x] WP-6 EC-02 真跑取证（上游恢复后 `SUCCEEDED`；真跑另外抓到第 8 个真缺陷并修复）

## 证据

| 项 | 文件 / 命令 | 读数 |
| --- | --- | --- |
| EC-01 结构面 | `tests/contracts/test_direction_to_report_v2_independence.py` | 18 passed（含按压） |
| EC-03 选择面 | `tests/application/test_experiment_script_comes_from_the_plan.py` | 17 passed（含子进程按压） |
| EC-04 回填验证器 | `tools/verify_goal{076,090,095}_closeout.py` | 48 / 51 / 54 条判词，0 FAIL |
| EC-04 短行登记 | `tests/tooling/test_short_archive_revision_rows_are_registered.py` | 7 passed（含两条按压） |
| EC-05 收口资产 | `tools/verify_goal098_closeout.py` | 100 条判词，0 FAIL |
| EC-02 真跑 | `.cursor/plans/goals/evidence/GOAL-20261027-098-ec02-novelty-independence-run.txt` | **`SUCCEEDED`**（`783e6dc7`）：两条判词 = `main/glm-5.3` + `main/minimax-m3`，作者 `novelty_writer` 不在其中；前几次失败读数逐条保留 |
| 契约与门 | `tests/contracts/ tests/loaders/ tests/tooling/…` | 634 passed / 72 skipped / 0 failed |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-27 | IN_PROGRESS | 建档 + WP-1…WP-6 落地；**七个 EC 全 PASS**（EC-02 在上游恢复后真跑成功取证） |
| 2026-10-28 | **DONE** | 收口账合上：EC-03 的**容器面**补取证（`test_experiment_script_selection_docker.py` + `evidence/GOAL-20261027-098-ec03-container-run.txt`，两个脚本各跑一次真容器、按容器指标的签名区分）⇒ 那份 docstring 里的悬空引用改成真实文件，并加一条**判据**钉住「引用了就必须在树」；本 PLAN 置 DONE、`ALL_PLAN` 勾选同步；两树复检在**最终 HEAD** 上重跑并归档判词 |

## 影响报告

- **Domain / API / schema**：无 DTO 变更。`novelty_author` 是**新增角色**（`role_type` 在
  schema 里是自由字符串，无需改枚举）；`design_script.py` 是**新增模块**；
  `ExperimentExecutionSpec` 一字未动（脚本选择走**计划产物**，不进契约）。
- **安全 / 凭据**：无新增凭据面。新增的 `novelty_author_model` 只用既有的 `main` 端点 +
  `LLM_MAIN_KEY`；`sk-` 仍只进 gitignored `.env`。**方案 (a)（模型写代码进容器）未做** ——
  它是安全面变更，登记为待拍板（`W-3`）。白名单选择面刻意**不接受**绝对路径 / `..` / 盘符。
- **兼容性 / 迁移**：`experiment_support.run()` 增一行调用；`plan_selected_script` 在没有
  `script` 键时**逐字**返回装配面的值（零回归，用 9 例判据钉住）。`design_from_plan` 只
  **新增** `plan_design_block`，既有 `read_design_from_plan` 一字未动。`len(roles)` 26→27
  与 `validate_bundle` 的 26→27 是**事实变更**，两处都逐条申报（RECHECK 有 `--numstat` 表）。
- **规模门**：`experiment_support.py` 450/450（本轮靠压缩三行注释换回一行）；
  `tests/application/test_experiment_script_comes_from_the_plan.py` 一度 451 行 ⇒ 把子进程
  按压形态分列到 `tests/application/subprocess_press_support.py`。
- **上游版本**：无新增依赖；无版本 pin 变更。
