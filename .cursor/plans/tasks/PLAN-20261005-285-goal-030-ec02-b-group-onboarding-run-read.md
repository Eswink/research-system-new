---
id: PLAN-20261005-285
slug: goal-030-ec02-b-group-onboarding-run-read
title: GOAL-030 cycle 2（EC-02）：B 组承接 —— `run.read` 的 RunStore 接线（`citation.validate` 经核实不可行，如实登记）
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-286-goal-030-ec02-b-group-onboarding.md
memory_entries: []
parent_goal: GOAL-20261005-030
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261005-030 的 **EC-02**。授权沿用该 GOAL 的 `authorization.ref`：
    「**新增 B 组能力承接**（`citation.validate` / `run.read` 等，**核实可行者为限**）」+
    「修实现过程中发现的**真缺陷**」+「新增判据 / 夹具（落 `tests/**`）」+ push-to-main-for-CI
    口径（**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据的**断言语义**；**不动** `policy.yaml` /
    `default_effect` / `_CAPABILITY_SCOPE`；**不让任何未放行能力变为协议可达**；**零**新依赖；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    按核实结论推进 B 组：**承接 `run.read`**（读既有 `RunStore` Port，与 HTTP 读面同一个
    `get_run`），并把「承接 ≠ 放行」做成**可区分**的机械事实；`citation.validate` 经实测
    判定**不可行**（声明它会打红两条 `tests/contracts/**` 的既有 pin 判据，而该面被本 GOAL
    的 `fix_policy` 明文禁改）⇒ **如实登记为受限面，不硬接**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **`run.read` 承接成立**：出厂目录（`tool_providers.yaml` 的 `m12_artifact`）声明它、
      `CanonicalReadProvider.list_tools` 真的承载它（专属 tool id `run_read`）、出厂绑定表
      有一条 `("run.read", "m12_artifact", "run_read")` —— 三者同轮在场。
    status: PASS
  - id: AC-2
    criterion: >-
      **真读得到**：给一个真在 `RunStore` 里的 run ⇒ 返回 `run_id` / `project_id` /
      `protocol_id` / `state` / 两个 manifest digest，**逐字段**与 store 事实一致；
      未冻结 ⇒ `null`（**不**回落冒充）。
    status: PASS
  - id: AC-3
    criterion: >-
      **缺依赖 / 未知 id 一律点名**：无 `RunStore` ⇒ 点名 `RunStore`；缺 `run_id` ⇒ 点名
      `run_id`；未知 run id ⇒ 点名该 id（由 `RunStore` 自己抛）。**不返回空壳**。
    status: PASS
  - id: AC-4
    criterion: >-
      **承接 ≠ 放行且可区分**：同一用例内同时断言「目录声明了它」与「真实
      `NativePolicyEvaluator(policy.yaml)` 判 `DENY` + `used default policy effect`」。
    status: PASS
  - id: AC-5
    criterion: >-
      **射程同源**（承 MEM-160，不得靠并集掩蔽）：
      `examples/config/tool_providers.yaml`（声明）、
      `tests/architecture/python/test_capability_coverage_is_implemented.py` 的
      `_IN_SCOPE`（+`run.read`）与 `_OUT_OF_SCOPE_REASONS`（−陈旧条目）、
      `docs/architecture/POLICY_SURFACE_AUDIT.md` 的 `run.read` 行（声明面列
      `roles` → `roles、tool_providers`）、provider 夹具能力列表 —— **同一轮**更新且全绿。
    status: PASS
  - id: AC-6
    criterion: >-
      **`citation.validate` 不可行的判定在树**：逐条写明打红了哪两条既有判据（文件 + 用例名 +
      断言）、它们为何在禁改面内、以及解除条件。
    status: PASS
  - id: AC-7
    criterion: >-
      **不改既有判据的断言语义**：`tests/contracts/**` 全绿且**逐字节未改**；
      AC-5 触及的是**夹具/登记表/文档声明面列**（同轮射程同步），不是断言强度。
    status: PASS
---

# PLAN-20261005-285 — GOAL-030 cycle 2（EC-02）

## B 组核实结论（逐条）

