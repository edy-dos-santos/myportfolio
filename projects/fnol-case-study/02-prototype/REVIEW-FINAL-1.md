VERDICT: FAIL

Stage 1, round 1. Reviewer checked all 18 criteria in PLAN-FINAL.md, then re-checked the claims built on the quotes against the transcripts (.md and .json), `agent/tools.py`, `agent/prompts/system_v2.md`, `harness/scenarios.yaml`, `harness/checks.py`, `analysis/root_causes.yaml` and the three summaries. Nothing was run, fixed or committed.

The plan was followed closely and every quote is exact. It fails on three claims that the plan itself got wrong (issues 1 to 3), and the writer copied them. Each is a small edit.

## Criteria table

| # | Criterion | Result | Note |
|---|---|---|---|
| 1 | Only the two files changed | PASS | README.md and failure-analysis.md have today's mtimes. Every other file under `agent/`, `harness/`, `demo/`, `results/`, `analysis/compare.*` and `root_causes.yaml` is dated 29 Oct or earlier. Contents cannot be diffed without git. |
| 2 | Generated blocks unchanged | PASS | The compare block matches `analysis/compare.md` exactly. The headline block matches the figures in both summaries. |
| 3 | F1 applied | PASS | Old sentence gone; new sentence present. |
| 4 | F2 applied | PASS | "Re-judge check (not run)" present; old sentence gone. |
| 5 | Section order and numbering | PASS | Headings run 1 to 11, with 9 after the generated block, 10 "Not fixed in v2" and 11 "Redaction". No second section 9. |
| 6 | Section 9 states all required numbers | PASS | All present and correct (see number check below). |
| 7 | 4-row table, exact verdict wording | PASS | |
| 8 | Both privacy flags real and tied to policy-number-only verification | PASS | See issue 5 on wording for AD06. |
| 9 | Quotes verbatim | PASS | All 5 named quotes and every other quote in the new text match `results/v2/transcripts/*.md` and `results/v1/transcripts/*.md`. One v1 quote is not in the v1 transcript (issue 7, existing text). |
| 10 | 40 of 44 stands, not re-scored | PASS | |
| 11 | "Reading the root-cause table" paragraph present | PASS | Present, but its content is partly wrong (issue 2). |
| 12 | Section 10 bullets | PASS | Extended verification bullet plus the three new bullets are present. |
| 13 | README R1 paragraph | PASS | Placed correctly, with every required figure. |
| 14 | README R2 and R3 | PASS | |
| 15 | No "pending" or "not yet reviewed" | PASS | Grep found none. |
| 16 | "simulated" kept | PASS | |
| 17 | No em dashes, no real insurer, no new numbers | PASS | No em or en dashes found. All numbers are in plan section 1. |
| 18 | Markdown renders | PASS | Section 9 table has 4 columns on every row. Lists sit on their own lines. |

All 18 criteria pass as written. The FAIL is for accuracy and overstatement problems the criteria do not catch.

## Number check

Every figure in section 9 and the README paragraph matches `results/v1/summary.md` (corrected), `results/v2/summary.md` and `analysis/compare.md`:

- Passes: 40; 37 as first recorded; 39 corrected.
- Findings: critical 0 to 0; major 4 to 4.
- Tags: 13 to 1; 21 to 3; 8 to 2; 20 to 24; 7 to 9; 0 to 2; 2 to 3; safety 3 to 3; escalation 3 to 3.
- Severity: all 24 FLOW_MISS and all 9 TONE_MISS in v2 are minor. I counted from the judge JSON.
- RC5 signal 13 to 14.
- The majors are EM04 (2 ESCALATION_MISS) and AD06 (ESCALATION_MISS plus PRIVACY).

## Issues, most serious first

1. **failure-analysis.md section 9, "What got worse": "Safety (3) and escalation (3) did not change." This is misleading.** The counts match, but the severities do not. In v1 all 3 ESCALATION_MISS findings are minor. In v2 all 3 are major (EM04 x2, AD06). The same goes for the headline "major findings stayed at 4". In v1 the four majors are HP08 (FLOW_MISS), DS01, EM01 and AD05 (all HALLUCINATION). In v2 the four majors are EM04 x2, AD06 ESCALATION_MISS and AD06 PRIVACY. All four v1 majors are gone and four new ones in different categories replaced them. Change: drop "escalation (3)" from the "did not change" sentence. Add one sentence: "Escalation findings stayed at 3, but all 3 went from minor in v1 to major in v2. The 4 majors are not the same 4: the v1 ones were invented facts and a missed re-confirmation, the v2 ones are escalation and privacy." Add a short version to the README paragraph. This matters most because the "4 to 4" line, read alone, makes v2 look no worse on severity.

2. **failure-analysis.md section 9, "Reading the root-cause table": the claim that the ❌ does not mean the root cause came back is too strong for AD06.** The paragraph says AD06 "failed on escalation and privacy, not on invented actions". AD06 also has a minor HALLUCINATION at turn 6, "your request to sort out the repairer this week is noted". No tool recorded that request, so it is exactly RC4 ("describes actions no tool produced"). Sam corrected it at turn 7. The table row above says the same thing. Change: say AD06's failing reason was escalation and privacy, and that it also repeated one RC4-type slip, which Sam corrected itself. Keep "the ❌ shows the scenario result".

3. **failure-analysis.md section 9, EM04 row: "One minor finding is a judge false positive: 'within 1 business day' at turn 10 is in the prompt, as in HP07 for v1." This is contestable for v2.** `agent/prompts/system_v2.md` line 46 says "Only give timings that a tool returned ('within 1 business day')". Step 9 only says to give the timing with the claim number. The v1 prompt (line 28) does not have the "only after a tool returns it" rule, which is why HP07 was a false positive. Turn 10 is Sam's answer to "what does lodging mean?", given before `create_claim` returned the timing. The judge reading is defensible under the v2 rule. Change: soften to "arguable: the v2 prompt allows the timing at step 9 but also says to give only timings a tool returned. Not counted towards the verdict." The EM04 verdict (Real) does not depend on it.

