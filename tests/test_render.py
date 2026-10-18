"""Tests for src/render.py and src/resume.typ (RT-002).

Every PDF and scratch TOML goes into pytest's tmp_path; nothing is written
into the tracked tree. Extracted text is compared in code (the Windows
console is cp1252 and shows en dashes and bullets as '?').
"""
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "src" / "render.py"
SAMPLE = ROOT / "examples" / "sample-resume.toml"

EN_DASH = "\u2013"
BULLET = "\u2022"
SECTIONS = ["Experience", "Projects", "Leadership", "Education", "Skills"]


def render(source, output, cwd):
    """Run the CLI as a user would; cwd is a scratch dir, not the repo."""
    return subprocess.run(
        [sys.executable, str(RENDER), str(source), str(output), "--no-master"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
    )


def pdf_text(reader):
    return "\n".join(page.extract_text() for page in reader.pages)


def render_toml(tmp_path, toml_text):
    """Write toml_text to a scratch file, render it, return (text, reader)."""
    source = tmp_path / "source.toml"
    source.write_text(toml_text, encoding="utf-8")
    output = tmp_path / "out.pdf"
    result = render(source, output, tmp_path)
    assert result.returncode == 0, result.stderr
    reader = PdfReader(output)
    return pdf_text(reader), reader


def lines(text):
    return [line.strip() for line in text.splitlines()]


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sample")
    output = tmp / "sample.pdf"
    result = render(SAMPLE, output, tmp)
    assert result.returncode == 0, result.stderr
    reader = PdfReader(output)
    return {"result": result, "path": output, "reader": reader, "text": pdf_text(reader)}


@pytest.fixture(scope="module")
def sample_data():
    with SAMPLE.open("rb") as f:
        return tomllib.load(f)


# --- Rendering the fictional sample -----------------------------------------

def test_cli_renders_sample_to_one_page(sample_pdf):
    assert sample_pdf["result"].stderr == ""
    assert "wrote" in sample_pdf["result"].stdout
    assert sample_pdf["path"].read_bytes().startswith(b"%PDF")
    assert len(sample_pdf["reader"].pages) == 1


def test_page_is_us_letter(sample_pdf):
    box = sample_pdf["reader"].pages[0].mediabox
    assert (round(float(box.width)), round(float(box.height))) == (612, 792)


def test_only_libertinus_serif_fonts_embedded(sample_pdf):
    fonts = set()
    for page in sample_pdf["reader"].pages:
        for ref in page["/Resources"]["/Font"].values():
            fonts.add(str(ref.get_object()["/BaseFont"]))
    assert fonts
    # Subset fonts are named like /ABCDEF+LibertinusSerif-Bold-Identity-H.
    for name in fonts:
        assert name.lstrip("/").split("+")[-1].startswith("LibertinusSerif-"), name


def test_text_has_contact_and_every_bullet(sample_pdf, sample_data):
    text = sample_pdf["text"]
    contact = sample_data["contact"]
    for value in [contact["name"], contact["email"], contact["phone"],
                  contact["location"], *contact["links"]]:
        assert value in text, value

    expected = []
    for job in sample_data["experience"]:
        for role in job["roles"]:
            expected += role["bullets"]
    for section in ("projects", "leadership"):
        for entry in sample_data[section]:
            expected += entry["bullets"]
    for edu in sample_data["education"]:
        expected += edu["details"]
    assert len(expected) == 14
    for bullet in expected:
        assert f"{BULLET} {bullet}" in text, bullet


def test_en_dashes_survive(sample_pdf):
    text = sample_pdf["text"]
    assert text.count(EN_DASH) == 5
    assert f"Mar 2022 {EN_DASH} Present" in text
    assert f"2014 {EN_DASH} 2018" in text


def test_section_order_and_certifications_last(sample_pdf):
    all_lines = lines(sample_pdf["text"])
    assert [line for line in all_lines if line in SECTIONS] == SECTIONS
    assert all_lines[-1].startswith("Certifications: ")
    assert "Tableau Desktop Specialist" in all_lines[-1]


# --- Optional sections and fields -------------------------------------------

MINIMAL = f"""
[contact]
name = "Pat Minimal"
email = "pat@example.com"
location = "Anytown, USA"

[[experience]]
company = "Acme Corp"

  [[experience.roles]]
  title = "Analyst"
  dates = "2020 {EN_DASH} 2024"
  bullets = ["Did one thing"]

[[education]]
school = "Anytown College"
degree = "B.A. in Math"
dates = "2016 {EN_DASH} 2020"

[[skills]]
category = "Tools"
items = ["SQL"]
"""


def test_optional_sections_absent_render_without_empty_headings(tmp_path):
    text, reader = render_toml(tmp_path, MINIMAL)
    assert len(reader.pages) == 1
    for word in ("Projects", "Leadership", "Certifications"):
        assert word not in text
    assert [line for line in lines(text) if line in SECTIONS] == [
        "Experience", "Education", "Skills"]
    # No education details: the only bullet is the one experience bullet.
    assert text.count(BULLET) == 1


def test_contact_line_has_no_stray_separators(tmp_path):
    text, _ = render_toml(tmp_path, MINIMAL)
    assert "Anytown, USA  |  pat@example.com" in lines(text)
    for line in lines(text):
        assert not line.startswith("|") and not line.endswith("|"), line
        assert "|  |" not in line, line


def test_name_only_contact_prints_no_separator_line(tmp_path):
    text, _ = render_toml(tmp_path, '[contact]\nname = "Solo Name"\nlinks = []\n')
    assert lines(text) == ["Solo Name"]


def test_empty_optional_lists_print_no_heading(tmp_path):
    toml = "certifications = []\nprojects = []\nleadership = []\n" + MINIMAL
    text, _ = render_toml(tmp_path, toml)
    for word in ("Projects", "Leadership", "Certifications"):
        assert word not in text


def test_certifications_without_skills_still_print_under_skills(tmp_path):
    text, _ = render_toml(tmp_path, 'certifications = ["Cert A"]\n[contact]\nname = "Cert Only"\n')
    assert lines(text)[-2:] == ["Skills", "Certifications: Cert A"]


def test_leadership_without_role_and_role_without_dates(tmp_path):
    toml = MINIMAL.replace(f'  dates = "2020 {EN_DASH} 2024"\n', "") + """
[[leadership]]
organization = "Some Club"
bullets = ["Ran the club"]
"""
    text, _ = render_toml(tmp_path, toml)
    assert "Analyst" in lines(text)
    assert "Some Club" in lines(text)
    assert f"{BULLET} Ran the club" in text


# --- Contact comes only from [contact] --------------------------------------

def test_contact_details_only_from_contact_table(tmp_path):
    toml = 'email = "toplevel-leak@example.com"\nphone = "+1 555 0100"\n' + MINIMAL + """
[profile]
email = "profile-leak@example.com"
"""
    text, _ = render_toml(tmp_path, toml)
    assert "pat@example.com" in text
    assert "leak@example.com" not in text
    assert "+1 555 0100" not in text


def test_renderer_never_references_master_resume():
    for path in (RENDER, ROOT / "src" / "resume.typ"):
        assert "master-resume" not in path.read_text(encoding="utf-8"), path


# --- Typst markup characters print literally --------------------------------

def test_typst_markup_characters_print_literally(tmp_path):
    toml = r"""
[contact]
name = "#Name *Star* $x$ _under_"
email = "a_b@example.com"

[[experience]]
company = "#Hash Co"

  [[experience.roles]]
  title = "*Lead* _Dev_"
  bullets = [
    "Saved $50 and $60 with #tags, *stars* and snake_case_names",
    'Path C:\temp @ref <label>',
  ]
"""
    text, _ = render_toml(tmp_path, toml)
    for literal in ["#Name *Star* $x$ _under_", "a_b@example.com", "#Hash Co",
                    "*Lead* _Dev_",
                    "Saved $50 and $60 with #tags, *stars* and snake_case_names",
                    "Path C:\\temp @ref <label>"]:
        assert literal in text, literal


# --- Error cases -------------------------------------------------------------

def assert_clean_failure(result):
    assert result.returncode == 1
    assert "render failed" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_source_file(tmp_path):
    output = tmp_path / "out.pdf"
    assert_clean_failure(render(tmp_path / "nope.toml", output, tmp_path))
    assert not output.exists()


def test_broken_toml(tmp_path):
    source = tmp_path / "broken.toml"
    source.write_text('[contact\nname = "x"\n', encoding="utf-8")
    output = tmp_path / "out.pdf"
    assert_clean_failure(render(source, output, tmp_path))
    assert not output.exists()


@pytest.mark.parametrize("toml", [
    '[contact]\nemail = "no-name@example.com"\n',
    '[[skills]]\ncategory = "X"\nitems = ["y"]\n',
], ids=["missing-contact-name", "missing-contact-table"])
def test_missing_contact(tmp_path, toml):
    source = tmp_path / "source.toml"
    source.write_text(toml, encoding="utf-8")
    output = tmp_path / "out.pdf"
    assert_clean_failure(render(source, output, tmp_path))
    assert not output.exists()


def test_toml_date_value_fails_cleanly(tmp_path):
    # A bare TOML date (not a string) can't be serialised to JSON.
    source = tmp_path / "source.toml"
    source.write_text('[contact]\nname = "A"\n[[projects]]\nname = "P"\ndates = 2023-01-01\n',
                      encoding="utf-8")
    output = tmp_path / "out.pdf"
    assert_clean_failure(render(source, output, tmp_path))
    assert not output.exists()


def test_output_in_missing_folder_fails_cleanly(tmp_path):
    assert_clean_failure(render(SAMPLE, tmp_path / "no-such-dir" / "out.pdf", tmp_path))
