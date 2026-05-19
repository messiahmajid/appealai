import asyncio
import re
from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    authors: str
    journal: str
    year: str
    publication_types: list[str]


@dataclass
class WebEvidence:
    source: str
    title: str
    summary: str
    citation: str
    url: str
    evidence_level: str


def _extract_xml_tag(xml: str, tag: str) -> str | None:
    pattern = rf"<{tag}[^>]*>([\s\S]*?)</{tag}>"
    match = re.search(pattern, xml, re.IGNORECASE)
    return match.group(1) if match else None


def _clean_xml_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_pubmed_xml(xml: str) -> list[PubMedArticle]:
    articles: list[PubMedArticle] = []
    blocks = xml.split("<PubmedArticle>")[1:]

    for block in blocks:
        try:
            pmid = _extract_xml_tag(block, "PMID") or ""
            title = _extract_xml_tag(block, "ArticleTitle") or ""
            abstract_text = _extract_xml_tag(block, "AbstractText") or ""
            journal = _extract_xml_tag(block, "Title") or ""
            year = _extract_xml_tag(block, "Year") or ""
            publication_types = [
                _clean_xml_text(m.group(1))
                for m in re.finditer(r"<PublicationType[^>]*>([^<]+)</PublicationType>", block, re.I)
            ]

            last_name_match = re.search(r"<LastName>([^<]+)</LastName>", block)
            authors = f"{last_name_match.group(1)} et al." if last_name_match else ""

            is_retracted = any(
                re.search(r"retracted|retraction", p, re.I) for p in publication_types
            ) or bool(re.search(r"retracted publication", block, re.I))

            if title and abstract_text and not is_retracted:
                articles.append(
                    PubMedArticle(
                        pmid=pmid,
                        title=_clean_xml_text(title),
                        abstract=_clean_xml_text(abstract_text)[:600],
                        authors=authors,
                        journal=_clean_xml_text(journal),
                        year=year,
                        publication_types=publication_types,
                    )
                )
        except Exception:
            continue

    return articles


async def _search_pubmed(
    client: httpx.AsyncClient, query: str, max_results: int = 5
) -> list[PubMedArticle]:
    try:
        search_resp = await client.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "retmode": "json", "retmax": max_results, "sort": "relevance", "term": query},
            timeout=8,
        )
        if not search_resp.is_success:
            return []

        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        fetch_resp = await client.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
            timeout=8,
        )
        if not fetch_resp.is_success:
            return []

        return _parse_pubmed_xml(fetch_resp.text)
    except Exception as e:
        logger.warning("pubmed_search_failed", error=str(e))
        return []


def _build_search_queries(
    denied_service: str, denial_reason: str, cpt_codes: str, icd10_codes: str
) -> list[str]:
    evidence_filter = (
        "(humans[MeSH Terms]) AND (systematic review[Publication Type] OR "
        "meta-analysis[Publication Type] OR practice guideline[Publication Type] OR "
        "randomized controlled trial[Publication Type] OR guideline[Publication Type])"
    )
    queries = [
        f"({denied_service}) AND medical necessity AND {evidence_filter}",
        f"({denied_service}) AND clinical outcomes AND evidence-based AND {evidence_filter}",
    ]
    if denial_reason:
        short_reason = denial_reason[:100]
        queries.append(f"({denied_service}) AND ({short_reason}) AND coverage criteria AND humans[MeSH Terms]")
    if cpt_codes or icd10_codes:
        queries.append(f"({denied_service}) AND ({cpt_codes} {icd10_codes}) AND medical policy AND humans[MeSH Terms]")
    return queries


def _evidence_level(publication_types: list[str]) -> str:
    joined = " ".join(publication_types).lower()
    if "practice guideline" in joined or "guideline" in joined:
        return "Guideline"
    if "systematic review" in joined or "meta-analysis" in joined:
        return "Systematic review/meta-analysis"
    if "randomized controlled trial" in joined:
        return "Randomized controlled trial"
    if "clinical trial" in joined:
        return "Clinical trial"
    return "Peer-reviewed article"


RELEVANCE_STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "when", "then", "than",
    "medical", "necessity", "guidelines", "guideline", "coverage", "criteria",
    "clinical", "outcomes", "evidence", "based", "requested", "procedure", "service",
    "does", "meet", "not",
}


def _relevance_tokens(*values: str) -> list[str]:
    tokens = [
        t.strip()
        for t in re.split(r"[^a-z0-9]+", " ".join(values).lower())
        if len(t.strip()) >= 4 and t.strip() not in RELEVANCE_STOP_WORDS and not t.strip().isdigit()
    ]
    return list(dict.fromkeys(tokens))


def _is_relevant_article(
    article: PubMedArticle,
    denied_service: str,
    denial_reason: str,
    icd10_codes: str,
) -> bool:
    service_tokens = _relevance_tokens(denied_service)
    context_tokens = _relevance_tokens(denied_service, denial_reason, icd10_codes)
    article_text = f"{article.title} {article.abstract}".lower()
    service_matches = sum(1 for token in service_tokens if token in article_text)
    context_matches = sum(1 for token in context_tokens if token in article_text)
    return service_matches >= 1 or context_matches >= 3


async def search_web_evidence(
    denied_service: str,
    denial_reason: str,
    cpt_codes: str,
    icd10_codes: str,
) -> dict:
    queries = _build_search_queries(denied_service, denial_reason, cpt_codes, icd10_codes)

    all_articles: list[PubMedArticle] = []
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(queries):
            articles = await _search_pubmed(client, query, 3)
            all_articles.extend(articles)
            if i < len(queries) - 1:
                await asyncio.sleep(0.5)

    seen: set[str] = set()
    unique: list[PubMedArticle] = []
    for a in all_articles:
        if a.pmid not in seen:
            seen.add(a.pmid)
            if _is_relevant_article(a, denied_service, denial_reason, icd10_codes):
                unique.append(a)

    evidence: list[WebEvidence] = [
        WebEvidence(
            source="PubMed",
            title=a.title,
            summary=a.abstract,
            citation=f"{a.authors} {a.journal}. {a.year}. PMID: {a.pmid}",
            url=f"https://pubmed.ncbi.nlm.nih.gov/{a.pmid}/",
            evidence_level=_evidence_level(a.publication_types),
        )
        for a in unique[:5]
    ]

    formatted_context = ""
    if evidence:
        formatted_context = "\n\n---\n\n".join(
            f"[PubMed {i + 1}] {e.title}\nEvidence Level: {e.evidence_level}\nCitation: {e.citation}\nURL: {e.url}\n\nFindings: {e.summary}"
            for i, e in enumerate(evidence)
        )

    return {
        "evidence": [
            {
                "source": e.source,
                "title": e.title,
                "citation": e.citation,
                "url": e.url,
                "evidenceLevel": e.evidence_level,
            }
            for e in evidence
        ],
        "formattedContext": formatted_context,
    }
