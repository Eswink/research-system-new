---
id: GOAL-20261120-116
slug: benchmark-parity-and-prd
title: 第一次外部读数——PRD 合并为单一权威 + ResearchClawBench 三阶对标
status: ACTIVE
created_at: 2026-11-20
updated_at: 2026-11-20
owners:
  - root-agent
latest_recheck: null
budget:
  max_cycles: 24
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
authorization:
  source: user-request
  ref: >-
    序 84（GOAL 号 116）。用户 2026-11-20 四项拍板：
    ① **PRD 合并成单一权威**（`docs/product/PRD.md` v1.0，吸收 PRODUCT.md 与
    PRD_GAP_ANALYSIS.md，旧两份留指针不删——61 处引用不可断链）；
    ② 外部基准取 **ResearchClawBench**（InternScience / MIT / 40 任务 × 10 学科）；
    ③ GOAL **分三阶**：基线读数 → 分析能力 → 扩量（零分是合法读数）；
    ④ **允许外部付费 judge，仅用于评分**：不进产品运行链、不进 canonical、
    不进 `examples/config/**`（`models.yaml` 仍只允许零价模型，判据必须保持绿）。
    沿用用户 2026-10-29 全权限预授权；push-to-main-for-CI：只推 main、不 force、
    不重写历史、不推旁支；`RESEARCHOS_*` 开关逐命令传，**绝不写进 `.env`**。
  benchmark:
    name: ResearchClawBench
    license: MIT
    paper: arXiv:2606.07591
    repo: https://github.com/InternScience/ResearchClawBench
    tasks: 40
    domains: 10
    deliverable: "<workspace>/report/report.md"
    score_semantics: ">50 = 达到已发表论文水平；>70 = 超越"
    public_best: 34.89
    judge_env: [JUDGE_API_KEY, JUDGE_API_BASE, JUDGE_MODEL_NAME]
    judge_scope: >-
      仅用于评分。凭据只在本机环境变量；**不得**进 `examples/config/**`、
      不得进任何被跟踪文件。judge 模型名必须写进证据（不同 judge 分数不可直接比）。
objective: >-
  让系统第一次拥有**可对外比较的外部读数**，并把「agent 自己写分析代码」这条
  被默认关闭的能力按三阶打开：先把 PRD 收敛成单一权威且可由判据防漂移，
  再接上 ResearchClawBench 取得零基线，再放开 AUTHORED 与科学计算栈取得能力后读数，
  最后扩到 3 任务 / ≥2 学科。
