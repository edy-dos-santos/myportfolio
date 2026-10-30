"""Offline tests for run_ab.py and chat_variant.py. No SDK call, no conversation, no network.

    python test_offline.py     # prints OK (n tests) or fails with an AssertionError

Importing run_ab and chat_variant starts no conversation. These tests never call run_conversation, judge,
preference, chat or any SDK client.
"""
import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import chat_variant
import run_ab

HERE = Path(__file__).resolve().parent
tests = 0


def check(label, got, want):
    global tests
    assert got == want, f"{label}: got {got!r}, want {want!r}"
    tests += 1


# ---- Issue 1: the session is saved and only "Session saved." is printed --------------------------

record = {"conversation_id": "R01-A", "persona_id": "R01", "variant": "A", "variant_name": "form_first",
          "data_source": "real", "card": "X", "transcript": [], "tool_calls": [], "handed_off": False}
out_dir = Path(tempfile.mkdtemp(prefix="fnol-ab-test-"))
try:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        saved = chat_variant.finish_session(record, out_dir=out_dir)
    check("finish_session prints only the line", buf.getvalue(), "Session saved.\n")
    check("finish_session saved file", (out_dir / "R01-A.json").exists(), True)
    check("finish_session returns path", saved, out_dir / "R01-A.json")
    saved_json = json.loads((out_dir / "R01-A.json").read_text(encoding="utf-8"))
    check("saved data_source", saved_json["data_source"], "real")
    log_lines = (out_dir / "session_log.txt").read_text(encoding="utf-8").splitlines()
    check("session_log line count", len(log_lines), 1)
    check("session_log fields", log_lines[0].split("\t")[1:], ["R01", "A", "R01-A.json"])
finally:
    shutil.rmtree(out_dir, ignore_errors=True)

source = (HERE / "chat_variant.py").read_text(encoding="utf-8")
check("chat_variant has no 'Session saved to' print", "Session saved to" in source, False)

# ---- Issue 3: the participant sees Sam's last message on a handoff -----------------------------

handoff = [{"role": "customer", "text": "I need a person.", "ms": 0},
           {"role": "sam", "text": "A person will join you now.", "tools": [], "ms": 900}]
msg = run_ab.questionnaire_message(handoff)
check("handoff message contains Sam's text", "A person will join you now." in msg, True)
check("handoff message ends with QUESTIONNAIRE_PROMPT", msg.endswith(run_ab.QUESTIONNAIRE_PROMPT), True)
check("handoff message starts with the lead-in", msg.startswith("Sam's last message to you was:"), True)

customer_last = [{"role": "sam", "text": "Is anyone hurt?", "tools": [], "ms": 500},
                 {"role": "customer", "text": "No.", "ms": 0}]
check("customer-last message is the prompt unchanged",
      run_ab.questionnaire_message(customer_last), run_ab.QUESTIONNAIRE_PROMPT)

# ---- Issue 7: --rerun clears the preferences of the personas that rerun ------------------------

check("stale P03-A rerun", run_ab.stale_preferences(["P03-A"], True), {"P03"})
check("stale P03-A, P03-B, P05-B rerun", run_ab.stale_preferences(["P03-A", "P03-B", "P05-B"], True),
      {"P03", "P05"})
check("stale no rerun", run_ab.stale_preferences(["P03-A"], False), set())

print(f"OK ({tests} tests)")
