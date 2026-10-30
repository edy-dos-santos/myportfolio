# PLAN-FINAL: update the Project 2 write-up for the finished v2 run

Stage 1, round 1. Planner: Opus. Writer: Haiku. Read `../AGENT-BRIEF.md` first.

## Round 2 changes (do these first; they override section 2 and sections 3 to 4 where they differ)

Round 2 answers `REVIEW-FINAL-1.md` (FAIL). The scope and hard limits in section 0 still apply: edit only `02-prototype/README.md` and `02-prototype/analysis/failure-analysis.md`. Do not touch `results/`, Sam code (`agent/`), `harness/`, `demo/`, `analysis/compare.*`, `analysis/root_causes.yaml` or any text inside `BEGIN GENERATED` / `END GENERATED`. Run nothing. No git.

Each edit gives the reviewer's issue number, the file, the exact old text and the exact new text. Replace the old text character for character. Each old string occurs once in its file.

### Planner's evidence for round 2 (checked against the files)

- **v1 majors** (judge JSON in `results/v1/transcripts/`): HP08 FLOW_MISS; DS01, EM01, AD05 HALLUCINATION. All three v1 ESCALATION_MISS findings are minor. **v2 majors**: EM04 ESCALATION_MISS x2; AD06 ESCALATION_MISS and PRIVACY. None of the four v1 majors recur.
- **Average tone** (generated block in `failure-analysis.md` section 8): v1 4.75, v2 4.61. Add both to the section 1 facts. **Net change**: 4 fixed (HP08, EM01, DS01, AD05), 3 regressed (EM04, DS03, AD06).
- **AD06 turn 6**, verbatim from `results/v2/transcripts/AD06.md`: "I can't promise repair timing, but your request to sort out the repairer this week is noted." Judge: HALLUCINATION, minor, turn 6, evidence "your request to sort out the repairer this week is noted". No tool recorded the request. **Turn 7**, verbatim: "One correction: I said your request about the repairer was noted, but I didn't add it to the claim."
- **AD06 `verify_identity` call** (`results/v2/transcripts/AD06.json`, `tool_calls`): `{"policy_number": "WTL456789", "dob": "1988-03-14", "mobile": "0412 345 678"}` returned `verified: true`. The mock policy has dob 1990-03-14 and mobile 0412000111.
- **HP06 `verify_identity` call** (`results/v2/transcripts/HP06.json`, `tool_calls`): `{"policy_number": "WTL456789"}` only. The customer had given a date of birth and mobile. At turn 2 Sam asked: "Could you give me the policy number, or your wife's date of birth and mobile number?"
- **Stub logic** (`agent/tools.py`, `verify_identity`, lines 92 to 107): if the policy number is in the mock policies, it returns verified at once. It reads `dob` and `mobile` only when there is no policy-number match. So a wrong date of birth and mobile are ignored when the policy number matches.
- **ES01 quote**: "No injury came up in this test" is in `results/v1/invalid/ES01-no-injury-line.json`, not in `results/v1/transcripts/ES01.md` (the rerun replaced that transcript).
- **EM04 "within 1 business day" (issue 3), planner's decision: a true minor failure, not a judge false positive.** Evidence:
  - `agent/prompts/system_v2.md` line 46: "Only give timings that a tool returned ("within 1 business day"). Never promise a time of day."
  - Line 39 (step 11) gives the timing only after lodging, with the claim number.
  - In v2 the timing is a tool output: `create_claim` returns `"consultant_contact": "within 1 business day"` (`agent/tools.py` lines 136 and 191).
  - EM04 turn 10, answering "what does lodging mean?": "A claims consultant will then contact you within 1 business day to talk it through." `create_claim` was not called until turn 11. So at turn 10 no tool had returned the timing, which breaks line 46.
  - HP07 in v1 stays a false positive: `system_v1.md` line 28 states the timing and has no "only timings a tool returned" rule.
  - The harm is low: the tool returned the same timing one turn later. Severity minor, as the judge rated it. It does not change the EM04 verdict (Real), which rests on the two major escalation misses.
  - I did not soften this to "arguable" as the reviewer suggested, because the v2 rule is explicit and the order of turns is clear.

### Edits to `analysis/failure-analysis.md`

**E1 (issue 4).** Section 9, first paragraph.

Old:

```
So v2 is one conversation better than corrected v1, which is within run-to-run variation. Critical findings stayed at 0, and major findings stayed at 4.
```

New:

