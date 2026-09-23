---
id: RECHECK-20260923-143
plan_id: PLAN-20260923-142
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-verify-script + root-agent-goal-012-ec02
baseline_ref: c6cf330
checked_head: dcade8c
---

# RECHECK-20260923-143 — 真实实验执行链跑到终态（GOAL-012 EC-02 / PLAN-142）

## 检查范围

**不采信本 cycle 的自我陈述**，分三层各自成立：

1. **独立复检脚本** `scratch/verify_goal012_c2.py`——**只读 / 只用标准库 / 不 import 仓库代码**，
   在当前树与**基线树**（`git worktree` 到 `c6cf330`，即本 cycle 之前的 tip）上各跑一遍；
2. **实跑层**——离线判据 / 真实一次 run / 套件 / m0 的原始输出（逐条落 `scratch/`）；
3. **样张的数据层断言**——live 样张以 JSON 读回（不经过被测代码），判终态、留痕、实验产物、
   证据来源与归账。

## 检查结果

### 一、独立复检脚本（两棵树成对）

| 树 | 结果 | 说明 |
| --- | --- | --- |
| **当前树**（`dcade8c`） | `checked=29 failures=0`（exit 0） | 29 条断言全绿：授权边界 7 + 判据成对 6 + 夹具缺省不变 3 + 样张数据层 11 + 环境/按压 2 |
| **基线树**（`c6cf330`，本 cycle 之前的 tip；`git worktree` 到仓外） | `checked=29 failures=10`（exit 1） | **判据不空转**：10 条红恰为本 cycle 的新增面（两个判据文件缺失、`with_sandbox_experiment` 的 `runtime` 可选参数、惰性工具按名分名）；而**「不得放宽」那七条**（`classify_risk` / `code.execute` 仍在 `allow_with_constraints` / 策略面未补 `evidence.read` / 通道只认 `TOOL_RISK_ELEVATED`+EXECUTE / 空交付物仍被拒 / 出站判据仍在 / run-ready 夹具缺省 runtime 未改）**在两棵树上都绿** |

⇒ **成对成立**：新判据在改动前红、改动后绿；授权边界**两棵树同结论**。

### 二、离线判据（`requires_docker`，零出网）

`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec02_experiment_chain_offline.py -q -rs`
⇒ **2 passed**（`egress guard: judged 2; blocked 0`）：

- 主判据：`sort_analysis_v1` 经既有 API 启动 ⇒ 冻结（`manifest_digest` 非空）⇒ 执行阶段派发到
  **既有 Docker 后端** ⇒ 容器产出 `analysis_report` 满足 `ARTIFACT_EXISTS` ⇒ review 会话登记 ⇒
  终态**恰为 `SUCCEEDED`**；三项读面（实验 / 证据 / 预算）齐备。
- **成对反证**：撤掉 `code.execute` 的显式允许 ⇒ **拒冻**（`state=FAILED`、`manifest_digest is None`）
  且**执行前终止**（零 task、零 experiment）。

**第一次失败逐字保留**（不是放宽，是按被执行的脚本重钉）：初版把指标名写成 `n_train`/`n_test`
（那是 m12 分类实验的指标名），实测被执行的脚本 `examples/experiments/sort_analysis_baseline.py`
产出的是 `corpus_size` / `worst_case_comparisons` ⇒ 断言按**实际产出**改正。

### 三、真实一次 run（`requires_live_llm`，最小必要次数）

`set -a; . ./.env; set +a; RESEARCHOS_AGENT_RUNTIME=openhands pytest tests/e2e/test_ec02_experiment_live.py -q -rs`
⇒ **1 passed**（`egress guard: judged 2; blocked 0`）。样张 `scratch/goal012-c2-live-sample.json`
（**不进仓库**）：

| 项 | 实测 |
| --- | --- |
| 协议 / 终态 | `sort_analysis_v1_0_1` / **`SUCCEEDED`**，失败面为空 |
| 冻结 | `manifest_digest` 非空；`manifest.frozen` payload 含 **4 条** `accepted_policy_exceptions`（`code.execute` / `workspace.read` / `workspace.write.code` / review 的 `workspace.read`；`decision=ALLOW`、`accepted_at` 非空） |
| 实验 | 恰 1 次：镜像摘要 `sha256:e95de2424c65…`（= 本机 `research-os-sandbox:m9-test`）、环境摘要在场、产物含 `analysis_report` / `experiment_result.json` / `stdout.log` / `stderr.log`、指标 `corpus_size=2048` / `worst_case_comparisons=19960` |
| 证据 | **6 条**：4 条实验制品（`GENERATED`）+ 1 条 `session_message`（review 会话交付物）+ 1 条 `sort_analysis_v1`（**`USER_PROVIDED`** 声明输入） |
| 归账 | `MODEL_TOKENS` **9738**（`quantity_status=KNOWN`）、`MODEL_REQUESTS 2`；成本如实 `UNKNOWN`（模型未定价，不补 0） |

### 四、本 cycle 撞到并修掉的真缺陷（一次真实取样换来的）

