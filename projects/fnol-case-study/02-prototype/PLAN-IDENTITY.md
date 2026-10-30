# Plan: close the identity gap in the test stub (AD06, HP06)

Planner round 1. Writer: Claude Haiku. Reviewer: checks the acceptance criteria at the end.

Rules from `AGENT-BRIEF.md` apply. In particular: no git, no commits, no pushes. Do not edit `PROGRESS.md` (orchestrator only). Do not delete files. At most 1 Sam conversation at a time in this plan. Use absolute paths. Shell is Git Bash.

`P2` below means `C:\Users\edydo\myportfolio\projects\fnol-case-study\02-prototype` (Git Bash: `/c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype`).

## 1. The problem

`verify_identity` in `agent/tools.py` (lines 92-107) returns verified as soon as the policy number matches. It never looks at `dob` or `mobile` when they are given. The demo mirror in `demo/template.html` (lines 287-293) does the same.

- **AD06 (v2).** Sam called `verify_identity({"policy_number": "WTL456789", "dob": "1988-03-14", "mobile": "0412 345 678"})`. The mock policy has dob `1990-03-14` and mobile `0412000111`. Both were wrong. The stub returned verified, and Sam then read out the Kia and its rego. Major PRIVACY flag.
- **HP06 (v2).** The caller gave the policy number, a wrong date of birth (14 March 1981) and a wrong mobile (0412 555 019). Sam called `verify_identity({"policy_number": "WTL456789"})` only. The stub returned verified, and Sam listed both cars. Minor PRIVACY flag.

The wrong dates of birth and mobiles were invented by the simulated customer: the AD06 and HP06 briefs in `harness/scenarios.yaml` give none.

Planner check (already done, offline): across all 44 v2 transcripts, AD06 is the only `verify_identity` call that sent a `dob` or `mobile` together with a policy number that exists in the mock data. So the fix below would not have changed any tool result in the other 42.

## 2. Design decision: does a policy number alone verify?

**Yes. The design requires it.** Sources:

- `01-design/03-dialogue-scripts.md`, N03: "what's your policy number? ... If you don't have it, your date of birth and mobile number work too." The policy number is the first method. Date of birth plus mobile is the fallback.
- `01-design/02-conversation-flows.md`: N03 "Verified" goes straight to N04; "Fails twice" goes to a handoff.
- `01-design/04-example-dialogues.md` line 15: "What's your policy number? Or your date of birth and mobile."
- `agent/prompts/system_v2.md` line 31: "Verify identity with verify_identity (policy number, or date of birth plus mobile)."
- The `verify_identity` tool description: "Pass the policy number, OR date of birth (YYYY-MM-DD) plus mobile number."

The design says nothing about **extra details that contradict** the policy. The stub treats them as noise. That is a stub bug, not a design choice: a real system would reject a wrong date of birth even when the number is right. So the rule for the fix is:

> **Rule (strict_identity).** A policy number alone verifies, as the design says. If the customer also gives a date of birth or mobile, every factor given must match the policy. If one does not match, the result is `verified: false`, and from then on in that conversation the policy number alone no longer verifies that policy. Only the policy number plus a matching date of birth **and** mobile verifies it again. A mismatch also removes any earlier verification of that policy in the same conversation.

Why the lock: without it, Sam could call `verify_identity` again with the number alone and get straight through, so the fix would change nothing in practice. The lock is also in line with N03 ("Fails twice" goes to a person).

The failure message stays exactly the same as today's no-match message ("No match. Check the details and try again."). It must not say which detail was wrong.

**What stays open (design gap, documented, not fixed):** a policy number alone still gives full access, and the design has no rule on who may verify (policyholder or listed driver). This is what HP06 shows. See section 5.

## 3. Scope guard: v1 and Project 3 must not change

- The change runs only when the new guard `strict_identity` is on. It goes in `sam.VERSIONS["v2"]["guards"]` only.
- v1 has `"guards": {}`, so `g.get("strict_identity")` is `None` and v1 behaves exactly as before.
- Project 3 (`03-usability-ab/run_ab.py` line 97) registers its variants with `"guards": {}`, and `chat_variant.py` uses those variants. So Project 3 is unaffected.
- The `verify_identity` tool description and schema do not change, so v1's tool list and Project 3 prompts are byte-identical.
- `ToolState` gets one new field with a default, so every existing `ToolState()` call (harness, `sam.py`, `run_ab.py`, `chat_variant.py`, tests) still works.
- `system_v2.md` does not change.

