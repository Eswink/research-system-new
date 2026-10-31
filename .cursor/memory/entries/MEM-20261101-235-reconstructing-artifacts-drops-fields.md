---
id: MEM-20261101-235
title: "手写重建 Artifact 的白名单是丢字段的高发面（mark/迁移/存根三处都要全字段）"
status: ACTIVE
created_at: 2026-11-01
updated_at: 2026-11-01
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261031-102-submission-package-and-revision-closure.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md
supersedes: []
---

# 手写重建 Artifact 的白名单是丢字段的高发面

## 做了什么

`Artifact` 新增 `supersedes` 字段后，`FakeArtifactStore.mark` 仍在用手写的字段白名单
重建对象 —— 父指针被静默丢掉：装配面写对了、存储读回来是 `None`。判据
（`test_a_revised_body_supersedes_the_manuscript_it_replaces`）当场先红后绿。

## 为什么这样做

域实体加字段时，所有「逐字段复制」的重建点（fake 的 `mark`、测试私有 stub、任何
`dataclasses` 之外的手写拷贝）都是静默丢字段的候选；`dataclasses.replace` 才是全字段
安全的写法。只修 store 不够 —— 判据必须读**存储里**的值（不信任装配路径）。

## 怎么做与复现

1. 给 `Artifact`（或任何 frozen dataclass 实体）加字段前先
   `rg "id=current.id" adapters/ tests/` 找重建点；
2. 逐处补齐（`dataclasses.replace(current, state=...)` 最稳）；
3. 判据断言 `store.meta(...)` 读回的字段，而不是装配函数的返回值。

## 适用边界

- 只覆盖「手写逐字段重建」这一类；`replace` 与序列化两侧（SQLite/PG 行）另有各自的
  往返判据。
- 测试私有 stub（如 `tests/application/artifacts/test_retention_schedule.py` 的本地
  stub）如果它的夹具从不携带新字段，可以不补 —— 但要在残余里如实登记。

## 来源

- GOAL-20261031-102 EC-02 的实测（交付提交见该 GOAL 的 CI 台账）。
