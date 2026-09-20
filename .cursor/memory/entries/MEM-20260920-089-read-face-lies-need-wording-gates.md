---
id: MEM-20260920-089
title: "读面谎言抓不到功能测试：文档/UI 对机制的不实声明要用措辞判据钉，且「文件里有这些字」与「这些字被渲染」是两条判据"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-116-supply-chain-registration-and-credential-discipline.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-116-supply-chain-registration-and-credential-discipline.md
supersedes: []
tags:
  - credential-boundary
  - docs-honesty
  - wording-gate
  - playwright
  - credential-audit
---

# 机制没做错、读面在说谎——这类缺陷只能由措辞判据抓（GOAL-20260920-008 / cycle 3）

## 做了什么

`docs/integration/LLM_ENDPOINTS.md` §9 长期写「API Key 加密/Secret Store」。实现是
`RegistryCredentialResolver`：`register()` 只写**进程内** dict，`resolve()` 未命中时才按
`credential_ref` 同名**环境变量**回退——既没有加密层，也没有 Secret Manager。**所有功能用例
都是绿的**（配置/读取/探测都对），因为错的不是行为，是**对行为的描述**。

处置三件事：

1. 文档 §9 改成三层事实表（Domain 只存 `credential_ref` / 进程内注册表 / 环境变量回退）
   + 三条边界（值存在哪里、重启需重新注入、不是 Secret Manager）；
2. 控制台端点详情抽屉加 `endpoint-credential-boundary` 声明（中英双语）；
3. 新增 `tests/architecture/python/test_credential_boundary_wording.py`：三面（文档 / UI /
   解析器 docstring）**必须同时出现**同一事实，另有一半是**禁止**——`Secret Store`、
   `凭据已保存` 这类持久化承诺在三面都不得出现。

## 为什么这样做（可复用结论）

1. **功能测试的射程止于行为**：判据写「调用能成功 / 返回正确的 DTO」时，一句不实的散文
   不会被任何用例发现。凡是「读面声称某机制存在」的地方，都需要一条**措辞判据**
   （判据读的是文案文本，不是行为），否则文档与实现的漂移只能靠人眼巡。
2. **「文件里有这些字」≠「用户能看到」**：实测反证（F8）——把 UI 里的挂载点删掉、只留函数体，
   措辞判据**仍然全绿**（文本还在文件里），只有渲染级 e2e 变红。两条判据钉的是两件事，
   都要有；少了 e2e，「注释掉挂载」这类改动就无人报警。
3. **禁止半与要求半同等重要**：只钉「必须说什么」不够，还得钉「不许说什么」——
   历史谎言（`Secret Store`）留在文档里就是复发点，所以 FORBIDDEN 列表与 REQUIRED 列表一起进判据。
4. **措辞判据变红是预期行为**：改文案就要同时改判据。这与「禁止为了变绿改断言」不冲突——
   该禁令针对**功能断言**；措辞判据的作用恰恰是把文案变更变成显式动作。
5. **凭据审计的「该扫而扫不成 ≠ 没命中」**：`tools/credential_audit.py` 在根目录不是 git
   工作树时把跟踪面记 `not_a_git_tree` 并**判红**（不是静默 0 命中），并提供 `--root`
   审计另一份 checkout——反证（往跟踪文件注入陌生键）因此可以在真树上做，也可以指向干净 clone。
6. **白名单按值不按路径**：审计放行的是**已逐个看过的杜撰串**（`sk-test` 等 14 条，逐条给理由），
   不是整个文件；代价是白名单由人维护（首次实跑 43 处命中里 42 处是
   `api_key = self._api_key()` 这类表达式噪声，收紧成「只认带引号的字面量」后才成门）。

## 怎么做与复现

```sh
# 措辞判据（三面同源 + 禁止不实声明）
uv run --frozen --no-sync pytest -q tests/architecture/python/test_credential_boundary_wording.py

# 渲染级判据（抽屉里的文案；设计门看不见这条分支）
pnpm --dir apps/web exec playwright test endpoint-credential-boundary --reporter=line

# 明文凭据审计（四面；命中即非零退出；--root 可审计另一份 checkout）
uv run --frozen --no-sync python -B tools/credential_audit.py

# 反证：删一句措辞 / 塞一句假声明 / 摘掉 UI 挂载点，三处都必须变红后逐字节还原
uv run --frozen --no-sync python -B scratch/ec03-wording-gate-falsification.py
uv run --frozen --no-sync python -B scratch/ec03-credential-audit-falsification.py
```

## 适用边界

- 适用于**读面声称机制存在**的场景（凭据、持久化、加密、审计、外部托管）；不适用于
  纯行为断言——措辞判据不能替代功能用例，两者互不覆盖。
- 措辞判据是**子串**匹配，不解析 AST：它钉的是「这句话在不在」，不是「这句话是不是真的」。
  写进判据的必须是**能长期成立的事实**（机制换实现时要一起改）。
- 凭据审计的四面是「跟踪文件 / `.cursor/plans` 记录 / 配置面 DB / 本机日志」；`.env`
  **有意不在其中**（它本就是凭据的合法落点），需靠「`.env` 必须保持 untracked」这条独立纪律兜住。
- 值级白名单是人维护的：新增真实凭据若恰好**包含**已放行子串会被静默放行（当前 14 条都指向
  测试替身/占位串，风险低但非零）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-116-supply-chain-registration-and-credential-discipline.md`（WP-C / WP-E）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-116-supply-chain-registration-and-credential-discipline.md`（F4–F8）
- 代码：`docs/integration/LLM_ENDPOINTS.md` §3/§9、`apps/web/src/features/endpoints/EndpointsHome.tsx`
  （`CredentialBoundaryNotice`）、`adapters/relay/registry_credential_resolver.py`、
  `tools/credential_audit.py`、`tests/tooling/test_credential_audit.py`
- 相关：[[MEM-20260920-088]]（新渲染分支可能落在设计门盲区——本条的 F8 是同一现象的另一面）
