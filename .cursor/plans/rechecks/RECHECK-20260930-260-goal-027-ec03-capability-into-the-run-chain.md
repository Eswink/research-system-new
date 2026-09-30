---
id: RECHECK-20260930-260
slug: goal-027-ec03-capability-into-the-run-chain
title: GOAL-027 EC-03 复检：新能力接进运行链（声明进编译产物 / 三类给参正反向 / 性质由声明决定 / 读面四列 / 反证成对）
plan_id: PLAN-20260929-259
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-30
completed_at: 2026-09-30
owners:
  - root-agent
---

# RECHECK-20260930-260 — GOAL-027 EC-03 复检

**复检口径**：不采信工具自己的叙述，也不采信「源码里写着判据」；本文件给出**可复核观察面**
（命令 / 判词行 / `rc` / raw `sha256` / 实测值）。**未实跑的不记通过**。

## 检查结果

### 1. 交付物属实（新增协议 + 判据 + 支持件，四道静态门）

- `examples/protocols/real_literature_chain_v1.yaml`（**60 行**）：`analysis` phase
  声明 `capability_execution: run_chain`、能力 `literature.search` / `literature.read`、
  合约 `real_retrieval_deliverable`（覆盖**两维**）、输入 `input-brief:real_research_v1`。
- `tests/e2e/test_literature_chain_run_offline.py`（**436 行**，无超 50 行函数）
  + `tests/e2e/literature_chain_support.py`（**285 行**）。
- 四道门：`ruff check` ⇒ `All checks passed!`；`ruff format --check` ⇒ 已格式化；
  `mypy`（strict）⇒ `Success: no issues found`；规模 436 / 285 < **450**。
- `validate_bundle.py` ⇒ **`验证通过`**（EXIT=0；含「Role / Agent / Model / Team / Task /
  Protocol 引用一致」——证明新协议**没有悬空引用**）。

### 2. 判定对象是产品那条链（不是夹具）

判据经 **Port 面与产品函数**驱动：`RunChainCall` → `execute_run_chain_capabilities`
（策略 `ScopedPolicy` + `require_frozen_tool_set` + 真 provider）→ `register_tool_evidence`
（唯一准入入口）→ `GET /runs/{id}/evidence`（读面投影）。装配走
`tests/e2e/live_run_support.openhands_deps`（真 adapter + mock relay），只有传输被换成
`httpx.MockTransport`（离线纪律）——**与既有离线判据同一手法**。

### 3. 五条 AC 的实测（11 passed）

```text
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_literature_chain_run_offline.py -q
⇒ 11 passed in 13.96s
⇒ egress guard: judged 9 connection attempt(s); blocked 0
```

- **AC-1 声明进编译产物**：YAML 逐字 `capability_execution: run_chain`；
  `compile_protocol(...).plan.tool_requirements` 的 provider 集合含 `europe_pmc`。
- **AC-2 三类给参**（正向 + 反向成对）：
  - 正向：离线传输里第 1 条请求 = `reproducibility of computational research`（brief 的
    `retrieval.query`，即 `arguments_from_input`）；第 2 条 = `EXT_ID:39284801`、
    第 3 条 = `EXT_ID:40601758`（即 `ids_from_previous` 拿的是**检索响应里返回的真 PMID**，
    单测 `retmax: 3` 来自 `fixed_arguments`）；
  - 反向：抹掉 `retrieval.query` ⇒ `retrieval.query` 点名 + **零请求**；
    零命中 ⇒ `'ids'` 点名 + **不再发读取请求**（`transport.requests == [BRIEF_QUERY]`）。
- **AC-3 性质由声明决定（两向 + 一处分化）**：
  - 声明 `www.ebi.ac.uk` ⇒ `{RETRIEVED}`；
  - **声明为空 ⇒ 触网前拒绝**（`outside the declared network_domains`，零请求）——
    这是 `europe_pmc` 的真实语义（声明同时是运行期出口门），**不是**降级；
  - 不声明的 stdio MCP provider ⇒ `{GENERATED}`（同一判定点、不同 adapter）。
