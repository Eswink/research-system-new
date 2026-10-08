---
id: MEM-20261008-208
title: "新增写路由会牵动两条『实测告警线』：写面端点计数与读面/出口登记的边界都是复核信号"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-339-goal-037-ec02-program-advance-entry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-340-goal-037-ec02-program-advance-entry.md
supersedes: []
tags: [write-face, read-face-registry, exit-census, measured-lines, goal-037]
---

## 做了什么

给控制面加**两个写路由**（`POST /projects/{id}/programs`、`POST /programs/{id}/advance`）
与**两个读路由**（`GET /programs/{id}`、`GET /projects/{id}/programs`）时，四条既有判据在
本地几乎同时判红 —— 它们都是**同一次改动的登记面**，但**形态各异**，逐条记下：

| 判据 | 红的形态 | 处置 |
| --- | --- | --- |
| `tests/api/test_write_face_cannot_be_bypassed.py::..._enumeration_is_derived_not_hardcoded` | `写面端点数为 63，与建档日实测的 61 不符`（**告警线**，docstring 明说「有意增删 ⇒ 复核后更新」） | 复核保护面后**更新计数**（61 → 63）+ 带日期理由；断言强度未动 |
| `tests/observability/test_privacy_read_face_canary.py::..._exact_partition...` | `未分类的读面路由`逐条点名两条新 GET | 读面登记**逐条**加（零命中档 + 理由），并把**真对象**建进金丝雀夹具（否则是空响应上的空真） |
| `tests/observability/test_privacy_exit_census.py::..._explicitly_classified` | `未分类的非 canonical 出口:services/api/routers/programs.py [failure_payload] / [read_face]` | 把新模块加进**已受判**的两个出口面的 `producers` 清单（不是新立一个豁免） |
| `tests/tooling/test_python_source_limits.py::[services\\api\\app.py]` | `create_app` **51 行**（上限 50）—— 挂两条路由把它顶过线 | **拆函数**（`_register_routers`），不调阈值 |

## 为什么这样做

这四条的共同点是：**它们不是"多写一条判据"，而是"同一次改动的四个登记面"**。它们的
强度**一格都没动**（计数是告警线、登记是逐条清单、规模是硬上限）—— 改动方式是
**同步登记**或**拆函数**。把它读成「改判据让它绿」是范畴错误：

- 告警线的**意图**就是「端点集变了就红一次、逼你复核」；复核完更新它正是它的用法；
- 读面登记与出口普查的意图是「**没有第三种状态**」：新路由/新出口必须逐条表态，
  沉默即判红；
- 规模门是硬上限 ⇒ 只能拆函数。

**连带的一条**（同一轮实测）：`create_app` 这种「长列表 + 逐条 include」的函数最容易顶破
50 行；新路由一来必然超线。**先拆再挂**比「挂了再拆」省一次红。

## 怎么做与复现

```bash
# 加完路由后，按这个顺序跑（四条会一次全报）：
uv run --frozen --no-sync python -B -m pytest \
  tests/api/test_write_face_cannot_be_bypassed.py \
  tests/observability/test_privacy_read_face_canary.py \
  tests/observability/test_privacy_exit_census.py \
  tests/tooling/test_python_source_limits.py -q
```

## 适用边界

- 适用于**控制面路由**的增删（读面 / 写面都一样）。
- 不适用于「判据本身写错」的场合：那要修的是判据逻辑；判别法是 —— 若红项点名的是
  **计数 / 清单 / 规模**这类**登记事实**，就是同步面；若点名的是**谓词 / 阈值 / 断言形态**，
  那不是同步能解决的（触达即 BLOCKED）。
- 计数类告警线的历史：61（GOAL-033 起）→ 63（本轮）；下次变动**同样**要带日期与理由。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-339-goal-037-ec02-program-advance-entry.md`
- `.cursor/plans/rechecks/RECHECK-20261008-340-goal-037-ec02-program-advance-entry.md`
