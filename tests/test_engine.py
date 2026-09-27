"""Unit tests for local retrieval and document ingestion."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSISTANT = ROOT / "projects" / "industrial-knowledge-assistant"
sys.path.insert(0, str(ASSISTANT))

from engine import DEFAULT_RETRIEVER, KnowledgeBaseError, answer, classify_intent, load_documents  # noqa: E402
from ingest import IngestionError, build_knowledge_base  # noqa: E402


class RetrieverTests(unittest.TestCase):
    def test_routes_maintenance_question_and_cites_source(self):
        result = answer("What should I do after an air pressure alarm?")
        self.assertEqual(result["route"]["category"], "maintenance")
        self.assertEqual(result["sources"][0]["id"], "OPS-004")
        self.assertIn("station", result["answer"])

    def test_routes_quality_and_signal_queries(self):
        self.assertEqual(classify_intent("weld retry limit"), "quality")
        self.assertEqual(classify_intent("stale PLC tag timestamp"), "data")

    def test_no_match_returns_no_citations(self):
        result = answer("quantum espresso weather")
        self.assertEqual(result["retrieved_count"], 0)
        self.assertEqual(result["sources"], [])
        self.assertIn("couldn't find", result["answer"])

    def test_query_length_is_bounded(self):
        with self.assertRaises(ValueError):
            answer("x" * 241)

    def test_ranking_is_stable(self):
        query = "quality inspection result trace identifier"
        self.assertEqual(
            [item["id"] for item in DEFAULT_RETRIEVER.search(query)],
            [item["id"] for item in DEFAULT_RETRIEVER.search(query)],
        )

    def test_invalid_document_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.json"
            path.write_text('[{"id":"BROKEN"}]', encoding="utf-8")
            with self.assertRaises(KnowledgeBaseError):
                load_documents(path)


class IngestionTests(unittest.TestCase):
    def test_source_build_is_stable_and_carries_hashes(self):
        first = build_knowledge_base(ASSISTANT / "data" / "source_docs")
        second = build_knowledge_base(ASSISTANT / "data" / "source_docs")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 8)
        self.assertEqual(len(first[0]["content_sha256"]), 64)

    def test_duplicate_document_ids_are_rejected(self):
        sample = (ASSISTANT / "data" / "source_docs" / "OPS-001.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "a.md").write_text(sample, encoding="utf-8")
            (source / "b.md").write_text(sample, encoding="utf-8")
            with self.assertRaises(IngestionError):
                build_knowledge_base(source)


if __name__ == "__main__":
    unittest.main()
