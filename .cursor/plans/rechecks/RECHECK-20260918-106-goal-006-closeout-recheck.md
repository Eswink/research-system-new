---
id: RECHECK-20260918-106
plan_id: PLAN-20260918-106
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-closeout
baseline_ref: b10760f
checked_head: b10760f (+ 本次收口提交；工作树干净)
---

# RECHECK-20260918-106 — GOAL-006 收口复检（六条 EC 的终态与残余）

## 检查范围

GOAL-20260918-006「读面与终态语义收口」的**收口独立复检**：六条 EC 的终态是否如实、
交付物在收口 head 上是否仍然成立、门禁与封印是否可复核、残余是否被隐藏。复检**不复述**
子 PLAN 的结论，而是回到树/门禁/封印上取证据（`b10760f`，工作树干净）。

**不在射程**：`DEAD_LETTER` 消费的实现（EC-02 走 (b) 只到 Proposed ADR，属人工拍板）；
「不进入循环 / 需人工拍板」六项（威胁建模/授权面、依赖 pin 升级等）；GOAL-005 / 004
（ACHIEVED）与 GOAL-003（BLOCKED）保持只读。

## 检查结果

| EC | 复检方式（回树取证） | 终态 |
| --- | --- | --- |
| EC-01 | 两方言 `adapters/{postgres,sqlite}/projections.py` 均为 `UNION ALL` 单语句取数 + 判别列；PG 装配入口 `adapters/postgres/workflow_dispatch.py`；两方言探针用例 `test_pg_the_read_face_answers_from_one_snapshot` / `test_sqlite_the_read_face_answers_from_one_snapshot` 在本轮实跑绿；`CONTROL_PLANE_API.md` + `PORTS.md` 快照口径在树 | **PASS**（RECHECK-20260918-100 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-02 | `docs/adr/ADR-0030-validation-failure-consumption.md`（**Status: Proposed**，含 `## Options`（A–E）/ `## Trigger（何时必须拍板）`/ `## Consequences`）+ `docs/INDEX.md` 唯一入口 + 三处声明面指针（`packages/domain/failure_policy.py` / `examples/contracts/task_contracts.yaml` / `docs/architecture/TASK_HANDOFF.md`）+ 判据 `tests/tooling/test_pending_validation_failure_registration.py`（本轮实跑绿） | **PASS**（RECHECK-20260918-101 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-03 | `apps/web/src/features/runs/RebuildReadiness.tsx` + `RunPanel.tsx` 渲染分支 `<RebuildReadiness rebuild={flow.run.data.rebuild} />`；**本轮复跑两条链**：stub `run-rebuild-readiness.spec.ts` **2 passed**、live `live-run-rebuild-readiness.spec.ts` **2 passed**（live 由 `playwrightLive.config.ts` 的 webServer 真起应用）；`CONTROL_PLANE_API.md` + `docs/frontend/CONSOLE_PAGE_MAP.md` 同源口径在树 | **PASS**（RECHECK-20260918-102 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-04 | `tests/postgres/test_claim_concurrency_pg.py` 的 `_ClaimProbe`（`attempts` + 同一个 `overlap` barrier 的 `arrival_index`）在树，断言不读调度产物；`tests/postgres/test_cross_process_real.py` 覆盖矩阵 + 有界等待（`deadline`）；矩阵机器判据 `tests/postgres/test_wall_clock_coverage_matrix.py`（含 `test_no_unbounded_sleep_in_the_file` / `test_uncovered_timings_are_stated`）本轮实跑绿 | **PASS**（RECHECK-20260918-103 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-05 | port `MAX_DISPATCH_OWNERSHIP_BATCH = 500` + `validate_dispatch_batch`（值唯一事实源）；三实现都调**同一句**校验（`adapters/{fakes,sqlite,postgres}/workflow_engine.py`，PG 在 `try` 之外）；服务层 `services/api/run_dispatch_view.py` 按上限分块；弱同判机器判据 `tests/contracts/test_dispatch_ownership_weak_equivalence.py`（7 条，本轮实跑绿）；`PORTS.md` + `CONTROL_PLANE_API.md` 同值同源 | **PASS**（RECHECK-20260918-104 = PASS_WITH_WARNINGS，W-1…W-5） |
| EC-06 | `EventType.RUN_RESUME_COMPENSATION_FAILED`（`packages/domain/events.py`）+ `run_terminals.publish_compensation_failure` + 服务薄封装 + `services/api/scheduler.py` 失败路径**先发后吸收**；读面用例（`tests/api/test_compensation_failure_visibility_api.py`：真跑一轮调度 + 反空洞）与键集合互钉判据（`tests/application/run_orchestration/test_resume_compensation_failure_event.py`）本轮实跑绿；`EVENT_MODEL.md` + `CONTROL_PLANE_API.md` 含「不含任务级归因」一等边界 | **PASS**（RECHECK-20260918-105 = PASS_WITH_WARNINGS，W-1…W-5） |

