---
id: RECHECK-20261104-106
slug: zcode-skill-distillation-and-explicit-invocation
title: PLAN-106 复检 —— ZCode 技能蒸馏 + 显式调用门禁
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-04
updated_at: 2026-11-04
plan_id: PLAN-20261104-106
parent_goal: null
owners:
  - root-agent
verify_paths:
  - .agents/skills/citation-binding/SKILL.md
  - .agents/skills/layered-default-resolution/SKILL.md
  - .agents/skills/criterion-authoring/SKILL.md
  - zcode.json
  - tools/zcode-hooks/skill_invocation_guard.py
  - tools/zcode-hooks/skill_index_context.py
  - tests/tooling/test_zcode_hook_registration.py
  - tests/tooling/test_zcode_skill_invocation_guard.py
  - tests/tooling/test_agent_skill_frontmatter.py
  - tests/tooling/test_tooling_scripts_meet_product_gates.py
---

# RECHECK-20261104-106

## 检查结果

`PASS_WITH_WARNINGS`。六个 AC 各有独立证据；两向按压确认判据真的会红。六条残余
（`W-1`…`W-6`）全部是**本轮刻意不做**的射程外事项，不是未完成的验收项。

## 1. 范围

只新增文件与一处清单登记，未改任何产品代码：

- 新增：`.agents/skills/{citation-binding,layered-default-resolution,criterion-authoring}/SKILL.md`、
  `tools/zcode-hooks/*.py`（2 个）、`zcode.json`、三条判据。
- 修改：`tests/tooling/test_tooling_scripts_meet_product_gates.py`（`IN_SCOPE` 加 2 条，
  同轮压缩 2 行注释以守 450 行上限；**未删任何登记条目**）、`.cursor/plans/ALL_PLAN.md`（加一行）。
- 修复（本轮实测阻断）：`.cursor/skills/system-spec-check/scripts/validate_bundle.py` 的
  版本扫描输入面 —— 见 §10。
- 未触碰：`packages/`、`services/`、`adapters/`、`schemas/`、`docs/api/`、`.cursor/hooks/`、
  `.cursor/skills/`（除上述 validator）、`AGENTS.md`。

## 2. 架构

- **配置面与事实面的分工**：`zcode.json` 只做注册（谁在什么事件上跑什么），
  裁决逻辑在 `tools/zcode-hooks/`，`canonical` 事实仍是仓库文件。hook 不写 Domain。
- **射程边界显式**：`GUARDED_SKILL_ROOT` 是一个具名常量，判据里同时钉住
  「`.agents/skills/` 必拦」与「`.cursor/skills/` 必不拦」两条臂。
- **单一技能根**：`skill_index_context.SKILLS_ROOT` 与 `skill_invocation_guard.GUARDED_SKILL_ROOT`
  指向同一个面（`.agents/skills`）。两者若漂移，索引会列出不可拦的技能 —— 该风险
  由两条判据合并覆盖（索引列出 3 个 + 门禁拦同一个名字）。

## 3. 验收逐条

| AC | 证据 | 判定 |
| --- | --- | --- |
| AC-01 技能可发现且 frontmatter 合规 | `test_agent_skill_frontmatter.py` 7 passed | PASS |
| AC-02 Read/Bash 双面 deny 且理由点名 | `test_zcode_skill_invocation_guard.py` 11 passed（含真进程臂与 BOM） | PASS |
| AC-03 射程边界显式 | 同上两条 allow 臂 | PASS |
| AC-04 注册面有判据 | `test_zcode_hook_registration.py` 6 passed | PASS |
| AC-05 两 hook 过 `tools/` 四道门 | `test_tooling_scripts_meet_product_gates.py` 30 passed | PASS |
| AC-06 按压证明 | 见下 §5 | PASS |
| AC-07 版本扫描输入面 | `test_validate_bundle_version_input_face.py` 4 passed；`validate_bundle` 由失败转「验证通过」 | PASS |
| AC-08 技能可被自动选择 | `test_agent_skill_frontmatter.py` 9 passed（发现面 + 路由面）；两向按压各恰 1 红 | PASS |

