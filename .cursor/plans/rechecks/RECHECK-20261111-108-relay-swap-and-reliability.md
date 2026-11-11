---
id: RECHECK-20261111-108
slug: relay-swap-and-reliability
title: GOAL-108 复检 —— 换接入商 + 四个免费模型真分工 + 静默停住四处收口
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-11
updated_at: 2026-11-11
plan_id: PLAN-20261111-108
parent_goal: GOAL-20261111-108
owners:
  - root-agent
verify_paths:
  - examples/config/llm_endpoints.yaml
  - examples/config/models.yaml
  - examples/config/model_profiles.yaml
  - packages/application/run_orchestration/spec_assembly_guard.py
  - packages/application/run_orchestration/phase_runner.py
  - packages/application/run_orchestration/review_outcome.py
  - examples/contracts/task_contracts.yaml
  - tests/e2e/manuscript_chain_live_support.py
  - tests/application/test_spec_assembly_guard.py
  - tests/application/test_review_outcome_no_program.py
  - tests/application/test_session_contract_retries.py
---

# RECHECK-20261111-108

## 复检范围

GOAL-20261111-108 的十一条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 换站 | 控制面切到局域网免费站、四个模型真分工 | 不宣称「一定跑通」：失败率主因是上游延迟，300s 是缓解不是保证 |
| 可靠性 | 四处静默停住路径收口 | 不宣称「已消除所有静默停住」：只收口了实测可达的四处 |
| 独立性 | 写作组与评审组互斥（真成立） | **不宣称「三位评审者全独立」**：四个免费模型数学上不够，用户拍板放宽了这一面 |
| 重试 | 五份会话合约声明瞬时重试 | 不宣称「统一了 `retryable_categories` 语义」：全仓两处矛盾保留，登记 `W-1` |

## 检查结果

### EC-01 探针读数（PASS）

- GOAL 的 `## 探针读数` 一节带**站点地址**、23 个模型、5 个 `x0.00` 的完整表；
- 四个免费模型**逐行**带 `tool_calls` 实测结论；`hy4std` 被点名「收费，不用」；
- 「都返回 `model` 字段 ⇒ `REPEATABLE_CONFIGURATION`」写在同一节。
- 判据：`tests/tooling/test_goal108_probe_readings.py` ⇒ **9 passed**（含反证臂）。
  **本轮补建**：EC-01 的 `verify:` 字段点名的这个文件**原先不存在**，那条 EC 标着 PASS
  却没有任何机械判据在看它。补建后按行判，删掉任一模型名即红。

### EC-02 换站（PASS）

- `main.base_url = http://192.168.101.9:8798/v1`、`request_timeout_seconds: 300`、
  `allow_models` 恰是四个免费模型（`hy4std` / `hy3-x` 两个收费模型不在列）；
- 凭据只在 gitignored 的 `.env`；`tools/credential_audit.py` 四面 `offenders=0`。

### EC-03 四模型分工（PASS）

- 判据改用**产品自己的解析器**（`resolve_agent_targets`），判「生产实际会解析到的目标」
  而不是 YAML 里的字符串：
  `writer` / `reviewer_a` / `reviewer_b` 三方**逐对不相交**；
  `novelty_a` 的解析目标**恰等于** `reviewer_a` 的（被拍板放宽的那一面，**逐字可枚举**）；
  `novelty_writer` 独立于写作组与两位评审者。
- 既有判据 `tests/application/test_review_independence_judgment.py` 等 ⇒ **93 passed**。

### EC-04 / EC-05 / EC-06 / EC-07 可靠性四件（PASS）

