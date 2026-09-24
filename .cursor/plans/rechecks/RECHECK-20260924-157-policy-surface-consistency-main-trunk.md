---
id: RECHECK-20260924-157
plan_id: PLAN-20260924-155
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: independent-recheck-script + root-agent-goal-014-ec01
baseline_ref: add2c37（cycle 1 的 derive 提交；功能改动前的树）
checked_head: 当前树（cycle 1 功能提交 4bfa6d0）+ 独立脚本 scratch/verify_goal014_c1.py
---

# RECHECK-20260924-157 — GOAL-014 EC-01 策略面一致性主干（cycle 1）

## 检查范围

`W-A` / `W-C`（同一协议在两套装配下两个结论）是否被**从根上消灭**：
① 真实控制面（`NativePolicyEvaluator` + `policy.yaml`，**无** `preflight_override`）
对 `sort_analysis_v1` 的 preflight 是否**不再 `FAIL`**、策略维度是否清零；
② live / run-ready 装配的结论是否与之**一致**（同为 `WARN` **且都可冻结**）；
③ 授权边界是否守住（只多一条 `evidence.read` 的 allow；镜像契约两处**真同步**）；
④ 成对反证是否**先红后绿**、按压后是否**逐字节还原**；
⑤ 两条因此变成假的**记录性陈述**是否已对齐（而不是被削弱）。

## 检查结果

### 一、两套装配的结论（实测，两份样张逐字）

装配由**产品入口**决定（D-1）：`services/api/run_execution.py` 的 `execution_inputs()` 在
`deps.preflight_override is None` 时走 `_live_preflight()`（真实控制面），在场时用该上下文
（live / run-ready 装配）。判据**不在产品入口之外另开一条路**。

| 面 | 改动前（基线 `add2c37`） | 改动后（当前树） |
| --- | --- | --- |
| 真实控制面 `status` | **`FAIL`** | **`WARN`** |
| 真实控制面的策略判词 | `[POLICY_DENIED] phase:review: policy denied capability evidence.read: used default policy effect` + 两份 `TASK_CONTRACT_MISSING` | 无策略判词；`TASK_CONTRACT_MISSING` 亦消失 |
| live 装配 `status` | `WARN` | `WARN` |
| `SAME_STATUS` | **`False`** | **`True`** |

样张：`scratch/goal014-c1-criterion-red.txt`（改前——判据在基线树上**红**的那一轮，
判词逐字含 2× `TASK_CONTRACT_MISSING` + 1× `POLICY_DENIED`）、
`scratch/goal014-c1-both-assemblies-after.txt`（改后，`SAME_STATUS = True   A=WARN  B=WARN`）。

**`FAIL` 有第二个来源（本 cycle 实测新发现，已登记为 GOAL 的 `F-9`）**：`sort_analysis_v1`
引用的两份 task contract 此前**只存在于测试夹具**（`tests/api/run_fixtures.py` 的
`replace_catalog_with_pins()` 用 `setdefault` 运行期注入），而该协议是**产品面可选模板**
（`services/api/routers/protocol_drafts.py` 的 `_TEMPLATE_SOURCES` 第 1 条）⇒ **只放行策略
不足以**让它脱离 `FAIL`，EC-01 与 EC-02 都会卡住。处置与授权面的登记见第四节。

### 二、可冻结面（「WARN **+ 可冻**」的那一半）

判据只断言 `status` 相等是不够的。实测**两套装配都能冻结**，且留痕覆盖**同一批四对**
`(phase_id, capability)`：

| 装配 | 冻结 | 留痕 | 逐条 `decision` |
| --- | --- | --- | --- |
| 真实控制面 | **OK**（`frozen_at` 非空） | 4 条 | `code.execute`/`workspace.write.code` = `ALLOW_WITH_CONSTRAINTS`；`workspace.read`×2 = `ALLOW` |
| live / run-ready | OK | 4 条 | 四条皆 `ALLOW`（该装配的 Fake 求值器全放行） |

样张：`scratch/goal014-c1-freeze-both-arms.txt`。**`decision` 的差异是装配差异的正确表现**
（两套用不同求值器，各记各的判定），因此判据只断言**结论**与**对集合**、**不**断言
`decision` —— 这条口径写在 `test_the_real_control_plane_warn_is_freezable` 的 docstring 里，
不是散在记录里。

### 三、授权边界（独立脚本 A/B 组，逐条实查）

- `policy.yaml`：`default_effect` 仍 `DENY`；`allow` 里 `evidence.read` **恰好一条**且
  `scope: project`；`deny` 的能力面仍 `(network.public,)`、动作面仍
  `(MOUNT_DOCKER_SOCKET, PRIVILEGED_CONTAINER)`；`require_approval` 仍 5 条；
  `allow_with_constraints` 仍 3 条 —— **全部逐条未动**。
