# TAILORING.md: from job link to approved PDF

This is the playbook for turning one job posting into one tailored resume. Claude follows it step by step, whether we're working in chat or through the `/tailor` command in Claude Code. Same steps, same checkpoint, same files at the end.

"I" and "the owner" both mean me, the person whose resume this is.

## The rules that never bend

1. **The master file is the only source of facts.** Every bullet, number, tool, title and date on a tailored resume comes from `master-resume.md`. If it isn't there, it doesn't go on the resume.
2. **Nothing gets invented.** Rewording is fine. New tools, new numbers, bigger titles or shifted dates are not.
3. **No PDF before the checkpoint is approved.** The checkpoint in step 4 is a hard stop.
4. **Connectors are read-only.** Read job postings, nothing else. No applying, no messages, no posting, no profile edits, on any site or connector.
5. **Private stays private.** Salary, interview-only stories and contact details live in local, git-ignored files. They never go into this repo.

## Step 1: Read the job

Pick the route by where the link comes from:

| Source | How to read it |
|---|---|
| Indeed | The Indeed connector (job details by link or job ID). If the connector fails, open the job page in the built-in browser. Indeed may show a security check first: Claude can't clear it, so I clear it in the browser pane and Claude reads the page after. |
| LinkedIn | The browser built into the Claude desktop app. I sign in to LinkedIn there once. Read the page text only; never click Apply, Easy Apply or Message. |
| Anything else, or reading fails | I paste the job description into the chat |

Save a copy of the posting right away, because postings get taken down. The copy goes into `job.md` in the application folder (step 2) with the link, the company, the role title, the location and work setup, and the full text.

If the posting is thin (no real requirements listed), say so before going further. A thin posting means a weaker match analysis.

## Step 2: Set up the application folder

Every job gets its own folder under `applications/`, which is git-ignored:

```
applications/
  TRACKER.md                     points to the Notion tracker (local only)
  _baseline/resume.toml          the approved general resume every job starts from
  YYYY-MM-DD_company_role/
    job.md                       copy of the posting and its link
    notes.md                     analysis, checkpoint, screening answers, decisions
    resume.toml                  the tailored resume source
    prep.md                      the prep sheet for forms and interviews (step 7)
    Lastname_Firstname_Resume_Company.pdf   the final PDF, the file I upload
```

- The date is the day we start tailoring. Company and role are short, lowercase, with hyphens: `2026-11-03_acme-foods_data-analyst`.
- The PDF name follows the pattern `Lastname_Firstname_Resume_Company.pdf`, with my real name filled in. It's the file a recruiter sees, so it carries my name and the company.

The tracker is a Notion database. `applications/TRACKER.md` (private) names it and gives its data source.

First look for an existing row with the same Link (a Notion rows query filtered on Link). If there is one, update only its Role, Deadline and Local folder, and never change its Status. Never add a second row. Otherwise add a row with Company, Role, Source, Link, Deadline (only if the posting states one), Local folder (the folder name) and Status **Drafting**.

If Notion can't be reached or the write fails, carry on with tailoring. Tell me plainly that the row was not added, and put the row's values under a "Tracker row not added" heading in `notes.md` so it can be added later.

Source is LinkedIn, Indeed or Other. Status is one of:

- **Drafting**: we're working on it
- **Applied**: I submitted the application myself
- **Assessment**: I was sent a test or assessment
- **Interview**: I heard back and have an interview
- **Offer**: I got an offer
- **Rejected**: they said no
- **Withdrawn**: I pulled out, or decided not to apply

## Step 3: Analyse the posting

Write the analysis into `notes.md`:

1. **Must-haves**: what the posting says is required (years, tools, degree, domain).
2. **Nice-to-haves**: what it lists as a plus.
3. **Keywords**: the exact words an ATS will scan for, as the posting spells them. "Power BI", not "PowerBI". "A/B testing", not "experiments".
4. **Match table**: one row per must-have and nice-to-have.

| Posting asks for | Master file has | Match |
|---|---|---|
| SQL, 3+ years | SQL in the last two roles, quoted from the master file | Yes |
| Tableau | Nothing | Gap |

Match is Yes, Partial (related but not the same thing) or Gap. Quote the master file line for every Yes and Partial, so I can check it.

