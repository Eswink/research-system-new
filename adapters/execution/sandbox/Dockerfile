# Research OS M9 实验沙盒镜像。
#
# 镜像供应链 pin（见 UPSTREAM_COMPONENTS.yaml 与
# docs/references/upstream/M9_DOCKER_QUALIFICATION.md）：
# - 基础镜像 python:3.12-slim 按 OCI index digest pin（Docker Hub registry
#   API 查询，2026-08-15），多架构可解析；
# - 每次 execute 由 DockerExecutionBackend 解析实际 image digest 写入
#   ExecutionRun.compute_usage_summary["image_digest"]，供
#   ReproducibilityAudit 绑定。
#
# 镜像内安全基线：非 root 用户（uid 1000）、/workspace 工作目录。
# 容器级隔离由运行时 host_config 施加（network none / cap drop ALL /
# no-new-privileges / readonly rootfs / tmpfs /tmp / CPU-mem-pids 限额），
# 不在此镜像内重复声明。
FROM python:3.12-slim@sha256:dd29372629eeba2dd003fd9e9d35a5b8236c44727875a0364254b5127af88e65

RUN useradd --create-home --uid 1000 --shell /bin/bash researcher \
    && mkdir -p /workspace \
    && chown researcher:researcher /workspace

USER researcher
WORKDIR /workspace

ENTRYPOINT []
CMD ["/bin/sh"]