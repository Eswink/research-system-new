# LEARN-20260821-004 — Validation Evidence Record

晋升时的确定性验证结果存档（2026-08-22）：

```
before replay: 不回滚安全门禁 hook 复现（回滚 fail-closed 安全门禁属高风险动作）；before 状态由 EXP-20260821-002
  原始拦截输出（browser_tabs/rename_chat 两次 permissionDenied）+ 临时 dump hook 捕获的真实 payload 存档，已满足确定性证据要求
after  replay: CallMcpTool(cursor-ide-browser, browser_tabs, {action: list}) → 成功返回（修复后 hook 放行，PASS）
regression:
  - .cursor/skills/governance-check/scripts/validate.py → Cursor 治理验证通过
  - .cursor/skills/learning-check/scripts/validate_cursor_learning.py → PASS: learning system validated
  - .cursor/skills/learning-check/scripts/run_cursor_learning_evals.py → LEARNING GATE EVAL PASS
  - .cursor/skills/system-spec-check/scripts/validate_bundle.py → 验证通过
  - .cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py → HOOK EVAL PASS（2026-08-21 修复时）
```

- 结果记录于 `.cursor/learning/accepted/LEARN-20260821-004.yaml` 的 validation 段。
- 授权记录见 `LEARN-20260821-004-authorization.md`。