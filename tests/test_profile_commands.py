"""Guards for the public /linkedin and /negotiate command files (RT-012, RT-013)."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import checks  # noqa: E402

COMMANDS = ROOT / ".claude" / "commands"
NAMES = ["linkedin", "negotiate"]
PESO = chr(0x20b1)
# Pay written without a peso sign: PHP 50,000, P50000, 50k, USD 900, $900.
AMOUNT = re.compile(
    r"(?i)\b(?:php|usd|p)\s?\d|\$\s?\d|\b\d{1,3}k\b|\b\d{1,3}(?:,\d{3})+\b|\b\d{4,}\b"
)


def read(name):
    return (COMMANDS / f"{name}.md").read_text(encoding="utf-8")


def frontmatter(text):
    front = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert front, "frontmatter must start at line 1"
    pairs = []
    for line in front.group(1).splitlines():
        key, _, value = line.partition(":")
        pairs.append((key, value.strip()))
    return pairs


def as_yaml_string(value):
    """Stdlib stand-in for a strict YAML read: return the string, or fail."""
    if value.startswith('"'):
        assert len(value) > 1 and value.endswith('"'), "unterminated quote"
        return value[1:-1]
    assert value, "empty value"
    assert value[0] not in "[]{}'&*!|>%@`#,", "unquoted value starts with a YAML indicator"
    assert ": " not in value and " #" not in value, "unquoted value holds ': ' or ' #'"
    return value


@pytest.mark.parametrize("name", NAMES)
def test_command_shape(name):
    text = read(name)
    pairs = frontmatter(text)
    assert [k for k, _ in pairs] == ["description", "argument-hint"]
    for _, value in pairs:
        assert as_yaml_string(value).strip()
    assert text.rstrip().endswith("$ARGUMENTS")
    assert PESO not in text


def test_the_yaml_rule_catches_the_two_known_mistakes():
    with pytest.raises(AssertionError):
        as_yaml_string("Prepare a job offer: total pay")
    with pytest.raises(AssertionError):
        as_yaml_string("[target roles, and a link]")
    assert as_yaml_string('"Prepare a job offer: total pay"') == "Prepare a job offer: total pay"


def test_linkedin_writes_a_private_file_and_never_edits_the_profile():
    text = read("linkedin")
    assert "`notes/linkedin.md`" in text
    assert "Never click edit, save, post, message, connect" in text
    assert "Never use a write action on any connector or website." in text


def test_negotiate_stops_before_writing_and_never_sends():
    text = read("negotiate")
    assert "`offer.md`" in text
    assert "Step 3, HARD STOP." in text
    assert "Do not write `offer.md` until the owner has approved the amounts." in text
    assert "Never send anything." in text
    assert "write action on any connector or website" in text


def test_private_folders_stay_blocked_from_commits():
    assert "notes/" in checks.PRIVATE_PREFIXES
    assert "applications/" in checks.PRIVATE_PREFIXES


def is_git_ignored(path):
    run = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    assert run.returncode in (0, 1), "git check-ignore failed"
    return run.returncode == 0


@pytest.mark.parametrize("path", ["notes/linkedin.md", "applications/2026-01-01_acme_analyst/offer.md"])
def test_private_output_files_are_git_ignored(path):
    assert is_git_ignored(path)


def test_the_ignore_check_can_see_a_public_file():
    assert not is_git_ignored("docs/not-private.md")


@pytest.mark.parametrize("name", NAMES)
def test_command_holds_no_pay_amounts(name):
    text = read(name).replace("2,600 characters", "")  # LinkedIn's About limit, not pay
    assert AMOUNT.findall(text) == []


@pytest.mark.parametrize("amount", ["PHP 50,000", "php50000", "P50,000", "50k", "USD 900", "$900", "50,000", "50000"])
def test_the_amount_rule_catches_pay_written_without_a_peso_sign(amount):
    assert AMOUNT.search(f"Ask for {amount} a month.")


def test_linkedin_facts_come_only_from_resume_ready_lines():
    text = read("linkedin")
    assert "Use only resume-ready master lines: top-level bullets, headings and plain lines." in text
    assert (
        "Never use indented sub-bullets, `>` note lines, the contact section, job-search preferences, pay, "
        "or any line marked interview only." in text
    )
    assert "Never print the owner's preferences." in text
    assert "Add contact details only if the owner asks." in text


def test_linkedin_applies_the_resume_rules():
    text = read("linkedin")
    assert "STYLE.md banned words and honest labels apply." in text
    assert "Skills on the master's never-list stay out." in text
    assert "No peso amounts." in text
    assert "Every number traces to resume-ready master text." in text


def test_linkedin_draft_limits_reports_and_overwrite_rule():
    text = read("linkedin")
    assert "Headline, 220 characters at most." in text
    assert "About, 2,600 characters at most." in text
    assert "Consistency report: compare titles and dates" in text
    assert "Flag differences and never change them." in text
    assert "Public exposure flag:" in text
    assert "List every line that holds an internal figure or an internal tool name" in text
    assert "If that file exists, ask before overwriting it." in text


def test_negotiate_reads_the_whole_master_file():
    text = read("negotiate")
    assert "- `master-resume.md`: the whole file." in text
    assert "the employee and contractor floors" in text
    assert "the justification, from master facts only" in text


def test_negotiate_covers_philippine_pay_items_and_both_floors():
    text = read("negotiate")
    for item in ["HMO", "13th month", "SSS", "PhilHealth", "Pag-IBIG"]:
        assert item in text
    assert "Pick the employee or contractor floor from the master." in text
    assert "who pays contributions and taxes" in text


def test_negotiate_researches_the_market_only_on_request_from_free_sources():
    text = read("negotiate")
    assert "Do market research only if the owner asks for it for this offer." in text
    assert "Use free sources and cite them." in text


def test_negotiate_money_and_honesty_rules():
    text = read("negotiate")
    assert "Show yearly gross only." in text
    assert "Give take-home only if the owner asks, labelled as an estimate." in text
    assert "Never invent a competing offer." in text
    assert "Never volunteer the owner's current salary." in text
    assert "Use no unsourced statistics." in text
    assert "The owner sends every message." in text


def test_negotiate_offer_file_has_fallbacks_and_written_terms():
    text = read("negotiate")
    assert "signing bonus, earlier salary review, HMO dependents, allowances, leave, work setup, start date" in text
    assert "for contracts, payment terms, currency and notice" in text
    assert "a reminder to get the final terms in writing" in text
