---
id: PLAN-20261120-119
slug: benchmark-parity-and-prd
title: GOAL-116 子计划 —— PRD 单一权威 + ResearchClawBench 三阶对标
status: IN_PROGRESS
created_at: 2026-11-20
updated_at: 2026-11-20
parent_goal: GOAL-20261120-116
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20261120-119

## 背景与靶子

序 84。建档取证（2026-11-20）：

- 本仓**从未有过任何外部评测**——所有读数都是自评。
- 行业已有公开基准 **ResearchClawBench**（InternScience / MIT / 40 任务 × 10 学科）：
  agent 从原始数据产出 `report/report.md`，多模态 LLM 按 rubric 打分；
  **>50 = 达到已发表论文水平**，公开榜首 **34.89**。
- 而本仓的实验相是**三个白名单脚本**，`AUTHORED_ALLOWED_BY_DEFAULT = False`，
  沙盒镜像就是 `python:3.12-slim`（无 numpy/pandas/scipy/matplotlib/h5py），
  容器 `network none` ⇒ **不放开就几乎必然零分**。
- 用户的地址 `apevonscience.com` 是 JS 空壳；真实站点 `apevon.ai`。

## 交付面（checkbox）

- [ ] EC-01 `docs/product/PRD.md` v1.0（九节）+ `tests/tooling/test_prd_claims_match_the_tree.py`
      + `docs/INDEX.md` 登记 + 旧两份文档指针
- [ ] EC-02 `tools/rcb_agent.py`（走 `assemble()`，导出 `report/report.md`，
      未产出非 0 退出）+ `tests/benchmarks/test_rcb_agent_contract.py`
- [ ] EC-03 一阶基线：1 个任务、证据 JSON（`run_kind == "baseline"`）
- [ ] EC-04 二阶能力：`research-os-analysis` 镜像（digest pin）+ AUTHORED profile 放行
      + `analysis_to_report_v1` 协议
- [ ] EC-05 二阶读数：同任务重跑 `score > baseline`
- [ ] EC-06 三阶扩量：3 任务 / ≥2 学科 + 证据 JSON
- [ ] EC-07 收口（`verify_goal116_closeout.py` + 两树 + m0 witness + CI）

## 实施清单

### WP-A：PRD（EC-01）

本窗口已预落 `docs/product/PRD.md` 与 `docs/benchmarks/RESEARCHCLAWBENCH.md`；
另一窗口需要补的是**判据**：

`tests/tooling/test_prd_claims_match_the_tree.py` —— 每条断言「PRD 的说法 == 树的事实」，
建议覆盖（全部离线、秒级）：

| 断言 | 数据来源 |
| --- | --- |
| `submission` 在 OpenAPI 零命中 | `docs/api/openapi.m13.json` |
| `DEFAULT_RETMAX == 3` 且 `MAX_RETMAX == 100` | `services/api/retrieval_wiring.py` |
| console = 14/18/1 | `apps/web/src/navigation/pageSupport.ts`（现算，不写死） |
| `AUTHORED_ALLOWED_BY_DEFAULT is False` | `packages/application/experiments/script_authority.py` |
| 沙盒 Dockerfile 无 numpy/pandas/scipy/matplotlib/h5py | `adapters/execution/sandbox/Dockerfile` |
| 十一相 = 9 会话相 + 2 确定性相 | `examples/protocols/direction_to_manuscript_v1.yaml` |
| `NOT_JUDGED` 恰 5 条且含 5 个主题词 | `manuscript_quality.py` |
| 能力计数 47 / 22 / 13 | `capabilities.yaml` + `tool_providers.yaml` + 协议 |
| `models.yaml` 零 `VISION` | `examples/config/models.yaml` |
| 需求表状态词只用四值 | PRD 自身（表格解析） |

**每条都要有反证臂**：改 PRD 的对应数字 ⇒ 判红并点名。

### WP-B：基准适配器（EC-02）

`tools/rcb_agent.py`：

```text
argv: --workspace <dir> --prompt-file <file>
1. 读 prompt → 研究方向
2. deps = assemble(ApiSettings(db_path=<scratch>/rcb-<uuid>.db))
   （复用 tests/e2e/manuscript_chain_live_support.py:149 的形态，不补缝）
3. 跑一次 run → 从 artifact store 取 research_report.md / manuscript.md
4. 写 <workspace>/report/report.md
5. 产出成功 → exit 0；未产出 → exit 2（stderr 点名缺什么）
```

判据（离线）：用假 workspace + 假 deps 断言 ① 导出路径正确 ② 未产出时非 0 退出
（**不得写空报告**）③ judge 相关环境变量**不被读取**（评分由 harness 做，适配器不碰）。

### WP-C：一阶基线（EC-03）

1. 选一个数据小的任务（Math 或 Information 学科）。
2. 按 `docs/benchmarks/RESEARCHCLAWBENCH.md` §5 跑 harness，agent 指向 `tools/rcb_agent.py`。
3. 记录：任务 id / 学科 / 耗时 / `report_produced` / `score` / `judge_model` /
   失败归因 / 数据文件 digest → `evidence/GOAL-20261120-116-rcb-baseline.json`。

