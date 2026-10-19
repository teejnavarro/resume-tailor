"""Render a resume source file (TOML) to a Harvard-style PDF."""
import argparse
import json
import sys
import tomllib
from pathlib import Path

import typst
from checks import MASTER, check_source
from pdf_checks import check_pdf

TEMPLATE = Path(__file__).with_name("resume.typ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="resume source file (.toml)")
    parser.add_argument("output", type=Path, help="PDF to write")
    parser.add_argument("--master", type=Path, default=MASTER, help="master file for the checks")
    parser.add_argument("--no-master", action="store_true", help="skip checks that need the master file")
    args = parser.parse_args()
    try:
        failures, warnings = check_source(
            args.source, args.master, use_master=not args.no_master
        )
        for message in [*warnings, *failures]:
            print(message, file=sys.stderr)
        if failures:
            print(
                f"render failed: {len(failures)} check(s) failed, no PDF written",
                file=sys.stderr,
            )
            return 1
        with args.source.open("rb") as f:
            data = tomllib.load(f)
        pdf = typst.compile(
            str(TEMPLATE),
            sys_inputs={"resume": json.dumps(data)},
            ignore_system_fonts=True,
        )
        pages, missing = check_pdf(pdf, data)
        if missing:
            more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
            print(
                f"render failed: text not readable in the PDF: {missing[0][:60]!r}{more}",
                file=sys.stderr,
            )
            return 1
        if pages >= 3:
            print(f"render failed: {pages} pages (2 max), no PDF written", file=sys.stderr)
            return 1
        args.output.write_bytes(pdf)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, TypeError, typst.TypstError) as e:
        print(f"render failed: {e}", file=sys.stderr)
        return 1
    print(f"wrote {args.output} ({pages} page{'s' if pages > 1 else ''}, all text readable)")
    if pages == 2:
        print("warning: 2 pages (1 preferred)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
