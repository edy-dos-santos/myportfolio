# FNOL case study: handoff

Last updated: 2026-10-29. Read this first. Rules for agents are in `AGENT-BRIEF.md`.

## Summary

Four projects for a Conversational AI Designer application. One scenario, one fictional insurer (Wattle Car Insurance), one assistant called Sam.

| Project | Status | Where |
|---|---|---|
| 1. Design: flows, persona, scripts | Done. On GitHub in PR #2 | `01-design/` |
| 2. Working prototype + test logs | Done. v1 and v2 runs complete (44 each). Final write-up passed review (round 2) | `02-prototype/` |
| 3. Usability and A/B test (simulated) | Done. Simulated run 20 of 20. Post-run write-up passed review (round 2) | `03-usability-ab/` |
| 4. Compliance and risk layer | Done. Passed review | `04-compliance-risk/` |

## Where things are

- **On GitHub:** only Project 1, in PR #2: https://github.com/edy-dos-santos/myportfolio/pull/2 (branch `fnol-case-study`). Nothing is merged to `main`.
- **On this PC only:** Projects 2, 3 and 4, `PROGRESS.md` and `AGENT-BRIEF.md`. Local path: `C:\Users\edydo\myportfolio\projects\fnol-case-study\`.
- **Nothing has been committed or pushed since Project 1.** Eddie asked for no pushes until he says so.

## Project 1: design (done)

Persona and tone guide, six flow diagrams (Mermaid), prompt inventory, example dialogues, journey maps, NLU and handoff spec. Folder `01-design/`. Mermaid diagrams not yet checked on GitHub.

## Project 2: prototype (done except publishing)

**What it is:** Sam, built on the Claude Agent SDK (Opus 5.5). Six simulated insurer tools, a simulated customer (Haiku 5.5), an LLM judge (Opus 5.5), and automatic tool checks. 44 scenarios.

**Results** (all simulated; judged by an LLM):

| Version | Passed | Notes |
|---|---|---|
| v1 (first prompt) | 37 as first recorded, 39 corrected | 2 checks excused: the customer asked for a person |
| v2 (new prompt + code gate) | 40 | Same 44 scenarios, all run on the final code |

- Over-promising: 13 → 1. Hallucination: 21 → 3. Advice: 8 → 2.
- **Flow misses rose: 20 → 24.** Tone misses rose: 7 → 9. v2 also has 2 privacy flags, not yet reviewed.
- EM02 (shaken, hit-and-run) still fails in v2.
- The confirmation gate (`prepare_claim` then `create_claim`) stops Sam lodging a claim before the customer confirms the latest read-back. It fixed the v1 failure in HP08.

**Files:**
- Sam code: `02-prototype/agent/sam.py`, `tools.py`, prompts in `agent/prompts/`
- Results: `02-prototype/results/v1/` and `results/v2/`. Set-aside runs: `results/v1/invalid/` (test faults, do not publish) and `results/v2/smoke-pre-fix/`
- Write-up: `02-prototype/README.md`, `analysis/failure-analysis.md`, comparison in `analysis/compare.md`
- Demo page: `02-prototype/demo/index.html` (built locally, not published)

**Still to do:**
1. Look at the 2 v2 privacy flags and the EM02 failure in the transcripts, and state them in the write-up.
2. Optional: rejudge 7 v1 conversations to test judge consistency (`run_tests.py v1 --rejudge --only DS01,AD03,EM05,ER03,HP08,EM01,AD05`).
3. Publish the demo (not done).

## Project 3: usability and A/B test (simulated pilot)

**What it is:** form-first (variant A) vs story-first (variant B) capture, with 10 simulated personas, each run through both variants (20 conversations). Simulated participants only, labelled "simulated" everywhere. The real-study kit for 8–10 people is in `03-usability-ab/real-study-kit/`.

**Status:** 16 of 20 done (P01 to P08, both variants). P09 and P10 were running when this was written. Check `results/simulated/transcripts/` for the count; the report's recommendation must be read only once all 20 are in.

**Still to do:**
1. Finish P09 and P10 if not complete: `python run_ab.py --only P09-A,P09-B,P10-A,P10-B --parallel 1`
2. Add the persona-drift limitation: in the first test conversation, the simulated participant changed a fact (the lights), which lowered its score. Read each facts-correct miss against its transcript after the run.
3. Keep the "Not measured" caption on the time chart: the time figures are modelled, not measured.
4. The report rebuilds at the end of the run. Check `README.md` and `report.html` afterwards.

## Project 4: compliance and risk (done)

19 risks, 30 controls, escalation matrix, review checklist, a worked example, and 17 Australian references in approved wording. Two review rounds; round 2 passed (41/41 checks). Folder `04-compliance-risk/`. Start with `README.md`.

## Before anything is pushed (blockers)

1. **Insurer names.** `02-prototype/harness/redact.py` and `harness/test_tools.py` contain real insurer names as match patterns. A push would publish them. Decide: keep them out of the published files, or remove them. Results are already masked.
2. **Grep before push.** Check all files for insurer names, including `results/v1/invalid/` and `results/v2/smoke-pre-fix/`, which were not masked.
3. **Exclude from push:** `__pycache__/` folders and `results/v1/invalid/`.
4. **Account.** Paperclip was linked to another GitHub account. It must be connected as `edy-dos-santos` before it can see the repo.

## Project 2 final write-up: review status

- Planner (Opus) wrote `02-prototype/PLAN-FINAL.md`. Writer (Haiku) applied it to `analysis/failure-analysis.md` (new section 9, renumbered 10 and 11) and `README.md`.
- Reviewer (Sonnet) round 1: **FAIL**, see `02-prototype/REVIEW-FINAL-1.md`. Quotes and numbers check out. The claims do not:
  1. Section 9 says safety and escalation counts "did not change". Escalation findings changed severity: v1 all minor, v2 major (EM04 twice, AD06). The four v2 majors differ from v1's four.
  2. AD06 has a minor HALLUCINATION at turn 6 ("your request to sort out the repairer this week is noted"), which the write-up omits.
  3. Overstated causality ("judge tags moved the way the fixes aimed", "within run-to-run variation" when variation was never measured). Average tone fell 4.75 to 4.61 and is omitted.
  4. Verification detail: in AD06 Sam sent a wrong date of birth and mobile, which the stub ignored because the policy number matched. In HP06 Sam sent the policy number only. Also, the ES01 quote comes from `results/v1/invalid/`, not the transcript.
- **Next:** planner round 2 for these fixes, then writer round 2, then reviewer round 2.
- **Open decision:** the identity-check gap in the test stub (`agent/tools.py`) caused the two privacy flags. Fix and rerun AD06 and HP06, or document it as a known limit. Not decided.

## Final state (2026-10-30)

- **Projects 1, 2, 3, 4:** all written and reviewed. Nothing is committed or pushed.
- **Project 3 result (simulated):** variant B (story-first) had task success for 10 personas against 8 (10 paired personas). The rule says recommend B. Only 7 of 10 preference answers exist (P04, P05, P06 are missing). That's a decision for Eddie.
- **Decisions still open for Eddie:**
  1. Run the 3 missing preference answers (3 Claude calls). They can't change the recommendation.
  2. The identity gap in the test stub: it let Sam share car details in AD06 and HP06. Fix and rerun those two, or document it as a known limit.
  3. Publishing: a new repo, or the existing PR #2 branch. Insurer-name check first (see Before anything is pushed).

## Latest (2026-10-30): documentation update, nothing pushed

- **Identity-gap fix (Project 2): done.** A policy number that has just failed a date-of-birth or mobile check no longer verifies (v2 only, `strict_identity` guard). Offline tests pass (22, 59, 14). Reruns: AD06 and HP06 were rerun, but neither rerun triggered the new check, so the fix is supported only by the offline tests. v2 still passes 40 of 44 (failing: EM02, EM04, DS03, HP06). The privacy flags are gone because of Sam's different paths in the reruns, not the fix.
- **Project 2 write-up:** final, reviewed (round 2 PASS). Identity write-up reviewed (PASS), with two wording fixes applied.
- **Project 3 (simulated):** 20 of 20 done. Recommendation: variant B (story-first), 10 personas against 8. Post-run write-up reviewed twice (PASS). Only 7 of 10 preference answers exist.
- **Project 4:** done, reviewed.
- **Git:** nothing committed or pushed. Staging was started and then fully unstaged. `origin/fnol-case-study` is still at Project 1 (`2c11916`).

### Decided
- Push to the existing PR #2 branch (`fnol-case-study`), not a new repo.

### Still open
1. **Preference answers for P04, P05, P06** (3 Claude calls). Deferred until Eddie is back. They can't change the recommendation.
2. **Push exclusions:** leave out `02-prototype/PLAN.md` and `02-prototype/REVIEW-1-1.md` (they contain real insurer names), `02-prototype/results/v1/invalid/`, `02-prototype/results/v2/smoke-pre-fix/`, `02-prototype/results/v2/pre-identity-fix/`, and all `__pycache__` folders. `harness/redact.py` and `harness/test_tools.py` hold the name patterns on purpose. Eddie to confirm whether those stay in the push.
3. **Insurer-name scan** must be re-run after exclusions, before any push.
4. **Missing G11 gap decision:** whether to add the HP06 issue (a policy number alone verifies) to Project 4's gap table.
5. **Paperclip:** it must be connected to GitHub as `edy-dos-santos` before it can see the repo.

### Commands once Eddie says go
- `git add projects/fnol-case-study` then unstage the excluded paths above, then commit with the Co-Authored-By trailers, then `git push origin fnol-case-study`.

## Repo and handoff

- Repo: `https://github.com/edy-dos-santos/myportfolio`
- Branch: `fnol-case-study` (PR #2, Project 1 only until pushed)
- Folder links once pushed: `.../tree/fnol-case-study/projects/fnol-case-study/<01-design | 02-prototype | 03-usability-ab | 04-compliance-risk>`
- Option A (recommended): a new repo `fnol-case-study` with only this folder. Option B: push to the existing branch. Not decided.

## Rules and tools for running tests

- At most 2 Sam conversations at once; 1 at a time is safer on this PC. Each conversation starts 2 Claude Code processes.
- Claude Code stops background runs when memory is low. Run in the foreground in batches of 4–6 (about 75 s per conversation). To turn the stop off: start Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`.
- Install Python packages with `uv pip install --system --system-certs <package>`. Plain pip corrupts downloads on this machine.
- No Anthropic API key here. Test runs use the Claude Code login.

## Log of main steps

| Date | Step | Result |
|---|---|---|
| 10-28 | Project 1 design, PR #2 | Done |
| 10-28 | Project 2: v1 run, planning, v2 build, reviews | v1 44/44 valid; v2 plan and build reviewed, PASS |
| 10-28 | Project 3: plan, build, two review rounds | Round 2 PASS |
| 10-28/29 | Project 4: plan, build, two review rounds | Round 2 PASS; polish fixes applied |
| 10-29 | Project 2: v2 run on final code | 44/44. Insurer names masked; demo built |
| 10-29 | Project 3: simulated run | 12/20. Stopped at P07-A |