第一次 live 取样**冻结成功、实验真跑了**，却死在 review 阶段的会话：
`task … failed: Duplicate tool names found: {'inert'}`。根因：测试侧惰性工具替身把冻结集里的
**两件** provider（`openhands_workspace` + `m12_artifact`）注册成**同一个类**，而 SDK 的
`ToolDefinition.name` 由**类名**派生 ⇒ 两件同名 ⇒ agent 初始化即失败（**零模型调用**）。
`real_research_task_v1`（1 件 provider）的真 run 一路绿，所以这个死法长期没暴露；
`sort_analysis_v1` 的每个阶段都是两件。

处置（**不是**改断言迁就）：`inert_tool_class_for()` 按注册名生成**独有类名**的惰性类
（模块全局只造一次、显式 `__qualname__`/`__module__`，避开 SDK 的 `<locals>` 与
"Duplicate class definition" 两种毒化）；并**新增离线判据**
`test_ec03_real_runtime_offline_chain.py::test_a_two_provider_frozen_set_starts_a_session`
（mock 端点 + `map_tools=True`）钉住它。

**按压（先红后绿）**：把 `register_inert_tools` 临时改回共用一个类 ⇒ 该用例**逐字复现** live 死法
（`scratch/goal012-c2-press-duplicate.txt`：`Duplicate tool names found: {'inert'}` 且 mock 端点
`requests == []`）；复原 ⇒ 绿（同文件 **5 passed / 1 skipped**）。

### 五、门与套件

| 门 | 结果 |
| --- | --- |
| `python/tests`（m0 内，全量） | **4408 passed / 19 skipped / 0 failed**（`scratch/goal012-c2-m0-rerun.log`） |
| `python/typecheck` | 首轮**红**：`test_ec02_experiment_chain_offline.py:58` 的 `dict[str, dict[str, str]]` 与 `dict[str, object] \| None` 不兼容 ⇒ 加显式标注后 `Success: no issues found in 995 source files`（第 2 轮 m0） |
| 定向套件 | `tests/e2e`：**116 passed / 10 skipped**（skip 全是 live/docker 诚实放行面）；`tests/api` + `tests/application`：**1212 passed / 1 skipped** |
| m0（23 项确定性检查） | 第 1 轮 **1 红**（typecheck，见上）；第 2 轮**唯一红项是 `framework/validate`**，原因是本 RECHECK 当时尚未落盘（MEM-110 的 `source_rechecks` 指向它）；第 3 轮（文档落盘后）⇒ **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c2-m0-final.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行；`python/tests` **4408 passed / 19 skipped / 0 failed**） |
| `git diff` 撤回纪律检查 | 本 cycle **未改**任何共享协议 / 共享合约 / 出站判据 / 策略面（脚本 A 组逐条在两棵树同结论） |
| 出站 | 全部 pytest 逐条 `egress guard: judged N; blocked 0`；live 判据默认门如实 skip |

## W 列表（本 cycle 的如实登记）

- **W-B 已闭合**（cycle 1 登记：冻结之后死在「会话结果无结构化输出」）：根因是**共享夹具的
  受控执行体不声明任何交付物**，而 `register_session_result` 对空交付物**如实拒绝**——
  那是既有语义，本 cycle **一字未改**。处置：离线判据**显式声明**交付物；
  `with_sandbox_experiment` 多一个**可选** `runtime` 参数（缺省沿用既有执行体，
  `make_run_ready_deps` 的缺省 runtime **未动**，共享夹具的失败形态不变）。
- **W-A（仍登记，需拍板）**：真实控制面（`NativePolicyEvaluator` + `examples/config/policy.yaml`）
  对 `sort_analysis_v1` 的 `evidence.read` 判 `DENY` ⇒ 该协议在真实控制面上是 `FAIL`（不是 `WARN`）。
  本 cycle 的 live 路径走**既有装配面**（与 GOAL-009/010/011 全部真实 run 同一条路径），
  **未**修改策略面（脚本 A4 两棵树同结论）。**留待拍板：是否给产品策略补 `evidence.read`。**
- **W-C（口径提醒）**：同一协议在两套装配下结论不同（真实控制面 `FAIL` vs 测试装配 `WARN`）。
  留痕里的 `decision: ALLOW` 来自**本次装配面**的求值器；实验那一步**另经真实求值器**的
  执行期检查（`GovernedExperimentExecutor._enforce_policy`，`code.execute` 为
  `allow_with_constraints`）——引用时必须写明装配。
- **环境提示**：本机 Docker daemon 可用（`29.2.1`），镜像 `research-os-sandbox:m9-test`
  在位（`e95de2424c65`）；EC-02 的离线判据在非 Linux 容器的守护进程下如实 skip（`requires_docker`）。

## 结论

**PASS**。EC-02 的三项要求（真实 LLM 驱动的 `sort_analysis_v1` 跑到终态、Docker 实验产物 /
证据 / 预算三面可读、终态如实为 `SUCCEEDED`）**各有实跑证据**；反证成对且先红后绿；
授权边界两棵树同结论（未放宽任何一条）。W-B 闭合，W-A/W-C 如实保留为需拍板与口径项。
