"""Pure metric functions for the Project 3 pilot (story-first vs form-first).

No SDK import. Inputs are conversation records (PLAN 7.4) and personas (personas.yaml).
Every number produced here describes SIMULATED participants (LLM personas), not real people.
"""
import re
import statistics
from collections import Counter
from pathlib import Path

import yaml

FACTS = ["policy_number", "vehicle_rego", "incident_type", "date", "location", "drivable", "driver"]
GT_KEY = {"policy_number": "policy_number", "vehicle_rego": "vehicle_rego", "incident_type": "incident_type",
          "date": "date_match", "location": "location_match", "drivable": "drivable", "driver": "driver_match"}
SLOT_QUESTION_PATTERNS = {
    "date_time":   r"\bwhen\b|what time|what day|which day|\bdate\b",
    "location":    r"\bwhere\b|street|suburb|address|location",
    "driver":      r"who was driving|were you driving|was anyone driving|behind the wheel|driving at the time",
    "drivable":    r"drive it|drivable|driveable|safe to drive|be driven|still drive",
    "other_party": r"other driver|other party|other car|other vehicle|their (name|details|number|rego)",
    "police_ref":  r"police",
}
CSV_COLUMNS = [
    "conversation_id", "persona_id", "persona_name", "age", "age_band", "digital_confidence", "emotional_state",
    "story_style", "incident_type", "variant", "variant_name", "order_position", "data_source", "sam_model",
    "customer_model", "started_at", "lodged", "claim_number", "handoff", "callback", "facts_checked",
    "facts_correct", "facts_correct_pct", "lodged_correct", "task_success", "sam_turns", "customer_turns",
    "questions_asked", "reasked_facts", "reasked_facts_judge", "sam_words", "customer_words",
    "est_customer_seconds", "time_source", "elapsed_seconds", "sam_seconds", "hit_turn_cap", "seq", "csat", "comment",
    "judge_effort", "judge_tone", "judge_rule_breaks", "error",
]
SUMMARY_METRICS = ["sam_turns", "questions_asked", "reasked_facts", "reasked_facts_judge", "est_customer_seconds",
                   "elapsed_seconds", "seq", "csat", "judge_effort", "facts_correct_pct"]
VARIANT_NAMES = {"A": "form_first", "B": "story_first"}