exit_criteria:
  - id: EC-01
    criterion: >-
      **PRD 落树且可检**：`docs/product/PRD.md` 九节齐全（产品是什么/不是什么、
      用户与场景、核心工作流、能力矩阵、差距与优先级、需求登记表、验收与读数、
      声称边界、非目标与暂不实施）；需求登记表列序为 `ID | 需求 | 状态 | 判据`、
      状态只用四值词表；`docs/INDEX.md` 登记；`PRODUCT.md` 与
      `PRD_GAP_ANALYSIS.md` 顶部有指针且内容未被删除。
      新判据 `tests/tooling/test_prd_claims_match_the_tree.py`：**逐条断言
      「PRD 的说法 == 树的事实」**（至少覆盖 R-05/R-07/R-08/R-09/R-10/R-12/R-13/
      R-15/R-16/R-19/R-20 与 console 计数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_prd_claims_match_the_tree.py -q`
      ⇒ 全绿；每条断言各带**反证臂**（改 PRD 里的数字 / 改树里的事实 ⇒ 判红并点名）。
    status: PASS
  - id: EC-02
    criterion: >-
      **基准适配器**：`tools/rcb_agent.py` 实现 RCB 的 agent 契约——读 `<PROMPT>` 与
      `<WORKSPACE>`，走**产品组合根** `assemble(ApiSettings(db_path=...))`（复用
      `tests/e2e/manuscript_chain_live_support.py:149` 的形态，**不补缝**），
      把本 run 的报告导出到 `<workspace>/report/report.md`；未产出 ⇒ 非 0 退出码
      （不得写空报告冒充成功）。`docs/benchmarks/RESEARCHCLAWBENCH.md` 记录跑法。
    verify: >-
      `uv run ... -m pytest tests/benchmarks/test_rcb_agent_contract.py -q` ⇒ 全绿
      （离线、不触网：用一个假 harness 目录断言「导出到 report/report.md」
      与「未产出时非 0 退出」两条）；`tests/loaders/test_free_model_only_policy.py`
      仍全绿（judge 凭据未污染 `models.yaml`）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **一阶：基线读数**（现有能力下）。跑 **1 个** RCB 任务（选数据小的 Math 或
      Information），产出 `.cursor/plans/goals/evidence/GOAL-20261120-116-rcb-baseline.json`：
      任务 id、耗时、是否产出 `report.md`、judge 分数、失败归因、judge 模型名、
      数据文件 digest。**零分是合法读数**；未产出也必须如实记录。
    verify: >-
      真实跑一次（手动，非 CI）；证据 JSON 的 `run_kind == "baseline"` 且
      `judge_model` 非空；`report_produced` 与 `score` 两个字段都必须在场（可为 0 / false）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **二阶：分析能力**。① 新沙盒镜像 `research-os-analysis`（numpy / pandas / scipy /
      matplotlib / h5py，基础镜像与依赖按 digest pin，`network none` 不变，
      非 root 不变）；② `AUTHORED` **只在具名 profile `authored-experiments-v1` 下**
      放行；③ 新协议 `analysis_to_report_v1`（数据勘察 → 分析计划 → AUTHORED 脚本执行
      → 校验 → 报告）。
    verify: >-
      定向套件既有回归全绿（`tests/application/experiments`）；
      **反证臂**：不传 profile ⇒ `AUTHORED` 仍被拒（默认行为逐字节不变，
      `AUTHORED_ALLOWED_BY_DEFAULT is False`）；镜像内容扫描断言科学栈在场且无网络安装。
    status: PENDING
  - id: EC-05
    criterion: >-
      **二阶：能力后读数**。同一任务重跑：`report.md` 含 **≥1 张图**，judge 分数
      **> 基线**（基线为 0 时 > 0）。若重跑仍为 0 ⇒ **点名结构性阻塞并置 BLOCKED**，
      不得改判据、不得换任务凑分。
    verify: >-
      证据 JSON 的 `run_kind == "after_capability"`；`score > baseline.score` 或
      `score > 0`（基线为 0 时）；`figures >= 1`。
      **反证臂**：把两次运行的读数对调 ⇒ 判据判红。
    status: PENDING
  - id: EC-06
    criterion: >-
      **三阶：扩量**。3 个任务 / ≥2 个学科，逐个记录任务 id、学科、分数、耗时、
      judge 模型名、失败分类，写入
      `.cursor/plans/goals/evidence/GOAL-20261120-116-rcb-scale.json`。
    verify: >-
      证据 JSON 的 `runs` 长度 == 3 且 `domains` 去重后 ≥ 2（**少跑一个即判红**，
      空真不算通过）。
    status: PENDING
  - id: EC-07
    criterion: >-
      **收口**：as-is m0 = `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 行、
      0 FAILED、`tree changed: False`）；`tools/verify_goal116_closeout.py` 断言集 0 FAIL；
      两树复检判词 `sha256` 相同；每提交 CI 八 job 至终态。
    verify: >-
      `uv run ... python -B tools/run_m0_with_witness.py`；
      `uv run ... python -B tools/verify_goal116_closeout.py`；两树复检脚本。
    status: PENDING
fix_policy:
  same_signature_retries: 3
  cycle_fix_retries: 10
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把 judge 凭据或 judge 模型名写进 `examples/config/**` 或任何被跟踪文件
    - 把零基线改写成「未跑」（零分是读数，不是缺席）
    - 改 `REVIEW_SCORE ≥ 0.8` 或 `panel_rejection()` 的语义
    - 把 `AUTHORED_ALLOWED_BY_DEFAULT` 改成 `True`（只许 profile 放行）
    - 把 RCB 任务数据（`.h5/.pt` 等）提交进仓库
    - 宣称「达到论文水平」（>50 才是）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含新沙盒镜像的依赖集合）
  - 同一失败签名超过 fix_policy 上限
  - judge 侧完全不可达（无可用多模态模型）且本窗口内无法解决
  - 三次扩量中有 ≥2 次因环境（非能力）失败且无法归因
child_plans:
  - .cursor/plans/tasks/PLAN-20261120-119-benchmark-parity-and-prd.md
memory_entries: []
---

# GOAL-20261120-116 — 第一次外部读数

## 目标与退出标准

EC 表见 frontmatter `exit_criteria`。

**建档取证（2026-11-20，全部实查）**：

