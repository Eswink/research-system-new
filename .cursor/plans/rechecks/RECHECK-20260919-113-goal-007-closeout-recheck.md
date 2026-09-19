---
id: RECHECK-20260919-113
plan_id: PLAN-20260919-113
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle7
baseline_ref: d001b62
checked_head: WORKTREE
---

# RECHECK-20260919-113 — GOAL-20260919-007 收口复检（EC-01…EC-06 独立复核）

## 检查范围

不采信六条 RECHECK 的结论文本：在**当前树**与**干净 checkout**（`git clone --no-hardlinks`
到仓库外的 `d001b62`）各跑一遍同一份三层判据脚本 `scratch/verify_goal007_closeout.py`
（**80 checks**：A 交付物在树 / B 判据用例在树 / C 登记面一致），并把六条 EC 的判据套件
**合并**真跑（同一命令、同一进程）。收口另外要求：GOAL「终止与收口 · 收口结论」+
`status: ACHIEVED` + `latest_recheck` 指向本文件 + 残余登记。

## 检查结果

### A/B 层：交付物与判据（当前树，实测）

| EC | 交付物（脚本逐条回证据） | 判据（脚本核对用例名；套件合并真跑见下） |
| --- | --- | --- |
| EC-01 | `services/api/runtime_support.py`（`resolve_runtime_selection` / `build_agent_runtime`）+ 两个组合根都经同一装配点 | `tests/api/test_runtime_selection_surface.py` 8 条代表用例（选择面 / 同侧 / 默认 demo / 失败点名 / 冻结 manifest 记录执行体 / 指纹显式 NOT VERIFIED） |
| EC-02 | `services/api/run_execution.py::_live_preflight`（裁决与 health **同源求值**） | `tests/api/test_runtime_egress_gate.py` 6 条（拒绝 ⇒ 0 出站 / 放行 ⇒ 确有出站（计数器非空转）/ 缺凭据先停 / 逐环点各自缺的事实 / 全仓只有一份 host 判据） |
| EC-03 | `adapters/openhands/runtime_adapter.py::_deliverable`（事实名 `session_message`） | `tests/e2e/test_ec03_real_runtime_offline_chain.py` 3 条 + `tests/api/test_session_llm_factory.py` |
| EC-04 | `services/api/run_execution_view.py::run_execution_dto` + `apps/web/src/features/runs/RunPanel.tsx::RunIdentityFacts` + 夹具声明面 `console_api_app.py::_with_substrate_disclosure` | stub 两条（四态可区分 / 指纹只报状态）+ live 一条（页面 == 读面）+ 设计基线 34 条 |
| EC-05 | `tests/architecture/python/test_tool_plane_boundary.py` 6 条结构判据 + fork 窄门（`session_builder.py` / `fakes/agent_runtime.py` 同契约）+ `TOOL_RUNTIME.md` §9 接入边界登记 | 契约用例两实现参数化 + adapter 公开面判据 |
| EC-06 | `docs/adr/ADR-0031-…`（`Status: Proposed`）+ `docs/INDEX.md` 登记 + 四处同源 | `tests/tooling/test_toolpack_capability_policy_pending.py` 6 条（Proposed / INDEX / 同源 / 真实策略 DENY / 生命周期不带 action / 验收门字面名） |

### C 层：登记面一致（实测）

- GOAL frontmatter EC 表**逐行**回归：EC-01…EC-03 早已 PASS；**EC-04 / EC-05 在 cycle 4 /
  cycle 5 回写时漏改**（`status` 仍是「未完成」枚举、`evidence` 为空串），与迭代日志、
  状态历史、RECHECK-110 / RECHECK-111 的结论矛盾 ⇒ 收口时按两条 RECHECK 更正为 PASS
  并补齐证据；EC-06 由 cycle 6 写入 PASS。
- child_plans 六个文件都存在且 `status: DONE`、正文无未勾选项；ALL_PLAN 六行 `[x] … DONE`；
  `latest_recheck` 指向本文件；memory_entries 六个 MEM 文件都在树。

### 复检**实测出的缺陷**（干净 checkout 上暴露，已修）

