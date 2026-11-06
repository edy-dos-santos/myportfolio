"""Offline tests for metrics.py. No SDK, no network, no conversation.

    python test_metrics.py     # prints OK (n tests) or fails with an AssertionError
"""
import copy
import json
import re
from pathlib import Path

import metrics as m

HERE = Path(__file__).resolve().parent
rec = json.loads((HERE / "tests" / "fixture_P01-A.json").read_text(encoding="utf-8"))
personas = m.load_personas(HERE / "personas.yaml")
p01 = personas["P01"]
tests = 0


def check(label, got, want):
    global tests
    assert got == want, f"{label}: got {got!r}, want {want!r}"
    tests += 1


row = m.conversation_row(rec, p01)

# Facts and lodging
check("facts_checked", row["facts_checked"], 7)
check("facts_correct", row["facts_correct"], 7)
check("lodged", row["lodged"], 1)
check("lodged_correct", row["lodged_correct"], 1)
check("task_success", row["task_success"], 1)
check("claim_number", row["claim_number"], "WTL-20500")

# Turn counts and questions
check("sam_turns", row["sam_turns"], 6)
check("customer_turns", row["customer_turns"], 7)
check("questions_asked", row["questions_asked"], 6)

# Repeat questions: date in Sam turn 2, location in Sam turn 3. The summary turn is excluded.
check("reasked_facts", row["reasked_facts"], 2)
check("reasked_facts (direct)", m.reasked_facts(rec["transcript"], p01["mentions"]), 2)
check("summary_turn_index", m.summary_turn_index(rec["transcript"]), 9)

# A wrong drivable answer lowers facts_correct and breaks success
bad = copy.deepcopy(rec)
create = [c for t in bad["transcript"] if t["role"] == "sam" for c in t["tools"] if c["tool"] == "create_claim"][0]
create["input"]["drivable"] = "no"
bad["tool_calls"] = [c if c["tool"] != "create_claim" else create for c in bad["tool_calls"]]
bad_row = m.conversation_row(bad, p01)
check("facts_correct with drivable=no", bad_row["facts_correct"], 6)
check("lodged_correct with drivable=no", bad_row["lodged_correct"], 0)
check("task_success with drivable=no", bad_row["task_success"], 0)

# Estimated customer time: formula from PLAN 8.2, computed here independently
words = lambda s: len(re.findall(r"\b\w+\b", s))
sam_w = sum(words(t["text"]) for t in rec["transcript"] if t["role"] == "sam")
cust_w = sum(words(t["text"]) for t in rec["transcript"] if t["role"] == "customer")
expected_secs = round(sam_w / p01["reading_wpm"] * 60 + cust_w / p01["typing_wpm"] * 60, 1)
check("est_customer_seconds", row["est_customer_seconds"], expected_secs)
check("est_customer_seconds (function)", m.est_customer_seconds(rec["transcript"], p01), expected_secs)

# Simulated records are modelled time (round 2, issue 4)
check("time_source simulated", row["time_source"], "modelled")

# Real records: measured time from the participant's ms over customer turns (round 2, issue 4)
real = copy.deepcopy(rec)
real["data_source"] = "real"
cust_turns = [t for t in real["transcript"] if t["role"] == "customer"]
for t, ms in zip(cust_turns, [0, 10000, 20000, 5000, 3000, 4000, 2000]):
    t["ms"] = ms
real_row = m.conversation_row(real, p01)
check("real est_customer_seconds", real_row["est_customer_seconds"], 44.0)
check("real time_source", real_row["time_source"], "measured")
check("real data_source", real_row["data_source"], "real")

# Row keys match the CSV column list, in order
check("conversation_row keys", list(row.keys()), m.CSV_COLUMNS)
check("data_source", row["data_source"], "simulated")

# Questionnaire fields and blanks when the judge is missing
check("seq", row["seq"], 6)
check("csat", row["csat"], 4)
check("judge_effort blank without judge", row["judge_effort"], "")

# Summary and pairing run on a single row without error
summary = m.summarise([row])
check("summary A n", summary["A"]["n"], 1)
check("summary complete_pairs", summary["complete_pairs"], 0)
check("paired empty", m.paired([row]), [])

# Decision rule: fewer than 6 complete pairs gives no recommendation
variant, reason = m.recommend(summary, [])
check("recommend variant", variant, None)
check("recommend reason", "Not enough data" in reason and reason.startswith("Simulated pilot result:"), True)


# ---- Decision rule (PLAN 8.5, round 2 issue 6) -------------------------------------------------

def mk(pid, variant, success, est, csat):
    """A conversation row with the fields the decision rule reads. Every other metric is blank."""
    r = {k: "" for k in m.CSV_COLUMNS}
    r.update({"persona_id": pid, "persona_name": pid, "variant": variant, "variant_name": m.VARIANT_NAMES[variant],
              "task_success": success, "lodged_correct": success, "est_customer_seconds": est, "csat": csat})
    return r


