---
id: PLAN-20260929-259
slug: goal-027-ec03-capability-into-the-run-chain
title: GOAL-027 cycle 3（EC-03）：能力接进运行链 — MCP/文献 provider 的 run-chain 声明 + 真标识 + 读面可见 + trust_label
status: DONE
created_at: 2026-09-30
updated_at: 2026-09-30
latest_recheck: .cursor/plans/rechecks/RECHECK-20260930-260-goal-027-ec03-capability-into-the-run-chain.md
memory_entries:
  - .cursor/memory/entries/MEM-20260930-176-run-chain-declaration-is-the-only-deterministic-retrieval-door.md
parent_goal: GOAL-20260929-027
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-027 的 **EC-03**（能力接进运行链）。授权沿用该 GOAL 的
    `authorization.ref`：「**新增 provider**（REST / MCP 均可）并把它们接进运行链
    （`capability_execution: run_chain`）」+「**新增 / 扩展协议与 phase 声明**
    （`examples/protocols/`、`examples/contracts/`）」+「新增判据 / 夹具 / 探针
    （落 `tests/**` ⇒ m0 条数仍 `23`）」；push-to-main-for-CI 口径（**只推 `main`**、
    不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**；**不修改**任何既有判据 / 门禁 /
    阈值 / 放行面（点名：`tests/e2e/test_run_chain_retrieval_offline.py`、
    `tests/e2e/test_run_chain_retrieval_live.py`、`tests/application/run_orchestration/
    test_run_chain_capabilities.py`、`tests/architecture/python/
    test_run_chain_capability_exposure.py`、`tests/egress_guard.py`、
    `tests/application/test_m2_audit.py`、`tests/application/preflight/**`、规模门、
    三道记录面判据、两树入口判据）；**不动** capabilities 词表 / `_CAPABILITY_SCOPE` /
    `policy.yaml`（复用既有能力名 ⇒ 三处零改动）；**不改** `PRODUCT_ROOTS` / m0 条数 /
    作业结构（终态行仍 `23`）；**零**新依赖；**默认门离线**（判据经 `httpx.MockTransport`
    走真解析，**不触网**）；真标识一律**线上实取**（真 PMID / DOI），**不得**编造；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    **一处对既有文件的受控改动（如实登记）**：`services/api/demo.py` 的
    `DECLARED_INPUTS` 若需新增条目（新协议声明输入制品）——只**追加**一条，
    **不动**既有三条；其既有消费者判据（`test_vertical_slice_happy_path` 的
    `4 + len(DECLARED_INPUTS)` 形态）按**推导**计数 ⇒ 追加不判红。
    若无需新输入制品则**零改动**（优先此路）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **run-chain 声明在树且经产品链可读**：新增协议（`examples/protocols/`）声明
      `capability_execution: run_chain`，且其 phase 的 `required_capabilities` 覆盖
      新 provider 的能力（`literature.search` / `literature.read`）；经
      `load_protocol` + `compile_protocol` 后 `plan.tool_requirements` 的
      `provider_ids` 含该 provider（**声明不是散文**：编译产物可证）。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明式给参 + 缺一 fail closed**：`RunChainCall` 三类参数来源
      （`arguments_from_input` / `fixed_arguments` / `ids_from_previous`）各自有
      **正向证据**（真的取到了值并真的发给了 provider）与**反向证据**（该来源缺席时
      `InvalidInputError` ⇒ 点名拒绝；零请求 / 零工具观测）。
    status: PASS
  - id: AC-3
    criterion: >-
      **证据落 canonical 且 `trust_label` 由声明决定**：`register_tool_evidence`
      是唯一准入入口；`RETRIEVED` 只由 provider 声明的 `network_domains` 触发
      （`_trust_label_for` 是唯一判定点）。两向都在判据里：声明网络域的 provider
      ⇒ `RETRIEVED`；不声明的 ⇒ `GENERATED`（同一条链、同一份内容）。
    status: PASS
  - id: AC-4
    criterion: >-
      **读面可见（本 EC 的核心交付）**：一次离线 run 里跑出**至少 2 条真实来源**
      （真 PMID / 真 DOI），且 `GET /runs/{id}/evidence` 的投影真能读到它们——
      断言四列（`id` / `source_ref` / `content_digest` / `source_trust_label`）
      与 `tool_refs`；只 `register_evidence` 不 `attach_relation` 的路径**读不到**
      （反证：去掉 relation ⇒ 读面为空 ⇒ 覆盖判据判拒 ⇒ run 收敛 FAILED）。
    status: PASS
  - id: AC-5
    criterion: >-
      **反证两向 + 按压 + 既有判据逐字节未改**：① 去掉 run-chain 声明 ⇒ 零工具观测
      且 `EVIDENCE_COVERAGE` 的性质维度判拒（`FAILED`，判词点名）；② 按压（改声明 /
      删 relation / 改 trust 声明）先红后绿 + raw `sha256` 逐字节复原；
      ③ 既有 run-chain 判据（offline / capabilities / exposure 三份）**一字不改**复跑全绿。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 判据文件 / 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | run-chain 声明在树 + 编译产物含该 provider | 新协议（`examples/protocols/`） | **PASS** |
