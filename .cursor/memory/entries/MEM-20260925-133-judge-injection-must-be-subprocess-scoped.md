---
id: MEM-20260925-133
title: "判据的注入必须限定在子进程：模块导入期改环境就是给整个会话制造假故障"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-164-local-gate-protocol-and-decision-briefing.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-165-local-gate-protocol-and-decision-briefing.md
supersedes: []
tags: [test-isolation, judges, ci-red, env-pollution, live-gate, subprocess]
---

## 做了什么

「默认门不得看见 live 凭据」的**判据本体**（`test_default_gate_credential_isolation.py`
初版）在**模块导入期**把凭据键写进 `os.environ`，用来「制造泄漏」再断言夹具把它抹掉。
它本身通过了本地跑，但**把凭据键泄漏给了整个 pytest 会话**：

`tests/e2e/test_run_chain_retrieval_live.py` 的 skip 条件是「环境里有没有凭据」
（`_live_credentials()` 只判键在不在）⇒ 该 live 用例**不再 skip**，在 CI 上带着这个探针值
**真的去调出厂端点** ⇒ `AuthenticationError: OpenAIException - Invalid token` ⇒ 默认门判红
（CI run `36048265860`，`quality-ubuntu-latest`；同一提交在本机凭据可解析时反而**通过**）。

修法：

- 注入全部移进**子进程**：判据用 `subprocess.run([sys.executable, "-m", "pytest", 探针, 按压文件])`，
  只把凭据键放进**子进程的 `env`**；父进程一行都不改。
- 新增探针 `tests/architecture/python/test_default_gate_isolation_probe.py`（会被常规收集，
  `--noconftest` 下即判红）；文件名必须 `test_*.py`——首版叫
  `default_gate_isolation_probe.py`，被 `tests/architecture/test_module_file_naming.py` 判红。

## 为什么这样做

- **判据的副作用面 = 它自己的断言面**：一条判据只要在导入期改环境，它的「被测对象」就不再是
  夹具，而是**整轮会话**——于是它能把别的、无关的用例变成真出网、真失败。
- **local green / CI red 的不对称**：本机凭据可解析 ⇒ live 用例本来就跳过不了（但那是我自己的
  环境）；CI 无凭据 ⇒ 探针值成了唯一凭据 ⇒ 只有 CI 暴露。**判据必须在两种环境里同义。**
- **不删 live 用例、不改 skip 条件**：那是「改判据使其通过」。被修的是**我自己的装置**。
- **探针要带 `test_` 前缀**：`tests/` 下的模块命名由门禁强制；不给豁免（豁免即改门禁）。

## 怎么做与复现

- 按压（必须红）：`LLM_MAIN_KEY=<任意值> pytest --noconftest
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ `1 failed`（点名
  `LLM_MAIN_KEY` 仍可见）。
- 正常（必须绿）：带根 conftest ⇒ `1 passed`，且 `blocked 0`；
  `LLM_MAIN_KEY=<任意值> pytest tests/architecture/python/test_default_gate_credential_isolation.py
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ `3 passed`。
- 命名门：`pytest tests/architecture/test_module_file_naming.py -q` ⇒ 绿（三者合计 `33 passed`）。
- 排查同类问题时：**判据里出现的 `os.environ[...] = ...` / `setdefault` 一律视为会话级副作用**，
  必须搬进子进程或改成显式参数。

## 适用边界

- 该判据现在有**两个**执行面：常规收集（夹具在 ⇒ 绿）与 `--noconftest` 按压（夹具不在 ⇒ 红）；
  两者必须同时成立才算非空判据。
- 子进程判据的成本是**第二次解释器启动**（约 4s），换来的是「父会话零污染」——本地与 CI 同义。
- 「环境里恰好有凭据就真出网」这一**设计性质**本身仍是待拍板项（决策简报 `D-11`）：
  本条目只保证**判据不再制造**这种状态，不改变 live 用例的开门条件。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-164-local-gate-protocol-and-decision-briefing.md`（WP5）
- `.cursor/plans/rechecks/RECHECK-20260925-165-local-gate-protocol-and-decision-briefing.md`
- `.cursor/plans/goals/GOAL-20260925-015-gate-trustworthiness.md`（CI 台账 cycle 1 行：
  红 run `36048265860` 的判词与归因）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-11（证据出处同源）