- `policy_check.py`：`_CAPABILITY_SCOPE` 共 **7** 条且含 `("evidence.read", "project")`；
  **`_GATE_CAPABILITY_SCOPES` 里没有它**（镜像判据的第二条断言要求如此）。
- **镜像一致性判据原件未改**（`tests/application/test_m2_audit.py` 不在本 cycle 的改动集里）。
- 出厂目录 `examples/contracts/task_contracts.yaml` 补入两份契约，字段齐（`version` /
  `purpose` / `required_capabilities` / `output_schema` / `acceptance_criteria` /
  `retry_policy` / `timeout_seconds`）；`tests/api/run_fixtures.py` 的 `setdefault` **仍在**
  （撤回纪律的检查点未失锚）。

### 四、成对反证（先红后绿，各自可复跑）

| 反证 | 按压 | 结果 | 样张 |
| --- | --- | --- | --- |
| ① 撤 allow | 从 `allow` 摘掉 `evidence.read`，`_CAPABILITY_SCOPE` 相应撤回 | 真实控制面判据**红**，判词逐字 `[POLICY_DENIED] severity=ERROR phase:review: policy denied capability evidence.read: used default policy effect`；镜像判据仍**绿**（证明撤回是**一致**的） | `scratch/goal014-c1-press1-allow-withdrawn.txt` |
| ② 镜像不同步 | **只**从 `_CAPABILITY_SCOPE` 摘掉那一对 | 镜像判据**红**：`AssertionError: assert … Extra items in the right set: ('evidence.read', 'project')`（`test_m2_audit.py:268`） | `scratch/goal014-c1-press2-mirror-desync.txt` |

**逐字节还原**：按压后 `git diff --stat examples/config/policy.yaml
packages/application/preflight/policy_check.py` **为空**（两个被按压的文件都回到提交态）；
还原后判据与镜像复跑**全绿**。

反证②顺带证明了 **F-5**：scope 表被摘掉后，`allow` 规则因 scope 不匹配而失效 ⇒
该能力在执行路径上再次落回 `default_effect`（判据同时转红）。**这证明 scope 表是真实求值
路径上的承重件，而不是装饰**。

### 五、记录性陈述对齐（两处旧事实，未被削弱）

| 文件 | 旧陈述 | 处置 |
| --- | --- | --- |
| `tests/application/preflight/test_policy_allowed_execute_freeze.py` | `_protocol_policy()` docstring 说 `evidence.read`「产品策略尚未放行」并运行期注入 | 改写为「放行后该分支是**幂等兜底**」；`any(...)` 分支现在返回**策略本体**，留痕断言从而读的是产品策略。**断言一字未改** |
| `tests/e2e/test_ec02_experiment_live.py` | 边界段说真实控制面「判 `DENY`」⇒ 该协议 `FAIL`（`W-A`） | 就地标注「GOAL-20260924-014 EC-01 更新」为新事实；**并如实保留**本条真正证明的东西（留痕来自 override 一侧的求值器，本文件不因修复而扩大证明力） |

### 六、本地门

- **判据**：`tests/application/preflight/test_policy_surface_consistency.py` **5 passed**
  （改前 4 failed）；`tests/application/preflight/` + `test_m2_audit.py` **28 passed**；
  受影响套件（`tests/loaders/` + `run_chain_capability_exposure` + `dry_run_no_side_effect` +
  `catalog_merge` + `sandbox_experiment_seam`）**81 passed**；e2e 离线三条 **9 passed / 1 skipped**。
- **出站**：全部判据轮次 `blocked 0`；判据自身 `judged 0`（零出网）。
- **m0**：`scratch/goal014-c1-m0.log` —— **22/23**，`python/tests` **4418 passed / 18 skipped /
  0 failed**，其余 21 项全 `PASS`。唯一未绿项 `framework/validate_bundle` = **环境型残余
  `R-F3`**（并发写者的 gitignored `scratch/self-governance-bootstrap-prompt.md` 被纯文本
  链接扫描读成本地链接），判词逐字：`Markdown 本地链接不存在:
  scratch\self-governance-bootstrap-prompt.md -> [A-Za-z]:\\|/(home|mnt|data|Users`。
  与 GOAL-013 cycle 6 的 as-is 跑法**同形**（同一项、同一原因）。
- **用例数归因（不留未解释的差）**：上一基线（GOAL-013 c6）4413 passed / 18 skipped
  ⇒ 本轮 **4418 / 18**，差 **+5** = 本 cycle 新增的**正好 5 条**判据；skipped 数不变。
