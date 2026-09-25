---
id: MEM-20260925-134
title: "「点名契约」类判据要三件套：行为成对 + 单一来源 + 按压；且配对粒度必须与契约粒度一致"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-168-missing-executor-must-be-named.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-169-missing-executor-must-be-named.md
supersedes: []
tags: [judges, preflight, tool-availability, reverse-search, pairing, goal-016]
---

## 做了什么

GOAL-016 的 **EC-01（D-01(b)）**把「出厂组合根缝为空 ⇒ preflight 必须**逐字点名**哪个能力
没人执行」钉成机械判据（`tests/application/preflight/test_missing_executor_is_named.py`）。
落地过程中确认了三件可复用的事：

1. **「它已经在树」≠「它稳定」**：点名逻辑本来就在 `check_tools` 里，但**没有任何判据**覆盖它
   （全仓搜 `no provider is available` 只命中实现自己）。所以「已完成」必须落成**判据**才算事实。
2. **成对反证是这类契约的最小充分证据**：只断言「缺执行体 ⇒ 点名」会被一个**恒点名**的实现
   骗过。补齐「恢复 provider ⇒ 该点名**消失**且该码计数归零」这一半，才排除了恒真。
3. **单一来源搜索把「碰巧在场」排除掉**：模板 `no provider is available for capability`
   在**生产源**（`packages/` / `services/` / `adapters/`）里只命中
   `packages/application/preflight/checks.py` 一处 ⇒ 命名来自**单一实现点**。
   搜索**必须排除测试 / 夹具目录**——判据文件自身就要写出这个模板，把测试算进去会让
   「唯一来源」变成恒假。

另外一个**判据自身的缺陷**（不是产品缺陷）：首版按**能力名**配对，被 `workspace.read`
判红——它在 `execution` 与 `review` **两个 phase** 上都被需要 ⇒ 一条点名会被误读成覆盖两处需求。
改成按 `(phase_id, capability)` 配对后才正确。

## 为什么这样做

- **契约的粒度决定判据的粒度**：`ToolRequirement` 的身份是 `(phase_id, capability)`，
  所以「点名是否覆盖了每条需求」必须按同一粒度判定；按能力名去重会**漏掉**同一能力在第二个
  phase 上的缺供给。这条通用：判据的配对键要与被判定对象的**身份键**一致。
- **反向搜索的排除面要写清**：`PRODUCTION_ROOTS = ("packages", "services", "adapters")`
  是有意为之（测试目录必然包含被断言的模板）。不写清排除面，后来的人会以为这是遗漏。
- **配对反证要「只改一个变量」**：两臂用**同一协议、同一判据、同一出厂目录**，只把
  `tool_providers` 置空 / 恢复 ⇒ 结论差异只能归因于供给面。

## 怎么做与复现

- 正向 + 反证 + 单一来源 + 按压：`uv run --frozen --no-sync python -B -m pytest
  tests/application/preflight/test_missing_executor_is_named.py -q` ⇒ `4 passed`。
- **同码不同链的坑（实测）**：缝为空时报告里**同时**有两条链的同名码——
  编译面 `no tool provider exposes capability {…}`（`CompileFindingCode`，来自
  `packages/application/protocol_compile/requirements.py`）与预检面
  `no provider is available for capability {…}`（`PreflightFindingCode`，来自
  `packages/application/preflight/checks.py`）。**断言面必须写清是后者**，否则判据会被
  前者的存在误导成"已经覆盖"。
- 第三种形态（**不**在本判据面内）：provider 已声明但全部不可用 ⇒
  `no healthy provider is available for capability {…}`（健康 / 信任面）。
- 只读探针（只有观测、不是判据）：`scratch/goal016_c1_probe.py`。

## 适用边界

- 判据遍历**协议声明的**工具需求；协议若新增能力，判据自动跟着覆盖（不写死能力名单）。
- 单一来源搜索只扫 `packages/` / `services/` / `adapters/` 的 `.py`；用
  `os.walk(followlinks=False)`（仓库里的悬空 pnpm 链接会让 `pathlib.rglob` 直接抛错）。
- 本条目**不**改变「出厂组合根不接执行体缝」这一事实（`D-01` 的 `M-1` 仍由装配方补执行体）；
  它只保证那条缝的**契约可判**。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-168-missing-executor-must-be-named.md`（WP1–WP4）
- `.cursor/plans/rechecks/RECHECK-20260925-169-missing-executor-must-be-named.md`
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-01）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-01（判词的证据出处同源）