def load_personas(path):
    """Return {persona_id: persona dict} from personas.yaml."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {p["id"]: p for p in data}


def _present(v):
    return v is not None and v != ""


def _norm_id(s):
    return re.sub(r"\s", "", str(s or "")).upper()


def _any_in(subs, text):
    t = str(text or "").lower()
    return any(s.lower() in t for s in subs)


def _create_call(calls):
    """The first create_claim call whose output has a claim_number, or None."""
    for c in calls or []:
        out = c.get("output")
        if c.get("tool") == "create_claim" and isinstance(out, dict) and "claim_number" in out:
            return c
    return None


def first_claim(calls):
    """Input of the first create_claim call that returned a claim_number, or None."""
    c = _create_call(calls)
    return c["input"] if c else None


def check_facts(claim, gt):
    """Fact -> True/False, or None when the ground truth value is null (not checked)."""
    res = {}
    for fact in FACTS:
        want = gt.get(GT_KEY[fact])
        if want is None:
            res[fact] = None
        elif claim is None:
            res[fact] = False
        elif fact in ("policy_number", "vehicle_rego"):
            res[fact] = _norm_id(claim.get(fact)) == _norm_id(want)
        elif fact == "incident_type":
            res[fact] = str(claim.get("incident_type") or "").lower() in [w.lower() for w in want]
        elif fact == "drivable":
            res[fact] = str(claim.get("drivable") or "").lower() in [w.lower() for w in want]
        elif fact == "date":
            res[fact] = _any_in(want, claim.get("date_time"))
        elif fact == "location":
            res[fact] = _any_in(want, claim.get("location"))
        elif fact == "driver":
            res[fact] = _any_in(want, claim.get("driver"))
    return res


def questions(text):
    """Sentences that end in a question mark."""
    return [q.strip() for q in re.findall(r"[^.?!\n]*\?", text or "")]


def slots_asked(question):
    """Slots whose question pattern matches the question."""
    q = question.lower()
    return {slot for slot, pat in SLOT_QUESTION_PATTERNS.items() if re.search(pat, q)}


def summary_turn_index(transcript):
    """Index of the Sam turn just before the first Sam turn that called create_claim. None if no claim."""
    prev = None
    for i, t in enumerate(transcript):
        if t["role"] != "sam":
            continue
        if any(c.get("tool") == "create_claim" for c in t.get("tools", [])):
            return prev
        prev = i
    return None


def reasked_facts(transcript, mentions):
    """Heuristic count of Sam questions about a slot the customer had already covered (keyword match)."""
    first_create = None
    for i, t in enumerate(transcript):
        if t["role"] == "sam" and any(c.get("tool") == "create_claim" for c in t.get("tools", [])):
            first_create = i
            break
    summary = summary_turn_index(transcript)
    cust_text, count = "", 0
    for i, t in enumerate(transcript):
        if first_create is not None and i >= first_create:
            break
        if t["role"] == "customer":
            cust_text += " " + t["text"].lower()
        elif i != summary:
            slots = set()
            for q in questions(t["text"]):
                slots |= slots_asked(q)
            for slot in slots:
                if any(k.lower() in cust_text for k in (mentions or {}).get(slot) or []):
                    count += 1
    return count


def word_count(text):
    return len(re.findall(r"\b\w+\b", text or ""))


def est_customer_seconds(transcript, persona):
    """Modelled estimate of the human's reading and typing time. Not measured."""
    sam_words = sum(word_count(t["text"]) for t in transcript if t["role"] == "sam")
    cust_words = sum(word_count(t["text"]) for t in transcript if t["role"] == "customer")
    return round(sam_words / persona["reading_wpm"] * 60 + cust_words / persona["typing_wpm"] * 60, 1)


def measured_customer_seconds(transcript):
    """Real records: sum of the participant's measured ms over customer turns, in seconds (1 decimal)."""
    return round(sum(t.get("ms", 0) for t in transcript if t["role"] == "customer") / 1000, 1)


