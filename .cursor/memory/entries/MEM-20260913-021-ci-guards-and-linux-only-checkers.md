---
id: MEM-20260913-021
title: CI 守卫事实（docker/GPU 探测式 skip、Linux 大小写检查器、守卫不得削弱专属门禁）
status: ACTIVE
created_at: 2026-09-13
updated_at: 2026-09-13
scope: repository
confidence: 0.9
review_after: 2026-12-13
source_plans:
  - .cursor/plans/tasks/PLAN-20260912-042-ci-debt-remediation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260913-042-ci-debt-remediation.md
supersedes: []
tags:
  - ci
  - test-guards
  - docker
  - gpu
  - docs-consistency
---

# MEM-20260913-021 — CI 环境守卫与 Linux-only 检查器事实

## 做了什么

GOAL-20260912-001 cycle 2（PLAN-042）为消除「CI 才暴露」的既有红项，固化以下事实：

1. **环境依赖测试的守卫应探测真实能力，并区分「可选」与「专属门禁」**。
   新增 `tests/conftest.py` 在 collection 时探测：docker 必须是
   **Linux-capable** daemon（`client.info()["OSType"] == "linux"`）——windows-latest
   的 Windows-container daemon 能 ping 通但跑不了 Linux sandbox 镜像，会假失败；
   GPU 用 `/dev/nvidia*`（Linux 权威）或 `nvidia-smi -L`（Windows 回退）。
   缺失时对 `requires_docker`/`requires_gpu` 用例 skip。
2. **但 `pytest -m requires_docker` 是 container-quality 作业的专属选择**：此时
   daemon 缺失必须 fail-closed（硬失败），否则整轮 skip 成 vacuous green，
   等于削弱门禁。钩子按 `config.option.markexpr == "requires_docker"` 判定。
3. **`tools/docs_consistency_check.py` 的 recheck 匹配曾有大小写 bug**：旧
   `rechecks.glob("*M*.md")` 配小写 milestone token，在大小写敏感的 Linux 上
   匹配不到 `RECHECK-...-m13-...`（本地 Windows 不敏感 → 假绿）。修为
   `milestone_id.lower()` + `glob("RECHECK-*.md")` + `-<token>-` 子串判定。
4. **本地 `docker build` 出来的镜像没有 `RepoDigests`**：`name@sha256:<config-id>`
   不是 daemon 可解析的引用（404）。pinned-reference 用例应优先 registry repo
   digest，无 digest 时退回同一消费路径的 image-id 引用。

## 为什么这样做

这些都是「产品正确但 CI 红」的假失败源；按不 skip 产品断言、不降门禁强度的
方式处置（补探测守卫、修检查器大小写、修测试对镜像引用的假设）。memory 记录
避免下次在 Linux runner 上重新踩坑。

## 怎么做与复现

- 复现 1（守卫）：无 docker 时 `pytest tests/adapters/execution -q` =
  58 passed / 31 skipped，**0 failed**；`pytest .../test_docker_backend_e2e.py
  -m requires_docker` = 硬失败（daemon 缺失仍红）。
- 复现 2（检查器）：`python tools/docs_consistency_check.py` = DOCS-CHECK PASS；
  `pytest tests/tooling/test_docs_consistency_check.py -q` = 10 passed。
- 复现 3（PG 标记）：无 PG 时 `pytest tests/postgres/test_workflow_engine_parity.py
  -q` = skipped（需模块级 `pytestmark = pytest.mark.postgres` 才能被 conftest 捕获）。

## 适用边界

适用于 tests/ 下按环境标记（requires_docker/requires_gpu/postgres）的套件与
CI 专属作业选择；普通产品断言与无环境依赖的单测不受影响。Linux-only 检查器
行为差异只在大小写敏感文件系统上暴露，Windows 本地验证不足以替代。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260912-042-ci-debt-remediation.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260913-042-ci-debt-remediation.md`
- 相关 run：GitHub Actions run #52（quality-ubuntu 失败清单）
