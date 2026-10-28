# Project 1: FNOL chatbot design

**Brief.** A customer has just had a car accident and opens chat to report it. Design the conversation so they can lodge a claim quickly, feel looked after, and never get a promise the insurer can't keep.

**Channel.** Web/app chat first. Voice notes are included where the design changes.

## What's in this folder

| File | What it covers |
|------|----------------|
| [01-persona-and-tone.md](01-persona-and-tone.md) | One-page persona, tone guide, the empathy ladder, words to use and avoid |
| [02-conversation-flows.md](02-conversation-flows.md) | Flow diagrams: master flow, happy path, error handling, digressions, disambiguation, escalation |
| [03-dialogue-scripts.md](03-dialogue-scripts.md) | Prompt inventory: every node's prompt, reprompts, confirmations and voice variant |
| [04-example-dialogues.md](04-example-dialogues.md) | The same intent in three emotional states, plus digression and disambiguation samples |
| [05-journey-map.md](05-journey-map.md) | Customer and claims-consultant journeys, emotion curve, where AI helps and where a human must |
| [06-nlu-and-handoff-spec.md](06-nlu-and-handoff-spec.md) | Intents, entities, slot rules, handoff payload, success metrics |

## The five design decisions that shape everything

1. **Safety before claim.** The first question after the greeting is "Is anyone hurt?" Injury or danger exits to 000 and a human. The claim can wait; a person can't.
2. **Story first, form second.** The customer tells it in their own words; the assistant extracts the details and asks only for what's missing. People in shock tell stories, not form fields. (Tested against form-first in Project 3.)
3. **Empathy scales with distress.** Same flow, different pace and wording. A calm customer gets efficiency; a shaken one gets slower turns, fewer questions and an early offer of a person.
4. **Inform, never decide.** The assistant can read the policy (e.g. the excess amount) but never says a claim is covered, who is at fault, or what will be paid. Those are claims decisions.
5. **Handoff without repeating.** Every escalation carries a structured summary, so the customer never tells the story twice.

## Scope

- **In:** collision with another vehicle, single-vehicle, hit while parked, theft, storm/hail, vandalism, windscreen. Policyholder or listed driver reporting.
- **Out (routed to a human):** injury claims, third parties claiming against a customer, commercial/fleet policies, claim disputes and complaints.

## Assumptions (fictional)

- Brand: Wattle Car Insurance. Assistant name: **Sam**.
- Tools available to the assistant: `verify_identity`, `get_policy`, `create_claim`, `book_tow`, `request_callback`, `handoff_to_human`.
- Service level stated to customers: a claims consultant contacts them within **1 business day**.