def conversation_row(rec, persona):
    """One CSV row (keys in CSV_COLUMNS order). Blanks are empty strings."""
    tr = rec["transcript"]
    data_source = rec.get("data_source", "simulated")
    calls = rec.get("tool_calls", [])
    cc = _create_call(calls)
    claim = cc["input"] if cc else None
    lodged = cc is not None
    facts = check_facts(claim, persona["ground_truth"])
    checked = [v for v in facts.values() if v is not None]
    n_checked, n_correct = len(checked), sum(1 for v in checked if v)
    lodged_correct = int(lodged and n_correct == n_checked)
    handoff = int(any(c.get("tool") == "handoff_to_human" for c in calls))
    callback = int(any(c.get("tool") == "request_callback" for c in calls))
    if persona.get("success_rule", "lodge") == "lodge":
        success = lodged_correct
    else:
        success = int(bool(lodged_correct or handoff or callback))

    sam = [t for t in tr if t["role"] == "sam"]
    cust = [t for t in tr if t["role"] == "customer"]
    j = rec.get("judge") or {}
    judge_ok = bool(rec.get("judge")) and "error" not in j
    q = rec.get("questionnaire") or {}
    seq, csat = q.get("seq"), q.get("csat")
    rule_breaks = j.get("rule_breaks")
    errors = [str(e) for e in (q.get("error"), j.get("error")) if e]

    row = {
        "conversation_id": rec["conversation_id"],
        "persona_id": persona["id"],
        "persona_name": persona["name"],
        "age": persona["age"],
        "age_band": persona["age_band"],
        "digital_confidence": persona["digital_confidence"],
        "emotional_state": persona["emotional_state"],
        "story_style": persona["story_style"],
        "incident_type": persona["incident_type"],
        "variant": rec["variant"],
        "variant_name": rec["variant_name"],
        "order_position": rec["order_position"],
        "data_source": data_source,
        "sam_model": rec.get("sam_model", ""),
        "customer_model": rec.get("customer_model", ""),
        "started_at": rec.get("started_at", ""),
        "lodged": int(lodged),
        "claim_number": cc["output"]["claim_number"] if cc else "",
        "handoff": handoff,
        "callback": callback,
        "facts_checked": n_checked,
        "facts_correct": n_correct,
        "facts_correct_pct": round(n_correct / n_checked * 100, 1) if n_checked else "",
        "lodged_correct": lodged_correct,
        "task_success": success,
        "sam_turns": len(sam),
        "customer_turns": len(cust),
        "questions_asked": sum(len(questions(t["text"])) for t in sam),
        "reasked_facts": reasked_facts(tr, persona.get("mentions", {})),
        "reasked_facts_judge": j.get("reasked_facts") if judge_ok and isinstance(j.get("reasked_facts"), int) else "",
        "sam_words": sum(word_count(t["text"]) for t in sam),
        "customer_words": sum(word_count(t["text"]) for t in cust),
        "est_customer_seconds": (measured_customer_seconds(tr) if data_source == "real"
                                 else est_customer_seconds(tr, persona)),
        "time_source": "measured" if data_source == "real" else "modelled",
        "elapsed_seconds": rec.get("elapsed_seconds", ""),
        "sam_seconds": round(sum(t.get("ms", 0) for t in sam) / 1000, 1),
        "hit_turn_cap": int(bool(rec.get("hit_turn_cap"))),
        "seq": seq if isinstance(seq, int) else "",
        "csat": csat if isinstance(csat, int) else "",
        "comment": re.sub(r"[\r\n]+", " ", str(q.get("comment") or "")).strip(),
        "judge_effort": j.get("effort_score") if judge_ok and isinstance(j.get("effort_score"), int) else "",
        "judge_tone": j.get("tone_score") if judge_ok and isinstance(j.get("tone_score"), int) else "",
        "judge_rule_breaks": len(rule_breaks) if judge_ok and isinstance(rule_breaks, list) else "",
        "error": "; ".join(errors),
    }
    return {k: row[k] for k in CSV_COLUMNS}


def _stats(vals):
    vals = [v for v in vals if _present(v)]
    if not vals:
        return {"n": 0, "mean": None, "median": None}
    return {"n": len(vals), "mean": round(statistics.mean(vals), 2), "median": round(statistics.median(vals), 2)}


def _complete_pairs(rows):
    have = {}
    for r in rows:
        have.setdefault(r["persona_id"], set()).add(r["variant"])
    return sorted(pid for pid, vs in have.items() if {"A", "B"} <= vs)


def summarise(rows):
    """Per variant: n, success counts and rates, and mean/median for each numeric metric (blanks skipped)."""
    out = {}
    for v in ("A", "B"):
        rs = [r for r in rows if r["variant"] == v]
        n = len(rs)
        succ = sum(r["task_success"] for r in rs)
        lodged_ok = sum(r["lodged_correct"] for r in rs)
        d = {"n": n, "successes": succ,
             "task_success_rate": round(succ / n * 100, 1) if n else None,
             "lodged_correct_rate": round(lodged_ok / n * 100, 1) if n else None}
        for m in SUMMARY_METRICS:
            d[m] = _stats([r[m] for r in rs])
        out[v] = d
    pairs = _complete_pairs(rows)
    out["complete_pairs"] = len(pairs)
    # Decision-rule basis: only personas with both variants complete (round 2, issue 2).
    both = [r for r in rows if r["persona_id"] in pairs]
    basis = {"n_pairs": len(pairs), "pair_ids": pairs}
    for v in ("A", "B"):
        rs = [r for r in both if r["variant"] == v]
        basis[v] = {"successes": sum(r["task_success"] for r in rs),
                    "est_customer_seconds_mean": _stats([r["est_customer_seconds"] for r in rs])["mean"],
                    "csat_mean": _stats([r["csat"] for r in rs])["mean"]}
    out["paired_basis"] = basis
    return out


