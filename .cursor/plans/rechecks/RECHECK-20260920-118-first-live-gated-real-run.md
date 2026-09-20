---
id: RECHECK-20260920-118
plan_id: PLAN-20260920-118
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle5
baseline_ref: 8b85f03
checked_head: 8c9d67c
---

# RECHECK-20260920-118 — 首次 live-gated 真实 run（EC-04 复检）

## 检查范围

不采信实施叙述：按 EC-04 判据在**当前树**上真跑，逐条做**先红后复原**的反证。
检查面：

- **门控**：默认关（runtime 未配置 / Fake / 无凭据三种情况都要关），且**关门即零出站**；
- **结论口径**：`REPEATABLE_CONFIGURATION` / `NOT_VERIFIED` 两态穷举，「完全可复现」在
  **类型上不可表达**；口径面必须出现「可重复配置」，**肯定式**越级宣称判红；
- **skip ≠ PASS**：无凭据产出结构化 `NOT_VERIFIED` 记录并点名 `credential_ref`；
  跳过不被任何判据当成通过；
- **指纹诚实**：必填项缺失降级为 `NOT_VERIFIED` 并点名缺项；provider 项缺失只登记不降级；
- **live 分支**：无凭据 ⇒ 真实 run 不跑，如实 skip（**skip 不是 PASS**）。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 词表 | `tests/domain/test_reproducibility_verdict.py`（**4 passed**：成员集合**恰好**两态 + 成员名不含 `REPRODUCIBLE/FULL/EXACT/IDENTICAL/PROVEN/CONFIRMED/GUARANTEED` 等越级痕迹 + 最强档只能含 `CONFIGURATION` 不含 `MODEL` + `NOT_VERIFIED` 与已验证态不同一） | PASS |
| AC-02 run 记录 | `tests/application/model_relay/test_live_run_record.py`（**13 passed**：skip 记录 `is_verified=False` 且点名 `credential_ref`；skip 必填理由；`NOT_VERIFIED` 无理由构造被拒；三个必填指纹项**逐个**参数化验证「缺失 ⇒ 降级 + 点名」；非终止态 ⇒ 降级；provider 项缺失只登记不降级；payload 暴露缺口；负数 usage 被拒） | PASS |
| AC-03 live 用例与门 | `tests/e2e/test_ec04_live_first_run.py`（**1 passed / 1 skipped**）：跳过的那条是 live 主判据（门关着，见下节）；通过的那条断言**本机门确实是关的**且理由点名未满足条件 | PASS（离线部分） |
| AC-04 离线可判 | `tests/e2e/test_ec04_live_gate_offline.py`（**13 passed**：runtime 未配置/配 Fake/凭据缺失/凭据为空四种关门；关门理由**列出全部**未满足条件；门**不物化凭据**（`resolve` 被禁仍判开门）；**零出站**（`socket.socket` 被拔掉仍能判门并产出 skip 记录）；skip ≠ PASS 三条；门控存在性两条（live 模块带 `requires_live_llm` + 导入不开 socket）） | PASS |
| AC-05 口径同源 | `tests/architecture/python/test_reproducibility_wording.py`（**5 passed**：六个口径面必须出现该档；扫描面非空（**没扫成 ≠ 没命中**）；全仓**无**肯定式越级表述；规则自检含「引用放行 / 否定句放行 / 肯定式判红 / 行尾不误判为引号」四条） | PASS |
| AC-06 反证 | F1–F5 全部**先红后复原**（见下表） | PASS |
| AC-07 门禁 | 定向 `38 passed / 2 skipped` + 治理 `validate.py` / `validate_bundle` / `docs_consistency_check` + **m0 全量 23 项**（`PASS: profile=m0; 23 deterministic checks`；**4190 passed / 12 skipped**，499.34s，冻结树 `7ce833f`；cycle 4 为 4146/11 ⇒ 净增 44 条判据、+1 skip = 新增 live 分支的如实跳过） | PASS |

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | `not_verified_live_run_record` 的结论改成 `REPEATABLE_CONFIGURATION`（把跳过说成已验证） | **3 failed**（记录判据 2 条 + 离线门判据 1 条） | 26 passed |
| F2 | `build_live_run_record` 不再收集缺失项（留白冒充「探了没问题」） | **6 failed**（必填项 ×3 参数化 + provider 项 ×2 + payload 缺口） | 13 passed |
| F3 | 门不再要求凭据可解析（无凭据也放行） | **4 failed**（缺凭据关门 ×2 + 完整点名 + skip ≠ PASS） | 13 passed |
| F4 | 口径面的 `≠` 改成 `=`（否定句变肯定句） | **1 failed**（越级表述判据） | 5 passed |
| F5 | 口径面删掉「可重复配置」 | **1 failed**（必填口径面判据） | 5 passed |

五处注入均以**逐字节还原**收尾（每步 `git diff --quiet -- <path>` 复核「与 HEAD 一致」，
脚本 `scratch/ec04-falsification.py` 把这一步作为**失败条件**而不是提示）。

### 本地门禁拦下的三处（G1–G3，均按缺陷修，未动门禁与断言强度）

