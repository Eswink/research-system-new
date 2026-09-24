---
id: MEM-20260924-129
title: "按压脚本要自带「保险闸」：被撤的量若还在，脚本必须拒跑，而不是跑出正向链路"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.9
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-160-acceptance-gate-input-face-wiring.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-162-acceptance-gate-input-face.md
supersedes: []
---

## 做了什么

同一份「按压」脚本（撤掉 `examples/config/policy.yaml` 的一条 allow ⇒ 真实控制面判 `DENY`
⇒ run 冻结前终止）有两种被误用的方式：忘了撤、或撤错能力。两种都会让脚本**跑起正向链路**
——而在本仓这正是**真实 LLM + 真实检索**（有成本、有出网）。

本 cycle 的做法是给脚本加**开跑前的保险闸**：先读产品策略面，若被撤的能力**仍在** `allow`
里，直接打印 `REFUSED` 并 `exit 2`，**不构造装配、不起 run**。

```python
allowed = _allowed_capabilities()          # adapters.contracts.load_policy(...)
if WITHDRAWN in allowed:
    print(f"REFUSED: {WITHDRAWN} 仍在 allow 里 ⇒ 按压未生效，本脚本拒绝起 run")
    return 2
```

另外两处同源纪律：① 按压用**默认（Fake）会话 runtime**（被按的是策略面，与 runtime 无关），
这样即使按压失灵也不会产生真实模型调用；② 装配仍走**产品组合根 + 只注入执行体**
的支持模块（`tests/e2e/live_control_plane_support.product_control_plane_deps`），
保证按压与正向是**同一台机器上的成对**，而不是另一套夹具。

## 为什么这样做

按压的价值全在「成对」：如果按压脚本在未生效时也能跑完，产出的 `FAILED` 就**证明不了**
任何事（它可能只是别的失败），而代价是真实调用。把「不可能跑正向」写进脚本本身，
比写在操作者的记忆里可靠。

## 怎么做与复现

- 任何**会改变状态再起真实链路**的按压脚本：先加「前置条件不满足就拒跑」的断言式护栏，
  并把拒跑的退出码与判词分开（本处 `exit 2` + 一行 `REFUSED`）。
- 按压结束按 `MEM-20260924-127` 的口径还原：**逐字节**核对（`sha256sum` 或
  `cmp` + CR 字节计数），不要只看 `git diff --stat` 为空。
- 复现：`scratch/goal014-c6-press-allow-withdrawn.py`（护栏在 `main()` 开头）；
  输出 `scratch/goal014-c6-press-allow-withdrawn.txt`
  （`state=FAILED` / `manifest_digest: null` / `preflight failed: POLICY_DENIED, TOOL_RISK_ELEVATED`
  / `tool_observed: []` / 零 task / 零实验 / 零证据）。

## 适用边界

- 只对**本机真跑**的按压脚本成立；默认门（CI）里的按压是 pytest 内注入坏值，没有真实调用风险，
  不需要这道闸（但「还原逐字节」的要求同样适用）。
- 护栏只保证「不可能跑正向」，**不**保证按压一定红：红要靠输出的形态判据（终态 + 零面 +
  点名原因）来读。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-160-acceptance-gate-input-face-wiring.md`（WP6/WP7 证据段）
- `.cursor/plans/rechecks/RECHECK-20260924-162-acceptance-gate-input-face.md`（第三节）
- `scratch/goal014-c6-press-allow-withdrawn.py` / `.txt`、`scratch/goal014-c6-policy-before.sha256`
