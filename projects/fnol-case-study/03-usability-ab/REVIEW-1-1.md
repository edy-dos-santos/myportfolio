VERDICT: FAIL

Stage 1, round 1. Reviewer: Sonnet. Scope: criteria 1-19 against the files; 20-26 pending the run. No Sam conversation was run. Commands run: diffs, `python test_metrics.py` (OK, 27 tests), `python run_ab.py --help`, `python build_report.py` (exit 0), `python chat_variant.py --help`, the criterion 6 import, SVG XML parse, greps, and a YAML/JSON/prompt comparison against PLAN.md.

The build is close and mostly sound. It fails on one stated criterion (17, the variant leak) plus three code defects that would distort the real run or the real study. All four fixes are small.

## Criteria table

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | story prompt = system_v1 | Met | `diff` prints nothing. |
| 2 | form prompt differs only at 24c24, text as in plan | Met | One hunk `24c24`; new line matches section 4 word for word. |
| 3 | Protected files unchanged | Met, partly unverified | No git, so no baseline diff. `tools.py` and `mock_data.json` are dated 13:25 (before the writer). `sam.py` and `run_tests.py` are dated 18:00, before the first writer file (18:03). Likely an orchestrator edit, but the writer's file list wasn't supplied. Orchestrator to confirm. PROGRESS.md was edited at 18:15 (orchestrator). |
| 4 | personas.yaml: 10 personas, alternating order, all fields | Met | `yaml.safe_load` of the file equals the YAML block in PLAN.md exactly. Orders AB/BA alternate. |
| 5 | ab_policies.json: 12 policies, no collision, GT ids exist | Met | JSON equals the plan block. No overlap with mock_data policies. Every persona's policy and rego is present. |
| 6 | Import registers abA, abB; WTL456810 present; no conversation starts | Met | Printed `['abA', 'abB', 'v1', 'v2'] True`. Import only creates an empty temp dir. |
| 7 | test_metrics.py OK, covers 8.4 | Met | `OK (27 tests)`. Every 8.4 check is present. No test for `recommend` rules 1-4 (see issue 6). |
| 8 | No args -> exit 2; parallel capped at 2 | Met (code read) | Not run without args, per instruction. `sys.exit(2)` after usage; `parallel > 2` prints WARNING and uses 2. `--help` works. |
| 9 | Skip finished, atomic writes, back-fill, calls build_report.main | Met, with a gap | All present (`write_json` and `.md.tmp` use `os.replace`). Gap: `--rerun` doesn't refresh an existing preference file (issue 7). |
| 10 | Reuse by import; prompts verbatim; judge blind to variant | Met | Imports `sam`, `tools`, `run_tests.render/customer_reply`. All four prompts equal the PLAN text. `judge()` sees only `render(transcript)`. |
| 11 | P01-A.json from smoke test, schema 7.4 | Pending run | `transcripts/` is empty. Code path read: the record has every 7.4 key; `ms` is an int per turn (opening 0); the questionnaire is clamped to int with an `error` fallback; `data_source` is "simulated"; the `.md` starts with the simulated label. One flaw to fix before the run: issue 3 (the participant doesn't see Sam's last message on a handoff). |
| 12 | build_report exits 0, writes all files, CSV header and `data_source` | Met | Exit 0. CSV, JSON, preferences CSV, README, report.html and 6 SVGs written. CSV header equals the 8.3 list in order (BOM present). No rows yet, so the `data_source` check is pending. |
| 13 | Simulated labelling | Met | Banner and blockquote use the 9.2 wording. All 6 chart titles start "Simulated: ". JSON has `data_source: simulated`. Comments tagged "(simulated)". `Simulated: ` appears 12 times in report.html. |
| 14 | report.html structure and hygiene | Met by static check | 10 sections in order. No `<script`, `<link` or `http`. `prefers-color-scheme` and a body background are present. Tables sit in `overflow-x:auto`. Not opened in a browser, so the 375px and console checks are by inspection only. SVG text shrinks to about 7px on a phone (issue 9). |
| 15 | SVGs | Met | All 6 parse as XML. Each has `<title>`, `<desc>`, `role="img"`, a dark media query and text value labels. README links resolve. |
| 16 | README renders; required content | Met | Only raw HTML is the first comment. Hypothesis, rule, line-24 text, limitations, reproduce commands, links and a files table are all present. |
| 17 | chat_variant --help; never prints the variant; saves to results/real with `data_source: real` | **Not met** | `--help` works and the save path/`data_source` are right. But `print(f"Session saved to {path}")` prints `...R01-A.json` to the participant's terminal. That shows the variant letter (issue 1). |
| 18 | Kit: 8 files, content, disclaimers, cards, counterbalancing, Privacy Act | Met | All 8 files present. Cards X/Y match WTL456811/812 in the policies. 10 rows use the 4 orders (R09-10 repeat 1-2). Consent names the Privacy Act 1988 (Cth), the APPs and the National Statement, no section numbers. `data-template.csv` header = 8.3 + `card`, `moderator_notes`. Every .md ends with the disclaimer. |
| 19 | No real brands, AU English, no emoji | Met | Grep for real insurer names: none. No emoji. No US spellings (only CSS `color`). |
| 20-26 | Data-dependent | Pending run | No transcripts or preferences yet. |

