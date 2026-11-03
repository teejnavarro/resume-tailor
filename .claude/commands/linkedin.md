---
description: Draft a LinkedIn headline, About and role descriptions from the master resume
argument-hint: "[target roles, and optionally your current profile text or link]"
---
Draft LinkedIn profile text for the owner to paste. Write it to a private local file. Never touch the profile itself.

Before anything else, read these files in full:
- `master-resume.md`: the only source of facts. It is private and local.
- `docs/STYLE.md`: voice rules, banned words and honest labels.
- `applications/_baseline/resume.toml`: the baseline resume, used for the consistency check.

Input:
- Target roles are optional. If none are given, use the preferred titles in the master's job-search section to choose keywords. Use them only for that. Never print the owner's preferences.
- The owner may paste their current profile, or give a link. For a link, use the browser built into the Claude desktop app and read the page text only.

Facts:
- Use only resume-ready master lines: top-level bullets, headings and plain lines. Never use indented sub-bullets, `>` note lines, the contact section, job-search preferences, pay, or any line marked interview only.
- Add contact details only if the owner asks.
- Follow any master note that restricts naming something.
- A new fact goes through TAILORING.md step 9 before it can appear in the draft.

Rules:
- STYLE.md banned words and honest labels apply.
- Skills on the master's never-list stay out.
- No peso amounts.
- Every number traces to resume-ready master text.
- First person is fine in the About section.

Draft contents:
1. Headline, 220 characters at most.
2. About, 2,600 characters at most. The first lines must stand alone, because that is all a reader sees before "see more".
3. A description for each role.
4. Skills in priority order.
5. A short paste checklist.

Consistency report: compare titles and dates across the master, the baseline resume and the current profile, if given. The master records the owner's chosen LinkedIn title. Keep it. Flag differences and never change them.

Public exposure flag: the profile is public and the current employer can see it. List every line that holds an internal figure or an internal tool name, and let the owner decide on each.

Output: write the draft to `notes/linkedin.md`. If that file exists, ask before overwriting it.

Never click edit, save, post, message, connect, or change a LinkedIn setting. Read page text only. Never use a write action on any connector or website.

The profile request: $ARGUMENTS