## 4. 质量门

```text
ruff check             : All checks passed!
ruff format --check    : 6 files already formatted
mypy (strict, 5 files) : Success: no issues found in 5 source files
pytest 定向（4 文件）  : 30 passed
```

## 5. 反证臂汇总

| 按压动作 | 预期 | 实测 | 判定 |
| --- | --- | --- | --- |
| 删 `zcode.json` 的 `hooks.enabled` | 注册面恰好 1 红 | 1 failed / 5 passed（`test_the_hook_runner_is_switched_on`） | 成立 |
| `GUARDED_SKILL_ROOT` 改成 `.cursor/skills` | 正向 3 + 边界 1 + 真进程 1 = 5 红 | 5 failed / 4 passed | 成立 |
| 复原后重跑 | 全绿 + `sha256` 与备份一致 | 16 passed；`e813fb0a…f68f75` 两侧相同 | 成立 |

**多红少红都算打偏**：第二次按压里 `test_reading_ordinary_sources_is_allowed` 等 4 条
allow 臂保持绿是**预期**——它们断言的是「不该拦」，换根不会让它们变红。

## 6. 安全

- 新增的是一条**限制性**门禁，不放宽任何既有 deny。
- 无新增 secret；`zcode.json` 不含任何凭据字段。
- 仓库级 `mimosa@zcode-plugins-official: false` 保持，且有判据
  `test_mimosa_stays_disabled_in_the_tracked_config` 钉住。
- **未做的安全项**（`W-1`）：`.cursor/hooks/` 的 15 个门禁在 ZCode 下不执行。这是本轮
  最大的已知缺口，必须进下一轮。

## 7. 兼容性

- 零 Domain/API/schema 改动；OpenAPI 快照零 diff；零 migration。
- `zcode.json` 与 `.zcode/config.json` 是**合并**读取（bundle `gpo()` 产出两个候选路径），
  不是二选一 ⇒ 既有 `.zcode/config.json` 的插件开关不失效。
- 解释器固定为 `python`（`process` 型，不经 shell）。若目标机器 PATH 上没有 `python`，
  hook 会失败——按 ZCode 语义这属于 hook 执行失败而非放行；手喂载荷是探测手段。

## 8. 计划完整性

- `.cursor/plans/tasks/PLAN-20261104-106-*.md`：七个章节齐备（含 `## 实施清单` /
  `## 证据` / `## 状态历史`）。
- `.cursor/plans/ALL_PLAN.md`：新增一行，未重排既有条目。
- `MEM-20261104-240`：记录「不同客户端有互不相交的配置面」这一非显然结论。

## 9. 残余与风险

见 `PLAN-20261104-106` 的「残余」段（`W-1`…`W-6`）。其中 `W-6` 需要用户拍板：
`zcode-unconstrained` 插件每轮注入与 `AGENTS.md` §9/§10 相反的 override 文本，
可逆处置是在 `zcode.json` 加一行 `false`。

## 结论

`PASS_WITH_WARNINGS`：显式调用面成立且能两向按压；安全门禁移植与技能迁移是
**射程外**的下一轮事项，已在计划与本节如实登记，未以「已完成」口径描述。

## 10. 本轮实测阻断（`AC-07`）

**现象**：`validate_bundle.py` 报
`发现旧项目版本引用: .zcode\plans\plan-sess_6e3a2b19-....md`，但该文件**不在 git 里**
（`.gitignore:49` 忽略整个 `.zcode/`），且 mtime 是**本次会话**的 19:27 —— 它是 ZCode
把本次会话的计划快照写下来的产物，内容里引用了计划正文中的历史版本字面量。

**归因**：`check_versions()` 的版本扫描走裸 `os.walk`（只看 `NON_SOURCE_DIRS`），
而同一文件的 `validate_local_markdown_links()` 早已改成按 `git_decided_inputs()`
（已跟踪 ∪ 未跟踪未忽略）筛选。**同一个缺陷只修了一半。**

**处置**（不加目录名例外、不删内容）：

