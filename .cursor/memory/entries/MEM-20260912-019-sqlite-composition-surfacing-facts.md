---
id: MEM-20260912-019
title: SQLite 组成浮现与前后端接缝收口的机械事实
status: ACTIVE
created_at: 2026-09-12
updated_at: 2026-09-12
scope: repository
confidence: 0.9
review_after: 2026-12-12
source_plans:
  - .cursor/plans/tasks/PLAN-20260912-040-frontend-backend-seams-and-surfacing.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260912-040-frontend-backend-seams-and-surfacing.md
supersedes: []
tags:
  - sqlite-composition
  - artifact-store
  - gitignore
  - mimosa-scanner
  - test-fixture
---

# MEM-20260912-019 — SQLite 组成浮现与接缝收口的机械事实

## 做了什么

PLAN-20260912-040 把「已有实现但没接线/没端点」的接缝接上时，实测并固化四条会
反复出现的机械事实（每条都会以假象误导排障，须以不削弱断言的方式处置）：

1. `SqliteArtifactStore` 的 `put/mark/delete` 原先裸 `self._conn.execute(...)`
   不带 `with self._conn:`（sqlite3 默认 `isolation_level=""` 下 DML 开隐式事务），
   元数据行只在写连接可见；把它接进 `_assemble_sqlite` 做「重启持久化」时
   `test_artifact_survives_reassemble` 直接暴露（旧 FakeArtifactStore 无此问题）。
   处置：三处写路径包 `with self._conn:`。教训：给共享连接型 SQLite adapter 做
   持久化接线前，先跑「close 后重开同文件读取」往返测试。
2. 根 `.gitignore` 的 `data/`（行 21，无前导斜杠）匹配任意层级的 `data/` 目录，
   包括 `apps/web/src/features/example-console/data/*.json`。这些 example fixture
   是工作树资源、不在 git 内；example 树 `import ... from "./data/x.json"` 只在
   工作树存在时可构建/跑 e2e。删除其中的死 fixture 是工作树清理、不产生 git
   变更（`git ls-files` 为 0，`git add` 报 pathspec did not match）。fresh clone
   不含这些文件属既有隐患，非本批引入。
3. 密封深度扫描（Mimosa L3）对 `packages/application/protocol_authoring/
   service.py:103` 的 `yaml.load(text, Loader=_StrictLoader)` 报 HIGH「不安全
   反序列化」属文本匹配误报：`_StrictLoader` 是 `yaml.SafeLoader` 子类（无任意
   对象构造能力），已有 `# noqa: S506` + 注释说明，重复键拒绝正是 SafeLoader
   钩子。commit-gate 与 sealed scan 采样/规则覆盖不同：sealed scan 能命中而
   此前基线记「主树 high=0」。处置：登记为已判定误报（docs/audits/PA1_MIMOSA_
   REVIEW.md 2026-09-12 节），不据此判定「项目安全」（coverage 仍 static_only）。
4. `tests/api/run_fixtures.py` 的 `make_run_ready_deps` 注释长期声称「ledger 为
   受控 Fake」但从未把它注入 `ApiDeps`（只喂了编排链内部），导致 live e2e 的
   evidence/claims/experiments 读链从未真正走过。教训：测试装配「与生产组成对齐」
   须逐字段核对，注释漂移本身是缺陷信号；本批补 ledger 共享 + agent/settings/
   override/worker/experiment 五个 SQLite store 注入，live e2e 才拿到真实读链。

## 为什么这样做

接缝类任务（既有代码接线，非新功能）的失败模式是「接了但没生效」或「测试双份
假绿」。以上四点各自造成过一类假象：不 commit 的持久化、被忽略的 fixture、
误报的 HIGH、缺注入的只读链。逐条以对齐生产 + 补往返/复跑证据的方式处置，不
放宽规则、不伪造状态。

## 怎么做与复现

- 事实 1：`uv run --frozen --no-sync pytest tests/api/test_composition_sqlite_persistence.py -q`
  （重启往返 artifact 可读）；回归在 `adapters/sqlite/artifact_store.py:75,125,151`。
- 事实 2：`git ls-files apps/web/src/features/example-console/data/` = 0、
  `git check-ignore -v .../run.json` 命中 `.gitignore:21:data/`。
- 事实 3：sealed scan `scan-2026-09-12T13-05-21`（seal `sha256:d01ee46b…`），
  处置表见 docs/audits/PA1_MIMOSA_REVIEW.md 末节。
- 事实 4：`RESEARCHOS_POSTGRES_DSN=<test dsn> uv run --frozen --no-sync pytest tests/api -q`
  = 237 passed；live e2e `pnpm run test:e2e:live` = 10/10（含新增参考协议/
  custom-role/clone/审批历史面）。

## 适用边界

任何「把既有 adapter/store 接进 composition root」「example fixture 隔离」
「Mimosa HIGH 处置」「测试装配与生产组成对齐」的后续工作（PLAN-041/042 尤其）。
事实 2 的 gitignore 结论适用于仓库任意层级 `data/` 目录（根 `data/` 模式无前导
斜杠）；事实 3 的误报判定只针对 `yaml.SafeLoader` 子类，若未来出现真实
`yaml.load(Loader=FullLoader/Loader)` 则不适用。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260912-040-frontend-backend-seams-and-surfacing.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260912-040-frontend-backend-seams-and-surfacing.md`
- 扫描处置：`docs/audits/PA1_MIMOSA_REVIEW.md`（2026-09-12 节）
- 相关 commit：`6d844e3`（WP-A）、`2022b02`（WP-B）、`d5abf18`（WP-C）、
  `af5df14`（WP-D）、`b86c693`（扫描处置）
