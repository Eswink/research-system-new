"""GOAL-098 的**模型独立性**判据（从断言集里分出的独立模块）。

**为什么独立成文件**：`goal098_closeout_assertions.py` 已贴 450 行硬上限，而这段判据
需要 import 产品解析器（约 30 行）。放进断言集会把文件推过门禁 ——
分文件是**尺寸约束**下的正确落点，不是把判据藏起来：断言集仍然调用它。

**判的是什么**：作者的执行目标 `(endpoint_id, model_name)` 与生产侧 + 三位评审者
**都不相交**。原判据断言 `"deepseek-v4-pro-0813" in models`，那是把某次接入商的
运营数据写成了判据 —— 换站必红而红不代表独立性坏了（GOAL-20261111-108 的同一条教训）。
"""

from __future__ import annotations

from pathlib import Path

#: 与断言集同源的三个声明面。
MODELS = "examples/config/models.yaml"
AGENTS = "examples/config/agents.yaml"
PROFILES = "examples/config/model_profiles.yaml"

#: 作者必须与之不相交的四个 agent（生产侧 + 三位评审者）。
OTHERS: tuple[str, ...] = ("writer", "reviewer_a", "reviewer_b", "novelty_a")


def author_sits_on_a_distinct_target(root: Path) -> bool:
    """作者组的目标与 `OTHERS` 的并集不相交（两边都必须解析成功，否则判 False）。"""
    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from adapters.contracts.models_loaders import load_model_profiles, load_models
    from adapters.contracts.roles_loaders import load_agents
    from packages.application.ports.resource_catalog import CatalogSnapshot
    from packages.application.preflight.review_independence import resolve_agent_targets

    snapshot = CatalogSnapshot(
        models=load_models(str(root / MODELS)),
        model_profiles=load_model_profiles(str(root / PROFILES)),
        agents=load_agents(str(root / AGENTS)),
        roles={},
    )
    author = resolve_agent_targets("novelty_writer", snapshot.agents["novelty_writer"], snapshot)
    if not author.resolved or not author.targets:
        return False
    others: set[tuple[str, str]] = set()
    for agent_id in OTHERS:
        resolved = resolve_agent_targets(agent_id, snapshot.agents[agent_id], snapshot)
        if not resolved.resolved or not resolved.targets:
            return False
        others |= resolved.targets
    return not (author.targets & others)


__all__ = ["OTHERS", "author_sits_on_a_distinct_target"]