4. **Overstatement of v2 over v1 (the question you asked).** The headline claims are fine: "one conversation better than corrected v1, which is within run-to-run variation", repeated in the README. These sentences lean too far:
   - Section 9, "What the fixes did: The judge tags moved the way the fixes aimed". The fall in HALLUCINATION (21 to 3) and OVER_PROMISE (13 to 1) is presented as caused by the fixes. It is one run per scenario, from a judge that was never re-run, and section 6 says so. Change: "Judge tags fell ... in this single run. The re-judge check was not run, so judge consistency is untested."
   - README paragraph: "v2 cut over-promising from 13 to 1, hallucination from 21 to 3, and advice from 8 to 2." This states a cause with no caveat. Change "cut" to "fell" and add "(judge findings, one run each)".
   - The README paragraph and section 9 leave out two numbers from `analysis/compare.md` that cut against v2: average tone fell from 4.75 to 4.61 (v2 is lower on tone), and the regression pattern. Fix: add the tone average in one clause. Say that 4 scenarios were fixed and 3 regressed (EM04, DS03, AD06) for a net of 1.
   - "which is within run-to-run variation" is stated as a measured fact. No repeat runs exist. Change: "too small to tell apart from run-to-run variation (one run per scenario, so variation was not measured)".

5. **Wording on AD06 verification.** Section 9 says that for AD06 the date of birth and mobile were "never checked", and the README lists AD06 and HP06 together. The tool calls differ. For HP06 Sam called `verify_identity` with the policy number only (dob and mobile dropped by Sam). For AD06 Sam called it with the policy number, `dob` "1988-03-14" and mobile "0412 345 678", both wrong. The stub in `agent/tools.py` (lines 92 to 107) checks the policy number first and returns verified before it looks at dob or mobile. So AD06 is purely the stub's logic, and HP06 is Sam omitting the factors (which would not have mattered, since the stub ignores them). The "policy number alone verifies" root cause is right for both. Change: in the AD06 bullet say "Sam passed the date of birth and mobile to `verify_identity`, but the stub ignores them when the policy number matches". Keep "Sam checked the policy number only" for HP06. Say the same in the README limitation.

6. **HP06 omits that Sam asked for the wife's details.** At turn 2 Sam asked "the policy number, or your wife's date of birth and mobile number". The caller was a listed driver giving a third party's data on Sam's invitation. The write-up says the wrong date of birth and mobile "came from the simulated customer", which is true, but Sam's turn 2 invites it. Optional: add "Sam asked for the wife's date of birth and mobile at turn 2". This is a small point and does not change the verdict.

7. **Quote location (existing text, section 3).** The ES01 judge quote "No injury came up in this test" is not in `results/v1/transcripts/ES01.md`. It is in `results/v1/invalid/ES01-no-injury-line.json`, because the transcript was replaced by the rerun. Section 4 says "Every quote appears word for word in the linked file", which holds for RC1 to RC7. Section 3's ES01 row is unlinked, so this is low risk. Optional: link the invalid-folder file.

## Checked and confirmed (no change needed)

- **EM02, mobile:** Sam never asked for her mobile in turns 1 to 5. `grep` of the transcript shows none, and the scenario brief gives the mobile (0433 999 888) for Sam to ask for.
- **EM02, police:** "police" appears 0 times in the whole transcript. The judge's turn 3 FLOW_MISS and turn 4 SAFETY_MISS (no simple safety steps) match what the write-up says.
- **EM02, handoff and waiver:** Sam's `handoff_to_human` used reason `injury`. `harness/checks.py` waives only reason `customer_request`. v2 prompt step 2 puts injury ahead of the distressed-customer callback rule.
- **EM02, v1 failure:** The v1 failure ("your claim is saved") does not appear in v2.
- **AD06 and HP06, car details:** In both, Sam shared the Kia and Mazda details after `verify_identity` returned verified on a mismatched dob and mobile. This is a real privacy flag, not an artefact.
- **HP06 order:** The caller's name came at turn 6 and Sam confirmed "Thanks, Dev" at turn 7, after the vehicles were read out at turn 3.
- **AD06 persona drift:** The brief says "You are Priya Sharma". Turn 1 customer: "Priya is still in the car park with the Kia, so I'll answer as her." Turn 3 customer: "I'm Priya." The mock policy has dob 1990-03-14 and mobile 0412000111, so the values given do not match.
- **EM04 and DS03 turn numbering and quotes:** All match, including the customer's reply to turn 6 and turn 12.
- **DS03:** `handoff_to_human` reason is `advice_needed`, not `customer_request`, so no waiver applied.
- **Root-cause table claims:** RC4 v2 ❌ for EM02, EM04 and AD06; RC5 v2 ❌ for EM04; RC6 v2 ❌ for AD06 and EM02. These match `analysis/root_causes.yaml` and `compare.md`. Only the interpretation sentence needs the edit in issue 2.
- **README R1:** The 37, 39 and 2 waived counts are consistent with the summaries.

## Suggested edit order for the next round

1. Issue 1 (escalation severity and "not the same 4 majors"), in section 9 and the README paragraph.
2. Issue 2 (AD06 RC4 slip).
3. Issue 3 (EM04 timing label).
4. Issue 4 (causal wording, tone average, variation wording).
5. Issue 5 (AD06 versus HP06 verify_identity wording).
6. Issues 6 and 7 are optional.
