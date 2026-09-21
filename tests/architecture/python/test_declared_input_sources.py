"""GOAL-010 EC-02 同源判据：**声明输入**这一条链的四个面必须一致。

链条（任何一环单独改，另几环不变，就是漂移）：

1. **协议声明**：`ProtocolPhase.inputs`（`examples/protocols/*.yaml`）——产品面的声明；
2. **制品表**：`services.api.demo.DECLARED_INPUTS`——声明 id → 内容文件（组合根据此种入）；
3. **种入点**：生产组合根与各 harness 在装配时调用 `seed_declared_inputs`；
4. **消费点**：`result_handler.register_session_result` 把声明的输入登记成
   **非模型自述**的来源，`evidence_source_count` 只数这一类。

本判据**不**复用适配器/编排里的辅助函数当预言机（那会变成「实现改了判据跟着改」）：
协议面直接读 YAML，制品面直接读常量，落盘面直接拿 `ArtifactStore` 复算 digest。
"""

from __future__ import annotations

from pathlib import Path

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.domain.core import Digest
from services.api.demo import DECLARED_INPUTS, seed_declared_inputs

_ROOT = Path(__file__).resolve().parents[3]

#: 声明了 `inputs:` 的协议 → 该协议声明的全部输入制品 id。
_PROTOCOLS = {
    "console_demo_research_v1.yaml": {"input-corpus:console_demo_v1"},
    "sort_analysis_v1.yaml": {"input-corpus:sort_analysis_v1"},
}


def _protocol_inputs(name: str) -> set[str]:
    import yaml

    raw = yaml.safe_load((_ROOT / "examples" / "protocols" / name).read_text(encoding="utf-8"))
    return {item for phase in raw["phases"] for item in phase.get("inputs", [])}


def test_protocols_declare_exactly_the_tabulated_inputs() -> None:
    declared = {item for name in _PROTOCOLS for item in _protocol_inputs(name)}
    assert declared, "至少一个协议要声明输入，否则本判据是空转"
    assert declared == set(DECLARED_INPUTS), (
        "协议声明的输入与 DECLARED_INPUTS 必须逐字一致："
        f"协议={sorted(declared)} 表={sorted(DECLARED_INPUTS)}"
    )


def test_each_declared_input_is_a_real_file_whose_digest_recomputes() -> None:
    """种进去的字节必须等于仓库文件的字节，且 digest 能重算（内容寻址）。"""
    store = FakeArtifactStore()
    seed_declared_inputs(store)
    for artifact_id, relative in DECLARED_INPUTS.items():
        on_disk = (_ROOT / relative).read_bytes()
        assert store.get(artifact_id) == on_disk, f"{artifact_id} 的字节与 {relative} 不一致"
        assert store.verify(artifact_id) is True
        meta = store.meta(artifact_id)
        assert meta is not None and str(meta.digest) == str(Digest.of_bytes(on_disk))
        assert meta.created_by == "composition-root", "来源必须是组合根，不能是任何 agent"


def _control_plane_roots_owning_an_artifact_plane() -> dict[str, str]:
    """控制面组合根 = `services/api/` **顶层**模块里既造 artifact 存储、又把它接进 deps 的。

    这份集合**从文件本身推出来**（不是抄一份白名单）：新增一个组合根会让本判据变红，
    加它的人必须当场决定它要不要供应声明输入，而不是悄悄多一条不种入的路径。
    job 平面（`worker_gateway/` 子包）不在集合里——它服务的是 worker 会话，
    不是跑验收门的 run 平面。
    """
    found: dict[str, str] = {}
    for path in sorted((_ROOT / "services" / "api").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "ArtifactStore(" in source and "artifacts=" in source:
            found[path.name] = source
    return found


def test_every_control_plane_root_that_owns_an_artifact_plane_seeds_the_inputs() -> None:
    """生产装配点必须真的种入——只声明不种入 ⇒ run 会在登记输入时点名失败（fail closed）。

    PG 组合根曾因此**真的**回归过：SQLite 那条链种了、PG 那条没种，`test_m13_pg_run_e2e`
    的 run 直接 `FAILED`（`RECHECK-20260921-128` 登记）。所以本判据盯的是**集合**，
    不是某一个文件名。
    """
    roots = _control_plane_roots_owning_an_artifact_plane()
    assert set(roots) == {"composition.py", "pg_composition.py"}, (
        "控制面组合根的集合变了：新增的根要么种入声明输入，要么把这里连同理由一起改"
        f"（现在看到 {sorted(roots)}）"
    )
    for name, source in roots.items():
        assert "seed_declared_inputs(" in source, (
            f"{name} 装配了 artifact 平面却没有种入 demo 协议声明的输入 ⇒ "
            "跑该协议的 run 会在登记输入时点名失败"
        )
