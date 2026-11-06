#!/usr/bin/env python3
"""Check that the front matter of every page parses as YAML.

    python3 -I tools/front-matter.py docs

MkDocs reads the block between the two "---" lines as YAML. A value holding a colon followed by a
space ("for PHP: signing") or a backslash ("Cose\\...Tag") is not a plain scalar, so the block fails
to parse and is rendered as the content of the page: the description comes out as the first heading
and the page loses its title in the navigation.

"mkdocs build --strict" does not catch this, which is why it is checked here. Quote the value with
single quotes, doubling any inner one; double quotes do not work, a backslash being an escape there.

This belongs in Spomky-Labs/docs/tools with the other shared tools once the other sites adopt it.
"""

import re
import sys
from pathlib import Path

import yaml

FRONT_MATTER = re.compile(r"^---\n(.*?\n)---\n", re.S)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2

    pages = sorted(Path(sys.argv[1]).rglob("*.md"))
    if not pages:
        print(f"No page found in {sys.argv[1]}", file=sys.stderr)
        return 1

    failures = 0
    for page in pages:
        match = FRONT_MATTER.match(page.read_text(encoding="utf-8"))
        if match is None:
            continue
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as error:
            print(f"{page}: {str(error).splitlines()[0]}", file=sys.stderr)
            failures += 1
            continue
        if not isinstance(data, dict):
            print(f"{page}: the front matter is not a mapping", file=sys.stderr)
            failures += 1

    if failures:
        print(f"\n{failures} page(s) whose front matter does not parse; quote the value.", file=sys.stderr)
        return 1

    print(f"The front matter of {len(pages)} pages parses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