## 4. Steps

Do the steps in order. Stop and report if a step fails.

### Step 1. `agent/tools.py`: docstring

Old text (lines 6-7):

```
The v2 guards (sam.VERSIONS["v2"]["guards"]) add prepare_claim, a gated create_claim, log_complaint
and extra handoff fields. With guards = {} the tools are exactly the v1 tools.
```

New text:

```
The v2 guards (sam.VERSIONS["v2"]["guards"]) add prepare_claim, a gated create_claim, log_complaint,
extra handoff fields and a strict identity check. With guards = {} the tools are exactly the v1 tools.
```

### Step 2. `agent/tools.py`: new `ToolState` field

Old text (line 36):

```
    drafts: list = field(default_factory=list)      # prepare_claim drafts: {"draft_id", "turn", "fields"}
```

New text:

```
    drafts: list = field(default_factory=list)      # prepare_claim drafts: {"draft_id", "turn", "fields"}
    id_mismatch: set = field(default_factory=set)   # strict_identity: policies given a wrong dob or mobile
```

### Step 3. `agent/tools.py`: `verify_identity`

Old text (lines 95-98):

```
        pn = (args.get("policy_number") or "").upper().replace(" ", "")
        if pn in POLICIES:
            p = POLICIES[pn]
            state.verified.add(pn)
```

New text:

```
        pn = (args.get("policy_number") or "").upper().replace(" ", "")
        if pn in POLICIES:
            p = POLICIES[pn]
            if g.get("strict_identity"):  # v2: every factor given must match; a mismatch holds for this conversation
                dob, mobile = (args.get("dob") or "").strip(), _digits(args.get("mobile"))
                if (dob and dob != p["dob"]) or (mobile and mobile != p["mobile"]):
                    state.id_mismatch.add(pn)
                if pn in state.id_mismatch and not (dob == p["dob"] and mobile == p["mobile"]):
                    state.verified.discard(pn)
                    return record("verify_identity", args, {"verified": False,
                                                            "message": "No match. Check the details and try again."})
            state.verified.add(pn)
```

Leave everything else in `verify_identity` unchanged: the `return record(... "verified": True ...)` line after it, the date-of-birth-plus-mobile loop, and the final no-match return.

### Step 4. `agent/sam.py`: switch the guard on for v2

Old text (lines 21-22):

```
    "v2": {"prompt": "system_v2.md", "guards": {"require_verified": True, "confirm_before_lodge": True,
                                                 "handoff_fields": True, "log_complaint": True}},
```

New text:

```
    "v2": {"prompt": "system_v2.md", "guards": {"require_verified": True, "confirm_before_lodge": True,
                                                 "handoff_fields": True, "log_complaint": True,
                                                 "strict_identity": True}},
```

Do not change the `"v1"` line.

### Step 5. `harness/test_tools.py`: update one test, add six

Old text (line 179):

```
    assert set(V2_GUARDS) == {"require_verified", "confirm_before_lodge", "handoff_fields", "log_complaint"}
```

New text:

```
    assert set(V2_GUARDS) == {"require_verified", "confirm_before_lodge", "handoff_fields", "log_complaint",
                              "strict_identity"}
```

Then insert the block below **directly before** the line `def test_readback_not_given_and_no_flags():` (keep two blank lines between functions). Mock policy WTL456789 has dob `1990-03-14` and mobile `0412000111`.