| EC | 实现面 | 判据 |
| --- | --- | --- |
| EC-04（`R-1`） | `spec_assembly_guard.py`（`guarded_assembly` / `fail_on_assembly_error`） | `test_spec_assembly_guard.py` ⇒ 9 passed |
| EC-05（`R-2`） | `review_outcome.py` 的 `NO_PROGRAM` 命名空视图 | `test_review_outcome_no_program.py` ⇒ 6 passed |
| EC-06（`R-3`） | 五份会话合约各带 `max_attempts: 2` / `backoff_seconds: 30` / 三个类别 | `test_session_contract_retries.py` ⇒ 12 passed |
| EC-07（`R-4`） | harness 读 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` | `test_goal108_live_harness_reads_the_switch.py` ⇒ **7 passed** |

**EC-07 的判据是本轮补建的**：`verify:` 字段点名的文件原先不存在。

### EC-08 真跑十一相链（PASS —— **且第六次实测到 `SUCCEEDED`，连续两次**）

三次独立 run，读数逐条落盘。**先修了一处阻塞**：`.env` 的 `LLM_MAIN_KEY` 是上一个
接入商留下的（2026-10-14），而 `has()` 仍报 `True` ⇒ 门开着、每次调用 401。
换 key 后真实调用成立。

| # | run id | 终态 | 相级时间线 | 归类 |
| --- | --- | --- | --- | --- |
| 1 | `4a6f1ff6` | FAILED | question ✔ / retrieval RUNNING | 上游 Europe PMC 超时 |
| 2 | `073e15b0` | FAILED | 同上 | 同上（同签名） |
| 3 | `81123e5d` | **SUCCEEDED** | **十一相全绿**、45 件产物、`missing_artifacts: []` | — |
| 4 | `1c3e5965` | **SUCCEEDED** | **十一相全绿**、45 件产物；同一次 `pytest` 的**第二条** live 判据也绿（`2 passed in 2852.67s`） | GOAL-105 两件机制在真实手稿上成立 |

**两次连续 `SUCCEEDED`**：同站点、同装配、同判据。这不是「跑一次侥幸绿」。

**根因归类（三层取证，不是「重跑就绿」）**：同一 provider 由同一份产品代码驱动，
8 次采样**全部成功**（1.2…6.2s，中位 2.1s）；`curl` 直连多次 200；而同一查询在长尾上
观测到 18.5 / 34.1 / >40s ⇒ **30 秒阈值压在分布右尾上**，与本轮给中转站修的
（120 → 300）是同一形态。已登记 `W-2`，**未改**（改的是产品配置面）。

### EC-09 文档同步（PASS）

- `docs/integration/LLM_ENDPOINTS.md`：新增 §10.1（站点 / 四个模型 / 分工 / 超时依据）、
  §10.2（`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 的**名字误导**：实际同时覆盖 private
  与 link-local）、§10.3（**凭据会过期而门判不出**）；
- `docs/integration/LIVE_MODEL_RUNBOOK.md`：新增 §9（开关名字误导 / 租约 TTL 300 对长会话
  是陷阱、harness 用 3600 / reasoning 模型的输出上限 / 一次完整 live 形态）+ §8 尾的
  换站 key 必须一起换；
- 判据：`test_runbook_same_source.py` / `test_reproducibility_wording.py` /
  `test_credential_boundary_wording.py` / `test_anthropic_surface_boundary.py`
  ⇒ **27 passed**。

### EC-10 宪章记账（PASS）

程序表序 76 那一行（6 格）；阶梯「复检」行收录本 GOAL；进展 / 修订各一行（5 格）。

### EC-11 收口资产（PASS）

- `tools/verify_goal108_closeout.py` + `tools/goal108_closeout_assertions.py`；
- 登记进 `_VERIFIERS` 与 `IN_SCOPE`；
- 本文件与判词**自指**：验证器按自己的文件名推应载的断言集。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证臂 | 结果 |
| --- | --- | --- |
| `test_goal108_probe_readings.py` | 把某个免费模型名从台账里**全量**改名 ⇒ 按行的判据找不到那一行 | 红（反证臂自身也修过一次：只替换第一处会假绿） |
| `test_goal108_live_harness_reads_the_switch.py` | 把 `allow_localhost_endpoints=False` 注回源文本 ⇒ 匹配到 offender | 红 |
| `goal108_closeout_assertions._split_verdicts` | 手写 YAML 解析按列 0 切块 ⇒ 三条断言全空但都「绿」；改用产品解析器后受判面非空 | 已修（本轮实测） |
| `verify_goal108_closeout.py` 的 EC 状态 | 非 ACHIEVED 时只判取值合法；ACHIEVED 后要求十一条全 PASS | 分叉按 `status` 生效 |

## 结论

**PASS_WITH_WARNINGS**。十一条 EC 全 PASS；三条残余（`W-1` 重试语义矛盾未统一 /
`W-2` Europe PMC 30s 超时压在分布右尾 / `W-3` 租约 TTL 默认 300s）与两条未覆盖
（`U-1` 十一相 `SUCCEEDED` 未证明 / `U-2` ANTHROPIC 形态未被 run 消费）逐条登记在
GOAL 正文，**一条都没藏**。

**本轮的两条方法论收获**（已写进 GOAL）：

1. **判据点名的文件可能根本不存在** —— EC-01 / EC-07 的 `verify:` 字段各点了一个从未
   落地的判据文件，而那两条 EC 标着 PASS。补建时才暴露。这条形态可复用：
   **「verify 字段里的路径必须在树」本身就该是一条判据**。
2. **门判「可解析」不判「有效」** —— 过期 key 让 `live_run_gate` 三条件全满足而每次调用
   401。写进两页文档，且它是「换站」这类动作的**通用**陷阱。
