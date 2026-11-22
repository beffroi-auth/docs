#!/usr/bin/env python3
"""Check that the navigation and the pages match, in both directions.

    python3 -I tools/nav.py mkdocs.yml

The navigation in mkdocs.yml is the table of contents of the site: a page that is not in it cannot be
reached from the sidebar, and an entry that names no page leads to a 404. "zensical build --strict"
validates links and anchors, not the navigation, which is why it is checked here.
"""

import sys
from pathlib import Path

import yaml


class _ConfigLoader(yaml.SafeLoader):
    """Reads mkdocs.yml without importing the Python objects its extensions name."""


_ConfigLoader.add_multi_constructor("tag:yaml.org,2002:python/", lambda loader, suffix, node: None)


def entries(nav) -> list[str]:
    paths = []
    for item in nav:
        value = next(iter(item.values())) if isinstance(item, dict) else item
        if isinstance(value, list):
            paths += entries(value)
        elif isinstance(value, str) and "://" not in value:
            paths.append(value)
    return paths


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2

    config_file = Path(sys.argv[1])
    config = yaml.load(config_file.read_text(encoding="utf-8"), Loader=_ConfigLoader)
    docs = config_file.parent / config.get("docs_dir", "docs")

    in_nav = entries(config.get("nav") or [])
    pages = {page.relative_to(docs).as_posix() for page in docs.rglob("*.md")}

    failures = 0
    for path in in_nav:
        if path not in pages:
            print(f"{config_file}: the navigation names {path}, which is not a page", file=sys.stderr)
            failures += 1
    for path in sorted(pages - set(in_nav)):
        print(f"{docs / path}: the page is not in the navigation", file=sys.stderr)
        failures += 1

    if failures:
        print(f"\n{failures} mismatch(es) between the navigation and the pages.", file=sys.stderr)
        return 1

    print(f"The navigation and the {len(pages)} pages match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