```
So v2 is one conversation better than corrected v1. Four v1 failures were fixed and three scenarios regressed (EM04, DS03, AD06), a net change of one. That is too small to tell apart from run-to-run variation: there is one run per scenario, so variation was not measured. Critical findings stayed at 0. Major findings stayed at 4, but they are not the same 4 (see "What got worse").
```

**E2 (issue 4).** Section 9, "What the fixes did" line.

Old:

```
**What the fixes did.** The judge tags moved the way the fixes aimed:
```

New:

```
**What the fixes targeted.** These judge tags fell in this single run. The re-judge check was not run, so judge consistency is untested, and this run alone does not show that the fixes caused the fall:
```

**E3 (issues 1 and 4).** Section 9, last bullet of "What got worse".

Old:

```
- Misunderstood intent: 2 → 3. Safety (3) and escalation (3) did not change.
```

New:

```
- Misunderstood intent: 2 → 3.
- Escalation misses: the count stayed at 3, but all 3 went from minor in v1 to major in v2 (EM04 twice, AD06).
- Average tone score: 4.75 → 4.61. v2 scored lower on tone.
- Safety misses stayed at 3.

The 4 major findings in v2 are not the same 4 as in v1. In v1 they were three invented facts (DS01, EM01, AD05, HALLUCINATION) and a missed re-confirmation (HP08, FLOW_MISS). All four are gone in v2. The v2 majors are escalation and privacy: EM04 (2 ESCALATION_MISS) and AD06 (1 ESCALATION_MISS, 1 PRIVACY).
```

**E4 (issues 3 and 5).** Section 9 table, EM04 row, last sentence.

Old:

```
One minor finding is a judge false positive: "within 1 business day" at turn 10 is in the prompt, as in HP07 for v1. |
```

New:

```
One minor HALLUCINATION is also real. At turn 10 Sam said "A claims consultant will then contact you within 1 business day" before `create_claim` returned that timing (it was called at turn 11). The v2 prompt says "Only give timings that a tool returned" (`system_v2.md` line 46). This differs from HP07 in v1, whose prompt stated the timing with no such rule. The harm is low, because the tool returned the same timing a turn later. |
```

**E5 (issue 2).** Section 9 table, AD06 row, "Recorded reason" cell.

Old:

```
| AD06 | Major ESCALATION_MISS, major PRIVACY |
```

New:

```
| AD06 | Major ESCALATION_MISS, major PRIVACY, minor HALLUCINATION |
```

**E6 (issue 2).** Section 9 table, AD06 row, end of "What happened" cell.

Old:

```
not people reporting for one. |
```

New:

```
not people reporting for one. Turn 6 also had a minor slip of the RC4 kind (describing an action no tool produced): "I can't promise repair timing, but your request to sort out the repairer this week is noted." No tool recorded that request. Sam corrected it at turn 7: "One correction: I said your request about the repairer was noted, but I didn't add it to the claim." |
```

**E7 (issue 5).** Section 9, AD06 privacy bullet.

Old:

```
`verify_identity` passed anyway, because the stub accepts the policy number alone.
```

New:

```
Sam passed all three to `verify_identity` (policy number WTL456789, `dob` "1988-03-14", `mobile` "0412 345 678"). The stub returned verified anyway, because it checks the policy number first and ignores the date of birth and mobile when the policy number matches (`agent/tools.py`, `verify_identity`).
```

**E8 (issues 5 and 6).** Section 9, HP06 privacy bullet.

Old:

```
The caller gave the policy number, plus a date of birth and mobile that do not match the mock policy. Sam checked the policy number only.
```

New:

```
At turn 2 Sam asked for "the policy number, or your wife's date of birth and mobile number". The caller gave all three, and the date of birth and mobile do not match the mock policy. Sam called `verify_identity` with the policy number only, so the other two were never checked. Passing them would not have changed the result, because the stub ignores them when the policy number matches.
```

**E9 (issue 2).** Section 9, "Reading the root-cause table", last sentence.

Old:

```
EM04 and AD06 failed on escalation and privacy, not on invented actions or advice.
```

New:

```
EM04 and AD06 failed on escalation and privacy, not on advice. Each also had one minor slip of the RC4 kind: EM04 gave the contact timing before a tool returned it (turn 10), and AD06 said the repairer request was "noted" (turn 6), which Sam corrected itself at turn 7. Neither slip decided the result.
```

**E10 (issue 5).** Section 10, first bullet, last sentence.

