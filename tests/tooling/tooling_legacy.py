"""`tools/` 射程**之外**的历史遗留：清单 + 理由。

输入方 = `test_tooling_scripts_meet_product_gates`。

**为什么单列**：那份判据正文贴着 **450 行硬上限**（`tests/` 在 `PRODUCT_ROOTS` 里，受
`test_python_source_limits.py` 管）。这张表有 45 条历史资产，留在判据文件里会让「加一个
新脚本」这类正常动作必然撞线。拆出来不改变语义 —— 它仍是**源码里的**「清单 + 理由」，
且**逐条**给出不纳入射程的原因（空理由不算豁免，与 `goal_commit_chain` 同一纪律）。

**消费方**：判据文件 `from tests.tooling.tooling_legacy import LEGACY_OUT_OF_SCOPE`
（作为模块属性读取，`getattr(judge, "LEGACY_OUT_OF_SCOPE", ())` 的既有形态照旧成立）。
"""

from __future__ import annotations

_REASON_PA1R = "PA-1R 历史资产（非 ASCII 命名落在 R-N1 豁免面）；纳入射程需另行授权"
_REASON_PROBE = "历史取证探针（一次性使用，非交付面）"
_REASON_SPIKE = "上游调研脚本（历史调研资产）"
_REASON_GOAL015 = "GOAL-015 专属脚本（其收口验证器是 GOAL-023 的一般化先例）；纳入射程需另行授权"
_REASON_CLI = "历史 CLI / 工具（有 tests/tooling 行为判据，但无格式 / 规模 / 类型门）"
_REASON_LAB = "M12 / M13 历史资产（参考 / 冒烟 / 实验门禁脚本）"

#: 射程**之外**的历史遗留（**清单 + 理由**；不纳入射程，且不为其变绿而改历史资产）。
LEGACY_OUT_OF_SCOPE: tuple[tuple[str, str], ...] = (
    ("tools/PA1R发布真相v1.py", _REASON_PA1R),
    ("tools/PA1R密钥审计v1.py", _REASON_PA1R),
    ("tools/PA1R恢复闭包v1.py", _REASON_PA1R),
    ("tools/PA1R故障演练v1.py", _REASON_PA1R),
    ("tools/PA1R质量门禁v1.py", _REASON_PA1R),
    ("tools/PA1R运行演练v1.py", _REASON_PA1R),
    ("tools/backup.py", _REASON_CLI),
    ("tools/classify_local_gate_reds.py", _REASON_GOAL015),
    ("tools/credential_audit.py", _REASON_CLI),
    ("tools/docs_consistency_check.py", _REASON_CLI),
    ("tools/freeze_eval_dataset.py", _REASON_LAB),
    ("tools/gen_openapi.py", _REASON_CLI),
    ("tools/m12_ncbi_smoke.py", _REASON_LAB),
    ("tools/m12_reference_workflow.py", _REASON_LAB),
    ("tools/m12_relay_smoke.py", _REASON_LAB),
    ("tools/personal_reference_workflow.py", _REASON_CLI),
    ("tools/probes/enumerate_clock_injected_pg_tests.py", _REASON_PROBE),
    ("tools/probes/probe_cancel_race.py", _REASON_PROBE),
    ("tools/probes/probe_canonical_state.py", _REASON_PROBE),
    ("tools/probes/probe_db_failure.py", _REASON_PROBE),
    ("tools/probes/probe_dependency_advisories.py", _REASON_PROBE),
    ("tools/probes/probe_dynamic_sql_forms.py", _REASON_PROBE),
    ("tools/probes/probe_migration.py", _REASON_PROBE),
    ("tools/probes/probe_outbox.py", _REASON_PROBE),
    ("tools/probes/probe_perf.py", _REASON_PROBE),
    ("tools/probes/probe_scheduled_recovery.py", _REASON_PROBE),
    ("tools/probes/probe_stale_worker.py", _REASON_PROBE),
    ("tools/probes/probe_telemetry_soak.py", _REASON_PROBE),
    ("tools/quarantine_and_run_m0.py", _REASON_GOAL015),
    ("tools/restore.py", _REASON_CLI),
    ("tools/snapshot_migrate.py", _REASON_CLI),
    ("tools/upstream-spikes/S1_import_fingerprint.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S2_llm_construction.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S3_agent_conversation_run.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S4_cancel_pause_error.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S5_local_workspace.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S6_persistence_resume.py", _REASON_SPIKE),
    ("tools/verify_goal015_closeout.py", _REASON_GOAL015),
)
