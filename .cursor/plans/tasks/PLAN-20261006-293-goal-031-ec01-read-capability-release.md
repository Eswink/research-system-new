---
id: PLAN-20261006-293
slug: goal-031-ec01-read-capability-release
title: GOAL-031 cycle 1（EC-01）：放行面扩容 —— 6 条只读能力逐条放行 + 镜像同步 + 三条新判据 + 两向反证 + 实跑使用
status: DONE
created_at: 2026-10-06
updated_at: 2026-10-06
latest_recheck: .cursor/plans/rechecks/RECHECK-20261006-293-goal-031-ec01-read-capability-release.md
memory_entries: []
parent_goal: GOAL-20261006-031
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 **EC-01**（授权 1：放行面扩容）。授权原文见该 GOAL 的
    `authorization.ref`：「用户 2026-10-06 明确下放全部权限给驱动」+「**可以有界放宽 allow**、
    **不得**放宽判据/断言」+ push-to-main-for-CI 口径（只推 `main`、不 force、不重写历史；
    push 前 `git pull --ff-only origin main`）。**本 PLAN 专属边界**：只放行 6 条**只读**能力
    （scope `project`）；`default_effect` / `deny` / `require_approval` / `allow_with_constraints`
    一律不动；镜像表同轮同步；**同步集以外**的任何既有判据改动 ⇒ BLOCKED；零新依赖；
    零真实凭据进树；默认门离线；**不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为
    「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 6 条**已承接但未放行**的只读能力（`run.read` / `claim.read` / `deliverable.read` /
    `budget.read` / `experiment.read` / `experiment_plan.read`）**逐条放行**（scope 对齐既有读
    能力 `project`），镜像表同轮同步；用**三条新判据**把「新增放行项全部只读」「`deny` +
    `require_approval` 面零改动」「`default_effect` 仍为 `DENY`」变成机械事实；两向反证；
    并在**默认装配**的一次 run 里让 **≥3 条**新放行能力**真的被用**（调用证据 + 下游消费证据）。
    放行是**有界放宽**：判据/门禁/阈值/断言的强度一律不动；被授权状态变化移动的既有钉定值
    按 fix_policy 的点名例外**重新定基**，逐条给出「强度未降」自证。
