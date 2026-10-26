---
id: PLAN-20261026-097
slug: goal-097-productive-entry-and-novelty
title: GOAL-097 六个 EC —— 产品入口真跑完整链 + 创新点两面
status: DONE
created_at: 2026-10-26
updated_at: 2026-10-26
parent_goal: GOAL-20261026-097
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261026-097-goal-097-productive-entry-and-novelty.md
memory_entries:
  - MEM-20261026-231
---

# PLAN-20261026-097 — 产品入口真跑完整链 + 创新点两面

- **GOAL**: `GOAL-20261026-097`（序 65）
- **状态**: ACTIVE
- **能力域**: 实验

## 一句话

把上一轮只在 e2e 手工装配里成立的六相链接进**两个产品组合根**（装配期零 Docker 连接、
契约 pin 的脚本/镜像真的生效），并让「创新点」在**声明面与评审面**同时站住
（声明必须命中本 run 检索到的标识；`novelty_reviewer` 真的激活、真的收到被评对象）。

## 为什么是这两件事

用户的目标是「给一个方向，剩下全自动」。上一轮证明了链路能在**一次 run 内**走完，但：

1. 从**产品入口**跑，`experiment` 与 `report` 两个相会**点名拒绝** —— 两道缝
   （`experiment_task` / `report_task`）在 `OrchestrationDependencies` 里早就有，工厂也早已
   存在，但**只有测试在接**（`rg "experiment_task|report_task" services/api/composition.py`
   零命中）。而「自动设计实验」这件事在产品入口上因此根本不可达。
2. 「创新点」在域层**结构性缺席**：`rg -iln "novelty" packages/ services/ adapters/` 零条；
   `novelty_reviewer` 是死配置（无 `review_panel_role` ⇒ `NONE`、无 agent 绑定、无协议点名）。
   一项研究从未被要求说明「它与最近的前人工作差在哪」，也从未被任何模型判过。

## 阶段与产出

| 阶段 | 产出 |
| --- | --- |
| EC-01 接缝 | `services/api/executor_wiring.py`（两道执行缝 + 运行链检索面）、`services/api/experiment_factories.py`（惰性/急切两个工厂）、`services/api/retrieval_wiring.py`（出厂检索 provider 与两步调用）、两个组合根接线 |
| EC-03 声明优先 | `experiment_support.declared_or_assembled`（契约 pin 优先、装配面兜底）+ `_DeferredExecution`（按镜像惰性取后端） |
| EC-04 创新点声明面 | `examples/protocols/direction_to_report_v2.yaml`（七相）、`novelty_claim_proposal` 合约、`packages/application/run_orchestration/novelty_claim.py`、`novelty_claim_step.py` |
| EC-04 创新点评审面 | `roles.yaml`（`review_panel_role: REVIEWER`）、`agents.yaml`（`novelty_a` → `minimax-m3`）、`models.yaml`（第三个第三方模型）、`team_templates.yaml`（进入 `standard`） |
| EC-02 真跑 | `tests/e2e/test_productive_entry_runs_the_whole_chain.py` + 取证文件 |
| EC-05 收口资产 | `tools/verify_goal097_closeout.py` + `tools/goal097_closeout_assertions.py` |

## 判据（每条都带反证臂）

- `tests/api/test_product_roots_carry_the_execution_seams.py`（EC-01，7 条）
- `tests/api/test_contract_pinned_experiment_spec_takes_effect.py`（EC-03，9 条）
- `tests/contracts/test_direction_to_report_v2_novelty.py`（EC-04，14 条）

## 已知的结构性边界（如实登记，不掩盖）

