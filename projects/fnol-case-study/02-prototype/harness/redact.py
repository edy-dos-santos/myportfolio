"""Replace real insurer names with "[another insurer]" in anything we publish.

    python harness/redact.py results/v1      # rewrites .md and .json files under the folder, in place
"""
import json, re, sys
from pathlib import Path

MASK = "[another insurer]"
# Match patterns only: these real insurer names are masked out of anything published, never shown.
NAMES = ["Suncorp", "Shannons", "Bingle", "Allianz", "Hollard", "Youi", "Budget Direct", "Real Insurance",
         "Woolworths Insurance", "Coles Insurance", "Kogan Insurance", "Huddle Insurance", "Zurich", "Chubb",
         "Lumley", "Elders Insurance", "Auto & General", "Australian Seniors", "Insurance Australia Group",
         "Virgin Car Insurance", "Virgin Money Insurance", "Apia", "ROLLiN'"]           # matched in any case
ACRONYMS = ["AAMI", "GIO", "NRMA", "CGU", "SGIO", "SGIC", "WFI", "IAG", "RACQ", "RACV", "RACT", "RAA", "RAC",
            "QBE", "AIG", "TIO", "Vero"]                                                # matched case-sensitively
_alt = lambda xs: "|".join(sorted(map(re.escape, xs), key=len, reverse=True))
PATTERN_NAMES = re.compile(rf"(?<!\w)({_alt(NAMES)})(?!\w)", re.I)
PATTERN_ACRO = re.compile(rf"(?<!\w)({_alt(ACRONYMS)})(?!\w)")


def redact_text(s):
    return PATTERN_ACRO.sub(MASK, PATTERN_NAMES.sub(MASK, s))


def redact_obj(o):
    if isinstance(o, str):
        return redact_text(o)
    if isinstance(o, list):
        return [redact_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: redact_obj(v) for k, v in o.items()}
    return o


def find(s):
    return PATTERN_NAMES.findall(s) + PATTERN_ACRO.findall(s)


def main(folder):
    changed = 0
    for path in sorted(Path(folder).rglob("*")):
        if not path.is_file() or path.suffix not in (".md", ".json"):
            continue
        text = path.read_text(encoding="utf-8")
        hits = len(find(text))
        if not hits:
            continue
        if path.suffix == ".md":
            new = redact_text(text)
        else:
            data = redact_obj(json.loads(text))
            if isinstance(data, dict):
                data["redacted"] = True
            new = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(new, encoding="utf-8")
        changed += 1
        print(f"{path}: {hits} name(s) masked")
    print(f"{changed} file(s) changed")


if __name__ == "__main__":
    main(sys.argv[1])
