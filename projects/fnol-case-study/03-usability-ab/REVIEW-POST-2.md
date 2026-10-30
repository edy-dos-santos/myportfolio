VERDICT: PASS

Reviewer, stage 2 post-run, round 2. Checked the three round-1 issues against the transcripts and current files. No conversation, judge or preference call. Git untouched. I reran `build_report.py` as asked, so `generated_at` is now 2026-10-30T06:32:13+10:00.

## Criteria

| # | Criterion | Result |
|---|---|---|
| 1 | P10-B unasked safety assurance named, counted as success | Pass. P10-B.md line 34 (Sam turn 5): "The front bumper is cracked, a headlight is broken, and the car is safe to drive." Customer line 31 said only "It still drives fine." Summary line 47 "Safe to drive: Yes", create_claim line 53 `drivable: "yes"`. README line 216 (and report.html) quotes it, says Sam said it "without asking", that it "counts as a success", and calls it "a real Sam error that the metric did not catch". |
| 2 | P01-A drift is persona's, first doubt from variant A | Pass. Quotes at P01-A.md lines 29, 33, 34, 40 all match. README line 215 reads "The drift is the persona's. But the first doubt came from variant A's form question about the tail-lights, so this miss is partly the test design." Present in both README and report.html. |
| 3 | Box opening gives the total | Pass. README line 16 and report.html: "task success for 10 personas against 8, out of 10 paired personas". |
| 4 | Modelled-time sentence | Pass. Box says "B would still win, but only on modelled time (21% less)". ab_results.json: A est_customer_seconds mean 1025.62, B 812.87; 1 - 812.87/1025.62 = 20.7%, rounds to 21%. Matches line 217 (813 s v 1026 s). |
| 5 | Kit "Changes after the simulated pilot" | Pass. Section is 84 words (including the closing disclaimer line), under 120. Items match transcripts: (1) persona drift, P01-A "I'm at the lights right now" then "Sorry, I shouldn't have said I was at the lights"; (2) later-mentioned conditions, P10-A night driving and broken headlight against ground truth "yes"; (3) form question planting doubt, P01-A line 29 then 30. |
| 6 | Rebuild and tests | Pass. "Built report: 20 of 20 conversations complete (simulated). Recommendation: B." test_metrics OK (59 tests). test_offline OK (14 tests). |
| 7 | Data unchanged | Pass. Compared with a copy taken before the rebuild: ab_results.json differs on `generated_at` only; both CSVs, all transcripts and preference files identical; all charts identical; README differs only on the "Generated ..." line. |
| 8 | Round-1 stale promise (issue 7) | Pass. Kit section now filled, so the README link lands on content. |

## Issues, most serious first (all minor, none block)

1. **Kit item 3 rests on one case.** "The form-first question can plant doubt the participant did not have" is shown only by P01-A. The wording is a recommendation to test it, not a finding, so it is acceptable. Optional: add "(seen once, in P01-A)".
2. **README line 217 "both followed A's fixed safe-to-drive question".** P01-A's question is the scripted one (generic tail-lights wording). P10-A's was tailored ("With the broken headlight, do you feel the car is safe to drive, including at night?"). It still came from A's safe-to-drive step, so the sentence is defensible, but "A's safe-to-drive step" would be more exact.
3. **Box wording is slightly awkward.** "10 personas against 8, out of 10 paired personas" is clear enough and now gives the total. Optional tidy: "10 of 10 personas against 8 of 10".
4. **Round-1 optional point still open.** The box does not mention the 7-of-10 preference gap (Limitations does). Not required.

Portfolio exercise review. No legal content assessed.
