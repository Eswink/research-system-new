"""执行权威与策略约束的判据（GOAL-20261107-107 EC-09 / EC-10 / EC-11）。

**它封住的失败形态**（每一种都会让「模型可以自己写实验脚本」变成一句话）：

1. **`AUTHORED` 悄悄打开**：出厂默认必须是关闭的 —— 否则本轮不是「建机制」，是「未经
   决定就改了安全姿态」。
2. **白名单被绕过**：非白名单路径、绝对路径、`..` 都必须点名拒绝。
3. **digest pin 形同虚设**：白名单命中但摘要为空 ⇒ 没有 pin，跑的不是被审过的字节。
4. **策略约束声明了但不执行**（既有缺陷）：`sandbox_required` / `path_prefix` /
   `max_seconds` 三条各自都要真的能拦住。

臂的分布：正向（白名单 + 约束满足 ⇒ 通过）／四条对抗性反证（无沙箱 / 越界路径 / 超时 /
`AUTHORED` 未放行）／边界（约束缺席 ≠ 拒绝；`..` 一律拒）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.application.experiments.script_authority import (
    AUTHORED_ALLOWED_BY_DEFAULT,
    MAX_SECONDS_KEY,
    PATH_PREFIX_KEY,
    SANDBOX_KEY,
    AuthorityError,
    ExecutionAuthority,
    ExecutionRequest,
    authority_for,
    check_constraints,
    digest_of,
    normalized_digest,
    shipped_scripts,
)

#: 出厂闭集里的第一条（从 `design_script` 取 —— 本文件不复制名单）。
_SHIPPED = shipped_scripts()[0]
_DIGEST = "sha256:" + "a" * 64


def _request(**overrides: object) -> ExecutionRequest:
    base: dict[str, object] = {
        "script_path": _SHIPPED,
        "digest": _DIGEST,
        "authored": False,
        "constraints": None,
        "write_path": None,
        "requested_seconds": None,
        "sandboxed": True,
    }
    base.update(overrides)
    return ExecutionRequest(**base)  # type: ignore[arg-type]


def test_the_shipped_whitelist_is_not_copied_here() -> None:
    """闭集来自 `design_script`（**同一个对象**，不是第二份清单）。"""
    from packages.application.experiments.design_script import SHIPPED_EXPERIMENT_SCRIPTS

    assert shipped_scripts() == tuple(SHIPPED_EXPERIMENT_SCRIPTS)
    assert len(shipped_scripts()) == 3


def test_authored_is_off_by_default() -> None:
    """**核心边界**：`AUTHORED` 出厂默认关闭 —— 打开它是一次安全姿态决定。

    这条同时是本轮「只建机制、不启用」的机械形态：如果哪天默认值被改成 `True`，
    这里先红。
    """
    assert AUTHORED_ALLOWED_BY_DEFAULT is False
    with pytest.raises(AuthorityError, match="not enabled"):
        authority_for(_request(authored=True))


def test_authored_passes_when_explicitly_enabled() -> None:
    """显式放行时才过（证明拒绝不是恒真）。

    **GOAL-20261111-112 EC-04**：显式放行现在是**两道门**——`authored_allowed=True`
    **且**具名安全 profile 在场。本用例补上门、仍然断言「都过时确实放行」；
    「只过一道就拒」由 `test_authored_profile.py` 双向覆盖。
    """
    from packages.application.experiments.script_authority import AUTHORED_SAFETY_PROFILE

    assert (
        authority_for(
            _request(authored=True),
            authored_allowed=True,
            declared_profile=AUTHORED_SAFETY_PROFILE,
        )
        is ExecutionAuthority.AUTHORED
    )


def test_a_script_outside_the_whitelist_is_named_not_run() -> None:
    """反证：非白名单脚本点名拒绝，判词列出闭集。"""
    with pytest.raises(AuthorityError, match="not one of the shipped scripts"):
        authority_for(_request(script_path="evil/authored.py"))


def test_an_absolute_or_escaping_path_cannot_smuggle_past_the_whitelist() -> None:
    """反证：绝对路径与 `..` 都不在闭集里 ⇒ 同样点名拒绝（不靠字符串前缀判断）。"""
    for path in ("/etc/passwd", "../../etc/passwd", "examples/experiments/../evil.py"):
        with pytest.raises(AuthorityError, match="not one of the shipped scripts"):
            authority_for(_request(script_path=path))


def test_a_shipped_script_without_a_digest_has_no_pin() -> None:
    """**边界**：白名单命中但摘要为空 ⇒ 拒绝（没有 pin 就等于「跑什么都行」）。"""
    with pytest.raises(AuthorityError, match="carries no digest"):
        check_constraints(_request(digest=""))


def test_both_digest_spellings_normalize_the_same_way() -> None:
    """`sha256:<hex>` 与裸 hex 归一后相等（比较面不因写法漂移）。"""
    assert normalized_digest("sha256:" + "A" * 64) == normalized_digest("a" * 64)


def test_the_digest_of_a_real_file_is_its_bytes() -> None:
    """`digest_of` 读的是字节（用仓里真实存在的一个脚本自证）。"""
    path = Path(_SHIPPED)
    assert digest_of(path) == digest_of(path)
    assert len(digest_of(path)) == 64


# ---------------------------------------------------------------- 三条策略约束（对抗性）


def test_sandbox_required_blocks_an_unsandboxed_execution() -> None:
    """**对抗反证 1**：声明 `sandbox_required: true` 而执行自称非沙箱 ⇒ 拒。"""
    constraints = {SANDBOX_KEY: True}
    with pytest.raises(AuthorityError, match="requires a sandbox"):
        check_constraints(_request(constraints=constraints, sandboxed=False))
    # 沙箱执行时同一条约束**不**拦（证明判据不是恒真）。
    assert check_constraints(_request(constraints=constraints, sandboxed=True))


def test_path_prefix_blocks_writes_outside_it() -> None:
    """**对抗反证 2**：写入越界 ⇒ 拒；前缀内 ⇒ 过。"""
    constraints = {PATH_PREFIX_KEY: "/code"}
    with pytest.raises(AuthorityError, match="outside the policy prefix"):
        check_constraints(_request(constraints=constraints, write_path="/etc/shadow"))
    assert check_constraints(_request(constraints=constraints, write_path="/code/analysis.py"))


def test_path_prefix_refuses_upward_escape_even_within_the_prefix() -> None:
    """`..` 一律拒 —— 即使归一后看起来在前缀内（前缀匹配不是路径归一）。"""
    constraints = {PATH_PREFIX_KEY: "/code"}
    with pytest.raises(AuthorityError, match="escapes upward"):
        check_constraints(_request(constraints=constraints, write_path="/code/../etc/passwd"))


def test_path_prefix_requires_a_declared_write_path() -> None:
    """声明了写入前缀却不说写哪里 ⇒ 拒（沉默不是合规）。"""
    with pytest.raises(AuthorityError, match="declares no write path"):
        check_constraints(_request(constraints={PATH_PREFIX_KEY: "/code"}))


def test_max_seconds_blocks_an_overlong_execution() -> None:
    """**对抗反证 3**：执行秒数超限 ⇒ 拒；未超 ⇒ 过。"""
    constraints = {MAX_SECONDS_KEY: 30}
    with pytest.raises(AuthorityError, match="exceeds the policy limit"):
        check_constraints(_request(constraints=constraints, requested_seconds=31))
    assert check_constraints(_request(constraints=constraints, requested_seconds=30))


def test_absent_constraints_do_not_invent_requirements() -> None:
    """**边界**：约束缺席 ≠ 拒绝 —— 本模块让既有声明生效，不新增策略。"""
    assert check_constraints(_request(constraints=None)) is ExecutionAuthority.SHIPPED
    assert check_constraints(_request(constraints={})) is ExecutionAuthority.SHIPPED


def test_the_governed_executor_now_reads_the_constraint_face() -> None:
    """**既有缺陷的机械形态**：执行边界必须**读** `constraints`。

    此前 `policy/native.py` 返回它、全仓没人读 ⇒ 三条声明等于不存在。这条判据钉的是
    源码里的读取点（`evaluation.constraints`），不是行为 —— 行为另有一条。
    """
    source = Path("packages/application/experiments/governed.py").read_text(encoding="utf-8")
    assert "evaluation.constraints" in source, (
        "执行边界没有读约束面 ⇒ sandbox_required / path_prefix / max_seconds 仍是死声明"
    )
    assert "_enforce_constraints(" in source
