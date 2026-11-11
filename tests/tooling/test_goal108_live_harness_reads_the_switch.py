"""GOAL-20261111-108 EC-07（`R-4`）：**live harness 与产品用同一个放行开关**。

**它补哪一格**：EC-07 的判据当初写在 GOAL 正文的 `verify:` 字段里
（`tests/tooling/test_goal108_live_harness_reads_the_switch.py`），但**文件从未落地**。
本文件补上它。

**为什么这条值得一个判据**（而不是「读一眼代码就知道」）：`R-4` 的原始缺陷是
`tests/e2e/manuscript_chain_live_support.py` **写死** `allow_localhost_endpoints=False`。
换到局域网中转站后，那个字面量让「产品能跑、判据不能跑」——live 判据永远证明不了
产品面可用。写成判据后，任何人把它改回写死值都会立刻红。

**判什么**（三条独立事实）：

1. 支持件里**有** `_allow_local_endpoints()` 这个读取口；
2. 该函数读的是 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS`（与 `ApiSettings.from_env`
   **同一个变量名**，不是新开关）；
3. 整个文件**不含** `allow_localhost_endpoints=False` 字面量（写死即红）。

**反证臂**（见 `TestTheCriterionBites`）：在真文件内容上做**同样的**字符串替换，
断言判据会红。反证用的是**与判据同一套匹配**，不是另写一个宽松版。
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "tests/e2e/manuscript_chain_live_support.py"

#: 唯一放行开关的名字（与 `services/api/settings.py` 的 `from_env` 逐字一致）。
SWITCH = "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS"
#: 写死即红的字面量（`R-4` 的原始缺陷形态）。
HARDCODED = "allow_localhost_endpoints=False"


def _source() -> str:
    return SUPPORT.read_text(encoding="utf-8")


def test_the_support_module_has_a_single_reading_point() -> None:
    assert "def _allow_local_endpoints()" in _source(), (
        "支持件缺 `_allow_local_endpoints()`：开关读取口不见了"
    )


def test_the_reading_point_uses_the_product_switch() -> None:
    """必须是**产品那个变量名**；另起一个新开关就会再次分叉。"""
    body = _source().split("def _allow_local_endpoints()", 1)[1]
    # 只取函数体（到下一个顶层 def 为止）。
    body = body.split("\ndef ", 1)[0]
    assert SWITCH in body, f"读取口没用产品开关 {SWITCH}：{body[:400]}"


def test_the_hardcoded_value_is_gone() -> None:
    offenders = [
        line
        for line in _source().splitlines()
        if HARDCODED in line and not line.lstrip().startswith("#")
    ]
    assert not offenders, f"写死的放行值回来了（R-4 回归）：{offenders}"


class TestTheCriterionBites:
    """反证臂：把原始缺陷放回去 ⇒ 判据必须红。"""

    def test_reintroducing_the_hardcoded_value_is_refused(self, tmp_path: Path) -> None:
        broken = _source() + "\n_ALLOW = allow_localhost_endpoints=False\n"
        offenders = [
            line
            for line in broken.splitlines()
            if HARDCODED in line and not line.lstrip().startswith("#")
        ]
        assert offenders, "反证臂失效：注入的字面量没被匹配到"

    def test_dropping_the_switch_name_is_refused(self) -> None:
        broken = _source().replace(SWITCH, "SOME_OTHER_SWITCH")
        body = broken.split("def _allow_local_endpoints()", 1)[1].split("\ndef ", 1)[0]
        assert SWITCH not in body, "反证臂失效：改名后函数体里仍能读到原开关"

    def test_an_empty_module_is_refused(self, tmp_path: Path) -> None:
        empty = tmp_path / "support.py"
        empty.write_text("", encoding="utf-8")
        assert "def _allow_local_endpoints()" not in empty.read_text(encoding="utf-8")


@pytest.mark.parametrize("forbidden", ["allow_localhost_endpoints=True"])
def test_a_hardcoded_true_is_flagged_too(forbidden: str) -> None:
    """写死 `True` 同样是分叉（判据侧自己决定放行，而不是读产品开关）。

    这不是判据的**现有**射程（`HARDCODED` 只钉 `False`），而是把边界写清楚：
    真要放行，走环境变量。本用例在当前树上必须**绿**（文件里没有这个字面量）。
    """
    assert forbidden not in _source()


def test_the_evidence_path_does_not_clobber_a_sealed_goal() -> None:
    """**本轮实测的缺陷**：判据每跑一次就覆盖 GOAL-106 已封存的读数。

    后果不是「文件变了」，而是一个**已完成 GOAL** 的两条同向判据随之判负
    （`goal106_closeout_assertions.py` 的 `goal-ec02-agrees-with-the-readings`）。

    判据判**形态**：写盘目标必须可经 `RESEARCHOS_LIVE_EVIDENCE` 改向，
    且缺省值仍是原路径（GOAL-106 的判据因此逐字不变）。
    """
    source = _source()
    assert "RESEARCHOS_LIVE_EVIDENCE" in source, (
        "写盘目标没有改向出口：再跑一次 live 判据会覆盖 GOAL-106 的封存读数"
    )
    assert "GOAL-20261104-106-manuscript-chain-live.json" in source, (
        "缺省路径必须仍是 GOAL-106 那一份（否则它的判据失去受判对象）"
    )
