---
id: MEM-20260927-150
title: "凭据泄漏判据要按出口逐个判，并分「结构 / 形态 / 裸值」三档如实断言——脱敏是形态匹配，不是值匹配"
status: ACTIVE
created_at: 2026-09-27
updated_at: 2026-09-27
scope: repository
confidence: 0.9
review_after: 2027-03-27
source_plans:
  - .cursor/plans/tasks/PLAN-20260927-203-control-plane-token-never-leaks.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260927-204-control-plane-token-never-leaks-recheck.md
supersedes: []
tags: [adversarial-self-check, credential-leak, redaction-shape, observability-privacy, goal-021, ec-02]
---

## 做了什么

对控制面认证 token 做**泄漏面**对抗性自检（GOAL-021 EC-02，AGENTS.md §10），交付
`tests/api/test_control_plane_token_never_leaks.py`（312 行 / 12 例），按**出口**逐个判：
日志（捕获 handler）/ 遥测 span 属性 / 401 响应体 / canonical 事件 payload /
前端持久层（引用既有判据）/ 记录面。

## 为什么这样做

- **「不要泄漏凭据」不是一个判据，是六个出口的六个判据**。按出口分开判，红的定位才是准的；
  合成一条「哪里都不许出现」，红了也不知道堵哪。
- **脱敏是`形态匹配`，不是`值匹配`**（实测）：`redact_text` 的
  `_BEARER_RE` 会把 `Bearer <x>` 换成 `REDACTED`，但**裸的不透明串**放在
  **允许清单内**的字符串键里**会原样留下**。⇒ 判据必须**分档**：
  ① **结构**档（未知键整个丢弃——`authorization` / `raw_headers` 根本进不去词表层）；
  ② **形态**档（允许键 + bearer 形态 ⇒ 必被脱敏，硬断言）；
  ③ **现状**档（裸不透明串 ⇒ 如实断言它**会**留下）。
  第三档看着像「判了个缺陷」，其实是**把边的位置写下来**：它防的是
  「以为已经覆盖而其实没有」。将来若强化为「允许键不得承载凭据」，该断言会红并提示更新。
- **日志判据要自带对照**：`test_the_capture_mechanism_itself_works` 先证明
  **捕获装置能截到日志**（发一条哨兵记录）。否则「零命中」可能只是
  「什么都没捕到」这类**假绿**——这是本轮设计时最先想到的失效模式。
- **401 文案要同时判两件事**：不泄漏凭据 **与** 成因可诊断（缺 Bearer 头 / 不匹配
  各自点名）。只判「不含 token」会把「两个 401 合并成一句话」这种**可用性倒退**
  放过去。

## 怎么做与复现

```bash
# 六出口现状取证（只读；含对抗输入）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec02-probe-leak-surfaces.py

# 判据本体
uv run --frozen --no-sync python -B -m pytest tests/api/test_control_plane_token_never_leaks.py -q
```

**反证形态（已实测可判红）**：在 `PrincipalAuthMiddleware.dispatch` 里对
`provided` 记一条日志（`logging.getLogger(...).warning("received token %s", provided)`）
⇒ `test_no_log_record_contains_the_token` **1 failed** ⇒ 逐字节复原
（sha256 `ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`）⇒ 12 passed。

## 适用边界

- **形态档不是值档**：裸不透明串在允许键内不会被脱敏（见上）。本判据**不**宣称
  「任意形态的凭据都拦得住」。
- **前端持久层**由既有 `tests/api/test_security_scan.py` 判（无条件字面量断言），
  本判据**不重复**；它只做**交叉引用**。
- **日志面判的是本进程捕获到的记录**（根 logger + handler）。生产侧的**外部采集链**
  （collector / 日志聚合）不在本轮范围。
- 判据中的 token 是**合成假值** ⇒ **不**验证真实 token 的形态分布；若真实 token
  恰是某种会被形态匹配命中的前缀，行为可能不同（应优先选**不被形态匹配**的高熵随机值）。
- **本判据证明「已声明的出口不泄漏」，不能证明「不存在未声明的出口」。**

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260927-203-control-plane-token-never-leaks.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260927-204-control-plane-token-never-leaks-recheck.md`
- 取证脚本：`scratch/goal021-ec02-probe-leak-surfaces.py`
- 相关：`MEM-20260926-141`（判据自身恒真）、`MEM-20260927-149`（枚举来自代码）
