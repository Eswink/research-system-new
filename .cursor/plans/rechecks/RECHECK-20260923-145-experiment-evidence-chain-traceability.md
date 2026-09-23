---
id: RECHECK-20260923-145
plan_id: PLAN-20260923-144
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-verify-script + root-agent-goal-012-ec03
baseline_ref: 31dfbd4
checked_head: 6ccdf46
---

# RECHECK-20260923-145 — 实验产出的证据链可追溯（GOAL-012 EC-03 / PLAN-144）

## 检查范围

三层各自成立，**不采信本 cycle 的自我陈述**：

1. **独立复检脚本** `scratch/verify_goal012_c3.py`——**只读 / 只用标准库 / 不 import 仓库代码**；
   在当前树与**基线树**（`git worktree` 到 `31dfbd4`，即本 cycle 之前的 tip）上各跑一遍，
   并**逐字节**比对与实验证据链相关的产品件（行尾归一：Windows 检出会把 CRLF 写回工作树，
   逐字节比会把「检出形态」误判成「代码改动」——这一条本身是本 cycle 第一次跑出来的假阳性）。
2. **判据层**：`tests/e2e/test_ec03_experiment_evidence_chain.py`（主干 + 成对反证）+ **四处按压**。
3. **样张层**：EC-02 的 live 样张以 JSON 读回，判「产物与证据同时在场且指向同一个 run」。

## 检查结果

### 一、独立复检脚本（两棵树成对）

| 树 | 结果 | 说明 |
| --- | --- | --- |
| **当前树**（`6ccdf46`） | `checked=24 failures=0`（exit 0） | 24 条断言全绿（A 产品件两树同指纹 9 条 + B 判据在位 5 条 + C 样张数据层 5 条 + D 环境/按压 5 条） |
| **基线树**（`31dfbd4`） | `checked=24 failures=6`（exit 1） | **判据不空转**：6 条红**恰是 EC-03 判据文件不存在**（B 组 5 条 + 文件缺失 1 条）；**A 组（产品件两树同指纹）在基线树上也绿** ⇒ 本 cycle 的产品代码**一字未改**（这是「纯判据 cycle」的独立证明） |

> **勘误（2026-09-23，GOAL-012 cycle 4 复测时发现）**：上表「当前树」那一行的数字**当时是在
> amend 之前的判据上测的**；B2 把判据的中间形态当字面量钉住，纯重构后复检脚本会自己变红。
> 详见文末「勘误」节——**结论不变**，复测在同一棵树上得同样数字。

### 二、判据（离线 + 真实容器，`requires_docker`，零出网）

`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec03_experiment_evidence_chain.py -q -rs`
⇒ **2 passed**（`egress guard: judged 2; blocked 0`）。判的是四条**各自可判**的事实：

1. **产物在读面且两面同源**：`GET /runs/{id}/experiments` 与 `GET /runs/{id}/artifacts` 都看得到
   这次实验的四件产物（`analysis_report` / `experiment_result.json` / `stdout.log` / `stderr.log`）。
   **第一次写错的断言当场纠正**：先写成「两面**相等**」，实测两面本就不相等（run 级面还含
   review 会话的 `review_decision` 与组合根种入的声明输入）⇒ 改成**子集方向**，并把四件产物在
   两面都可见作为实质判据（相等会把「别的阶段也有产物」误判成红）。
2. **内容 digest 可重算**：`GET /artifacts/{id}/content` 的字节 ⇒ `Digest.of_bytes` 必须等于
   **证据条目**登记的 `content_digest`，且**来源记录**（canonical 的 `SourceRecord`）的
   `content_digest` 必须等于同一值；有证据的制品**每一件**都算（实测 6 件：4 件产物 +
   会话交付物 + 声明输入）。
3. **来源可独立复核**：实验记录的 `image_digest` == **独立查 daemon**（`docker image inspect`，
   不经产品适配器）得到的镜像 Id；`environment_digest` 非空；canonical 的**语义摘要**与指标在
   两次执行之间**相同**（同 seed / 同镜像 ⇒ 同语义）。
4. **不得用模型自述冒充**（EC-03 明文）：四件产物的证据 `extracted_by == experiment:<run id>`、
   `source_origin` 以 `<experiment_run_id>:` 起头、`run_id` 是本次 run，且来源记录的信任标签是
   实验路径的 `GENERATED`。

### 三、成对反证（同文件第 2 条）

反证脚本与 `sort_analysis_baseline.py` **同构**，只把产物写到 `report.txt`（不写声明产物）：

| 断言 | 实测 |
| --- | --- |
| run 终态 | `FAILED` |
| 失败判词 | 含 `acceptance gate` 且**点名** `analysis_report` |
| 产物读面 | **没有** `analysis_report`；**有** `report.txt` / `experiment_result.json` ⇒ 红的理由是「声明产物缺失」，不是「实验没跑」 |
| 实验记录 | 指标在场（实验确实跑完） |

### 四、四处按压（先红后绿；记录落 `scratch/`）

