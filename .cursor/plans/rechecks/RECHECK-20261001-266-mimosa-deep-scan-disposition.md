---
id: RECHECK-20261001-266
slug: mimosa-deep-scan-disposition
title: Mimosa 深扫（2026-10-01）处置复检：密封回执 / 36 条逐类核实 / 依赖面刷新 / 记录面与 m0
plan_id: PLAN-20261001-265
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-01
completed_at: 2026-10-01
owners:
  - root-agent
---

# RECHECK-20261001-266 — Mimosa 深扫处置复检

**复检口径**：不采信叙述与旧台账的转述；本文件给出**可复核观察面**（命令 / 判词行 / `rc` /
实测值），且 findings 的判定按**当前字节**重新取证。**未实跑的不记通过**。

## 检查结果

### 1. 密封回执与覆盖状态（AC-1）

- scanId `scan-2026-10-01T07-47-51.288Z-3fce4de3077a`；seal
  `sha256:66c19cdf656595ddee577628afc3f57c4783634dc4870ac1bb5ba24b738ad8eb`
  （覆盖 manifest / findings / coverage 三份语义产物；逐份摘要已在处置期核对）。
- `runStatus=inconclusive`、`completeness=partial`（threatModel partial：0 入口/0 主体/0 授权面；
  validation completed 但 investigated=0）、`verdictEffect=none`、
  `evidenceBoundary=static_only_no_runtime_execution`。⇒ 结论射程只到「已覆盖范围内」。

### 2. 36 条 findings 逐类核实（AC-2）

**HIGH ×1**（`packages/application/protocol_authoring/service.py:103`）：
- 当前字节复核：加载器为 `yaml.SafeLoader` 子类（同文件 `class _StrictLoader(yaml.SafeLoader)`），
  仅追加重复键拒绝与尺寸上限；不使用 FullLoader/Loader。
- 反回归判据实跑：`uv run --frozen --no-sync python -B -m pytest
  tests/application/protocol_authoring/test_draft_service.py -q` ⇒ **13 passed**（含
  `!!python/*` 标签拒执行、loader 子类断言、重复键拒绝、尺寸上限各用例）。判**误报**。

**MEDIUM ×28**（跨文件污点启发式）：
- 结构反证实跑：`tools/probes/probe_dynamic_sql_forms.py --selftest` ⇒ 8/8 分类正确；
  `--root packages --root services --root adapters` ⇒ 532 文件、**22 处**字符串构造的
  `.execute` 首参，全部为常量/字面量/`%s` 参数化（与 0918 同值），`tools/` 内 **0** 处。
- 逐组复核：`scratch/` ×17 与 `tools/probes/` ×10 的源均为环境变量（DSN 连接串形态，
  见 `tools/probes/probe_cancel_race.py:36`），汇点为 `adapters/postgres/db.py` 的 `migrate()`
  —— SQL 文本来自仓库内 migrations 文件与字面量，DSN 是连接目标不是 SQL；
  `services/worker/__main__.py:135` 的路径汇点为 `tempfile.mkdtemp` 隔离目录
  （`adapters/execution/gpu_probe.py:148`）。判**误报**。

**LOW ×7**（不安全随机数）：全部为实验脚本 `random.Random(seed)` 确定性语料
（m12 ×5 既有 + `exact_match_index_benchmark.py:41`、`sort_analysis_baseline.py:35` 两条新增）。
判**误报**。

**点名面**：四个在改文件（ModelDetails.tsx / model_drift.py / dto/models.py / middleware.py）
本轮 findings 零命中；其 git-status「M」经复核为纯 CRLF/LF 行尾差异（内容与 HEAD 相同，
`git diff` 为空补丁），与安全面无关。

**小结**：36/36 误报或范围外 ⇒ 无产品代码缺陷、无产品代码变更。

### 3. 依赖 advisory 复核（AC-3）

- 复跑：`probe_dependency_advisories.py` 离线构建 **413** 查询（PyPI 149 + npm 264）；
  单次 `curl` 打 `https://api.osv.dev/v1/querybatch`（公开只读、无凭据）；
  合并出记录 `hitCount=4`。
