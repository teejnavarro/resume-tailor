`render.py` turns a resume source file (TOML) into a PDF, using the layout in `resume.typ`.

`checks.py` runs the content checks (banned words, untraced numbers, blocked skills, peso amounts) before every render, and scans staged files for personal data when run with `--staged`.
