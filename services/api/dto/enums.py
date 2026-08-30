"""Closed value vocabularies exposed by the Control Plane API."""

from __future__ import annotations

from typing import Literal, TypeAlias

CostAmountStatusValue: TypeAlias = Literal[
    "ACTUAL",
    "ESTIMATED",
    "MONETARY_UNAVAILABLE",
    "USAGE_UNKNOWN",
    "ZERO",
    "NO_DATA",
    "CURRENCY_CONFLICT",
    "PARTIALLY_METERED",
]

PriceDimensionValue: TypeAlias = Literal["model", "tool", "experiment", "evaluation"]

ResourceTypeValue: TypeAlias = Literal[
    "MODEL_TOKENS",
    "MODEL_REQUESTS",
    "MODEL_COST",
    "EVALUATION_SCORER",
    "TOOL_REQUESTS",
    "TOOL_COST",
    "CPU_TIME",
    "GPU_TIME",
    "MEMORY",
    "STORAGE",
    "NETWORK",
    "WALL_CLOCK",
    "AGENT_TURNS",
    "PARALLELISM",
]

LedgerCostStatusValue: TypeAlias = Literal["KNOWN", "UNKNOWN"]
LedgerQuantityStatusValue: TypeAlias = Literal["KNOWN", "UNKNOWN"]
OutboxPendingStatusValue: TypeAlias = Literal["KNOWN", "UNKNOWN"]
QualityGateVerdictValue: TypeAlias = Literal["PASS", "PASS_WITH_WARNINGS", "REVISE", "BLOCK"]
TrendPointVerdictValue: TypeAlias = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "REVISE",
    "BLOCK",
    "INDETERMINATE",
    "MISSING_EVALUATION",
]
RegressionVerdictValue: TypeAlias = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "REVISE",
    "BLOCK",
    "INDETERMINATE",
]
ComparabilityVerdictValue: TypeAlias = Literal[
    "COMPARABLE",
    "CASE_SET_CHANGED",
    "RUBRIC_CHANGED",
    "DATASET_CHANGED",
    "GATE_CONFIG_CHANGED",
    "SCORER_CHANGED",
    "EVALUATOR_CHANGED",
    "SYSTEM_VERSION_CHANGED",
    "SEGMENTED",
    "INCOMPATIBLE_GENERATION",
]

__all__ = [
    "ComparabilityVerdictValue",
    "CostAmountStatusValue",
    "LedgerCostStatusValue",
    "LedgerQuantityStatusValue",
    "OutboxPendingStatusValue",
    "PriceDimensionValue",
    "QualityGateVerdictValue",
    "RegressionVerdictValue",
    "ResourceTypeValue",
    "TrendPointVerdictValue",
]