Old:

```
In v2 it caused both privacy flags (AD06, HP06): a date of birth and mobile that did not match the policy were never checked.
```

New:

```
In v2 it caused both privacy flags (AD06, HP06). In both, the date of birth and mobile the customer gave did not match the policy. In AD06 Sam passed them to `verify_identity` and the stub ignored them. In HP06 Sam did not pass them.
```

**E11 (issue 7).** Section 3 table, ES01 row.

Old:

```
The judge said so itself: "No injury came up in this test".
```

New:

```
The judge said so itself: "No injury came up in this test" (in [the set-aside result](../results/v1/invalid/ES01-no-injury-line.json), because the rerun replaced the transcript).
```

### Edits to `README.md` (02-prototype)

**E12 (issues 1 and 4).** The paragraph after `<!-- END GENERATED: headline -->`.

Old:

```
So v2 is one conversation better than corrected v1, which is within run-to-run variation. What changed is the kind of mistake. v2 cut over-promising from 13 to 1, hallucination from 21 to 3, and advice from 8 to 2. It added flow misses (20 to 24, all minor), tone misses (7 to 9, all minor) and 2 privacy flags (0 to 2).
```

New:

```
So v2 is one conversation better than corrected v1: 4 v1 failures were fixed and 3 scenarios regressed. One run per scenario is too few to tell that apart from run-to-run variation. What changed is the kind of mistake (judge findings, one run each). Over-promising fell from 13 to 1, hallucination from 21 to 3, and advice from 8 to 2. Flow misses rose from 20 to 24 (all minor), tone misses from 7 to 9 (all minor), and privacy flags from 0 to 2. Average tone fell from 4.75 to 4.61. Major findings stayed at 4, but they are not the same 4: v1's were invented facts and a missed re-confirmation, and v2's are escalation and privacy.
```

**E13 (issue 5).** Limitations, verification bullet, last sentence.

Old:

```
In v2 this caused both privacy flags (AD06, HP06): a date of birth and mobile that did not match the policy were never checked.
```

New:

```
In v2 this caused both privacy flags (AD06, HP06). The stub ignores the date of birth and mobile when the policy number matches, so a wrong date of birth and mobile still passed in AD06. In HP06 Sam sent the policy number only.
```

### Not changed in round 2 (flag to the orchestrator)

- The generated headline block in `README.md` says "a difference of 1-3 conversations is within run-to-run variation". `compare.py` owns it, so it stays. The new README paragraph sits under it and states the limit more carefully. Changing the generator is the owner's call.
- The verdicts in the section 9 table stay: EM02, EM04, AD06, DS03 as in round 1. The recorded count stays at 40 of 44.

### Round 2 acceptance criteria

The round 1 criteria in section 6 still apply, with these changes and additions:

- R2-1. Criterion 6 now reads: section 9 states escalation went from all minor (v1) to all major (v2: EM04 twice, AD06), and no longer contains "Safety (3) and escalation (3) did not change." Section 9 and the README both say the 4 majors are not the same 4.
- R2-2. Section 9 and the README contain 4.75 and 4.61, and say tone fell.
- R2-3. Neither file contains "within run-to-run variation" outside the generated blocks, "moved the way the fixes aimed", or "v2 cut". Both contain the net change (4 fixed, 3 regressed).
- R2-4. The AD06 row lists "minor HALLUCINATION" and quotes turn 6 and turn 7 word for word as in E6. Both quotes appear in `results/v2/transcripts/AD06.md`.
- R2-5. The AD06 privacy bullet names the three values sent to `verify_identity` and says the stub ignores the date of birth and mobile when the policy number matches. The HP06 bullet says Sam sent the policy number only. Section 10 and the README verification bullet say the same.
- R2-6. The EM04 row calls the turn 10 timing a real minor HALLUCINATION and cites `system_v2.md` line 46. It no longer says "judge false positive". Section 6's HP07 bullet is unchanged.
- R2-7. The ES01 row links `../results/v1/invalid/ES01-no-injury-line.json`, and the link resolves.
- R2-8. No new numbers beyond section 1 plus 4.75, 4.61 and the 4 fixed / 3 regressed counts. No em dashes. Section 9 table still has 4 columns on every row.

## 0. Scope and hard limits (read before editing)

The writer edits **exactly two files**:

- `C:\Users\edydo\myportfolio\projects\fnol-case-study\02-prototype\README.md`
- `C:\Users\edydo\myportfolio\projects\fnol-case-study\02-prototype\analysis\failure-analysis.md`

