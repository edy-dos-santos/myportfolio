"""Build the Project 3 outputs from results/simulated/: CSV and JSON data, six SVG charts,
report.html and README.md.

    python build_report.py      # safe to re-run at any time; rebuilds everything from the saved results

Everything here is SIMULATED (LLM personas). With zero results the files are still written, with a
"Results pending" note, and the script exits 0.
"""
import csv
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import metrics

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "simulated"
CHARTS = ROOT / "charts"
PROTO = ROOT.parent / "02-prototype"
PLANNED = 20
TURN_CAP = 20  # must match MAX_TURNS in run_ab.py
LABEL = "SIMULATED participants (LLM personas). Not real user research."
BANNER = ("SIMULATED PILOT. Participants are LLM personas, not real people. This de-risks the study design; "
          "it is not user research.")
PREF_COLUMNS = ["persona_id", "persona_name", "data_source", "chat1_variant", "chat2_variant",
                "preferred_variant", "reason"]
PENDING = "Results pending: run `python run_ab.py --all`."
# Post-run text (PLAN-POST.md). Written for the complete 20-conversation simulated run of 30 October 2026.
# Shown only when all PLANNED conversations are complete.
POST_RUN_NOTE = (" Read this result with care. It comes from 10 simulated personas, and a gap of 2 personas is "
                 "small: one changed outcome would put it below the rule's threshold. Both of A's misses were on "
                 "one fact, whether the car is safe to drive, and neither was an error by Sam (see Limitations). "
                 "If both had counted as successes, B would still win, but only on modelled time (21% less). "
                 "This result is not evidence about real people. The real study should test it.")
POST_RUN_LIMITS = [
    "Simulated participants can drift from their brief. In P01-A, Chloe's brief says the car drives fine. When "
    "Sam asked about the tail-lights, she said: \"I haven't checked the tail-lights closely yet, so I'm not sure "
    "whether they're working.\" She then said \"I'm at the lights right now\", although the crash was that "
    "morning, and took it back a turn later: \"Sorry, I shouldn't have said I was at the lights.\" Sam recorded "
    "drivable as \"unsure\", and she confirmed the summary. The facts check expects \"yes\", so this counts as a "
    "failure. The drift is the persona's. But the first doubt came from variant A's form question about the "
    "tail-lights, so this miss is partly the test design.",
    "The facts check can mark a careful answer as wrong. In P10-A, Jordan's car has a broken headlight. Sam "
    "asked: \"With the broken headlight, do you feel the car is safe to drive, including at night?\" Jordan "
    "said: \"Not really sure about night driving.\" Sam recorded \"unsure\" and noted daylight only. The ground "
    "truth allows only \"yes\", so this counts as a failure. In P10-B, story-first Sam said \"a headlight is "
    "broken, and the car is safe to drive\" without asking, and that counts as a success. The customer had only "
    "said \"It still drives fine.\" This is a real Sam error that the metric did not catch.",
    "A's two task failures (P01-A, P10-A) are the only facts misses in the run. Both are on the same fact, "
    "drivable, and both followed A's fixed safe-to-drive question. Neither is a Sam error. If both had counted "
    "as successes, task success would be 10 against 10 and rule 1 would not fire. Rule 2 would then pick B on "
    "estimated time (813 s against 1026 s, 21% less, with CSAT 4.4 against 4.2). That time is modelled, not "
    "measured. So B stays the recommendation under the rule, but the evidence for it is weak.",
]


