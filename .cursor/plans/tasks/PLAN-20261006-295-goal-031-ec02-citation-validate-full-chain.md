---
id: PLAN-20261006-295
slug: goal-031-ec02-citation-validate-full-chain
title: GOAL-031 cycle 2（EC-02）：`citation.validate` 全链 —— 三态判定 + 复用 `_elink` 取数 + 新 provider `ncbi_citation` + pin 最小追加 + 两向反证
status: DONE
created_at: 2026-10-06
updated_at: 2026-10-06
latest_recheck: .cursor/plans/rechecks/RECHECK-20261006-295-goal-031-ec02-citation-validate-full-chain.md
memory_entries: []
parent_goal: GOAL-20261006-031
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 **EC-02**（授权 2：`citation.validate` 全链）。路线已由建档实测
    标定为**路线 F = 新增 provider `ncbi_citation`**（只声明 `citation.validate`；既有
    `ncbi_eutils` 工具面逐字不变 ⇒ 只打红 1 条 set 字面量 + 2 条夹具 pin 下界断言）。
    **本 PLAN 专属边界**：取数**复用** `NcbiEutilsProvider._elink`（不新造第二套取数）；
    判定规则**显式三态**（成立 / 不成立 / 无法判定）；pin 夹具**仅追加**（断言一字不改、
    `git diff --numstat` 删除行 0）；判据/门禁/阈值/断言强度一律不动（新增判据不受限）。
    零真实凭据进树；默认门离线；不得宣称项目安全（`R-M1`）；不得宣称投递语义为
    「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    `citation.validate`（`citation.inspect` 的**判定层**）承接面从零到全链：① 三态判定
    规则写成**常量 + 语义文档 + 判据**（不得二值化含糊）；② 取数走既有 `_elink` →
    `normalize_elink`；③ 实现（真工具）+ 出厂绑定 + 目录声明 + `policy.yaml` 放行
    + `POLICY_SURFACE_AUDIT.md` 登记面同轮同步；④ pin 夹具最小追加（删除行 0 自证）；
    ⑤ 两向反证：不被支持 ⇒ **不成立**并点名；来源缺失 ⇒ **无法判定**（不得当成立）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **三态规则显式**：`citation.validate` 的判定规则写成**模块级常量**（三态枚举或等价
      结构化字段）+ docstring 语义 + 判据；三态的判据逐条：**成立**（linkset 在场且 ≥1 条
      PMC 链接）/ **不成立**（linkset 在场但零链接）/ **无法判定**（无 linkset / 来源缺失）。
      「无法判定」**不得**被算成「成立」（判据显式断言二者不同）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_citation_validate_three_state.py -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **取数复用既有 `_elink`**：新 provider 复用同一取数路径（同一 `_elink` → 同一
      `normalize_elink`），**不新造第二套取数**；判据以**行为**取证（同一个 elink 响应
      经两条路径得到同一 linkset 归一化结果），并有反证（把新 provider 的取数换成
      另一套 ⇒ 判据判红 / 或以「唯一取数实现点」的结构断言钉住）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_citation_validate_three_state.py -q`
      ⇒ 全绿（含取数同源臂）。
    status: PASS
  - id: AC-3
    criterion: >-
      **承接面登记 + 放行**：`tool_providers.yaml` 新增 `ncbi_citation`（capabilities =
      `[citation.validate]`，READ_ONLY，network_domains 与 ncbi 同源）；出厂绑定表
      （`DEFAULT_SESSION_TOOL_BINDINGS`）登记该工具名；`policy.yaml` 放行（scope 对齐
      `citation.inspect` 所在形态 = `approved_tool_providers`，与既有取数 provider 一致）；
      `POLICY_SURFACE_AUDIT.md` 登记面同轮同步；`capability_coverage` 分类表同步。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts
      tests/application/preflight tests/architecture/python/test_capability_coverage_is_implemented.py
      -q` ⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **pin 夹具最小追加**：受影响的 pin **只追加条目**，断言一字不改；
      `git diff --numstat` 对受影响 pin 文件**删除行为 0**（若某文件形态上必须产生 1 行
      替换，则按 `W31-3` **如实出示**该读数并说明，不得伪称 0）。
    verify: >-
      `git diff --numstat -- tests/api/run_fixtures.py tests/contracts/*.py` 读数留档；
      断言逐字节对照（只有列表变长）。
    status: PASS
  - id: AC-5
    criterion: >-
      **反证两向**：① 不被来源支持的引用（linkset 在场、零 PMC 链接）⇒ 判**不成立**且
      **点名缺口**；② 来源缺失（无 linkset / elink 返回空结构）⇒ 判**无法判定**，
      **不得**当成「成立」。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_citation_validate_three_state.py -q`
      ⇒ 两向反证用例全绿；判词原文留档。
    status: PASS
---

# PLAN-20261006-295 — GOAL-031 cycle 2（EC-02）：`citation.validate` 全链

## 目标与范围（一句话）

把 `citation.validate`（B 组最后一条可承接的读能力）从「无实现」推进到**全链**：
三态判定 + 复用既有取数 + 登记/放行 + pin 最小追加 + 两向反证。

## 为什么另立 provider（路线 F，建档实测的决策）

建档实测两条路线的判红面（逐条点名）：

| 判据 | 钉的是什么 | 路线 A（扩 ncbi_eutils） | 路线 F（新增 ncbi_citation） |
| --- | --- | --- | --- |
| `test_ncbi_provider_contract` 工具名集合 | 恰为三条 | **红** | 绿（既有工具面不变） |
| `test_existing_providers_are_untouched` | 目录 provider 集合恰为 4 | 红 | 红（**多行 set 字面量 ⇒ 纯追加一行**） |
| 夹具 pin 下界（两条断言） | 目录非 NATIVE ⊆ 夹具 pin 源 | 绿 | 红（`_PROVIDERS` 单行 tuple） |
| `test_contract_loaders` ncbi 能力逐字 | 三条不变 | **红** | 绿 |
| `capability_coverage` 分类表 | 声明 ⇒ 实现 | 红 | 红（登记表同步，属点名例外⑤） |

⇒ 路线 F 让「既有 ncbi 工具面」**逐字保持**，受影响面最小。

## 三态判定规则（本 PLAN 的核心语义）

```text
成立   (SUPPORTED)     ：来源解析出 linkset 且 ≥1 条 PMC 链接
不成立 (UNSUPPORTED)   ：来源解析出 linkset 但零链接 ⇒ 引用不被来源支持
无法判定 (UNDETERMINED)：无 linkset / 来源缺失 ⇒ **不得**当成「成立」
```

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-5，收口时全部 `PASS`）。三条机械判据：
三态两两不等 + 判词点名（12 条判据）／取数点唯一 = 1（结构与行为两臂）／pin 判据文件删除行 0。

## 实施清单

- [x] **WP-A（实现）**：`adapters/research_tools/ncbi_citation.py`（复用 `_elink` 取数）+ 三态常量。
- [x] **WP-B（登记）**：`tool_providers.yaml` + 出厂绑定表 + `policy.yaml` 放行 + AUDIT 登记面。
- [x] **WP-C（pin 最小追加）**：夹具 pin 源 + set 字面量（删除行 0 或如实出示）。
- [x] **WP-D（判据）**：三态 + 取数同源 + 两向反证。
- [x] **WP-E（记录）**：RECHECK + GOAL 回写 + 迭代日志。
- [x] **WP-F（门）**：记录面 → 全量定向 → m0（独占、记录后）→ 治理 → commit → push → CI。

## 证据

**判词归档（进树）**：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec02-release-and-pin-ledger.txt`
（放行求值 / 取数点唯一 / numstat 逐文件 / pin 判据删除行 0 逐字节）。