**复检抓到的登记面缺陷（返工事实，不粉饰）**：EC 状态表的 **EC-03 / EC-04 两行漏改**——
cycle 3 / cycle 4 回写时未把状态列从「未完成」枚举改成 PASS（该枚举字面量不在此回写），与两条 EC 的 frontmatter `status: PASS`、
「状态历史」条目、RECHECK-102 / 103 的结论**矛盾**，而治理 validator 与两轮回写都没抓到。
收口复检脚本首版的 EC 表判据取「`| EC-0X |` 之后 400 字符内是否出现 `**PASS**`」——会把
**下一行**的状态当成自己的（首跑因此漏判这两条）；加严为「取本行最后一个非空单元格」后
**先见红**（EC-03 / EC-04 = 未完成枚举），再按 frontmatter 与 RECHECK 更正为 PASS 后全绿。

## 门禁

- 复检脚本 `scratch/verify_goal006_closeout.py`（只读，gitignored，与 GOAL-004 / 005 收口
  脚本同处置）在本轮实跑 **88 checks 全 PASS**（三层判据：A 交付物在树 / B 判据用例在树 /
  C 登记面一致——GOAL `status: ACHIEVED`、`latest_recheck` 指向、六条 EC 表**逐行取本行状态列**
  PASS、child_plans 指向的文件存在、ALL_PLAN 七行 DONE）。
- 六条 EC 的判据套件合并**真跑 104 passed**（28.51s，DSN 固化配方 + `postgres-test` 容器）：
  `test_dispatch_read_snapshot_pg` / `test_dispatch_read_snapshot`(sqlite) /
  `test_dispatch_ownership_contract` / `test_dispatch_ownership_weak_equivalence` /
  `test_pending_validation_failure_registration` / `test_claim_concurrency_pg` /
  `test_wall_clock_coverage_matrix` / `test_cross_process_real` / `test_run_dispatch_view_api` /
  `test_compensation_failure_visibility_api` / `test_resume_compensation_failure_event` /
  `test_retry_dispatch_scheduler` / `test_m5_domain_increments`。
- 本机 m0 全量 **`PASS: profile=m0; 23 deterministic checks`**（首跑即绿，无 flake；其中
  `python/tests` = **3978 passed / 10 skipped**，482.66s）；治理 `validate.py`「Cursor 治理验证通过」。
- web 链（EC-03 复跑）：stub **2 passed** + live **2 passed**；CI 侧 `console-frontend` job
  在每次推送的 head 上重跑全量 stub/live 套件。

## 安全封印（收口独立复扫）

- **干净 checkout 深扫**：`git archive HEAD`（`b10760f`）导出 **3087 文件 == `git ls-files` 3087**，
  树内 `scratch/` 文件 0、`git ls-files artifacts/` = 0（导出里 12 个含 "artifacts" 的路径全部是
  **产品模块**：`packages/{application,domain}`、`services/api/{dto,routers}`、`tests/**`）。
  scanId `scan-2026-09-18T23-20-28.015Z-a786716787f9`，
  seal `sha256:0c36bb3c6bb5f7a2c073e80f67fcde41de1f24049dc152c321a6ac6cb6e4ca60`，
  findings **25**（1 high / 19 medium / 5 low），coverage `partial` / `runStatus inconclusive`
  （`threatModel` 0 入口），`verdictEffect=none`、`evidenceBoundary=static_only_no_runtime_execution`。
