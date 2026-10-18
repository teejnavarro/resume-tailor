"""Content checks for resume sources, and a guard for staged files (RT-004).

Standard library only. Rules come from two places: docs/STYLE.md (banned
words) and the private master file (numbers, blocked skills, contact data).
The master file is read only to compare against, never printed.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "master-resume.md"
STYLE = ROOT / "docs" / "STYLE.md"
PESO = "\u20b1"

PRIVATE_PATHS = ("master-resume.md", "FOUNDRY.md")
PRIVATE_PREFIXES = ("applications/", "assets/source/", "notes/")
NEVER_LIST = "Never list in Skills:"
TABLE_RE = re.compile(r"^\[\[?([\w.]+)\]\]?")
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


class Failure(NamedTuple):
    path: str
    line_no: int
    rule: str
    detail: str

    def __str__(self):
        return f"{self.path}:{self.line_no}: {self.rule}: {self.detail}"


def _norm(text):
    return text.replace("’", "'")


def banned_terms(style_path=STYLE):
    """Banned words and phrases, read from the STYLE.md list at run time."""
    terms = []
    in_section = False
    for line in Path(style_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## Banned words"):
            in_section = True
            continue
        if in_section and (line.startswith("##") or line.startswith("Plain swaps")):
            break
        if in_section and "·" in line:
            for item in line.split("·"):
                item = re.sub(r"\(.*?\)", "", _norm(item))
                item = item.replace("…", "").replace("...", "")
                terms.extend(t.strip() for t in item.split("/") if t.strip())
    return terms


def master_lines(master_path):
    """Yield (line, is_private) for each master-file line."""
    section = ""
    for line in Path(master_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        private = (
            section == "contact"
            or section.startswith("job-search preferences")
            or line[:1].isspace()
            or "interview only" in line.lower()
            or line.startswith(">")
        )
        yield line, private


def master_regions(master_path):
    """Return (resume-ready text, list of skills that must never be listed)."""
    ready = []
    never = []
    for line, private in master_lines(master_path):
        if NEVER_LIST in line:
            never = [s.strip() for s in line.split(NEVER_LIST, 1)[1].split(",")]
            never = [s for s in never if s]
        if not private:
            ready.append(line)
    return "\n".join(ready), never


def numbers(text):
    return {n.replace(",", "").rstrip(".") for n in NUMBER_RE.findall(text)}


def word_re(term):
    body = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


def check_source(source_path, master_path=MASTER, style_path=STYLE, use_master=True):
    """Check a resume source file. Returns (failures, warnings)."""
    failures, warnings = [], []
    name = str(source_path)
    banned = [(t, word_re(t)) for t in banned_terms(style_path)]
    master_path = Path(master_path)
    have_master = use_master and master_path.exists()
    if have_master:
        ready_text, never = master_regions(master_path)
        known = numbers(ready_text)
        never = [(t, word_re(t)) for t in never]
    elif use_master:
        warnings.append(
            f"warning: no master file at {master_path}; number and skill checks skipped"
        )
    table = ""
    text = Path(source_path).read_text(encoding="utf-8")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        header = TABLE_RE.match(stripped)
        if header:
            table = header.group(1)
            continue
        if stripped.startswith("#"):
            continue
        line = _norm(raw)
        for term, pattern in banned:
            if pattern.search(line):
                failures.append(Failure(name, line_no, "banned-word", term))
        if PESO in line:
            failures.append(Failure(name, line_no, "peso-amount", "no peso amounts on a resume"))
        if not have_master:
            continue
        if table != "contact":
            for token in sorted(numbers(line)):
                if token not in known:
                    failures.append(Failure(name, line_no, "untraced-number", token))
        if table in ("skills", ""):
            for term, pattern in never:
                if pattern.search(line):
                    failures.append(Failure(name, line_no, "blocked-skill", term))
    return failures, warnings


def _contact_bullets(master_path):
    section = ""
    bullets = []
    for line in Path(master_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        elif section == "contact" and line.startswith("- "):
            bullets.append(line[2:].strip())
    return bullets


def _contact_patterns(master_path):
    """Regexes for the owner's phone and address, read from the master Contact."""
    phone = address = None
    for i, bullet in enumerate(_contact_bullets(master_path)):
        digits = re.sub(r"\D", "", bullet)
        if len(digits) >= 9 and phone is None:
            phone = re.compile(r"[\s().-]*".join(digits[-10:]))
        elif (
            i > 0
            and address is None
            and "@" not in bullet
            and ".com" not in bullet
            and "/" not in bullet
            and len(digits) < 9
        ):
            address = word_re(bullet.split(",")[0].strip())
    return phone, address


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def check_staged(master_path=MASTER):
    """Scan staged files for personal data. Returns (failures, warnings)."""
    failures, warnings = [], []
    phone = address = None
    if Path(master_path).exists():
        phone, address = _contact_patterns(master_path)
    else:
        warnings.append(
            f"warning: no master file at {master_path}; phone and address checks skipped"
        )
    names = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    for path in filter(None, names.decode("utf-8").split("\0")):
        if path in PRIVATE_PATHS or path.startswith(PRIVATE_PREFIXES):
            failures.append(Failure(path, 0, "private-path", "private file must not be committed"))
            continue
        blob = _git("show", f":{path}").decode("utf-8", errors="ignore")
        for line_no, line in enumerate(blob.splitlines(), start=1):
            if PESO in line:
                failures.append(Failure(path, line_no, "peso-amount", "no peso amounts in tracked files"))
            if phone and phone.search(line):
                failures.append(Failure(path, line_no, "private-phone", "owner phone number"))
            if address and address.search(_norm(line)):
                failures.append(Failure(path, line_no, "private-address", "owner address"))
    return failures, warnings


def main(argv=None):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Run resume content checks.")
    parser.add_argument("source", nargs="?", type=Path, help="resume source file (.toml)")
    parser.add_argument("--staged", action="store_true", help="scan staged files for personal data")
    parser.add_argument("--master", type=Path, default=MASTER, help="master file to compare against")
    parser.add_argument("--no-master", action="store_true", help="skip checks that need the master file")
    args = parser.parse_args(argv)
    if bool(args.source) == args.staged:
        parser.error("give either a source file or --staged")
    if args.staged:
        failures, warnings = check_staged(args.master)
    else:
        try:
            failures, warnings = check_source(args.source, args.master, use_master=not args.no_master)
        except (OSError, UnicodeDecodeError) as e:
            print(f"checks failed: {e}", file=sys.stderr)
            return 1
    for message in [*warnings, *failures]:
        print(message, file=sys.stderr)
    if failures:
        print(f"checks failed: {len(failures)} problem(s)", file=sys.stderr)
        return 1
    print("checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
