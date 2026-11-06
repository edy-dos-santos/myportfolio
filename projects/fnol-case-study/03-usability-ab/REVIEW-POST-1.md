VERDICT: PASS

Reviewer, stage 2 post-run, round 1. Checked against PLAN-POST.md section 7 and AGENT-BRIEF.md. No conversation, judge or preference call was made. Git untouched. I reran `build_report.py` (as asked), so `README.md`, `report.html` and the `generated_at` in `ab_results.json` now read 2026-10-30T06:29:06+10:00. Content is identical to the writer's 06:28 build.

## Criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Only build_report.py hand-edited | Pass. metrics.py, run_ab.py, chat_variant.py, personas.yaml, ab_policies.json, kit README, PROGRESS.md (03:00) all older than 30 Oct 06:00. Newest transcript/preference write 06:20, before PLAN-POST (06:27). |
| 2 | Edits E1 to E6 present | Pass, judged by output: every section-6 string is in both files (see 6). I did not diff the source line by line. |
| 3 | build_report.py exit 0 and message | Pass. "Built report: 20 of 20 conversations complete (simulated). Recommendation: B." |
| 4 | Tests | Pass. test_metrics OK (59 tests), test_offline OK (14 tests). |
| 5 | Generated line | Pass. README line 1 is the generated comment; "Generated ..." time equals `generated_at`. |
| 6 | Section 6 strings in both; "Complete pairs so far" absent | Pass (all 7 strings True in README and decoded HTML; old string absent in both). |
| 7 | Recommendation box content | Pass with comments (see issues 2 and 4). B stands; reason sentence equals `recommendation.reason`. |
| 8 | Quotes verbatim | Pass. P01-A.md lines 30, 34, 40; P10-A.md lines 41, 42; P10-B.md line 34 all match word for word. |
| 9 | Data unchanged | Pass, run against p3-post-before before my rebuild: JSON equal except generated_at (06:20:50 vs 06:28:06), both CSVs identical, all six SVGs identical. |
| 10 | Time caption | Pass. "Not measured" in both files. |
| 11 | Numbers | Pass. Summary bullets and the 813 s / 1026 s / 21% match `ab_results.json`. Only P01-A (6/7) and P10-A (5/6) have facts_correct < facts_checked. |
| 12 | Classification | Pass with a qualification (issue 1). |
| 13 | No Claude call | Pass. 40 transcript files, 7 preference files, none modified after 06:20. |
| 14 | Plain English, labelling | Pass. "Simulated: " appears 6 times in README and 12 in report.html; banner intact; no emoji. |

## Issues, most serious first

1. **P10-B is a real Sam error and the write-up does not say so.** `P10-B.md` line 34, Sam turn 5: "The front bumper is cracked, a headlight is broken, and the car is safe to drive." The customer only said (line 31) "It still drives fine." Sam never asked, turned "drives fine" into a safety assurance with a broken headlight, then put "**Safe to drive:** Yes" in the summary and sent `drivable: "yes"`. For an insurer that is the riskier behaviour. The Limitations bullet calls it only "the metric rewarded the variant that asked less about safety", and the box says "neither was an error by Sam" about A's misses, so a reader never learns that B's one "success" here is an unsafe statement. Change (build_report.py, POST_RUN_LIMITS bullet 2): add "In P10-B, Sam told the customer the car was safe to drive without asking, with a broken headlight. That is a Sam error the metric counted as a success." Consider one clause in the box too, since it is the finding that most weakens "B 10 of 10".

