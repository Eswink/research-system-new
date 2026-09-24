---
id: RECHECK-20260925-163
plan_id: PLAN-20260925-161
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-015-cycle1 + 普查探针（scratch/goal015_c1_*，只读 / 零出网）
baseline_ref: d472b7f（cycle 1 derive：PLAN-161 + ALL_PLAN 投影 + child_plans）
checked_head: 当前树（WP1–WP5 实施 + 收口记录）
---

# RECHECK-20260925-163 — 跨套件隔离普查与两处真实来源修复（GOAL-015 cycle 1）

## 检查范围

① 普查是否**先于修**且每条红有**可复现最小命令**（AC-1）；② R-1 的修法是否落在**真实
来源**（被测系统的排序语义）而非调用例/门禁迁就（AC-2）；③ R-2 的修法是否为**夹具隔离**
且不改任何判据（AC-3）；④ **同一套件组合连续两轮全绿**（AC-4）；⑤ **成对反证**：修前状态
能否**重新构造**出同签名红（AC-5）；⑥ **判据只增不减**：`git diff` 逐条 + 逐用例 ID 差集
（AC-6）；⑦ 本地门（定向套件 / 规模 / 快照 / m0 / 治理）与 CI 到终态。

## 检查结果

### 一、普查（先于修；表在册，每条可复跑）

`docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`：as-is 本机 m0 = **21/23**，两条未绿项拆成
**四个可独立复现的红项**（R-1…R-4）+ 一段历史签名复核。最小复现命令逐条为：

| ID | 最小复现（逐字） | 修前观测 | 分类 |
| --- | --- | --- | --- |
| R-1 | `pytest tests/contracts/test_protocol_draft_store_order_tie.py -q` | **3 failed in 0.34s**（三实现全红） | (i) 真实缺陷 |
| R-2 | `LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q` | `egress guard: FAIL … blocked 2`（**2.24s** 取代 569s 全量） | (i) 真实缺陷（测试隔离） |
| R-3 | 同 m0 的 `framework/validate_bundle` 检查项 | `FAILED [framework/validate_bundle]: exit 1` | (iii) 门禁 scoping |
| R-4 | 见第 4 节（定向跑挂死 vs 全量跳过） | 定向跑 120s 无输出（exit 143） | (i) 真实缺陷（测试隔离） |

**历史签名复核（普查必须点名）**：`W-D` 的最小组合（`pytest tests/api/test_worker_plane_composition.py
tests/e2e/test_pg_crash_restart.py -q`）在本日**实测 7 passed** ⇒ 该形态已由后续改动消解，
不再列为在册红项；**同类修法口径**（修共享来源、不调用例）沿用 GOAL-007 的判例。

**一处承继归因的事实更正**（普查第 2 节）：此前把出站红灯归因为「本机 fake-IP DNS 特殊 ⇒
环境项」。实测：判据放行面只有 `localhost`，任何**可解析**的非环回目的地都会被拦并判红；
本机 DNS 只让 `kind` 显示为 `private`。**凭据在场**才是红的原因（CI 无 `.env` ⇒ 不可解析 ⇒
不探端点 ⇒ 全绿）⇒ 分类改为「真实缺陷（测试隔离）」，处置是修隔离，**不**登记为环境项、
**不**豁免 fake-IP 段。

### 二、R-1：修「按新近」不是全序（真实来源），判据先红后绿

- **修前（判据先红）**：`pytest tests/contracts/test_protocol_draft_store_order_tie.py -q`
  ⇒ `3 failed in 0.34s`；断言逐字
  `assert ['pdraft_00000001', 'pdraft_00000002'] == ['pdraft_00000002', 'pdraft_00000001']`。
- **改动（`git diff` 逐条，仅三处）**：`adapters/sqlite/protocol_draft_store.py` 与
  `adapters/postgres/protocol_draft_store.py` 的 `ORDER BY d.created_at DESC, d.draft_id`
  ⇒ `…, d.draft_id DESC`；`packages/application/protocol_authoring/memory_store.py` 的
  `sorted(key=lambda item: item[1].created_at, reverse=True)`
  ⇒ `key=lambda item: (item[1].created_at, item[0])`。**三实现同语义**、tie 与新近一致。
- **修后（判据后绿）**：`12 passed in 0.52s`（3 条新判据 + 既有契约 9 条，**断言未动**）。
- **为何不是「调用例迁就」**：契约用例的断言一字未改；改的是「按新近」这个语义在
  `created_at` 同刻时的**全序性**——修后旧断言**必然**成立，而不是靠时钟运气。

### 三、R-2：默认门凭据隔离（夹具隔离），判据未动