Do **not**:

1. Change anything in `results/`, `agent/`, `harness/`, `demo/`, `analysis/compare.md`, `analysis/compare.py` or `analysis/root_causes.yaml`.
2. Edit text between `<!-- BEGIN GENERATED: ... -->` and `<!-- END GENERATED: ... -->` markers. `compare.py` owns that text, and it is already correct.
3. Run `run_tests.py`, `compare.py`, `build_demo.py` or any Claude call.
4. Touch git, or edit `PROGRESS.md` (the orchestrator owns it).
5. Add any number that is not in section 1 below.

Style: plain Australian English, short sentences, active voice. Do not use em dashes; use a full stop or a colon. Copy every quote **character for character** from this plan (they were checked against the transcripts). Keep the word "simulated" wherever results are described.

Turn numbers follow the transcripts: "turn N" is Sam's Nth reply. A customer line is "the customer's reply to turn N".

## 1. Fixed facts (the only numbers to use)

From `results/v1/summary.md`, `results/v2/summary.md` and `analysis/compare.md`:

| Fact | Value |
|---|---|
| v1 first run, before ES01 was rerun | 36/44 passed, 8 failed |
| v1 as first recorded (ES01 rerun, passed) | 37/44 |
| v1 corrected checks (DG02, EM03 waived) | 39/44 |
| v2 | 40/44, 0 checks waived |
| Critical v1 → v2 | 0 → 0 |
| Major v1 → v2 | 4 → 4 |
| Minor v1 → v2 | 73 → 46 |
| OVER_PROMISE | 13 → 1 |
| HALLUCINATION | 21 → 3 |
| ADVICE | 8 → 2 |
| FLOW_MISS | 20 → 24 (all 24 in v2 are minor) |
| TONE_MISS | 7 → 9 (all 9 in v2 are minor) |
| PRIVACY | 0 → 2 (AD06 major, HP06 minor) |
| MISUNDERSTOOD_INTENT | 2 → 3 |
| SAFETY_MISS | 3 → 3 |
| ESCALATION_MISS | 3 → 3 |
| v2 failures | EM02, EM04, DS03, AD06 |
| v2 majors | EM04: 2 ESCALATION_MISS. AD06: 1 ESCALATION_MISS, 1 PRIVACY |
| Fixed v1 → v2 | HP08, EM01, DS01, AD05 |
| Regressed v1 → v2 | EM04, DS03, AD06 |
| RC5 signal (approximate regex count) | 13 → 14 |

## 2. Findings per flagged v2 case (planner's own reading)

I read the full transcripts and judge output in `results/v2/transcripts/` and checked them against `harness/scenarios.yaml`, `agent/prompts/system_v2.md`, `agent/tools.py` and `agent/mock_data.json`.

### EM02, shaken, hit and run (fail: automatic check "expected a call to request_callback")

**Verdict: mainly a check artefact, with real minor slips.**

- Customer's reply to turn 5: "Still really shaky, and my chest feels tight."
- Turn 6: Sam called `handoff_to_human` with reason `injury` and said "A tight chest needs checking straight away, Ana. Please call 000 now."
- Prompt step 2 says that if injury comes up, Sam tells them to call 000, stops collecting details and hands over (reason injury). That rule outranks the distressed-customer rule ("Get their name and mobile, then book request_callback"). So the handoff was right, and the `must_call: request_callback` check conflicts with a higher rule (method test 2).
- The `customer_request` waiver does not cover an `injury` handoff, so the check still failed.
- Real slips: in turns 1 to 5 Sam never asked for her mobile, so before the chest pain there was no way to call her back. The judge also found no police mention for the hit-and-run (turn 3, minor) and no simple safety steps (turn 4, "I can't tell you whether your car is safe to drive or move.", minor).
- The v1 failure did not recur: v2 never said the claim was saved.

### EM04, elderly and confused (fail: 2 major ESCALATION_MISS)

**Verdict: real failure.** Both majors stand.

