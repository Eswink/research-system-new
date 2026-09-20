---
id: PLAN-20260920-121
slug: first-live-sampling-run
title: 首次 live 采样：把 EC-04 的 live 分支从「如实 skip」跑到「有真实样本」（run 到终态 + 指纹可判 + usage 真归账 + 制品与证据可读，口径停在可重复配置）
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 1 = EC-01（live 采样第一次）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（授权在端点 `https://apihub.agnes-ai.com`、模型 `agnes-2.5-flash` 上做 **live-gated 真实调用**，**次数取最小必要**，不做压测/批量/重复重跑；该凭据为**可弃用的免费额度**，泄露风险已由用户明示接受——此声明只降低追责口径，**不放松凭据纪律**）、第 (2) 条（键名 `LLM_MAIN_KEY`，值只存在于本机 gitignored 的 `.env`；值不得写入任何 tracked 文件、DB、记录、日志或命令回显；**不得**把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`，它只作为单条命令的内联前缀）、第 (3) 条（默认 runtime 保持 Fake、默认 CI 离线；live 分支必须**显式** `RESEARCHOS_AGENT_RUNTIME=openhands` 才开门）与 AGENTS.md §4（结论口径停在「可重复配置」，**不得**声称「完全模型可复现」）。本 PLAN 遵守：不新增依赖、不改 pin、不改 Policy/eligibility、不把真实 runtime 设为默认、不把凭据写进 CI、不修改任何门禁或断言强度；**live 调用次数取最小必要（本 PLAN 只跑一次真实调用序列）**。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md
memory_entries:
  - .cursor/memory/entries/MEM-20260920-094-live-gate-credential-visibility-and-designed-failed.md
  - .cursor/memory/entries/MEM-20260920-095-credential-availability-breaks-hermetic-tests.md
---

# PLAN-20260920-121 — 首次 live 采样（GOAL-009 cycle 1 = EC-01）

## 目标

把 GOAL-008 收口时**如实 skip** 的 live 分支推进到**有真实样本**：

1. **真实 run 到终态**：用登记端点（`agnes-anthropic` 的 `base_url`）与登记模型
   （`agnes-2.5-flash`）跑一次真实 run，**到终态**且失败也是终态（不掩盖）；
2. **四段判据逐条为真**：probe 段 `verified and ok`；run 到终态；运行时**指纹可判**；
   usage **真归账**到 BudgetLedger；制品与证据**可读**；
3. **口径停在「可重复配置」**：`verdict` 恰为 `REPEATABLE_CONFIGURATION`
   （AGENTS.md §4）——`system_fingerprint` 缺失是**如实的缺口**，**不**降级、**不**冒充；
4. **样本如实登记**：run id / UTC 时间 / probe 返回的 model 名——**不含凭据值或片段**；
5. **顺手带出 EC-03 的原始样本**：同一次 probe 的「实测返回 model 名 vs 声明值」原样留证
   （EC-03 复用本次样本，**不另发调用**）；
6. **反证门仍关**：去掉内联前缀 ⇒ 同一命令**走 skip** 且记录 `NOT_VERIFIED`（零出站）。

## 先探明再动手（建档时只读勘察 + 离线实跑已确认的事实）

1. **凭据可用**（本 GOAL 与 GOAL-008 的关键差别）：`.env` 存在且 gitignored
   （`git check-ignore -v .env` ⇒ `.gitignore:1:.env`；`git ls-files --error-unmatch .env`
   ⇒ 不匹配）；`LLM_MAIN_KEY` 值非空（**只测长度，未打印值**）。
2. **dotenv 来自导入栈而非仓库代码**：全仓 `grep -rn "load_dotenv" --include=*.py` ⇒ **0 命中**；
   裸导入 `adapters.relay.credential_resolver` 时 `has('LLM_MAIN_KEY')` 为 `False`，
   导入 litellm 后为 `True`。⇒ **判据必须跑在完整导入栈里**（pytest 路径满足）。
3. **门的默认姿态是关的，且理由逐字可读**（离线实跑，**无网络**）：
   `pytest tests/e2e/test_ec04_live_first_run.py` ⇒ **1 passed / 1 skipped**
   （`test_live_gate_stays_closed_without_configuration` PASSED、live 分支 SKIPPED）。
4. **门在完整 pytest 进程里能开**（离线实跑，**无网络**）：
   `RESEARCHOS_AGENT_RUNTIME=openhands pytest … -k closed` ⇒ 该用例 **SKIPPED**
   （跳过理由即「gate is open on this machine」）——证明**两条**开门条件在 pytest 进程内同时成立，
   且内联前缀**没有被** 导入栈的 dotenv 覆盖（`load_dotenv` 默认不覆盖既有变量）。
5. **端点面已登记**（`examples/config/llm_endpoints.yaml`）：`agnes-anthropic`
   `protocol: ANTHROPIC`、`base_url: https://apihub.agnes-ai.com/v1`、`credential_ref: LLM_MAIN_KEY`；
   `validation` 面 `main` 为 `OPENAI_COMPATIBLE`。模型 `agnes_flash` 的 `endpoint: main`
   ⇒ 本次 run **走 OPENAI_COMPATIBLE 面**，anthropic 面由 probe 段驱动（EC-02 的另一半）。