| # | 按压（临时改，随后复原） | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | `registration_from_experiment` 的产物收集置空（**去掉登记产物的那一步**） | 主干红 | `1 failed`（`goal012-c3-press1.txt`：run 停在 `state != SUCCEEDED`——容器产出了产物也没用） |
| 2a | `SourceRecord.content_digest` 换成常量 | 主干红 | `1 failed`（`press2a.txt`：来源记录重算那条） |
| 2b | `Evidence.content_digest` 换成常量 | 主干红 | `1 failed`（`press2b.txt`：证据条目重算那条） |
| 3 | 反证脚本改成**写声明产物** | 反证用例红 | `1 failed`（`press3.txt`） |

**按压暴露的一处判据盲点（如实记录）**：第一次尝试的按压只改了 `SourceRecord.content_digest`，
判据**依旧绿**——因为当时判据只对**证据条目**的 digest 做重算，没看 canonical 的来源记录。
这正是按压的用途 ⇒ 判据**加强**为「两条记录各算一遍」（上表 2a/2b 因此各有一次红）。
**加强的是判据，不是放松**；产品代码在这四次按压后由 `git diff` 确认**逐字回到 HEAD**。

### 五、门与套件

| 门 | 结果 |
| --- | --- |
| 首轮 `python/product-lint` | **红**：新判据文件里有未使用的 `import json`（反证脚本是字符串字面量，用不到模块级 json）⇒ 删除 |
| 首轮 `python/tests` | **红**：规模门禁 50 行/函数被判据的 80 行主干函数触发（`tests/tooling/test_python_source_limits.py`）⇒ 主干拆成 4 个 ≤50 行的判据函数（断言逐条未减）；修后该门 1006 passed |
| 第 2 轮 m0 | **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c3-m0-rerun.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行；`python/tests` **4411 passed / 19 skipped / 0 failed**） |
| 定向 e2e | `tests/e2e` ⇒ **118 passed / 10 skipped**（skip 全是 live/docker 诚实放行面；`judged 18; blocked 0`） |
| `mypy` / `ruff` / 格式 | `Success: no issues found in 996 source files`；`All checks passed!`；`1013 files already formatted` |
| 出站 | 判据逐条 `egress guard: judged N; blocked 0`；本 cycle **未做任何 live 调用**（真实 run 侧复用 EC-02 样张） |

## 结论

**PASS**。EC-03 的两条要求各有实跑证据：**产物与来源记录进 canonical 且读面可追溯**
（两读面同源、内容 digest 在两个记录上都可重算、镜像摘要可独立复核、语义摘要跨重跑稳定、
产物出自实验路径而非模型自述）；**成对反证**「去掉产物 ⇒ 判据红」（写别的名字的脚本被判拒绝
并点名，且读面上其余产物仍在）。四处按压 + 两棵树成对（当前树 24/24、基线树 6 红，且产品件
两树同指纹）⇒ 判据不空转、**本 cycle 未改任何产品代码**。

## 勘误（2026-09-23，GOAL-012 cycle 4 复测时发现）

**发现方式**：cycle 4 为做两棵树成对复检，重跑了本记录所引的 `scratch/verify_goal012_c3.py`，
**在当前树上得到 `checked=24 failures=1`**（红的是 B2），与本记录上表「当前树 24/24」不符。

**根因（可证明，不是推测）**：

1. 本 cycle 的判据文件在 m0 的 50 行/函数门禁下被**纯重构**过：内容 digest 从
   「先取字节、再 `Digest.of_bytes(content)`」并成一行
   （`digest = Digest.of_bytes(client.get(f"/artifacts/{artifact_id}/content").content)`），
   断言逐条未减。amend 之前的提交仍在 reflog 里：
   `git diff 919ad2c 6ccdf46 -- tests/e2e/test_ec03_experiment_evidence_chain.py` 可见
   `-        content = client.get(...).content` / `-        digest = Digest.of_bytes(content)`。
2. 复检脚本的 B2 当时把 `"Digest.of_bytes(content)"` 这个**中间形态的字面量**当判据 ⇒
   只对 amend 之前的判据成立。**上表「当前树」那一行的数字因此是在 amend 之前的判据上测的**
   （判据的语义三条都在，只是写法变了）。

**处置**：B2 改为判**语义**且**更强**（四个 token 同时在场：`Digest.of_bytes(`、
`/artifacts/{artifact_id}/content`、`get_source(`、`extracted_by == f"experiment:{experiment_run_id}"`）。
复测：

| 树 | 复测结果 |
| --- | --- |
| 当前树（同 `6ccdf46`，判据文件此后一字未改） | `checked=24 failures=0`（exit 0） |
| 基线树 `31dfbd4` | `checked=24 failures=6`（B 组 5 条 + 文件缺失 1 条） |

⇒ 与原记录**同一结论与同一组数字**，只是测量对象换成了 amend 之后的那棵树。

**边界（不掩饰）**：

- 这不是「判据被削弱」：改的是**复检脚本**对判据的**读法**（语义 vs 中间形态字面量），
  判据文件本身未改；断言强度只增不减（四个 token 取代原来的三个）。
- 这是一次**记录早于 amend**的时序错误：先测、后改、未复测就落记录。**教训**（已进工程记忆）：
  ①复检脚本不要钉被检对象的中间形态字面量；②**任何 amend/重跑之后，此前写下的验证数字必须复测**。
