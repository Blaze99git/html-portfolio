"""Assemble the browser-safe static site, excluding server and test code."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = ["index.html", "activity.html", "site-config.js", ".nojekyll", "robots.txt", "sitemap.xml", "404.html", "about.html", "contact.html"]
PROJECT_FILES = {
    "operations-monitor": ["index.html", "app.js", "README.md", "sql/schema.sql", "sql/queries.sql", "sql/sample_data.sql"],
    "industrial-knowledge-assistant": ["index.html", "app.js", "README.md", "data/knowledge_base.json"],
}


def build_site(output: Path) -> Path:
    """Build to a new or empty output directory without deleting user files."""
    output = output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("build output must be outside the source repository")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"build output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    for name in ROOT_FILES:
        shutil.copy2(ROOT / name, output / name)
    shutil.copytree(ROOT / "assets", output / "assets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "data", output / "data", dirs_exist_ok=True)
    for project, files in PROJECT_FILES.items():
        source_dir = ROOT / "projects" / project
        target_dir = output / "projects" / project
        for name in files:
            source = source_dir / name
            target = target_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        if project == "industrial-knowledge-assistant":
            shutil.copytree(source_dir / "data" / "source_docs", target_dir / "data" / "source_docs", dirs_exist_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new or empty build directory")
    args = parser.parse_args()
    destination = build_site(args.output)
    print(f"Built static site at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