- **工作树对照扫**：scanId `scan-2026-09-18T23-23-15.483Z-001f1884ab3a`，
  seal `sha256:5bd2490f00719eefdbf2a7bdaaefa7a8cc7c9a0af8b9d97e568c4f72e3d60937`，
  findings **34**（1 / 28 / 5），`packagesScanned` 182（干净输入 11）。差集（medium 净 +9）：
  gitignored `scratch/probe_*.py` 探针在对照扫里出现 17 条，而干净扫在 `tools/probes/probe_migration.py`（7）
  与 `tools/PA1R运行演练v1.py`（1）上的 8 条在对照扫里被归到同名 scratch 副本 ⇒ **输入边界改变剖面**，
  干净输入才是可复核口径。
- **逐条处置（干净输入 25 条，全部有依据）**：

| # | 严重度 | 类别 | 位置 | 处置依据 |
| --- | --- | --- | --- | --- |
| 1 | high | 不安全反序列化 | `packages/application/protocol_authoring/service.py:103` | 误报（有缓解证据）：`yaml.load(text, Loader=_StrictLoader)`，`_StrictLoader` 继承 `yaml.SafeLoader`（无任意构造器，只追加重复键拒绝），行内 `# noqa: S506 - SafeLoader 子类`；规则只匹配了 `yaml.load(` 字面 |
| 2 | low | 不安全的随机数 | `examples/experiments/m12_reference_classification.py:33` | 误报：带种子 `random.Random(seed)` 的演示词表/权重生成（确定性、无安全用途），不构成 CWE-330 场景 |
| 3 | low | 不安全的随机数 | `examples/experiments/m12_reference_classification.py:42` | 误报：带种子 `random.Random(seed)` 的演示词表/权重生成（确定性、无安全用途），不构成 CWE-330 场景 |
| 4 | low | 不安全的随机数 | `examples/experiments/m12_reference_classification.py:64` | 误报：带种子 `random.Random(seed)` 的演示词表/权重生成（确定性、无安全用途），不构成 CWE-330 场景 |
| 5 | low | 不安全的随机数 | `examples/experiments/m12_reference_classification.py:69` | 误报：带种子 `random.Random(seed)` 的演示词表/权重生成（确定性、无安全用途），不构成 CWE-330 场景 |
| 6 | low | 不安全的随机数 | `examples/experiments/m12_reference_classification.py:142` | 误报：带种子 `random.Random(seed)` 的演示词表/权重生成（确定性、无安全用途），不构成 CWE-330 场景 |
| 7 | medium | 疑似跨文件污点 | `services/worker/__main__.py:135` | 工具面/部署域：operator 环境变量 `RESEARCHOS_WORKER_GPU_IMAGE` ⇒ GPU 沙箱镜像，属部署配置而非外部输入 |
| 8 | medium | 疑似跨文件污点 | `tools/PA1R运行演练v1.py:56` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 9 | medium | 疑似跨文件污点 | `tools/probes/probe_cancel_race.py:73` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 10 | medium | 疑似跨文件污点 | `tools/probes/probe_canonical_state.py:96` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 11 | medium | 疑似跨文件污点 | `tools/probes/probe_db_failure.py:100` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 12 | medium | 疑似跨文件污点 | `tools/probes/probe_db_failure.py:140` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 13 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:117` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 14 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:143` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 15 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:177` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 16 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:183` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 17 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:187` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 18 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:197` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 19 | medium | 疑似跨文件污点 | `tools/probes/probe_migration.py:203` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 20 | medium | 疑似跨文件污点 | `tools/probes/probe_outbox.py:90` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 21 | medium | 疑似跨文件污点 | `tools/probes/probe_outbox.py:127` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 22 | medium | 疑似跨文件污点 | `tools/probes/probe_scheduled_recovery.py:100` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 23 | medium | 疑似跨文件污点 | `tools/probes/probe_scheduled_recovery.py:142` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 24 | medium | 疑似跨文件污点 | `tools/probes/probe_stale_worker.py:103` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |
| 25 | medium | 疑似跨文件污点 | `tools/probes/probe_stale_worker.py:134` | 工具面：运维/诊断探针脚本（不进产品路径、不进容器镜像；本地手工运行） |

