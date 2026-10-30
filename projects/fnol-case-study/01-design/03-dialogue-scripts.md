# Dialogue scripts: prompt inventory

Each node: the main prompt, two reprompts, and a voice variant where it differs. `{braces}` are variables. Copy is written at empathy level 1; level 2-3 overrides are listed at the end.

## Opening and safety

| ID | Prompt | Reprompt 1 | Reprompt 2 | Voice |
|----|--------|------------|------------|-------|
| N01 | Hi, I'm Sam, Wattle's claims assistant. I'm an AI, and I can help you report an accident or damage to your car. A person is available any time, just ask. | – | – | Same, minus "just ask"; add "say 'person' any time". |
| N02 | First, is anyone hurt, or is anyone in danger right now? | Just so I know you're safe: is anyone injured? [Yes] [No] [Not sure] | – (No-match counts as "Not sure") | Same. Treat silence as "Not sure" after one repeat. |
| S01 | Please call 000 now if anyone needs help. Your safety comes first and your claim can wait. When you're ready, I can arrange for a claims consultant to call you. [Call me later] [I'm OK, continue] | – | – | Says "Hang up and call triple zero." |

## Identity and vehicle

| ID | Prompt | Reprompt 1 | Reprompt 2 | Voice |
|----|--------|------------|------------|-------|
| N03 | To look up your policy, what's your policy number? It starts with WTL. If you don't have it, your date of birth and mobile number work too. | I couldn't find that one. Could you check the number, or use your date of birth and mobile instead? | I'm still not finding it. I'll connect you with someone who can look you up another way. | Read back in chunks: "W T L, four five six, seven eight nine. Right?" |
| N04 | Thanks, {first_name}. Which car was it? [{car_1}] [{car_2}] [Something else] | Which car: the {car_1} or the {car_2}? | – (buttons already shown; go to handoff offer) | "Was it the {car_1}, or the {car_2}?" |

## Story capture

| ID | Prompt | Reprompt 1 | Reprompt 2 |
|----|--------|------------|------------|
| N05 | Sorry to hear about the accident. In your own words, what happened? Include where and when if you can. | No problem if it's hard to put into words. Was it a crash with another car, something hitting your car while it was parked, or something else? | [Crash with another car] [Hit while parked] [Single car, e.g. hit a pole] [Theft] [Storm or hail] [Something else] |

## Missing-slot questions (asked only if the story didn't answer them)

| ID | Slot | Prompt | Reprompt 1 |
|----|------|--------|------------|
| N07 | `incident_type` | Were you driving at the time, or was the car parked? | [Driving] [Parked] [Not sure] |
| N08 | `date_time` | When did it happen? A rough time is fine. | For example, "this morning around 8" or "Saturday night". |
| N09 | `location` | Where did it happen? A street and suburb is enough. | You can also share your location if you're still there. [Share location] |
| N10 | `drivable` | Can the car be driven safely? | Is it safe to drive, or does it need a tow? [Safe to drive] [Needs a tow] [Not sure] |
| N10a | tow | I can book a tow now. Where's the car? | [Use my location] [Type an address] |
| N11 | `driver` | Were you driving, or someone else? | [I was] [Someone else] |
| N11a | `driver_name` | What's the driver's name? | – |
| N12 | `other_party` | Did you get the other driver's details? Their name, phone, rego, and insurer if they said. Whatever you have is fine. | No worries if you didn't. Do you have their rego, even a partial one? [I have some details] [I don't have any] |
| N13 | `police_ref` | Did the police attend, or have you reported it to them? | [Yes, I have a reference number] [Yes, no number yet] [No] |

## Confirmation, photos, lodgement

| ID | Prompt | Notes |
|----|--------|-------|
| N14 | Here's what I've got: {summary}. Is that all correct? [Yes, that's right] [Change something] | Summary in short lines, not a paragraph. On "Change": "What would you like to change?" |
| N15 | If you can, add a few photos of the damage. This helps the assessor. You can also add them later. [Add photos] [Later] | Never required. |
| N16 | Your claim is lodged. Your claim number is **{claim_id}**. A claims consultant will contact you within 1 business day to talk about next steps, including assessment and repairs. I've sent this to {email/mobile}. | "Lodged", never "approved". |
| N17 | Is there anything else I can help with? | – |
| N18 | Take care, {first_name}. If anything changes, reply to the message I sent and it'll come straight to your claim. | – |

## Digression responses (D)

| ID | Trigger | Response |
|----|---------|----------|
| D01 | Excess | Your policy schedule shows a basic excess of **${excess}**. Whether it applies to this claim depends on the details. For example, some policies waive it if you weren't at fault and the other driver can be identified. Your claims consultant will confirm. Shall we keep going? |
| D02 | Cover | Your policy is {policy_type}. Whether this claim is covered is confirmed when a consultant reviews it, so I can't say yes or no, but lodging it now is the first step. Shall we keep going? |
| D03 | Fault | I can't say who's at fault. That's worked out from the details of the claim. One general tip: it's best not to admit fault at the scene. Shall we keep going? |
| D04 | Hire car | Your policy {does / doesn't} list hire car cover. Your consultant can talk through options. Shall we keep going? |
| D05 | Premium | I can't predict that. Premiums are reviewed at renewal and depend on several things. Shall we keep going? |
| D06 | Claim or not | That's your call, and I can't advise either way. I can note the incident without lodging a claim, or connect you with someone to talk it through. [Note it only] [Lodge the claim] [Talk to someone] |

## Escalation and errors

| ID | Prompt |
|----|--------|
| H01 Ask for a person | Sure. I'll connect you now. I've saved everything you've told me, so you won't need to start again. |
| H02 Complaint | I'm sorry this hasn't gone the way it should. I've recorded your concerns as a complaint, and I can connect you with someone now. [Connect me] [Call me later] |
| H03 Vulnerability | Thank you for telling me. You don't have to go through the rest with me. Would you like someone from our team to call you? They can help with this. [Yes, call me] [Keep going here] |
| E05 System down | I couldn't lodge your claim just now because of a problem on our side. I've saved everything, and a claims consultant will call you within 1 business day to finish it. You won't need to start again. |
| No-input | Still there? No rush. Everything you've told me is saved. |

## Empathy level overrides

| Node | Level 2 (stressed) | Level 3 (distressed) |
|------|--------------------|----------------------|
| N05 | That sounds really stressful. When you're ready, tell me what happened. Just the basics is fine. | You're doing the right thing by reporting it. There's no rush. Are you somewhere safe right now? |
| N12 | If you didn't get their details, that's OK. | Skip; capture later by phone. |
| N15 | Skip; send photo link by SMS later. | Skip. |
| Any | Offer: "I can save this and we can finish later." | Offer a person after every second turn. |
