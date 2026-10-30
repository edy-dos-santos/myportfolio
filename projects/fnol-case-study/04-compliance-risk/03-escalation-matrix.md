# Escalation matrix: revised triggers and gap table

This revises section 6 of [02-conversation-flows.md](../01-design/02-conversation-flows.md) and the handoff payload in [06-nlu-and-handoff-spec.md](../01-design/06-nlu-and-handoff-spec.md). Project 1 files are not edited. The changes are proposed here, for the Conversation Design Lead and the Privacy Officer to approve. Rows T01 to T08 keep the original triggers. Rows T09 to T15 are new. Turn references such as EM05 or ES03 point to simulated v1 test conversations.

Priority: **1** is immediate and overrides the flow. **2** is offered now, at the next turn. **3** is a note for the consultant.

## Revised trigger matrix

| ID | Trigger | Detected by | Sam says / does | Tool and `handoff_reason` | Payload flags | Priority | Risk IDs |
|----|---------|-------------|-----------------|---------------------------|---------------|----------|----------|
| T01 | Anyone hurt, in danger, or unsure | N02 answer, or injury words anywhere (flows section 6) | "000 first", then a callback. Stop claim capture. | `handoff_to_human` (injury), or `request_callback` if they would rather be called | `injury: yes` | 1 | R05, R11 |
| T02 | Customer asks for a person | "agent", "human", "real person", "call me" (flows section 6) | Honour at once. One sentence on what is saved. No "are you sure?". | `handoff_to_human` (customer_request) | none | 1 | R11, R04 |
| T03 | Complaint or dissatisfaction | "not happy", "complain", "ridiculous", "useless" (flows section 6). Dissatisfaction aimed at the chatbot counts (AD05). | Acknowledge without defending. Log the complaint, then offer a person. | `log_complaint` (proposed, C15) and `handoff_to_human` (complaint) | `complaint: yes` | 2 | R06 |
| T04 | Vulnerability cues | Family violence, financial hardship, disability, language difficulty, severe distress (flows section 6) | Empathy level 3. Offer a person. Keep to the minimum detail. Ask about safe contact (ES04). | `handoff_to_human` (vulnerability), or a callback | `vulnerability: yes`; `contact_preferences` (proposed) | 2 | R04, R08 |
| T05 | Third party claiming against a customer | Disambiguation W (flows section 5) | Third-party team. No policyholder data shared. | `handoff_to_human` (third_party) | none | 2 | R07, R15 |
| T06 | Three no-matches on one node | Error flow (flows section 3) | Offer a person and keep the draft. | `handoff_to_human` (no_match) | none | 2 | R11, R13 |
| T07 | Question needing a decision or advice | Digression table, "decision or advice" column (flows section 4) | Say who decides and when. Offer a person if they want one now. | Offer `handoff_to_human` (advice_needed) | none | 2 | R02, R19 |
| T08 | Possible fraud signals | Back-end rules only (flows section 6) | No change to the conversation. Never accuse. | Back-end flag only. No tool call in the chat. | back-end flag only | 3 | R16, R10 |
| T09 | New: two digressions in a row on cover or money, or confusion about cover | Digression count (flows section 4 rule) | Offer a person. | Offer `handoff_to_human` (advice_needed) | none | 2 | R01, R02 |
| T10 | New: tool or system failure (E03 to E05), or Sam cannot proceed | Tool error response (flows section 3) | Say so plainly. Never invent a number. Offer a callback or a person. | `request_callback`, or `handoff_to_human` (system_error) | `system_error: yes` (proposed) | 2 | R03, R11, R17 |
| T11 | New: handoff itself fails, or no one is available (out of hours) | `handoff_to_human` error, or no agent available | Book a callback with the summary. Tell the customer plainly when to expect contact. | `request_callback` with summary | `callback_pending: yes` (proposed) | 2 | R11, R17 |
| T12 | New: legal question or threatened legal action (AD07) | Words such as "sue" or "lawyer" | Offer a person (advice needed). Suggest independent legal advice, in general terms. No legal advice. | Offer `handoff_to_human` (advice_needed) | none | 2 | R01, R02 |
| T13 | New: customer asks to change a material fact (date, driver, damage) to something they have said is untrue (AD03) | Request to change a fact that the tools or earlier answers contradict | Record the true account. No accusation. No comment on cover. | No handoff needed. Neutral note in `create_claim` flags. | `disputed_fact_note` (proposed) | 3 | R12, R10, R16 |
| T14 | New: limited English or communication difficulty | Short broken replies, or a request for another language (ES05) | Offer an interpreter service or a person. | `handoff_to_human` (vulnerability), or `request_callback`. No interpreter route in v1. | `interpreter_needed`, `language_preference` (proposed) | 2 | R13, R04 |
| T15 | New: customer believes their cover is different from the record (EM05: "I thought I had comprehensive?") | Customer says the cover on the record is not what they expected | Note it in the claim flags. The consultant reviews it. Sam does not decide cover. | No handoff. Note in `create_claim` flags. If they express dissatisfaction, apply T03. | `cover_query: yes` (proposed) | 3 | R01, R06 |

