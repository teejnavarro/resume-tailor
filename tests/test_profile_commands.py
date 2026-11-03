"""Guards for the public /linkedin and /negotiate command files (RT-012, RT-013)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import checks  # noqa: E402

COMMANDS = ROOT / ".claude" / "commands"
NAMES = ["linkedin", "negotiate"]
PESO = chr(0x20b1)


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
