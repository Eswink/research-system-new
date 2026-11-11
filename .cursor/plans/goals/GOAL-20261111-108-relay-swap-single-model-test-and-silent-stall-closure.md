---
id: GOAL-20261111-108
slug: relay-swap-single-model-test-and-silent-stall-closure
title: 换接入商 + 四个免费模型真分工 + 静默停住四处收口
status: ACTIVE
created_at: 2026-11-11
updated_at: 2026-11-11
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-11 给出新接入点 `http://192.168.101.9:8798/v1` 与模型 `hy4free`，明确
    「只测免费的，其他收费」；随后在探针确认新站有 4 个 `x0.00` 且支持 tool_calls 的模型后
    拍板「四个免费模型分工」。当四个免费模型在数学上无法满足全部独立性约束时（穷举 4^7
    无解），用户拍板「**保作者独立**」—— 即放宽「创新点评审与另外两位评审互异」，保留
    「创新点作者独立于写作组与两位评审者」。
    沿用用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E / RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS
    逐命令传，绝不写进 .env。
objective: >-
  把控制面切到局域网免费中转站并**真的跑起来**：① 事实探针（模型清单 / tool_calls / 是否
  回 `model` 字段）；② 四个 `x0.00` 模型在**写作组 / 评审 A / 评审 B / 创新点作者**上真分工
  （`(endpoint, model_name)` 三组互斥，`HETEROGENEITY_VIOLATION` 不触发）；③ 四处既有
  **静默停住**可达路径收口（装配面异常边界 / `review_outcome` 的 resume 阻塞 / 会话合约
  重试声明 / live harness 与产品同一放行开关）；④ 真跑一次十一相链并如实记录终态。
