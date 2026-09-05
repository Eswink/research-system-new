# Backup & Recovery — v0.4.0

PostgreSQL Domain entities are business truth. Content-addressed Artifact blobs are the
corresponding payload store. A valid backup/restore claim requires both; an archive that merely
exists is insufficient.

## Backup scope

- PostgreSQL canonical tables, migration identity, leases/outbox, EvalReport and Usage rows;
- Artifact blob root referenced by PostgreSQL `artifacts.digest` rows;
- version/release identity and deployment configuration templates;
- secret references only, never secret values;
- runtime workspace and telemetry are non-authoritative and are not the sole backup source.

## Supported command

Use the cross-platform binary-safe CLI documented in
[`PERSONAL_DEPLOYMENT.md`](PERSONAL_DEPLOYMENT.md):

```text
uv run --frozen --no-sync python -B tools/backup.py --container <postgres> --blob-root <blob-root> --out <backup-dir> --keep 7 --verify --sample 100
```

The output is one PostgreSQL custom-format dump, one Artifact tar archive, and one timestamped
manifest. `--verify` checks live canonical Artifact rows against live blobs; it does not replace an
actual restore drill.

## Restore order

```text
Fresh PostgreSQL 16 target
→ tools/restore.py streams the custom dump without shell redirection
→ tools/restore.py extracts into an empty Artifact root and verifies every blob digest
→ configure a read-only API against the restored DB/blob root
→ cross-restore Research Truth audit
→ only then restore worker/runtime service
```

Supported restore command:

```text
uv run --frozen --no-sync python -B tools/restore.py --container <fresh-postgres> --dump <dump> --artifact-archive <archive> --blob-target <empty-dir>
```

The restore CLI rejects path traversal, links, malformed content-addressed paths, digest mismatch,
and non-empty Artifact targets. PostgreSQL cross-major direct restore is unsupported; restore into
the same major first.

## Required post-restore audit

For at least one completed Run, resolve and verify:

```text
Run
→ Run Manifest Artifact
→ Experiment Artifact(s)
→ Evidence and Source
→ Claim
→ EvalReport
→ Deliverable Artifact
```

Also verify ExperimentRun/Audit, Usage, Memory, migration `001..010`, and all restored Artifact
SHA-256 values. A missing reference, stale blob path, digest mismatch, or unverifiable Deliverable
makes the restore invalid.

## Recovery semantics

- Expired leases are recovered by scheduler policy; operators do not edit PostgreSQL manually.
- RUNNING work is re-evaluated through lease/fence semantics; late results cannot overwrite a
  higher fence.
- Non-idempotent external side effects remain subject to explicit operator review.
- Run Manifest and runtime image compatibility must be checked before resumed execution.

## Secret and retention controls

Canary scanning must cover the dump, Artifact archive, restored blobs, logs, telemetry, exports,
Git current tree/history, and process logs. Report only fingerprints and finding counts. Retention,
RPO, RTO, encrypted off-host copies, and backup key rotation are operator decisions; this personal
baseline does not promise a fixed SLA or cross-region disaster recovery.
