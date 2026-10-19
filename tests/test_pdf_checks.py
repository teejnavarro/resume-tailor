"""Tests for src/pdf_checks.py and its use by render.py (RT-005).

Everything is written to pytest's tmp_path. Fake resumes are fictional and
contain no digits, so the content checks pass with --no-master.
"""
import json
import subprocess
import sys
import tomllib
import typst
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pdf_checks  # noqa: E402

RENDER = ROOT / "src" / "render.py"
TEMPLATE = ROOT / "src" / "resume.typ"
SAMPLE = ROOT / "examples" / "sample-resume.toml"


def render(source, output, cwd):
    return subprocess.run(
        [sys.executable, str(RENDER), str(source), str(output), "--no-master"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )


def fake_resume(tmp_path, role_count):
    """A fictional resume with role_count roles of six one-line bullets each."""
    blocks = []
    for r in range(role_count):
        bullets = (","+chr(10)).join(
            f'    "Reviewed fictional report batch {chr(97 + r % 26)}{chr(97 + i)} for the sample team"'
            for i in range(6)
        )
        blocks.append(
            f"""[[experience]]
company = "Example Works {chr(97 + r % 26)}{chr(97 + r // 26)}"

  [[experience.roles]]
  title = "Analyst"
  dates = "Jan to Dec"
  bullets = [
{bullets}
  ]
"""
        )
    text = f"""[contact]
name = "Pat Fictional"
location = "Sampletown"
email = "pat@example.com"

{chr(10).join(blocks)}
[[education]]
school = "Example University"
location = "Sampletown"
degree = "Bachelor of Arts"
dates = "Then to now"
"""
    path = tmp_path / "fake.toml"
    path.write_text(text, encoding="utf-8")
    return path


def sample_pdf_and_data():
    data = tomllib.loads(SAMPLE.read_text(encoding="utf-8"))
    pdf = typst.compile(
        str(TEMPLATE), sys_inputs={"resume": json.dumps(data)}, ignore_system_fonts=True
    )
    return pdf, data


def test_one_page_passes_with_summary(tmp_path):
    out = tmp_path / "out.pdf"
    result = render(SAMPLE, out, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "1 page, all text readable" in result.stdout
    assert result.stderr == ""
    assert out.exists()


def test_two_pages_warns_and_writes(tmp_path):
    out = tmp_path / "out.pdf"
    result = render(fake_resume(tmp_path, 10), out, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "2 pages, all text readable" in result.stdout
    assert "warning: 2 pages" in result.stderr
    assert out.exists()


def test_three_pages_fails_and_writes_nothing(tmp_path):
    out = tmp_path / "out.pdf"
    result = render(fake_resume(tmp_path, 24), out, tmp_path)
    assert result.returncode == 1
    assert "render failed: " in result.stderr and " pages (2 max)" in result.stderr
    assert not out.exists()


def test_check_pdf_reports_missing_text():
    pdf, data = sample_pdf_and_data()
    data["leadership"] = [{"name": "text that is not in the pdf"}]
    pages, missing = pdf_checks.check_pdf(pdf, data)
    assert pages == 1
    assert missing == ["text that is not in the pdf"]


def test_check_pdf_matches_straight_quote_and_extra_spaces(tmp_path):
    data = {
        "contact": {"name": "Pat O'Fictional", "email": "pat@example.com"},
        "skills": [{"category": "Tools", "items": ["spreadsheets"]}],
    }
    pdf = typst.compile(
        str(TEMPLATE), sys_inputs={"resume": json.dumps(data)}, ignore_system_fonts=True
    )
    spaced = {"contact": {"name": "Pat   O'Fictional"}, "skills": [{"items": ["spread sheets"]}]}
    assert pdf_checks.check_pdf(pdf, spaced) == (1, [])


def test_squash_normalises_curly_quotes_and_whitespace():
    assert pdf_checks._squash("it\u2019s  a \u201cgo\u201d"+chr(10)) == pdf_checks._squash("it's a \"go\"")


def test_strings_walks_nested_values_but_not_keys():
    data = {"a": "one", "b": [{"c": "two"}, "three"], "d": {"e": ["four"]}, "n": 5}
    assert list(pdf_checks.strings(data)) == ["one", "two", "three", "four"]


def test_check_pdf_ignores_tables_the_template_does_not_print():
    pdf, data = sample_pdf_and_data()
    data["profile"] = {"email": "not-printed@example.com"}
    assert pdf_checks.check_pdf(pdf, data) == (1, [])