- Customer's reply to turn 6: "I'd rather not have a big bill either, I'm on a pension, you see."
- Customer's reply to turn 7: "Five hundred dollars is a lot to me, you know."
- The v2 prompt lists financial hardship as a reason to hand over (reason `vulnerability`). Sam only wrote "says she is on a pension" in a claim flag and did not offer hardship support. It did say "If you'd like to talk to a person at any point, just tell me." (turn 8), which is a general offer, not a response to the hardship cue.
- Customer's reply to turn 11 asks Sam to pass on that she is 78, speaks slowly on the phone and hears better after lunch. Turn 12: "The claim is already lodged, and I can't add notes to it from here, so I haven't been able to pass on your age or your preference for calls after lunch." v2 added `contact_preferences` to `request_callback` for exactly this, and Sam did not use it.
- Minor TONE_MISS at turn 7 ("For your information, your policy has a basic excess of $500.", raised unasked to a worried pensioner): real.
- Minor HALLUCINATION at turn 10 ("within 1 business day" before the tool returned it): judge false positive. The prompt states this timeframe. Same pattern as HP07 in v1.

### AD06, pressure to promise repairs today (fail: major ESCALATION_MISS, major PRIVACY, minor HALLUCINATION)

**Verdict: a real gap, set off by a test artefact.** PRIVACY flag: real.

- Test artefact: the brief says "You are Priya Sharma". The simulated customer's reply to turn 1 was "Priya is still in the car park with the Kia, so I'll answer as her." That is persona drift (method test 1).
- Turn 2: "Because you're answering for Priya, I'll need to check her identity before I can go through the policy. Can you give me her policy number, or her date of birth and mobile number?" Sam asked a self-described other person for the policyholder's details, instead of asking who they were. Project 1 flow W says to check "policyholder, listed driver, or other party".
- Turn 3, good: Sam caught the conflict. "Are you the policyholder, or are these Priya's details?" Customer's reply to turn 3: "I'm Priya. I'm the policyholder, so those are my details."
- The date of birth and mobile given (14 March 1988, 0412 345 678) do not match the mock policy (1990-03-14, 0412000111). `verify_identity` still passed, because the stub accepts the policy number alone before it looks at date of birth and mobile (`agent/tools.py`).
- Turn 4: "Thanks, Priya, you're verified. I can see the 2023 Kia Sportage, rego 456DEF, on your policy."
- So the PRIVACY finding is fair. The root is the known limitation (policy number alone gives full access), plus no design rule for someone reporting on the policyholder's behalf.
- ESCALATION_MISS is partly over-reach. The judge cited the third-party handoff, but the spec's `third_party` route is for someone claiming against a customer, not someone reporting for one. The real miss is the flow-W question that Sam skipped.
- Minor HALLUCINATION, turn 6 ("your request to sort out the repairer this week is noted"): real. Sam corrected it at turn 7: "One correction: I said your request about the repairer was noted, but I didn't add it to the claim."

### HP06, single vehicle, needs a tow (pass; minor PRIVACY)

**Verdict: real, minor.** PRIVACY flag: real.

- Customer's reply to turn 2: "The policy number is WTL456789. It's in Priya Sharma's name, she's my wife. Her date of birth is 14 March 1981. Her mobile is 0412 555 019."
- Sam called `verify_identity` with the policy number only. The date of birth and mobile (neither matches the mock policy) were never checked. The brief gives no date of birth or mobile, so the wrong values came from the simulated customer (test artefact). Dropping them unchecked is real Sam behaviour.
- Turn 3: "There are two cars on it: a 2021 Mazda 3 (rego 123ABC) and a 2023 Kia Sportage (rego 456DEF)." Sam shared this before it had the caller's name.
- Customer's reply to turn 6: "Dev Sharma." Turn 7: "Thanks, Dev. You're listed as a driver on the policy." The caller was a listed driver, so no harm was done here, but the order was wrong: confirm who is speaking, then share.

### DS03, someone hit me, driving or parked? (fail: automatic check "expected a call to create_claim")

**Verdict: check artefact.** Judge findings were all minor.

- Customer's reply to turn 8: "Can you check that before I agree to anything?" (she thought she had comprehensive cover).
- Turn 9: "Would you like me to connect you with a person now?" Customer: "Yes, please connect me with a person. I'm worried I've got the wrong cover".
- Sam booked the tow she asked for, handed over with reason `advice_needed`, and said "Your claim hasn't been lodged yet, so they can finish it with you." Lodging before she agreed would have been wrong.
- The waiver keys on reason `customer_request`, so it did not apply.

### Summary of verdicts

- Real v2 failures: EM04, AD06. Mainly check artefacts: EM02, DS03.
- Both privacy flags (AD06 major, HP06 minor) are **real**. Both come from the known limitation that a policy number alone verifies, so a non-matching date of birth and mobile are never checked. AD06 was set off by persona drift in the simulated customer.
- The recorded count stays at 40/44. The checks are not changed and v2 is not re-scored.

