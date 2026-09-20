---
id: RECHECK-20260920-120
plan_id: PLAN-20260920-120
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-closeout
baseline_ref: b3bb96a
checked_head: b3bb96a
---

# RECHECK-20260920-120 — GOAL-008 收口复检（EC-01…EC-06）

## 检查范围

不采信六条 RECHECK 的结论文本：在**当前树**与**干净 checkout**（`git clone --no-hardlinks`
到仓库外的 `D:\research-system-seal-20260920`，tip `b3bb96a`）各跑一遍同一份三层判据脚本
`scratch/verify_goal008_closeout.py`（**65 checks**：A 交付物在树 / B 判据用例在树 /
C 登记面一致），并把六条 EC 的判据套件**合并**真跑（同一命令、同一进程）。
收口另外要求：GOAL「终止与收口 · 收口结论」+ `status: ACHIEVED` + `latest_recheck`
指向本文件 + 残余登记 + CI 台账尾巴。

## 检查结果

### A/B/C 三层（当前树，实测）

| 层 | 判的是什么 | checks | 结果 |
| --- | --- | --- | --- |
| A 交付物 | 六条 EC 的关键交付物文件 + 其中必须出现的符号（如 `ANTHROPIC_MESSAGES`、`class ModelReproducibilityVerdict`、`def assess_model_drift`、`## 3. 重启后重输的边界`、`probe-drift`） | 22 | PASS |
| B 判据用例 | 每条 EC 的判据文件里按名找到代表用例（如 `test_verdict_is_exactly_the_two_states`、`test_skip_record_is_not_verified`、`test_no_affirmative_fully_reproducible_claim`、`unknown is not the same as no drift`） | 17 | PASS |
| C 登记面 | GOAL 的 EC 表 6 行逐行 `**PASS`、`latest_recheck` 指向存在的 RECHECK 且 `result: PASS*`、child_plans 5 个文件存在且 `status: DONE`、`memory_entries` 6 个文件存在、ALL_PLAN 有对应行 | 26 | PASS |
| **合计** | | **65** | **PASS** |

### 合并判据套件（六条 EC 一次跑完）

同一命令、同一进程，包含 EC-03 的离线全链与**曾被污染**的 fork 契约用例：

```sh
pytest tests/adapters/relay/test_anthropic_messages.py tests/architecture/python/test_protocol_vocabulary.py \
  tests/architecture/python/test_model_config_face_wiring.py tests/domain/test_entities_invariants.py \
  tests/application/test_endpoint_policy.py tests/tooling/test_credential_audit.py \
  tests/architecture/python/test_credential_boundary_wording.py tests/api/test_llm_endpoints_api.py \
  tests/domain/test_reproducibility_verdict.py tests/application/model_relay/test_live_run_record.py \
  tests/e2e/test_ec04_live_gate_offline.py tests/e2e/test_ec04_live_first_run.py \
  tests/architecture/python/test_reproducibility_wording.py tests/domain/test_model_drift.py \
  tests/api/test_models_api.py tests/architecture/python/test_runbook_same_source.py \
  tests/e2e/test_ec03_real_runtime_offline_chain.py tests/contracts/test_agent_runtime_contract.py \
  tests/adapters/openhands/test_fork_override.py
```

- **当前树：196 passed / 9 skipped**；
- **干净 checkout：196 passed / 9 skipped**（同一解释器，cwd = clone）；
- ⇒ 两棵树**结论一致**：干净 checkout 不引入新绿，也不引入新红。

### 干净 checkout 封印

- `git clone --no-hardlinks` 到 `D:\research-system-seal-20260920`，checkout `b3bb96a`
  （六条 EC 全部落地的 tip）；克隆树 `git status` **干净**；`git ls-files` 计数
  **3170 == 3170**（与当前树一致）；
- 复检脚本在克隆树：`GOAL008_ROOT=<clone>` ⇒ **65 checks PASS**，与当前树同结论；
- 合并判据套件在克隆树：**196 passed / 9 skipped**，与当前树同结论；
- **唯一的人为补足（如实披露）**：克隆树没有 `.venv`，判据用**主仓库的 venv 解释器**
  运行（依赖是**安装物**、不是仓库内容），cwd = 克隆树以确保 `pythonpath=["."]` 解析到克隆树。
  这不是证据面的补足——判据读的代码、文档、记录全部来自克隆树；
- **已知的时序说明**：本轮收口自身的记录（RECHECK-120 / PLAN-120 / GOAL 的收口结论）
  以及 cycle-6 的 CI 台账提交**不在**该 tip 里（它们产生于克隆之后），与 GOAL-007 收口
  （RECHECK-113）同一情形，**不是证据面缺陷**。

