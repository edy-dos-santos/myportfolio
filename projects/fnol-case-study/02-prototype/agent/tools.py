"""Tool stubs for Sam. They stand in for the insurer's systems and record every call.

Each conversation gets its own ToolState, so tests can inject outages and inspect
what Sam did (which tools it called, with what, and in what order).

The v2 guards (sam.VERSIONS["v2"]["guards"]) add prepare_claim, a gated create_claim, log_complaint,
extra handoff fields and a strict identity check. With guards = {} the tools are exactly the v1 tools.
"""
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

DATA = json.loads((Path(__file__).parent / "mock_data.json").read_text(encoding="utf-8"))
POLICIES = DATA["policies"]

SERVER = "fnol"
TOOL_NAMES = ["verify_identity", "get_policy", "prepare_claim", "create_claim", "book_tow",
              "request_callback", "handoff_to_human", "log_complaint"]
ALLOWED = [f"mcp__{SERVER}__{n}" for n in TOOL_NAMES]


@dataclass
class ToolState:
    outages: list = field(default_factory=list)   # tool names that fail, e.g. ["create_claim"]
    guards: dict = field(default_factory=dict)    # code-level guardrails, switched on per agent version
    calls: list = field(default_factory=list)     # [{"tool", "input", "output"}]
    verified: set = field(default_factory=set)    # policy numbers verified in this conversation
    handed_off: bool = False
    seq: int = field(default_factory=lambda: random.randint(20480, 20999))
    turn: int = 0                                   # customer messages seen so far (set by sam.ask)
    last_customer_text: str = ""                    # latest customer message (set by sam.ask)
    drafts: list = field(default_factory=list)      # prepare_claim drafts: {"draft_id", "turn", "fields"}
    id_mismatch: set = field(default_factory=set)   # strict_identity: policies given a wrong dob or mobile


CLAIM_PROPS = {  # the create_claim properties (v1 schema, unchanged)
    "policy_number": {"type": "string"}, "vehicle_rego": {"type": "string"},
    "incident_type": {"type": "string", "enum": ["collision", "parked_hit", "single_vehicle", "theft",
                                                 "storm", "vandalism", "windscreen", "other"]},
    "date_time": {"type": "string"}, "location": {"type": "string"},
    "description": {"type": "string", "description": "The customer's account, in their words where possible"},
    "drivable": {"type": "string", "enum": ["yes", "no", "unsure"]}, "driver": {"type": "string"},
    "other_party": {"type": "string"}, "police_ref": {"type": "string"},
    "flags": {"type": "array", "items": {"type": "string"}}}
CLAIM_REQUIRED = ["policy_number", "incident_type", "date_time", "location", "description"]

READBACK = [("vehicle_rego", "Car (rego)"), ("incident_type", "Type of incident"), ("date_time", "When"),
            ("location", "Where"), ("description", "What happened"), ("drivable", "Can be driven safely"),
            ("driver", "Who was driving"), ("other_party", "Other party"), ("police_ref", "Police reference")]


def readback(fields):
    """Customer-facing summary. Flags are for the consultant only, so they are never shown (gap G10)."""
    return "\n".join(f"- {label}: {fields.get(k) or 'not given'}" for k, label in READBACK)


def _norm(s):
    return " ".join((s or "").lower().split())


def _text(obj):
    return {"content": [{"type": "text", "text": json.dumps(obj)}]}


def _digits(s):
    return re.sub(r"\D", "", s or "")