在 clone（`d001b62`）上合并跑六条 EC 的判据套件时 **2 failed**：
`tests/contracts/test_agent_runtime_contract.py` 的两条 openhands fork 用例。**同一命令在
当前树也红**（说明与干净 checkout 无关），逐层定位到根因：

- `tests/e2e/test_ec03_real_runtime_offline_chain.py` 的惰性工具把 `Action` 子类定义在
  **函数内**；SDK 构建判别联合时会枚举 `Action` 的全部具体子类，遇到 `<locals>` 限定名
  直接抛 `Local classes not supported! … / openhands.sdk.tool.schema.Action`，
  ⇒ **同进程内此后任何事件 round-trip 全挂**（fork 路径正好走它）。
- 触发条件 = 该 e2e 文件在契约文件**之前**执行；m0 与 CI 是字母序（`tests/contracts` 在
  `tests/e2e` 前），因此**CI 看不见**。复现命令（两条命令等价，可在任意树跑）：
  `pytest tests/e2e/test_ec03_real_runtime_offline_chain.py tests/contracts/test_agent_runtime_contract.py`。
- 修复：把三个类提升到**模块级**（与 `tests/adapters/openhands/test_spike_e2e.py` 同形态），
  **未改任何断言**。对照：修复前 83 passed / **2 failed** / 1 skipped；修复后
  **85 passed / 1 skipped**（同一命令）。

### 干净 checkout 封印

- `git clone --no-hardlinks` 到 `D:\research-system-seal-20260919`（`d001b62`，六条 EC 全部
  落地的 tip），`git status` 干净；`node_modules` 以 junction 指向本机已安装依赖（依赖是
  安装物、不是仓库内容；**这是本封印唯一的人为补足，如实披露**）。
- 在 clone 上跑复检脚本：`GOAL007_ROOT=<clone>` ⇒ 80 checks，唯一失败项是「RECHECK-113
  不存在」——因为该 tip 早于本轮收口（收口循环自身的记录文件），**不是证据面缺陷**。
- 在 clone 上跑合并判据套件：83 passed / 2 failed / 1 skipped ⇒ 即上面那条跨套件污染，
  clone 与当前树**结论一致**（这正是"干净 checkout"该有的性质：不引入新绿，也不引入新红）。

## CI 台账（逐 job conclusion，GitHub REST API）

| 推送 | run | 结论 |
| --- | --- | --- |
| cycle 6 批量推送（tip `fcc8538`） | M0 **35471008774** | **cancelled**（`concurrency.cancel-in-progress`：紧随其后的回写推送取消了在飞的 M0；同一内容的覆盖由 `d001b62` 的 run 承担，属结构性取消而非失败） |
| 同上 | Push-on-main **35471008451** | success |
| cycle 6 回写提交（`d001b62`） | M0 **35471382908** | **success**（六个 job 全 success：quality-ubuntu-latest / quality-windows-latest / console-frontend / collector-quality / container-quality / eval-gate） |
| 同上 | Push-on-main **35471382634** | success |
| cycle 7 收口提交 | 见回合汇报（闭合约定：本条推送的 run 不在本文件写回） | — |

## Warnings（不阻断，如实登记）

- **W-1**：`docs/adr/ADR-0031-toolpack-capability-policy.md` 仍是 **`Status: Proposed`** ——
  `tool_pack.*` 的产品决策**没有被解决**，只是被登记成可拍板的形状。真实部署下控制台供应链
  写面仍 403。
- **W-2**：EC-05 的 `execute_tool_call` / `execute_tool_gated` **在生产零调用点**；"DENY 不触达
  executor"是真的，但没有生产路径在跑工具（`ApiDeps.tool_providers` 恒空、无 provider→SDK
  映射、无 MCP server）。
- **W-3**：本 GOAL 的任何 PASS **不构成整体安全结论**。Mimosa 侧全程沿用兼容策略
  （`scanner_enobufs`：提交/推送前未取得完整扫描结论）；扫描 `verdictEffect=none`、coverage
  `inconclusive`、`threatModel` partial 的既有口径不变；威胁建模 / BOLA-BFLA / 业务逻辑风险
  **未覆盖**，需独立审计射程与决策面。
- **W-4**：`artifacts/` 内未跟踪明文 token 文件的清理仍属操作者决策（`git ls-files artifacts/`
  = 0，从未提交，事实已登记）。
