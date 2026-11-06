# Task cards and session commands

Print one card per task. Hand the card to the participant face up. Do not show the other card during the session.

Each card states "Today is Wednesday 28 October 2026 in this scenario." Keep to the scenario, even if the chat asks something the card does not cover. Use plausible answers that fit the card.

---

## Card X

**Today is Wednesday 28 October 2026 in this scenario.**

You are **Jamie Brooks**. Your policy number is **WTL456811**. Your car is a 2020 Mazda 2, rego **111JBX**.

Yesterday, about 2pm, a reversing car hit your parked car in the Chermside shopping centre car park. The rear bumper is cracked. The driver left a note on the windscreen: **Jo Hart, 0455 900 911, rego 911JHT**.

The car drives fine. No police were called. Nobody was hurt.

---

## Card Y

**Today is Wednesday 28 October 2026 in this scenario.**

You are **Robin Avery**. Your policy number is **WTL456812**. Your car is a 2019 Hyundai i20, rego **112RAY**.

This morning, about 8am, you were rear-ended at the lights on Wynnum Rd, Cannon Hill. You were driving. The boot is dented. The other driver was **Pat Kelly, 0455 900 912, rego 912PKY**.

The car drives fine. No police were called. Nobody was hurt.

---

## Counterbalancing

Four orders are used. Each participant does one task with variant A and one with variant B. The two cards are split across the two tasks, so each card is used with each variant across the group.

| Order | Task 1 | Task 2 |
|---|---|---|
| 1 | A with Card X | B with Card Y |
| 2 | B with Card X | A with Card Y |
| 3 | A with Card Y | B with Card X |
| 4 | B with Card Y | A with Card X |

Participants R01 to R08 take orders 1 to 4 in turn. R09 and R10 repeat orders 1 and 2.

## Session commands

Run from the `03-usability-ab` folder. Each command starts one session. The session file is saved when the chat ends (type `quit`). Each participant has two files: `Rnn-A.json` and `Rnn-B.json`.

| Participant | Order | Task 1 command | Task 2 command |
|---|---|---|---|
| R01 | 1 | `python chat_variant.py --participant R01 --variant A --card X` | `python chat_variant.py --participant R01 --variant B --card Y` |
| R02 | 2 | `python chat_variant.py --participant R02 --variant B --card X` | `python chat_variant.py --participant R02 --variant A --card Y` |
| R03 | 3 | `python chat_variant.py --participant R03 --variant A --card Y` | `python chat_variant.py --participant R03 --variant B --card X` |
| R04 | 4 | `python chat_variant.py --participant R04 --variant B --card Y` | `python chat_variant.py --participant R04 --variant A --card X` |
| R05 | 1 | `python chat_variant.py --participant R05 --variant A --card X` | `python chat_variant.py --participant R05 --variant B --card Y` |
| R06 | 2 | `python chat_variant.py --participant R06 --variant B --card X` | `python chat_variant.py --participant R06 --variant A --card Y` |
| R07 | 3 | `python chat_variant.py --participant R07 --variant A --card Y` | `python chat_variant.py --participant R07 --variant B --card X` |
| R08 | 4 | `python chat_variant.py --participant R08 --variant B --card Y` | `python chat_variant.py --participant R08 --variant A --card X` |
| R09 | 1 | `python chat_variant.py --participant R09 --variant A --card X` | `python chat_variant.py --participant R09 --variant B --card Y` |
| R10 | 2 | `python chat_variant.py --participant R10 --variant B --card X` | `python chat_variant.py --participant R10 --variant A --card Y` |

Notes:

- Start the session only after the consent form is signed.
- The terminal shows only "Sam:" and "You:". Do not print or show the variant to the participant.
- If a session is interrupted, the script still saves what it has. A second run for the same participant and variant is blocked, so move the first file aside and tell the analyst.
- The session file has `order_position` set to null. Use the order column in this table when you analyse.

Portfolio exercise, not legal or ethics advice. Check references against current versions before use.
