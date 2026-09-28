---
id: MEM-20260928-162
title: "读面零命中必须配「有上界的白名单」：字段名不等于内容语义，canonical 有内容才让零命中非空真"
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
scope: repository
confidence: 0.9
review_after: 2027-03-28
source_plans:
  - .cursor/plans/tasks/PLAN-20260928-231-goal-024-ec02-read-face-canary.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260928-232-goal-024-ec02-read-face-canary.md
supersedes: []
tags: [read-face, whitelist, content-canary, upper-bound, lineage-label, goal-024, ec-02]
---

## 做了什么

GOAL-024 cycle 3 把「读面不得泄漏用户内容」落成可复跑判据：**应用自己的路由树**（68 条 GET
叶子，含 FastAPI 新版 `_IncludedRouter` 包装下的子路由）**逐条**判定为「声明载体」或
「零命中面」，然后实取 + 扫描。结论：canonical 里真的有内容时，**9 条声明载体看得到内容、
51/53 条零命中路由一个金丝雀都不出现**。

## 为什么这样做（为什么值得记）

三条教训都不是"再跑一遍"能发现的，它们决定判据会不会变成假绿或假红：

- **读面天然含内容**：`GET /artifacts/{id}/content`、草稿正文路由、claims/export **契约本来
  就是**把 canonical 内容端出来 ⇒ 「读面零命中」这句话**错**，必须写成「只在声明载体上出现」。
- **白名单必须同时有上界**：只有"未分类判红"的话，把任何路由标成"声明内容"就能全绿。
  上界（声明面 ≤ 15）+ 下界（零命中面 ≥ 45）+ 实取到非空响应的零命中路由 ≥ 40，三条合起
  才让"清单正确"这件事可证伪。
- **字段名不等于内容语义（实测踩到）**：`LineageNodeDto.label` 的字面意思是"标签"，但
  `/runs/{id}/lineage` 与 `/projects/{id}/lineage` **真的**把 claim statement（正文）放进去。
  任何"按字段名推断哪条路由含内容"的做法都会在这里判错。字段名只能作线索，**必须实取核对**。
- **零命中要先证 canonical 有内容**：夹具没把金丝雀写进业务真相时，全表零命中是**空真**。
  本轮先直接读存储对象（草稿记录 / 制品 store / ledger claim）证三种金丝雀都在，再谈零命中。

## 怎么做与复现

1. **枚举**：递归路由树取 GET 叶子（`_IncludedRouter` 要拆 `original_router`），
   把结果与登记清单做**双向**差分（未分类 / 陈旧各判一次红）。
2. **分区**：每条路由 `declared_content`（理由 + 声明会承载的 kind）或 `zero_hit`（理由非空）；
   理由抽空、重复、未知判定一律判红。
3. **上下界**：声明的上界 + 零命中的下界 + 「实取到非空响应」的下界，三条都进判据。
4. **正控制**：声明载体必须真的看到它声明的内容（看不到就判红）——白名单不许靠"不返回"过关。
5. **实取要拿真对象**：路径参数用夹具里的真 id（本轮为此专门建端点/模型/制品/claim），
   取不到的路由**逐条登记**（不许静默跳过）。
6. **两向反证**：零命中路由出现金丝雀 ⇒ 判红点名"路由 + kind"；真实应用上新增未登记路由 ⇒
   分区判红；登记里出现树里没有的路径 ⇒ 陈旧判红。

## 适用边界

- 判据只覆盖**响应体文本**；响应头（`Content-Disposition` 文件名、`ETag`）**不在面**上（未证伪）。
- 白名单是**人工判定 + 机械自审**，不是从 OpenAPI/契约自动推导：语义错漏只能靠上界与实取核对兜住。
- 只对**默认离线链**（Fake runtime + SQLite 域存储）成立；真实 runtime / 工具面 / 生产部署面未验证。
- **不构成**任何"项目安全"结论（`R-M1` 未收口）。

## 来源

- 交付：`tests/observability/read_face_canary_support.py`、`read_face_route_registry.py`、
  `test_privacy_read_face_canary.py`（10 例全绿）
- 复检：RECHECK-20260928-232（`PASS_WITH_WARNINGS`；`W-1` 就是 `label` 那条实测反例）
- 记录：RECHECK-20260928-230（cycle 2 的读面 `NOT_YET_OBSERVED` 登记，本轮关闭）
