#!/usr/bin/env python3
"""Check package entries and required frontmatter text; not a full YAML validator."""

import argparse
import re
import sys
from pathlib import Path


def check_skill(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"cannot read UTF-8 SKILL.md: {exc}"]
    if not lines or lines[0] != "---":
        return ["missing opening frontmatter delimiter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return ["missing closing frontmatter delimiter"]

    # Inspect top-level keys only, never examples in the Markdown body.
    metadata = lines[1:end]
    errors = []
    for field in ("name", "description"):
        entries = [
            (index, line[len(field) + 1 :].strip())
            for index, line in enumerate(metadata)
            if line.startswith(field + ":")
        ]
        if len(entries) != 1:
            errors.append(f"expected exactly one top-level {field} field")
            continue
        index, value = entries[0]
        # These checks cover the repository's plain, quoted and block text
        # forms. They do not attempt to parse arbitrary YAML or other fields.
        if value.startswith(("'", '"')):
            quoted = re.fullmatch(r"(['\"])(.*?)\1(?:\s+#.*)?", value)
            valid = quoted is not None and bool(quoted.group(2).strip())
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
            if re.fullmatch(r"[|>][+-]?", value):
                continuation = []
                for line in metadata[index + 1 :]:
                    if line and not line[0].isspace():
                        break
                    continuation.append(line)
                valid = bool("\n".join(continuation).strip())
            else:
                valid = (
                    bool(value)
                    and not value.startswith(("#", "[", "{", "&", "*", "!"))
                    and value.lower()
                    not in ("null", "~", "true", "false", "yes", "no", "on", "off")
                    and not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value)
                )
        if not valid:
            errors.append(f"{field} must contain plain, quoted or block text")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to this script's repository)",
    )
    root = parser.parse_args().root.resolve()
    skills = root / "skills"
    if not skills.is_dir():
        print(f"ERROR: missing skills directory: {skills}", file=sys.stderr)
        return 1
    paths = [root / "SKILL.md"] + [
        directory / "SKILL.md"
        for directory in sorted(skills.iterdir())
        if directory.is_dir() and not directory.name.startswith(".")
    ]
    failures = 0
    for path in paths:
        for error in check_skill(path):
            failures += 1
            print(f"{path.relative_to(root)}: {error}", file=sys.stderr)
    if failures:
        print(
            f"FAIL: {failures} error(s) in {len(paths)} skill packages.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: checked {len(paths)} skill packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