### 复检**实测出的缺陷**（已修）

本脚本第一版在 EC-02 的证据映射里指向 `tests/application/test_model_config_face_wiring.py`，
**该路径不存在**——真实位置是 `tests/architecture/python/test_model_config_face_wiring.py`。
脚本在**当前树第一次跑就红了**（2 条不成立），按事实更正路径后 65 checks 全绿。
这条不是产品缺陷，而是**收口脚本自己的证据映射写错**：它的价值恰好说明「三层判据回证据面」
是有效的——记录里写「PC-02 已落地」不会让它绿，文件真的在才会。

## Warnings（不阻断，如实登记）

- **W-1 live 分支未实测（能力边界，GOAL 明文要求逐字写明）**：EC-04 与 EC-05 的 live 分支
  在**本机没有发生过**——六项候选凭据环境变量（`LLM_MAIN_KEY` / `DEV_LLM_API_KEY` /
  `RESEARCHOS_LIVE_E2E_KEY` / `RESEARCHOS_LIVE_E2E_ENDPOINT` / `OPENAI_API_KEY` /
  `ANTHROPIC_API_KEY`）**全部 absent**，`RESEARCHOS_AGENT_RUNTIME` 未配置 ⇒
  `evaluate_live_run_gate` 的两条开门条件**都不满足**，门是关的；
  因此 `tests/e2e/test_ec04_live_first_run.py` 的主判据**跳过**，产出的是 `NOT_VERIFIED` 记录。
  **真实端点上的那次 run 从未发生**，`agnes-2.5-flash` 的真实返回标识、
  `system_fingerprint`、真实 usage 归账**都没有样本**。
  **这不自动阻塞 ACHIEVED**（GOAL「终止与收口」明文），但**不得**写成「已实测通过」。
- **W-2 EC-04 的 live 路径绑定不是 anthropic 面**：目录里所有模型绑 `main`
  （`OPENAI_COMPATIBLE`）；登记进目录的 `agnes-anthropic` 端点只由 probe 段驱动 ⇒
  「一次 run 自身消费 ANTHROPIC 面」需要改模型→端点绑定（会移动既有角色行为），未做。
- **W-3 EC-06 的同源判据只覆盖存在性**：路径/变量名/符号存在 ≠ 行为一致；
  runbook 里 live 步骤与 `curl` 片段**未实跑校对**（请求体形态）。
- **W-4 判据的启发式射程**：EC-04 的口径判据（引用-豁免是行级）、EC-06 的变量名判据
  （全大写 + 下划线才判）、EC-06 的白名单（人维护）与 demo 清单（完备性未判）——
  四处都写在各自判据的 docstring/记录里。
- **W-5 单个 cycle 的 W 条目未逐条复核**：本轮只复核「EC 级证据面」与「登记面一致」，
  六条 RECHECK 里的 30+ 条 W（逐 cycle 如实登记的边界）**逐字采信**，没有一条条重建实验
  ——它们是**已知边界的登记**，不是「已验证」的主张。
- **W-6 m0 是单机 Windows 结果**：CI（ubuntu + windows 六 job）是另一条独立证据，
  两者都绿才记 PASS；本轮的 m0 数字只代表本机。

## 结论

**PASS_WITH_WARNINGS**。EC-01…EC-06 全部 PASS，且证据在**两棵树**上一致：

1. **A/B/C 三层 65 checks** 在当前树与干净 checkout 上都 `PASS`——判据回的是**证据面**
   （文件在不在、用例在不在、登记一不一致），不是「记录里说 PASS」；
2. **合并判据套件 196 passed / 9 skipped**，两棵树同结论；9 个 skip 全部是
   live-gated / 环境门控用例的**如实跳过**（含 EC-04 主判据），不是掩盖；
3. **干净 checkout 封印成立**：3170 个跟踪文件、`git status` 干净、结论与当前树一致；
4. **GOAL 的 live 分支条款**：EC-04/EC-05 的 live 分支**未跑且已逐字登记**（W-1），
   未写成「已实测通过」；
5. **残余 6 条**如实登记（W-1…W-6），其中 W-1 是**能力边界**（需要用户注入凭据），
   W-2/W-3 是**已知缺口**（需要单独决策），W-4/W-5/W-6 是**射程边界**。

据此，GOAL-20260920-008 满足「终止与收口」的 ACHIEVED 条件：
EC-01…EC-06 全 PASS + 实跑证据 + 本收口复检（**PASS_WITH_WARNINGS**）+
`latest_recheck` 指向本文件 + 收口结论写明仍未处理项。
