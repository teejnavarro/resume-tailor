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
    data["leadership"] = [{"organization": "text that is not in the pdf"}]
    pages, missing, unprinted = pdf_checks.check_pdf(pdf, data)
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
    assert pdf_checks.check_pdf(pdf, spaced) == (1, [], [])


def test_squash_normalises_curly_quotes_and_whitespace():
    assert pdf_checks._squash("it\u2019s  a \u201cgo\u201d"+chr(10)) == pdf_checks._squash("it's a \"go\"")


def test_strings_walks_nested_values_but_not_keys():
    data = {"a": "one", "b": [{"c": "two"}, "three"], "d": {"e": ["four"]}, "n": 5}
    assert list(pdf_checks.strings(data)) == ["one", "two", "three", "four"]


def test_check_pdf_ignores_tables_the_template_does_not_print():
    pdf, data = sample_pdf_and_data()
    data["profile"] = {"email": "not-printed@example.com"}
    assert pdf_checks.check_pdf(pdf, data) == (1, [], [])


# --- QA edge cases ----------------------------------------------------------


def compile_data(data):
    return typst.compile(
        str(TEMPLATE), sys_inputs={"resume": json.dumps(data)}, ignore_system_fonts=True
    )


def with_bullet(text):
    return {
        "contact": {"name": "Pat Fictional"},
        "experience": [{"company": "Co", "roles": [{"title": "Analyst", "bullets": [text]}]}],
    }


def write_toml(tmp_path, text):
    path = tmp_path / "source.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_one_page_summary_is_a_single_line(tmp_path):
    out = tmp_path / "out.pdf"
    result = render(SAMPLE, out, tmp_path)
    assert result.stdout.strip() == f"wrote {out} (1 page, all text readable)"


def test_two_page_summary_is_a_single_line_plus_warning(tmp_path):
    out = tmp_path / "out.pdf"
    result = render(fake_resume(tmp_path, 10), out, tmp_path)
    assert result.stdout.strip() == f"wrote {out} (2 pages, all text readable)"
    assert result.stderr.strip() == "warning: 2 pages (1 preferred)"


@pytest.mark.parametrize(
    "text",
    [
        "Jan 2019 \u2013 Dec 2021",
        "Did this \u2014 then that",
        "One \u2022 two",
        "R&D and P&L",
        "office fluffy affinity waffle",
        "Jos\u00e9 Pi\u00f1a M\u00fcller",
        "Pat's \"best\" '90s work",
        "#strong *bold* _x_ $y$ <z> @ref",
        "and so on\u2026",
        "https://example.com/a-very/long/path/that/wraps/around/the/end/of/the/line/here",
    ],
)
def test_check_pdf_reads_back_special_characters(text):
    data = with_bullet(text)
    assert pdf_checks.check_pdf(compile_data(data), data) == (1, [], [])


def test_check_pdf_reads_skills_and_certifications():
    data = {
        "contact": {"name": "Pat Fictional"},
        "skills": [{"category": "Tools", "items": ["Excel", "SQL", "Power BI"]}],
        "certifications": ["Cert Alpha", "Cert Beta"],
    }
    pdf = compile_data(data)
    assert pdf_checks.check_pdf(pdf, data) == (1, [], [])
    data["certifications"].append("Cert Gamma")
    assert pdf_checks.check_pdf(pdf, data) == (1, ["Cert Gamma"], [])


def test_skills_are_printed_joined_with_comma_space():
    data = {"contact": {"name": "Pat"}, "skills": [{"category": "Tools", "items": ["Excel", "SQL"]}]}
    reader = pdf_checks.PdfReader(pdf_checks.io.BytesIO(compile_data(data)))
    assert "Excel, SQL" in reader.pages[0].extract_text()


