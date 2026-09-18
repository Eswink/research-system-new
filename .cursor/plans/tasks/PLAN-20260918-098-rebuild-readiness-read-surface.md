---
id: PLAN-20260918-098
slug: rebuild-readiness-read-surface
title: 历史行可追溯：重建能力读面点名缺失事实（EC-06 (b)：一等事实 + 读面写明）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 6 = EC-06（GOAL-004 收口结论表第 6 项 / RECHECK-084 W-2 + RECHECK-087 W-1）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-098-rebuild-readiness-read-surface.md
memory_entries:
  - MEM-20260918-072
---

# PLAN-20260918-098 — 历史行可追溯：重建能力读面（GOAL-005 cycle 6 = EC-06）

## 目标

EC-06 的两条历史行缺口是：① 旧 run **没有冻结正文**（`protocol_body` 为 None，重启续跑
仍依赖外部来源）；② 旧 `manifest.frozen` 事件**没有 `semantic_digest`**（resume 漂移校验
拿不到输入）。今天的读面用一个 `None` 回答三种互不相同的处境（"功能前历史行" /
"起步时冻结失败" / "还没冻结"），并把"缺的是哪条事实"只留在**拒绝文案**里（要点一次
`/resume` 才看得到，且文案分散在 `run_resume` 与 `convergence` 两处）。

本 PLAN 走 EC-06 的 **(b) 一等事实 + 读面写明**：把"这份 run 记录能不能重建、缺哪条事实"
做成**一等的读面事实**（一个纯函数分类器 + 一个读面字段），使读面能**正面回答**
"这是历史行 / 缺的事实叫什么 / 此路不通（点到 fork/revision）"，而不是含糊的 `None`；
并让 `/resume` 的拒绝前缀与读面**同源**（同一个分类器），不再各写一套判据。

**不做**（本 PLAN 明确不做，避免伪装成已收口）：

- 不做 (a) 迁移/回填：`tools/snapshot_migrate.py` 已存在且是**显式 opt-in 的运营动作**
  （`keep`/`re-freeze`/`fork`；re-freeze 需要重新编译协议，失败要人工）。本 PLAN **不**
  在循环内对任何库跑迁移，也不改它的分类语义。
- 不做 (c) 的"不可回填"裁决：那需要产品决策；本 PLAN 只让读面**点名事实**并给出
  拒绝路径（fork/revision，沿用既有文案），不新增"不可回填"这一类判断。
- 不动 `convergence.assert_semantics_frozen` 的判据与文案（漂移拒绝的语义不变）。
- 不做前端 UI：只做 API 读面（+ TS 类型/夹具一致性），不新增页面元素。

## 口径

- **分类器是唯一判据来源**：`packages/application/run_orchestration/rebuild_readiness.py`
  的纯函数读同一份 run 行的四个事实（`manifest_digest` / `manifest_semantic_digest` /
  `protocol_body` / `protocol_source`）给出 `status` + **确定性排序**的 `missing`。
  读面与 `/resume` 的拒绝前缀都从这里取，**不许**出现第二套"缺什么"的枚举。
- **`missing` 用行上的字段名**（`manifest_digest` / `manifest_semantic_digest` /
  `protocol_body` / `protocol_source`）：读面点名的事实必须能与 canonical 行的字段一一对上。
- **三种 status 只描述"记录够不够重建"，不描述"该不该重建"**：状态机、策略、预算不在
  这个读面里（诚实边界写进 DTO 注释与文档）。
- **旧事件形状**（`manifest.frozen` payload 只有 `digest`）必须有用例：它落到
  `semantic_digest=None` ⇒ 读面必须点名 `manifest_semantic_digest`（此前无用例，
  `tests/api/test_api_restart_recovery.py` 的 run 行自带语义 digest，没覆盖这条回填分支）。

## 验收条件

- **AC-01（历史行与当前行在读面可区分）**：同一读面在三种记录形态上给三种取值——
  自足（正文 + 两个 digest）/ 依赖来源（两个 digest、无正文）/ 缺事实（`missing` 点名）；
  用例断言取值两两不同且 `missing` 逐字等于期望元组。
- **AC-02（拒绝原因点名事实，且与读面同源）**：对同一行，`/resume` 拒绝文案点名的事实
  与读面 `missing` **一致**（结构性：拒绝前缀由分类器给出）；用例覆盖
  "缺语义 digest"（历史事件形态）与"无正文 + 无来源"（旧 run 形态）两种。
