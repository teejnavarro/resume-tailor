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


# --- QA edge cases ----------------------------------------------------------


def write_source(tmp_path, lines):
    path = tmp_path / "source.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_banned_phrase_with_ellipsis_and_curly_apostrophe(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Grew sales In Today\u2019s Fast-Paced market")
    failures, _ = run_source(path, master)
    assert rules(failures) == [
        (line_of(path, "Fast-Paced"), "banned-word", "in today's fast-paced")
    ]


def test_banned_word_not_matched_inside_a_longer_word(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Ran robustness tests on a data-driven model")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "robustness"), "banned-word", "data-driven")]


def test_number_tokens():
    text = "1,200+ users, 2023\u201325, 3.5 hours, 79%, ended in 10."
    assert checks.numbers(text) == {"1200", "2023", "25", "3.5", "79", "10"}


def test_decimal_number_must_match_exactly(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Cut 14.5 hours")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "14.5"), "untraced-number", "14.5")]


def test_number_range_checks_both_ends(tmp_path, master):
    passing = make_source(tmp_path, extra_bullet="Ran 14\u201379 tests")
    assert run_source(passing, master)[0] == []
    path = make_source(tmp_path, extra_bullet="Ran 14\u201380 tests")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "80"), "untraced-number", "80")]


def test_number_with_comma_matches_master_without_comma(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Reached 1200 segments")
    assert run_source(path, master)[0] == []


def test_number_on_quoted_master_line_is_untraced(tmp_path):
    master = tmp_path / "m.md"
    master.write_text("## Experience\n> note: 321 calls\n- Set up 14 phones\n", encoding="utf-8")
    path = make_source(tmp_path, extra_bullet="Took 321 calls")
    failures, _ = run_source(path, master)
    assert "321" in [f.detail for f in failures]


def test_interview_only_match_is_case_insensitive(tmp_path):
    master = tmp_path / "m.md"
    master.write_text("## Experience\n- Gap year (Interview Only): 321\n", encoding="utf-8")
    path = make_source(tmp_path, extra_bullet="Took 321 calls")
    assert "321" in [f.detail for f in run_source(path, master)[0]]


def test_comment_lines_are_skipped(tmp_path, master):
    lines = list(SOURCE_LINES)
    lines.insert(0, "# draft: leveraged 987 things")
    failures, _ = run_source(write_source(tmp_path, lines), master)
    assert failures == []


def test_line_numbers_are_one_based(tmp_path, master):
    path = write_source(tmp_path, ['summary = "Leveraged 987 tools"', *SOURCE_LINES])
    failures, _ = run_source(path, master)
    assert rules(failures) == [(1, "banned-word", "leveraged"), (1, "untraced-number", "987")]


def test_contact_numbers_ignored_only_inside_contact(tmp_path, master):
    lines = list(SOURCE_LINES)
    lines.insert(lines.index("[[experience]]") + 1, f'note = "{FAKE_PHONE}"')
    path = write_source(tmp_path, lines)
    failures, _ = run_source(path, master)
    assert {f.detail for f in failures} == {"1", "555", "010", "9999"}
    assert {f.line_no for f in failures} == {line_of(path, "note =")}


def test_peso_in_contact_table_still_fails(tmp_path, master):
    lines = list(SOURCE_LINES)
    lines.insert(1, f'rate = "{PESO}500"')
    failures, _ = run_source(write_source(tmp_path, lines), master)
    assert [(f.line_no, f.rule) for f in failures] == [(2, "peso-amount")]


def test_blocked_skill_case_insensitive(tmp_path, master):
    path = make_source(tmp_path, skills='["SQL", "dax"]')
    failures, _ = run_source(path, master)
    assert rules(failures) == [(line_of(path, "items"), "blocked-skill", "DAX")]


def test_blocked_skill_not_matched_inside_another_word(tmp_path, master):
    path = make_source(tmp_path, skills='["SQL", "C", "Daxter", "Pythonic"]')
    assert run_source(path, master)[0] == []


def test_blocked_skill_only_checked_inside_skills_tables(tmp_path, master):
    lines = [*SOURCE_LINES, "[[projects]]", 'name = "Python and DAX tool"']
    assert run_source(write_source(tmp_path, lines), master)[0] == []


def headline_source(tmp_path, headline):
    return write_source(tmp_path, [f'headline = "{headline}"', "", *SOURCE_LINES])


def test_clean_headline_passes(tmp_path, master):
    path = headline_source(tmp_path, "Analyst | SQL")
    assert run_source(path, master)[0] == []


def test_headline_with_banned_word_fails(tmp_path, master):
    path = headline_source(tmp_path, "Passionate analyst")
    failures, _ = run_source(path, master)
    assert [(f.line_no, f.rule) for f in failures] == [(1, "banned-word")]


def test_headline_with_untraced_number_fails(tmp_path, master):
    path = headline_source(tmp_path, "Analyst with 15 years of SQL")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(1, "untraced-number", "15")]


def test_headline_with_blocked_skill_fails(tmp_path, master):
    path = headline_source(tmp_path, "Analyst | SQL, DAX")
    failures, _ = run_source(path, master)
    assert rules(failures) == [(1, "blocked-skill", "DAX")]