## Payload changes (proposed, for 06-nlu-and-handoff-spec.md)

- **`contact_preferences`**: safe channels and times. Needed for ES04 and T04. Gap G05.
- **`complaint_id`**: links a handoff to a logged complaint. Needs `log_complaint` (C15).
- **`language_preference` and `interpreter_needed`**: for T14. Gap G05.
- **`prompt_version` and `model_version`**: stamped on each claim and handoff record (C27). Gap G05.
- **`other`**: add to the documented reason list. It exists in the `handoff_to_human` enum in `tools.py` but not in the spec.
- **`system_error`**: the spec already lists it as a reason. Add it as a path in the flows for T10 and T11 (gap G04).

## Gap table

Each gap was checked against the file it cites.

| Gap ID | Where (file + section) | Gap | Risk | Proposed fix | Control |
|--------|------------------------|-----|------|--------------|---------|
| G01 | `02-prototype/agent/prompts/system_v1.md`, "When to hand over to a person" | Advice or decision questions (flows section 4, T07) and the two-digressions rule (T09) are not in the list | R02, R01 | Add both triggers to the list | C05 |
| G02 | `system_v1.md`, "Questions off the main path"; `tools.py` | No way to record a complaint if the customer declines a person. Script H02 in [03-dialogue-scripts.md](../01-design/03-dialogue-scripts.md) says "I've recorded your concerns as a complaint", which v1 cannot do. That is a risk of a misleading statement. | R06, R01 | Add `log_complaint` to `tools.py`. Change H02 until it exists. | C15 |
| G03 | `tools.py`, `handoff_to_human` | Always succeeds. No failure path or out-of-hours fallback is designed or tested. | R11 | Add a failure response, a `request_callback` fallback and an out-of-hours message (T11) | C20 |
| G04 | [02-conversation-flows.md](../01-design/02-conversation-flows.md), section 6 | No row for system errors, although `system_error` is a handoff reason | R03, R11 | Add a system-error row (T10) | C20 |
| G05 | [06-nlu-and-handoff-spec.md](../01-design/06-nlu-and-handoff-spec.md), "Handoff payload" | No safe-contact preferences, language or interpreter fields, and no prompt or model version | R04, R14 | Add the fields in "Payload changes" above | C16, C27 |
| G06 | [02-conversation-flows.md](../01-design/02-conversation-flows.md), section 6, against scenario AD03 | The matrix says fraud is "back-end rules only". AD03 expects a neutral flag from the conversation. | R16, R10 | Resolve with T13: a neutral note in the claim flags, no accusation | C23 |
| G07 | `system_v1.md`, greeting (flow step 1) | No privacy collection notice | R08 | Add a notice to the greeting with a link to the privacy policy. Text approved by the Privacy Officer. | C17 |
| G08 | [03-dialogue-scripts.md](../01-design/03-dialogue-scripts.md), script D01; `system_v1.md`, "Questions off the main path" (excess) | The excess-waiver line is given for every policy, including policies where the record does not state a waiver condition (EM05) | R01 | Give the waiver line only when the record states a waiver condition. Otherwise say the consultant confirms. | C02 |
| G09 | `02-prototype/agent/tools.py`, `ToolState.guards`; `sam.py` version table | The `require_verified` guard exists but is off in v1 (the v1 guards are empty) | R07, R15 | Turn it on for v1, or test with it on before v2 | C07 |
| G10 | `system_v1.md`, "How you talk" and step 8 (read back a summary) | Vulnerability details may be read back to the customer in the summary (EM05 turn 6). The spec says flags are for the consultant only. | R08, R04 | Add a rule: keep vulnerability and hardship notes out of read-backs | C16 |

> This document is a portfolio exercise, not legal advice. References should be checked against current versions.
