# Real-study kit: story-first vs form-first (Wattle Car Insurance)

This kit runs a small usability study with real people. It tests the two capture strategies for Sam, the Wattle Car Insurance claims chat. Sam is fictional.

Read this first. It explains the whole study. The other files are the tools you use on the day.

## Goal

Decide which capture strategy to keep for Sam's first-notification-of-loss flow, or whether the real study says no clear winner.

## Research questions

1. Does story-first (B) reduce effort (fewer questions, less time) without hurting accuracy (task success)?
2. Who prefers which chat, and why?

## Design

- Within-subjects. Each participant does two tasks: one with variant A (form-first) and one with variant B (story-first).
- Two task cards, X and Y. Each participant uses a different card for each variant, so card and variant are mixed.
- 8 to 10 participants (R01 to R10). Orders are counterbalanced (see `04-task-cards.md`).
- Participants are recruited with `01-screener.md`. Quotas keep the group mixed in age, digital confidence and claims experience.
- Tasks use fictional policies and cars. Participants play a card. They do not report their own accident.

## Session

- Length: 50 minutes, in one session. The timed plan is in `03-moderator-script.md`.
- Setup: a laptop running `chat_variant.py` in a terminal. The participant types. The moderator sits beside them.
- Screen and audio are recorded only if the participant ticks the recording box on `02-consent.md`.
- Participants can stop at any time and keep the incentive.

## Roles

- Moderator: runs the script, reads the tasks, asks the neutral prompts and keeps time.
- Note-taker: fills the note grid in `03-moderator-script.md` and marks quotes. Does not speak during tasks.

## Timeline

1. Finalise this kit and check the pilot results (`../README.md`).
2. Do a dry run with a colleague who is not in the study. Test `chat_variant.py` on the laptop.
3. Recruit and book 8 to 10 participants.
4. Run the sessions, one at a time. Save each session file after the session.
5. Analyse with `06-analysis-plan.md`. Compare the direction of each metric (task success, SEQ, time, questions, repeat questions, CSAT, preference) in the real and simulated data. Note where they agree and where they differ.
6. Decide, and record the decision in the main case study.

## Materials

| File | Use |
|---|---|
| `01-screener.md` | Qualify and quota participants |
| `02-consent.md` | Participant information and consent. Signed before the session |
| `03-moderator-script.md` | Timed script, prompts and note grid for the session |
| `04-task-cards.md` | Cards X and Y, counterbalancing table, and the command for each session |
| `05-post-task-questionnaire.md` | Questions after each task and after both |
| `06-analysis-plan.md` | Metrics, tests, Power BI steps and the decision rule |
| `data-template.csv` | Blank data file. One row per session, same columns as the simulated results |

## Link back to the simulated pilot

The simulated pilot is in `../README.md`. It used LLM personas, not people. It was run to de-risk this study design. It is not user research, and its results do not replace this study.

## Changes after the simulated pilot

The simulated pilot found three things to change before the real study:

1. Simulated personas drift from their briefs. Add a stricter in-character check before each run.
2. Ground-truth checks must cover conditions the participant mentions later, such as night driving or a broken headlight.
3. The form-first question can plant doubt the participant did not have. Test that question's effect on its own.

Portfolio exercise, not legal or ethics advice. Check references against current versions before use.
