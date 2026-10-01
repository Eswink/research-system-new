---
id: MEM-20261001-179
title: "第三方 advisory 原始转储含历史版本列表（如 pyjwt 的 0.2.x / 0.3.x 系列）⇒ 落在树内会被 validate_bundle 的「旧项目版本引用」判据判红；树内只留版本无关的结论态证据"
status: ACTIVE
created_at: 2026-10-01
updated_at: 2026-10-01
scope: repository
confidence: 0.9
review_after: 2027-04-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261001-265-mimosa-deep-scan-disposition.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261001-266-mimosa-deep-scan-disposition.md
supersedes: []
tags: [mimosa, validate-bundle, audit-evidence, scratch, gate-self-harm, goal-027, plan-265]
---

## 做了什么

Mimosa 深扫处置轮（PLAN-20261001-265）在跑全量 m0 时**实际判红一次**，红点是自己造成的：

- 判红：`framework/validate_bundle` ⇒ `发现旧项目版本引用: scratch\mimosa-20261001\vuln-*.json /
  advisories\*.json`（6 个文件）。
- 根因：`validate_bundle.py` 有一条「旧项目版本」正则
  （`0.2.x` 与 `0.3.x` 系列的字面串，VERSION 现为 `0.4.0`），
  而我从 OSV 抓的**原始转储**里，第三方包（pyjwt）的 `affected[].versions` 恰好列出
  该系列历史版本 ⇒ 命中判据。
- 修复：把**原始转储移出树外**（`%LOCALAPPDATA%\Temp\mimosa-20261001-raw\`），
  树内只保留**版本无关**的结论 JSON（id / CVE 别名 / severity / 修复版本 / URL）。
  复核 `validate_bundle.py` ⇒ `EXIT=0`。

## 为什么这样做

- **判据问的是「树内文本里有没有旧版本串」**，不是「这些话是谁说的」：第三方数据的转储
  与自家引用**同权受判**。取证资产越「原始」，越容易带上别人家的版本清单。
- **修复方向是移动证据，不是放宽判据**（本仓禁令：不得削弱门禁）。结论态证据保留全部
  判定所需字段，原始转储留在**仓库外**的固定路径，可追溯且不再污染扫描面。
- 与 `scratch/` 既有教训同族：**中间产物不是免费场地** —— 前有「跑门期间别改工作树」，
  现在再加一条「**跑门之前先清树内中间产物**」。

## 怎么做与复现

1. 复现判红：把任何含 `0.2.x` / `0.3.x` 系列字面串（如 OSV 原始 advisory JSON）的文件放进树内
   （`scratch/` 也算，`validate_bundle` 会扫到），跑
   `uv run --frozen --no-sync python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`
   ⇒ `EXIT=1` + `发现旧项目版本引用: <path>`。
2. 修复：`mv` 原始转储到仓库外（本轮用 `%LOCALAPPDATA%\Temp\mimosa-20261001-raw\`），
   树内只留结论 JSON；复跑同一命令 ⇒ `EXIT=0`。
3. 判据位置：`.cursor/skills/system-spec-check/scripts/validate_bundle.py` 的
   `old_version` 正则（约 `:318`，写此记忆时的行号）。
4. 佐证命令：全量 m0 首跑日志 `scratch/mimosa-20261001/m0a.log`（红）、
   记录写入后终态 `scratch/mimosa-20261001/m0b.log`（`PASS: profile=m0; 23 deterministic checks`）。

## 适用边界

- 该正则是**文本级**判据：任何含旧版本形态的数字串都会被扫到（第三方数据、样例、测试夹具）；
  本记忆不评价该判据的宽窄，只记录其**行为**与安全移出方案。
- 移出后的原始转储**不在仓库证据链内**（仓库外路径会随机器清空）；树内结论 JSON 必须
  **自带判据所需字段**（本轮的 `docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20261001.json`
  即该形态），否则证据会退化成「引用了一个不在树里的文件」。
- 不得据此宣称项目安全（`R-M1` 仍在）；扫描为 static-only / coverage partial，
  不得把「扫描干净」读成「无漏洞」。

## 来源

- `PLAN-20261001-265` 与 `RECHECK-20261001-266` 的「轮内处置」节；
- 判据：`.cursor/skills/system-spec-check/scripts/validate_bundle.py`（`old_version`）；
- 日志：`scratch/mimosa-20261001/m0a.log`（判红）、`scratch/mimosa-20261001/m0b.log`（终态）；
- 证据：`docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20261001.json`；
- 同族记忆：[[local-gate-protocol-and-flake-classes]]（跑门期间别改树）、
  [[record-face-is-gated-run-the-gate-last]]（记录面受门覆盖：门必须最后跑）、
  [[mimosa-scanner-false-positives]]（扫描器误报形态）。
