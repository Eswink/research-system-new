---
id: GOAL-20261111-108
slug: relay-swap-single-model-test-and-silent-stall-closure
title: 换接入商 + 四个免费模型真分工 + 静默停住四处收口
status: ACHIEVED
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
    status: PASS
  - id: EC-09
    criterion: >-
      **文档同步**：`docs/integration/LLM_ENDPOINTS.md` 与
      `docs/integration/LIVE_MODEL_RUNBOOK.md` 写明新站、四个免费模型、局域网放行开关
      与租赁 TTL 的注意点。
    verify: >-
      两文件 grep 命中新站地址与开关名；`tests/tooling/` 相关文档判据绿。
    status: PASS
  - id: EC-10
    criterion: >-
      **宪章记账**：程序表序 76（已登记，与序 77…80 一并）；阶梯按实际推进写；
      进展 / 修订各追加一行（5 格、表内连续）。序 74 的两行已归档（`archive/`）。
    verify: >-
      `tests/tooling/test_mainline_program_is_intact.py`、
      `test_mainline_research_ladder_advances.py`、
      `test_mainline_archive_is_continuous.py`、
      `test_record_tables_are_structurally_sound.py` 全绿。
    status: PASS
  - id: EC-11
    criterion: >-
      **收口资产**：`tools/verify_goal108_closeout.py` + `tools/goal108_closeout_assertions.py`，
      登记进 `_VERIFIERS` 与 `IN_SCOPE`。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal108_closeout.py --root . --verdict-only`
      全 PASS 且判词不含绝对路径。
    status: PASS
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

**站点**：`http://192.168.101.9:8798/v1`（局域网，私有 IP；放行开关见 EC-07 / 文档 §10.2）。

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

**结论先说**：十一相链**真的跑通了，而且是两次** —— 真实中转站、真实模型（`hy4free`
会话真出 `tool_calls`、真写 `research_question`）、真实检索、真实沙箱。
**run 3 与 run 4 的终态都是 `SUCCEEDED`**：**十一相全部 `SUCCEEDED`、各 45 件产物、
`missing_artifacts` 为空**。同一次 `pytest` 里第二条 live 判据也绿
（`2 passed in 2852.67s`）—— GOAL-105 的两件机制在**真实手稿**上成立。

### 先修的一处**阻塞**（不是产品缺陷，是凭据过期）

第一次尝试时**每一次调用都回 401**。根因：`.env` 里的 `LLM_MAIN_KEY` 是 2026-10-14
留下的**上一个接入商的 key**（文件 mtime 可证），而 `EnvCredentialResolver.has()` 对它
仍报 `True` ⇒ `live_run_gate` **开门**（三条件全满足）⇒ 失败发生在真正的 HTTP 层。

**这是一条可复用的判据边界**：门判的是「凭据**可解析**」，不是「凭据**有效**」；
后者只能由一次真实调用证明。换站时 key 必须一起换。已写进
`docs/integration/LLM_ENDPOINTS.md` §10.3 与 `LIVE_MODEL_RUNBOOK.md` §8 尾。

### 三次 run 的读数

| # | run id | 终态 | 相级时间线 | 失败形态 |
|---|---|---|---|---|
| 1 | `4a6f1ff6-96c1-4e36-adc2-c7f61cfae627` | `FAILED` | `question` SUCCEEDED / `retrieval` RUNNING / 其余 PENDING | `europe pmc request timed out` |
| 2 | `073e15b0-6222-4531-afc5-3ffb01c918d9` | `FAILED` | 同上 | 同上 |
| 3 | `81123e5d-42af-4bc2-90ed-2f871a799edc` | **`SUCCEEDED`** | **十一相全部 `SUCCEEDED`**（`question` → `retrieval` → `novelty` → `plan` → `experiment` → `review` → `manuscript` → `editorial` → `revision` → `submission` → `report`） | 无（45 件产物，`missing_artifacts` 为空，`experiment_rows=3`） |
| 4 | `1c3e5965-2818-4d52-9947-f0c0d1fa351b` | **`SUCCEEDED`** | **十一相全部 `SUCCEEDED`**（同上） | 无（45 件产物，`missing_artifacts` 为空）。**同一次 `pytest` 跑完两条 live 判据：`2 passed in 2852.67s`** —— 第二条是 GOAL-105 的两件机制在**真实手稿**上的取证：引用读数可解析且与正文重算逐项相等（`14 sentence(s) / 6 mark(s) / 3 cited`、`match: True`）、应答信如实说了「评审没提出可应答的点」（`no_points: True`） |

**读数文件**：
- `.cursor/plans/goals/evidence/GOAL-20261111-108-live-run2.json`（run 2：`run_id` /
  `state` / `phase_states` / 制品字节长度 / 失败事件）；