exit_criteria:
  - id: EC-01
    criterion: >-
      **事实探针入台账**：新站 `GET /v1/models` 的完整读数（模型数 / 各模型 `credits` /
      `context_length` / `max_output_tokens` / `capabilities.tool_calls`），且对四个
      `x0.00` 模型逐个实测 `POST /chat/completions`（是否回 `model` 字段、是否真出
      `finish_reason: tool_calls` 且参数正确）。
    verify: >-
      本 GOAL 的 `## 探针读数` 一节逐项在场；判据
      `tests/tooling/test_goal108_probe_readings.py` 断言四个免费模型名逐字出现且
      `tool_calls` 的实测结论非空。
    status: PASS
  - id: EC-02
    criterion: >-
      **换站完成且凭据只在 `.env`**：`examples/config/llm_endpoints.yaml` 的 `main.base_url`
      指向局域网地址、`request_timeout_seconds` 提到实测分布之上（120→300，依据台账 F-14 的
      99.8/76.1/78.4s 与一条 120.1s 超时）、`allow_models` 只列四个免费模型；
      `LLM_MAIN_KEY` 只写在 gitignore 的 `.env`。
    verify: >-
      `tools/credential_audit.py` 四面 `offenders=0`；
      `tests/loaders/test_contract_loaders.py` 全绿（判据已改为**结构性**断言：
      不断言具体秒数与具体模型名，见 `## 影响报告`）。
    status: PASS
  - id: EC-03
    criterion: >-
      **四个免费模型真分工**：写作组（`writer`/`director`/`domain_a`/`editor`）= `hy4free`；
      评审 A（`reviewer_a` 经 `critic_independent`）= `hy4-preview-f`；评审 B
      （`reviewer_b`）= `hy4flash-exp4`；创新点作者（`novelty_writer`）= `hy3`；
      创新点评审（`novelty_a`）= `hy4-preview-f`。**写作组与评审组交集为空**
      ⇒ `HETEROGENEITY_VIOLATION` 不触发。用户拍板放宽的那一面（创新点评审与评审 A
      同目标）必须**可枚举**。
    verify: >-
      `tests/application/test_review_independence_judgment.py`、
      `tests/application/preflight/test_review_independence_gate.py`、
      `tests/contracts/test_direction_to_report_v2_independence.py`、
      `tests/contracts/test_direction_to_report_v2_novelty.py`、
      `tests/loaders/test_contract_loaders.py` ⇒ **93 passed**；
      `test_the_shared_review_target_is_recorded` 把共用目标变成可读事实。
    status: PASS
  - id: EC-04
    criterion: >-
      **R-1 装配面异常边界**：`phase_runner._run_group_task` 的五个 spec helper 曾经全在
      任务级 `try` 之外、而 `phase_runner.py` / `service.py` 全无 `try/except`
      ⇒ 任一 helper 抛错会穿透整条栈（GOAL-106 `F-17` 的静默停住）。新建
      `spec_assembly_guard.py`（`guarded_assembly` / `assemble_spec` / `fail_on_assembly_error`），
      抛错走**既有的唯一分叉** `deps.fail(...)`；无异常时产物与原来同一个对象。
    verify: >-
      `tests/application/test_spec_assembly_guard.py` ⇒ 四臂：① 成功路径 `is` 相同；
      ② 抛错返回 `(None, SpecAssemblyError)` 且判词点名步骤；③ `assemble_spec` **链式**
      （第二步看到第一步的产物）；④ `fail_on_assembly_error` 走 `deps.fail`
      （`system_failure=True`）。
    status: PASS
  - id: EC-05
    criterion: >-
      **R-2 `review_outcome` 的 resume 阻塞**：`run` 不属于任何程序时原实现抛
      `ValueError`，而该 helper 在**每个**任务前被调用 ⇒ 任何非程序 run 走 resume 必然在
      第一个任务上抛错，叠加旧的无异常边界 = 静默停住。改为返回**点名的**空视图
      `NO_PROGRAM`，与「有前序但读不到判词」（`NO_FINDINGS`，fail-closed）严格区分。
    verify: >-
      `tests/application/test_review_outcome_no_program.py` ⇒ 三臂：① 非程序 run 返回
      空视图且 `reason` 含 `NO_PROGRAM`；② **不抛**（resume 不再停住）；③ 有程序但无前序
      ⇒ 仍走 `NO_PRIOR_RUN`（两种「空」分得开）。
    status: PASS
  - id: EC-06
    criterion: >-
      **R-3 会话合约重试声明**：五份会话合约（`research_manuscript` /
      `retrieval_report_from_the_run_chain` / `multi_role_review` / `author_response` /
      `submission_package`）此前 `max_attempts: 1` + 空类别 ⇒ 一次
      `MODEL_RELAY_UNAVAILABLE` 即 `retry budget exhausted`（终态）。改为
      `max_attempts: 2` + `backoff_seconds: 30` + **显式列出**三个瞬时类别
      （`MODEL_RELAY_UNAVAILABLE` / `MODEL_RATE_LIMIT` / `MODEL_TIMEOUT`）。
      **不统一**全仓 `retryable_categories: []` 的两处矛盾语义（登记 `W-1`）。
    verify: >-
      `tests/application/test_session_contract_retries.py` ⇒ 五份合约逐一断言三个字段；
      反证：把 `max_attempts` 改回 1 ⇒ 判红。文件行尾保持 **LF**（曾误写成 CRLF 并因此
      打断一条 LF 锚点判据，已复原并登记）。
    status: PASS
  - id: EC-07
    criterion: >-
      **R-4 live harness 与产品同一放行开关**：`tests/e2e/manuscript_chain_live_support.py`
      曾写死 `allow_localhost_endpoints=False` ⇒ 换到局域网后「产品能跑、判据不能跑」，
      那条判据永远证明不了产品面可用。改为读 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS`
      （与 `ApiSettings.from_env` 同一个变量）。
    verify: >-
      `tests/tooling/test_goal108_live_harness_reads_the_switch.py` ⇒ 源码判据：该文件
      含 `_allow_local_endpoints()` 且**不含** `allow_localhost_endpoints=False` 字面量。
    status: PASS
  - id: EC-08
    criterion: >-
      **真跑一次十一相链**（`direction_to_manuscript_v1`），记录终态与失败形态。
      **成功或失败都算达成**：本轮判的是「能跑起来」，不是「一定成功」——失败率主因是
      上游延迟，300s 超时是缓解不是保证。
    verify: >-
      本 GOAL 的 `## 真跑读数` 一节记录 run id / 终态 / 相级时间线 / 若失败的形态归类。
    status: PENDING
  - id: EC-09
    criterion: >-
      **文档同步**：`docs/integration/LLM_ENDPOINTS.md` 与
      `docs/integration/LIVE_MODEL_RUNBOOK.md` 写明新站、四个免费模型、局域网放行开关
      与租赁 TTL 的注意点。
    verify: >-
      两文件 grep 命中新站地址与开关名；`tests/tooling/` 相关文档判据绿。
    status: PENDING
  - id: EC-10
    criterion: >-
      **宪章记账**：程序表序 76（已登记，与序 77…80 一并）；阶梯按实际推进写；
      进展 / 修订各追加一行（5 格、表内连续）。序 74 的两行已归档（`archive/`）。
    verify: >-
      `tests/tooling/test_mainline_program_is_intact.py`、
      `test_mainline_research_ladder_advances.py`、
      `test_mainline_archive_is_continuous.py`、
      `test_record_tables_are_structurally_sound.py` 全绿。
    status: PENDING
  - id: EC-11
    criterion: >-
      **收口资产**：`tools/verify_goal108_closeout.py` + `tools/goal108_closeout_assertions.py`，
      登记进 `_VERIFIERS` 与 `IN_SCOPE`。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal108_closeout.py --root . --verdict-only`
      全 PASS 且判词不含绝对路径。
    status: PENDING
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 把钉住「运维数据」（具体模型名 / 具体秒数）的判据改为**结构性**断言
    - 新增判据文件与两向按压
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把真实 key 写进任何被跟踪文件（只进 gitignored `.env`）
    - 为让判据变绿而把新站地址改成公网/主机名绕开地址策略
    - "统一全仓 `retryable_categories: []` 的矛盾语义（会影响 29 份合约，登记为待拍板）"
    - 改 `.github/workflows/**`（本轮关闭）
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（本轮只**在判据侧**显式放行局域网，产品默认不变）
  - 新站不可达或凭据无效 ⇒ 停 BLOCKED 点名，不回退旧站
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261111-108-relay-swap-and-reliability.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261111-108-relay-swap-and-reliability.md
memory_entries: []
---

# GOAL-20261111-108 —— 换接入商 + 四个免费模型真分工 + 静默停住四处收口

## 目标与退出标准

承用户 2026-11-11 指令：换接入商、只用免费模型、把可靠性问题解决掉。

## 探针读数（EC-01，2026-11-11 实查）

**新站 `GET /v1/models`**：**23 个模型**。其中 `credits: x0.00`（免费）的 **5 个**：

| 模型 | credits | context_length | max_output_tokens | tool_calls |
|---|---|---|---|---|
| `hy4free` | **x0.00** | 960000 | 64000 | ✅ |
| `hy4-preview-f` | **x0.00** | 1000000 | 64000 | ✅ |
| `hy4flash-exp4` | **x0.00** | 960000 | 64000 | ✅ |
| `hy3` | **x0.00** | 192000 | 64000 | ✅ |
| `hy4std` | x0.29 | 960000 | 64000 | ✅（**收费，不用**） |

**逐个实测 `POST /chat/completions`**（四个免费模型）：

| 模型 | 返回 `model` 字段 | `finish_reason` | tool_calls 参数 | 备注 |
|---|---|---|---|---|
| `hy4free` | `"hy4free"` ✅ | `tool_calls` | `{"city": "Paris"}` ✅ | 64-token 上限时 `content` 为空、`reasoning_tokens: 64` |
| `hy4-preview-f` | `"hy4-preview-f"` ✅ | `tool_calls` | ✅ | — |
| `hy4flash-exp4` | `"hy4flash-exp4"` ✅ | `tool_calls` | ✅ | — |
| `hy3` | `"hy3"` ✅ | `tool_calls` | ✅ | 最省：20 completion tokens / 0 reasoning |

**三条结论**：① 四个都能用、都支持 tool_calls；② **都返回 `model` 字段** ⇒ run 指纹可落
`REPEATABLE_CONFIGURATION`（不是 `NOT_VERIFIED`）；③ **四个都是 reasoning 模型**
（`reasoning_tokens` 会吃掉输出预算）⇒ 输出上限不能设小。

## 真跑读数（EC-08）

（收口时填写：run id / 终态 / 相级时间线 / 失败形态归类。）

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 十一条 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住 ⇒ 移入「残余与未覆盖范围」，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动（并发驱动）⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive → ② 执行 → ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错 → ⑦ 回写记录 + 下一轮。

**记录顺序**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py` → 之后不再改树 → 提交推送。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位；**修产品优先，禁改断言迁就** |
| live 判据在 CI 上 skip | `requires_live_llm` 无凭据 | **预期**：live 只在操作者本地跑；skip 不是 PASS |
| 局域网地址被拒 | `ENDPOINT_URL_DENIED` | 默认 deny 是**正确**的；只在判据侧显式放行（`allow_private=True`），不改产品默认 |
| 行尾漂移 | 一条 LF 锚点判据突然红 | **检查是不是自己把文件写成 CRLF**（本轮踩过：`task_contracts.yaml` 被写成 CRLF，导致一条 LF 锚点判据红；已复原并登记） |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |
| 上游不可用 | 新站不可达 / 401 | **停 BLOCKED 点名，不回退旧站**（用户明确要换站） |

## 终止与收口

- **ACHIEVED**：十一条 EC 全 PASS + RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过上限，或 `max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261111-108 | （待填） | 探针 4/4 免费模型可用；独立性 93 passed；规模门 1422 passed；合约 62 passed | （待填） | 三处真缺陷（novelty_writer 撞 domain_a / research_strong fallback 落评审 A / task_contracts 被写成 CRLF） | EC-08…11 待收口 | 真跑 + 文档 + 收口资产 |

## 影响报告

（收口时填写。）

**本轮已确定的判据口径变化（须逐条登记理由）**：判据里写死「具体模型名 / 具体秒数」
的地方改为**结构性**断言 —— 那些值属**运维数据**（换接入商就变），把它们写成判据会让
「换站」变成「改判据」，反而掩盖判据真正守的东西（`(endpoint, model_name)` 互异、
参数被读进来、fallback 不落到评审面）。

## 残余与未覆盖范围

（收口时填写。）

### 残余（本轮已交付里仍然存在的缺口）

- （待填）

### 未覆盖范围（本轮**没有**触及的面）

- （待填）

### 声称边界（**不得宣称**的事）

- （待填）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-11 | ACTIVE | 建档：序 76；十一条 EC；探针与换站已完成 |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