- 版本扫描与版本命名扫描都改为先按 `git_decided_inputs()` 筛选；
- git 面不可用 ⇒ 与链接检查同款**硬失败 + 点名** `not_a_git_tree`；
- 被判内容（正则、后缀集、既有三条例外）一字未动；
- 新增 `tests/tooling/test_validate_bundle_version_input_face.py`：四条身份臂
  （忽略不判红 / 已跟踪照红 / force-add 照红 / 未跟踪未忽略照红）+ 非 git 根硬失败
  + 源码锚点（防止回退成裸 walk）。

**按压**：删掉版本循环里的 `relative not in version_inputs` ⇒ **恰好 1 红**；
复原后 `sha256` 两侧同为 `1037af89…30f92`，两条输入面判据合计 7 passed。

**为什么这不是「为过门而改判据」**：判据变的是**输入面**而不是**判定内容**，而且方向是
对齐到既有先例（GOAL-017 `D-10`）的严格版本 —— 已跟踪文件一个都没被豁免，force-add
进被忽略目录的文件也仍然照扫。

## 11. AC-08：上一轮的方向错误（本轮反转）

**用户要求**：ZCode 要能**自己的选择**使用技能。

**上一轮的实际做法是反的**：三个技能都写了 `disable-model-invocation: true`，判据还
断言这个值「必须为 true」。那是 **Cursor** 的语义（禁止模型自动调用）。

**取证**：

- `disable-model-invocation` 在 ZCode bundle 里**零命中** ⇒ 该字段对 ZCode 无效；
- ZCode 的模型侧提示词写的是「Available skills appear in a system-reminder listing with
  one-line descriptions. When the task at hand is one a listed skill covers, call this
  tool first」⇒ 自动选择的前提是「被发现 + 描述可路由」；
- 发现根由 `skillRootsForBase` 给出：`<base>/.zcode/skills` 与 `<base>/.agents/skills`，
  base 从 cwd 上溯到 git 根 ⇒ `.agents/skills` 落点正确。

**修正**：

1. 三个技能删掉 `disable-model-invocation`；
2. `description` 改成 `Use when …` 的**触发式**（含适用条件、覆盖范围、不适用边界）——
   这是模型路由的唯一依据；
3. 判据反转为 `test_skills_are_available_for_model_invocation`（不得为 true），
   并新增 `test_the_skills_root_is_one_zcode_scans`（发现面）与
   `test_description_carries_a_routing_trigger`（路由面，含「不得含显式限定语」）；
4. hook 的拒绝措辞从「读取被拒绝」改为「下一步调 Skill(skill=…)」——门禁的目的从
   「禁止读」变成「导向可取证的加载路径」。

**按压**：描述改成名词短语 ⇒ 恰 1 红；加回 `disable-model-invocation: true` ⇒ 恰 1 红；
复原后 8 passed，`sha256` 两侧同为 `4d57cc1b…b127672`。

**未证明的部分**（`W-9`）：判据证明「被发现且可路由」，不证明「某次具体任务真的会调」。
后者是模型行为，静态判据无法承担；复验方式是观察新会话的 system-reminder 技能清单与
真实任务的 Skill 调用。

**2026-11-05 闭合（真实会话实测）**：信任批准后，本会话完整链路成立 ——
`Read .agents/skills/citation-binding/SKILL.md` 被 PreToolUse 拦下并给出
`Skill(skill='citation-binding')`；`Skill(citation-binding)` 成功载入正文（回传含
`Base directory: D:\research-system\.agents\skills\citation-binding`）；SessionStart
注入列出三个技能。**「模型在具体任务上主动选择」仍属模型行为**，判据只保证
「可发现 + 可路由 + 未禁用」。

**新增残余 `W-10`（信任关卡）**：项目级 hook 需工作区信任，日志出现 15 次
`config.project_hooks.pending_trust` 且零执行记录。信任按**配置内容摘要**持久化
（存在 `stale_digest` 状态）⇒ 每次改 `zcode.json` 或 hook 脚本都要重新审批。该状态不在
任何可安全编辑的配置文件里，本轮未伪造。
