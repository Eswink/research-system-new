---
id: MEM-20260928-161
title: "出口普查必须是「受判 ∪ 带理由豁免」的分区：判据自跑第一件事是抓自己清单的错"
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
scope: repository
confidence: 0.9
review_after: 2027-03-28
source_plans:
  - .cursor/plans/tasks/PLAN-20260928-227-goal-024-ec01-privacy-exit-census.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260928-228-goal-024-ec01-privacy-exit-census.md
supersedes: []
tags: [exit-census, partition, explicit-classification, shape-predicate, self-audit, goal-024, ec-01]
---

## 做了什么

GOAL-024 EC-01 把「非 canonical 出口」做成**源码内的清单**：

```text
候选 = AST 形态谓词 × 产品根（apps/services/packages/adapters）
候选 → 恰好一条分类：受判出口（judged） | 带理由的豁免（exempt）
问题 = 未分类 ∪ 重复分类 ∪ 登记陈旧 ∪ 空理由 ∪ 受判面无观测方式/无生产者
```

实测剖面：**113 个候选**，7 种形态（`application_log` 2 / `stdout` 4 / `otlp_span` 12 /
`otlp_metric` 11 / `disk_write` 8 / `read_face` 29 / `failure_payload` 47），
受判出口 **6** 条（traces / metrics / 应用日志 / 读面 / 失败载荷 / 磁盘制品）+
豁免出口 1 条（stdout：默认进程内路径**没有**生产点）+ 豁免生产者 **25** 条（逐条带理由）。

**判据第一次自跑就抓到两处自己的真错**：

1. **重复分类**：`adapters/otel/failsafe.py [otlp_metric]` 同时被受判面
   `otlp-metrics-wire` 与豁免面认领 —— 两份来源互相矛盾，只有「重复也要判红」才看得见。
2. **形态自检样本写错**：`read_face` 的样本写成赋值式 `f = router.get('/x')(f)`，
   而谓词认的是**装饰器**位形 ⇒ 样本不匹配。**谓词是对的，样本是错的** ——
   若没有「每种形态一段同源正样本」，这条谓词可能悄悄永不命中（发现集变小而判据仍绿）。

## 为什么这样做（为什么值得记）

- **只列「受判面」的清单无法证明完整性**：漏掉的出口不会出现在任何地方。把**豁免**也做成
  **带非空理由的显式条目**，清单才成为**分区**，而「未分类」与「重复」两条断言让分区**自审**。
- **空发现 = 空真**：形态谓词失效、扫描根写错、只扫了空目录，都会让「全部已分类」恒真。
  必须有一条**非空下限**（本轮：候选 ≥ 50 且命中形态 ≥ 6）与**每形态正样本**。
- **登记是双向的**：清单里的生产者消失（**陈旧**）也必须判红，否则清单会「看起来永远覆盖」。
- **真实树按压比合成候选更硬**：本轮在真实产品根新建一个只含 `print` 的模块 ⇒ 判据立刻
  点名 `未分类的非 canonical 出口:packages/application/observability/press_probe_module.py [stdout]`。

## 怎么做与复现

任何「枚举全部 X 并证明没有漏」的判据（出口、受判面、门禁面、扫描根）：

1. **发现**：形态谓词 + 声明式根集合写在源码里（新增形态必须显式加入）。
2. **分区**：`judged` ∪ `exempt(理由非空)`；**没有第三种状态**。
3. **四类红**：未分类 / 重复分类 / 登记陈旧（双向）/ 空理由。
4. **每形态一段正样本**（同文件内，`ast.parse` 内存样本即可），谓词静默失效即红。
5. **非空下限**：候选计数与形态计数都有地板，防「空集上的全绿」。
6. 按压矩阵至少覆盖「真实树新增出口」与「清单条目消失」两向，且**逐字节复原**（raw `sha256`）。

复现（本仓）：`uv run --frozen --no-sync python -B -m pytest tests/observability/test_privacy_exit_census.py -q`
⇒ 13 passed；按压任意一条清单条目（Edit 工具）⇒ `1 failed, 12 passed` 且失败消息点名 `(module, kind)`。

## 适用边界

- 射程是**形态驱动**的：`UNCOVERED_SHAPES` 里显式登记的形态（显式 `open` 写、目录镜像、
  DB 文件、出站请求体）**不在**普查内 —— 清单只保证「已声明的形态没有漏」。
- 粒度是 `(module, kind)`：同一模块内**新增同形态**发射点不产生新的分类需求（漏位置不漏形态）。
- `exempt` 是**有理由的登记**，不是「已证明永不进入默认路径」；组合根被改写时需要重新分类。
- 与 [MEM-20260928-160](MEM-20260928-160-union-scope-hides-a-shrinking-required-list.md) 配套：
  受判面的**下界**必须来自判据源码里的必备清单（本判据由 `REQUIRED_JUDGED_EXITS` 给出）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260928-227-goal-024-ec01-privacy-exit-census.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260928-228-goal-024-ec01-privacy-exit-census.md`
  （`W-1`…`W-6`；含四向按压与 raw `sha256` 复原证据）
- 交付物：`tests/observability/privacy_exit_census.py`（259 行）+
  `tests/observability/test_privacy_exit_census.py`（407 行 / 13 例）
