"""Offline tests for the tool stubs, the v2 guards, the automatic checks and redaction. No Claude calls.

    python harness/test_tools.py
"""
import asyncio
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "harness"))
import sam  # noqa: E402
from tools import ToolState, build_tools, readback  # noqa: E402
from checks import auto_checks, waived_checks  # noqa: E402
from redact import redact_obj, redact_text  # noqa: E402

V1_TOOLS = {"verify_identity", "get_policy", "create_claim", "book_tow", "request_callback", "handoff_to_human"}
V2_GUARDS = sam.VERSIONS["v2"]["guards"]
POLICY = "WTL456789"


def fresh(guards):
    state = ToolState()
    state.guards = guards
    return state, {t.name: t for t in build_tools(state)}


def call(tools, name, args):
    out = asyncio.run(tools[name].handler(args))
    return json.loads(out["content"][0]["text"])


def v2_with_verified():
    state, tools = fresh(dict(V2_GUARDS))
    state.verified.add(POLICY)
    return state, tools


CLAIM = {"policy_number": POLICY, "incident_type": "parked_hit", "date_time": "Tuesday 27 October, 4pm",
         "location": "Westfield Carindale car park", "description": "Reversed into my parked car."}


def test_v1_tool_set_and_behaviour():
    state, tools = fresh({})
    assert set(tools) == V1_TOOLS, sorted(tools)
    assert "prepare_claim" not in tools and "log_complaint" not in tools
    assert call(tools, "get_policy", {"policy_number": POLICY}).get("policy_number") == POLICY  # no verification
    out = call(tools, "create_claim", dict(CLAIM))
    assert out["claim_number"].startswith("WTL-"), out


def test_v1_schemas_have_no_handoff_fields():
    _, tools = fresh({})
    assert "contact_preferences" not in tools["handoff_to_human"].input_schema["properties"]
    assert "contact_preferences" not in tools["request_callback"].input_schema["properties"]


def test_v2_unverified_policy_read_refused():
    _, tools = fresh(dict(V2_GUARDS))
    assert call(tools, "get_policy", {"policy_number": POLICY})["error"] == "not_verified"


def test_v2_create_without_draft_refused():
    _, tools = v2_with_verified()
    out = call(tools, "create_claim", {"draft_id": "D1", "customer_confirmation": "yes"})
    assert out["error"] == "no_draft", out


def test_v2_prepare_then_create_same_turn_refused():
    state, tools = v2_with_verified()
    draft = call(tools, "prepare_claim", dict(CLAIM))
    out = call(tools, "create_claim", {"draft_id": draft["draft_id"], "customer_confirmation": "yes"})
    assert out["error"] == "not_confirmed", out


def test_v2_confirmed_draft_lodges():
    state, tools = v2_with_verified()
    state.turn = 1
    draft = call(tools, "prepare_claim", dict(CLAIM))
    assert draft["draft_id"] == "D1" and "Car (rego)" in draft["readback"]
    state.turn = 2
    state.last_customer_text = "Yes, that's all correct"
    out = call(tools, "create_claim", {"draft_id": "D1", "customer_confirmation": "yes, that's all correct"})
    assert out.get("claim_number", "").startswith("WTL-"), out
    assert "lodged" in state.calls[-1]["input"], state.calls[-1]


def test_v2_stale_draft_refused():
    state, tools = v2_with_verified()
    state.turn = 1
    call(tools, "prepare_claim", dict(CLAIM))
    call(tools, "prepare_claim", dict(CLAIM))
    state.turn = 2
    state.last_customer_text = "yes"
    out = call(tools, "create_claim", {"draft_id": "D1", "customer_confirmation": "yes"})
    assert out["error"] == "stale_draft", out


def test_v2_quote_not_in_latest_message_refused():
    state, tools = v2_with_verified()
    state.turn = 1
    call(tools, "prepare_claim", dict(CLAIM))
    state.turn = 2
    state.last_customer_text = "No, the date was wrong"
    out = call(tools, "create_claim", {"draft_id": "D1", "customer_confirmation": "yes that's all correct"})
    assert out["error"] == "not_confirmed", out


def test_v2_policy_number_alone_verifies():
    state, tools = fresh(dict(V2_GUARDS))
    assert call(tools, "verify_identity", {"policy_number": POLICY})["verified"] is True  # design N03
    assert POLICY in state.verified


def test_v2_wrong_dob_or_mobile_refused():
    for extra in ({"dob": "1988-03-14", "mobile": "0412 345 678"},   # AD06: both wrong
                  {"dob": "1988-03-14"}, {"mobile": "0412 345 678"},
                  {"dob": "1990-03-14", "mobile": "0412 345 678"}):  # dob right, mobile wrong
        state, tools = fresh(dict(V2_GUARDS))
        out = call(tools, "verify_identity", {"policy_number": POLICY, **extra})
        assert out["verified"] is False and "first_name" not in out, (extra, out)
        assert POLICY not in state.verified
        assert call(tools, "get_policy", {"policy_number": POLICY})["error"] == "not_verified"