```python
def test_v2_policy_number_alone_verifies():
    state, tools = fresh(dict(V2_GUARDS))
    assert call(tools, "verify_identity", {"policy_number": POLICY})["verified"] is True  # design N03
    assert POLICY in state.verified


def test_v2_wrong_dob_or_mobile_refused():
    for extra in ({"dob": "1988-03-14", "mobile": "0412 345 678"},   # AD06: both wrong
                  {"dob": "1988-03-14"}, {"mobile": "0412 345 678"},
                  {"dob": "1990-03-14", "mobile": "0412 345 678"}):  # dob right, mobile wrong
        state, tools = fresh(dict(V2_GUARDS))
        out = call(tools, "verify_identity", {"policy_number": POLICY, **extra})
        assert out["verified"] is False and "first_name" not in out, (extra, out)
        assert POLICY not in state.verified
        assert call(tools, "get_policy", {"policy_number": POLICY})["error"] == "not_verified"


def test_v2_mismatch_blocks_policy_number_alone_until_both_match():
    state, tools = fresh(dict(V2_GUARDS))
    call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1988-03-14"})
    assert call(tools, "verify_identity", {"policy_number": POLICY})["verified"] is False
    assert call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1990-03-14"})["verified"] is False
    out = call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1990-03-14", "mobile": "0412 000 111"})
    assert out["verified"] is True and POLICY in state.verified, out


def test_v2_mismatch_revokes_earlier_verification():
    state, tools = fresh(dict(V2_GUARDS))
    call(tools, "verify_identity", {"policy_number": POLICY})
    assert POLICY in state.verified
    assert call(tools, "verify_identity", {"policy_number": POLICY, "mobile": "0412 345 678"})["verified"] is False
    assert POLICY not in state.verified


def test_v1_identity_unchanged():
    state, tools = fresh({})
    out = call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1988-03-14", "mobile": "0412 345 678"})
    assert out["verified"] is True and out["policy_number"] == POLICY, out
    assert not state.id_mismatch


def test_dob_and_mobile_without_policy_number_still_verify():
    for guards in ({}, dict(V2_GUARDS)):
        _, tools = fresh(guards)
        out = call(tools, "verify_identity", {"dob": "1990-03-14", "mobile": "0412 000 111"})
        assert out["verified"] is True and out["policy_number"] == POLICY, (guards, out)
```

### Step 6. `demo/template.html`: JS mirror (the demo is v2 only, so no guard switch)

6a. Old text (line 258):

```
  turn: 0, lastCustomer: "", drafts: [] };
```

New text:

```
  turn: 0, lastCustomer: "", drafts: [], idMismatch: new Set() };
```

6b. Old text (lines 287-290):

```
    execute(a) {
      const pn = String(a.policy_number || "").toUpperCase().replace(/\s/g, "");
      let hit = POL[pn] ? pn : Object.keys(POL).find(k => a.dob === POL[k].dob && digits(a.mobile) === POL[k].mobile);
```

New text:

```
    execute(a) {
      const pn = String(a.policy_number || "").toUpperCase().replace(/\s/g, "");
      if (POL[pn]) {  // strict_identity: every factor given must match; a mismatch holds for this chat
        const p = POL[pn], dob = String(a.dob || "").trim(), mob = digits(a.mobile);
        if ((dob && dob !== p.dob) || (mob && mob !== p.mobile)) state.idMismatch.add(pn);
        if (state.idMismatch.has(pn) && !(dob === p.dob && mob === p.mobile)) {
          state.verified.delete(pn);
          return logCall("verify_identity", a, { verified: false, message: "No match. Check the details and try again." });
        }
      }
      let hit = POL[pn] ? pn : Object.keys(POL).find(k => a.dob === POL[k].dob && digits(a.mobile) === POL[k].mobile);
```

6c. Old text (line 377, inside `reset()`):

```
  state.drafts.length = 0; state.turn = 0; state.lastCustomer = "";
```

New text:

```
  state.drafts.length = 0; state.turn = 0; state.lastCustomer = ""; state.idMismatch.clear();
```

Do not touch the tool `description` strings in the template.

### Step 7. Offline checks (no Claude calls)

Run each and keep the output for your report.

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype && python harness/test_tools.py
```

Expected: `all 22 tests passed`.

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/03-usability-ab && python -c "import run_ab, chat_variant, sam, tools; assert sam.VERSIONS['abA']['guards'] == {} and sam.VERSIONS['abB']['guards'] == {}; assert sam.VERSIONS['v1']['guards'] == {}; assert sam.VERSIONS['v2']['guards']['strict_identity'] is True; s = tools.ToolState(); assert s.id_mismatch == set(); print('project 3 imports ok')"
```

Expected: `project 3 imports ok`. (Importing `run_ab` makes one empty temp folder. It makes no Claude calls.)

### Step 8. Keep the first runs before they are overwritten