exit_criteria:
  - id: AC-1
    criterion: >-
      **6 条只读能力逐条放行**：`examples/config/policy.yaml` 的 `allow` 新增恰 6 条
      `capability:` 规则，逐条 scope = `project`；镜像表
      `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` 同轮同步恰 6 条；
      既有镜像一致性判据
      （`tests/application/test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml`）
      **逐字节未改**且绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_m2_audit.py -q`
      ⇒ 全绿；`git diff --numstat` 对两个产品文件的读数（只增行，policy 12 行 / 镜像 6 行）。
    status: PASS
  - id: AC-2
    criterion: >-
      **New judge ①（只读面）**：本轮新增放行项**逐条断言是只读能力** —— 受判面 =
      **声明集本身**（fix_policy 里写死的 6 条能力名清单），不是交集；每条断言
      ① 在 `capabilities.yaml` 词表内；② 末段 ∈ {read, inspect, validate}；③ 承载 provider 的
      `effect_class` 为 `READ_ONLY`；并带**可判红用例**（把 `package.install` /
      `workspace.delete` 这类非只读能力代入 ⇒ 判据报出）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight/test_release_expansion_is_read_only.py -q`
      ⇒ 全绿（含合成输入的判红用例）。
    status: PASS
  - id: AC-3
    criterion: >-
      **New judge ②（deny 面零改动）**：`deny` 与 `require_approval` 两段的内容与**建档基线**
      逐条相等（与 `deny`/`require_approval` 两段**重新计算**的形态比较，判据内写死基线片段
      `sha256`：`bf04fa4efdbbafb8449c4f0248f4e4dc6ed9daae1f3dc7125f20fc2d4ad537a4`
      （LF 归一化口径））；同时断言 `default_effect` 仍为 `DENY`（New judge ③）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight/test_release_expansion_is_read_only.py::TestTheDenyFaceIsByteIdentical -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证两向**：① 把一条放行删掉（`budget.read`）⇒ **该能力在 run 里被拒且点名**
      （`POLICY_DENIED` 判词逐字，不是静默跳过）：用真实 `NativePolicyEvaluator(policy.yaml)`
      对删掉后的副本求值 ⇒ `DENY` + `used default policy effect`；② 把一条**非只读**能力
      （`workspace.delete`）代入 AC-2 只读面清单 ⇒ 该判据判红并点名。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight/test_release_expansion_is_read_only.py -q`
      ⇒ 两向反证用例全绿；配套留档两向判红原文。
    status: PASS
  - id: AC-5
    criterion: >-
      **实跑使用证据（≥3 条新放行能力真的被用）**：默认装配的一次 run 里，至少 3 条本轮新放行
      能力**真的被调用**（工具证据 `tool_refs` 逐条点名 provider/tool）**且产出被下游消费**
      （下游返回内容含上游工具证据 id），跑到 `SUCCEEDED`。判据必须**逐条**点名缺哪条
      （MEM-160：不得用交集掩蔽）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_granted_read_capabilities_used_in_a_run.py -q`
      ⇒ 全绿；配套留档调用证据（`tool_refs` 逐字）+ 下游消费证据（消费 id 的对应关系）。
    status: PASS
  - id: AC-6
    criterion: >-
      **同步集（被授权状态变化移动的既有钉定值）逐条重新定基 + 强度未降自证**：
      ① `docs/architecture/POLICY_SURFACE_AUDIT.md` 差集表行与计数（输入登记面）；
      ② `EXPECTED_REGISTERED` 15 → 9（**精确计数谓词形态不变**）；
      ③ `_REGISTERED_NOT_GRANTED` `claim.read` → `citation.inspect`（**三态归属谓词不变**）；
      ④ `test_run_read_onboarding` 的「已承接未放行」断言按新状态翻转（**保留承接侧隐藏侧
      两侧断言**，强度不降）。每条给出 before/after 与自证。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight
      tests/adapters/canonical/test_run_read_onboarding.py
      tests/adapters/openhands/test_session_tool_reaches_executor.py tests/contracts -q`
      ⇒ 全绿；配套留档 before/after 逐条对照。
    status: PASS
  - id: AC-7
    criterion: >-
      **未放行的护栏仍在**：`citation.inspect` / `citation.validate` / `dataset.read` /
      `provenance.read` 等**仍未被放行**（用真实求值器逐条断言 `DENY` + `used default policy
      effect`），`require_approval` 三件套（`package.install` / `workspace.delete` /
      `external.publish`）仍 `REQUIRE_APPROVAL`，`deny` 面（`network.public` 等）仍 `DENY`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight/test_release_expansion_is_read_only.py::TestTheUnreleasedSideStaysDenied -q`
      ⇒ 全绿。
    status: PASS
---

# PLAN-20261006-293 — GOAL-031 cycle 1（EC-01）：放行面扩容

## 目标与范围（一句话）

**把 6 条已承接未放行的只读能力逐条放行**，并把「放了什么、没动什么、真的用得上」变成
机械事实。**唯一放宽面 = `allow`**；判据/门禁/阈值/断言强度不动。

## 建档实测的同步集（本 PLAN 的实施依据）

建档在隔离 worktree（`D:/rs-goal031-probe`）上把「policy +6 / 镜像 +6」单独落地后跑
`tests/application + tests/adapters + tests/architecture + tests/api + tests/contracts +
tests/loaders` ⇒ **6 failed / 4428 passed**；把同步动作全部落地后 ⇒ **60 passed**。六条判红
与它们的同步动作（**逐条**，见 GOAL 记录「事实层结论」第 2 条）：