6. **run 是同步的**：`tests/e2e/live_run_support.py` 的 `start_run` 之后**没有**轮询循环，
   说明 `POST /projects/{p}/runs` 内联跑到终态 ⇒ 单次调用即出终态，无需额外等待。
7. **判据已存在**：`tests/e2e/test_ec04_live_first_run.py` 的
   `test_live_first_run_reaches_a_terminal_state` 已实现四段断言 + `verdict` 断言；
   本 PLAN **不改判据**，只**执行**它并**登记样本**。

## 口径（先写死，避免实施时漂移）

- **调用次数**：真实调用序列**只跑一次**（probe + run 同属一次序列）。若失败，按 fix_policy
  修复后再跑；**不为「再确认一次」重复跑**。
- **凭据纪律**：值**只**在进程内传；记录里只出现**键名** `LLM_MAIN_KEY`。任何回显/日志/记录
  **不得**出现值或片段（发现即停止并按 escalation 处置）。
- **开关不留痕**：`RESEARCHOS_AGENT_RUNTIME` 只作为**单条命令的内联前缀**；跑完确认它
  **不在** shell 环境、**不在** `.env`（`.env` 里只有一个**名字以其结尾但完全不同**的
  `AGENT_RUNTIME` 键，`services/api/settings.py` 只读 `RESEARCHOS_AGENT_RUNTIME`）。
- **口径**：只能说「可重复配置」。**不得**从单次样本推出「模型可复现」「永不漂移」。
- **失败也是终态**：失败**如实**归类（端点面 / 协议面 / 装配面）并写进证据，**不**写成 PASS，
  **不**降低断言。

## 验收条件

- **AC-1**：`RESEARCHOS_AGENT_RUNTIME=openhands … pytest tests/e2e/test_ec04_live_first_run.py -v`
  ⇒ `test_live_first_run_reaches_a_terminal_state` **PASS（非 skip）**，且
  `test_live_gate_stays_closed_without_configuration` 走 skip 分支（门已开）。
- **AC-2**：落盘的 run 记录 `verdict == "REPEATABLE_CONFIGURATION"`，且
  `reached_terminal_state` / `returned_model_identifier` / `usage_entries` / `model_tokens` /
  `artifact_ids` / `evidence_ids` 六项均为真（`missing_fields` 如实列出缺口）。
- **AC-3**：样本（run id / UTC 时间 / probe 返回 model 名 / 声明值）落进 RECHECK 与
  `docs/integration/LIVE_MODEL_RUNBOOK.md` 的样本条目；**无凭据值或片段**。
- **AC-4**（反证）：去掉内联前缀跑同一命令 ⇒ live 分支 **skip**，且产出记录
  `verdict == NOT_VERIFIED`、理由点名未满足条件（**零出站**）。
- **AC-5**：跑后 `RESEARCHOS_AGENT_RUNTIME` **不在** shell 环境、**不在** `.env`；
  `git status` 无意外改动（只含本 PLAN 的显式路径）。
- **AC-6**：本地门禁绿——`make validate-all`（m0 全量 23 项）+ 受影响定向套件
  （e2e live 相关 + 架构同源判据）+ web 门未被牵动；治理 `validate.py` 绿。

## 实施清单

