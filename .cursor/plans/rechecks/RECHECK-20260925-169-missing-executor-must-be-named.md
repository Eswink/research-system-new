---
id: RECHECK-20260925-169
plan_id: PLAN-20260925-168
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-016-cycle1 + 只读探针（scratch/goal016_c1_probe.py，零出网）
baseline_ref: 建档提交 `4afb314`（GOAL-016 建档，零代码改动）
checked_head: 当前树（判据 + 记录；**产品代码零改动**）
---

# RECHECK-20260925-169 — D-01(b) 判据化（GOAL-016 cycle 1）

## 检查范围

① 判据是否真的走**产品入口 + 出厂目录**（而不是判据自己拼的上下文）；② 「缺执行体 ⇒ 逐字点名
能力」是否**逐条**成立（AC-1）；③ **反证成对**是否成立——只改供给面就让该点名消失且计数归零
（AC-2）；④ 点名模板是否**单一生产来源**（AC-3）；⑤ 判据是否**可被按压**（AC-4）；
⑥ **产品代码是否零改动**（AC-5）。

## 检查结果

### 一、AC-1｜行为证据（正向）——缝为空 ⇒ 逐字点名

- **载体是产品路径**：判据用 `services.api.catalog`（出厂目录加载器）+
  `services.api.catalog.load_protocol_definition`（出厂协议加载器）+
  `packages.application.preflight.preflight.compile_and_preflight`（产品入口）。
  **不是**判据手工拼的 `CompiledRunPlan`。
- **缝为空 = D-01(b) 的生产形态**：`dataclasses.replace(catalog, tool_providers={})`
  （对应 `ApiDeps.tool_providers` 生产为空）。
- **实测**（`scratch/goal016_c1_probe.py`，只读、零出网）：
  `sort_analysis_v1.yaml` 的工具需求 = `execution` 上 `artifact.write` / `code.execute` /
  `workspace.read` / `workspace.write.code`，`review` 上 `evidence.read` / `workspace.read`
  ⇒ **6 条 `ToolRequirement`，`provider_ids` 全为 `()`**。
- **判据断言**：每一条都得到
  `TOOL_UNAVAILABLE` + `no provider is available for capability {能力名}` +
  归属 `phase:{phase_id}`；且 `report.status is FAIL`（ERROR 级，不得降级）。
- **判据运行**：`uv run --frozen --no-sync python -B -m pytest
  tests/application/preflight/test_missing_executor_is_named.py -q` ⇒ **`4 passed`**。

### 二、AC-2｜行为证据（反证成对）——恢复 provider ⇒ 点名消失

- 同一协议、同一判据、同一出厂目录，**只**把 `tool_providers` 换回出厂集合 ⇒
  **6 条点名全部消失**，且 `TOOL_UNAVAILABLE` 在报告中**计数归零**（探针实测 `0`，
  判据 `test_restoring_executors_removes_the_named_findings` 逐条断言）。
- ⇒ 点名归因于**供给面的缺失**，不是协议里的固定文本、也不是恒点名实现。

### 三、AC-3｜反向搜索——单一生产来源

- 模板 `no provider is available for capability` 在 `packages/` / `services/` /
  `adapters/` 的 `.py` 里**只命中一处**：
  `packages/application/preflight/checks.py`（判据断言该列表**逐字等于**这一个路径）。
- **排除面写清**：测试 / 夹具目录**不参与**搜索——判据文件自身必须写出该模板，
  把它算进去会让「唯一来源」变成恒假。
- 全仓搜同码的邻居实现（避免把别的链误当成本判据的覆盖）：
  - `adapters/**` 的 `FailureCategory.TOOL_UNAVAILABLE` 是**运行时失败分类**，不是 preflight 点名；
  - `packages/application/protocol_compile/requirements.py` 是**编译面**
    （`no tool provider exposes capability {…}`），同码不同链；
  - `packages/application/preflight/checks.py` 的**健康 / 信任面**分支是第三种形态
    （`no healthy provider is available for capability {…}`）。
  ⇒ 三者**互不顶替**，本判据只覆盖**预检面的缺供给分支**，并在判据 docstring 里披露。

