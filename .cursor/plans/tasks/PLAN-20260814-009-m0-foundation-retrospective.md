---
id: PLAN-20260814-009
slug: m0-foundation-retrospective
title: M0 Repository Foundation Quality Gate — Retrospective Reconstruction
status: DONE
created_at: 2026-08-14
updated_at: 2026-08-14
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "M0-M7 Documentation Reconciliation & Completion Prompt：为缺失 Plan 的阶段创建 retrospective stage record"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md
memory_entries:
  - MEM-20260814-009
---

# PLAN-20260814-009 — M0 Retrospective Reconstruction

> RETROSPECTIVE_RECONSTRUCTION: true
>
> 本记录由 2026-08-14 文档对账任务依据 git history、当前代码/测试与
> 可执行 validator 事后重建。M0 开发窗口（2026-08-10 ~ 2026-08-11）当时
> 未创建独立任务计划、复检与工程记忆文件；本记录不声称这些文件在开发时
> 已存在，也不虚构当时的讨论、评审或测试结果。

## 目标（原 M0 定义）

按 `CODEX_BOOTSTRAP.md` 与 `docs/roadmap/MILESTONES.md` 的 M0 定义：
Repository Foundation Quality Gate —— 可复现 Python/TypeScript 工具链、
`domain / application / adapter / entry` 依赖边界、architecture/contract
test 入口、Windows/Linux CI 确定性门禁，以及 system-spec / Cursor
governance validators 接入 CI。

## 验收条件（retrospective 重建记录自身的验收）

- [x] AC-01：本记录全部陈述可由 git history、当前代码/测试或可执行
      validator 直接支持；无虚构的讨论、评审或测试结果。
- [x] AC-02：M0 的 DoD（CODEX_BOOTSTRAP M0 完成条件）逐项有当前证据。
- [x] AC-03：重建记录通过 governance validator（章节/ID/状态机）与
      bundle validator（链接/版本引用）。
- [x] AC-04：retrospective 性质在文件头显式标注
      `RETROSPECTIVE_RECONSTRUCTION: true`。

## 实际实现范围

- Python 3.12 + uv exact lockfile（`pyproject.toml`、`uv.lock`、
  `.python-version`）：ruff（line-length 100 / mccabe max-complexity 10 /
  max-args 5 / max-nested-blocks 4）、mypy strict、pytest、import-linter。
- TypeScript 22.18.0 + pnpm lockfile（`tsconfig.base.json`、
  `pnpm-lock.yaml`、`.node-version`）：ESLint（含自定义架构规则
  `tools/eslint-rules/architecture.mjs`）、dependency-cruiser。
- 依赖边界正反向夹具：`tests/architecture/python/`（valid/invalid
  fixtures + `.importlinter`、`.importlinter.application`、
  `.importlinter.domain`、`.importlinter.fakes`、`.importlinter.relay`
  契约）与 `tests/architecture/typescript/`（dependency-cruiser 规则 +
  双语言夹具）。
- 离线质量入口：`.cursor/skills/cursor-framework-check/scripts/`
  （run_all_checks.py 等 5 个脚本，`--profile m0|framework|python|typescript`）。
- CI 门禁定义：`.github/workflows/m0-quality.yml`。
- 契约资产基线：`schemas/`（25 个 JSON Schema）、`examples/`（config /
  contracts / protocols 共 29 个 YAML）、`VERSION=0.4.0`、
  `UPSTREAM_COMPONENTS.yaml`、`.cursor/skills/system-spec-check/scripts/validate_bundle.py`、
  `.cursor/skills/governance-check/scripts/validate.py`。
- M0 依据其定义未创建空生产包，也未实现产品业务能力。

## 非目标

- 不创建只有占位文件的生产目录（`packages/`、`adapters/`、`services/`、
  `apps/web` 在 M1 起随真实模块进入）。
- 不引入真实 LLM、OpenHands、数据库或 UI 业务行为。
- 不实现 Domain / Protocol Compiler / Model Relay / Role / Task 等业务逻辑。

## Dependencies

- 无上游依赖（起始阶段）；此前置工作为 2026-08-10 治理初始化
  （PLAN-20260810-001 cursor-governance-bootstrap、-002 git 策略、
  -003 治理规则审计）与 bootstrap 配置（commit `5045c59`，
  Research OS Bootstrap 早期配置/schema/validation 脚本，M0 前身）。

## Architecture boundaries

- 编译期依赖：`apps / services / adapters → packages/application →
  packages/domain`，由 import-linter 与 dependency-cruiser 双语言强制。
- 运行时控制流：`entry adapter → application use case → domain`；
  出站副作用经 `application → inward-owned Port → adapter`。
- M0 以正反向夹具证明门禁可放行正确图、拒绝错误图；不承载业务语义。

## 主要 implementation artifacts

| 类型 | 位置 |
| --- | --- |
| Python 工程配置 | `pyproject.toml`、`uv.lock`、`.python-version`、`.importlinter*` |
| TS 工程配置 | `pnpm-lock.yaml`、`.node-version`、`tsconfig.base.json`、`tsconfig.json`、`.prettierrc.json` |
| 边界测试 | `tests/architecture/python/`（20 个测试文件 + fixtures）、`tests/architecture/typescript/` |
| 工具链测试 | `tests/tooling/`（eslint-rule、python 源码阈值、release 文件选择） |
| CI | `.github/workflows/m0-quality.yml` |
| 质量聚合入口 | `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py` |

