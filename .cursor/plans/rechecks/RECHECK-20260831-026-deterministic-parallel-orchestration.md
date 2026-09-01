---
id: RECHECK-20260831-026
plan_id: PLAN-20260831-026
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-08-31
completed_at: 2026-08-31
reviewer: root-agent-independent-pass
baseline_ref: "git HEAD b39603ad（M16 WP3，并行会话）；本任务变更见 git status 白名单"
checked_head: "工作区（未提交；按 Git Hard Boundaries 本任务不创建 commit）"
---

# RECHECK-20260831-026 — 确定性并行 Agent 编排（Cursor SDK 编排器）

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260831-026-deterministic-parallel-orchestration.md`
  （授权来源：用户批准的 Cursor Plan `确定性并行编排_8eeb3644.plan.md`）
- 验收条件：AC-01..AC-09（见下表逐条映射）
- 变更范围（白名单）：
  - 新增：`.cursor/skills/parallel-agent-orchestration/`（SKILL.md + scripts/{types,waves,model-preflight,runner,sdk-adapter,cli,fakes}.ts + 2 个 .test.ts）、`docs/references/upstream/CURSOR_SDK_QUALIFICATION.md`、`tests/tooling/test_validate_bundle_npm.py`
  - 修改：`package.json`、`pnpm-lock.yaml`、`tsconfig.json`、`eslint.config.mjs`、`UPSTREAM_COMPONENTS.yaml`、`docs/INDEX.md`、`docs/references/LICENSE_MATRIX.md`、`.cursor/rules/10-agent-delegation.mdc`、`.cursor/knowledge/{SUBAGENT_DESIGN,KNOWN_CAVEATS,CURSOR_PRIMITIVES,INDEX,SOURCES}`、`.cursor/hooks/session_context.py`、`.cursor/compatibility/CURSOR_COMPATIBILITY.yaml`、`.cursor/skills/system-spec-check/scripts/validate_bundle.py`
  - 删除：`tests/tooling/typescript/parallel-agent-{cli,runner}.test.ts`（移至 Skill scripts/ 下以缩短相对导入路径；该两文件曾被并行 M16 会话的 `ae20e27` commit 裹挟提交，历史保留）
- 基线：本任务开始时工作区已含并行 M16 会话产物（WP0–WP3 提交）；本复检仅对白名单范围负责

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | SDK 类型仅存在于 `scripts/sdk-adapter.ts`（单一 import 点）；编排器不进入 packages/domain、application、services、apps；`docs/INDEX.md` 已登记 qualification | PASS |
| G-02 | 验收条件 | 下表 AC-01..AC-09 逐条 | PASS（AC-07/AC-08 见 F-01/F-02 影响说明） |
| G-03 | lint/typecheck/test | `pnpm run lint` PASS；`pnpm run typecheck` PASS（root strict + web）；`pnpm run format:check` PASS；`agents:parallel:test` 15/15 PASS；`pytest tests/tooling/test_validate_bundle_npm.py` 8/8 PASS；全量 `pytest -q` 2558 passed / 2 failed（失败均非本任务引入，见 F-01/F-02）；`run_all_checks.py --profile typescript` 9/9 PASS | PASS |
| G-04 | 安全与凭据 | `agents:parallel` 仅从 `CURSOR_API_KEY` 环境变量读取（`requireApiKey` 缺失即拒绝）；CLI 不接受命令行 key、不读 `.env`；Agent 以 `tools: [read,grep,glob,ls]` 创建（无 shell/edit/mcp/task，工具面禁嵌套委派）+ `sandboxOptions.enabled: true` + `settingSources: []`；摘要只含 id/模型/状态/耗时/digest，`serializeSummaries` 白名单有测试；`subagent_guard`/`subagent_pretool_guard` 3 路上限与 failClosed 未改动（hook evals PASS） | PASS |
| G-05 | 兼容性与迁移 | `@cursor/sdk@1.0.30` exact pin + tarball sha256 `b26bf8bd…884c1` 登记 `UPSTREAM_COMPONENTS.yaml`（NPM 分支校验）+ `pnpm-lock.yaml`；Node engines `>=22.13` 与仓库 `>=22.18.0 <23` 兼容；上游策略 dependency > adapter（BUILD_TOOLING）；原生 Task 路径与全部 Hook 语义不变 | PASS |
| G-06 | 计划、记忆、供应链 | `validate_cursor_framework.py` PASS（0 warning）；framework/hook/learning evals PASS；learning validator PASS；`governance-check` 与 `validate_bundle` 的全部剩余 finding 均来自并行 M16 会话文件（F-01/F-02），白名单范围 0 finding；`FRAMEWORK_MANIFEST.json`/`RELEASE_EVIDENCE.json` 未触碰（release-assets-immutable PASS）；未写入产品 Memory/数据库/telemetry | PASS |

### 验收条件映射

| AC | 验收条件 | 证据 |
| --- | --- | --- |
| AC-01 | GPT 父 Agent 不再需要单消息批量 Task 调用即可获得并行 Agent 运行 | 编排器由 Node 进程发起多个独立 `Agent.create` 会话；wave 内并发由确定性单测「三个任务在同一波内并发进入（区间重叠）」「第四个任务在下一波启动」证明（fake barrier） |
| AC-02 | 每 wave 最多 3、超 3 顺序分波、无累计上限、无嵌套 | `MAX_PARALLEL_PER_WAVE=3`；`splitWaves` 拒绝 >3（RangeError 测试）；`tools` 无 `task`；多波顺序测试证明无累计配额 |
| AC-03 | 区分启动失败/运行失败/取消；单项失败不污染他项；句柄释放 | 测试「单个任务启动失败不影响其他任务」「运行失败与取消分别保留，且 dispose 全路径执行」 |
| AC-04 | 请求/解析模型、agent/run/request id、重叠区间、digest 可审计；fallback fail closed | 摘要字段测试 + 「解析模型与请求模型不一致时按 model_drift 失败」+ 「模型目录 preflight」三态测试 |
| AC-05 | 默认输出无 prompt/结果正文/key/环境变量/workspace 内容；读任务不修改工作树 | 「serializeSummaries 不包含 prompt、凭据或额外字段」；只读工具集 + sandbox；workspace `statSync` 校验 |
| AC-06 | 无真实 LLM/网络/凭据进入默认 CI；单测可重复证明并发/波次/故障/清理 | `agents:parallel:test` 全部 AgentFactory fake；smoke 明确标记 NOT VERIFIED（qualification 文档） |
| AC-07 | package.json/lockfile/UPSTREAM/许可证/qualification 对 SDK 版本、digest、许可证、门禁一致 | `UPSTREAM_COMPONENTS.yaml` cursor_sdk 条目 + NPM 分支校验通过（`validate_bundle` 无 cursor_sdk finding）；LICENSE_MATRIX 行；qualification 文档 |
| AC-08 | Rule/Knowledge/Hook 说明模型行为是 caveat，无 GPT 特例；3 路上限/no-nesting/fail-closed 不变 | `10-agent-delegation.mdc` 增补保留 validator 必需短语；KNOWN_CAVEATS 模型行为段更新；hook evals PASS；`framework.json` subagent_policy 未改 |
| AC-09 | 治理/Framework/TypeScript/回归校验通过；Manifest 由 release 流程管理 | G-03/G-06 全部命令输出；release assets 未修改（immutable PASS） |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | WARNING（非本任务） | `test_openapi_snapshot_is_current` 失败：`gen_openapi.py` 触发 `sqlite3.OperationalError: no such column: kind`；`git log` 证明 `adapters/sqlite/db.py` 最后改动为并行 M16 会话 commit `ae20e27 feat(m16): WP1 worker gateway + authentication`（同日连续 WP0–WP3 提交）。与本任务白名单文件零交集 | 不修复：属活跃 M16 会话领域；移交该会话按其 WP0 计划收口。本任务不创建 commit，不会冻结该状态 |
| F-02 | WARNING（非本任务） | `governance-check`/`validate_bundle`/`docs_consistency` 报 `.cursor/plans/m16_分布式执行_1657b1d6.plan.md` 13 条失效链接与 `ADR-0027` 引用缺失文档：全部指向尚未实现的 M16 路径（部分为仓库根相对路径写法）；`ADR-0027` 为 M16 会话产物 | 不修复：避免与并行会话写冲突；M16 WP0 本身计划把计划固化到 `tasks/` 并建索引，届时收口 |
| F-03 | INFO | 并行 M16 会话的 commit `ae20e27` 裹挟提交了本任务当时未跟踪的 `tests/tooling/typescript/parallel-agent-*.test.ts`；本任务将其移至 Skill scripts/ 后 git 显示 D。历史保留不回退 | 保留移动后的位置（所有权更清晰）；在完成报告向用户说明 |
| F-04 | INFO | 手工 smoke（真实 `CURSOR_API_KEY` 的并发重叠/模型目录/sandbox 负测）未执行：用户未提供临时 key | qualification 文档如实标记 NOT VERIFIED；fail-closed 语义保证未验证能力不会假 PASS；后续凭用户 key 单独执行 |

## 结论

- 结果：`PASS_WITH_WARNINGS`
- 理由：白名单范围内的全部验收条件均有确定性证据（单测/validator/evals 全绿）；两处 WARNING 均为并行 M16 会话在共享工作区引入的状态，与本任务变更文件零交集，且不阻塞本任务交付物；SDK 实际并发/沙盒行为按计划标记 NOT VERIFIED，不伪造 PASS。
- 后续动作：
  1. 用户提供临时 `CURSOR_API_KEY` 后执行 qualification 文档列出的手工 smoke（模型目录确认 → 2–3 个只读任务重叠验证 → sandbox 负测），补记本 recheck 附录；
  2. M16 会话收口其计划文件链接与 sqlite schema 回归（F-01/F-02）；
  3. 如需把本任务纳入 Framework Release，走显式 `framework-release` 流程重建 Manifest。
