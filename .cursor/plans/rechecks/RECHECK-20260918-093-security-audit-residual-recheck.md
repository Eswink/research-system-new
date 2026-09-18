---
id: RECHECK-20260918-093
plan_id: PLAN-20260918-093
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle1
baseline_ref: 6007b01
checked_head: worktree
---

# RECHECK-20260918-093 — 安全审计残留复核（GOAL-005 cycle 1 = EC-01）

## 检查范围

PLAN-20260918-093 声称的交付面：① 干净 checkout 重扫的封印与剖面；② 依赖 advisory 的
**署名与结论**；③ hook 侧 `scanner_enobufs` 的复现与根因；④ 25 条 findings 逐条处置与
未覆盖范围。**不在本轮**：依赖版本升级（pin 变更 = escalation）、hook 侧修复动作
（环境变更 + 安全策略决定）、威胁建模/授权面覆盖。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| 干净 checkout 输入边界 | 导出树文件数 vs `git ls-files`；树内 `scratch/`、`artifacts/` 存在性 | PASS（**3025 == 3025**；两者均不存在） |
| 重扫封印成立 | MCP `security_scan_status` 读 `scanId`/`seal`/`findingCount`；三件产物 sha256 逐件重算与 `seal.json.artifacts` 对照 | PASS（`scan-2026-09-18T05-00-08.268Z-e6e01fa153c8`；`sha256:1e549272…`；三件 **OK/OK/OK**） |
| 剖面与差异可解释 | 干净 checkout 25 条 vs 工作树 36 条，按「严重度 × 顶层目录」逐格对照 | PASS（差异恰为 `artifacts/` 2 HIGH + `scratch/` 17 MEDIUM；`tools/` 10→18 有解释） |
| 依赖 advisory 有署名 | 独立 OSV 查询（413 包）→ 包名/版本/advisory id/CVE/CVSS/修复版本/来源；lockfile digest 与命令可复跑 | PASS（**3 包 20 条**，全部 dev 链） |
| 扫描器自报的可信度被检验 | 两次扫描自报与独立查询三方对照 | PASS（182/1 未署名 vs 11/0 vs 独立 413/3 ⇒ **不作依据**，已写明） |
| hook 侧复现 | 手工喂 PreToolUse payload 给 `git-gate-hook.mjs`，≥2 次 | PASS（2/2 次逐字 `scanner_no_output`，790/767 ms） |
| hook 侧根因 | `cli.js semgrep status --json` + `which semgrep` + `pip show semgrep` + `installDir` 存在性 | PASS（`installed:false` / `reason:install_metadata_missing`；目录不存在；无 PATH/发行版安装） |
| 25 条逐条处置 | 逐行核对位置与汇点（含 1 条新增签名 `tools/PA1R运行演练v1.py:56`） | PASS（全部误报/开发工具；无产品代码变更） |
| 动态 SQL 判据的覆盖更正 | AST 结构判据 + 自带 `--selftest` 反证 | PASS（`--selftest` 8/8；产品树 **22 处**逐处核对为常量/固定记号；`tools/` 0 处） |
| 未覆盖范围写明 | 记录 §5 六条 | PASS |
| 不宣称「项目安全」 | 记录开头与结论逐条同读 | PASS |
| 记录链与门禁 | 治理 validator；PLAN/RECHECK/MEM/ALL_PLAN/GOAL 交叉引用；本地 m0；CI 六 job | 见「门禁」与「结论」 |

## 反证与实测

- **输入边界会改变结论（判据有效性的正面证据）**：同一台扫描器、同一天、同一份代码，
  只把输入从「工作树」换成「tracked 导出树」，19 条落在非仓库内容上的 findings **全部
  消失**。若判据是套话，这 19 条的差异不会出现。
- **AST 判据不是空转**：`probe_dynamic_sql_forms.py --selftest` 用**合成 AST 节点**
  （不写任何危险源码文本，规避写路径守卫）验证分类器能分离开四种构造形态与三种良性
  形态 ⇒ 8/8 ok；随后产品树 22 处的「逐处判安全」才有意义。
- **扫描器依赖阶段的自相矛盾是实测**：同一份 lockfile，`182/1（未署名）` 与 `11/0`
  两次自报；独立查询 413 包。三者并列写进记录，**不挑一个当结论**。
- **未做的验证**：没有为「证明判据有效」而向产品代码注入真实缺陷；本 PLAN 的判据是
  文档 + 命令 + 已执行用例，不涉及产品行为断言。

## 告警（W）

- **W-1（依赖升级未做，需人工/ADR）**：3 个包共 20 条 advisory 全部有修复版本，但
  `vite` / `yaml` / `undici` 的版本变更属**上游 pin 变更**（GOAL-005 `escalation_triggers`）
  ⇒ 本循环不改，登记待拍板。**不得**读作「依赖面无风险」。
- **W-2（hook 侧 L3 门仍是失败开放）**：根因定位为检测层缺失，但修复动作未执行；
  且修复后 `graded` 模式的 medium=ask 可能挡住无人值守提交 ⇒ 修与不修都是安全策略决定。
- **W-3（依赖阶段覆盖率不可知）**：扫描器自报只覆盖 11 个包（本轮）与 182 个包（上轮），
  其选择逻辑未明；本 PLAN 用独立查询绕开它，但**没有**修好它。
- **W-4（历史记录的口径更正）**：RECHECK-091 的「产品树动态 SQL 零命中」按 grep 判据写成，
  本轮 AST 判据显示有 22 处构造（逐处判安全）。**结论未变、依据被更正**；后续引用
  RECHECK-091 该条时应以本轮记录为准。
- **W-5（本轮处置未覆盖 `tools/` 之外的深度）**：25 条的处置是静态结论 + 逐处代码核对 +
  已执行用例的组合，**不是**运行时验证；授权面仍未覆盖（见记录 §5）。

## 门禁

- 治理 validator：`.cursor/skills/governance-check/scripts/validate.py` 绿（本机实跑）。
- 定向：`tests/tooling/test_python_source_limits.py` **930 passed**；
  `tests/application/protocol_authoring/test_draft_service.py` **13 passed**（沿用并复跑）。
- 探针自证：`probe_dynamic_sql_forms.py --selftest` **8/8 ok**；
  `probe_dependency_advisories.py` 两步（build 413 查询 / merge 3 命中）实跑一致。
- 本地 m0 与 CI 六 job 终态：见 PLAN 状态历史与 GOAL-005 迭代日志（循环内回填）。

## 结论

EC-01 的四条判据**全部成立**：干净 checkout 重扫取得可复核封印（三件产物摘要全 OK，
剖面 25 条且差异可解释）、依赖 advisory 拿到**署名与结论**（3 包 20 条，带 CVE/CVSS/
修复版本/来源）、hook 侧 `scanner_enobufs` **可复现且根因已定位**（检测层缺失）、
25 条 findings 逐条处置完毕。本轮**无产品代码变更**，也未改任何依赖版本。

结果为 **PASS_WITH_WARNINGS**：W-1（依赖升级待拍板）与 W-2（L3 门修复属安全策略决定）
是需要人工推进的两条；W-3/W-4/W-5 是覆盖与口径的如实登记。**本复检不主张「项目安全」**，
也不以「扫描没报问题」作为任何结论的依据。
