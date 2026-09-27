"""Validate static-site file targets and in-page anchors without dependencies."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.image_errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element_id = attrs.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "img" and not attrs.get("alt"):
            self.image_errors.append(attrs.get("src", "(missing src)"))
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"script", "img"} else None
        if attribute and attrs.get(attribute):
            self.targets.append((attribute, attrs[attribute]))


def read_markup(path: Path) -> Markup:
    parser = Markup()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def check_site(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    pages = sorted(root.rglob("*.html"))
    checked_targets = 0
    for page in pages:
        markup = read_markup(page)
        relative_page = page.relative_to(root)
        for identifier in sorted(markup.duplicate_ids):
            failures.append(f"{relative_page}: duplicate id #{identifier}")
        for source in markup.image_errors:
            failures.append(f"{relative_page}: image has no alt text: {source}")
        for attribute, value in markup.targets:
            url = urlparse(value)
            if url.scheme or url.netloc or value.startswith("//") or value == "#":
                continue
            target = (page.parent / url.path).resolve() if url.path else page.resolve()
            if root.resolve() not in target.parents and target != root.resolve():
                failures.append(f"{relative_page}: {attribute} escapes site root: {value}")
                continue
            if not target.exists():
                failures.append(f"{relative_page}: missing {attribute} target: {value}")
                continue
            checked_targets += 1
            if url.fragment and target.suffix == ".html":
                target_markup = read_markup(target)
                if url.fragment not in target_markup.ids:
                    failures.append(f"{relative_page}: missing fragment target: {value}")

    if not pages:
        failures.append("no HTML pages found")
    if failures:
        print("Site validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return failures
    print(f"Site validation passed: {len(pages)} pages, {checked_targets} local file targets, unique anchors, image alt text.")
    return []


if __name__ == "__main__":
    raise SystemExit(1 if check_site() else 0)