- **修前（判据先红）**：`LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q`
  ⇒ `egress guard: FAIL … blocked 2`、`198.18.0.83:443 (kind=private) by
  tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`。
- **根因链（逐跳可点）**：`litellm/__init__.py:27` 导入期 `load_dotenv()` ⇒ gitignored `.env`
  的 `LLM_MAIN_KEY` 进进程环境 ⇒ `services/api/preflight_support.py:92`
  `deps.credentials.resolve(endpoint.credential_ref)` 成功 ⇒ `probe_connectivity` 真的发起
  HTTP（出厂端点 `https://apihub.agnes-ai.com/v1`）⇒ 出站判据在**任何数据包之前**拦下并
  判红整轮。
- **改动（仅两处新增 + 一处导入）**：新增 `tests/default_gate_credentials.py`（名单 +
  出厂目录 `credential_ref` 解析）、新增 autouse 夹具于 `tests/conftest.py`（未标记
  `requires_live_llm` 的用例逐个 `monkeypatch.delenv`，用例结束自动还原）、新增判据
  `tests/architecture/python/test_default_gate_credential_isolation.py`（三条：名单 ↔
  出厂目录**双向对齐**、导入期泄漏下的**非空真**隔离断言、**子进程按压**）。
- **修后**：`LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q` ⇒ `blocked 0`、
  `16 passed`；判据自身 `3 passed in 3.91s`。
- **判据未动**：`tests/egress_guard.py` 逐字节未改（见第六节 `git diff` 清单）；放行面仍
  同源（隔离夹具与出站判据共用同一个 `ALLOW_MARKER`）⇒ live 用例照旧可读真实凭据。

### 四、R-4：只普查不实施（本 cycle 的显式边界）

同一份 `tests/api/test_worker_plane_composition.py`，PG 不可达时两种收集形态结论不同：
**A** 定向跑（不收集 `tests/postgres`）⇒ 120s 内无输出、`timeout` 杀掉、`exit 143`（**挂死**）；
**B** 同文件 + 收集 `tests/postgres` ⇒ `16 passed, 93 skipped in 4.22s`（3 条 `postgres` 标记
被跳过）。根因 = 跳过钩子只写在 `tests/postgres/conftest.py` / `tests/distributed/conftest.py`，
**只在被收集到时才加载**。分类 (i)，**实施放 cycle 2（EC-02 的本地跑法协议）**——本 cycle
不把它算作 EC-01 的顺序依赖。

### 五、AC-4：同一套件组合**连续两轮全绿**

组合命令（两轮逐字相同；DSN 固化 = `RESEARCHOS_POSTGRES_DSN` pin 到 postgres-test DSN、
`DATABASE_URL` / `POSTGRES_DSN` 清空）：

```
uv run --frozen --no-sync python -B -m pytest --ignore=tests/architecture/python/test_dependency_boundaries.py -q
```

| 轮 | 输出末行（逐字） | 出站判据 | 证据 |
| --- | --- | --- | --- |
| A | `4455 passed, 19 skipped, 88 warnings in 523.96s (0:08:43)` | `egress guard: FAIL` 计数 **0**；阻断只来自判据自身探针 `198.51.100.1` | `scratch/goal015-c1-roundA.log` |
| B | `4455 passed, 19 skipped, 88 warnings in 521.72s (0:08:41)` | `egress guard: FAIL` 计数 **0** | `scratch/goal015-c1-roundB.log` |

对照 as-is 基线（修前同一配方）：`1 failed, 4445 passed, 19 skipped … in 569.15s` +
`egress guard: FAIL … blocked 10`（2 条产品端点 + 8 条自身探针）⇒ **两条红项归零**。
**一次如实登记的返工**：第一次 ROUND-1 跑判红一条，根因是**本 cycle 新增文档**里
`tests/postgres/conftest` 这个 backtick 引用不存在（`tests/tooling/test_docs_consistency_check.py::test_real_repo_is_clean`）
⇒ 修正为 `tests/postgres/conftest.py` 后重跑，**A/B 两轮取自修正后的树**。

### 六、AC-5：成对反证（先红后绿 + 逐字节还原）

把三处产品改动与 `tests/conftest.py` 用 `git stash push -- <显式路径>` 撤回到修前状态
（**新增判据文件不在暂存范围**，所以按压跑的是「旧代码 + 新判据」）：

| 按压 | 命令 | 修前（撤后）观测 | 修后（还原）观测 |
| --- | --- | --- | --- |
| P-1 | `pytest tests/contracts/test_protocol_draft_store_order_tie.py -q` | **3 failed in 0.34s**（exit 1） | `12 passed`（含既有契约 9 条） |
| P-2 | `LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q` | `egress guard: FAIL … blocked 2`（exit 1） | `blocked 0` / `16 passed`（exit 0） |