def _const(path, name, default):
    """Read a constant from a source file as text, so this script does not import the SDK."""
    m = re.search(rf'^{name} = "([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else default


SAM_MODEL = _const(PROTO / "agent" / "sam.py", "MODEL", "unknown")
SAM_EFFORT = _const(PROTO / "agent" / "sam.py", "EFFORT", "unknown")
CUSTOMER_MODEL = _const(PROTO / "harness" / "run_tests.py", "CUSTOMER_MODEL", "unknown")
JUDGE_MODEL = _const(PROTO / "harness" / "run_tests.py", "JUDGE_MODEL", "unknown")

SVG_STYLE = """<style>
.ab-text { fill: #18241f; font: 16px system-ui, Arial, sans-serif; }
.ab-title { font-size: 18px; font-weight: 700; }
.ab-value { font-size: 15px; }
.ab-muted { fill: #4d5d55; font: 12px system-ui, Arial, sans-serif; }
.ab-grid { stroke: #d3dbd5; stroke-width: 1; }
.ab-axis { stroke: #18241f; stroke-width: 1; }
.ab-line { stroke: #18241f; stroke-width: 2; }
.ab-mean { stroke: #18241f; stroke-width: 4; }
.ab-a { fill: #b88a00; }
.ab-b { fill: #3f6b5c; }
.ab-none { fill: #8a958f; }
@media (prefers-color-scheme: dark) {
  .ab-text { fill: #e5ece8; }
  .ab-muted { fill: #aebdb5; }
  .ab-grid { stroke: #2c3a34; }
  .ab-axis { stroke: #e5ece8; }
  .ab-line { stroke: #e5ece8; }
  .ab-mean { stroke: #e5ece8; }
  .ab-a { fill: #e3b731; }
  .ab-b { fill: #8cc2ae; }
  .ab-none { fill: #9aa7a0; }
}
</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def _svg(name, title, desc, height, body):
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {height}" width="100%" role="img" '
             f'aria-labelledby="{name}-t {name}-d">',
             f'<title id="{name}-t">{esc(title)}</title>',
             f'<desc id="{name}-d">{esc(desc)}</desc>',
             SVG_STYLE]
    lines += body
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _text(x, y, s, cls="ab-text"):
    return f'<text class="{cls}" x="{x}" y="{y}">{esc(s)}</text>'


def _title_elems(title, limit=48):
    """Chart title on one or more lines (about `limit` characters each). Returns (elements, extra height)."""
    lines, cur = [], ""
    for word in title.split():
        cand = f"{cur} {word}".strip()
        if len(cand) > limit and cur:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    lines.append(cur)
    return [_text(10, 26 + 22 * i, s, "ab-text ab-title") for i, s in enumerate(lines)], 22 * (len(lines) - 1)


def _class_for(label):
    if label.startswith("A "):
        return "ab-a"
    if label.startswith("B "):
        return "ab-b"
    return "ab-none"


def svg_bars(name, title, desc, items, max_value):
    """Horizontal bars. items = [(label, value, text)]. Value labels sit beside each bar."""
    row_h, x0, x1 = 44, 230, 450                       # x1 leaves room for the value label on a full bar
    title_el, extra = _title_elems(title)
    top = 50 + extra
    height = top + row_h * max(len(items), 1) + 16
    body = list(title_el)
    for i, (label, val, text) in enumerate(items):
        y = top + i * row_h
        body.append(_text(10, y + 19, label))
        if val is None or not max_value:
            body.append(_text(x0, y + 19, "no data yet", "ab-muted"))
            continue
        w = max(0.0, min(val / max_value, 1.0)) * (x1 - x0)
        body.append(f'<rect class="{_class_for(label)}" x="{x0}" y="{y + 4}" width="{w:.1f}" height="24" rx="2"/>')
        body.append(_text(round(x0 + w + 8, 1), y + 21, text, "ab-text ab-value"))
    body.append(f'<line class="ab-axis" x1="{x0}" y1="{top - 6}" x2="{x0}" y2="{height - 14}"/>')
    return _svg(name, title, desc, height, body)


def svg_dumbbell(name, title, desc, rows, unit):
    """One row per persona: A and B dots joined by a line. rows = [(label, a, b)]."""
    vals = [v for _l, a, b in rows for v in (a, b) if v is not None]
    maxv = (max(vals) * 1.1) if vals else 1
    x0, x1, row_h = 230, 380, 36                      # x1 leaves room for the value label after the dots
    title_el, extra = _title_elems(title)
    top = 56 + extra
    height = top + row_h * max(len(rows), 1) + 50

    def sx(v):
        return x0 + (v / maxv) * (x1 - x0)

    body = list(title_el)
    for t in (0, maxv / 2, maxv):
        body.append(f'<line class="ab-grid" x1="{sx(t):.1f}" y1="{top - 8}" x2="{sx(t):.1f}" '
                    f'y2="{height - 40}"/>')
        body.append(_text(round(sx(t) - 14, 1), height - 22, f"{t:.0f}", "ab-muted"))
    if not rows:
        body.append(_text(10, top + 20, "No completed pairs yet.", "ab-muted"))
    for i, (label, a, b) in enumerate(rows):
        y = top + i * row_h + 12
        body.append(_text(10, y + 5, label))
        if a is None or b is None:
            body.append(_text(x0, y + 5, "no data yet", "ab-muted"))
            continue
        body.append(f'<line class="ab-line" x1="{sx(a):.1f}" y1="{y}" x2="{sx(b):.1f}" y2="{y}"/>')
        body.append(f'<circle class="ab-a" cx="{sx(a):.1f}" cy="{y}" r="7"/>')
        body.append(f'<circle class="ab-b" cx="{sx(b):.1f}" cy="{y}" r="7"/>')
        body.append(_text(round(max(sx(a), sx(b)) + 12, 1), y + 5,
                          f"A {a:g} {unit} / B {b:g} {unit}", "ab-text ab-value"))
    return _svg(name, title, desc, height, body)


def svg_grouped(name, title, desc, groups, a_vals, b_vals):
    """Pairs of bars per group (A above B)."""
    vals = [v for v in a_vals + b_vals if v is not None]
    maxv = (max(vals) * 1.2) if vals else 1
    x0, x1, g_h = 260, 520, 74                        # wider label column for "Repeat questions (heuristic)"
    title_el, extra = _title_elems(title)
    top = 50 + extra
    height = top + g_h * max(len(groups), 1) + 10

    body = list(title_el)
    for i, g in enumerate(groups):
        y = top + i * g_h
        body.append(_text(10, y + 18, g))
        for j, (vals_, cls, tag) in enumerate(((a_vals, "ab-a", "A"), (b_vals, "ab-b", "B"))):
            v = vals_[i]
            yy = y + 4 + j * 28
            if v is None:
                body.append(_text(x0, yy + 16, "no data yet", "ab-muted"))
                continue
            w = (v / maxv) * (x1 - x0)
            body.append(f'<rect class="{cls}" x="{x0}" y="{yy}" width="{w:.1f}" height="22" rx="2"/>')
            body.append(_text(round(x0 + w + 8, 1), yy + 16, f"{tag} {v:.1f}", "ab-text ab-value"))
    body.append(f'<line class="ab-axis" x1="{x0}" y1="{top - 6}" x2="{x0}" y2="{height - 6}"/>')
    return _svg(name, title, desc, height, body)


def svg_strip(name, title, desc, a_vals, b_vals, lo, hi):
    """Dots per conversation on a lo-hi scale, with a mean tick per variant."""
    x0, x1 = 150, 600                                 # wider label column for "B story-first" at 16px
    rows_y = {"A": 110, "B": 185}

    def sx(v):
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)

    height = 268
    body = [_text(10, 26, title, "ab-text ab-title")]
    for k in range(lo, hi + 1):
        body.append(f'<line class="ab-grid" x1="{sx(k):.1f}" y1="70" x2="{sx(k):.1f}" y2="208"/>')
        body.append(_text(round(sx(k) - 4, 1), 226, str(k), "ab-muted"))
    for tag, vals, cls in (("A", a_vals, "ab-a"), ("B", b_vals, "ab-b")):
        y = rows_y[tag]
        body.append(_text(10, y + 5, f"{tag} {'form-first' if tag == 'A' else 'story-first'}"))
        nums = [v for v in vals if isinstance(v, (int, float))]
        if not nums:
            body.append(_text(x0 + 4, y + 5, "no data yet", "ab-muted"))
            continue
        for idx, v in enumerate(nums):
            dy = ((idx * 7) % 9 - 4) * 3
            body.append(f'<circle class="{cls}" cx="{sx(v):.1f}" cy="{y + dy}" r="5"/>')
        mean = sum(nums) / len(nums)
        body.append(f'<line class="ab-mean" x1="{sx(mean):.1f}" y1="{y - 20}" x2="{sx(mean):.1f}" y2="{y + 20}"/>')
        body.append(_text(round(sx(mean) - 30, 1), y - 26, f"mean {mean:.1f}", "ab-muted"))
    fmt_vals = lambda vals: ", ".join(f"{v:g}" for v in vals if isinstance(v, (int, float))) or "none yet"
    body.append(_text(10, 258, f"A values: {fmt_vals(a_vals)}. B values: {fmt_vals(b_vals)}.", "ab-muted"))
    return _svg(name, title, desc, height, body)


def load_inputs():
    personas = metrics.load_personas(ROOT / "personas.yaml")
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((OUT / "transcripts").glob("*.json"))]
    prefs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((OUT / "preferences").glob("*.json"))]
    return personas, recs, prefs


def write_text_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fmt(v, nd=1):
    if v is None or v == "":
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def pct(s):
    if s["n"] == 0:
        return "no data yet"
    return f"{fmt(s['task_success_rate'])}% ({s['successes']} of {s['n']})"


def make_charts(personas, rows, summary, pairs, prefs):
    a, b = summary["A"], summary["B"]
    by = {(r["persona_id"], r["variant"]): r for r in rows}
    charts = {}
    charts["success"] = svg_bars(
        "success", "Simulated: task success by variant (% of personas)",
        "Simulated pilot. Share of personas whose task succeeded, by variant.",
        [(f"A form-first (n={a['n']})", a["task_success_rate"], pct(a)),
         (f"B story-first (n={b['n']})", b["task_success_rate"], pct(b))], 100)
    time_rows = []
    for p in pairs:
        pid = p["persona_id"]
        time_rows.append((f"{pid} {personas[pid]['name']}",
                          by[(pid, "A")]["est_customer_seconds"], by[(pid, "B")]["est_customer_seconds"]))
    charts["time"] = svg_dumbbell(
        "time", "Simulated: estimated participant time per persona (seconds)",
        "Simulated pilot. Modelled reading and typing time per persona, A and B joined. Not measured.",
        time_rows, "s")
    groups = ["Sam turns", "Questions asked", "Repeat questions (heuristic)"]
    charts["effort"] = svg_grouped(
        "effort", "Simulated: Sam turns, questions and repeat questions (mean per conversation)",
        "Simulated pilot. Mean Sam turns, questions and repeat questions per conversation, by variant.",
        groups,
        [a["sam_turns"]["mean"], a["questions_asked"]["mean"], a["reasked_facts"]["mean"]],
        [b["sam_turns"]["mean"], b["questions_asked"]["mean"], b["reasked_facts"]["mean"]])
    charts["seq"] = svg_strip(
        "seq", "Simulated: ease rating, SEQ 1-7",
        "Simulated pilot. One dot per conversation; the tick is the mean. Scale 1 (very difficult) to 7 (very easy).",
        [r["seq"] for r in rows if r["variant"] == "A"],
        [r["seq"] for r in rows if r["variant"] == "B"], 1, 7)
    charts["csat"] = svg_strip(
        "csat", "Simulated: satisfaction, CSAT 1-5",
        "Simulated pilot. One dot per conversation; the tick is the mean. Scale 1 (very dissatisfied) to 5.",
        [r["csat"] for r in rows if r["variant"] == "A"],
        [r["csat"] for r in rows if r["variant"] == "B"], 1, 5)
    counts = Counter(p.get("preferred_variant") for p in prefs)
    charts["preference"] = svg_bars(
        "preference", "Simulated: which chat did personas prefer?",
        "Simulated pilot. Number of personas preferring each chat, from a simulated preference question.",
        [("A form-first", counts["A"], f"{counts['A']} of {len(prefs)}"),
         ("B story-first", counts["B"], f"{counts['B']} of {len(prefs)}"),
         ("No preference", counts["none"], f"{counts['none']} of {len(prefs)}")],
        max(len(prefs), 1))
    CHARTS.mkdir(parents=True, exist_ok=True)
    for name, svg in charts.items():
        write_text_atomic(CHARTS / f"{name}.svg", svg)
    return charts


def missing_prefs(summary, prefs):
    """Persona ids with both chats complete but no preference file (post-run note, PLAN-POST.md)."""
    have = {p.get("persona_id") for p in prefs}
    return [pid for pid in summary.get("paired_basis", {}).get("pair_ids", []) if pid not in have]


def summary_points(summary, prefs):
    a, b = summary["A"], summary["B"]
    if a["n"] == 0 and b["n"] == 0:
        return ["No simulated conversations yet. " + PENDING]

    def pair(key, nd=1):
        return f"A {fmt(summary['A'][key]['mean'], nd)}, B {fmt(summary['B'][key]['mean'], nd)}"

    counts = Counter(p.get("preferred_variant") for p in prefs)
    missing = missing_prefs(summary, prefs)
    miss_note = f"; no preference recorded for {', '.join(missing)}" if missing else ""
    return [
        f"Task success: A {pct(a)}; B {pct(b)}.",
        f"Estimated participant time (modelled from word counts, not measured), mean seconds: "
        f"{pair('est_customer_seconds')}.",
        f"Sam turns, mean: {pair('sam_turns')}. Questions asked, mean: {pair('questions_asked')}. "
        f"Repeat questions (keyword heuristic), mean: {pair('reasked_facts')}.",
        f"Ease, SEQ 1 to 7, mean: {pair('seq')}. Satisfaction, CSAT 1 to 5, mean: {pair('csat')}.",
        f"Preference: A {counts['A']}, B {counts['B']}, no preference {counts['none']} "
        f"(of {len(prefs)} personas{miss_note}).",
    ]


def direction_note(summary):
    ra, rb = summary["A"]["reasked_facts"]["mean"], summary["B"]["reasked_facts"]["mean"]
    ja, jb = summary["A"]["reasked_facts_judge"]["mean"], summary["B"]["reasked_facts_judge"]["mean"]
    if None in (ra, rb, ja, jb):
        return "Not enough judged conversations yet to compare the keyword heuristic with the judge."
    if ra == rb or ja == jb:
        return "The keyword heuristic and the judge do not yet show a clear difference in repeat questions."
    if (ra > rb) == (ja > jb):
        return "The keyword heuristic and the judge agree on which variant repeats more questions."
    return ("The keyword heuristic and the judge disagree on which variant repeats more questions. "
            "Treat the repeat-question result as unresolved.")


def build_blocks(personas, rows, summary, pairs, prefs, recommendation, generated):
    n = summary["complete_pairs"]
    complete = len(rows)
    variant, reason = recommendation
    line_a = (ROOT.parent / "02-prototype" / "agent" / "prompts" / "system_ab_form.md").read_text(
        encoding="utf-8").splitlines()[23]
    line_b = (ROOT.parent / "02-prototype" / "agent" / "prompts" / "system_ab_story.md").read_text(
        encoding="utf-8").splitlines()[23]
    capped = [r["conversation_id"] for r in rows if r["hit_turn_cap"] == 1]
    cap_note = (f"{len(capped)} conversation(s) reached the {TURN_CAP}-turn cap: {', '.join(capped)}. "
                "Their results are partial."
                if capped else f"No conversation reached the {TURN_CAP}-turn cap.")

    s1 = [("banner", BANNER),
          ("p", f"{complete} of {PLANNED} conversations complete. " + ("" if complete == PLANNED else PENDING))]

    s2 = [("h2", "Summary (simulated)"), ("ul", summary_points(summary, prefs)),
          ("box", "Recommendation (rule written before the run)",
           reason.replace(" (paired personas only).", f", out of {n} paired personas.") + " This simulated pilot tests the study design. It does not show how real people behave."
           + (POST_RUN_NOTE if complete == PLANNED else ""))]

    s3 = [("h2", "What we tested"),
          ("p", "One variable changes: how Sam captures the claim. Everything else stays the same: the same "
                "model, tools, policies, personas and questionnaire. Variant A (form-first) asks each detail one "
                "at a time, in a fixed order. Variant B (story-first) lets the customer tell it in their own words, "
                "then asks only for the gaps. B is the Project 1 design. A is the comparison, written for this test."),
          ("table", ["Variant A: form-first (line 24)", "Variant B: story-first (line 24)"], [[line_a, line_b]]),
          ("p", "Why A confirms rather than skips: a guided form gives every field its own turn. That is the "
                "strategy under test. So when A reaches a detail the customer already gave, it confirms it "
                "(\"You mentioned Logan Rd, Mount Gravatt. Is that right?\") instead of skipping it."),
          ("p", "Prompt files: `02-prototype/agent/prompts/system_ab_form.md` and "
                "`02-prototype/agent/prompts/system_ab_story.md`. Both are copies of `system_v1.md`; only line 24 "
                "differs.")]

    persona_rows = [[p["id"], p["name"], p["age"], p["digital_confidence"], p["emotional_state"],
                     p["incident_type"], p["order"]] for p in personas.values()]
    s4 = [("h2", "Method"),
          ("p", "**Hypothesis (written before the run, 28 October 2026):** story-first (B) needs fewer questions and less participant time "
                "than form-first (A), with equal or better task success. Form-first may capture facts more "
                "completely for vague or low-confidence personas."),
          ("h3", "Simulated participants"),
          ("p", "Ten LLM personas, all fictional. Each runs both variants. Ages 19 to 83; digital confidence "
                "5 high, 3 medium, 2 low."),
          ("table", ["ID", "Name", "Age", "Digital confidence", "State", "Incident", "Order"], persona_rows),
          ("p", "Counterbalancing: order AB means variant A runs first (5 personas), order BA means variant B runs "
                "first (5 personas). The order is fixed per persona, not randomised."),
          ("h3", "Models"),
          ("ul", [f"Sam: `{SAM_MODEL}` at {SAM_EFFORT} effort (sam.py).",
                  f"Simulated participants: `{CUSTOMER_MODEL}`.",
                  f"Judge: `{JUDGE_MODEL}`. It grades Sam only and is never told the variant."]),
          ("h3", "Metrics"),
          ("ul", ["Task success: a claim lodged with all key facts correct. For Helen Fraser (P08), a handoff or "
                  "callback also counts.",
                  "Facts correct: up to seven facts checked against the first successful create_claim call. "
                  "The driver is not checked when nobody was driving (P02, P04, P05 and P10), so those personas "
                  "have six.",
                  "Questions asked: question sentences in Sam's turns.",
                  "Repeat questions: keyword heuristic. Sam asks about a slot the customer already covered. The "
                  "judge's count is shown for cross-check.",
                  "Estimated participant time: word counts divided by the persona's reading and typing speed. "
                  "A model, not a measure.",
                  "SEQ (1-7) and CSAT (1-5): the simulated participant's answers after the chat."]),
          ("h3", "Decision rule (written before the run)"),
          ("p", "The same team wrote the plan, the prompts and this rule, and runs the test. The rule is fixed in "
                "`PLAN.md` before any full run. It is not registered with a third party."),
          ("p", "n is the number of personas with both variants complete. With fewer than 6, there is no "
                "recommendation. All four rules use only personas with both variants complete."),
          ("ul", ["If task success differs by 2 or more personas, recommend the higher.",
                  "Else, if mean estimated time differs by 15% or more (against the slower variant), and the faster "
                  "variant's mean CSAT is not lower by more than 0.5, recommend the faster.",
                  "Else, if one variant is preferred by at least 7 of 10 personas, recommend it.",
                  "Else: no clear winner. Keep the current design (B) and let the real study decide."])]

    chart_specs = [
        ("success", "Simulated: task success by variant (% of personas)",
         "Share of personas whose task succeeded, by variant.",
         ["Variant", "Task success"],
         [["A form-first", pct(summary["A"])], ["B story-first", pct(summary["B"])]]),
        ("time", "Simulated: estimated participant time per persona (seconds)",
         "Modelled reading and typing time per persona. A and B are joined by a line.",
         ["Persona", "A (s)", "B (s)"],
         [[f"{p['persona_id']} {personas[p['persona_id']]['name']}",
           fmt(next(r for r in rows if r["persona_id"] == p["persona_id"] and r["variant"] == "A")
               ["est_customer_seconds"]),
           fmt(next(r for r in rows if r["persona_id"] == p["persona_id"] and r["variant"] == "B")
               ["est_customer_seconds"])] for p in pairs] or [["no pairs yet", "", ""]]),
        ("effort", "Simulated: Sam turns, questions and repeat questions (mean per conversation)",
         "Means per conversation, by variant. Repeat questions use the keyword heuristic.",
         ["Measure", "A", "B"],
         [["Sam turns", fmt(summary["A"]["sam_turns"]["mean"]), fmt(summary["B"]["sam_turns"]["mean"])],
          ["Questions asked", fmt(summary["A"]["questions_asked"]["mean"]),
           fmt(summary["B"]["questions_asked"]["mean"])],
          ["Repeat questions (heuristic)", fmt(summary["A"]["reasked_facts"]["mean"]),
           fmt(summary["B"]["reasked_facts"]["mean"])]]),
        ("seq", "Simulated: ease rating, SEQ 1-7",
         "One dot per conversation. The tick is the mean.",
         ["Variant", "Mean SEQ", "n"],
         [["A form-first", fmt(summary["A"]["seq"]["mean"]), summary["A"]["seq"]["n"]],
          ["B story-first", fmt(summary["B"]["seq"]["mean"]), summary["B"]["seq"]["n"]]]),
        ("csat", "Simulated: satisfaction, CSAT 1-5",
         "One dot per conversation. The tick is the mean.",
         ["Variant", "Mean CSAT", "n"],
         [["A form-first", fmt(summary["A"]["csat"]["mean"]), summary["A"]["csat"]["n"]],
          ["B story-first", fmt(summary["B"]["csat"]["mean"]), summary["B"]["csat"]["n"]]]),
        ("preference", "Simulated: which chat did personas prefer?",
         "Number of personas preferring each chat in the simulated preference question.",
         ["Preference", "Personas"],
         [["A form-first", sum(1 for p in prefs if p.get("preferred_variant") == "A")],
          ["B story-first", sum(1 for p in prefs if p.get("preferred_variant") == "B")],
          ["No preference", sum(1 for p in prefs if p.get("preferred_variant") == "none")]]),
    ]
    captions = {
        "success": "Share of personas whose task succeeded, by variant.",
        "time": "Modelled reading and typing time per persona, from word counts. Not measured. "
                "Each row is one persona; A and B are joined.",
        "effort": "Mean Sam turns, questions and repeat questions per conversation. Repeat questions use a keyword "
                  "heuristic.",
        "seq": "SEQ ease rating per conversation (1 very difficult, 7 very easy). The tick is the mean.",
        "csat": "CSAT satisfaction per conversation (1 very dissatisfied, 5 very satisfied). The tick is the mean.",
        "preference": "Which chat each simulated persona said they would rather use.",
    }
    pending_note = f" {PENDING}" if complete < PLANNED else ""
    s5 = [("h2", "Results (simulated)"),
          ("p", f"All results are simulated. Complete pairs: {n} of 10 personas.{pending_note}")]
    for name, title, desc, headers, data in chart_specs:
        s5.append(("chart", name, title, captions[name], headers, data))

    conv_rows = []
    for r in rows:
        conv_rows.append([
            ("link", r["conversation_id"], f"results/simulated/transcripts/{r['conversation_id']}.md"),
            f"{r['persona_name']}", "A" if r["variant"] == "A" else "B",
            "yes" if r["task_success"] == 1 else "no",
            f"{r['facts_correct']}/{r['facts_checked']}", r["sam_turns"], r["questions_asked"],
            f"{r['reasked_facts']} / {fmt(r['reasked_facts_judge'], 0)}", fmt(r["est_customer_seconds"]),
            fmt(r["seq"], 0), fmt(r["csat"], 0)])
    s6 = [("h2", "Per conversation (simulated)"),
          ("p", "Repeat questions show the keyword heuristic first, then the judge's count. Each ID links to the "
                "transcript."),
          ("table", ["Conversation", "Persona", "Variant", "Success", "Facts", "Sam turns", "Questions",
                     "Repeats (heur. / judge)", "Est. seconds", "SEQ", "CSAT"], conv_rows or
           [["no conversations yet", "", "", "", "", "", "", "", "", "", ""]])]

    comments = {"A": [], "B": []}
    for r in rows:
        if r["comment"]:
            comments[r["variant"]].append(f"{r['persona_id']} {r['persona_name']} (variant {r['variant']}): "
                                          f"\"{r['comment']}\" (simulated)")
    s7 = [("h2", "What the simulated participants said (simulated)"),
          ("h3", "Form-first (A)"),
          ("ul", comments["A"] or ["No comments yet."]),
          ("h3", "Story-first (B)"),
          ("ul", comments["B"] or ["No comments yet."])]

    pref_gap = missing_prefs(summary, prefs)
    pref_note = ([f"Preferences were recorded for {len(prefs)} of {n} personas. None was recorded for "
                  f"{', '.join(pref_gap)}. The preference result is incomplete. Rule 3 was not reached, so it did "
                  "not change the recommendation."] if pref_gap and complete == PLANNED else [])
    s8 = [("h2", "Limitations"),
          ("ul", ["The participants are LLM personas, not people. They are simulated and cannot show real "
                  "confusion, distress or trust.",
                  "The same model family plays Sam, the participants and the judge. Their blind spots may match.",
                  "LLM raters tend to score chats positively. Read the ease and satisfaction scores as relative "
                  "only.",
                  "No memory between a persona's two chats, so order effects cannot appear here. Counterbalancing in "
                  "this pilot only rehearses the protocol.",
                  "The repeat-question count is a keyword heuristic. " + direction_note(summary),
                  "Estimated participant time is modelled from word counts, not measured.",
                  f"n = 10 simulated personas. Complete pairs: {n}. With n this small, a gap of 2 personas in "
                  "task success is small.",
                  cap_note,
                  "Form-first's prompt tells Sam to ask each detail in turn and to confirm details already given. So "
                  "some of A's extra questions and repeat questions are built into its prompt, not discovered by the "
                  "test. The test compares two prompt texts that carry two strategies. It does not isolate the "
                  "strategy from its wording.",
                  "Estimated time comes from word counts, so it rises with the length of Sam's messages. That is also "
                  "a prompt effect.",
                  "The repeat-question heuristic uses broad keywords such as 'today', 'saturday' and 'night'. For vague "
                  "personas (P05, P09), a fair follow-up for a precise time counts as a repeat. This penalises "
                  "story-first's gap questions more, so it works against the hypothesis. Compare with the judge's "
                  "count."] + (POST_RUN_LIMITS if complete == PLANNED else []) + pref_note),
          ("p", "Decision rule, as applied: " + reason)]

    s9 = [("h2", "Next: the real study"),
          ("p", "This pilot tests the study design. It does not show how real people behave. The real study uses "
                "8 to 10 people, the same two variants and two task cards. Read the kit at "
                "[real-study-kit/README.md](real-study-kit/README.md). Confirm the result with the real study before "
                "changing the design."),
          ("p", "Changes after the simulated pilot are recorded in the kit's README once the run is complete.")]

    s10 = [("h2", "Data and files"),
           ("p", f"Generated {generated} by build_report.py. Data source: simulated. Files: "
                 "[ab_results.csv](results/simulated/ab_results.csv), [ab_results.json](results/simulated/ab_results.json), "
                 "[ab_preferences.csv](results/simulated/ab_preferences.csv).")]

    return [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]


def inline_html(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t


def cell_html(c):
    if isinstance(c, tuple) and c[0] == "link":
        return f'<a href="{esc(c[2])}">{esc(c[1])}</a>'
    return esc(c)


def cell_md(c):
    if isinstance(c, tuple) and c[0] == "link":
        return f"[{c[1]}]({c[2]})"
    return str(c).replace("|", "/")


def block_html(b):
    kind = b[0]
    if kind == "h2":
        return f"<h2>{esc(b[1])}</h2>"
    if kind == "h3":
        return f"<h3>{esc(b[1])}</h3>"
    if kind == "p":
        return f"<p>{inline_html(b[1])}</p>"
    if kind == "ul":
        return "<ul>" + "".join(f"<li>{inline_html(i)}</li>" for i in b[1]) + "</ul>"
    if kind == "banner":
        return f'<div class="banner" role="note"><p>{esc(b[1])}</p></div>'
    if kind == "box":
        return f'<div class="box"><h3>{esc(b[1])}</h3><p>{esc(b[2])}</p></div>'
    if kind == "table":
        head = "".join(f"<th>{esc(h)}</th>" for h in b[1])
        body = "".join("<tr>" + "".join(f"<td>{cell_html(c)}</td>" for c in r) + "</tr>" for r in b[2])
        return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if kind == "chart":
        _k, name, title, caption, headers, data = b
        svg = (CHARTS / f"{name}.svg").read_text(encoding="utf-8")
        svg = svg.replace(' xmlns="http://www.w3.org/2000/svg"', "", 1)
        table = block_html(("table", headers, data))
        return (f'<figure id="chart-{name}"><div class="chart-scroll">\n{svg}</div>'
                f'<figcaption>{esc(caption)}</figcaption></figure>\n'
                f'<details><summary>Data for this chart</summary>{table}</details>')
    raise ValueError(kind)


def block_md(b):
    kind = b[0]
    if kind == "h2":
        return f"## {b[1]}\n"
    if kind == "h3":
        return f"### {b[1]}\n"
    if kind == "p":
        return f"{b[1]}\n"
    if kind == "ul":
        return "\n".join(f"- {i}" for i in b[1]) + "\n"
    if kind == "banner":
        return f"> **{b[1]}**\n"
    if kind == "box":
        return f"> **{b[1]}** {b[2]}\n"
    if kind == "table":
        head = "| " + " | ".join(str(h).replace("|", "/") for h in b[1]) + " |"
        sep = "|" + "|".join("---" for _ in b[1]) + "|"
        rows = ["| " + " | ".join(cell_md(c) for c in r) + " |" for r in b[2]]
        return "\n".join([head, sep] + rows) + "\n"
    if kind == "chart":
        _k, name, title, caption, headers, data = b
        return f"![{title}](charts/{name}.svg)\n\n*{caption}*\n\n" + block_md(("table", headers, data))
    raise ValueError(kind)


HTML_HEAD = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Story-first vs form-first</title>
<style>
:root {
  --bg: #f7f9f6; --fg: #18241f; --muted: #4d5d55; --line: #d3dbd5; --link: #2a5a4b;
  --code-bg: #e9efeb; --box-bg: #eef5f1; --banner-bg: #ffe08a; --banner-fg: #1d1500; --banner-line: #7a5c00;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #101815; --fg: #e5ece8; --muted: #aebdb5; --line: #2c3a34; --link: #8cc2ae;
    --code-bg: #202e28; --box-bg: #1a2a24; --banner-bg: #5c4a00; --banner-fg: #fff6d6; --banner-line: #e3b731;
  }
}
:root[data-theme="dark"] {
  --bg: #101815; --fg: #e5ece8; --muted: #aebdb5; --line: #2c3a34; --link: #8cc2ae;
  --code-bg: #202e28; --box-bg: #1a2a24; --banner-bg: #5c4a00; --banner-fg: #fff6d6; --banner-line: #e3b731;
}
body { margin: 0; background: #f7f9f6; background: var(--bg); color: var(--fg);
  font: 16px/1.55 system-ui, Arial, sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 16px; box-sizing: border-box; }
h1 { font-size: 1.6rem; line-height: 1.25; }
h2 { font-size: 1.25rem; margin-top: 2.2rem; padding-top: 1rem; border-top: 1px solid var(--line); }
h3 { font-size: 1.05rem; margin-top: 1.4rem; }
a { color: var(--link); }
code { background: var(--code-bg); padding: 0 .25em; border-radius: 3px; font-size: .92em; word-break: break-word; }
.banner { background: var(--banner-bg); color: var(--banner-fg); border: 2px solid var(--banner-line);
  border-radius: 6px; padding: 12px 14px; font-weight: 700; }
.banner p { margin: 0; }
.box { background: var(--box-bg); border-left: 4px solid var(--link); padding: 10px 14px; border-radius: 4px; }
.box h3 { margin: 0 0 .3rem; }
.box p { margin: 0; }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .92rem; }
th, td { border-bottom: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
figure { margin: 1.2rem 0 .4rem; }
figure svg { display: block; width: 100%; height: auto; max-width: 640px; }
.chart-scroll { overflow-x: auto; }
.chart-scroll svg { min-width: 520px; }
figcaption { color: var(--muted); font-size: .92rem; }
details { margin: .3rem 0 1rem; }
summary { cursor: pointer; color: var(--link); }
footer { color: var(--muted); font-size: .9rem; }
</style>
</head>
<body>
<main>
"""


def build_html(title, sections):
    parts = [HTML_HEAD, f"<h1>{esc(title)}</h1>"]
    for i, blocks in enumerate(sections, 1):
        parts.append(f'<section id="s{i}" data-section="{i}">')
        parts += [block_html(b) for b in blocks]
        parts.append("</section>")
    parts.append("</main>\n</body>\n</html>\n")
    return "\n".join(parts)


def build_md(title, sections):
    out = ["<!-- Generated by build_report.py. Edit the template there, not this file. -->", f"# {title}", ""]
    for blocks in sections:
        out += [block_md(b) for b in blocks]
    out += ["## How to reproduce", "",
            "Run from `03-usability-ab/`:", "",
            "```",
            "python run_ab.py --all --parallel 2   # resumable: re-run the same command after an interruption",
            "python build_report.py",
            "python test_metrics.py",
            "```", "",
            "Links: [report.html](report.html) (the same content on one page) and "
            "[real-study-kit/README.md](real-study-kit/README.md) (the real study).", "",
            "## Files", "",
            "| File | What |", "|---|---|",
            "| `personas.yaml` | The 10 simulated personas (fictional) |",
            "| `ab_policies.json` | 12 fictional policies, merged into the tools at runtime |",
            "| `metrics.py` | Pure metric functions and the decision rule (no SDK import) |",
            "| `run_ab.py` | Runs the simulated conversations, judge and preferences |",
            "| `build_report.py` | Writes the CSV, JSON, charts, this README and `report.html` |",
            "| `test_metrics.py`, `tests/fixture_P01-A.json` | Offline tests for metrics.py |",
            "| `chat_variant.py` | Terminal chat for the real study (blind to the variant) |",
            "| `real-study-kit/` | The ready-to-run kit for 8 to 10 real participants |",
            "| `../02-prototype/agent/prompts/system_ab_story.md` | Variant B prompt (story-first) |",
            "| `../02-prototype/agent/prompts/system_ab_form.md` | Variant A prompt (form-first) |",
            "| `results/simulated/` | Simulated run outputs: transcripts, preferences, CSV, JSON |",
            "| `charts/*.svg` | The six charts |", "",
            "Portfolio exercise. Simulated data only. Not research with real people.", ""]
    return "\n".join(out)


def main():
    personas, recs, prefs = load_inputs()
    rows = []
    for rec in recs:
        persona = personas.get(rec.get("persona_id"))
        if persona is not None:
            rows.append(metrics.conversation_row(rec, persona))
    rows.sort(key=lambda r: r["conversation_id"])
    prefs.sort(key=lambda p: p.get("persona_id", ""))
    OUT.mkdir(parents=True, exist_ok=True)

    summary = metrics.summarise(rows)
    pairs = metrics.paired(rows)
    recommendation = metrics.recommend(summary, prefs)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    # CSV and JSON data (UTF-8 with BOM, flat, snake_case)
    with (OUT / "ab_results.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=metrics.CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    pref_rows = [{"persona_id": p.get("persona_id", ""),
                  "persona_name": personas[p["persona_id"]]["name"] if p.get("persona_id") in personas else "",
                  "data_source": "simulated", "chat1_variant": p.get("chat1_variant", ""),
                  "chat2_variant": p.get("chat2_variant", ""), "preferred_variant": p.get("preferred_variant", ""),
                  "reason": p.get("reason", "")} for p in prefs]
    with (OUT / "ab_preferences.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=PREF_COLUMNS)
        w.writeheader()
        w.writerows(pref_rows)
    results_json = {
        "data_source": "simulated", "label": LABEL, "generated_at": generated,
        "conversations_complete": len(rows), "conversations_planned": PLANNED,
        "summary": summary, "paired": pairs,
        "recommendation": {"variant": recommendation[0], "reason": recommendation[1]},
        "rows": rows, "preferences": prefs,
    }
    write_text_atomic(OUT / "ab_results.json", json.dumps(results_json, indent=2, ensure_ascii=False))

    charts = make_charts(personas, rows, summary, pairs, prefs)  # noqa: F841 (files written)

    title = "Project 3: story-first vs form-first (simulated pilot)"
    sections = build_blocks(personas, rows, summary, pairs, prefs, recommendation, generated)
    write_text_atomic(ROOT / "report.html", build_html(title, sections))
    write_text_atomic(ROOT / "README.md", build_md(title, sections))
    print(f"Built report: {len(rows)} of {PLANNED} conversations complete (simulated). "
          f"Recommendation: {recommendation[0] or 'none'}.")


if __name__ == "__main__":
    main()
