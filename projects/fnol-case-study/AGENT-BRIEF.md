# Brief for agents working on this case study

Read this first. It is the shared context for every planner, writer and reviewer.

## Goal

Eddie (Edy Santos, Brisbane) is applying for a **Conversational AI Designer** role at an Australian general insurer rolling out agentic AI. This case study is his portfolio evidence. One scenario runs through all four projects: **Sam**, a car insurance first-notification-of-loss (FNOL) chat assistant for a fictional insurer, **Wattle Car Insurance**.

Eddie: former lawyer (10+ years, Brazil), Grad Cert Data Analytics (QUT). Skills: SQL, Python, Power BI, Excel, R. His angle is legal/compliance judgment plus data analysis.

The role asks for: end-to-end flows, personas and tone, dialogue scripts, user research, usability and A/B testing, journey mapping, working with technical specialists, compliance and ethical AI, design documentation, and risk reporting.

## Repo layout (all under `C:\Users\edydo\myportfolio\projects\fnol-case-study\`)

- `README.md`: overview table of the four projects
- `PROGRESS.md`: progress log (only the orchestrator edits this)
- `01-design/`: Project 1, done. Persona/tone, flows, scripts, example dialogues, journey map, NLU + handoff spec. **Read the relevant files before designing anything that depends on them.**
- `02-prototype/`: Project 2. Sam on the Claude Agent SDK (`agent/sam.py`, `agent/tools.py`, `agent/mock_data.json`, `agent/prompts/system_v1.md`), test harness (`harness/run_tests.py`, `harness/scenarios.yaml`), results (`results/v1/`), demo page (`demo/template.html`, `harness/build_demo.py`)
- `03-usability-ab/`: Project 3
- `04-compliance-risk/`: Project 4

## Hard rules

1. **Never fabricate research data or present simulated data as real.** Anything produced by simulated users must be labelled "simulated" everywhere it appears, including chart titles and the report summary.
2. **Never invent regulatory facts.** For Australian law and regulation, cite only instruments you are confident exist, name them precisely, and avoid section numbers unless certain. Add a line that the document is a portfolio exercise, not legal advice, and that references should be checked against current versions.
3. **Fictional brand.** Never use a real insurer's name, logo or branding.
4. **Don't commit, push, or touch git.** Don't delete files you didn't create. The orchestrator handles git.
5. **Memory limit:** this PC runs low on memory. Each Sam conversation in the harness spawns 2 Claude Code processes. Never run more than **2 conversations at once** in total, and check with the orchestrator before any long run (more than ~20 conversations).
6. **No API key exists.** Claude calls go through the Claude Agent SDK (`claude_agent_sdk`), which uses the Claude Code login. Install Python packages with `uv pip install --system --system-certs <pkg>` (plain pip downloads get corrupted on this machine).
7. **Eddie's preferences:** "one link and play" deliverables (static pages, Markdown that renders on GitHub, single HTML files), no setup for the reader. Concise, scannable documents. Plain Australian English, short sentences, active voice.
8. Platform is Windows 11; shell is Git Bash. Use absolute paths.

## Loop roles

- **Planner** writes or revises `<project>/PLAN.md`: deliverables (exact file paths), steps, and **acceptance criteria** a reviewer can check one by one. On a revision round, read the latest `REVIEW-*.md` and address each issue.
- **Writer** implements PLAN.md exactly. Ends by listing the files created or changed and any step it could not complete, with why.
- **Reviewer** checks every acceptance criterion against the actual files (open them, run scripts where cheap). Writes `<project>/REVIEW-<stage><round>.md` with a verdict line `VERDICT: PASS` or `VERDICT: FAIL`, then a numbered list of issues (file, what's wrong, what to change). A PASS means it is good enough to show a hiring manager.
