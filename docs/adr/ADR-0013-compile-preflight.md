# ADR-0013 — Compile and Preflight Before Run

Status: Accepted

Protocol 必须先编译为 CompiledRunPlan，并通过 Preflight 后才能冻结 Manifest 和进入 RUNNING。

目的：把模型、Tool、预算、权限和资源错误前移，而不是运行数小时后才失败。
