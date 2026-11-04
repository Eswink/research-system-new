---
id: MEM-20261104-240
title: "不同客户端有互不相交的配置面：规则、技能与 hook 都不跨客户端生效"
status: ACTIVE
created_at: 2026-11-04
updated_at: 2026-11-04
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261104-106-zcode-skill-distillation-and-explicit-invocation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261104-106-zcode-skill-distillation-and-explicit-invocation.md
supersedes: []
tags: [agent-config, zcode, cursor, hooks, skills, discoverability]
---

# 不同客户端有互不相交的配置面

## 做了什么

把「引用绑定 + 只读读数」「多层配置的缺省抹平」「判据落地纪律」蒸馏成三个技能，落在
`.agents/skills/`；并用根 `zcode.json` + `tools/zcode-hooks/` 让 ZCode 侧
「调技能」成为机器门禁，`Read` / `Bash` 直接读技能正文会被 deny。

## 为什么这样做

**本仓的工程配置面是按客户端分裂的，而分裂本身没有任何判据能看见。**

- `.cursor/rules/` 的 14 条规则、`.cursor/skills/` 的 17 个技能、`.cursor/hooks.json` 的
  15 个门禁，**只对 Cursor 生效**。ZCode 扫描的技能根是 `~/.zcode/skills`、
  `~/.agents/skills`、`<repo>/.zcode/skills`、`<repo>/.agents/skills` 与插件根 ——
  `.cursor/skills/` 不在其中。证据是自明的：本轮 ZCode 会话的技能清单里，
  仓内 17 个一个都没出现。
- 反过来，ZCode 的 hook 协议（七个事件、`hooks.events.<Event>`、`hookSpecificOutput`
  输出）与 Cursor 的 `hooks.json`（`failClosed`、`loop_limit`、`permission` 载荷）
  是两套 schema。**换客户端不报错，只是全部静默不执行。**
- `.gitignore` 忽略整个 `.zcode/` ⇒ 写在那里的配置既不可共享也不可审计，所以仓库级
  配置只能落 `zcode.json` 与可跟踪的 `.agents/`。

这解释了为什么「规则写了但模型没遵守」有时不是模型的问题：那条规则可能压根没进上下文。
也解释了为什么「装了 hook 但没拦住」：那个 hook 可能属于另一个客户端。

## 怎么做与复现

1. 判断一条工程约束**在哪一侧**生效，先查它能被谁发现：
   - Cursor：`.cursor/rules`（`alwaysApply` / `globs`）、`.cursor/skills`、`.cursor/hooks.json`。
   - ZCode：`AGENTS.md`、`.agents/skills` / `.zcode/skills`、`zcode.json` 的 `hooks.events`。
2. 需要**两侧都生效**的约束，要么两侧各落一份（并接受漂移风险），要么把
   **可机械验证的部分**下沉到仓库门禁（测试/validator），让客户端无关。
3. 新增 ZCode 侧配置时按三步取证：①技能根真的被扫描（用会话可见的技能清单自证）；
   ②`hooks.enabled: true`（配置面 hook 缺省不跑）；③手喂 stdin 载荷跑一次真进程。
4. 判据面：`test_zcode_hook_registration.py`（注册面）、
   `test_zcode_skill_invocation_guard.py`（裁决面 + 真进程）、
   `test_agent_skill_frontmatter.py`（frontmatter 面）。

## 适用边界

- 适用于：多客户端（Cursor / ZCode / Codex）共用同一仓库时的配置落点判断与「为什么不生效」归因。
- 不适用于：单客户端仓库——那里没有歧义。
- 本条**不**断言「两份配置必须同步」。本轮刻意只落 ZCode 侧一份，`.cursor/skills/` 原样保留。
- 若将来 ZCode 支持扫描 `.cursor/skills/`，本条的核心结论（面不互通）失效，
  但归因方法（用会话可见清单自证）仍成立。

## 失效与复核触发器

- ZCode 或 Cursor 变更技能发现根、hook 事件名或输出 schema（本机 ZCode 3.12.x 实测）。
- 仓库开始双写（`.cursor/skills/` 与 `.agents/skills/` 各一份）——那时要重新评估漂移风险。
- 到达 `review_after`。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261104-106-zcode-skill-distillation-and-explicit-invocation.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261104-106-zcode-skill-distillation-and-explicit-invocation.md`（§5 反证臂汇总）
- 仓库：`zcode.json`、`tools/zcode-hooks/skill_invocation_guard.py`、
  `.cursor/hooks.json`（15 个 Cursor-only 门禁）
- 判据：`tests/tooling/test_zcode_hook_registration.py`（6）、
  `tests/tooling/test_zcode_skill_invocation_guard.py`（11）、
  `tests/tooling/test_agent_skill_frontmatter.py`（7）

## 相关

- `[[a-field-default-is-not-a-declaration]]`/`MEM-20261103-239`：同一批沉淀的另一条
  形态（缺省值抹平「未声明」）。
- `[[declared-but-never-constructed-is-a-dead-seam]]`：同族 —— 声明存在而接线不在。