def test_v2_mismatch_blocks_policy_number_alone_until_both_match():
    state, tools = fresh(dict(V2_GUARDS))
    call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1988-03-14"})
    assert call(tools, "verify_identity", {"policy_number": POLICY})["verified"] is False
    assert call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1990-03-14"})["verified"] is False
    out = call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1990-03-14", "mobile": "0412 000 111"})
    assert out["verified"] is True and POLICY in state.verified, out


def test_v2_mismatch_revokes_earlier_verification():
    state, tools = fresh(dict(V2_GUARDS))
    call(tools, "verify_identity", {"policy_number": POLICY})
    assert POLICY in state.verified
    assert call(tools, "verify_identity", {"policy_number": POLICY, "mobile": "0412 345 678"})["verified"] is False
    assert POLICY not in state.verified


def test_v1_identity_unchanged():
    state, tools = fresh({})
    out = call(tools, "verify_identity", {"policy_number": POLICY, "dob": "1988-03-14", "mobile": "0412 345 678"})
    assert out["verified"] is True and out["policy_number"] == POLICY, out
    assert not state.id_mismatch


def test_dob_and_mobile_without_policy_number_still_verify():
    for guards in ({}, dict(V2_GUARDS)):
        _, tools = fresh(guards)
        out = call(tools, "verify_identity", {"dob": "1990-03-14", "mobile": "0412 000 111"})
        assert out["verified"] is True and out["policy_number"] == POLICY, (guards, out)


def test_readback_not_given_and_no_flags():
    fields = {"incident_type": "collision", "date_time": "Monday", "location": "Logan Rd", "description": "Rear-ended",
              "flags": ["SECRET FLAG TEXT"]}
    text = readback(fields)
    assert "- Police reference: not given" in text, text
    assert "SECRET FLAG TEXT" not in text and "flags" not in text.lower()


def test_v2_complaint_and_handoff_fields():
    _, tools = v2_with_verified()
    out = call(tools, "log_complaint", {"summary": "Waited a month for a call back"})
    assert out["complaint_ref"].startswith("CMP-"), out
    assert "contact_preferences" in tools["handoff_to_human"].input_schema["properties"]
    assert "interpreter_needed" in tools["handoff_to_human"].input_schema["properties"]
    assert "contact_preferences" in tools["request_callback"].input_schema["properties"]


def test_auto_checks_waives_must_call_on_customer_request():
    sc = {"checks": {"must_call": ["create_claim"]}}
    calls = [{"tool": "handoff_to_human", "input": {"reason": "customer_request", "summary": "x"}, "output": {}}]
    assert auto_checks(sc, calls) == []
    assert len(waived_checks(sc, calls)) == 1


def test_auto_checks_never_waives_must_not_call():
    sc = {"checks": {"must_call": ["create_claim"], "must_not_call": ["get_policy"]}}
    calls = [{"tool": "handoff_to_human", "input": {"reason": "customer_request", "summary": "x"}, "output": {}},
             {"tool": "get_policy", "input": {}, "output": {}}]
    assert auto_checks(sc, calls), "must_not_call should still fail"


def test_auto_checks_no_waiver_without_customer_request():
    sc = {"checks": {"must_call": ["create_claim"]}}
    calls = [{"tool": "handoff_to_human", "input": {"reason": "injury", "summary": "x"}, "output": {}}]
    assert auto_checks(sc, calls) == ["expected a call to create_claim"]
    assert waived_checks(sc, calls) == []


def test_redaction_masks_names_and_keeps_places():
    assert redact_text("insurer possibly Hollard") == "insurer possibly [another insurer]"
    assert redact_text("Coles car park in Camp Hill") == "Coles car park in Camp Hill"
    assert "AAMI" not in redact_text("my AAMI policy") and "[another insurer]" in redact_text("my AAMI policy")
    nested = redact_obj({"a": ["Hollard", {"b": "rang AAMI today"}], "n": 3})
    assert nested == {"a": ["[another insurer]", {"b": "rang [another insurer] today"}], "n": 3}, nested


def test_ask_accepts_two_arguments_and_tracks_turns():
    params = inspect.signature(sam.ask).parameters
    assert list(params)[:2] == ["client", "text"] and params["state"].default is None
    inspect.signature(sam.ask).bind(object(), "hi")  # Project 3 calls it with two arguments

    class FakeClient:
        async def query(self, text):
            self.sent = text

        async def receive_response(self):
            return
            yield  # makes this an empty async generator

    state = ToolState()
    reply, tools = asyncio.run(sam.ask(FakeClient(), "hello", state))
    assert (reply, tools) == ("", []) and state.turn == 1 and state.last_customer_text == "hello"
    asyncio.run(sam.ask(FakeClient(), "again"))  # no state: nothing to track, no error


def test_versions_config():
    assert sam.VERSIONS["v1"]["guards"] == {}
    assert sam.VERSIONS["v1"]["prompt"] == "system_v1.md"
    assert set(V2_GUARDS) == {"require_verified", "confirm_before_lodge", "handoff_fields", "log_complaint",
                              "strict_identity"}


TESTS = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]


def main():
    for t in TESTS:
        t()
    print(f"all {len(TESTS)} tests passed")


if __name__ == "__main__":
    main()