- **诚实边界**：扫描 `verdictEffect=none`、coverage `inconclusive` ⇒ **不得**读作"项目安全"；
  离线 advisory 通道两次输入答案不同（干净 11 包 0 命中 / 工作树 182 包 1 命中）
  ⇒ **不作依赖结论**；本 GOAL 的六条 EC PASS 同样不构成整体安全结论。

## 残余（如实登记，不因收口而消失）

1. **「不进入循环 / 需人工拍板」六项**原样保留：威胁建模/授权面（BOLA/BFLA）覆盖、
   `artifacts/` 内未跟踪明文 token 文件的清理、按声明给 adapter 接线与 `tool_pack.*` 策略、
   450 行硬上限贴线的持续重构、依赖 pin 升级（`undici` / `vite` / `yaml`）、hook 侧 L3 门修复。
2. **EC-02 只到 Proposed ADR**：`DEAD_LETTER` 消费（`on_validation_failure`）仍未实现；
   选项 A–E 的取舍待人工拍板后在后续承接 GOAL 做。
3. **六条 EC 的 W 列表**全部保留（见 GOAL「收口结论」表第三列）。
4. **扫描 coverage 缺口**：`threatModel` / `findingDiscovery` 长期 partial，静态扫描不给出
   授权面结论；`verdictEffect=none` 不得读作项目安全。
5. **产品/运营决策**：RECHECK-098 W-2（历史行要不要 re-freeze/fork）、RECHECK-090 W-5
   （`/resume` 仍回 200 + `continuation=FAILED`）。

## 告警（W）

- **W-1** 复检脚本是**结构性判据**（文件/符号/用例名/登记面），不是行为复测；行为面由
  判据套件（104 passed）与两条 web 链承担。
- **W-2** 封印取自收口前的最后一个提交 `b10760f`；本次收口提交**只改 `.cursor/**` 记录**
  ——差集已实测（`scratch/ec05/seal_input_diff.py`：逐文件 sha256 对比封印输入与收口提交的
  `git archive` 导出 ⇒ 新增 1 = RECHECK-106 本身、变更 3 = ALL_PLAN / GOAL-006 / PLAN-106，
  **非 `.cursor/` 差异 0 条**），但**封印不是**对收口提交自身重新取的。
- **W-3** 工作树对照扫的差集已量化（+9 medium，全部落在 gitignored `scratch/`），但
  "同名副本被归到哪一份"是扫描器的去重口径，未逐条归因。
- **W-4** 离线 advisory 通道两次输入答案不同 ⇒ 依赖结论仍以联网查询（GOAL-005 EC-01 的
  带署名结论）为准。
- **W-5** 收口**不宣称项目安全**：扫描 `verdictEffect=none` + coverage inconclusive。

## 结论

**PASS_WITH_WARNINGS**。六条 EC 的终态在收口 head 上**逐条可复核**（交付物在树、判据用例
可跑并本轮真跑 104 passed、两链 e2e 复跑、封印可重算、m0 23/23 首跑即绿）。收口独立复检
**抓到并当场更正了两处登记面缺陷**（EC-03 / EC-04 的状态表行漏改；复检脚本自身的 EC 表
判据过弱——先加严见红、再更正转绿）。**GOAL-006 达成（ACHIEVED）**：EC-01…EC-06 全 PASS，
`status: ACHIEVED`、`latest_recheck` 指向本 RECHECK、「收口结论」写明残余与恢复条件。
W 与残余已如实登记——**收口不等于这些已解决**。

## 门禁

- 复检脚本 `scratch/verify_goal006_closeout.py` 本轮实跑 **88 checks 全 PASS**（三层判据见上）。
- 判据套件合并 **104 passed**；m0 **23/23**（`python/tests` 3978 passed / 10 skipped，482.66s）；
  治理 validator 绿；web stub **2 passed** + live **2 passed**。
- CI：本 GOAL 全部推送的 run 到终态（台账表见 GOAL-006「收口结论」）；本次收口提交自身的
  run 按闭合口径在回合汇报给出终态。