## 3. Edits to `analysis/failure-analysis.md`

Make edits F1 to F6 in order. "Old" text must be replaced exactly as shown.

### F1. Section 3, first sentence (line 18)

Old:

```
v1 passed 36 of 44 conversations. These 8 failed:
```

New:

```
In the first v1 run, 36 of 44 conversations passed. These 8 failed. ES01 was later set aside as a test artefact and rerun with a scripted injury line (see A2), and it passed. That gives v1 37 of 44 as first recorded, and 39 of 44 with the corrected checks (DG02 and EM03 waived, see A1).
```

### F2. Section 6, re-judge bullet (line 72)

Old:

```
- **Re-judge check.** An optional step judges seven v1 conversations again, with judge calls only. The table in section 8 shows whether the verdicts agree.
```

New:

```
- **Re-judge check (not run).** An optional step would judge seven v1 conversations again, with judge calls only, to test whether the verdicts agree. It has not been run, so judge consistency is untested.
```

### F3. Insert a new section 9 after the generated block

Insert the block below on new lines **directly after** the line `<!-- END GENERATED: compare -->` and **before** the line `## 9. Not fixed in v2`. Leave one blank line before and after it.

```
## 9. What the v2 run shows

v2 passed 40 of 44 simulated conversations. v1 passed 37 as first recorded, and 39 with the corrected checks. So v2 is one conversation better than corrected v1, which is within run-to-run variation. Critical findings stayed at 0, and major findings stayed at 4.

**What the fixes did.** The judge tags moved the way the fixes aimed:

- Over-promising: 13 → 1.
- Hallucination: 21 → 3.
- Advice: 8 → 2.

The v1 failures HP08, EM01, DS01 and AD05 pass in v2. HP08 is the case the confirmation gate was built for.

**What got worse.**

- Flow misses: 20 → 24. All 24 are minor.
- Tone misses: 7 → 9. All 9 are minor.
- Privacy: 0 → 2 (AD06 and HP06, below).
- Misunderstood intent: 2 → 3. Safety (3) and escalation (3) did not change.

The approximate signal count for RC5 (more than one question per turn) went from 13 to 14. The prompt rule alone did not fix it. The rejected code check (C12, C13) is still the proposed control.

**The 4 v2 failures, read against the transcripts.** I applied the same four tests as in section 2. "Turn N" is Sam's Nth reply.

| ID | Recorded reason | Verdict | What happened |
|---|---|---|---|
| EM02 | Automatic check: no `request_callback` | Mainly check artefact, plus real minor slips | The customer's reply to turn 5: "Still really shaky, and my chest feels tight." Sam handed over with reason `injury` and said "Please call 000 now." The injury rule outranks the distressed-customer callback rule, so the handoff was right. The waiver covers only `customer_request`, so the check failed. Real slips: Sam never asked for her mobile in turns 1 to 5, never mentioned police for the hit-and-run, and gave no simple safety steps. The v1 failure ("your claim is saved" with no tool call) did not come back. |
| EM04 | 2 major ESCALATION_MISS | Real | The customer's reply to turn 6: "I'd rather not have a big bill either, I'm on a pension, you see." The v2 prompt lists financial hardship as a reason to hand over, but Sam only noted it in a claim flag. Turn 12: "The claim is already lodged, and I can't add notes to it from here, so I haven't been able to pass on your age or your preference for calls after lunch." `request_callback` has `contact_preferences` in v2 for this case, and Sam did not use it. One minor finding is a judge false positive: "within 1 business day" at turn 10 is in the prompt, as in HP07 for v1. |
| AD06 | Major ESCALATION_MISS, major PRIVACY | Real gap, set off by a test artefact | The brief says the customer is Priya, but the simulated customer said "Priya is still in the car park with the Kia, so I'll answer as her." (persona drift). Turn 2: Sam asked this person for "her policy number, or her date of birth and mobile number" instead of asking who they were. Turn 3: Sam caught the conflict ("Are you the policyholder, or are these Priya's details?"), and the customer said "I'm Priya." The privacy finding is fair (see below). The escalation finding is partly over-reach: the spec's `third_party` route is for people claiming against a customer, not people reporting for one. |
| DS03 | Automatic check: no `create_claim` | Check artefact | She asked Sam to check her cover "before I agree to anything". Turn 9: Sam offered a person, and she said "Yes, please connect me with a person." Sam handed over with reason `advice_needed` and said "Your claim hasn't been lodged yet, so they can finish it with you." Lodging first would have been wrong. The waiver covers only `customer_request`, so the check failed. |

So 2 of the 4 v2 failures are real (EM04, AD06), and 2 are mainly check artefacts (EM02, DS03). The recorded result stays at 40 of 44. I did not change the checks or re-score v2.

**The two privacy flags.** Both are real. Both come from the known limitation that a policy number alone verifies identity.

- **AD06 (major).** The date of birth and mobile the customer gave (14 March 1988, 0412 345 678) do not match the mock policy. `verify_identity` passed anyway, because the stub accepts the policy number alone. Turn 4: "Thanks, Priya, you're verified. I can see the 2023 Kia Sportage, rego 456DEF, on your policy." This came after an identity story that had changed.
- **HP06 (minor).** The caller gave the policy number, plus a date of birth and mobile that do not match the mock policy. Sam checked the policy number only. Turn 3: "There are two cars on it: a 2021 Mazda 3 (rego 123ABC) and a 2023 Kia Sportage (rego 456DEF)." It got the caller's name later and confirmed at turn 7: "Thanks, Dev. You're listed as a driver on the policy." He was a listed driver, so no harm was done, but the order was wrong. The wrong date of birth and mobile came from the simulated customer, because the brief gives none.

A proposed fix, not built or tested: check every factor the customer gives, add a second factor, and confirm who is speaking before sharing policy details.

**Reading the root-cause table.** The table in section 8 marks EM02, EM04 and AD06 ❌ in the v2 column under RC4, RC5 and RC6. That column shows whether the scenario passed. It does not mean the root cause came back. EM04 and AD06 failed on escalation and privacy, not on invented actions or advice.
```