**实测读数**：
- 三态判据 `test_citation_validate_three_state.py` ⇒ **12 passed**（含两向反证 + 自检）；
- 受判面合跑（contracts + preflight + m2_audit + coverage）⇒ **586 passed / 69 skipped**；
- 扩展合跑（+ adapters + loaders）⇒ **1157 passed / 72 skipped**；
- 会话注册面 + 目录合并 ⇒ **18 passed**；
- 放行求值：`ALLOW` / `matched allow rule`；scope = `approved_tool_providers`；
- 取数点唯一：`'elink.fcgi'` 在 `adapters/research_tools/ncbi.py` 出现 **1** 次；
- pin 判据删除行：`test_europe_pmc_pin_and_registration.py` **0**；
  `test_mcp_registration_and_refutations.py` **0**；`run_fixtures.py` **-1**（见 W-EC02-1）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | IN_PROGRESS | 建档（cycle 2 derive）；路线 F 与三态规则由 cycle 0/1 的实测标定。 |
| 2026-10-06 | DONE | WP-A…WP-D 实测落地；三态判据 12 passed；合跑 586 / 1157 / 18；复检 `RECHECK-20261006-295` = `PASS_WITH_WARNINGS`（W-EC02-1 夹具 1 行重写 / W-EC02-2 两层新增 / W-EC02-3 离线射程）。 |

## 影响报告

**Domain / API / schema 变化**：无。（新增 provider 是**目录/配置面**；适配器是新增实现；
`normalize_elink` 的返回形状**未改** —— 三态是**新增函数** `validate_citation_support`。）

**安全 / 凭据面变化**：新增 1 条**只读**能力放行（`citation.validate`，scope
`approved_tool_providers`），`deny` / `require_approval` / `allow_with_constraints` /
`default_effect` **零改动**。**不**新增凭据、**不**新增出网域（复用 `eutils.ncbi.nlm.nih.gov`）。

**兼容性 / 迁移风险**：低。`citation.inspect` 的返回值逐字未变（原函数未改语义）；
新增 provider 只影响「谁承接 `citation.validate`」这一件事。

**上游版本影响**：无新依赖、无版本变化。

## 无可复用事实

**无**（产出全部可复用：三态常量 + 单取数点结构 + 判据 + 证据归档都在树内）。
`memory_entries` 在 GOAL 层回填。


