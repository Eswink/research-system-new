---
id: PLAN-20261001-265
slug: mimosa-deep-scan-disposition
title: Mimosa 深扫（2026-10-01）处置 — 36 条 findings 逐类核实 + 依赖 advisory 复核刷新 + 记录面落档与门禁复跑
status: DONE
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: .cursor/plans/rechecks/RECHECK-20261001-266-mimosa-deep-scan-disposition.md
memory_entries:
  - .cursor/memory/entries/MEM-20261001-179-raw-advisory-dumps-belong-outside-the-tree.md
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-01 用户会话指令：「对我们的项目使用 mimosa（mimosa-security-scan 技能）扫描，然后进行修复」。
    **本 PLAN 专属边界**：处置记录 + 守卫为主；**不改**任何依赖 pin（已知面承 D-03 维持现状；
    上轮之后**新出现**的 pyjwt / urllib3 / brace-expansion 面只登记、不处置，升级需**单独授权**）；
    **不动**任何门禁 / 阈值 / 放行面；**不安装** hook 检测层、**不初始化**
    `.mimosa/security-policy.json`（D-04「本项不做」）；**不删不改** `scratch/` 既有取证资产；
    **不得**宣称项目安全（`R-M1` 未收口）；扫描为 static-only / coverage partial，
    结论射程只到「已覆盖范围内未发现产品代码缺陷」。
exit_criteria:
  - id: AC-1
    criterion: >-
      **密封回执**：deep 扫描完成并落 scanId + seal + 产物目录 + coverage 摘录到
      `docs/audits/MIMOSA_DEEP_SCAN_20261001.md`（§1/§2）。
    status: PASS
  - id: AC-2
    criterion: >-
      **36 条 findings 逐类核实**：HIGH ×1 + MEDIUM ×28 + LOW ×7 全部复核当前字节，
      给出误报/范围外判定与依据（含 HIGH 的反回归判据实跑、AST 结构反证）；
      四个点名文件零命中且 git-status「M」被证实为 CRLF 差异（§3）。
    status: PASS
  - id: AC-3
    criterion: >-
      **依赖 advisory 复核刷新**：413 个锁定包 OSV 离线构建 + 单次 curl 查询，
      证据落 `docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20261001.json`；
      新出现的 pyjwt / urllib3 / brace-expansion 面**登记为残余**并标注需单独授权（§4/§6）。
    status: PASS
  - id: AC-4
    criterion: >-
      **记录面与门禁**：PLAN / RECHECK / MEM 与 `ALL_PLAN.md` / memory INDEX / `docs/INDEX.md`
      交叉引用一致；记录面判据与全量 m0 在**记录写入之后**运行，m0 终态行
      `PASS: profile=m0; 23 deterministic checks`（§证据）。
    status: PASS
  - id: AC-5
    criterion: >-
      **残余与未覆盖逐条**：undici（D-03 维持）、hook 检测层（D-04 维持）、`R-M1` 原样、
      三个新出现依赖面、static-only / threatModel partial 未覆盖范围逐条在位（§残余）。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | 密封回执落档（scanId/seal/coverage） | `docs/audits/MIMOSA_DEEP_SCAN_20261001.md` §1/§2 | **PASS** |
| AC-2 | 36 条逐类核实 + 四文件点名校验 | 同文档 §3；判据复跑见 RECHECK-266 | **PASS** |
| AC-3 | 依赖复核刷新 + 新面登记 | `MIMOSA_DEPENDENCY_ADVISORIES_20261001.json` | **PASS** |
| AC-4 | 记录面 + m0（记录写入后） | `scratch/mimosa-20261001/m0b.log` 终态行 | **PASS** |
| AC-5 | 残余与未覆盖逐条 | 本文「影响报告」；RECHECK-266 §结论 | **PASS** |

## 目标

用户要求：对本仓跑 Mimosa 安全扫描并「进行修复」。处置结论：本次 deep 扫描
（`scan-2026-10-01T07-47-51.288Z-3fce4de3077a`）的 36 条 findings 经逐类核实
**全部为误报或范围外，未发现产品代码缺陷** ⇒ 无产品代码「修复」可做；
本轮的「修复」动作落在三处：①把与既有台账一致的新一轮证据**落档**；
②把依赖 advisory 复核**刷新到当前锁定面**，并把上轮之后**新出现**的三个包 + undici 第 13 条
如实登记；③把「本轮中间产物混入树内会自伤门禁」这一实际发生的问题**修复并留档**
（见 RECHECK-266 的轮内处置节）。

## 实施清单