- **AC-03（旧事件形状有覆盖）**：`FrozenManifestRefs.from_payload({"digest": ...})`
  ⇒ `semantic_digest is None`，且该 run 的读面 `missing` 含 `manifest_semantic_digest`
  （把此前没有用例的回填分支钉住）。
- **AC-04（不改判定）**：`convergence` 守卫、`/resume` 的拒绝**条件**与既有文案逐字不变；
  既有 `tests/api/test_run_source_and_rebuild_api.py` / `test_failed_run_semantic_digest_api.py`
  / e2e 收敛用例全绿（只加读面，不改拒绝语义）。
- **AC-05（文档同源 + 快照 + 门禁）**：`CONTROL_PLANE_API.md`（读面字段与历史行口径）、
  `EVENT_MODEL.md`（`manifest.frozen` 旧 payload 形态与读面回答）写明；OpenAPI 快照与
  `apps/web/src/api/types.ts` + e2e 夹具同步；定向 + web 门 + m0 绿；CI 六 job 到终态并记账。
- **反证（实跑）**：把分类器里 `manifest_semantic_digest` 那条事实判定去掉（假装不缺）
  ⇒ AC-01/AC-02/AC-03 的对应用例必红；恢复后复跑绿。

## 实施清单

### WP-A — 分类器（应用层，纯函数）

- `packages/application/run_orchestration/rebuild_readiness.py`（新）：
  `RebuildReadiness(status, missing)` +
  `rebuild_readiness(run) -> RebuildReadiness`；规则（**与今天 `rebuild_and_resume`
  的拒绝条件逐条对齐**）：
  - `manifest_digest is None` ⇒ `missing += ("manifest_digest",)`
    （今天的拒绝："run has no frozen manifest digest; cannot verify rebuild"）；
  - `manifest_semantic_digest is None` ⇒ `missing += ("manifest_semantic_digest",)`
    （`convergence` 守卫会拒："lacks a semantic digest; fork run or revision required"）；
  - `protocol_body is None and protocol_source is None` ⇒ `missing += ("protocol_body",
    "protocol_source")`（今天的两条点名：正文 + 来源）；
  - 排序固定为 `manifest_digest` → `manifest_semantic_digest` → `protocol_body` →
    `protocol_source`（可复核、与声明顺序无关）；
  - `status`：有阻塞缺失 ⇒ `REFUSED`；否则 `protocol_body is not None` ⇒
    `SELF_CONTAINED`，否则 `SOURCE_DEPENDENT`。
  - `refusal_prefix()`：给出 `/resume` 今天用的前缀（"run has no frozen protocol body; " /
    "run has no recorded protocol source (predates source recording)"），由 `missing` 推出。
- `tests/application/run_orchestration/test_rebuild_readiness.py`（新）：逐个事实组合的
  判定矩阵 + `missing` 顺序确定性 + `refusal_prefix` 与 `missing` 一致。

### WP-B — 读面（控制面 API）

- `services/api/dto/runs.py`：新增 `RebuildReadinessDto(status, missing)`；
  `RunDetailDto.rebuild: RebuildReadinessDto`（**任何状态都给**：回答"记录够不够重建"，
  不回答"该不该重建"）。
- `services/api/run_rebuild_view.py`（新）：`rebuild_readiness_dto(run) -> RebuildReadinessDto`
  （DTO 映射只有这一处）。
- `services/api/routers/runs.py::_detail_dto`：带上 `rebuild`（详情与列表同一处装配）。
- `tools/gen_openapi.py` 重新生成 `docs/api/openapi.m13.json`；
  `apps/web/src/api/types.ts` + `apps/web/tests/e2e/apiFixtures.ts` 同步。

### WP-C — 拒绝路径同源（不改编语义与文案）

- `services/api/run_resume.py`：两条前缀（无正文 / 无来源）改为从分类器的 `missing`
  推出；拒绝**条件**与**文案**逐字不变（既有用例是这条约束的判据）。

### WP-D — 文档与记录

- `docs/api/CONTROL_PLANE_API.md`：读面字段 + "历史行 vs 当前行"的口径 + 诚实边界
  （不回答该不该重建；`missing` 是行上的字段名）。
