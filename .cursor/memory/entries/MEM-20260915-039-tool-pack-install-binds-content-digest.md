---
id: MEM-20260915-039
title: ToolPack 写面：pin 由控制面重算自证；权限扩张不生效直到 approve-update
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.92
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-064-tool-pack-supply-chain-write-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-064-tool-pack-supply-chain-write-surface.md
supersedes: []
tags:
  - supply-chain
  - tool-pack
  - approval-semantics
  - capability-vocabulary
  - write-surface-consumption
---

# ToolPack install/approve：pin 自洽 + 扩张待批准

## 做了什么

ADR-0019 的 `ToolPackLifecycle` 只被测试调用（无 store、无路由、无装配），
`docs/api/CONTROL_PLANE_API.md` 把三条端点记为"(未提供)"。本轮把它接成真实写面：

```text
GET    /tool-packs                            生效版本 + 待批准版本分开呈现
POST   /tool-packs/install                    201 安装 / 200 无扩张更新 / `unchanged` 内容相同 / 409 重复·终态·内置 id / 422 内容或 capability 非法 / 503 未装配
POST   /tool-packs/{id}/approve-update        200 扩张此刻生效 / 403 policy / 404 未知 / 409 无待批准
POST   /tool-packs/{id}/revoke                200 终态（reason 必填）/ 404 / 409 已吊销
```

## 为什么这样做

1. **pin 是控制面自己算出来的，不是采信调用方写的字面量**：请求体同时带内容与
   `digest`，服务端用 `toolpack_content_digest()` 重算并要求相等 ⇒ 内容与 pin 不符
   即 422。这关掉了 RECHECK-060 W-3 的 pack 侧（"pin 只校验形态"）。
2. **权限扩张不生效直到批准**：同 id 提交的 manifest 若新增 capability / network
   domain / credential（`permission_diff` 非空），只登记为 **pending**——生效版本仍是
   旧 manifest、目录里的 digest 不变；`approve-update` 过 policy（`tool_pack.update.expanded`）
   后才替换。**"已提交"≠"已生效"**，与 provider 注册的 PENDING→ACTIVE 同一哲学。
3. **capability 取值域**（W-2 的书写面修法）：`requested_capabilities` 与各 tool 声明的
   capabilities 必须都在 `examples/config/capabilities.yaml`（与离线 bundle validator 同源），
   否则 422 并点名；词表读不到 → 503（不降级成放行）。
4. **内置 pack id 不影子覆盖**：`examples/contracts/toolpack_*.yaml` 的 id 一律 409。
5. **写面被读面消费**：state=INSTALLED 的 pack 把 digest 合入 `tool_pack_digests`
   （键 = pack id 去掉 `_vN` 后缀，与 examples 契约同口径）——这是 preflight/compile
   读的同一张表，所以 install / pending / revoke 三态在读面上各不相同。

## 怎么做与复现

```python
# 控制面重算 + 状态机（packages/application/tool_plane/lifecycle.py）
_verify_supply_chain(manifest)   # manifest.digest == toolpack_content_digest(manifest)?
existing = store.get(manifest.id)
if existing is None:                     → install（policy tool_pack.install）
elif existing.manifest.digest == manifest.digest → "unchanged"（不写任何东西）
elif permission_diff(...) 非空           → 待批准（pending_manifest 与生效版本同一行写入）
else                                    → 直接替换生效
```

```bash
python -m pytest tests/api/test_tool_packs_api.py -q          # 9 passed（含三态消费证明）
python -m pytest tests/application/test_tool_plane_execution.py -q   # 生命周期 12 条
python -m pytest tests/contracts/test_openapi_snapshot.py -q  # 写方法 + 422/409 语义锁定
```

## 适用边界（踩过的坑）

- **`InvalidInputError` 是 `PermanentPortError` 的子类**：异常→HTTP 映射必须先判子类，
  否则"未知 pack"会被当成"内容不符"返回 422（首版就是这个 bug，被"未知 pack 404"用例抓住）。
- **控制面不取远端交付物**：重算 digest 只证明"提交内容与声明的 pin 自洽"，不证明
  "pin 与上游仓库实际内容一致"——后者需要远端取证，控制面不做，也不应宣称。
- **preflight finding 级翻转在当前示例数据下不可达**：`SUPPLY_CHAIN_UNPINNED` 只对
  非 NATIVE 且未被 pin 的 provider 触发，而 examples 已为唯一的非 NATIVE provider
  （`ncbi_eutils`）提供了基线 pin；消费证明因此落在 `merged_catalog_snapshot`
  （preflight/compile 的同一读面）上，而不是某一个 finding 的翻转。
- **`manifest_document` 的内容口径**：文档里多出的只有 digest/signature（不参与内容
  digest），因此"文档→实体→重算"往返不漂移；skill 的 `status`/`digest` 不在内容字典里，
  往返时按缺省 ACTIVE/None 处理（既有口径，本轮未改）。

## 来源

- PLAN-20260915-064 / RECHECK-20260915-064（GOAL-20260915-003 cycle 2 / EC-02）。
- 结转告警：RECHECK-060 W-2（capability 取值域）、W-3（pin 与交付物绑定）。
- 相关：[[MEM-20260915-036]]（注册状态推导信任——同一治理族的 provider 侧）、
  [[MEM-20260915-035]]（写面必须被读面消费）。