## Step 4: CHECKPOINT (hard stop)

Stop and show me one report with three parts. Don't build the resume source or render anything until I've answered all three.

### Part 1: Gaps

For every Gap and Partial in the match table, ask me directly: "The posting asks for X. The master file has nothing on it. Do you have experience with X?"

- If I say no, it stays off the resume. Say whether the gap looks like a dealbreaker (a must-have) or not (a nice-to-have).
- If I say yes and tell you about it, that's a new fact. It goes through step 9 before it can go on any resume.
- If I go ahead without answering a gap question, treat the gap as a no: keep it off the resume, and say so in your reply and in `notes.md`.
- Skills the master file marks *Never list in Skills* are gaps no matter what. Flag them when the posting asks for them and never claim them, not in Skills and not in a bullet. The master file notes the one exception: a skill that may appear inside a specific bullet only. Follow that note exactly.

### Part 2: Screening questions

List every question the posting or its application form asks (years of experience, work setup, start date, notice period, salary, work authorization, relocation), with a suggested answer for each.

- Base answers on the master file's job-search preferences section.
- **Salary**: always answer with a range, never a single number. Never put a salary figure in an answer, or anywhere I might paste it, without my OK for that specific job. Point out which kind of role it is (employee or contractor), since the master file keeps separate floors for each.
- If a question can't be answered from the master file, ask me instead of guessing.

### Part 3: Proposed resume

Show the full proposed content in reading order:

- which roles, bullets and skills to keep, cut or move up, with one line on why
- the proposed headline (the line under my name), with the posting term it uses
- the opening bullet of each role, so I can see what each role leads with
- every reworded bullet next to its master file original, so I can see exactly what changed
- how many bullets are reused unchanged from the baseline, and which ones
- which posting keywords each change brings in

Save the whole checkpoint in `notes.md` before waiting:

- every gap you asked about
- every screening question with its suggested answer, or "none in the posting"
- a short summary of the proposed resume

Then wait. I'll approve it, change parts of it, or say no. Add my answers and decisions to `notes.md`.

## Step 5: Rewriting bullets

All wording follows [STYLE.md](STYLE.md): strong, specific verbs, real names and numbers, one idea per bullet, no banned words. On top of that:

- **Rewrite by default.** Reusing a baseline bullet word for word is the exception, and Part 3 says how many I'm reusing. Write the bullets for this job. The baseline is the starting selection, not fixed text. For every bullet kept, rewrite it around what this posting cares about: lead with the part of the work the posting asks for, use its terms where they're true, and pick which facts from that master file entry to show (any resume-ready detail in it is fair game). Same facts, different emphasis per job.
- **Vary the opening bullet.** In each role, the first bullet matches the posting's top must-have. Two jobs with different top must-haves get different opening bullets.
- **Skills per job.** Reorder the Skills lines so the ones the posting cares about come first. Rename a category or item to the posting's term where it's true. Drop lines that don't help for this job.
- **Current role: about 6 bullets, mostly one line.** A wall of text is hard to read. Facts that don't fit go to Skills or the prep sheet.
- **Headline.** One line under my name, set per job. It uses only titles I have held or my LinkedIn wording, plus skills in the master file. Never a job title I haven't held. The banned words and number tracing apply to it like any other line.
- **Truthful only.** A reworded bullet can swap in the posting's word for the same thing ("audience segmentation" for "building customer audiences"). It can't add a tool, a number, a title or a date that the master file doesn't have.
- **Numbers stay as they are.** Don't round up, don't combine two numbers into a bigger one, don't turn "about" into an exact figure.
- **No peso amounts** on any resume. The checks block them.
- **Labels stay honest.** A pilot is called a pilot, AI-assisted work says so.
- **Mirror keywords where they're true.** If the posting says "stakeholder reporting" and the master file has reports for the marketing team, use the posting's term once and name the team. Keyword stuffing reads badly and an ATS doesn't need it.
- **Length budget.** About 17 bullets plus the skills lines fit on one page. Two pages is allowed but needs a reason.

## Step 6: Build and render

Only after the checkpoint is approved:

