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

## 做了什么

在 GOAL-009 cycle 1 里跑成了本仓**第一次**真实 live run（`PLAN-20260920-121`），
并把三件在动手前**不清楚**的事固定成事实：

1. **凭据「可解析」取决于导入栈，不取决于 `.env` 是否存在。** 本仓**没有任何**
   `load_dotenv` 调用点（`grep -rn "load_dotenv" --include=*.py` 零命中）；`.env` 是被**依赖**
   在导入期加载的——`openhands-sdk → litellm` 在 import 时自动跑 `load_dotenv()`，向上找到仓库
   根的 operator `.env`。实测（2026-09-20）：

   ```text
   uv run … python -c "from adapters.relay.credential_resolver import EnvCredentialResolver;
                       print(EnvCredentialResolver().has('LLM_MAIN_KEY'))"
   # ⇒ False   （只 import 了 resolver，没有触发 litellm）

   uv run … python -c "import litellm
                       from adapters.relay.credential_resolver import EnvCredentialResolver;
                       print(EnvCredentialResolver().has('LLM_MAIN_KEY'))"
   # ⇒ True
   ```

2. **内联前缀开门、去掉前缀即回到如实 skip**（可逆、零残留）。`evaluate_live_run_gate` 的两条
   条件缺一不开：runtime **显式**配成 live runtime + 端点凭据**可解析**（只问 `has`，不物化值）。
   三条判据都能**无网络**读出来：默认门跑 `tests/e2e/test_ec04_live_first_run.py` ⇒
   **1 passed / 1 skipped**；内联前缀 + `-k closed` ⇒ 关门用例 **SKIPPED**（跳过理由即
   「gate is open on this machine」）；去前缀复跑 ⇒ 回到 **1 passed / 1 skipped**。

3. **真实 runtime 跑 console demo 协议，终态就是 `FAILED`（设计内）。**
   `console_demo_research_v1.yaml` 的 task contract 要的是 `analysis_report`，真实 OpenHands
   会话产出的是 `session_message` ⇒ acceptance gate 按合约**判拒**，run 落到 `FAILED`；
   `reached_terminal_state` 的语义是「state ∈ `ResearchRunState.terminal()`」——**包含**
   `FAILED`，所以「run 到终态」的判据**可以**在终态为 `FAILED` 时通过。

## 为什么这样做

- **第一件**：同一个「凭据在不在」的判断，会因为没有触发导入链而给出**相反**的答案；
  据此下的结论（「没有凭据 ⇒ live 只能 skip」）会**假**，而它看起来像事实——GOAL-008 收口时
  写下的「六项候选凭据环境变量全部 absent」正是这类读数的产物，而当时 `.env` 里其实有值。
- **第二件**：`load_dotenv()` **只设缺席的键**、不覆盖既有值，因此
  `RESEARCHOS_AGENT_RUNTIME=openhands` 这类**单条命令的内联前缀不会被 `.env` 顶掉**——
  这正是「门只在内联前缀下开、默认姿态保持 Fake」能成立的前提，值得写下来免得日后被
  「`.env` 会不会把开关顶掉」再绊一次。
- **第三件**：`FAILED` 看起来像失败，容易被当成缺陷去「修」；但它其实是登记链在正常工作。
  把它写成记忆，是为了让下一次看到 `FAILED` 的人先去对照判据，而不是先去改产品代码。

## 怎么做与复现

```bash
# 1) 凭据可见性必须在完整导入栈里判（裸导入会给 False）
uv run --frozen --no-sync python -B -c "import litellm; \
  from adapters.relay.credential_resolver import EnvCredentialResolver; \
  print(EnvCredentialResolver().has('LLM_MAIN_KEY'))"

# 2) 默认门（离线，零出站）：应 1 passed / 1 skipped
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec04_live_first_run.py -v

# 3) 只验证「门能开」而不发起任何调用（离线）
RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
  tests/e2e/test_ec04_live_first_run.py -k closed -v      # ⇒ 该用例 SKIPPED（gate is open）

# 4) 真正跑一次 live（只在需要样本时；一次序列 = probe + run）
RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
  tests/e2e/test_ec04_live_first_run.py -v --basetemp=scratch/live-run-ec01
```

`--basetemp` 让用例落盘的 `live-run-record.json` 留在 `scratch/`（否则 `tmp_path` 会被清掉）。

`FAILED` 是不是缺陷，按这三条对照（判据已固化在
`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的 `_assert_deliverable_adjudicated`）：

1. 制品 id 后缀是不是 `:session_message`（合约要的是 `analysis_report` ⇒ 不符 ⇒ 判拒）；
2. 该文件是否仍把「`FAILED` + 点名 acceptance gate」钉为期望、并把
   「出现 `carries no structured output`」当判红信号（那才说明登记链被跳过）；
3. probe 段是否 `verified and ok` 且 usage 是否真实归账（若是，LLM 链路本身是通的）。

## 适用边界

- **适用于**：任何「凭据在不在 / live 门能不能开」的前置自检；记录或解释 live run 的
  `terminal_state`；判断一个 `FAILED` 是设计内判拒还是真缺陷。
- **不适用于**：把 `FAILED` 解释成「端点/协议有问题」（须先走上面三条对照）；
  也**不**支持把「run 到终态」表述成「run 成功 / SUCCEEDED」——**必须**写出实际取值。
- 同族的诚实边界：该次运行的**逐条失败消息**只活在进程内 in-memory 事件库，进程结束即消失
  ——想知道字面消息就得**再跑一次**（与「次数取最小必要」冲突），所以要么当场捕获、要么如实
  登记「未捕获 + 归类依据是收敛证据」。**不要**把归纳说成直读。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md`（GOAL-009 cycle 1 = EC-01）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md`
  （`result: PASS_WITH_WARNINGS`，W-1…W-7；独立脚本 `scratch/verify_goal009_cycle1.py` 22 checks PASS，
  凭据面 `hits=0`）
- 目标：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
- 相关记忆：[[m0-gating-dsn-pinning]]、[[test-env-contamination-and-commit-chain]]
