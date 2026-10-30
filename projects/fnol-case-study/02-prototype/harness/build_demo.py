"""Build demo/index.html: the template plus Sam's v2 prompt, mock data and every saved test result.

    python harness/build_demo.py
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "harness"))
from sam import system_prompt  # noqa: E402
from tools import DATA  # noqa: E402
from checks import passed  # noqa: E402
from redact import find, redact_obj  # noqa: E402

expect = {s["id"]: redact_obj(s["expect"]) for s in yaml.safe_load((ROOT / "harness" / "scenarios.yaml").read_text(encoding="utf-8"))}


def load(version):
    d = ROOT / "results" / version
    if not (d / "summary.json").exists():
        return None
    items = []
    for p in sorted((d / "transcripts").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        fails = r["judge"].get("failures", [])
        items.append(redact_obj({
            "id": r["id"], "title": r["title"], "category": r["category"], "expect": expect.get(r["id"], ""),
            "pass": passed(r),
            "failures": [{k: f.get(k) for k in ("tag", "severity", "turn", "why")} for f in fails],
            "auto": r["auto_check_failures"], "waived": r.get("checks_waived", []),
            "task": r["judge"].get("task_score"), "tone": r["judge"].get("tone_score"),
            "summary": r["judge"].get("summary"), "transcript": r["transcript"]}))
    return {"summary": json.loads((d / "summary.json").read_text(encoding="utf-8")), "items": items}


data = {"prompt": system_prompt("v2"), "mock": DATA,
        "results": {v: r for v in ("v1", "v2") if (r := load(v))}}
results_text = json.dumps(data["results"], ensure_ascii=False)
assert not find(results_text), f"insurer name left in demo data: {find(results_text)}"
print(f"masked insurer names in results: {results_text.count('[another insurer]')}")
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (ROOT / "demo" / "template.html").read_text(encoding="utf-8").replace("__DATA__", blob)
(ROOT / "demo" / "index.html").write_text(html, encoding="utf-8")
print(f"demo/index.html: {len(html) // 1024} KB, versions: {list(data['results'])}")
