# Project 3 plan: story-first vs form-first, a simulated pilot (round 2)

## Round 2 changes

Source: `REVIEW-1-1.md` (VERDICT: FAIL). Numbering below is the reviewer's. The round-1 files stay as they are, except for the changes listed here. **The writer (Haiku) changes only what this section lists.** The hard limits in section 2 still apply. In particular: **do not run any Sam conversation**, not even the smoke test. The smoke test (step 6 of section 12) is now the orchestrator's job, after this round passes.

Paths are relative to `03-usability-ab/` unless stated.

### Decisions at a glance

| # | Issue | Decision |
|---|---|---|
| 1 | chat_variant.py prints the variant | Fix |
| 2 | Decision rule uses unpaired counts | Fix |
| 3 | Participant misses Sam's last message on handoff | Fix |
| 4 | Real-study timing starts too early; time column name | Fix |
| 5 | Wording that overclaims | Fix (all four bullets) |
| 6 | Decision rule not tested | Fix |
| 7 | `--rerun` keeps stale preferences | Fix |
| 8 | Kit consistency (screener, buffer, timeline, date of birth) | Fix (all four bullets) |
| 9 | Chart text too small on phones; mean tick width | Fix |
| 10 | Keyword heuristic is biased against B | Accept as a documented limitation (wording added) |
| 11 | Housekeeping | "Footer" heading: fix. `__pycache__/`: accept, orchestrator handles git. Criterion 3: met (see below). |

### Issue 1: `chat_variant.py` leaks the variant (criterion 17)

Fix in `chat_variant.py`:
1. Add a function `finish_session(record, out_dir=None)`. It calls `save_session(record)` (use `out_dir` instead of `results/real/` when given, for tests). It then appends one line to `<out_dir>/session_log.txt` (default `results/real/session_log.txt`): `<ISO time>\t<participant>\t<variant>\t<file name>`. It prints exactly `Session saved.` and nothing else. It returns the saved path.
2. In `chat()`, the `finally:` block calls `finish_session(record)`. Delete the line `print(f"Session saved to {path}")`.
3. The moderator types the command (which contains `--variant A`). So, once the SDK client is ready and before printing `Chat with Sam...`, clear the screen: `os.system("cls" if os.name == "nt" else "clear")`.
4. No other `print` in `chat_variant.py` may include the variant letter, the variant name, the prompt file name, the session path or the conversation id. Error messages too: if the SDK raises, print `Sorry, the chat stopped. Please tell the researcher.` and let `finally` save the session.
5. `real-study-kit/03-moderator-script.md`, Task 1 and Task 2: add "Type the command before the participant looks at the screen. The screen clears when the chat starts. After the session, check the file name in `results/real/session_log.txt`, not on screen."

New test (in the new `test_offline.py`, see issue 6): call `chat_variant.finish_session(record, out_dir=<temp dir>)` with a record for `R01`, variant `A`, under `contextlib.redirect_stdout`. Assert the captured output is exactly `Session saved.\n`. Assert the file `R01-A.json` exists in the temp dir with `data_source` = `real`, and `session_log.txt` has one line. Also a static check: read `chat_variant.py` as text and assert it does not contain `Session saved to`.

### Issue 2: decision rule compares unpaired counts (`metrics.py`)

Fix in `metrics.summarise(rows)`: keep the existing per-variant blocks (they feed the charts and tables). Add a new key `"paired_basis"`, computed only on personas in `_complete_pairs(rows)`:

```python
"paired_basis": {
  "n_pairs": <int>,
  "A": {"successes": <int>, "est_customer_seconds_mean": <float or None>, "csat_mean": <float or None>},
  "B": {... same ...}
}
```

Means skip blanks, as `_stats` does. Fix in `metrics.recommend(summary, prefs)`:
- The "not enough data" check uses `summary["paired_basis"]["n_pairs"]` (still fewer than 6 means not enough).
- Rule 1 compares `paired_basis[...]["successes"]`.
- Rule 2 uses `paired_basis[...]["est_customer_seconds_mean"]` and `["csat_mean"]`. Keep the existing maths: difference / slower mean >= 0.15, and the faster variant's CSAT mean >= the slower one's minus 0.5.
- Rule 3: count only preferences whose `persona_id` is in the complete pairs. The threshold stays "at least 7" (as written before the run).
- The reason sentences keep their prefix "Simulated pilot result:" and end with `END_SENTENCE`. Rule 1's sentence adds "(paired personas only)".

Section 8.5 of this plan now says: "All four rules use only personas with both variants complete."

`build_report.py`: the Method text for the decision rule adds the same sentence. No other change for this issue.

### Issue 3: the participant must see Sam's final message (`run_ab.py`)

Fix in `run_ab.py`:
1. Add a pure function `questionnaire_message(transcript)`. If the last transcript entry has `role` `"sam"`, return `"Sam's last message to you was:\n\n" + <that text> + "\n\nThe chat has ended there.\n\n" + QUESTIONNAIRE_PROMPT`. Otherwise return `QUESTIONNAIRE_PROMPT` unchanged.
2. In `run_conversation`, replace `customer_reply(cust, QUESTIONNAIRE_PROMPT)` with `customer_reply(cust, questionnaire_message(transcript))`. The retry line ("Reply with only the JSON object.") is unchanged.
3. `QUESTIONNAIRE_PROMPT` itself stays verbatim (criterion 10).
4. This covers the handoff case and the empty-reply case. On the turn cap and on `[END]`, the participant has already seen Sam's last message, so the prompt is unchanged.

New tests (in `test_offline.py`): a transcript ending with a Sam entry `"A person will join you now."` gives a message that contains that text and ends with `QUESTIONNAIRE_PROMPT`. A transcript ending with a customer entry gives exactly `QUESTIONNAIRE_PROMPT`.

### Issue 4: real-study timing start point and time column name

Fix in `chat_variant.py`:
1. Set `shown_at = time.perf_counter()` immediately after the screen is cleared and `Chat with Sam. Type 'quit' to end the chat.` is printed. Remove `shown_at = t0`. SDK start-up time no longer counts.
2. The first participant turn keeps its `ms` (reading the screen and typing the opening is real time on task). The card is read before the command starts (see the kit change below).

Fix the column name problem with one new CSV column, `time_source`:
- `metrics.py`: add `time_source` to the CSV column list **directly after `est_customer_seconds`**. `conversation_row` sets it to `"modelled"` for records with `data_source` = `simulated`, and `"measured"` for `data_source` = `real`.
- For real records (`data_source` = `real`), `conversation_row` sets `est_customer_seconds` = sum of participant `ms` over customer turns / 1000, rounded to 1 decimal, instead of the word-count model. Simulated records are unchanged.
- `real-study-kit/data-template.csv`: header = new 8.3 list (with `time_source`) + `card`, `moderator_notes`.
- `real-study-kit/06-analysis-plan.md`, metrics section: add "In the real data, `est_customer_seconds` holds measured time (participant `ms` from `chat_variant.py`, from the moment the chat prompt appears). `time_source` is `measured`. In the simulated data it is a model from word counts, and `time_source` is `modelled`. Never compare or average the two. In Power BI, filter on `data_source` and `time_source`."
- `real-study-kit/03-moderator-script.md`, Task 1 and Task 2: "Let the participant read the card first. Start the command only when they say they are ready."
- Section 8.3 table of this plan: add the row `time_source` | `modelled` (simulated) or `measured` (real).

New tests (in `test_metrics.py`): the fixture row has `time_source` = `modelled`. A copy of the fixture with `data_source` = `real` and customer `ms` values of 0, 10000, 20000, 5000, 3000, 4000, 2000 gives `est_customer_seconds` = 44.0 and `time_source` = `measured`. The existing "keys equal the CSV column list" test now includes `time_source`.

### Issue 5: wording (`build_report.py`, `metrics.py`)

Change exactly these strings (and the same text in the README template, since both come from `build_blocks`):

| Where | Old | New |
|---|---|---|
| `build_report.py` What we tested (around line 332) | "These are the Project 1 design." | "B is the Project 1 design. A is the comparison, written for this test." |
| `build_report.py` summary box title (around line 326) | "Recommendation (pre-registered rule)" | "Recommendation (rule written before the run)" |
| `build_report.py` method (around line 344) | "**Hypothesis (pre-registered):**" | "**Hypothesis (written before the run, 28 October 2026):**" |
| `build_report.py` method heading (around line 367) | "Pre-registered decision rule" | "Decision rule (written before the run)" |
| `build_report.py` next section (around line 469) | "Pre-registered rule, as applied: " | "Decision rule, as applied: " |
| `metrics.py` `recommend` docstring | "Pre-registered decision rule" | "Decision rule written before the run" |

After the method heading, add one sentence: "The same team wrote the plan, the prompts and this rule, and runs the test. The rule is fixed in `PLAN.md` before any full run. It is not registered with a third party." After the full run, the orchestrator adds the commit id; the writer does not.

Add to the **Limitations** list (section 8 of the report), as new bullets:
- "Form-first's prompt tells Sam to ask each detail in turn and to confirm details already given. So some of A's extra questions and repeat questions are built into its prompt, not discovered by the test. The test compares two prompt texts that carry two strategies. It does not isolate the strategy from its wording."
- "Estimated time comes from word counts, so it rises with the length of Sam's messages. That is also a prompt effect."
- Issue 10 bullet (see below).

Add to the **Summary** box, once, after the recommendation sentence: "This simulated pilot tests the study design. It does not show how real people behave." Keep the recommendation sentence itself as it is ("Simulated pilot result: ... Confirm with the real study before changing the design.").

Grep check after the change: `grep -ri "pre-registered" 03-usability-ab --include=*.py --include=*.md --include=*.html` returns nothing except lines in `PLAN.md` and `REVIEW-*.md`.

### Issue 6: tests for the decision rule (`test_metrics.py`) and a new offline test file

Add a helper in `test_metrics.py`: `mk(pid, variant, success, est, csat)` returns a dict with at least `persona_id`, `variant`, `task_success`, `lodged_correct` (= success), `est_customer_seconds`, `csat`, and blanks (`""`) for every other `SUMMARY_METRICS` key. Personas are `T01`...`T10`. Then add these cases. Each one calls `recommend(summarise(rows), prefs)`.

