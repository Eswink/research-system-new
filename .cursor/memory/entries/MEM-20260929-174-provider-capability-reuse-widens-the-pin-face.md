---
id: MEM-20260929-174
title: "登记一个「复用既有能力名」的 provider 会按 capability 反查同时扩宽多份协议的 pin 面 ⇒ 整表替换的夹具 pin 源必须同轮扩表；按压篡改必须篡成「语义合法」的另一个值，否则断言被别的分支满足（P4 实测假绿）"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.92
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-255-goal-027-ec01-real-literature-source-expansion.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-256-goal-027-ec01-europe-pmc-literature-source.md
supersedes: []
tags: [provider-onboarding, supply-chain-pin, fixture, press-test, scale-gate, goal-027, ec-01]
---

## 做了什么

新增第二个真实文献源（Europe PMC）并接进 provider 面。四条**实测**得到的事实：

- **复用一个既有能力名会同时扩宽多份协议的 pin 面**：编译期
  `protocol_compile/requirements.py::tool_requirements` 按 capability 反查 provider ⇒
  声明了 `literature.search` / `literature.read` 的 `europe_pmc` 同时进入
  `ai_ml_research_v0_4_0` / `human_gate_demo_v1` / `m12_reference_research_v1` /
  `real_experiment_research_v1` / `real_retrieval_research_v1` 五份协议的
  `provider_ids`；而 `tests/api/run_fixtures.py::replace_catalog_with_pins` 是**整表替换**
  （`tool_pack_digests={pid: "sha256:"+"1"*64 for pid in _PROVIDERS}`，
  `tests/api/run_fixtures.py:47`）⇒ 缺条目即 `SUPPLY_CHAIN_UNPINNED`（ERROR）⇒ 预检 FAIL
  ⇒ `freeze_manifest` 拒冻。实测：`tests/api/test_runs_api.py` **3 failed**（`run.failed`）。
- **单行扩表即复绿**：`_PROVIDERS` 追加 `"europe_pmc"`（该文件只此一行改动）⇒ `tests/api/`
  **580 passed**。
- **新增下界断言防静默落后**：新判据断言「目录内非 NATIVE provider 集合 ⊆ 夹具 pin 源」
  且**受判集合非空**（不是空真）；按压 P3（去掉该条目）⇒ 下界判据 1 条红 **且** run 链 3 条红。
- **规模门对 `tests/**` 同样生效**：新判据首版 **537 行**超 450 硬上限 ⇒ 拆出
  `tests/contracts/europe_pmc_support.py`（共享样本 + 装配辅助，**不含用例**），判据分两份。

## 为什么这样做

- **pin 面不是「新 provider 自己一条」**：能力名是**共享键**，承接方是**多对一**关系 ⇒
  新增承接者会把它带进**所有**声明该能力的协议。任何「整表替换」形态的 pin 源都必须同轮扩表，
  否则受害的是**既有**协议（实测是 PASS→FAIL 的真实回退，不是新功能的失败）。
- **下界断言不能用并集掩蔽**（承 [[MEM-160]] 同族）：只断言「新 provider 在表里」不够，
  要断言「目录内**每一个**非 NATIVE provider 都在表里」，否则下一个新 provider 会重演同一坑。
- **按压要压出「只有被测机制能拦」的形态**：P4 首压（删掉 `_read_args` 的 `argument_digest`
  比对）**没有判红**——原判据篡改成的参数对 `literature_search` 本身就非法（缺 `query`），
  于是删掉 digest 校验后仍被「入参非法」那条分支抛出的同一异常满足。**按压假绿**。
  修法：篡改值换成**语义完全合法**的另一种参数（另一个真 PMID 的检索串），并**额外断言
  `transport.count == 0`**（只有触网前的 digest 校验能拦住它）；重压即红
  （`DID NOT RAISE`）。
- **`toolpack_*.yaml` 的 `digest` 是声明值**：全仓只有
  `services/api/catalog.py::_load_tool_pack_digests` 读它（只读、剥 `_vN`）、preflight 的
  `_is_pinned_digest` 只做 `Digest.parse` 形状校验；内容重算只发生在 install 生命周期。
  实测既有 `toolpack_ncbi_eutils.yaml` 声明值 `947cbb22…` **既不等于**文件字节 sha256
  （`d127e4dd…`）**也不等于**规范化 JSON 重算值（`70c3f0ad…`）⇒ 新 pack 照**字段形态**写、
  把来源配方写进注释，**不要**用「内容寻址」措辞描述它。

## 怎么做与复现

1. 诊断 pin 覆盖面（只读，不改树）：
   `PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal027_c1_diag_pins.py`
   ⇒ 打印目录内 provider、`tool_pack_digests`、每个非 NATIVE provider 的 pin 状态、
   以及按 capability 反查出的 provider 列表。
2. 查真值来源：`services/api/catalog.py::_load_tool_pack_digests`（读 YAML）、
   `packages/application/preflight/checks.py::_provider_trust_findings`（查 `plan.tool_pack_digests`）、
   `packages/application/protocol_compile/requirements.py::tool_requirements`（按 capability 反查）。
3. 按压四条的配方与留档见 `scratch/goal027-c1-press/press-matrix.log`
   （2825 字节 / `CR` 计数 0 / 二进制写盘）；每条都记了基线 raw `sha256` 与复原后的值。
4. 规模门自查：单文件 ≤ 450 行（`splitlines()`）、单函数 ≤ 50 行（`end_lineno - lineno + 1`），
   对 `tests/**` 同样适用（`tests/tooling/test_python_source_limits.py`）。

## 适用边界

- 结论落在**本仓的 provider 登记面与 run_ready 夹具**上；换仓需重核
  `_PROVIDERS` 是否仍是整表替换、以及 capability→provider 反查是否存在。
- **「篡改要篡成合法的」这条是通用按压纪律**，不限本 provider：任何「非法入参」与
  「防篡改」两条分支共存的地方，用非法值按压都会假绿。
- 出口执法（`network_domains` 白名单 + 保留类判据）本轮**只覆盖新 provider**：
  仓内没有全局出口网关，其它 provider 仍未受此判据约束 ⇒ 不得据此宣称「全仓出站已受控」。
- `digest` 是声明 ⇒ 它证明「已按 pin 先行登记」，**不**证明「包内容与声明字节一致」。

## 来源

- `PLAN-20260929-255`（GOAL-027 EC-01）与 `RECHECK-20260929-256`（§4 / §6 / §7 / §9）；
- 留档：`scratch/goal027-c1-press/press-matrix.log`、`scratch/goal027_c1_diag_pins.py`、
  `scratch/goal027_c1_pin_digest.py`、`scratch/europepmc-sample.json`（线上实测样本）；
- 相关代码：`adapters/research_tools/europe_pmc*.py`、`examples/contracts/toolpack_europe_pmc.yaml`、
  `examples/config/tool_providers.yaml`、`tests/contracts/test_europe_pmc_*.py`、
  `tests/api/run_fixtures.py`；
- 同族记忆：[[provider-registration-expands-provider-ids]]（本条的**建档版**：能力名复用 ⇒
  pin 面扩宽，本条补上了实测的**受害面**与**下界断言**形态）、
  [[toolpack-builtin-pin-is-declaration-only]]（`digest` 是声明的同族结论）、
  [[press-tests-need-real-failures-not-skips]]（按压纪律：判据不能被 skip 或别的分支满足）。
