---
id: MEM-20260920-094
title: "live 门的两条条件与凭据可见性来自导入栈（litellm load_dotenv，裸导入看不到）；以及真实 runtime 跑 demo 协议终态是设计内 FAILED，不是缺陷"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md
supersedes: []
tags:
  - live-run
  - credential
  - dotenv
  - import-stack
  - acceptance-gate
  - terminal-state
  - goal-009
---

# live 门的凭据可见性 + 真实 runtime 的设计内 FAILED（GOAL-009 cycle 1）

## 事实一：凭据「可解析」取决于**导入栈**，不取决于 `.env` 是否存在

`EnvCredentialResolver` 读的是 `os.environ`。本仓**没有任何** `load_dotenv` 调用点
（`grep -rn "load_dotenv" --include=*.py` 零命中）——`.env` 是被**依赖**在导入期加载的：
`openhands-sdk → litellm` 在 import 时自动跑 `load_dotenv()`，向上找到仓库根的 operator `.env`。

后果（实测，2026-09-20）：

```text
uv run … python -c "from adapters.relay.credential_resolver import EnvCredentialResolver;
                    print(EnvCredentialResolver().has('LLM_MAIN_KEY'))"
# ⇒ False   （只 import 了 resolver，没有触发 litellm）

uv run … python -c "import litellm
                    from adapters.relay.credential_resolver import EnvCredentialResolver;
                    print(EnvCredentialResolver().has('LLM_MAIN_KEY'))"
# ⇒ True
```

**Why:** 同一个「凭据在不在」的判断，会因为没有触发导入链而给出相反的答案；据此下的结论
（「没有凭据 ⇒ live 只能 skip」）会**假**，而它看起来像事实。

**How to apply:** 任何 live 门/凭据的前置自检，都必须跑在**完整导入栈**里（pytest 路径，
或显式 `import litellm` / `import tests.e2e.live_run_support`）。
`load_dotenv()` **只设缺席的键**、不覆盖既有值，因此 `RESEARCHOS_AGENT_RUNTIME=openhands`
这类**单条命令的内联前缀不会被 `.env` 顶掉**——这正是「门只在内联前缀下开」能成立的前提。

## 事实二：内联前缀开门，去掉前缀即回到如实 skip（可逆、零残留）

`evaluate_live_run_gate` 的两条条件缺一不开：runtime **显式**配成 live runtime + 端点凭据
**可解析**（只问 `has`，不物化值）。判据可**无网络**地读出来：

- 默认门：`pytest tests/e2e/test_ec04_live_first_run.py` ⇒ **1 passed / 1 skipped**；
- 内联前缀 + `-k closed` ⇒ 关门用例 **SKIPPED**（跳过理由即「gate is open on this machine」）
  ⇒ 两条条件在 pytest 进程内同时成立，**且没发起任何调用**；
- 去掉前缀复跑 ⇒ 回到 **1 passed / 1 skipped**（无残留）。

## 事实三：真实 runtime 跑 console demo 协议，终态**就是** `FAILED`（设计内）

`console_demo_research_v1.yaml` 的 task contract 要的是 `analysis_report`，而真实 OpenHands
会话产出的是 `session_message` ⇒ acceptance gate 按合约**判拒**，run 落到 `FAILED`。

**这不是缺陷**：`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的
`_assert_deliverable_adjudicated` 把「`FAILED` + 点名 acceptance gate」固定为该路径的**期望**，
并把「出现 `carries no structured output`」当判红条件（那才说明登记链被跳过）。

**Why:** `reached_terminal_state` 的语义是「state ∈ `ResearchRunState.terminal()`」——
**包含** `FAILED`。于是「run 到终态」的判据**可以**在终态为 `FAILED` 时通过。

**How to apply:** 记录 live 样本时，**必须**把 `terminal_state` 的**实际取值**写出来
（`FAILED` 就写 `FAILED`），**不得**把「判据通过」表述成「run 成功 / SUCCEEDED」；
归类失败时先对照 `:session_message` 制品后缀与离线同路径期望，再决定它是不是缺陷。
同族的诚实边界：该次运行的**逐条失败消息**只活在进程内 in-memory 事件库，进程结束即消失
——想知道字面消息就得**再跑一次**（与「次数取最小必要」冲突），所以要么当场捕获、要么如实
登记「未捕获 + 归类依据是收敛证据」。相关：[[m0-gating-dsn-pinning]]、
[[test-env-contamination-and-commit-chain]]。