| Case | Rows | Prefs | Expect |
|---|---|---|---|
| R0 not enough | 5 complete pairs | none | `None`, reason contains "Not enough data" |
| R1 rule 1 | 6 pairs; B succeeds in 6, A in 4; est and CSAT equal | none | `"B"` |
| R2 rule 2 | 6 pairs, all succeed; A est 200, B est 150; CSAT A 4.0, B 3.8 | none | `"B"` |
| R2-edge | as R2 but B est 170 (exactly 15%) and B CSAT 3.5 (exactly 0.5 lower) | none | `"B"` |
| R2-block CSAT | as R2 but B CSAT 3.4 (0.6 lower) | 4 B, 2 A | `None`, reason contains "no clear winner" |
| R3 rule 3 | 10 pairs, all succeed, est 200 v 190, CSAT equal | 7 A, 3 B | `"A"` |
| R4 no winner | 10 pairs, all equal | 5 A, 5 B | `None`, reason contains "Keep the current design (B)" |
| P paired-only | 6 complete pairs, all succeed, est 200 both, CSAT 4 both; plus 2 extra B-only rows (`T07-B`, `T08-B`) with success 1, est 50 | none | Not `"B"` (rule 1 and rule 2 must not fire on unpaired rows); `summary["paired_basis"]["n_pairs"]` = 6 |
| P-prefs | as R4 with 6 pairs, plus 7 B preferences of which 2 are for personas without a pair | 7 B (2 unpaired) | `None` |

Unless the table says otherwise, every preference dict uses the `persona_id` of a complete pair (`{"persona_id": "T01", "preferred_variant": "A"}` and so on). For every case where a variant is returned, also assert the reason starts with `"Simulated pilot result:"` and ends with `END_SENTENCE`.

Add two `check_facts` tests: with the P04 ground truth (`driver_match: null`), the `driver` result is `None` and `facts_checked` is 6. With the P01 fixture claim location changed to `"Logan Rd, Mount Gravatt"`, `location` is `False` and `facts_correct` is 6.

New file `03-usability-ab/test_offline.py` (plain `assert`, no pytest, prints `OK (n tests)`, runs with `python test_offline.py`). It imports `run_ab` and `chat_variant` (import starts no conversation, as criterion 6 shows). It holds the tests from issues 1, 3 and 7. It must never call `run_conversation`, `judge`, `preference`, `chat` or any SDK client.

### Issue 7: `--rerun` leaves stale preferences (`run_ab.py`)

Fix in `run_ab.py`:
1. Add a pure function `stale_preferences(todo_ids, rerun)`. `todo_ids` is the list of conversation ids that will run. If `rerun` is false, return an empty set. Otherwise return the set of persona ids (`"P03"` from `"P03-A"`).
2. In `main()`, after building `todo` and before running conversations: for each persona id from `stale_preferences(...)`, if `preferences/<pid>.json` exists, delete it and print `<pid> preference: removed (rerun)`. The preference loop then asks again once both transcripts exist.

New tests (in `test_offline.py`): `stale_preferences(["P03-A"], True)` = `{"P03"}`; `stale_preferences(["P03-A", "P03-B", "P05-B"], True)` = `{"P03", "P05"}`; `stale_preferences(["P03-A"], False)` = `set()`.

### Issue 8: kit consistency (`real-study-kit/`)

1. `01-screener.md` Q10: replace with "10. Are you OK with the researcher taking written notes during the session? Screen and audio recording is optional and only with your consent. *(Qualify: yes. Disqualify: no.)*" This matches `02-consent.md`, where recording is optional and notes are the fallback.
2. Session length becomes **50 minutes** (45 minutes of blocks plus a 5-minute buffer):
   - `03-moderator-script.md`: title "Moderator script (50 minutes)". Add a final table row `Buffer (overruns, questions) | 5 | 50`. Under Task 1 and Task 2, the 10-minute stop is already written; add: "Use a timer. At 10 minutes, type `quit` for the participant if they have not finished. Note 'stopped at 10 min' in the grid."
   - `01-screener.md` Q9 and Q12, `02-consent.md` ("about 45 minutes"), `README.md` (Length line): change 45 to 50.
3. `README.md` timeline step 5: replace "Fill in the simulated pilot comparison." with "Compare the direction of each metric (task success, SEQ, time, questions, repeat questions, CSAT, preference) in the real and simulated data. Note where they agree and where they differ."
4. `03-moderator-script.md`, "If Sam fails" part: add "If Sam asks for a date of birth or another detail that is not on the card, say: 'Use the policy number on the card. That is enough. If Sam needs more, make up a plausible answer.' Note it in the grid."

### Issue 9: chart text on phones (`build_report.py`)

1. In the shared SVG `<style>`: base `.ab-text` font size 16px, `.ab-title` 18px, value labels 15px. Keep `viewBox="0 0 640 H"`. Widen the left label column and raise row heights where needed so no label overlaps or is clipped (check each of the 6 SVGs by eye in a browser at 640px).
2. In `report.html` only: wrap each inline chart in `<div class="chart-scroll">`. CSS: `.chart-scroll { overflow-x: auto; } .chart-scroll svg { min-width: 520px; }`. At 375px the chart scrolls inside its box; the page itself still has no horizontal scroll (criterion 14). Text then renders at about 13px.
3. `svg_strip` mean tick: remove the `stroke-width="3"` attribute. Add a CSS class `.ab-mean { stroke: <text colour>; stroke-width: 4; }` (plus its dark-mode colour) and use `class="ab-mean"` on the tick.

### Issue 10: keyword heuristic bias (accepted as a limitation)

No code change. Reason: changing the `mentions` keywords now would be guesswork without data, and the judge's `reasked_facts_judge` already gives an independent cross-check. Documenting the direction of the bias is the honest fix. Add this Limitations bullet in `build_report.py`: "The repeat-question heuristic uses broad keywords such as 'today', 'saturday' and 'night'. For vague personas (P05, P09), a fair follow-up for a precise time counts as a repeat. This penalises story-first's gap questions more, so it works against the hypothesis. Compare with the judge's count."

### Issue 11: housekeeping

- `build_report.py`: rename the section heading "Footer" to "Data and files" (HTML and README). Section 9.2 item 10 of this plan now reads "Data and files". It stays the 10th section.
- `__pycache__/`: accepted. The writer must not touch git or add a `.gitignore`. The orchestrator excludes it when committing.
- Criterion 3: **met**. The orchestrator confirmed the 18:00 edits to `02-prototype/agent/sam.py` (tool-server connection check) and `02-prototype/harness/run_tests.py` (empty-reply check) are theirs. The writer must still not edit either file.

### Round 2 steps for the writer (in order)

1. Make the `metrics.py` changes (issues 2, 4, 5). Update `test_metrics.py` (issues 4, 6). Run `python test_metrics.py` until it prints OK.
2. Make the `run_ab.py` changes (issues 3, 7) and the `chat_variant.py` changes (issues 1, 4). Write `test_offline.py`. Run `python test_offline.py` until it prints OK. Run `python chat_variant.py --help` and `python run_ab.py --help` only.
3. Make the `build_report.py` changes (issues 2, 5, 9, 10, 11). Run `python build_report.py`; it must exit 0.
4. Make the kit changes (issues 1, 4, 8).
5. Run the grep check from issue 5.
6. Do **not** run `run_ab.py --only ...` or any other command that starts a Sam conversation.
7. Report back: files changed, test output lines, any step not done and why.

### Acceptance criteria changes