## Issues (most serious first)

1. **`chat_variant.py` line 93: leaks the variant to the participant.** The end-of-session line prints the file path `R01-A.json`. The first chat reveals its letter, and the second is then obvious. This breaks blinding and criterion 17. Fix: print `Session saved.` only. Keep the path for the moderator in a log or stderr line the participant doesn't see.

2. **`metrics.py` `summarise` / `recommend` rule 1: compares unpaired counts.** `successes` is summed over all rows per variant, including personas with only one variant finished. After a partial run or an error, `n >= 6` pairs can pass while A and B have different row counts. Then rule 1 can fire on a gap that is only missing rows. Rule 2's time and CSAT means have the same problem. Fix: compute rules 1 and 2 only on personas in `_complete_pairs`. Add a test that proves it.

3. **`run_ab.py` `run_conversation`: the participant never sees Sam's last message on a handoff or turn cap.** On `state.handed_off` the loop breaks before `customer_reply`. The questionnaire is then the next message in the participant's session. P08 (Helen) is the persona most likely to be handed over, and her SEQ/CSAT would rate a chat whose ending she never saw. Fix: before the questionnaire, if the last transcript entry is Sam's, send it to the participant first (a `customer_reply` call whose answer is discarded, or prefix the questionnaire with "Sam's last message was: ..."). Do this before the full run.

4. **`chat_variant.py` timing: the first participant `ms` is inflated.** `shown_at = t0` is set before the SDK client starts, so the first message includes start-up time and card reading. The analysis plan uses these `ms` values as measured time on task. Fix: set `shown_at` after the "Chat with Sam" line prints and record the first message separately, or have the plan drop turn 1 from time. Also say in `06-analysis-plan.md` that the column `est_customer_seconds` holds measured time in the real data. The same name for modelled and measured time invites mixing them. Suggest a `customer_seconds_source` column or a distinct name.

5. **Wording that overclaims or misleads (README/report text in `build_report.py`).**
   - "These are the Project 1 design" (What we tested) is true for B only. A is new. Say: "B is the Project 1 design. A is the comparison."
   - "Hypothesis (pre-registered)" and "pre-registered rule" are stronger than the facts. The plan and the prompts were written by the same people who run the test. Say "written before the run" and give the date or a commit once committed.
   - The form-first prompt tells Sam to confirm facts already given. So more questions and more repeat questions in A are partly built into the prompt, not discovered. State this in Limitations. A fair reader will ask whether the study measures the prompt text or the strategy.
   - The "Summary" and "Next" sections should say once, in the summary box, that the simulated result tests the design of the study. It doesn't show how real people behave. The banner does this, but the recommendation box says "Simulated pilot result: variant B ..." and could be quoted alone. The wording is good. Keep "Confirm with the real study".