- [x] WP1 **离线基线**（无网络）：默认门下跑 `tests/e2e/test_ec04_live_first_run.py`
      ⇒ 记录 1 passed / 1 skipped；再以 `-k closed` + 内联前缀确认门能开（SKIPPED）。
- [x] WP2 **执行 live 采样（唯一一次真实调用序列）**：
      `RESEARCHOS_AGENT_RUNTIME=openhands … pytest tests/e2e/test_ec04_live_first_run.py -v
      --basetemp=scratch/live-run-ec01` ⇒ 记录 PASS + 落盘记录路径。
- [x] WP3 **登记样本**：把 run id / UTC 时间 / 返回 model 名 / 声明值 / 判定 / 口径
      写进本 PLAN 的证据段与 RECHECK；在 `docs/integration/LIVE_MODEL_RUNBOOK.md` 增加
      **首次 live 样本**条目（**不得**引入会被同源判据判红的反引号 token）。
- [x] WP4 **反证门**：去掉内联前缀复跑 ⇒ skip + `NOT_VERIFIED`；并确认开关未留痕。
- [x] WP5 **本地验证**：`make validate-all`（m0 23 项）+ 定向套件 + 治理 `validate.py`
      + `validate_bundle` + DOCS-CHECK；跑后复核 `git status`。
- [x] WP6 **收口**：写 RECHECK（独立复检）、置本 PLAN 为 DONE、投影 ALL_PLAN、
      回写 GOAL-009 的 EC-01 状态 / 迭代日志 / 状态历史；commit（显式路径）→ push → CI 到终态。

## 证据

（执行时逐条填入；**不得**出现凭据值或片段。）

### WP1 离线基线

- 默认门：`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec04_live_first_run.py -v`
  ⇒ **1 passed, 1 skipped in 8.61s**（live 分支 SKIPPED、关门用例 PASSED）。
- 门可开（内联前缀 + `-k closed`）⇒ **1 skipped, 1 deselected in 7.24s**（跳过即「gate is open」）。

### WP2 首次 live 采样

**AC-1 PASS**：`RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest
tests/e2e/test_ec04_live_first_run.py -v -p no:randomly --basetemp=scratch/live-run-ec01`
⇒ **1 passed, 1 skipped, 3 warnings in 28.69s**：

- `test_live_first_run_reaches_a_terminal_state` **PASSED**（首个真实 live run 到终态）；
- `test_live_gate_stays_closed_without_configuration` **SKIPPED**（跳过即「gate is open」）。

**落盘记录**（`scratch/live-run-ec01/test_live_first_run_reaches_a_0/live-run-record.json`，
**不含凭据值或片段**）：

| 字段 | 值 |
| --- | --- |
| `run_id` | `142f7e77-cd4d-4044-a953-79296509fd54` |
| `terminal_state` | `FAILED`（**设计内**，见下「失败归类」） |
| `verdict` | `REPEATABLE_CONFIGURATION` |
| `endpoint_config_digest` | `sha256:51997c6f…` |
| `returned_model_identifier` | `agnes-2.5-flash` |
| `system_fingerprint` | `null`（如实缺口，进 `missing_fields`） |
| `probe_suite_digest` | `sha256:d384cbb5…` |
| `missing_fields` | `["system_fingerprint", "safe_response_metadata"]` |
| `model_tokens` | `15219` |
| `usage_entries` | `1` |
| `artifact_ids` | `["400c60fc-870e-4f39-8657-ed9e16b9b7dc:session_message"]` |
| `evidence_ids` | `["evidence:400c60fc-…:session_message"]` |
| `reason` | `null` |

**AC-2 PASS**：六项判据为真——`reached_terminal_state`（`FAILED` ∈ 域终态集）、
`returned_model_identifier` 非空（**指纹可判**）、`usage_entries ≥ 1`、`model_tokens > 0`
（**usage 真归账**）、`artifact_ids` 与 `evidence_ids` 非空（**制品与证据可读**）；
`verdict` 恰为 `REPEATABLE_CONFIGURATION`（口径停在「可重复配置」）。

**失败归类（本 PLAN 最要紧的一条诚实记录）**：终态是 **`FAILED`**——**不**写成 SUCCEEDED。
归类结论是 **协议设计内的 acceptance gate 判拒，不是端点/协议/装配缺陷**，依据三条收敛证据：

1. 制品 id 后缀是 **`:session_message`**——合约要的是 `analysis_report`，真实会话给的是
   `session_message`，两者不符 ⇒ 判拒；