def test_headline_with_peso_amount_fails(tmp_path, master):
    path = headline_source(tmp_path, f"Analyst who saved {PESO}150")
    failures, _ = run_source(path, master)
    assert (1, "peso-amount") in [(f.line_no, f.rule) for f in failures]


def test_render_refuses_failing_headline(tmp_path, master):
    path = headline_source(tmp_path, "Passionate analyst")
    out = tmp_path / "out.pdf"
    result = run_cli(RENDER, path, out, "--master", master, cwd=tmp_path)
    assert result.returncode == 1
    assert f"{path}:1: banned-word" in result.stderr
    assert "no PDF written" in result.stderr
    assert not out.exists()


def certs_source(tmp_path, certs_lines):
    return write_source(tmp_path, [*certs_lines, "", *SOURCE_LINES])


def test_blocked_skill_in_one_line_certifications_fails(tmp_path, master):
    path = certs_source(tmp_path, ['certifications = ["SQL Basics", "DAX Fundamentals"]'])
    failures, _ = run_source(path, master)
    assert rules(failures) == [(1, "blocked-skill", "DAX")]


def test_blocked_skill_in_multi_line_certifications_fails_on_item_line(tmp_path, master):
    path = certs_source(tmp_path, ["certifications = [", '  "SQL Basics",', '  "C++ Essentials",', "]"])
    failures, _ = run_source(path, master)
    assert rules(failures) == [(3, "blocked-skill", "C++")]


def test_clean_certifications_pass(tmp_path, master):
    path = certs_source(tmp_path, ['certifications = ["SQL Basics", "Data Handling"]'])
    assert run_source(path, master)[0] == []


def test_never_list_parsing(tmp_path):
    master = tmp_path / "m.md"
    master.write_text("## Skills\n- Never list in Skills:  Python , ,C++,  A/B \n", encoding="utf-8")
    _, never = checks.master_regions(master)
    assert never == ["Python", "C++", "A/B"]


def test_cli_passing_source(tmp_path, master):
    result = run_cli(CHECKS_CLI, make_source(tmp_path), "--master", master, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "checks passed" in result.stdout


@pytest.mark.parametrize("args", [[], ["x.toml", "--staged"]])
def test_cli_needs_exactly_one_of_source_or_staged(tmp_path, args):
    result = run_cli(CHECKS_CLI, *args, cwd=tmp_path)
    assert result.returncode == 2
    assert "give either a source file or --staged" in result.stderr


@pytest.mark.parametrize("script", [CHECKS_CLI, RENDER])
def test_non_utf8_source_fails_without_traceback(tmp_path, script):
    path = tmp_path / "bad.toml"
    path.write_bytes(b'title = "Caf\xe9"\n')
    args = [path] if script == CHECKS_CLI else [path, tmp_path / "out.pdf"]
    result = run_cli(script, *args, "--no-master", cwd=tmp_path)
    assert result.returncode == 1
    assert "failed:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "out.pdf").exists()


def test_render_missing_master_warns_and_still_renders(tmp_path):
    path = make_source(tmp_path)
    out = tmp_path / "out.pdf"
    result = run_cli(RENDER, path, out, "--master", tmp_path / "nope.md", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "warning: no master file" in result.stderr
    assert out.exists()


def test_render_refuses_untraced_number(tmp_path, master):
    path = make_source(tmp_path, extra_bullet="Saved 987 hours")
    out = tmp_path / "out.pdf"
    result = run_cli(RENDER, path, out, "--master", master, cwd=tmp_path)
    assert result.returncode == 1
    assert f"{path}:{line_of(path, '987')}: untraced-number: 987" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize(
    "name",
    ["FOUNDRY.md", "notes/idea.md", "assets/source/old.pdf", "applications/TRACKER.md", ".gsd/x-log.md", "backlog/RT-001.md"],
)
def test_staged_private_paths_fail(repo, master, name):
    stage(repo, name, "x\n")
    result = run_staged(repo, master)
    assert result.returncode == 1
    assert f"{name}:0: private-path" in result.stderr


@pytest.mark.parametrize(
    "text",
    ["5550109999", "+1-555-010-9999", "tel 555 0109999", "(555) 010-9999", "555.010.9999", "+1 (555) 010 9999", "555  010 - 9999"],
)
def test_staged_phone_variants_fail(repo, master, text):
    stage(repo, "a.txt", f"{text}\n")
    assert "a.txt:1: private-phone" in run_staged(repo, master).stderr


def test_staged_address_needs_whole_word(repo, master):
    stage(repo, "a.txt", "Faketownship is a made-up word\n")
    result = run_staged(repo, master)
    assert result.returncode == 0, result.stderr


def test_staged_guard_scans_staged_content_not_working_tree(repo, master):
    stage(repo, "a.txt", "clean\n")
    (repo / "a.txt").write_text(f"cost {PESO}20\n", encoding="utf-8")
    assert run_staged(repo, master).returncode == 0


def test_staged_deleted_file_is_not_scanned(repo, master):
    stage(repo, "a.txt", f"cost {PESO}20\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "core.hooksPath="]
    subprocess.run([*git, "commit", "-qm", "x"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "rm", "-q", "a.txt"], cwd=repo, check=True, capture_output=True)
    assert run_staged(repo, master).returncode == 0
