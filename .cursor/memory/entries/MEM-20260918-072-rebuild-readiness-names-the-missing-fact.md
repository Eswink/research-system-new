---
id: MEM-20260918-072
title: "历史行的'缺什么'要做成读面事实（一个分类器同时喂读面与拒绝文案），不要指望调用方从 None 里猜"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-098-rebuild-readiness-read-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-098-rebuild-readiness-read-surface.md
supersedes: []
tags:
  - read-surface
  - migration
  - ports
  - honesty
---

# 历史行：把"缺哪条事实"做成读面，而不是留给拒绝文案

## 做了什么

GOAL-005 cycle 6（EC-06 (b)）把"旧 run 没有冻结正文 / 旧 `manifest.frozen` 事件没有
`semantic_digest`"两类历史行做成一等读面：新增纯函数分类器
`packages/application/run_orchestration/rebuild_readiness.py`（读 `manifest_digest` /
`manifest_semantic_digest` / `protocol_body` / `protocol_source` 四个字段），读出
`status`（`SELF_CONTAINED` / `SOURCE_DEPENDENT` / `REFUSED`）+ 按**行字段名**点名的
`missing`；`RunDetailDto.rebuild` 暴露它，`/resume` 的两条早退与异常前缀也改从它取。

## 为什么这样做

- **一个 `None` 回答不了三个问题**：`manifest_semantic_digest=None` 既可能是"功能前的
  历史行"，也可能是"起步时冻结失败"，还可能是"还没冻结"；调用方从 None 里猜不出来，
  于是只能靠人读日志。做法是**把事实判出来**（不是把 None 变多）。
- **同源比"两处写得一样"可靠**：拒绝文案此前分散在 `run_resume`（两条早退 + `body is None`
  前缀）与 `convergence`（守卫）。把"缺什么"收敛成一个分类器的输出后，读面与控制面
  在同一个行上永远说同一条事实（`early_refusal()` / `dependency_prefix()` 都是它的方法）。
- **不要顺手发明裁决**：读面 `REFUSED` 只说"重建会被拒"，**不说**"不可回填"——回填是
  运营动作（`tools/snapshot_migrate.py` 是显式 opt-in，re-freeze 要重编译协议）。
- **分类器要显式带出它判过的每个事实**：`body_frozen` 单独成字段，是因为"异常前缀"
  问的正是这一件事。若把它塞进 `status`（"SOURCE_DEPENDENT 才没正文"），
  "既缺正文又缺语义 digest"的行就会丢前缀——既有用例当场变红。

## 怎么做与复现

```bash
# 分类器矩阵 + 值对象不变量
uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_rebuild_readiness.py -q
# 读面三态 / 与拒因同源 / 旧事件形态（DSN pin 配方）
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/api/test_run_source_and_rebuild_api.py \
  tests/api/test_failed_run_semantic_digest_api.py -q
# 反证：把 `if run.manifest_semantic_digest is None` 那条判定去掉 ⇒ 6 条红
```

## 适用边界（踩过的坑）

- **分类器只读 canonical 行**：不读文件、不解析来源 ⇒ 读面没有 IO，也不会因为"看一眼磁盘"
  改变结论。
- **旧事件回填分支要专门造用例**：既有 restart 用例的 run 行自带语义 digest，永远走不到
  `from_payload` 的"缺键 ⇒ None"分支；覆盖它必须直接喂旧形态 payload。
- **新增必填 DTO 字段会牵动三处**：OpenAPI 快照（`tools/gen_openapi.py`）、web
  `types.ts`、e2e 夹具（`apiFixtures.ts` 的类型字面量）——漏掉夹具会让 typecheck 红。
- 相关：[[MEM-20260917-064]]（读面来源与既有诚实边界）、
  [[MEM-20260918-071]]（同一批读面纪律：判据只有一处）、
  [[MEM-20260918-069]]（声明未消费项的处置：移除或给真实消费者）。

## 来源

- PLAN-20260918-098 / RECHECK-20260918-098（GOAL-20260918-005 cycle 6 = EC-06）。
- 上游：RECHECK-20260917-084 W-2 / RECHECK-20260917-087 W-1（历史行缺口）。