def build_tools(state: ToolState):
    g = state.guards

    def record(name, args, out):
        state.calls.append({"tool": name, "input": args, "output": out})
        return _text(out)

    def down(name, args):
        if name in state.outages:
            return record(name, args, {"error": "service_unavailable",
                                       "message": f"{name} is not responding. Try again later."})
        return None

    @tool("verify_identity",
          "Verify the customer's identity. Pass the policy number, OR date of birth (YYYY-MM-DD) "
          "plus mobile number. Returns whether they are verified and their policy number.",
          {"type": "object", "properties": {
              "policy_number": {"type": "string"},
              "dob": {"type": "string", "description": "YYYY-MM-DD"},
              "mobile": {"type": "string"}}})
    async def verify_identity(args):
        if (r := down("verify_identity", args)):
            return r
        pn = (args.get("policy_number") or "").upper().replace(" ", "")
        if pn in POLICIES:
            p = POLICIES[pn]
            if g.get("strict_identity"):  # v2: every factor given must match; a mismatch holds for this conversation
                dob, mobile = str(args.get("dob") or "").strip(), _digits(args.get("mobile"))
                if (dob and dob != p["dob"]) or (mobile and mobile != p["mobile"]):
                    state.id_mismatch.add(pn)
                if pn in state.id_mismatch and not (dob == p["dob"] and mobile == p["mobile"]):
                    state.verified.discard(pn)
                    return record("verify_identity", args, {"verified": False,
                                                            "message": "No match. Check the details and try again."})
            state.verified.add(pn)
            return record("verify_identity", args, {"verified": True, "policy_number": pn,
                                                    "first_name": p["first_name"]})
        for pn, p in POLICIES.items():
            if args.get("dob") == p["dob"] and _digits(args.get("mobile")) == p["mobile"]:
                state.verified.add(pn)
                return record("verify_identity", args, {"verified": True, "policy_number": pn,
                                                        "first_name": p["first_name"]})
        return record("verify_identity", args, {"verified": False,
                                                "message": "No match. Check the details and try again."})

    @tool("get_policy",
          "Get policy details: holder, policy type, vehicles, listed drivers, basic excess, hire car cover.",
          {"type": "object", "properties": {"policy_number": {"type": "string"}},
           "required": ["policy_number"]})
    async def get_policy(args):
        if (r := down("get_policy", args)):
            return r
        pn = (args.get("policy_number") or "").upper().replace(" ", "")
        if state.guards.get("require_verified") and pn not in state.verified:
            return record("get_policy", args, {"error": "not_verified",
                                               "message": "Verify identity before reading policy details."})
        if pn not in POLICIES:
            return record("get_policy", args, {"error": "not_found"})
        p = {k: v for k, v in POLICIES[pn].items() if k not in ("dob", "mobile")}
        return record("get_policy", args, {"policy_number": pn, **p})

    @tool("create_claim",
          "Lodge the claim once the customer has confirmed the summary. Returns a claim number.",
          {"type": "object", "properties": CLAIM_PROPS, "required": CLAIM_REQUIRED})
    async def create_claim(args):
        if (r := down("create_claim", args)):
            return r
        pn = (args.get("policy_number") or "").upper()
        if state.guards.get("require_verified") and pn not in state.verified:
            return record("create_claim", args, {"error": "not_verified"})
        state.seq += 1
        return record("create_claim", args, {"claim_number": f"WTL-{state.seq}", "status": "lodged",
                                             "consultant_contact": "within 1 business day"})

    # ---- v2: confirm_before_lodge ----
    @tool("prepare_claim",
          "Prepare the claim for the customer to check before lodging. Returns a draft_id and a read-back. "
          "Show the read-back to the customer and ask them to confirm it. If anything changes, call "
          "prepare_claim again with the corrected details.",
          {"type": "object", "properties": CLAIM_PROPS, "required": CLAIM_REQUIRED})
    async def prepare_claim(args):
        pn = (args.get("policy_number") or "").upper().replace(" ", "")
        if g.get("require_verified") and pn not in state.verified:
            return record("prepare_claim", args, {"error": "not_verified"})
        draft_id = f"D{len(state.drafts) + 1}"
        state.drafts.append({"draft_id": draft_id, "turn": state.turn, "fields": {**args, "policy_number": pn}})
        return record("prepare_claim", args, {
            "draft_id": draft_id, "readback": readback(args),
            "next": "Show this read-back to the customer and ask them to confirm it. Call create_claim only "
                    "after they confirm this latest version."})

    @tool("create_claim",
          "Lodge the claim after the customer has confirmed the latest read-back from prepare_claim. Pass its "
          "draft_id and the customer's confirming words, quoted from their latest message. Returns a claim number.",
          {"type": "object", "properties": {
              "draft_id": {"type": "string"},
              "customer_confirmation": {"type": "string",
                                        "description": "The customer's confirming words, quoted from their latest message"}},
           "required": ["draft_id", "customer_confirmation"]})
    async def create_claim_confirmed(args):
        if (r := down("create_claim", args)):
            return r
        latest = state.drafts[-1] if state.drafts else None
        if latest is None:
            return record("create_claim", args, {"error": "no_draft", "message":
                          "Call prepare_claim first, show the read-back, and wait for the customer to confirm."})
        if args.get("draft_id") != latest["draft_id"]:
            return record("create_claim", args, {"error": "stale_draft", "message":
                          f"The latest draft is {latest['draft_id']}. Show that read-back and get it confirmed."})
        if latest.get("claim_number"):  # already lodged: never create a second claim from one draft
            return record("create_claim", args, {"claim_number": latest["claim_number"], "status": "already_lodged"})
        if latest["turn"] >= state.turn:
            return record("create_claim", args, {"error": "not_confirmed", "message":
                          "The customer hasn't replied since this read-back was prepared. Show it and wait for them to confirm."})
        quote, said = _norm(args.get("customer_confirmation")), _norm(state.last_customer_text)
        # a fragment like "ok" lifted from a long reply isn't a confirmation: quote at least 12 characters
        # (or the whole message, if it's shorter)
        if not quote or quote not in said or len(quote) < min(len(said), 12):
            return record("create_claim", args, {"error": "not_confirmed", "message":
                          "Quote the customer's confirmation from their latest message."})
        fields = latest["fields"]
        if g.get("require_verified") and fields["policy_number"] not in state.verified:
            return record("create_claim", args, {"error": "not_verified"})
        state.seq += 1
        latest["claim_number"] = f"WTL-{state.seq}"
        return record("create_claim", {**args, "lodged": fields},
                      {"claim_number": f"WTL-{state.seq}", "status": "lodged",
                       "consultant_contact": "within 1 business day"})

    @tool("book_tow", "Book a tow truck to the car's location.",
          {"type": "object", "properties": {"location": {"type": "string"},
                                            "policy_number": {"type": "string"}},
           "required": ["location"]})
    async def book_tow(args):
        if (r := down("book_tow", args)):
            return r
        return record("book_tow", args, {"booking": f"TOW-{random.randint(7000, 7999)}", "eta_minutes": 45})

    # ---- v2: handoff_fields (extra optional fields only; handlers unchanged) ----
    callback_schema = {"type": "object", "properties": {"name": {"type": "string"}, "mobile": {"type": "string"},
                                                        "reason": {"type": "string"}, "summary": {"type": "string"}},
                       "required": ["mobile", "reason"]}
    handoff_schema = {"type": "object", "properties": {
        "reason": {"type": "string", "enum": ["customer_request", "injury", "complaint", "vulnerability",
                                              "no_match", "system_error", "third_party", "advice_needed",
                                              "other"]},
        "summary": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string"}}},
        "required": ["reason", "summary"]}
    if g.get("handoff_fields"):
        contact = {"type": "string", "description": "Safe ways and times to contact the customer, in their words"}
        callback_schema["properties"]["contact_preferences"] = contact
        handoff_schema["properties"]["contact_preferences"] = contact
        handoff_schema["properties"]["language"] = {"type": "string", "description": "Preferred language, if not English"}
        handoff_schema["properties"]["interpreter_needed"] = {"type": "boolean"}

    @tool("request_callback", "Book a call from a claims consultant.", callback_schema)
    async def request_callback(args):
        if (r := down("request_callback", args)):
            return r
        return record("request_callback", args, {"booked": True, "when": "within 1 business day"})

    @tool("handoff_to_human",
          "Transfer the chat to a person now. Include a summary so the customer doesn't repeat themselves.",
          handoff_schema)
    async def handoff_to_human(args):
        state.handed_off = True
        return record("handoff_to_human", args, {"transferred": True,
                                                 "message": "A team member is joining the chat."})

    # ---- v2: log_complaint ----
    @tool("log_complaint",
          "Record a complaint about Wattle's service, in the customer's words. Use it even if they don't want a person.",
          {"type": "object", "properties": {
              "summary": {"type": "string", "description": "What the customer is unhappy about, in their words"},
              "about": {"type": "string", "enum": ["previous_claim", "this_claim", "service", "other"]},
              "policy_number": {"type": "string"}},
           "required": ["summary"]})
    async def log_complaint(args):
        return record("log_complaint", args, {"logged": True, "complaint_ref": f"CMP-{random.randint(1000, 9999)}",
                                              "follow_up": "A complaints officer reviews every logged complaint and contacts the customer."})

    # v1 order is kept: verify_identity, get_policy, create_claim, book_tow, request_callback, handoff_to_human
    out = [verify_identity, get_policy]
    out += [prepare_claim, create_claim_confirmed] if g.get("confirm_before_lodge") else [create_claim]
    out += [book_tow, request_callback, handoff_to_human]
    if g.get("log_complaint"):
        out.append(log_complaint)
    return out


def build_server(state: ToolState):
    return create_sdk_mcp_server(SERVER, tools=build_tools(state))