def test_empty_optional_sections_pass(tmp_path):
    source = write_toml(
        tmp_path,
        """projects = []
leadership = []
certifications = []

[contact]
name = "Pat Fictional"
location = ""

[[experience]]
company = "Example Works"
location = ""

  [[experience.roles]]
  title = "Analyst"
  bullets = []

[[skills]]
category = "Tools"
items = []
""",
    )
    out = tmp_path / "out.pdf"
    result = render(source, out, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "1 page, all text readable" in result.stdout
    assert out.exists()


def test_unreadable_text_fails_and_writes_nothing(tmp_path):
    name = "Pat " + chr(0x6F22) + chr(0x5B57)
    source = write_toml(tmp_path, f'[contact]\nname = "{name}"\n')
    out = tmp_path / "out.pdf"
    result = render(source, out, tmp_path)
    assert result.returncode == 1
    assert "render failed: text not readable in the PDF:" in result.stderr
    assert result.stderr.strip().endswith(", no PDF written")
    assert "Traceback" not in result.stderr
    assert not out.exists()


def test_unreadable_text_reports_how_many_more(tmp_path):
    cjk = chr(0x6F22) + chr(0x5B57)
    source = write_toml(
        tmp_path,
        f'[contact]\nname = "Pat"\nlocation = "{cjk}"\n\n[[skills]]\ncategory = "{cjk}"\nitems = ["{cjk}"]\n',
    )
    result = render(source, tmp_path / "out.pdf", tmp_path)
    assert result.returncode == 1
    assert "(and 2 more)" in result.stderr


def failing_source(tmp_path, kind):
    if kind == "three-pages":
        return fake_resume(tmp_path, 24)
    if kind == "unreadable":
        return write_toml(tmp_path, f'[contact]\nname = "Pat {chr(0x6F22)}"\n')
    if kind == "unprinted":
        return write_toml(tmp_path, '[contact]\nname = "Pat"\nnickname = "P"\n')
    return write_toml(tmp_path, "[contact\nname = broken\n")


@pytest.mark.parametrize("kind", ["three-pages", "unreadable", "unprinted", "broken-toml"])
def test_failed_render_removes_an_older_pdf(tmp_path, kind):
    source = failing_source(tmp_path, kind)
    out = tmp_path / "out.pdf"
    out.write_bytes(b"older pdf")
    result = render(source, out, tmp_path)
    assert result.returncode == 1
    assert not out.exists()
    assert "removed old" in result.stderr


def test_content_check_failure_removes_an_older_pdf(tmp_path):
    source = write_toml(tmp_path, '[contact]\nname = "Pat"\nlocation = "Leveraged Town"\n')
    out = tmp_path / "out.pdf"
    out.write_bytes(b"older pdf")
    result = render(source, out, tmp_path)
    assert result.returncode == 1
    assert "banned-word" in result.stderr
    assert not out.exists()


def test_missing_source_keeps_an_older_pdf(tmp_path):
    out = tmp_path / "out.pdf"
    out.write_bytes(b"older pdf")
    result = render(tmp_path / "typo.toml", out, tmp_path)
    assert result.returncode == 1
    assert out.read_bytes() == b"older pdf"
    assert "removed old" not in result.stderr


def test_non_utf8_source_keeps_an_older_pdf(tmp_path):
    source = tmp_path / "source.toml"
    source.write_bytes(b'[contact]\nname = "Pat \xff"\n')
    out = tmp_path / "out.pdf"
    out.write_bytes(b"older pdf")
    result = render(source, out, tmp_path)
    assert result.returncode == 1
    assert out.read_bytes() == b"older pdf"


def test_output_same_as_source_is_never_deleted(tmp_path):
    source = write_toml(tmp_path, '[contact]\nname = "Pat"\nnickname = "P"\n')
    before = source.read_bytes()
    result = render(source, source, tmp_path)
    assert result.returncode == 1
    assert source.read_bytes() == before
    assert "removed old" not in result.stderr


def test_unprinted_field_gets_a_clear_message(tmp_path):
    source = write_toml(
        tmp_path,
        '[contact]\nname = "Pat"\nnickname = "P"\n\n[[experience]]\ncompany = "Co"\n\n'
        '  [[experience.roles]]\n  title = "Analyst"\n  notes = "x"\n',
    )
    out = tmp_path / "out.pdf"
    result = render(source, out, tmp_path)
    assert result.returncode == 1
    assert "field contact.nickname is not printed by the template (and 1 more), no PDF written" in result.stderr
    assert "text not readable" not in result.stderr
    assert not out.exists()


def test_check_pdf_lists_unprinted_field_names():
    data = with_bullet("ok")
    pdf = compile_data(data)
    data["experience"][0]["roles"][0]["notes"] = "n"
    data["contact"]["nickname"] = "P"
    pages, missing, unprinted = pdf_checks.check_pdf(pdf, data)
    assert missing == []
    assert unprinted == ["contact.nickname", "experience.roles.notes"]


def test_unreadable_headline_is_reported():
    data = with_bullet("ok")
    data["headline"] = "text that is not in the pdf"
    pages, missing, unprinted = pdf_checks.check_pdf(compile_data(with_bullet("ok")), data)
    assert pages == 1
    assert missing == ["text that is not in the pdf"]
    assert unprinted == []


def test_headline_is_not_listed_as_unprinted():
    data = with_bullet("ok")
    data["headline"] = "Data Analyst"
    assert pdf_checks.check_pdf(compile_data(data), data) == (1, [], [])


def test_every_field_in_the_sample_is_in_fields():
    data = tomllib.loads(SAMPLE.read_text(encoding="utf-8"))
    assert pdf_checks.check_pdf(compile_data(data), data) == (1, [], [])


def test_pypdf_is_a_runtime_requirement():
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8").split()
    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").split()
    assert "pypdf==6.21.0" in runtime and "typst==0.15.0" in runtime
    assert "-r" in dev and "requirements.txt" in dev
    assert not any(line.startswith("pypdf") for line in dev)