- **REST provider 在默认装配下的健康探测会出网** ⇒ 预检 `TOOL_HEALTH_UNPROVEN` 是 WARNING
  且**没有接受通道** ⇒ `freeze_manifest` 拒冻。这条语义不一致在本轮**之前**就存在
  （`examples/protocols/real_retrieval_research_v1.yaml:11-19` 已登记），本轮**不改门禁**；
  出厂检索 provider 因此只接**运行链执行面**，`ApiDeps.tool_providers` 保持空（预检探测面
  与今天逐字一致）。改这条要用户拍板（动门禁）。
- 实验**脚本**仍是预置脚本之一（契约可 pin，但不是为新问题生成的实验）—— 下一轮候选。

## 验收条件

- [x] EC-01：两个产品组合根都接上实验缝 / 报告缝 / 运行链检索面，装配期零 Docker 连接
      （正 + 反两向判据；9 条用例全过）
- [x] EC-02：从产品入口（`assemble()` 的 deps，不补缝）跑通七相链 —— `SUCCEEDED`，
      `missing_phase_artifacts: []`，novelty 声明命中真实检索标识且两位评审者都引用了它
- [x] EC-03：契约 pin 的 `script`/`image` 真的生效（声明优先、装配面兜底；两向 + 反证；9 条）
- [x] EC-04：创新点两面都在（七相编译零 ERROR + 声明落检索 + 角色激活 + 三评审目标互异；15 条）
- [x] EC-05：`tools/verify_goal097_closeout.py` + 断言集在树并登记（78 条判词全过）
- [x] EC-06：上一轮三处记录更正逐条核对未回退

## 实施清单

1. `services/api/executor_wiring.py` / `experiment_factories.py` / `retrieval_wiring.py`（新）
2. `services/api/composition.py` / `pg_composition.py` / `experiment_support.py` /
   `session_tool_support.py` / `settings.py`（接缝 + 惰性代理 + TTL 可配）
3. `examples/protocols/direction_to_report_v2.yaml`（七相）
4. `examples/contracts/task_contracts.yaml`（`novelty_claim_proposal` +
   `retrieval_report_from_the_run_chain`）
5. `examples/config/{roles,agents,models,team_templates}.yaml`（评审面三处 + 第三模型）
6. `packages/application/run_orchestration/novelty_claim.py` / `novelty_claim_step.py`（新）
7. 判据：`tests/api/…seams.py`（9）、`tests/api/…pinned…py`（9）、
   `tests/contracts/…novelty.py`（15）、`tests/e2e/…whole_chain.py`（真跑）
8. 收口资产：`tools/verify_goal097_closeout.py` + `tools/goal097_closeout_assertions.py`

## 证据

- `.cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt`（真跑读数）
- `.cursor/plans/goals/evidence/M0-WITNESS.json`（全量 m0 见证）
- `.cursor/plans/rechecks/RECHECK-20261026-097-goal-097-productive-entry-and-novelty.md`
- `tools/verify_goal097_closeout.py --root . --verdict-only` ⇒ 78 PASS / 0 FAIL

## 影响报告

- **Domain / API / schema**：无 DTO 变更（`settings` 新增可配项，不是 API 面）；协议与合约是**新增**
  文件与**新增**条目，既有条目一字未改。
- **安全 / 凭据**：无新增凭据面；`sk-` 仍只进 gitignored `.env` 的 `LLM_MAIN_KEY`。
- **兼容性 / 迁移**：`experiment_support._governed_executor` 签名保持单参（既有判据的
  lambda 替换仍有效）；`SandboxExperimentAssembly` 新增可选 `execution_factory`（缺省 `None`
  ⇒ 逐字沿用 `execution`）。`composition.py` 448/450 行、`experiment_support.py` 450/450。
- **上游版本**：无新增依赖。
- **下一项任务**：序 66 候选（实验脚本由方向决定 / 检索结果驱动下一轮问题 / 归档面三处漏洞）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-26 | IN_PROGRESS | 开工：读数器拒绝残余，按正文逐条处置 |
| 2026-10-26 | DONE | 六个 EC 全达成；真跑 `SUCCEEDED`；78 条收口判词全过 |
