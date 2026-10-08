---
id: PLAN-20261008-333
slug: goal-036-ec03-04-consumption-and-registry
title: GOAL-036 cycle 2（EC-03/EC-04）：`review.read` 真的被一次实跑用上（+ 两向反证）+ 登记面与覆盖读数
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-334-goal-036-ec03-04-consumption-and-registry.md
memory_entries:
  - offline-agent-pool-decides-the-protocol-roles
parent_goal: GOAL-20261008-036
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-036 的 **EC-03 + EC-04**（真用判据 + 登记面与读数）。授权原文见该 GOAL
    的 `authorization.ref`。**本 PLAN 专属边界**：**新增**协议与合约（既有协议 / 合约一字
    不动）；受判对象是**产品路径**（run-ready 装配 + 运行链 + 既有读面）；**不为了让判据过
    而往夹具里塞 agent**（按**实际在场**的 agent 池选角色）；**不建第二套**读口径；
    反证臂必须**点名**（缺实现 / 未放行）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 EC-03 从「承接五件事齐」推进到「**真的被一次实跑用上**」：① 新协议
    （`review_consumption_v1`）两 phase 都由**运行链**执行 —— `produce` 交付评审决定
    （验收门落库逐条判词），`consume` 经 `review.read` 读**本 run 自己**的落库结论；
    ② **下游消费**证据 = 工具结果内容里出现 `produce` 落库的**逐字**判词；
    ③ **两向反证**（缺 provider / 未放行）逐条点名；④ EC-04 的登记面与**覆盖读数**
    （19/46 → 20/46，逐条）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **真用的三段事实**：run 跑到 `SUCCEEDED` 且 `manifest_digest` 在场（冻结真的发生）；
      `tool_refs` 逐条点名 `("m12_artifact", "review_read")` 且该证据属于 `consume` 任务；
      工具结果落在 `tool-result:` 内容寻址制品上（读面取得到、digest 在场）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_review_read_on_the_run_path.py -q` ⇒ 6 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **下游消费（核心）**：`consume` 的工具结果里含 `produce` 落库的**逐字**判词
      （`ARTIFACT_EXISTS: artifact review_decision exists` 与
      `REVIEW_SCORE: review score 0.95 GTE 0.8`），且 `count` 与逐条数一致 ——
      不是「两个 phase 都调了工具」。
    verify: >-
      同文件 `test_the_read_result_carries_the_verbatim_recorded_verdicts`；**按压**
      （`review_read` 改成空结果）⇒ 该条判红且**只有它**判红。
    status: PASS
  - id: AC-3
    criterion: >-
      **两向反证点名**：① 装配不给 provider 实例 ⇒ run `FAILED` 且判词点名 provider 与
      工具 id，且**不留调用证据**；② 把 `review.read` 从 `allow` 删掉（内存内副本）⇒
      run 级判词带 `POLICY_DENIED`，且 **preflight 报告**里那条 finding **点名该能力**。
    verify: >-
      同文件两条反证测试 + 报告面测试。
    status: PASS
  - id: AC-4
    criterion: >-
      **EC-04 登记面与读数**：分类清单**纯收紧**（`review.read` 移入射程、登记表 −1）+
      出厂形态夹具同轮 +1；**覆盖读数 19/46 → 20/46** 且逐条给出名字与命令；
      放行的仍是**只读**一条（写面 / 执行面 / 审批面零变化，由既有段指纹与逐条判据钉住）。
    verify: >-
      覆盖读数命令 + `tests/architecture` / `tests/application/preflight` 全绿读数。
    status: PASS
---

# PLAN-20261008-333 — GOAL-036 cycle 2（EC-03/EC-04）

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 真用三段事实（终态 / 调用证据 / 内容寻址） | PASS |
| AC-2 | 下游消费（逐字判词）+ 按压只咬该条 | PASS |
| AC-3 | 两向反证点名（缺实现 / 未放行 + 报告面逐能力） | PASS |
| AC-4 | 登记面纯收紧 + 覆盖读数 19→20 逐条 | PASS |

## 实施清单

- [x] `examples/protocols/review_consumption_v1.yaml`（新，2 phase、两 phase 都
      `capability_execution: run_chain`）。
- [x] `examples/contracts/task_contracts.yaml`：新增 `review_consumption_deliverable`
      （`ARTIFACT_EXISTS(meta_review)`；**既有契约一字不动**）。
- [x] `tests/e2e/review_read_support.py`（新）：装配 + 读面辅助（`ChainReads` /
      `tool_evidence` / `phase_of_task` / `preflight_report`）。
- [x] `tests/e2e/test_review_read_on_the_run_path.py`（新，6 例）。
- [x] 记录面：本 PLAN、`RECHECK-20261008-334`、`MEM-20261008-205`、GOAL 迭代日志 / 状态历史 / 台账。

## 证据

### 判据读数（实测）

```
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_review_read_on_the_run_path.py -q
⇒ 6 passed
```

| 臂 | 受控执行体声明 | 读数 |
| --- | --- | --- |
| 主路 | `produce` 交 `review_decision.score=0.95`；`consume` 交 `meta_review` | `SUCCEEDED` + `manifest_digest` 在场；`consume` 的工具证据 `tool_refs = ["m12_artifact","review_read"]`；工具结果含**逐字**判词 `ARTIFACT_EXISTS: artifact review_decision exists` / `REVIEW_SCORE: review score 0.95 GTE 0.8` |
| 反证① | 调用声明照旧，装配**不给** provider | run `FAILED`，判词点名 `m12_artifact` 与 `review_read`；**零调用证据** |
| 反证② | 内存内删掉 `review.read` 的 `allow` | run `FAILED`，run 级判词 `preflight failed: POLICY_DENIED`；**报告面** finding `policy denied capability review.read: used default policy effect` |

### 按压（本判据的自我按压）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `review_read` 改成**空结果**（`records = ()`；模拟「调了但读不到」） | **1 failed**（只有下游消费那条判红）⇒ `RESTORED`（6 passed） |

（反证①②本身**内建**在判据里，且是**产品路径**上的反证 —— 不是合成输入。）

### 覆盖读数（EC-04 (c)，逐条）

```bash
# 词表 / 声明面（distinct）
PYTHONPATH=. uv run --frozen --no-sync python -B -c "...(见 RECHECK-334 第 3 节)"
```

| 读数 | 建档时 | 本轮 |
| --- | --- | --- |
| 词表（`capabilities.yaml`） | 46 | 46（**未改**） |
| 声明面 distinct（`tool_providers.yaml`） | **19** | **20** |
| 新承接的一条 | — | **`review.read` → `['m12_artifact']`** |

**不做数量目标**（MAINLINE 明文）：本轮只承接这一条，其余条目**分组与理由原样保留**。

### 门（本 PLAN 触及面）

| 门 | 读数 |
| --- | --- |
| `ruff check` / `ruff format --check` / `mypy`（strict） | 绿（新增 3 个文件全过） |
| `tests/e2e` + `tests/contracts` + `tests/loaders` + `tests/application` + `tests/architecture` | **1887 passed, 86 skipped** |
| **as-is m0**（冻结树，全部记录写入之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5367 passed, 20 skipped**；收集数 **+8** 逐文件分解 = 新判据 6 例 + 源文件参数化 +2（新判据与支撑件各一条）；`skipped` 20 未升） |

**一次真红并修（如实登记）**：m0 首跑 `python/product-lint` + `python/typecheck` 判红 —— 本轮新判据的 import 未排序（`ruff`）与支撑件的两处 union/None 收窄（`mypy`）。处置是**修代码**（`ruff --fix` + 显式 `assert` 收窄），**未**改任何 lint / mypy 配置或断言；随后广面四道门与全量 m0 重跑通过。

## 影响报告

- **Domain / API / schema 变化**：**零**（新协议 / 新合约是声明面资产；无新 DTO / 路由）。
- **安全 / 凭据变化**：无新增放行（`policy.yaml` 的改动在 cycle 1）。
- **兼容性 / 迁移风险**：**新增**协议与合约 ⇒ 既有协议的编译 / 冻结行为逐字不变；
  新增判据文件是**新增**（不改既有断言）。
- **观测隐私**：工具结果内容 = 评审结论（与既有 `GET /runs/{id}/reviews` 同一内容面）；
  内容寻址落盘 + 读面取回与既有读工具同一条路径。
- **上游版本影响**：无。
- **下一项任务**：cycle 3（EC-05 自举收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 协议 / 合约 / 判据落地；三态（主路 + 两向反证）逐条跑通。 |
| 2026-10-08 | DONE | 6 passed + 按压 P-1 只咬该条；覆盖读数 19→20 逐条；广面套件 1887 passed。`RECHECK-20261008-334` 独立复检。 |
