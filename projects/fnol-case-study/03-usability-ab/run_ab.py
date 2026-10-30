"""Project 3 pilot: simulated participants chat with two variants of Sam, then a judge and a preference step.

    python run_ab.py --help
    python run_ab.py --only P01-A --parallel 1     # one conversation (smoke test)
    python run_ab.py --all --parallel 2            # every pending conversation (orchestrator)

Participants are SIMULATED (LLM personas, Claude Haiku). This is a pilot to de-risk the study design.
It is not user research. Each conversation starts 2 Claude Code processes, so keep --parallel at 2 or lower.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock, query

ROOT = Path(__file__).resolve().parent                 # 03-usability-ab
PROTO = ROOT.parent / "02-prototype"
sys.path.insert(0, str(PROTO / "agent"))
sys.path.insert(0, str(PROTO / "harness"))
import sam    # noqa: E402  (reused, not copied)
import tools  # noqa: E402
from run_tests import render, customer_reply, CUSTOMER_MODEL, JUDGE_MODEL  # noqa: E402
import metrics  # noqa: E402

OUT = ROOT / "results" / "simulated"
MAX_TURNS = 20                                         # form-first needs more turns than the harness's 14
WORKDIR = Path(tempfile.mkdtemp(prefix="fnol-ab-"))    # empty cwd so no project settings leak in
VARIANTS = {"A": {"key": "abA", "prompt": "system_ab_form.md", "name": "form_first"},
            "B": {"key": "abB", "prompt": "system_ab_story.md", "name": "story_first"}}
PERSONAS = metrics.load_personas(ROOT / "personas.yaml")
PERSONA_LIST = list(PERSONAS.values())

PARTICIPANT_PROMPT = """You are taking part in a usability study of an insurance claims chat assistant. You play the
person described below, as realistically as you can. Today is {today}.

Who you are and what happened:
{brief}

Rules:
- Write only your next chat message, as this person would type it. No narration, no quotes, no stage directions.
- When asked an open question such as "what happened?", answer the way your brief says.
- When asked a specific question, answer it. You may mention other facts if this person naturally would.
- If you are asked for something you already said, react as this person would, then answer.
- If asked something your brief doesn't cover, give a plausible answer that fits.
- Never say you are an AI, a simulation or a test participant.
- When the chat has reached its natural end (you have a claim number and have said goodbye, you've been told a
  person will call or is joining, or you would realistically leave), reply with exactly: [END]"""

QUESTIONNAIRE_PROMPT = """The chat is over. A researcher asks you three quick questions about the chat you just had.
Answer as the person you are playing, honestly, based only on how that chat felt to them.
1. Overall, how easy or difficult was it to report your claim? 1 = very difficult, 7 = very easy.
2. How satisfied are you with the chat? 1 = very dissatisfied, 5 = very satisfied.
3. In one or two sentences, in your own voice: what stood out?
Return only this JSON, nothing else: {"seq": <1-7>, "csat": <1-5>, "comment": "<text>"}"""

JUDGE_PROMPT = """You are reviewing a chat between a customer and "Sam", an AI claims assistant for a fictional
Australian car insurer. Grade Sam only. The customer was simulated.

Transcript (tool calls in [brackets]):
{transcript}

Count "reasked_facts": the number of times Sam asked for, or asked the customer to confirm, a fact the customer
had already clearly given earlier (date, time, place, driver, whether drivable, other party, police). Do not count
the single read-back summary before lodging.
Score "effort_score" 1-5 for how easy the chat was for the customer (5 = very low effort).
Score "tone_score" 1-5 against: calm, plain Australian English, empathy matched to the customer's state, one
question per turn, no "don't worry", no exclamation marks.
List "rule_breaks": any over-promise on cover/payment/fault, personal advice, privacy breach, invented numbers,
or failure to say it is an AI.

Return only JSON: {{"reasked_facts": <int>, "reasked_examples": ["<short quote>"], "effort_score": <1-5>,
"tone_score": <1-5>, "rule_breaks": [{{"rule": "<name>", "evidence": "<short quote>"}}], "summary": "<one sentence>"}}"""

PREFERENCE_PROMPT = """Earlier you had two chats with the claims assistant about the same incident. Here they are,
in the order you had them.

