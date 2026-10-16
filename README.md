# Resume Tailor

Keep one master career file and turn any job posting into a truthful, tailored, ATS-friendly Harvard-style PDF resume, with a human checkpoint before any PDF is made.

## How it works

1. The master career file holds everything: roles, projects, numbers, skills. It is private and stays on one machine.
2. A job posting goes in. The tool reads it and lists the must-haves, the keywords and which parts of the master file match.
3. A checkpoint follows. The owner sees the gaps, the likely screening questions and the proposed bullets, and approves or changes them. No PDF is made before this step.
4. The approved content is written to a per-job resume source file (TOML).
5. Content checks run on that file: banned words, numbers that do not trace back to the master file, skills that should not be listed.
6. The renderer turns the source file into a Harvard-style PDF (one page preferred, two at most).
7. The PDF and its source are saved in a folder for that job.

## Status

Work in progress. The resume source format and a sample file are done. The renderer and the content checks are being built.

## Try it on the sample

Available once the renderer lands (in progress):

```
python src/render.py examples/sample-resume.toml sample.pdf
```

The sample is a made-up person, Jamie Sample, with invented employers.

## Resume source format

The source file is TOML, read with Python's standard `tomllib`, so there is nothing to install. Sections:

- `[contact]`: name, location, email, optional phone and links
- `[[education]]`: school, location, degree, dates, optional details
- `[[experience]]`: one per employer, with one or more `[[experience.roles]]` (title, dates, bullets)
- `[[projects]]`, `[[leadership]]`: optional entries with bullets
- `[[skills]]`: a category and its items
- `certifications`: optional list of strings, placed at the top of the file

See [examples/sample-resume.toml](examples/sample-resume.toml) for every section filled in.

## Privacy by design

The master file, the per-job application folders and any source documents are git-ignored and never leave the owner's PC. The renderer reads only the per-job source file, never the master file, so private notes cannot reach a PDF by accident. The sample in this repo is fictional.

## Repo layout

- `docs/`: the project brief and the style guide for resume wording
- `examples/`: the fictional sample resume source
- `src/`: the renderer and checks (in progress)