## Git commits

- `5045c59`（2026-08-10）Add configuration files, schemas, and validation
  script for Research OS Bootstrap（M0 前身，bootstrap 配置与校验）。
- `3cc6130`（2026-08-11）chore(release): establish v0.4.0 M0 engineering
  baseline（M0 正式基线）。

## Tests / validation

- `tests/architecture/python`：domain 禁止 vendor SDK、application 依赖方向、
  fakes 边界、relay 边界（含 invalid fixtures 负测）。
- `tests/architecture/typescript`：dependency-cruiser 正反向夹具。
- `tests/tooling`：ESLint 自定义规则（exhaustive-switch 等）、Python 源码
  规模阈值、release 文件选择。
- 门禁聚合：`run_all_checks.py --profile m0`（README 定义的 18 项
  确定性门禁，后续 M1-M7 每阶段复用并扩展）。
- 本重建记录的有效性验证由 RECHECK-20260814-009 于 2026-08-14 重跑
  m0 profile / validators 后判定。

## DoD

按 CODEX_BOOTSTRAP M0 完成条件核对：

- [x] Windows/Linux 可从 lockfile 确定性安装（uv + pnpm exact lockfile）。
- [x] lint、strict typecheck、dependency boundary、unit/contract test 均有
      命令入口（run_all_checks.py profiles）。
- [x] CI 执行门禁及 system-spec / Cursor governance validators
      （`.github/workflows/m0-quality.yml`）。
- [x] composition root 是具体 adapter 的唯一装配位置（架构文档约束，
      后续阶段经 import-linter 与代码审查落实）。
- [x] 不引入真实 LLM、OpenHands、数据库或 UI 业务行为。

## 发现过的重要问题

- 无 M0 开发窗口的独立计划/复检/记忆记录（本次重建的动因）；M0 此前仅以
  BACKLOG 勾选与 README「当前阶段」描述存在，README 描述在 M1-M7 落地后
  已过时（由本对账任务 STEP-04 修正）。
- 2026-08-10 治理初始化阶段（archive）的 4 个 recheck 为
  PASS_WITH_WARNINGS 群，与 M1-M7 的 PASS 不同；属治理基线早期收敛过程，
  不影响 M0 门禁有效性。

## 最终状态

- 状态：DONE（以 git `3cc6130` 与 m0 profile 可执行门禁为证）。
- M0 交付的工程基线在 M1-M7 全程复用：每阶段 m0 profile 回归均为绿色。

## 对下一阶段提供的 Contract

- 依赖边界门禁可执行、可扩展：新增生产目录或新契约时必须同步更新
  `.importlinter.*` / dependency-cruiser / `tests/architecture/` 正反向
  夹具与 `validate_bundle.py` 交叉引用。
- `packages/`、`adapters/` 只在首个真实职责模块及其测试同时进入时创建
  （M1 起按此执行）。
- 质量门禁以 `run_all_checks.py --profile m0` 为统一入口，后续阶段在此
  基础上增加专项测试。

## 已知非阻断技术债

- 无产品级技术债（M0 不包含业务代码）；工程债为缺失的阶段性文档记录，
  由本次 reconstruction 补足。
- CI 定义（m0-quality.yml）的 Windows 执行验证依赖 runner 可用性，
  本地以 PowerShell 等价命令覆盖。

## 实施清单（重建动作）

- [x] STEP-01：从 git log / 目录结构 / validator 提取 M0 实现证据。
- [x] STEP-02：核对 CODEX_BOOTSTRAP M0 完成条件并逐项落证据。
- [x] STEP-03：创建本 retrospective 计划并登记 ALL_PLAN。
- [x] STEP-04：执行 retrospective recheck（RECHECK-20260814-009，
      2026-08-14 实际重跑 validators/门禁）。
- [x] STEP-05：创建工程记忆 MEM-20260814-009 并登记 INDEX。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 实现范围 | git | `3cc6130`（M0 baseline）；`5045c59`（前身） | 存在 |
| EV-02 | 工具链 | file | `pyproject.toml` / `uv.lock` / `pnpm-lock.yaml` / `.python-version` / `.node-version` | 存在 |
| EV-03 | 边界门禁 | test | `tests/architecture/python`（20 文件）与 `tests/architecture/typescript` 正反向夹具 | 存在 |
| EV-04 | 质量聚合 | file | `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py` | 存在 |
| EV-05 | DoD 核对 | check | 2026-08-14 重跑 m0 profile + validate_bundle + governance | 见 RECHECK-20260814-009 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-14 | — | IN_PROGRESS | 文档对账任务创建 retrospective 重建记录 | 本计划创建 |
| 2026-08-14 | IN_PROGRESS | DONE | RECHECK-20260814-009 PASS（2026-08-14 实际重跑） | RECHECK 文件 |

## 影响报告

- Domain/API/schema：无。
- 安全/凭据：无。
- 兼容性/迁移：无。
- 上游版本：无（M0 无上游运行组件；UPSTREAM_COMPONENTS 为契约基线）。
- 下一项任务：M1 Domain Kernel（PLAN-20260811-001）在 M0 门禁之上落地。