按压记录：`scratch/goal015-c1-press-r1-after-revert.txt`、`scratch/goal015-c1-press-r2-after-revert.txt`。
**还原逐字节复核**：`sha256sum -c scratch/goal015-c1-press-files-before.sha256` ⇒
四行全 `OK`（`f7b4eb0c…` / `ac6ac960…` / `c3ee0307…` / `148ac42c…`）；按压后工作树与按压前同态。

### 七、AC-6：判据只增不减 + 用例数归因（逐用例 ID）

- **`git diff` 清单（改动只落在下列文件）**：三个适配器/实现各 1 行语义修正；
  `tests/conftest.py` 增一个 autouse 夹具 + 一行 import；新增 3 个文件
  （`tests/default_gate_credentials.py`、两条判据文件）；新增普查文档 1 份。
- **逐用例 ID 差集**：`4446（4445 passed + 1 failed）→ 4455` = **+9、零删除**：
  +6 = 新判据 6 条（`--collect-only` 逐 ID 列出：order-tie 3 + credential-isolation 3）；
  +3 = `tests/tooling/test_python_source_limits.py` 对**新增 3 个 `.py`** 的参数化。
- **零放宽自查**：`tests/egress_guard.py`、`.cursor/skills/cursor-framework-check/**`
  （`framework/validate_bundle` 所在）、`tests/application/test_m2_audit.py`、
  450/50 行阈值、OpenAPI / 设计基线快照 —— **均不在本 cycle 改动清单内**（`git diff` 为空）。

### 八、本地门与 CI

- **m0 终态（as-is，可支持的终态行）**：`run_all_checks.py --profile m0 --keep-going`（DSN 固化、
  独占运行）⇒ `FAILED: 1 check(s): framework/validate_bundle=1`；`PASS [` 行 **23** 条
  （22 项 m0 check + `release-assets-immutable`）、`FAILED [` **1** 条、`python/tests`
  = `4455 passed, 19 skipped`（**第三轮连续全绿**）、`egress guard: FAIL` 计数 **0**
  （证据 `scratch/goal015-c1-m0-final.log`）。
  **口径**：as-is 本地 m0 = **22/23**，唯一未绿 = `R-3`（`framework/validate_bundle`，
  仓库外 gitignored 文件）；**不**把「代管后可达 23/23」写成「本机 23/23」。
  **一次如实登记的返工**：本 cycle 首次 m0 判红 `framework/validate`（本 cycle 新增的
  MEM 条目缺必需章节且未入 `INDEX`）⇒ 补齐后重跑取上面的终态行。
- **定向套件**：`pytest tests/contracts tests/application/protocol_authoring
  tests/architecture/python/test_default_gate_credential_isolation.py tests/api -q`
  ⇒ `993 passed, 2 skipped`、`blocked 0`。
- **规模门禁**：新增文件 `114` / `47` / `68` 行（均 < 450；函数均 < 50 行），
  由 m0 的 `python/tests` 内 `test_python_source_limits` 参数化覆盖。
- **治理**：`python .cursor/skills/governance-check/scripts/validate.py` ⇒
  `Cursor 治理验证通过`；`tools/docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`。
- **CI 台账**：见 GOAL-015 的 CI 台账表（本 cycle 的推送 run 与六 job + CodeQL 结论）。

## 结论

**`PASS_WITH_WARNINGS`**。EC-01 的六个验收条件①–⑥逐条达成：普查先于修且每条红有可复现
最小命令；两处修法都落在**真实共享来源**（排序语义 / 凭据隔离），**没有**改动任何判据、
阈值、快照或既有断言；同一套件组合**连续两轮全绿**（`4455 passed` ×2）；成对反证在
**修前状态重新构造**下**按同签名判红**并以逐字节复核还原；用例数 +9 零删除。

**警告两条（如实保留，不隐藏）**：

- **W-1｜`R-3` 未消**：`framework/validate_bundle` 仍被**仓库外**的 gitignored 文件
  （`scratch/self-governance-bootstrap-prompt.md`，`69944` B / `sha256:7af32093…`）判红 ⇒
  as-is 本地 m0 = **22/23**（不是 23/23）。按 GOAL-015 授权，**不在本循环改门禁**：分类为
  **(iii) 门禁 scoping**，只登记，进 EC-03（cycle 3）的决策简报。
- **W-2｜`R-4` 只普查未实施**：定向跑在 PG 不可达时**挂死**（既非跳过也非快失败）。
  已给根因与修法，实施排在 cycle 2（EC-02 的本地跑法协议）——它是「本地判定确定性」的
  直接输入，不是 EC-01 的顺序依赖。
