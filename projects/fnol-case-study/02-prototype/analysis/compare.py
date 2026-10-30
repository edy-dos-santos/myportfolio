"""Before and after tables for Project 2. All results are SIMULATED (simulated customers, LLM judge).

    python analysis/compare.py

Reads results/v1, results/v2 (if present), harness/scenarios.yaml and analysis/root_causes.yaml.
Writes analysis/compare.md and fills the generated blocks in analysis/failure-analysis.md and README.md.
Makes no Claude calls. Shows "pending" for v2 until results/v2 exists.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
from checks import auto_checks, waived_checks  # noqa: E402

SCEN_LIST = yaml.safe_load((ROOT / "harness" / "scenarios.yaml").read_text(encoding="utf-8"))
SCEN = {s["id"]: s for s in SCEN_LIST}
ROOT_CAUSES = yaml.safe_load((ROOT / "analysis" / "root_causes.yaml").read_text(encoding="utf-8"))
PENDING = "pending"
SEVERE = ("critical", "major")


def load(version):
    """One dict per saved conversation. Returns None when the version has no results yet."""
    d = ROOT / "results" / version / "transcripts"
    if not d.exists() or not any(d.glob("*.json")):
        return None
    items = []
    for p in sorted(d.glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        fails = r["judge"].get("failures", [])
        corrected = auto_checks(SCEN[r["id"]], r["tool_calls"])
        first = r.get("auto_check_failures_original", r["auto_check_failures"])
        items.append({
            "id": r["id"], "title": r["title"], "category": r["category"], "fails": fails,
            "pass_first": not first and not any(f["severity"] in SEVERE for f in fails),
            "pass": not corrected and not any(f["severity"] in SEVERE for f in fails),
            "waived": waived_checks(SCEN[r["id"]], r["tool_calls"]),
            "task": r["judge"].get("task_score"), "tone": r["judge"].get("tone_score"),
        })
    return {i["id"]: i for i in items}


def rejudge_rows():
    d = ROOT / "results" / "v1" / "rejudge"
    if not d.exists():
        return []
    rows = []
    for p in sorted(d.glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        orig, new = r["original"].get("failures", []), r["rejudge"].get("failures", [])
        rows.append((r["id"], orig, new))
    return rows


def verdict(fails):
    ok = not any(f["severity"] in SEVERE for f in fails)
    tags = ", ".join(sorted({f["tag"] for f in fails})) or "none"
    return ("pass" if ok else "fail"), tags


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def mark(item):
    return "pending" if item is None else ("✅" if item else "❌")


def avg(items, key):
    vals = [i[key] for i in items if i[key] is not None]
    return round(sum(vals) / len(vals), 2) if vals else "-"


def build_tables(v1, v2):
    v2_on = v2 is not None
    sections = []

    # 1. Headline
    def head_row(name, items):
        if items is None:
            return [name, "0 (pending)", PENDING, PENDING, PENDING, PENDING, PENDING, PENDING, PENDING, PENDING]
        vals = list(items.values())
        sev = Counter(f["severity"] for i in vals for f in i["fails"])
        return [name, len(vals), sum(i["pass_first"] for i in vals), sum(i["pass"] for i in vals),
                sev["critical"], sev["major"], sev["minor"], sum(len(i["waived"]) for i in vals),
                avg(vals, "task"), avg(vals, "tone")]
    sections.append(("Simulated test results: headline", md_table(
        ["Version", "Conversations", "Passed (as first recorded)", "Passed (corrected checks)", "Critical", "Major",
         "Minor", "Checks waived", "Avg task", "Avg tone"],
        [head_row("v1", v1), head_row("v2", v2)])))

    # 2. By category
    cats = sorted({i["category"] for i in (v1 or {}).values()} | {i["category"] for i in (v2 or {}).values()})

    def cat_count(items, c):
        if items is None:
            return PENDING
        sel = [i for i in items.values() if i["category"] == c]
        return f"{sum(i['pass'] for i in sel)}/{len(sel)}"
    sections.append(("Simulated test results: passed by category", md_table(
        ["Category", "v1 passed", "v2 passed"],
        [[c, cat_count(v1, c), cat_count(v2, c)] for c in cats])))

    # 3. Failure tags
    def tag_counts(items):
        return Counter(f["tag"] for i in (items or {}).values() for f in i["fails"])
    t1, t2 = tag_counts(v1), tag_counts(v2)
    tag_rows = [[t, t1[t], t2[t] if v2_on else PENDING] for t in sorted(set(t1) | set(t2), key=lambda t: -t1[t])]
    sections.append(("Simulated test results: failure tags (judge findings)", md_table(
        ["Tag", "v1", "v2"], tag_rows)))

    # 4. Root causes
    def signal(sig, items):
        if items is None:
            return PENDING
        if sig.get("invalid"):
            return "n/a (rerun)"
        if sig.get("checks"):
            return sum(len(i["waived"]) for i in items.values())
        tags = set(sig.get("tags") or [])
        rx = re.compile(sig["pattern"], re.I)
        return sum(1 for i in items.values() for f in i["fails"]
                   if (not tags or f["tag"] in tags) and rx.search(f.get("evidence", "") + " " + f.get("why", "")))

    def results_text(ids, items):
        if items is None:
            return "; ".join(f"{s} {PENDING}" for s in ids)
        parts = []
        for s in ids:
            i = items.get(s)
            if i is None:
                parts.append(f"{s} not run")
                continue
            txt = f"{s} {mark(i['pass'])}"
            if i["pass"] != i["pass_first"]:
                txt += f" (first recorded {mark(i['pass_first'])})"
            parts.append(txt)
        return "; ".join(parts)

    rc_rows = []
    for rc in ROOT_CAUSES:
        s1, s2 = signal(rc["signal"], v1), signal(rc["signal"], v2)
        rc_rows.append([f"{rc['id']}: {rc['name']}", rc["fix"], rc["layer"], ", ".join(rc["scenarios"]),
                        results_text(rc["scenarios"], v1), results_text(rc["scenarios"], v2),
                        f"{s1} → {s2 if v2_on else PENDING}" if s1 != PENDING else PENDING])
    sections.append(("Simulated test results: root causes", md_table(
        ["Root cause", "Fix", "Layer", "Scenarios", "v1 result", "v2 result", "Signal findings v1 → v2"], rc_rows)
        + "\n\nSignal counts are approximate: a regex over judge text, and one finding can match more than one root cause."
        + "\n\nv1 results use the corrected checks. The first-recorded result is shown when it differs."))

    # 5. Per scenario
    rows = []
    for s in SCEN_LIST:
        sid = s["id"]
        a = v1.get(sid) if v1 else None
        b = v2.get(sid) if v2 else None
        p1 = mark(a["pass"]) if a else "not run"
        p2 = mark(b["pass"]) if b else (PENDING if not v2_on else "not run")
        if a and b:
            change = "same" if a["pass"] == b["pass"] else ("fixed" if b["pass"] else "regressed")
        else:
            change = PENDING
        rows.append([sid, s["title"], p1, p2, change])
    sections.append(("Simulated test results: per scenario", md_table(
        ["ID", "Scenario", "v1 pass", "v2 pass", "Change"], rows)))

    # 6. Judge agreement (only when re-judge files exist)
    rj = rejudge_rows()
    if rj:
        rows = []
        for sid, orig, new in rj:
            ov, ot = verdict(orig)
            nv, nt = verdict(new)
            rows.append([sid, f"{ov} ({ot})", f"{nv} ({nt})", "yes" if ov == nv else "no"])
        same = sum(1 for r in rows if r[3] == "yes")
        sections.append((f"Simulated judge agreement: re-judged {len(rows)} conversations, {same} with the same verdict",
                         md_table(["ID", "Original verdict (tags)", "Re-judge verdict (tags)", "Same verdict?"], rows)))
    return sections


def headline_text(v1, v2):
    def count(items, fn):
        return PENDING if items is None else fn(items)
    p1 = count(v1, lambda it: f"{sum(i['pass'] for i in it.values())}/{len(it)}")
    p2 = count(v2, lambda it: f"{sum(i['pass'] for i in it.values())}/{len(it)}")
    def sev(items, level):
        return count(items, lambda it: str(sum(1 for i in it.values() for f in i["fails"] if f["severity"] == level)))
    return "\n\n".join([
        f"**Simulated test results (corrected checks).** Conversations passed: v1 {p1}, v2 {p2}.",
        f"Critical findings: v1 {sev(v1, 'critical')} → v2 {sev(v2, 'critical')}. "
        f"Major findings: v1 {sev(v1, 'major')} → v2 {sev(v2, 'major')}.",
        "Simulated customers, single run per scenario: run-to-run variation was not measured, so a difference of 1-3 conversations may be noise.",
    ])


def fill(path, name, body):
    begin, end = f"<!-- BEGIN GENERATED: {name} -->", f"<!-- END GENERATED: {name} -->"
    if not path.exists():
        print(f"WARNING: {path} not found; {name} block not filled")
        return
    text = path.read_text(encoding="utf-8")
    pat = re.compile(re.escape(begin) + r"(.*?)" + re.escape(end), re.S)
    if not pat.search(text):
        print(f"WARNING: marker pair '{name}' missing in {path.name}; file left alone")
        return
    new = pat.sub(lambda m: begin + "\n" + body.strip() + "\n" + end, text, count=1)
    path.write_text(new, encoding="utf-8")
    print(f"filled '{name}' block in {path.relative_to(ROOT)}")


def main():
    v1, v2 = load("v1"), load("v2")
    if v2 is None:
        print("results/v2 not found yet: v2 columns show pending")
    sections = build_tables(v1, v2)
    compare_md = ["# Simulated test results: before and after", "",
                  "All results are simulated: simulated customers, judged by an LLM. Generated by `python analysis/compare.py`.",
                  ""]
    for title, body in sections:
        compare_md += [f"### {title}", "", body, ""]
    (ROOT / "analysis" / "compare.md").write_text("\n".join(compare_md), encoding="utf-8")
    print("wrote analysis/compare.md")

    block = "Filled by `python analysis/compare.py`.\n\n" + "\n\n".join(f"### {t}\n\n{b}" for t, b in sections)
    fill(ROOT / "analysis" / "failure-analysis.md", "compare", block)
    fill(ROOT / "README.md", "headline", headline_text(v1, v2))


if __name__ == "__main__":
    main()