### 四、AC-4｜按压自身

- 把报告里的模板**在内存内**改坏（`dataclasses.replace`，**不改仓库文件**）⇒
  匹配器判空（`_named(broken, capability) == []`）⇒ 判据真的在读那条消息，不是恒真。
- 同时保留了「现状下该能力必须被点名」的前置断言 ⇒ 按压本身也不空转。

### 五、AC-5｜产品代码零改动

- 本 cycle 的改动集只含：判据文件（新增）、本 PLAN / 本 RECHECK / MEM-134、
  `ALL_PLAN.md`、GOAL-016。
- `packages/application/preflight/`、`packages/application/ports/`、
  `examples/config/policy.yaml`、`tests/egress_guard.py`、
  `.cursor/skills/governance-check/scripts/validate.py`：**均未改动**。

### 六、质量门禁（本地）

- `ruff check` = `All checks passed!`；`ruff format --check` = `1 file already formatted`。
- 规模 / 命名门禁：`tests/tooling/test_python_source_limits.py` +
  `tests/architecture/test_module_file_naming.py` ⇒ **`1054 passed`**；
  新文件 **213 行**（软阈值 300 行以内，硬阈值 450 行）。
- `egress guard` 判词 = `judged 0 connection attempt(s); blocked 0`（判据零出网）。
- m0 终态行：见本 RECHECK 的「附：m0 终态行」与 GOAL-016 的 CI 台账
  （**记录只写实跑结果；本机无法验证的项不记 PASS**）。

## 附：m0 终态行

- **代管后的树**（`R-3` 的文件临时移出）：`PASS: profile=m0; 23 deterministic checks`
  （退出码 0）。代管脚本逐字节复核 **一致**：`size=69944` /
  `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`（三者全等）。
  日志：`scratch/goal016-c1-m0-quarantined.log`；轮次输出：
  `scratch/goal016-c1-m0-quarantine-run.txt`。
- **as-is 的树**：**22/23**——唯一红项 = `framework/validate_bundle`，且**单条 check 直跑**复现
  的判词**只有一条**：`Markdown 本地链接不存在:
  scratch\self-governance-bootstrap-prompt.md -> [A-Za-z]:\\|/(home|mnt|data|Users`
  ⇒ 归因 = **`R-3`**（仓库外 / 仓库内 gitignored 的并发写者文件被纯文本链接扫描读成本地链接），
  与本 cycle 的改动**无关**（该文件由**别人**写、本 GOAL **不碰**）。
- **口径**：本终态行取自**代管后的树**——**不得**读成「as-is 本机全绿」。
  `R-3` 的处置属 **D-10**（**需另行授权**），本 GOAL 只引用、不改。
- **记录时序声明**：本轮 m0 在**冻结树**上跑（记录写完后无并发写入）；本节与 GOAL-016
  台账行的补写发生在 m0 **之后**，属**只写记录**（不改判据 / 产品代码 / 门禁）。

## 结论

- **AC-1…AC-5 全部成立** ⇒ **GOAL-016 EC-01 = PASS**。
- **PASS_WITH_WARNINGS 的两条警告**：
  - **W-1｜本判据不覆盖另外两条同名码链**（编译面的 `no tool provider exposes capability …`
    与健康 / 信任面的 `no healthy provider is available …`）。这是**设计边界**（已在判据
    docstring 披露），但读者若只看到「TOOL_UNAVAILABLE 已被判据覆盖」会高估覆盖度。
  - **W-2｜`R-3` 仍在**：本机 as-is m0 的唯一预置红仍来自**仓库外** gitignored 文件
    （`framework/validate_bundle`），与 cycle 1 的改动**无关**；本 RECHECK **不**宣称本地全绿。
    `R-3` 的处置属 **D-10**（**需另行授权**），本 GOAL 只引用不改。
- **未改动**：产品代码、策略面、门禁、阈值、依赖 pin、运行时默认值（逐项对照见第五节）。
