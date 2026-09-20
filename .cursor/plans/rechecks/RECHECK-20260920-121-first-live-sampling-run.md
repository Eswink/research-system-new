---
id: RECHECK-20260920-121
plan_id: PLAN-20260920-121
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-009-cycle1
baseline_ref: 291224f
checked_head: dab74b0
---

# RECHECK-20260920-121 — 首次 live 采样（EC-01 复检）

## 检查范围

**不采信实施叙述**：只读磁盘上的记录、runbook 与 git 索引，自行重算判定。
独立复检脚本 `scratch/verify_goal009_cycle1.py`（gitignored）分四面：

- **A 记录面**：从 `live-run-record.json` **重新算出**（不是复述）终态是否真终态、口径是否为
  `REPEATABLE_CONFIGURATION`、指纹是否可判、usage 是否真归账、制品与证据是否可读、
  缺项是否**声明**而非留白；
- **B 同源面**：runbook 的样本条目必须与记录**逐值一致**（防抄错、防两处漂移），
  且必须写明单次样本的**证明力边界**与**未捕获项**；
- **C 判据面**：设计内 `FAILED` 的依据必须仍在代码里（离线同路径期望 + 判红信号）；
- **D 凭据面**：凭据值**不得**出现在任何 **tracked** 文件（**只输出命中数，不打印值**）、
  `.env` 不得带 `RESEARCHOS_AGENT_RUNTIME`、进程环境不得留开关。

## 检查结果

**独立脚本：PASS 22 checks**（A=8 / B=8 / C=2 / D=4）。

| 面 | 判据 | 实测 |
| --- | --- | --- |
| A1–A2 | run id 非空；`terminal_state` ∈ {SUCCEEDED, FAILED, CANCELLED, TIMED_OUT} | `142f7e77-cd4d-4044-a953-79296509fd54`；`FAILED` |
| A3 | `verdict` **恰为** `REPEATABLE_CONFIGURATION` | 一致（「完全可复现」在本记录里不可表达） |
| A4 | 指纹可判 | `agnes-2.5-flash` |
| A5 | usage 真归账 | `usage_entries=1`、`model_tokens=15219` |
| A6 | 制品与证据可读 | artifacts=1、evidence=1 |
| A7 | 缺项**声明**而非留白 | `['system_fingerprint', 'safe_response_metadata']` |
| A8 | 制品 id 带 `:session_message` 后缀（判拒路径的形状） | `400c60fc-…:session_message` |
| B | runbook 样本**逐值**等于记录（run id / 返回 model / 终态 / 口径 / tokens 五值） | 五值全中 |
| B | runbook 写明终态是 `FAILED`（**未**宣称 SUCCEEDED）、写明单次样本边界、写明未捕获项 | 三处全中 |
| C | 离线同路径判据仍把 `FAILED`+acceptance gate 钉为**期望**，并把 `carries no structured output` 当判红信号 | 仍在（未被改动） |
| D1–D2 | 凭据值存在于本机 `.env`；**tracked 文件命中数 = 0** | `hits=0`（**未打印值**） |
| D3–D4 | `.env` 不带 `RESEARCHOS_AGENT_RUNTIME`；进程环境开关为空 | 均成立（`''`） |

**独立佐证（C 面之外的实跑）**：离线同路径套件真跑
`tests/e2e/test_ec03_real_runtime_offline_chain.py` ⇒ **2 passed / 1 skipped in 17.13s**，
其中 `test_real_runtime_offline_chain_segments` 内部就含 `_assert_deliverable_adjudicated`
（断言 `run["state"] == "FAILED"` 且点名 acceptance gate）——**同一真实 runtime 路径**
（mock 端点、**零公网调用**）独立复现了「判拒是链在正常工作」。

**反证与复原（离线，无真实调用）**：

| # | 动作 | 观察 | 复原 |
| --- | --- | --- | --- |
| F1 | 默认门（无内联前缀）跑 live 文件 | **1 passed / 1 skipped** | ——（本即基线） |
| F2 | 加内联前缀 + `-k closed` | 关门用例 **SKIPPED**（「gate is open」）⇒ 两条开门条件成立 | 去掉前缀 |
| F3 | 去前缀复跑同一文件 | 回到 **1 passed / 1 skipped**（**无残留**） | —— |
| F4 | 读 runbook 同源判据 | **10 passed**（新增样本条目**未**引入判红 token） | —— |
| F5 | 凭据面扫描 | tracked 文件命中 **0** | —— |

**真实调用次数**：**1 次序列**（probe + run 同属一次），与授权「次数取最小必要、不重复重跑」
一致。EC-03 的漂移原始样本由**同一次** probe 带出，**未**另发调用。

## Warnings（不阻断，如实登记）

- **W-1 终态是 `FAILED`（设计内 acceptance-gate 判拒），不是 `SUCCEEDED`。** 本 GOAL 的 EC-01
  判据词是「**到终态**」，`FAILED` ∈ `ResearchRunState.terminal()`，因此判据成立；但这**不等于**
  「垂直切片用真实模型端到端成功」。归类依据是三条**收敛**证据（制品 id 后缀 `:session_message`、
  usage 真归账、probe `verified and ok`）+ 离线同路径判据的既有期望（C 面 + 其真跑）。
  **不得**在任何读面把它表述成「run 成功」。
- **W-2 该次运行的逐条失败消息未捕获。** 它们只活在进程内 in-memory 事件库，进程结束即消失；
  要拿到字面消息须**再跑一次**，与「次数取最小必要」冲突。因此归类是**收敛证据 + 既有离线期望**，
  **不是**直接读到的失败字符串——已在 runbook 与 PLAN 里**逐字登记**。
