---
id: RECHECK-20260918-099
plan_id: PLAN-20260918-099
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-closeout
baseline_ref: 0cb68db
checked_head: 0cb68db (worktree clean)
---

# RECHECK-20260918-099 — GOAL-005 收口复检（六条 EC 的终态与残余）

## 检查范围

GOAL-20260918-005「残留收口与声明清账」的**收口独立复检**：六条 EC 的终态是否如实、
交付物在收口 head 上是否仍然成立、门禁与封印是否可复核、残余是否被隐藏。复检**不复述**
子 PLAN 的结论，而是回到树/门禁/封印上取证据（`0cb68db`，工作树干净）。

**不在射程**：EC-05 的 ②（PG 两读快照一致性，EC 允许"至少一项"）；GOAL-004 收口时已登记、
本 GOAL 有意不做的六项人工决策面（见「残余」）。

## 检查结果

| EC | 复检方式（回树取证） | 终态 |
| --- | --- | --- |
| EC-01 | `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md`（19.3 KB）+ `MIMOSA_DEPENDENCY_ADVISORIES_20260918.json` 在树；干净 checkout 封印 `sha256:1e549272…`（审计 §首页与 §6）；advisory 署名 `undici@5.29.0` 12 / `vite@6.3.5` 7 / `yaml@2.8.1` 1；`scanner_enobufs` 根因（semgrep 检测层未装）+ 复现命令 + 人工步骤清单；未覆盖范围段（威胁建模/授权面/业务逻辑/动态渗透） | **PASS**（RECHECK-093 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-02 | 补偿接线在位：`services/api/routers/approvals.py:174` 与 `:253` 调 `deps.runs.compensate_failed_resume(...)`，与 `scheduler.py` 共用同一域方法；用例 `tests/api/test_approval_resume_compensation_api.py` + `test_resume_compensation_api.py`（本轮复跑绿） | **PASS**（RECHECK-094 = PASS） |
| EC-03 | `ClaimRequest` 已无请求级 `lease_ttl_seconds`（port docstring 写明"引擎级配置"与移除理由），用例 `tests/contracts/test_claim_fencing_contract.py:62` 钉住字段不存在；示例契约只留 `on_task_failure`，用例 `tests/loaders/test_contract_loaders.py:180` 钉住 `unhonored == ()`；同源文档四处 | **PASS**（RECHECK-095 = PASS_WITH_WARNINGS） |
| EC-04 | **收口 head 重跑枚举探针**（`tools/probes/enumerate_clock_injected_pg_tests.py`）：`postgres test files: 27` / `clock-injected files: 12` / `files with wall-clock reads: 0` / `files with clockless constructors: 6` —— 与 RECHECK-096 的判定表**逐数一致**（12/12 判定为"安全"，依据落在写入路径上） | **PASS**（RECHECK-096 = PASS_WITH_WARNINGS，W-1…W-4） |
| EC-05 | `dispatch_ownership_many` 在 port 与三实现（`adapters/{sqlite,postgres,fakes}`）齐全（PG 侧装配在 `adapters/postgres/workflow_dispatch.py`）；N+1 哨兵用例 `tests/api/test_run_dispatch_view_api.py:229`、批量≡逐 run 契约用例 `tests/contracts/test_dispatch_ownership_contract.py:190`；文档两面（`CONTROL_PLANE_API.md` 列表路径 + 两条易读错事实、`PORTS.md`） | **PASS**（RECHECK-097 = PASS_WITH_WARNINGS，W-1…W-4；② 未做，见残余） |
| EC-06 | 分类器 `packages/application/run_orchestration/rebuild_readiness.py` + 读面 `RunDetailDto.rebuild` + `services/api/run_rebuild_view.py` 在树；`/resume` 拒绝由同一分类器给出（`services/api/run_resume.py` 两条早退 + 异常前缀）；用例覆盖旧事件形态、旧 run 形态、读面与拒因同源；`CONTROL_PLANE_API.md` / `EVENT_MODEL.md` 同源写明 | **PASS**（RECHECK-098 = PASS_WITH_WARNINGS，W-1…W-4） |

**门禁（收口 head 实跑）**：m0 `PASS: profile=m0; 23 deterministic checks`（全量 pytest
**3932 passed / 10 skipped**，491.81s）；规模门禁 `test_python_source_limits.py` **935 passed**；
治理 `validate.py`「Cursor 治理验证通过」；六条 EC 的判据用例合并复跑
（`test_run_dispatch_view_api` / `test_run_source_and_rebuild_api` /
`test_failed_run_semantic_digest_api` / `test_approval_resume_compensation_api` /
`test_claim_fencing_contract` / `test_contract_loaders` /
`test_dispatch_ownership_contract` / `test_rebuild_readiness` /
`test_snapshot_migration`）⇒ **130 passed**；web 六门（cycle 6 内实跑）lint / typecheck /
unit **76** / build / stub e2e **83** / live e2e **36**。

## 安全封印（收口独立复扫）

- **干净 checkout 深扫**（`git archive HEAD` 导出 3053 == `git ls-files` 3053，树内无
  `scratch/`/`artifacts/`）：scanId `scan-2026-09-18T10-38-30.552Z-601d81807a9b`，
  seal `sha256:c0202d05a57e3919139a80416e16d6e02e4350ebfbf196b614248c9d28c52f89`，
  findings **25**（1 high / 19 medium / 5 low），coverage `partial` / `runStatus
  inconclusive`（`threatModel` + `findingDiscovery` partial）。
