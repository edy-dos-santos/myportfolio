# Controls catalogue

The catalogue lists the 30 controls used in the [risk register](01-risk-register.md). Status is kept honest. A control is **In v1** only when the v1 prompt, code or harness does it today. Controls marked **Proposed** are not built, and the register treats them as target controls for residual ratings only.

Layer: `prompt` means the system prompt in `02-prototype/agent/prompts/system_v1.md`; `code` means the Python code in `02-prototype/agent/` or `02-prototype/harness/`; `process` means a people or governance step.

| ID | Control | Type | Layer | Status | Risks | Owner role | Where (file or system) |
|----|---------|------|-------|--------|-------|------------|------------------------|
| C01 | "Never" rules in system prompt (cover, fault, advice, invented facts, sharing details) | Preventive | prompt | In v1 | R01, R02, R03, R07, R10, R16, R19 | Conversation Design Lead | `02-prototype/agent/prompts/system_v1.md`, "What you must never do" |
| C02 | Scripted digression limits D01-D06 ("can say / must not say") | Preventive | prompt | In v1 | R01, R02, R19 | Conversation Design Lead | `system_v1.md`, "Questions off the main path"; [02-conversation-flows.md](../01-design/02-conversation-flows.md) digression table |
| C03 | AI disclosure in greeting and whenever asked; never pose as human | Preventive | prompt | In v1 | R09 | Conversation Design Lead | `system_v1.md`, "Who you are" and flow step 1 |
| C04 | Safety-first question after greeting; 000 and stop capture on injury or doubt | Preventive | prompt | In v1 | R05 | Conversation Design Lead | `system_v1.md`, flow step 2 |
| C05 | Handoff triggers in system prompt (request, injury, complaint, vulnerability, third party, 3 misunderstandings) | Preventive / Corrective | prompt | In v1 | R02, R04, R05, R06, R09, R11, R18 | Conversation Design Lead | `system_v1.md`, "When to hand over to a person" |
| C06 | Facts only from tool results; claim and tow numbers generated only by tools | Preventive | prompt + code | In v1 | R03 | AI Platform Lead | `system_v1.md`, "What you must never do"; `02-prototype/agent/tools.py` |
| C07 | `require_verified` guard: `get_policy` and `create_claim` refuse unverified policy numbers | Preventive | code | Built, off in v1 (`state.guards`) | R07, R15 | AI Platform Lead | `02-prototype/agent/tools.py` (`ToolState.guards`); `sam.py` version table (v1 guards empty) |
| C08 | Structured handoff payload with fixed reason list, summary and flags | Corrective | code | In v1 (summary, reason, flags only) | R11 | AI Platform Lead | `tools.py`, `handoff_to_human`; [06-nlu-and-handoff-spec.md](../01-design/06-nlu-and-handoff-spec.md) |
| C09 | Tool-call log per conversation (tool, input, output) | Detective | code | In v1 (harness) | R03, R07, R14 | QA Lead | `02-prototype/harness/run_tests.py` (`tool_calls` in each transcript JSON) |
| C10 | 44-scenario regression harness with simulated customer, LLM judge and failure tags | Detective | code + process | In v1 | R03, R05, R09, R10, R17 | QA Lead | `02-prototype/harness/run_tests.py`, `harness/scenarios.yaml` |
| C11 | Outage injection in tests (`outages`) | Detective | code | In v1 | R03, R11 | QA Lead | `harness/scenarios.yaml` (`outages`); `tools.py` (`ToolState.outages`) |
| C12 | Output check before sending: block or rewrite over-promise and advice phrases ("you're covered", "approved", "you won't pay", "guarantee", "you should") | Preventive / Detective | code | Proposed | R01, R02, R10 | AI Platform Lead | Proposed: reply check in `02-prototype/agent/sam.py` (not built) |
| C13 | Grounding check: every amount, claim/tow number, date and place in Sam's reply must appear in tool output or customer text; else flag | Detective | code | Proposed | R01, R03, R12 | AI Platform Lead | Proposed: reply check in `sam.py` (not built) |
| C14 | Confirmation gate: `create_claim` refused unless the latest read-back was confirmed after the last change to any slot | Preventive | code | Proposed | R12 | AI Platform Lead | Proposed: `create_claim` in `tools.py` (not built) |
| C15 | Complaint capture: low-threshold complaint detection plus a `log_complaint` tool that records the complaint even if the customer declines a person | Preventive / Corrective | code + prompt | Proposed | R06 | IDR / Complaints Manager | Proposed: new `log_complaint` tool in `tools.py`; complaint wording in `system_v1.md` |
| C16 | Vulnerability handling: minimum-detail flag, safe-contact preferences in the payload, never read back to the customer | Preventive / Detective | code + prompt | Proposed | R04, R08 | Customer Vulnerability Lead | Proposed: payload fields in [06-nlu-and-handoff-spec.md](../01-design/06-nlu-and-handoff-spec.md); read-back rule in `system_v1.md` |
| C17 | Privacy collection notice in the greeting flow with a link to the privacy policy (text approved by Privacy Officer) | Preventive | prompt + process | Proposed | R08 | Privacy Officer | Proposed: greeting in `system_v1.md`; notice text approved by the Privacy Officer |
| C18 | Transcript redaction, access control and retention schedule; deletion on schedule | Preventive / Corrective | code + process | Proposed | R07, R08, R14 | Privacy Officer | Proposed: redaction in `harness/run_tests.py` output; retention schedule (process, not yet written) |
| C19 | Injection resistance: customer text treated as data; Sam has no tool that can approve, pay or edit a policy | Preventive | code + prompt | In v1 (no approve/pay tool exists); hardening Proposed | R10 | AI Platform Lead | `tools.py` (no approve, pay or edit tool); `system_v1.md` |
| C20 | Fallback path: if a tool, handoff or the model fails, offer a person or `request_callback`; never send the customer away empty-handed | Corrective | prompt + code | Proposed (E03-E05 cover some cases) | R03, R04, R05, R11, R13, R17 | Claims Operations Manager | [02-conversation-flows.md](../01-design/02-conversation-flows.md) section 3 (E03-E05); `system_v1.md`, "When things go wrong" |
| C21 | Sampled conversation review using the checklist ([04-review-checklist.md](04-review-checklist.md)) | Detective | process | Proposed | all | QA Lead | [04-review-checklist.md](04-review-checklist.md) |
| C22 | Release gate: full regression run before any prompt, model or vendor change; zero critical findings to ship | Preventive | process | Proposed | R17 | AI Platform Lead | Process (release checklist, not yet written) |
| C23 | Fraud-flag governance: back-end only, no change to conversation, human decision, periodic fairness review of flag outcomes | Preventive / Detective | process | Proposed | R10, R16 | Claims Integrity Manager | Process; flags sent with `create_claim` in `tools.py` |
| C24 | Language and accessibility support: plain-English level, offer interpreter or person, accessible chat UI | Preventive | prompt + process | Proposed | R13 | Conversation Design Lead | `system_v1.md`, "How you talk"; interpreter route (process) |
| C25 | Monitoring dashboard: escalation rate by trigger, over-promise rate, complaint capture, handoff failures, repeat-story rate (Power BI) | Detective | process | Proposed | R04, R06, R11, R13, R17, R19 | Compliance Manager | Power BI dashboard (not built) |
| C26 | Incident and remediation: correct the record, contact the customer, log the breach review | Corrective | process | Proposed | R01, R02, R03, R04, R06, R07, R08, R10, R12, R15, R16, R19 | Compliance Manager | Process (incident procedure, not yet written) |
| C27 | Model and prompt version pinning, change log, version stamped on each claim and handoff record, vendor assessment | Preventive / Corrective | code + process | Proposed (model IDs pinned in harness only) | R14, R17 | AI Platform Lead | Model IDs in `02-prototype/agent/sam.py` and `harness/run_tests.py`; change log and claim-record field not yet built |
| C28 | Date and fact sanity checks (E01 future / over 12 months; E06 contradiction asked once) | Preventive | prompt | In v1 (date resolution in prompt); E01/E06 checks Proposed for prompt | R12 | Conversation Design Lead | `system_v1.md`, "Resolve relative dates"; [02-conversation-flows.md](../01-design/02-conversation-flows.md) section 3 (E01, E06) |
| C29 | Third-party route: no policyholder data shared; collect only claimant name, contact and incident | Preventive | prompt + code | In v1 (prompt rule); code check Proposed | R07, R15 | Privacy Officer | `system_v1.md`, "When to hand over" (third party); `tools.py` (code check Proposed) |
| C30 | Scope list: what Sam does and where other requests go (claim status, policy changes) | Preventive | prompt | Proposed | R18 | Conversation Design Lead | Proposed: scope list in `system_v1.md` (none yet) |

