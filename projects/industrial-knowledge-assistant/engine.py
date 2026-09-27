"""Local, citation-first retrieval over the fictional portfolio knowledge base."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent / "data" / "knowledge_base.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "about", "after", "an", "and", "are", "at", "be", "before", "by",
    "do", "for", "from", "how", "i", "if", "in", "is", "it", "me", "my",
    "of", "on", "or", "should", "the", "this", "to", "what", "when", "where",
    "which", "with", "you",
}
INTENT_TERMS = {
    "maintenance": {"alarm", "air", "compressor", "equipment", "gauge", "lubrication", "maintenance", "pressure", "regulator", "repair", "service"},
    "quality": {"defect", "inspection", "quality", "reject", "retry", "serial", "test", "trace", "weld", "hold"},
    "data": {"communication", "flag", "freshness", "plc", "quality", "signal", "stale", "tag", "timestamp", "telemetry"},
    "operations": {"downtime", "handover", "line", "operator", "shift", "station", "start", "stop", "work", "order"},
}
TOOL_NAMES = {
    "maintenance": "maintenance notes",
    "quality": "quality procedures",
    "data": "signal health notes",
    "operations": "operations procedures",
    "all": "full knowledge library",
}


class KnowledgeBaseError(ValueError):
    """Raised when the generated knowledge base violates its document contract."""


def tokens(text: str) -> list[str]:
    """Normalize text into searchable lowercase terms."""
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def validate_documents(docs: Any) -> list[dict[str, Any]]:
    """Check the normalized document contract before indexing any content."""
    if not isinstance(docs, list) or not docs:
        raise KnowledgeBaseError("knowledge base must be a non-empty list")
    seen: set[str] = set()
    required = {"id", "title", "category", "section", "revision", "source_path", "content_sha256", "text"}
    for index, doc in enumerate(docs):
        if not isinstance(doc, dict) or required - doc.keys():
            raise KnowledgeBaseError(f"document {index} is missing required fields")
        if not all(isinstance(doc[key], str) and doc[key] for key in required):
            raise KnowledgeBaseError(f"document {doc.get('id', index)} has empty or invalid fields")
        if doc["id"] in seen:
            raise KnowledgeBaseError(f"duplicate document id: {doc['id']}")
        if doc["category"] not in TOOL_NAMES or doc["category"] == "all":
            raise KnowledgeBaseError(f"unsupported category on {doc['id']}")
        seen.add(doc["id"])
    return docs


def load_documents(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    """Load and validate the generated corpus before serving queries."""
    with path.open(encoding="utf-8") as source:
        return validate_documents(json.load(source))


def classify_intent(query: str) -> str:
    """Route a query to one local category, with a stable all-documents fallback."""
    query_terms = set(tokens(query))
    scores = {category: len(query_terms & terms) for category, terms in INTENT_TERMS.items()}
    priority = ("maintenance", "data", "quality", "operations")
    best_category = min(priority, key=lambda category: (-scores[category], priority.index(category)))
    return best_category if scores[best_category] else "all"


class KnowledgeRetriever:
    """In-memory TF-IDF-style retriever with deterministic source citations."""

    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = validate_documents(documents)
        self._terms: list[Counter[str]] = []
        self._title_terms: list[Counter[str]] = []
        self._document_frequency: Counter[str] = Counter()
        for document in documents:
            body_terms = Counter(tokens(document["text"]))
            title_terms = Counter(tokens(f"{document['title']} {document['section']}"))
            self._terms.append(body_terms)
            self._title_terms.append(title_terms)
            self._document_frequency.update(set(body_terms) | set(title_terms))

    def search(self, query: str, *, category: str = "all", limit: int = 3) -> list[dict[str, Any]]:
        """Return the highest-ranked passages, favoring title and section matches."""
        query_terms = set(tokens(query))
        if not query_terms or limit < 1:
            return []
        candidates = [
            index for index, document in enumerate(self.documents)
            if category == "all" or document["category"] == category
        ]
        if not candidates:
            return []

        ranked: list[dict[str, Any]] = []
        corpus_size = max(len(self.documents), 1)
        for index in candidates:
            document = self.documents[index]
            score = 0.0
            matched: list[str] = []
            for term in query_terms:
                title_frequency = self._title_terms[index].get(term, 0)
                body_frequency = self._terms[index].get(term, 0)
                frequency = body_frequency + title_frequency * 2
                if not frequency:
                    continue
                matched.append(term)
                inverse_frequency = math.log(1 + corpus_size / (1 + self._document_frequency[term]))
                score += (1 + math.log(frequency)) * inverse_frequency
            if score <= 0:
                continue
            ranked.append({
                "id": document["id"],
                "title": document["title"],
                "category": document["category"],
                "section": document["section"],
                "revision": document["revision"],
                "source_path": document["source_path"],
                "text": document["text"],
                "score": round(score, 4),
                "matched_terms": sorted(matched),
            })
        ranked.sort(key=lambda item: (-item["score"], item["id"]))
        return ranked[: min(limit, 10)]


def route_query(query: str, retriever: KnowledgeRetriever, *, limit: int = 3) -> dict[str, Any]:
    """Route, retrieve, and return an evidence-only answer plus its trace."""
    normalized = query.strip()
    if not normalized or len(normalized) > 240:
        raise ValueError("question must contain between 1 and 240 characters")
    category = classify_intent(normalized)
    matches = retriever.search(normalized, category=category, limit=limit)
    fallback = False
    if not matches and category != "all":
        matches = retriever.search(normalized, category="all", limit=limit)
        fallback = bool(matches)

    if matches:
        lead = matches[0]
        response = f"In {lead['title']} ({lead['id']}), the sample procedure says: {lead['text']}"
    else:
        response = "I couldn't find a matching passage in the local sample library. Try terms from a station event, quality check, maintenance note, signal issue, or shift procedure."

    return {
        "query": normalized,
        "answer": response,
        "route": {
            "category": category,
            "tool": TOOL_NAMES[category],
            "fallback_to_all": fallback,
        },
        "sources": matches,
        "retrieved_count": len(matches),
    }


DEFAULT_RETRIEVER = KnowledgeRetriever(load_documents())


def search(query: str, *, limit: int = 3) -> list[dict[str, Any]]:
    """Public search helper over the bundled corpus."""
    category = classify_intent(query)
    results = DEFAULT_RETRIEVER.search(query, category=category, limit=limit)
    return results or DEFAULT_RETRIEVER.search(query, category="all", limit=limit)


def answer(query: str) -> dict[str, Any]:
    """Return a deterministic response composed only from retrieved evidence."""
    return route_query(query, DEFAULT_RETRIEVER)