- **AC-4 读面四列（本 EC 的核心）**：run `SUCCEEDED`；读面两条工具证据
  `(europe_pmc, literature_search)` / `(europe_pmc, literature_read)`；读取步
  `id` / `source_ref` / `content_digest` / `source_trust_label=RETRIEVED` 四列齐，
  `id` 与 `source_ref` 各含真 PMID `39284801`，`artifact_id` 以 `tool-result:` 开头；
  `RETRIEVED` 来源 ≥2 条；`USER_PROVIDED`（声明输入）`tool_refs` 为空。
- **AC-5 反证成对**：去掉能力步接线 ⇒ 零工具观测 + **零请求** + run `FAILED`，
  判词含 `acceptance gate` 与 `retrieved sources`（证明判拒来自**覆盖判据的性质维度**，
  不是别的门）。

### 4. 按压矩阵（三条，先红后绿 + 逐字节复原）

| 按压 | 改动 | 实测（红） | 复原验证 |
| --- | --- | --- | --- |
| P-F | 协议声明 `run_chain` → `session` | **3 failed**（声明面 1 + 读面 2） | `4ad4ade4e4e82bb8cef9a589217efa72ba4348ce115ef59a09d28038882b9f87`（= 基线）⇒ 11 passed |
| P-G | `result_handler.py` 不把 `retrieved_evidence` 并进 claim | **1 failed**（**只**钉读面四列那条） | `37634dda32ef75234fbd5d3d42b33b0439cb094f327b39bd14c7ac08e2a6c366`（= 基线）⇒ 13 passed |
| P-H | `phase_capabilities.py::_trust_label_for` 判定被架空 | **4 failed**（本 EC 1 + 既有 `test_run_chain_retrieval_offline` 1 + 既有 `test_run_chain_capabilities` 1 + 读面 1） | `e0dc7699b6238e163785631d6aae935eba5e8d33f39cbfb0e50d69093ea5b2f2`（= 基线）⇒ 24 passed |

**P-H 的观察**：架空的是一条**共享**判定点 —— 既有两份判据同时转红
⇒ 它证明的不仅是本 EC 的判据有牙，还证明本 EC 没有绕开既有语义另起一套。

### 5. 一处判据口径的实测校准（如实登记）

首版把「不声明网络域 ⇒ `GENERATED`」写成对 `europe_pmc` 的普遍断言 ⇒ 实测**判红**：

```text
run-chain capability step failed: europe pmc host 'www.ebi.ac.uk' is outside
the declared network_domains []
```

`europe_pmc` 的 URL 策略（EC-01 的净增量）把**声明**同时当运行期出口门
⇒ 声明为空时它在**触网前拒绝**（零请求），`GENERATED` 那一向因此改用
**不声明的 stdio MCP provider** 取证。**错的是我的普遍化断言，产品代码未因此改动**；
判据现在把两种真实语义分开钉住（拒绝 vs 降级）。

### 6. 回归面（既有判据逐字节未改）

| 套件 | 结果 |
| --- | --- |
| 本 EC + `tests/e2e/test_run_chain_retrieval_offline.py`（GOAL-011 的判据，**一字未改**） | 13 passed |
| 上述 + `tests/application/run_orchestration/test_run_chain_capabilities.py`（**一字未改**） | 24 passed |
| `tests/e2e/` + `tests/loaders/` + `tests/architecture/python/` + `tests/tooling/`（一次合并运行，canonical DSN pin） | **1644 passed, 12 skipped**（EXIT=0） |

`egress guard: BLOCKED …` 的若干行是**该守卫自己的用例**（故意构造被拒连接并断言点名），
不是失败。

### 7. 离线纪律（实测）

本 EC 的判据**零出网**：Europe PMC 链走 `httpx.MockTransport`（真解析不上网）、
MCP 链走真 stdio 子进程（`tools/research_mcp_server.py`，离线确定性）。
`tests/egress_guard.py` **一字未改**（默认门离线口径未被放宽）。

