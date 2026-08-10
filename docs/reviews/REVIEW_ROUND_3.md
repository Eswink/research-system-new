# Review Round 3 — Security, Governance & Operations

Threshold: **9.2 / 10**
Score: **9.1 / 10**
Result: **REJECTED → Reworked**

## Rubric

| Dimension | Score |
|---|---:|
| Runtime/tool security | 9.6 |
| Model relay risk handling | 9.5 |
| Workflow recovery | 9.5 |
| Identity/authorization | 8.4 |
| Data governance | 8.5 |
| Backup/operations | 8.3 |
| Research integrity | 9.0 |

## Findings

1. Team deployment lacked a formal human/service/agent identity model.
2. Agent permissions were not explicitly separated from the initiating human's permissions.
3. The LLM relay was modeled technically but not yet as a data-processing/egress boundary.
4. No formal source rights, retention, deletion or data residency policy existed.
5. Backup/restore, incident controls, SLO indicators and capacity admission were not documented.
6. Research integrity rules were distributed across Evidence docs rather than frozen as a governance contract.

## Remediation

- Added Identity & Access and task-scoped AgentPrincipal.
- Added Data Governance and Research Integrity contracts.
- Added Operations Runbook, Backup/Recovery and SLO/Capacity docs.
- Added access-control and retention examples.
- Extended API/DB/Index and added ADR-0022..0024.

A fourth final release gate is required because Round 3 remained below threshold.