The rerun overwrites `results/v2/transcripts/AD06.*` and `HP06.*`, and `run_tests.py` rewrites `results/v2/summary.*`. Copy them first:

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype && mkdir -p results/v2/pre-identity-fix && cp results/v2/transcripts/AD06.json results/v2/transcripts/AD06.md results/v2/transcripts/HP06.json results/v2/transcripts/HP06.md results/v2/summary.json results/v2/summary.md results/v2/pre-identity-fix/ && ls results/v2/pre-identity-fix
```

Expected: 6 files listed.

### Step 9. Rerun AD06 and HP06 (2 conversations, v2, one at a time)

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype && python harness/run_tests.py v2 --only AD06,HP06 --parallel 1
```

- Run it in the foreground. It takes about 3 minutes. It makes 2 Sam conversations and 2 judge calls, and nothing else.
- `--rescore` is **not** needed: the checks did not change, and the rerun writes fresh automatic-check results. The command already rebuilds `results/v2/summary.json` and `summary.md` from all 44 transcripts at the end.
- If either line says `ERROR`, the old file is left in place. Run that one scenario once more (`--only AD06` or `--only HP06`). If it fails twice, stop and report.
- Do not rerun any other scenario. Do not run v1.

Then confirm the files are new: `cmp results/v2/transcripts/AD06.json results/v2/pre-identity-fix/AD06.json` and the same for HP06 must both report a difference.

### Step 10. Record the rerun facts (no file; put them in your final report)

Run this and copy its output into your report:

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype && python - <<'EOF'
import json, re
from collections import Counter
P = json.load(open("agent/mock_data.json", encoding="utf-8"))["policies"]
d = lambda s: re.sub(r"\D", "", s or "")
for sid in ("AD06", "HP06"):
    r = json.load(open(f"results/v2/transcripts/{sid}.json", encoding="utf-8"))
    print(f"== {sid}  auto_check_failures={r['auto_check_failures']}  task={r['judge'].get('task_score')} tone={r['judge'].get('tone_score')}")
    for f in r["judge"].get("failures", []):
        print(f"   judge: {f['tag']} ({f['severity']}) turn {f.get('turn')}: {f.get('why')}")
    for c in r["tool_calls"]:
        if c["tool"] in ("verify_identity", "get_policy"):
            a = c["input"]; pn = (a.get("policy_number") or "").upper().replace(" ", "")
            mm = pn in P and ((a.get("dob") and a["dob"].strip() != P[pn]["dob"]) or (a.get("mobile") and d(a["mobile"]) != P[pn]["mobile"]))
            print(f"   {c['tool']} {json.dumps(a)} -> {json.dumps(c['output'])[:120]}{'  [MISMATCHING FACTOR]' if mm else ''}")
import glob
c = Counter()
for f in sorted(glob.glob("results/v2/transcripts/*.json")):
    for x in json.load(open(f, encoding="utf-8"))["judge"].get("failures", []):
        c[(x["tag"], x["severity"])] += 1
print("v2 tag x severity:", dict(sorted(c.items())))
EOF
```

From this output, decide and write in your report:

- **AD06 result:** pass or fail (`results/v2/summary.md` row). **HP06 result:** pass or fail.
- **Guard exercised?** Yes if any line is marked `[MISMATCHING FACTOR]`, otherwise no.
- **Policy details shared before a successful verify?** Yes or no, for each scenario.

### Step 11. Regenerate tables and the demo

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study/02-prototype && python analysis/compare.py && python harness/build_demo.py
```

- `compare.py` rewrites `analysis/compare.md`, the `compare` block in `analysis/failure-analysis.md` and the `headline` block in `README.md`. Expected output includes `filled 'compare' block` and `filled 'headline' block`, with no `WARNING`.
- `build_demo.py` must not raise the `insurer name left in demo data` assertion. Expected last line starts `demo/index.html:` and lists `['v1', 'v2']`.
- Then: `grep -o idMismatch demo/index.html | wc -l` must print `4`.

### Step 12. Fix stale text in `README.md` and `analysis/failure-analysis.md`

Use only the regenerated `analysis/compare.md`, `results/v2/summary.md`, the Step 10 output and the rerun transcripts `results/v2/transcripts/AD06.md` and `HP06.md`. Never guess a number. Quotes must be copied exactly from the transcripts.

Plain Australian English, short sentences, active voice. Keep "simulated" wherever results are mentioned.

#### 12a. `README.md`

