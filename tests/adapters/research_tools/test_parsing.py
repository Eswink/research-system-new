"""PA-1: NCBI efetch XML parsing guards — entity-expansion (DTD/ENTITY)
rejection, size cap, malformed-XML InvalidInputError; normal sample passes."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from adapters.research_tools.parsing import (
    extract_article,
    normalize_elink,
    normalize_esearch,
    parse_efetch_xml,
)
from packages.application.ports.errors import InvalidInputError

_SAMPLE = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>123</PMID>
      <Article>
        <ArticleTitle>Example findings</ArticleTitle>
        <Abstract><AbstractText>Some abstract.</AbstractText></Abstract>
        <Journal>
          <Title>J Example</Title>
          <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
        </Journal>
        <AuthorList><Author><LastName>Doe</LastName><ForeName>Jane</ForeName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

_ENTITY_BOMB = b"""<?xml version="1.0"?>
<!DOCTYPE bomb [<!ENTITY x "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa">]>
<PubmedArticleSet>&x;</PubmedArticleSet>
"""

_EXTERNAL_ENTITY = b"""<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY ext SYSTEM "file:///etc/passwd">]>
<PubmedArticleSet>&ext;</PubmedArticleSet>
"""

#: 内部子集但**没有**实体声明（考的是"内部子集"这一条守卫本身）。
_INTERNAL_SUBSET = b"""<?xml version="1.0"?>
<!DOCTYPE r [<!ELEMENT r ANY>]>
<PubmedArticleSet/>
"""

#: 真实 efetch 响应的形状（GOAL-011 EC-01 live 实测：**外部 DOCTYPE**）。
_REAL_DOCTYPE = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2025//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>38000001</PMID>
      <Article><ArticleTitle>Real shape</ArticleTitle></Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_normal_sample_parses() -> None:
    from typing import Any

    result = parse_efetch_xml(_SAMPLE)
    articles: list[dict[str, Any]] = result["articles"]  # type: ignore[assignment]
    assert len(articles) == 1
    article = articles[0]
    assert article["pmid"] == "123"
    assert article["title"] == "Example findings"
    assert article["authors"] == ["Jane Doe"]


def test_entity_expansion_declaration_rejected() -> None:
    with pytest.raises(InvalidInputError, match="ENTITY"):
        parse_efetch_xml(_ENTITY_BOMB)


def test_external_entity_declaration_rejected() -> None:
    with pytest.raises(InvalidInputError, match="ENTITY"):
        parse_efetch_xml(_EXTERNAL_ENTITY)


def test_internal_dtd_subset_rejected() -> None:
    """无实体声明的内部子集同样拒绝（实体定义只能写在那里，守在最外一层）。"""
    with pytest.raises(InvalidInputError, match="internal DTD subset"):
        parse_efetch_xml(_INTERNAL_SUBSET)


def test_real_external_doctype_is_accepted() -> None:
    """真实响应的外部 DOCTYPE 必须放行（GOAL-011 EC-01 live 实测的回归守卫）。

    反证：把守卫改回"拒绝一切 DOCTYPE"⇒ 本条立刻红，而真实 `literature_read`
    会在每一次调用上失败（离线夹具不带 DOCTYPE，所以那条路此前全绿）。
    """
    result = parse_efetch_xml(_REAL_DOCTYPE)
    articles = result["articles"]
    assert isinstance(articles, list) and len(articles) == 1
    assert articles[0]["pmid"] == "38000001"


def test_oversize_rejected() -> None:
    with pytest.raises(InvalidInputError, match="5MB"):
        parse_efetch_xml(b"<x/>" + b" " * (5 * 1024 * 1024))


def test_malformed_xml_rejected() -> None:
    with pytest.raises(InvalidInputError, match="well-formed"):
        parse_efetch_xml(b"<PubmedArticleSet><unclosed>")


def test_normalize_helpers_unaffected() -> None:
    assert normalize_esearch({"esearchresult": {"count": "2", "idlist": [1, 2]}}, "t") == {
        "count": 2,
        "ids": ["1", "2"],
        "query": "t",
    }
    assert normalize_elink({"linksets": [{"linksetdbs": [{"links": [7]}]}]}, "9") == {
        "pmid": "9",
        "pmc_links": ["7"],
    }
    assert extract_article(ET.fromstring("<MedlineCitation/>")) == {
        "pmid": "",
        "title": "",
        "abstract": "",
        "journal": "",
        "year": "",
        "authors": [],
    }
