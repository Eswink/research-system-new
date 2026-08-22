# LEARN-20260813-002 — Validation Evidence Record

晋升时的确定性验证结果存档（2026-08-22）：

```
before replay: python -B -c "import openhands" → ModuleNotFoundError: No module named 'openhands'（FAIL 复现）
after  replay: uv run --frozen --no-sync python -B -c "import openhands; print('openhands import OK')" → openhands import OK（PASS）
regression:
  - .cursor/skills/governance-check/scripts/validate.py → Cursor 治理验证通过
  - .cursor/skills/learning-check/scripts/validate_cursor_learning.py → PASS: learning system validated
  - .cursor/skills/learning-check/scripts/run_cursor_learning_evals.py → LEARNING GATE EVAL PASS
  - .cursor/skills/system-spec-check/scripts/validate_bundle.py → 验证通过
```

- 结果记录于 `.cursor/learning/accepted/LEARN-20260813-002.yaml` 的 validation 段。
- 授权记录见 `LEARN-20260813-002-authorization.md`。