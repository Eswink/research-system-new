"""Protocol phase DAG 的确定性校验测试。"""

import pytest

from packages.application.preflight import run_preflight
from packages.application.protocol_compile.dag import compile_dag
from packages.domain.core import Version
from packages.domain.protocols import (
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)


def test_dag_missing_forward_and_cycle_findings() -> None:
    missing = ProtocolDefinition(
        id="simple_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="a",
                strategy=PhaseStrategy.DETERMINISTIC,
                depends_on=["missing"],
            )
        ],
    )
    assert compile_dag(missing).findings[0].code == "DAG_MISSING_DEPENDENCY"

    forward = ProtocolDefinition(
        id="simple_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC, depends_on=["b"]),
            ProtocolPhase(id="b", strategy=PhaseStrategy.DETERMINISTIC),
        ],
    )
    assert compile_dag(forward).findings[0].code == "DAG_FORWARD_REFERENCE"

    cycle = compile_dag(
        ProtocolDefinition(
            id="simple_protocol_v0_4_0",
            version=Version("0.4.0"),
            phases=[
                ProtocolPhase(
                    id="a",
                    strategy=PhaseStrategy.DETERMINISTIC,
                    depends_on=["b"],
                ),
                ProtocolPhase(
                    id="b",
                    strategy=PhaseStrategy.DETERMINISTIC,
                    depends_on=["a"],
                ),
            ],
        )
    )
    assert "DAG_CYCLE" in {finding.code for finding in cycle.findings}


def test_protocol_phase_rejects_duplicate_dependencies() -> None:
    with pytest.raises(ValueError, match="dependencies must be unique"):
        ProtocolPhase(
            id="a",
            strategy=PhaseStrategy.DETERMINISTIC,
            depends_on=["b", "b"],
        )


def test_orphan_phase_is_info_finding_not_blocking() -> None:
    from packages.application.protocol_compile import compile_protocol
    from packages.domain.protocols import (
        ProtocolDefinition,
        ProtocolPhase,
    )
    from tests.application.protocol_fixtures import catalog, context

    orphan = ProtocolDefinition(
        id="simple_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC),
            ProtocolPhase(id="b", strategy=PhaseStrategy.DETERMINISTIC, depends_on=["a"]),
            ProtocolPhase(
                id="solo",
                strategy=PhaseStrategy.DETERMINISTIC,
                required_roles=[RoleRequirement("researcher", 1, 1)],
            ),
        ],
    )
    result = compile_dag(orphan)
    codes = {finding.code for finding in result.findings}
    assert "DAG_ORPHAN_PHASE" in codes
    assert result.valid
    compiled = compile_protocol(orphan, catalog(), context().project)
    assert compiled.plan is not None
    # INFO finding 必须可观测（不再被静默丢弃），但不阻断 preflight
    assert "DAG_ORPHAN_PHASE" in {finding.code for finding in compiled.findings}
    report = run_preflight(compiled.plan, context())
    assert report.status.value == "PASS"
