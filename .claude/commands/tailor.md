---
description: Tailor a resume to one job posting by following docs/TAILORING.md
argument-hint: <job link, or the pasted job description>
---
Tailor a resume to the job below by following the playbook in this project.

Before anything else, read these files in full:
- `docs/TAILORING.md`: the playbook. Follow its steps 1 to 8 in order.
- `docs/STYLE.md`: voice rules and banned words.
- `master-resume.md`: the only source of facts. It is private and local.
- `applications/TRACKER.md`: the tracker.

Run every command from the project root.

Reading the job (TAILORING.md step 1):
- Indeed link: use the Indeed connector's job details tool. If it fails, open the job page in the browser built into the Claude desktop app. If Indeed shows a security check, ask the owner to clear it in the browser pane, then read the page.
- LinkedIn link: use the browser built into the Claude desktop app. Read the page text only. Never click Apply, Easy Apply or Message.
- Anything else, or if reading fails: ask the owner to paste the job description.

Step 4 is a hard stop. Show the checkpoint report, then end your turn. Do not create `resume.toml`, run the renderer or write any PDF until the owner has explicitly approved the checkpoint. If the owner asks for changes, update the report and stop again.

Never apply, send messages, or use any write action on a connector or website.

The job: $ARGUMENTS