| # | 拦下它的检查 | 缺陷 | 修法 |
| --- | --- | --- | --- |
| G1 | m0 `python/typecheck`（fail-fast，第一轮） | 新判据里写了两条**字面量**枚举成员的同一性/取值比较（`X is not Y`、`X.value != Y.value`）⇒ mypy `comparison-overlap`（已收窄成 `Literal`）。**与 cycle 4 的 G1 同族**（连续两轮被同一陷阱拦下） | 改成运行期枚举派生：`list(Enum)` + 成员数 + `{m.value}` 去重计数（`97380c1`）；语义不变，F1 复跑仍红 |
| G2 | m0 `python/tests` | 新代码两处**函数超 50 行**（`build_live_run_record` 73 行；live 用例主体 70 行） | 各自拆出私有助手（`_fingerprint_facts` / `_assess`；`_live_run_facts` / `_execute_live_run` / `_record_from` / `_assert_four_segments`）⇒ 三个文件**无超 50 行函数**（`7ce833f`） |
| G3 | m0 `python/tests`（6 failed：`test_fork_override` ×3、`test_full_adapter` ×1、`test_agent_runtime_contract` ×2） | **跨套件污染**：EC-04 的 live 用例 `from tests.e2e.test_ec03_real_runtime_offline_chain import …` 让同一文件被**两个模块名**加载（pytest 的 top-level `test_ec03_…` + 我的 `tests.e2e.test_ec03_…`）⇒ SDK 的 `Action` 子类被定义两次，判别联合在**同进程后续任何事件 round-trip** 上抛 `Duplicate class definition for openhands.sdk.tool.schema.Action`——fork 路径首当其冲 | 把共享装配抽到**单一名**模块 `tests/e2e/live_run_support.py`（EC-03 与 EC-04 都从它 import）；同进程复跑该组合 **57 passed / 8 skipped**（`4f54e53`） |

G3 是本节最值得记的一条：它与 GOAL-007 收口时修的污染**同族但不同因**——
那次是**函数内局部类**（`<locals>` 限定名），这次是**同一文件两个模块名**。
两次都只在「两个套件同进程」时暴露，而 m0 的字母序恰好让它们同进程。

### live 分支：**如实 skip**（不是 PASS）

- 本轮实跑复核（只看存在性、**未读值**）：`LLM_MAIN_KEY` / `DEV_LLM_API_KEY` /
  `RESEARCHOS_LIVE_E2E_KEY` / `RESEARCHOS_LIVE_E2E_ENDPOINT` / `OPENAI_API_KEY` /
  `ANTHROPIC_API_KEY` **全部 absent**；`RESEARCHOS_AGENT_RUNTIME` 未配置。
- 因此**真实 run 一次都没跑**：门在两条上都关着（runtime 未配置 + 凭据不可解析），
  `tests/e2e/test_ec04_live_first_run.py` 的主判据**跳过**，产出的是 `NOT_VERIFIED` 记录。
- 本 cycle 的绿全部来自**离线判据**。它能证明「门开/关的判定正确、skip 不会伪装成通过、
  口径词表挡得住越级宣称」；**不能**证明「真实端点上的 run 会成功、指纹会齐、归账会正向」。

## Warnings（不阻断，如实登记）

- **W-1 真实 run 未发生**（能力边界）：EC-04 的靶心是「一次真实 run」，本机无凭据 ⇒
  靶心**未命中**。判据只覆盖了离线可判部分；live 路径（probe → 终态 → 归账 → 制品与证据）
  从未被执行过，其中的 API 形状/时序问题**只会在第一次真跑时暴露**。
- **W-2 live 路径的模型绑定不是 anthropic 面**：目录里所有模型都绑 `main`
  （`OPENAI_COMPATIBLE`）；登记进目录的 `agnes-anthropic` 端点只由 probe 段单独驱动。
  ⇒ 「一次 run 自身消费 ANTHROPIC 面」需要改模型→端点绑定（会移动既有角色行为），
  本轮**没做**，已在文档与测试 docstring 里点名。
- **W-3 门只看两个条件**：runtime 配置 + 凭据可解析。策略允许（Policy）、预算可预留、
  端点健康等 preflight 条件本轮**没有**进门的判据——它们由既有 preflight 负责，
  门只回答「该不该走 live 分支」。这是刻意的分工，但「门开着 ≠ run 一定跑得通」。
- **W-4 口径判据的引用-豁免是行级启发式**：把肯定式宣称加引号写出来可以绕过。
  判据挡的是默认漂移，不是恶意规避（已在判据 docstring 里写明射程）。
- **W-5 记录的 usage/制品字段靠调用方填**：`LiveRunRecord` 只做类型与「负数」校验，
  不校验「模型 token 数是否等于 ledger 真实值」——live 判据里才有那层断言，
  而 live 判据本轮没跑（见 W-1）。
- **W-6 `NOT_VERIFIED` 的用途边界**：它同时覆盖「无凭据」与「跑了但没终止/缺指纹」。
  两者在 `reason` 里可区分（`not terminal` / `missing fingerprint fields` /
  `credential_ref=…`），但**同一枚举值**。若要机器分流，需要另加来源字段（未做）。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的**离线可判部分全部成立**，每条关键判据都有独立反证
（F1–F5）：

1. **门默认关闭且零出站**：四种关门情形可判，关门理由列出**全部**未满足条件；
   门**不物化凭据**（只问 `has`）；拔掉 socket 仍能判门并产出记录；
2. **skip 不是 PASS 被两处独立钉住**：记录层（`is_verified=False` + `NOT_VERIFIED`
   必须有理由 + F1）与门层（`skip_record_for_gate` 对开着的门直接拒绝 + F3）；
3. **口径从文案升级为词表**：两态穷举、越级宣称在类型上不可表达（F5），
   并且全仓**肯定式**越级表述有判据把守（F4，否定句与引用放行）；
4. **指纹诚实**：必填项缺失降级并点名（F2），provider 项缺失只登记不降级；
5. **残余 6 条如实登记**，其中 **W-1（真实 run 未发生）是能力边界**——本机无凭据，
   EC-04 的靶心要等凭据注入后才能命中；W-2（模型绑定不是 anthropic 面）是**已知缺口**，
   需要单独的绑定决策。
