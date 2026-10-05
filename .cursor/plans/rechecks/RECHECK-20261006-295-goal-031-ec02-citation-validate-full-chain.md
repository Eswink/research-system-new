---
id: RECHECK-20261006-295
slug: goal-031-ec02-citation-validate-full-chain
title: 复检：GOAL-031 EC-02 —— `citation.validate` 全链（三态判定 + 单一取数面 + 承接放行 + pin 最小追加 + 两向反证）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-06
updated_at: 2026-10-06
plan_id: PLAN-20261006-295
reviewer: root-agent
parent_goal: GOAL-20261006-031
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/contracts
    tests/application/preflight tests/application/test_m2_audit.py
    tests/architecture/python/test_capability_coverage_is_implemented.py -q ⇒ 586 passed / 69 skipped
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/contracts tests/application/preflight
    tests/application/test_m2_audit.py
    tests/architecture/python/test_capability_coverage_is_implemented.py tests/adapters
    tests/loaders -q ⇒ 1157 passed / 72 skipped
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/api/test_production_session_tool_registration.py
    tests/api/test_catalog_merge.py -q ⇒ 18 passed
owners:
  - root-agent
---

# RECHECK-20261006-295 — GOAL-031 EC-02（`citation.validate` 全链）

## 结论

**PASS_WITH_WARNINGS**。EC-02 的五半（三态规则 / 单一取数面 / 承接+放行 / pin 最小追加 /
两向反证）**实测到场**；路线 F（新增 provider `ncbi_citation`）**如实**把受影响的既有判据面
收到最小（1 条目录集合字面量 + 1 条夹具 pin 源），且**三条 pin 判据文件里两条删除行为 0**。

## 检查结果

| EC-02 要求 | 判据 / 读数 | 实测 |
| --- | --- | --- |
| (a) 三态规则显式 | `test_citation_validate_three_state.py`（12 条）+ `parsing.CITATION_VERDICTS` | 三常量在场；三输入 ⇒ 三判词**两两不等**（二值实现必红） |
| (b) 取数复用既有 `_elink` | 行为（两条能力读到同一 links）+ 结构（`'elink.fcgi'` 在实现里**只 1 处**） | 同一读数、各恰好一次请求、取数点唯一 = 1 |
| (c) 承接 + 放行 | 目录声明 + 出厂绑定表 + `policy.yaml` + AUDIT 登记面 + 覆盖分类表 | `ALLOW` + `matched allow rule`；scope = `approved_tool_providers`（与同取数 provider 的既有放行同栏） |
| (d) pin 最小追加 | `git diff --numstat` + 逐字节删除行对照 | 两条 pin **判据**文件删除行 0（纯追加）；`run_fixtures.py` **-1 行**（见 W-EC02-1，如实登记） |
| (e) 反证两向 | `UNSUPPORTED`（linkset 在场零链接）/ `UNDETERMINED`（无 linkset） | 两者判词**不等**；判词点名 `zero PMC links` / `no linkset` |

## 三态的语义边界（写在这里，免得被读成二值）

```text
SUPPORTED    : 来源解析出 linkset 且 ≥1 条 PMC 链接 ⇒ 引用被来源支持
UNSUPPORTED  : 来源解析出 linkset 但零链接        ⇒ 引用不被来源支持（**说了「零条」**）
UNDETERMINED : 来源没有 linkset                   ⇒ **无法判定**（**根本没说话**）
```

后两者在二值实现里会合并 —— 本判据的 `test_the_three_verdicts_are_pairwise_distinct`
专门钉住这一点。

## 按压（两处，判词归档）

1. **三态非二值**：三种输入 ⇒ 三判词两两不等（`{SUPPORTED, UNSUPPORTED, UNDETERMINED}`）；
   `test_undetermined_is_not_supported` 单独断言「无法判定 ≠ 成立」。
2. **单一取数面**：行为臂（同一 mock 响应 ⇒ 两条能力 `pmc_links` 逐字相等）+ 结构臂
   （AST 数 `elink.fcgi` 调用点 == 1）；对照臂证明「换一种归一化会给出不同读数」
   （本判据不是在恒真断言）。

## 复检发现（如实登记）

- **`W-EC02-1`｜`run_fixtures.py` 的 `_PROVIDERS` 追加产生 1 行删除**：它是**单行 tuple**
  字面量 ⇒ 追加条目必然重写该行（`+8 / -1`）。这正是 `W31-3` 预先登记的结构性事实，
  本轮**如实出示**而非伪称删除为 0。**两条 pin 判据文件的删除行为 0**（纯追加），
  断言逐字节未改。⇒ 「pin 零删除」在**判据断言**面上成立；在**夹具数据面**上受既有
  文件形态限制（改写一行数据，不动任何断言）。
- **`W-EC02-2`｜`citation.validate` 是「声明层 + 判定层」两层新增**：能力此前已在
  `roles.yaml` / `skills.yaml` / 词表里（声明层），本轮补的是**实现层**（provider + 工具 +
  三态）。⇒ 本 EC 的「新承接」**不含**新的能力名进词表（词表 46 条未变）。
- **`W-EC02-3`｜判定只在**离线 mock** 上实测**：CC 网络面（真实 elink 响应）不在本判据
  射程内 —— 真实出网属 live 面，本轮**默认门离线**（§11 与既有 D-13 口径）。
  三态的**结构**判定（linkset 在场性 / 链接数）与真实响应形态一致（`normalize_elink`
  是既有实现，`citation.inspect` 已用它跑过真实响应），但**「真实来源的 linkset 形态分布」
  未被本判据采样**。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通 / exactly-once 未实现（**明确否认**；口径只能是 at-least-once +
idempotency + deduplication）。**不得**据此宣称项目安全。