| AC-2 | 三类参数来源各自正反向证据；缺一 fail closed | 新判据 | **PASS** |
| AC-3 | `trust_label` 两向（声明 / 不声明）由唯一判定点给 | 新判据 | **PASS** |
| AC-4 | ≥2 条真实来源 + `GET /runs/{id}/evidence` 四列可读 | 新判据（离线 e2e 形态） | **PASS** |
| AC-5 | 反证两向 + 按压 + 既有判据逐字节未改 | 新判据 + 按压留档 | **PASS** |

## 目标

GOAL-027 的 **EC-03**：让系统在 run 时**确定性执行**检索（而不是把证据押在「模型恰好调了
工具」上）。既有装置（`capability_execution: run_chain` + `RunChainCall` +
`execute_run_chain_capabilities` + `register_tool_evidence`）由 GOAL-011 建立，
本 EC 的净增量是：**把 cycle 2 新接入的 MCP provider 与 cycle 1 的 Europe PMC
接进这条链**，并证明**读面真能读到**两条真实来源。

## 实施清单

- [x] WP-1：勘察三条失败面（声明缺席 / relation 缺席 / 性质维度）在现有判据里的覆盖情况
- [x] WP-2：新增协议（run-chain 声明 + 真标识检索）
- [x] WP-3：新增离线判据（真解析 + 真标识 + 读面四列 + 反证两向）
- [x] WP-4：按压（改声明 / 删 relation / 改 trust 声明）+ 逐字节复原
- [x] WP-5：消费者复跑（既有三份 run-chain 判据一字不改）
- [x] WP-6：记录（PLAN / RECHECK / MEM / GOAL 回写 / ALL_PLAN）+ m0 + push + CI

## 设计要点（本轮勘察已核实）

1. **`ids_from_previous` 的点分路径是 cycle 2 的产物**：MCP provider 的溢出内容是一层
   信封（`{text[], structured}`）⇒ 链式取 `structured.ids`（`phase_capabilities.py`）。
   本 EC 的判据要覆盖这条路径（它是 MCP 进链的**前置条件**）。
2. **读面只经 claim relations 投影**（`services/api/run_evidence.py::evidence_of_run`）：
   只 `register_evidence` 不 `attach_relation` ⇒ 读面为空。这是 EC-03 ④ 的反证面。
3. **`trust_label` 的唯一判定点**是 `phase_capabilities.py::_trust_label_for`
   （按 provider 声明的 `network_domains` 给值）；本 EC 判据必须**两向**覆盖它。
4. **离线装配形状**（沿 `tests/e2e/test_run_chain_retrieval_offline.py`）：
   `httpx.MockTransport` + 真 provider + `with_run_chain_capabilities` 注入；
   断言读面快照（`_read_chain` 的 `evidence` 列表）。
5. **既有判据一字不改**：offline / capabilities / exposure 三份是本 EC 的**回归面**。

## 证据

### ① 交付物与四道静态门

- 新增协议 `examples/protocols/real_literature_chain_v1.yaml`（**60 行**）：`analysis` phase 声明
  `capability_execution: run_chain` + `literature.search` / `literature.read` +
  `task_contract: real_retrieval_deliverable`（覆盖**两维**）+ `inputs: [input-brief:real_research_v1]`。