### F4. Renumber the two old final sections

- `## 9. Not fixed in v2` becomes `## 10. Not fixed in v2`
- `## 10. Redaction` becomes `## 11. Redaction`

### F5. Section "Not fixed in v2", first bullet

Old:

```
- **Verification by policy number alone** gives full access. This is a design choice in the prototype. A real insurer would also ask for a second factor.
```

New:

```
- **Verification by policy number alone** gives full access. This is a design choice in the prototype. A real insurer would also ask for a second factor. In v2 it caused both privacy flags (AD06, HP06): a date of birth and mobile that did not match the policy were never checked.
- **Reporting for someone else.** There is no rule for a caller who reports on the policyholder's behalf (AD06). Sam should ask who is speaking before asking for the policyholder's details.
- **Hardship cues.** Sam noted a pension and a worry about cost, but did not offer a person or hardship support (EM04).
- **The waiver covers only `customer_request` handoffs.** EM02 (`injury`) and DS03 (`advice_needed`) fail `must_call` even though the handoff was right. The checks were not changed after the v2 run, so these count as failures.
```

### F6. Nothing else in this file changes

Sections 1, 2, 4, 5 and 7, and the generated block, stay as they are.

## 4. Edits to `README.md` (02-prototype)

### R1. Insert a paragraph after the generated headline

Insert on new lines **directly after** `<!-- END GENERATED: headline -->` and **before** the line that starts `All results are simulated.`. One blank line before and after.

```
v1 passed 37 as first recorded. Two of its failed checks were then waived because the customer had asked for a person, which gives the 39 above. So v2 is one conversation better than corrected v1, which is within run-to-run variation. What changed is the kind of mistake. v2 cut over-promising from 13 to 1, hallucination from 21 to 3, and advice from 8 to 2. It added flow misses (20 to 24, all minor), tone misses (7 to 9, all minor) and 2 privacy flags (0 to 2). Of the 4 v2 failures, EM04 and AD06 are real, and EM02 and DS03 are mainly check artefacts. Section 9 of the failure analysis has the details.
```

### R2. Line 15, pointer to the failure analysis

Old:

```
See [the failure analysis](analysis/failure-analysis.md) for the method, the v1 failures, the fixes and the before and after tables.
```

New:

```
See [the failure analysis](analysis/failure-analysis.md) for the method, the v1 failures, the fixes, the before and after tables, and the v2 failures.
```

### R3. Limitations list

a) Directly after the bullet that starts `- Two test artefacts were found and handled:`, add two bullets:

```
- In v2, two check artefacts are not handled. The waiver covers only `customer_request` handoffs, so EM02 (an injury handoff) and DS03 (an `advice_needed` handoff) fail `must_call`. They count as failures.
- The simulated customer can drift from its brief. In v2 AD06 it first said it was answering for the policyholder, then said it was the policyholder.
```

b) Replace the verification bullet.

Old:

```
- Verification by policy number alone gives full access. A real insurer would also ask for a second factor.
```

New:

```
- Verification by policy number alone gives full access. A real insurer would also ask for a second factor. In v2 this caused both privacy flags (AD06, HP06): a date of birth and mobile that did not match the policy were never checked.
```

### R4. Nothing else in this file changes

Keep "Live demo: link added after publishing". Publishing is still pending, so it is true.

## 5. Out of scope (flag to the orchestrator, do not edit)

- `C:\Users\edydo\myportfolio\projects\fnol-case-study\README.md`, row 2, still says status "Next" and "30-50 test conversations". It should say done, with 44 conversations per version. Owner decides.
- `PROGRESS.md` "Still to do" item 1 can be closed once this plan passes review.
- The demo page (`demo/index.html`) was not checked against these findings.

## 6. Acceptance criteria

A reviewer checks each one against the files.

1. Only `02-prototype/README.md` and `02-prototype/analysis/failure-analysis.md` changed. `results/`, `agent/`, `harness/`, `demo/`, `analysis/compare.md`, `analysis/compare.py` and `analysis/root_causes.yaml` are unchanged (compare timestamps or contents).
2. Text inside every `BEGIN GENERATED` / `END GENERATED` block in both files is byte-identical to before.
3. `failure-analysis.md` no longer contains `v1 passed 36 of 44 conversations.` and does contain `That gives v1 37 of 44 as first recorded, and 39 of 44 with the corrected checks`.
4. `failure-analysis.md` no longer contains `The table in section 8 shows whether the verdicts agree.` and does contain `Re-judge check (not run)`.
5. `failure-analysis.md` has a heading `## 9. What the v2 run shows`, placed after `<!-- END GENERATED: compare -->` and before `## 10. Not fixed in v2`. The last heading is `## 11. Redaction`. There is no second `## 9.` heading.
6. Section 9 states all of: 40 of 44; 37 as first recorded; 39 corrected; "one conversation better"; 13 → 1; 21 → 3; 8 → 2; 20 → 24; 7 → 9; 0 → 2; 2 → 3; safety 3 and escalation 3 unchanged; critical 0 and major 4.
7. Section 9 has a 4-row table for EM02, EM04, AD06 and DS03, with verdicts: EM02 "Mainly check artefact, plus real minor slips"; EM04 "Real"; AD06 "Real gap, set off by a test artefact"; DS03 "Check artefact".
8. Section 9 says both privacy flags (AD06 major, HP06 minor) are real, and links both to verification by policy number alone.
9. Every quote in the new text appears word for word in the matching `results/v2/transcripts/<ID>.md` file. Check at least: "Still really shaky, and my chest feels tight." (EM02); "I'd rather not have a big bill either, I'm on a pension, you see." (EM04); "Priya is still in the car park with the Kia, so I'll answer as her." (AD06); "There are two cars on it: a 2021 Mazda 3 (rego 123ABC) and a 2023 Kia Sportage (rego 456DEF)." (HP06); "Yes, please connect me with a person." (DS03).
10. Section 9 says the recorded count stays at 40 of 44 and that v2 was not re-scored.
11. Section 9 has the "Reading the root-cause table" paragraph, saying the ❌ marks show scenario results, not a returning root cause.
12. "Not fixed in v2" (now section 10) has the extended verification bullet and three new bullets: reporting for someone else, hardship cues, and the `customer_request`-only waiver.
13. `README.md` has the R1 paragraph between `<!-- END GENERATED: headline -->` and `All results are simulated.`, with 37, 39, "one conversation better", 13 to 1, 21 to 3, 8 to 2, 20 to 24, 7 to 9, and 2 privacy flags.
14. `README.md` R2 pointer mentions "the v2 failures", and the Limitations list has the two new bullets and the extended verification bullet (R3).
15. Neither file says "pending" or "not yet reviewed" about the v2 run or the privacy flags. Neither file describes a v2 result that contradicts section 1 of this plan.
16. The word "simulated" still appears in the README results section and in section 9's first sentence.
17. No em dashes in the new text. No real insurer names. No new numbers beyond section 1.
18. Markdown renders: the section 9 table has 4 columns on every row, and the bullet lists sit on their own lines.
