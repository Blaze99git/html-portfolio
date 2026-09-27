"""Validate and compile the fictional Markdown source library into JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
DEFAULT_SOURCE = ROOT / "data" / "source_docs"
DEFAULT_OUTPUT = ROOT / "data" / "knowledge_base.json"
ALLOWED_CATEGORIES = {"operations", "quality", "maintenance", "data"}
ALLOWED_FIELDS = {"id", "title", "category", "section", "revision"}
ID_PATTERN = re.compile(r"^[A-Z]{3}-\d{3}$")


class IngestionError(ValueError):
    """Raised when an input document does not match the source contract."""


def parse_document(path: Path, source_root: Path = DEFAULT_SOURCE) -> dict[str, Any]:
    """Parse one Markdown document with a small, strict metadata header."""
    raw = path.read_text(encoding="utf-8")
    if len(raw.encode("utf-8")) > 64_000:
        raise IngestionError(f"{path.name}: source exceeds the 64 KB limit")
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise IngestionError(f"{path.name}: expected a metadata block delimited by ---")
    metadata_text, body = raw[4:].split("\n---\n", 1)
    metadata: dict[str, str] = {}
    for line_number, line in enumerate(metadata_text.splitlines(), start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise IngestionError(f"{path.name}:{line_number}: expected key: value")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key not in ALLOWED_FIELDS:
            raise IngestionError(f"{path.name}:{line_number}: unsupported metadata field {key!r}")
        if key in metadata:
            raise IngestionError(f"{path.name}:{line_number}: duplicate metadata field {key!r}")
        metadata[key] = value

    missing = ALLOWED_FIELDS - metadata.keys()
    if missing:
        raise IngestionError(f"{path.name}: missing metadata fields: {', '.join(sorted(missing))}")
    if not ID_PATTERN.fullmatch(metadata["id"]):
        raise IngestionError(f"{path.name}: id must match OPS-000 format")
    if metadata["category"] not in ALLOWED_CATEGORIES:
        raise IngestionError(f"{path.name}: unsupported category {metadata['category']!r}")
    if not metadata["title"] or len(metadata["title"]) > 120:
        raise IngestionError(f"{path.name}: title must be between 1 and 120 characters")
    if not metadata["section"] or not metadata["revision"]:
        raise IngestionError(f"{path.name}: section and revision cannot be empty")

    body = " ".join(part.strip() for part in body.splitlines() if part.strip())
    if len(body) < 40 or len(body) > 6_000:
        raise IngestionError(f"{path.name}: body must be between 40 and 6,000 characters")
    try:
        source_path = path.resolve().relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        raise IngestionError(f"{path.name}: source must be within {source_root}") from exc

    return {
        **metadata,
        "source_path": source_path,
        "content_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "text": body,
    }


def build_knowledge_base(source_dir: Path = DEFAULT_SOURCE) -> list[dict[str, Any]]:
    """Read Markdown sources in stable order and reject duplicate IDs."""
    paths = sorted(source_dir.rglob("*.md"))
    if not paths:
        raise IngestionError(f"no Markdown documents found under {source_dir}")
    if len(paths) > 500:
        raise IngestionError("the demo knowledge base is limited to 500 source documents")
    documents = [parse_document(path, source_dir) for path in paths]
    seen: set[str] = set()
    for document in documents:
        if document["id"] in seen:
            raise IngestionError(f"duplicate document id: {document['id']}")
        seen.add(document["id"])
    return documents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="directory of Markdown sources")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="generated JSON knowledge base")
    args = parser.parse_args()
    try:
        documents = build_knowledge_base(args.source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, IngestionError) as exc:
        print(f"ingestion failed: {exc}", file=sys.stderr)
        return 1
    print(f"Built {len(documents)} documents at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