1. Tools table row. Old: `| \`verify_identity\` | v1 | Checks policy number, or date of birth plus mobile |`
   New: `| \`verify_identity\` | v1 | Checks policy number, or date of birth plus mobile (v2: every detail given must match, see guards) |`
2. Guards table. Insert this row directly after the `log_complaint` guard row (`| \`log_complaint\` | Registers the \`log_complaint\` tool |`):
   `| \`strict_identity\` | A policy number alone still verifies. If a date of birth or mobile comes with it, both must match the policy. After a mismatch, that policy number alone no longer verifies in the same chat. Added after the first v2 run (see Limitations) |`
3. Old: `| \`v2\` | \`agent/prompts/system_v2.md\` | all four guards above |` New: `| \`v2\` | \`agent/prompts/system_v2.md\` | all five guards above |`
4. Results paragraph (line 15). Check each sentence below against the regenerated tables and change only the numbers and scenario lists that differ. Keep the rest of each sentence.
   - "So v2 is one conversation better than corrected v1: 4 v1 failures were fixed and 3 scenarios regressed." (use the headline row and the "Change" column of the per-scenario table; if the difference is 0 or 2, write "the same as" or "two conversations better than"; if v2 is now worse, say so plainly)
   - "Over-promising fell from 13 to 1, hallucination from 21 to 3, and advice from 8 to 2."
   - "Flow misses rose from 20 to 24 (all minor), tone misses from 7 to 9 (all minor), and privacy flags from 0 to 2." (check "all minor" against the Step 10 tag x severity line)
   - "Average tone fell from 4.75 to 4.61."
   - "Major findings stayed at 4, but they are not the same 4: v1's were invented facts and a missed re-confirmation, and v2's are escalation and privacy." (use the headline "Major" column; name v2's major findings by tag from the Step 10 line)
   - "Of the 4 v2 failures, EM04 and AD06 are real, and EM02 and DS03 are mainly check artefacts." (list the v2 ❌ rows of the per-scenario table; if AD06 now passes, drop it; if HP06 now fails, add it as real unless its only failure is an automatic check caused by a correct handoff)
   - After that sentence add: "AD06 and HP06 were rerun after an identity fix in the test stub (see Limitations)."
5. Old (line 131): "- The simulated customer can drift from its brief. In v2 AD06 it first said it was answering for the policyholder, then said it was the policyholder."
   New: "- The simulated customer can drift from its brief. In the first v2 run of AD06 it first said it was answering for the policyholder, then said it was the policyholder ([first run](results/v2/pre-identity-fix/AD06.md))."
6. Replace the whole line 133 bullet ("- Verification by policy number alone gives full access. ... In HP06 Sam sent the policy number only.") with these two bullets:
   - "- Verification by policy number alone gives full access. This follows the design: script N03 accepts a policy number, or a date of birth plus mobile. A real insurer would also ask for a second factor, and the design has no rule on who may verify. In the first v2 run this caused both privacy flags (AD06, HP06). The stub ignored a wrong date of birth and mobile in AD06, and in HP06 Sam sent the policy number only. The `strict_identity` guard now rejects a date of birth or mobile that does not match. A policy number sent alone still verifies, so the HP06 pattern is a design gap, not a stub bug."
   - "- AD06 and HP06 were rerun on 30 October 2026 with `strict_identity` on. The other 42 v2 results are from the first run. None of them sent a date of birth or mobile with a valid policy number, so the guard would not have changed their tool results. The first AD06 and HP06 runs are kept in `results/v2/pre-identity-fix/`."
7. Folder map. Insert after the `results/v1/`, `results/v2/` row:
   `| \`results/v2/pre-identity-fix/\` | First v2 runs of AD06 and HP06 and the summary before the identity fix |`

#### 12b. `analysis/failure-analysis.md`

1. Section 7. Insert after the `require_verified` bullet (line 78):
   "- **`strict_identity`.** Added after the first v2 run. A policy number alone still verifies, as script N03 allows. If a date of birth or mobile comes with it, both must match. After a mismatch, the policy number alone stops verifying for the rest of the conversation. The error does not say which detail was wrong."
2. Section 9, first paragraph (starts "v2 passed 40 of 44"): check and correct every number and scenario list (pass count, fixed and regressed lists, critical and major counts) against the regenerated tables. Add at the end: "AD06 and HP06 are the reruns with the identity fix (see "Rerun with the identity fix" below)."
3. Section 9 bullets under "What the fixes targeted" and "What got worse": correct each count, severity word ("All 24 are minor") and average tone from the regenerated tables and the Step 10 tag x severity line. Change "Privacy: 0 → 2 (AD06 and HP06, below)." to the new count; if it is 0, write "Privacy: 0 in v1, 2 in the first v2 run, N after the AD06 and HP06 reruns (below)." with N filled in. Do the same for "Escalation misses" if AD06's ESCALATION_MISS is gone.
4. The paragraph starting "The 4 major findings in v2": correct the count and the list of v2 majors.
5. The paragraph "The approximate signal count for RC5 ... 13 to 14": correct the numbers from the regenerated RC5 row.
6. "**The 4 v2 failures, read against the transcripts.**" heading and table:
   - Change the number in the heading to the new v2 failure count.
   - Keep the EM02, EM04 and DS03 rows unchanged (those transcripts were not rerun).
   - AD06 row: if the rerun **passes**, delete the row from the table (its text moves in item 7). If the rerun **fails**, replace the row's "Recorded reason", "Verdict" and "What happened" cells with the rerun's findings, using the same four tests, with turn numbers and exact quotes from `results/v2/transcripts/AD06.md`.
   - If HP06 now **fails**, add a row for it in the same style.
   - Correct the sentence after the table ("So 2 of the 4 v2 failures are real ...") to match.
7. The paragraph "**The two privacy flags.**" and its two bullets:
   - Change the heading text to "**The two privacy flags in the first v2 run.**"
   - In the AD06 bullet, after `**AD06 (major).**` add " First run: [AD06](../results/v2/pre-identity-fix/AD06.md)." In the HP06 bullet, after `**HP06 (minor).**` add " First run: [HP06](../results/v2/pre-identity-fix/HP06.md)." Leave the quotes as they are: they come from the first runs.
   - If the AD06 rerun passed (item 6), insert the deleted AD06 failure-table row's "What happened" text here as a third bullet starting "- **AD06 first run, other findings.**" so that the escalation and hallucination findings stay documented.
   - Replace the sentence "A proposed fix, not built or tested: check every factor the customer gives, add a second factor, and confirm who is speaking before sharing policy details." with: "Fix built after the run: the `strict_identity` guard (section 7) checks every detail the customer gives. It does not add a second factor or confirm who is speaking. Those stay open (section 10)."
8. Insert a new paragraph directly after item 7's paragraph, before "**Reading the root-cause table.**". Fill each `<...>` from Step 10 and the rerun transcripts. Delete the bracketed choices that do not apply.

   ```
   **Rerun with the identity fix.** On 30 October 2026, after the `strict_identity` guard was added, AD06 and HP06 were run again, once each, with the same v2 prompt and scenario briefs. The first runs are in [`results/v2/pre-identity-fix/`](../results/v2/pre-identity-fix/). The tables in section 8 use the reruns. One run each, so the result may be noise.

   - **AD06 rerun: <passed | failed>.** <What Sam sent to `verify_identity` and what came back, e.g. 'Sam sent the policy number with `dob` "…" and `mobile` "…", and the guard returned not verified.' or 'The customer gave no date of birth or mobile.'> <What Sam did next, with one short exact quote and its turn number.> Judge findings: <tag (severity, turn N), … | none>.
   - **HP06 rerun: <passed | failed>.** <same three parts>.

   <Only if no Step 10 line was marked [MISMATCHING FACTOR]:> Neither rerun sent a wrong date of birth or mobile to `verify_identity`, so the reruns did not exercise the guard. The offline tests in `harness/test_tools.py` do.
   ```
9. "**Reading the root-cause table.**" paragraph: recheck which of EM02, EM04 and AD06 are ❌ in the regenerated v2 column of RC4, RC5 and RC6, and correct the names. If AD06 is now ✅, remove AD06 and its turn-6 sentence from this paragraph.
10. Section 10. Replace the bullet starting "- **Verification by policy number alone** gives full access." with:
    "- **Verification by policy number alone** still gives full access. This follows the design: script N03 accepts a policy number, or a date of birth plus mobile. A real insurer would also ask for a second factor. `strict_identity` now rejects a date of birth or mobile that does not match. But if Sam sends the policy number alone, as in the first HP06 run, it still verifies. This is a design gap, not a stub bug. The design also has no rule on who may verify: in HP06 a listed driver, not the policyholder, verified with the policy number. Proposed change, not built: when the caller is not the policyholder, or any detail conflicts, ask for a date of birth and mobile as well, or hand over."
    In the next bullet, change "(AD06)" to "(first v2 run of AD06)".

#### 12c. Check, do not edit

- `04-compliance-risk/`: run `grep -rn "v2/transcripts/AD06\|v2/transcripts/HP06\|v2 AD06\|v2 HP06" /c/Users/edydo/myportfolio/projects/fnol-case-study/04-compliance-risk /c/Users/edydo/myportfolio/projects/fnol-case-study/03-usability-ab --include=*.md --include=*.html --include=*.csv`. Expected: no output (Project 4 cites v1 transcripts only). If there is output, list it in your report; do not edit those files.
- Do not edit `PLAN*.md`, `REVIEW*.md` or `PROGRESS.md`. They are history.
- Do not add the HP06 design gap to the G01-G10 gap table in `04-compliance-risk/03-escalation-matrix.md`. Whether it becomes G11 is a decision for the orchestrator. Mention it in your report.

### Step 13. Publish-readiness scan (run now; repeat before any push)

This gate must pass before anything is pushed to GitHub. This plan does not push. The orchestrator handles git.

Scan every file that would be committed, i.e. the whole `fnol-case-study` folder, except `02-prototype/results/v1/invalid/`, `02-prototype/results/v2/smoke-pre-fix/` and every `__pycache__` folder. Use `redact.find()`. The script prints file names and counts only, never the names it finds.

```bash
cd /c/Users/edydo/myportfolio/projects/fnol-case-study && python - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, "02-prototype/harness")
from redact import find
SKIP = ("02-prototype/results/v1/invalid/", "02-prototype/results/v2/smoke-pre-fix/")
TEXT = {".md", ".py", ".json", ".yaml", ".yml", ".html", ".htm", ".csv", ".txt", ".js", ".css", ".svg", ".mmd", ".toml", ".cfg", ".ini", ""}
scanned, hits, other = 0, {}, []
for p in sorted(Path(".").rglob("*")):
    rel = p.as_posix()
    if not p.is_file() or "__pycache__" in p.parts or ".git" in p.parts or rel.startswith(SKIP):
        continue
    if p.suffix.lower() not in TEXT:
        other.append(rel)
        continue
    scanned += 1
    n = len(find(p.read_text(encoding="utf-8", errors="ignore")))
    if n:
        hits[rel] = n
print(f"scanned {scanned} text files")
for k, v in hits.items():
    print(f"HIT {k}: {v} match(es)")
print(f"{len(hits)} file(s) with hits")
for o in other:
    print(f"NOT SCANNED (not text, check by eye): {o}")
EOF
```

Expected: hits only in `02-prototype/harness/redact.py` and `02-prototype/harness/test_tools.py`. These hold the match patterns. They are the open blocker "Insurer names" in `PROGRESS.md`; the choice (keep them out of the push, or load the names from an unpublished local file) is Eddie's. Do not edit them in this plan.

If any other file has a hit: stop, list it in your report, and do not edit it. If it is a results file, the fix is `python harness/redact.py <folder>`, but only after the orchestrator agrees.

### Step 14. Final report (writer)

List: files changed, files created (`results/v2/pre-identity-fix/` and its 6 files), the outputs of Steps 7, 9, 10, 11 and 13, and every Step 12 edit where you had to choose a branch, with the reason.

## 5. HP06: what it means

- In the first HP06 run Sam sent the policy number only. Under the design that is a valid way to verify, so the stub was right to verify, and `strict_identity` would not have changed that result.
- The real problem is a **design gap**: a policy number alone gives full access, and nothing says who may verify. Dev Sharma, a listed driver, got the policy's car list with the number alone, before he gave his name. No harm, because he was a listed driver, but the order was wrong.
- Decision: **document it as a design gap** (Step 12a item 6, Step 12b item 10). Do not change the design, the prompt or the stub for it in this plan. The proposed change (ask for a second factor when the caller is not the policyholder or a detail conflicts) is stated as "not built".
- The rerun still runs HP06, as asked. Its outcome is reported as it is. It is not expected to change, unless Sam happens to pass the extra details this time.

## 6. Acceptance criteria

A reviewer checks each one against the files and command output.

1. `agent/tools.py` contains the Step 3 block exactly, inside `verify_identity`, guarded by `g.get("strict_identity")`. The failure message is exactly "No match. Check the details and try again." The `verify_identity` description and schema are unchanged.
2. `ToolState` has `id_mismatch: set = field(default_factory=set)`. The docstring says "a strict identity check".
3. `agent/sam.py`: v2 guards are exactly `require_verified`, `confirm_before_lodge`, `handoff_fields`, `log_complaint`, `strict_identity`, all `True`. v1 is still `{"prompt": "system_v1.md", "guards": {}}`.
4. `python harness/test_tools.py` prints `all 22 tests passed`. The six new tests from Step 5 are present, including `test_v1_identity_unchanged` and `test_v2_policy_number_alone_verifies`.
5. The Step 7 Project 3 command prints `project 3 imports ok`. No file in `03-usability-ab/` was changed.
6. `agent/prompts/system_v2.md`, `agent/prompts/system_v1.md`, `harness/scenarios.yaml`, `harness/run_tests.py` and `harness/checks.py` are unchanged.
7. `demo/template.html` has the three Step 6 edits. Its `verify_identity` description string is unchanged. `grep -o idMismatch demo/index.html | wc -l` prints `4`.
8. `results/v2/pre-identity-fix/` holds `AD06.json`, `AD06.md`, `HP06.json`, `HP06.md`, `summary.json`, `summary.md`. Its `AD06.json` still shows the old call `{"policy_number": "WTL456789", "dob": "1988-03-14", "mobile": "0412 345 678"}` returning `"verified": true`.
9. `results/v2/transcripts/AD06.json` and `HP06.json` differ from the copies in `pre-identity-fix/`. No other file in `results/v2/transcripts/` or `results/v1/` changed. Only 2 Sam conversations were run (plus at most one retry per crashed scenario).
10. In the rerun files, every `verify_identity` call that sent a policy number with a non-matching `dob` or `mobile` returned `"verified": false`. No `get_policy` call returned policy data for that policy until a `verify_identity` call for it returned `"verified": true`.
11. `results/v2/summary.json` has `"conversations": 44`. `analysis/compare.md`, the `compare` block in `failure-analysis.md` and the `headline` block in `README.md` match it (pass count, major count, PRIVACY count).
12. `python harness/build_demo.py` ran without the insurer-name assertion, and `demo/index.html` is newer than `results/v2/summary.json`.
13. `README.md` has: the updated tools row, the `strict_identity` guard row, "all five guards above", the two Step 12a item 6 bullets, the edited persona-drift bullet with its link, and the `pre-identity-fix` folder-map row. Every number in the line-15 paragraph matches the regenerated tables.
14. `failure-analysis.md` has: the section 7 `strict_identity` bullet; corrected numbers in section 9 that match the regenerated tables; the renamed "first v2 run" privacy paragraph with links to `pre-identity-fix`; the replaced "Fix built after the run" sentence; the filled-in "Rerun with the identity fix" paragraph with no `<...>` placeholders left; and the new section 10 bullet that calls HP06 a design gap and says policy number alone still verifies.
15. No sentence in `README.md` or `failure-analysis.md` describes the first AD06 or HP06 run as the current v2 result without saying "first v2 run" or linking to `pre-identity-fix`. No sentence still says the identity fix is "not built or tested". Every quote attributed to an AD06 or HP06 rerun appears word for word in `results/v2/transcripts/AD06.md` or `HP06.md`.
16. The Step 12c grep printed nothing, or its output is listed in the writer's report with no edits made.
17. The Step 13 scan ran after Step 11 and Step 12. It reports hits only in `02-prototype/harness/redact.py` and `02-prototype/harness/test_tools.py`, or any other hit is listed in the writer's report and left unedited. The scan excluded `results/v1/invalid/`, `results/v2/smoke-pre-fix/` and all `__pycache__` folders, and its output contains no insurer names.
18. `PROGRESS.md`, all `PLAN*.md` and `REVIEW*.md` files, and everything under `01-design/` and `04-compliance-risk/` are unchanged. Nothing was committed or pushed.
19. All new text uses "simulated" where results are described, plain Australian English, short sentences, and no real insurer name.
