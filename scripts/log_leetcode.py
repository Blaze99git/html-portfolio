"""Validate and upsert one public LeetCode practice entry."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "leetcode-log.json"
ALLOWED_STATUSES = {"solved", "attempted", "revisit"}


def parse_entry(values: argparse.Namespace) -> dict[str, str]:
    title = values.title.strip()
    if not title or len(title) > 160:
        raise ValueError("problem title must contain 1 to 160 characters")
    entry_date = values.date.strip() or datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    try:
        date.fromisoformat(entry_date)
    except ValueError as error:
        raise ValueError("date must use YYYY-MM-DD format") from error
    if values.status not in ALLOWED_STATUSES:
        raise ValueError("status must be solved, attempted, or revisit")
    url = values.url.strip()
    if url:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {"leetcode.com", "www.leetcode.com"}:
            raise ValueError("problem URL must be an HTTPS link on leetcode.com")
    reflection = values.reflection.strip()
    if len(reflection) > 400:
        raise ValueError("reflection must be 400 characters or fewer")
    if any(ord(character) < 32 and character not in "\n\t" for character in reflection):
        raise ValueError("reflection contains unsupported control characters")
    return {
        "date": entry_date,
        "title": title,
        "url": url,
        "status": values.status,
        "reflection": reflection,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def save_entry(entry: dict[str, str], path: Path = LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"entries": []}
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("practice log has an invalid structure")
    entries = [item for item in data["entries"] if not (
        isinstance(item, dict)
        and item.get("date") == entry["date"]
        and str(item.get("title", "")).casefold() == entry["title"].casefold()
    )]
    entries.append(entry)
    entries.sort(key=lambda item: (item.get("date", ""), item.get("title", "").casefold()), reverse=True)
    encoded = json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        temporary.write(encoded)
        temp_path = Path(temporary.name)
    temp_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=os.environ.get("STUDY_DATE", ""))
    parser.add_argument("--title", default=os.environ.get("STUDY_TITLE", ""))
    parser.add_argument("--url", default=os.environ.get("STUDY_URL", ""))
    parser.add_argument("--status", default=os.environ.get("STUDY_STATUS", "solved"))
    parser.add_argument("--reflection", default=os.environ.get("STUDY_REFLECTION", ""))
    args = parser.parse_args()
    try:
        entry = parse_entry(args)
        save_entry(entry)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(f"Saved public LeetCode log entry: {entry['date']} · {entry['title']} ({entry['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