2. 同路径的**离线判据**（`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的
   `_assert_deliverable_adjudicated`）把「`FAILED` + 点名 acceptance gate」固定为该路径的
   **期望**结果，并把「出现 `carries no structured output`」当判红条件（那才说明登记链被跳过）；
3. probe 段 `verified and ok` 且 usage 真实归账 ⇒ LLM 链路本身是通的。

**未捕获项（如实登记）**：该次运行的**逐条失败消息**只存在于进程内的 in-memory 事件库，
进程结束即消失，**没有**留成文本 ⇒ 上面的归类依据是上述三条收敛证据 + 既有离线期望，
**不是**直接读到的失败字符串。**本 PLAN 因此不重复跑真实调用**（授权要求次数取最小必要）。

**同一次 probe 带出的 EC-03 原始样本**：实测返回 model 名 `agnes-2.5-flash` == 声明值
`agnes-2.5-flash`（`examples/config/models.yaml` 的 `agnes_flash.model_name`）⇒ 漂移判定
**一致**。**证明力边界**：单次一致**不**等于「永不漂移」，**不**升级三态里的「一致」为永久结论。

**顺带观察（非缺陷登记）**：pytest 输出 3 条同类 warning——litellm 对
`model=agnes-2.5-flash` 无价格映射（`Cost calculation failed: This model isn't mapped yet`）。
这是**如实的能力边界**（该模型不在 litellm 价格表里），**不**影响归账（token 数由响应 usage 得出），
本 PLAN **不**为消除该 warning 而改依赖或改 pin。

### WP5 本地验证

**AC-6 PASS**（m0 三轮，**全部如实登记**）：

| 轮 | 配置 | 结果 |
| --- | --- | --- |
| 1 | test DSN pin | 22/23（红：`python/tests` 单条；4200 passed / 12 skipped） |
| 2 | `RESEARCHOS_POSTGRES_DSN=""`（+另三个空） | 同一个红（4008 passed / 204 skipped） |
| 3 | test DSN pin + `LLM_MAIN_KEY=""` | **PASS：profile=m0; 23 deterministic checks**（**4201 passed / 12 skipped**，557.61s） |

- **红项根因（反证定位，不是 DSN）**：`tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
  对**凭据是否可解析**不封闭。前序模块 import 过 openhands-sdk（⇒ litellm ⇒ `load_dotenv()`）
  后 `.env` 的凭据进入进程 ⇒ 目录里 `main` 端点（`discovery.enabled: true`）**真的发起端点发现**
  ⇒ 控制面状态改变 ⇒ run 走到 `FAILED` 却**不再产出 `run.failed`** ⇒ 断言空集。
- **最小复现**：`pytest tests/adapters/openhands <该用例>` ⇒ **1 failed, 83 passed in 28.08s**，
  日志里有 `GET https://apihub.agnes-ai.com/v1/models "HTTP/1.1 200 OK"`。
- **决定性反证**：同一对命令加 `LLM_MAIN_KEY=""` ⇒ **84 passed in 18.25s**，**无任何出站记录**
  ⇒ **红 ⇔ 凭据可解析**；**CI 无 `.env`、无凭据**（`quality-*` job 只设 `PYTHONUTF8` /
  `PYTHONIOENCODING`，已逐行核对 workflow）⇒ **该红在 CI 上不可复现**。
- **被自己推翻的中间假设**：曾把根因归给 DSN pin（第 1 轮后）；**第 2 轮空 DSN 仍红 ⇒ 假设不成立**，
  已在 RECHECK W-7 与 `MEM-20260920-095` 里**如实改正**。
- 定向套件：runbook 同源判据 **10 passed**；离线同路径 **2 passed / 1 skipped**；
  独立复检脚本 **22 checks PASS**。
- 治理：`validate.py` / `validate_bundle` / DOCS-CHECK 绿。

### WP4 反证

**AC-4 PASS**：去掉内联前缀跑同一文件
（`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec04_live_first_run.py -v -p no:randomly`）
⇒ **1 passed, 1 skipped in 9.66s**：live 用例 **SKIPPED**、关门用例 **PASSED**
—— 即回到 GOAL-008 的「如实 skip + `NOT_VERIFIED`」语义，**零出站**（门关着不构造 URL、不碰 socket）。

