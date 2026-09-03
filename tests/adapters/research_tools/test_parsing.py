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


def test_normal_sample_parses() -> None:
    result = parse_efetch_xml(_SAMPLE)
    assert len(result["articles"]) == 1
    article = result["articles"][0]
    assert article["pmid"] == "123"
    assert article["title"] == "Example findings"
    assert article["authors"] == ["Jane Doe"]


def test_entity_expansion_declaration_rejected() -> None:
    with pytest.raises(InvalidInputError, match="DOCTYPE/ENTITY"):
        parse_efetch_xml(_ENTITY_BOMB)


def test_external_entity_declaration_rejected() -> None:
    with pytest.raises(InvalidInputError, match="DOCTYPE/ENTITY"):
        parse_efetch_xml(_EXTERNAL_ENTITY)


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