- 新增判据 `tests/e2e/test_literature_chain_run_offline.py`（**436 行**，无超 50 行函数）
  + 共享支持件 `tests/e2e/literature_chain_support.py`（**285 行**）。
- `ruff check` / `ruff format --check` / `mypy`（strict）三道门 ⇒ 全绿；规模 436 / 285 行 < 450。
  `validate_bundle.py` ⇒ `验证通过`（含「Role / Agent / Model / Team / Task / Protocol 引用一致」）。

### ② 判据实跑（11 passed）

```text
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_literature_chain_run_offline.py -q
⇒ 11 passed in 13.96s
⇒ egress guard: judged 9 connection attempt(s); blocked 0
```

| 面 | 实测 |
| --- | --- |
| 声明（AC-1） | YAML 里 `capability_execution: run_chain`；编译产物 `plan.tool_requirements` 的 provider 集合含 `europe_pmc` |
| 三类给参（AC-2） | 正向：离线传输里第 1 条请求 = brief 的 `reproducibility of computational research`，第 2 条 = `EXT_ID:39284801`（**检索回来的真 PMID**），第 3 条 = `EXT_ID:40601758`；反向：query 路径缺 ⇒ `retrieval.query` 点名 + **零请求**；零命中 ⇒ `'ids'` 点名 + 不再发读取请求 |
| 性质（AC-3） | 声明 `www.ebi.ac.uk` ⇒ `{RETRIEVED}`；声明为空 ⇒ **触网前拒绝**（`outside the declared network_domains`，零请求 —— 实测语义，**不是**降级）；不声明的 stdio MCP provider ⇒ `{GENERATED}` |
| 读面（AC-4） | run `SUCCEEDED`；`GET /runs/{id}/evidence` 读到两条工具证据 `(europe_pmc, literature_search)` / `(europe_pmc, literature_read)`；读取步四列齐（`id` / `source_ref` / `content_digest` / `source_trust_label=RETRIEVED`）且 `id` / `source_ref` 各含真 PMID `39284801`、`artifact_id` 以 `tool-result:` 开头；`RETRIEVED` 来源 ≥2 条、`USER_PROVIDED` 声明输入 `tool_refs` 为空 |
| 反证（AC-5） | 不接线 ⇒ 零工具观测 + **一个请求都不发** + run `FAILED`，判词含 `acceptance gate` 与 `retrieved sources`（覆盖判据的**性质维度**） |

### ③ 按压矩阵（三条，先红后绿 + 逐字节复原）

| 按压 | 改动 | 实测（红） | 复原 raw `sha256` |
| --- | --- | --- | --- |
| P-F | 协议 `capability_execution: run_chain` → `session` | **3 failed**（声明面 1 + 读面 2） | `4ad4ade4…b9f87`（= 基线）⇒ 11 passed |
| P-G | `result_handler.py` 不把 `retrieved_evidence` 挂进 claim | **1 failed**（读面四列那条 —— 只钉投影面） | `37634dda…2a6c366`（= 基线）⇒ 13 passed |
| P-H | `phase_capabilities.py::_trust_label_for` 判定被架空 | **4 failed**（本 EC 1 + 既有 `test_run_chain_retrieval_offline` 1 + 既有 `test_run_chain_capabilities` 1 + 读面 1）⇒ 证明是**共享判定点** | `e0dc7699…3ea5b2f2`（= 基线）⇒ 24 passed |

### ④ 回归面

| 套件 | 结果 |
| --- | --- |
| `tests/e2e/test_literature_chain_run_offline.py` + `test_run_chain_retrieval_offline.py` | 13 passed（后者**一字未改**） |
| 上述 + `tests/application/run_orchestration/test_run_chain_capabilities.py` | 24 passed（该文件**一字未改**） |
| `tests/e2e/` + `tests/loaders/` + `tests/architecture/python/` + `tests/tooling/`（一次合并运行，canonical DSN pin） | **1644 passed, 12 skipped**（EXIT=0；`BLOCKED …` 行是 egress guard 自己的用例） |

### ⑤ 一处判据口径的实测校准（如实登记）