| 候选 | 取数面 | 判定语义 | 结论 |
| --- | --- | --- | --- |
| `run.read` | ✅ `RunStore` 是既有 Port（`list_runs`/`get_run`/`save_run`），两组合根都持有实例 | 不需要新语义（读既有域字段） | **可行 ⇒ 本轮承接** |
| `citation.validate` | ✅ `NcbiEutilsProvider._elink` → `normalize_elink` | 可写死（`pmc_links` 非空 ⇒ 通过） | **不可行 ⇒ 受限面**（见下） |

### `citation.validate` 为何不可行（实测，逐条）

把它声明进 `examples/config/tool_providers.yaml` 的 `ncbi_eutils.capabilities` 后，
**两条既有判据同时判红**（两条都在 `tests/contracts/**`，本 GOAL `fix_policy` 明文禁改）：

1. `tests/contracts/test_ncbi_provider_contract.py::TestCredentialAndHealth::test_list_tools_schema`
   —— 断言 `names == {"literature_search", "literature_read", "citation_inspect"}`；
   实测失败：`Left contains one more item: 'citation.validate'`。
2. `tests/contracts/test_europe_pmc_pin_and_registration.py::TestRegistration::test_existing_providers_are_untouched`
   —— 断言 `ncbi.capabilities == ["literature.search", "literature.read", "citation.inspect"]`；
   实测失败：`assert ['literature....ion.validate'] == ['literature....tion.inspect']`。

**消红的唯一路径是改这两条判据**（或改其 pin 值）⇒ 命中 GOAL 的明文不做。
按「**不得为凑数硬接**」登记为**受限面**。**解除条件**：对上述两处 pin 的同轮同步取得授权
（它们钉的是「既有 provider 的声明逐条未改」，而新增一条能力恰恰要改这一列为真）。

## 改动（显式路径）

| 文件 | 改动 |
| --- | --- |
| `adapters/canonical/run_read.py` | **新增**：`run.read` 的执行实现（读 `RunStore.get_run`，逐字段；缺 store / 缺 id 点名） |
| `adapters/canonical/read_surface.py` | 工具面描述子：`run_read` + `run.read` 映射 |
| `adapters/canonical/read_provider.py` | 构造参数 `run_store` + 一行委派（恰守 450 行） |
| `services/api/session_tool_support.py` | 绑定表 + `session_tool_face` / `sqlite_session_tools` / `canonical_read_register` 透传 `run_store` |
| `services/api/composition.py` | `_SqliteStoreParts.runs_store`（**复用同一实例**给 `ApiDeps`，消灭第二个 store 实例）；**净增 0 行**（450） |
| `services/api/pg_composition.py` | `session_tool_face(..., c["runs_store"])` |
| `examples/config/tool_providers.yaml` | 声明 `run.read` |
| `tests/architecture/python/test_capability_coverage_is_implemented.py` | 射程清单 + 陈旧条目移除（同轮同步） |
| `docs/architecture/POLICY_SURFACE_AUDIT.md` | `run.read` 行声明面列同轮更新 |
| `tests/adapters/canonical/test_canonical_read_provider.py` | provider 夹具能力列表同轮更新 |
| `tests/adapters/canonical/test_run_read_onboarding.py` | **新增判据**（10 passed） |

## 按压记录（两向，逐字节复原）

**撤回 `run_read` 的能力映射**（`read_surface.py` 的 `_TOOL_CAPABILITIES` 去掉该条目）⇒
**3 failed**，每条都点名 `run.read`：
- `test_the_provider_lists_it_when_declared`（实现面不复存在）；
- `test_every_declared_capability_has_an_implementation`（**声明了但没实现** ⇒ 点名）；
- `test_the_in_scope_list_has_a_floor`（射程内清单里有不具实现的条目）。
复原后 `sha256sum -c` 三文件全 `OK` ⇒ 全绿。

## 本地验证

- `tests/adapters/canonical/test_run_read_onboarding.py` ⇒ **10 passed**；
- `tests/adapters/canonical` ⇒ **34 passed**；
- `tests/architecture/python + tests/application/preflight + tests/application/evidence +
  tests/contracts + tests/loaders + tests/tooling + tests/adapters + tests/e2e + tests/api`
  ⇒ **3471 passed / 89 skipped**（无回归）；
