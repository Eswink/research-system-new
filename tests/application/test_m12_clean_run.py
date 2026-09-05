"""M12 clean-run harness（M12-R1 WP8）：从干净状态重建同一真相。

验证（Fake 注入，deterministic，无需 docker/live）：
- 全链闭合并输出 run/manifest/experiment/artifact/evidence/claim/eval/budget/
  deliverable 标识；audit PASS；eval verdict PASS（评测输入来自持久状态，
  空输入自证被禁止）；
- 两次 clean-run 同 run_id：semantic digest 一致，deliverable digest 一致
  （确定性 render），raw artifact digest 允许 variance（WP4）；
- 无 relay 配置：relay 段 NOT VERIFIED 占位，其余链仍闭合；
- 输出不含 credentials。

fixtures：tests/application/m12_clean_run_fixtures.py（与生产标识一致）。
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from packages.application.m12_reference.clean_run import run_clean_workflow
from tests.application.m12_clean_run_fixtures import (
    COMMAND,
    EXPERIMENT_RUN_ID,
    PLAN_ID,
    RUN_ID,
    make_deps,
)


class TestCleanRunHarness:
    def test_full_chain_closes_and_outputs_ids(self, tmp_path: Path) -> None:
        deps = make_deps(tmp_path)
        result = run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        payload = result.to_payload()
        assert payload["run_id"] == RUN_ID
        assert payload["manifest_digest"]
        assert payload["semantic_digest"]
        assert payload["experiment_run_id"] == EXPERIMENT_RUN_ID
        assert payload["artifact_ids"]
        assert payload["artifact_digests"]
        assert payload["evidence_ids"]
        assert payload["claim_id"] == f"claim:{EXPERIMENT_RUN_ID}:result"
        assert payload["claim_status"] == "VERIFIED"
        assert payload["audit_status"] == "PASS"
        assert payload["audit_digest"]
        assert payload["eval_report_digest"]
        assert payload["eval_verdict"] == "PASS"
        budget_entries = payload["budget_entries"]
        assert isinstance(budget_entries, int) and budget_entries >= 2
        assert payload["deliverable_digest"]
        relay = payload["relay"]
        assert isinstance(relay, dict) and relay.get("verified") is False

    def test_no_credentials_in_output(self, tmp_path: Path) -> None:
        result = run_clean_workflow(
            make_deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        serialized = json.dumps(result.to_payload())
        assert "fixture-key" not in serialized
        assert "sk-" not in serialized
        assert "LLM_" not in serialized

    def test_semantic_digest_stable_across_clean_runs(self, tmp_path: Path) -> None:
        first = run_clean_workflow(
            make_deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        second = run_clean_workflow(
            make_deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        # 同 run_id 两次 clean-run：semantic digest、claim/eval/audit 标识稳定
        assert first.semantic_digest == second.semantic_digest
        assert first.claim_id == second.claim_id
        assert first.eval_report_digest == second.eval_report_digest
        assert first.audit_digest == second.audit_digest

    def test_claim_verified_and_memory_committed(self, tmp_path: Path) -> None:
        deps = make_deps(tmp_path)
        run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        claim = deps.ledger.get_claim(f"claim:{EXPERIMENT_RUN_ID}:result")
        assert claim.status.value == "VERIFIED"
        memory = deps.memory.get(f"mem:{RUN_ID}:negative-result")
        provenance = memory.provenance
        assert provenance == f"{EXPERIMENT_RUN_ID}:experiment_result.json"

    def test_manifest_anchors_present(self, tmp_path: Path) -> None:
        result = run_clean_workflow(
            make_deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        assert result.manifest_digest
        assert result.semantic_digest

    def test_budget_records_experiment_and_eval_usage(self, tmp_path: Path) -> None:
        deps = make_deps(tmp_path)
        run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        entries = deps.budget.snapshot().entries
        types = {entry.resource_type.value for entry in entries}
        assert "CPU_TIME" in types
        # 确定性 scorer 不再被记为 model usage（M15 WP3c）；评测归账走独立
        # EVALUATION_SCORER 资源类型，实验时长走 CPU_TIME。
        assert "EVALUATION_SCORER" in types
        assert "MODEL_REQUESTS" not in types
        experiment = [e for e in entries if e.resource_type.value == "CPU_TIME"][0]
        assert experiment.quantity == 12
        assert experiment.cost_status.value == "UNKNOWN"

    def test_claim_statement_comes_from_reference_run_configuration(self, tmp_path: Path) -> None:
        statement = "mixed precision preserves accuracy under the fixed GPU budget"
        deps = replace(make_deps(tmp_path), claim_statement=statement)

        with pytest.raises(RuntimeError, match="evaluation gate not passed"):
            run_clean_workflow(
                deps,
                experiment_plan_id=PLAN_ID,
                experiment_command=COMMAND,
            )

        claim_id = f"claim:{EXPERIMENT_RUN_ID}:result"
        assert deps.ledger.get_claim(claim_id).statement == statement