## Proposed changes to Project 1 and 2

These are proposals only. Project 1 and Project 2 files are not edited. Each item names the Proposed controls it would carry.

**`01-design/02-conversation-flows.md`**

- Section 3: add the E01 and E06 checks to the prompt (C28).
- Section 4: keep the two-digressions rule and add it to the prompt (C05, see gap G01).
- Section 6: add rows for T09 to T15 and a system-error row (C20, gaps G04 and G06). See [03-escalation-matrix.md](03-escalation-matrix.md).

**`01-design/03-dialogue-scripts.md`**

- Script D01: give the excess-waiver line only when the policy record states a waiver condition (C02, gap G08).
- Script H02: change "I've recorded your concerns as a complaint" until a complaint tool exists (C15, gap G02).

**`01-design/06-nlu-and-handoff-spec.md`**

- Payload: add the six fields and the `other` reason note (C16, C27). See [03-escalation-matrix.md](03-escalation-matrix.md).

**`02-prototype/agent/prompts/system_v1.md`**

- "When to hand over": add advice or decision questions and the two-digressions rule (C05, gap G01).
- Greeting: add the privacy collection notice (C17, gap G07).
- Read-back step: keep vulnerability notes out of read-backs (C16, gap G10).
- Add a scope list (C30) and plain-English and one-question-per-turn wording (C24).
- Add a date and fact sanity rule (C28).

**`02-prototype/agent/tools.py`**

- Add a `log_complaint` tool (C15, gap G02).
- Add a failure response and out-of-hours fallback to `handoff_to_human` (C20, gap G03).
- Turn the `require_verified` guard on for v1, or test it before v2 (C07, gap G09).
- Add a confirmation gate to `create_claim` (C14), a version field (C27) and a fixed vocabulary for flags (C23).

**`02-prototype/agent/sam.py`**

- Add a reply check for over-promise, advice and grounding (C12, C13).
- Stamp the model and prompt version on each claim and handoff (C27).

**`02-prototype/harness/scenarios.yaml` and `run_tests.py`**

- Add the regression scenario proposed in the [worked example](05-worked-example-EM05.md) (EM07). Not added.
- Add scenarios for T09 to T15 (C10).
- Add a release gate that runs the full set before any change (C22).

> This document is a portfolio exercise, not legal advice. References should be checked against current versions.