6. **`test_metrics.py`: the decision rule is not tested.** Only the "Not enough data" branch is covered. The portfolio pitch is the pre-registered rule. Add four small cases (rule 1 wins, rule 2 wins, rule 3 wins, rule 4 no winner), plus a case where CSAT blocks rule 2, and the issue 2 case. Also test `check_facts` on a null ground truth and a wrong location.

7. **`run_ab.py --rerun` leaves stale preferences.** Rerunning P03-A replaces the transcript, but `preferences/P03.json` already exists and is skipped, so it describes the old chat. Fix: when a selected persona is rerun, delete or redo its preference file.

8. **Kit consistency.**
   - `01-screener.md` Q10 disqualifies anyone not comfortable with recording "only if you agree". Recording is optional in `02-consent.md`, so this question screens out nobody sensibly and may exclude people who would take part with notes only. Remove it or reword: "Are you OK with notes being taken?"
   - `03-moderator-script.md`: the 45-minute plan has no buffer (blocks total exactly 45) and the 10-minute task stop is not enforced anywhere. Add a 5-minute buffer, or say 50 minutes.
   - `README.md` timeline step 5 says "Fill in the simulated pilot comparison" without saying what to compare. Say: "Compare real and simulated direction on each metric."
   - Participants are told to "chat as you would if this had really happened" while using a card. Fine, but tell the moderator what to do if Sam asks for a date of birth (cards give the policy number only, which is enough; say so).

9. **`build_report.py` charts on phones.** The SVGs use a 640px viewBox. At 375px wide the 12-13px text scales to about 7px. Either raise the base font in the SVG (about 16px) or let the figure scroll horizontally. Also, `stroke-width="3"` on the mean tick in `svg_strip` is overridden by the `.ab-line` CSS (2px), so the tick is no heavier than the other lines. Minor.

10. **Heuristic limits, worth one sentence in Limitations.** `mentions` keywords are broad ("today", "saturday", "night"). For vague personas (P09 Tane, P05 Sofia), a legitimate follow-up for a precise time counts as a "repeat". This hits story-first's gap questions harder, which cuts against the hypothesis. The judge count is the cross-check. The existing `direction_note` covers disagreement but not this bias.

11. **Housekeeping.**
    - The README has a final section headed "Footer", which reads oddly on GitHub. Use "Data and files".
    - `__pycache__/` was created in `03-usability-ab/`. Leave it out of git.
    - Criterion 3: orchestrator to confirm that the 18:00 changes to `sam.py` and `run_tests.py` are theirs.

## Hiring-manager view

- **Study design: sound.** One variable (line 24), counterbalanced order, identical Sam, tools and policies. A fixed pass/fail ground truth is checked against the actual `create_claim` input, so success is not self-reported. The decision rule is written down before the data, with a "not enough data" exit and a default. The "Limitations" section is honest (same model family, no memory between chats, positive LLM raters, modelled time). This is above the usual portfolio standard.
- **Simulated labelling: strong.** Banner, chart titles, "(simulated)" tags, a `data_source` column and a "do not mix" step in the Power BI notes. I found no place where simulated data reads as real. The main risk is the quoted recommendation sentence; its prefix and suffix already cover it.
- **Fair metrics: mostly.** Issue 5 (the question and repeat counts follow from the prompt) and issue 10 (keyword bias) are the weak spots. Estimated time depends on Sam's word count, which is also a prompt effect. Say so; don't hide it.
- **Real-study kit: usable.** It covers screener with quotas, consent with the right Australian references and tick boxes, a timed script with a distress protocol, cards, counterbalancing with exact commands, a questionnaire, an analysis plan (exploratory tests flagged as such) and a data template. A researcher could run it after fixing issues 1, 4 and 8. The placeholders ([name], [retention period]) are honest.
- **Writing:** short sentences, active voice, Australian spelling throughout the kit and README. The generated README is long because every chart has a data table; fine for the GitHub view since the tables sit under the charts.

## What is needed for PASS

Fix issues 1 to 4 and 6 (all small), apply the wording changes in issue 5, and re-run `python test_metrics.py` and `python build_report.py`. Issues 7 to 11 can be done in the same pass. Criterion 11's data part stays pending until the smoke test.
