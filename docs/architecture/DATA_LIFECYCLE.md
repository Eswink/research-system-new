# Data & Artifact Lifecycle v0.4.0

## 1. Source of Truth

PostgreSQL：

- entities
- relationships
- status
- provenance
- policy/budget metadata

Object Store：

- documents
- datasets
- logs
- code bundles
- figures
- checkpoints
- deliverables

## 2. Content-addressed Artifact

```text
digest
size
media_type
storage_uri
created_by
source_refs
classification
retention_policy
```

相同内容可去重。

## 3. Artifact State

```text
STAGED
VERIFIED
QUARANTINED
ACTIVE
ARCHIVED
DELETED_TOMBSTONE
```

## 4. Retention

按类型/项目/分类：

```text
keep forever
keep N days
archive
delete after export
legal hold
```

删除需要 Tombstone 和索引清理。

## 5. SourceRecord

记录：

```text
origin
access_time
license/terms
authors/DOI/URL
content digest
trust label
parser version
```

## 5a. Evidence structured provenance

IG-1 起，`Evidence` 可携带结构化跨阶段 provenance：

```text
run_id
experiment_run_id
metric_refs
workspace_snapshot_before / after
image_digest
environment_digest
tool_refs / skill_refs / model_refs
manifest_digest
```

这些字段由 `ExperimentEvidenceAdmission` 从 `ExperimentRun + RunManifest`
填充；不允许用自由文本 summary 替代结构化 provenance。

## 6. Derived Index

全文索引、embedding、Knowledge Graph projection 都可重建。

不得成为唯一事实源。

## 7. Export

Project/Run 应支持导出：

```text
manifest
domain JSON
artifacts
event/audit summary
reproducibility bundle
```
