---
id: MEM-20260917-066
title: "完整安全审计的终态写法：hook 侧 enobufs 与独立密封深扫是两条通道、判定实跑不靠读报告、误报也要有反证"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-091-security-audit-terminal-state.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-091-security-audit-terminal-state.md
supersedes: []
tags:
  - security-audit
  - mimosa
  - false-positive-disposition
  - evidence
  - coverage-gap
---

# 安全审计终态：扫描跑通之后要交付什么

## 做了什么

GOAL-004 cycle 8（EC-07）把 `scanner_enobufs` 意义上的"审计不可用"收口成**终态 a**：
独立密封深扫跑通（`scan-2026-09-17T20-05-18.700Z-663d0976701f`，seal
`sha256:b2af6739…`，36 findings = high 3 / medium 28 / low 5），逐条处置并于
`docs/audits/MIMOSA_DEEP_SCAN_20260917.md` 落终态记录。

## 为什么这样做

1. **两条通道别混**：commit hook 侧的 `scanner_enobufs`（拿不到完整结论）与 MCP
   独立触发的密封深扫是**两条通道**；后者跑通**不消除**前者现象。记录里必须同时写，
   否则下一轮会误以为"已解决"。
2. **`inconclusive` 是常态不是回归**：同一 projectId 连续 6 次深扫（09-16 → 09-17）
   剖面逐次相同（3/28/5）、`runStatus=inconclusive` + `completeness=partial` 同口径
   （与 `docs/audits/PA1_MIMOSA_REVIEW.md` 的 09-03/09-06 记录一致）⇒ **该扫描器在本
   仓库只做静态面**。判 PASS 的依据只能是「逐条处置 + 可重跑证据」，不能是"没报问题"。
3. **误报判定要落到可重跑的东西**：判"env → SQL 文本"为误报，靠的是
   (a) 产品树全量动态 SQL 形态检索零命中 **且** (b) 同一模式对四种蓄意形态命中、
   对参数化写法不命中（**反证**），再加 (c) 汇点逐行核对（迁移文件文本 / 字面量 DDL /
   `%s` 参数化 INSERT，env 只进 DSN）。少了 (b)，(a) 可能只是模式写错。

## 怎么做与复现

```bash
# 独立密封深扫：MCP security_scan_start(project=…, depth=deep) → security_scan_status 轮询至 completed
# 产物：~/.mimosa/security-scans/<projectId>/<scanId>/{scan-manifest,findings,coverage,seal,report}
# 逐件摘要复核（seal.json.artifacts 三件）：
python -c "import hashlib,json,pathlib; a=json.load(open('seal.json'))['artifacts']; print({k:('ok' if 'sha256:'+hashlib.sha256(pathlib.Path(k).read_bytes()).hexdigest()==v else 'BAD') for k,v in a.items()})"
# 产品树动态 SQL 形态检索（期望空）：
grep -rn --include=*.py -E "execute\([^)]*(f\"|f'|%s\" %|\.format\(|\+ *[a-z_]+)" adapters/ packages/ services/ apps/ tools/ examples/
```

## 适用边界（踩过的坑）

- **聚合 seal 不可由产物复算**：`seal.json` 顶层 `digest` 的合成方式在扫描器内部，多种
  朴素合成都不等于它 ⇒ 记录里只宣称"逐件摘要可复核"，不宣称聚合值可复算。
- **扫描输入含 gitignored 内容**：`scratch/`（17 条）与 `artifacts/`（2 条 HIGH）合计
  19/36 条 findings 落在非仓库内容上；`artifacts/` 内还有一个**明文 token 文件**
  （从未提交，`git log --all` 为空，`.gitignore:36` 覆盖）。要"只看仓库"必须在干净
  checkout 上重跑。
- **写路径守卫会拦 Bash 直写源码**：本轮想把反证样本写进仓库做负验证，被 Mimosa
  PreToolUse 拦下并要求改走 Write/Edit ⇒ 改用 stdin 喂给 grep，反证照样成立。
- **依赖 advisory 未署名**：密封产物只给「182 包 / 命中 1 包 1 条」，`packages` 数组为空
  ⇒ 无法定位包名，联网复核超出本机可验证范围 ⇒ 作为未决项（W-1）写进记录，
  **不得读作"无已知漏洞"**。
- 相关：[[MEM-20260915-047]]（声明要有消费者 / 证据口径）、
  [[MEM-20260917-065]]（同 cycle 族的诚实边界写法）。

## 来源

- PLAN-20260917-091 / RECHECK-20260917-091（GOAL-20260917-004 cycle 8 = EC-07）。
