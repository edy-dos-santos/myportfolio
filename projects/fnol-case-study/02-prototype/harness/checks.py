"""Automatic checks on Sam's tool calls. Shared by run_tests.py, analysis/compare.py and build_demo.py."""


def requested_person(calls):
    return any(c["tool"] == "handoff_to_human" and (c.get("input") or {}).get("reason") == "customer_request"
               for c in calls)


def waived_checks(sc, calls):
    """must_call items excused because the customer asked for a person (design rule T02 beats finishing the task)."""
    names = [c["tool"] for c in calls]
    if not requested_person(calls):
        return []
    return [f"{t} not required: the customer asked for a person"
            for t in (sc.get("checks") or {}).get("must_call", []) if t not in names and t != "handoff_to_human"]


def auto_checks(sc, calls):
    names = [c["tool"] for c in calls]
    chk, fails = sc.get("checks") or {}, []
    for t in chk.get("must_call", []):
        if t not in names and not (requested_person(calls) and t != "handoff_to_human"):
            fails.append(f"expected a call to {t}")
    for t in chk.get("must_not_call", []):
        if t in names:
            fails.append(f"should not have called {t}")
    if "handoff_reason" in chk:
        reasons = [c["input"].get("reason") for c in calls if c["tool"] == "handoff_to_human"]
        cb = "request_callback" in names
        if not reasons and not cb:
            fails.append(f"expected a handoff ({'/'.join(chk['handoff_reason'])}) or callback")
        elif reasons and not set(reasons) & set(chk["handoff_reason"]):
            fails.append(f"handoff reason {reasons} not in {chk['handoff_reason']}")
    if "order" in chk:
        a, b = chk["order"]
        if a in names and b in names and names.index(a) > names.index(b):
            fails.append(f"{a} should happen before {b}")
    return fails


def passed(result):
    fails = result["judge"].get("failures", [])
    return not result["auto_check_failures"] and not any(f["severity"] in ("critical", "major") for f in fails)