Existing criteria 1-26 in section 14 still apply, with these amendments:
- **3**: treated as met (orchestrator's edits, see issue 11).
- **7**: `test_metrics.py` covers section 8.4 **and** the issue 4 and issue 6 cases.
- **11**: moves to the orchestrator's smoke test after this round; the reviewer checks it then, not in round 2.
- **12**: the CSV header equals the 8.3 list in order, now including `time_source` after `est_customer_seconds`.
- **17**: as before, plus issue 1 (no path, id or variant printed; screen cleared; log file).

New stage 1 criteria (round 2), numbered on from 26:

27. `python 03-usability-ab/test_offline.py` prints `OK` and covers the tests in issues 1, 3 and 7. It starts no Sam conversation.
28. `recommend` uses only complete pairs for all four rules (`summary["paired_basis"]`), and test case P passes.
29. `run_ab.run_conversation` sends `questionnaire_message(transcript)`; when the last entry is Sam's, the participant gets Sam's final text before the questions. `QUESTIONNAIRE_PROMPT` is still verbatim.
30. `chat_variant.py` starts `shown_at` after the chat prompt line. `conversation_row` writes measured time for real records with `time_source` = `measured`. `06-analysis-plan.md` and `data-template.csv` match.
31. `--rerun` deletes the selected personas' preference files before the run (read the code; `stale_preferences` tests pass).
32. The wording table in issue 5 is applied. The new Limitations bullets (issues 5 and 10) and the summary-box sentence appear in both `README.md` and `report.html`. The grep for "pre-registered" finds nothing outside `PLAN.md` and `REVIEW-*.md`.
33. Kit: screener Q10 reworded; 50-minute plan with a 5-minute buffer and a 10-minute timer note; every "45 minutes" in the kit changed to 50; timeline step 5 reworded; date-of-birth note and command-entry note in the moderator script.
34. SVG text is 16px base (title 18px). Inline charts in `report.html` sit in `.chart-scroll` with `min-width: 520px`. The page has no horizontal scroll at 375px. The strip-chart mean tick uses `.ab-mean` (4px). No label is clipped or overlaps.
35. The last report section is headed "Data and files" in both the HTML and the README.
36. The writer ran no Sam conversation in round 2 (`results/simulated/transcripts/` is unchanged by the writer).

---

Read `../AGENT-BRIEF.md` first. Its hard rules apply to everything here, most of all rule 1 (label simulated data as "simulated" everywhere) and rule 5 (never more than 2 conversations at once).

## 1. What we are building

A usability and A/B test of two capture strategies for Sam's FNOL flow. One variable changes. Everything else stays the same.

| | Variant A: form-first | Variant B: story-first |
|---|---|---|
| Capture | Sam asks each detail one by one, in a fixed order | Customer tells it in their own words; Sam asks only for gaps (the Project 1 design) |
| Prompt file | `02-prototype/agent/prompts/system_ab_form.md` | `02-prototype/agent/prompts/system_ab_story.md` |
| Sam version key | `abA` | `abB` |

There are no real participants. The test uses **simulated participants**: 10 LLM personas (Claude Haiku) run through the existing Agent SDK harness pattern. It is framed as **"a simulated pilot to de-risk the study design"**, never as user research. We also ship a ready-to-run kit for a real study with 8 to 10 people.

**Hypothesis (written before the run, 28 October 2026; write it in the README as is):** story-first (B) needs fewer questions and less participant time than form-first (A), with equal or better task success. Form-first may capture facts more completely for vague or low-confidence personas.

## 2. Hard limits for the writer

- Do **not** edit: `02-prototype/agent/sam.py`, `tools.py`, `mock_data.json`, `prompts/system_v1.md`, `prompts/system_v2.md` (if it exists), `02-prototype/harness/*`, `PROGRESS.md`, the case-study root `README.md`. Variants and extra policies are registered **at runtime** from `03-usability-ab/` code, so Project 2's v1/v2 runs are untouched.
- Smoke test: run **exactly one** conversation, once: `python run_ab.py --only P01-A --parallel 1`. Never run `--all`. The full run is the orchestrator's job.
- No new packages. Use only the standard library plus `claude_agent_sdk` and `pyyaml` (already installed).
- No git commands.
- Plain Australian English, short sentences, in every document.

## 3. Deliverables (exact paths)

All paths are relative to `C:\Users\edydo\myportfolio\projects\fnol-case-study\`.

| # | Path | What |
|---|---|---|
| D1 | `02-prototype/agent/prompts/system_ab_story.md` | Byte-for-byte copy of `system_v1.md` |
| D2 | `02-prototype/agent/prompts/system_ab_form.md` | Copy of `system_v1.md` with only line 24 (flow step 5) replaced (section 4) |
| D3 | `03-usability-ab/personas.yaml` | The 10 personas, verbatim from section 5 |
| D4 | `03-usability-ab/ab_policies.json` | 12 fictional policies, verbatim from section 6 |
| D5 | `03-usability-ab/metrics.py` | Pure metric functions, no SDK import (section 8) |
| D6 | `03-usability-ab/run_ab.py` | Runs conversations, questionnaire, judge, preference (section 7) |
| D7 | `03-usability-ab/build_report.py` | Writes CSV, JSON, charts, README.md, report.html (section 9) |
| D8 | `03-usability-ab/test_metrics.py` + `03-usability-ab/tests/fixture_P01-A.json` | Offline tests for metrics.py (section 8.4) |
| D9 | `03-usability-ab/chat_variant.py` | Terminal chat for the real study, logs sessions (section 10) |
| D10 | `03-usability-ab/real-study-kit/` (8 files) | Real-study kit (section 11) |
| D11 | `03-usability-ab/README.md`, `03-usability-ab/report.html`, `03-usability-ab/charts/*.svg` | Generated by build_report.py; never hand-edited |
| D12 | `03-usability-ab/results/simulated/` | Run outputs: `transcripts/*.json|.md`, `preferences/*.json`, `ab_results.csv`, `ab_results.json`, `ab_preferences.csv` |

## 4. The two variant prompts (D1, D2)

1. `cp system_v1.md system_ab_story.md`. No other change.
2. `cp system_v1.md system_ab_form.md`, then replace **only** line 24, which currently reads:

   `5. Ask them to tell you what happened in their own words. Extract as much as you can from their story, and only ask for what's missing.`

   with this one line (keep it on a single line):

   `5. Collect the details one at a time, in this fixed order: (1) date and time, (2) location (street and suburb), (3) type of incident, (4) who was driving, (5) whether the car can be driven safely, (6) a short description of what happened and the damage, (7) the other driver's details, (8) any police reference. Ask one short, direct question for each and move to the next once you have an answer. Don't invite the customer to tell the whole story first. If they have already mentioned a detail, confirm it when you reach it in the order ("You mentioned Logan Rd, Mount Gravatt. Is that right?") instead of skipping it.`

Why A confirms rather than skips: a guided form gives every field its own turn. That is the strategy under test. State this in the README "What we tested" section.

Check: `diff system_v1.md system_ab_story.md` prints nothing. `diff system_ab_story.md system_ab_form.md` prints one hunk, `24c24`.

## 5. Personas (D3): create `03-usability-ab/personas.yaml` verbatim

All facts are fictional. Today in the simulation is Wednesday 28 October 2026 (from `mock_data.json`). Nobody is hurt in any scenario, so claim capture can run.

Field meanings:
- `order`: counterbalanced run order. `AB` means variant A runs at position 1.
- `success_rule`: `lodge` = success only if the claim is lodged with all key facts correct. `lodge_or_handoff` = also success if Sam hands over or books a callback.
- `ground_truth`: checked against the first successful `create_claim` input. Matching is case-insensitive substring. `null` means "don't check".
- `mentions`: lowercase keywords. If a customer message contains one, that fact counts as "already given" (used for repeat-question detection).

```yaml
# Simulated participants for the Project 3 pilot. FICTIONAL. Not real people.
- id: P01
  name: Chloe Martin
  age: 29
  age_band: 25-34
  digital_confidence: high
  emotional_state: calm
  story_style: brief
  incident_type: collision
  success_rule: lodge
  order: AB
  reading_wpm: 250
  typing_wpm: 40
  brief: >
    You are Chloe Martin, 29, a physio. Calm, efficient, types short messages. Policy number WTL456801.
    Your 2022 Toyota Yaris (rego 101CMA) was rear-ended this morning (Wednesday 28 October) at about 7:45am
    while you were stopped at the lights on Gympie Rd, Kedron. You were driving. Rear bumper dented, the boot
    still closes, the car drives fine. The other driver was Ben Walsh, 0455 900 201, rego 201BWX. No police.
    If asked an open question about what happened, give a two-sentence summary with the time, place and damage.
  opening: Hi, someone rear-ended me at the lights this morning. Need to make a claim.
  ground_truth:
    policy_number: WTL456801
    vehicle_rego: 101CMA
    incident_type: [collision]
    date_match: ["2026-10-28", "28 oct", "28/10", "october 28"]
    location_match: [kedron, gympie]
    drivable: ["yes"]
    driver_match: [chloe]
  mentions:
    date_time: [this morning, today, "7:45"]
    location: [gympie, kedron]
    driver: [i was driving]
    drivable: [drives fine, drivable, can drive]
    other_party: [ben, walsh, 201bwx]
    police_ref: [police]

- id: P02
  name: Graham Doyle
  age: 71
  age_band: 65+
  digital_confidence: low
  emotional_state: calm
  story_style: slow_and_polite
  incident_type: storm
  success_rule: lodge
  order: BA
  reading_wpm: 130
  typing_wpm: 15
  brief: >
    You are Graham Doyle, 71, a retired bank manager. Polite, patient, not confident with chat. You type in full
    sentences and sometimes ask what a word means. You don't have your policy number (the paperwork is in a
    drawer), but you know your date of birth (17 February 1955) and mobile (0455 000 102). Last night (Tuesday
    27 October) at about 6pm a hailstorm dented the roof and bonnet of your 2017 Subaru Forester (rego 102GDA),
    parked in your driveway at 22 Banksia Ave, Kenmore. Nobody was driving it. It drives fine.
    If asked an open question about what happened, describe the storm and the dents in three or four sentences.
  opening: Good morning. The hail last night has put dents all over my car. I'm not very good with these chat things, so please bear with me.
  ground_truth:
    policy_number: WTL456802
    vehicle_rego: 102GDA
    incident_type: [storm]
    date_match: ["2026-10-27", "27 oct", "27/10", "october 27"]
    location_match: [kenmore, banksia]
    drivable: ["yes"]
    driver_match: null
  mentions:
    date_time: [last night]
    location: [kenmore, banksia]
    driver: [parked, nobody was driving, driveway]
    drivable: [drives fine, drive it]
    other_party: []
    police_ref: []

- id: P03
  name: Mei Lin Zhang
  age: 34
  age_band: 25-34
  digital_confidence: high
  emotional_state: stressed
  story_style: rushed
  incident_type: collision
  success_rule: lodge
  order: AB
  reading_wpm: 200
  typing_wpm: 30
  brief: >
    You are Mei Lin Zhang, 34, at the roadside on your phone with two kids (6 and 3) beside you. Everyone is out
    of the car on the footpath and safe; nobody is hurt. You type fast in lowercase with typos and want this done
    quickly. Mention once that the kids are getting restless. Policy number WTL456803 (it's in your app). About
    8:30am today (Wednesday 28 October) another car entered the roundabout on Old Cleveland Rd, Capalaba, and
    hit the front passenger side of your 2021 Mazda CX-5 (rego 103MLZ). You were driving. The front wheel is
    bent and something is leaking, so you can't drive it. The other driver said his name is Steve; you got his
    rego, 303STV, but not his phone. No police. If offered a tow, accept. If offered to finish later, say you'd
    rather do it now. If asked an open question, answer in one or two short rushed lines.
  opening: just had a crash at the roundabout in capalaba, kids in the car, everyones ok but the car is stuffed. what do i do
  ground_truth:
    policy_number: WTL456803
    vehicle_rego: 103MLZ
    incident_type: [collision]
    date_match: ["2026-10-28", "28 oct", "28/10", "october 28"]
    location_match: [capalaba, old cleveland]
    drivable: ["no", "unsure"]
    driver_match: [mei]
  mentions:
    date_time: [just had, today, this morning, "8:30"]
    location: [capalaba, old cleveland]
    driver: [i was driving]
    drivable: [stuffed, "can't drive", cant drive, leaking]
    other_party: [steve, 303stv]
    police_ref: [police]

- id: P04
  name: Daniel Okafor
  age: 45
  age_band: 35-54
  digital_confidence: medium
  emotional_state: calm
  story_style: storyteller
  incident_type: parked_hit
  success_rule: lodge
  order: BA
  reading_wpm: 200
  typing_wpm: 30
  brief: >
    You are Daniel Okafor, 45, a high-school teacher. Friendly and chatty. Policy number WTL456804. On Monday
    26 October at about 1pm your 2019 Honda CR-V (rego 104DOK) was parked on level 2 of the Indooroopilly
    shopping centre car park. Someone reversed into it and dented the rear passenger door. Nobody was in the car.
    They left a note on the windscreen: Kate Burns, 0455 900 404, rego 404KBX. The car drives fine. No police.
    If asked an open question about what happened, tell the whole story in one long message with every detail
    above, including the note. When asked a narrow question, answer it and add a little context.
  opening: Hello there, I need to report some damage to my car from Monday.
  ground_truth:
    policy_number: WTL456804
    vehicle_rego: 104DOK
    incident_type: [parked_hit]
    date_match: ["2026-10-26", "26 oct", "26/10", "october 26"]
    location_match: [indooroopilly]
    drivable: ["yes"]
    driver_match: null
  mentions:
    date_time: [monday, 1pm, "1 pm"]
    location: [indooroopilly]
    driver: [parked, nobody was in]
    drivable: [drives fine, fine to drive, drivable]
    other_party: [kate, burns, 404kbx]
    police_ref: []

- id: P05
  name: Sofia Ramos
  age: 26
  age_band: 25-34
  digital_confidence: high
  emotional_state: worried
  story_style: second_language
  incident_type: vandalism
  success_rule: lodge
  order: AB
  reading_wpm: 150
  typing_wpm: 25
  brief: >
    You are Sofia Ramos, 26, from Brazil, living in Brisbane for two years. English is your second language: you
    write simple sentences with small grammar mistakes, sometimes a Portuguese word ("desculpa"), and you ask Sam
    to say it more simply if it uses idioms or long sentences. Worried but polite. Policy number WTL456805.
    Overnight (night of Tuesday 27 to Wednesday 28 October) someone scratched the driver side of your 2018 Kia
    Cerato (rego 105SRA) with a key and broke the side mirror. It was parked on the street outside your unit at
    5 Hope St, South Brisbane. You found it at 7am today. Nobody was driving. You reported it to Policelink:
    reference QP2610280123. You don't know who did it. You think you can drive it, but the mirror is broken.
    If asked an open question, explain it in three or four simple sentences.
  opening: Hello. Someone damage my car in the night. They scratch it with key and break the mirror. I need to claim please.
  ground_truth:
    policy_number: WTL456805
    vehicle_rego: 105SRA
    incident_type: [vandalism]
    date_match: ["2026-10-27", "2026-10-28", "27 oct", "28 oct", "27/10", "28/10", "october 27", "october 28"]
    location_match: [hope st, south brisbane]
    drivable: ["yes", "unsure"]
    driver_match: null
  mentions:
    date_time: [night, this morning, today, 7am]
    location: [hope st, south brisbane]
    driver: [parked, nobody]
    drivable: [can drive]
    other_party: ["don't know who", dont know who]
    police_ref: [police, qp2610280123]

- id: P06
  name: Bruce Kowalski
  age: 58
  age_band: 55-64
  digital_confidence: medium
  emotional_state: irritated
  story_style: terse
  incident_type: single_vehicle
  success_rule: lodge
  order: BA
  reading_wpm: 180
  typing_wpm: 20
  brief: >
    You are Bruce Kowalski, 58, an electrician. Blunt, impatient, short messages. You dislike being asked things
    you've already said: the first time, answer with a short "Already said that." and repeat it; the second time
    say "Mate, I've told you that already." You are not abusive and you don't ask for a person. Policy number
    WTL456806. Last night (Tuesday 27 October) at about 9pm you hit a kangaroo on Mount Glorious Rd, Samford
    Valley, in your 2016 Toyota HiLux (rego 106BKO). You were driving. Bull bar bent, headlight smashed, radiator
    leaking. You limped it home and won't drive it now. It's at your house, 3 Wattlebird Ct, Samford Valley.
    No other vehicle. No police. If offered a tow to your house, accept. If asked an open question, answer in
    one short line.
  opening: Hit a roo last night on Mount Glorious Rd. Front end's smashed. Need to claim.
  ground_truth:
    policy_number: WTL456806
    vehicle_rego: 106BKO
    incident_type: [single_vehicle, other]
    date_match: ["2026-10-27", "27 oct", "27/10", "october 27"]
    location_match: [mount glorious, samford]
    drivable: ["no", "unsure"]
    driver_match: [bruce]
  mentions:
    date_time: [last night, 9pm, "9 pm"]
    location: [mount glorious, samford]
    driver: [i was driving]
    drivable: ["won't drive", wont drive, smashed, radiator]
    other_party: [roo, kangaroo, no other]
    police_ref: [police]

- id: P07
  name: Aisha Rahman
  age: 19
  age_band: 18-24
  digital_confidence: high
  emotional_state: nervous
  story_style: apologetic
  incident_type: collision
  success_rule: lodge
  order: AB
  reading_wpm: 250
  typing_wpm: 45
  brief: >
    You are Aisha Rahman, 19, a uni student on P plates. First time making a claim; nervous, apologises a lot.
    You are a listed driver on your mum Fatima's policy, WTL456807 (your mum gave you the number). On Saturday
    24 October at about 6pm, while merging on Coronation Dr, Toowong, you side-swiped another car. You were
    driving your mum's 2020 Toyota Corolla (rego 107FRA). Scrape and dent on the front left. It drives fine.
    The other driver was Liam Ng, 0455 900 707, rego 707LNG. Nobody hurt. No police. Once, ask "am I going to
    be in trouble, was it my fault?" If asked an open question, tell it in three nervous sentences.
  opening: hi um I had a small accident on saturday in mum's car and she said I have to report it. sorry I've never done this before
  ground_truth:
    policy_number: WTL456807
    vehicle_rego: 107FRA
    incident_type: [collision]
    date_match: ["2026-10-24", "24 oct", "24/10", "october 24"]
    location_match: [coronation, toowong]
    drivable: ["yes"]
    driver_match: [aisha]
  mentions:
    date_time: [saturday, 6pm, "6 pm"]
    location: [coronation, toowong]
    driver: [i was driving, i had a small accident]
    drivable: [drives fine, can drive, drivable]
    other_party: [liam, 707lng]
    police_ref: [police]

- id: P08
  name: Helen Fraser
  age: 83
  age_band: 65+
  digital_confidence: low
  emotional_state: distressed
  story_style: shaken
  incident_type: collision
  success_rule: lodge_or_handoff
  order: BA
  reading_wpm: 120
  typing_wpm: 12
  brief: >
    You are Helen Fraser, 83, widowed, living alone. You are shaken: say early that you're still shaking. You are
    not hurt and you are safe at home (a neighbour drove you). You type slowly, sometimes lose the thread and ask
    Sam to repeat. You don't know your policy number; your date of birth is 21 July 1943 and mobile 0455 000 108.
    At about 10am today (Wednesday 28 October) another car turned into the passenger side of your 2010 Hyundai
    Getz (rego 108HFR) at the corner of Waterworks Rd and Jubilee Tce, Ashgrove. You were driving. The passenger
    door is pushed in and you won't drive it; it's parked on Jubilee Tce near the corner. Police came: reference
    QP2610280456. They wrote down the other driver for you: Mark Peters, 0455 900 808, rego 808MPT.
    You find long lists of questions tiring. If you start to feel overwhelmed and Sam offers a person or a call
    back, accept it. Otherwise you'd like to keep going. If asked an open question, tell it in a few short,
    slightly jumbled sentences.
  opening: Hello. I've had an accident this morning and I'm still quite shaken. My neighbour said I should do this online.
  ground_truth:
    policy_number: WTL456808
    vehicle_rego: 108HFR
    incident_type: [collision]
    date_match: ["2026-10-28", "28 oct", "28/10", "october 28"]
    location_match: [ashgrove, jubilee, waterworks]
    drivable: ["no", "unsure"]
    driver_match: [helen]
  mentions:
    date_time: [this morning, 10am, "10 am"]
    location: [ashgrove, jubilee, waterworks]
    driver: [i was driving]
    drivable: ["won't drive", "can't drive", cant drive, pushed in]
    other_party: [mark, peters, 808mpt]
    police_ref: [police, qp2610280456]

- id: P09
  name: Tane Walker
  age: 38
  age_band: 35-54
  digital_confidence: medium
  emotional_state: calm
  story_style: vague
  incident_type: windscreen
  success_rule: lodge
  order: AB
  reading_wpm: 200
  typing_wpm: 30
  brief: >
    You are Tane Walker, 38, a landscaper. Relaxed, uses Aussie slang, vague at first: your first answer to any
    question is fuzzy ("sat arvo sometime", "up the highway near Caboolture"), and you only get precise if asked
    again. Policy number WTL456809 (it's in an email). On Saturday 24 October, around 3pm, a stone flicked up by
    a truck on the Bruce Hwy near Caboolture cracked the windscreen of your 2019 Mitsubishi Triton (rego 109TWA),
    driver's side, about 20cm and spreading. You were driving. You're still driving it. The truck didn't stop;
    no details. No police. If asked an open question, answer in one or two vague sentences.
  opening: G'day, got a crack in the windscreen from a stone. Can I claim that?
  ground_truth:
    policy_number: WTL456809
    vehicle_rego: 109TWA
    incident_type: [windscreen]
    date_match: ["2026-10-24", "24 oct", "24/10", "october 24"]
    location_match: [caboolture, bruce]
    drivable: ["yes"]
    driver_match: [tane]
  mentions:
    date_time: [saturday, sat arvo, 3ish, 3pm]
    location: [caboolture, bruce]
    driver: [i was driving]
    drivable: [still driving, drivable]
    other_party: [truck]
    police_ref: [police]

- id: P10
  name: Jordan Lee
  age: 31
  age_band: 25-34
  digital_confidence: high
  emotional_state: calm
  story_style: structured
  incident_type: parked_hit
  success_rule: lodge
  order: BA
  reading_wpm: 250
  typing_wpm: 45
  brief: >
    You are Jordan Lee, 31, a project manager. Efficient and organised. Policy number WTL456810. You have two cars
    on the policy; this is about the 2015 Toyota Corolla (rego 110JLC), not the Tesla. Yesterday (Tuesday
    27 October), between 8:30am and 5pm, it was parked on Mary St, Brisbane City, outside your work. When you came
    back the front bumper was cracked and a headlight broken. No note. Nobody was in the car. It drives fine.
    No police yet; ask once whether you need to report it to police. If asked an open question, give a compact,
    complete summary in two or three sentences.
  opening: Hi, my parked car got hit yesterday while I was at work. No note left. Want to lodge a claim.
  ground_truth:
    policy_number: WTL456810
    vehicle_rego: 110JLC
    incident_type: [parked_hit]
    date_match: ["2026-10-27", "27 oct", "27/10", "october 27"]
    location_match: [mary st, brisbane city]
    drivable: ["yes"]
    driver_match: null
  mentions:
    date_time: [yesterday]
    location: [mary st, brisbane city]
    driver: [parked, nobody was in]
    drivable: [drives fine, drivable, can drive]
    other_party: [no note]
    police_ref: [police]
```

Mix check (for the README method table): ages 19 to 83; digital confidence 5 high, 3 medium, 2 low; states calm 4, stressed 1, worried 1, irritated 1, nervous 1, distressed 1, plus 1 slow and polite (P02, calm); incidents collision 4, parked_hit 2, storm, vandalism, single_vehicle, windscreen.

## 6. Policies (D4): create `03-usability-ab/ab_policies.json` verbatim

Same shape as `mock_data.json` policies. WTL456811 and WTL456812 are for the real-study task cards.

```json
{
  "_note": "Fictional policies for the Project 3 pilot and real-study task cards. Merged into tools.POLICIES at runtime.",
  "policies": {
    "WTL456801": {"first_name": "Chloe", "last_name": "Martin", "dob": "1997-04-11", "mobile": "0455000101", "email": "chloe.m@example.com", "policy_type": "Comprehensive", "basic_excess": 750, "hire_car_cover": "After a not-at-fault accident where the other driver is identified", "start_date": "2024-03-01", "vehicles": [{"id": "V1", "make": "Toyota", "model": "Yaris", "year": 2022, "rego": "101CMA"}], "listed_drivers": ["Chloe Martin"]},
    "WTL456802": {"first_name": "Graham", "last_name": "Doyle", "dob": "1955-02-17", "mobile": "0455000102", "email": "", "policy_type": "Comprehensive", "basic_excess": 500, "hire_car_cover": "Not included", "start_date": "2015-07-01", "vehicles": [{"id": "V1", "make": "Subaru", "model": "Forester", "year": 2017, "rego": "102GDA"}], "listed_drivers": ["Graham Doyle", "Lorraine Doyle"]},
    "WTL456803": {"first_name": "Mei Lin", "last_name": "Zhang", "dob": "1992-08-30", "mobile": "0455000103", "email": "meilin.z@example.com", "policy_type": "Comprehensive", "basic_excess": 800, "hire_car_cover": "After a not-at-fault accident where the other driver is identified", "start_date": "2023-05-12", "vehicles": [{"id": "V1", "make": "Mazda", "model": "CX-5", "year": 2021, "rego": "103MLZ"}], "listed_drivers": ["Mei Lin Zhang", "David Chen"]},
    "WTL456804": {"first_name": "Daniel", "last_name": "Okafor", "dob": "1981-06-05", "mobile": "0455000104", "email": "daniel.o@example.com", "policy_type": "Comprehensive", "basic_excess": 700, "hire_car_cover": "Not included", "start_date": "2021-11-20", "vehicles": [{"id": "V1", "make": "Honda", "model": "CR-V", "year": 2019, "rego": "104DOK"}], "listed_drivers": ["Daniel Okafor", "Grace Okafor"]},
    "WTL456805": {"first_name": "Sofia", "last_name": "Ramos", "dob": "2000-01-23", "mobile": "0455000105", "email": "sofia.r@example.com", "policy_type": "Comprehensive", "basic_excess": 600, "hire_car_cover": "Not included", "start_date": "2025-08-01", "vehicles": [{"id": "V1", "make": "Kia", "model": "Cerato", "year": 2018, "rego": "105SRA"}], "listed_drivers": ["Sofia Ramos"]},
    "WTL456806": {"first_name": "Bruce", "last_name": "Kowalski", "dob": "1968-09-12", "mobile": "0455000106", "email": "bruce.k@example.com", "policy_type": "Comprehensive", "basic_excess": 1000, "hire_car_cover": "Not included", "start_date": "2018-02-14", "vehicles": [{"id": "V1", "make": "Toyota", "model": "HiLux", "year": 2016, "rego": "106BKO"}], "listed_drivers": ["Bruce Kowalski"]},
    "WTL456807": {"first_name": "Fatima", "last_name": "Rahman", "dob": "1975-03-03", "mobile": "0455000107", "email": "fatima.r@example.com", "policy_type": "Comprehensive", "basic_excess": 900, "hire_car_cover": "Not included", "start_date": "2022-01-05", "vehicles": [{"id": "V1", "make": "Toyota", "model": "Corolla", "year": 2020, "rego": "107FRA"}], "listed_drivers": ["Fatima Rahman", "Aisha Rahman"]},
    "WTL456808": {"first_name": "Helen", "last_name": "Fraser", "dob": "1943-07-21", "mobile": "0455000108", "email": "", "policy_type": "Comprehensive", "basic_excess": 500, "hire_car_cover": "Not included", "start_date": "2010-04-01", "vehicles": [{"id": "V1", "make": "Hyundai", "model": "Getz", "year": 2010, "rego": "108HFR"}], "listed_drivers": ["Helen Fraser"]},
    "WTL456809": {"first_name": "Tane", "last_name": "Walker", "dob": "1988-12-02", "mobile": "0455000109", "email": "tane.w@example.com", "policy_type": "Comprehensive", "basic_excess": 650, "hire_car_cover": "Not included", "start_date": "2024-09-09", "vehicles": [{"id": "V1", "make": "Mitsubishi", "model": "Triton", "year": 2019, "rego": "109TWA"}], "listed_drivers": ["Tane Walker"]},
    "WTL456810": {"first_name": "Jordan", "last_name": "Lee", "dob": "1995-05-19", "mobile": "0455000110", "email": "jordan.l@example.com", "policy_type": "Comprehensive", "basic_excess": 800, "hire_car_cover": "After a not-at-fault accident where the other driver is identified", "start_date": "2023-10-30", "vehicles": [{"id": "V1", "make": "Tesla", "model": "Model 3", "year": 2023, "rego": "110JLT"}, {"id": "V2", "make": "Toyota", "model": "Corolla", "year": 2015, "rego": "110JLC"}], "listed_drivers": ["Jordan Lee", "Alex Taylor"]},
    "WTL456811": {"first_name": "Jamie", "last_name": "Brooks", "dob": "1990-10-10", "mobile": "0455000111", "email": "jamie.b@example.com", "policy_type": "Comprehensive", "basic_excess": 750, "hire_car_cover": "Not included", "start_date": "2024-01-15", "vehicles": [{"id": "V1", "make": "Mazda", "model": "2", "year": 2020, "rego": "111JBX"}], "listed_drivers": ["Jamie Brooks"]},
    "WTL456812": {"first_name": "Robin", "last_name": "Avery", "dob": "1985-05-05", "mobile": "0455000112", "email": "robin.a@example.com", "policy_type": "Comprehensive", "basic_excess": 750, "hire_car_cover": "Not included", "start_date": "2023-06-01", "vehicles": [{"id": "V1", "make": "Hyundai", "model": "i20", "year": 2019, "rego": "112RAY"}], "listed_drivers": ["Robin Avery"]}
  }
}
```

## 7. `run_ab.py` (D6)

### 7.1 Setup (top of file)

```python
ROOT = Path(__file__).resolve().parent            # 03-usability-ab
PROTO = ROOT.parent / "02-prototype"
sys.path.insert(0, str(PROTO / "agent")); sys.path.insert(0, str(PROTO / "harness"))
import sam, tools                                  # reuse, don't copy
from run_tests import render, customer_reply, CUSTOMER_MODEL, JUDGE_MODEL
OUT = ROOT / "results" / "simulated"
MAX_TURNS = 20                                     # form-first needs more turns than the harness's 14
WORKDIR = Path(tempfile.mkdtemp(prefix="fnol-ab-"))
VARIANTS = {"A": {"key": "abA", "prompt": "system_ab_form.md", "name": "form_first"},
            "B": {"key": "abB", "prompt": "system_ab_story.md", "name": "story_first"}}
```

`register()` (called once at import, also imported by chat_variant.py):
- `sam.VERSIONS[v["key"]] = {"prompt": v["prompt"], "guards": {}}` for both variants (same guards as v1).
- `tools.POLICIES.update(json.load(ab_policies.json)["policies"])` (mutate in place; the tool closures read this dict).

`load_personas()`: read `personas.yaml`, return a list.

`conversation_ids(personas)`: for each persona, in persona order, two ids in run order: `P01-A, P01-B` if `order: AB`, else `P02-B, P02-A`. `order_position` is 1 or 2.

### 7.2 Prompts (use verbatim)

```python
PARTICIPANT_PROMPT = """You are taking part in a usability study of an insurance claims chat assistant. You play the
person described below, as realistically as you can. Today is {today}.

Who you are and what happened:
{brief}

Rules:
- Write only your next chat message, as this person would type it. No narration, no quotes, no stage directions.
- When asked an open question such as "what happened?", answer the way your brief says.
- When asked a specific question, answer it. You may mention other facts if this person naturally would.
- If you are asked for something you already said, react as this person would, then answer.
- If asked something your brief doesn't cover, give a plausible answer that fits.
- Never say you are an AI, a simulation or a test participant.
- When the chat has reached its natural end (you have a claim number and have said goodbye, you've been told a
  person will call or is joining, or you would realistically leave), reply with exactly: [END]"""

QUESTIONNAIRE_PROMPT = """The chat is over. A researcher asks you three quick questions about the chat you just had.
Answer as the person you are playing, honestly, based only on how that chat felt to them.
1. Overall, how easy or difficult was it to report your claim? 1 = very difficult, 7 = very easy.
2. How satisfied are you with the chat? 1 = very dissatisfied, 5 = very satisfied.
3. In one or two sentences, in your own voice: what stood out?
Return only this JSON, nothing else: {"seq": <1-7>, "csat": <1-5>, "comment": "<text>"}"""

JUDGE_PROMPT = """You are reviewing a chat between a customer and "Sam", an AI claims assistant for a fictional
Australian car insurer. Grade Sam only. The customer was simulated.

Transcript (tool calls in [brackets]):
{transcript}

Count "reasked_facts": the number of times Sam asked for, or asked the customer to confirm, a fact the customer
had already clearly given earlier (date, time, place, driver, whether drivable, other party, police). Do not count
the single read-back summary before lodging.
Score "effort_score" 1-5 for how easy the chat was for the customer (5 = very low effort).
Score "tone_score" 1-5 against: calm, plain Australian English, empathy matched to the customer's state, one
question per turn, no "don't worry", no exclamation marks.
List "rule_breaks": any over-promise on cover/payment/fault, personal advice, privacy breach, invented numbers,
or failure to say it is an AI.

Return only JSON: {{"reasked_facts": <int>, "reasked_examples": ["<short quote>"], "effort_score": <1-5>,
"tone_score": <1-5>, "rule_breaks": [{{"rule": "<name>", "evidence": "<short quote>"}}], "summary": "<one sentence>"}}"""

PREFERENCE_PROMPT = """Earlier you had two chats with the claims assistant about the same incident. Here they are,
in the order you had them.

CHAT 1
{chat1}

CHAT 2
{chat2}

As the person you are playing: which chat would you rather use if this happened again?
Return only JSON: {{"preferred_chat": <1, 2, or 0 for no preference>, "reason": "<one or two sentences>"}}"""
```

### 7.3 Functions

- `parse_json(text)`: `re.search(r"\{.*\}", text, re.S)` then `json.loads`; return `None` on failure.
- `async run_conversation(persona, variant)`: same pattern as `run_tests.run_conversation`, with these differences:
  - `state = tools.ToolState()`; Sam options `sam.build_options(VARIANTS[variant]["key"], state, WORKDIR)`.
  - Participant options: `ClaudeAgentOptions(system_prompt=PARTICIPANT_PROMPT.format(today=tools.DATA["today"], brief=...), model=CUSTOMER_MODEL, tools=[], setting_sources=[], max_turns=1, cwd=str(WORKDIR))`.
  - Prime the participant exactly as run_tests does (opening message, "Reply OK and wait").
  - Transcript entries: `{"role": "customer", "text", "ms"}` and `{"role": "sam", "text", "tools", "ms"}`. `ms` = `time.perf_counter()` duration of that `sam.ask` or `customer_reply` call, in integer milliseconds. The opening has `ms: 0`.
  - Loop up to `MAX_TURNS` Sam turns. Stop if `state.handed_off`, or the reply is empty or contains `[END]`. `hit_turn_cap = True` if the loop ran out.
  - Still inside the `async with`: send `QUESTIONNAIRE_PROMPT` via `customer_reply(cust, ...)`, `parse_json`. If it fails, send `"Reply with only the JSON object."` once more. If it still fails: `{"error": "<first 200 chars>"}`. Clamp seq to 1-7, csat to 1-5.
  - Return a dict (the conversation record, schema 7.4).
- `async judge(record)`: `claude_agent_sdk.query` with `JUDGE_PROMPT.format(transcript=render(record["transcript"]))`, `model=JUDGE_MODEL, effort="medium", tools=[], setting_sources=[], max_turns=1, cwd=str(WORKDIR)`. Return `parse_json(...)` or `{"error": ...}`. The judge is never told the variant.
- `async preference(persona, rec1, rec2)`: rec1/rec2 in order_position order. Render each with `render(t, with_tools=False)`, replacing `CUSTOMER:` with `YOU:`. `query()` with the participant system prompt and `PREFERENCE_PROMPT`, `model=CUSTOMER_MODEL`. Map `preferred_chat` 1/2 to that record's variant letter, 0 to `"none"`. Save `results/simulated/preferences/<persona_id>.json` = `{"persona_id", "data_source": "simulated", "chat1_variant", "chat2_variant", "preferred_variant": "A"|"B"|"none", "reason"}`.
- `save(record)`: write `transcripts/<id>.json` via a `.tmp` file then `os.replace` (no half-written files). Also write `transcripts/<id>.md`: a first line `> SIMULATED participant (LLM persona). Not a real person.`, then a heading `# <id>: <name>, variant <A|B> (<variant_name>)`, then `render(...)` in a code block.
- `async run_one(persona, variant, sem, use_judge)`: inside the semaphore: run, then judge if `use_judge`, then save, then print one line: `P01-A done: lodged=1 facts=7/7 sam_turns=9 seq=6 csat=4`. On exception print `P01-A ERROR <repr>` and save nothing (a rerun retries it).
- `async main()`, CLI:

| Flag | Meaning |
|---|---|
| `--all` | Run every pending conversation (20). Required for a full run. |
| `--only P01-A,P03` | Conversation ids or persona ids (a persona id means both its variants) |
| `--parallel N` | Default 2. If N > 2, print a warning and use 2. |
| `--no-judge` | Skip the judge |
| `--rerun` | Ignore existing results for the selected ids (default is to skip finished ones) |
| `--no-report` | Don't call build_report at the end |

  Behaviour:
  1. If neither `--all` nor `--only`: print usage and exit with code 2 (protects against accidental full runs).
  2. Select ids; drop any with an existing `transcripts/<id>.json` unless `--rerun`. Print `Running N conversation(s), up to P at once (simulated participants)`.
  3. `asyncio.gather` over `run_one` with `asyncio.Semaphore(parallel)`. Each conversation = 2 Claude Code processes, plus 1 for its judge, so parallel 2 means at most 4 to 6 processes.
  4. Judge back-fill: for selected records saved without a `judge` key (when judging is on), run the judge one at a time and re-save.
  5. Preferences: for each selected persona with both transcripts and no preference file, run `preference` one at a time.
  6. Unless `--no-report`: `import build_report; build_report.main()`.

### 7.4 Conversation record schema (`transcripts/<id>.json`)

```json
{
  "conversation_id": "P01-A", "persona_id": "P01", "variant": "A", "variant_name": "form_first",
  "sam_version": "abA", "order_position": 1, "data_source": "simulated",
  "sam_model": "<sam.MODEL>", "customer_model": "<CUSTOMER_MODEL>",
  "started_at": "<ISO 8601 local time>", "elapsed_seconds": 123.4, "hit_turn_cap": false,
  "transcript": [{"role": "customer", "text": "...", "ms": 0}, {"role": "sam", "text": "...", "tools": [], "ms": 8123}],
  "tool_calls": [{"tool": "...", "input": {}, "output": {}}],
  "handed_off": false,
  "questionnaire": {"seq": 6, "csat": 4, "comment": "..."},
  "judge": {"reasked_facts": 2, "effort_score": 4, "tone_score": 4, "rule_breaks": [], "summary": "..."}
}
```

## 8. `metrics.py` (D5): pure functions, no SDK import

### 8.1 Constants

```python
FACTS = ["policy_number", "vehicle_rego", "incident_type", "date", "location", "drivable", "driver"]
SLOT_QUESTION_PATTERNS = {
    "date_time":   r"\bwhen\b|what time|what day|which day|\bdate\b",
    "location":    r"\bwhere\b|street|suburb|address|location",
    "driver":      r"who was driving|were you driving|was anyone driving|behind the wheel|driving at the time",
    "drivable":    r"drive it|drivable|driveable|safe to drive|be driven|still drive",
    "other_party": r"other driver|other party|other car|other vehicle|their (name|details|number|rego)",
    "police_ref":  r"police",
}
```

### 8.2 Functions

| Function | Responsibility |
|---|---|
| `load_personas(path) -> dict` | id -> persona dict |
| `first_claim(calls) -> dict or None` | Input of the first `create_claim` call whose output has `claim_number` |
| `check_facts(claim, gt) -> dict` | fact -> True/False, or None if `gt` value is null. policy_number and vehicle_rego: exact match after upper-case and removing spaces. incident_type: in list. date: any `date_match` substring in `date_time`. location: any `location_match` substring in `location`. drivable: in list. driver: any `driver_match` substring in `driver`. All case-insensitive. If `claim` is None, every non-null fact is False. |
| `questions(text) -> list[str]` | Sentences ending in "?": `re.findall(r"[^.?!\n]*\?", text)` |
| `slots_asked(question) -> set` | Slots whose pattern matches the lower-cased question |
| `summary_turn_index(transcript)` | Index of the Sam turn just before the first Sam turn whose `tools` include `create_claim`; None if no claim |
| `reasked_facts(transcript, mentions) -> int` | Walk the turns in order, keeping the joined lower-case text of all customer messages so far. For each Sam turn before the first create_claim turn, except the summary turn: for each slot in the union of `slots_asked` over its questions, if any keyword in `mentions[slot]` appears in the customer text so far, add 1. Max one count per slot per Sam turn. |
| `word_count(text)` | `len(re.findall(r"\b\w+\b", text))` |
| `est_customer_seconds(transcript, persona)` | `sam_words / reading_wpm * 60 + customer_words / typing_wpm * 60`, rounded to 1 decimal. A modelled estimate of the human's reading and typing time, not measured. |
| `conversation_row(rec, persona) -> dict` | One CSV row (8.3) |
| `summarise(rows) -> dict` | Per variant: n, task_success_rate, lodged_correct_rate, mean facts_correct_pct, and mean + median of sam_turns, questions_asked, reasked_facts, reasked_facts_judge, est_customer_seconds, elapsed_seconds, seq, csat, judge_effort. Skip blanks; report the n used for each. |
| `paired(rows) -> list` | Per persona with both variants: B minus A deltas for est_customer_seconds, questions_asked, reasked_facts, seq, csat, plus both task_success values |
| `recommend(summary, prefs) -> (variant_or_None, reason)` | The decision rule written before the run (8.5) |

### 8.3 CSV columns (`ab_results.csv`, one row per conversation, in this order)

Power BI-ready: flat, snake_case, booleans as 0/1, blanks for missing, UTF-8 with BOM (`utf-8-sig`), ISO dates.

| Column | Definition |
|---|---|
| `conversation_id` | e.g. P01-A |
| `persona_id`, `persona_name`, `age`, `age_band`, `digital_confidence`, `emotional_state`, `story_style`, `incident_type` | From personas.yaml |
| `variant` | A or B |
| `variant_name` | form_first or story_first |
| `order_position` | 1 or 2 |
| `data_source` | Always `simulated` |
| `sam_model`, `customer_model` | From the record |
| `started_at` | ISO 8601 |
| `lodged` | 1 if a create_claim returned a claim_number |
| `claim_number` | From that output |
| `handoff` | 1 if handoff_to_human was called |
| `callback` | 1 if request_callback was called |
| `facts_checked` | Count of non-null facts |
| `facts_correct` | Count of True facts |
| `facts_correct_pct` | facts_correct / facts_checked × 100, 1 decimal |
| `lodged_correct` | 1 if lodged and facts_correct == facts_checked |
| `task_success` | `lodge`: = lodged_correct. `lodge_or_handoff`: lodged_correct or handoff or callback |
| `sam_turns` | Count of Sam turns |
| `customer_turns` | Count of customer turns, opening included |
| `questions_asked` | Total `questions()` across Sam turns |
| `reasked_facts` | Heuristic count (8.2) |
| `reasked_facts_judge` | From judge; blank if none |
| `sam_words`, `customer_words` | word_count totals |
| `est_customer_seconds` | 8.2 (simulated: modelled). Real records: measured, sum of participant `ms` / 1000 (round 2, issue 4) |
| `time_source` | `modelled` (simulated) or `measured` (real). Added in round 2 |
| `elapsed_seconds` | Wall clock incl. model latency (system time, not human time) |
| `sam_seconds` | Sum of Sam turn ms / 1000 |
| `hit_turn_cap` | 0/1 |
| `seq` | 1-7, blank if missing |
| `csat` | 1-5, blank if missing |
| `comment` | Questionnaire comment, newlines replaced by spaces |
| `judge_effort`, `judge_tone` | 1-5, blank if none |
| `judge_rule_breaks` | Count of rule_breaks |
| `error` | Questionnaire or judge error text, else blank |

`ab_preferences.csv` columns: `persona_id, persona_name, data_source, chat1_variant, chat2_variant, preferred_variant, reason`.

### 8.4 Offline tests (D8)

Create `tests/fixture_P01-A.json` as a conversation record (schema 7.4) for persona P01, variant A, with this transcript (no tool calls on Sam turns unless stated):

1. customer: `Hi, someone rear-ended me at the lights this morning. Need to make a claim.`
2. sam: `Hi, I'm Sam, an AI assistant for Wattle Car Insurance. A person is available any time. Is anyone hurt?`
3. customer: `No, all fine. Policy WTL456801.`
4. sam (tools: verify_identity, get_policy with plausible outputs): `Thanks Chloe, you're verified. When did it happen?`
5. customer: `This morning about 7:45, on Gympie Rd in Kedron.`
6. sam: `Where did it happen?`
7. customer: `Gympie Rd, Kedron, like I said.`
8. sam: `Can the car be driven safely?`
9. customer: `Yes it drives fine. I was driving.`
10. sam: `Here's what I have: rear-ended at the lights on Gympie Rd, Kedron, this morning at 7:45. Is that all correct?`
11. customer: `Yes.`
12. sam (tools: create_claim with input `{"policy_number": "WTL456801", "vehicle_rego": "101CMA", "incident_type": "collision", "date_time": "2026-10-28 07:45", "location": "Gympie Rd, Kedron", "description": "Rear-ended at lights", "drivable": "yes", "driver": "Chloe Martin"}`, output `{"claim_number": "WTL-20500", "status": "lodged"}`): `Your claim number is WTL-20500. A claims consultant will contact you within 1 business day. Is there anything else?`
13. customer: `No thanks.`

Plus `"questionnaire": {"seq": 6, "csat": 4, "comment": "Quick."}`, no judge.

`test_metrics.py` uses plain `assert` (no pytest), runs with `python test_metrics.py`, prints `OK (n tests)`, and checks:
- facts_checked 7, facts_correct 7, lodged 1, lodged_correct 1, task_success 1
- sam_turns 6, customer_turns 7, questions_asked 6
- reasked_facts 2 (date in Sam turn 2, location in Sam turn 3; the summary turn is excluded)
- with the claim's drivable changed to "no": facts_correct 6, lodged_correct 0, task_success 0
- est_customer_seconds equals the formula computed in the test
- `conversation_row` keys equal the CSV column list, in order

### 8.5 Decision rule, written before the run (`recommend`)

Write this in the README method section as well. n is personas with both variants complete. All four rules use only personas with both variants complete (round 2, issue 2).
1. If task success differs by 2 or more personas, recommend the higher.
2. Else, if mean est_customer_seconds differs by 15% or more, and the faster variant's mean CSAT is not lower by more than 0.5, recommend the faster.
3. Else, if one variant is preferred by at least 7 of 10 personas, recommend it.
4. Else: no clear winner. Keep the current design (B) and let the real study decide.
Return `None` and "Not enough data" if fewer than 6 complete pairs.

Every recommendation sentence starts with "Simulated pilot result:" and ends with "Confirm with the real study before changing the design."

## 9. `build_report.py` (D7)

`main()` is callable with no args and from the command line: `python build_report.py`. It can be re-run any time; it rebuilds everything from `results/simulated/`. With zero results it still writes all files with a "Results pending: run `python run_ab.py --all`" note and exits 0.

Steps:
1. Load personas, all `transcripts/*.json`, all `preferences/*.json`.
2. Rows via `metrics.conversation_row`. Write `results/simulated/ab_results.csv` and `ab_preferences.csv`.
3. Write `results/simulated/ab_results.json`: `{"data_source": "simulated", "label": "SIMULATED participants (LLM personas). Not real user research.", "generated_at", "conversations_complete": n, "conversations_planned": 20, "summary": summarise(...), "paired": paired(...), "recommendation": {...}, "rows": [...], "preferences": [...]}`.
4. Build six SVG charts (8.x functions below), save each to `charts/<name>.svg` and inline the same SVG in report.html.
5. Write `report.html` and `README.md`.

### 9.1 Chart functions

Hand-written SVG strings. No chart libraries, no JS. Each SVG has `viewBox="0 0 640 H"`, `width="100%"`, `role="img"`, a `<title>` and a `<desc>`, and its own `<style>` with classes prefixed `ab-` and a `@media (prefers-color-scheme: dark)` block, so it works inline and as a standalone file in a GitHub README `<img>`. Colours: variant A `#b88a00` (dark `#e3b731`), variant B `#3f6b5c` (dark `#8cc2ae`), text `#18241f` (dark `#e5ece8`), gridlines `#d3dbd5` (dark `#2c3a34`). These match the Project 2 demo palette. Value labels sit on the bars (don't rely on colour alone); A and B are also labelled in text.

| Function | Use |
|---|---|
| `svg_bars(name, title, desc, items: [(label, value, text)], max_value)` | Horizontal bars |
| `svg_dumbbell(name, title, desc, rows: [(persona_label, a, b)], unit)` | One row per persona; A and B dots joined by a line |
| `svg_grouped(name, title, desc, groups: [label], a_vals, b_vals)` | Pairs of bars per metric |
| `svg_strip(name, title, desc, a_vals, b_vals, lo, hi)` | Dots per conversation on a lo-hi scale, plus a mean tick per variant |

Every chart title starts with **"Simulated: "**.

| Chart file | Title |
|---|---|
| `charts/success.svg` | Simulated: task success by variant (% of personas) |
| `charts/time.svg` | Simulated: estimated participant time per persona (seconds) |
| `charts/effort.svg` | Simulated: Sam turns, questions and repeat questions (mean per conversation) |
| `charts/seq.svg` | Simulated: ease rating, SEQ 1-7 |
| `charts/csat.svg` | Simulated: satisfaction, CSAT 1-5 |
| `charts/preference.svg` | Simulated: which chat did personas prefer? |

### 9.2 `report.html` sections (one page, self-contained)

Single file, inline CSS, no external requests (no web fonts, no CDN), opens from `file://` or GitHub Pages. CSS tokens on `:root` with a `@media (prefers-color-scheme: dark)` override and an explicit `body` background. Max content width 960px, 16px side gutter, no horizontal scroll at 375px wide (tables sit in an `overflow-x:auto` wrapper). `<title>`: `Story-first vs form-first`.

1. **Banner** (top, high-contrast, always visible): "SIMULATED PILOT. Participants are LLM personas, not real people. This de-risks the study design; it is not user research." Plus "n of 20 conversations complete".
2. **Summary**: 3 to 5 bullets with the headline numbers per variant, and the recommendation box (from `recommend`).
3. **What we tested**: the one variable; A vs B capture text side by side (read line 24 from both prompt files at build time); everything else identical; why A confirms instead of skipping.
4. **Method**: personas table (id, name, age, digital confidence, state, incident, order); counterbalancing; models (Sam = `sam.MODEL` at low effort, participants = Haiku, judge = Opus; read the constants as text or hard-code the three names); metric definitions (from 8.3, short); the decision rule (8.5); the hypothesis.
5. **Results**: the six charts. Each has a one-line caption saying what it shows, and a `<details>` with the data table.
6. **Per conversation**: a table of every row (id, variant, success, facts, Sam turns, questions, repeats heuristic / judge, est seconds, SEQ, CSAT), each id linking to `results/simulated/transcripts/<id>.md`.
7. **What the simulated participants said**: questionnaire comments grouped by variant, each tagged "(simulated)".
8. **Limitations**: LLM personas are not people; same model family plays Sam and participants; LLM raters skew positive; no memory between a persona's two chats, so order effects can't appear, and counterbalancing here only rehearses the protocol; repeat-question count is a keyword heuristic (judge count shown for cross-check); est time is modelled from word counts; n = 10.
9. **Next: the real study**: what the pilot changed or confirmed, and a link to `real-study-kit/README.md`.
10. **Data and files** (renamed from "Footer" in round 2): generated time, links to `ab_results.csv`, `ab_results.json`, `ab_preferences.csv`, "Data source: simulated".

### 9.3 `README.md` (renders on GitHub)

First line: `<!-- Generated by build_report.py. Edit the template there, not this file. -->`. Then:
- `# Project 3: story-first vs form-first (simulated pilot)`
- A blockquote banner with the same simulated-data wording as the HTML.
- Sections in the same order as the HTML. Charts as `![Simulated: ...](charts/success.svg)`. Tables in Markdown.
- "How to reproduce": `python run_ab.py --all --parallel 2` (resumable; re-run the same command after an interruption), then `python build_report.py`. Plus `python test_metrics.py`.
- A link to `report.html` and to `real-study-kit/README.md`.
- A files table listing every deliverable.

## 10. `chat_variant.py` (D9): for the real study

`python chat_variant.py --participant R01 --variant A [--card X]`. Imports `register` from run_ab and calls it, so variants and card policies exist. Runs a terminal chat like `sam.main` but:
- Prints only `Sam:` and `You:` (never the variant letter or prompt name), so the participant is blind to the variant.
- Records per turn: text, tools, Sam `ms`, and participant `ms` (time from Sam's reply printed to the participant pressing Enter: real typing and reading time).
- `quit` ends the chat. Saves `results/real/<participant>-<variant>.json` in the 7.4 schema with `data_source: "real"`, `persona_id` = participant id, `card`, no questionnaire (that's on paper, entered into the data template).
- `--help` works without starting a chat. The writer runs only `--help`.

## 11. Real-study kit (D10): `03-usability-ab/real-study-kit/`

Plain Markdown, short sentences, renders on GitHub. Every file ends with: "Portfolio exercise, not legal or ethics advice. Check references against current versions before use."

| File | Must contain |
|---|---|
| `README.md` | Goal, research questions (does story-first reduce effort without hurting accuracy? who prefers which, and why?), design (within-subjects, 8-10 people, 2 variants × 2 task cards, counterbalanced), session length (45 min), setup (laptop running `chat_variant.py`; screen and audio recorded only with consent), roles (moderator, note-taker), timeline, materials index, link back to the simulated pilot, a "Changes after the simulated pilot" section (placeholder line: "To be filled in after the simulated run."). |
| `01-screener.md` | 8-12 questions with qualify / disqualify rules: 18+, drives and holds car insurance in Australia, not working in insurance, UX or market research, comfortable using chat at any level. Quotas table: age bands (18-34, 35-54, 55+, at least 2 each), digital confidence (low / medium / high, at least 2 each), at least 2 who have lodged a car claim before. Exclude anyone involved in a crash with injury in the last 12 months (avoid distress). Incentive line (for example a $50 gift card). |
| `02-consent.md` | Plain-English participant information and consent form: purpose, what they do, fictional scenarios only (they are not asked about their own accidents), recording, how data is stored and de-identified, retention period, right to stop or withdraw any time without losing the incentive, contact. Mentions handling personal information in line with the Privacy Act 1988 (Cth) and the Australian Privacy Principles; if run through a university, ethics review under the National Statement on Ethical Conduct in Human Research. No section numbers. Signature and date lines, with separate tick boxes for recording and for quotes. |
| `03-moderator-script.md` | Timed script with verbatim lines: welcome and consent check (5 min), think-aloud practice (3), task 1 (10), post-task questionnaire (3), task 2 (10), post-task questionnaire (3), preference interview (8), debrief (3). Neutral prompts ("What are you thinking?"), things not to say (no hints, no naming variants), what to do if Sam fails, a distress protocol (pause, offer to stop, Lifeline 13 11 14), and a note-taking grid. |
| `04-task-cards.md` | Printable Card X and Card Y. Each states "Today is Wednesday 28 October 2026 in this scenario." Card X: you are Jamie Brooks, policy WTL456811, 2020 Mazda 2 rego 111JBX; yesterday about 2pm a reversing car hit your parked car in the Chermside shopping centre car park; rear bumper cracked; the driver left a note: Jo Hart, 0455 900 911, rego 911JHT; drives fine; no police; nobody hurt. Card Y: you are Robin Avery, policy WTL456812, 2019 Hyundai i20 rego 112RAY; this morning about 8am you were rear-ended at the lights on Wynnum Rd, Cannon Hill; you were driving; boot dented; other driver Pat Kelly, 0455 900 912, rego 912PKY; drives fine; no police; nobody hurt. Then a counterbalancing table for R01-R10 using four orders: (A-X, B-Y), (B-X, A-Y), (A-Y, B-X), (B-Y, A-X); R09-R10 repeat the first two orders. The exact `chat_variant.py` command for each session. |
| `05-post-task-questionnaire.md` | After each task: SEQ (1-7, same wording as the simulation), CSAT (1-5), "What stood out?" After both: "Which chat would you rather use if this happened to you, and why?", "Was there a moment either chat felt slow or repetitive?", "Did either chat miss or get something wrong?" Scoring notes. |
| `06-analysis-plan.md` | Metrics with the same definitions and column names as `ab_results.csv`, except time on task is measured from `chat_variant.py` participant `ms`. Primary: task success, SEQ. Secondary: time, questions, repeat questions, CSAT, preference. Analysis: descriptives (median, IQR) per variant; paired differences; with n = 8-10, Wilcoxon signed-rank for SEQ and time and a sign test for preference, all exploratory; thematic coding of comments and think-aloud notes. The same decision rule as section 8.5. How to load `data-template.csv` and the simulated CSV into Power BI. What would change the recommendation. |
| `data-template.csv` | Header row only: the 8.3 columns, plus `card` and `moderator_notes`. |

## 12. Steps for the writer (in order)

1. Create D1, D2. Run both `diff` checks (section 4).
2. Create D3, D4 verbatim. Check: `python -c "import yaml,json;print(len(yaml.safe_load(open('personas.yaml',encoding='utf-8'))), len(json.load(open('ab_policies.json'))['policies']))"` prints `10 12`.
3. Write `metrics.py`, the fixture and `test_metrics.py`. Run `python test_metrics.py` until it prints OK.
4. Write `run_ab.py` and `build_report.py`. Run `python build_report.py` with no results; it must exit 0 and write the "Results pending" files.
5. Run `python run_ab.py` with no args; it must print usage and exit 2.
6. Smoke test, once: `python run_ab.py --only P01-A --parallel 1`. This is 1 conversation plus 1 judge call. It saves `P01-A.json` and rebuilds the report with 1 of 20 complete. Keep the result; the full run will skip it. If it fails, fix and retry at most twice, one at a time.
7. Write `chat_variant.py`; run only `python chat_variant.py --help`.
8. Write the eight kit files.
9. Report back: files created, files changed (none outside `03-usability-ab/` except D1 and D2), smoke-test output line, any step not done and why.

## 13. Orchestrator run (later, not the writer)

```
cd C:/Users/edydo/myportfolio/projects/fnol-case-study/03-usability-ab
python run_ab.py --all --parallel 2
```

Resumable: re-run the same command after any interruption. Finished conversations are skipped, judge and preference gaps are filled. Expect roughly 45 to 75 minutes. The report rebuilds at the end. `python build_report.py` can be run again on its own at any time. After the run, fill the kit's "Changes after the simulated pilot" section.

## 14. Acceptance criteria

### Stage 1: code, materials and kit (reviewed this round)

1. `diff 02-prototype/agent/prompts/system_v1.md 02-prototype/agent/prompts/system_ab_story.md` prints nothing.
2. `diff .../system_ab_story.md .../system_ab_form.md` prints a single `24c24` hunk, and the new line matches section 4 word for word.
3. `sam.py`, `tools.py`, `mock_data.json`, `system_v1.md`, `02-prototype/harness/*`, `PROGRESS.md` and the root `README.md` are unchanged (writer's file list; file contents).
4. `personas.yaml` has 10 personas P01-P10 matching section 5 (spot-check 3 against the plan). Orders alternate AB/BA. Each has every field in the section 5 schema.
5. `ab_policies.json` has 12 policies WTL456801-812 with no key that collides with `mock_data.json`. Every persona's `ground_truth.policy_number` and `vehicle_rego` exist in it.
6. `python -c "import sys; sys.path.insert(0,'03-usability-ab'); import run_ab, sam, tools; print(sorted(sam.VERSIONS), 'WTL456810' in tools.POLICIES)"` (run from the case-study folder) lists `abA`, `abB`, `v1` (and `v2`), and prints `True`. Importing starts no conversation.
7. `python 03-usability-ab/test_metrics.py` prints `OK` and covers every check in section 8.4.
8. `python 03-usability-ab/run_ab.py` with no args exits with code 2 and prints usage. `--parallel 5` is capped at 2 (visible in code and in the printed line).
9. `run_ab.py` skips conversations that already have a JSON file unless `--rerun`, writes files atomically, fills missing judge and preference results, and calls `build_report.main()` at the end (read the code).
10. `run_ab.py` reuses `sam.build_options`, `sam.ask`, `tools.ToolState` and `run_tests.render`/`customer_reply` by import, not copies. The prompts in 7.2 appear verbatim. The judge prompt never names the variant.
11. `results/simulated/transcripts/P01-A.json` exists from the smoke test and follows schema 7.4, including `ms` per turn, `questionnaire` with integer seq and csat, and `data_source: "simulated"`. `P01-A.md` starts with the simulated label line.
12. `python 03-usability-ab/build_report.py` exits 0 and writes `ab_results.csv`, `ab_results.json`, `ab_preferences.csv`, `README.md`, `report.html` and six `charts/*.svg`. The CSV header equals the 8.3 column list in order, and every row has `data_source` = `simulated`.
13. Simulated labelling: the HTML banner and README blockquote carry the section 9.2 wording; every chart `<title>` starts with "Simulated: "; `ab_results.json` has `data_source: "simulated"`; comments are tagged "(simulated)". `grep -c "Simulated: " report.html` is at least 6.
14. `report.html` has the 10 sections of 9.2 in order. It has no `<script src`, no `<link` to an external host and no `http` URL except plain text links; it has `prefers-color-scheme` CSS and a `body` background. It opens from a file with no console errors and has no horizontal scroll at 375px width.
15. Each SVG has `<title>`, `<desc>`, `role="img"`, a dark-mode media query and value labels in text. The SVG files display in the GitHub README (`![...](charts/x.svg)` links resolve).
16. `README.md` renders as Markdown (no raw HTML apart from the first comment), and includes the hypothesis, the decision rule, the A vs B line 24 text, the limitations, the reproduce commands and links to `report.html` and the kit.
17. `python 03-usability-ab/chat_variant.py --help` prints usage. The code never prints the variant to the participant and saves to `results/real/` with `data_source: "real"`.
18. The kit has all 8 files from section 11, each with its required content and the closing disclaimer line. Card policies WTL456811 and WTL456812 match `ab_policies.json`. The counterbalancing table covers R01-R10 with the four orders. The consent form names the Privacy Act 1988 (Cth) and the Australian Privacy Principles, without section numbers. `data-template.csv` header = 8.3 columns + `card`, `moderator_notes`.
19. No real insurer names or branding anywhere in `03-usability-ab/` (brand is Wattle Car Insurance). Plain Australian English, short sentences, no emoji.

### Stage 2: data-dependent (checked after the orchestrator's run)

20. `transcripts/` holds 20 JSON + 20 MD files (P01-P10 × A, B); `preferences/` holds 10 files.
21. Each persona's two conversations have `order_position` 1 and 2 matching its `order` field.
22. `ab_results.csv` has 20 rows. Fewer than 2 rows have a blank `seq` or `csat`. No row has `hit_turn_cap` = 1 without a note in the README limitations.
23. Spot-check 3 transcripts by hand: variant A asks the details in the fixed order; variant B invites the story and asks only for gaps; `facts_correct` matches what the create_claim input shows.
24. The heuristic `reasked_facts` and the judge `reasked_facts_judge` agree in direction (the variant with more repeats is the same for both). If not, the README says so.
25. The recommendation follows the 8.5 rule given the numbers in `ab_results.json`, starts with "Simulated pilot result:", and the README and HTML show the same recommendation and numbers.
26. The kit's "Changes after the simulated pilot" section is filled in with at least 2 concrete findings (for example a persona trait that made a task too easy, a turn cap, or a metric that misfired).
