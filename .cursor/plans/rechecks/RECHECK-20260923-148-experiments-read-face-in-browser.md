---
id: RECHECK-20260923-148
plan_id: PLAN-20260923-147
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-verify-script + root-agent-goal-012-ec05
baseline_ref: 2e5b218
checked_head: d5baf05
---

# RECHECK-20260923-148 — 实验读面在浏览器里用真实数据渲染（GOAL-012 EC-05 / PLAN-147）

## 检查范围

三层，**不采信本 cycle 的自我陈述**：

1. **实跑**：live e2e（真实 HTTP + 真实浏览器）跑通，且页面渲染的值**逐条等于读面**；
2. **独立复检脚本** `scratch/verify_goal012_c5.py`（只读 / 只用标准库 / 不 import 仓库代码）：
   在当前树与**基线树**（`2e5b218`，本 cycle 之前的 tip）上各跑一遍，并两棵树比对**产品面**指纹；
3. **门**：stub 套件（新 live spec 必须被排除）+ m0 + `validate.py`。

## 检查结果

### 一、实跑（live：Fake Ports + 真实浏览器，零出网）

`pnpm --dir apps/web exec playwright test --config playwrightLive.config.ts live-experiments`
⇒ **2 passed**：

| 用例 | 判的是什么 |
| --- | --- |
| 主干 | 先 `page.request.get` 取 `GET /runs/{id}/experiments`，再断言表格的**制品引用数**、**镜像指纹**（`slice(0,20)`，组件真实口径）、**指标字段数**与抽屉里的**指标原始投影**（`JSON.stringify(metrics, null, 2)`）逐字等于读面返回的值 |
| 成对反证 | 第二条 run 的实验**只有一件非 JSON 制品** ⇒ 读面 `metrics` 为空（判据先断言这一点）⇒ 同一页面/同一组件显示空态、**没有**指标 `<pre>` |

读面快照与截图落 `scratch/goal012-c5/`（`read-face.json` / `read-face-bare.json` /
`page-values.json` / 两张 PNG；**不进仓库、不上传外部服务**——`scratch/` 在 `.gitignore` 里）。

### 二、按压（先红后绿；记录落 `scratch/goal012-c5-press{1,2}.txt`）

| # | 按压 | 期望 | 实测 |
| --- | --- | --- | --- |
| 2 | 把页面上的指标投影临时改成常量（`{"stub": true}`） | 主干红 | **1 failed**：红在 `toHaveText(JSON.stringify(experiment.metrics, null, 2))`；**反证那条仍绿**（它期望没有 `<pre>`）——这正是判「页面 == 读面」的那一刀 |
| 1 | 把受控制品 JSON 的 `metrics` 键改名 | 主干红 | **1 failed**：红在夹具自检（`Object.keys(metrics).length > 0`） |

**如实记下一处判据性质**（进 `MEM-20260923-113`）：**数据按压对「页面 == 读面」不敏感**——
两边同源，怎么改数据都一致；只有按**页面**那一段才动得了这条判据。数据按压的证据价值在于
「夹具数据确实经产品路径流到读面」，不是在于判页面。

按压后产品代码**逐字复原**：`git diff --stat -- apps/web/src/features/experiments/ExperimentMetadata.tsx`
为空；夹具的 `metrics` 键已回改。

### 三、独立复检脚本（两棵树成对）

| 树 | 结果 | 说明 |
| --- | --- | --- |
| **当前树** | `checked=32 failures=0`（exit 0） | A 判据形态 7 + B 清单登记 5 + C 产品面两树同指纹 8 + D 新面确实不同 5 + E 快照与诚实边界 7 |
| **基线树**（`2e5b218`） | `checked=32 failures=15`（exit 1） | 15 条红**全部**是本 cycle 新增面（live spec 不存在 / 夹具没有该链 / suite 未登记）；**C 组 8 条（前端页面·组件·DTO 类型·导航·API 路由·DTO·egress 判据）在基线树上也绿** ⇒ 本 cycle **未改产品面** |

### 四、诚实边界（本判据**不**声称什么）

