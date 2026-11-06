"""Terminal chat for the real study. One participant, one variant, one session.

    python chat_variant.py --participant R01 --variant A [--card X]
    python chat_variant.py --help

The participant sees only "Sam:" and "You:". The variant letter and prompt name are never printed,
so the participant is blind to the variant. Each session is saved to results/real/<participant>-<variant>.json
(the PLAN 7.4 schema, with data_source "real"). The questionnaire is on paper, so there is no questionnaire here.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "02-prototype" / "agent"))
import sam    # noqa: E402
import tools  # noqa: E402
from run_ab import VARIANTS, WORKDIR, register  # noqa: E402

REAL_DIR = ROOT / "results" / "real"
register()


def session_path(participant, variant):
    return REAL_DIR / f"{participant}-{variant}.json"


def save_session(record, out_dir=None):
    base = Path(out_dir) if out_dir else REAL_DIR
    path = base / f"{record['persona_id']}-{record['variant']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path


def finish_session(record, out_dir=None):
    """Save the session and log it for the moderator. Prints only 'Session saved.' (the participant can see the screen)."""
    path = save_session(record, out_dir)
    log = path.parent / "session_log.txt"
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{stamp}\t{record['persona_id']}\t{record['variant']}\t{path.name}\n")
    print("Session saved.")
    return path


async def chat(participant, variant, card):
    state = tools.ToolState()
    v = VARIANTS[variant]
    transcript = []
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.perf_counter()
    try:
        async with ClaudeSDKClient(options=sam.build_options(v["key"], state, WORKDIR)) as client:
            # Clears the screen so the typed command (which names the variant) is not visible to the participant.
            # The command is a fixed string with no user input.
            os.system("cls" if os.name == "nt" else "clear")
            print("Chat with Sam. Type 'quit' to end the chat.\n")
            shown_at = time.perf_counter()              # when the "You:" prompt is shown (start-up not counted)
            while True:
                text = input("You: ").strip()
                participant_ms = int((time.perf_counter() - shown_at) * 1000)
                if text.lower() == "quit":
                    break
                if not text:
                    continue
                transcript.append({"role": "customer", "text": text, "ms": participant_ms})
                seen = len(state.calls)
                t = time.perf_counter()
                await client.query(text)
                reply = []
                async for m in client.receive_response():
                    if isinstance(m, AssistantMessage):
                        reply += [b.text for b in m.content if isinstance(b, TextBlock)]
                    elif isinstance(m, ResultMessage) and m.is_error:
                        reply.append(f"[agent error: {m.subtype}]")
                reply_text = "\n\n".join(reply).strip()
                transcript.append({"role": "sam", "text": reply_text, "tools": state.calls[seen:],
                                   "ms": int((time.perf_counter() - t) * 1000)})
                print(f"Sam: {reply_text}\n")
                if state.handed_off:
                    print("(The chat has been passed to a person. The session ends here.)\n")
                    break
                shown_at = time.perf_counter()
    except Exception:
        print("Sorry, the chat stopped. Please tell the researcher.")
    finally:
        record = {
            "conversation_id": f"{participant}-{variant}", "persona_id": participant,
            "variant": variant, "variant_name": v["name"], "sam_version": v["key"],
            "order_position": None,                     # from the kit's counterbalancing table
            "data_source": "real", "card": card,
            "sam_model": sam.MODEL, "customer_model": "human participant",
            "started_at": started, "elapsed_seconds": round(time.perf_counter() - t0, 1),
            "hit_turn_cap": False, "transcript": transcript, "tool_calls": state.calls,
            "handed_off": state.handed_off,
        }
        finish_session(record)
    return record


def main():
    ap = argparse.ArgumentParser(
        description="Terminal chat for the real study. The participant sees only Sam and You, never the variant. "
                    "Saves the session to results/real/.")
    ap.add_argument("--participant", required=True, help="participant id, e.g. R01")
    ap.add_argument("--variant", required=True, choices=sorted(VARIANTS), help="A (form-first) or B (story-first)")
    ap.add_argument("--card", choices=["X", "Y"], default=None, help="task card the participant is using")
    args = ap.parse_args()

    if not re.fullmatch(r"R\d{2}", args.participant):
        ap.error("participant id must look like R01")
    if session_path(args.participant, args.variant).exists():
        ap.error("a session file for this participant and variant already exists. "
                 "Move or delete it first, so no session is overwritten.")

    asyncio.run(chat(args.participant, args.variant, args.card))


if __name__ == "__main__":
    main()
