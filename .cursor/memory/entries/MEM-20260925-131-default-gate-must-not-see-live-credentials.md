---
id: MEM-20260925-131
title: "默认门不得看见 live 凭据：夹具隔离 + 名单与出厂目录双向对齐"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-161-cross-suite-isolation-census-and-fix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-163-cross-suite-isolation-census-and-fix.md
supersedes: []
tags: [test-isolation, credentials, litellm-dotenv, egress-guard, default-gate]
---

## 做了什么

`litellm` 在**导入期**调用 `load_dotenv()`（`litellm/__init__.py`）⇒ 本机 gitignored 的
`.env` 会进**进程环境**。于是「未配置控制面」的 hermetic 用例（只删 DSN 键）在整轮里
拿到可解析的凭据后，会真的走完 `credentials.resolve` → `gateway.probe_connectivity`
（`services/api/preflight_support.py` 的顺序），探出厂端点 `https://apihub.agnes-ai.com/v1`
——默认门的出站结构判据（`tests/egress_guard.py`）随即按设计判红整轮。

修法（**夹具隔离**，不动判据）：

- `tests/default_gate_credentials.py`：名单 `LIVE_CREDENTIAL_KEYS` +
  `catalog_credential_refs()`（按 YAML 解析出厂目录里**有效**的 `credential_ref`，
  注释里的提及不算）。
- `tests/conftest.py`：autouse 夹具——未标记 `requires_live_llm` 的用例逐个
  `monkeypatch.delenv`（用例结束自动还原）。**放行面与出站判据同源**（同一个
  `ALLOW_MARKER`），live 用例照旧能读到真实凭据。
- `tests/architecture/python/test_default_gate_credential_isolation.py`：① 名单 ↔ 出厂目录
  **双向对齐**（新增凭据漏登记即判红）；② **子进程按压**：把凭据键只放进**子进程的 `env`**，
  在同一次子进程里跑探针 `tests/architecture/python/test_default_gate_isolation_probe.py` 与
  `tests/api/test_runs_api.py` ⇒ 探针**看不到**凭据键、默认门必须 `blocked 0`。
  **注入只能发生在子进程内**——初版在**模块导入期**注入，结果泄漏给整个 pytest 会话，
  让 live 用例不再 skip、在 CI 上真去调端点（run `36048265860` 判红）；细节与复现见
  `MEM-20260925-133`。

## 为什么这样做

- **不能改判据**：出站判据是对的（默认门不该出网）。「让红消失」的两条歪路——豁免 fake-IP
  网段、或把该用例 skip 掉——都会削弱门禁，本轮明文禁止。
- **也不该只改单个用例**：这只修补一个洞。「默认门不得看见 live 凭据」是**全类**规则，
  所以放在根夹具里，并配一条**机械对齐判据**防止新凭据静默逃出隔离。
- **CI 天然全绿不代表本地是假红**：CI 无 `.env` ⇒ 凭据不可解析 ⇒ 不探端点。本机因此
  更早暴露了隔离漏洞——这也是「本地红先按类归因、再决定动不动判据」的价值。

## 怎么做与复现

- 复现（修前）：`LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q`
  ⇒ `egress guard: FAIL … blocked 2`（2.24s）。
- 复现（修后）：同一条命令 ⇒ `blocked 0` / `16 passed`。
- 判据：`pytest tests/architecture/python/test_default_gate_credential_isolation.py -q`
  ⇒ 3 passed（含子进程按压）。
- 排查同类问题时：**先看凭据是否可解析**（出厂目录 `credential_ref` → 环境变量名），
  而不是先看 DNS / 网络。目的地类别只决定判词的 `kind`，不决定「有没有这次出站」。

## 适用边界

- 隔离只覆盖**出厂目录声明**的凭据引用；代码里硬编码读别的环境变量名不在名单内，
  需要把它加进 `tests/default_gate_credentials.py`（对齐判据会强制这一步做对）。
- 带 `requires_live_llm` 的 live 用例**不受隔离影响**——这正是「改隔离而不是改判据」的
  分界线：默认门收紧，live 面原样。
- 真实 operator 的 `.env` **不删不改**：夹具只在测试进程里临时移除并按用例还原。
- CI 上该夹具是**空操作**（无凭据键），因此它不会掩盖 CI 的真实行为。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-161-cross-suite-isolation-census-and-fix.md`（WP3）
- `.cursor/plans/rechecks/RECHECK-20260925-163-cross-suite-isolation-census-and-fix.md`
- `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md` 第 2 节（根因链与事实更正）
- 证据：`scratch/goal015-c1-press-r2-after-revert.txt`（修前 `blocked 2`）、
  `scratch/goal015-c1-roundA.log` / `-roundB.log`（修后 `egress guard: FAIL` 计数 0）
- 后续：`MEM-20260925-133`（判据的注入必须限定在子进程，含 CI 红 run `36048265860` 的归因）