首版把「不声明网络域 ⇒ `GENERATED`」写成对 `europe_pmc` 的断言 ⇒ 实测**判红**：
`europe_pmc` 的 URL 策略把**声明**同时当运行期出口门，声明为空时它在触网前**拒绝**
（`europe pmc host 'www.ebi.ac.uk' is outside the declared network_domains`，零请求）。
`GENERATED` 那一向改用**不声明的 stdio MCP provider** 取证（同一判定点、不同 adapter）。
⇒ 错的是我的普遍化断言，**产品代码未因此改动**；判据现在把两种真实语义分开钉住。

### ⑥ as-is 本机 m0（记录写入之后，独占运行，首跑即终态）

```text
uv run --frozen --no-sync python -B   .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4921 passed, 21 skipped（python/tests 段 in 704.33s）
⇒ 日志 scratch/goal027-c3-m0.log（canonical DSN pin、不接管道、零 python 残留）
```

用例数 4921（cycle 2 收口 4908）⇒ **只增不减**，与「新增判据 ⇒ m0 条数仍 23」一致。

### ⑦ CI 台账

**M0 [`36674564892`](https://github.com/Eswink/research-system-new/actions/runs/36674564892) 八 job 全 `success` + Push-on-main（CodeQL）[`36674564604`](https://github.com/Eswink/research-system-new/actions/runs/36674564604) 3/3 `success`**；两者 `run_attempt=1`（**一次成功、无 flake**；原始 JSON 实查 `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=dd8bafe3…` 与推送 sha 一致；轮询日志 `scratch/goal027-c3-ci-poll.log`）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-30 | IN_PROGRESS | cycle 3 派生：EC-03 = 能力接进运行链。勘察已定：读面经 claim relations 投影、`trust_label` 唯一判定点在 `_trust_label_for`、MCP 信封需点分路径（cycle 2 已提供）。 |
| 2026-09-30 | DONE | **cycle 3 收口**：AC-1…AC-5 全部 PASS。新增协议 + 判据 + 支持件；**按压三条**（声明 / relation 投影 / 性质判定点）先红后绿且 raw `sha256` 逐字节复原；**既有三份 run-chain 判据一字未改**（其中两份参与 P-H 复压）；读面四列 + 真 PMID 实测可读；反证（不接线 ⇒ 零观测 + 零请求 + 性质维度判拒）成对。一处判据口径按实测校准（`europe_pmc` 空声明 = 拒绝而非降级）。**残余**：`W-1` 新协议与既有检索协议并存（两条都消费同一份 brief，检索策略不同）；`W-2` MCP 进链证据在 EC-02 文件里（单层信封，未覆盖深层嵌套）；`W-3` 性质维度的两向用两个 adapter 取证（同一判定点，但 adapter 语义有别）。 |

## 影响报告

- **Domain/API/schema**：**零** Domain 类型变化、**零** OpenAPI 变化、**零** migrations。
  新增：1 个协议（`examples/protocols/`）+ 1 份判据 + 1 份支持件。
  **零产品代码改动**（本 EC 只消费既有产品面：`RunChainCall` / `execute_run_chain_capabilities` /
  `register_tool_evidence` / `GET /runs/{id}/evidence`）。
- **安全/凭据**：新协议复用既有能力名 ⇒ capabilities 词表 / `_CAPABILITY_SCOPE` /
  `policy.yaml` **三处零改动**；判据全部离线（Europe PMC 链走 `httpx.MockTransport`、
  MCP 链走真 stdio 子进程，**零出网**）；`trust_label` 由**声明**决定（`_trust_label_for`
  是唯一判定点，本 EC 未改它，按压 P-H 证明它与既有判据共享）。
  **不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：纯**追加**（新协议 + 新判据）；既有三份 run-chain 判据、既有协议、
  既有 provider 声明**逐字节未改**。无数据迁移。
- **上游版本影响**：零新依赖。
- **可靠性口径**：运行链给参沿用既有 fail-closed 语义；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径固定为 at-least-once + idempotency + deduplication）。
- **剩余差距 / 下一项任务**：本 EC 的**未覆盖范围**——新协议与 `real_retrieval_research_v1`
  并存（同读一份 brief、检索策略不同：本协议两步链含按 id 精确取记录）；
  深层信封嵌套未测；`network_domains` 的运行时执法仍只覆盖声明它的 provider。
  cycle 4 = **EC-04**（多 role 科研子迭代）。