- **工作树对照扫**：seal `sha256:2e666a4a…`，findings **34**（1 / 28 / 5）。两组差集 =
  gitignored `scratch/probe_*.py`（13 条 medium）——与 EC-01 的结论一致：**输入边界改变
  剖面**，干净输入才是可复核口径。
- **逐类处置（干净输入 25 条，全部有依据）**：
  - **1 high「不安全反序列化」= 误报（有缓解证据）**：`packages/application/protocol_authoring/
    service.py:103` 是 `yaml.load(text, Loader=_StrictLoader)`，而 `_StrictLoader` 继承
    `yaml.SafeLoader`（同文件 83-99 行：无任意构造器，只追加重复键拒绝），模块 docstring
    写明"只允许安全加载"，行内 `# noqa: S506` 说明理由 ⇒ 规则只匹配了 `yaml.load(` 字面。
  - **5 low「不安全的随机数」= 误报（判据可查）**：`examples/experiments/
    m12_reference_classification.py` 的 `random.Random(seed)` 是**带种子**的演示词表生成
    （确定性、无安全用途），不构成 CWE-330 场景。
  - **19 medium「疑似跨文件污点」= 工具面，不是产品面**：全部落在**运维诊断脚本**
    （`tools/probes/*.py`、`tools/PA1R运行演练v1.py`）与 `services/worker/__main__.py:135`。
    前者是手工跑的场景复现脚本（EC-01 已用 AST 判据逐处核对产品树的动态 SQL 形态为
    常量/固定记号）；后者是 **operator 环境变量** `RESEARCHOS_WORKER_GPU_IMAGE` →
    worker plane 的 GPU 沙箱镜像，属部署域配置而非外部输入。
- **诚实边界**：扫描 `verdictEffect=none`、coverage `inconclusive` ⇒ **不得**读作"项目安全"；
  离线 advisory 通道两次输入给出不同答案（工作树 1 包命中 / 干净 0 包），**不作依赖结论**，
  依赖结论仍以 EC-01 的联网 OSV 查询（3 包 20 条，带署名）为准。

## 残余（如实登记，不因收口而消失）

1. **人工决策面六项**（本 GOAL「不进入循环 / 需人工拍板」）：威胁建模/授权面覆盖
   （BOLA/BFLA）、`artifacts/` 明文 token 清理、后继入口第 8 项（按声明给 adapter 接线 /
   `tool_pack.*` 策略）、450 行硬上限的持续搬迁、依赖 pin 升级（`undici`/`vite`/`yaml`
   有修复版本）、hook 侧 L3 门修复（semgrep 检测层未装 + graded 模式会交互询问）。
2. **EC-05 ②**（PG 两读快照一致性）未做：批量读消掉的是 N+1，不是撕裂读；边界在 port
   docstring / `PORTS.md` / RECHECK-097 W-1。
3. **收口扫的覆盖缺口**：`threatModel`/`findingDiscovery` partial（entryPoints 0 /
   authorizationSurfaces 0）⇒ 静态扫描不给出授权面结论；未覆盖范围与 EC-01 同。
4. **各 cycle 的 W 列表**（RECHECK-093…098）继续有效：EC-01 的依赖 pin 与 hook 门、
   EC-02 的诚实边界、EC-03 的 `DEAD_LETTER` 消费（canonical 状态机 + ADR 边界）、
   EC-04 的调度依赖断言/真墙钟矩阵、EC-05 的无分页上限与 Fake 弱同判、EC-06 的不预测
   重建结果/不裁决"不可回填"/前端未消费 `rebuild`。
5. **GOAL-005 期间新登记、未在六条 EC 内**：`docs/` 无新增长程项；`BACKLOG.md` 未改动。

## 结论

**PASS_WITH_WARNINGS**。六条 EC 的终态在收口 head 上**逐条可复核**（交付物在树、判据用例
可跑、封印可重算、探针重跑逐数一致），门禁全绿（m0 23/23 + web 六门 + 规模/治理），
收口独立复扫取得新封印且**每条发现都有处置依据**（1 high 有缓解证据的误报 / 5 low 误报 /
19 medium 在运维诊断面）。**GOAL-005 达成（ACHIEVED）**：EC-01…EC-06 全 PASS，且本复检
独立确认了六条终态。W 与残余已如实登记（人工决策面六项、EC-05 ②、扫描覆盖缺口、
各 cycle 的 W 列表）——**收口不等于这些已解决**。

## 门禁

复检脚本 `scratch/verify_goal005_closeout.py`（只读，gitignored，与 GOAL-004 收口脚本同处置）
在本轮实跑 **56 checks 全 PASS**（三层判据：交付物在树 / 判据用例在树 / 登记面一致——含
GOAL 的 `status: ACHIEVED`、`latest_recheck` 指向、六条 EC 表逐条 PASS、ALL_PLAN 七行 DONE）。
定向套件（九个子集合并）**130 passed**（17.71s，DSN pin 配方）。

- 上述全部实跑记录见本文件「检查结果」「安全封印」节；CI 六 job 见 GOAL-005「状态历史」。