**AC-5 PASS**：跑前跑后 `echo` 环境 ⇒ `RESEARCHOS_AGENT_RUNTIME` 为 **unset**；
`grep -c '^RESEARCHOS_AGENT_RUNTIME' .env` ⇒ **0**。开关**没有**留在环境或 `.env`。

## 状态历史

- 2026-09-20 收口：**DONE**。EC-01 判据全部成立且经**独立复检**（
  `.cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md`，
  `result: PASS_WITH_WARNINGS`，W-1…W-7）。独立脚本 `scratch/verify_goal009_cycle1.py`
  **22 checks PASS**（记录面 8 / 同源面 8 / 判据面 2 / 凭据面 4），其中凭据面是
  **扫描全部 tracked 文件找凭据值、只输出命中数**（`hits=0`，**未打印值**）。
  离线同路径套件真跑 **2 passed / 1 skipped**，独立复现「判拒是链在正常工作」。
  **真实调用 1 次序列**（probe + run），与授权的最小必要口径一致；EC-03 的漂移原始样本
  由同一次 probe 带出，未另发调用。工程记忆沉淀：`MEM-20260920-094`。**未改任何判据、
  未改门禁、未新增依赖、未改 pin**。

- 2026-09-20 本地门禁（三轮，如实登记）：第 1 轮 **22/23**、第 2 轮**同一个红**、
  第 3 轮（`LLM_MAIN_KEY=""` 复现 CI 的「无凭据」条件 + test DSN pin）**PASS：profile=m0;
  23 deterministic checks（4201 passed / 12 skipped）**。红项经**反证**定位为「凭据可得性」驱动的
  环境签名（最小复现 + 决定性反证见 WP5），**不是**本轮改动造成的回归（本轮只改文档与记录）；
  **中间假设被自己推翻并已改正**（RECHECK W-7 / `MEM-20260920-095`）。同轮还捕获到**一次真实出站**
  （`GET https://apihub.agnes-ai.com/v1/models` **200 OK**）——「本地门离线」**不是**结构保证，
  已作为残余登记。**未改任何断言、门禁或快照**：改的是环境输入，且被阻断的正是 CI 不具备的输入。

- 2026-09-20 建档：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 1（EC-01）。
  建档前只读勘察 + **两次离线实跑**（默认门 1 passed / 1 skipped；内联前缀下关门用例 SKIPPED）
  已确认：**凭据可用且门能开**，且内联前缀未被 dotenv 覆盖。**本 PLAN 不修改任何判据**。

## 影响报告

**Domain / API / Schema**：无变化。本 PLAN **不新增也不修改**任何域实体、DTO、路由或迁移；
它只**执行**既有 live 判据并**登记样本**。EC-02（anthropic 面绑定）若选改绑路径，其
Domain/读面影响在**那条** PLAN 里单独评估——本 PLAN 不预支。

**安全 / 凭据**：无新增信任面。live 调用走**既有**门（`evaluate_live_run_gate`，两条条件缺一
不开）与**既有** URL 策略（`EndpointUrlPolicy`，`allow_localhost=False` ⇒ 真端点必须是公网
地址，默认 deny 姿态不放松）。凭据值只在进程内传递；**新增的记录面只有键名** `LLM_MAIN_KEY`。
**本 PLAN 明确禁止**把凭据写进 CI——CI 保持离线，live 证据只在本地产生。

**兼容性 / 迁移风险**：无迁移。`docs/integration/LIVE_MODEL_RUNBOOK.md` 的新增样本条目受
既有同源判据约束（`tests/architecture/python/test_runbook_same_source.py`）——因此样本条目
**不得**引入会被判红的反引号 token（大写且含下划线的 token 必须能在代码里找到；仓库路径必须
存在；pytest 目标必须存在）。**风险**：若 live 面暴露缺陷，本 PLAN 的剩余 WP 转为按缺陷修复
（fix_policy 上限内），**不**通过放宽断言绕过。

**上游版本影响**：无。**不新增依赖、不改任何 pin**（需要新依赖即 BLOCKED）。

**下一项任务**：WP2 的首次 live 采样（一次真实调用序列）→ WP3 登记样本 →
WP4 反证门 → WP5 本地门禁 → WP6 收口并回写 GOAL-009 的 EC-01。
