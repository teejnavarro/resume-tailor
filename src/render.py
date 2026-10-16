"""Render a resume source file (TOML) to a Harvard-style PDF."""
import argparse
import json
import sys
import tomllib
from pathlib import Path

import typst

TEMPLATE = Path(__file__).with_name("resume.typ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="resume source file (.toml)")
    parser.add_argument("output", type=Path, help="PDF to write")
    args = parser.parse_args()
    try:
        with args.source.open("rb") as f:
            data = tomllib.load(f)
        pdf = typst.compile(
            str(TEMPLATE),
            sys_inputs={"resume": json.dumps(data)},
            ignore_system_fonts=True,
        )
        args.output.write_bytes(pdf)
    except (OSError, tomllib.TOMLDecodeError, typst.TypstError) as e:
        print(f"render failed: {e}", file=sys.stderr)
        return 1
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