| 事实 | 读数 |
| --- | --- |
| 外部基准 | 本仓**从未有过**任何外部评测；所有读数都是自评 |
| ResearchClawBench | 40 任务 / 10 学科；MIT；agent 产出 `<workspace>/report/report.md`；多模态 LLM judge 按 rubric 打分 |
| 评分语义 | **>50 = 达到已发表论文水平**；>70 = 超越；公开榜首 **34.89**（InnoClaw），另一读数 28.38 |
| 当前能力 | 实验相是**三个白名单脚本**；`AUTHORED_ALLOWED_BY_DEFAULT = False`；沙盒镜像 = `python:3.12-slim`，**无科学栈**；容器 `network none` |
| 十一相真实 run | 4 SUCCEEDED / 31 FAILED / 1 PAUSED（36 次，截至 2026-11-18） |
| 双评审真实 run（新站） | 3 次：k1 FAILED（2/2 判负）· k2 FAILED（2/2 判负）· **k3 SUCCEEDED**（2/2 通过）；三次 `voters=2`、`independent=True`、**`dissent` 均为空** |
| 地址更正 | 用户给的 `apevonscience.com` 是 **JS 空壳**；真实站点是 **`apevon.ai`** |

**如实登记（不得读成已完成）**：

- **零分不是失败。** EC-03 要的就是一个诚实的基线——若现有能力连报告都产不出，
  那个 0 与「§5 结构性差距」互为证据。
- **不宣称达到论文水平。** 即使 EC-05/06 拿到非零分，也只记录分数；
  >50 才是论文水平。
- **judge 是 LLM，不是人工评审。** 分数不等于录用结果；换 judge 分数不可比。
- **Apevon 的宣称未经实测。** PRD §4 只作「公开宣称」引用。
- **`iceman-contributor-free` 非 ZDR**（GOAL-115 已登记，PRD §8 保留）。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的幂等恢复六条，以「迭代日志最后一行 +
工作树实况 + 远端实况」判定续点。任何一步完成**立即**回写本文件。

**记账的自我指涉边界**（`goals/README.md` 新增节，GOAL-115 立）：只改 `.cursor/`
的 record-only 提交**不进台账义务**；记账提交主题**不带** `goal116`。

## 单 cycle SOP

① derive：从剩余 EC + 上一轮「剩余差距」圈定最小可独立验收主题 → 写子 PLAN →
② 执行（每 WP 独立 commit，**只加显式路径**）→ ③ 本地验证（先自查规模门禁
50 行/450 行与快照类门禁，再跑全量 m0 + 定向套件 + web 门）→ ④ commit →
⑤ push + CI（`git pull --ff-only`；只推 main；轮询至终态）→ ⑥ 失败分类纠错 →
⑦ 回写（EC 状态 / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史）。

**记录顺序纪律**：写记录 → 记录面判据 → **最后**跑 `tools/run_m0_with_witness.py`
→ 之后不改树。

## CI 失败分类与纠错

| 分类 | 处置 |
| --- | --- |
| (i) 判据实现缺陷 | 改判据并在迭代日志点名；**不改产品迁就判据** |
| (ii) 环境资源型（超时 / flake / RSS 阈值） | `rerun-failed-jobs`；**绝不动阈值** |
| (iii) 产品真缺陷 | 修复 + 反向按压；新 commit 点名 `goal116` |
| (iv) 基础设施 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |
| (v) 治理/安全门禁 | 按处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：七条 EC 全 PASS + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  全量 m0 witness 绿 + 两树 `sha256` 相同 + CI 八 job 终态 + 本文件收口。
- **BLOCKED**：连续 2 轮零 EC 推进；或命中 `escalation_triggers`；
  或 EC-05 重跑仍为 0（那是**结构性阻塞**，要留原因不留假绿）。
- **ABORTED**：用户叫停。

## 不进入循环 / 需人工拍板

| # | 事项 | 为什么不能自动做 |
| --- | --- | --- |
| 1 | 提高 `retmax` 出厂默认 | 影响成本与检索语义 |
| 2 | 加文献全文抓取 | 新出网面与许可问题 |
| 3 | `HypothesisSet` 假设发散 | 新域概念，改 Canonical State |
| 4 | 长时程 / 分支探索 | 重写编排语义 |
| 5 | 真实投稿端点 / 期刊接入 | 决定外部世界互动 |
| 6 | RBAC / 多租户 | M18 整块 |
| 7 | `AUTHORED` **出厂默认**开启 | 安全面扩大（本轮只做 profile 放行） |

