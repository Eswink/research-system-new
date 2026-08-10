# ADR-0002 — PostgreSQL Canonical State + Immutable RunManifest

Status: Accepted

Domain state is canonical.
Runtime/workflow histories are execution records.

Every run freezes a semantic RunManifest to prevent silent model/tool/prompt/protocol drift during resume.