2. **"The cause is the persona, not Sam" (P01-A) is too strong.** Quotes, verbatim. Customer line 10: "No, nobody's hurt. We're both okay and the car's still driveable." The persona never mentions tail-lights until A's fixed step 5, Sam turn 7 (line 29): "You mentioned the car can still be driven. Is it safe to drive? For example, are the lights, boot and tail-lights working...". Customer line 30: "I haven't checked the tail-lights closely yet, so I'm not sure whether they're working." Sam turn 8 (line 33) then offers the exit: "If not, I'll record it as "unsure" for now". Customer line 34: "I'm at the lights right now and can't check them myself." Line 40: "Sorry, I shouldn't have said I was at the lights." Classification: participant drift is right for the "I'm at the lights right now" contradiction (the crash was that morning). But the first "unsure" is a plausible human answer to a question that planted the doubt, which makes P01-A partly a variant-A prompt effect and partly a ground-truth strictness problem like P10-A (a person who has not checked the lights is honestly unsure). Suggest: "Persona drift, triggered by A's scripted question and by Sam offering 'unsure' as an answer; the ground truth also allows only 'yes'." Keep "not a Sam failure" only if it is worded as "Sam recorded what the participant said".

3. **P10-A classification (metric artefact) is right.** Quotes: line 41 Sam: "You said it still drives fine. With the broken headlight, do you feel the car is safe to drive, including at night?"; line 42 customer: "Not really sure about night driving. The headlight is out on that side, so I'd rather not drive it at night until it's fixed. It's been fine in daylight so far."; Sam line 43: "I'll note it's drivable in daylight only"; summary line 65 "In daylight only. Headlight out, so not at night." Sam recorded `drivable: "unsure"` with flag `drivable_daylight_only_headlight_out` and the customer confirmed. The ground truth `["yes"]` is the weak part. This is the more careful behaviour of the two variants and the report says so.

4. **Box limits: honest but still easy to misread.** B is still justified: rule 1 fires at exactly the threshold (10 vs 8, "2 or more"); the reason sentence is the tested one. The appended note states simulated, 10 simulated personas, a 2-persona gap is small, one changed outcome drops below the threshold, not evidence about real people, real study should test it. All five required points are present. Two weaknesses: (a) the first sentence still says "task success for 10 personas against 8", which reads like counts of successes out of an unstated total; the note rescues it but only after a long paragraph. (b) The note says nothing about modelled time or the 7 of 10 preferences, and rule 2's fallback (if misses were forgiven) rests on word-count-modelled time that is partly a prompt-length effect (Limitations already say so). Optional: add "Even if both misses were forgiven, B would win only on modelled time." to the box.

5. **Seven facts fix and preference count: done.** "Facts correct: up to seven facts checked ... (P02, P04, P05 and P10) ... six" matches the data (the 6/6 and 5/6 rows are consistent). Preference bullet reads "A 3, B 4, no preference 0 (of 7 personas; no preference recorded for P04, P05, P06)", and Limitations explains the gap and that rule 3 was not reached. The reason for the missing files is stated as missing, not why they are missing (the parse or run did not produce them); the plan notes that cause as unknown/out of scope, so acceptable, but "why" is not given.

6. **Overclaim check as a hiring manager.** I found no sentence that presents a simulated result as a finding about people. The banner, section heading "Results (simulated)", chart titles, quote labels "(simulated)", and Limitations are all clear. Residual risks, all minor:
   - "This de-risks the study design" and "Recommendation: variant B" in a box titled "Recommendation (rule written before the run)" can read as a product decision. The box does say "Confirm with the real study", so acceptable.
   - "Estimated participant time" as a heading for what is Sam-message word count; labelled modelled in the summary, fine.
   - Simulated participant quotes include emotional lines ("glad someone was helping me", "a real relief", "still shaking"). Each is tagged "(simulated)"; they are not evidence of feeling.
   - "If both had counted as successes ... B stays the recommendation ... the evidence for it is weak" is honest and a strength. However it is post-hoc reasoning about the scoring; the plan correctly refuses to change the scoring after seeing results and the report shows that.

7. **Stale promise, out of scope but visible.** README line 226 and report.html line 471: "Changes after the simulated pilot are recorded in the kit's README once the run is complete." The run is complete, and `real-study-kit/README.md` line 62 still says "To be filled in after the simulated run." A reader following the link finds nothing. Orchestrator should fill the kit section (candidates: persona drift on a safety probe, ground truth allowing a conditional drivable answer, P10-B unasked safety assurance, 7 of 10 preferences) or reword the sentence. PLAN-POST section 8 already flags this.

Portfolio exercise review. No legal content assessed.