## 迭代日志

**cycle 1 owner**：goal-mode 会话（`root-agent`）。**并发事实**（如实登记）：02:02–02:06
另一驱动编辑过 `MAINLINE.md` 与 `PRD.md`，其 02:04 的全量 m0 见证为红
（`python/tests=1, framework/docs_consistency_check=1`）。本轮按「一个驱动持有 ACTIVE
cycle」声明占用；并发风险与处置见残余 `W-4`。

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 见「CI 台账」 | 治理 `validate.py` 绿；记录面判据绿 | 见「CI 台账」 | — | EC-01…07 全 PENDING | cycle 1 = EC-01（PRD + 防漂移判据） |
| 1 | `PLAN-20261120-119`（WP-A） | `b36031ce`（并发窗口的会话工作区默认根，**非本 GOAL**）/ `a07f814b`（PRD v1.0 + 防漂移判据） | 判据 **39 passed**（20 个条号各配反证臂，双向按压真红）；邻接面 **1494 passed**；`docs_consistency_check` PASS；ruff format/check + mypy（4 个新文件）全绿 | 见「CI 台账」（本批 tip 待回填） | 阈值/断言未动；按树的事实改正 PRD 三处漂移（后端 108/133→**109/134**；能力「13 被协议使用」→**14**；R-08 裸文件名、R-14「全仓无」口径） | **EC-01 PASS**（verify 已实跑）；EC-02…07 仍 PENDING | cycle 2 = EC-02（`tools/rcb_agent.py` + 离线契约判据） |

## 状态历史

- 2026-11-20：建档。四项拍板写进 `authorization.ref`；PRD（v1.0）与
  `docs/benchmarks/RESEARCHCLAWBENCH.md` 同轮落树；旧两份产品文档加指针并入。
- 2026-11-20（cycle 1）：**EC-01 PASS**。`docs/product/PRD.md` v1.0 与
  `docs/benchmarks/RESEARCHCLAWBENCH.md` 入树、`docs/INDEX.md` 登记、旧两份文档保留
  指针；防漂移判据 `tests/tooling/test_prd_claims_match_the_tree.py` 39 passed（事实从树
  里算，不写死；20 个条号各配反证臂）。**写判据时抓到三处 PRD 漂移并改正**（后端
  108/133→109/134、能力 13→14、R-08 裸文件名 / R-14 口径）。并发窗口的会话工作区 WIP
  先以独立提交落库（`b36031ce`，非本 GOAL），使见证能覆盖干净树。

## 残余与未覆盖范围

（每轮收口时追加。`tools/next_round_charter.py` 从这里读出下一轮 charter。）

### 残余

- `W-1`（承接 GOAL-114/115）采集器仍是判据侧驱动，产品面没有「从 run 库自动汇总」的命令。
- `W-2`（承接 GOAL-114）`plan_fallback` 是死缝：有实现、被 preflight 读、运行期从不切。
- `W-3`（本轮新增）**外部基准只取 3 个任务**：40 个任务里只跑 3 个 ⇒ 分数不代表全榜。
- `W-4`（本轮新增）**并发驱动**：02:02–02:06 另一驱动编辑过 `MAINLINE.md` / `PRD.md`
  并留下一次红见证（02:04）。本轮已把并发窗口的会话工作区 WIP 单独落库以避免脏树，
  但**两驱动都指向 EC-01** 这一可能性未消除；下一轮进入前须先按入口协议复核
  「迭代日志末行 + 工作树 + 远端」是否已含有别人写的 EC-01 产物（防重复劳动）。

### 未覆盖范围

- `U-1` RCB 的 judge 是 LLM 且换模型不可比 ⇒ 本仓分数**不能**直接与公开榜并列展示。
- `U-2` 长时程 / 分支探索仍未覆盖（§5.3）。
- `U-3` 文献全文、假设发散、投稿端点均未触及。

### 声称边界

- `R-1` **不宣称达到论文水平**（>50 才是）。
- `R-2` **不宣称项目安全**（`R-M1` 未收口）。
- `R-3` **不宣称 Apevon 的能力真伪**：PRD §4 只作公开宣称引用。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `b36031ce` + `a07f814b`（同一批 push） | 待回填（本批 tip 的读数为准） | 待回填 | 建档 + PRD v1.0 + 防漂移判据 + 并发窗口的会话工作区默认根 |
