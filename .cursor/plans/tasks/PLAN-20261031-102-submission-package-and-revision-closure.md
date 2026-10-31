---
id: PLAN-20261031-102
slug: submission-package-and-revision-closure
title: GOAL-102 子计划 —— Artifact 父指针 + 改稿闭环 + 投稿包五件制品 + 期刊闭集
status: DONE
created_at: 2026-10-31
updated_at: 2026-11-01
parent_goal: GOAL-20261031-102
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md
memory_entries:
  - .cursor/memory/entries/MEM-20261101-235-reconstructing-artifacts-drops-fields.md
---

# PLAN-20261031-102

## 背景与靶子

GOAL-20261031-102 的三个靶子（缺口是建档实测的，靶面不在本计划重新推导）：

1. **改稿闭环**：`Artifact.supersedes` 父指针（域 + 两侧序列化）+ 应答会话携带改稿
   正文 + `action_taken` 引用真实制品；
2. **投稿包**：`submission` 会话相 + 报告相装配五件制品（信 / CRediT 分工 / COI /
   数据可得性 / 补充材料索引）；
3. **期刊闭集**：`journals.yaml` 声明面 + `editorial_decision` 的两个字段 + 三判据。

## 交付面（checkbox）

- [x] EC-01 域字段 + SQLite/Postgres 序列化 + 链校验判据（五条含三环）
- [x] EC-02 改稿装配 + 引用判据 + 三条反证 + 产品入口判据
- [x] EC-03 十一相协议 + 合约 + 五件制品装配 + 11 条单元判据 + 4 条产品判据
- [x] EC-04 闭集声明 + 选择解析/校验 + 9 条判据（四向反证 + 镜像 + 评分禁入）
- [x] EC-05 收口验证器 + 断言集 + 两处清单登记
- [x] EC-06 宪章记账（程序表序 70 / 阶梯 / 进展 / 修订 / ALL_PLAN）

## 复检

收口复检：`tools/verify_goal102_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，见 GOAL 的 latest_recheck）。

## 影响报告

- **Domain**：`Artifact` 新增可选字段 `supersedes: str | None = None`（缺省 `None` ⇒
  既有构造点零回归）+ `SupersedesError` / `validate_supersedes`。**API/schema**：SQLite
  `SCHEMA_SQL` 加可空列；Postgres 追加 migration `030_artifact_supersedes.sql`（纯新增
  列，既有行 NULL = 不是任何制品的下一版）。读面 DTO / OpenAPI 快照**未动**（supersedes
  经存储面读取，不进公开路由）。
- **安全/凭据**：零变化（无新凭据、无新出网；期刊闭集是声明文件）。
- **兼容性/迁移**：旧 SQLite dev 库按既有纪律删除重建（`data/research-os-control.db`
  gitignored）；Postgres 由 `pg_migrate` 幂等补列。
- **上游**：零依赖变化。

## 验收条件

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | 域 19 + sqlite 13 passed；PG 判据在树（无 DSN 跳过） |
| EC-02 | **PASS** | 改稿闭环 8 passed + 产品入口判据（v2 / supersedes / 正文真的改了） |
| EC-03 | **PASS** | 投稿包 11 passed + 产品入口 4 条 + 协议 39 passed |
| EC-04 | **PASS** | 期刊判据 9 passed + 产品入口闭集校验 |
| EC-05 | **PASS** | 收口验证器 83 判词全 PASS；两处登记 |
| EC-06 | **PASS** | mainline + 记录面判据全过 |

## 实施清单

- [x] EC-01 域字段 + 两侧序列化 + 链校验判据（含三环反证）
- [x] EC-02 改稿装配 + 引用判据 + 三反证 + 产品入口判据
- [x] EC-03 十一相协议 + 合约 + 五件制品 + 11 条单元判据 + 4 条产品判据
- [x] EC-04 闭集声明 + 选择解析/校验 + 9 条判据
- [x] EC-05 收口验证器 + 断言集 + `_VERIFIERS` / `IN_SCOPE` 登记
- [x] EC-06 宪章记账（序 70 / 阶梯两行 / 进展+修订两表各 3 行 / ALL_PLAN）

## 证据

- 单元 **154 passed**：域 19 / sqlite 13 / 改稿闭环 8 / 投稿包 11 / 期刊 9 / 协议 39 /
  手稿装配与编辑等 55。
- 产品入口 **15 passed**（`tests/e2e/test_goal102_product_path.py` 6 +
  `test_direction_to_manuscript_product_path.py` 9；mock 中转站 + 离线 Europe PMC +
  **真容器实验**）。
- 收口验证器 `tools/verify_goal102_closeout.py --root . --verdict-only` ⇒ 83 判词全 PASS。
- 凭据审计四面 `offenders=0`。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-31 | CREATED | 建档（承 GOAL-20261031-102）。 |
| 2026-11-01 | DONE | 六个 EC 全 PASS；交付提交 + 见证提交见 GOAL 的 CI 台账。 |

## 可复用事实

1. **「会话多产物」的正确形态**：信封只承载**一个**声明产物（`_declared_deliverable_name`
   多名 ⇒ 回落 `session_message`）—— 一份会话要产出多件结构化产物时，用**并列的
   围栏 JSON 块**装进同一条回复，由装配面按**期望键**各自解开（`declared_object` 的
   key 筛选互不顶替）。
2. **字段重建白名单是丢字段的高发面**：任何手写的 `Artifact(...)` 重建（mark/迁移/存根）
   都必须带上全部字段 —— 本轮 `FakeArtifactStore.mark` 丢 `supersedes` 由判据当场抓红
   （`test_a_revised_body_supersedes_the_manuscript_it_replaces` 先红后绿）。
3. **带注解的模块级常量是 `AnnAssign`**：AST 读清单的判据必须同时认 `Assign` 与
   `AnnAssign`（`ROLE_CREDIT: dict[str, str] = {...}` 让只认 `Assign` 的读取器实测得 0）。

## 备注

- migration 撞冻结面的预案（EC-01/02 Postgres 侧移序 71）**未触发**：030 是纯新增
  可空列，没有动任何既有行。