- **W-3 litellm 无该模型的价格映射**（`Cost calculation failed: This model isn't mapped yet.
  model=agnes-2.5-flash`，pytest 输出 3 条同类 warning）。**不影响**归账（token 数取自响应
  usage），但意味着**成本估算**这条面在真实模型上仍无依据。**未**为消除 warning 改依赖/pin。
- **W-4 「一致」是单次样本。** 实测返回标识 == 声明值，但单次一致**不能**推出「永不漂移」，
  也**不能**推出底层模型与声明完全同一；口径仍只能是「可重复配置」（AGENTS.md §4）。
- **W-5 `system_fingerprint` 与 `safe_response_metadata` 缺失**（进 `missing_fields`）。
  该端点未返回这两项 ⇒ 指纹面**只有**「返回标识」一个可判字段，**不是**完整运行时指纹。
- **W-6 EC-02 的 anthropic 面问题在本轮**未处理**：`agnes_flash.endpoint` 仍是 `main`
  （`OPENAI_COMPATIBLE`），anthropic 面由 probe 段驱动——这正是 EC-02 要收敛的二选一。
- **W-7 全量 m0 的红项是一条「凭据可得性」驱动的环境签名，已用反证定位到根因；CI 不可能复现。**
  三轮如实登记（**不**只记最后那轮）：

  | 轮 | 配置 | 结果 |
  | --- | --- | --- |
  | 1 | test DSN pin | **22/23 PASS**，红：`python/tests` 的单条用例（4200 passed / 12 skipped） |
  | 2 | `RESEARCHOS_POSTGRES_DSN=""`（+另三个空） | **同一个红**（4008 passed / 204 skipped） |
  | 3 | test DSN pin + **`LLM_MAIN_KEY=""`**（复现 CI 的「无凭据」条件） | **PASS：profile=m0; 23 deterministic checks**（**4201 passed / 12 skipped**，557.61s） |

  - **红项**：`tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
    （`assert failed, events` ⇒ `[]`，即没有 `run.failed` 事件）。
  - **中间假设被自己推翻（如实登记）**：第 1 轮后曾把根因归给「为让 `tests/postgres` 连库而
    钉的 test DSN 活过了该用例只清 3 个键的 hermetic 守卫」。**第 2 轮用空 DSN 复跑仍红 ⇒ 该假设
    不成立**，DSN **不是**触发条件（空 DSN 只把 postgres 用例从 12 skipped 变成 204 skipped，
    红项不变）。
  - **真正的根因（反证定位）**：该用例对**凭据是否可解析**不 hermetic。前序模块只要
    import 过 openhands-sdk（⇒ litellm ⇒ `load_dotenv()`）⇒ `.env` 的凭据进入进程 ⇒
    目录里 `main` 端点的 `discovery.enabled: true` 于是**真的发起端点发现**；发现成功后控制面
    状态改变，run 走到 `FAILED` 却**不再产出 `run.failed` 事件** ⇒ 断言空集。
  - **最小复现**：`pytest tests/adapters/openhands tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
    ⇒ **1 failed, 83 passed in 28.08s**，且该用例 captured log 里出现
    `GET https://apihub.agnes-ai.com/v1/models "HTTP/1.1 200 OK"`。
  - **反证（决定性）**：同一对命令加 **`LLM_MAIN_KEY=""`**（键存在且为空 ⇒ litellm 的
    `load_dotenv` **不覆盖**）⇒ **84 passed in 18.25s**，**且没有任何出站记录**。
    ⇒ **红 ⇔ 凭据可解析**。**CI 两样都没有**（无 `.env`、无凭据，`quality-*` job 只设
    `PYTHONUTF8` / `PYTHONIOENCODING`，已逐行核对 workflow）⇒ **该红在 CI 上不可能发生**。
  - **第 3 轮为什么是绿**：把 `LLM_MAIN_KEY` 置空（键存在且为空 ⇒ litellm 的 `load_dotenv` **不覆盖**）
    就复现了 **CI 的条件**（CI 无 `.env`、无凭据）⇒ 该红消失。**这不是绕过门禁**：改的是
    **环境输入**而非任何断言/门禁/快照，且被阻断的正是 CI 根本不具备的输入。**postgres 用例仍在跑**
    （12 skipped 与 GOAL-008 基线一致，不是第 2 轮的 204 skipped）。
  - **同轮观察到的出网（安全相关，如实登记）**：`GET https://apihub.agnes-ai.com/v1/models`
    **200 OK** 是**真实出站请求**。即「本地门离线」**不是**结构保证——只要 operator `.env` 里有
    可用凭据且前序代码 import 过 litellm，默认门就会替你真调用。**未修**（跑测试改测试、
    改 hermetic 守卫不在 EC-01 射程内），作为**残余**登记并沉淀为 `MEM-20260920-095`。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01 的判据全部成立且**经独立脚本重算**（22 checks）：
live 分支**真跑**过、终态为真终态、指纹可判、usage 真归账、制品与证据可读、口径恰为
`REPEATABLE_CONFIGURATION`；反证证明门在无前缀时**如实 skip 且无残留**；凭据值在 tracked 文件中
**命中数为 0**。PLAN-20260920-121 可置 **DONE**。

**Warning 不阻断的理由**：W-1/W-2/W-3/W-5 是**如实登记的边界**（终态取值、未捕获项、
无价格映射、缺指纹字段），**不是**被判据掩盖的失败；W-4 是口径纪律；W-6 是**下一个** EC 的入口；
W-7 是全量门的时序，结果单独记账。**没有**任何一条 WW 是靠放宽断言或改门禁获得的。