- `.cursor/plans/goals/evidence/GOAL-20261111-108-live-run3-SUCCEEDED.json`（run 3 的
  **十一相全绿**读数，45 件产物、`missing_artifacts: []`）；
- `.cursor/plans/goals/evidence/GOAL-20261111-108-live-run4-both-tests.json`（run 4：
  十一相全绿 + GOAL-105 两件机制的读数）。

**两次连续 `SUCCEEDED`**（run 3 / run 4，各自 45 件产物、`missing_artifacts: []`）——
这不是「跑一次侥幸绿」：同一站点、同一装配、同一判据，两次都到终态。

### 失败归类（**不许用「重跑就绿」掩盖**）

run 1 / run 2 的根因是**上游**：Europe PMC 那一次请求超过了适配器的 30 秒超时。
证据链（三层，逐层排除）：

1. **不是产品缺陷**：同一个 provider 由**同一份产品代码**驱动，8 次采样
   **全部成功**，延迟 `1.2 / 1.7 / 1.8 / 1.8 / 2.4 / 2.5 / 4.5 / 6.2 s`
   （中位数 2.1s、最大 6.2s）。
2. **不是网络不可达**：`curl` 直连 `www.ebi.ac.uk` 多次 200。
3. **是延迟分布的长尾**：同一查询在长尾上观测到 `18.5s` / `34.1s` / `>40s（超时）`
   —— 30 秒阈值**压在分布右尾上**，与 GOAL-108 给中转站修的那条
   （120s 压在 99.8/76.1/78.4s 的右尾）**是同一形态**。

**第三跑的作用**：确认「越过检索相之后链能继续」—— 它把 `retrieval` 跑过去了
（4 个任务 `SUCCEEDED`、29 件制品），因此上面的归类不是「链本身跑不动」。
**EC-08 的判据是「能跑起来且如实记录」**，不是「一次成功」：三次 run 的相级时间线
都逐字在案，失败的那两次各自带根因。

**如实边界**：run 3 的终态按读数文件为准；**本轮不宣称十一相 `SUCCEEDED`**。
`SUCCEEDED` 在什么条件下可达：检索命中的那次长尾不在 run 窗口内（重试或提高
provider 超时都能达到）—— 后者会改产品配置面，属**待拍板**（见 `W-2`）。

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
| 1 | PLAN-20261111-108 | `371b6a8f` | 探针 4/4 免费模型可用；独立性 93 passed；规模门 1422 passed；合约 62 passed | 见 `## CI 台账` | 三处真缺陷（novelty_writer 撞 domain_a / research_strong fallback 落评审 A / task_contracts 被写成 CRLF） | EC-08…11 待收口 | 真跑 + 文档 + 收口资产 |
| 2 | PLAN-20261111-108 | 见 `## CI 台账` | 收口验证器 **87 PASS / 0 FAIL**；可靠性 36 passed；loaders+contracts 92 passed；文档 28 passed；credential_audit 四面 `offenders=0`；ruff/format/mypy 三道具名 | 见 `## CI 台账` | **五处**：① `.env` 的 key 是上一个站的（门开着、每次 401）；② EC-01 的判据点名了一个**不存在**的判据文件；③ EC-07 同上；④ live harness 覆盖 GOAL-106 的**封存**读数（须 `RESEARCHOS_LIVE_EVIDENCE` 出口）；⑤ 宪章进度行写了状态枚举词（被 `test_no_goal_or_criterion_status_is_mirrored_in_the_charter` 抓到） | `W-1` / `W-2` / `W-3` 三条残余（均待拍板）；`U-1` / `U-2` 两条未覆盖。**run 3 终态 `SUCCEEDED`（十一相全绿 / 45 件产物 / 0 缺失）** | 序 77（配对消融） |

## 影响报告

**Domain / API / schema 变化**：**零**。本轮改的是配置（`llm_endpoints.yaml` /
`models.yaml` / `model_profiles.yaml`）、应用层（`spec_assembly_guard.py` 新增、
`review_outcome.py` 的 `NO_PROGRAM` 分支）、合约声明（五份会话合约的重试字段）与
判据/文档。没有新增或修改 Domain 实体、HTTP 路由或 schema。

