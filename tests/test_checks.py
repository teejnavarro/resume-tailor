"""Tests for src/checks.py and its use by render.py (RT-004).

A fictional master file and scratch sources live in pytest's tmp_path.
docs/STYLE.md is the real one, to prove banned words are read at run time.
No real personal data and no literal peso sign appear in this file.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import checks  # noqa: E402

PESO = "\u20b1"
CHECKS_CLI = ROOT / "src" / "checks.py"
RENDER = ROOT / "src" / "render.py"
FAKE_PHONE = "+1 555 010 9999"

MASTER_TEXT = """# MASTER

## Contact
- Fake Person
- Faketown, Nowhere 0000
- +1 555 010 9999
- fake@example.com

## Job-search preferences (private)
- Salary floor 90,000

## Experience
- Set up 14 phones that cut testing by 79% for 1,200+ segments
  - Fact: it took 2 hours
- A plain line about interview only with 77

## Skills
- Data: SQL
- Never list in Skills: Python, DAX, C++
"""

SOURCE_LINES = [
    "[contact]",
    'name = "Fake Person"',
    f'phone = "{FAKE_PHONE}"',
    "",
    "[[experience]]",
    'company = "Acme"',
    "  [[experience.roles]]",
    '  title = "Analyst"',
    "  bullets = [",
    '    "Set up 14 phones",',
    '    "Cut testing by 79% for 1,200+ segments",',
    "  ]",
    "",
    "[[skills]]",
    'category = "Data"',
    'items = ["SQL"]',
    "",
]


@pytest.fixture
def master(tmp_path):
    path = tmp_path / "fake-master.md"
    path.write_text(MASTER_TEXT, encoding="utf-8")
    return path


def make_source(tmp_path, extra_bullet=None, skills=None):
    """Write the passing source, optionally adding a bullet or new skills."""
    lines = list(SOURCE_LINES)
    if extra_bullet:
        lines.insert(lines.index("  ]"), f'    "{extra_bullet}",')
    if skills:
        lines[lines.index('items = ["SQL"]')] = f"items = {skills}"
    path = tmp_path / "source.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def line_of(path, needle):
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if needle in line:
            return n
    raise AssertionError(needle)


def run_source(path, master):
    return checks.check_source(path, master_path=master)


def rules(failures):
    return [(f.line_no, f.rule, f.detail) for f in failures]


def run_cli(script, *args, cwd):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )


def test_passing_source(tmp_path, master):
    failures, warnings = run_source(make_source(tmp_path), master)
    assert failures == [] and warnings == []


def test_banned_word_case_insensitive(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Leveraged the data")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "Leveraged"), "banned-word", "leveraged")]


def test_banned_phrase_with_different_spacing(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Showed a Proven  Track Record")
    failures, _ = run_source(path, master)
    assert [f.rule for f in failures] == ["banned-word"]


def test_banned_words_read_from_style_file_at_run_time(tmp_path, master):
    style = tmp_path / "STYLE.md"
    text = (ROOT / "docs" / "STYLE.md").read_text(encoding="utf-8")
    added = text.replace("spearheaded ·", "spearheaded · zorbify ·", 1)
    assert added != text
    style.write_text(added, encoding="utf-8")
    assert "zorbify" in checks.banned_terms(style)
    path = make_source(tmp_path, extra_bullet="Zorbify the reports")
    failures, _ = checks.check_source(path, master_path=master, style_path=style)
    assert rules(failures) == [(line_of(path, "Zorbify"), "banned-word", "zorbify")]
    plain, _ = run_source(path, master)
    assert plain == []


def test_banned_terms_parsed_from_real_style_file():
    terms = checks.banned_terms()
    for expected in ["spearheaded", "leveraging", "seamless", "drove", "stakeholders", "proven track record"]:
        assert expected in terms


def test_untraced_number(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Saved 987 hours")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "987"), "untraced-number", "987")]


def test_number_only_in_indented_fact_is_untraced(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Fixed it in 2 hours")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "2 hours"), "untraced-number", "2")]


def test_salary_number_is_untraced(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Earned 90,000 a year")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "90,000"), "untraced-number", "90000")]


def test_number_on_interview_only_line_is_untraced(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Handled 77 cases")
    failures, _ = run_source(path, master)
    assert [f.detail for f in failures] == ["77"]


def test_contact_numbers_are_ignored(tmp_path, master):
    failures, _ = run_source(make_source(tmp_path), master)
    assert failures == []


def test_blocked_skill_in_skills_section(tmp_path, master):
    path = make_source(tmp_path, skills='["SQL", "DAX", "C++"]')
    failures, _ = run_source(path, master)
    row = line_of(path, "items")
    assert rules(failures) == [(row, "blocked-skill", "DAX"), (row, "blocked-skill", "C++")]


def test_blocked_skill_allowed_inside_a_bullet(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Built a Python app with DAX notes")
    failures, _ = run_source(path, master)
    assert failures == []


def test_peso_amount_fails(tmp_path, master):
    path = make_source(tmp_path, extra_bullet=f"Caught a {PESO}150 offer")
    failures, _ = run_source(path, master)
    assert (line_of(path, PESO), "peso-amount") in [(f.line_no, f.rule) for f in failures]


def test_missing_master_warns_and_keeps_other_checks(tmp_path):
    path = make_source(tmp_path, extra_bullet=f"Leveraged {PESO}5 gains of 987")
    failures, warnings = checks.check_source(path, master_path=tmp_path / "nope.md")
    assert len(warnings) == 1 and "no master file" in warnings[0]
    assert sorted(f.rule for f in failures) == ["banned-word", "peso-amount"]


def test_no_master_flag_skips_master_checks(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Saved 987 hours")
    failures, warnings = checks.check_source(path, master_path=master, use_master=False)
    assert failures == [] and warnings == []


def test_cli_failure_names_file_line_and_rule(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Saved 987 hours")
    result = run_cli(CHECKS_CLI, path, "--master", master, cwd=tmp_path)
    assert result.returncode == 1
    assert f"{path}:{line_of(path, '987')}: untraced-number: 987" in result.stderr


def test_render_passes_and_writes_pdf(tmp_path, master):
    path = make_source(tmp_path)
    out = tmp_path / "out.pdf"
    result = run_cli(RENDER, path, out, "--master", master, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_render_refuses_failing_source(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Leveraged the data")
    out = tmp_path / "out.pdf"
    result = run_cli(RENDER, path, out, "--master", master, cwd=tmp_path)
    assert result.returncode == 1
    assert f"{path}:{line_of(path, 'Leveraged')}: banned-word" in result.stderr
    assert "no PDF written" in result.stderr
    assert not out.exists()


# --- staged-files guard ---------------------------------------------------


def run_staged(repo, master):
    return run_cli(CHECKS_CLI, "--staged", "--master", master, cwd=repo)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    return path


def stage(repo, name, text):
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True, capture_output=True)


def test_staged_clean_file_passes(repo, master):
    stage(repo, "notes.txt", "nothing private here\n")
    result = run_staged(repo, master)
    assert result.returncode == 0, result.stderr
    assert "checks passed" in result.stdout


def test_staged_private_path_fails(repo, master):
    stage(repo, "master-resume.md", "anything\n")
    result = run_staged(repo, master)
    assert result.returncode == 1
    assert "master-resume.md:0: private-path" in result.stderr


def test_staged_applications_folder_fails(repo, master):
    stage(repo, "applications/job/resume.toml", "x = 1\n")
    assert "private-path" in run_staged(repo, master).stderr


def test_staged_phone_with_different_spacing_fails(repo, master):
    stage(repo, "a.txt", "ok\ncall 555-010-9999 today\n")
    result = run_staged(repo, master)
    assert result.returncode == 1
    assert "a.txt:2: private-phone" in result.stderr


def test_staged_address_fails(repo, master):
    stage(repo, "a.txt", "I live in FAKETOWN.\n")
    result = run_staged(repo, master)
    assert result.returncode == 1
    assert "a.txt:1: private-address" in result.stderr


def test_staged_peso_amount_fails(repo, master):
    stage(repo, "a.txt", f"cost {PESO}20\n")
    result = run_staged(repo, master)
    assert result.returncode == 1
    assert "a.txt:1: peso-amount" in result.stderr


def test_staged_without_master_still_checks_paths_and_peso(repo, tmp_path):
    stage(repo, "a.txt", f"cost {PESO}20\n")
    result = run_staged(repo, tmp_path / "missing.md")
    assert result.returncode == 1
    assert "warning: no master file" in result.stderr
    assert "peso-amount" in result.stderr
