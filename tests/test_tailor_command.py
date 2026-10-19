"""Guards for the public /tailor command file (RT-008)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / ".claude" / "commands" / "tailor.md"


def test_tailor_command_shape():
    text = COMMAND.read_text(encoding="utf-8")
    front = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert front, "frontmatter must start at line 1"
    keys = [line.split(":", 1)[0] for line in front.group(1).splitlines()]
    assert keys == ["description", "argument-hint"]
    assert text.rstrip().endswith("$ARGUMENTS")


def test_tailor_command_follows_the_playbook_and_stops_at_step_4():
    text = COMMAND.read_text(encoding="utf-8")
    assert "`docs/TAILORING.md`" in text
    assert (ROOT / "docs" / "TAILORING.md").exists()
    assert "Step 4 is a hard stop." in text
    assert "until the owner has explicitly approved the checkpoint" in text


def test_tailor_command_only_writes_the_notion_tracker_row():
    text = COMMAND.read_text(encoding="utf-8")
    assert "Never apply, send messages" in text
    assert text.count("exception") == 1
    assert "The one exception: adding or updating this job's row in the Notion tracker database" in text