**安全 / 凭据变化**：`LLM_MAIN_KEY` 的**值**换了（换站），仍只在 gitignored 的 `.env`；
`tools/credential_audit.py` 四面 `offenders=0`。**没有**改 §9 默认 deny：
`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 只在**显式设置它的进程**里放行，
产品默认仍是拒（`endpoint_policy` 对 private 的判定逐字未改）。

**兼容性 / 迁移风险**：
- 五份会话合约的 `retry_policy` 从 `max_attempts: 1` 变成 2 ⇒ 瞬时失败会**多试一次**
  （语义收紧，不是放宽）；`retryable_categories: []` 的两处矛盾**未统一**（`W-1`）。
- `EuropePmcConfig.timeout_seconds` 仍是 30（`W-2`）⇒ 检索长尾仍会失败。
- `workflow_lease_ttl_seconds` 默认仍是 300（`W-3`）⇒ 长会话仍可能在崩溃恢复面受限。

**上游版本影响**：零。`litellm` 对 `hy4free` 报 `Cost calculation failed: This model
isn't mapped yet` —— 这是**读数**（该模型不在 litellm 的 cost map 里），不是故障；
`credits: x0.00` 意味着计价本就是 0。

**本轮两条方法论收获**：
1. **`verify:` 字段点名的文件可能根本不存在** —— EC-01 / EC-07 各点了一个从未落地的
   判据文件，而那两条 EC 当时已标 PASS。「`verify:` 里的路径必须在树」本身该是一条判据。
2. **门判「可解析」不判「有效」** —— 过期 key 让 `live_run_gate` 三条件全满足而每次
   调用 401。这是「换站」这类动作的**通用**陷阱，已写进两页文档。

**本轮已确定的判据口径变化（须逐条登记理由）**：判据里写死「具体模型名 / 具体秒数」
的地方改为**结构性**断言 —— 那些值属**运维数据**（换接入商就变），把它们写成判据会让
「换站」变成「改判据」，反而掩盖判据真正守的东西（`(endpoint, model_name)` 互异、
参数被读进来、fallback 不落到评审面）。

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- `W-1` **`retryable_categories: []` 的两处语义仍自相矛盾**：`task_executor._retryable`
  把空表当**通配**，`TaskContract.decide_failure` 把空表当**全不重试**。本轮只给五份会话
  合约**显式列出**三个类别（绕开这个歧义），**没有**统一它 —— 统一会影响 29 份合约的
  语义，属**待拍板**，不在本 GOAL 的授权面内。
- `W-2` **Europe PMC 的 30 秒超时压在实测分布右尾上**（观测到 18.5 / 34.1 / >40 s）。
  这与本轮给中转站修的那条（120 → 300）是**同一形态**，但修它要改 `EuropePmcConfig`
  的默认值 —— 那是产品配置面，且会改变所有检索调用的失败窗口。已登记，**未改**。
- `W-3` **租赁 TTL 默认 300 秒对长会话仍是陷阱**：live harness 显式传 3600 绕开了它，
  但**产品默认没改**。改默认会拖慢所有 run 的崩溃恢复延迟，属**待拍板**。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **十一相 `SUCCEEDED` 只有两次样本**（run 3 `81123e5d` / run 4 `1c3e5965`，
  各 45 件产物、`missing_artifacts: []`）。两次不足以谈**成功率**：同一批尝试里前两次
  死在同一站点检索相的长尾上（`W-2`）⇒ 4 次尝试中 2 次成功。本轮**不宣称**成功率，
  也不宣称在 CI 上可复现（CI 无凭据，该判据走 skip）。
- `U-2` **`agnes-anthropic` 的 ANTHROPIC 形态在新站上从未被 run 消费**：端点保留启用
  只为 `test_anthropic_surface_boundary` 的 probe 腿有对象；新站是否真提供 Messages 形态
  由健康探测如实回报，本轮没有验证。

### 声称边界（**不得宣称**的事）

- `R-1` **不宣称「三位评审者全独立」**：四个免费模型满足不了全部独立性约束
  （4^7 穷举 **0 解**），用户拍板「保作者独立」⇒ 创新点评审与评审 A 共用
  `hy4-preview-f`。**写作组与评审组交集为空**这一面仍成立，且放宽的那一面由判据
  逐字枚举。
- `R-2` **不宣称「已消除所有静默停住」**：只收口了实测可达的四处（R-1…R-4）。
- `R-3` **不宣称「凭据有效」由门判定**：门只判「可解析」。本轮实际踩到了这条 ——
  过期 key 让门开着而每次调用 401。真实有效性只能由一次真实调用证明。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-11 | ACTIVE | 建档：序 76；十一条 EC；探针与换站已完成 |
| 2026-11-11 | ACHIEVED | 十一条 EC 逐条落地；真跑四次（后两次连续 `SUCCEEDED`）并如实归类；文档 / 宪章 / 收口资产到位；三条残余 + 两条未覆盖逐条明写 |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `371b6a8f` | `43003040534` Push on main / `43003040916` M0 Quality Gates | 两者均 `success` | 首轮交付（探针 / 换站 / 分工 / R-1…R-4）。M0 run 覆盖同一次 push 的全部提交。 |