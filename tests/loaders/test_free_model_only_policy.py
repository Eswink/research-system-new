"""EC-01：**只允许零价模型**出现在 `examples/config/models.yaml`，且端点指向新站。

**它补哪一格**（GOAL-20261119-115 建档实测）：换站之后「我们只用免费模型」这条纪律
只写在 YAML 注释里 —— 往 `models.yaml` 加一个收费模型名，全仓没有任何判据会红，
而后果是**真实扣费**。这不是一条"好看的门"，它是钱包边界。

**判什么**（每条都指向具体字节或具体名字）：

1. `models.yaml` 的每个 `model_name` ∈ **零价集合**；零价集合由
   `GET https://opencode.ai/inference/go/v1/models` 的 `cost.text.*.price == 0`
   推出。判据读**离线夹具**（`tests/fixtures/free_models_catalog.json`，2026-11-20 实查
   裁剪），因此**默认零出网**；`test_the_live_catalog_still_agrees` 是那条显式开关的
   真查用例。
2. `main.base_url` = `/inference/go/openai/v1`、`agnes-anthropic.base_url` =
   `/inference/go/anthropic/v1`（**不是** `/inference/v1` 那棵另一棵树，也不是旧站）。
3. `main.discovery.allow_models` 恰是零价集合（声明面与实测面**逐字相同**）。
4. 两个端点都带 `x-opencode-session` 静态头：新站的推理面缺它即 400
   （2026-11-20 实测），没有它整条运行链不可用。

**反证臂**（本文件自带，不靠外部脚本）：把零价集合里的名字换成夹具里的收费名
（`deepseek-v4-pro`）⇒ 判据必须红且**点名**该模型；把 `extra_headers` 摘掉 ⇒ 判红。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from adapters.contracts.models_loaders import load_llm_endpoints, load_models

_ROOT = Path(__file__).resolve().parents[2]
_MODELS = "examples/config/models.yaml"
_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_CATALOG = _ROOT / "tests" / "fixtures" / "free_models_catalog.json"

#: 新站的 OpenAI 兼容面（run 腿只能走这条）。
_OPENAI_BASE_URL = "https://opencode.ai/inference/go/openai/v1"
#: 新站的 Anthropic 面（probe 腿）。
_ANTHROPIC_BASE_URL = "https://opencode.ai/inference/go/anthropic/v1"
#: 推理面必填的会话路由头（实测 400 `MissingSessionID`）。
_SESSION_HEADER = "x-opencode-session"


def catalog() -> dict[str, Any]:
    # `cast` 而不是 `# type: ignore`：strict 配置下后者是 syntax error（既有纪律）。
    return cast(dict[str, Any], json.loads(_CATALOG.read_text(encoding="utf-8")))


def zero_price_models(payload: dict[str, Any]) -> set[str]:
    """从 `/models` 响应里挑出**零价**模型 id。

    判法：把 `cost.text` 下所有 `price` 数字取出来，**全部为 0** 才算零价。
    `cost.text.input.cache.read` 也算（缓存读价非零的模型不是"免费"）。
    一个没有 `price` 字段的模型**不**算零价（缺证据 ≠ 免费）。
    """
    free: set[str] = set()
    for item in payload.get("data", []):
        prices = _prices((item.get("cost") or {}).get("text") or {})
        if prices and all(price == 0 for price in prices):
            free.add(str(item["id"]))
    return free


def _prices(node: Any) -> list[float]:
    found: list[float] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "price" and isinstance(value, (int, float)):
                found.append(float(value))
            else:
                found.extend(_prices(value))
    return found


def declared_model_names(path: Path | None = None) -> list[str]:
    """`models.yaml` 的 `model_name` 行（只读**声明行**，不读注释）。

    注释里写旧模型名不会让判据变绿，也不会让它变红 —— 判据要判的是"配了什么"。
    """
    target = path or (_ROOT / _MODELS)
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return [str(item["model_name"]) for item in (raw.get("models") or {}).values()]


class TestOnlyFreeModelsAreConfigured:
    """受判面：`models.yaml` 的九个 `model_name` 全部落在零价集合里。"""

    def test_the_catalog_reading_is_non_vacuous(self) -> None:
        """零价集合**非空**（空集合会让下面那条断言空转成永久绿）。"""
        free = zero_price_models(catalog())
        assert len(free) == 4, sorted(free)
        assert free == {
            "hy4-flash-free",
            "longcat-2.5-free",
            "beam-free",
            "iceman-contributor-free",
        }, sorted(free)

    def test_every_configured_model_name_is_zero_price(self) -> None:
        free = zero_price_models(catalog())
        declared = declared_model_names()
        assert declared, "models.yaml 里没有任何 model_name ⇒ 受判面不成立"
        paid = sorted({name for name in declared if name not in free})
        assert not paid, f"这些收费模型名出现在 models.yaml 里（会真实扣费）：{paid}"

    def test_the_press_naming_a_paid_model_is_refused(self, tmp_path: Path) -> None:
        """**反证臂**：把任意一个 model_name 换成夹具里的收费名 ⇒ 判据红且点名。"""
        text = (_ROOT / _MODELS).read_text(encoding="utf-8")
        pressed = text.replace("model_name: hy4-flash-free", "model_name: deepseek-v4-pro", 1)
        assert pressed != text, "按压前提失效：配置里没有 hy4-flash-free"
        target = tmp_path / "models.yaml"
        target.write_text(pressed, encoding="utf-8")
        free = zero_price_models(catalog())
        paid = sorted({name for name in declared_model_names(target) if name not in free})
        assert paid == ["deepseek-v4-pro"], paid

    def test_a_paid_model_really_is_absent_from_the_zero_set(self) -> None:
        """反证的**前提**也要判：`deepseek-v4-pro` 确实是收费的（否则上面那条空转）。"""
        assert "deepseek-v4-pro" not in zero_price_models(catalog())


class TestTheEndpointsPointAtTheNewStation:
    """受判面：两个 `base_url` 是新站的两张脸，且都带会话头。"""

    def test_the_run_leg_sits_on_the_openai_face(self) -> None:
        endpoints = load_llm_endpoints(_ENDPOINTS)
        assert endpoints["main"].base_url == _OPENAI_BASE_URL
        assert endpoints["main"].protocol == "OPENAI_COMPATIBLE"

    def test_the_probe_leg_sits_on_the_anthropic_face(self) -> None:
        endpoints = load_llm_endpoints(_ENDPOINTS)
        assert endpoints["agnes-anthropic"].base_url == _ANTHROPIC_BASE_URL
        assert endpoints["agnes-anthropic"].protocol == "ANTHROPIC"

    def test_neither_face_is_the_other_inference_tree(self) -> None:
        """`/inference/v1` 是**另一棵树**（模型集不同），别混用。"""
        for endpoint in load_llm_endpoints(_ENDPOINTS).values():
            assert "/inference/v1" not in endpoint.base_url, endpoint.base_url
            assert endpoint.base_url.startswith("https://opencode.ai/inference/go/"), (
                f"{endpoint.id} 不在新站的 go 树里：{endpoint.base_url}"
            )

    @pytest.mark.parametrize("endpoint_id", ["main", "agnes-anthropic"])
    def test_both_faces_declare_the_session_header(self, endpoint_id: str) -> None:
        """缺这个头 ⇒ 推理面 400（2026-11-20 实测，鉴权通过也拒）。"""
        endpoint = load_llm_endpoints(_ENDPOINTS)[endpoint_id]
        names = {name.lower() for name, _value in endpoint.extra_headers}
        assert _SESSION_HEADER in names, (
            f"{endpoint_id} 没有声明 {_SESSION_HEADER}："
            "新站的 chat/completions 会 400 MissingSessionID"
        )

    def test_the_session_header_is_not_a_credential(self) -> None:
        """反向：这条缝**不得**被用来携带凭据（域构造期就拒，这里判配置面没绕）。"""
        for endpoint in load_llm_endpoints(_ENDPOINTS).values():
            names = {name.lower() for name, _value in endpoint.extra_headers}
            assert not (names & {"authorization", "x-api-key"}), names


class TestTheDiscoveryDeclarationMatchesTheReading:
    """`allow_models` 是「只用零价」的**可读声明**；它必须与实测集合逐字相同。"""

    def test_allow_models_is_exactly_the_zero_price_set(self) -> None:
        endpoints = load_llm_endpoints(_ENDPOINTS)
        assert endpoints["main"].discovery is not None
        declared = set(endpoints["main"].discovery.allow_models)
        assert declared == zero_price_models(catalog()), sorted(declared)


@pytest.mark.requires_live_llm
class TestTheLiveCatalogStillAgrees:
    """**显式开关**才跑的真查：夹具读数与当下的 `/models` 是否仍然一致。

    默认 skip 是**如实**的：本判据的零出网契约要求 CI 不依赖外部服务。
    `requires_live_llm` 只**允许**出网，它本身不跳过 —— 所以这里显式 `skip`，
    理由点名缺的开关。换站/换模型之后跑它来刷新夹具
    （`tools/refresh_free_model_catalog.py`）。
    """

    def test_the_live_catalog_still_agrees(self) -> None:
        if not _live_switch_on():
            pytest.skip(
                "live catalog check skipped: set RESEARCHOS_LIVE_E2E=1 to compare the "
                "frozen fixture with the live /models response"
            )
        import httpx

        response = httpx.get("https://opencode.ai/inference/go/v1/models", timeout=60.0)
        response.raise_for_status()
        live = zero_price_models(response.json())
        recorded = zero_price_models(catalog())
        assert live == recorded, (
            "零价集合与夹具读数不同：夹具已陈旧，用 tools/refresh_free_model_catalog.py 刷新"
            f"（live={sorted(live)} recorded={sorted(recorded)}）"
        )


def _live_switch_on() -> bool:
    return os.environ.get("RESEARCHOS_LIVE_E2E", "") in {"1", "true", "yes", "on"}


def test_the_loader_points_at_the_file_this_judge_reads() -> None:
    """受判面自检：本文件判的是 `load_models` 读的那份文件（防止判据盯错路径）。"""
    loaded = load_models(_MODELS)
    free = zero_price_models(catalog())
    assert loaded, "load_models 读出空目录 ⇒ 受判面不成立"
    assert all(item.model_name in free for item in loaded.values()), sorted(
        item.model_name for item in loaded.values()
    )
