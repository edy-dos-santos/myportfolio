VERDICT: PASS

Stage 1, round 2. Reviewer: Sonnet. No Sam conversation run. Checked: `test_metrics.py` (OK, 59 tests), `test_offline.py` (OK, 14 tests), code read of `run_ab.py`, `chat_variant.py`, `metrics.py`, the P01-A record and transcript, the kit, and `report.html` in a browser (375px light, 1280px dark, via `http.server` on 8765, now stopped).

Ready for the full 20-conversation run. The issues below are minor and none blocks it. Issue 1 is worth a note in the README after the run.

## Round-1 issues

| # | Issue | Status |
|---|---|---|
| 1 | Variant leak | Fixed. `finish_session` prints only `Session saved.`, writes `session_log.txt`, screen clears before the chat prompt, no variant in any other print, error text is neutral. Tested. |
| 2 | Unpaired decision rule | Fixed. `paired_basis` drives all four rules; paired-only and paired-prefs tests pass. |
| 3 | Participant misses Sam's last message | Fixed (`questionnaire_message`), see (a). |
| 4 | Real-study timing and column | Fixed. `shown_at` starts after the prompt line; `time_source` column added; measured sum tested (44.0). Kit and template updated. |
| 5 | Overclaiming wording | Fixed. "pre-registered" grep is clean outside PLAN/REVIEW. New limitations and summary sentence found in both README and HTML. |
| 6 | Rule untested | Fixed. R0-R4, P, P-prefs, `check_facts` tests present. |
| 7 | `--rerun` stale preferences | Fixed. `stale_preferences` and deletion in `main()`. |
| 8 | Kit consistency | Fixed. Buffer row, 50 minutes (no "45 min" left), command-entry note, read-card-first note, date-of-birth note. |
| 9 | Chart text on phones | Fixed, with a UX cost (see issue 3). |
| 10 | Keyword bias | Documented as a limitation. |
| 11 | Housekeeping | "Data and files" heading done. `__pycache__/` left for the orchestrator. |

## Criteria

| # | Status | Note |
|---|---|---|
| 1-10, 12, 13, 15, 16, 18, 19 | Met | Unchanged from round 1, no regressions; CSV header now includes `time_source`, and the P01-A row has `data_source` = simulated. |
| 3 | Met | Per orchestrator, as round 1. |
| 11 | Met | Record has every schema 7.4 key; integer `ms` per turn (opening 0); `questionnaire` seq 6, csat 4; `data_source` "simulated"; `.md` starts with the simulated line. `lodged=1`, `facts=6/7`, 14 Sam turns, `hit_turn_cap` false. The last transcript entry is Sam's, so the participant ended with `[END]` and the questionnaire got Sam's final text. Tools used: verify_identity, get_policy, create_claim. |
| 14 | Met | No horizontal page scroll at 375px (scrollWidth 360 = clientWidth). No horizontal scroll at 1280px. Only console error is the `favicon.ico` 404 from `http.server`, not the page. Dark mode background applies. |
| 17 | Met | Tested. |
| 20-26 | Pending run | |
| 27 | Met | `OK (14 tests)`, no SDK call. |
| 28 | Met | Code and tests. |
| 29 | Met | `QUESTIONNAIRE_PROMPT` unchanged. |
| 30 | Met | |
| 31 | Met | |
| 32 | Met | |
| 33 | Met | |
| 34 | Met, with a caveat | SVG text 18px at the root, `.chart-scroll` with 520px minimum, `.ab-mean` tick visible and heavier in the 1280px screenshot. At 375px each chart scrolls inside its box; nothing overlaps. Bars and value labels are cut off until the reader scrolls (issue 3). |
| 35 | Met | |
| 36 | Met | `transcripts/` holds only the orchestrator's P01-A. |

## Deviations

- (a) Sam's final message shown again on `[END]`: **acceptable.** It applies to both variants equally, so it can't bias the comparison. Handoff and empty-reply cases need it anyway. Mention it in the method text if you want the plan and code to match exactly.
- (b) Extra `pair_ids` key in `paired_basis`: **acceptable.** Rule 3 needs it. It adds a list to the JSON summary only.
- (c) `data_source` read from the record: **acceptable, and better.** Real records must say `real`. The plan's 8.3 table should read "simulated for run_ab output, real for chat_variant output". The simulated report path always passes simulated records, so the report is unaffected.
- (d) "Already exists" error no longer names the file: **acceptable.** The error is raised before the participant looks at the screen, and the moderator knows the command. The wording "this participant and variant" is fine.

## Issues (most serious first)

1. **Persona improvisation changed a fact in P01-A (data-quality risk, no code change needed before the run).** The brief says the car drives fine. When Sam's form-first safety check asked about lights, Chloe (Haiku) said she hadn't checked the tail-lights, accepted "unsure", then said "I'm at the lights right now" (a slip: the crash was this morning) and corrected herself a turn later. `drivable` became "unsure", so `facts=6/7` and task success is 0. Nothing here is a bug in the harness, but some of the 20 task-success results will reflect persona improvisation, not Sam's capture strategy. The Limitations list should say this. After the run, read each `facts_correct` miss against the transcript before quoting success rates. This also means a persona is not fully fixed by its brief, which the README's "LLM personas are not people" bullet only partly covers.
2. **Modelled time is large.** P01-A's `est_customer_seconds` is 502.7 s, mostly typing at 40 wpm over 231 words and reading 651 words of Sam text. It is labelled `modelled`, so this is honest. A hiring manager may still read it as real time on task. Keep the "Not measured" caption on the time chart and don't quote it as seconds without that.
3. **Chart readability on phones.** At 375px the charts sit in a 328px scroll box over a 520px SVG. Bars and value labels run past the right edge (visible in the success and effort charts) until the reader scrolls. It is acceptable and meets criterion 34, but the data table under each chart is the reliable phone view. Optional: add "Scroll sideways to see the full chart" to the caption.
4. Small: the plan 8.3 table still says `data_source` is "Always `simulated`" (see deviation c). Also, `__pycache__/` is still in the folder; the orchestrator should exclude it from the commit.

Portfolio exercise, not legal advice. Check references against current versions.
