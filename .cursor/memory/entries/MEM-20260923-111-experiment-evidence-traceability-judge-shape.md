---
id: MEM-20260923-111
title: "实验证据链「可追溯」的判据形态：两读面是子集不是相等；digest 要在证据条目与来源记录两条上各算一遍；镜像摘要等于 daemon 的 Image.Id 可独立复核"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.92
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-144-experiment-evidence-chain-traceability.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-145-experiment-evidence-chain-traceability.md
supersedes: []
---

## 做了什么

GOAL-012 EC-03 把「实验跑过」与「产物已登记且可追溯」判成同一条可复跑的事实
（`tests/e2e/test_ec03_experiment_evidence_chain.py`，离线 + 真实容器）。判据落地时踩到两个
**具体形态**的坑，都是实测出来的：

1. **两读面不是同一组制品**。`GET /runs/{id}/experiments` 的 `artifact_ids` = 实验产物 +
   组合根种入的**声明输入**；`GET /runs/{id}/artifacts` = 全 run 的制品（还含**别的阶段**的产物，
   例如 review 会话的 `review_decision`）。正确的判据方向是**子集**（这次实验的产物在两面都可见），
   写成相等会把「别的阶段也有产物」误判成红。
2. **digest 要在两条记录上各算一遍**：读面的 `Evidence.content_digest`，以及 canonical 的
   `SourceRecord.content_digest`（`ledger.get_source(origin)`）。只查前者是**盲点**——按压
   （把来源记录的 digest 换成常量）实测仍然绿；补上后者之后同一次按压才红。「产物已登记」与
   「来源已登记」是两件事。

另外两条可直接复用的产品事实：`image_digest` 就是 daemon 的 `inspect_image(image)["Id"]`
（`adapters/execution/docker_backend.py:_resolve_image_digest`）⇒ 可用 `docker image inspect`
在**另一条代码路径**上独立复核；`semantic_metrics_digest`（`metric_extraction.py`）是
**非观测性子集**的 canonical digest、**跨重跑稳定** ⇒ 可作「同 seed / 同镜像 ⇒ 同语义」的复现判据。

## 为什么这样做

- EC-03 的明文是「产物与**来源记录**进 canonical，读面**可追溯**，来源/镜像摘要**可独立复核**」，
  以及「**不得**用模型自述充当实验产物」。三条各有对应的可判事实：产物名在两读面、两条记录的
  digest 可重算、`extracted_by == experiment:<run id>` + `source_origin` 前缀。
- 反证的形态是**改名字不删执行**：同构脚本把产物写成 `report.txt` ⇒ 门拒收且点名
  `analysis_report`，读面上没有它，而 `report.txt` / `experiment_result.json` **仍在**
  ⇒ 红的理由恰是「声明产物缺失」，不是「实验没跑」。只断言 run `FAILED` 会被「实验崩了」蒙混过去。
- 判据函数要拆到 **≤50 行**：规模门禁（`tests/tooling/test_python_source_limits.py`）会抓主干函数；
  拆成若干 `_assert_*` helper 时**断言逐条不减**（拆的是长度，不是强度）。

## 怎么做与复现

1. 判据：`pytest tests/e2e/test_ec03_experiment_evidence_chain.py -q` ⇒ **2 passed**（`requires_docker`，`judged N; blocked 0`）。
2. 按压（先红后绿，记录落 `scratch/goal012-c3-press{1,2a,2b,3}.txt`）：
   去掉 `registration_from_experiment` 的产物收集 / 给 `SourceRecord.content_digest` 写常量 /
   给 `Evidence.content_digest` 写常量 / 让反证脚本写回声明产物 —— 四种都 `1 failed`。
3. 两棵树成对：`python scratch/verify_goal012_c3.py <root> --baseline <other>`（只读/只用标准库）；
   产品件**行尾归一后**比指纹（Windows 检出会把 CRLF 写回工作树，逐字节比会出假阳性）。

## 适用边界

- 判据依赖 `requires_docker`；非 Linux 容器的 daemon 下如实 skip（由 `container-quality` 作业真跑）。
- 「语义摘要跨重跑稳定」这条只在**同镜像 + 同脚本 seed** 成立；换镜像/换 seed 必须重新取样。
- `docker image inspect` 的独立复核在 CLI 不可用时**如实跳过该断言**（不伪装通过）。
- 本判据不覆盖「实验产物被篡改后仍能检出」——内容 digest 只能证明**登记值与内容一致**，
  不证明内容本身可信（那是签名/公证层面的问题）。

## 来源

- GOAL-20260923-012 EC-03；PLAN-20260923-144；RECHECK-20260923-145（PASS）。
- 实测：`scratch/goal012-c3-press{1,2a,2b,3}.txt`、`scratch/goal012-c3-m0-rerun.log`。
