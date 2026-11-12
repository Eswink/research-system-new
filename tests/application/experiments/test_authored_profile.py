"""GOAL-20261111-112 EC-04：`authored` 的**具名安全 profile** 与「不启用」的逐字事实。

**判什么**：

1. **`AUTHORED_ALLOWED_BY_DEFAULT` 仍是 `False`**（逐字断言——本轮交付的是网，不是启用）；
2. **两道门都要过**：`authored_allowed=True` **且** 具名 profile 在场 ⇒ 放行；
   只过一道 ⇒ **点名拒绝**（缺哪一道可读）；
3. **profile 的值必须逐字相等**（`1` / `true` / 空 ⇒ 都不放行——与 `RESEARCHOS_LIVE_E2E`
   同一条纪律：值必须一眼判）；
4. **`script_source` 声明**：缺席 ⇒ `shipped`；`authored` ⇒ 读得出；
   非法取值 ⇒ **点名拒绝**（不回落 `shipped`）。

**射程**：本文件**不**跑一次真实 `authored` 实验（那是 `U-1`）；它判的是闸门本身。
"""

from __future__ import annotations

import pytest

from packages.application.experiments.design_from_plan import ExperimentDesignUnreadableError
from packages.application.experiments.design_script import (
    SCRIPT_SOURCES,
    declared_script_source,
)
from packages.application.experiments.script_authority import (
    AUTHORED_ALLOWED_BY_DEFAULT,
    AUTHORED_SAFETY_PROFILE,
    AuthorityError,
    ExecutionRequest,
    authority_for,
    check_constraints,
    profile_is_declared,
)

_AUTHORED_REQUEST = ExecutionRequest(
    script_path="work/model_written_experiment.py",
    digest="sha256:" + "b" * 64,
    authored=True,
)


class TestTheDefaultStaysFalse:
    """「不启用」是逐字事实，不是措辞。"""

    def test_authored_is_not_allowed_by_default(self) -> None:
        assert AUTHORED_ALLOWED_BY_DEFAULT is False

    def test_the_default_path_refuses_authored(self) -> None:
        """即使 profile 在场，**不显式传** `authored_allowed=True` 仍拒。"""
        with pytest.raises(AuthorityError, match="not enabled"):
            authority_for(_AUTHORED_REQUEST, declared_profile=AUTHORED_SAFETY_PROFILE)

    def test_the_profile_name_is_a_stable_literal(self) -> None:
        """profile 名是个**具名常量**（判据与文档引用它；改名要改三处）。"""
        assert AUTHORED_SAFETY_PROFILE == "authored-experiments-v1"


class TestBothGatesAreRequired:
    """两道门：调用方意图 + 运维模式。缺一即拒，且判词点名缺哪一道。"""

    def test_explicit_allow_without_the_profile_is_refused(self) -> None:
        assert profile_is_declared(None) is False
        with pytest.raises(AuthorityError, match="named safety profile"):
            authority_for(_AUTHORED_REQUEST, authored_allowed=True)

    def test_the_profile_without_explicit_allow_is_refused(self) -> None:
        assert profile_is_declared(AUTHORED_SAFETY_PROFILE) is True
        with pytest.raises(AuthorityError, match="not enabled"):
            authority_for(_AUTHORED_REQUEST, authored_allowed=None)

    def test_both_gates_together_admit_authored(self) -> None:
        authority = authority_for(
            _AUTHORED_REQUEST, authored_allowed=True, declared_profile=AUTHORED_SAFETY_PROFILE
        )
        assert str(authority) == "AUTHORED"

    def test_the_full_check_also_passes_with_both_gates(self) -> None:
        """`check_constraints` 与 `authority_for` 同结论（约束为空 ⇒ 不检查那一条）。"""
        request = ExecutionRequest(
            script_path=_AUTHORED_REQUEST.script_path,
            digest=_AUTHORED_REQUEST.digest,
            authored=True,
            constraints={"sandbox_required": True},
            sandboxed=True,
        )
        admitted = check_constraints(
            request, authored_allowed=True, declared_profile=AUTHORED_SAFETY_PROFILE
        )
        assert str(admitted) == "AUTHORED"


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "AUTHORED-EXPERIMENTS-V1", ""])
def test_the_profile_value_must_match_exactly(value: str) -> None:
    """**值必须一眼判**：除逐字相等外一律不算（不做真值解析、不做大小写归一）。"""
    assert profile_is_declared(value) is False, value
    with pytest.raises(AuthorityError, match="named safety profile"):
        authority_for(_AUTHORED_REQUEST, authored_allowed=True, declared_profile=value)


class TestTheScriptSourceDeclaration:
    """`experiment_design.script_source` 的闭集与缺省。"""

    def test_the_closed_set_is_two_values(self) -> None:
        assert SCRIPT_SOURCES == ("shipped", "authored")

    def test_absent_means_shipped(self) -> None:
        assert declared_script_source({}, where="plan") == "shipped"

    def test_authored_is_readable(self) -> None:
        assert declared_script_source({"script_source": "authored"}, where="plan") == "authored"

    def test_case_and_whitespace_are_normalized(self) -> None:
        assert declared_script_source({"script_source": "  AUTHORED "}, where="plan") == "authored"

    @pytest.mark.parametrize("value", ["generated", "model", "", 1, None])
    def test_an_illegal_value_is_refused_by_name(self, value: object) -> None:
        """**不回落 `shipped`**：回落会把「模型说要用自己写的脚本」静默改写成「跑出厂脚本」。"""
        with pytest.raises(ExperimentDesignUnreadableError, match="must be one of"):
            declared_script_source({"script_source": value}, where="plan")

    def test_a_non_object_design_is_refused(self) -> None:
        with pytest.raises(ExperimentDesignUnreadableError, match="is not an object"):
            declared_script_source(["not", "a", "mapping"], where="plan")