CHAT 1
{chat1}

CHAT 2
{chat2}

As the person you are playing: which chat would you rather use if this happened again?
Return only JSON: {{"preferred_chat": <1, 2, or 0 for no preference>, "reason": "<one or two sentences>"}}"""


def register():
    """Make the two variants and the 12 pilot policies known to sam and tools. Mutates shared objects in place."""
    for v in VARIANTS.values():
        sam.VERSIONS[v["key"]] = {"prompt": v["prompt"], "guards": {}}   # same guards as v1
    extra = json.loads((ROOT / "ab_policies.json").read_text(encoding="utf-8"))["policies"]
    tools.POLICIES.update(extra)


register()


def load_personas():
    """All personas from personas.yaml, in file order."""
    return list(metrics.load_personas(ROOT / "personas.yaml").values())


def conversation_ids(personas):
    """(conversation_id, persona, variant, order_position) in run order, persona by persona."""
    out = []
    for p in personas:
        run_order = ["A", "B"] if p["order"] == "AB" else ["B", "A"]
        for pos, v in enumerate(run_order, 1):
            out.append((f"{p['id']}-{v}", p, v, pos))
    return out


def questionnaire_message(transcript):
    """The questionnaire message. If Sam had the last word, the participant is shown it first (round 2, issue 3)."""
    if transcript and transcript[-1]["role"] == "sam":
        return ("Sam's last message to you was:\n\n" + transcript[-1]["text"] + "\n\nThe chat has ended there.\n\n"
                + QUESTIONNAIRE_PROMPT)
    return QUESTIONNAIRE_PROMPT


def stale_preferences(todo_ids, rerun):
    """Persona ids whose preference file is out of date when these conversations rerun (round 2, issue 7)."""
    if not rerun:
        return set()
    return {cid.split("-")[0] for cid in todo_ids}


def parse_json(text):
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def write_json(path, obj):
    """Write via a .tmp file and os.replace, so no half-written files are left behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def clamp_questionnaire(q):
    if q is None:
        return None
    try:
        return {"seq": min(7, max(1, int(q["seq"]))), "csat": min(5, max(1, int(q["csat"]))),
                "comment": str(q.get("comment", ""))}
    except (KeyError, TypeError, ValueError):
        return {"error": f"bad questionnaire: {json.dumps(q)[:200]}"}


async def _query_text(prompt, opts):
    text = ""
    async for m in query(prompt=prompt, options=opts):
        if isinstance(m, AssistantMessage):
            text += "".join(b.text for b in m.content if isinstance(b, TextBlock))
    return text.strip()


def participant_system(persona):
    return PARTICIPANT_PROMPT.format(today=tools.DATA["today"], brief=persona["brief"].strip())


async def run_conversation(persona, variant):
    """Run one simulated conversation. Returns the conversation record (PLAN 7.4)."""
    v = VARIANTS[variant]
    state = tools.ToolState()
    opening = persona["opening"].strip()
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.perf_counter()
    transcript = [{"role": "customer", "text": opening, "ms": 0}]
    hit_cap = False
    cust_opts = ClaudeAgentOptions(system_prompt=participant_system(persona), model=CUSTOMER_MODEL,
                                   tools=[], setting_sources=[], max_turns=1, cwd=str(WORKDIR))
    async with ClaudeSDKClient(options=sam.build_options(v["key"], state, WORKDIR)) as sam_client, \
            ClaudeSDKClient(options=cust_opts) as cust:
        await cust.query(f"(The chat is starting. Your opening message was: {opening}) "
                         "Reply OK and wait for the assistant.")
        async for _ in cust.receive_response():
            pass
        for _ in range(MAX_TURNS):
            seen = len(state.calls)
            t = time.perf_counter()
            reply, _ = await sam.ask(sam_client, transcript[-1]["text"])
            transcript.append({"role": "sam", "text": reply, "tools": state.calls[seen:],
                               "ms": int((time.perf_counter() - t) * 1000)})
            if state.handed_off:
                break
            t = time.perf_counter()
            nxt = await customer_reply(cust, reply)
            ms = int((time.perf_counter() - t) * 1000)
            if not nxt and len(transcript) < 4:
                raise RuntimeError("simulated customer gave no reply; conversation not valid")
            if not nxt or "[END]" in nxt:
                break
            transcript.append({"role": "customer", "text": nxt, "ms": ms})
        else:
            hit_cap = True

        # Questionnaire, still inside the sessions: the simulated participant answers three questions.
        q_text = await customer_reply(cust, questionnaire_message(transcript))
        q = parse_json(q_text)
        if q is None:
            q_text = await customer_reply(cust, "Reply with only the JSON object.")
            q = parse_json(q_text)
        questionnaire = clamp_questionnaire(q) if q is not None else {"error": q_text[:200]}

    return {
        "conversation_id": f"{persona['id']}-{variant}", "persona_id": persona["id"],
        "variant": variant, "variant_name": v["name"], "sam_version": v["key"],
        "order_position": 1 if persona["order"][0] == variant else 2, "data_source": "simulated",
        "sam_model": sam.MODEL, "customer_model": CUSTOMER_MODEL, "started_at": started,
        "elapsed_seconds": round(time.perf_counter() - t0, 1), "hit_turn_cap": hit_cap,
        "transcript": transcript, "tool_calls": state.calls, "handed_off": state.handed_off,
        "questionnaire": questionnaire,
    }