**预期**：近乎必然零分或未产出。**这个零分是本轮最重要的读数**，如实记录即可。

### WP-D：二阶能力（EC-04）

1. `adapters/execution/sandbox/Dockerfile.analysis`：基于已 pin 的 `python:3.12-slim`，
   烘入 numpy / pandas / scipy / matplotlib / h5py（版本 pin 写进 `UPSTREAM_COMPONENTS.yaml`）。
2. `services/api/executor_wiring.py` 增加 `ANALYSIS_IMAGE` 常量（不动既有
   `DEFAULT_EXPERIMENT_IMAGE`）。
3. `AUTHORED` 放行：只经 `AUTHORED_SAFETY_PROFILE = "authored-experiments-v1"`，
   **不改** `AUTHORED_ALLOWED_BY_DEFAULT`。
4. 新协议 `examples/protocols/analysis_to_report_v1.yaml`：
   `inspect_data`（运行链读数据目录，产出清单）→ `analysis_plan`（会话，写脚本）
   → `execute`（确定性相，AUTHORED 脚本进沙盒）→ `validate`（会话，核对指标与图）
   → `report`（确定性汇编，复用既有报告/手稿装配器）。
   相数与契约要在 `examples/contracts/task_contracts.yaml` 里新增对应条目。

### WP-E：二阶读数（EC-05）

同一任务重跑；断言 `report.md` 含 ≥1 张图片引用（扫描以感叹号+方括号开头的行）且
`score > baseline`。若仍为 0 ⇒ 点名结构性原因（镜像/网络/协议/模型）并 BLOCKED。

### WP-F：三阶扩量（EC-06）

3 个任务 / ≥2 学科；每个记分数、耗时、judge 模型、失败分类。

### WP-G：收口（EC-07）

`tools/verify_goal116_closeout.py` + `tools/goal116_closeout_assertions.py`；
登记 `_VERIFIERS` 与 `IN_SCOPE`；两树复检；全量 m0 witness。

## 验证

```bash
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_prd_claims_match_the_tree.py -q
uv run --frozen --no-sync python -B -m pytest tests/benchmarks -q
uv run --frozen --no-sync python -B -m pytest tests/loaders/test_free_model_only_policy.py -q
uv run --frozen --no-sync python -B -m pytest tests/application/experiments -q
# 真实基准（手动，非 CI）
JUDGE_API_KEY=... JUDGE_API_BASE=... JUDGE_MODEL_NAME=... <harness 命令>
uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
uv run --frozen --no-sync python -B tools/verify_goal116_closeout.py
```

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-00 | 建档 | survey | 本轮调研（PRD §4 来源） | RCB 40/10、榜首 34.89、`apevon.ai` 更正 |
| EV-01 | EC-01 | doc | `docs/product/PRD.md` + `docs/benchmarks/RESEARCHCLAWBENCH.md` | 本窗口已落 |
| EV-02 | EC-01 | test | `tests/tooling/test_prd_claims_match_the_tree.py` | 待填 |
| EV-03 | EC-02 | test | `tests/benchmarks/test_rcb_agent_contract.py` | 待填 |
| EV-04 | EC-03 | live | `.cursor/plans/goals/evidence/GOAL-20261120-116-rcb-baseline.json` | 待填 |
| EV-05 | EC-04 | image | `adapters/execution/sandbox/Dockerfile.analysis`（digest） | 待填 |
| EV-06 | EC-05 | live | `…-rcb-after-capability.json` | 待填 |
| EV-07 | EC-06 | live | `…-rcb-scale.json` | 待填 |
| EV-08 | EC-07 | verifier | `tools/verify_goal116_closeout.py` | 待填 |

## 验收条件

- 七条 EC 全部 PASS（EC-03 的零分是**合法 PASS**）；
- PRD 防漂移判据全绿且每断言有反证臂；
- judge 凭据零污染（`models.yaml` 仍只含零价模型）；
- `AUTHORED` 默认仍关闭；
- 全量 m0 witness 绿 + 两树 `sha256` 相同 + CI 八 job 终态。

## 状态历史

- 2026-11-20：建档（PLAN + GOAL-116 + PRD v1.0 + RCB 接入说明同轮落树；
  执行在另一窗口）。

## 影响报告

- **Domain/API/schema**：预期新增一个确定性相与新协议；`AUTHORED` 只经 profile 放行；
  不改 `REVIEW_SCORE` / `panel_rejection` / `NOT_JUDGED`。
- **安全/凭据**：judge 凭据只在本机环境变量，**不进** `examples/config/**`；
  `network none` 不变；沙盒仍非 root。
- **兼容性/迁移**：新镜像按 digest pin；既有 `research-os-sandbox:m9-test` 不动。
- **上游版本影响**：新增镜像依赖集合（numpy 等）需登记进 `UPSTREAM_COMPONENTS.yaml`。