| # | 判据 | 同步动作 |
| --- | --- | --- |
| 1 | `test_policy_surface_difference_set` 双向完备 | 更新 AUDIT 差集表（6 行移出差集） |
| 2 | `…` 逐行判定 | 同上（计数与交集清单同轮） |
| 3 | `test_read_grant_is_per_item` 该登记计数 | `EXPECTED_REGISTERED` 15 → 9 |
| 4 | `test_run_read_onboarding` 未放行断言 | 按新状态翻转为已放行（双向断言保留） |
| 5 | `test_session_tool_reaches_executor` 未放行臂 | `_REGISTERED_NOT_GRANTED` → `citation.inspect` |
| 6 | `…` 三态归属表 | 同上常量 |

## 改动（显式路径）

| 文件 | 改动 |
| --- | --- |
| `examples/config/policy.yaml` | `allow` 追加 6 条只读能力（scope `project`），其余三面零改动 |
| `packages/application/preflight/policy_check.py` | `_CAPABILITY_SCOPE` 镜像同步 6 条 |
| `docs/architecture/POLICY_SURFACE_AUDIT.md` | 差集表：6 行移出；计数 15 → 9；交集清单 9 → 15 |
| `tests/application/preflight/test_read_grant_is_per_item.py` | `EXPECTED_REGISTERED` 15 → 9（同步集点名例外） |
| `tests/adapters/canonical/test_run_read_onboarding.py` | 未放行断言 → 已放行（双向保留，强度不降） |
| `tests/adapters/openhands/test_session_tool_reaches_executor.py` | `_REGISTERED_NOT_GRANTED` → `citation.inspect` |
| `tests/application/preflight/test_release_expansion_is_read_only.py` | **新增判据**（只读面 / deny 零改动 / default_effect / 未放行护栏 / 两向反证） |
| `tests/e2e/test_granted_read_capabilities_used_in_a_run.py` | **新增判据**（实跑：≥3 条新放行能力被调用 + 下游消费） |
| `examples/protocols/granted_reads_used_in_a_run_v1.yaml` | **新增协议**（把新放行读能力接进运行链） |
| `examples/contracts/task_contracts.yaml` | 新增两份契约（纯追加） |
| `.cursor/plans/goals/GOAL-20261006-031-…md` | 迭代日志 / EC 状态回写 |

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7，收口时全部 `PASS`）。三条**机械**判据分别为：
放行面扩容（`test_release_expansion_is_read_only.py` 的 16 条）／单条 denied 效果的
可判红（两向反证 4 臂）／实跑使用（`test_granted_read_capabilities_used_in_a_run.py`
的 15 条）；existing 钉定值的重新定基逐条自证见复检记录。

## 实施清单

- [x] **WP-A（放行）**：`policy.yaml` allow +6；镜像表 +6；`m2_audit` 镜像判据绿（未改）。
- [x] **WP-B（登记面同步）**：AUDIT 差集表 6 行移出 + 计数 + 交集清单；两条差集判据绿。
- [x] **WP-C（既有钉定值重新定基）**：`EXPECTED_REGISTERED` / `_REGISTERED_NOT_GRANTED` /
      onboarding 翻转 —— 逐条附「强度未降」自证。
- [x] **WP-D（新判据）**：`test_release_expansion_is_read_only.py`（只读面 + deny 零改动
      + `default_effect` + 未放行护栏 + 两向反证）。
- [x] **WP-E（实跑）**：协议 + 契约 + e2e 判据（≥3 条被调用 + 下游消费 + 反证点名）。
- [x] **WP-F（记录）**：本 PLAN + `RECHECK` + GOAL 回写 + 迭代日志。
- [x] **WP-G（门）**：记录面判据 → 全量定向套件 → m0（独占、记录之后）→ 治理 → commit → push → CI。

## 证据

**判词归档（进树，二进制写盘）**：