async def judge(record):
    """LLM judge grades Sam only. It is never told the variant."""
    prompt = JUDGE_PROMPT.format(transcript=render(record["transcript"]))
    opts = ClaudeAgentOptions(model=JUDGE_MODEL, effort="medium", tools=[], setting_sources=[],
                              max_turns=1, cwd=str(WORKDIR))
    text = await _query_text(prompt, opts)
    parsed = parse_json(text)
    return parsed if parsed is not None else {"error": text[:200]}


async def preference(persona, rec1, rec2):
    """Ask the simulated participant which of its two chats it prefers. Returns the saved dict or None."""
    recs = sorted([rec1, rec2], key=lambda r: r["order_position"])

    def chat(r):
        return render(r["transcript"], with_tools=False).replace("CUSTOMER:", "YOU:")

    prompt = PREFERENCE_PROMPT.format(chat1=chat(recs[0]), chat2=chat(recs[1]))
    opts = ClaudeAgentOptions(system_prompt=participant_system(persona), model=CUSTOMER_MODEL,
                              tools=[], setting_sources=[], max_turns=1, cwd=str(WORKDIR))
    parsed = parse_json(await _query_text(prompt, opts))
    if parsed is None:
        return None                                    # no file written, so a rerun asks again
    try:
        pref = int(parsed.get("preferred_chat", 0))
    except (TypeError, ValueError):
        pref = 0
    letter = {1: recs[0]["variant"], 2: recs[1]["variant"]}.get(pref, "none")
    return {"persona_id": persona["id"], "data_source": "simulated",
            "chat1_variant": recs[0]["variant"], "chat2_variant": recs[1]["variant"],
            "preferred_variant": letter, "reason": str(parsed.get("reason", ""))}


def save(record):
    persona = PERSONAS[record["persona_id"]]
    write_json(OUT / "transcripts" / f"{record['conversation_id']}.json", record)
    md = (f"> SIMULATED participant (LLM persona). Not a real person.\n\n"
          f"# {record['conversation_id']}: {persona['name']}, variant {record['variant']} "
          f"({record['variant_name']})\n\n```\n{render(record['transcript'])}\n```\n")
    tmp = OUT / "transcripts" / f"{record['conversation_id']}.md.tmp"
    tmp.write_text(md, encoding="utf-8")
    os.replace(tmp, OUT / "transcripts" / f"{record['conversation_id']}.md")


async def run_one(persona, variant, sem, use_judge):
    cid = f"{persona['id']}-{variant}"
    async with sem:
        try:
            record = await run_conversation(persona, variant)
            if use_judge:
                record["judge"] = await judge(record)
        except Exception as e:  # keep the batch going; nothing is saved, so a rerun retries it
            print(f"{cid} ERROR {e!r}")
            return
        save(record)
        row = metrics.conversation_row(record, persona)
        print(f"{cid} done: lodged={row['lodged']} facts={row['facts_correct']}/{row['facts_checked']} "
              f"sam_turns={row['sam_turns']} seq={row['seq']} csat={row['csat']}")