- **W-5**：450 行硬上限贴线文件（如 `packages/application/run_orchestration/service.py`）仍是
  「下一行就会红」的状态；本 GOAL 未做专项重构。
- **W-6**：依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的 devDependency 链）与 hook
  侧 L3 门（semgrep 检测层未装；装上后 medium 会交互式询问）**均属需人工拍板**的安全策略决定，
  本循环未动。
- **W-7**：EC-04 的 live 第二种执行体是**声明**出来的（判「页面 == 读面」，不是真跑第二种
  执行体）；`run_execution_dto` 只在详情路径（列表路径仍是 N+1 边界）；`events(run_id)` 是
  outbox 全表扫描；`_frozen_payload` 取第一条 `MANIFEST_FROZEN`（将来允许 Manifest Revision
  需改）。
- **W-8**：真实 runtime × 声明式合约仍**必判拒**（`session_message` vs `analysis_report`，
  D2 未拍板）；真实端点路径只在 `requires_live_llm` 人工门控下跑，本机只证明 skip 路径。
- **W-9（本轮新发现，已登记）**：**GOAL 的 EC 表（frontmatter）与迭代日志/状态历史会漂**——
  EC-04 / EC-05 的 `status` 在 cycle 4 / cycle 5 回写时漏改，直到收口才由复检脚本抓出；
  GOAL-006 收口时出现过**同一类**漂移（EC-03 / EC-04）。形态化建议：回写时把 EC 表行
  与迭代日志行当作**同一笔改动**（或让复检脚本常驻 CI）。本轮只更正记录，未改任何门禁。
- **W-10（本轮新发现，已修）**：跨套件污染（见「检查结果」）——修复只动类定义位置，
  **未削弱任何断言**；但这类"顺序依赖的假绿"提醒：m0 的字母序本身也是判据的一部分，
  重新排序会改变结果。后续新增 e2e 文件时应避免在函数内定义 SDK 模型子类。

## 结论

GOAL-20260919-007 六条 EC **全部 PASS**，且本轮在**当前树**与**干净 checkout** 两处独立
回证据：三层判据脚本 80 checks（唯一失败项是本轮才产生的 RECHECK-113 文件自身），
六条 EC 的判据套件合并真跑 **85 passed / 1 skipped**。收口期间发现并修复一处**跨套件污染**
（函数内定义 SDK `Action` 子类 ⇒ 同进程后续事件 round-trip 全挂；修复 = 类提升到模块级，
未改断言；修复前后同一命令 83/2/1 → 85/0/1），并更正一处**登记面漂移**（EC-04 / EC-05 的
frontmatter 状态行在 cycle 4 / cycle 5 漏改）。**收口复检结论：PASS_WITH_WARNINGS**，
W-1…W-10 如实登记，其中 W-1（ADR 仍是草案）、W-2（门控无生产调用点）、W-3（不构成整体
安全结论）、W-9（登记面漂移是反复出现的失败模式）必须留档。

## 门禁

| 门 | 结果 |
| --- | --- |
| 复检脚本（当前树） | **80 checks / 0 failures**（A 交付物 + B 判据名 + C 登记面；新增 RECHECK-113 后重跑） |
| 复检脚本（干净 checkout `d001b62`） | 80 checks / 1 failure（仅 RECHECK-113 文件尚不存在，属收口循环自身产物） |
| 六条 EC 判据套件合并真跑（当前树） | **85 passed / 1 skipped**（修复后；修复前同一命令 83 passed / **2 failed** / 1 skipped） |
| 六条 EC 判据套件合并真跑（干净 checkout） | 83 passed / 2 failed / 1 skipped（= 当前树修复前的同一签名，两树一致） |
| 尺寸门（450 行 / 50 行函数） | **950 passed** |
| `ruff check` / `ruff format --check` | 绿（含本轮改动的 e2e 文件） |
| `mypy` | 绿（含本轮改动的 e2e 文件） |
| m0（23 项） | **PASS: profile=m0; 23 deterministic checks** |
| 治理 `validate.py` | 绿 |
| CI（逐 job conclusion） | 见「CI 台账」；cycle 6 的覆盖 run 六 job 全 success，收口推送的 run 见回合汇报 |