- `ruff check` / `ruff format --check` 绿；`mypy` 绿（1097 files）；
- `services/api/composition.py` 恰 **450 行**（规模门绿）。

## 剩余差距

- EC-03（科研动作深度）/ EC-04（判据射程自查）/ EC-05（自举收口）未做；
- `citation.validate` 与五条未放行读能力同属**受限面**（前者待 pin 授权，后者待 `D-02(b)` 拍板）；
- `run.read` 已承接但**未放行** ⇒ 不可协议可达（与另五条同）。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7）。

## 实施清单

- [x] **WP-A（核实）**：`run.read` 的 `RunStore` Port 面核实（两组合根都持有实例）⇒ 可行。
- [x] **WP-B（核实并判否）**：`citation.validate` 的可复用取数面核实（`_elink`）→ 实测声明
      会打红两条 `tests/contracts/**` 的既有 pin 判据 ⇒ **判定不可行**，登记受限面。
- [x] **WP-C（实现）**：`adapters/canonical/run_read.py` + `read_surface` 映射 +
      `read_provider` 一行委派（恰守 450 行）。
- [x] **WP-D（装配）**：`session_tool_support` 绑定表与四个入口透传 `run_store`；
      两个组合根接线；`_SqliteStoreParts.runs_store` **复用同一实例**（净增 0 行）。
- [x] **WP-E（射程同源）**：目录 / `_IN_SCOPE` / 审计文档声明面列 / provider 夹具**同轮**更新。
- [x] **WP-F（判据）**：`tests/adapters/canonical/test_run_read_onboarding.py`（10 passed）。
- [x] **WP-G（按压两向）**：撤回能力映射 ⇒ 3 failed；复原 `sha256` 全 `OK`。
- [x] **WP-H（记录）**：本 PLAN + `RECHECK-20261005-286` + `ALL_PLAN` 投影 + GOAL 回写。

## 证据

- **判据**：`uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical/test_run_read_onboarding.py -q`
  ⇒ **10 passed**。
- **受判面**：`tests/architecture/python` + `tests/application/preflight` +
  `tests/application/evidence` + `tests/contracts` + `tests/loaders` + `tests/tooling` +
  `tests/adapters` + `tests/e2e` + `tests/api` ⇒ **3471 passed / 89 skipped**。
- **按压判词**：三条失败各自点名 `run.read`（`set() == {'run_read'}` /
  `('声明了承接但既没有实现、也没有登记理由', ['run.read'])` / `('射程内清单里有不具备实现能力的条目', ['run.read'])`）。
- **不可行判定判词**：`Left contains one more item: 'citation.validate'`（两条 pin 判据）。
- **质量门**：`ruff check` / `ruff format --check` / `mypy`（1097 files）/ 规模门
  （`composition.py` 恰 450 行）绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 2 derive）；WP-A/WP-B 核实（一条可行、一条判否）。 |
| 2026-10-05 | DONE | WP-C…WP-H 收口；判据 10 passed；按压两向逐字节复原；`RECHECK-20261005-286` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：产品 6 文件（新 `run_read.py` + `read_surface` / `read_provider` /
  `session_tool_support` / `composition` / `pg_composition`）+ 配置 1 文件（声明）+
  判据 1 文件 + 夹具 1 文件 + 文档 1 文件。
- **Domain/API/schema 变化**：无 DTO / OpenAPI 变化；新增一条工具面能力（`run.read`）。
- **安全/凭据变化**：**零**新凭据面；`policy.yaml` 未动；默认 deny 不变；
  `run.read` **未放行**（判据钉住该状态）。
- **兼容性/迁移风险**：`ApiDeps.runs_store` 与 `_SqliteStoreParts.runs_store` 现在**共享实例**
  —— 语义更正确（同一 run 读写必须同一实例），但属行为面变化（见 `RECHECK` 的 `W-2`）。
- **上游版本影响**：无。

## 无可复用事实

本轮产出是**能力承接 + 判据**，不含新的跨 GOAL 工程约定。两条判定（`run.read` 可行 /
`citation.validate` 不可行）的对象是**本仓当前的 pin 判据布局**，属**现状事实**而非通用约定
⇒ 写在 GOAL 记录与 `RECHECK` 里，**不另立 `MEM`**。
