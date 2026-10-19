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


def _remove_stale(output: Path, source: Path) -> None:
    """Delete an older PDF so a failed render cannot be mistaken for a good one."""
    try:
        if output.is_file() and output.resolve() != source.resolve():
            output.unlink()
            print(f"removed old {output}", file=sys.stderr)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="resume source file (.toml)")
    parser.add_argument("output", type=Path, help="PDF to write")
    parser.add_argument("--master", type=Path, default=MASTER, help="master file for the checks")
    parser.add_argument("--no-master", action="store_true", help="skip checks that need the master file")
    args = parser.parse_args()
    source_read = False  # once the source was read, a failure removes an older PDF

    def fail(message: str) -> int:
        print(f"render failed: {message}", file=sys.stderr)
        if source_read:
            _remove_stale(args.output, args.source)
        return 1

    try:
        failures, warnings = check_source(
            args.source, args.master, use_master=not args.no_master
        )
        source_read = True
        for message in [*warnings, *failures]:
            print(message, file=sys.stderr)
        if failures:
            return fail(f"{len(failures)} check(s) failed, no PDF written")
        with args.source.open("rb") as f:
            data = tomllib.load(f)
        pdf = typst.compile(
            str(TEMPLATE),
            sys_inputs={"resume": json.dumps(data)},
            ignore_system_fonts=True,
        )
        pages, missing, unprinted = check_pdf(pdf, data)
        if unprinted:
            more = f" (and {len(unprinted) - 1} more)" if len(unprinted) > 1 else ""
            return fail(
                f"field {unprinted[0]} is not printed by the template{more}, no PDF written"
            )
        if missing:
            more = f" (and {len(missing) - 1} more)" if len(missing) > 1 else ""
            return fail(
                f"text not readable in the PDF: {missing[0][:60]!r}{more}, no PDF written"
            )
        if pages >= 3:
            return fail(f"{pages} pages (2 max), no PDF written")
        args.output.write_bytes(pdf)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, TypeError, typst.TypstError) as e:
        return fail(str(e))
    print(f"wrote {args.output} ({pages} page{'s' if pages > 1 else ''}, all text readable)")
    if pages == 2:
        print("warning: 2 pages (1 preferred)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