- [x] WP-1：deep 扫描（外部 MCP 通道）+ 密封回执与 coverage 摘录
- [x] WP-2：36 条 findings 逐类核实（含 HIGH 的测试钉住反证、AST 动态 SQL 反证）
- [x] WP-3：依赖 advisory 离线构建 + OSV 查询 + 逐条详情抓取 + 证据落档
- [x] WP-4：`docs/audits/MIMOSA_DEEP_SCAN_20261001.md` + `docs/INDEX.md` 两行登记
- [x] WP-5：记录面（本 PLAN + RECHECK-266 + MEM-179 + 索引）与 ALL_PLAN 登记
- [x] WP-6：记录写入后跑记录面判据与全量 m0；轮内自伤修复（scratch 中间产物移出树）
- [x] WP-7：残余与未覆盖逐条落档

## 设计要点

1. **「修复」的边界由证据决定**：36 条全为误报/范围外时不产出产品代码变更；把「无变更」
   写成可复核的判定（判据实跑 + 结构反证）而不是一句结论，是本轮的主要交付。
2. **误报判定沿用既有台账的口径**，但每条都按**当前字节**复核（不引用旧结论当事实）；
   与 0918 的差异只有 2 条新增 LOW（GOAL-027 的确定性实验脚本）。
3. **依赖面单独取证**：扫描器自带依赖相不可用作证据（口径同 0918）；用
   `tools/probes/probe_dependency_advisories.py` + 单次 curl 的 OSV 复核取代之。
4. **新增面如实登记**：pyjwt（1 critical + 5 high 等 13 条）、urllib3（2 high 等 3 条）、
   brace-expansion（2 high 等 3 条）均为 0918 之后**新发布**的 advisory ⇒ 不属于本轮授权
   处置范围，逐条登记 + 标注「升级需单独授权」。
5. **树内只留结论态证据**：原始 advisory 转储（含第三方包的历史版本列表）**移出树外**，
   树内仅保留版本无关的结论 JSON —— 这一条由本轮一次真实判红换来（见 RECHECK §轮内处置）。

## 证据

### ① 密封回执（§1）

```text
scanId = scan-2026-10-01T07-47-51.288Z-3fce4de3077a
seal   = sha256:66c19cdf656595ddee577628afc3f57c4783634dc4870ac1bb5ba24b738ad8eb
产物    = ~/.mimosa/security-scans/project-c96f90c714f9f3dc0bd2d97f/<scanId>/
coverage: runStatus=inconclusive / completeness=partial / verdictEffect=none
```

### ② findings 逐类核实（§3 判据实跑）

```text
uv run --frozen --no-sync python -B tools/probes/probe_dynamic_sql_forms.py --selftest
⇒ selftest: 0 failure(s)（8/8 分类正确）
uv run ... probe_dynamic_sql_forms.py --root packages --root services --root adapters
⇒ scanned 532 python files; 22 dynamic construction hit(s)（全部常量/字面量/%s 参数化；tools/ 0）
uv run ... -m pytest tests/application/protocol_authoring/test_draft_service.py -q
⇒ 13 passed in 0.12s
```

### ③ 依赖 advisory 复核

```text
413 queries（PyPI 149 + npm 264）；hitCount=4（pyjwt 13 / urllib3 3 / brace-expansion 3 / undici 13）
uv.lock sha256:98af1c42…3390（与 0918 相同）；pnpm-lock.yaml sha256:f857c70b…5cca（已更新）
证据：docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20261001.json
```

### ④ m0（记录写入之后，独占运行）

```text
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py \
    --profile m0 --keep-going      # canonical DSN pin、不接管道
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行
⇒ 4928 passed, 21 skipped（python/tests 段）
⇒ 日志 scratch/mimosa-20261001/m0b.log
```

首跑（记录写入前，`m0a.log`）有一处红：`framework/validate_bundle` 被本轮 scratch 里的
原始 advisory 转储触发「旧项目版本引用」判据；修复 = 原始转储移出树外（树内只留结论 JSON）。
详见 RECHECK-266。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | 用户指令：扫描 + 修复。先跑 deep 扫描（回执见 §1），再定处置面。 |
| 2026-10-01 | DONE | 36 条逐类核实完毕（全误报/范围外，无产品缺陷）；依赖面刷新并登记 3 个新包 + undici 第 13 条；记录落档；m0 记录写入后到 23/23。 |

## 影响报告

- **Domain/API/schema**：零变化。
- **安全/凭据**：新增审计记录与依赖证据（纯只读核查）；未改任何门禁 / pin / 策略。
  **不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：纯新增文档与记录；无运行时面变化。
- **上游版本影响**：零新依赖、零升级（新出现 advisory 只登记）。
- **剩余差距 / 下一项任务**：pyjwt / urllib3 / brace-expansion 的升级评估（需单独授权）；
  undici 承 D-03；hook 检测层承 D-04；`R-M1` 原样。