1. Copy `applications/_baseline/resume.toml` into the job folder as `resume.toml`.
2. Apply the approved changes from step 4 and nothing else. That includes the headline, set as `headline = "..."` at the top of the file, before `[contact]`.
3. Render it:

   ```
   .venv\Scripts\python src/render.py applications/<folder>/resume.toml applications/<folder>/Lastname_Firstname_Resume_Company.pdf
   ```

   The render runs the checks on its own:
   - **Content checks** before the PDF: banned words from STYLE.md, numbers that don't trace to the master file, skills that are never listed, peso amounts.
   - **Output checks** after: 1 page passes, 2 pages passes with a warning, 3 or more fails, and all the text has to read back out of the PDF the way an ATS would read it.

   If any check fails, no PDF is written. The error names the file, line and rule.
4. If a check fails, fix `resume.toml`. If the fix changes what the resume says (not just a typo), show me the change first.
5. Show me the PDF. I read it aloud. Anything I wouldn't say in an interview comes out or gets reworded, and we render again.

## Step 7: Prep sheet

Right after I approve the PDF, write `prep.md` in the job folder. It's my one-page cheat sheet for the application form and the interviews. It's private and never committed.

Use only the posting and `master-resume.md`. Interview-only stories and private notes from the master file are fine here, since that's what they're for, but they still never go on the resume. If something isn't in either file, leave it out or mark it "ask me".

```markdown
# Prep: <Company> - <Role>

## The role in brief
3 to 5 lines from the posting only: what the job is, who it reports to,
what they care about most, setup and schedule. No outside research unless I ask.

## Form and screening answers
| Question | My answer |
|---|---|
(The checkpoint answers I approved. Pay: only a range I approved for this job,
otherwise "ask me first".)

## Likely interview questions
4 to 6 questions the posting points to. For each, a short answer in my voice,
STAR where it fits (situation, task, action, result), with numbers from the master file.

## Gaps and how I'll handle them
| Gap | Honest answer |
|---|---|
(From the checkpoint: what I have that's closest, and how I'd close the gap.
Never claim the gap.)

## Questions to ask them
3 to 5 questions about the team, the work and how success is measured.

## Pay notes
The approved range, if any, and the package questions to ask: HMO for dependents,
bonus, 13th month; for contracts, payment terms, currency, notice and paid time off.
```

Keep it to about one page, in the STYLE.md voice.

## Step 8: Save and track

When I approve the PDF:

- Check the folder has all five files: `job.md`, `notes.md`, `resume.toml`, the PDF and `prep.md`.
- Check the Notion row has its Link and Local folder filled in, and leave its status as it is (**Drafting** for a new job). If the earlier write failed, try again now, and once it works, remove the "Tracker row not added" note from `notes.md`.
- The status moves to **Applied** only when I say I've applied, and the Applied date is set to that day. This tool never applies for me.
- Later updates (Assessment, Interview, Offer, Rejected, Withdrawn) are made to the same Notion row when I report them.

## Step 9: Feed new facts back to the master file

During tailoring I sometimes remember something that isn't in the master file: a tool I used, a number, a project. Don't use it straight away. Instead:

1. Write it up as a proposed addition: where it goes in `master-resume.md`, and the exact wording.
2. Mark whether it's resume-ready (a top-level bullet) or a private note (an indented line, for interviews only).
3. Add it only after I say yes. Then it can go on this resume and future ones.

The master file is what keeps every resume truthful, so it only changes with my OK.

## Checklist

1. Read the job (Indeed connector, LinkedIn in the built-in browser, or pasted text). Save `job.md`.
2. Create `applications/YYYY-MM-DD_company_role/`. Add or update the Notion tracker row: Drafting.
3. Write the analysis in `notes.md`: must-haves, nice-to-haves, keywords, match table.
4. **CHECKPOINT**: gaps, screening questions (salary as a range, only with OK), proposed resume. Wait for approval.
5. Reword by STYLE.md. Truthful only, no peso amounts, about 17 bullets. Rewrite by default, vary each role's opening bullet, tune Skills, keep the current role to about 6 bullets, and write the headline.
6. Copy the baseline, apply the approved changes (headline included), render, fix failed checks, owner reads the PDF aloud.
7. Write `prep.md`: role brief, form answers, likely questions, gaps, questions to ask, pay notes.
8. Five files in the folder. Notion row updated. Applied only when I say so.
9. New facts go to the master file only with my OK.