- `docs/architecture/EVENT_MODEL.md`：`manifest.frozen` 旧 payload 形态（只有 `digest`）
  与读面回答；说明执行期失败收敛的回填分支。
- RECHECK-20260918-098、MEM、`ALL_PLAN`、`memory/INDEX.md`、GOAL-005 回写。

## 证据

- **反证（实跑）**：把分类器里 `manifest_semantic_digest` 那条事实判定临时去掉
  （`if False and ...`）⇒
  `pytest tests/application/run_orchestration/test_rebuild_readiness.py tests/api/test_run_source_and_rebuild_api.py tests/api/test_failed_run_semantic_digest_api.py`
  **6 failed / 25 passed**（红点 = 三条分类器矩阵用例 + 读面点名用例两条 + 旧事件形态读面用例）；
  还原后同一命令 **31 passed**。
- **定向（DSN pin）**：`tests/api tests/contracts tests/application tests/adapters tests/e2e`
  ⇒ **2053 passed / 7 skipped**（322.87s）。
- **web 门**：`pnpm run lint` 通过（`--max-warnings 0`）、`typecheck` 通过、
  `test`（unit）**76 passed**、`build` 通过、`test:e2e`（stub）**83 passed**（4.8m）、
  `test:e2e:live`（真 API + vite）**36 passed**（44.7s）。
- **结构判据**：`missing` 里每个名字都属于 `ResearchRun` 的字段（用例 `test_the_missing_set_is_the_field_names_of_the_row`
  用 `dataclasses.fields` 钉住）；`RebuildReadiness` 的构造不变量（REFUSED 必须点名、
  非 REFUSED 不得带 missing、`body_frozen` 与 `protocol_body` 不得互相矛盾）有用例。
- **快照**：`tools/gen_openapi.py` 重生成 `docs/api/openapi.m13.json`（新增
  `RebuildReadinessDto`、`RunDetailDto.required += rebuild`）；`apps/web/src/api/types.ts`
  与 e2e 夹具同步。
- **门禁**：`tests/tooling/test_python_source_limits.py` **935 passed**；m0 见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 6 = EC-06，driver=client-goal / owner=root-agent）：
  选 (b) 一等事实 + 读面写明；已探明事实见 GOAL「当前续点」（正文不入库、两种 None 混用、
  拒绝文案分散、`snapshot_migrate` 是 opt-in、旧事件回填分支无用例）。
  `status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A…WP-D 完成；分类器 10 用例、API 读面 3 用例、旧事件形态 2 用例；
  反证 6 红（还原后 31 绿）；定向 **2053 passed / 7 skipped**；web 六门绿；
  `status: DONE`。**实现过程中发现并修正的设计缺陷**：最初把 `/resume` 的"没有冻结正文"
  前缀绑定在 `status=SOURCE_DEPENDENT` 上 ⇒ 既有用例
  `test_a_run_without_a_frozen_body_names_both_missing_facts` 变红（那一行同时缺语义
  digest，状态是 `REFUSED`，但确实没有正文）。修正 = 分类器显式带出 `body_frozen`
  这一个事实（前缀只问这一件事），**没有改既有断言**。

## 影响报告

- **Domain / API / schema**：Domain 无变化（只读 `ResearchRun` 既有字段）。API 新增
  `RunDetailDto.rebuild`（**必填**：任何状态都给）⇒ OpenAPI 快照与 web TS 类型/夹具同步；
  `/resume` 的**拒绝条件与文案逐字不变**（只把文案来源换成同一个分类器）。
- **持久化 / 迁移**：无迁移、无回填；新旧 run 行走同一条读路径（历史行从此有名字）。
- **安全 / 凭据**：无凭据面变化；读面只读 canonical 行上的 digest/来源事实，不读文件、
  不解析来源（不会因为读面去看磁盘）。
- **兼容性 / 迁移风险**：低。`rebuild` 是新增必填字段 ⇒ 旧客户端忽略即可（不改既有字段
  语义）；web 类型与夹具已同步。
- **上游版本影响**：无。
- **下一项任务**：GOAL-005 收口（EC-01…EC-06 全 PASS 后的收口 RECHECK 与终止结论）；
  若收口后仍有残余，按 GOAL 收口结论登记后继入口。