def load_record(cid):
    p = OUT / "transcripts" / f"{cid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


async def main():
    ap = argparse.ArgumentParser(
        description="Run simulated participants through two variants of Sam (Project 3 pilot). "
                    "Participants are simulated LLM personas, not real people.")
    ap.add_argument("--all", action="store_true", help="run every pending conversation (20). Full run.")
    ap.add_argument("--only", default="", help="conversation ids or persona ids, comma separated, e.g. P01-A,P03")
    ap.add_argument("--parallel", type=int, default=2,
                    help="conversations at once. Default 2. Values above 2 are capped at 2.")
    ap.add_argument("--no-judge", action="store_true", help="skip the judge")
    ap.add_argument("--rerun", action="store_true", help="ignore existing results for the selected ids")
    ap.add_argument("--no-report", action="store_true", help="don't rebuild the report at the end")
    args = ap.parse_args()

    if not args.all and not args.only:
        ap.print_usage()
        print("Nothing selected. Use --only P01-A for one conversation, or --all for the full run.")
        sys.exit(2)

    all_ids = conversation_ids(PERSONA_LIST)
    if args.all:
        chosen = all_ids
    else:
        wanted = [t.strip().upper() for t in args.only.split(",") if t.strip()]
        known = {cid for cid, *_ in all_ids}
        personas_known = set(PERSONAS)
        bad = [t for t in wanted if t not in known and t not in personas_known]
        if bad:
            print(f"Unknown id(s): {', '.join(bad)}")
            sys.exit(2)
        chosen = [x for x in all_ids if x[0] in wanted or x[1]["id"] in wanted]

    parallel = args.parallel
    if parallel > 2:
        print(f"WARNING: --parallel {parallel} capped at 2 (each conversation runs 2 Claude Code processes).")
        parallel = 2
    parallel = max(1, parallel)
    use_judge = not args.no_judge

    (OUT / "transcripts").mkdir(parents=True, exist_ok=True)
    (OUT / "preferences").mkdir(parents=True, exist_ok=True)

    todo = []
    for cid, persona, variant, _pos in chosen:
        if not args.rerun and (OUT / "transcripts" / f"{cid}.json").exists():
            print(f"{cid} skipped (already done; use --rerun to redo)")
            continue
        todo.append((persona, variant))

    # --rerun: a preference is about the two chats, so drop it when either chat is redone (round 2, issue 7).
    todo_ids = [f"{persona['id']}-{variant}" for persona, variant in todo]
    for pid in sorted(stale_preferences(todo_ids, args.rerun)):
        pref_path = OUT / "preferences" / f"{pid}.json"
        if pref_path.exists():
            pref_path.unlink()
            print(f"{pid} preference: removed (rerun)")

    print(f"Running {len(todo)} conversation(s), up to {parallel} at once (simulated participants)")
    sem = asyncio.Semaphore(parallel)
    if todo:
        await asyncio.gather(*(run_one(p, v, sem, use_judge) for p, v in todo))

    # Back-fill the judge for selected records saved without one.
    if use_judge:
        for cid, _p, _v, _pos in chosen:
            rec = load_record(cid)
            if rec is None or "judge" in rec:
                continue
            print(f"{cid} judging (back-fill)")
            rec["judge"] = await judge(rec)
            save(rec)

    # Preferences: one per persona with both transcripts and no preference file yet.
    seen_personas = set()
    for _c, persona, _v, _pos in chosen:
        pid = persona["id"]
        if pid in seen_personas:
            continue
        seen_personas.add(pid)
        pref_path = OUT / "preferences" / f"{pid}.json"
        if pref_path.exists():
            continue
        recs = [load_record(f"{pid}-A"), load_record(f"{pid}-B")]
        if not all(recs):
            continue
        result = await preference(persona, recs[0], recs[1])
        if result is None:
            print(f"{pid} preference: no parsable answer; will retry on the next run")
            continue
        write_json(pref_path, result)
        print(f"{pid} preference: {result['preferred_variant']}")

    if not args.no_report:
        import build_report  # noqa: E402
        build_report.main()


if __name__ == "__main__":
    asyncio.run(main())
