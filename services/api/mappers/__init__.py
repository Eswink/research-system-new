"""Control Plane API 映射层：Domain → DTO 显式转换（禁止 __dict__ dump）。

本层允许 import packages.domain（services → application → domain 方向内），
不得 import adapters（.importlinter.api 门禁与 routers 同级）。
"""
