---
id: MEM-20260915-040
title: 待批准必须在界面上与已生效分开；写面能力要跟平台策略词表对齐
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-065-tool-pack-console-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-065-tool-pack-console-surface.md
supersedes: []
tags:
  - console
  - pending-vs-effective
  - policy-vocabulary
  - live-e2e-fixtures
  - design-baseline
---

# pending 呈现：候选走横幅、生效列不变；能力名要与 policy 词表对齐

## 做了什么

把 ToolPack 供应链写面做成 console 可操作的投影（GOAL-003 cycle 3 / EC-02）：

```text
ops/integrations
  ├─ 表：id / 状态(+待批准 chip) / **生效 digest** / 版本 / capabilities / 目录 / 吊销
  ├─ 安装表单：完整 manifest JSON → POST /tool-packs/install（422 detail 行内显示）
  └─ 待批准横幅：候选 digest + diff 明细（新增 capability/domain/credential）+ 批准按钮
```

## 为什么这样做

1. **"待批准"必须在界面上与"已生效"分开**：候选 digest 只出现在横幅里，表里的 digest
   列**始终是生效版本**；行上只加一个 `待批准` chip。若把 pending digest 显示进 digest 列，
   这个 UI 就在撒谎——用户会把"已提交"读成"已升级"。
2. **拒绝原因落在动作附近**：422（digest mismatch / 未知 capability）与 409（内置 id /
   终态 / 无待批准）都渲染在面板内（`useAsyncAction` 的 error ← `ApiError.message`
   = problem.detail），不弹全局 toast、不吞掉。
3. **夹具只放行"方法"、不伪装"内容"**：stub 的 digest 校验用 canonical JSON→sha256 的
   镜像实现（自洽即可）；live 用的 manifest 由**域代码生成**，并由
   `tests/tooling/test_console_toolpack_fixtures.py` 守住"仓库 JSON == 域现算 + capability
   ∈ 平台词表"——drift 在这里红，而不是在 live 用例里以 422 的形式红。

## 怎么做与复现

```bash
# stub（有状态替身 + reset）
pnpm --dir apps/web exec playwright test tool-pack-write        # 6 passed
# live（真实 uvicorn + 真实 SQLite；fixture 由域代码生成）
pnpm --dir apps/web exec playwright test --config playwrightLive.config.ts tool-pack-write  # 2 passed
# fixture 同步守卫
uv run --frozen --no-sync python -m pytest tests/tooling/test_console_toolpack_fixtures.py -q  # 2 passed
```

## 适用边界（踩过的坑）

- **默认策略可能根本没放行你的写面**：lifecycle 按 `tool_pack.install/update/revoke`
  求值，而 `examples/config/policy.yaml` 里只有 `action: TOOL_PACK_INSTALL_OR_UPDATE`
  ⇒ `default_effect: DENY`。live e2e 第一次跑就 403 并把 detail 显示在面板上（**这本身
  是界面正确工作的证据**）。新增写面时必须检查"我求值的能力名在平台策略词表里吗"，
  否则真实部署里按钮只会 403。本轮不改产品策略，只在夹具层放行并登记（RECHECK-065 W-1）。
- **页面新增面板 = 结构判据必红、像素判据可能不报**：本次 `ops-integrations` 结构签名
  +18 节点判红，而 33 条像素用例同一次运行全绿（2% 阈值）——重生成基线时**两个平台都要**
  重生成（本机 win32 + pinned noble 容器 linux），并目检。
- **live fixture 的 digest 不能手写**：控制面重算内容 digest，手写的 digest 只会在 422
  上打转；用域代码生成 + 同步守卫（本仓既有 `design-outlines.json` 同一模式）。
- **`catalog_digest_active` 是状态投影**（`state is INSTALLED`），不是"目录合并确实执行过"
  的独立证据；UI 列名不要写成"已生效于 preflight"。

## 来源

- PLAN-20260915-065 / RECHECK-20260915-065（GOAL-20260915-003 cycle 3 / EC-02）。
- 相关：[[MEM-20260915-039]]（ToolPack 写面的 pin 自证与扩张待批准，本记忆是它的 UI 侧）、
  [[MEM-20260915-038]]（结构签名与像素判据互补——本轮拿到第一次真实拦截）。