- **独立复检脚本**：`scratch/verify_goal014_c1.py`（只读、标准库、不 import 仓库代码、
  由**调用目录**定 ROOT）⇒ `checked=45 failures=0`。

## 判据性质披露（必须读的一段）

- **能被什么按压**：撤 allow（策略维度立刻红，反证① 实测）、只改镜像一处（镜像判据红，
  反证② 实测）、摘 scope 表（执行期路径失效，反证② 的副产物）。
- **不能被什么按压**：改**非策略**面的 finding 文案 / 端点 health / 供应链事实 ——
  本判据只读 `status` 与 `POLICY_DENIED`，两套装配在这些维度上**本就不同源**（D-3），
  断言 findings 逐字相等会把它误判成不一致。
- **语义正确性不由本判据承载**：本判据是**结论一致性**判据；「真实控制面能不能真的跑完一个
  研究闭环」由 EC-02 的真实 run 承载（**尚未开始**）。

## 结论

**EC-01 PASS**：真实控制面不再是 `FAIL`、策略维度清零、与 live 装配**同结论（`WARN`）且
都可冻结**，`W-C` 消灭；两条成对反证**先红后绿**且按压文件**逐字节还原**；授权边界逐条守住
（只多一条 `evidence.read` 的 allow，`default_effect` / `deny` / `require_approval` /
`allow_with_constraints` 全部未动，镜像契约两处真同步、镜像判据原件未改）。

**警告一条（`R-F3`）**：本机 as-is m0 停在 **22/23**，唯一未绿项是**仓库外**并发写者的
gitignored 在制品造成的 `framework/validate_bundle`，与本 cycle 改动无关（CI 检出无 `scratch/`）。
**未转绿前不得声称本地全绿**；本地 23/23 的终局行留给 EC-05 收口复检。

## 授权面的一处如实登记（不是静默扩展）

本 cycle 对 GOAL-014 的授权做了**一处具名扩展**（已在 `PLAN-20260924-155` 的
`authorization.ref` 内写明，回退面 = 单 WP 的提交）：把两份 `sort_analysis_*` 契约从
**测试夹具的运行期注入**提升为**出厂目录声明**。

- **为什么必需**：EC-01 的判据「真实控制面**不再是 `FAIL`**」经实测有**两个**独立来源，
  只放行策略不消除第二来源；EC-02 的真实 run 同样会死在冻结前。**不做这一处，
  EC-01 与 EC-02 都不可达**。
- **它改的是什么**：**声明面**（协议引用的契约在出厂目录里不存在）——正是本 GOAL 要消灭的
  「声明与现实漂移」那一类，与 W-B 的处置同类。
- **它没有改什么**：**不触碰任何策略面**；**不属** AGENTS.md §9 默认 deny 的任一条；
  **不**新增依赖、**不**改上游 pin、**不**动 Accepted ADR / Canonical State 边界。
- **风险与已数的消费者**：`examples/contracts/task_contracts.yaml` 是共享契约文件 ⇒
  建档当日先数消费者：`grep -rn TASK_CONTRACT_MISSING tests/` **无**消费者断言该失败形态；
  `test_load_task_contracts_*` 全是**按键取值**、无计数断言；`test_example_contracts_declare_
  only_honored_failure_policy_keys` 要求 `unhonored == ()`，新契约按此写（不含 `failure_policy`）。
  `tests/architecture/python/test_run_chain_capability_exposure.py` 编译**全部**协议，
  断言的是 `capability_execution` 与 `result.plan is not None`，实测仍全绿。
- **若判定越界**：单独 revert `9bba68d` 即可回退（该提交只含这一份文件）。

## 仍未处理项（如实登记）

- `W-A` / `W-C`：**由本 cycle 消灭**（判据在册、反证成对）；GOAL-012/013 的记录**原样保留**
  （历史事实，不返工）。
- `R-M1`（Mimosa 钩子侧未得完整结论 ⇒ **不得**宣称项目安全）、`R-D1`（23 条依赖告警）、
  `R-B1`（路径 (B) 已否证）、`R-N1`（30 条非 ASCII 路径豁免）、`R-F1` / `R-F2`：**原样承继**。
- `R-F3`：本机 as-is m0 = 22/23（**唯一警告**，原因见上）；CI 不受影响。
- **13 条人工面**：原样保留（第 3 / 12 项已完成、第 13 项已豁免，按事实标注）。
- **EC-02 未开始**：真实控制面端到端 run（真实 LLM + 真实检索 + 真实实验）在其后。
- **EC-03（双向差集）的起点数字**已实测（声明面并集 41 / policy 提及 14 / 交集 10 /
  声明未提及 31 / 提及未声明 4），**含一处判据陷阱**（朴素正则会误收 `network_domains`
  域名串）——留给 EC-03 的 cycle 处置。
