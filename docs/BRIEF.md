# PROJECT BRIEF — Resume Tailor

**Status:** APPROVED by owner in Claude chat, 2026-10-16. `/intake` should skip the questions and go straight to folder setup.

**Goal:** Keep one complete master record of my career, and for any job link produce a truthful, tailored Harvard-style PDF resume, curated together.

**Final deliverable:**
1. `master-resume.md`: the full master file (everything, unfiltered)
2. A Harvard-style PDF template plus a small script that renders a resume from the master file
3. A tailoring playbook (`docs/TAILORING.md`) that chat follows, plus a `/tailor` command in Claude Code that follows the same playbook
4. An `applications/` folder (one subfolder per job) and a tracker list

**Audience:** Me (owner), recruiters and ATS systems for roles found on LinkedIn and Indeed.

## In scope
- Build the master file from my current resume and my Indeed resume, then fill the gaps together over one or more review sessions
- Read job postings:
  - Indeed → Indeed connector (free)
  - LinkedIn → the browser on my PC (I sign in to LinkedIn there once)
  - Anything else, or if reading fails → I paste the job description
- Analyse each job: must-haves, nice-to-haves, keywords, and which of my items match
- **CHECKPOINT before any PDF.** Claude reports:
  - gaps (JD asks for X, master file has nothing; do I have experience?)
  - screening or application questions in the posting, with suggested answers
  - the proposed selection and reworded bullets, for my approval
- Rewrite bullets to match JD keywords: truthful only, never inventing tools, numbers, titles or dates
- Per job: save the JD copy, notes/answers, and the final PDF in `applications/YYYY-MM-DD_company_role/`; add a row to the tracker
- New facts I share during tailoring get added back to the master file (with my OK)

## Out of scope
- Cover letters (can be added later)
- Auto-applying or submitting anything
- Posting to LinkedIn, or using any write action on any connector
- Paid job-reading services (Composio LinkedIn job reader declined)
- A standalone web app (could come later as a separate project)
- Editing my LinkedIn profile

## Expectations
- Harvard style: one column, clean serif, sections Education / Experience / Skills (+ Projects/Leadership as relevant)
- ATS-friendly: real selectable text, no tables, images or columns
- 1 page preferred, 2 pages max
- Strong action verbs and quantified results
- **Natural, human voice:** plain, specific, professional. It should read like I wrote it on a good day.
- Banned-words list kept in `docs/STYLE.md`, e.g. spearheaded, leveraged, synergy, dynamic, passionate, results-driven, cutting-edge, robust, seamless, utilize, delve, "in today's fast-paced…", "proven track record". I can add to it anytime.
- Prefer concrete over impressive: "Built a weekly sales dashboard in Power BI used by 12 store managers" beats "Spearheaded data-driven insights to empower stakeholders."
- No em-dash-heavy or overly symmetrical phrasing; vary sentence openings so it doesn't read like a template.

## Constraints
- No paid APIs or services
- LinkedIn connectors (Zapier, Composio) can post as me; they're used read-only, or not at all
- Claude can't write to `.claude/` from chat, so the `/tailor` command is created in Claude Code on my PC
- Reading LinkedIn needs my PC on, with the Claude desktop app open

## Success criteria
- Master file covers everything in my current resume, plus the gaps we fill
- Every claim in a tailored resume traces back to the master file
- I'm always shown gaps and JD questions before the PDF is made
- A tailored PDF fits 1 page (2 max), renders cleanly, and its text is readable by a plain-text extraction check
- No banned words in any tailored resume (checked automatically before the PDF)
- Passes my read-aloud test: nothing I wouldn't say in an interview
- First real job link goes from link to approved PDF in one session

## Plan
1. Set up the project folder (`/intake` in Claude Code)
2. Review my current resume and Indeed resume together, then build `master-resume.md` (several sittings are fine). Write `docs/STYLE.md` with my input, including 2–3 bullets I like the sound of, as a reference for the voice
3. Build the Harvard PDF template and render script; render the master resume as a test
4. Write `TAILORING.md` (the playbook) and the `/tailor` command
5. Trial run on a real Data Analytics job link (one LinkedIn, one Indeed if possible), then adjust
6. `/review-brief` against these criteria

**Open questions:** None. My current resume file is needed at step 2.

## Assumptions
- Master file is Markdown (easy to edit by hand, and readable by Claude)
- Project folder: `10-Active/2026-10_resume-tailor`
- Starting focus is Data Analytics (my current field), but the master file isn't limited to it
- Contact details live in the master file only and appear only in my own PDFs
- The PC browser is the browser built into the Claude desktop app, so I sign in to LinkedIn there once (separate from my Chrome)

---

## Amendment 2026-10-16 (approved by owner during `/pm`)
- **Public GitHub repo added to scope:** the project is published at `github.com/teejnavarro/resume-tailor` as a portfolio piece with tracked commits.
- **Personal data stays local:** `master-resume.md`, `applications/` (incl. the tracker) and `assets/source/` are git-ignored and never pushed. The public repo holds the code, `docs/STYLE.md`, `docs/TAILORING.md`, the `/tailor` command (if copied in) and a fictional sample resume.
- **Fresh history:** the public repo starts with one clean first commit. The old local history (which contains the master file) is never pushed.
- **Tracker format:** Markdown (`applications/TRACKER.md`), local only. Notion/Gmail tracking discussed and left out for now; it would need a further brief change.

## Amendment 2026-10-19 (approved by owner): prep sheet
- **Added to scope:** for every tailored resume, a role-specific prep sheet for application forms and interviews, saved as `applications/<job folder>/prep.md` (private, git-ignored) on every run, right after the PDF is approved.
- **Contents:** role and company brief, application-form and screening answers, likely interview questions with answers (STAR where it fits), gaps and how to handle them honestly, questions to ask, pay notes.
- **Rules:** facts only from `master-resume.md` and the posting. Interview-only stories are allowed on the prep sheet but never on the resume. The company brief comes from the posting only; no web research unless the owner asks. Pay only as a range the owner approved for that job. STYLE.md voice, about one page.
- **Still out of scope:** cover letters, and anything sent or submitted for the owner.
- **Success:** every new job folder has a `prep.md` that traces to the master file and the posting, and that the owner would be happy to read ten minutes before an interview.