def paired(rows):
    """Per persona with both variants: B minus A deltas, plus both task_success values."""
    by = {}
    for r in rows:
        by.setdefault(r["persona_id"], {})[r["variant"]] = r
    out = []
    for pid in sorted(by):
        p = by[pid]
        if "A" not in p or "B" not in p:
            continue
        a, b = p["A"], p["B"]

        def delta(k):
            return round(b[k] - a[k], 2) if _present(a[k]) and _present(b[k]) else None

        out.append({
            "persona_id": pid, "persona_name": b["persona_name"],
            "task_success_A": a["task_success"], "task_success_B": b["task_success"],
            "delta_est_customer_seconds": delta("est_customer_seconds"),
            "delta_questions_asked": delta("questions_asked"),
            "delta_reasked_facts": delta("reasked_facts"),
            "delta_seq": delta("seq"),
            "delta_csat": delta("csat"),
        })
    return out


END_SENTENCE = "Confirm with the real study before changing the design."


def recommend(summary, prefs):
    """Decision rule written before the run (PLAN 8.5). Returns (variant or None, reason).

    All four rules use only personas with both variants complete (summary["paired_basis"]).
    """
    basis = summary.get("paired_basis", {})
    n = basis.get("n_pairs", summary.get("complete_pairs", 0))
    if n < 6:
        return None, f"Simulated pilot result: Not enough data ({n} of 6 complete pairs needed). {END_SENTENCE}"
    a, b = basis["A"], basis["B"]
    # Rule 1: task success differs by 2 or more personas.
    if abs(a["successes"] - b["successes"]) >= 2:
        win = "B" if b["successes"] > a["successes"] else "A"
        return win, (f"Simulated pilot result: variant {win} ({VARIANT_NAMES[win]}) had task success for "
                     f"{max(a['successes'], b['successes'])} personas against {min(a['successes'], b['successes'])} "
                     f"(paired personas only). {END_SENTENCE}")
    # Rule 2: mean estimated time differs by 15% or more (relative to the slower variant), and the faster
    # variant's mean CSAT is not lower by more than 0.5.
    ea, eb = a["est_customer_seconds_mean"], b["est_customer_seconds_mean"]
    if ea and eb and ea != eb:
        fast, slow = ("A", "B") if ea < eb else ("B", "A")
        ef, es = min(ea, eb), max(ea, eb)
        cf, cs = basis[fast]["csat_mean"], basis[slow]["csat_mean"]
        if (es - ef) / es >= 0.15 and cf is not None and cs is not None and cf >= cs - 0.5:
            return fast, (f"Simulated pilot result: variant {fast} ({VARIANT_NAMES[fast]}) took less estimated "
                          f"participant time ({round(ef)} s against {round(es)} s, a difference of "
                          f"{round((es - ef) / es * 100)}%) without a lower CSAT. {END_SENTENCE}")
    # Rule 3: one variant preferred by at least 7 personas. Only preferences from complete pairs count.
    pair_ids = set(basis.get("pair_ids", []))
    paired_prefs = [p for p in prefs if p.get("persona_id") in pair_ids]
    counts = Counter(p.get("preferred_variant") for p in paired_prefs)
    for v in ("A", "B"):
        if counts[v] >= 7:
            return v, (f"Simulated pilot result: {counts[v]} of {len(paired_prefs)} personas preferred variant {v} "
                       f"({VARIANT_NAMES[v]}). {END_SENTENCE}")
    # Rule 4: no clear winner. Keep the current design (B).
    return None, ("Simulated pilot result: no clear winner. Keep the current design (B) and let the real study "
                  f"decide. {END_SENTENCE}")