- 夹具的**执行体**不是真容器：本判据只覆盖「**读面 → DTO → 页面**」这一段；真实容器的实验全链
  在 pytest 层（`tests/e2e/test_ec02_experiment_chain_offline.py`、
  `test_ec03_experiment_evidence_chain.py`，`requires_docker`）。
- 实验的 canonical 记录由**产品自己的准入路径**写入
  （`packages.application.experiments.register_experiment_evidence`，run 链同一函数），
  指标由**内容寻址制品**的 JSON 承载（读面 `_metrics_for` 的取数口径）——夹具只决定数据内容，
  不复制读写逻辑。
- 读面的 `reproduction_available` 在控制面**恒为 False**（`REPRODUCTION_NOTE` 已诚实标注
  unavailable）⇒ 页面显示 `UNAVAILABLE` 是本 cycle 之外的既有边界，不是本判据的结论。

### 五、门与套件

| 门 | 结果 |
| --- | --- |
| stub 套件（`playwright.config.ts`） | **96 passed** —— 新 live spec 被 `testIgnore` 排除（清单登记生效） |
| 首轮 m0 | **4 红**（本 cycle 自己撞到并当轮修掉，见下） |
| 第 2 轮 m0 | **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c5-m0-rerun.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行；`python/tests` **4411 passed / 19 skipped / 0 failed**，与 cycle 3/4 同数） |
| python 侧 | `tests/tooling/test_toolpack_capability_policy_pending.py` **10 passed**（唯一 import 该夹具的 pytest）；`mypy` 996 files 干净；规模门禁 1006 passed |
| 出站 | 浏览器只访问 `127.0.0.1`（live app:8011 / vite:5174）；零真实出网、零凭据读取、零真实 LLM |

**首轮 m0 的 4 处红（如实记录，全部当轮修掉）**：
① `python/typecheck`：`register_experiment_evidence` 的第 3 实参是 `ArtifactStore | None`
（未收窄）+ `MetricValue(value=int)` 与 `Decimal | str | bool | None` 不兼容 ⇒ 加 `assert store is not None`
并把指标值改成 `Decimal(value)`；② `python/tests`：规模门禁抓到 `_admit_controlled_experiment` **51 行**
⇒ 拆出 `_controlled_experiment`（断言与语义未变）；③ `typescript/lint`：`process.env["…"]`
的 dot-notation 与两行超 100 字符 ⇒ 按 lint 口径改写；④ `framework/validate`：
`subagent_parallel_limit` 必须是 **3**（写成 2）+ 工程记忆引用的复检文件当时尚不存在 ⇒ 改为 3、复检落盘后转绿。

### 六、CI（如实记录一次**判红**与它的根因）

功能提交 `d5baf05` 的 CI（M0 run [35847860197](https://github.com/Eswink/research-system-new/actions/runs/35847860197)）
里 `quality-windows-latest` 与 `quality-ubuntu-latest` **判红**，根因**同一条**：

```
Cursor 治理验证失败:
- 工程记忆来源不存在: MEM-20260923-113: .cursor/plans/rechecks/RECHECK-20260923-148-…md
```

即本 cycle 把「工程记忆」与「它引用的复检文件」拆到了两个提交里（本地工作树里那份复检已存在，
所以 `validate.py` 一直绿）——**记录自身不自洽**，属**提交切分错误**，不是产品缺陷、不是判据缺陷。
**其余四 job 全 success**（含 `console-frontend`：新增的 live spec 在 CI 上也跑绿）。

**处置**：回写提交把 `RECHECK-148`（连同 `MEM-114`）落盘 ⇒ 同一判据转绿；**判据未放宽**。
事实进 `MEM-20260923-114`（引用方与产物必须同一次提交落地）。

## 结论

**PASS**。EC-05 的可选要求达成：实验读面在**浏览器**里用**真实数据**渲染产物与指标
（页面值逐条等于读面值、反证那条证明同一组件按数据照实显示空态），读面快照与截图落 `scratch/`
（不进仓库）；本 cycle **零产品面改动**（前端页面/组件/DTO/API 两棵树同指纹）、**零出网**、
既有 stub 套件不回归。