### 8. 未覆盖范围（明写，不夸大）

- 新协议与 `real_retrieval_research_v1` **并存**：两条都读同一份 brief，检索策略不同
  （本协议的两步链含按 id 精确取记录 ⇒ 读面出现第二条工具证据）；
  本 EC **不**声称新协议是既有协议的替代。
- `ids_from_previous` 的**点分路径**只覆盖单层信封（`structured.ids`）；更深嵌套未测
  （MCP 进链证据在 `tests/contracts/test_mcp_registration_and_refutations.py`，本 EC 未重复）。
- `network_domains` 的运行时出口执法**只覆盖声明它的 provider**（`europe_pmc`）；
  仓内没有全局出口网关。
- 读面认证 / 多租户 / BOLA·BFLA / 部署面 / `R-M1` —— 承继 GOAL-027 的未覆盖范围，逐条仍在位。
- **不宣称**项目安全（`R-M1` 未收口）；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

### 9. as-is 本机 m0 到 23/23（记录写入之后，独占运行，首跑即终态）

```text
uv run --frozen --no-sync python -B \n  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4921 passed, 21 skipped（python/tests 段 in 704.33s）
⇒ 日志 scratch/goal027-c3-m0.log（canonical DSN pin；**零 python 残留**）
```

**首跑即终态**（无红点）。用例数 4921（cycle 2 收口 4908）⇒ 只增不减。
环境口径：`RESEARCHOS_POSTGRES_DSN`=test DSN + `DATABASE_URL` / `POSTGRES_DSN` / `RESEARCHOS_DATABASE_URL` 置空 + `LLM_MAIN_KEY=""`。

### 10. CI 台账到终态（推送 `dd8bafe`；原始 JSON 实查）

M0 [**36674564892**](https://github.com/Eswink/research-system-new/actions/runs/36674564892) 八 job 全 `success`；Push-on-main（CodeQL）[**36674564604**](https://github.com/Eswink/research-system-new/actions/runs/36674564604) 3/3 `success`。两者 `run_attempt=1`（一次成功、无 flake）。原始 JSON 实查：

```text
run=36674564892 name='M0 Quality Gates' conclusion=success attempt=1 head=dd8bafe3 jobs=8 ok=8 bad=[]
run=36674564604 name='Push on main' conclusion=success attempt=1 head=dd8bafe3 jobs=3 ok=3 bad=[]
```

轮询日志 `scratch/goal027-c3-ci-poll.log`；取值文件 `scratch/goal027-c3-run-{36674564892,36674564604}{,-jobs}.json`。空集合 / 空字段一律按「未取证」处理（本轮到终态，无 cancelled）。

## 结论

`PASS_WITH_WARNINGS`。五条 AC 全部 PASS：声明进编译产物（AC-1）；三类给参正反向成对、
缺一 fail closed（AC-2）；性质由唯一判定点按**声明**给、两向 + 一处分化实测（AC-3）；
一次离线 run 的真 PMID 经读面四列可读、`SUCCEEDED`（AC-4）；反证成对 + 按压三条逐字节复原 +
既有判据一字未改（AC-5）。

**警告（残余，逐条在位）**：

- `W-1`：新协议与既有检索协议并存（同读一份 brief）；语义边界写在协议注释里，
  **没有**机器判据防止两者的检索策略未来漂移成同一个。
- `W-2`：`ids_from_previous` 点分路径只覆盖单层信封；深层嵌套未测，改动它时无判据保护。
- `W-3`：性质两向由**两个 adapter** 取证（`europe_pmc` 拒绝 / MCP `GENERATED`）——
  同一判定点，但若未来有 adapter 在「声明为空」时行为再分化，本判据不会自动覆盖新形态。
- `W-4`：本 EC 的离线 run 用受控 `FakePolicyEvaluator`（默认 ALLOW）；
  策略 DENY 面对本协议未重测（既有判据在 `test_run_chain_capabilities.py` 覆盖 `ncbi` 侧）。