- 锁定面：`uv.lock` `sha256:98af1c42…3390`（与 0918 证据相同）；`pnpm-lock.yaml`
  `sha256:f857c70b…5cca`（已随 GOAL-016/018 更新）。
- 命中：pyjwt 2.13.0 ×13（含 1 critical；修复 2.14.0，一条需 2.15.0；均 published
  2026-09-29…10-01）、urllib3 2.7.0 ×3（2 high；修复 2.8.0）、brace-expansion 5.0.9 ×3
  （2 high；修复 5.0.10/11/12）、undici 5.29.0 ×13（相对 0918 +1 条 LOW）。
- 三个包为 0918 之后**新出现** ⇒ 只登记、不处置（升级 pin 需单独授权，见「结论」）。

### 4. 门禁与记录面（AC-4）

- 顺序：本记录与 PLAN / MEM / 索引**先**写完，**再**跑全量门（承 LOCAL_GATE_PROTOCOL 的
  记录面覆盖条款）。
- m0 终态行与用例数见下方「m0」小节；`framework/validate_bundle` 的轮内自伤与处置见下节。

### 轮内处置（真实判红一次，如实登记）

首跑（`scratch/mimosa-20261001/m0a.log`）红在 `framework/validate_bundle`：
`发现旧项目版本引用: scratch\mimosa-20261001\vuln-*.json / advisories\*.json` ×6。
根因：`validate_bundle.py` 对树内文本有「旧项目版本」正则（`0.2.x` / `0.3.x` 系列字面串），而
**原始 OSV 转储**里第三方包（pyjwt）的受影响版本列表恰好含该系列字面串。
修复 = 把原始转储**移出树外**（`%LOCALAPPDATA%\Temp\mimosa-20261001-raw\`），
树内只保留**版本无关**的结论 JSON（id / severity / 修复版本 / URL）。
复核：`validate_bundle.py` ⇒ `EXIT=0`。此坑已写入 MEM-179。

**该判红随后又复发一次（第二个实例，同样如实登记）**：本记录与 MEM-179 的初稿在**引述**该
判据时写了字面版本串 ⇒ 记录自身再次命中同一正则。两处改为「`0.2.x` / `0.3.x` 系列」表述后干净。
⇒ 结论：**记录引述判据文本时，也必须不命中被引述的判据**。

## m0

```text
uv run --frozen --no-sync python -B \n  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行
⇒ 4928 passed, 21 skipped（python/tests 段）
⇒ 日志 scratch/mimosa-20261001/m0b.log（canonical DSN pin、记录写入之后、独占运行）
```

用例数与 GOAL-027 收口同值（4928）：本轮零产品代码/判据变化，条数不变符合预期。

## 结论

`PASS_WITH_WARNINGS`。

- **36 条 findings 全部为误报或范围外**（依据见 §2），**无产品代码缺陷、无产品代码变更**；
  本轮「修复」的实际动作 = 证据落档 + 依赖面刷新 + 一处轮内自伤修复（原始转储移出树）。
- **残余与未覆盖（逐条）**：
  1. **pyjwt 2.13.0**（1 critical + 5 high 等 13 条，修复 2.14.0）——0918 后新出现，**未处置**，
     升级 pin 需单独授权；
  2. **urllib3 2.7.0**（2 high 等 3 条，修复 2.8.0）——同上；
  3. **brace-expansion 5.0.9**（2 high 等 3 条，修复 5.0.10+）——同上（dev 链）；
  4. **undici 5.29.0**（13 条）——维持现状（D-03）；
  5. **hook 检测层**——维持现状（D-04「本项不做」）；
  6. **`R-M1`（`scanner_enobufs`）**——原样保留；
  7. **未覆盖范围**——static-only（无运行时验证）/ threatModel partial（0 授权面）/
     读面未认证 / 多租户 / BOLA·BFLA / 部署面。
- **不宣称**项目安全；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
