VERDICT: FAIL

The code half is correct and tested. The fail is because Steps 8 to 12 were not done: README.md and analysis/failure-analysis.md are unedited, and demo/index.html was not rebuilt. Criteria 8 to 12 and 16 are pending the reruns, as agreed.

## Criteria

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | tools.py lines 92-108: Step 3 block matches the plan, inside `if g.get("strict_identity")`. Message is exactly "No match. Check the details and try again." Description and schema unchanged. |
| 2 | PASS | `id_mismatch: set = field(default_factory=set)` present. Docstring says "a strict identity check". |
| 3 | PASS | sam.py v2 guards are the five guards, all True. v1 is `{"prompt": "system_v1.md", "guards": {}}`. |
| 4 | PASS | `python harness/test_tools.py` prints `all 22 tests passed`. The six new tests are in the file. |
| 5 | PASS | Project 3 command prints `project 3 imports ok`. test_metrics.py: OK (59 tests). test_offline.py: OK (14 tests). All 03-usability-ab .py files date from 29 Oct or earlier. No git here, so checked by mtime only. |
| 6 | PASS (mtime) | system_v1.md, system_v2.md, scenarios.yaml, run_tests.py, checks.py all dated 28-29 Oct, before the fix. |
| 7 | FAIL | template.html has the three Step 6 edits (4 `idMismatch` occurrences: lines 258, 291, 292, 385). `node --check` on the script block passes. The `verify_identity` description is unchanged. But `grep -o idMismatch demo/index.html` finds 0, not 4. index.html is dated 29 Oct and was not rebuilt (Step 11). |
| 8-12 | PENDING | `results/v2/pre-identity-fix/` does not exist yet. Awaiting reruns. |
| 13 | FAIL | README.md has 0 mentions of `strict_identity` and 0 of `pre-identity-fix`. Step 12a not done. |
| 14 | FAIL | failure-analysis.md has 0 mentions of `strict_identity` and 0 of `pre-identity-fix`. Step 12b not done. |
| 15 | FAIL | failure-analysis.md line 229 still says "A proposed fix, not built or tested". Reruns do not exist, so no rerun quotes. |
| 16 | PENDING | Step 12c grep waits for the reruns. |
| 17 | PARTIAL | I ran the Step 13 scan. Hits: `02-prototype/harness/redact.py` (40), `harness/test_tools.py` (6), plus `02-prototype/PLAN.md` (46) and `02-prototype/REVIEW-1-1.md` (2). The last two are older history files that the plan says not to edit. The plan expected hits only in redact.py and test_tools.py. See issue 3. The 6 hits in test_tools.py are all outside the new tests (new-test block: 0 hits). tools.py, sam.py, template.html, README.md, failure-analysis.md: 0 hits. |
| 18 | PASS (mtime) | No edits found to PROGRESS.md, PLAN*.md, REVIEW*.md, 01-design or 04-compliance-risk after the fix. Not verifiable through git. |
| 19 | PENDING | No new prose exists yet to check. |

## Attack results on `verify_identity` (v2 guards, called through the real handler)

| Sequence | Result |
|---|---|
| Policy number alone, then policy number plus wrong dob | `[True, False]`; verification revoked. |
| Wrong dob, then policy number alone | `[False, False]`; stays locked. |
| Wrong dob, then policy number plus correct dob and mobile | `[False, True]`; unlocks as designed. |
| Blank or whitespace dob and mobile with a valid policy number | `[True, True]`; blanks are treated as not given. |
| Mismatch, then dob plus mobile with no policy number | `[False, True]`. By the plan's rule only the policy-number path is locked, so this verifies. See issue 2. |
| Lowercase or spaced policy number with a wrong dob, then the number alone | `[False, False]`; normalisation is applied before the lock. |
| Non-string dob (integer) | `AttributeError` on `.strip()`. See issue 4. |

Python and JS logic are identical in structure: same condition, same lock, same discard and message. The failure message does not say which detail was wrong (the same string as the ordinary no-match). v1 is unaffected: `test_v1_identity_unchanged` passes, and v1 guards are `{}`.

## Issues

1. **Steps 8 to 12 not done (blocking).** Run `python harness/build_demo.py` so `demo/index.html` gets the four `idMismatch` hits. Make the README.md edits (12a) and the failure-analysis.md edits (12b), using the real rerun numbers. Reruns, the `pre-identity-fix` backup and `compare.py` must come first. Re-review after that.
2. **Design note (not a blocker).** After a mismatch on a policy number, a caller can still verify by sending dob plus mobile with no policy number, because the loop below the guard is not locked. This matches the plan text, and it needs both correct factors, so it is arguably right. Say so in the "Rerun" paragraph or section 10 so a reader does not think the lock is total.
3. **Step 13 expectation is wrong.** PLAN.md (46 hits) and REVIEW-1-1.md (2 hits) hold the match patterns or names. They are committed history files that the plan says not to edit. Before any push, the orchestrator must decide: redact them, or exclude them from the push alongside redact.py and test_tools.py. I did not print any names.
4. **Minor robustness.** `(args.get("dob") or "").strip()` raises if the model sends a non-string dob. The v1 path would just fail to match. A `str(...)` wrapper would be safer. Low risk because the tool schema declares the type as a string, and the JS mirror already uses `String(a.dob || "")`.
