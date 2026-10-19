# Resume Tailor

Keep one master career file and turn any job posting into a truthful, tailored, ATS-friendly Harvard-style PDF resume, with a human checkpoint before any PDF is made.

## How it works

1. The master career file holds everything: roles, projects, numbers, skills. It is private and stays on one machine.
2. A job posting goes in. The tool reads it and lists the must-haves, the keywords and which parts of the master file match.
3. A checkpoint follows. The owner sees the gaps, the likely screening questions and the proposed bullets, and approves or changes them. No PDF is made before this step.
4. The approved content is written to a per-job resume source file (TOML).
5. Content checks run on that file: banned words, numbers that do not trace back to the master file, skills that should not be listed.
6. The renderer turns the source file into a Harvard-style PDF (one page preferred, two at most).
7. The PDF, its source and a one-page prep sheet for the application form and interviews are saved in a folder for that job.

## Status

Working. The resume source format, a sample file, the renderer, the content and output checks, the tailoring playbook ([docs/TAILORING.md](docs/TAILORING.md)) and the `/tailor` command are done. The full workflow has been tried on real job postings from LinkedIn and Indeed, and the playbook was updated from what those runs showed.

## Try it on the sample

Needs Python 3.11 or newer. There are two dependencies, `typst` and `pypdf`, installed with pip:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python src/render.py examples/sample-resume.toml sample.pdf
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`.

The sample is a made-up person, Jamie Sample, with invented employers.

The renderer runs the content checks first and writes no PDF if one fails; without a master file it prints a warning and skips the number and skill checks (or pass `--no-master` to skip them quietly). To run the tests, install `requirements-dev.txt` and run `python -m pytest`. To turn on the commit guard that blocks personal data, run `git config core.hooksPath hooks` once.

Each successful render ends with a one-line summary, for example `wrote sample.pdf (1 page, all text readable)`. The output checks read the finished PDF back: two pages print a warning (one is preferred), and three or more pages, or text that cannot be read back from the PDF, write no PDF at all. So does a field the template does not print (the message names it). Whenever a render fails after the source file was read, an older PDF at the output path is removed so it cannot be mistaken for the new one; a source file that cannot be read never deletes anything.

## Tailoring a resume with Claude Code

`.claude/commands/tailor.md` adds a `/tailor` command to Claude Code. Open Claude Code in this folder and run `/tailor <job link>` (or paste the job description). It follows [docs/TAILORING.md](docs/TAILORING.md) step by step and stops at the checkpoint: no PDF is made until you approve the proposed resume. It needs three things that are not in this repo, because they are private: a `master-resume.md` in the project root, a baseline source at `applications/_baseline/resume.toml`, and `applications/TRACKER.md`, a short file that points to a Notion database used as the applications tracker (the Notion connector must be connected). TAILORING.md step 2 shows the folder layout.

## Resume source format

The source file is TOML, read with Python's standard `tomllib`. Sections:

- `[contact]`: name, location, email, optional phone and links
- `[[education]]`: school, location, degree, dates, optional details
- `[[experience]]`: one per employer, with one or more `[[experience.roles]]` (title, dates, bullets)
- `[[projects]]`, `[[leadership]]`: optional entries with bullets
- `[[skills]]`: a category and its items
- `certifications`: optional list of strings, placed at the top of the file

Optional: `phone`, `links`, `location`, education `details`, and the whole `projects`, `leadership` and `certifications` sections. A section with no entries is left out of the PDF.

The PDF prints the sections in this order: Experience, Projects, Leadership, Education, Skills. Certifications print as the last line of Skills.

See [examples/sample-resume.toml](examples/sample-resume.toml) for every section filled in.

## Privacy by design

The master file, the per-job application folders and any source documents are git-ignored and never leave the owner's PC. The renderer builds the PDF from the per-job source file only, so private notes cannot reach a PDF by accident. The content checks read the master file only to compare against, never to print it. They reject peso amounts on a resume, and a pre-commit hook blocks private files, peso amounts and the owner's phone and address from being committed. The sample in this repo is fictional.

## Repo layout

- `docs/`: the project brief, the style guide for resume wording, and the tailoring playbook (`TAILORING.md`)
- `examples/`: the fictional sample resume source
- `src/`: the renderer (`render.py` and the layout template `resume.typ`), the content checks (`checks.py`) and the output checks (`pdf_checks.py`)
- `.claude/commands/`: the `/tailor` command
- `hooks/`: the pre-commit guard
- `tests/`: the test suite
- `requirements.txt`: the two pinned dependencies (`typst` and `pypdf`)
