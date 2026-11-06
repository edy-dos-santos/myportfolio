# NLU and handoff spec

## Intents

| Intent | Example utterances | Notes |
|--------|--------------------|-------|
| `report_incident` | "I've had an accident", "someone hit my car", "need to make a claim", "my car got stolen" | Main entry |
| `injury_or_danger` | "my wife's hurt", "I hit my head", "there's smoke", "the other driver's yelling at me" | Global; overrides everything |
| `ask_excess` | "how much is my excess", "do I have to pay the excess" | Digression D01 |
| `ask_cover` | "am I covered", "will you pay for this" | D02 |
| `ask_fault` | "was it my fault", "do I admit fault" | D03 |
| `ask_hire_car` | "can I get a rental", "how will I get to work" | D04 |
| `ask_premium` | "will my premium go up" | D05 |
| `should_i_claim` | "is it worth claiming", "should I just pay myself" | D06, never advise |
| `request_human` | "agent", "real person", "call me", "this isn't working" | Global; honour at once |
| `complaint` | "I want to complain", "this is ridiculous", "you people are useless" | Global; RG 271-style recognition |
| `pause` | "can I finish later", "I have to go" | Save draft + resume link |
| `third_party` | "the other driver's insured with you", "your customer hit me" | Third-party route |
| `check_claim` | "what's happening with my claim" | Out of scope: route to claim status |

**Confidence rule:** below threshold on `injury_or_danger`, `complaint` or `request_human`, ask rather than ignore. A false positive costs one question; a false negative can cost much more.

## Entities and slots

| Slot | Entity type | Required to lodge | Validation | Confirm? |
|------|-------------|-------------------|------------|----------|
| `vehicle` | Policy vehicle (from `get_policy`) | Yes | Must match a car on the policy, or flag "not listed" | If inferred |
| `incident_type` | collision, parked_hit, single_vehicle, theft, storm, vandalism, windscreen, other | Yes | – | If inferred |
| `date_time` | Date + time window | Yes (date) | Not future; check if over 12 months | Always, as full date |
| `location` | Street + suburb, or GPS | Yes | Suburb present | In summary |
| `description` | Free text (customer's words kept verbatim) | Yes | – | In summary |
| `drivable` | yes / no / unsure | Yes | unsure = treat as no | – |
| `driver` | policyholder / listed driver / other | Yes | – | – |
| `other_party` | name, phone, rego, insurer | No | Partial accepted | In summary |
| `police_ref` | Reference number | No | – | – |
| `photos` | Files | No | – | – |

Minimum to save a draft: **name + mobile**. Minimum to lodge: the six required slots.

## Handoff payload

Sent with every escalation so the consultant starts where Sam stopped.

```json
{
  "handoff_reason": "customer_request | injury | complaint | vulnerability | no_match | system_error | third_party | advice_needed",
  "summary": "Rear-ended on M1 near Gateway merge, Wed 28 Oct ~8:10am. Boot won't close. Tow booked. Kids in car, not injured.",
  "customer_words": "just got rear ended on the M1 near the gateway merge. kids in the back. what do i do",
  "identity": { "status": "matched_by_mobile", "policy_id": "WTL456790" },
  "slots_filled": { "incident_type": "collision", "location": "M1, Gateway merge", "drivable": "no" },
  "slots_missing": ["other_party", "police_ref"],
  "flags": { "distress": "medium", "injury": "no", "vulnerability": false, "hit_and_run": false, "complaint": false },
  "actions_taken": ["book_tow: TOW-7781"],
  "claim_id": "WTL-20482",
  "transcript_url": "…"
}
```

Vulnerability flags are visible to the consultant only, never shown to the customer, and only with the minimum detail needed to help.

## Success metrics

| Metric | Target (hypothesis) | Why it matters |
|--------|---------------------|----------------|
| FNOL completion rate (lodged or saved draft) | 85%+ | Core task success |
| Median time to lodge | Under 6 minutes | Effort |
| Questions asked per claim | 6 or fewer | Tests story-first extraction |
| "Repeat yourself" rate after handoff | Under 10% | Tests handoff payload |
| Appropriate escalation rate (sampled review) | 95%+ of injury, complaint and vulnerability cases escalated | Safety and compliance |
| Over-promise rate (sampled review) | 0 | Statements on cover, fault or payment |
| CSAT after lodging | 4.2 / 5+ | Experience |

Containment is deliberately **not** a primary metric: an assistant that keeps distressed or complaining customers away from people is failing, even if the numbers look good.

These metrics are measured in Project 2 (test logs), Project 3 (usability and A/B) and reviewed in Project 4 (compliance).
