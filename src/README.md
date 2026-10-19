`render.py` turns a resume source file (TOML) into a PDF, using the layout in `resume.typ`.

`checks.py` runs the content checks (banned words, untraced numbers, blocked skills, peso amounts) before every render, and scans staged files for personal data when run with `--staged`.

`pdf_checks.py` checks the finished PDF before it is written: the page count and that the text can be read back from the PDF, as an ATS would.