def pairs(n, a_succ=None, b_succ=None, a_est=200, b_est=200, a_csat=4.0, b_csat=4.0):
    """n complete pairs, personas T01..Tnn. Success lists are per persona; default all succeed."""
    a_succ = a_succ or [1] * n
    b_succ = b_succ or [1] * n
    rows = []
    for i in range(n):
        pid = f"T{i + 1:02d}"
        rows.append(mk(pid, "A", a_succ[i], a_est, a_csat))
        rows.append(mk(pid, "B", b_succ[i], b_est, b_csat))
    return rows


def prefs_for(letters):
    """Preference dicts for T01.. in order, from a string such as 'AAABBB'."""
    return [{"persona_id": f"T{i + 1:02d}", "preferred_variant": v} for i, v in enumerate(letters)]


def check_winner(label, rows, prefs, want):
    variant, reason = m.recommend(m.summarise(rows), prefs)
    check(f"{label} variant", variant, want)
    if want is not None:
        check(f"{label} reason prefix", reason.startswith("Simulated pilot result:"), True)
        check(f"{label} reason end", reason.endswith(m.END_SENTENCE), True)
    return reason


# R0: not enough data (5 complete pairs)
reason = check_winner("R0", pairs(5), [], None)
check("R0 reason", "Not enough data" in reason, True)

# R1: rule 1. B succeeds for 6 personas, A for 4. Estimates and CSAT equal.
r1 = pairs(6, a_succ=[1, 1, 1, 1, 0, 0], b_succ=[1] * 6)
check_winner("R1 rule 1", r1, [], "B")
check("R1 reason mentions paired", "(paired personas only)" in m.recommend(m.summarise(r1), [])[1], True)

# R2: rule 2. A est 200 s, B est 150 s (25% faster). CSAT A 4.0, B 3.8.
r2 = pairs(6, a_est=200, b_est=150, a_csat=4.0, b_csat=3.8)
check_winner("R2 rule 2", r2, [], "B")

# R2-edge: exactly 15% faster and CSAT exactly 0.5 lower. Both still pass.
r2e = pairs(6, a_est=200, b_est=170, a_csat=4.0, b_csat=3.5)
check_winner("R2-edge", r2e, [], "B")

# R2-block CSAT: 15% faster, but CSAT 0.6 lower. Rule 2 is blocked. 4 B, 2 A preferences: no rule 3 winner.
r2b = pairs(6, a_est=200, b_est=150, a_csat=4.0, b_csat=3.4)
reason = check_winner("R2-block CSAT", r2b, prefs_for("BBBBAA"), None)
check("R2-block CSAT reason", "no clear winner" in reason, True)

# R3: rule 3. All succeed, 5% time gap (below 15%). 7 of 10 prefer A.
r3 = pairs(10, a_est=200, b_est=190)
check_winner("R3 rule 3", r3, prefs_for("AAAAAAABBB"), "A")

# R4: no winner. Everything equal, 5 A and 5 B preferences.
r4 = pairs(10)
reason = check_winner("R4 no winner", r4, prefs_for("AAAAABBBBB"), None)
check("R4 reason", "Keep the current design (B)" in reason, True)

# P: paired-only basis. Two B-only rows would win rule 1 and rule 2 if they were counted.
rp = pairs(6) + [mk("T07", "B", 1, 50, 4.0), mk("T08", "B", 1, 50, 4.0)]
sp = m.summarise(rp)
check("P paired n_pairs", sp["paired_basis"]["n_pairs"], 6)
check("P paired B successes", sp["paired_basis"]["B"]["successes"], 6)
variant, reason = m.recommend(sp, [])
check("P paired-only variant is not B", variant != "B", True)
check("P paired-only variant", variant, None)

# P-prefs: rule 3 counts only preferences from complete pairs. 7 B preferences, 2 from unpaired personas.
rpp = pairs(6) + []
prefs_pp = prefs_for("BBBBB") + [{"persona_id": "T07", "preferred_variant": "B"},
                                  {"persona_id": "T08", "preferred_variant": "B"}]
check_winner("P-prefs", rpp, prefs_pp, None)


# ---- check_facts (round 2, issue 6) ------------------------------------------------------------

# P04 has driver_match null: the driver fact is not checked and facts_checked is 6.
p04 = personas["P04"]
claim_p01 = m.first_claim(rec["tool_calls"])
facts_p04 = m.check_facts(claim_p01, p04["ground_truth"])
check("P04 driver result", facts_p04["driver"], None)
check("P04 facts_checked", sum(1 for v in facts_p04.values() if v is not None), 6)

# A wrong location: the P01 claim says Logan Rd, so location is False and facts_correct drops to 6.
wrong = copy.deepcopy(rec)
loc_call = [c for c in wrong["tool_calls"] if c["tool"] == "create_claim"][0]
loc_call["input"]["location"] = "Logan Rd, Mount Gravatt"
for t in wrong["transcript"]:
    for c in t.get("tools", []):
        if c["tool"] == "create_claim":
            c["input"]["location"] = "Logan Rd, Mount Gravatt"
wrong_facts = m.check_facts(m.first_claim(wrong["tool_calls"]), p01["ground_truth"])
check("wrong location fact", wrong_facts["location"], False)
check("wrong location facts_correct", m.conversation_row(wrong, p01)["facts_correct"], 6)

print(f"OK ({tests} tests)")