| 文件 | 内容 |
| --- | --- |
| `.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-release-ledger.txt` | (a) 6 条放行项 (能力名, scope) 逐条；(b) 镜像表逐条 `policy_scope_for`；(c) deny 面基线 `sha256` 前后 + `default_effect` |
| `.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-refutation-verdicts.txt` | 两向反证判词原文（4 臂） |
| `.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-run-usage-evidence.txt` | 实跑：run id / 终态 / manifest digest / 调用证据逐条 / 下游消费对应关系 |

**实测读数**：

- EC-01 verify（5 路径合跑）⇒ **93 passed**；
- `tests/application + tests/adapters + tests/architecture + tests/loaders` ⇒ **1607 passed / 4 skipped**；
- `tests/tooling/test_python_source_limits.py` ⇒ **1112 passed**（本轮 e2e 判据一度 535 行触 450 硬上限，
  已拆成 `tests/e2e/granted_reads_support.py` + 321 行判据文件）；
- `deny` 面基线片段 `sha256`：建档 `bf04fa4e…` == 当前 `bf04fa4e…`（逐字节相等，实测）；
- **as-is m0（第三次跑，独占、记录定稿后）**：`PASS: profile=m0; 23 deterministic checks`
  （`FAILED [` 0 / `PASS [` 24 = 23 计数内 + `release-assets-immutable`；零 python 残留）。
  首跑四红与第二跑的处置逐条登记在 `RECHECK-20261006-293`（三处真缺陷 + 一处已知 flake）。
- 实跑读数：`run.read` / `budget.read` / `claim.read` 三条被调用（`tool_refs` 逐条点名
  `('m12_artifact', <tool_id>)`），probe 的 2 条工具证据被 `claim.read` 与 `evidence.read`
  **各消费一次**，run `SUCCEEDED`，`manifest_digest` 在场。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | IN_PROGRESS | 建档（cycle 1 derive）；建档实测已标定同步集与判据设计。 |
| 2026-10-06 | DONE | WP-A…WP-E 全部实测落地（EC-01 verify 93 passed；定向回归 1607 passed）；两向反证 + 实跑使用证据归档进树；WP-F 记录完成、复检 `RECHECK-20261006-293` = `PASS_WITH_WARNINGS`（W-1 判据自缺口已修 / W-2 run 级消息不点名能力 / W-3 示例名字绑定）。 |

## 影响报告

**Domain / API / schema 变化**：无。（`policy.yaml` 是策略配置面；`policy_check.py` 的镜像表是
应用层常量；两者都不改 Domain 类型、不改 DTO、不动 OpenAPI 快照。）

**安全 / 凭据面变化**：`allow` 面新增 6 条**只读**能力（scope `project`），`deny` /
`require_approval` / `allow_with_constraints` / `default_effect` **零改动**（字节级实测）。
**不**新增凭据、**不**新增出网面、**不**改变默认 posture（默认 runtime 仍 Fake、默认 CI 仍离线）。
**不得**据此宣称项目安全（`R-M1` 未收口）。

**兼容性 / 迁移风险**：低。放行是**单调放宽**（原先落 `default_effect: DENY`），不放宽任何
既有约束；唯一影响是「此前写进协议必然 FAIL 的 6 条读能力现在可被 preflight 放行」。
既有钉定值的重新定基逐条登记在复检记录里。

**上游版本影响**：无新依赖、无版本变化。

**门禁面**：本轮**没有**降低任何既有判据/门禁/阈值/断言的强度；同步集四条按授权重新定基
（逐条自证见 RECHECK-20261006-293）。新判据第一版被自己的按压抓到「受判面是写法清单」缺口
⇒ 已修并留按压用例（`W-1`）。

## 无可复用事实

**无**（本 PLAN 的产出全部是可复用资产：放行面 + 判据 + 证据归档，三者都留在树内，
后续 GOAL 可直接引用而不必重建）。收口判定：`memory_entries` 另行回填在 GOAL 层。


